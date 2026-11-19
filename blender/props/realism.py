"""Realistic NYC station detail (2026-11-17 upgrade).

Researched from Sophie's reference photos (East Broadway, W 4 St, 23 St, 14 St, Museum of
Natural History) and NYC sources (IND tile system, Vickers-era oak benches, enamel
column signs, ADA truncated-dome edges). Everything is still code: procedural
materials plus small meshes, so the light bake carries the detail and the GLB stays small.

  materials(base)       swaps the station_shell materials for realistic ones (same keys)
  ibeam_column(...)     riveted steel H column with base, knee braces and an enamel name plate
  ceiling_steel(...)    girders over the column lines, cross beams, conduit, speakers
  fixture(...)          open fluorescent strip fixture on hangers
  coping(...)           the platform edge: concrete coping and dark rubbing face
  third_rail(...)       contact rail with its wooden cover board
  oak_bench(...)        the classic divided oak bench
  modern_bench(...)     the newer oak-and-steel bench with steel loop dividers
  trash_can()           ribbed black can
  countdown_screen(...) hanging two-row arrivals screen
  kiosk(...)            standing arrivals kiosk
  band_tablet(...)      small black IND name tablet
"""
import math
from common import *
from common import _face_coords
from props.train_util import Part, circle, rrect

STEEL_GREEN = "#2e5a45"
BAND = "#3f9a5c"          # IND "hunter green" family, cheerful but true to 14 St
BAND_DARK = "#24603a"
TACTILE = "#f2b81c"


