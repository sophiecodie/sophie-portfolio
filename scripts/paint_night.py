"""
Paint a quiet NYC night for the street floor: sky, a far skyline, a row of brownstones with
water towers, park trees and a few lamps. Everything is drawn in layers, so the depth map is
exact (no model needed). Writes night.jpg and night-depth.png (white = near).

    python scripts/paint_night.py [--seed N] [--out DIR]   (needs numpy + pillow)
"""
import argparse, math, pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument("--seed", type=int, default=7)
ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent.parent / "public" / "street"))
ap.add_argument("--name", default="night")
ap.add_argument("--w", type=int, default=6144)
ap.add_argument("--h", type=int, default=1280)
A = ap.parse_args()
W, H = A.w, A.h
rng = np.random.default_rng(A.seed)
S = H / 1280  # scale for sizes

def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255

img = np.zeros((H, W, 3), np.float32)
depth = np.zeros((H, W), np.float32)
glow = np.zeros((H, W, 3), np.float32)  # light that will be bloomed

# ---------------------------------------------------------------- sky
y = np.linspace(0, 1, H)[:, None]
top, mid, low = hexc("#070b18"), hexc("#16203a"), hexc("#3b3550")
sky = np.where(y < 0.55, top + (mid - top) * (y / 0.55), mid + (low - mid) * ((y - 0.55) / 0.45))
img[:] = np.broadcast_to(sky[..., :], (H, W, 3)) if sky.ndim == 3 else sky[:, None, :]
# a warm city haze near the horizon
hz = np.exp(-((y - 0.78) / 0.12) ** 2)
img += hz[..., None] * hexc("#3a2a2a") * 0.55
# stars, sparse and faint
n = int(900 * S * S)
sx, sy = rng.integers(0, W, n), (rng.random(n) ** 1.6 * H * 0.6).astype(int)
b = rng.random(n) ** 3 * 0.55
img[sy, sx] += b[:, None] * hexc("#cfd8ff")
# moon with a soft halo
mx, my, mr = int(W * 0.62), int(H * 0.34), int(30 * S)
yy, xx = np.mgrid[0:H, 0:W]
d = np.hypot(xx - mx, yy - my)
img += (np.exp(-(d / (mr * 7)) ** 2) * 0.10)[..., None] * hexc("#c9d4ff")
moon = np.clip((mr - d) / 1.5, 0, 1)
img = img * (1 - moon[..., None]) + moon[..., None] * hexc("#f3efe2")

def layer(mask_img, color, z, windows=None):
    """Composite a silhouette mask (L image) with flat color at depth z."""
    m = np.asarray(mask_img, np.float32) / 255
    img[:] = img * (1 - m[..., None]) + m[..., None] * color
    depth[:] = np.maximum(depth, m * z)
    return m

def windows_on(rects, density, warm, size, z, rows_gap, cols_gap, mask):
    """Light some windows inside each building rect."""
    for (x0, y0, x1, y1) in rects:
        wx, wy = size
        for yy0 in range(int(y0 + rows_gap * 0.6), int(y1 - wy), int(rows_gap)):
            for xx0 in range(int(x0 + cols_gap * 0.4), int(x1 - wx), int(cols_gap)):
                if rng.random() > density:
                    continue
                c = warm * (0.55 + 0.45 * rng.random())
                if rng.random() < 0.15:
                    c = hexc("#a9c4ff") * 0.5  # a cool TV glow here and there
                ys, xs = slice(yy0, yy0 + wy), slice(xx0, xx0 + wx)
                if mask[ys, xs].size == 0 or mask[ys, xs].mean() < 0.9:
                    continue
                img[ys, xs] = c
                glow[ys, xs] += c * 0.9

# ---------------------------------------------------------------- far skyline
base_far = int(H * 0.80)
far = Image.new("L", (W, H), 0)
fd = ImageDraw.Draw(far)
rects = []
x = -20
while x < W:
    bw = int(rng.integers(60, 190) * S)
    bh = int((rng.random() ** 1.7 * 330 + 90) * S)
    if rng.random() < 0.08:
        bh = int(rng.integers(420, 560) * S)  # an occasional tower
    fd.rectangle([x, base_far - bh, x + bw, H], fill=255)
    if bh > 380 * S:  # setbacks and a spire
        fd.rectangle([x + bw * 0.2, base_far - bh - 50 * S, x + bw * 0.8, base_far - bh], fill=255)
        fd.rectangle([x + bw * 0.42, base_far - bh - 120 * S, x + bw * 0.58, base_far - bh - 50 * S], fill=255)
        fd.line([x + bw * 0.5, base_far - bh - 200 * S, x + bw * 0.5, base_far - bh - 120 * S], fill=255, width=max(2, int(4 * S)))
    rects.append((x, base_far - bh, x + bw, base_far))
    x += bw + int(rng.integers(-10, 25) * S)
