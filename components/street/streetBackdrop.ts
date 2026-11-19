// The quiet NYC night seen behind the top (street) floor.
//
// Same trick Felix Rieseberg used for the view outside his room: a picture plus a depth map,
// and a shader that shifts each pixel by its depth as the camera and the pointer move, so the
// view has real parallax for the price of two textures and one quad. The night scene is painted
// in code (scripts/paint_night.py), so its depth map is exact. scripts/street_depth.py makes a
// depth map for a photo instead (Depth Anything V2), if a photo mood is ever added.
//
// The picture is treated as a far-away view: which part of it you see depends on the direction
// you look, and it slides only a little when the camera pans along the track. That keeps the
// skyline and trees in the strip above the street floor wherever you are along the station.
//
// More than one mood can be listed in STREET_MOODS; StreetMoodToggle then shows a switch and the
// backdrop cross-fades between them. With one mood the switch hides itself.

import * as THREE from "three";

export type StreetMood = "night";

type MoodSpec = {
  photo: string;
  depth: string;
  /** picture height / width */
  aspect: number;
  /** picture v (0 = bottom, 1 = top) that sits on the street-floor line in the overview */
  anchorV: number;
  /** horizontal picture u at the middle of the track */
  centerU: number;
  /** 0..1 falling rain drawn on top */
  rain: number;
  /** color grade: multiply, then lift (linear) */
  tint: [number, number, number];
  lift: [number, number, number];
  /** attribution shown under the switch, for Creative Commons photos */
  credit?: { title: string; author: string; license: string; licenseUrl: string; source: string };
};

export const STREET_MOODS: Record<StreetMood, MoodSpec> = {
  night: {
    photo: "/street/night.jpg", depth: "/street/night-depth.png", aspect: 1280 / 6144,
    anchorV: 0.12, centerU: 0.5, rain: 0, tint: [1, 1, 1], lift: [0, 0, 0],
  },
};

export const STREET_MOOD_LABELS: Record<StreetMood, string> = { night: "Night" };
const MOODS = Object.keys(STREET_MOODS) as StreetMood[];
const DEFAULT_MOOD: StreetMood = "night";

// ------------------------------------------------------------------ mood store
const KEY = "street-mood";
const listeners = new Set<(m: StreetMood) => void>();
let current: StreetMood | null = null;

export function getStreetMood(): StreetMood {
  if (current) return current;
  let saved: string | null = null;
  try { saved = window.localStorage.getItem(KEY); } catch { /* private mode */ }
  current = (MOODS as string[]).includes(saved ?? "") ? (saved as StreetMood) : DEFAULT_MOOD;
  return current;
}

export function setStreetMood(m: StreetMood) {
  current = m;
  try { window.localStorage.setItem(KEY, m); } catch { /* private mode */ }
  listeners.forEach((f) => f(m));
}

export function onStreetMood(f: (m: StreetMood) => void) {
  listeners.add(f);
  return () => { listeners.delete(f); };
}

// ------------------------------------------------------------------ shader
const vert = /* glsl */ `
varying vec3 vWorld;
void main() {
  vec4 w = modelMatrix * vec4(position, 1.0);
  vWorld = w.xyz;
  gl_Position = projectionMatrix * viewMatrix * w;
}`;

