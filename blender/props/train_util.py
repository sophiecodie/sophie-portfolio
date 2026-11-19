"""Shared pieces for the subway car: dimensions, a small builder for convex parts
(boxes and extruded outlines), and the boolean cut that opens windows and doors.

Everything is numbers, so the car stays parametric. Car coordinates: the front
is at y=0 and the body runs to +Y; z=0 is the station's rail datum. The car's
floor sits at the platform edge, and the trucks sit on the rail heads.
"""
import math
import bpy
from mathutils import Euler, Vector
from common import mat, link, R, PROJECTS

# ---------------------------------------------------------------- dimensions (m)
L_CAR = 15.5                 # body length
HALF = 1.35                  # half width of the shell (2.7 m wide)
FLOOR = 0.20                 # car floor == platform edge (layout.PLAT_Z)
EAVE = 2.90                  # wall turns into the roof arch here
CROWN = 3.63                 # rail to roof = 3.7 m
RAIL_TOP = -0.0725           # rail head top in station coordinates
# The platform is only 0.27 m above the rail, so the floor leaves room for
# wheels of about 0.24 m. Raising layout.PLAT_Z would allow real 0.86 m wheels.
WHEEL_R = 0.12
AXLE_Z = RAIL_TOP + WHEEL_R
WALL_T = 0.06                # shell thickness; the cavity is the interior
CEIL_Z = 3.20                # interior ceiling
DOOR_W = 1.30
DOOR_Z = (FLOOR + 0.02, 2.75)
WIN_Z = (1.45, 2.50)
DOOR_YS = [L_CAR * (k + 1) / 5 for k in range(4)]   # four doors, evenly spaced
TRUCK_YS = (3.0, L_CAR - 3.0)

# (in-plane axis a, in-plane axis b, extrusion axis) for each face normal
AX = {"x": (1, 2, 0), "y": (0, 2, 1), "z": (0, 1, 2)}


# ---------------------------------------------------------------- 2D outlines
def rrect(w, h, r, seg=3):
    """Rounded rectangle centred on 0, counter-clockwise."""
    r = max(0.005, min(r, w / 2, h / 2))
    cx, cy = w / 2 - r, h / 2 - r
    pts = []
    for ox, oy, a0 in ((cx, cy, 0), (-cx, cy, 90), (-cx, -cy, 180), (cx, -cy, 270)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90 * k / seg)
            pts.append((ox + r * math.cos(a), oy + r * math.sin(a)))
    return pts


def circle(r, seg=12):
    return [(r * math.cos(2 * math.pi * k / seg), r * math.sin(2 * math.pi * k / seg)) for k in range(seg)]


