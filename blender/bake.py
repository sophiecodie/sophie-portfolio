"""Bake Cycles lighting into texture atlases and export a glTF.

Every static object is converted to a mesh and joined into one object per
CHUNK-long slice of the station. Each slice gets a lightmap UV and three bakes:

  color  surface color without light (noise free, 1 sample)
  light  direct + bounce light from Cycles (noisy, so it is denoised with an
         island-aware blur; light changes slowly, so detail survives)
  glow   emission from lamps, signs and the arrivals board (1 sample)

They are combined as color * light + glow into one atlas per slice. In the
browser the slices render unlit, so the soft bounce light comes for free.
"""
import bpy, os, time
import numpy as np
from layout import CHUNK, STATION_START, STATION_END


def _prep():
    bpy.ops.object.select_all(action="DESELECT")
    for o in list(bpy.context.scene.objects):
        if o.type in ("CURVE", "FONT", "MESH"):
            o.select_set(True)
    bpy.context.view_layer.objects.active = next(o for o in bpy.context.selected_objects)
    bpy.ops.object.convert(target="MESH")          # applies bevels, text, curves
    for o in bpy.context.selected_objects:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    for o in list(bpy.context.scene.objects):
        if o.type == "EMPTY":
            bpy.data.objects.remove(o)


def _chunks():
    groups = {}
    for o in bpy.context.scene.objects:
        if o.type != "MESH":
            continue
        ys = [(o.matrix_world @ v.co).y for v in o.data.vertices] or [o.location.y]
        yc = (min(ys) + max(ys)) / 2
        yc = min(max(yc, STATION_START + 0.1), STATION_END - 0.1)   # tunnels join the end slices
        k = int((yc + 1000) // CHUNK) - int(1000 // CHUNK)
        groups.setdefault(k, []).append(o)
    out = []
    for k, objs in sorted(groups.items()):
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.join()
        j = bpy.context.view_layer.objects.active
        j.name = "chunk_%02d" % (k + 2)
        out.append(j)
    return out


def _uv(o):
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o
    for uv in list(o.data.uv_layers):
        o.data.uv_layers.remove(uv)
    o.data.uv_layers.new(name="bake")
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.003, area_weight=0.6, scale_to_bounds=True)
    bpy.ops.uv.pack_islands(margin=0.003, rotate=True)
    bpy.ops.object.mode_set(mode="OBJECT")


def bake_and_export(path, res=2048, samples=96):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
    sc.cycles.samples = samples; sc.cycles.use_denoising = False
    sc.render.bake.margin = 6
    sc.render.bake.use_pass_direct = True; sc.render.bake.use_pass_indirect = True
    _prep()
    chunks = _chunks()
    tex_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders", "bake"); os.makedirs(tex_dir, exist_ok=True)
    baked = {}
    passes = {}
    t0 = time.time()
    for o in chunks:
        _uv(o)
        for kind in ("color", "light", "glow"):
            passes[(o.name, kind)] = bpy.data.images.new("%s_%s" % (o.name, kind), res, res, alpha=False, float_buffer=True)
        # private copies of the materials so each slice can bake into its own atlas
        for i, m in enumerate(list(o.data.materials)):
            mc = m.copy(); o.data.materials[i] = mc
            node = mc.node_tree.nodes.new("ShaderNodeTexImage"); node.name = "BAKE"
    print("[bake] unwrapped %d slices in %.0fs" % (len(chunks), time.time() - t0), flush=True)

    def run(kind, btype, filt, smp):
        for o in chunks:
            for m in o.data.materials:
                node = m.node_tree.nodes["BAKE"]; node.image = passes[(o.name, kind)]; m.node_tree.nodes.active = node
        bpy.ops.object.select_all(action="DESELECT")
        for o in chunks:
            o.select_set(True)
        bpy.context.view_layer.objects.active = chunks[0]
        sc.cycles.samples = smp
        t = time.time()
        bpy.ops.object.bake(type=btype, pass_filter=filt, use_clear=True)
        print("[bake] %s pass in %.0fs" % (kind, time.time() - t), flush=True)

    run("color", "DIFFUSE", {"COLOR"}, 1)
    run("glow", "EMIT", set(), 1)
    run("light", "DIFFUSE", {"DIRECT", "INDIRECT"}, samples)

    def px(img):
        a = np.empty(res * res * 4, dtype=np.float32); img.pixels.foreach_get(a)
        return a.reshape(res, res, 4)[..., :3]

    def blur(a, r):
        k = np.exp(-0.5 * (np.arange(-3 * r, 3 * r + 1) / r) ** 2); k /= k.sum()
        for ax in (0, 1):
            a = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), ax, a) if a.ndim == 2 else \
                np.stack([np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), ax, a[..., c]) for c in range(a.shape[-1])], -1)
        return a

    for o in chunks:  # keep the raw passes so a later failure can't cost a re-bake
        for kind in ("color", "light", "glow"):
            np.save(os.path.join(tex_dir, "%s_%s.npy" % (o.name, kind)), px(passes[(o.name, kind)]).astype(np.float16))
    for o in chunks:
        col = px(passes[(o.name, "color")]); lit = px(passes[(o.name, "light")]); glow = px(passes[(o.name, "glow")])
        mask = (col.max(-1) > 0.0005).astype(np.float32)
        # island-aware denoise: normalized blur so empty atlas space doesn't darken edges
        r = max(1.0, res / 1024)
        lit_s = blur(lit * mask[..., None], r) / np.maximum(blur(mask, r), 1e-4)[..., None]
        out = np.clip(col * lit_s + glow, 0, 1)
        out = np.where(out <= 0.0031308, 12.92 * out, 1.055 * np.power(out, 1 / 2.4) - 0.055)  # linear -> sRGB
        img = bpy.data.images.new(o.name, res, res, alpha=False)
        rgba = np.concatenate([out, np.ones((res, res, 1))], -1).astype(np.float32)
        img.pixels.foreach_set(rgba.ravel())
        img.filepath_raw = os.path.join(tex_dir, o.name + ".png"); img.file_format = "PNG"; img.save()
        baked[o.name] = img
    print("[bake] combined atlases", flush=True)
    # swap to one plain material per chunk that just shows the atlas
    for o in chunks:
        m = bpy.data.materials.new(o.name + "_baked"); m.use_nodes = True
        nt = m.node_tree; p = nt.nodes["Principled BSDF"]
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = baked[o.name]
        nt.links.new(t.outputs["Color"], p.inputs["Base Color"])
        p.inputs["Roughness"].default_value = 1.0
        o.data.materials.clear(); o.data.materials.append(m)
    bpy.ops.object.select_all(action="DESELECT")
    for o in chunks:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True,
                              export_image_format="JPEG", export_jpeg_quality=86,
                              export_apply=True, export_texcoords=True, export_normals=False,
                              export_materials="EXPORT", export_yup=True)
    print("[bake] wrote", path, flush=True)
