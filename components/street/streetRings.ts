// The night around you when you step onto the street floor.
//
// From the overview the street floor shows a flat painted backdrop (streetBackdrop.ts). Once you
// click into the street level, this takes over: a sky dome with the moon and stars, three
// see-through painted rings at real distances (park trees and lamps at 52 m, brownstones at
// 110 m, the far skyline at 300 m) and a dark ground out to the horizon. Turning or moving the
// camera makes the near trees slide past the brownstones while the skyline barely moves, so the
// street has real depth for the cost of three textures. The rings are painted by
// scripts/paint_night_rings.py; keep RINGS in sync with that script.

import * as THREE from "three";

const RINGS = [
  { name: "skyline", r: 300, z0: -6, z1: 230, order: -9 },
  { name: "rows", r: 110, z0: -2, z1: 34, order: -8 },
  { name: "trees", r: 52, z0: -1, z1: 15, order: -7 },
] as const;

const SKY_R = 360;
const GROUND_R = 340;

const skyVert = /* glsl */ `
varying vec3 vDir;
void main() {
  vDir = normalize(position);
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}`;
const skyFrag = /* glsl */ `
uniform float uOpacity;
uniform vec3 uMoon;
varying vec3 vDir;
float hash(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }
void main() {
  vec3 d = normalize(vDir);
  float h = clamp(d.y, -0.2, 1.0);
  vec3 top = vec3(0.003, 0.005, 0.016), mid = vec3(0.01, 0.015, 0.04), low = vec3(0.045, 0.038, 0.065);
  vec3 c = h < 0.12 ? mix(low, mid, smoothstep(-0.02, 0.12, h)) : mix(mid, top, smoothstep(0.12, 0.7, h));
  // stars: sparse, faint, only well above the roofs
  vec3 cell = floor(d * 320.0);
  float st = hash(cell);
  float star = step(0.9965, st) * smoothstep(0.08, 0.3, h) * (0.35 + 0.65 * hash(cell + 3.1));
  c += vec3(0.8, 0.85, 1.0) * star * 0.5;
  // the moon and its halo
  float m = dot(d, normalize(uMoon));
  c += vec3(0.4, 0.45, 0.65) * pow(max(m, 0.0), 900.0) * 0.12;
  c = mix(c, vec3(0.86, 0.84, 0.76), smoothstep(0.99984, 0.99989, m));
  gl_FragColor = vec4(c, uOpacity);
  #include <colorspace_fragment>
}`;

// Pavement out to the park railing: square concrete flags with dark joints, a curb, and an
// asphalt street on each side of the station; it fades into night haze toward the horizon.
// Coordinates: vXY = (blender x, blender y - middle of the track), in meters.
const groundFrag = /* glsl */ `
uniform float uOpacity;
uniform float uMidY;             // blender y of the ring center, so the flag grid lines up with the baked sidewalk
varying vec2 vXY;
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
  vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}
void main() {
  vec2 p = vXY;
  float r = length(p);
  float ax = abs(p.x);
  // flagstones, 1.5 m squares on the same world grid as the baked sidewalk (from x = 0, y = 0)
  vec2 q = vec2(p.x, p.y + uMidY) / 1.5;
  vec2 g = abs(fract(q) - 0.5);
  float w = fwidth(q.x) * 1.2 + 0.012;
  float joint = 1.0 - smoothstep(0.5 - w - 0.02, 0.5 - 0.02, max(g.x, g.y));
  float tile = 0.85 + 0.3 * hash(floor(q));
  float grit = 0.8 + 0.4 * noise(p * 3.0);
  // near the station the flags are as bright as the baked sidewalk (lit by the entrance lamps),
  // then they dim with distance into the night
  float lit = mix(4.2, 1.0, smoothstep(10.0, 40.0, r));
  vec3 flag = vec3(0.034, 0.034, 0.038) * tile * grit * lit;
  vec3 pave = mix(vec3(0.012), flag, joint);
  // asphalt street 17..27 m out on each side, with a faded lane line and a curb
  float road = step(17.0, ax) * step(ax, 27.0);
  vec3 asphalt = vec3(0.014, 0.015, 0.018) * (0.85 + 0.3 * noise(p * 1.7));
  float dash = step(0.5, fract(p.y / 6.0)) * (1.0 - smoothstep(0.06, 0.12, abs(ax - 22.0)));
  asphalt += vec3(0.07, 0.065, 0.05) * dash * 0.5;
  vec3 c = mix(pave, asphalt, road);
  float curb = (1.0 - smoothstep(0.0, 0.18, abs(ax - 17.0))) + (1.0 - smoothstep(0.0, 0.18, abs(ax - 27.0)));
  c = mix(c, vec3(0.05, 0.05, 0.055), clamp(curb, 0.0, 1.0) * 0.8);
  // a little cool moonlight sheen and warm lamplight near the park
  c += vec3(0.0, 0.002, 0.006) * noise(p * 0.15);
  c += vec3(0.02, 0.013, 0.005) * smoothstep(30.0, 50.0, r) * (1.0 - smoothstep(52.0, 60.0, r));
  // fade to haze toward the horizon
  c = mix(c, vec3(0.03, 0.028, 0.045), smoothstep(60.0, 320.0, r));
  gl_FragColor = vec4(c, uOpacity);
  #include <colorspace_fragment>
}`;
const groundVert = /* glsl */ `
varying vec2 vXY;
void main() {
  vXY = position.xy;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}`;

