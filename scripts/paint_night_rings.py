"""
Paint the quiet night around the street floor as see-through layers that wrap all the way
around (360 degrees). The site puts each layer on its own ring at a real distance, so when you
stand on the street level and look around, near trees slide past the brownstones and the far
skyline barely moves: real depth, three textures, no 3D models.

    python scripts/paint_night_rings.py [--seed N]

Writes public/street/ring-skyline.png, ring-rows.png, ring-trees.png. The sky, moon, stars and
ground are drawn by the shader in components/street/streetRings.ts. Ring sizes (radius and the
height each texture covers) must match RINGS in that file.
"""
import argparse, math, pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument("--seed", type=int, default=11)
ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent.parent / "public" / "street"))
A = ap.parse_args()
rng = np.random.default_rng(A.seed)
OUT = pathlib.Path(A.out); OUT.mkdir(parents=True, exist_ok=True)

def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255

# radius (m), texture size, height range above the street floor (m) -- keep in sync with RINGS
RINGS = {
    "skyline": dict(r=300, w=8192, h=1024, z0=-6, z1=230),
    "rows":    dict(r=110, w=8192, h=512, z0=-2, z1=34),
    "trees":   dict(r=52,  w=8192, h=512, z0=-1, z1=15),
}

class Ring:
    """A wrap-around canvas measured in meters along the ring and meters of height."""
    def __init__(self, r, w, h, z0, z1):
        self.r, self.W, self.H, self.z0, self.z1 = r, w, h, z0, z1
        self.circ = 2 * math.pi * r
        self.px = w / self.circ                # pixels per meter along the ring
        self.py = h / (z1 - z0)                # pixels per meter of height
        self.rgb = np.zeros((h, w, 3), np.float32)
        self.a = np.zeros((h, w), np.float32)
    def X(self, s): return s * self.px
    def Y(self, z): return (self.z1 - z) * self.py
    def mask(self):
        m = Image.new("L", (self.W, self.H), 0)
        return m, ImageDraw.Draw(m)
    def paint(self, m, color, blur=0.0):
        """Composite an L mask with a flat color. Wraps: masks are drawn with shapes repeated at +-W."""
        if blur: m = m.filter(ImageFilter.GaussianBlur(blur))
        k = np.asarray(m, np.float32) / 255
        self.rgb = self.rgb * (1 - k[..., None]) + k[..., None] * color
        self.a = np.maximum(self.a, k)
        return k
    def save(self, name):
        rgba = np.dstack([np.clip(self.rgb, 0, 1), np.clip(self.a, 0, 1)])
        Image.fromarray((rgba * 255).astype(np.uint8), "RGBA").save(OUT / f"ring-{name}.png", optimize=True)
        print("wrote", OUT / f"ring-{name}.png", self.W, self.H)

def wrapped(R, draw_fn, s, width):
    """Draw a shape at s (meters along the ring) and again across the seam if it straddles it."""
    draw_fn(s)
    if R.X(s - width) < 0: draw_fn(s + R.circ)
    if R.X(s + width) > R.W: draw_fn(s - R.circ)

