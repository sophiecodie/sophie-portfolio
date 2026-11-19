"""Shared helpers for the subway scene: materials, primitives, text, lights.

Every texture here is procedural (node noise, brick and mosaic patterns), so the
whole station is reproducible from code. Pattern textures use *world-space*
coordinates picked by face direction, so they stay put when objects are joined
for light baking.
"""
import bpy, bmesh, math, os
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
# Wayfinding typeface: the NYC subway font (Brandon Sugiyama, nycsubwayfont.com, licensed).
# Put the licensed file in blender/fonts/ as NYCSubway.otf (or .ttf) and it is used everywhere
# signage text is set. Until then the Inter fallback is used.
SIGN_FONT = "NYCSubway"
SIGN_FONT_SLOTS = ("Inter_wght_800", "Inter_wght_500")
R = math.radians

# Project palette (matches data/projects.ts order on the site)
PROJECTS = [
    ("college-app-atlas", "College App Atlas", "A", "#3a5ccc"),
    ("purchase-intent", "Shopping Intent ML", "M", "#e8732c"),
    ("new-york-census", "New York Census", "N", "#e6a823"),
    ("folio", "Folio", "F", "#c2508a"),
    ("agent00hl7", "Agent00HL7", "7", "#2a9d8f"),
    ("dream-team", "Dream Team", "D", "#7c5cbf"),
    ("neurobiome", "Neurobiome Navigator", "B", "#4f9a5b"),
]


# ---------------------------------------------------------------- scene setup
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def render_setup(w=1440, h=900, samples=64, exposure=0.0, view="Standard"):
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "CPU"
    s.cycles.samples = samples
    s.cycles.use_denoising = True
    s.cycles.use_adaptive_sampling = True
    s.cycles.max_bounces = 6
    s.render.resolution_x, s.render.resolution_y = w, h
    s.render.resolution_percentage = 100
    # "Standard" matches what the browser shows for baked textures.
    s.view_settings.view_transform = view
    s.view_settings.exposure = exposure
    s.render.image_settings.file_format = "PNG"
    return s


def world(color=(1, .95, .88), strength=0.4):
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*color, 1)
    bg.inputs[1].default_value = strength


