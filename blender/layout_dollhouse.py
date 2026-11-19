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
# Condensed (2026-11-13) so the full-screen view has little empty space: 44 m instead of 58.
DH_START, DH_END = -4.0, 40.0
TITLE_Y = 6.2
PROJECT_Y0, PROJECT_STEP = 10.6, 3.8     # mosaic tiles are 3.4 m long (PROJECT_TILE_W), 0.4 m apart
PROJECT_TILE_W = 3.4
PROJECT_SIGN_W = 2.6                     # the mosaic name tile itself (smaller than its 3.4 m slot)
MAP_Y, BOARD_Y, NEWSSTAND_Y = 8.0, 15.5, 24.0
# the line map (3.8 x 2.95 m as built) and the arrivals board (3.6 x 2.3 m) are scaled down to
# about 2.7 m wide and hung on the right wall, panels centered a little above eye height
MAP_S, BOARD_S = 0.72, 0.8
KIOSK_OFF = 0.45                          # the mezzanine arrivals kiosk stands this far off the right wall
MAP_Z = MEZ + 2.05                       # map panel center; its header ends ~0.35 m under the ceiling
BOARD_Z = MEZ + 1.95          # map by the stairs down (right), books left of center
# The street stairs sit at the far (+Y) end, which is the left edge of the full-screen view.
STAIRS_Y = DH_END - 0.6 - STAIR_STEPS * STAIR_RUN      # 47.0: foot of the stairs up to the street
STAIRS_X = 0.0
STAIR_TOP_Y = STAIRS_Y + STAIR_STEPS * STAIR_RUN       # 36.4: where the stairs reach the street
STAIR_HALF_OPEN = 1.5                                  # half width of the opening in the street slab
STAIR_HOLE = (STAIRS_Y - 0.2, STAIR_TOP_Y + 0.2)       # y range of that opening
# Stairs from the platform up to the mezzanine, at the near (-Y) end: the right edge of the view.
# They stand on the left (-X) platform, across the track, so they don't block the opening view
# down the right platform (Sophie, 2026-11-17).
PSTAIR_STEPS = 21                                      # 4.2 m: platform (0.2) up to the mezzanine (4.4)
PSTAIR_X, PSTAIR_W = -3.4, 2.4                         # on the left-hand platform, along the fourth wall
# They climb toward the end wall (-Y): the foot is on the platform, the top lands on the
# mezzanine near the right edge of the view, with a 1.4 m landing before the end wall.
PSTAIR_TOP_Y = DH_START + 1.4                          # -2.6: where they reach the mezzanine
PSTAIR_Y = PSTAIR_TOP_Y + PSTAIR_STEPS * STAIR_RUN     # 4.12: foot of the stairs on the platform
# opening in the mezzanine floor over them: (x0, x1, y0, y1)
PSTAIR_HOLE = (PSTAIR_X - PSTAIR_W / 2 - 0.15, PSTAIR_X + PSTAIR_W / 2 + 0.15, PSTAIR_TOP_Y, PSTAIR_Y + 0.2)
# Free space on the street for the props designed separately, as (x0, x1, y0, y1) on the sidewalk
# (z = STREET_WALK_TOP). The entrance sits around the opening of the stairs down; the
# billboard stands toward the back of the street, facing the viewer (-X), mid-station.
ENTRANCE_SLOT = (-2.4, 2.4, STAIR_HOLE[0] - 0.6, DH_END)
# the About-me chalkboard stands about 5 m in front of the entrance so both share a view
BILLBOARD_X, BILLBOARD_Y = 3.5, STAIR_HOLE[0] - 5.0     # 27.8 (its face is toward -X)
BILLBOARD_SLOT = (BILLBOARD_X - 0.8, BILLBOARD_X + 0.8, BILLBOARD_Y - 1.0, BILLBOARD_Y + 1.0)
TREES = [(6.5, -1.0), (8.0, 6.0), (6.5, 13.0), (8.0, 20.0), (7.0, 36.5)]   # (x, y) on the street
TRAIN_STOP_Y = PROJECT_Y0 - 4.0          # front of the train after the opening
TRAIN_AHEAD = 2.6                        # a project's train stops with its front this far past the tile (-Y)
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
        "title": {"pos": [1.2, -2.6, 1.6], "look": [-0.3, 10.0, 1.3], "fov": 62},
        # straight on; the map sits left of center, clear of the line panel on the right
        "map": {"pos": [0.0, MAP_Y - 1.1, MEZ + 1.75], "look": [WALL_X, MAP_Y - 1.1, MEZ + 2.0], "fov": 50},
        # the arrivals kiosk, a little from the side so it stands out from the wall
        "board": {"pos": [2.2, BOARD_Y - 1.5, MEZ + 1.6], "look": [WALL_X - KIOSK_OFF, BOARD_Y, MEZ + 1.35], "fov": 45},
        "newsstand": {"pos": [2.0, NEWSSTAND_Y - 5.5, MEZ + 1.7], "look": [3.4, NEWSSTAND_Y, MEZ + 1.9], "fov": 55},
        # back from the foot of the stairs, under the Exit sign, looking up them to the night sky
        "exit": {"pos": [-0.9, STAIRS_Y - 5.5, MEZ + 1.6], "look": [0.0, STAIRS_Y + 4.0, MEZ + 3.0], "fov": 60},
        # on the street, with the chalkboard on the right and the whole entrance on the left
        "street": {"pos": [-7.0, BILLBOARD_Y + 1.0, 10.2],
                   "look": [2.0, STAIR_HOLE[0] - 1.0, 9.4], "fov": 55},
    }
    for i, pid in enumerate(PROJECT_IDS):
        y = project_y(i)
        # on the platform past the tile, looking back up the track: the train pulls in with its
        # front (and route bullet) toward you, and the tile is on the right wall
        s["project:" + pid] = {"pos": [3.4, y - 3.4, 1.7], "look": [2.2, y + 1.6, 1.9], "fov": 62}
    return s


