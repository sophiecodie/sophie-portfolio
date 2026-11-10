"""Framed 'Choose your line' system map, modeled (not a texture): raised colored
lines on a cream panel, white station discs, labels. Faces -Y; built at origin.
"""
from common import *
from layout import LINES
from props.signage import bullet

# station positions on the panel (meters, panel is 3.6 x 2.2, origin at center)
STOPS = {
    "new-york-census": (-1.2, 0.55), "purchase-intent": (-0.3, 0.55), "college-app-atlas": (0.65, 0.2),
    "agent00hl7": (-1.2, -0.45), "dream-team": (-0.2, -0.1), "neurobiome": (1.25, -0.45),
    "folio": (1.25, 0.2), "reading": (1.25, 0.7),
}
LABELS = {
    "new-york-census": ("New York Census", (-1.2, 0.73)), "purchase-intent": ("Shopping ML", (-0.3, 0.73)),
    "college-app-atlas": ("College App Atlas", (0.65, 0.42)), "agent00hl7": ("Agent00HL7", (-1.2, -0.63)),
    "dream-team": ("Dream Team", (-0.2, -0.3)), "neurobiome": ("Neurobiome", (1.25, -0.63)),
    "folio": ("Folio", (1.5, 0.2)), "reading": ("Books & Writing", (1.25, 0.88)),
}
PATHS = {
    "data": [(-1.6, 0.55), (-1.2, 0.55), (-0.3, 0.55), (0.3, 0.55), (0.65, 0.2)],
    "health": [(-1.6, -0.45), (-1.2, -0.45), (-0.55, -0.45), (-0.2, -0.1), (0.3, -0.1), (0.65, -0.45), (1.25, -0.45)],
    "words": [(1.25, -0.75), (1.25, 0.2), (1.25, 0.7)],
}


def build():
    W, H = 3.6, 2.2
    frame = mat("map_frame", "#2f6b4f", 0.35, coat=0.5)
    panel = mat("map_panel", "#f7f0e1", 0.25, coat=0.6)
    water = mat("map_water", "#cfe3e8", 0.4)
    park = mat("map_park", "#dfe9cf", 0.6)
    ink = mat("map_ink", "#2a2219", 0.5)
    disc = mat("map_disc", "#ffffff", 0.3)
    hdr = mat("map_header", "#1c1c1c", 0.35)
    white = mat("sign_white", "#ffffff", 0.3, emit="#ffffff", emit_str=1.0)
    o = [cube("map_frame", (0, 0.03, 0), (W + 0.2, 0.06, H + 0.2), frame, bevel=0.02),
         cube("map_panel", (0, -0.005, 0), (W, 0.02, H), panel)]
    o.append(cube("map_water", (0, -0.017, -H / 2 + 0.17), (W, 0.004, 0.3), water))
    o.append(cube("map_park", (0.0, -0.017, 0.25), (0.45, 0.004, 0.5), park, bevel=0.05))
    for key, pts in PATHS.items():
        c = LINES[key]["color"]
        o.append(tube("line_" + key, [(x, -0.03, z) for x, z in pts], 0.028, mat("line_" + key, c, 0.35, coat=0.4)))
    for sid, (x, z) in STOPS.items():
        o.append(cyl("stop", (x, -0.045, z), 0.06, 0.03, disc, rot=(R(90), 0, 0), verts=24))
        o.append(cyl("stop_ring", (x, -0.04, z), 0.075, 0.025, ink, rot=(R(90), 0, 0), verts=24))
    for sid, (label, (x, z)) in LABELS.items():
        o.append(text(label, (x, -0.03, z), 0.075, "Inter_wght_800", ink, extrude=0.002))
    # header band with bullets
    o.append(cube("map_hdr", (0, 0.0, H / 2 + 0.36), (W + 0.2, 0.08, 0.42), hdr))
    o.append(text("CHOOSE YOUR LINE", (-W / 2 + 0.15, -0.05, H / 2 + 0.36), 0.2, "Inter_wght_800", white, extrude=0.003, align="LEFT"))
    for i, key in enumerate(["data", "health", "words"]):
        for b in bullet(LINES[key]["letter"], LINES[key]["color"], r=0.15, y=-0.05):
            b.location.x += W / 2 - 0.3 - (2 - i) * 0.42
            b.location.z += H / 2 + 0.36
            o.append(b)
    o.append(text("You are here", (-1.55, -0.03, -0.85), 0.06, "Inter_wght_500", ink, extrude=0.001, align="LEFT"))
    o.append(cyl("here", (-1.62, -0.04, -0.85), 0.035, 0.02, mat("here_red", "#d94f4f", 0.4), rot=(R(90), 0, 0), verts=16))
    return o
