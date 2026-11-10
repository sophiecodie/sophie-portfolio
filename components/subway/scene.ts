// Three.js side of the subway site: loads the baked station + the live-lit train,
// moves the camera between stops, and reports clicks on props back to React.
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { DRACOLoader } from "three/examples/jsm/loaders/DRACOLoader.js";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";

export type Stop = { pos: number[]; look: number[]; fov: number };
export type Layout = {
  stops: Record<string, Stop>;
  projectY0: number;
  projectStep: number;
  titleSignY: number;
};

// Blender is Z-up with the track along +Y; three is Y-up. (x, y, z) -> (x, z, -y)
export const b2t = (v: number[]) => new THREE.Vector3(v[0], v[2], -v[1]);

type Hotspot = { id: string; box: THREE.Box3 };

export class SubwayScene {
  renderer: THREE.WebGLRenderer;
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(60, 1, 0.05, 400);
  train?: THREE.Object3D;
  private raf = 0;
  private hot: Hotspot[] = [];
  private from = { pos: new THREE.Vector3(), look: new THREE.Vector3(), fov: 60 };
  private to = { pos: new THREE.Vector3(), look: new THREE.Vector3(), fov: 60 };
  private look = new THREE.Vector3();
  private t = 1;
  private dur = 1;
  private trainT = 0;
  private trainFrom = -100;
  private trainTo = -10.5;
  private pointer = new THREE.Vector2(0, 0);
  private sway = new THREE.Vector2(0, 0);
  private clock = new THREE.Clock();
  reduced = false;
  onHover?: (id: string | null) => void;