def srgb(hexs):
    hexs = hexs.lstrip("#")
    c = [int(hexs[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def col(c):
    return srgb(c) if isinstance(c, str) else c


# ---------------------------------------------------------------- materials
_mat_cache = {}


def mat(name, color, rough=0.5, metal=0.0, emit=None, emit_str=0.0, coat=0.0):
    key = (name, color, rough, metal, emit, emit_str, coat)
    if key in _mat_cache:
        return _mat_cache[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*col(color), 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if coat:
        p.inputs["Coat Weight"].default_value = coat
    if emit:
        p.inputs["Emission Color"].default_value = (*col(emit), 1)
        p.inputs["Emission Strength"].default_value = emit_str
    _mat_cache[key] = m
    return m


def _face_coords(nt, scale=1.0):
    """World-space 2D coords chosen by dominant normal axis (cheap triplanar)."""
    n, L = nt.nodes, nt.links
    geo = n.new("ShaderNodeNewGeometry")
    pos = n.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], pos.inputs[0])
    nrm = n.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Normal"], nrm.inputs[0])

    def op(o, a, b=None):
        m = n.new("ShaderNodeMath"); m.operation = o
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                m.inputs[i].default_value = x
            else:
                L.new(x, m.inputs[i])
        return m.outputs[0]

    ax, ay, az = (op("ABSOLUTE", nrm.outputs[i]) for i in range(3))
    mx = op("MULTIPLY", op("GREATER_THAN", ax, ay), op("GREATER_THAN", ax, az))
    rest = op("SUBTRACT", 1.0, mx)
    my = op("MULTIPLY", rest, op("GREATER_THAN", ay, az))
    mz = op("SUBTRACT", rest, my)
    X, Y, Z = pos.outputs["X"], pos.outputs["Y"], pos.outputs["Z"]
    # u: Y on X-facing walls, X otherwise. v: Z on vertical walls, Y on floors.
    u = op("ADD", op("MULTIPLY", mx, Y), op("MULTIPLY", op("ADD", my, mz), X))
    v = op("ADD", op("MULTIPLY", op("ADD", mx, my), Z), op("MULTIPLY", mz, Y))
    c = n.new("ShaderNodeCombineXYZ")
    L.new(op("MULTIPLY", u, scale), c.inputs["X"]); L.new(op("MULTIPLY", v, scale), c.inputs["Y"])
    return c.outputs[0]


def tile_mat(name="tile", base="#f3ede1", grout="#cdc3b0", tile_w=0.15, tile_h=0.075, gloss=0.12):
    """Glazed 3x6 subway tile, running bond, with grout bump and slight color jitter."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; n, L = nt.nodes, nt.links
    p = n["Principled BSDF"]
    br = n.new("ShaderNodeTexBrick")
    br.offset = 0.5
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = tile_w
    br.inputs["Row Height"].default_value = tile_h
    br.inputs["Mortar Size"].default_value = 0.004
    br.inputs["Mortar Smooth"].default_value = 0.5
    b = col(base)
    br.inputs["Color1"].default_value = (*b, 1)
    br.inputs["Color2"].default_value = (*(x * 0.94 for x in b), 1)
    br.inputs["Mortar"].default_value = (*col(grout), 1)
    L.new(_face_coords(nt), br.inputs["Vector"])
    L.new(br.outputs["Color"], p.inputs["Base Color"])
    rr = n.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = gloss; rr.inputs["To Max"].default_value = 0.7
    L.new(br.outputs["Fac"], rr.inputs["Value"]); L.new(rr.outputs["Result"], p.inputs["Roughness"])
    bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.7; bump.inputs["Distance"].default_value = 0.004
    inv = n.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1
    L.new(br.outputs["Fac"], inv.inputs[1]); L.new(inv.outputs[0], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], p.inputs["Normal"])
    return m


def mosaic_mat(name, colors, grout="#6b5a48", tess=0.012, rough=0.35):
    """Small square tesserae, each a random pick from `colors`."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; n, L = nt.nodes, nt.links
    p = n["Principled BSDF"]
    br = n.new("ShaderNodeTexBrick"); br.offset = 0.0
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = tess
    br.inputs["Row Height"].default_value = tess
    br.inputs["Mortar Size"].default_value = tess * 0.14
    br.inputs["Color1"].default_value = (0, 0, 0, 1)
    br.inputs["Color2"].default_value = (1, 1, 1, 1)
    L.new(_face_coords(nt), br.inputs["Vector"])
    sep = n.new("ShaderNodeSeparateColor"); L.new(br.outputs["Color"], sep.inputs[0])
    ramp = n.new("ShaderNodeValToRGB"); cr = ramp.color_ramp; cr.interpolation = "CONSTANT"
    k = len(colors)
    cr.elements[0].position = 0; cr.elements[0].color = (*col(colors[0]), 1)
    cr.elements[1].position = (k - 1) / k; cr.elements[1].color = (*col(colors[-1]), 1)
    for i, c in enumerate(colors[1:-1], 1):
        e = cr.elements.new(i / k); e.color = (*col(c), 1)
    L.new(sep.outputs[0], ramp.inputs[0])
    mix = n.new("ShaderNodeMix"); mix.data_type = "RGBA"
    L.new(br.outputs["Fac"], mix.inputs["Factor"])
    L.new(ramp.outputs[0], mix.inputs[6]); mix.inputs[7].default_value = (*col(grout), 1)
    L.new(mix.outputs[2], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = rough
    bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.8; bump.inputs["Distance"].default_value = 0.002
    inv = n.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1
    L.new(br.outputs["Fac"], inv.inputs[1]); L.new(inv.outputs[0], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], p.inputs["Normal"])
    return m


def noise_mat(name, a, b, scale=8.0, rough=0.6, metal=0.0, detail=6.0):
    """Two-tone noise (terrazzo floors, concrete, brushed metal)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; n, L = nt.nodes, nt.links
    p = n["Principled BSDF"]
    nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = detail
    L.new(_face_coords(nt), nz.inputs["Vector"])
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35; ramp.color_ramp.elements[0].color = (*col(a), 1)
    ramp.color_ramp.elements[1].position = 0.65; ramp.color_ramp.elements[1].color = (*col(b), 1)
    L.new(nz.outputs["Fac"], ramp.inputs[0]); L.new(ramp.outputs[0], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = rough; p.inputs["Metallic"].default_value = metal
    return m


def terrazzo_mat(name="terrazzo", base="#e9dfcd", chips=("#c9b79a", "#f7f1e6", "#b89c7c")):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; n, L = nt.nodes, nt.links
    p = n["Principled BSDF"]
    v = n.new("ShaderNodeTexVoronoi"); v.inputs["Scale"].default_value = 60
    L.new(_face_coords(nt), v.inputs["Vector"])
    ramp = n.new("ShaderNodeValToRGB"); cr = ramp.color_ramp; cr.interpolation = "CONSTANT"
    cr.elements[0].position = 0; cr.elements[0].color = (*col(base), 1)
    cr.elements[1].position = 0.85; cr.elements[1].color = (*col(chips[2]), 1)
    e = cr.elements.new(0.55); e.color = (*col(chips[0]), 1)
    e = cr.elements.new(0.7); e.color = (*col(chips[1]), 1)
    L.new(v.outputs["Color"], ramp.inputs[0])
    L.new(ramp.outputs[0], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.35
    return m


# ---------------------------------------------------------------- geometry
def link(o):
    bpy.context.collection.objects.link(o)
    return o


def assign(o, m):
    o.data.materials.clear(); o.data.materials.append(m)
    return o


def cube(name, loc, size, m=None, bevel=0.0, seg=2):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object; o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("bev", "BEVEL"); b.width = bevel; b.segments = seg; b.limit_method = "ANGLE"
        bpy.ops.object.shade_smooth_by_angle()
    if m:
        assign(o, m)
    return o


def cyl(name, loc, r, depth, m=None, rot=(0, 0, 0), verts=32, smooth=True):
    bpy.ops.mesh.primitive_cylinder_add(location=loc, radius=r, depth=depth, rotation=rot, vertices=verts)
    o = bpy.context.object; o.name = name
    if smooth:
        bpy.ops.object.shade_smooth_by_angle()
    if m:
        assign(o, m)
    return o


def sphere(name, loc, r, m=None, seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(location=loc, radius=r, segments=seg, ring_count=seg // 2)
    o = bpy.context.object; o.name = name; bpy.ops.object.shade_smooth()
    if m:
        assign(o, m)
    return o


def plane(name, loc, size, m=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(location=loc, rotation=rot)
    o = bpy.context.object; o.name = name
    o.scale = (size[0] / 2, size[1] / 2, 1)
    bpy.ops.object.transform_apply(scale=True)
    if m:
        assign(o, m)
    return o


def tube(name, points, r, m=None, res=8):
    """A rounded bar through 3D points (handrails, cords)."""
    c = bpy.data.curves.new(name, "CURVE"); c.dimensions = "3D"
    c.bevel_depth = r; c.bevel_resolution = 3; c.use_fill_caps = True
    sp = c.splines.new("POLY"); sp.points.add(len(points) - 1)
    for p, xyz in zip(sp.points, points):
        p.co = (*xyz, 1)
    o = link(bpy.data.objects.new(name, c))
    if m:
        o.data.materials.append(m)
    return o


def _font_file(name):
    for ext in (".otf", ".ttf"):
        p = os.path.join(FONTS, name + ext)
        if os.path.exists(p):
            return p
    return None


def text(body, loc, size, font="Inter_wght_800", m=None, extrude=0.0, rot=(R(90), 0, 0),
         align="CENTER", valign="CENTER", spacing=1.0, bevel=0.0):
    # Wayfinding text uses SIGN_FONT; the Inter fallback keeps the build running until the file is added.
    if font in SIGN_FONT_SLOTS:
        font = SIGN_FONT if _font_file(SIGN_FONT) else "Inter_wght_800"
    c = bpy.data.curves.new("T", "FONT"); c.body = body
    c.font = bpy.data.fonts.load(_font_file(font) or os.path.join(FONTS, font + ".ttf"), check_existing=True)
    c.size = size; c.extrude = extrude; c.align_x = align; c.align_y = valign
    c.space_character = spacing; c.bevel_depth = bevel
    c.resolution_u = 4; c.bevel_resolution = 1
    o = link(bpy.data.objects.new("T_" + body[:12], c))
    o.location = loc; o.rotation_euler = rot
    if m:
        o.data.materials.append(m)
    return o


def group(objs, loc=(0, 0, 0), rz=0.0, s=1.0, name="G"):
    e = link(bpy.data.objects.new(name, None))
    for o in objs:
        o.parent = e
    e.location = loc; e.rotation_euler = (0, 0, R(rz)); e.scale = (s, s, s)
    return e


# ---------------------------------------------------------------- lights & camera
def area(loc, rot, size, power, color=(1, .92, .8), sy=None, name="Area"):
    d = bpy.data.lights.new(name, "AREA"); d.energy = power; d.color = color
    d.shape = "RECTANGLE" if sy else "SQUARE"; d.size = size
    if sy:
        d.size_y = sy
    o = link(bpy.data.objects.new(name, d)); o.location = loc; o.rotation_euler = rot
    return o


def point(loc, power, color=(1, .85, .6), r=0.1):
    d = bpy.data.lights.new("Point", "POINT"); d.energy = power; d.color = color; d.shadow_soft_size = r
    o = link(bpy.data.objects.new("Point", d)); o.location = loc
    return o


def sun(rot, strength, color=(1, .85, .65), angle=3):
    d = bpy.data.lights.new("Sun", "SUN"); d.energy = strength; d.color = color; d.angle = R(angle)
    o = link(bpy.data.objects.new("Sun", d)); o.rotation_euler = rot
    return o


def camera(loc, target, lens=35, dof=None, fstop=2.8):
    d = bpy.data.cameras.new("Cam"); d.lens = lens
    o = link(bpy.data.objects.new("Cam", d)); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = o
    if dof:
        d.dof.use_dof = True; d.dof.focus_distance = dof; d.dof.aperture_fstop = fstop
    return o


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
