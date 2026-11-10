"""Exit stairs up to the street (About / Contact). Stairs rise along +Y from
the origin; the street, lamp globes, trees and brownstones sit at the top.
"""
from common import *
from props.signage import hanging_sign


def build(width=2.6, steps=18, rise=0.2, run=0.32):
    step = terrazzo_mat("stair_terrazzo", base="#ddd0b8")
    nose = mat("stair_nosing", "#f2c24c", 0.5)
    tile = tile_mat("stair_tile")
    rail = mat("rail_green", "#2f6b4f", 0.35, coat=0.5)
    globe = mat("lamp_globe", "#a8f0c0", 0.2, emit="#a8f0c0", emit_str=5)
    walk = noise_mat("sidewalk", "#d9ccb4", "#e6dbc6", scale=3, rough=0.85)
    trunk = mat("tree_trunk", "#7a5a42", 0.8)
    leaves = noise_mat("tree_leaves", "#6f9f5a", "#94c070", scale=4, rough=0.8)
    brick = [noise_mat("brick_" + c, c, c, scale=1) for c in ("#c98d74", "#d9a88a", "#b97a68")]
    window = mat("bld_window", "#fff1c9", 0.3, emit="#ffe4a8", emit_str=1.2)
    o = []
    for i in range(steps):
        o.append(cube("tread", (0, i * run + run / 2, (i + 1) * rise / 2), (width, run, (i + 1) * rise), step))
        o.append(cube("nosing", (0, i * run + 0.02, (i + 1) * rise + 0.003), (width, 0.04, 0.008), nose))
    top_y, top_z = steps * run, steps * rise
    for sx in (-1, 1):
        o.append(cube("stair_wall", (sx * (width / 2 + 0.06), top_y / 2, top_z / 2 + 1.2), (0.12, top_y + 0.2, top_z + 2.4), tile))
        o.append(tube("handrail", [(sx * (width / 2 - 0.08), -0.3, 0.95), (sx * (width / 2 - 0.08), top_y, top_z + 0.95)], 0.025, rail))
    # street level
    o.append(cube("sidewalk", (0, top_y + 8, top_z - 0.05), (24, 16, 0.1), walk))
    for sx in (-1, 1):
        o.append(cyl("lamp_post", (sx * (width / 2 + 0.3), top_y + 0.2, top_z + 1.1), 0.05, 2.2, rail))
        o.append(sphere("globe", (sx * (width / 2 + 0.3), top_y + 0.2, top_z + 2.3), 0.2, globe))
        # railing around the entrance
        o.append(tube("rail_top", [(sx * (width / 2 + 0.12), top_y - 2.5, top_z + 1.0), (sx * (width / 2 + 0.12), top_y, top_z + 1.0)], 0.03, rail))
    for (x, y) in [(-4.5, 5), (4.5, 4), (-7, 10), (7.5, 9)]:
        o.append(cyl("trunk", (x, top_y + y, top_z + 0.9), 0.12, 1.8, trunk))
        o.append(sphere("crown", (x, top_y + y, top_z + 2.4), 1.1, leaves, seg=16))
    for k, (x, w, h) in enumerate([(-7, 5, 9), (-1.5, 5.5, 11), (4.5, 5, 8), (9.5, 4.5, 10)]):
        o.append(cube("brownstone", (x, top_y + 15, top_z + h / 2), (w, 3, h), brick[k % 3]))
        for r in range(int(h / 1.6)):
            for c in range(3):
                o.append(cube("win", (x - w / 3 + c * w / 3, top_y + 13.48, top_z + 1.2 + r * 1.6), (0.7, 0.04, 0.9), window))
    sign = hanging_sign(["ABOUT  ·  CONTACT", "Exit to street  ↑"], w=2.4, h=0.7, letter=None, sizes=(0.16, 0.1), rod=0.6)
    o.append(group(sign, (0, -0.2, 2.75)))
    return o