def windows(R, x0, x1, ztop, zbot, ww, wh, col_gap, row_gap, lit, warm=hexc("#ffc979")):
    """Lit windows on a facade (meters)."""
    z = zbot + row_gap * 0.8
    while z + wh < ztop - 0.6:
        s = x0 + col_gap * 0.6
        while s + ww < x1 - col_gap * 0.3:
            if rng.random() < lit:
                c = warm * (0.55 + 0.45 * rng.random())
                if rng.random() < 0.12: c = hexc("#9fb7ff") * 0.55
                ya, yb = int(R.Y(z + wh)), int(R.Y(z))
                for off in (0, R.circ, -R.circ):
                    xa, xb = int(R.X(s + off)), int(R.X(s + ww + off))
                    if xb <= 0 or xa >= R.W: continue
                    xa, xb = max(0, xa), min(R.W, xb)
                    if R.a[ya:yb, xa:xb].mean() > 0.9:
                        R.rgb[ya:yb, xa:xb] = c
                        # a warm curtain line, so windows don't look like flat stickers
                        R.rgb[ya:ya + max(1, (yb - ya) // 6), xa:xb] *= 0.75
            s += col_gap
        z += row_gap

# ------------------------------------------------------------------ far skyline
R = Ring(**RINGS["skyline"])
m, d = R.mask()
rects = []
s = 0.0
while s < R.circ:
    bw = rng.uniform(22, 60)
    bh = rng.uniform(25, 95) * (rng.random() ** 0.6)
    if rng.random() < 0.10: bh = rng.uniform(120, 200)  # a tower now and then
    bh = max(bh, 18)
    def box(s0, bw=bw, bh=bh):
        d.rectangle([R.X(s0), R.Y(bh), R.X(s0 + bw), R.H], fill=255)
        if bh > 110:  # setbacks + spire
            d.rectangle([R.X(s0 + bw * .18), R.Y(bh + 12), R.X(s0 + bw * .82), R.Y(bh)], fill=255)
            d.rectangle([R.X(s0 + bw * .38), R.Y(bh + 26), R.X(s0 + bw * .62), R.Y(bh + 12)], fill=255)
            d.line([R.X(s0 + bw * .5), R.Y(bh + 48), R.X(s0 + bw * .5), R.Y(bh + 26)], fill=255, width=2)
    wrapped(R, box, s, bw)
    rects.append((s, bh, bw))
    s += bw + rng.uniform(-6, 10)
R.paint(m, hexc("#1a2036"), blur=0.8)
for (s0, bh, bw) in rects:
    windows(R, s0, s0 + bw, bh, 0, 1.4, 2.0, 4.0, 4.2, 0.13, hexc("#ffcf8a") * 0.8)
R.rgb = R.rgb * 0.85 + hexc("#262a44") * 0.15  # haze
R.save("skyline")

# ------------------------------------------------------------------ brownstones and walk-ups
R = Ring(**RINGS["rows"])
m, d = R.mask()
fronts = []
s = 0.0
while s < R.circ:
    bw = rng.uniform(6.5, 10)
    floors = int(rng.integers(4, 7))
    bh = floors * 3.3 + 1.2
    tone = [hexc("#2a1d1c"), hexc("#1e2029"), hexc("#2b2219"), hexc("#1b2226"), hexc("#30201d")][int(rng.integers(0, 5))]
    tower = rng.random() < 0.4
    tx = rng.uniform(0.2, 0.65)
    def bld(s0, bw=bw, bh=bh, tower=tower, tx=tx):
        d.rectangle([R.X(s0), R.Y(bh), R.X(s0 + bw), R.H], fill=255)
        d.rectangle([R.X(s0 - .25), R.Y(bh + .5), R.X(s0 + bw + .25), R.Y(bh)], fill=255)  # cornice
        if tower:  # wooden water tower on legs
            x0 = s0 + bw * tx; tw = 2.6; th = 3.0; legs = 2.0
            d.rectangle([R.X(x0), R.Y(bh + legs + th), R.X(x0 + tw), R.Y(bh + legs)], fill=255)
            d.polygon([(R.X(x0 - .2), R.Y(bh + legs + th)), (R.X(x0 + tw / 2), R.Y(bh + legs + th + 1.4)), (R.X(x0 + tw + .2), R.Y(bh + legs + th))], fill=255)
            for lx in (x0 + .25, x0 + tw - .45):
                d.rectangle([R.X(lx), R.Y(bh + legs), R.X(lx + .2), R.Y(bh)], fill=255)
    wrapped(R, bld, s, bw)
    fronts.append((s, bw, bh, tone, floors))
    s += bw + rng.uniform(0, .25)
k = R.paint(m, hexc("#1d1a1f"), blur=0.6)
for (s0, bw, bh, tone, floors) in fronts:  # each building its own brick or stone
    for off in (0, R.circ, -R.circ):
        xa, xb = int(R.X(s0 + off)), int(R.X(s0 + bw + off))
        if xb <= 0 or xa >= R.W: continue
        xa, xb = max(0, xa), min(R.W, xb)
        sl = R.a[:, xa:xb, None]
        R.rgb[:, xa:xb] = R.rgb[:, xa:xb] * (1 - sl) + sl * tone
for (s0, bw, bh, tone, floors) in fronts:
    windows(R, s0, s0 + bw, bh, 0.8, 1.1, 1.8, 2.3, 3.3, 0.32)
# fire escapes: thin dark platforms and zigzag ladders on some fronts
m, d = R.mask()
for (s0, bw, bh, tone, floors) in fronts:
    if rng.random() < 0.45:
        c = s0 + bw * rng.uniform(.35, .6); half = 1.9
        for f in range(1, floors):
            z = f * 3.3 + .9
            def fe(cc, z=z):
                d.line([R.X(cc - half), R.Y(z), R.X(cc + half), R.Y(z)], fill=255, width=3)
                d.line([R.X(cc - half), R.Y(z + .9), R.X(cc + half), R.Y(z + .9)], fill=150, width=1)
                d.line([R.X(cc - half * .8), R.Y(z), R.X(cc + half * .6), R.Y(z - 3.3)], fill=200, width=2)
            wrapped(R, fe, c, half)
R.paint(m, hexc("#09090c"))
R.save("rows")

# ------------------------------------------------------------------ park trees, lamps, railing
R = Ring(**RINGS["trees"])
m, d = R.mask()
spots = []
s = rng.uniform(0, 4)
while s < R.circ:
    cr = rng.uniform(2.4, 3.8)          # canopy radius
    cz = rng.uniform(5.6, 7.6)          # canopy center height
    blobs = [(rng.uniform(0, 2 * math.pi), math.sqrt(rng.random()) * .85, rng.uniform(.14, .32)) for _ in range(110)]
    def tree(s0, cr=cr, cz=cz, blobs=blobs):
        d.rectangle([R.X(s0 - .18), R.Y(cz), R.X(s0 + .18), R.H], fill=255)
        d.line([R.X(s0), R.Y(cz - 1.4), R.X(s0 + cr * .5), R.Y(cz + .2)], fill=255, width=4)
        d.line([R.X(s0), R.Y(cz - 1.0), R.X(s0 - cr * .45), R.Y(cz + .4)], fill=255, width=4)
        for a, rr, br in blobs:
            bx, bz = s0 + math.cos(a) * rr * cr * 1.15, cz + math.sin(a) * rr * cr * .85
            b = br * cr
            d.ellipse([R.X(bx - b), R.Y(bz + b), R.X(bx + b), R.Y(bz - b)], fill=255)
    wrapped(R, tree, s, cr * 1.4)
    spots.append((s, cr, cz))
    s += rng.uniform(6.5, 11)
k_tree = R.paint(m, hexc("#0e1a15"), blur=1.0)
# leafy mottling and a cool moonlit rim on the canopy tops
mot = rng.random((R.H // 5 + 1, R.W // 5 + 1)).astype(np.float32)
mot = np.asarray(Image.fromarray((mot * 255).astype(np.uint8)).resize((R.W, R.H), Image.BICUBIC), np.float32) / 255
R.rgb += (k_tree * (mot - .5) * .07)[..., None] * hexc("#8fb59c")
edge = np.clip(k_tree - np.roll(k_tree, 5, axis=0), 0, 1)
R.rgb += (edge * .08)[..., None] * hexc("#a9bde0")
# low iron park railing along the whole ring
m, d = R.mask()
d.rectangle([0, R.Y(1.05), R.W, R.Y(.95)], fill=255)
d.rectangle([0, R.Y(.15), R.W, R.Y(.05)], fill=255)
step = R.X(.16)
x = 0.0
while x < R.W:
    d.line([x, R.Y(1.05), x, R.H], fill=230, width=1); x += step
R.paint(m, hexc("#0a0c0d"))
# lamp posts with a warm glow, between some trees
glow = np.zeros((R.H, R.W), np.float32)
yy, xx = np.mgrid[0:R.H, 0:R.W]
m, d = R.mask()
for (s0, cr, cz) in spots:
    if rng.random() < .5: continue
    ls = s0 + cr + rng.uniform(1.2, 2.5)
    def lamp(l):
        d.rectangle([R.X(l - .07), R.Y(4.3), R.X(l + .07), R.H], fill=255)
        d.ellipse([R.X(l - .28), R.Y(4.9), R.X(l + .28), R.Y(4.3)], fill=255)
    wrapped(R, lamp, ls, .5)
    for off in (0, R.circ, -R.circ):
        gx, gy = R.X(ls + off), R.Y(4.6)
        if -400 < gx < R.W + 400:
            dd = np.hypot((xx - gx) / R.px, (yy - gy) / R.py)  # meters
            glow += np.exp(-(dd / .35) ** 2) * 1.2 + np.exp(-(dd / 1.6) ** 2) * .35 + np.exp(-(dd / 4.5) ** 2) * .12
R.paint(m, hexc("#0b0e10"))
gc = hexc("#ffd59a")
g = np.clip(glow, 0, 1.5)
R.rgb = R.rgb + g[..., None] * gc * (1 - R.a[..., None] * .4)
R.a = np.maximum(R.a, np.clip(g, 0, 1) * .9)
R.rgb = np.where(R.a[..., None] > 1e-3, R.rgb / np.maximum(R.a[..., None], 1e-3) * np.minimum(R.a[..., None], 1) , R.rgb)  # straight alpha
R.save("trees")
