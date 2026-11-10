"""Platform newsstand for Books & Writing: green kiosk, striped awning, shelves of
books with random spines, magazines on the counter. Front faces -X; origin at
the kiosk's floor center.
"""
import random
from common import *
from props.signage import hanging_sign

SPINES = ["#3a5ccc", "#e8732c", "#e6a823", "#c2508a", "#2a9d8f", "#7c5cbf", "#4f9a5b", "#a0522d",
          "#f5ead6", "#1e3a5f", "#d94f4f", "#5b3a52", "#b08a4f"]


def build(seed=5):
    rnd = random.Random(seed)
    green = mat("kiosk_green", "#2f6b4f", 0.4, coat=0.5)
    wood = noise_mat("kiosk_wood", "#7a4e31", "#9a6640", scale=30, rough=0.5)
    brass = mat("kiosk_brass", "#c9a24a", 0.3, metal=0.7)
    stripe_a = mat("awning_orange", "#e8732c", 0.6)
    stripe_b = mat("awning_cream", "#f5ead6", 0.6)
    bulb = mat("kiosk_bulb", "#fff3d6", 0.3, emit="#ffd9a0", emit_str=8)
    books = [mat("spine_" + c, c, 0.55) for c in SPINES]
    o = []
    D, Wd = 1.3, 2.8  # depth (x), width (y)
    o.append(cube("k_base", (0.15, 0, 0.6), (D, Wd, 1.2), green, bevel=0.03))
    o.append(cube("k_counter", (-0.55, 0, 1.22), (0.5, Wd + 0.1, 0.05), wood, bevel=0.01))
    o.append(cube("k_back", (0.65, 0, 2.0), (0.1, Wd, 1.6), wood))
    for sy in (-1, 1):
        o.append(cube("k_side", (0.15, sy * (Wd / 2 - 0.04), 2.0), (D, 0.08, 1.6), green))
    o.append(cube("k_roof", (0.1, 0, 2.86), (D + 0.5, Wd + 0.4, 0.12), green, bevel=0.03))
    o.append(cube("k_trim", (-0.6, 0, 2.86), (0.04, Wd + 0.44, 0.16), brass))
    # striped awning
    n = 12
    for i in range(n):
        y = -Wd / 2 - 0.1 + (i + 0.5) * (Wd + 0.2) / n
        a = cube("awning", (-0.86, y, 2.62), (0.62, (Wd + 0.2) / n + 0.002, 0.02), stripe_a if i % 2 == 0 else stripe_b)
        a.rotation_euler = (0, R(28), 0)
        o.append(a)
    # shelves + books
    for z in (1.5, 1.95, 2.4):
        o.append(cube("shelf", (0.45, 0, z - 0.02), (0.36, Wd - 0.16, 0.03), wood))
        y = -Wd / 2 + 0.12
        while y < Wd / 2 - 0.14:
            t = rnd.uniform(0.035, 0.08); h = rnd.uniform(0.22, 0.36)
            b = cube("book", (0.45, y + t / 2, z + h / 2), (0.22 + rnd.uniform(-0.02, 0.02), t, h), rnd.choice(books), bevel=0.004, seg=2)
            if rnd.random() < 0.07:
                b.rotation_euler = (R(rnd.choice([-12, 12])), 0, 0)
            o.append(b)
            y += t + 0.006
    # magazines on the counter
    for i in range(6):
        mgz = cube("magazine", (-0.6, -1.1 + i * 0.44, 1.255), (0.3, 0.38, 0.012), rnd.choice(books))
        mgz.rotation_euler = (0, 0, R(rnd.uniform(-6, 6)))
        o.append(mgz)
    # warm bulbs under the roof
    for y in (-0.9, 0, 0.9):
        o.append(sphere("bulb", (-0.45, y, 2.7), 0.05, bulb, seg=12))
    sign = hanging_sign(["BOOKS & WRITING"], w=2.6, h=0.5, letter="W", color="#a0522d", sizes=(0.19,), rod=0.0)
    g = group(sign[:-2], (-0.62, 0, 3.22), rz=-90)
    for x in sign[-2:]:
        bpy.data.objects.remove(x)
    o.append(g)
    return o
