"""Signs: hanging black station signs, mosaic name tiles, route bullets, posters.

All built facing -Y at the origin; place them with common.group(...).
"""
from common import *

WHITE = None


def _white():
    return mat("sign_white", "#ffffff", 0.3, emit="#ffffff", emit_str=1.0)


def bullet(letter, color, r=0.2, depth=0.02, y=0.0):
    """A round route bullet, face toward -Y."""
    return [cyl("bullet", (0, y, 0), r, depth, mat("bullet_" + color, color, 0.35, coat=0.4), rot=(R(90), 0, 0), verts=48),
            text(letter, (0, y - depth / 2 - 0.002, 0), r * 1.15, "Inter_wght_800", _white(), extrude=0.002)]


def hanging_sign(lines, w=3.4, h=0.95, letter="S", color="#e8732c", sizes=(0.34, 0.16),
                 fonts=("Inter_wght_800", "Inter_wght_500"), rod=1.0):
    signm = mat("sign_black", "#1c1c1c", 0.35, coat=0.6)
    gold = mat("sign_gold", "#f2c24c", 0.3, emit="#f2c24c", emit_str=0.4)
    steel = mat("rod_steel", "#a9adb3", 0.3, metal=0.85)
    o = [cube("sign", (0, 0, 0), (w, 0.2, h), signm, bevel=0.05),
         cube("sign_line", (0, -0.105, 0), (w - 0.18, 0.01, h - 0.12), gold),
         cube("sign_in", (0, -0.112, 0), (w - 0.26, 0.01, h - 0.2), signm)]
    off = 0.2 if letter else 0
    if len(lines) == 2:
        o.append(text(lines[0], (off, -0.12, h * 0.13), sizes[0], fonts[0], _white(), extrude=0.004))
        o.append(text(lines[1], (off, -0.12, -h * 0.24), sizes[1], fonts[1], _white(), extrude=0.004, spacing=1.6))
    else:
        o.append(text(lines[0], (off, -0.12, 0), sizes[0], fonts[0], _white(), extrude=0.004))
    if letter:
        for b in bullet(letter, color, r=min(0.2, h * 0.24), y=-0.12):
            b.location.x += -w / 2 + 0.38
            o.append(b)
    for sx in (-w / 2 + 0.3, w / 2 - 0.3):
        o.append(cyl("rod", (sx, 0, h / 2 + rod / 2), 0.022, rod, steel, verts=12))
    return o


def mosaic_tile(name, w=3.6, h=0.95, size=0.3, field=("#8a3b26", "#9c4a30", "#7c321f", "#a5543a"),
                border=("#4e7a5c", "#5c8a68", "#45704f", "#6a9876")):
    """A Beaux-Arts style mosaic name panel, flat against a wall facing -Y."""
    green = mosaic_mat("mosaic_border", list(border), grout="#33433a", tess=0.014)
    tan = mosaic_mat("mosaic_rim", ["#d9a066", "#c98a52", "#e0b07a", "#cf955c"], grout="#8a6a48", tess=0.011)
    terra = mosaic_mat("mosaic_field_" + field[0], list(field), grout="#4a2a1e", tess=0.011)
    ivory = mosaic_mat("mosaic_ivory", ["#fbf6ea", "#f1e9d6", "#fffdf6", "#e9dfc8"], grout="#9c8e78", tess=0.012, rough=0.25)
    o = [cube("m_border", (0, 0, 0), (w, 0.04, h), green),
         cube("m_rim", (0, -0.02, 0), (w - 0.24, 0.03, h - 0.24), tan),
         cube("m_field", (0, -0.035, 0), (w - 0.36, 0.03, h - 0.36), terra)]
    o.append(text(name.upper(), (0, -0.052, 0), size, "Cinzel_wght_700", ivory, extrude=0.008, spacing=1.05))
    return o


def poster(title, sub, color, w=1.05, h=1.4, shape=0):
    """A cheerful geometric poster in a frame (no image textures needed)."""
    frame = mat("poster_frame", "#d7c7ab", 0.45)
    bg = mat("poster_" + color, color, 0.5)
    lighter = mat("poster_soft", "#fff6e6", 0.6)
    o = [cube("p_frame", (0, 0.01, 0), (w + 0.12, 0.03, h + 0.12), frame),
         cube("p_bg", (0, -0.008, 0), (w, 0.01, h), bg)]
    if shape == 0:
        o.append(cyl("p_circle", (w * 0.18, -0.016, h * 0.18), w * 0.32, 0.006, lighter, rot=(R(90), 0, 0), verts=48))
    elif shape == 1:
        s = cube("p_square", (-w * 0.12, -0.016, h * 0.2), (w * 0.5, 0.006, w * 0.5), lighter); s.rotation_euler = (0, R(15), 0)
    else:
        for k in range(3):
            o.append(cube("p_bar", (0, -0.016, h * 0.32 - k * 0.16), (w * 0.7, 0.006, 0.07), lighter))
    if shape == 1:
        o.append(s)
    o.append(text(title, (-w / 2 + 0.08, -0.02, -h * 0.28), 0.1, "Fraunces_wght_700", _white(), extrude=0.002, align="LEFT"))
    o.append(text(sub, (-w / 2 + 0.08, -0.02, -h * 0.4), 0.05, "Inter_wght_500", _white(), extrude=0.001, align="LEFT"))
    return o
