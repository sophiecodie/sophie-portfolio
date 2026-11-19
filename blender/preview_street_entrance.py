"""Quick stills of the street entrance and the About chalkboard on a bare street slab,
without building or baking the whole station.

  python blender/preview_street_entrance.py [samples]   # -> blender/renders/street_entrance_*.png
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from props import street_entrance, stair_flight

RENDERS = os.path.join(HERE, "renders")
Z = 8.3                       # STREET_WALK_TOP
HOLE_Y = (32.8, 39.6)         # STAIR_HOLE (shortened station)
HALF = 1.5                    # STAIR_HALF_OPEN
BB = (3.5, 27.8)              # BILLBOARD_X, BILLBOARD_Y


def scene(night):
    reset()
    import common; common._mat_cache.clear()   # materials die with the old scene
    walk = noise_mat("street_walk", "#d9ccb4", "#e6dbc6", scale=3, rough=0.85)
    earth = noise_mat("cut_earth", "#7b6248", "#94785a", scale=5, rough=0.95, detail=8)
    y0, y1 = 14.0, 40.0
    hy0, hy1 = HOLE_Y
    for name, z0, z1, m in (("earth", 8.0, 8.2, earth), ("walk", 8.2, Z, walk)):
        cube(name, (0, (y0 + hy0) / 2, (z0 + z1) / 2), (24, hy0 - y0, z1 - z0), m)
        cube(name, (0, (hy1 + y1) / 2, (z0 + z1) / 2), (24, y1 - hy1, z1 - z0), m)
        for sx in (-1, 1):
            cube(name, (sx * (HALF + 12) / 2, (hy0 + hy1) / 2, (z0 + z1) / 2), (12 - HALF, hy1 - hy0, z1 - z0), m)
    group(stair_flight.build(width=2.6, steps=20), (0, HOLE_Y[0] + 0.2, 4.4))
    street_entrance.build_pavement(y0, y1, 12.0, HOLE_Y, HALF, 8.2, Z)
    stair_flight.trees([(7.0, 22.0), (7.5, 31.0), (6.8, 37.5)], Z)
    group(street_entrance.build_entrance(HALF, hy0 - (hy0 + hy1) / 2, hy1 - (hy0 + hy1) / 2),
          (0, (hy0 + hy1) / 2, Z), name="entrance")
    group(street_entrance.build_chalkboard(), (BB[0], BB[1], Z), name="chalkboard")
    if night:
        world((0.12, 0.15, 0.3), 0.35)
        sun((R(50), 0, R(200)), 0.15, (0.7, 0.8, 1.0))
    else:
        world((1, .95, .88), 0.25)
        sun((R(40), 0, R(180)), 3.0, (1, .93, .8))


def shot(name, pos, look, lens=35):
    if ONLY and not name.startswith(ONLY):
        return
    cam = camera(pos, look, lens=lens)
    out = os.path.join(RENDERS, "street_entrance_" + name + ".png")
    render(out)
    bpy.data.objects.remove(cam)
    print("rendered", out)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    samples = int(args[0]) if args else 32
    os.makedirs(RENDERS, exist_ok=True)
    ONLY = args[1] if len(args) > 1 else None
    for night in (False, True):
        tag = "night" if night else "day"
        scene(night)
        render_setup(1440, 810, samples)
        # straight on from the cut, like the overview's street band
        shot("section_" + tag, (-40, 30, Z + 1.9), (0, 30, Z + 1.6), lens=50)
        shot("street_" + tag, (-6.5, 22.5, Z + 2.6), (1.5, 33.0, Z + 0.6), lens=24)
        shot("entrance_" + tag, (-6.5, 30.0, Z + 3.4), (0, 36.2, Z + 0.4), lens=32)
        shot("chalkboard_" + tag, (0.0, 26.4, Z + 1.3), (BB[0], 27.8, Z + 0.95), lens=35)
