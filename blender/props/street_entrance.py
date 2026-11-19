"""The street-level subway entrance and the "About me" chalkboard, for the dollhouse station.

Both are built in local coordinates, with z = 0 on the sidewalk:

  build_entrance(): centered on the stair opening. The stairs go down toward -Y, so the
      open end (where you step in) is +Y. Cast-iron railing on a granite curb around the
      other three sides, two globe lamps at the open end, "Subway" panels on the sides.
  build_chalkboard(): a sidewalk A-frame chalkboard with hand-lettered About-me chalk
      text, its lettered side facing -X (the camera), centered on the origin. It is the
      About entry.

The railing is open (balusters, no solid wall), so the stairs stay visible from the cut.
Everything stays under about 3 m so it fits the street band of the overview.
Nothing here changes the existing props; colors reuse the station's greens and the
site's line colors (Data red, Health green, Words purple).
"""
import math
import bpy
from common import *

GREEN = "#2f6b4f"            # same as rail_green in props/stairs.py
LINES = (("D", "#c8402f"), ("H", "#2f8a4c"), ("W", "#7d4aa8"))


def _mats():
    return {
        "iron": mat("entrance_iron", GREEN, 0.38, metal=0.3, coat=0.5),
        "granite": noise_mat("entrance_granite", "#4e5552", "#646b67", scale=14, rough=0.6),
        "globe": mat("entrance_globe", "#8fe3b0", 0.15, emit="#7fdca2", emit_str=2.5),
        "brass": mat("entrance_brass", "#d8b25a", 0.3, metal=0.9),
        "sign": mat("sign_black", "#1c1c1c", 0.35, coat=0.6),
        "white": mat("sign_white", "#ffffff", 0.3, emit="#ffffff", emit_str=1.0),
    }


# ------------------------------------------------------------------ pieces
def _fence(M, a, b, z0=0.28, z1=1.12, gap=0.13):
    """A run of railing from a to b (x, y): top and bottom rails, round balusters."""
    (ax, ay), (bx, by) = a, b
    L = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
    o = [tube("ent_rail_top", [(ax, ay, z1), (bx, by, z1)], 0.035, M["iron"]),
         tube("ent_rail_mid", [(ax, ay, z1 - 0.14), (bx, by, z1 - 0.14)], 0.018, M["iron"]),
         tube("ent_rail_bot", [(ax, ay, z0 + 0.06), (bx, by, z0 + 0.06)], 0.022, M["iron"])]
    n = max(2, int(L / gap))
    for i in range(1, n):
        t = i / n
        o.append(cyl("ent_baluster", (ax + (bx - ax) * t, ay + (by - ay) * t, (z0 + z1) / 2),
                     0.012, z1 - z0, M["iron"], verts=8))
    return o


def _newel(M, x, y, h=1.22):
    """A square post with a stepped cap and a small ball finial."""
    return [cube("ent_newel", (x, y, 0.28 + h / 2 - 0.14), (0.11, 0.11, h - 0.28 + 0.28), M["iron"], bevel=0.01),
            cube("ent_newel_cap", (x, y, h + 0.03), (0.15, 0.15, 0.05), M["iron"], bevel=0.01),
            sphere("ent_finial", (x, y, h + 0.1), 0.05, M["iron"], seg=16)]


def _lamp(M, x, y, h=2.55):
    """A tall fluted lamp post with a glowing globe (and a light so it bakes a warm pool)."""
    o = [cyl("ent_lamp_base", (x, y, 0.35), 0.11, 0.7, M["iron"], verts=8),
         cyl("ent_lamp_collar", (x, y, 0.72), 0.13, 0.05, M["iron"], verts=8),
         cyl("ent_lamp_post", (x, y, (0.72 + h) / 2), 0.05, h - 0.72, M["iron"], verts=12),
         cyl("ent_lamp_cup", (x, y, h + 0.02), 0.1, 0.06, M["brass"], verts=24),
         sphere("ent_globe", (x, y, h + 0.24), 0.21, M["globe"], seg=24),
         sphere("ent_globe_cap", (x, y, h + 0.46), 0.04, M["iron"], seg=12)]
    o.append(point((x, y, h + 0.24), 60, (0.82, 1.0, 0.88), r=0.2))
    return o


