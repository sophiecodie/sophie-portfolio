"""Preview stills of the realistic station without baking.

  python blender/preview_realism.py [samples] [out_dir] [views...]
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from common import *
import build_dollhouse as B
from layout_dollhouse import *

VIEWS = {
    "title": None, "project:new-york-census": None,
    # close looks at the new detail
    "column": ((-0.4, 10.2, 1.5), (2.45, 15.0, 1.7), 45),
    "edge": ((2.6, 13.0, 1.2), (1.9, 15.5, 0.15), 50),
    "bench": ((2.6, 10.8, 1.2), (4.6, 12.5, 0.6), 50),
    "ceiling": ((3.2, 9.0, 1.6), (2.0, 15.0, 3.9), 50),
    "kiosk": ((1.5, 14.5, 1.6), (-3.5, 19.5, 1.4), 45),
    "portal_far": ((3.4, 30.0, 1.7), (0.0, 40.0, 1.8), 40),
    "portal_near": ((-1.0, 8.0, 1.7), (0.5, -4.0, 1.8), 45),
    "mezz": ((-1.5, 4.0, 6.1), (4.5, 14.0, 5.9), 40),
    "train_front": ((0.9, TRAIN_STOP_Y - 5.5, 1.5), (0.0, TRAIN_STOP_Y, 1.7), 40),
    "train_3q": ((3.6, TRAIN_STOP_Y - 3.0, 1.6), (0.3, TRAIN_STOP_Y + 4.0, 1.6), 35),
}


def run(samples, out, names):
    B.assemble()
    render_setup(960, 600, samples)
    os.makedirs(out, exist_ok=True)
    st = stops()
    import build_train
    for name in names:
        before = set(o.name for o in bpy.data.objects)
        if name.startswith("project:") or name.startswith("train"):
            build_train.make_train(TRAIN_STOP_Y)
        if VIEWS.get(name):
            pos, look, lens = VIEWS[name]
            cam = camera(pos, look, lens=lens)
        else:
            cam = B._camera(st[name])
        render(os.path.join(out, "real_" + name.replace(":", "_") + ".png"))
        bpy.data.objects.remove(cam)
        for o in [o for o in bpy.data.objects if o.name not in before and o.type != "CAMERA"]:
            bpy.data.objects.remove(o)
        print("rendered", name, flush=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    run(int(a[0]) if a else 16, a[1] if len(a) > 1 else os.path.join(HERE, "renders"), a[2:] or list(VIEWS))
