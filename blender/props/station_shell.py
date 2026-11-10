"""The station box: platforms, tile walls, ceiling, green columns, track bed.

Long surfaces are cut into CHUNK-long segments so each light-bake atlas covers
one slice of the station.
"""
import math
from common import *
from layout import *


def materials():
    return dict(
        tile=tile_mat("wall_tile"),
        trim=mosaic_mat("trim_mosaic", ["#7d4a2c", "#8c5634", "#6e3f25", "#9a6440"], grout="#4a2f20", tess=0.02),
        band=mosaic_mat("band_mosaic", ["#4e7a5c", "#5c8a68", "#45704f", "#6a9876"], grout="#33433a", tess=0.02),
        floor=terrazzo_mat("platform_floor"),
        edge=mosaic_mat("edge_tactile", ["#f2c24c", "#eebd45", "#f5c851"], grout="#c99a28", tess=0.06, rough=0.6),
        dots=mat("edge_dots", "#d9a92e", 0.6),
        ceiling=mat("ceiling", "#efe4d0", 0.8),
        lamp=mat("lamp", "#fffaf0", 0.4, emit="#fff4dc", emit_str=6.0),
        column=mat("column_green", "#2f6b4f", 0.35, coat=0.5),
        column_cap=mat("column_cap", "#c9a24a", 0.35, metal=0.6),
        bed=noise_mat("track_bed", "#8a7358", "#a58b6a", scale=6, rough=0.95),
        sleeper=noise_mat("sleeper", "#7a5c40", "#8e6b4a", scale=20, rough=0.85),
        rail=mat("rail_steel", "#b4b8bd", 0.3, metal=0.9),
        base=mat("wall_base", "#6f5b4b", 0.6),
        tunnel=mat("tunnel_dark", "#2e2622", 0.95),
        end=mat("end_wall", "#e8dcc6", 0.75),
    )


def segment(m, y0, y1, walls=(-1, 1), stair_gap=False):
    """stair_gap: leave the ceiling open over the right platform for the exit stairs."""
    L = y1 - y0
    yc = (y0 + y1) / 2
    objs = []
    for sx in (-1, 1):
        # platform slab + floor + edge
        objs.append(cube("plat", (sx * (PLAT_INNER + WALL_X) / 2, yc, PLAT_Z / 2 - 0.45), (WALL_X - PLAT_INNER, L, PLAT_Z + 0.9 - 0.02), m["floor"]))
        objs.append(cube("edge", (sx * (PLAT_INNER + 0.3), yc, PLAT_Z + 0.006), (0.6, L, 0.012), m["edge"]))
        if sx in walls:
            # tile wall, mosaic band near the top, dark base
            objs.append(cube("wall", (sx * (WALL_X + 0.05), yc, 2.1), (0.1, L, 4.0), m["tile"]))
            objs.append(cube("band", (sx * (WALL_X - 0.01), yc, 3.55), (0.04, L, 0.36), m["band"]))
            objs.append(cube("trim", (sx * (WALL_X - 0.015), yc, 3.3), (0.03, L, 0.1), m["trim"]))
            objs.append(cube("trim2", (sx * (WALL_X - 0.015), yc, 3.8), (0.03, L, 0.1), m["trim"]))
            objs.append(cube("base", (sx * (WALL_X - 0.01), yc, PLAT_Z + 0.12), (0.04, L, 0.24), m["base"]))
    # ceiling and lamp strips
    if stair_gap:
        objs.append(cube("ceil", ((-WALL_X - 0.1 + 1.9) / 2, yc, CEIL_Z + 0.05), (WALL_X + 0.1 + 1.9, L, 0.1), m["ceiling"]))
    else:
        objs.append(cube("ceil", (0, yc, CEIL_Z + 0.05), (2 * WALL_X + 0.2, L, 0.1), m["ceiling"]))
    for x in ((-3.5, 0) if stair_gap else (-3.5, 3.5, 0)):
        objs.append(cube("lampbox", (x, yc, CEIL_Z - 0.03), (0.22, L - 0.6, 0.06), m["ceiling"]))
        objs.append(cube("lamp", (x, yc, CEIL_Z - 0.065), (0.14, L - 0.8, 0.01), m["lamp"]))
    # track bed, sleepers, rails
    objs.append(cube("bed", (0, yc, -0.45), (2 * PLAT_INNER, L, 0.3), m["bed"]))
    n = int(L / 0.6)
    for k in range(n):
        objs.append(cube("sleeper", (0, y0 + 0.3 + k * 0.6, -0.26), (2.3, 0.2, 0.09), m["sleeper"], bevel=0.008))
    for rx in (-0.72, 0.72):
        objs.append(cube("rail_web", (rx, yc, -0.16), (0.03, L, 0.12), m["rail"]))
        objs.append(cube("rail_head", (rx, yc, -0.09), (0.07, L, 0.035), m["rail"], bevel=0.01))
    # columns
    yy = math.ceil(y0 / COL_STEP) * COL_STEP
    while yy < y1:
        for sx in ((-1,) if stair_gap else (-1, 1)):
            objs.append(cyl("column", (sx * COL_X, yy, (PLAT_Z + CEIL_Z) / 2), 0.13, CEIL_Z - PLAT_Z, m["column"]))
            objs.append(cyl("capital", (sx * COL_X, yy, CEIL_Z - 0.12), 0.19, 0.16, m["column_cap"]))
            objs.append(cyl("plinth", (sx * COL_X, yy, PLAT_Z + 0.08), 0.18, 0.16, m["column_cap"]))
        yy += COL_STEP
    return objs


def ends(m):
    """End walls with dark tunnel mouths beyond the platforms."""
    objs = []
    hw = 1.6  # half width of the tunnel opening
    for y, s in ((STATION_START, -1), (STATION_END, 1)):
        side = WALL_X + 0.1 - hw
        for sx in (-1, 1):
            objs.append(cube("endwall", (sx * (hw + side / 2), y + s * 0.1, 1.8), (side, 0.2, 4.6), m["end"]))
        objs.append(cube("lintel", (0, y + s * 0.1, 3.3), (2 * hw, 0.2, 1.6), m["end"]))
        # dark tunnel box behind the opening (open toward the station)
        objs.append(cube("tun_top", (0, y + s * 6, 2.55), (2 * hw, 12, 0.1), m["tunnel"]))
        objs.append(cube("tun_back", (0, y + s * 12, 1.0), (2 * hw, 0.1, 3.4), m["tunnel"]))
        for sx in (-1, 1):
            objs.append(cube("tun_side", (sx * hw, y + s * 6, 1.0), (0.1, 12, 3.4), m["tunnel"]))
        objs.append(cube("tun_floor", (0, y + s * 6, -0.45), (2 * hw, 12, 0.3), m["bed"]))
        for rx in (-0.72, 0.72):
            objs.append(cube("rail_t", (rx, y + s * 6, -0.12), (0.07, 12, 0.1), m["rail"]))
    return objs
