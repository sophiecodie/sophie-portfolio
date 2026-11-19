"""Build the arriving train (three cars) and either export public/subway/train.glb or
render preview stills.

  python blender/build_train.py                 # export public/subway/train.glb
  python blender/build_train.py preview [n]     # stills -> blender/renders/train_*.png

The train moves in the browser, so it keeps plain PBR materials and is lit live.
The glTF origin is the front of car 0 at rail level, which matches scene.ts
(placeTrain moves the train along the track by its front).
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from common import *
from props import train, station_shell
from props.train_util import tris
import build_station

ROOT = os.path.dirname(HERE)
RENDERS = os.path.join(HERE, "renders")
TRAIN_Y = 10.5        # where the front of the arriving train stops (scene.ts trainTo)
CAR_GAP = 0.6


def make_train(front_y=0.0):
    """Three cars, front car first. Each car's objects are prefixed car<k>_ so names stay unique."""
    groups = []
    for k in range(3):
        objs = train.car(front=(k == 0), route="S", color="#e8732c", seed=k, coupler=(k < 2))
        for o in objs:
            o.name = "car%d_%s" % (k, re.sub(r"\.\d+$", "", o.name))
        groups.append(group(objs, (0, front_y + k * (train.L_CAR + CAR_GAP), 0), name="car_%d" % k))
    return groups


def convert_text():
    """Sign and number text becomes plain mesh, so the glTF carries the final shapes."""
    fonts = [o for o in bpy.data.objects if o.type == "FONT"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in fonts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = fonts[0]
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.select_all(action="DESELECT")


def report():
    per_car = {}
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name.startswith("car0_"):
            per_car[o.name] = tris(o)
    total = sum(per_car.values())
    for name, n in sorted(per_car.items(), key=lambda kv: -kv[1]):
        print("  %-28s %6d tris" % (name, n))
    print("car 0 total: %d tris (budget 60000 per car)" % total)


def export():
    reset()
    make_train(0.0)
    convert_text()
    report()
    bpy.ops.object.select_all(action="SELECT")
    out = os.path.join(ROOT, "public", "subway", "train.glb")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_apply=True, export_yup=True)
    print("wrote", out)


def preview(samples=32):
    """Renders the train at the title stop, on a platform stub with the station lights."""
    reset()
    m = station_shell.materials()
    for y in range(-10, 60, 10):
        station_shell.segment(m, y, y + 10)
    build_station.lights()
    make_train(TRAIN_Y)
    convert_text()
    report()
    render_setup(960, 600, samples)
    os.makedirs(RENDERS, exist_ok=True)
    views = {
        # 3/4 view from the platform
        "train_3q": ((3.4, 4.0, 1.7), (0.0, 13.0, 1.6), 35),
        # front-on, from the far end of the platform
        "train_front": ((0.0, 3.0, 1.6), (0.0, 12.0, 1.6), 35),
        # close-up of the first truck, from the track-level gap beside the car
        # (the platform edge is as high as the trucks, so it hides them from above)
        "train_truck": ((1.5, 11.4, 0.04), (0.7, 13.5, 0.05), 50),
        # through the side window of the first car
        "train_window": ((3.2, 14.73, 1.95), (0.0, 14.73, 2.0), 40),
    }
    for name, (pos, look, lens) in views.items():
        cam = camera(pos, look, lens=lens)
        render(os.path.join(RENDERS, name + ".png"))
        bpy.data.objects.remove(cam)
        print("rendered", name)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if args and args[0] == "preview":
        preview(int(args[1]) if len(args) > 1 else 32)
    else:
        export()
