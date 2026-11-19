// Three.js side of the dollhouse station. It loads the baked cutaway (its fourth wall is
// its own set of meshes, so it can be hidden), and the live-lit train. It flies the camera
// between stops, runs the drift and look-around, and answers hover, pick and screen-rect
// queries for the React side. Coordinates are Blender's (Z up, track along +Y) and are
// converted with b2t.
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { DRACOLoader } from "three/examples/jsm/loaders/DRACOLoader.js";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";

// raw: use fov as is (the overview frames itself); otherwise fov is widened on narrow screens
export type Stop = { pos: number[]; look: number[]; fov: number; raw?: boolean };
export type Hotspot = { id: string; level: string; c: number[]; s: number[] };
export type Layout = {
  stops: Record<string, Stop>;
  hotspots: Hotspot[];
  walk: Record<string, string[]>;
  levels: Record<string, { floor: number; ceiling: number | null }>;
  station: { yMin: number; yMax: number; xHalf: number; streetHalf: number };
  train: { stopY: number; parkY: number; ahead?: number };
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
// a train pulling in: fast out of the tunnel, braking gently to a stop
const brake = (k: number) => 1 - Math.pow(1 - k, 3);

// The overview is a straight-on section through the cut: street, mezzanine and platform
// stacked and filling the canvas from top to bottom, and the camera slides along the track.
// z0..z1 is the slice of the station that fills the canvas height, in meters, measured on the
// cut plane at x = plane. A narrow lens keeps it close to a flat section drawing; the small
// tilt lets you see a little of each floor. Edit these to reframe.
// minW: on a narrow (phone) screen the view widens to at least this many meters of track and
// the extra height goes to the sky above the street.
const SECTION = { z0: -1.1, z1: 11.4, plane: -6, tilt: 0.03, fov: 14, backX: 5, minW: 12 };
// how far across each walkable floor you can go (Blender x, m); the platform keeps you between
// its edge (x = 1.7, the tracks are past it) and the poster wall (x = 5)
const WALK_X = { platform: [2.1, 4.3] as [number, number] };
// inside a level, screens narrower than this keep the horizontal field of view of this aspect
const REF_ASPECT = 1.3;

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
  private trainAnim: { from: number; to: number; dur: number; t: number; fn: (k: number) => number; done: () => void } | null = null;
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
  // inside a level, how far the camera has been scrolled along the track (m, Blender +y)
  private slide = 0;
  private slideTarget = 0;
  // the mezzanine is walkable: an offset from the stop (three.js units), eased toward its target
  private walkOff = new THREE.Vector3();
  private walkTarget = new THREE.Vector3();
  // night sky seen up the street stairs from the mezzanine (only shown on that floor)
  private exitSky?: THREE.Mesh;
  // the train's look: its line color and route bullet, and how see-through it is
  private trainPaint: THREE.MeshStandardMaterial[] = [];
  private trainMats: THREE.Material[] = [];
  private bullet?: { tex: THREE.CanvasTexture; ctx: CanvasRenderingContext2D };
  private trainAlpha = 1;
  trainLine: string | null = null;
  // overview pan: where along the track (Blender y) the section is centered
  private panY: number;
  private panTarget: number;
  // the slot behind the street level for the NYC street background (a placeholder sky for now)
  private backdrop: THREE.Mesh;

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

    // the overview opens at the far end: street entrance, About chalkboard, books
    this.panY = this.panTarget = layout.station.yMax;
    this.base = this.overviewView();
    this.cut(this.base, "overview");
    this.backdrop = this.makeBackdrop();
    this.scene.add(this.backdrop);
    this.exitSky = this.makeExitSky();
    this.scene.add(this.exitSky);
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
    train.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      for (const mt of (Array.isArray(m.material) ? m.material : [m.material]) as THREE.MeshStandardMaterial[]) {
        if (!this.trainMats.includes(mt)) this.trainMats.push(mt);
        const n = mt.name || "";
        if (n.startsWith("car_paint_") || (n.startsWith("car_route_") && n !== "car_route_white")) this.trainPaint.push(mt);
      }
    });
    // the route bullet on the cab: a drawn disc over the baked-in letter, so it can change
    const letter = train.getObjectByName("car0_T_S");
    if (letter?.parent) {
      const c = document.createElement("canvas");
      c.width = c.height = 128;
      const tex = new THREE.CanvasTexture(c);
      tex.colorSpace = THREE.SRGBColorSpace;
      this.bullet = { tex, ctx: c.getContext("2d")! };
      const disc = new THREE.Mesh(new THREE.PlaneGeometry(0.46, 0.46), new THREE.MeshBasicMaterial({ map: tex, transparent: true }));
      disc.position.copy(letter.position).add(new THREE.Vector3(0, 0, 0.012));
      letter.parent.add(disc);
      letter.visible = false;
    }
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

  // ------------------------------------------------------------ the full-screen section (overview)
  /** Camera for the section view centered at track position y (Blender). */
  /** Height of the section on screen (m), the camera distance, and the height of its center. */
  private frame() {
    const S = SECTION;
    const h = Math.max(S.z1 - S.z0, S.minW / Math.max(0.1, this.camera.aspect));
    const dist = h / 2 / Math.tan(THREE.MathUtils.degToRad(S.fov / 2));
    return { h, dist, zc: S.z0 + h / 2 };
  }

  private overviewView(y = this.panY): View {
    const S = SECTION;
    const { dist, zc } = this.frame();
    return {
      pos: b2t([S.plane - dist * Math.cos(S.tilt), y, zc + dist * Math.sin(S.tilt)]),
      look: b2t([S.plane, y, zc]),
      fov: S.fov,
    };
  }

  /** Half the visible length of track, measured at the back wall (the widest part seen). */
  private halfSpan() {
    const S = SECTION;
    const { h, dist } = this.frame();
    return (h / 2) * this.camera.aspect * ((dist + S.backX - S.plane) / dist);
  }

  /** The range the overview can pan over without showing past either end of the station. */
  panRange() {
    const st = this.layout.station;
    const half = this.halfSpan();
    const lo = st.yMin + half, hi = st.yMax - half;
    return lo <= hi ? { lo, hi, at: this.panTarget } : { lo: (lo + hi) / 2, hi: (lo + hi) / 2, at: (lo + hi) / 2 };
  }

  private clampPan(y: number) {
    const r = this.panRange();
    return Math.max(r.lo, Math.min(r.hi, y));
  }

  /** Slide the section along the track by dy meters (positive = further along the line). */
  panBy(dy: number) {
    if (this.mode !== "overview" || this.flight) return;
    this.panTarget = this.clampPan(this.panTarget + dy);
  }

  /** Meters of track per screen pixel in the overview, at the cut plane. */
  metersPerPixel() {
    const { h } = this.frame();
    return h / Math.max(1, this.canvas.clientHeight);
  }

  /** The overview as a stop to fly to, optionally centered on track position y. */
  overviewStop(y?: number): Stop {
    if (y !== undefined) this.panY = this.panTarget = this.clampPan(y);
    const v = this.overviewView(this.panTarget);
    const back = (p: THREE.Vector3) => [p.x, -p.z, p.y];
    return { pos: back(v.pos), look: back(v.look), fov: v.fov, raw: true };
  }

  /** Where a Blender point lands on screen, in client pixels. */
  toScreen(v: number[]): { x: number; y: number } {
    this.camera.updateMatrixWorld();
    const r = this.canvas.getBoundingClientRect();
    const p = b2t(v).project(this.camera);
    return { x: r.left + ((p.x + 1) / 2) * r.width, y: r.top + ((1 - p.y) / 2) * r.height };
  }

  /**
   * The slot behind the street level. Right now it is a plain sky gradient; the NYC street
   * background (photo + depth) replaces it through setStreetBackdrop.
   */
  private makeBackdrop() {
    const c = document.createElement("canvas");
    c.width = 4;
    c.height = 256;
    const g = c.getContext("2d")!;
    const grad = g.createLinearGradient(0, 0, 0, 256);
    grad.addColorStop(0, "#8fb9d6");
    grad.addColorStop(0.5, "#f6e2c4");
    grad.addColorStop(0.62, "#7b6248");
    grad.addColorStop(1, "#5a4634");
    g.fillStyle = grad;
    g.fillRect(0, 0, 4, 256);
    const tex = new THREE.CanvasTexture(c);
    tex.colorSpace = THREE.SRGBColorSpace;
    // a tall wall far behind the street, from z = -14 to 40 (Blender), horizon near the sidewalk
    const st = this.layout.station;
    const m = new THREE.Mesh(new THREE.PlaneGeometry(st.yMax - st.yMin + 160, 54), new THREE.MeshBasicMaterial({ map: tex, depthWrite: false }));
    m.name = "street_backdrop";
    m.position.copy(b2t([st.streetHalf + 20, (st.yMin + st.yMax) / 2, 13]));
    m.rotation.y = -Math.PI / 2;
    m.renderOrder = -1;
    return m;
  }

  /**
   * The night beyond the top of the street stairs, as seen from the mezzanine: a dark blue sky
   * with a few stars and a low skyline. It stands past the end of the station and is only
   * drawn while you are inside the mezzanine, so it never shows in the other views.
   */
  private makeExitSky() {
    const c = document.createElement("canvas");
    c.width = 512;
    c.height = 512;
    const g = c.getContext("2d")!;
    const grad = g.createLinearGradient(0, 0, 0, 512);
    grad.addColorStop(0, "#070b1c");
    grad.addColorStop(0.6, "#14204a");
    grad.addColorStop(1, "#2b3768");
    g.fillStyle = grad;
    g.fillRect(0, 0, 512, 512);
    let seed = 7;
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    g.fillStyle = "rgba(255,255,255,0.8)";
    for (let i = 0; i < 70; i++) g.fillRect(rnd() * 512, rnd() * 300, 1.5, 1.5);
    // a low row of buildings with a few warm windows
    for (let x = 0; x < 512; ) {
      const w = 30 + rnd() * 50, h = 50 + rnd() * 110;
      g.fillStyle = "#0b0f22";
      g.fillRect(x, 512 - h, w, h);
      g.fillStyle = "#f6c86a";
      for (let k = 0; k < 4; k++) if (rnd() < 0.5) g.fillRect(x + 5 + rnd() * (w - 12), 512 - h + 8 + rnd() * (h - 20), 4, 5);
      x += w + 2;
    }
    const tex = new THREE.CanvasTexture(c);
    tex.colorSpace = THREE.SRGBColorSpace;
    const st = this.layout.station;
    const zFloor = this.layout.levels.street.floor;
    const m = new THREE.Mesh(new THREE.PlaneGeometry(36, 24), new THREE.MeshBasicMaterial({ map: tex, fog: false }));
    m.name = "exit_sky";
    // 10 m past the end of the station, facing back down the stairs (-Y), bottom at the street
    m.position.copy(b2t([0, st.yMax + 10, zFloor - 1 + 12]));
    m.visible = false;
    return m;
  }

  /** Swap in a texture (or any material) for the background behind the street level. */
  setStreetBackdrop(material: THREE.Material) {
    const old = this.backdrop.material as THREE.Material;
    this.backdrop.material = material;
    old.dispose();
  }

  // ------------------------------------------------------------ views and flights
  private viewOf(s: Stop): View {
    let fov = s.fov;
    const a = this.camera.aspect;
    if (!s.raw && a < REF_ASPECT) {
      // keep the side-to-side view of a wider screen, so a phone sees the same things
      const t = Math.tan(THREE.MathUtils.degToRad(fov / 2)) * REF_ASPECT / a;
      fov = Math.min(100, THREE.MathUtils.radToDeg(2 * Math.atan(t)));
    }
    return { pos: b2t(s.pos), look: b2t(s.look), fov };
  }

  /** Jump to a view with no motion. */
  private cut(v: View, mode: Mode) {
    this.base = v;
    this.mode = mode;
    this.yaw = 0;
    this.pitch = 0;
    this.slide = 0;
    this.slideTarget = 0;
    this.walkOff.set(0, 0, 0);
    this.walkTarget.set(0, 0, 0);
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
    // already there (or every waypoint is where we stand): a curve needs two points, so just cut
    if (pts.length < 2) { this.cut(to, mode); return Promise.resolve(); }
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

  /** Jump straight to a named stop with no flight (used for the opening shot). */
  jump(name: string, mode: Mode) {
    const s = this.layout.stops[name];
    if (s) this.cut(this.viewOf(s), mode);
  }

  setActiveLevel(level: string | null) {
    this.activeLevel = level;
  }

  /** Overview: pointer parallax and scroll zoom. Inside: drag to look around. */
  setPointer(nx: number, ny: number) {
    this.pointer.set(nx, ny);
  }

  /** Scrolling: slides the section in the overview, and slides the camera along the level inside. */
  zoomBy(dy: number) {
    if (this.mode === "overview") this.panBy(dy * 0.02);
    else if (this.walkable() && !this.flight) this.walkBy(-dy * 0.01);
    else if (this.mode === "inside" && !this.flight) this.slideTarget = Math.max(-7, Math.min(7, this.slideTarget + dy * 0.01));
  }

  drag(dx: number, dy: number, touch = false) {
    if (this.mode === "overview") {
      // screen right is -y along the track (the camera looks through the left-hand cut)
      this.panBy(dx * this.metersPerPixel());
      return;
    }
    if (this.mode !== "inside" || this.flight) return;
    if (this.walkable()) {
      // the mezzanine: turn all the way around; on a touch screen, dragging up walks forward
      this.yaw -= dx * 0.004;
      if (touch) this.walkBy(dy * 0.02);
      else this.pitch = Math.max(-0.6, Math.min(0.6, this.pitch - dy * 0.003));
      return;
    }
    this.yaw = Math.max(-0.9, Math.min(0.9, this.yaw - dx * 0.004));
    this.pitch = Math.max(-0.4, Math.min(0.4, this.pitch - dy * 0.003));
  }

  /** Every floor is walkable once you are inside it: look all the way around, scroll to move. */
  walkable() {
    return this.mode === "inside" && this.activeLevel !== null;
  }

  /** Walk m meters along the way you are facing (level), staying inside the current floor. */
  walkBy(m: number) {
    const dir = this.insideLook().sub(this.base.pos);
    dir.y = 0;
    if (dir.lengthSq() < 1e-6) return;
    dir.normalize().multiplyScalar(m);
    const st = this.layout.station;
    const p = this.base.pos.clone().add(this.walkTarget).add(dir);
    // three.js x = Blender x (across), three.js z = -Blender y (along the track).
    // The platform runs from its edge (x = 1.7) to the tile wall (x = 5): stay off the tracks.
    const [xMin, xMax] = this.activeLevel === "platform" ? WALK_X.platform
      : this.activeLevel === "street" ? [-(st.streetHalf - 1), st.streetHalf - 1]
      : [-(st.xHalf - 0.8), st.xHalf - 0.8];
    p.x = Math.max(xMin, Math.min(xMax, p.x));
    p.z = Math.max(-(st.yMax - 1.0), Math.min(-(st.yMin + 1.0), p.z));
    this.walkTarget.copy(p.sub(this.base.pos));
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
      this.trainAnim = { from: this.trainY, to: y, dur, t: 0, fn: ease, done: resolve };
    });
  }

  /**
   * The opening: the train comes out of the far tunnel (past the end of the station) and
   * brakes to a stop at the platform, like the original ride-through version did.
   */
  arrive(dur = 6): Promise<void> {
    this.trainY = this.layout.station.yMax + 4;
    this.placeTrain();
    if (this.reduced) dur = 0;
    return new Promise((resolve) => {
      this.trainAnim = { from: this.trainY, to: this.layout.train.stopY, dur, t: 0, fn: brake, done: resolve };
    });
  }

  /** Paint the train in a line's color with its route bullet (number or letter). */
  setTrainLine(color: string, label: string) {
    this.trainLine = label;
    const c = new THREE.Color(color);
    for (const m of this.trainPaint) {
      m.color.copy(c);
      if (m.emissive && m.emissiveIntensity > 0) m.emissive.copy(c);
    }
    if (this.bullet) {
      const g = this.bullet.ctx;
      g.clearRect(0, 0, 128, 128);
      g.fillStyle = color;
      g.beginPath(); g.arc(64, 64, 60, 0, Math.PI * 2); g.fill();
      g.fillStyle = "#fff";
      g.font = "700 76px 'Helvetica Neue', Helvetica, Arial, sans-serif";
      g.textAlign = "center"; g.textBaseline = "middle";
      g.fillText(label, 64, 68);
      this.bullet.tex.needsUpdate = true;
    }
  }

  /** Is the train standing at the platform with its front at y? */
  trainAt(y: number) {
    return !this.trainAnim && Math.abs(this.trainY - y) < 0.05;
  }

  /** The train pulls out, front first, and leaves through the near tunnel. */
  depart(dur = 1.6): Promise<void> {
    const st = this.layout.station;
    if (this.trainY > st.yMax + 2 || this.trainY < st.yMin - 60) return Promise.resolve();
    if (this.reduced) dur = 0;
    return new Promise((resolve) => {
      this.trainAnim = { from: this.trainY, to: this.trainY - 70, dur, t: 0, fn: (k) => k * k, done: () => {
        this.trainY = this.layout.train.parkY; this.placeTrain(); resolve();
      } };
    });
  }

  /** A train comes in from the far tunnel and brakes with its front at y. */
  arriveAt(y: number, dur = 3): Promise<void> {
    this.trainY = this.layout.station.yMax + 6;
    this.placeTrain();
    if (this.reduced) dur = 0;
    return new Promise((resolve) => {
      this.trainAnim = { from: this.trainY, to: y, dur, t: 0, fn: brake, done: resolve };
    });
  }

  /** Jump a moving train to where it is going. */
  finishTrain() {
    if (this.trainAnim) this.trainAnim.t = 1 - 1e-6;
  }

  get trainBusy() {
    return this.trainAnim !== null;
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
    if (this.flight) return null;
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

    // in the overview the train fades out of the way, so the project tiles behind it show;
    // it fades back in as you fly into a floor, and stays put while you are inside
    const alpha = this.mode === "overview" && !this.flight ? 0 : 1;
    if (Math.abs(this.trainAlpha - alpha) > 1e-3) {
      this.trainAlpha += Math.sign(alpha - this.trainAlpha) * Math.min(Math.abs(alpha - this.trainAlpha), dt / 0.4);
      for (const m of this.trainMats) {
        m.transparent = this.trainAlpha < 0.999;
        m.opacity = this.trainAlpha;
        m.depthWrite = this.trainAlpha > 0.999;
        m.needsUpdate = true;
      }
      if (this.train) this.train.visible = this.trainAlpha > 0.001;
    }

    if (this.trainAnim) {
      const a = this.trainAnim;
      a.t = a.dur > 0 ? Math.min(1, a.t + dt / a.dur) : 1;
      this.trainY = a.from + (a.to - a.from) * a.fn(a.t);
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
      // the section, framed to the canvas every frame (so a resize just works), easing toward
      // the pan target, with a hint of pointer parallax
      this.panTarget = this.clampPan(this.panTarget);
      this.panY += (this.panTarget - this.panY) * (this.reduced ? 1 : Math.min(1, dt * 8));
      this.base = this.overviewView(this.panY);
      const k = this.reduced ? 0 : 1;
      this.pointerSmooth.lerp(this.pointer, Math.min(1, dt * 3));
      this.pos.copy(this.base.pos).add(new THREE.Vector3(0, this.pointerSmooth.y * 0.25 * k, 0));
      this.look.copy(this.base.look);
      this.fov = this.base.fov;
    } else {
      this.slide += (this.slideTarget - this.slide) * (this.reduced ? 1 : Math.min(1, dt * 6));
      this.walkOff.lerp(this.walkTarget, this.reduced ? 1 : Math.min(1, dt * 6));
      const off = new THREE.Vector3(0, 0, -this.slide).add(this.walkOff);
      this.pos.copy(this.base.pos).add(off);
      this.look.copy(this.insideLook()).add(off);
      this.fov = this.base.fov;
    }

    if (this.exitSky) this.exitSky.visible = this.mode === "inside" && this.activeLevel === "mezzanine";
    this.camera.position.copy(this.pos);
    this.camera.lookAt(this.look);
    if (Math.abs(this.camera.fov - this.fov) > 1e-3) {
      this.camera.fov = this.fov;
      this.camera.updateProjectionMatrix();
    }
    if (this.outline.visible) this.outlineMat.opacity = 0.65 + 0.35 * Math.sin(this.time * 4);
  }
}