const frag = /* glsl */ `
uniform sampler2D uPhotoA, uDepthA, uPhotoB, uDepthB;
uniform vec4 uGeomA, uGeomB;     // aspect, anchorV, centerU, rain
uniform vec3 uTintA, uTintB, uLiftA, uLiftB;
uniform float uMix;              // 0 = A, 1 = B
uniform float uTime;
uniform vec2 uPointer;
uniform vec3 uCam0;              // reference camera position (three.js coordinates)
uniform float uAngW;             // angular width of the photo, radians
uniform float uPitch0;           // pitch of the street-floor line seen from the overview
uniform float uPan;              // photo widths per meter of camera travel along the track
uniform float uDepthPx;          // strength of the depth parallax
uniform float uOpacity;          // fades out while the immersive night (streetRings) is on
varying vec3 vWorld;

float hash(float n) { return fract(sin(n * 127.1) * 43758.5453); }

// look direction -> photo uv, then push by depth (two refinement steps, no smearing at edges)
vec3 sampleMood(sampler2D photo, sampler2D depthTex, vec4 g, vec3 dir) {
  float yaw = atan(dir.z, dir.x);
  float pitch = atan(dir.y, length(dir.xz));
  float angH = uAngW * g.x;
  vec2 uv = vec2(g.z + yaw / uAngW, g.y + (pitch - uPitch0) / angH);
  vec3 d = cameraPosition - uCam0;
  uv.x += d.z * uPan;
  // camera travel + pointer sway + a slow breath, all scaled by nearness
  vec2 push = vec2(d.z * uDepthPx, d.y * uDepthPx * 0.6 / g.x)
            + uPointer * vec2(0.010, 0.006)
            + vec2(sin(uTime * 0.21), cos(uTime * 0.17)) * 0.0025;
  vec2 p = uv;
  for (int i = 0; i < 2; i++) {
    float z = pow(texture2D(depthTex, clamp(p, 0.0, 1.0)).r, 0.75);
    p = uv + push * (z - 0.25);
  }
  // mirror past the sides, hold the top row (sky) above the photo
  p.x = 1.0 - abs(mod(p.x, 2.0) - 1.0);
  float above = smoothstep(1.0, 1.25, p.y);
  vec3 c = texture2D(photo, vec2(p.x, clamp(p.y, 0.002, 0.998))).rgb;
  c = mix(c, c * 0.6, above);
  // Below the painting is the ground. Tall (phone) frames look further down than the paint
  // goes, and holding the last row would smear it into vertical streaks, so draw the street
  // instead: far sidewalk, curb, asphalt with a faded centre line, near curb, then flagstones.
  float b = -p.y;                                   // photo heights below the painting
  if (b > -0.002) {
    float z = 1.0 / (b + 0.02);                      // ground distance, large near the painting
    vec3 g = vec3(0.0095, 0.0095, 0.011);            // far sidewalk
    float road = smoothstep(0.028, 0.032, b) * (1.0 - smoothstep(0.16, 0.165, b));
    vec3 asphalt = vec3(0.0065, 0.0068, 0.008) * (0.9 + 0.2 * hash(floor(p.x * 900.0) + floor(z * 8.0) * 13.0));
    float dash = step(0.5, fract(p.x * 40.0)) * smoothstep(0.006, 0.0, abs(b - 0.08));
    asphalt += vec3(0.03, 0.026, 0.016) * dash * 0.35;
    g = mix(g, asphalt, road);
    float curb = smoothstep(0.005, 0.0, abs(b - 0.03)) + smoothstep(0.006, 0.0, abs(b - 0.163));
    g = mix(g, vec3(0.022, 0.022, 0.024), clamp(curb, 0.0, 1.0));
    // flagstones on the near sidewalk: joints across, closer together toward the painting
    float near = smoothstep(0.165, 0.175, b);
    float zj = fract(z * 1.6);
    float joint = smoothstep(0.06, 0.0, min(zj, 1.0 - zj));
    vec3 flag = vec3(0.012, 0.012, 0.0135) * (0.85 + 0.3 * hash(floor(z * 1.6) * 7.0 + floor(p.x * 60.0)));
    g = mix(g, mix(flag, flag * 0.45, joint), near);
    // faint moonlight sheen that fades toward the viewer
    g += vec3(0.002, 0.0025, 0.004) * exp(-b * 5.0);
    c = mix(c, g, smoothstep(-0.002, 0.002, b));
  }
  // a low stone park wall hides the bottom of the painting (tree trunks, building bases)
  float w = smoothstep(-0.062, -0.058, b) * (1.0 - smoothstep(-0.002, 0.002, b));
  if (w > 0.0) {
    float wy = (b + 0.06) / 0.06;                    // 0 at the cap, 1 at the foot
    float course = floor(wy * 3.0);
    float sx = p.x * 170.0 + course * 0.5;
    float stone = 0.8 + 0.4 * hash(floor(sx) + course * 31.0);
    float mortar = max(smoothstep(0.06, 0.0, min(fract(sx), 1.0 - fract(sx))),
                       smoothstep(0.08, 0.0, min(fract(wy * 3.0), 1.0 - fract(wy * 3.0))));
    vec3 wall = vec3(0.016, 0.015, 0.016) * stone * (1.0 - 0.5 * mortar) * (1.0 - 0.35 * wy);
    wall = mix(wall, vec3(0.03, 0.029, 0.03), smoothstep(0.08, 0.0, wy));   // lighter capstone
    c = mix(c, wall, w);
  }
  return c;
}

float rain(vec2 q, float t) {
  float r = 0.0;
  for (int L = 0; L < 3; L++) {
    float fl = float(L);
    float cols = 70.0 + fl * 55.0;
    vec2 s = vec2(q.x * cols + q.y * 6.0, q.y * (3.0 + fl) + t * (2.2 + fl * 0.7));
    float id = floor(s.x);
    float h = hash(id + fl * 31.0);
    float y = fract(s.y + h * 7.0);
    float x = abs(fract(s.x) - 0.5);
    float drop = smoothstep(0.09, 0.0, x) * smoothstep(0.0, 0.08, y) * smoothstep(0.32, 0.08, y);
    r += drop * step(0.55, h) * (0.55 - fl * 0.12);
  }
  return r;
}

void main() {
  vec3 dir = normalize(vWorld - cameraPosition);
  vec3 a = sampleMood(uPhotoA, uDepthA, uGeomA, dir) * uTintA + uLiftA;
  vec3 b = uMix > 0.0 ? sampleMood(uPhotoB, uDepthB, uGeomB, dir) * uTintB + uLiftB : a;
  vec3 c = mix(a, b, uMix);
  float wet = mix(uGeomA.w, uGeomB.w, uMix);
  if (wet > 0.0) {
    vec2 q = vec2(atan(dir.z, dir.x), atan(dir.y, length(dir.xz))) / uAngW;
    c += vec3(0.55, 0.6, 0.68) * rain(q, uTime) * wet * 0.35;
  }
  gl_FragColor = vec4(c, uOpacity);
  #include <colorspace_fragment>
}`;

