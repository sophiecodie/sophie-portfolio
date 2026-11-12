"""Light bake for the dollhouse: one atlas per level and per 20 m slice.

bake.py slices the station along Y only, so the platform, the mezzanine and the street
would share atlases. This file also groups by level (taken from each object's height),
and it keeps the fourth wall (objects named fw_*) in its own chunks, named fourth_wall_*,
so the site can hide them. The passes and the denoise are the same as bake.py, and
bake.py itself is not changed. Its _prep and _uv helpers are reused as they are.
"""
import bpy, os, time
import numpy as np
from bake import _prep, _uv
from layout_dollhouse import DH_START, DH_END, MEZ_CEIL
from common import HERE

SLICE = 20.0


def level_of(z):
    if z < -0.8:
        return "ground"
    if z < 4.1:
        return "platform"
    if z < MEZ_CEIL - 0.02:
        return "mezzanine"
    return "street"


def _chunks():
    """Group the scene's meshes into (fourth wall?, level, slice) chunks and join each one."""
    groups = {}
    for o in bpy.context.scene.objects:
        if o.type != "MESH":
            continue
        pts = [o.matrix_world @ v.co for v in o.data.vertices] or [o.location]
        ys = [p.y for p in pts]
        zs = [p.z for p in pts]
        yc = min(max((min(ys) + max(ys)) / 2, DH_START + 0.1), DH_END - 0.1)
        zc = (min(zs) + max(zs)) / 2
        k = int((yc - DH_START) // SLICE)
        groups.setdefault((o.name.startswith("fw_"), level_of(zc), k), []).append(o)
    out = []
    for (fw, lvl, k), objs in sorted(groups.items()):
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.join()
        j = bpy.context.view_layer.objects.active
        j.name = ("fourth_wall" if fw else "main") + "_%s_%d" % (lvl, k)
        j.data.name = j.name   # so the glTF node and mesh carry the chunk name too
        # the fourth wall is only seen up close, so a smaller atlas is enough
        out.append((j, fw))
    return out


def bake_levels_and_export(path, res=2048, samples=96):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = False
    sc.render.bake.margin = 6
    sc.render.bake.use_pass_direct = True
    sc.render.bake.use_pass_indirect = True
    _prep()
    chunks = _chunks()
    res_of = {}
    for o, fw in chunks:
        res_of[o.name] = res // 2 if fw else res
    tex_dir = os.path.join(HERE, "renders", "bake_dollhouse")
    os.makedirs(tex_dir, exist_ok=True)
    passes = {}
    t0 = time.time()
    for o, _ in chunks:
        _uv(o)
        r = res_of[o.name]
        for kind in ("color", "light", "glow"):
            passes[(o.name, kind)] = bpy.data.images.new("%s_%s" % (o.name, kind), r, r, alpha=False, float_buffer=True)
        # private material copies so each chunk bakes into its own atlas
        for i, mt in enumerate(list(o.data.materials)):
            mc = mt.copy()
            o.data.materials[i] = mc
            node = mc.node_tree.nodes.new("ShaderNodeTexImage")
            node.name = "BAKE"
    print("[bake] unwrapped %d chunks in %.0fs" % (len(chunks), time.time() - t0), flush=True)

    def run(kind, btype, filt, smp):
        for o, _ in chunks:
            for mt in o.data.materials:
                node = mt.node_tree.nodes["BAKE"]
                node.image = passes[(o.name, kind)]
                mt.node_tree.nodes.active = node
        bpy.ops.object.select_all(action="DESELECT")
        for o, _ in chunks:
            o.select_set(True)
        bpy.context.view_layer.objects.active = chunks[0][0]
        sc.cycles.samples = smp
        t = time.time()
        bpy.ops.object.bake(type=btype, pass_filter=filt, use_clear=True)
        print("[bake] %s pass in %.0fs" % (kind, time.time() - t), flush=True)

    run("color", "DIFFUSE", {"COLOR"}, 1)
    run("glow", "EMIT", set(), 1)
    run("light", "DIFFUSE", {"DIRECT", "INDIRECT"}, samples)

    def px(img, r):
        a = np.empty(r * r * 4, dtype=np.float32)
        img.pixels.foreach_get(a)
        return a.reshape(r, r, 4)[..., :3]

    def blur(a, r):
        k = np.exp(-0.5 * (np.arange(-3 * r, 3 * r + 1) / r) ** 2)
        k /= k.sum()
        for ax in (0, 1):
            a = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), ax, a) if a.ndim == 2 else \
                np.stack([np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), ax, a[..., c]) for c in range(a.shape[-1])], -1)
        return a

    for o, _ in chunks:  # keep the raw passes so a later failure can't cost a re-bake
        r = res_of[o.name]
        for kind in ("color", "light", "glow"):
            np.save(os.path.join(tex_dir, "%s_%s.npy" % (o.name, kind)), px(passes[(o.name, kind)], r).astype(np.float16))
    baked = {}
    for o, _ in chunks:
        r = res_of[o.name]
        col = px(passes[(o.name, "color")], r)
        lit = px(passes[(o.name, "light")], r)
        glow = px(passes[(o.name, "glow")], r)
        mask = (col.max(-1) > 0.0005).astype(np.float32)
        # island-aware denoise: normalized blur so empty atlas space doesn't darken edges
        rad = max(1.0, r / 1024)
        lit_s = blur(lit * mask[..., None], rad) / np.maximum(blur(mask, rad), 1e-4)[..., None]
        out = np.clip(col * lit_s + glow, 0, 1)
        out = np.where(out <= 0.0031308, 12.92 * out, 1.055 * np.power(out, 1 / 2.4) - 0.055)  # linear -> sRGB
        img = bpy.data.images.new(o.name, r, r, alpha=False)
        rgba = np.concatenate([out, np.ones((r, r, 1))], -1).astype(np.float32)
        img.pixels.foreach_set(rgba.ravel())
        img.filepath_raw = os.path.join(tex_dir, o.name + ".png")
        img.file_format = "PNG"
        img.save()
        baked[o.name] = img
    print("[bake] combined atlases", flush=True)
    # one plain material per chunk that just shows its atlas
    for o, _ in chunks:
        m = bpy.data.materials.new(o.name + "_baked")
        m.use_nodes = True
        nt = m.node_tree
        p = nt.nodes["Principled BSDF"]
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = baked[o.name]
        nt.links.new(t.outputs["Color"], p.inputs["Base Color"])
        p.inputs["Roughness"].default_value = 1.0
        o.data.materials.clear()
        o.data.materials.append(m)
    bpy.ops.object.select_all(action="DESELECT")
    for o, _ in chunks:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True,
                              export_image_format="JPEG", export_jpeg_quality=86,
                              export_apply=True, export_texcoords=True, export_normals=False,
                              export_materials="EXPORT", export_yup=True)
    print("[bake] wrote", path, flush=True)
