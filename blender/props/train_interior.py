"""Interior of the car, visible through the windows. Kept light: about 15k triangles.

Side walls have openings where the windows are, so the seats show through.
Cream walls, orange bench seats, stainless poles, an ad strip of project cards,
and warm ceiling light strips.
"""
from props.train_util import *
from common import PROJECTS

PROJECT_IDS = [pid for pid, *_ in PROJECTS]


def _band(p, mat_, x, z0, z1, gaps):
    """A wall panel from z0 to z1, with the gaps (doors or windows) left open."""
    for a, b in bays(gaps, y0=0.3, y1=L_CAR - 0.3):
        p.box((x, (a + b) / 2, (z0 + z1) / 2), (0.02, b - a, z1 - z0), mat_)


def build(pal, rnd, front):
    p = Part("interior")
    zb = FLOOR + WALL_T
    yc = L_CAR / 2
    # floor, ceiling and the two warm light strips
    p.box((0, yc, zb + 0.01), (2.3, L_CAR - 0.6, 0.02), pal["floor"])
    p.box((0, yc, CEIL_Z), (2.0, L_CAR - 0.6, 0.02), pal["ceiling"])
    for x in (-0.45, 0.45):
        p.box((x, yc, CEIL_Z - 0.02), (0.3, L_CAR - 1.0, 0.02), pal["light"])
    # bulkheads behind the end windows
    for yb in (0.38, L_CAR - 0.38):
        p.box((0, yb, (zb + CEIL_Z) / 2), (2.5, 0.02, CEIL_Z - zb), pal["cream"])
    if front:
        # motorman's console behind the cab window
        p.box((-0.9, 0.9, 0.9), (0.4, 0.5, 0.9), pal["board"])

    win_gaps = door_gaps(0.0) + [(c - w / 2, c + w / 2) for c, w in windows()]
    for sx in (-1, 1):
        x = sx * (HALF - WALL_T - 0.02)
        _band(p, pal["cream"], x, zb, WIN_Z[0], door_gaps(0.0))
        _band(p, pal["cream"], x, WIN_Z[0], WIN_Z[1], win_gaps)
        _band(p, pal["cream"], x, WIN_Z[1], DOOR_Z[1], door_gaps(0.0))
        _band(p, pal["cream"], x, DOOR_Z[1], CEIL_Z, [])

        for a, b in bays(door_gaps(0.12), y0=0.3, y1=L_CAR - 0.3):
            ln_all = b - a
            # ad strip above the windows, one card per slot
            p.box((sx * 1.25, (a + b) / 2, 2.7), (0.01, ln_all, 0.4), pal["cream_dark"])
            n = max(1, int(ln_all / 0.95))
            for i in range(n):
                cy = a + (i + 0.5) * ln_all / n
                key = "card_" + rnd.choice(PROJECT_IDS)
                p.box((sx * 1.245, cy, 2.7), (0.01, ln_all / n - 0.15, 0.32), pal[key])
            # molded bench seats in sections of about 0.9 m
            n = max(1, int(ln_all / 0.95))
            seg = ln_all / n
            for i in range(n):
                s0 = a + i * seg + 0.04
                s1 = a + (i + 1) * seg - 0.04
                ln, mid = s1 - s0, (s0 + s1) / 2
                p.box((sx * 1.06, mid, 0.39), (0.1, ln, 0.22), pal["cream"])            # pedestal
                p.box((sx * 1.04, mid, 0.55), (0.36, ln, 0.1), pal["seat"])            # cushion
                p.box((sx * 1.20, mid, 0.875), (0.07, ln, 0.55), pal["seat"])          # backrest

    # stainless poles beside each doorway, and an overhead rail along each side
    for yd in DOOR_YS:
        for dy in (-0.9, 0.9):
            for sx in (-1, 1):
                p.prism(circle(0.022, 10), "z", (sx * 0.72, yd + dy, (zb + CEIL_Z) / 2),
                        CEIL_Z - zb, pal["pole"])
    for sx in (-1, 1):
        p.box((sx * 0.95, yc, 3.0), (0.03, L_CAR - 1.0, 0.03), pal["pole"])
    return p