// ------------------------------------------------------------------ material
export type StreetBackdropOptions = {
  /** Reference camera position in three.js coordinates (the overview at mid-track). */
  cam0: THREE.Vector3;
  /** Pitch, in radians, of the street-floor line seen from the overview camera. */
  pitch0?: number;
  /** Angular width of the photo in radians. Smaller = bigger street. */
  angularWidth?: number;
  /** Where the files live (prefix for /street/...). */
  base?: string;
  reducedMotion?: boolean;
};

const loader = new THREE.TextureLoader();
const cache = new Map<string, Promise<THREE.Texture>>();
function tex(url: string, color: boolean) {
  let p = cache.get(url);
  if (!p) {
    p = loader.loadAsync(url).then((t) => {
      t.colorSpace = color ? THREE.SRGBColorSpace : THREE.NoColorSpace;
      t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
      t.minFilter = THREE.LinearMipmapLinearFilter;
      t.anisotropy = 4;
      return t;
    });
    cache.set(url, p);
  }
  return p;
}

/**
 * Build the street material. It starts on the saved mood and follows setStreetMood() with a
 * one-second cross-fade. Pass the result to DollhouseScene.setStreetBackdrop().
 */
export function createStreetBackdrop(opts: StreetBackdropOptions) {
  const base = opts.base ?? "";
  const blank = new THREE.DataTexture(new Uint8Array([90, 80, 70, 255]), 1, 1);
  blank.needsUpdate = true;
  const flat = new THREE.DataTexture(new Uint8Array([0, 0, 0, 255]), 1, 1);
  flat.needsUpdate = true;
  const geom = (m: MoodSpec) => new THREE.Vector4(m.aspect, m.anchorV, m.centerU, m.rain);

  const u = {
    uPhotoA: { value: blank as THREE.Texture }, uDepthA: { value: flat as THREE.Texture },
    uPhotoB: { value: blank as THREE.Texture }, uDepthB: { value: flat as THREE.Texture },
    uGeomA: { value: geom(STREET_MOODS[DEFAULT_MOOD]) }, uGeomB: { value: geom(STREET_MOODS[DEFAULT_MOOD]) },
    uTintA: { value: new THREE.Vector3(1, 1, 1) }, uTintB: { value: new THREE.Vector3(1, 1, 1) },
    uLiftA: { value: new THREE.Vector3() }, uLiftB: { value: new THREE.Vector3() },
    uMix: { value: 0 },
    uTime: { value: 0 },
    uPointer: { value: new THREE.Vector2() },
    uCam0: { value: opts.cam0.clone() },
    uAngW: { value: opts.angularWidth ?? 0.45 },
    uPitch0: { value: opts.pitch0 ?? 0.025 },
    uPan: { value: 0.0016 },
    uDepthPx: { value: 0.0012 },
    uOpacity: { value: 1 },
  };
  const material = new THREE.ShaderMaterial({ uniforms: u, vertexShader: vert, fragmentShader: frag, depthWrite: false, transparent: true });
  material.name = "street_backdrop_photo";

  const setSlot = (slot: "A" | "B", m: MoodSpec, photo: THREE.Texture, depth: THREE.Texture) => {
    u[`uPhoto${slot}`].value = photo;
    u[`uDepth${slot}`].value = depth;
    u[`uGeom${slot}`].value = geom(m);
    u[`uTint${slot}`].value.set(...m.tint);
    u[`uLift${slot}`].value.set(...m.lift);
  };
  const load = (mood: StreetMood) => {
    const m = STREET_MOODS[mood];
    return Promise.all([tex(base + m.photo, true), tex(base + m.depth, false)]).then(([p, d]) => ({ m, p, d }));
  };

  let shown: StreetMood | null = null;
  let fade = 0; // 0..1 while cross-fading A -> B
  let fading = false;
  let want = getStreetMood();
  let token = 0;
  const show = (mood: StreetMood) => {
    want = mood;
    const my = ++token;
    void load(mood).then(({ m, p, d }) => {
      if (my !== token || disposed) return;
      if (shown === null || opts.reducedMotion) {
        setSlot("A", m, p, d);
        u.uMix.value = 0;
        fading = false;
      } else {
        setSlot("B", m, p, d);
        fade = 0;
        fading = true;
      }
      shown = mood;
      // warm the other mood in the background so switching is instant
      for (const other of MOODS) if (other !== mood) setTimeout(() => void load(other), 1500);
    }).catch(() => { /* keep the placeholder */ });
  };
  show(want);
  const off = onStreetMood((m) => { if (m !== want) show(m); });

  // pointer sway, independent of the scene so it works in every mode
  const target = new THREE.Vector2();
  const onMove = (e: PointerEvent) => target.set((e.clientX / window.innerWidth) * 2 - 1, -((e.clientY / window.innerHeight) * 2 - 1));
  window.addEventListener("pointermove", onMove, { passive: true });

  let last = performance.now();
  material.onBeforeRender = () => {
    const now = performance.now();
    const dt = Math.min((now - last) / 1000, 0.05);
    last = now;
    if (!opts.reducedMotion) {
      u.uTime.value += dt;
      u.uPointer.value.lerp(target, Math.min(1, dt * 2.5));
    }
    if (fading) {
      fade = Math.min(1, fade + dt / 1.1);
      u.uMix.value = fade * fade * (3 - 2 * fade);
      if (fade >= 1) {
        // B becomes A
        u.uPhotoA.value = u.uPhotoB.value; u.uDepthA.value = u.uDepthB.value;
        u.uGeomA.value = u.uGeomB.value.clone();
        u.uTintA.value.copy(u.uTintB.value); u.uLiftA.value.copy(u.uLiftB.value);
        u.uMix.value = 0;
        fading = false;
      }
    }
  };

  let disposed = false;
  material.addEventListener("dispose", () => {
    disposed = true;
    off();
    window.removeEventListener("pointermove", onMove);
  });
  return material;
}

