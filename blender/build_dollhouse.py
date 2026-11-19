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
from props import cutaway, stair_flight, stair_exit
from props import realism
from layout import COL_X, COL_STEP, PLAT_INNER, PLAT_Z as SHELL_PLAT_Z
import build_station   # BLURB: the lightbox text, unchanged

ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(ROOT, "public", "subway")
RENDERS = os.path.join(HERE, "renders")

FOURTH = {"plat", "edge", "column", "capital", "plinth", "coping", "rubbing"}   # left-side station pieces from segment()
# the site's route bullets (components/subway/Experience.tsx BULLET): number by project, color by line
RED, GREEN, PURPLE = "#ee352e", "#00933c", "#b933ad"
BULLET = {"college-app-atlas": ("1", RED), "purchase-intent": ("2", RED), "new-york-census": ("3", RED),
          "agent00hl7": ("4", GREEN), "dream-team": ("5", GREEN), "neurobiome": ("6", GREEN), "folio": ("7", PURPLE)}
FIELDS = [("#8a3b26", "#9c4a30", "#7c321f", "#a5543a"), ("#1f3f8f", "#24489c", "#1a3678", "#2a52a8")]


def _center(o):
    """Middle of an object's bounding box, in its parent's space (meshes keep their offset in the vertices)."""
    from mathutils import Vector
    return sum((o.matrix_basis @ Vector(c) for c in o.bound_box), Vector()) / 8


def _concrete_steps():
    """Stairs get concrete treads like the platform (their yellow nosings stay)."""
    conc = None
    for o in bpy.data.objects:
        if o.type == "MESH":
            for i, mt in enumerate(o.data.materials):
                if mt and mt.name.startswith("stair_terrazzo"):
                    conc = conc or realism.concrete("stair_concrete", "#a9a49a", "#bdb8ad", joint=50.0, wear=False)
                    o.data.materials[i] = conc


def _flat(objs, name, loc, rz):
    """group() and return the children, so they can be named into the fourth wall."""
    group(objs, loc, rz=rz, name=name)
    return objs


def fourth(objs):
    """Name objects fw_* so the bake puts them in fourth_wall chunks the site can hide."""
    for o in objs:
        o.name = "fw_" + o.name
    return objs


def realistic_segment(m, y0, y1, gs=0):
    """Riveted columns with name plates, girders and conduit, fluorescent strips, the
    edge coping and the third rail (props/realism.py). gs: the side whose ceiling is open
    over the platform stairs (-1 left, 1 right, 0 none)."""
    yy = math.ceil(y0 / COL_STEP) * COL_STEP
    while yy < y1:
        for sx in (-1, 1):
            if sx == gs:
                continue
            objs = realism.ibeam_column(m, CEIL_Z - SHELL_PLAT_Z)
            # the enamel name plates bake with the signs, so their letters stay sharp
            plates = [o for o in objs if o.name.startswith(("col_plate", "T_"))]
            group([o for o in objs if o not in plates], (sx * COL_X, yy, SHELL_PLAT_Z), name="column_g")
            group(plates, (sx * COL_X, yy, SHELL_PLAT_Z), name="sign_colplate")
            if sx < 0:
                fourth(objs)
        yy += COL_STEP
    realism.ceiling_steel(m, y0, y1, CEIL_Z, WALL_X, COL_X, COL_STEP, PLAT_INNER, skip_side=gs)
    for x in (-4.0, -2.0, 2.0, 4.0):
        if gs and (x > 0) == (gs > 0):
            continue
        realism.fixture(m, x, y0, y1, CEIL_Z)
    for sx in (-1, 1):
        objs = realism.coping(m, sx, y0, y1, PLAT_INNER, SHELL_PLAT_Z)
        if sx < 0 and not (gs < 0):
            fourth(objs)
    realism.third_rail(m, 1, y0, y1, x=1.5)


def _segments():
    y = DH_START
    while y < DH_END - 1e-6:
        y1 = min(y + CHUNK, DH_END)
        yield y, y1
        y = y1