# ---------------------------------------------------------------- materials
def _nodes(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    return m, nt, nt.nodes, nt.links, nt.nodes["Principled BSDF"]


def _op(n, L, o, a, b=None):
    m = n.new("ShaderNodeMath"); m.operation = o
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            m.inputs[i].default_value = x
        else:
            L.new(x, m.inputs[i])
    return m.outputs[0]


def square_tile(name, base="#f6f4ee", grout="#c9c6bd", size=0.108, gloss=0.06, jitter=0.035):
    """Glazed 4-1/4 in square tile, stacked grid (as in the 14 St and E Broadway photos).
    Each tile gets its own tiny tint and glaze tilt, so reflections break up like real tile."""
    m, nt, n, L, p = _nodes(name)
    uv = _face_coords(nt)
    br = n.new("ShaderNodeTexBrick"); br.offset = 0.0; br.offset_frequency = 1
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = size
    br.inputs["Row Height"].default_value = size
    br.inputs["Mortar Size"].default_value = 0.005
    br.inputs["Mortar Smooth"].default_value = 0.6
    b = col(base)
    br.inputs["Color1"].default_value = (*b, 1)
    br.inputs["Color2"].default_value = (*(x * (1 - jitter) for x in b), 1)
    br.inputs["Mortar"].default_value = (*col(grout), 1)
    br.inputs["Bias"].default_value = 0.0
    L.new(uv, br.inputs["Vector"])
    # large soft variation (hand-set walls are never perfectly even)
    nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.8; nz.inputs["Detail"].default_value = 3
    L.new(uv, nz.inputs["Vector"])
    mix = n.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.12
    L.new(br.outputs["Color"], mix.inputs[6]); L.new(nz.outputs["Color"], mix.inputs[7])
    L.new(mix.outputs[2], p.inputs["Base Color"])
    rr = n.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = gloss; rr.inputs["To Max"].default_value = 0.75
    L.new(br.outputs["Fac"], rr.inputs["Value"]); L.new(rr.outputs["Result"], p.inputs["Roughness"])
    # grout sits back and the glaze pillows toward the tile edges
    bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.9; bump.inputs["Distance"].default_value = 0.005
    inv = _op(n, L, "SUBTRACT", 1.0, br.outputs["Fac"])
    L.new(inv, bump.inputs["Height"])
    L.new(bump.outputs["Normal"], p.inputs["Normal"])
    p.inputs["Coat Weight"].default_value = 0.35
    p.inputs["Coat Roughness"].default_value = 0.08
    return m


def concrete(name="concrete_floor", a="#9d988e", b="#b3aea3", joint=1.83, wear=True):
    """Sealed concrete platform: soft mottling, fine aggregate speckle, saw-cut joints,
    and a gently polished, darker walking path. Clean, not grimy."""
    m, nt, n, L, p = _nodes(name)
    uv = _face_coords(nt)
    nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.9; nz.inputs["Detail"].default_value = 8
    nz.inputs["Roughness"].default_value = 0.62
    L.new(uv, nz.inputs["Vector"])
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.3; ramp.color_ramp.elements[0].color = (*col(a), 1)
    ramp.color_ramp.elements[1].position = 0.7; ramp.color_ramp.elements[1].color = (*col(b), 1)
    L.new(nz.outputs["Fac"], ramp.inputs[0])
    # aggregate speckle
    vo = n.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 140
    L.new(uv, vo.inputs["Vector"])
    sp = n.new("ShaderNodeMapRange"); sp.inputs["From Min"].default_value = 0.0; sp.inputs["From Max"].default_value = 0.08
    sp.inputs["To Min"].default_value = 0.82; sp.inputs["To Max"].default_value = 1.0
    L.new(vo.outputs["Distance"], sp.inputs["Value"])
    c1 = n.new("ShaderNodeMix"); c1.data_type = "RGBA"; c1.blend_type = "MULTIPLY"; c1.inputs["Factor"].default_value = 1.0
    L.new(ramp.outputs[0], c1.inputs[6])
    cc = n.new("ShaderNodeCombineColor"); L.new(sp.outputs[0], cc.inputs[0]); L.new(sp.outputs[0], cc.inputs[1]); L.new(sp.outputs[0], cc.inputs[2])
    L.new(cc.outputs[0], c1.inputs[7])
    # saw-cut joints: a big stacked grid with hairline mortar
    br = n.new("ShaderNodeTexBrick"); br.offset = 0.0
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = joint
    br.inputs["Row Height"].default_value = joint
    br.inputs["Mortar Size"].default_value = 0.006
    br.inputs["Mortar Smooth"].default_value = 0.3
    br.inputs["Color1"].default_value = (1, 1, 1, 1); br.inputs["Color2"].default_value = (1, 1, 1, 1)
    br.inputs["Mortar"].default_value = (0.45, 0.43, 0.4, 1)
    L.new(uv, br.inputs["Vector"])
    c2 = n.new("ShaderNodeMix"); c2.data_type = "RGBA"; c2.blend_type = "MULTIPLY"; c2.inputs["Factor"].default_value = 1.0
    L.new(c1.outputs[2], c2.inputs[6]); L.new(br.outputs["Color"], c2.inputs[7])
    out = c2.outputs[2]
    if wear:
        # a faint few spots and scuffs, the lived-in bit (kept light)
        sc = n.new("ShaderNodeTexNoise"); sc.inputs["Scale"].default_value = 7; sc.inputs["Detail"].default_value = 10
        L.new(uv, sc.inputs["Vector"])
        sr = n.new("ShaderNodeMapRange"); sr.inputs["From Min"].default_value = 0.62; sr.inputs["From Max"].default_value = 0.75
        sr.inputs["To Min"].default_value = 0.0; sr.inputs["To Max"].default_value = 0.12
        L.new(sc.outputs["Fac"], sr.inputs["Value"])
        c3 = n.new("ShaderNodeMix"); c3.data_type = "RGBA"
        L.new(sr.outputs[0], c3.inputs["Factor"]); L.new(out, c3.inputs[6]); c3.inputs[7].default_value = (*col("#6f6a62"), 1)
        out = c3.outputs[2]
    L.new(out, p.inputs["Base Color"])
    rough = n.new("ShaderNodeMapRange"); rough.inputs["To Min"].default_value = 0.42; rough.inputs["To Max"].default_value = 0.8
    L.new(nz.outputs["Fac"], rough.inputs["Value"]); L.new(rough.outputs[0], p.inputs["Roughness"])
    bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25; bump.inputs["Distance"].default_value = 0.002
    L.new(vo.outputs["Distance"], bump.inputs["Height"]); L.new(bump.outputs["Normal"], p.inputs["Normal"])
    return m


def tactile(name="tactile_edge", color=TACTILE, pitch=0.06, panel=0.61):
    """ADA detectable warning strip: truncated domes (0.9 in wide, 2.35 in apart, in line)
    on 2 x 2 ft yellow panels. The domes are a bump map so the bake shades every one."""
    m, nt, n, L, p = _nodes(name)
    uv = _face_coords(nt)
    sc = n.new("ShaderNodeVectorMath"); sc.operation = "SCALE"; sc.inputs["Scale"].default_value = 1.0 / pitch
    L.new(uv, sc.inputs[0])
    fr = n.new("ShaderNodeVectorMath"); fr.operation = "FRACTION"; L.new(sc.outputs[0], fr.inputs[0])
    sub = n.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = (0.5, 0.5, 0)
    L.new(fr.outputs[0], sub.inputs[0])
    ln = n.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; L.new(sub.outputs[0], ln.inputs[0])
    # flat-topped dome: full height inside r=0.14, sloping out to r=0.2 (in pitch units)
    dome = n.new("ShaderNodeMapRange"); dome.interpolation_type = "SMOOTHSTEP"
    dome.inputs["From Min"].default_value = 0.24; dome.inputs["From Max"].default_value = 0.08
    L.new(ln.outputs["Value"], dome.inputs["Value"])
    # panel seams every 2 ft
    br = n.new("ShaderNodeTexBrick"); br.offset = 0.0
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = panel; br.inputs["Row Height"].default_value = panel
    br.inputs["Mortar Size"].default_value = 0.004
    br.inputs["Color1"].default_value = (*col(color), 1)
    br.inputs["Color2"].default_value = (*(x * 0.95 for x in col(color)), 1)
    br.inputs["Mortar"].default_value = (*col("#8a6a1a"), 1)
    L.new(uv, br.inputs["Vector"])
    # dome tops are a touch lighter (scuffed by shoes), bases a touch darker
    tint = n.new("ShaderNodeMix"); tint.data_type = "RGBA"; tint.blend_type = "MULTIPLY"
    L.new(dome.outputs[0], tint.inputs["Factor"])
    L.new(br.outputs["Color"], tint.inputs[6]); tint.inputs[7].default_value = (1.12, 1.1, 1.05, 1)
    nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3; nz.inputs["Detail"].default_value = 6
    L.new(uv, nz.inputs["Vector"])
    dirt = n.new("ShaderNodeMix"); dirt.data_type = "RGBA"; dirt.blend_type = "MULTIPLY"; dirt.inputs["Factor"].default_value = 0.18
    L.new(tint.outputs[2], dirt.inputs[6]); L.new(nz.outputs["Color"], dirt.inputs[7])
    L.new(dirt.outputs[2], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.55
    h = _op(n, L, "SUBTRACT", dome.outputs[0], br.outputs["Fac"])
    bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 1.0; bump.inputs["Distance"].default_value = 0.012
    L.new(h, bump.inputs["Height"]); L.new(bump.outputs["Normal"], p.inputs["Normal"])
    return m


def painted_steel(name="steel_" + STEEL_GREEN, color=STEEL_GREEN, rough=0.38):
    """Many coats of enamel on steel: a soft gloss, tiny orange-peel and brush unevenness."""
    m, nt, n, L, p = _nodes(name)
    uv = _face_coords(nt)
    nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 18; nz.inputs["Detail"].default_value = 6
    L.new(uv, nz.inputs["Vector"])
    ramp = n.new("ShaderNodeValToRGB")
    c = col(color)
    ramp.color_ramp.elements[0].position = 0.35; ramp.color_ramp.elements[0].color = (*(x * 0.86 for x in c), 1)
    ramp.color_ramp.elements[1].position = 0.7; ramp.color_ramp.elements[1].color = (*c, 1)
    L.new(nz.outputs["Fac"], ramp.inputs[0]); L.new(ramp.outputs[0], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = rough
    p.inputs["Coat Weight"].default_value = 0.4
    bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.08; bump.inputs["Distance"].default_value = 0.001
    L.new(nz.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs["Normal"], p.inputs["Normal"])
    return m


def oak(name="oak_varnished", a="#7a4526", b="#b47a4a", grain=(36.0, 1.2, 36.0)):
    """Laminated oak under reddish varnish, grain streaked along Y (benches run along Y)."""
    m, nt, n, L, p = _nodes(name)
    geo = n.new("ShaderNodeNewGeometry")
    mp = n.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = grain
    L.new(geo.outputs["Position"], mp.inputs["Vector"])
    wv = n.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "X"
    wv.inputs["Scale"].default_value = 0.6; wv.inputs["Distortion"].default_value = 2.5; wv.inputs["Detail"].default_value = 3
    L.new(mp.outputs[0], wv.inputs["Vector"])
    nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.5; nz.inputs["Detail"].default_value = 8
    L.new(mp.outputs[0], nz.inputs["Vector"])
    mixf = n.new("ShaderNodeMix"); mixf.data_type = "FLOAT"; mixf.inputs["Factor"].default_value = 0.5
    L.new(wv.outputs["Fac"], mixf.inputs[2]); L.new(nz.outputs["Fac"], mixf.inputs[3])
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.25; ramp.color_ramp.elements[0].color = (*col(a), 1)
    ramp.color_ramp.elements[1].position = 0.8; ramp.color_ramp.elements[1].color = (*col(b), 1)
    L.new(mixf.outputs[0], ramp.inputs[0]); L.new(ramp.outputs[0], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.45
    p.inputs["Coat Weight"].default_value = 0.3
    p.inputs["Coat Roughness"].default_value = 0.15
    bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.15; bump.inputs["Distance"].default_value = 0.001
    L.new(wv.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs["Normal"], p.inputs["Normal"])
    return m


def materials(base):
    """Same keys as station_shell.materials(), with the realistic versions."""
    M = dict(base)
    M.update(
        tile=square_tile("wall_tile_white"),
        band=square_tile("band_tile_green", base=BAND, grout="#2b5a3b", gloss=0.05, jitter=0.06),
        trim=square_tile("trim_tile_dark", base=BAND_DARK, grout="#1d3f28", size=0.054, gloss=0.05),
        base=square_tile("base_tile_dark", base=BAND_DARK, grout="#1d3f28", gloss=0.08),
        floor=concrete(),
        edge=tactile(),
        ceiling=concrete("ceiling_paint", "#e9e1cf", "#f2ebdc", joint=50.0, wear=False),
        column=painted_steel(),
        column_cap=painted_steel(),
        bed=noise_mat("track_bed_concrete", "#4f4943", "#635b53", scale=4, rough=0.95, detail=8),
        sleeper=noise_mat("tie_wood", "#4a3424", "#5d4330", scale=22, rough=0.9),
        rail=mat("rail_steel", "#8e8a86", 0.35, metal=0.9),
        end=concrete("end_wall_paint", "#e6ddca", "#efe7d6", joint=50.0, wear=False),
    )
    M["rail_head"] = mat("rail_head_bright", "#d4d6d9", 0.18, metal=1.0)
    M["coping"] = concrete("coping_concrete", "#bdb7ab", "#cbc5b9", joint=1.5, wear=False)
    M["rubbing"] = mat("platform_face", "#3d3a36", 0.85)
    M["cover"] = noise_mat("cover_board", "#8a6a45", "#9c7b52", scale=12, rough=0.85)
    M["conduit"] = mat("conduit_paint", "#d9d3c4", 0.45, metal=0.2)
    M["housing"] = mat("fixture_housing", "#e7e5df", 0.4, metal=0.3)
    M["tube"] = mat("fluorescent_tube", "#ffffff", 0.2, emit="#fff4e0", emit_str=9.0)
    M["rivet"] = M["column"]
    return M


def _white():
    return mat("sign_white", "#ffffff", 0.3, emit="#ffffff", emit_str=1.0)


def _enamel_black():
    return mat("enamel_black", "#141414", 0.18, coat=0.8)


# ---------------------------------------------------------------- columns
def _rivet_row(part, m, axis, fixed, along, z0, z1, step=0.11, r=0.011):
    """Low domed rivets in a vertical row on a face whose normal is `axis` (+x/-x/+y/-y)."""
    sgn = 1 if axis[0] == "+" else -1
    ax = axis[1]
    z = z0
    while z <= z1 + 1e-6:
        # a short 8-sided cone frustum reads as a rivet head once baked
        poly = circle(r, 8)
        top = circle(r * 0.55, 8)
        verts = []
        for (a, b), lift in [(q, 0.0) for q in poly] + [(q, r * 0.75) for q in top]:
            if ax == "x":
                verts.append((fixed + sgn * lift, along + a, z + b))
            else:
                verts.append((along + a, fixed + sgn * lift, z + b))
        faces = [(i, (i + 1) % 8, 8 + (i + 1) % 8, 8 + i) for i in range(8)] + [tuple(range(8, 16))]
        part._add(verts, faces, m)
        z += step


def ibeam_column(M, h, plate=("Sophie", "Shih"), w=0.30, d=0.30, tf=0.022, tw=0.014, plates_on=("+x", "-x")):
    """A riveted H column like W 4 St and E Broadway: flanges face +/-X (track and wall),
    the web runs across. Origin at the floor. Built of boxes so normals are always right."""
    st = M["column"]
    p = Part("column")
    # flanges and web
    for sx in (-1, 1):
        p.box((sx * (d / 2 - tf / 2), 0, h / 2), (tf, w, h), st)
    p.box((0, 0, h / 2), (d - 2 * tf, tw, h), st)
    # built-up look: cover plates riveted near top and bottom, and stitch plates between
    for zc, hh in ((0.45, 0.5), (h - 0.55, 0.6)):
        for sx in (-1, 1):
            p.box((sx * (d / 2 + 0.006), 0, zc), (0.012, w + 0.01, hh), st)
    # rivets: two rows on each flange face, closer spaced at the plates
    for sx, ax in ((1, "+x"), (-1, "-x")):
        for yy in (-w / 2 + 0.035, w / 2 - 0.035):
            _rivet_row(p, M["rivet"], ax, sx * (d / 2 + 0.012), yy, 0.25, 0.65, step=0.08)
            _rivet_row(p, M["rivet"], ax, sx * (d / 2 + 0.012), yy, h - 0.8, h - 0.3, step=0.08)
            _rivet_row(p, M["rivet"], ax, sx * d / 2, yy, 0.8, h - 0.9, step=0.22)
    # concrete pedestal and steel base plate
    p.box((0, 0, 0.06), (d + 0.12, w + 0.12, 0.12), M["coping"])
    p.box((0, 0, 0.13), (d + 0.06, w + 0.06, 0.02), st)
    # knee braces up into the girder (along Y)
    for sy in (-1, 1):
        for k in range(4):
            t = (k + 1) / 5
            p.box((0, sy * (w / 2 + 0.16 * t), h - 0.42 * (1 - t) - 0.02), (tw, 0.16 * 1.2 / 5 + 0.02, 0.42 * t + 0.04), st)
    objs = [p.obj("column")]
    # enamel name plate (black with white letters, Helvetica-style) at eye level
    if plate:
        for side in plates_on:
            sx = 1 if side == "+x" else -1
            pl = cube("col_plate", (sx * (d / 2 + 0.016), 0, 1.95), (0.012, 0.34, 0.42), _enamel_black(), bevel=0.004)
            objs.append(pl)
            for k, line in enumerate(plate):
                t = text(line, (sx * (d / 2 + 0.024), -0.13 * sx, 2.04 - k * 0.12), 0.085, "Inter_wght_500", _white(),
                         extrude=0.001, align="LEFT", rot=(R(90), 0, R(90 if sx > 0 else -90)))
                objs.append(t)
    return objs


# ---------------------------------------------------------------- ceiling
def _ibeam_y(part, m, x, y0, y1, ztop, depth=0.42, w=0.24, tf=0.02, tw=0.012):
    L, yc = y1 - y0, (y0 + y1) / 2
    part.box((x, yc, ztop - tf / 2), (w, L, tf), m)
    part.box((x, yc, ztop - depth + tf / 2), (w, L, tf), m)
    part.box((x, yc, ztop - depth / 2), (tw, L, depth - 2 * tf), m)


def _ibeam_x(part, m, x0, x1, y, ztop, depth=0.34, w=0.2, tf=0.018, tw=0.012):
    L, xc = x1 - x0, (x0 + x1) / 2
    part.box((xc, y, ztop - tf / 2), (L, w, tf), m)
    part.box((xc, y, ztop - depth + tf / 2), (L, w, tf), m)
    part.box((xc, y, ztop - depth / 2), (L, tw, depth - 2 * tf), m)


def ceiling_steel(M, y0, y1, ceil_z, wall_x, col_x, col_step, plat_inner, skip_side=0):
    """Steel under the ceiling slab: a girder over each column line, cross beams every
    column (shallow over the track so the train clears), a center girder, conduit runs
    with hangers, and round PA speakers. skip_side: leave out one side (stair opening)."""
    p = Part("ceiling_steel")
    st = M["column"]
    sides = [s for s in (-1, 1) if s != skip_side]
    for sx in sides:
        _ibeam_y(p, st, sx * col_x, y0, y1, ceil_z)
    _ibeam_y(p, st, 0.0, y0, y1, ceil_z, depth=0.2, w=0.18)
    yy = math.ceil(y0 / col_step) * col_step
    while yy < y1:
        for sx in sides:
            a, b = sorted((sx * plat_inner, sx * wall_x))
            _ibeam_x(p, st, a, b, yy, ceil_z)
        _ibeam_x(p, st, -plat_inner, plat_inner, yy, ceil_z, depth=0.18)
        yy += col_step
    objs = [p.obj("ceiling_steel")]
    # conduit: three runs along each platform, strapped to the slab
    c = Part("conduit")
    for sx in sides:
        for k, (dx, r, dz) in enumerate(((0.55, 0.028, 0.09), (0.75, 0.02, 0.07), (1.25, 0.035, 0.1))):
            x = sx * (col_x + dx)
            c.prism(circle(r, 10), "y", (x, (y0 + y1) / 2, ceil_z - dz), y1 - y0, M["conduit"])
            hy = y0 + 0.6
            while hy < y1:
                c.box((x, hy, ceil_z - dz / 2), (0.012, 0.02, dz), M["conduit"])
                hy += 1.5
        # PA speaker cans, one per bay
        sy = math.ceil(y0 / col_step) * col_step + col_step / 2
        while sy < y1:
            c.prism(circle(0.13, 16), "z", (sx * (col_x + 1.0), sy, ceil_z - 0.12), 0.16, M["housing"])
            c.prism(circle(0.1, 16), "z", (sx * (col_x + 1.0), sy, ceil_z - 0.205), 0.01, M["rubbing"])
            sy += col_step * 2
    objs.append(c.obj("conduit"))
    return objs


def fixture(M, x, y0, y1, ceil_z, drop=0.28, tubes=2):
    """Open fluorescent strip: steel channel on threaded hangers, bare tubes underneath."""
    p = Part("fixture")
    L, yc = y1 - y0 - 0.4, (y0 + y1) / 2
    z = ceil_z - drop
    p.box((x, yc, z), (0.13, L, 0.06), M["housing"])
    p.box((x, yc, z - 0.035), (0.17, L, 0.012), M["housing"])
    for k in range(tubes):
        p.prism(circle(0.014, 10), "y", (x + (k - (tubes - 1) / 2) * 0.06, yc, z - 0.06), L - 0.1, M["tube"])
    hy = y0 + 0.5
    while hy < y1 - 0.3:
        p.prism(circle(0.006, 6), "z", (x, hy, (ceil_z + z) / 2), drop, M["conduit"])
        hy += 2.4
    return [p.obj("fixture")]


# ---------------------------------------------------------------- track and edge
def coping(M, sx, y0, y1, plat_inner, plat_z):
    """Concrete edge coping outside the yellow strip and the dark face down to the track."""
    L, yc = y1 - y0, (y0 + y1) / 2
    return [cube("coping", (sx * (plat_inner + 0.0) , yc, plat_z + 0.004), (0.02, L, 0.008), M["coping"]),
            cube("rubbing", (sx * (plat_inner - 0.012), yc, plat_z - 0.18), (0.024, L, 0.36), M["rubbing"])]


def third_rail(M, sx, y0, y1, x=1.25):
    """Contact rail on insulators, under a wooden cover board on brackets."""
    p = Part("third_rail")
    L, yc = y1 - y0, (y0 + y1) / 2
    xr = sx * x
    p.box((xr, yc, -0.12), (0.07, L, 0.07), M["rail"])
    p.box((xr, yc, 0.0), (0.26, L, 0.025), M["cover"])
    yy = y0 + 0.4
    while yy < y1:
        p.box((xr + sx * 0.08, yy, -0.06), (0.03, 0.05, 0.12), M["rail"])
        p.box((xr, yy, -0.17), (0.06, 0.06, 0.05), mat("insulator", "#6b4a2f", 0.4))
        yy += 1.8
    return [p.obj("third_rail")]


# ---------------------------------------------------------------- furniture
def oak_bench(length=2.4, seats=4):
    """The classic divided oak bench (Museum, 14 St photos): laminated seat and back,
    solid arms, block dividers, two pedestal legs, wooden plugs over the tie rods.
    Along Y, seat facing -X, back against +X. Origin at floor center."""
    wood = oak()
    dark = oak("oak_end_grain", "#6e3a1c", "#93552d")
    o = []
    seat_d, seat_t, seat_z = 0.46, 0.07, 0.44
    o.append(cube("bench_seat", (0, 0, seat_z), (seat_d, length, seat_t), wood, bevel=0.012))
    # back: one deep laminated plank, leaning back slightly
    b = cube("bench_back", (seat_d / 2 - 0.02, 0, 0.72), (0.07, length, 0.34), wood, bevel=0.012)
    b.rotation_euler = (0, R(-8), 0)
    o.append(b)
    # arms at the ends
    for sy in (-1, 1):
        o.append(cube("bench_arm", (0.0, sy * (length / 2 - 0.05), seat_z + 0.13), (seat_d + 0.02, 0.1, 0.2), wood, bevel=0.01))
    # dividers between seats
    for k in range(1, seats):
        yy = -length / 2 + k * length / seats
        o.append(cube("bench_divider", (0.02, yy, seat_z + 0.1), (0.36, 0.08, 0.14), wood, bevel=0.01))
    # pedestal legs
    for sy in (-1, 1):
        o.append(cube("bench_leg", (0.02, sy * (length / 2 - 0.4), seat_z / 2 - 0.02), (0.36, 0.14, seat_z - 0.04), dark, bevel=0.01))
    # wooden plugs over the tie rods on the seat front
    for k in range(seats + 1):
        yy = -length / 2 + 0.12 + k * (length - 0.24) / seats
        o.append(cyl("bench_plug", (-seat_d / 2 - 0.002, yy, seat_z), 0.012, 0.006, dark, rot=(0, R(90), 0), verts=10))
    return o


def modern_bench(length=2.6, seats=4):
    """The newer bench (23 St photo): long oak seat and back on two steel posts,
    black steel loop armrests and dividers. Along Y, seat facing -X."""
    wood = oak("oak_new", "#a85d2c", "#d08a4a")
    steel = mat("bench_steel_black", "#1d1d1f", 0.35, metal=0.6, coat=0.3)
    o = []
    seat_z = 0.46
    o.append(cube("mb_seat", (0, 0, seat_z), (0.44, length, 0.05), wood, bevel=0.01))
    bk = cube("mb_back", (0.24, 0, 0.74), (0.045, length, 0.28), wood, bevel=0.01)
    bk.rotation_euler = (0, R(-10), 0)
    o.append(bk)
    for sy in (-1, 1):
        o.append(cube("mb_post", (0.06, sy * (length / 2 - 0.55), seat_z / 2), (0.07, 0.07, seat_z), steel))
        o.append(cube("mb_foot", (0.06, sy * (length / 2 - 0.55), 0.01), (0.28, 0.12, 0.02), steel))
    o.append(cube("mb_rail", (0.06, 0, seat_z - 0.05), (0.06, length - 0.4, 0.04), steel))
    # loop dividers / armrests: a flat steel loop standing on the seat
    for k in range(seats + 1):
        yy = -length / 2 + 0.04 + k * (length - 0.08) / seats
        p = Part("mb_loop")
        p.box((-0.02, yy, seat_z + 0.2), (0.36, 0.03, 0.025), steel)
        p.box((-0.19, yy, seat_z + 0.11), (0.025, 0.03, 0.2), steel)
        p.box((0.15, yy, seat_z + 0.11), (0.025, 0.03, 0.2), steel)
        o.append(p.obj("mb_loop"))
    return o


def trash_can():
    """Ribbed black can with a domed lid, the kind on every platform."""
    black = mat("can_black", "#222224", 0.55, coat=0.2)
    rim = mat("can_rim", "#2e2e31", 0.4, metal=0.4)
    o = [cyl("can", (0, 0, 0.42), 0.27, 0.84, black, verts=28)]
    for z in (0.12, 0.42, 0.72):
        o.append(cyl("can_rib", (0, 0, z), 0.282, 0.05, rim, verts=28))
    o.append(cyl("can_lid", (0, 0, 0.87), 0.29, 0.06, rim, verts=28))
    o.append(sphere("can_dome", (0, 0, 0.9), 0.24, black, seg=20))
    o[-1].scale = (1, 1, 0.3)
    return o


# ---------------------------------------------------------------- arrivals screens
def _screen_rows(rows, w, h, y, zc, glow):
    """Two-row countdown text, like the E Broadway screen: bullet, destination, minutes."""
    out = []
    for i, (label, sub, color, mins) in enumerate(rows):
        z = zc + h / 4 - i * h / 2
        out.append(cyl("scr_bullet", (-w / 2 + 0.12, y, z), 0.05, 0.004,
                       mat("glow_" + color, color, 0.4, emit=color, emit_str=1.5), rot=(R(90), 0, 0), verts=20))
        out.append(text(label[0], (-w / 2 + 0.12, y - 0.004, z), 0.06, "Inter_wght_800", _white(), extrude=0.001))
        out.append(text(label[1:], (-w / 2 + 0.22, y - 0.003, z + 0.02), 0.065, "Inter_wght_800", _white(), extrude=0.001, align="LEFT"))
        out.append(text(sub, (-w / 2 + 0.22, y - 0.003, z - 0.05), 0.04, "Inter_wght_500",
                        mat("scr_soft", "#c9dcff", 0.4, emit="#c9dcff", emit_str=1.2), extrude=0.001, align="LEFT"))
        out.append(text(mins, (w / 2 - 0.1, y - 0.003, z), 0.09, "Inter_wght_800", _white(), extrude=0.001, align="RIGHT"))
    return out


def countdown_screen(rows, w=1.5, h=0.42, rod=0.7):
    """Hanging LCD countdown clock: black bezel, blue screen. Faces -Y; origin at its center."""
    body = mat("clock_body", "#1a1b1e", 0.35, coat=0.4)
    screen = mat("clock_screen", "#123a7a", 0.3, emit="#1d4fa8", emit_str=1.4)
    steel = mat("rod_steel", "#a9adb3", 0.3, metal=0.85)
    o = [cube("clock_body", (0, 0.02, 0), (w + 0.1, 0.12, h + 0.12), body, bevel=0.015),
         cube("clock_screen", (0, -0.042, 0), (w, 0.005, h), screen)]
    o += _screen_rows(rows, w, h, -0.046, 0, screen)
    for sx in (-w / 3, w / 3):
        o.append(cyl("clock_rod", (sx, 0.02, h / 2 + 0.06 + rod / 2), 0.015, rod, steel, verts=10))
    return o


def kiosk(rows, title="Next trains"):
    """Standing arrivals kiosk (On-the-Go style): stainless post, tall portrait screen.
    Faces -Y; origin at the floor."""
    steel = mat("kiosk_steel", "#9ea3a8", 0.3, metal=1.0)
    body = mat("clock_body", "#1a1b1e", 0.35, coat=0.4)
    screen = mat("kiosk_screen", "#0f2550", 0.3, emit="#173a80", emit_str=1.1)
    o = [cube("kiosk_post", (0, 0.02, 0.45), (0.5, 0.18, 0.9), steel, bevel=0.01),
         cube("kiosk_foot", (0, 0.02, 0.02), (0.6, 0.3, 0.04), steel),
         cube("kiosk_body", (0, 0.02, 1.45), (0.72, 0.16, 1.15), body, bevel=0.02),
         cube("kiosk_screen", (0, -0.062, 1.45), (0.62, 0.005, 1.04), screen)]
    o.append(text(title, (-0.27, -0.066, 1.9), 0.045, "Inter_wght_800", _white(), extrude=0.001, align="LEFT"))
    # rows shrink to fit: up to 5 at full size, more get packed tighter
    st = min(0.13, 0.92 / max(1, len(rows)))
    k = st / 0.13
    for i, (label, sub, color, mins) in enumerate(rows):
        z = 1.83 - st / 2 - i * st
        o.append(cube("kiosk_row", (0, -0.065, z), (0.58, 0.002, 0.11 * k), mat("kiosk_row", "#1d3f86", 0.4, emit="#244a99", emit_str=1.0)))
        o.append(cyl("kiosk_bullet", (-0.24, -0.068, z), 0.035 * k, 0.003,
                     mat("glow_" + color, color, 0.4, emit=color, emit_str=1.5), rot=(R(90), 0, 0), verts=18))
        o.append(text(label[0], (-0.24, -0.071, z), 0.042 * k, "Inter_wght_800", _white(), extrude=0.001))
        o.append(text(label[1:], (-0.18, -0.07, z + 0.012 * k), 0.038 * k, "Inter_wght_800", _white(), extrude=0.001, align="LEFT"))
        o.append(text(sub, (-0.18, -0.07, z - 0.03 * k), 0.024 * k, "Inter_wght_500", _white(), extrude=0.001, align="LEFT"))
        o.append(text(mins, (0.26, -0.07, z), 0.05 * k, "Inter_wght_800", _white(), extrude=0.001, align="RIGHT"))
    return o


def band_tablet(label, w=0.9, h=0.22):
    """Small IND name tablet set into the color band: black tile, white block letters. Faces -Y."""
    black = square_tile("tablet_black", base="#151515", grout="#2a2a2a", size=0.054, gloss=0.05, jitter=0.02)
    white = mat("tablet_letters", "#f4f2ea", 0.2)
    return [cube("tablet", (0, 0, 0), (w, 0.02, h), black),
            text(label, (0, -0.012, 0), h * 0.6, "Inter_wght_800", white, extrude=0.002, spacing=1.1)]


# ---------------------------------------------------------------- platform end walls
def _arch(half=1.7, spring=3.0, crown=3.95, bottom=-0.7, seg=20):
    """Opening outline (x, z): straight jambs up to the springline, then a segmental arch
    whose crown clears the car roof (3.63 m) with the train passing through."""
    rr = (half ** 2 + (crown - spring) ** 2) / (2 * (crown - spring))
    zc = crown - rr
    a0 = math.atan2(spring - zc, half)
    pts = [(half, bottom)]
    for k in range(seg + 1):
        a = a0 + (math.pi - 2 * a0) * k / seg
        pts.append((rr * math.cos(a), zc + rr * math.sin(a)))
    pts.append((-half, bottom))
    return pts


def end_portal(M, y, s, wall_x, ceil_z, plat_z, tunnel=12.0):
    """A tiled end wall across the platform level at y (s = +1 far end, -1 near end), with an
    arched tunnel mouth over the track, a dark tunnel behind it and the rails running on."""
    t = 0.2
    yc = y + s * t / 2
    out = []
    w = cube("end_tile", (0, yc, (ceil_z - 0.7) / 2), (2 * wall_x + 0.2, t, ceil_z + 0.7), M["tile"])
    c = Part("arch_cut")
    c.prism(_arch(), "y", (0, yc, 0), t + 0.2, M["tile"])
    from props.train_util import cut
    cut(w, c.obj("arch_cut"))
    out.append(w)
    # the green band, dark base and a soffit ring follow the walls round, interrupted by the arch
    face = y - s * 0.02
    for sx in (-1, 1):
        x0, x1 = 1.85, wall_x
        xc, L = sx * (x0 + x1) / 2, x1 - x0
        out.append(cube("end_band", (xc, face, 3.55), (L, 0.04, 0.36), M["band"]))
        out.append(cube("end_trim", (xc, face, 3.3), (L, 0.03, 0.1), M["trim"]))
        out.append(cube("end_base", (xc, face, plat_z + 0.12), (L, 0.04, 0.24), M["base"]))
    ring = Part("arch_ring")
    pts = _arch()
    for (xa, za), (xb, zb) in zip(pts[1:-1], pts[2:-1]):
        mx, mz = (xa + xb) / 2, (za + zb) / 2
        L = math.hypot(xb - xa, zb - za) + 0.01
        ring.box((mx, face, mz), (L, 0.06, 0.14), M["band"], rot=(0, -math.atan2(zb - za, xb - xa), 0))
    out.append(ring.obj("arch_ring"))
    # the tunnel: an arch-shaped tube of dark concrete, track bed and rails carrying on
    dark = mat("tunnel_concrete", "#2d2a27", 0.95)
    tube = Part("tunnel")
    tube.prism([(x * 1.15, z + (0.15 if z > 0 else 0)) for x, z in _arch()], "y", (0, y + s * tunnel / 2, 0), tunnel, dark)
    tobj = tube.obj("tunnel")
    inner = Part("tunnel_in")
    inner.prism(_arch(), "y", (0, y + s * tunnel / 2, 0), tunnel + 0.5, dark)
    cut(tobj, inner.obj("tunnel_in"))
    out.append(tobj)
    yt = y + s * tunnel / 2
    out.append(cube("tun_bed", (0, yt, -0.45), (3.4, tunnel, 0.3), M["bed"]))
    for rx in (-0.72, 0.72):
        out.append(cube("tun_rail", (rx, yt, -0.16), (0.07, tunnel, 0.16), M["rail"]))
    out.append(cube("tun_back", (0, y + s * tunnel, 1.6), (4.4, 0.1, 5.0), mat("tunnel_black", "#0b0a09", 1.0)))
    # a red signal lamp beside the mouth, like the one at W 4 St
    out.append(cube("signal_box", (-1.55, y + s * 0.4, 2.6), (0.18, 0.12, 0.42), mat("signal_body", "#1a1a1a", 0.5)))
    out.append(cyl("signal_red", (-1.55, y + s * 0.4 - s * 0.065, 2.7), 0.05, 0.01,
                   mat("signal_red", "#ff3b30", 0.3, emit="#ff2a1f", emit_str=6), rot=(R(90), 0, 0), verts=16))
    out.append(cyl("signal_green", (-1.55, y + s * 0.4 - s * 0.065, 2.52), 0.05, 0.01,
                   mat("signal_green", "#3ad96b", 0.3, emit="#2fd060", emit_str=3), rot=(R(90), 0, 0), verts=16))
    return out
