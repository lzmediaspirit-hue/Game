"""The terrain atlas layout: which tile sits in which 16 x 16 cell of art/topdown/proto_tiles.png.

The atlas is 32 cells wide. Rows 0-6 hold the Phase 3 contract tiles, at the places they always had (the TileSet and
the Phase 1 loader draw them):
  0  tops (the Phase 1 loader's names first) and the stairs
  1  faces: the first row under a lip (`*_face_top`) and the rows below it (`*_face`)
  2  plain water frames 0-3, the light overlays
  3  grass over dirt, the 16 corner cases (corner order TL TR BL BR, 1 = grass)
  4  grass over paving, the same 16
  5-6 water with its shore, the 16 side cases (bit 1 N, 2 E, 4 S, 8 W = land) x 4 frames side by side, 8 cases a row
From row 7 down, the Terrain v2 sets the room view draws (docs/redesign/art_bible.md "Terrain v2"), packed in shelves:
the material patterns (4 x 4 tiles; the paving 8 x 8), the water pattern's four frames, the face patterns (a first row
and two body rows of 4), the positional grass overlays and tint masks (a 4 x 4 block per corner case each), the decals,
the shore overlays in four frames, the inner-corner foam, the pilings' ripples and the face's foot shade.
"""
from __future__ import annotations

import flood as fl
import sand_snow as ss
import terrain2 as t2
import tiles as tl
from canvas import T, Img

COLS = 32
CONTRACT_ROWS = 7

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
    ("marsh_a", lambda: tl.grass(33, "marsh")), ("marsh_b", lambda: tl.grass(34, "marsh")),
    ("sand_a", lambda: tl.sand(1)), ("sand_b", lambda: tl.sand(3)), ("sand_c", lambda: tl.sand(5)),
    ("snow_a", lambda: tl.snow(1)), ("snow_b", lambda: tl.snow(2)), ("snowpack_a", lambda: tl.snow(1, True)),
    ("snowpack_b", lambda: tl.snow(3, True)),
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
    ("pave_face_top", lambda: tl.stone_face(20, True, t2.PAVE2)), ("pave_face", lambda: tl.stone_face(20, False, t2.PAVE2)),
    ("sand_face_top", lambda: tl.face_set("sand")[0][0]), ("sand_face", lambda: tl.face_set("sand")[1][0]),
    ("snow_face_top", lambda: tl.face_set("snow")[0][0]), ("snow_face", lambda: tl.face_set("snow")[1][0]),
]

OVERLAYS = ["rim_w", "rim_e", "rim_n", "ao_n", "shade_w", "end_w", "end_e", "cheek_w", "cheek_e"]

# Terrain v2: the materials with a macro pattern, the face kinds with a face pattern, the decal sets.
MACROS = ["grass", "dirt", "stone", "rock", "wood", "roof", "pave", "wall", "sand", "snow", "snowpack"]
FACE_KINDS = ["rock", "earth", "stone", "pave", "bank", "wood", "wall", "sand", "snow"]
# Decision 44: the materials that creep over their neighbours on the same level with overlays of their own (grass has
# the Phase 3 set, `over`).
CREEP = ["sand", "snow", "snowpack"]
FACE_JOINS = ["earth", "sand", "snow"]   # the faces that run into a neighbour's where their tops creep over it


class Packer:
    """Shelf packing of blocks (w x h cells) into the atlas, left to right, a new shelf when a block no longer fits."""

    def __init__(self, y0: int):
        self.x, self.y, self.shelf = 0, y0, 0

    def block(self, w: int, h: int) -> tuple[int, int]:
        if self.x + w > COLS:
            self.x, self.y, self.shelf = 0, self.y + self.shelf, 0
        at = (self.x, self.y)
        self.x += w
        self.shelf = max(self.shelf, h)
        return at

    def rows(self) -> int:
        return self.y + self.shelf


