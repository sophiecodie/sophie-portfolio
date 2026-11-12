"""New structure for the dollhouse cut: the earth around the levels, the mezzanine
floor and walls, the street slab with its stair opening, lamp strips, and the
platform's left wall (the fourth wall).

It uses the materials from station_shell and common and does not change them.
Placement comes from layout_dollhouse.py.
"""
from common import *
from layout import WALL_X, PLAT_Z
from layout_dollhouse import *


def materials(shell):
    """The station_shell materials plus the earth and sidewalk surfaces for the cut."""
    M = dict(shell)
    M["earth"] = noise_mat("cut_earth", "#7b6248", "#94785a", scale=5, rough=0.95, detail=8)
    M["walk"] = noise_mat("street_walk", "#d9ccb4", "#e6dbc6", scale=3, rough=0.85)
    return M


def _box(name, x0, x1, y0, y1, z0, z1, m):
    return cube(name, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), m)


def ground(M, y0, y1):
    """The earth under the track. Its front and end faces are the cut."""
    return [_box("cut_ground", -EARTH_X, EARTH_X, y0, y1, EARTH_BOTTOM, EARTH_TOP, M["earth"])]


def mezz_floor(M, y0, y1):
    """Earth slab that the mezzanine stands on, with a terrazzo walk surface."""
    return [_box("cut_mezz_earth", -EARTH_X, EARTH_X, y0, y1, MEZ_SLAB_BOT, MEZ_EARTH_TOP, M["earth"]),
            _box("cut_mezz_floor", -WALL_X, WALL_X, y0, y1, MEZ_EARTH_TOP, MEZ, M["floor"])]


def street(M, y0, y1):
    """Street slab: earth below, sidewalk on top. It is open over the stairs, and it
    doubles as the mezzanine's ceiling everywhere else."""
    hy0, hy1 = STAIR_HOLE
    xw, xh = STREET_X, STAIR_HALF_OPEN

    def slab(name, z0, z1, m):
        parts = []
        if hy0 > y0:
            parts.append(_box(name + "_a", -xw, xw, y0, hy0, z0, z1, m))
        if y1 > hy1:
            parts.append(_box(name + "_b", -xw, xw, hy1, y1, z0, z1, m))
        parts.append(_box(name + "_l", -xw, -xh, hy0, hy1, z0, z1, m))
        parts.append(_box(name + "_r", xh, xw, hy0, hy1, z0, z1, m))
        return parts

    return (slab("cut_street_earth", MEZ_CEIL, STREET_EARTH_TOP, M["earth"]) +
            slab("cut_street_walk", STREET_EARTH_TOP, STREET_WALK_TOP, M["walk"]))


def mezz_wall(M, sx, y0, y1):
    """Tile wall for the mezzanine, with the same bands and base as the platform."""
    L = y1 - y0
    yc = (y0 + y1) / 2
    zc = (MEZ + MEZ_CEIL) / 2
    return [cube("mz_wall", (sx * (WALL_X + 0.05), yc, zc), (0.1, L, MEZ_CEIL - MEZ), M["tile"]),
            cube("mz_band", (sx * (WALL_X - 0.01), yc, MEZ + 2.9), (0.04, L, 0.36), M["band"]),
            cube("mz_trim", (sx * (WALL_X - 0.015), yc, MEZ + 2.6), (0.03, L, 0.1), M["trim"]),
            cube("mz_trim2", (sx * (WALL_X - 0.015), yc, MEZ + 3.3), (0.03, L, 0.1), M["trim"]),
            cube("mz_base", (sx * (WALL_X - 0.01), yc, MEZ + 0.12), (0.04, L, 0.24), M["base"])]


def mezz_lamps(M, y0, y1):
    """A cream ceiling under the street slab, with two lamp strips like the platform's."""
    L = y1 - y0
    yc = (y0 + y1) / 2
    out = [_box("mz_ceiling", -WALL_X, WALL_X, y0, y1, MEZ_CEIL - 0.04, MEZ_CEIL, M["ceiling"])]
    for x in (-2.5, 2.5):
        out.append(cube("mz_lampbox", (x, yc, MEZ_CEIL - 0.03), (0.22, L - 0.6, 0.06), M["ceiling"]))
        out.append(cube("mz_lamp", (x, yc, MEZ_CEIL - 0.065), (0.14, L - 0.8, 0.01), M["lamp"]))
    return out


def platform_wall(M, sx, y0, y1):
    """The platform's tile wall on side sx. The left one is the fourth wall; the right
    one comes from station_shell.segment, so the numbers match its wall."""
    L = y1 - y0
    yc = (y0 + y1) / 2
    return [cube("pf_wall", (sx * (WALL_X + 0.05), yc, 2.1), (0.1, L, 4.0), M["tile"]),
            cube("pf_band", (sx * (WALL_X - 0.01), yc, 3.55), (0.04, L, 0.36), M["band"]),
            cube("pf_trim", (sx * (WALL_X - 0.015), yc, 3.3), (0.03, L, 0.1), M["trim"]),
            cube("pf_trim2", (sx * (WALL_X - 0.015), yc, 3.8), (0.03, L, 0.1), M["trim"]),
            cube("pf_base", (sx * (WALL_X - 0.01), yc, PLAT_Z + 0.12), (0.04, L, 0.24), M["base"])]