def assemble():
    reset()
    # realistic materials (props/realism.py) under the same keys, so every builder picks them up
    m = realism.materials(station_shell.materials())
    M = cutaway.materials(m)

    # platform: track, columns, and the right wall. The left side is the fourth wall.
    for y0, y1 in _segments():
        # the ceiling over the stairs platform is left open where the stairs go up
        gap = y0 < PSTAIR_Y
        for o in station_shell.segment(m, y0, y1, walls=(1,), stair_gap=(-1 if PSTAIR_X < 0 else 1) if gap else False):
            base = o.name.split(".")[0]
            # under stairs on the left platform, its slab stays put (not part of the fourth wall)
            if gap and PSTAIR_X < 0 and base in ("plat", "edge"):
                continue
            # the simple columns and lamp strips make way for the realistic ones below
            if base in ("column", "capital", "plinth", "lampbox", "lamp"):
                bpy.data.objects.remove(o, do_unlink=True)
                continue
            if base in FOURTH and o.location.x < -0.5:
                o.name = "fw_" + o.name
        realistic_segment(m, y0, y1, gs=(-1 if PSTAIR_X < 0 else 1) if gap else 0)
    # long walls are built in 10 m pieces so their UV islands pack well (sharp tile in the bake)
    for y0, y1 in _segments():
        fourth(cutaway.platform_wall(M, -1, y0, y1))

    # platform end walls with an arched tunnel mouth over the track (Sophie, 2026-11-17).
    # Part of the fourth wall, so the overview still looks into the cut.
    for yy, sg in ((DH_START, -1), (DH_END, 1)):
        fourth(realism.end_portal(m, yy, sg, WALL_X, CEIL_Z, SHELL_PLAT_Z))

    # earth, the mezzanine floor, the street slab (with the stair opening)
    cutaway.ground(M, DH_START, DH_END)
    cutaway.mezz_floor_open(M, DH_START, DH_END, PSTAIR_HOLE)
    cutaway.street(M, DH_START, DH_END)
    for y0, y1 in _segments():
        cutaway.mezz_wall(M, 1, y0, y1)
        fourth(cutaway.mezz_wall(M, -1, y0, y1))
    # the mezzanine ceiling is open over the street stairs, so they rise into the night
    for o in cutaway.mezz_lamps(M, DH_START, DH_END):
        # (the flush lamp strips make way for open fluorescent fixtures, realism.fixture)
        if o.name.split(".")[0] in ("mz_ceiling", "mz_lampbox", "mz_lamp"):
            bpy.data.objects.remove(o, do_unlink=True)
    for y0, y1 in _segments():
        for x in (-2.5, 2.5):
            realism.fixture(m, x, y0, y1, MEZ_CEIL, drop=0.22)
    stair_exit.open_ceiling(M, DH_START, DH_END, STAIR_HOLE, STAIR_HALF_OPEN, WALL_X, MEZ_CEIL)
    stair_exit.end_walls(M, DH_START, DH_END, WALL_X, MEZ, MEZ_CEIL)

    # title sign over the platform
    group(signage.hanging_sign(["Sophie Shih's", "P O R T F O L I O"], w=3.6, h=1.0),
          (3.15, TITLE_Y, 2.85), rz=-28)

    # arrivals: a hanging countdown screen and a standing kiosk on the far platform
    arr = [("1Uptown & The Bronx", "Data line", "#ee352e", "2 min"), ("5Downtown", "Health line", "#00933c", "6 min")]
    fourth(_flat(realism.countdown_screen(arr, rod=1.0), "sign_countdown", (-3.6, 12.0, 2.75), 0))
    kio = [("1College App Atlas", "Data line", "#ee352e", "2"), ("4Agent00HL7", "Health line", "#00933c", "5"),
           ("7Folio", "Words line", "#b933ad", "9"), ("2Shopping Intent ML", "Data line", "#ee352e", "12"),
           ("5Dream Team", "Health line", "#00933c", "15")]
    fourth(_flat(realism.kiosk(kio), "sign_kiosk", (-3.9, 19.0, PLAT_Z), 90))

    # seven project stops on the right wall: mosaic tile, lightbox, bench or bin. The lightbox
    # bullets match the site: numbered by project, colored by line (BULLET).
    for i, (pid, name, letter, color) in enumerate(PROJECTS):
        yy = project_y(i)
        letter, color = BULLET[pid]
        # the name tiles were made smaller (Sophie, 2026-11-17): 2.6 x 0.72 m, letters scaled to match
        size = 0.21 if len(name) < 16 else 0.165
        group(signage.mosaic_tile(name, w=PROJECT_SIGN_W, h=0.72, size=size, field=FIELDS[i % 2]),
              (WALL_X - 0.02, yy, 2.85), rz=-90, name="project_" + pid)
        group(furniture.lightbox(name, build_station.BLURB[pid], letter, color),
              (WALL_X - 0.05, yy, 1.45), rz=-90)
        # benches alternate between the classic divided oak one and the newer oak-and-steel one
        if i % 4 == 0:
            group(realism.oak_bench(2.0, 3), (WALL_X - 0.55, yy + PROJECT_STEP / 2, PLAT_Z))
        elif i % 4 == 2:
            group(realism.modern_bench(2.2, 3), (WALL_X - 0.55, yy + PROJECT_STEP / 2, PLAT_Z))
        else:
            group(realism.trash_can(), (WALL_X - 0.5, yy + PROJECT_STEP / 2, PLAT_Z))
        # a small IND-style name tablet in the green band between the tiles
        group(realism.band_tablet("SOPHIE SHIH"), (WALL_X - 0.045, yy + PROJECT_STEP / 2, 3.55), rz=-90, name="sign_tablet_%d" % i)

    # posters on the fourth wall (left side of the platform)
    for k, yy in enumerate(range(0, int(DH_END) - 6, 6)):
        pid, name, letter, color = PROJECTS[k % len(PROJECTS)]
        if PSTAIR_X < 0 and yy + 1.5 - 0.7 < PSTAIR_Y + 0.3:
            continue  # the platform stairs stand against this wall here
        title = name.replace(" ", "\n", 1) if len(name) > 12 else name
        objs = fourth(signage.poster(title, "Next stop: platform " + letter, color, shape=k % 3))
        group(objs, (-WALL_X + 0.03, yy + 1.5, 1.65), rz=90)

    # mezzanine: line map, bench, arrivals board, newsstand, the stairs up to the street
    # the line map and the arrivals board hang on the right wall at eye height, the same size,
    # with a bench between them (MAP_S, BOARD_S and the heights are in layout_dollhouse.py)
    group(map_board.build(), (WALL_X - 0.06, MAP_Y, MAP_Z), rz=-90, s=MAP_S, name="sign_map")
    group(realism.oak_bench(2.4, 4), (WALL_X - 0.55, (MAP_Y + BOARD_Y) / 2, MEZ), rz=0)
    # the arrivals kiosk (Sophie, 2026-11-17: in place of the hanging digital board), standing
    # against the right wall and facing the walkway; each row is a project with its bullet
    line_of = {"#ee352e": "Data line", "#00933c": "Health line", "#b933ad": "Words line"}
    mins = ["Now", "2", "4", "6", "9", "12", "15", "18"]
    rows = [(BULLET[pid][0] + name, line_of[BULLET[pid][1]], BULLET[pid][1], mins[i])
            for i, (pid, name, _, _) in enumerate(PROJECTS)] + [("WBooks & Writing", "Newsstand", "#fccc0a", mins[7])]
    group(realism.kiosk(rows, title="Arrivals"), (WALL_X - KIOSK_OFF, BOARD_Y, MEZ), rz=-90, name="sign_board")
    group(newsstand.build(), (3.7, NEWSSTAND_Y, MEZ), name="newsstand")
    # stairs up to the street, at the far end (the left edge of the full-screen view).
    # stairs.build is unchanged; only its steps and handrails are kept. Its tile walls hid
    # the steps, and its street-level dressing (lamps, sign, sidewalk, trees, brownstones)
    # makes way for the subway entrance and the About-me billboard (ENTRANCE_SLOT and
    # BILLBOARD_SLOT in layout_dollhouse.py).
    up = []
    for o in stairs.build(steps=STAIR_STEPS):
        if o.name.split(".")[0] in ("tread", "nosing", "handrail"):
            up.append(o)
        else:
            for k in [o] + list(o.children_recursive):
                bpy.data.objects.remove(k, do_unlink=True)
    group(up, (STAIRS_X, STAIRS_Y, MEZ), name="stairs")
    # the way out: an Exit sign over the foot of the stairs, moonlight falling down them
    group(stair_exit.exit_sign(), (STAIRS_X, STAIR_HOLE[0] - 0.35, MEZ_CEIL - 0.2 - 0.27), name="sign_exit")
    stair_exit.night_light(STAIRS_X, STAIR_HOLE[0], STAIR_HOLE[1], STREET_TOP + 2.0, STAIR_HALF_OPEN)

    # stairs from the platform up to the mezzanine, at the near end (the right edge)
    # (turned around, so it climbs toward the end wall and lands by the right edge)
    group(stair_flight.build(width=PSTAIR_W, steps=PSTAIR_STEPS), (PSTAIR_X, PSTAIR_Y, PLAT_Z), rz=180, name="stairs_down")
    _concrete_steps()
    hx0, hx1, ha, hb = PSTAIR_HOLE
    stair_flight.guard(hx0 - 0.05, hx1, ha, hb - 0.15, MEZ, open_end="-y")

    # a few trees along the back of the street, clear of the entrance and the chalkboard
    stair_flight.trees(TREES, STREET_WALK_TOP)

    # SLOTS: the subway entrance (over the stair opening) and the About-me billboard go here
    from props import street_entrance
    hy0, hy1 = STAIR_HOLE
    hyc = (hy0 + hy1) / 2
    group(street_entrance.build_entrance(STAIR_HALF_OPEN, hy0 - hyc, hy1 - hyc),
          (STAIRS_X, hyc, STREET_WALK_TOP), name="entrance")
    group(street_entrance.build_chalkboard(), (BILLBOARD_X, BILLBOARD_Y, STREET_WALK_TOP), name="chalkboard")
    # grey flagstones over the sidewalk, matching the night street around it
    street_entrance.build_pavement(DH_START, DH_END, STREET_X, STAIR_HOLE, STAIR_HALF_OPEN, STREET_EARTH_TOP, STREET_WALK_TOP)

    lights()


def lights():
    world((1, .95, .88), 0.25)
    for y0, y1 in _segments():
        yc, L = (y0 + y1) / 2, y1 - y0
        for x in (-4.0, -2.0, 2.0, 4.0):   # under the fluorescent strips (realism.fixture)
            area((x, yc, CEIL_Z - 0.4), (0, 0, 0), 0.25, 95, (1, .92, .8), sy=L - 1.0)
        for x in (-2.5, 2.5):      # mezzanine lamps, under the street slab
            area((x, yc, MEZ_CEIL - 0.34), (0, 0, 0), 0.25, 110, (1, .92, .8), sy=L - 1.0)
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