# ---------------------------------------------------------------- part builder
class Part:
    """Collects convex pieces (boxes, extruded outlines) into one mesh.

    Each piece can use its own material. Face winding is fixed from the piece's
    centre, so callers never think about normals.
    """

    def __init__(self, name):
        self.name = name
        self.v, self.f, self.m, self.mats = [], [], [], []

    def _mi(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def _add(self, verts, faces, m):
        base = len(self.v)
        self.v.extend(verts)
        n = len(verts)
        c = [sum(p[i] for p in verts) / n for i in range(3)]
        mi = self._mi(m)
        for f in faces:
            pts = [verts[i] for i in f]
            nx = ny = nz = 0.0
            for i in range(len(pts)):
                x1, y1, z1 = pts[i]
                x2, y2, z2 = pts[(i + 1) % len(pts)]
                nx += (y1 - y2) * (z1 + z2)
                ny += (z1 - z2) * (x1 + x2)
                nz += (x1 - x2) * (y1 + y2)
            fc = [sum(p[i] for p in pts) / len(pts) for i in range(3)]
            if nx * (fc[0] - c[0]) + ny * (fc[1] - c[1]) + nz * (fc[2] - c[2]) < 0:
                f = f[::-1]
            self.f.append(tuple(base + i for i in f))
            self.m.append(mi)

    def prism(self, poly, axis, center, depth, m):
        """Extrude a convex 2D outline (relative to center) along `axis`."""
        ia, ib, ik = AX[axis]
        h, n = depth / 2, len(poly)
        verts = []
        for s in (-h, h):
            for a, b in poly:
                p = [0.0, 0.0, 0.0]
                p[ia] = center[ia] + a
                p[ib] = center[ib] + b
                p[ik] = center[ik] + s
                verts.append(tuple(p))
        faces = [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
        faces += [tuple(range(n)), tuple(range(n, 2 * n))]
        self._add(verts, faces, m)

    def box(self, c, s, m, rot=(0, 0, 0)):
        hx, hy, hz = s[0] / 2, s[1] / 2, s[2] / 2
        corners = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
                   (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
        M = Euler(rot).to_matrix()
        verts = []
        for p in corners:
            q = M @ Vector(p)
            verts.append((c[0] + q.x, c[1] + q.y, c[2] + q.z))
        faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self._add(verts, faces, m)

    def obj(self, name=None, origin=(0, 0, 0)):
        """Make a Blender object. `origin` becomes its pivot (e.g. a door's slide axis)."""
        name = name or self.name
        me = bpy.data.meshes.new(name)
        verts = [(x - origin[0], y - origin[1], z - origin[2]) for x, y, z in self.v]
        me.from_pydata(verts, [], self.f)
        for m in self.mats:
            me.materials.append(m)
        for p, mi in zip(me.polygons, self.m):
            p.material_index = mi
        me.update()
        o = link(bpy.data.objects.new(name, me))
        o.location = origin
        return o


# ---------------------------------------------------------------- object ops
def cut(obj, cutter):
    """Boolean difference, applied, then the cutter object is removed."""
    bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.new("cut", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cutter
    mod.solver = "EXACT"
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def smooth(obj, deg=35):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(deg))
    obj.select_set(False)


def tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


# ---------------------------------------------------------------- layout helpers
def door_gaps(margin=0.0):
    return [(yd - DOOR_W / 2 - margin, yd + DOOR_W / 2 + margin) for yd in DOOR_YS]


def bays(gaps, y0=0.5, y1=L_CAR - 0.5):
    """Intervals between gaps: the stretches of wall that are left."""
    out, cur = [], y0
    for a, b in sorted(gaps):
        if a > cur:
            out.append((cur, a))
        cur = max(cur, b)
    if y1 > cur:
        out.append((cur, y1))
    return out


def windows():
    """(y centre, width) of every side window: two per bay between doors."""
    out = []
    for a, b in bays(door_gaps(0.05)):
        n = 2 if (b - a) > 1.5 else 1
        sub = (b - a) / n
        w = min(0.62, sub - 0.25)
        for i in range(n):
            out.append((a + sub * (i + 0.5), w))
    return out


def pane(p, m, axis, c, w, h, depth=0.02):
    p.prism(rrect(w, h, 0.07), axis, c, depth, m)


def frame(p, m, axis, c, w, h, depth=0.03, t=0.03):
    """Four bars around an opening: a rubber gasket that sits on the hole's edge."""
    ia, ib, ik = AX[axis]
    for a, b, sa, sb in ((0, h / 2, w + t, t), (0, -h / 2, w + t, t),
                         (-w / 2, 0, t, h + t), (w / 2, 0, t, h + t)):
        cen = [0.0, 0.0, 0.0]
        cen[ia], cen[ib], cen[ik] = c[ia] + a, c[ib] + b, c[ik]
        size = [0.0, 0.0, 0.0]
        size[ia], size[ib], size[ik] = sa, sb, depth
        p.box(tuple(cen), tuple(size), m)


# ---------------------------------------------------------------- materials
def glass_mat():
    """Tinted, reflective glass. Transmission lets the lit interior show through."""
    m = mat("car_glass", "#dcefe9", 0.03)
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Transmission Weight"].default_value = 0.92
    p.inputs["IOR"].default_value = 1.45
    return m


def palette(color):
    key = color.lstrip("#")
    pal = dict(
        steel=mat("car_steel", "#c9ced3", 0.3, metal=1.0),
        steel_dark=mat("car_steel_dark", "#9aa1a9", 0.4, metal=1.0),
        rubber=mat("car_rubber", "#16161b", 0.8),
        under=mat("car_underframe", "#3b3e44", 0.6, metal=0.3),
        wheel=mat("car_wheel", "#8f959c", 0.35, metal=1.0),
        paint=mat("car_paint_" + key, color, 0.4, coat=0.3),
        glass=glass_mat(),
        head=mat("car_headlight", "#fffbe8", 0.2, emit="#fff6d0", emit_str=20),
        amber=mat("car_amber", "#ffb36b", 0.3, emit="#ffa040", emit_str=6),
        dest=mat("car_dest_amber", "#ffb000", 0.4, emit="#ffa000", emit_str=5),
        board=mat("car_dest_board", "#141416", 0.6),
        route=mat("car_route_" + key, color, 0.35, emit=color, emit_str=2.5),
        route_white=mat("car_route_white", "#ffffff", 0.3, emit="#ffffff", emit_str=1.5),
        plate=mat("car_plate", "#f2efe6", 0.5),
        cream=mat("car_cream", "#efe6d2", 0.7),
        cream_dark=mat("car_cream_dark", "#d9ccb2", 0.7),
        floor=mat("car_floor", "#4a4c52", 0.9),
        seat=mat("car_seat_orange", "#e8732c", 0.5),
        light=mat("car_ceiling_light", "#fff1d6", 0.4, emit="#fff1d6", emit_str=8),
        ceiling=mat("car_ceiling", "#f4eedf", 0.8),
        pole=mat("car_pole", "#c7ccd2", 0.25, metal=1.0),
    )
    for pid, _name, _letter, hexc in PROJECTS:
        pal["card_" + pid] = mat("car_card_" + pid, hexc, 0.45)
    return pal
