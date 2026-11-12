"""Where everything sits in the dollhouse cutaway. Units are meters; the track runs
along +Y and the levels stack along +Z.

The station is cut open like a dollhouse: the platform at the bottom, the mezzanine
above it, and the street on top. This file only decides positions and camera stops.
The props are the same builders as before (props/*.py, unchanged). The cut structure
is in props/cutaway.py. The old layout.py and build_station.py are left as they were.
"""
from layout import WALL_X, CEIL_Z, PLAT_Z

# ---------------------------------------------------------------- level heights (z)
EARTH_TOP, EARTH_BOTTOM = -0.6, -2.0     # earth block under the track bed
PLAT_CEIL = CEIL_Z                       # platform ceiling is 4.0..4.1 (station_shell)
MEZ_SLAB_BOT = 4.1                       # underside of the mezzanine floor slab
MEZ_EARTH_TOP = 4.25                     # earth part of the slab; terrazzo walk surface on top
MEZ = 4.4                                # mezzanine walking surface
STAIR_STEPS, STAIR_RUN, STAIR_RISE = 20, 0.32, 0.2     # stairs.build(steps=20): 4.0 m rise
STREET_TOP = MEZ + STAIR_STEPS * STAIR_RISE            # 8.4: top of the stairs and sidewalk
STREET_WALK_TOP = STREET_TOP - 0.1                     # 8.3: walkable top of the street slab
STREET_EARTH_TOP = STREET_TOP - 0.2                    # 8.2: earth part of the street slab
MEZ_CEIL = STREET_TOP - 0.4                            # 8.0: underside of the street slab
EARTH_X = 6.0                            # cut faces stick out past the walls
STREET_X = 12.0                          # matches the 24 m sidewalk from stairs.build()

# ---------------------------------------------------------------- positions along Y
DH_START, DH_END = -4.0, 54.0
TITLE_Y = 6.0
PROJECT_Y0, PROJECT_STEP = 14.0, 4.4     # mosaic tiles are 4.0 m long along Y, so 3 to 3.5 m would overlap
MAP_Y, BOARD_Y, NEWSSTAND_Y, STAIRS_Y = 6.0, 14.0, 22.0, 30.0
STAIRS_X = 0.0
STAIR_TOP_Y = STAIRS_Y + STAIR_STEPS * STAIR_RUN       # 36.4: where the stairs reach the street
STAIR_HALF_OPEN = 1.5                                  # half width of the opening in the street slab
STAIR_HOLE = (STAIRS_Y - 0.2, STAIR_TOP_Y + 0.2)       # y range of that opening
TRAIN_STOP_Y = PROJECT_Y0 - 4.0          # front of the train when a project opens
TRAIN_PARK_Y = -80.0                     # parked out of frame until needed

PROJECT_IDS = ["college-app-atlas", "purchase-intent", "new-york-census", "folio",
               "agent00hl7", "dream-team", "neurobiome"]   # same order as common.PROJECTS


def project_y(i):
    return PROJECT_Y0 + i * PROJECT_STEP


