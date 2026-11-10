"""Assemble the station, then either render preview stills or bake light into
textures and export public/subway/station.glb.

  python blender/build_station.py preview [samples]       # stills -> blender/renders/
  python blender/build_station.py bake [res] [samples]    # station.glb + layout.json

Run with the `bpy` module (pip install bpy==5.2.3) or `blender -b -P`.
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from common import *
from layout import *
from props import station_shell, signage, map_board, countdown_clock, newsstand, stairs, furniture

ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(ROOT, "public", "subway")
RENDERS = os.path.join(HERE, "renders")

# Short lines for each project's lightbox (full details live in data/projects.ts)
BLURB = {
    "college-app-atlas": "Brainstorm, draft and track college\napplications in one cozy place.",
    "purchase-intent": "Predicts whether a shopping session\nends in a purchase. 0.92 ROC-AUC.",
    "new-york-census": "NYC told through Census data\non a subway map of 55 neighborhoods.",
    "folio": "Pinterest for literature: news,\npreprints and pop culture.",
    "agent00hl7": "LLM agents turn radiology reports\ninto patient-friendly letters.",
    "dream-team": "Agents that read a report, find the\nright specialist and book the visit.",
    "neurobiome": "How the microbiome relates to\nParkinson's, explained by an AI agent.",
}


def stops():
    """Camera stops the site moves between (position, look-at)."""
    s = {
        # every stop keeps x >= 1.9 so camera moves never pass through the parked train
        "title": {"pos": [3.9, -3.2, 1.55], "look": [-0.3, 10.0, 1.3], "fov": 62},
        "map": {"pos": [2.0, MAP_Y - 1.6, 1.75], "look": [WALL_X, MAP_Y + 0.3, 1.95], "fov": 55},
        "board": {"pos": [3.0, BOARD_Y - 5.8, 1.6], "look": [3.2, BOARD_Y, 2.55], "fov": 55},
        "newsstand": {"pos": [2.0, NEWSSTAND_Y - 5.5, 1.7], "look": [3.4, NEWSSTAND_Y, 1.9], "fov": 55},
        "exit": {"pos": [3.1, STAIRS_Y - 5.0, 1.6], "look": [3.35, STAIRS_Y + 3, 2.8], "fov": 60},
    }
    for i, (pid, *_rest) in enumerate(PROJECTS):
        y = PROJECT_Y0 + i * PROJECT_STEP
        s["project:" + pid] = {"pos": [2.0, y - 2.0, 1.7], "look": [WALL_X, y + 0.2, 1.95], "fov": 55}
    return s


def assemble():
    reset()
    m = station_shell.materials()
    y = STATION_START
    while y < STATION_END:
        top = y >= STAIRS_Y - 0.01
        station_shell.segment(m, y, y + CHUNK, stair_gap=top)
        y += CHUNK
    station_shell.ends(m)

    # Title sign over the right platform, angled toward the arriving train/camera
    group(signage.hanging_sign(["Sophie Shih's", "P O R T F O L I O"], w=3.6, h=1.0), (3.15, TITLE_SIGN_Y, 2.85), rz=-28)

    # Map wall (right wall, facing -X) with a bench in front
    group(map_board.build(), (WALL_X - 0.08, MAP_Y, 1.95), rz=-90)
    group(furniture.bench(2.4), (WALL_X - 0.75, MAP_Y, PLAT_Z), rz=0)

    # Arrivals board hanging over the platform
    rows = [(name, c) for (_, name, _, c) in PROJECTS] + [("Books & Writing", "#a0522d")]
    group(countdown_clock.build(rows), (3.25, BOARD_Y, 2.55), rz=-12, s=0.85)

    # Project stops: mosaic name tile + lightbox on the right wall
    fields = [("#8a3b26", "#9c4a30", "#7c321f", "#a5543a"), ("#1f3f8f", "#24489c", "#1a3678", "#2a52a8")]
    for i, (pid, name, letter, color) in enumerate(PROJECTS):
        yy = PROJECT_Y0 + i * PROJECT_STEP
        size = 0.3 if len(name) < 16 else 0.24
        group(signage.mosaic_tile(name, w=4.0, h=0.95, size=size, field=fields[i % 2]), (WALL_X - 0.02, yy, 2.85), rz=-90)
        group(furniture.lightbox(name, BLURB[pid], letter, color), (WALL_X - 0.05, yy, 1.45), rz=-90)
        if i % 2 == 0:
            group(furniture.bench(2.0), (WALL_X - 0.75, yy + 2.9, PLAT_Z))
        else:
            group(furniture.trash_can(), (WALL_X - 0.5, yy + 2.6, PLAT_Z))

    # Newsstand and exit stairs
    group(newsstand.build(), (3.7, NEWSSTAND_Y, PLAT_Z))
    group(stairs.build(), (3.35, STAIRS_Y, PLAT_Z))

    # Posters on the far (left) wall facing +X
    shapes = 0
    for k, yy in enumerate(range(-5, 78, 6)):
        pid, name, letter, color = PROJECTS[k % len(PROJECTS)]
        title = name.replace(" ", "\n", 1) if len(name) > 12 else name
        group(signage.poster(title, "Next stop: platform " + letter, color, shape=k % 3), (-WALL_X + 0.03, yy + 1.5, 1.65), rz=90)

    lights()


def lights():
    world((1, .95, .88), 0.25)
    # warm light under each lamp strip, plus a soft fill per chunk
    y = STATION_START
    while y < STATION_END:
        for x in (-3.5, 0, 3.5):
            if x > 3 and y >= STAIRS_Y - 0.01:
                continue
            area((x, y + CHUNK / 2, CEIL_Z - 0.09), (0, 0, 0), 0.3, 120, (1, .9, .74), sy=CHUNK - 1.0)
        y += CHUNK
    # daylight down the stairwell
    sun((R(40), 0, R(180)), 3.0, (1, .93, .8))


def preview(samples=24):
    s = render_setup(960, 600, samples)
    os.makedirs(RENDERS, exist_ok=True)
    for name, st in stops().items():
        if name.startswith("project:") and not name.endswith("new-york-census"):
            continue
        cam = camera(st["pos"], st["look"])
        cam.data.sensor_fit = "VERTICAL"; cam.data.sensor_height = 24
        cam.data.lens = 12 / math.tan(math.radians(st["fov"]) / 2)
        render(os.path.join(RENDERS, name.replace(":", "_") + ".png"))
        bpy.data.objects.remove(cam)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    mode = args[0] if args else "preview"
    assemble()
    if mode == "preview":
        preview(int(args[1]) if len(args) > 1 else 24)
    elif mode == "bake":
        from bake import bake_and_export
        res = int(args[1]) if len(args) > 1 else 2048
        smp = int(args[2]) if len(args) > 2 else 96
        bake_and_export(os.path.join(OUT_DIR, "station.glb"), res, smp)
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(os.path.join(OUT_DIR, "layout.json"), "w") as f:
            json.dump({"stops": stops(), "projectY0": PROJECT_Y0, "projectStep": PROJECT_STEP,
                       "lines": LINES, "station": [STATION_START, STATION_END],
                       "titleSignY": TITLE_SIGN_Y}, f, indent=1)