/**
 * Hook the street into a DollhouseScene: one call after the scene is created.
 *
 * - From the overview, the street floor shows the flat painted night (this file).
 * - When the street level becomes the active level (you clicked into it), the immersive night
 *   from streetRings.ts fades in around you and the flat backdrop fades out; leaving the level
 *   reverses it. This listens by wrapping scene.setActiveLevel, so scene.ts needs no changes.
 *
 * `section` is the overview framing (SECTION in scene.ts); it is only used to line the flat
 * picture up with the street floor, so it is fine if it drifts a little.
 */
export function attachStreetBackdrop(
  scene: {
    setStreetBackdrop(m: THREE.Material): void;
    setActiveLevel(level: string | null): void;
    scene: THREE.Scene;
    reduced?: boolean;
  },
  layout: { station: { yMin: number; yMax: number }; levels: Record<string, { floor: number }> },
  section = { z0: -1.1, z1: 11.4, plane: -6, tilt: 0.03, fov: 14 },
) {
  const h = section.z1 - section.z0;
  const dist = h / 2 / Math.tan(THREE.MathUtils.degToRad(section.fov / 2));
  const camX = section.plane - dist * Math.cos(section.tilt);
  const camZ = (section.z0 + section.z1) / 2 + dist * Math.sin(section.tilt);
  const midY = (layout.station.yMin + layout.station.yMax) / 2;
  const floor = layout.levels.street?.floor ?? 8.3;
  // three.js coordinates are (blender x, blender z, -blender y)
  const material = createStreetBackdrop({
    cam0: new THREE.Vector3(camX, camZ, -midY),
    pitch0: Math.atan2(floor - camZ, section.plane - camX),
    reducedMotion: scene.reduced,
  });
  scene.setStreetBackdrop(material);

  // the immersive night around the street level
  void import("./streetRings").then(({ createStreetRings }) => {
    const rings = createStreetRings(new THREE.Vector3(0, floor, -midY));
    scene.scene.add(rings.group);
    const flat = material.uniforms.uOpacity;
    material.addEventListener("dispose", () => { rings.dispose(); scene.scene.remove(rings.group); });
    // keep the flat backdrop the inverse of the rings
    rings.group.children[0].onBeforeRender = () => { flat.value = 1 - rings.amount(); };
    material.onBeforeRender = ((prev) => function (this: THREE.Material, ...args: Parameters<THREE.Material["onBeforeRender"]>) {
      flat.value = 1 - rings.amount();
      prev.apply(this, args);
    })(material.onBeforeRender);
    const orig = scene.setActiveLevel.bind(scene);
    scene.setActiveLevel = (level: string | null) => {
      orig(level);
      rings.setImmersed(level === "street", scene.reduced);
    };
    // in case the street was entered before this finished loading (a #about deep link)
    if ((scene as unknown as { activeLevel?: string | null }).activeLevel === "street") rings.setImmersed(true, true);
  });
  return material;
}