export type StreetRings = {
  group: THREE.Group;
  /** fade the whole night in (true) or out (false) */
  setImmersed(on: boolean, instant?: boolean): void;
  /** 0..1, how far the fade has got; used to fade the flat backdrop the other way */
  amount(): number;
  dispose(): void;
};

/**
 * Build the street night. `center` is the middle of the street floor in three.js coordinates
 * (y = the street floor height). Add `group` to the scene.
 */
export function createStreetRings(center: THREE.Vector3, base = ""): StreetRings {
  const group = new THREE.Group();
  group.name = "street_night";
  group.position.copy(center);
  group.visible = false;
  const mats: { m: THREE.Material; set(o: number): void }[] = [];

  // sky
  const skyMat = new THREE.ShaderMaterial({
    vertexShader: skyVert, fragmentShader: skyFrag, side: THREE.BackSide, transparent: true, depthWrite: false,
    // the moon sits ahead of you on the street (toward +x), a little to the left, low in the sky
    uniforms: { uOpacity: { value: 0 }, uMoon: { value: new THREE.Vector3(1, 0.36, 0.3) } },
  });
  const sky = new THREE.Mesh(new THREE.SphereGeometry(SKY_R, 48, 24), skyMat);
  sky.renderOrder = -10;
  group.add(sky);
  mats.push({ m: skyMat, set: (o) => { skyMat.uniforms.uOpacity.value = o; } });

  // painted rings
  const loader = new THREE.TextureLoader();
  for (const R of RINGS) {
    const tex = loader.load(`${base}/street/ring-${R.name}.png`);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.wrapS = THREE.RepeatWrapping;
    tex.repeat.x = -1; // seen from inside, so flip it back the right way round
    tex.anisotropy = 8;
    const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, side: THREE.BackSide, opacity: 0 });
    const h = R.z1 - R.z0;
    const mesh = new THREE.Mesh(new THREE.CylinderGeometry(R.r, R.r, h, 160, 1, true), mat);
    mesh.position.y = R.z0 + h / 2;
    mesh.renderOrder = R.order;
    mesh.name = "street_ring_" + R.name;
    group.add(mesh);
    mats.push({ m: mat, set: (o) => { mat.opacity = o; } });
  }

  // ground out to the horizon, just under the sidewalk so it never fights with the station
  const groundMat = new THREE.ShaderMaterial({
    vertexShader: groundVert, fragmentShader: groundFrag, transparent: true,
    uniforms: { uOpacity: { value: 0 }, uMidY: { value: -center.z } },
  });
  const ground = new THREE.Mesh(new THREE.CircleGeometry(GROUND_R, 96), groundMat);
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.06;
  ground.renderOrder = -6;
  group.add(ground);
  mats.push({ m: groundMat, set: (o) => { groundMat.uniforms.uOpacity.value = o; } });

  let target = 0, value = 0, last = performance.now();
  const apply = () => {
    const e = value * value * (3 - 2 * value);
    for (const x of mats) x.set(e);
    group.visible = value > 0.001;
  };
  // drive the fade from the sky's render callback (it only runs while the group is visible),
  // plus a small rAF while fading in from hidden
  let raf = 0;
  const tick = () => {
    const now = performance.now();
    const dt = Math.min((now - last) / 1000, 0.05);
    last = now;
    if (value !== target) {
      value = target > value ? Math.min(target, value + dt / 0.9) : Math.max(target, value - dt / 0.6);
      apply();
      raf = requestAnimationFrame(tick);
    } else raf = 0;
  };
  return {
    group,
    setImmersed(on, instant = false) {
      target = on ? 1 : 0;
      if (instant) { value = target; apply(); return; }
      last = performance.now();
      if (!raf) raf = requestAnimationFrame(tick);
    },
    amount: () => value,
    dispose() {
      cancelAnimationFrame(raf);
      group.traverse((o) => {
        const m = o as THREE.Mesh;
        if (m.isMesh) {
          m.geometry.dispose();
          const mat = m.material as THREE.MeshBasicMaterial;
          mat.map?.dispose();
          mat.dispose();
        }
      });
    },
  };
}