def build() -> tuple[Img, dict, dict, dict]:
    """The atlas image, the name -> [x, y, w, h] map, the Phase 3 auto-tile tables and the Terrain v2 sets."""
    placed: list = []
    at: dict = {}

    def place(name: str, img: Img, cx: int, cy: int, h: int = T) -> None:
        placed.append((img, cx, cy))
        at[name] = [cx * T, cy * T, T, h]

    # ---- rows 0-6: the Phase 3 contract
    for k, (name, fn) in enumerate(TOPS):
        place(name, fn(), k, 0, 8 if name == "stairs" else T)
    for k, (name, fn) in enumerate(FACES):
        place(name, fn(), k, 1)
    for f in range(4):
        place("water_%d" % f, tl.water(f), f, 2)
    for k, name in enumerate(OVERLAYS):
        place(name, tl.overlay(name), 5 + k, 2)
    dirt0, pave0 = tl.macro("dirt")[0][0], tl.macro("pave")[0][0]
    auto = {"grass_dirt": {}, "grass_paving": {}, "grass_sand": {}, "shore": {}}
    for k, corners in enumerate(tl.CORNER_KEYS):
        key = tl.corner_name(corners)
        name = "grass_dirt_" + key
        place(name, tl.blend_corners(dirt0, corners), k, 3)
        auto["grass_dirt"][key] = name
        name = "grass_paving_" + key
        place(name, tl.blend_corners(pave0, corners), k, 4)
        auto["grass_paving"][key] = name
    for sides in range(16):
        cx, cy = (sides % 8) * 4, 5 + sides // 8
        names = []
        for f in range(4):
            name = "shore_%02d_%d" % (sides, f)
            place(name, tl.water(f, sides), cx + f, cy)
            names.append(name)
        auto["shore"]["%02d" % sides] = names

    # ---- rows 7-: Terrain v2
    pk = Packer(CONTRACT_ROWS)
    v2: dict = {"macro": {}, "faces": {}, "over": {}, "tint_mask": {}, "decals": {}, "water": {}}
    for kind in MACROS:
        tiles, w, h = tl.macro(kind)
        x0, y0 = pk.block(w, h)
        names = []
        for i, img in enumerate(tiles):
            name = "%s_m%d%d" % (kind, i % w, i // w)
            place(name, img, x0 + i % w, y0 + i // w)
            names.append(name)
        v2["macro"][kind] = {"w": w, "h": h, "tiles": names}
    frames = []
    for f in range(4):
        x0, y0 = pk.block(t2.M, t2.M)
        names = []
        for i, img in enumerate(tl.water_frames()[f]):
            name = "water_m%d%d_%d" % (i % t2.M, i // t2.M, f)
            place(name, img, x0 + i % t2.M, y0 + i // t2.M)
            names.append(name)
        frames.append(names)
    v2["water"]["macro"] = {"w": t2.M, "h": t2.M, "frames": frames}
    for kind in FACE_KINDS:
        tops, body = tl.face_set(kind)
        x0, y0 = pk.block(t2.M, 3)
        top_names, body_names = [], []
        for i, img in enumerate(tops):
            name = "%s_face_top_v%d" % (kind, i)
            place(name, img, x0 + i, y0)
            top_names.append(name)
        for i, img in enumerate(body):
            name = "%s_face_v%d" % (kind, i)
            place(name, img, x0 + i % t2.M, y0 + 1 + i // t2.M)
            body_names.append(name)
        v2["faces"][kind] = {"top": top_names, "body": body_names}
    # Decision 44: a face's first row running into its neighbour's where the neighbour's top creeps over it (the grassy
    # bank into a beach, a beach into the embankment, the snow's lip into the bare rock's), per side and column.
    v2["face_end"] = {}
    for kind in FACE_JOINS:
        tops, _ = tl.face_set(kind)
        x0, y0 = pk.block(8, 1)
        ends = {"w": [], "e": []}
        for si, side in enumerate(("w", "e")):
            for c in range(t2.M):
                name = "%s_join_%s%d" % (kind, side, c)
                place(name, ss.face_join(tops[c], side, c), x0 + si * t2.M + c, y0)
                ends[side].append(name)
        v2["face_end"][kind] = ends
    for corners in tl.CORNER_KEYS:
        if corners in ((0, 0, 0, 0), (1, 1, 1, 1)):
            continue
        key = tl.corner_name(corners)
        x0, y0 = pk.block(t2.M, t2.M)
        names = []
        for py in range(t2.M):
            for px in range(t2.M):
                name = "over_%s_%d%d" % (key, px, py)
                place(name, tl.grass_over(corners, (px, py)), x0 + px, y0 + py)
                names.append(name)
        v2["over"][key] = names
    for corners in tl.CORNER_KEYS:
        if corners == (0, 0, 0, 0):
            continue
        key = tl.corner_name(corners)
        x0, y0 = pk.block(t2.M, t2.M)
        names = []
        for py in range(t2.M):
            for px in range(t2.M):
                name = "tint_%s_%d%d" % (key, px, py)
                place(name, t2.tint_mask(corners, (px, py)), x0 + px, y0 + py)
                names.append(name)
        v2["tint_mask"][key] = names
    v2["tint"] = {**t2.TINTS, "wet": ss.WET_TINT}
    # Decision 44: sand and snow creeping over their neighbours, per corner case and place (as `over`); grass over
    # sand for the Phase 3 contract's top(), as grass over dirt and paving (the TileSet keeps those two only).
    v2["creep"] = {}
    for kind in CREEP:
        v2["creep"][kind] = {}
        for corners in tl.CORNER_KEYS:
            if corners in ((0, 0, 0, 0), (1, 1, 1, 1)):
                continue
            key = tl.corner_name(corners)
            x0, y0 = pk.block(t2.M, t2.M)
            names = []
            for py in range(t2.M):
                for px in range(t2.M):
                    name = "%s_over_%s_%d%d" % (kind, key, px, py)
                    place(name, tl.creep_over(kind, corners, (px, py)), x0 + px, y0 + py)
                    names.append(name)
            v2["creep"][kind][key] = names
    sand0 = tl.macro("sand")[0][0]
    x0, y0 = pk.block(16, 1)
    for k, corners in enumerate(tl.CORNER_KEYS):
        key = tl.corner_name(corners)
        name = "grass_sand_" + key
        place(name, tl.blend_corners(sand0, corners), x0 + k, y0)
        auto["grass_sand"][key] = name
    for kind, imgs in tl.decal_sets().items():
        x0, y0 = pk.block(len(imgs), 1)
        names = []
        for i, img in enumerate(imgs):
            name = "decal_%s_%d" % (kind, i)
            place(name, img, x0 + i, y0)
            names.append(name)
        v2["decals"][kind] = names
    shore = {}
    for sides in range(1, 16):
        x0, y0 = pk.block(4, 1)
        names = []
        for f in range(4):
            name = "shorefx_%02d_%d" % (sides, f)
            place(name, tl.shore_overlay(sides, f), x0 + f, y0)
            names.append(name)
        shore["%02d" % sides] = names
    v2["water"]["shore"] = shore
    beach = {}
    for sides in range(1, 16):
        x0, y0 = pk.block(4, 1)
        names = []
        for f in range(4):
            name = "beachfx_%02d_%d" % (sides, f)
            place(name, tl.beach_overlay(sides, f), x0 + f, y0)
            names.append(name)
        beach["%02d" % sides] = names
    v2["water"]["beach"] = beach
    corners = {}
    for c in ("ne", "nw", "se", "sw"):
        x0, y0 = pk.block(4, 1)
        corners[c] = []
        for f in range(4):
            name = "corner_%s_%d" % (c, f)
            place(name, t2.inner_corner(c, f), x0 + f, y0)
            corners[c].append(name)
    v2["water"]["corner"] = corners
    x0, y0 = pk.block(5, 1)
    v2["water"]["ripple"] = []
    for f in range(4):
        name = "ripple_%d" % f
        place(name, t2.post_ripple(f), x0 + f, y0)
        v2["water"]["ripple"].append(name)
    place("face_ao", t2.overlay("face_ao"), x0 + 4, y0)
    v2["face_ao"] = "face_ao"
    # R2: shallow water over a floor a body wades (flood.py), per corner case and place (as `over`), the whole case too.
    v2["flood"] = {}
    for corners in tl.CORNER_KEYS:
        if corners == (0, 0, 0, 0):
            continue
        key = tl.corner_name(corners)
        x0, y0 = pk.block(t2.M, t2.M)
        names = []
        for py in range(t2.M):
            for px in range(t2.M):
                name = "flood_%s_%d%d" % (key, px, py)
                place(name, fl.flood_over(corners, (px, py)), x0 + px, y0 + py)
                names.append(name)
        v2["flood"][key] = names

    sheet = Img(COLS * T, pk.rows() * T)
    for img, cx, cy in placed:
        sheet.paste(img, cx * T, cy * T)
    return sheet, at, auto, v2