# ---------------------------------------------------------------- camera stops
def stops():
    s = {
        # outside the cut, a little to the side: all three levels on screen
        "overview": {"pos": [-30.0, 16.0, 9.0], "look": [0.0, 26.0, 3.5], "fov": 40},
        # standing on the platform, looking down the track toward the title sign
        "title": {"pos": [3.9, -3.2, 1.55], "look": [-0.3, 10.0, 1.3], "fov": 62},
        "map": {"pos": [2.0, MAP_Y - 1.6, MEZ + 1.75], "look": [WALL_X, MAP_Y + 0.3, MEZ + 1.95], "fov": 55},
        "board": {"pos": [3.0, BOARD_Y - 5.8, MEZ + 1.6], "look": [3.2, BOARD_Y, MEZ + 1.4], "fov": 55},
        "newsstand": {"pos": [2.0, NEWSSTAND_Y - 5.5, MEZ + 1.7], "look": [3.4, NEWSSTAND_Y, MEZ + 1.9], "fov": 55},
        "exit": {"pos": [-1.2, STAIRS_Y - 3.0, MEZ + 1.6], "look": [0.0, STAIRS_Y + 4.0, MEZ + 2.4], "fov": 60},
        "street": {"pos": [-1.0, STAIR_TOP_Y + 1.2, STREET_WALK_TOP + 1.6],
                   "look": [1.5, STAIR_TOP_Y + 12.0, STREET_WALK_TOP + 1.8], "fov": 58},
    }
    for i, pid in enumerate(PROJECT_IDS):
        y = project_y(i)
        s["project:" + pid] = {"pos": [2.0, y - 2.0, 1.7], "look": [WALL_X, y + 0.2, 1.95], "fov": 55}
    return s


# ---------------------------------------------------------------- clickable objects
def hotspots():
    """Boxes (center c, size s) the site raycasts against. Objects win over levels."""
    H = []

    def add(id_, level, c, s):
        H.append({"id": id_, "level": level, "c": list(c), "s": list(s)})

    add("title", "platform", (3.15, TITLE_Y, 2.85), (3.2, 1.8, 1.2))
    for i, pid in enumerate(PROJECT_IDS):
        add("project:" + pid, "platform", (WALL_X - 0.1, project_y(i), 2.2), (0.5, 4.2, 2.4))
    add("map", "mezzanine", (WALL_X - 0.1, MAP_Y, MEZ + 1.9), (0.5, 4.0, 2.6))
    add("board", "mezzanine", (3.25, BOARD_Y, MEZ + 1.4), (1.0, 3.4, 2.4))
    add("newsstand", "mezzanine", (3.85, NEWSSTAND_Y, MEZ + 1.6), (1.6, 3.2, 3.4))
    add("exit", "mezzanine", (STAIRS_X, STAIRS_Y + 3.2, MEZ + 2.0), (2.8, 6.6, 4.0))
    add("street", "street", (0.0, STAIR_TOP_Y + 10.0, STREET_WALK_TOP + 3.0), (20.0, 14.0, 6.0))
    # whole levels, for clicking the empty part of a level
    mid = (DH_START + DH_END) / 2
    L = DH_END - DH_START
    add("level:platform", "platform", (0.0, mid, 2.05), (2 * WALL_X, L, PLAT_CEIL + 0.1))
    add("level:mezzanine", "mezzanine", (0.0, mid, (MEZ + MEZ_CEIL) / 2), (2 * WALL_X, L, MEZ_CEIL - MEZ))
    add("level:street", "street", (0.0, mid, STREET_WALK_TOP + 1.5), (2 * STREET_X, L, 3.0))
    return H


def describe():
    """Written to public/subway/layout-dollhouse.json for the site."""
    return {
        "stops": stops(),
        "hotspots": hotspots(),
        # what the arrow keys walk through, in order, per level
        "walk": {
            "platform": ["title"] + ["project:" + p for p in PROJECT_IDS],
            "mezzanine": ["map", "board", "newsstand", "exit"],
            "street": ["street"],
        },
        # walking surface and ceiling of each level, in meters
        "levels": {"platform": {"floor": PLAT_Z, "ceiling": PLAT_CEIL},
                   "mezzanine": {"floor": MEZ, "ceiling": MEZ_CEIL},
                   "street": {"floor": STREET_WALK_TOP, "ceiling": None}},
        "station": {"yMin": DH_START, "yMax": DH_END, "xHalf": WALL_X, "streetHalf": STREET_X},
        "train": {"stopY": TRAIN_STOP_Y, "parkY": TRAIN_PARK_Y},
        "projectY0": PROJECT_Y0,
        "projectStep": PROJECT_STEP,
        "titleSignY": TITLE_Y,
    }
