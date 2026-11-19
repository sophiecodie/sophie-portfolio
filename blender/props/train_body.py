"""The car's shell: a curved hollow profile, boolean-cut openings, and the steel
trim that sits on it (flutes, seams, rivets, paint band, roof gear, doorways)."""
import math
from props.train_util import *


def _right_half(off=0.0):
    """Outline from the floor corner up to the crown, on the +X side (x, z).

    The bottom tumbles inward, the walls are straight, and the roof is a
    quarter ellipse that gives rounded eaves and a shallow arch.
    """
    H, F, C, E = HALF - off, FLOOR + off, CROWN - off, EAVE
    tuck = [(1.12 - off, F), (1.20 - off, F + 0.15), (1.27 - off, F + 0.45),
            (1.33 - off, 0.9), (H, 1.1), (H, E)]
    b = C - E
    arc = [(H * math.cos(t), E + b * math.sin(t)) for t in (math.pi / 2 * k / 8 for k in range(1, 9))]
    return tuck + arc


def profile(off=0.0):
    right = _right_half(off)
    left = [(-x, z) for x, z in reversed(right)]
    return right + left[1:]


_RIGHT = _right_half()


def wall_x(z):
    """Outer wall x at height z, for placing flutes on the curved lower body."""
    for (x0, z0), (x1, z1) in zip(_RIGHT, _RIGHT[1:]):
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0) if z1 > z0 else 0.0
            return x0 + t * (x1 - x0)
    return HALF


def shell(pal):
    """Solid profile minus its inner cavity, so the walls are 6 cm thick."""
    outer = Part("body")
    outer.prism(profile(0.0), "y", (0, L_CAR / 2, 0), L_CAR, pal["steel"])
    cav = Part("cavity")
    cav.prism(profile(WALL_T), "y", (0, L_CAR / 2, 0), L_CAR - 2 * WALL_T, pal["steel"])
    body = outer.obj("body")
    cut(body, cav.obj("cavity"))
    return body


def openings(pal, front):
    """Cutters for every side window and door, plus the end windows."""
    c = Part("cutters")
    zc = sum(WIN_Z) / 2
    zh = WIN_Z[1] - WIN_Z[0]
    for sx in (-1, 1):
        for yc, w in windows():
            c.prism(rrect(w, zh, 0.09), "x", (sx * HALF, yc, zc), 0.8, pal["steel"])
        for yd in DOOR_YS:
            c.prism(rrect(DOOR_W, DOOR_Z[1] - DOOR_Z[0], 0.08), "x",
                    (sx * HALF, yd, sum(DOOR_Z) / 2), 0.8, pal["steel"])
    # the front car's end is closed: its R160 cab (train_r160.py) is applied over it
    for y in ((L_CAR,) if front else (0.0, L_CAR)):
        c.prism(rrect(0.84, zh, 0.09), "y", (0, y, zc), 0.6, pal["steel"])
    return c.obj("cutters")


def glazing(g, pal, front):
    """Glass panes and rubber gaskets for every window, plus the end windows."""
    zc, zh = sum(WIN_Z) / 2, WIN_Z[1] - WIN_Z[0]
    for sx in (-1, 1):
        for yc, w in windows():
            pane(g, pal["glass"], "x", (sx * (HALF - 0.03), yc, zc), w - 0.04, zh - 0.04)
            frame(g, pal["rubber"], "x", (sx * HALF, yc, zc), w, zh)
    ends = [(0.0, 0.84, L_CAR)] if front else [(0.0, 0.84, 0.0), (0.0, 0.84, L_CAR)]
    for xc, w, y in ends:
        inset = 0.03 if y == 0.0 else -0.03
        pane(g, pal["glass"], "y", (xc, y + inset, zc), w - 0.04, zh - 0.04)
        frame(g, pal["rubber"], "y", (xc, y, zc), w, zh)


def trim(t, pal):
    """Everything bolted to the shell: flutes, paint band, seams, rivets, roof."""
    zc, zh = sum(WIN_Z) / 2, WIN_Z[1] - WIN_Z[0]
    for sx in (-1, 1):
        # R160 sides are smooth stainless (no fluting): a panel seam low down, and a
        # thin band in the line's color below the windows (the site recolors it)
        for a, b in bays(door_gaps(0.05)):
            t.box((sx * (wall_x(0.62) + 0.003), (a + b) / 2, 0.62), (0.006, b - a, 0.012), pal["steel_dark"])
            # thin paint band just below the windows
            t.box((sx * (HALF + 0.003), (a + b) / 2, 1.25), (0.006, b - a, 0.09), pal["paint"])
        # raised ribs at each window edge
        for yc, w in windows():
            for dy in (-1, 1):
                t.box((sx * (HALF + 0.004), yc + dy * (w / 2 + 0.02), zc),
                      (0.008, 0.035, zh + 0.1), pal["steel_dark"])
        # rivet rows above the lower fluting and above the windows
        for z in (1.13, 2.62):
            for a, b in bays(door_gaps(0.05)):
                n = max(1, int((b - a) / 0.22))
                for i in range(n):
                    y = a + (i + 0.5) * (b - a) / n
                    t.prism(circle(0.016, 6), "x", (sx * (HALF + 0.006), y, z), 0.012, pal["steel_dark"])
        # dark door-pocket recess above each doorway
        for yd in DOOR_YS:
            t.box((sx * (HALF + 0.004), yd, 2.82), (0.008, DOOR_W - 0.1, 0.1), pal["rubber"])
    # roof: two HVAC housings with louvres, a walkway strip, two antenna stubs
    for yc in (4.2, 11.2):
        for x in (-0.5, 0.5):
            t.box((x, yc, 3.5), (0.9, 2.4, 0.4), pal["steel_dark"])
            for k in range(4):
                t.box((x, yc - 0.9 + k * 0.6, 3.72), (0.7, 0.14, 0.04), pal["under"])
    t.box((0, L_CAR / 2, 3.6), (0.4, L_CAR - 2.4, 0.06), pal["rubber"])
    for x in (-0.3, 0.3):
        t.prism(circle(0.02, 6), "z", (x, 7.8, 3.7), 0.4, pal["steel"])


def doors(pal):
    """Sliding door leaves: two per doorway and side. Each leaf's origin sits on its
    slide axis, so the site can open it by moving it along Y."""
    out = []
    zc = sum(DOOR_Z) / 2
    zh = DOOR_Z[1] - DOOR_Z[0]
    for sx in (-1, 1):
        side = "L" if sx > 0 else "R"
        for k, yd in enumerate(DOOR_YS):
            for leaf, (y0, y1) in enumerate(((yd - DOOR_W / 2, yd), (yd, yd + DOOR_W / 2))):
                yc = (y0 + y1) / 2
                lw = (y1 - y0) - 0.012
                origin = (sx * HALF, yc, zc)
                p = Part("doors_%s_%d%s" % (side, k, "ab"[leaf]))
                p.box((sx * (HALF - 0.03), yc, zc), (0.04, lw, zh), pal["steel"])
                # tall narrow window with a rubber surround
                pane(p, pal["glass"], "x", (sx * (HALF + 0.002), yc, 2.0), lw - 0.2, 1.0, depth=0.008)
                frame(p, pal["rubber"], "x", (sx * (HALF + 0.002), yc, 2.0), lw - 0.2, 1.0, depth=0.012, t=0.02)
                # rubber edge seals along both vertical edges
                for ye in (y0, y1):
                    p.box((sx * (HALF + 0.002), ye, zc), (0.012, 0.03, zh), pal["rubber"])
                out.append(p.obj(p.name, origin=origin))
    return out
