"""The way out of the mezzanine: the street stairs should read as leading up and outdoors.

- open_ceiling: the mezzanine ceiling with the stair opening cut out of it, so the stairs
  rise into the open instead of into a solid ceiling (replaces cutaway.mezz_lamps' ceiling).
- exit_sign: a black hanging sign at the foot of the stairs, "Exit / To street".
- night_light: cool moonlight falling down the stairwell, so the top of the stairs reads as
  outdoors at night against the warm lamps of the mezzanine.

The night sky beyond the top of the stairs is drawn by the site (scene.ts, exit_sky).
Existing props are not changed.
"""
from common import *
from props import cutaway


def open_ceiling(M, y0, y1, hole_y, half_x, x_half, z_top):
    """Ceiling boxes covering y0..y1 except x in (-half_x, half_x), y in hole_y."""
    m = M["ceiling"]
    h0, h1 = hole_y
    z0, z1 = z_top - 0.04, z_top
    out = []
    if h0 > y0:
        out.append(cutaway._box("mz_ceiling_a", -x_half, x_half, y0, h0, z0, z1, m))
    if y1 > h1:
        out.append(cutaway._box("mz_ceiling_b", -x_half, x_half, h1, y1, z0, z1, m))
    out.append(cutaway._box("mz_ceiling_l", -x_half, -half_x, h0, h1, z0, z1, m))
    out.append(cutaway._box("mz_ceiling_r", half_x, x_half, h0, h1, z0, z1, m))
    return out


def exit_sign(w=1.9, h=0.52, rod=0.2):
    """Hanging sign facing -Y, centered at the origin: an up arrow, then 'Exit' / 'To street'."""
    black = mat("sign_black", "#1c1c1c", 0.35, coat=0.6)
    white = mat("sign_white", "#ffffff", 0.3, emit="#ffffff", emit_str=1.0)
    green = mat("exit_green", "#00933c", 0.4, emit="#00933c", emit_str=0.6)
    steel = mat("rod_steel", "#a9adb3", 0.3, metal=0.85)
    o = [cube("exit_sign", (0, 0, 0), (w, 0.14, h), black, bevel=0.04)]
    # up arrow in a green disc
    ax = -w / 2 + 0.34
    o.append(cyl("exit_disc", (ax, -0.075, 0), 0.19, 0.01, green, rot=(R(90), 0, 0), verts=32))
    o.append(cube("exit_arrow", (ax, -0.085, -0.045), (0.05, 0.01, 0.17), white))
    # the arrow head: a triangle pointing up (a 3-sided prism turned to face -Y)
    o.append(cyl("exit_arrow_head", (ax, -0.085, 0.05), 0.1, 0.01, white, rot=(0, R(-90), R(90)), verts=3, smooth=False))
    # big, simple words: small thin letters don't survive the light bake
    o.append(text("Exit", (ax + 0.3, -0.08, h * 0.1), 0.22, "Inter_wght_800", white, extrude=0.003, align="LEFT"))
    o.append(text("To street", (ax + 0.3, -0.08, -h * 0.26), 0.13, "Inter_wght_800", white, extrude=0.003, align="LEFT"))
    for sx in (-w / 2 + 0.25, w / 2 - 0.25):
        o.append(cyl("rod", (sx, 0, h / 2 + rod / 2), 0.02, rod, steel, verts=12))
    return o


def night_light(x, y0, y1, z, half_x):
    """Cool moonlight from above the stair opening, pointing down the stairs."""
    return area((x, (y0 + y1) / 2, z), (R(-12), 0, 0), 2 * half_x, 260, (0.62, 0.72, 1.0), sy=(y1 - y0), name="moonlight")


def end_walls(M, y0, y1, x_half, z0, z1):
    """Tiled end walls for the mezzanine (y0 and y1), so walking to either end meets a wall
    with the same bands as the side walls, not the dark cut. Seen edge-on in the section view."""
    out = []
    # named fw_ so the bake gives them their own atlas (the site shows them with the fourth wall,
    # which is on whenever you are inside the mezzanine); this keeps the sign lettering sharp
    for name, y, sy in (("fw_mz_end_a", y0, 1), ("fw_mz_end_b", y1, -1)):
        yc = y + sy * 0.05
        out.append(cube(name, (0, y - sy * 0.05, (z0 + z1) / 2), (2 * x_half, 0.1, z1 - z0), M["tile"]))
        out.append(cube(name + "_band", (0, yc, z0 + 2.9), (2 * x_half, 0.04, 0.36), M["band"]))
        out.append(cube(name + "_trim", (0, yc, z0 + 2.6), (2 * x_half, 0.03, 0.1), M["trim"]))
        out.append(cube(name + "_trim2", (0, yc, z0 + 3.3), (2 * x_half, 0.03, 0.1), M["trim"]))
        out.append(cube(name + "_base", (0, yc, z0 + 0.12), (2 * x_half, 0.04, 0.24), M["base"]))
    return out