far = far.filter(ImageFilter.GaussianBlur(1.2 * S))
m_far = layer(far, hexc("#1b2238"), 0.08)
windows_on(rects, 0.16, hexc("#ffcf8a") * 0.75, (max(2, int(5 * S)), max(2, int(7 * S))), 0.08, 16 * S, 13 * S, m_far)
# atmospheric haze over the far layer
img[:] = img * 0.86 + hexc("#2a2c45") * 0.14 * m_far[..., None]

# ---------------------------------------------------------------- brownstones with water towers
base_mid = int(H * 0.86)
mid_mask = Image.new("L", (W, H), 0)
md = ImageDraw.Draw(mid_mask)
mrects = []
x = -10
while x < W:
    bw = int(rng.integers(150, 260) * S)
    bh = int(rng.integers(230, 330) * S)
    top_y = base_mid - bh
    md.rectangle([x, top_y, x + bw, H], fill=255)
    md.rectangle([x - 4 * S, top_y - 10 * S, x + bw + 4 * S, top_y], fill=255)  # cornice
    if rng.random() < 0.45:  # a water tower on the roof
        tx = x + bw * rng.uniform(0.2, 0.7)
        tw, th = 42 * S, 52 * S
        legs = 34 * S
        md.rectangle([tx, top_y - legs - th, tx + tw, top_y - legs], fill=255)
        md.polygon([(tx - 4 * S, top_y - legs - th), (tx + tw / 2, top_y - legs - th - 26 * S), (tx + tw + 4 * S, top_y - legs - th)], fill=255)
        for lx in (tx + 4 * S, tx + tw - 6 * S):
            md.rectangle([lx, top_y - legs, lx + 3 * S, top_y], fill=255)
        md.line([tx + 4 * S, top_y - legs * 0.5, tx + tw - 4 * S, top_y - legs * 0.5], fill=255, width=max(1, int(2 * S)))
    mrects.append((x, top_y, x + bw, base_mid))
    x += bw + int(rng.integers(0, 6) * S)
mid_mask = mid_mask.filter(ImageFilter.GaussianBlur(0.8 * S))
m_mid = layer(mid_mask, hexc("#141823"), 0.32)
# each building a slightly different brick or stone tone
for (x0, y0, x1, y1) in mrects:
    tone = [hexc("#1d1619"), hexc("#171a24"), hexc("#1f1a17"), hexc("#141a1f")][rng.integers(0, 4)]
    xs = slice(max(0, int(x0)), min(W, int(x1)))
    img[:, xs] = img[:, xs] * (1 - m_mid[:, xs, None]) + m_mid[:, xs, None] * tone
# brick warmth: a faint vertical texture
img += (m_mid * 0.012 * np.sin(xx / (3.1 * S)))[..., None] * hexc("#ff9a6a")
windows_on(mrects, 0.30, hexc("#ffc979"), (max(3, int(17 * S)), max(4, int(26 * S))), 0.32, 52 * S, 40 * S, m_mid)
# fire escapes on some fronts: thin dark railings and zigzag stairs
fe = Image.new("L", (W, H), 0); fdw = ImageDraw.Draw(fe)
for (x0, y0, x1, y1) in mrects:
    if rng.random() < 0.4:
        cx = x0 + (x1 - x0) * rng.uniform(0.3, 0.6); half = 46 * S
        for fy in np.arange(y0 + 70 * S, y1 - 40 * S, 52 * S):
            fdw.line([cx - half, fy, cx + half, fy], fill=255, width=max(1, int(3 * S)))
            fdw.line([cx - half, fy - 14 * S, cx + half, fy - 14 * S], fill=170, width=max(1, int(1.5 * S)))
            fdw.line([cx - half * 0.8, fy, cx + half * 0.6, fy + 52 * S], fill=200, width=max(1, int(2 * S)))
layer(fe, hexc("#07080b"), 0.34)