def _panel(M, w, h, title, size):
    """A black enamel panel facing -Y at the origin: title on the left, line bullets on the right."""
    o = [cube("ent_panel", (0, 0, 0), (w, 0.03, h), M["sign"], bevel=0.008),
         text(title, (-w / 2 + 0.1, -0.017, -size * 0.05), size, "Inter_wght_800", M["white"],
              extrude=0.002, align="LEFT")]
    r = h * 0.26
    for k, (letter, color) in enumerate(LINES):
        x = w / 2 - 0.1 - r - (len(LINES) - 1 - k) * (2 * r + 0.05)
        o.append(cyl("ent_bullet", (x, -0.018, 0), r, 0.006,
                     mat("bullet_" + color, color, 0.35, coat=0.4), rot=(R(90), 0, 0), verts=32))
        o.append(text(letter, (x, -0.022, 0), r * 1.15, "Inter_wght_800", M["white"], extrude=0.001))
    return o


# ------------------------------------------------------------------ the entrance
def build_entrance(half_open=1.5, y0=-3.4, y1=3.4):
    """Railing around a stair opening of half width half_open from y0 to y1 (open at +Y)."""
    M = _mats()
    xo = half_open + 0.14                       # railing line, just outside the opening
    ya, yb = y0 - 0.14, y1
    o = []
    # granite curb: two sides and the closed (-Y) end
    for sx in (-1, 1):
        o.append(cube("ent_curb", (sx * xo, (ya + yb) / 2, 0.14), (0.24, yb - ya + 0.24, 0.28), M["granite"], bevel=0.02))
    o.append(cube("ent_curb", (0, ya, 0.14), (2 * xo + 0.24, 0.24, 0.28), M["granite"], bevel=0.02))
    # railing runs, split by newel posts every ~2.3 m
    posts_y = [ya + (yb - ya) * t for t in (0, 1 / 3, 2 / 3, 1)]
    for sx in (-1, 1):
        x = sx * xo
        for p, q in zip(posts_y, posts_y[1:]):
            o += _fence(M, (x, p), (x, q))
        for p in posts_y[1:-1]:
            o += _newel(M, x, p)
    o += _fence(M, (-xo, ya), (0, ya)) + _fence(M, (0, ya), (xo, ya))
    o += _newel(M, -xo, ya) + _newel(M, xo, ya) + _newel(M, 0, ya)
    # the two lamps mark the way in
    for sx in (-1, 1):
        o += _lamp(M, sx * xo, yb)
    # "Subway" panels hung on the outside of both side railings, readable from outside
    for sx in (-1, 1):
        panel = _panel(M, 2.0, 0.42, "Subway", 0.24)
        o.append(group(panel, (sx * (xo + 0.05), (ya + yb) / 2, 0.86), rz=-90 if sx < 0 else 90, name="ent_panel_g"))
    return o


# ------------------------------------------------------------------ the chalkboard
CHALK_FONT = "CaveatBrush_Regular"      # Caveat Brush, Google Fonts, SIL Open Font License


def _chalk_mats():
    return {
        "board": noise_mat("chalkboard", "#1f2426", "#2e3538", scale=3, rough=0.92, detail=4),
        "wood": noise_mat("chalk_wood", "#a8774a", "#c4935f", scale=6, rough=0.7),
        "white": noise_mat("chalk_white", "#ece8dc", "#fbf8ef", scale=40, rough=0.95),
        "yellow": mat("chalk_yellow", "#f3d36b", 0.95),
        "pink": mat("chalk_pink", "#f2a7b6", 0.95),
        "brass": mat("entrance_brass", "#d8b25a", 0.3, metal=0.9),
        "line": [mat("chalk_" + c, c, 0.95) for c in ("#ef8a7a", "#86c995", "#b99be0")],   # soft D/H/W
    }


