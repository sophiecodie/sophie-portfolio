"""
Bake the street-floor backdrops: resize each photo and make its depth map with
Depth Anything V2 (Small, Apache-2.0), the same trick Felix Rieseberg used for his "view outside".

    pip install torch transformers pillow numpy
    python scripts/street_depth.py path/to/sunny.jpg path/to/rainy.jpg

The output file names come from the input names (a trailing "-orig" is dropped).

Writes public/street/<name>.jpg (2560 px wide) and public/street/<name>-depth.png
(1280 px wide, white = near, black = far) next to each other.
"""
import os, sys, pathlib
import numpy as np
from PIL import Image, ImageFilter
from transformers import pipeline

OUT = pathlib.Path(__file__).resolve().parent.parent / "public" / "street"
if len(sys.argv) > 1 and sys.argv[1].startswith("--out="):
    OUT = pathlib.Path(sys.argv.pop(1)[6:])
OUT.mkdir(parents=True, exist_ok=True)

pipe = pipeline("depth-estimation", model=os.environ.get("DAV2_MODEL", "depth-anything/Depth-Anything-V2-Small-hf"))

for src in sys.argv[1:]:
    name = pathlib.Path(src).stem.replace("-orig", "")
    img = Image.open(src).convert("RGB")
    photo = img.resize((2560, round(2560 * img.height / img.width)), Image.LANCZOS)
    photo.save(OUT / f"{name}.jpg", quality=84, optimize=True, progressive=True)

    # run the model a bit above its native 518 px so thin things (lamp posts, fire escapes) survive
    pipe.image_processor.size = {"height": 770, "width": 770}
    d = np.asarray(pipe(photo)["predicted_depth"].squeeze().cpu().numpy(), dtype=np.float32)
    lo, hi = np.percentile(d, 1), np.percentile(d, 99.5)
    d = np.clip((d - lo) / (hi - lo), 0, 1)
    dm = Image.fromarray((d * 255).astype(np.uint8)).resize((1280, round(1280 * photo.height / photo.width)), Image.BICUBIC)
    # a soft blur hides stair-step edges when the shader shifts pixels
    dm.filter(ImageFilter.GaussianBlur(1.2)).save(OUT / f"{name}-depth.png", optimize=True)
    print(name, photo.size, dm.size)
