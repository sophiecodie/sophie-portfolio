# Blender scene for the subway site

The station, train and props are Python that drives Blender as a library. No
downloaded models: every mesh and texture (tile, mosaic, terrazzo, wood, steel)
is generated here, so the whole scene can be rebuilt from code.

| File | What it builds |
| --- | --- |
| `layout.py` | Where everything sits (meters, track along +Y). The site reads the same stops from `public/subway/layout.json`. |
| `common.py` | Materials (procedural tile, mosaic, terrazzo, noise), primitives, text, lights, camera. |
| `props/station_shell.py` | Platforms, tactile edges, tile walls with mosaic bands, ceiling lamps, green columns, track, tunnel mouths. |
| `props/signage.py` | Hanging black station signs, mosaic name tiles, route bullets, geometric posters. |
| `props/map_board.py` | The "Choose your line" map, modeled with raised lines and station discs. |
| `props/countdown_clock.py` | The "Next trains" arrivals board. |
| `props/newsstand.py` | The Books & Writing kiosk with randomly sized books. |
| `props/stairs.py` | Exit stairs up to a street with lamp globes, trees and brownstones. |
| `props/furniture.py` | Benches, trash cans, the glowing lightbox under each project tile. |
| `props/train.py` | A friendly stainless subway car (generic, no real-world branding). |
| `build_station.py` | Puts it all together. `preview` renders stills; `bake` bakes light and exports `public/subway/station.glb`. |
| `bake.py` | Joins the station into 10 m slices, unwraps each, bakes Cycles light + color into one atlas per slice, exports glTF. |
| `build_train.py` | Exports `public/subway/train.glb` (lit live in the browser because it moves). |

## Run it

```bash
python -m venv .venv && .venv/bin/pip install bpy==5.2.3   # Blender as a Python module (needs Python 3.13)
.venv/bin/python blender/build_station.py preview          # stills in blender/renders/
.venv/bin/python blender/build_station.py bake 2048 24     # station.glb + layout.json (~15 min on 4 CPU cores)
.venv/bin/python blender/build_train.py                    # train.glb
```

Fonts in `fonts/` are from Google Fonts under the SIL Open Font License.
