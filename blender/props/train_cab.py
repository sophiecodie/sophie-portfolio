"""Front cab (front car only), and the car ends: grab handles, the coupler and the
rubber diaphragm that bridges the gap to the next car."""
from props.train_util import *
from common import text


def cab(t, l, pal, route, seed):
    """Destination board, round route sign, lights, wiper, number plate, bumper.

    Returns the text objects, which are converted to meshes at export.
    """
    texts = []
    # amber destination board above the storm window
    t.box((0, -0.02, 2.95), (1.5, 0.03, 0.26), pal["board"])
    texts.append(text("SOPHIE SHIH · PORTFOLIO", (0, -0.045, 2.95), 0.085, "Inter_wght_800", pal["dest"]))
    # round route sign with a backlit bullet, on the side opposite the motorman's window
    t.prism(circle(0.27, 28), "y", (0.85, -0.02, 2.0), 0.04, pal["board"])
    l.prism(circle(0.22, 28), "y", (0.85, -0.045, 2.0), 0.02, pal["route"])
    texts.append(text(route, (0.85, -0.07, 2.0), 0.3, "Inter_wght_800", pal["route_white"]))
    # headlights and marker lights
    for sx in (-1, 1):
        l.prism(circle(0.09, 20), "y", (sx * 0.6, -0.03, 0.9), 0.04, pal["head"])
        l.prism(circle(0.035, 12), "y", (sx * 1.2, -0.02, 2.6), 0.03, pal["amber"])
    # windshield wiper arm on the motorman's window
    t.box((-0.9, -0.03, 1.55), (0.55, 0.02, 0.02), pal["rubber"], rot=(0, R(25), 0))
    # number plate on the storm door
    t.box((0, -0.02, 0.7), (0.24, 0.02, 0.1), pal["plate"])
    texts.append(text(str(1000 + (seed * 137) % 9000), (0, -0.035, 0.7), 0.07, "Inter_wght_500", pal["rubber"]))
    # bumper, anti-climber bar and coupler knuckle
    t.box((0, -0.09, 0.09), (2.5, 0.12, 0.1), pal["rubber"])
    t.box((0, -0.15, 0.18), (2.1, 0.03, 0.04), pal["steel"])
    t.box((0, -0.16, 0.3), (0.2, 0.2, 0.12), pal["under"])
    return texts


def ends(t, l, pal, coupler):
    """Grab handles at both ends, the diaphragm and coupler to the next car, and tail
    lights on the last car."""
    for y in (-0.05, L_CAR + 0.05):
        for sx in (-1, 1):
            t.prism(circle(0.018, 8), "z", (sx * 1.2, y, 1.6), 1.4, pal["steel"])
    if coupler:
        t.box((0, L_CAR + 0.3, 1.6), (1.6, 0.6, 2.0), pal["rubber"])
        t.box((0, L_CAR + 0.3, 0.32), (0.22, 0.6, 0.12), pal["under"])
    else:
        for sx in (-1, 1):
            l.prism(circle(0.035, 12), "y", (sx * 1.2, L_CAR + 0.02, 2.6), 0.03, pal["amber"])
