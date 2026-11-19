"""Trucks and underframe. Each truck has two axles with flanged wheels resting on the
rail heads (x = ±0.72 m, the track gauge), side frames, springs, brake shoes."""
from props.train_util import *


def truck(pal, yt, name):
    p = Part(name)
    for sx in (-1, 1):
        xw = sx * 0.72
        for dy in (-1.0, 1.0):          # two axles, 2.0 m apart
            ya = yt + dy
            # wheel tread on the rail, with the flange on the inside
            p.prism(circle(WHEEL_R, 18), "x", (xw, ya, AXLE_Z), 0.1, pal["wheel"])
            p.prism(circle(WHEEL_R + 0.015, 18), "x", (sx * 0.665, ya, AXLE_Z), 0.03, pal["wheel"])
            p.prism(circle(0.03, 8), "z", (sx * 0.8, ya, 0.15), 0.06, pal["under"])   # spring
            p.box((sx * 0.62, ya, 0.1), (0.05, 0.14, 0.07), pal["under"])             # brake shoe
        p.box((sx * 0.86, yt, 0.07), (0.1, 2.3, 0.08), pal["under"])                  # side frame
    for dy in (-1.0, 1.0):
        p.prism(circle(0.025, 8), "x", (0, yt + dy, AXLE_Z), 1.44, pal["under"])     # axle
    p.box((0, yt, 0.09), (1.8, 0.14, 0.1), pal["under"])                             # bolster
    return p


def underframe(pal):
    """Dark equipment boxes along the sides and an air tank, all under the floor."""
    p = Part("underframe")
    for x in (-1.0, 1.0):
        for yc in (6.0, 9.5):
            p.box((x, yc, 0.14), (0.34, 1.5, 0.12), pal["under"])
    p.prism(circle(0.07, 16), "y", (0, 7.75, 0.13), 2.2, pal["under"])
    return p