# ---------------------------------------------------------------- clickable objects
def hotspots():
    """Boxes (center c, size s) the site raycasts against. Objects win over levels."""
    H = []

    def add(id_, level, c, s):
        H.append({"id": id_, "level": level, "c": list(c), "s": list(s)})

    add("title", "platform", (3.15, TITLE_Y, 2.85), (3.2, 1.8, 1.2))
    for i, pid in enumerate(PROJECT_IDS):
        add("project:" + pid, "platform", (WALL_X - 0.1, project_y(i), 2.2), (0.5, PROJECT_TILE_W + 0.1, 2.4))
    add("map", "mezzanine", (WALL_X - 0.1, MAP_Y, MAP_Z + 0.25), (0.5, 3.8 * MAP_S, 2.95 * MAP_S))
    add("board", "mezzanine", (WALL_X - KIOSK_OFF, BOARD_Y, MEZ + 1.05), (0.5, 0.9, 2.1))
    add("newsstand", "mezzanine", (3.85, NEWSSTAND_Y, MEZ + 1.6), (1.6, 3.2, 3.4))
    add("exit", "mezzanine", (STAIRS_X, STAIRS_Y + 3.2, MEZ + 2.0), (2.8, 6.6, 4.0))
    # the About-me billboard opens the About card; the subway entrance leads down to the mezzanine
    add("street", "street", (BILLBOARD_X - 0.15, BILLBOARD_Y, STREET_WALK_TOP + 0.9), (0.9, 1.4, 1.9))  # 9.2
    add("entrance", "street", (STAIRS_X, (ENTRANCE_SLOT[2] + ENTRANCE_SLOT[3]) / 2, STREET_WALK_TOP + 1.4),
        (ENTRANCE_SLOT[1] - ENTRANCE_SLOT[0], ENTRANCE_SLOT[3] - ENTRANCE_SLOT[2], 2.8))
    # the stairs down to the platform (they lead to the platform stop)
    add("stairs_down", "mezzanine", (PSTAIR_X, (PSTAIR_Y + PSTAIR_TOP_Y) / 2, (PLAT_Z + MEZ + 1.0) / 2),
        (PSTAIR_W + 0.3, PSTAIR_TOP_Y - PSTAIR_Y, MEZ + 1.0 - PLAT_Z))
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
        "train": {"stopY": TRAIN_STOP_Y, "parkY": TRAIN_PARK_Y, "ahead": TRAIN_AHEAD},
        "projectY0": PROJECT_Y0,
        "projectStep": PROJECT_STEP,
        "titleSignY": TITLE_Y,
    }
