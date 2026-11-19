# Street floor background

Inside the street level, `ring-skyline.png`, `ring-rows.png` and `ring-trees.png` wrap around
you at 300 m, 110 m and 52 m (see `components/street/streetRings.ts`). They are painted by
`scripts/paint_night_rings.py`, also made for this site. The sky and the pavement are drawn by
shaders.

`night.jpg` and `night-depth.png` are painted in code by `scripts/paint_night.py` for this site
(sky, far skyline, brownstones with water towers, park trees, lamps). No outside images are used,
so there is nothing to credit. The depth map is exact because every layer is drawn at a known
depth (white = near, black = far).

    python scripts/paint_night.py            # writes public/street/night.jpg + night-depth.png
    python scripts/paint_night.py --seed 3   # a different arrangement of buildings and trees

To use a photo instead, make its depth map with `scripts/street_depth.py` (Depth Anything V2
Small, Apache-2.0), add it to `STREET_MOODS` in `components/street/streetBackdrop.ts` with its
credit, and the credit line appears on the site automatically.