# ---------------------------------------------------------------- park trees
trees = Image.new("L", (W, H), 0)
td = ImageDraw.Draw(trees)
base_tree = int(H * 0.97)
x = int(rng.integers(0, 120) * S)
tree_spots = []
while x < W + 100 * S:
    r = rng.integers(80, 175) * S
    cy = base_tree - r * rng.uniform(1.7, 2.2)
    # trunk
    td.rectangle([x - 7 * S, cy, x + 7 * S, H], fill=255)
    # canopy: a cloud of blobs
    for _ in range(int(90)):
        a = rng.uniform(0, 2 * math.pi)
        rr = r * math.sqrt(rng.random()) * 0.85
        bx, by = x + math.cos(a) * rr * 1.15, cy + math.sin(a) * rr * 0.85
        br = r * rng.uniform(0.12, 0.30)
        td.ellipse([bx - br, by - br, bx + br, by + br], fill=255)
    tree_spots.append((x, cy, r))
    x += int(rng.integers(170, 330) * S)
trees = trees.filter(ImageFilter.GaussianBlur(1.5 * S))
m_tree = layer(trees, hexc("#0c1512"), 0.62)
# leafy mottling so canopies read as foliage, not blobs
mot = rng.random((H // 6 + 1, W // 6 + 1)).astype(np.float32)
mot = np.asarray(Image.fromarray((mot * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
img += (m_tree * (mot - 0.5) * 0.05)[..., None] * hexc("#7fa08a")
glow *= (1 - m_tree)[..., None]

# ---------------------------------------------------------------- lamps between the trees
lamp_glow = np.zeros((H, W), np.float32)
lamps = Image.new("L", (W, H), 0)
ld = ImageDraw.Draw(lamps)
for (tx, cy, r) in tree_spots:
    lx = tx + int(rng.uniform(0.45, 0.6) * 260 * S)
    if lx > W or rng.random() < 0.55: continue
    top_l = base_tree - 200 * S
    ld.rectangle([lx - 3 * S, top_l, lx + 3 * S, H], fill=255)
    ld.ellipse([lx - 12 * S, top_l - 24 * S, lx + 12 * S, top_l], fill=255)
    lamp_glow += np.exp(-(np.hypot(xx - lx, yy - (top_l - 12 * S)) / (14 * S)) ** 2)
m_lamp = layer(lamps.filter(ImageFilter.GaussianBlur(0.6 * S)), hexc("#0b0f12"), 0.75)
img += lamp_glow[..., None] * hexc("#ffdca0") * 1.0
glow += lamp_glow[..., None] * hexc("#ffc77a") * 1.6
# lamplight catching the canopies
lit = np.zeros((H, W), np.float32)
for (tx, cy, r) in tree_spots:
    lit += np.exp(-(np.hypot(xx - (tx + 140 * S), yy - (cy + r * 0.4)) / (r * 1.4)) ** 2)
img += (m_tree * np.clip(lit, 0, 1) * 0.10)[..., None] * hexc("#c8a060")
edge = np.clip(m_tree - np.roll(m_tree, int(6 * S), axis=0), 0, 1)
img += (edge * 0.05)[..., None] * hexc("#9fb4d8")

# ---------------------------------------------------------------- bloom, grade, grain
g = Image.fromarray((np.clip(glow, 0, 1) * 255).astype(np.uint8))
bloom = sum(np.asarray(g.filter(ImageFilter.GaussianBlur(r * S)), np.float32) / 255 * k for r, k in ((6, 0.5), (22, 0.45), (70, 0.35)))
img += bloom
img += rng.normal(0, 0.012, img.shape).astype(np.float32)  # grain
# gentle vignette top and bottom
img *= (0.85 + 0.15 * np.sin(np.clip(y, 0, 1) * math.pi))[..., None]
out = pathlib.Path(A.out); out.mkdir(parents=True, exist_ok=True)
Image.fromarray((np.clip(img, 0, 1) ** (1 / 1.0) * 255).astype(np.uint8)).save(out / f"{A.name}.jpg", quality=86, optimize=True, progressive=True)
dm = Image.fromarray((np.clip(depth / 0.8, 0, 1) * 255).astype(np.uint8)).resize((W // 2, H // 2), Image.BILINEAR)
dm.filter(ImageFilter.GaussianBlur(1.5)).save(out / f"{A.name}-depth.png", optimize=True)
print("wrote", out / f"{A.name}.jpg")
