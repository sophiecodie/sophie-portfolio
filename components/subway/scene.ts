// Three.js side of the dollhouse station. It loads the baked cutaway (its fourth wall is
// its own set of meshes, so it can be hidden), and the live-lit train. It flies the camera
// between stops, runs the drift and look-around, and answers hover, pick and screen-rect
// queries for the React side. Coordinates are Blender's (Z up, track along +Y) and are
// converted with b2t.
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { DRACOLoader } from "three/examples/jsm/loaders/DRACOLoader.js";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";

export type Stop = { pos: number[]; look: number[]; fov: number };
export type Hotspot = { id: string; level: string; c: number[]; s: number[] };
export type Layout = {
  stops: Record<string, Stop>;
  hotspots: Hotspot[];
  walk: Record<string, string[]>;
  levels: Record<string, { floor: number; ceiling: number | null }>;
  station: { yMin: number; yMax: number; xHalf: number; streetHalf: number };
  train: { stopY: number; parkY: number };
  projectY0: number;
  projectStep: number;
  titleSignY: number;
};
export type Mode = "overview" | "inside";
export type Rect = { left: number; top: number; width: number; height: number };

// Blender is Z-up with the track along +Y; three is Y-up. (x, y, z) -> (x, z, -y)
export const b2t = (v: number[]) => new THREE.Vector3(v[0], v[2], -v[1]);

const UP = new THREE.Vector3(0, 1, 0);
const GOLD = 0xf2c24c;
const ease = (k: number) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2);

type View = { pos: THREE.Vector3; look: THREE.Vector3; fov: number };
type Flight = {
  curve: THREE.CatmullRomCurve3;
  fromLook: THREE.Vector3;
  toLook: THREE.Vector3;
  fromFov: number;
  toFov: number;
  dur: number;
  t: number;
  done: () => void;
};

export class DollhouseScene {
  renderer: THREE.WebGLRenderer;
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(40, 1, 0.05, 400);
  reduced = false;

  private raf = 0;
  private clock = new THREE.Clock();
  private time = 0;
  private raycaster = new THREE.Raycaster();
  private hot = new Map<string, THREE.Box3>();
  private hotSpec = new Map<string, Hotspot>();
  private dimMeshes = new Map<string, THREE.Mesh>();
  private outline: THREE.LineSegments;
  private outlineMat: THREE.LineBasicMaterial;
  private hoverId: string | null = null;
  private fourthMeshes: THREE.Mesh[] = [];
  private fourthMats: THREE.MeshBasicMaterial[] = [];
  private fw = 0;
  private fwTarget = 0;
  private train?: THREE.Object3D;
  private trainY: number;
  private trainAnim: { from: number; to: number; dur: number; t: number; done: () => void } | null = null;
  private flight: Flight | null = null;
  private base: View;
  private mode: Mode = "overview";
  private activeLevel: string | null = null;
  private pos = new THREE.Vector3();
  private look = new THREE.Vector3();
  private fov = 40;
  private yaw = 0;
  private pitch = 0;
  private zoom = 0;
  private pointer = new THREE.Vector2();
  private pointerSmooth = new THREE.Vector2();

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

    this.base = this.viewOf(layout.stops.overview);
    this.cut(this.base, "overview");
    this.trainY = layout.train.parkY;

