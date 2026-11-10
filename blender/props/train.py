"""A friendly stainless subway car (generic, no real-world branding).

Faces -Y (front cab at y=0), body extends to +Y. Origin at rail-top center.
Materials are plain PBR colors so they export cleanly to glTF and are lit live
in the browser (the train moves, so it isn't baked).
"""
from common import *

L_CAR = 15.5


def car(front=True, back_cab=False, letter="S", stripe="#e8732c", seed=0):
    steel = mat("car_steel", "#c9ced3", 0.28, metal=0.9)
    rib = mat("car_rib", "#b7bcc2", 0.32, metal=0.9)
    roof = mat("car_roof", "#9aa0a6", 0.45, metal=0.6)
    dark = mat("car_dark", "#2b2b2e", 0.6)
    glass = mat("car_glass", "#5a4a3a", 0.1, emit="#ffd995", emit_str=0.6)
    stripe_m = mat("car_stripe_" + stripe, stripe, 0.35, coat=0.4)
    head = mat("car_headlight", "#fffbe8", 0.2, emit="#fff6d0", emit_str=20)
    tail = mat("car_marker", "#ffb36b", 0.3, emit="#ffa040", emit_str=6)
    W, H, Z0 = 2.7, 2.9, 0.35
    o = []
    o.append(cube("body", (0, L_CAR / 2, Z0 + H / 2), (W, L_CAR, H), steel, bevel=0.12, seg=4))
    o.append(cube("roof", (0, L_CAR / 2, Z0 + H + 0.04), (W - 0.5, L_CAR - 0.3, 0.16), roof, bevel=0.07))
    o.append(cube("skirt", (0, L_CAR / 2, Z0 + 0.12), (W - 0.2, L_CAR - 1.0, 0.35), dark))
    for y in (2.2, L_CAR - 2.2):
        o.append(cube("truck", (0, y, Z0 - 0.08), (2.1, 2.4, 0.4), dark))
        for dy in (-0.75, 0.75):
            for sx in (-0.72, 0.72):
                o.append(cyl("wheel", (sx, y + dy, Z0 - 0.06), 0.38, 0.12, dark, rot=(0, R(90), 0), verts=24))
    for sx in (-1, 1):
        x = sx * (W / 2 + 0.005)
        # horizontal ribs on the lower body
        for k in range(4):
            o.append(cube("rib", (x, L_CAR / 2, Z0 + 0.45 + k * 0.12), (0.02, L_CAR - 1.2, 0.035), rib))
        o.append(cube("stripe", (x, L_CAR / 2, Z0 + 1.15), (0.02, L_CAR - 0.8, 0.12), stripe_m))
        # 4 double doors with windows, windows between them
        for d in range(4):
            yd = 1.9 + d * (L_CAR - 3.8) / 3
            o.append(cube("door", (x, yd, Z0 + 1.15), (0.03, 1.3, 2.0), rib))
            o.append(cube("door_seam", (x + sx * 0.012, yd, Z0 + 1.15), (0.012, 0.02, 2.0), dark))
            for dy in (-0.32, 0.32):
                o.append(cube("door_win", (x + sx * 0.02, yd + dy, Z0 + 1.55), (0.012, 0.4, 0.7), glass, bevel=0.05))
            if d < 3:
                for wv in range(2):
                    yw = yd + 1.25 + wv * 1.15
                    o.append(cube("win", (x + sx * 0.012, yw, Z0 + 1.65), (0.012, 0.95, 0.75), glass, bevel=0.06))
    if front:
        o.append(cube("cab", (0, -0.02, Z0 + H / 2), (W - 0.1, 0.06, H - 0.2), steel, bevel=0.05))
        o.append(cube("cab_door", (0, -0.06, Z0 + 1.2), (0.7, 0.04, 2.0), rib))
        o.append(cube("cab_door_win", (0, -0.085, Z0 + 1.65), (0.42, 0.02, 0.7), glass, bevel=0.06))
        for sx in (-1, 1):
            o.append(cube("cab_win", (sx * 0.85, -0.07, Z0 + 1.7), (0.7, 0.02, 0.75), glass, bevel=0.06))
            o.append(cyl("headlight", (sx * 0.85, -0.08, Z0 + 0.65), 0.1, 0.04, head, rot=(R(90), 0, 0), verts=20))
            o.append(cyl("marker", (sx * 0.85, -0.08, Z0 + 0.95), 0.06, 0.03, tail, rot=(R(90), 0, 0), verts=16))
        o.append(cube("bumper", (0, -0.12, Z0 + 0.3), (W - 0.3, 0.2, 0.25), dark))
        # route bullet in the cab window area
        o.append(cyl("route_disc", (0.85, -0.09, Z0 + 1.7), 0.2, 0.02, mat("route_disc", stripe, 0.35, emit=stripe, emit_str=1.0), rot=(R(90), 0, 0), verts=32))
        o.append(text(letter, (0.85, -0.1, Z0 + 1.7), 0.24, "Inter_wght_800", mat("route_white", "#ffffff", 0.3, emit="#ffffff", emit_str=1.5), extrude=0.003))
    return o