def _chalk_panel(C, L, w, words):
    """One side of the A-frame, standing in the YZ plane from z = 0 to L, face toward -X.
    Wooden frame with short legs, chalkboard inside, and (front only) the chalk lettering."""
    t, b = 0.045, 0.065                                   # frame thickness (x) and bar width
    foot = 0.2                                            # legs below the bottom rail
    o = []
    for sy in (-1, 1):
        o.append(cube("ch_stile", (0, sy * (w / 2 - b / 2), L / 2), (t, b, L), C["wood"], bevel=0.008))
    o.append(cube("ch_rail_top", (0, 0, L - b / 2), (t, w - 2 * b, b), C["wood"], bevel=0.008))
    o.append(cube("ch_rail_bot", (0, 0, foot + b / 2), (t, w - 2 * b, b), C["wood"], bevel=0.008))
    z0, z1 = foot + b, L - b
    o.append(cube("ch_board", (0, 0, (z0 + z1) / 2), (0.018, w - 2 * b + 0.01, z1 - z0), C["board"]))
    if not words:
        return o
    fx = -0.012
    rot = (R(90), 0, R(-90))                              # facing -X, reading toward -Y

    def chalk(body, v, size, m, u=0.0, align="CENTER"):
        o.append(text(body, (fx, -u, v), size, CHALK_FONT, m, extrude=0.0, rot=rot, align=align))

    top = z1 - 0.06
    chalk("Hi! I'm", top - 0.1, 0.15, C["white"])
    chalk("SOPHIE", top - 0.32, 0.27, C["yellow"])
    for k, m in enumerate(C["line"]):                     # three colored chalk underlines
        u = -0.28 + k * 0.28
        o.append(tube("ch_under", [(fx, -(u - 0.12), top - 0.5 - k * 0.006),
                                   (fx, -(u + 0.12), top - 0.49 + k * 0.006)], 0.008, m))
    chalk("CS + Neuro @ Duke", top - 0.66, 0.1, C["white"])
    chalk("I build AI & data", top - 0.82, 0.085, C["white"])
    chalk("tools for medicine", top - 0.94, 0.085, C["white"])
    chalk("& cities :)", top - 1.06, 0.085, C["white"])
    chalk("about me", top - 1.26, 0.13, C["pink"], u=-0.1)
    av = top - 1.255                                      # a hand-drawn chalk arrow after it
    o.append(tube("ch_arrow", [(fx, -0.2, av), (fx, -0.4, av + 0.006)], 0.006, C["pink"]))
    for dv in (0.045, -0.045):
        o.append(tube("ch_arrow", [(fx, -0.4, av + 0.006), (fx, -0.355, av + dv)], 0.006, C["pink"]))
    # a little chalk sun in the top corner
    cu, cv = w / 2 - 0.2, top - 0.12
    ring = [(fx, -(cu + 0.05 * math.cos(a / 12 * 2 * math.pi)), cv + 0.05 * math.sin(a / 12 * 2 * math.pi)) for a in range(13)]
    o.append(tube("ch_sun", ring, 0.006, C["yellow"]))
    for a in range(8):
        ang = a / 8 * 2 * math.pi
        o.append(tube("ch_ray", [(fx, -(cu + 0.075 * math.cos(ang)), cv + 0.075 * math.sin(ang)),
                                 (fx, -(cu + 0.11 * math.cos(ang)), cv + 0.11 * math.sin(ang))], 0.005, C["yellow"]))
    return o


