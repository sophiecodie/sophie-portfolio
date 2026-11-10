"""Small platform props: wooden bench, friendly trash can, project lightbox."""
from common import *
from props.signage import bullet


def bench(length=2.2):
    """Bench along Y, seat facing -X (back against +X). Origin at floor center."""
    wood = noise_mat("bench_wood", "#9a6640", "#b07a4a", scale=25, rough=0.5)
    iron = mat("bench_iron", "#2b2b2b", 0.45, metal=0.5)
    o = []
    for k in range(3):
        o.append(cube("slat", (-0.12 + k * 0.13, 0, 0.45), (0.11, length, 0.04), wood, bevel=0.008))
    for k in range(2):
        o.append(cube("back_slat", (0.2, 0, 0.62 + k * 0.14), (0.04, length, 0.1), wood, bevel=0.008))
    for y in (-length / 2 + 0.2, length / 2 - 0.2):
        o.append(cube("leg", (0.02, y, 0.22), (0.42, 0.05, 0.44), iron))
        o.append(cube("back_leg", (0.2, y, 0.6), (0.04, 0.05, 0.4), iron))
    return o


def trash_can():
    green = mat("can_green", "#2f6b4f", 0.45, coat=0.3)
    steel = mat("can_steel", "#b4b8bd", 0.35, metal=0.8)
    return [cyl("can", (0, 0, 0.45), 0.25, 0.9, green, verts=24),
            cyl("can_lid", (0, 0, 0.92), 0.27, 0.05, steel, verts=24),
            cyl("can_band", (0, 0, 0.6), 0.255, 0.04, steel, verts=24)]


def lightbox(title, line, letter, color, w=1.6, h=0.9):
    """Glowing info panel under each project's mosaic tile. Faces -Y."""
    frame = mat("lightbox_frame", "#2f6b4f", 0.35, coat=0.5)
    glow = mat("lightbox_glow", "#fff8ea", 0.3, emit="#fff1d6", emit_str=0.35)
    ink = mat("lightbox_ink", "#2a2219", 0.5)
    soft = mat("lightbox_soft", "#7a6a55", 0.5)
    o = [cube("lb_frame", (0, 0.02, 0), (w + 0.1, 0.08, h + 0.1), frame, bevel=0.015),
         cube("lb_face", (0, -0.025, 0), (w, 0.01, h), glow)]
    for b in bullet(letter, color, r=0.13, y=-0.035):
        b.location.x += -w / 2 + 0.22; b.location.z += h / 2 - 0.22
        o.append(b)
    o.append(text(title, (-w / 2 + 0.42, -0.035, h / 2 - 0.22), 0.1, "Fraunces_wght_700", ink, extrude=0.002, align="LEFT"))
    o.append(text(line, (-w / 2 + 0.12, -0.035, -0.02), 0.055, "Inter_wght_500", soft, extrude=0.001, align="LEFT", valign="TOP"))
    o.append(text("Tap to step inside  →", (-w / 2 + 0.12, -0.035, -h / 2 + 0.12), 0.055, "Inter_wght_800",
                  mat("lb_" + color, color, 0.4), extrude=0.001, align="LEFT"))
    return o
