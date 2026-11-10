"""Hanging 'Next trains' arrivals board. Rows glow amber; faces -Y at origin."""
from common import *

MINUTES = ["Arriving", "2 min", "4 min", "6 min", "9 min", "12 min", "15 min", "Express"]


def build(rows):
    """rows: list of (title, color) in display order."""
    W, H = 3.6, 2.3
    board = mat("board_body", "#1b2633", 0.3, coat=0.6)
    face = mat("board_face", "#0f1720", 0.5)
    amber = mat("board_amber", "#ffcf6b", 0.4, emit="#ffc04d", emit_str=4)
    green = mat("board_green", "#8ee6a8", 0.4, emit="#7ee09a", emit_str=4)
    label = mat("board_label", "#9fb2c6", 0.5, emit="#9fb2c6", emit_str=1.2)
    steel = mat("rod_steel", "#a9adb3", 0.3, metal=0.85)
    o = [cube("board", (0, 0, 0), (W, 0.3, H), board, bevel=0.06),
         cube("board_face", (0, -0.155, 0), (W - 0.2, 0.01, H - 0.2), face)]
    o.append(text("NEXT TRAINS", (-W / 2 + 0.25, -0.165, H / 2 - 0.3), 0.13, "Inter_wght_800", label, extrude=0.003, align="LEFT"))
    o.append(text("MIN", (W / 2 - 0.25, -0.165, H / 2 - 0.3), 0.1, "Inter_wght_800", label, extrude=0.003, align="RIGHT"))
    for i, (title, color) in enumerate(rows):
        z = H / 2 - 0.55 - i * 0.215
        o.append(cyl("row_bullet", (-W / 2 + 0.32, -0.162, z), 0.075, 0.01,
                     mat("glow_" + color, color, 0.4, emit=color, emit_str=1.5), rot=(R(90), 0, 0), verts=24))
        o.append(text(title, (-W / 2 + 0.48, -0.165, z), 0.115, "Inter_wght_500", amber, extrude=0.003, align="LEFT"))
        o.append(text(MINUTES[i % len(MINUTES)], (W / 2 - 0.25, -0.165, z), 0.115, "Inter_wght_500",
                      green if i == 0 else amber, extrude=0.003, align="RIGHT"))
    for sx in (-W / 2 + 0.4, W / 2 - 0.4):
        o.append(cyl("rod", (sx, 0, H / 2 + 0.35), 0.03, 0.7, steel, verts=12))
    return o
