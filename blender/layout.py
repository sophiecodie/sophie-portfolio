"""Where everything sits in the station. Units are meters; the track runs along +Y.

The site reads the same numbers (exported to public/subway/layout.json) so camera
stops line up with the props.
"""
TRACK_START, TRACK_END = -20.0, 100.0
PLAT_INNER = 1.7       # platform edge, both sides
WALL_X = 5.0           # tile walls at +/- WALL_X
CEIL_Z = 4.0
PLAT_Z = 0.2           # platform surface height above rail bed top
COL_X = 2.45           # column line
COL_STEP = 5.0
CHUNK = 10.0           # light-bake chunk length
STATION_START, STATION_END = -10.0, 90.0

TITLE_SIGN_Y = 6.0
MAP_Y = 13.0
BOARD_Y = 19.0
PROJECT_Y0, PROJECT_STEP = 27.0, 6.0     # seven project stops on the right wall
NEWSSTAND_Y = 72.0
STAIRS_Y = 80.0                          # foot of the exit stairs

LINES = {
    "data":   {"name": "Data line",   "letter": "D", "color": "#e8732c", "stops": ["new-york-census", "purchase-intent", "college-app-atlas"]},
    "health": {"name": "Health line", "letter": "H", "color": "#2a9d8f", "stops": ["agent00hl7", "dream-team", "neurobiome"]},
    "words":  {"name": "Words line",  "letter": "W", "color": "#c2508a", "stops": ["folio", "reading"]},
}
