"""The terrain atlas layout: which tile sits in which 16 x 16 cell of art/topdown/proto_tiles.png.

The atlas is 32 cells wide. Rows:
  0  tops (the Phase 1 loader's names first) and the stairs
  1  faces: the first row under a lip (`*_face_top`) and the rows below it (`*_face`)
  2  plain water frames 0-3, the light overlays
  3  grass over dirt, the 16 corner cases (corner order TL TR BL BR, 1 = grass)
  4  grass over paving, the same 16
  5-6 water with its shore, the 16 side cases (bit 1 N, 2 E, 4 S, 8 W = land) x 4 frames side by side, 8 cases a row
The names the Phase 1 loader draws (grass_a, grass_b, grass_flowers, paving_a, paving_b, dirt, wood, rock, stone_top,
water_0-3, stairs, earth/stone/rock/wood/bank _face_top and _face) keep their meaning.
"""
from __future__ import annotations

import tiles as tl
from canvas import T, Img
from palette import DIRT, GRASS, PAVE

COLS = 32
ROWS = 7

TOPS = [
    ("grass_a", lambda: tl.grass(1)), ("grass_b", lambda: tl.grass(2)), ("grass_c", lambda: tl.grass(4, "lush")),
    ("grass_d", lambda: tl.grass(5, "clover")), ("grass_flowers", lambda: tl.grass(3, "flowers")),
    ("dirt", lambda: tl.dirt(6)), ("dirt_b", lambda: tl.dirt(16)),
    ("paving_a", lambda: tl.paving(4, "a")), ("paving_b", lambda: tl.paving(5, "b")), ("paving_c", lambda: tl.paving(15, "c")),
    ("paving_d", lambda: tl.paving(25, "m")),
    ("stone_top", lambda: tl.stone_top(12)), ("stone_top_b", lambda: tl.stone_top(13, True)),
    ("rock", lambda: tl.rock_top(7)), ("rock_b", lambda: tl.rock_top(17)),
    ("wood", lambda: tl.wood_deck(3)), ("wood_b", lambda: tl.wood_deck(23)),
    ("roof_top", lambda: tl.roof_top(9)), ("roof_top_b", lambda: tl.roof_top(19)),
    ("wall_top", lambda: tl.wall_top(8)),
    ("stairs", tl.stairs),
]

FACES = [
    ("earth_face_top", lambda: tl.earth_face(11, True)), ("earth_face", lambda: tl.earth_face(11, False)),
    ("stone_face_top", lambda: tl.stone_face(12, True)), ("stone_face", lambda: tl.stone_face(12, False)),
    ("rock_face_top", lambda: tl.rock_face(13, True)), ("rock_face", lambda: tl.rock_face(13, False)),
    ("bank_face_top", lambda: tl.bank_face(14, True)), ("bank_face", lambda: tl.bank_face(14, False)),
    ("wood_face_top", lambda: tl.wood_face(15, True)), ("wood_face", lambda: tl.wood_face(15, False)),
    ("roof_face_top", lambda: tl.eave_face(16)), ("roof_face", lambda: tl.plaster_face(16)),
    ("plaster_face_window", lambda: tl.plaster_face(17, "window")), ("plaster_face_door", lambda: tl.plaster_face(18, "door")),
    ("wall_face_top", lambda: tl.wall_face(19, True)), ("wall_face", lambda: tl.wall_face(19, False)),
    ("pave_face_top", lambda: tl.stone_face(20, True, PAVE)), ("pave_face", lambda: tl.stone_face(20, False)),
]

OVERLAYS = ["rim_w", "rim_e", "rim_n", "ao_n", "shade_w"]


def build() -> tuple[Img, dict, dict]:
    """The atlas image, the name -> [x, y, w, h] map, and the auto-tile tables."""
    sheet = Img(COLS * T, ROWS * T)
    at: dict = {}

    def place(name: str, img: Img, cx: int, cy: int, h: int = T) -> None:
        sheet.paste(img, cx * T, cy * T)
        at[name] = [cx * T, cy * T, T, h]

    for k, (name, fn) in enumerate(TOPS):
        place(name, fn(), k, 0, 8 if name == "stairs" else T)
    for k, (name, fn) in enumerate(FACES):
        place(name, fn(), k, 1)
    for f in range(4):
        place("water_%d" % f, tl.water(f), f, 2)
    for k, name in enumerate(OVERLAYS):
        place(name, tl.overlay(name), 5 + k, 2)

    grass_img, dirt_img, pave_img = tl.grass(1), tl.dirt(6), tl.paving(4, "a")
    auto = {"grass_dirt": {}, "grass_paving": {}, "shore": {}}
    for k, corners in enumerate(tl.CORNER_KEYS):
        key = tl.corner_name(corners)
        name = "grass_dirt_" + key
        place(name, tl.blend_corners(grass_img, dirt_img, corners, 50 + k, GRASS, DIRT), k, 3)
        auto["grass_dirt"][key] = name
        name = "grass_paving_" + key
        place(name, tl.blend_corners(grass_img, pave_img, corners, 70 + k, GRASS, PAVE), k, 4)
        auto["grass_paving"][key] = name
    for sides in range(16):
        cx, cy = (sides % 8) * 4, 5 + sides // 8
        names = []
        for f in range(4):
            name = "shore_%02d_%d" % (sides, f)
            place(name, tl.water(f, sides), cx + f, cy)
            names.append(name)
        auto["shore"]["%02d" % sides] = names
    return sheet, at, auto
