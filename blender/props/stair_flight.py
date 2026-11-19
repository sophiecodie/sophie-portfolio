"""Stairs from the platform up to the mezzanine, for the dollhouse station.

A plain flight that rises along +Y from the origin. It has no side walls: its -X side
faces the cut, so the steps read clearly in the full-screen section view, and its +X
side runs along the platform wall. Also here: the guard rail around the opening in the
mezzanine floor, and the street trees (the ones stairs.build adds now fall past the end
of the cut, since the street stairs moved to the far end).

Materials use the same names and colors as props/stairs.py. stairs.py is not changed.
"""
from common import *


def build(width=2.4, steps=21, rise=0.2, run=0.32):
    step = terrazzo_mat("stair_terrazzo", base="#ddd0b8")
    nose = mat("stair_nosing", "#f2c24c", 0.5)
    rail = mat("rail_green", "#2f6b4f", 0.35, coat=0.5)
    o = []
    for i in range(steps):
        o.append(cube("tread", (0, i * run + run / 2, (i + 1) * rise / 2), (width, run, (i + 1) * rise), step))
        o.append(cube("nosing", (0, i * run + 0.02, (i + 1) * rise + 0.003), (width, 0.04, 0.008), nose))
    top_y, top_z = steps * run, steps * rise
    for sx in (-1, 1):
        x = sx * (width / 2 - 0.08)
        o.append(tube("handrail", [(x, -0.3, 0.95), (x, top_y, top_z + 0.95)], 0.025, rail))
        # posts every few steps hold the rail up
        for i in range(1, steps, 4):
            y, z = i * run + run / 2, (i + 1) * rise
            o.append(cyl("baluster", (x, y, z + 0.47), 0.018, 0.94, rail, verts=12))
    return o


def guard(x0, x1, y0, y1, z, open_end="+y"):
    """A rail around a floor opening at height z, open on one end (where the stairs arrive)."""
    rail = mat("rail_green", "#2f6b4f", 0.35, coat=0.5)
    sides = {"-x": [(x0, y0), (x0, y1)], "+x": [(x1, y0), (x1, y1)],
             "-y": [(x0, y0), (x1, y0)], "+y": [(x0, y1), (x1, y1)]}
    o = []
    for k, (a, b) in sides.items():
        if k == open_end:
            continue
        o.append(tube("guard_top", [(a[0], a[1], z + 1.0), (b[0], b[1], z + 1.0)], 0.03, rail))
        o.append(tube("guard_mid", [(a[0], a[1], z + 0.5), (b[0], b[1], z + 0.5)], 0.015, rail))
        n = max(1, int(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5 / 1.2))
        for i in range(n + 1):
            t = i / n
            o.append(cyl("guard_post", (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, z + 0.5), 0.025, 1.0, rail, verts=12))
    return o


def trees(points, z):
    """Street trees, the same as the ones in stairs.build."""
    trunk = mat("tree_trunk", "#7a5a42", 0.8)
    leaves = noise_mat("tree_leaves", "#6f9f5a", "#94c070", scale=4, rough=0.8)
    o = []
    for (x, y) in points:
        o.append(cyl("trunk", (x, y, z + 0.9), 0.12, 1.8, trunk))
        o.append(sphere("crown", (x, y, z + 2.4), 1.1, leaves, seg=16))
    return o
