"""Export the arriving train (three cars) to public/subway/train.glb.

The train moves in the browser, so it keeps plain PBR materials and is lit live
instead of baked.  python blender/build_train.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from common import *
from props import train

ROOT = os.path.dirname(HERE)

if __name__ == "__main__":
    reset()
    objs = []
    for k in range(3):
        parts = train.car(front=(k == 0))
        objs.append(group(parts, (0, k * (train.L_CAR + 0.6), 0), name="car_%d" % k))
    # bake bevels/text into meshes so glTF gets the final shapes
    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.context.scene.objects:
        if o.type in ("MESH", "CURVE", "FONT"):
            o.select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.select_all(action="SELECT")
    out = os.path.join(ROOT, "public", "subway", "train.glb")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_apply=True, export_yup=True)
    print("wrote", out)
