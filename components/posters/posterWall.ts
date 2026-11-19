// The platform posters. Each project's lightbox on the platform wall gets a framed ad poster
// hung over it, like the ads on real NYC subway platforms, each project a different kind of ad.
// The posters are images drawn by scripts/posters/posters.html (render_posters.js).
// The baked station is untouched: the posters are extra boxes added on top.
import * as THREE from "three";
import { b2t, type DollhouseScene, type Layout } from "../subway/scene";

const PROJECT_IDS = ["college-app-atlas", "purchase-intent", "new-york-census", "folio", "agent00hl7", "dream-team", "neurobiome"];
// The lightbox (blender/props/furniture.py) is 1.6 x 0.9 m in a 1.7 x 1.0 m frame, centered
// 1.45 m up, standing 7 cm off the tile wall at x = 5. The poster box covers all of it: its
// face is 10 cm off the wall, a hair in front of the lightbox's raised letters.
const WALL_X = 5.0, CENTER_Z = 1.45, OFF_WALL = 0.1;
const W = 1.74, H = 1.04, DEPTH = 0.12;

/** Hang a poster over each project's lightbox. */
export function attachPosters(scene: DollhouseScene, layout: Layout, base = "/subway/posters") {
  const loader = new THREE.TextureLoader();
  const maxAniso = scene.renderer.capabilities.getMaxAnisotropy();

  // a shallow box from the poster face back to the wall, so the old lightbox frame is hidden
  // from the side too; its edges are the dark aluminum of the poster frame
  const geo = new THREE.BoxGeometry(W, H, DEPTH);
  const edge = new THREE.MeshBasicMaterial({ color: 0x3a3936 });
  PROJECT_IDS.forEach((id, i) => {
    const map = loader.load(`${base}/${id}.jpg`);
    map.colorSpace = THREE.SRGBColorSpace;
    map.anisotropy = maxAniso;
    // a touch under full white, so a poster sits in the warm baked light like a backlit ad
    const face = new THREE.MeshBasicMaterial({ color: 0xf7f0e4, map });
    // box faces: +x, -x, +y, -y, +z (the poster), -z
    const m = new THREE.Mesh(geo, [edge, edge, edge, edge, face, edge]);
    m.name = "poster_" + id;
    m.position.copy(b2t([WALL_X - OFF_WALL + DEPTH / 2, layout.projectY0 + i * layout.projectStep, CENTER_Z]));
    m.rotation.y = -Math.PI / 2; // the poster (+z) faces the platform (-x)
    scene.scene.add(m);
  });
}