    for (const h of layout.hotspots) {
      const c = h.c, s = h.s;
      const a = b2t([c[0] - s[0] / 2, c[1] - s[1] / 2, c[2] - s[2] / 2]);
      const b = b2t([c[0] + s[0] / 2, c[1] + s[1] / 2, c[2] + s[2] / 2]);
      this.hot.set(h.id, new THREE.Box3().setFromPoints([a, b]));
      this.hotSpec.set(h.id, h);
      if (h.id.startsWith("project:")) {
        const m = new THREE.Mesh(
          new THREE.BoxGeometry(s[0], s[2], s[1]),
          new THREE.MeshBasicMaterial({ color: 0x1b1410, transparent: true, opacity: 0.5, depthWrite: false }),
        );
        m.position.copy(b2t(c));
        m.visible = false;
        this.scene.add(m);
        this.dimMeshes.set(h.id, m);
      }
    }
    // hover outline: a unit box scaled to whichever hotspot is under the pointer
    this.outlineMat = new THREE.LineBasicMaterial({ color: GOLD, transparent: true, opacity: 0.95, depthTest: false });
    this.outline = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(1, 1, 1)), this.outlineMat);
    this.outline.renderOrder = 10;
    this.outline.visible = false;
    this.scene.add(this.outline);
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
    const [station, train] = await Promise.all([
      get(base + "/station-dollhouse.glb", "station"),
      get(base + "/train.glb", "train"),
    ]);
    station.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      const old = m.material as THREE.MeshStandardMaterial;
      const fourth = m.name.startsWith("fourth_wall") || (old.name || "").startsWith("fourth_wall");
      // the bake already lit everything, so the station is shown unlit
      const mat = new THREE.MeshBasicMaterial({ map: old.map, transparent: fourth });
      m.material = mat;
      old.dispose();
      if (fourth) {
        this.fourthMeshes.push(m);
        this.fourthMats.push(mat);
      }
    });
    this.scene.add(station);
    this.setFourthWall(false, true);
    train.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) (m.material as THREE.MeshStandardMaterial).envMapIntensity = 0.9;
    });
    this.train = train;
    this.scene.add(train);
    this.placeTrain();
    onProgress(1);
  }

  start() {
    const loop = () => {
      this.raf = requestAnimationFrame(loop);
      const dt = Math.min(this.clock.getDelta(), 0.05);
      this.update(dt);
      this.renderer.render(this.scene, this.camera);
    };
    loop();
  }

  resize() {
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  dispose() {
    cancelAnimationFrame(this.raf);
    this.renderer.dispose();
  }

  // ------------------------------------------------------------ views and flights
  private viewOf(s: Stop): View {
    return { pos: b2t(s.pos), look: b2t(s.look), fov: s.fov };
  }

  /** Jump to a view with no motion. */
  private cut(v: View, mode: Mode) {
    this.base = v;
    this.mode = mode;
    this.yaw = 0;
    this.pitch = 0;
    this.pos.copy(v.pos);
    this.look.copy(v.look);
    this.fov = v.fov;
  }

  /**
   * Fly the camera to a stop. `via` holds waypoints in Blender coordinates; the route
   * passes through them, so a flight into a level can come in from outside the cut.
   * Resolves when the camera arrives. Reduced motion turns this into a cut.
   */
  fly(stop: Stop, mode: Mode, via: number[][] = []): Promise<void> {
    const to = this.viewOf(stop);
    if (this.reduced) {
      this.cut(to, mode);
      return Promise.resolve();
    }
    const pts = [this.pos.clone()];
    for (const v of via) {
      const p = b2t(v);
      if (p.distanceTo(pts[pts.length - 1]) > 0.05) pts.push(p);
    }
    if (to.pos.distanceTo(pts[pts.length - 1]) > 0.05) pts.push(to.pos.clone());
    const curve = new THREE.CatmullRomCurve3(pts, false, "centripetal");
    const len = curve.getLength();
    // 0.8 to 1.2 seconds, a little longer for a longer swoop
    const dur = Math.min(1.2, Math.max(0.8, 0.6 + len / 60));
    return new Promise((resolve) => {
      this.flight = {
        curve,
        fromLook: this.look.clone(),
        toLook: to.look.clone(),
        fromFov: this.fov,
        toFov: to.fov,
        dur,
        t: 0,
        done: () => {
          this.cut(to, mode);
          resolve();
        },
      };
    });
  }

  setActiveLevel(level: string | null) {
    this.activeLevel = level;
  }

  /** Overview: pointer parallax and scroll zoom. Inside: drag to look around. */
  setPointer(nx: number, ny: number) {
    this.pointer.set(nx, ny);
  }

  zoomBy(dy: number) {
    if (this.mode !== "overview") return;
    this.zoom = Math.max(-6, Math.min(6, this.zoom + dy * 0.01));
  }

  drag(dx: number, dy: number) {
    if (this.mode !== "inside" || this.flight) return;
    this.yaw = Math.max(-0.9, Math.min(0.9, this.yaw - dx * 0.004));
    this.pitch = Math.max(-0.4, Math.min(0.4, this.pitch - dy * 0.003));
  }

  private insideLook(): THREE.Vector3 {
    const dir = this.base.look.clone().sub(this.base.pos).normalize();
    dir.applyAxisAngle(UP, this.yaw);
    const right = new THREE.Vector3().crossVectors(dir, UP).normalize();
    dir.applyAxisAngle(right, this.pitch);
    return this.base.pos.clone().add(dir);
  }

  setFourthWall(visible: boolean, instant = false) {
    this.fwTarget = visible ? 1 : 0;
    if (instant || this.reduced) {
      this.fw = this.fwTarget;
      this.applyFourth();
    }
  }

  private applyFourth() {
    for (const m of this.fourthMats) m.opacity = this.fw;
    for (const m of this.fourthMeshes) m.visible = this.fw > 0.01;
  }

  // ------------------------------------------------------------ train
  private placeTrain() {
    if (this.train) this.train.position.set(0, 0, -this.trainY);
  }

  /** Move the train's front to a Blender y over `dur` seconds (0 = now). */
  trainTo(y: number, dur: number): Promise<void> {
    if (this.reduced) dur = 0;
    return new Promise((resolve) => {
      this.trainAnim = { from: this.trainY, to: y, dur, t: 0, done: resolve };
    });
  }

  // ------------------------------------------------------------ hover, dim, pick
  setHover(id: string | null) {
    if (id === this.hoverId) return;
    this.hoverId = id;
    const h = id ? this.hotSpec.get(id) : undefined;
    if (!h) {
      this.outline.visible = false;
      return;
    }
    this.outline.visible = true;
    this.outline.position.copy(b2t(h.c));
    this.outline.scale.set(h.s[0] * 1.02, h.s[2] * 1.02, h.s[1] * 1.02);
  }

  /** Dim the project tiles that are not in `ids` (null clears the filter). */
  setDim(ids: string[] | null) {
    for (const [id, m] of this.dimMeshes) m.visible = ids !== null && !ids.includes(id.replace("project:", ""));
  }

  pick(clientX: number, clientY: number): string | null {
    if (this.flight || this.trainAnim) return null;
    const r = this.canvas.getBoundingClientRect();
    const ndc = new THREE.Vector2(((clientX - r.left) / r.width) * 2 - 1, -((clientY - r.top) / r.height) * 2 + 1);
    this.raycaster.setFromCamera(ndc, this.camera);
    let obj: { id: string; d: number } | null = null;
    let lvl: { id: string; d: number } | null = null;
    const p = new THREE.Vector3();
    for (const [id, box] of this.hot) {
      const spec = this.hotSpec.get(id);
      if (!spec) continue;
      // inside a level only that level's objects can be picked
      if (this.mode === "inside" && (id.startsWith("level:") || spec.level !== this.activeLevel)) continue;
      if (!this.raycaster.ray.intersectBox(box, p)) continue;
      const d = p.distanceTo(this.raycaster.ray.origin);
      if (id.startsWith("level:")) {
        if (!lvl || d < lvl.d) lvl = { id, d };
      } else if (!obj || d < obj.d) {
        obj = { id, d };
      }
    }
    // objects win over the level around them
    return (obj ?? lvl)?.id ?? null;
  }

  /** Where a hotspot sits on the screen, in client pixels (for the card's opening animation). */
  screenRect(id: string): Rect | null {
    const h = this.hotSpec.get(id);
    if (!h) return null;
    this.camera.updateMatrixWorld();
    const r = this.canvas.getBoundingClientRect();
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const dx of [-0.5, 0.5]) for (const dy of [-0.5, 0.5]) for (const dz of [-0.5, 0.5]) {
      const p = b2t([h.c[0] + dx * h.s[0], h.c[1] + dy * h.s[1], h.c[2] + dz * h.s[2]]).project(this.camera);
      const x = r.left + ((p.x + 1) / 2) * r.width;
      const y = r.top + ((1 - p.y) / 2) * r.height;
      x0 = Math.min(x0, x); x1 = Math.max(x1, x);
      y0 = Math.min(y0, y); y1 = Math.max(y1, y);
    }
    return { left: x0, top: y0, width: x1 - x0, height: y1 - y0 };
  }

  // ------------------------------------------------------------ frame
  private update(dt: number) {
    this.time += dt;

    // fourth wall fades in or out over about 0.3 s
    if (this.fw !== this.fwTarget) {
      const step = dt / 0.3;
      this.fw = this.fwTarget > this.fw ? Math.min(this.fwTarget, this.fw + step) : Math.max(this.fwTarget, this.fw - step);
      this.applyFourth();
    }

    if (this.trainAnim) {
      const a = this.trainAnim;
      a.t = a.dur > 0 ? Math.min(1, a.t + dt / a.dur) : 1;
      this.trainY = a.from + (a.to - a.from) * ease(a.t);
      this.placeTrain();
      if (a.t >= 1) {
        this.trainAnim = null;
        a.done();
      }
    }

    if (this.flight) {
      const f = this.flight;
      f.t = Math.min(1, f.t + dt / f.dur);
      const e = ease(f.t);
      this.pos.copy(f.curve.getPointAt(e));
      this.look.lerpVectors(f.fromLook, f.toLook, e);
      this.fov = f.fromFov + (f.toFov - f.fromFov) * e;
      if (f.t >= 1) {
        this.flight = null;
        f.done();
      }
    } else if (this.mode === "overview") {
      const k = this.reduced ? 0 : 1;
      this.pointerSmooth.lerp(this.pointer, Math.min(1, dt * 3));
      // a slow drift, and a parallax of a few degrees at most
      const drift = new THREE.Vector3(0, Math.sin(this.time * 0.09) * 0.5 * k, Math.cos(this.time * 0.06) * 0.25 * k);
      this.pos.copy(this.base.pos).add(drift);
      this.look.copy(this.base.look).add(new THREE.Vector3(this.pointerSmooth.x * 1.2 * k, this.pointerSmooth.y * 0.5 * k, 0));
      this.fov = this.base.fov + this.zoom;
    } else {
      this.pos.copy(this.base.pos);
      this.look.copy(this.insideLook());
      this.fov = this.base.fov;
    }

    this.camera.position.copy(this.pos);
    this.camera.lookAt(this.look);
    if (Math.abs(this.camera.fov - this.fov) > 1e-3) {
      this.camera.fov = this.fov;
      this.camera.updateProjectionMatrix();
    }
    if (this.outline.visible) this.outlineMat.opacity = 0.65 + 0.35 * Math.sin(this.time * 4);
  }
}
