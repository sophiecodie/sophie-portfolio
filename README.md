# Sophie Shih · Subway Portfolio

![The title stop](docs/title.jpg)

My portfolio as a sunny, slightly storybook New York subway station you ride through.
The station is modeled in **Blender** entirely from Python, its light is baked with
Cycles into textures, and the site plays it back in the browser with **Three.js**
inside a static **Next.js** app.

## How you move through it

| Way | What happens |
| --- | --- |
| Scroll, arrow keys, swipe, or **Next stop** | Ride forward along the platform, one stop at a time |
| **Line map** | Pick a line (Data, Health, Words) and jump to any stop on it |
| **Arrivals** board | Every project is a train; click a row to go there |
| Click things in the station | The map, the board, each project's mosaic sign, the newsstand, the stairs |
| **All stops** | A plain list of everything, one click away the whole time |

Stops, in riding order: the title platform (the train pulls in under the
"Sophie Shih's Portfolio" sign), the line map, the arrivals board, seven project
stations (mosaic name tile + lightbox, details open in a side panel), the Books &
Writing newsstand, and the exit stairs up to the street for About & contact.
`prefers-reduced-motion` turns camera moves into cuts.

## Layout

```
app/                    Next.js app (static export)
components/subway/      Experience.tsx (UI, navigation) and scene.ts (Three.js)
data/                   projects, books, writing, contact info
blender/                the 3D scene as code (see blender/README.md)
public/subway/          station.glb (baked), train.glb, layout.json (camera stops)
public/draco/           Draco decoder for the compressed meshes
```

## Run

```bash
npm install
npm run dev        # http://localhost:3000
npm run build      # static site in out/
```

## Rebuild the 3D scene

```bash
python3.13 -m venv .venv && .venv/bin/pip install bpy==5.2.3
.venv/bin/python blender/build_station.py preview      # quick stills in blender/renders/
.venv/bin/python blender/build_station.py bake 2048 24 # station.glb + layout.json
.venv/bin/python blender/build_train.py                # train.glb
npm run compress                                       # Draco-compress both (about 15x smaller)
```

Inspired by Felix Rieseberg's process of describing a scene, having Claude write the
geometry as code, rendering a still, and iterating
([felixrieseberg.com/made-by-mechanical-means](https://felixrieseberg.com/made-by-mechanical-means/)).
