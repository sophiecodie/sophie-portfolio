"""R160-style front end (from Sophie's East Broadway photo): a silver fiberglass bonnet,
the operator's window on the left with a black surround, the storm door in the middle
with its window and black V, decals on the right, round headlights low in each corner,
red markers, and the round LED route sign up top. Generic decals only (no MTA marks).

cab_r160(t, l, pal, route, seed) adds parts to the trim and lights Parts and returns the
text objects (converted to meshes at export). The route letter object keeps the name
T_<route> and the car_route_* materials, so the site can recolor it per line.
"""
import math
from props.train_util import *
from common import text, mat

Y = 0.0   # the front face of the shell


def _mats():
    return dict(
        bonnet=mat("car_bonnet", "#c3c7cc", 0.32, metal=0.65),
        mask=mat("car_mask_black", "#121214", 0.35, coat=0.5),
        dark_glass=mat("car_front_glass", "#1d2830", 0.04, coat=1.0),
        flag_red=mat("decal_red", "#c8202f", 0.5),
        flag_white=mat("decal_white", "#f3f1ea", 0.5),
        flag_blue=mat("decal_blue", "#24306e", 0.5),
        roundel=mat("decal_roundel", "#1f4aa8", 0.45),
        tail=mat("car_tail_red", "#ff3030", 0.3, emit="#ff2020", emit_str=4),
    )


def _stroke(t, m, a, b, w, y):
    """A flat strip from point a to b (x, z) on the front face."""
    (x0, z0), (x1, z1) = a, b
    L = math.hypot(x1 - x0, z1 - z0)
    th = math.atan2(-(z1 - z0), x1 - x0)
    t.box(((x0 + x1) / 2, y, (z0 + z1) / 2), (L, 0.01, w), m, rot=(0, th, 0))


def cab_r160(t, l, pal, route, seed):
    M = _mats()
    texts = []
    # bonnet skin over the flat end of the shell, following its outline
    t.prism(profile_front(0.02), "y", (0, Y - 0.012, 0), 0.024, M["bonnet"])
    f = Y - 0.026          # front surface for applied parts
    # operator's window (viewer's left) with a black surround
    t.box((-0.78, f, 2.06), (0.92, 0.01, 1.26), M["mask"])
    t.box((-0.78, f - 0.008, 2.07), (0.8, 0.008, 1.1), M["dark_glass"])
    # windshield wiper parked along the bottom
    t.box((-0.8, f - 0.02, 1.58), (0.6, 0.012, 0.018), pal["rubber"], rot=(0, math.radians(8), 0))
    # storm door: silver leaf in a black frame, tall window, the black V below it
    t.box((0, f, 1.5), (0.84, 0.01, 2.5), M["mask"])
    t.box((0, f - 0.008, 1.5), (0.72, 0.01, 2.38), M["bonnet"])
    t.box((0, f - 0.016, 2.08), (0.52, 0.008, 0.98), M["mask"])
    t.box((0, f - 0.022, 2.08), (0.46, 0.008, 0.9), M["dark_glass"])
    _stroke(t, M["mask"], (-0.3, 1.55), (0.0, 0.92), 0.05, f - 0.018)
    _stroke(t, M["mask"], (0.3, 1.55), (0.0, 0.92), 0.05, f - 0.018)
    t.box((0.27, f - 0.02, 1.35), (0.04, 0.02, 0.16), pal["steel"])       # door handle
    # top band: route sign housing and a small LED destination strip
    t.box((0, f, 3.05), (1.9, 0.01, 0.36), M["mask"])
    t.prism(circle(0.165, 32), "y", (-0.42, f - 0.01, 3.05), 0.012, pal["board"])
    l.prism(circle(0.145, 32), "y", (-0.42, f - 0.02, 3.05), 0.008, pal["route"])
    texts.append(text(route, (-0.42, f - 0.028, 3.05), 0.21, "Inter_wght_800", pal["route_white"]))
    t.box((0.4, f - 0.008, 3.05), (0.9, 0.008, 0.17), pal["board"])
    texts.append(text("PORTFOLIO", (0.4, f - 0.016, 3.05), 0.08, "Inter_wght_800", pal["dest"]))
    # decals on the right: a flag and a round line roundel
    fx, fz, fw, fh = 0.8, 2.5, 0.5, 0.3
    for k in range(7):
        t.box((fx, f - 0.004, fz + fh / 2 - fh / 13 * (2 * k + 0.5)), (fw, 0.004, fh / 13), M["flag_red"])
    t.box((fx, f - 0.002, fz), (fw, 0.004, fh), M["flag_white"])
    t.box((fx - fw / 2 + 0.11, f - 0.008, fz + fh / 2 - 0.08), (0.22, 0.004, 0.16), M["flag_blue"])
    t.prism(circle(0.17, 32), "y", (fx, f - 0.004, 1.98), 0.006, M["flag_white"])
    t.prism(circle(0.155, 32), "y", (fx, f - 0.008, 1.98), 0.006, M["roundel"])
    texts.append(text("Sophie Shih", (fx, f - 0.013, 2.01), 0.042, "Inter_wght_800", pal["route_white"]))
    texts.append(text("Subway", (fx, f - 0.013, 1.95), 0.042, "Inter_wght_500", pal["route_white"]))
    # headlights low in each corner: a big lamp and a smaller one in a black pod
    for sx in (-1, 1):
        t.box((sx * 0.9, f, 0.72), (0.5, 0.012, 0.26), M["mask"])
        l.prism(circle(0.085, 24), "y", (sx * 1.03, f - 0.01, 0.72), 0.01, pal["head"])
        l.prism(circle(0.055, 20), "y", (sx * 0.8, f - 0.01, 0.72), 0.01, pal["head"])
        l.prism(circle(0.035, 14), "y", (sx * 1.12, f - 0.01, 0.98), 0.01, M["tail"])
        l.prism(circle(0.035, 14), "y", (sx * 1.12, f - 0.01, 2.85), 0.01, pal["amber"])
    # car number under the operator's window
    t.box((-0.78, f - 0.004, 1.25), (0.26, 0.006, 0.1), pal["plate"])
    texts.append(text(str(8600 + (seed * 137) % 400), (-0.78, f - 0.009, 1.25), 0.07, "Inter_wght_800", pal["rubber"]))
    # anti-climber ribs, bumper, coupler
    t.box((0, f - 0.05, 0.36), (2.4, 0.1, 0.16), pal["under"])
    for k in range(3):
        t.box((0, f - 0.105, 0.31 + k * 0.05), (2.3, 0.012, 0.02), pal["steel_dark"])
    t.box((0, f - 0.12, 0.18), (0.24, 0.24, 0.13), pal["under"])
    # grab irons and the step beside the door
    for sx in (-1, 1):
        t.prism(circle(0.014, 8), "z", (sx * 0.52, f - 0.05, 1.7), 0.9, pal["steel"])
    return texts


def profile_front(inset):
    """The end outline of the shell (x, z), slightly inset, for the bonnet skin."""
    from props.train_body import profile
    pts = profile(0.0)
    cx = 0.0
    cz = sum(z for _, z in pts) / len(pts)
    return [(x - math.copysign(inset, x) if abs(x) > inset else x, z if z < cz else z - inset * (z - cz) / max(1e-6, (3.6 - cz)))
            for x, z in pts]
