"""The dollhouse station: a platform, a mezzanine and a street, cut open.

  python blender/build_dollhouse.py preview [samples]   # stills -> blender/renders/dollhouse_*.png
  python blender/build_dollhouse.py bake [res] [samples] # public/subway/station-dollhouse.glb + layout-dollhouse.json

The props are the existing builders (props/*.py, unchanged), called at the positions in
layout_dollhouse.py. The cut structure is in props/cutaway.py. The bake is level-aware
(bake_levels.py). The fourth wall is exported in its own chunks, named fourth_wall_*.
The old build_station.py still builds the old station.
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from common import *
from layout import CHUNK, CEIL_Z
from layout_dollhouse import *
from props import station_shell, signage, map_board, countdown_clock, newsstand, stairs, furniture
from props import cutaway
import build_station   # BLURB: the lightbox text, unchanged

ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(ROOT, "public", "subway")
RENDERS = os.path.join(HERE, "renders")

FOURTH = {"plat", "edge", "column", "capital", "plinth"}   # left-side station pieces from segment()
FIELDS = [("#8a3b26", "#9c4a30", "#7c321f", "#a5543a"), ("#1f3f8f", "#24489c", "#1a3678", "#2a52a8")]


def fourth(objs):
    """Name objects fw_* so the bake puts them in fourth_wall chunks the site can hide."""
    for o in objs:
        o.name = "fw_" + o.name
    return objs


def _segments():
    y = DH_START
    while y < DH_END - 1e-6:
        y1 = min(y + CHUNK, DH_END)
        yield y, y1
        y = y1


def assemble():
    reset()
    m = station_shell.materials()
    M = cutaway.materials(m)

    # platform: track, columns, and the right wall. The left side is the fourth wall.
    for y0, y1 in _segments():
        for o in station_shell.segment(m, y0, y1, walls=(1,)):
            if o.name.split(".")[0] in FOURTH and o.location.x < -0.5:
                o.name = "fw_" + o.name
    fourth(cutaway.platform_wall(M, -1, DH_START, DH_END))

    # earth, the mezzanine floor, the street slab (with the stair opening)
    cutaway.ground(M, DH_START, DH_END)
    cutaway.mezz_floor(M, DH_START, DH_END)
    cutaway.street(M, DH_START, DH_END)
    cutaway.mezz_wall(M, 1, DH_START, DH_END)
    fourth(cutaway.mezz_wall(M, -1, DH_START, DH_END))
    cutaway.mezz_lamps(M, DH_START, DH_END)

    # title sign over the platform
    group(signage.hanging_sign(["Sophie Shih's", "P O R T F O L I O"], w=3.6, h=1.0),
          (3.15, TITLE_Y, 2.85), rz=-28)

    # seven project stops on the right wall: mosaic tile, lightbox, bench or bin
    for i, (pid, name, letter, color) in enumerate(PROJECTS):
        yy = project_y(i)
        size = 0.3 if len(name) < 16 else 0.24
        group(signage.mosaic_tile(name, w=4.0, h=0.95, size=size, field=FIELDS[i % 2]),
              (WALL_X - 0.02, yy, 2.85), rz=-90, name="project_" + pid)
        group(furniture.lightbox(name, build_station.BLURB[pid], letter, color),
              (WALL_X - 0.05, yy, 1.45), rz=-90)
        if i % 2 == 0:
            group(furniture.bench(2.0), (WALL_X - 0.75, yy + 2.9, PLAT_Z))
        else:
            group(furniture.trash_can(), (WALL_X - 0.5, yy + 2.6, PLAT_Z))

    # posters on the fourth wall (left side of the platform)
    for k, yy in enumerate(range(0, int(DH_END) - 6, 6)):
        pid, name, letter, color = PROJECTS[k % len(PROJECTS)]
        title = name.replace(" ", "\n", 1) if len(name) > 12 else name
        objs = fourth(signage.poster(title, "Next stop: platform " + letter, color, shape=k % 3))
        group(objs, (-WALL_X + 0.03, yy + 1.5, 1.65), rz=90)

    # mezzanine: line map, bench, arrivals board, newsstand, the stairs up to the street
    group(map_board.build(), (WALL_X - 0.08, MAP_Y, MEZ + 1.95), rz=-90)
    group(furniture.bench(2.4), (WALL_X - 0.75, MAP_Y, MEZ), rz=0)
    rows = [(name, c) for (_, name, _, c) in PROJECTS] + [("Books & Writing", "#a0522d")]
    group(countdown_clock.build(rows), (3.25, BOARD_Y, MEZ + 1.4), rz=-12, s=0.85)
    group(newsstand.build(), (3.7, NEWSSTAND_Y, MEZ), name="newsstand")
    group(stairs.build(steps=STAIR_STEPS), (STAIRS_X, STAIRS_Y, MEZ), name="stairs")

    lights()


def lights():
    world((1, .95, .88), 0.25)
    for y0, y1 in _segments():
        yc, L = (y0 + y1) / 2, y1 - y0
        for x in (-3.5, 0, 3.5):   # platform ceiling lamps
            area((x, yc, CEIL_Z - 0.09), (0, 0, 0), 0.3, 120, (1, .9, .74), sy=L - 1.0)
        for x in (-2.5, 2.5):      # mezzanine lamps, under the street slab
            area((x, yc, MEZ_CEIL - 0.09), (0, 0, 0), 0.3, 120, (1, .9, .74), sy=L - 1.0)
    sun((R(40), 0, R(180)), 3.0, (1, .93, .8))   # daylight on the street


def _camera(st):
    cam = camera(st["pos"], st["look"])
    cam.data.sensor_fit = "VERTICAL"
    cam.data.sensor_height = 24
    cam.data.lens = 12 / math.tan(math.radians(st["fov"]) / 2)
    return cam


VIEWS = ["overview", "title", "map", "board", "newsstand", "exit", "street", "project:new-york-census"]


def preview(samples=24):
    assemble()
    render_setup(960, 600, samples)
    os.makedirs(RENDERS, exist_ok=True)
    st_all = stops()
    import build_train
    for name in VIEWS:
        st = st_all[name]
        # the site hides the fourth wall in the overview and shows it inside a level
        for o in bpy.data.objects:
            if o.name.startswith("fw_"):
                o.hide_render = (name == "overview")
        before = set(o.name for o in bpy.data.objects)
        if name.startswith("project:"):
            # the train pulls in behind the lightbox for a project
            build_train.make_train(TRAIN_STOP_Y)
        cam = _camera(st)
        out = os.path.join(RENDERS, "dollhouse_" + name.replace(":", "_") + ".png")
        render(out)
        bpy.data.objects.remove(cam)
        for o in [o for o in bpy.data.objects if o.name not in before and o.type != "CAMERA"]:
            bpy.data.objects.remove(o)
        print("rendered", out)


def bake(res=2048, samples=96):
    assemble()
    from bake_levels import bake_levels_and_export
    os.makedirs(OUT_DIR, exist_ok=True)
    bake_levels_and_export(os.path.join(OUT_DIR, "station-dollhouse.glb"), res, samples)
    with open(os.path.join(OUT_DIR, "layout-dollhouse.json"), "w") as f:
        json.dump(describe(), f, indent=1)
    print("wrote layout-dollhouse.json")


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    mode = args[0] if args else "preview"
    if mode == "bake":
        bake(int(args[1]) if len(args) > 1 else 2048, int(args[2]) if len(args) > 2 else 96)
    else:
        preview(int(args[1]) if len(args) > 1 else 24)