def build_chalkboard(h=1.8, w=1.2, spread=0.42):
    """A sidewalk A-frame chalkboard (sandwich board) with the About-me lettering.
    It stands on z = 0 centered on the origin; the lettered side faces -X (the camera)."""
    C = _chalk_mats()
    a = math.atan2(spread, h)
    L = (h * h + spread * spread) ** 0.5
    o = []
    for side in (-1, 1):                                  # -1: front (lettered), +1: back
        e = link(bpy.data.objects.new("ch_side", None))
        for p in _chalk_panel(C, L, w, words=(side < 0)):
            p.parent = e
        e.location = (side * spread, 0, 0)
        e.rotation_euler = (0, -side * a, 0)
        o.append(e)
    # hinges at the top and a little chain holding the legs
    for sy in (-1, 1):
        o.append(cyl("ch_hinge", (0, sy * (w / 2 - 0.1), h + 0.01), 0.018, 0.09, C["brass"], rot=(R(90), 0, 0), verts=12))
    for sy in (-1, 1):
        o.append(tube("ch_chain", [(-spread * 0.45, sy * (w / 2 - 0.03), h * 0.55),
                                   (0, sy * (w / 2 - 0.03), h * 0.5),
                                   (spread * 0.45, sy * (w / 2 - 0.03), h * 0.55)], 0.006, C["brass"]))
    return o


# ------------------------------------------------------------------ the pavement
def flagstone_mat(name="street_flags", size=1.5, joint=0.025,
                  a="#7f8382", b="#8e9291", grout="#45494a"):
    """Grey concrete flags in world space (size m squares, dark joints), dusk-dark so the
    street reads as night next to the background. Same 1.5 m grid as the background's pavement."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; n, L = nt.nodes, nt.links
    p = n["Principled BSDF"]
    geo = n.new("ShaderNodeNewGeometry")
    sep = n.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sep.inputs[0])

    def op(o, x, y=None):
        k = n.new("ShaderNodeMath"); k.operation = o
        for i, v in enumerate((x, y)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                k.inputs[i].default_value = v
            else:
                L.new(v, k.inputs[i])
        return k.outputs[0]

    def edge(c):           # 1 near a joint line, 0 inside a flag
        f = op("FRACT", op("DIVIDE", c, size))
        d = op("MINIMUM", f, op("SUBTRACT", 1.0, f))
        return op("LESS_THAN", d, joint / size)

    mask = op("MAXIMUM", edge(sep.outputs["X"]), edge(sep.outputs["Y"]))
    nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3; nz.inputs["Detail"].default_value = 6
    L.new(geo.outputs["Position"], nz.inputs["Vector"])
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35; ramp.color_ramp.elements[0].color = (*col(a), 1)
    ramp.color_ramp.elements[1].position = 0.65; ramp.color_ramp.elements[1].color = (*col(b), 1)
    L.new(nz.outputs["Fac"], ramp.inputs[0])
    mix = n.new("ShaderNodeMix"); mix.data_type = "RGBA"
    L.new(mask, mix.inputs["Factor"]); L.new(ramp.outputs[0], mix.inputs[6])
    mix.inputs[7].default_value = (*col(grout), 1)
    L.new(mix.outputs[2], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.85
    return m


def build_pavement(y0, y1, half_w, hole_y, hole_half, z0, z1):
    """A flagstone skin over the street slab's walk layer (z0..z1), from y0 to y1 and
    |x| <= half_w, open over the stairs. It sits a hair proud of the old surface and
    past its cut face, so it replaces the beige sidewalk without editing cutaway.py.
    World coordinates (no group)."""
    m = flagstone_mat()
    e = 0.005
    hy0, hy1 = hole_y
    xa, xb, za, zb = -half_w - e, half_w + e, z0 - e, z1 + e

    def box(x0, x1, ya, yb):
        return cube("street_flags", ((x0 + x1) / 2, (ya + yb) / 2, (za + zb) / 2), (x1 - x0, yb - ya, zb - za), m)

    o = []
    if hy0 > y0:
        o.append(box(xa, xb, y0 - e, hy0))
    if y1 > hy1:
        o.append(box(xa, xb, hy1, y1 + e))
    o.append(box(xa, -hole_half, hy0, hy1))
    o.append(box(hole_half, xb, hy0, hy1))
    return o