  constructor(private canvas: HTMLCanvasElement, private layout: Layout) {
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: "high-performance" });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.NoToneMapping;
    this.scene.background = new THREE.Color("#2a211c");
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this.scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    // live light for the train only (the station is baked)
    this.scene.add(new THREE.HemisphereLight("#fff3df", "#6b5a4a", 1.6));
    const d = new THREE.DirectionalLight("#ffe7c4", 1.4);
    d.position.set(3, 4, 2);
    this.scene.add(d);
    this.buildHotspots();
    const s = layout.stops.title;
    this.jump(s);
  }

  async load(base: string, onProgress: (p: number) => void) {
    const loader = new GLTFLoader();
    const draco = new DRACOLoader();
    draco.setDecoderPath("/draco/");
    loader.setDRACOLoader(draco);
    const prog: Record<string, number> = { station: 0, train: 0 };
    const tick = () => onProgress(prog.station * 0.85 + prog.train * 0.15);
    const get = (url: string, key: string) =>
      new Promise<THREE.Group>((res, rej) =>
        loader.load(url, (g) => res(g.scene), (e) => { if (e.total) { prog[key] = e.loaded / e.total; tick(); } }, rej));
    const [station, train] = await Promise.all([get(base + "/station.glb", "station"), get(base + "/train.glb", "train")]);
    station.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) {
        const old = m.material as THREE.MeshStandardMaterial;
        m.material = new THREE.MeshBasicMaterial({ map: old.map });
        old.dispose();
      }
    });
    this.scene.add(station);
    train.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) (m.material as THREE.MeshStandardMaterial).envMapIntensity = 0.9;
    });
    this.train = train;
    this.scene.add(train);
    this.placeTrain(0);
    onProgress(1);
  }

  /** Train slides in from the far tunnel and stops by the title sign. */
  arrive() {
    this.trainT = this.reduced ? 1 : 0.0001;
  }

  private placeTrain(k: number) {
    if (!this.train) return;
    const e = 1 - Math.pow(1 - k, 3);
    // train front faces -Y in Blender (toward the camera at the title stop). Its local +Y runs back.
    const yB = this.trainFrom + (this.trainTo - this.trainFrom) * e; // three z
    this.train.position.set(0, 0, yB);
  }

  private buildHotspots() {
    const L = this.layout;
    const box = (id: string, c: number[], s: number[]) => {
      const a = b2t([c[0] - s[0] / 2, c[1] - s[1] / 2, c[2] - s[2] / 2]);
      const b = b2t([c[0] + s[0] / 2, c[1] + s[1] / 2, c[2] + s[2] / 2]);
      this.hot.push({ id, box: new THREE.Box3().setFromPoints([a, b]) });
    };
    box("map", [4.9, 13, 2.1], [0.4, 4, 3]);
    box("board", [3.25, 19, 2.55], [1, 3.4, 2.2]);
    box("newsstand", [3.6, 72, 1.6], [2, 3.2, 3.2]);
    box("exit", [3.35, 83, 2.2], [2.6, 7, 4.4]);
    box("train", [0, -4, 1.6], [2.8, 30, 3.2]);
    const ids = ["college-app-atlas", "purchase-intent", "new-york-census", "folio", "agent00hl7", "dream-team", "neurobiome"];
    ids.forEach((id, i) => box("project:" + id, [4.9, L.projectY0 + i * L.projectStep, 2.1], [0.4, 4.2, 2.6]));
  }

  pick(clientX: number, clientY: number): string | null {
    const r = this.canvas.getBoundingClientRect();
    const v = new THREE.Vector2(((clientX - r.left) / r.width) * 2 - 1, -((clientY - r.top) / r.height) * 2 + 1);
    const ray = new THREE.Raycaster();
    ray.setFromCamera(v, this.camera);
    let best: { id: string; d: number } | null = null;
    const p = new THREE.Vector3();
    for (const h of this.hot) {
      if (h.id === "train" && !this.train) continue;
      if (ray.ray.intersectBox(h.box, p)) {
        const d = p.distanceTo(ray.ray.origin);
        if (d < 30 && (!best || d < best.d)) best = { id: h.id, d };
      }
    }
    return best?.id ?? null;
  }

  setPointer(x: number, y: number) {
    this.pointer.set(x, y);
  }

  jump(s: Stop) {
    this.from.pos.copy(b2t(s.pos)); this.to.pos.copy(this.from.pos);
    this.from.look.copy(b2t(s.look)); this.to.look.copy(this.from.look);
    this.from.fov = this.to.fov = s.fov; this.t = 1;
    this.apply(1);
  }

  goTo(s: Stop) {
    if (this.reduced) return this.jump(s);
    this.from.pos.copy(this.camera.position);
    this.from.look.copy(this.look);
    this.from.fov = this.camera.fov;
    this.to.pos.copy(b2t(s.pos)); this.to.look.copy(b2t(s.look)); this.to.fov = s.fov;
    const dist = this.from.pos.distanceTo(this.to.pos);
    this.dur = Math.min(3.2, 0.9 + dist / 14);
    this.t = 0;
  }

  private apply(k: number) {
    const e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
    this.camera.position.lerpVectors(this.from.pos, this.to.pos, e);
    // lift the camera slightly mid-move, like walking
    this.camera.position.y += Math.sin(Math.PI * e) * 0.15;
    this.look.lerpVectors(this.from.look, this.to.look, e);
    this.camera.fov = this.from.fov + (this.to.fov - this.from.fov) * e;
  }

  resize() {
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  start() {
    const loop = () => {
      this.raf = requestAnimationFrame(loop);
      const dt = Math.min(this.clock.getDelta(), 0.05);
      if (this.t < 1) { this.t = Math.min(1, this.t + dt / this.dur); this.apply(this.t); }
      if (this.trainT > 0 && this.trainT < 1) { this.trainT = Math.min(1, this.trainT + dt / 6); this.placeTrain(this.trainT); }
      // gentle look-around that follows the pointer
      const k = this.reduced ? 0 : 1;
      this.sway.lerp(new THREE.Vector2(this.pointer.x * k, this.pointer.y * k), 0.05);
      const target = this.look.clone();
      const right = new THREE.Vector3().subVectors(target, this.camera.position).cross(new THREE.Vector3(0, 1, 0)).normalize();
      target.addScaledVector(right, this.sway.x * 0.6).add(new THREE.Vector3(0, this.sway.y * 0.35, 0));
      this.camera.lookAt(target);
      this.camera.updateProjectionMatrix();
      this.renderer.render(this.scene, this.camera);
    };
    loop();
  }

  dispose() {
    cancelAnimationFrame(this.raf);
    this.renderer.dispose();
  }
}
