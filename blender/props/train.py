"""A friendly stainless subway car (generic, no real-world branding).

car() builds one car in its own frame: the front (cab) faces -Y at y=0, the body
runs to +Y, and z=0 is the station's rail datum. The car's floor sits at the
platform edge and the trucks rest on the rails.

Parts (object names): body, trim, glass, lights, interior, underframe,
truck_0, truck_1, doors_L_<k><a|b>, doors_R_<k><a|b>, plus text for the signs.
Materials are plain PBR values (procedural only where Blender can't export it),
so the glTF keeps them and the site lights the moving train live.
"""
import random
from props.train_util import *
from props import train_body, train_cab, train_interior, train_truck, train_r160


def car(front=True, route="S", color="#e8732c", seed=0, coupler=True):
    rnd = random.Random(seed)
    pal = palette(color)

    body = train_body.shell(pal)
    cut(body, train_body.openings(pal, front))
    smooth(body)

    trim = Part("trim")
    train_body.trim(trim, pal)
    lights = Part("lights")
    for sx in (-1, 1):
        for yd in DOOR_YS:
            lights.prism(circle(0.035, 10), "x", (sx * (HALF + 0.004), yd, 2.92), 0.012, pal["amber"])
    texts = []
    if front:
        texts = train_r160.cab_r160(trim, lights, pal, route, seed)
    train_cab.ends(trim, lights, pal, coupler)

    glass = Part("glass")
    train_body.glazing(glass, pal, front)

    interior = train_interior.build(pal, rnd, front)
    trucks = [train_truck.truck(pal, yt, "truck_%d" % i).obj() for i, yt in enumerate(TRUCK_YS)]
    underframe = train_truck.underframe(pal).obj()

    return ([body, trim.obj("trim"), glass.obj("glass"), lights.obj("lights"),
             interior.obj("interior"), underframe] + trucks + train_body.doors(pal) + texts)
