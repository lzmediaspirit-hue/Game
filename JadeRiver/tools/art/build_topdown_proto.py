"""Top-down redesign, Phase 1 (docs/redesign_top_down_plan.md): the prototype tile set, props and placeholder body.

Draws, at native art resolution (1 art px = 1 px of the 640x360 world viewport, nearest neighbour):
  art/topdown/proto_tiles.png      16x16 floor tops, cliff faces, stairs and four water frames
  art/topdown/proto_props.png      a riverside house, a storehouse, a willow, lanterns, barrels, crates, a notice board, reeds, a boat
  art/topdown/placeholder_body.png PLACEHOLDER body: S, E, N (W mirrors E) x idle 2, walk 4, jump 3, dash 2, strike 2
  art/topdown/placeholder_foes.png PLACEHOLDER foes (Phase 2): crab, rat, boarlet, E (W mirrors) x idle, walk, windup, attack, hurt
  data/topdown/proto_tileset.json  where each tile, prop and frame sits, prop footprints and origins
Everything is original to Jade River and uses its palette tokens (docs/art-contracts.md) plus local hues. No
randomness: noise comes from a coordinate hash, and the PNGs carry no metadata, so a rebuild is byte-identical.
The body is a stand-in to judge the controller's feel; the layered character set is Phase 5 (AGENTS.md rules 1-4).

Usage: python3 tools/art/build_topdown_proto.py
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
T = 16

def c(h: str, a: int = 255) -> tuple:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)

# Palette tokens (docs/art-contracts.md) and local hues that sit with them.
INK, NIGHT, TEAL, JSHADOW, JADE, BJADE = c("071015"), c("0A2027"), c("0D3035"), c("15514F"), c("2C9E8F"), c("67D6BD")
BRONZE, GOLD, PGOLD, PAPER, MIST, RED = c("9A6A35"), c("E5B84C"), c("FFE6A1"), c("E8E1CF"), c("AFC9D1"), c("E45858")
GRASS = [c("2F4F2A"), c("3E6534"), c("4F7D3F"), c("67944C"), c("86AE5E")]
EARTH = [c("3A2A1E"), c("56402C"), c("6E553A"), c("8A6D4A")]
STONE = [c("3E4344"), c("565C5B"), c("6F7572"), c("8B908A"), c("A9ACA2")]
PAVE = [c("4D5250"), c("6A706B"), c("828781"), c("9DA199"), c("B5B7AC")]
WOOD = [c("3B2518"), c("5A3822"), c("78502F"), c("9A6A3E"), c("B8864F")]
ROCK = [c("2B3434"), c("3C4847"), c("50605D"), c("687A74"), c("83968D")]
WATER = [c("0D3035"), c("134652"), c("1B5C68"), c("2A7385"), c("4E97A3"), c("8FCBCB")]
ROOF = [c("1D2A2E"), c("2A3B40"), c("3A5056"), c("4F686C"), c("6C8686")]
TIMBER = [c("3E1F1A"), c("5C2E24"), c("7A3E2E")]
PLASTER = [c("B9B09A"), c("D3CBB6"), c("E8E1CF")]
CLEAR = (0, 0, 0, 0)

def h01(x: int, y: int, s: int = 0) -> float:
    n = (x * 374761393 + y * 668265263 + s * 2246822519) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65536.0

class Sheet:
    def __init__(self, w: int, h: int):
        self.img = Image.new("RGBA", (w, h), CLEAR)
        self.px = self.img.load()
        self.w, self.h = w, h

    def put(self, x: int, y: int, col) -> None:
        if 0 <= x < self.w and 0 <= y < self.h and col is not None:
            self.px[x, y] = col

    def rect(self, x: int, y: int, w: int, h: int, col) -> None:
        for j in range(y, y + h):
            for i in range(x, x + w):
                self.put(i, j, col)

    def ellipse(self, cx: float, cy: float, rx: float, ry: float, col) -> None:
        for j in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for i in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((i + 0.5 - cx) / rx) ** 2 + ((j + 0.5 - cy) / ry) ** 2 <= 1.0:
                    self.put(i, j, col)

    def outline(self, x0: int, y0: int, w: int, h: int, col=INK) -> None:
        """A 1 px outline round every opaque shape inside the box (drawn on transparent neighbours)."""
        src = [[self.px[i, j][3] > 0 for i in range(x0, x0 + w)] for j in range(y0, y0 + h)]
        for j in range(h):
            for i in range(w):
                if src[j][i]: continue
                if any(0 <= j + dj < h and 0 <= i + di < w and src[j + dj][i + di] for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    self.put(x0 + i, y0 + j, col)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.img.save(path, optimize=False)

# --------------------------------------------------------------------------------------------- tiles
def tile_grass(s: Sheet, ox: int, oy: int, seed: int, flowers: bool = False) -> None:
    for j in range(T):
        for i in range(T):
            n = h01(i, j, seed)
            s.put(ox + i, oy + j, GRASS[1] if n < 0.30 else GRASS[2] if n < 0.82 else GRASS[3])
    for k in range(7):   # blade tufts: a light tip over a dark root
        x, y = int(h01(k, 1, seed) * 15), int(h01(k, 2, seed) * 14) + 1
        s.put(ox + x, oy + y, GRASS[4])
        s.put(ox + x, oy + y + 1, GRASS[0])
    if flowers:
        for k in range(3):
            x, y = 2 + int(h01(k, 5, seed) * 12), 2 + int(h01(k, 6, seed) * 12)
            s.put(ox + x, oy + y, PAPER if k != 1 else PGOLD)
            s.put(ox + x, oy + y + 1, GRASS[0])

def tile_paving(s: Sheet, ox: int, oy: int, seed: int) -> None:
    # Flagstones in staggered courses of 8 x 5; each stone lit from the upper left, joints in the dark tone.
    for j in range(T):
        row = j // 5 if j < 15 else 3
        shift = 4 if row % 2 else 0
        for i in range(T):
            sx = (i + shift) % 8
            sy = j % 5 if j < 15 else 4
            stone = int(h01((i + shift) // 8, row, seed) * 3)
            col = PAVE[1 + stone]
            if sx == 0 or sy == 0: col = PAVE[0]
            elif sx == 1 or sy == 1: col = PAVE[min(4, 2 + stone)]
            elif h01(i, j, seed + 9) < 0.06: col = PAVE[max(0, stone)]
            s.put(ox + i, oy + j, col)

def tile_dirt(s: Sheet, ox: int, oy: int, seed: int) -> None:
    for j in range(T):
        for i in range(T):
            n = h01(i, j, seed)
            s.put(ox + i, oy + j, EARTH[2] if n < 0.7 else EARTH[3] if n < 0.88 else EARTH[1])

def tile_wood(s: Sheet, ox: int, oy: int) -> None:
    # Deck planks running east-west, 4 px each, with nail heads and a dark seam.
    for j in range(T):
        for i in range(T):
            k = j % 4
            col = WOOD[1] if k == 3 else WOOD[3] if k == 0 else WOOD[2]
            if h01(i, j // 4, 3) < 0.08 and k != 3: col = WOOD[4]
            s.put(ox + i, oy + j, col)
        if j % 4 == 1:
            s.put(ox + 2, oy + j, WOOD[0])
            s.put(ox + 13, oy + j, WOOD[0])

def tile_rock(s: Sheet, ox: int, oy: int, seed: int) -> None:
    for j in range(T):
        for i in range(T):
            n = h01(i // 2, j // 2, seed)
            s.put(ox + i, oy + j, ROCK[2] if n < 0.5 else ROCK[3] if n < 0.8 else ROCK[1])
    for k in range(4):
        s.put(ox + int(h01(k, 3, seed) * 16), oy + int(h01(k, 4, seed) * 16), GRASS[2])

def tile_stone_top(s: Sheet, ox: int, oy: int) -> None:
    for j in range(T):
        for i in range(T):
            col = STONE[3] if (i + (j // 8) * 8) % 16 else STONE[1]
            if j % 8 == 0: col = STONE[1]
            if j % 8 == 1 and (i + (j // 8) * 8) % 16: col = STONE[4]
            s.put(ox + i, oy + j, col)

def tile_water(s: Sheet, ox: int, oy: int, frame: int) -> None:
    for j in range(T):
        for i in range(T):
            n = h01(i, j, 71)
            s.put(ox + i, oy + j, WATER[2] if n < 0.6 else WATER[1])
    # Two glints drift east a pixel a frame (four frames loop over 16 px as the tile repeats).
    for k, (gx, gy) in enumerate(((2, 4), (9, 11))):
        x = (gx + frame * 4) % T
        for d in range(3 + k):
            s.put(ox + (x + d) % T, oy + gy, WATER[4] if d else WATER[5])
        s.put(ox + (x + 1) % T, oy + gy + 1, WATER[3])

def face(s: Sheet, ox: int, oy: int, ramp: list, lip, first: bool, seed: int, courses: int = 4) -> None:
    """A south-facing cliff or wall face: darker than any top, stone courses, a lit lip under the top on the first row."""
    for j in range(T):
        for i in range(T):
            row = j // courses
            shift = (row % 2) * 4
            col = ramp[1]
            if (i + shift) % 8 == 0 or j % courses == 0: col = ramp[0]
            elif h01(i, j, seed) < 0.12: col = ramp[2]
            s.put(ox + i, oy + j, col)
    if first:   # the rim: the top's edge seen from the front, and the dark first course under it (plan section 1.5)
        for i in range(T):
            s.put(ox + i, oy, lip[1])
            s.put(ox + i, oy + 1, lip[0])
            if lip is GRASS and h01(i, 0, seed) < 0.4: s.put(ox + i, oy + 2, GRASS[1])
            s.put(ox + i, oy + 2 + (1 if lip is GRASS else 0), ramp[0])

def face_wood(s: Sheet, ox: int, oy: int, first: bool) -> None:
    for j in range(T):
        for i in range(T):
            post = i % 8 in (1, 2)
            col = WATER[1] if not post else (WOOD[2] if i % 8 == 1 else WOOD[1])
            if j < 3 and first: col = WOOD[3] if j == 0 else WOOD[1]
            s.put(ox + i, oy + j, col)

def stairs(s: Sheet, ox: int, oy: int) -> None:
    # One step, 16 x 8: a lit tread of 5 px over a riser of 3 in the face tone.
    for j in range(8):
        for i in range(T):
            col = STONE[4] if j == 0 else STONE[3] if j < 5 else STONE[1] if j < 7 else STONE[0]
            s.put(ox + i, oy + j, col)

TILES = ["grass_a", "grass_b", "grass_flowers", "paving_a", "paving_b", "dirt", "wood", "rock",
         "stone_top", "water_0", "water_1", "water_2", "water_3", "stairs", "",  "",
         "earth_face_top", "earth_face", "stone_face_top", "stone_face", "rock_face_top", "rock_face", "wood_face_top", "wood_face",
         "bank_face_top", "bank_face"]

def build_tiles() -> tuple[Sheet, dict]:
    s = Sheet(8 * T, 4 * T)
    at = {}
    for k, name in enumerate(TILES):
        if not name: continue
        ox, oy = (k % 8) * T, (k // 8) * T
        at[name] = [ox, oy, T, T]
        match name:
            case "grass_a": tile_grass(s, ox, oy, 1)
            case "grass_b": tile_grass(s, ox, oy, 2)
            case "grass_flowers": tile_grass(s, ox, oy, 3, True)
            case "paving_a": tile_paving(s, ox, oy, 4)
            case "paving_b": tile_paving(s, ox, oy, 5)
            case "dirt": tile_dirt(s, ox, oy, 6)
            case "wood": tile_wood(s, ox, oy)
            case "rock": tile_rock(s, ox, oy, 7)
            case "stone_top": tile_stone_top(s, ox, oy)
            case "stairs":
                stairs(s, ox, oy)
                at[name] = [ox, oy, T, 8]
            case "earth_face_top" | "earth_face": face(s, ox, oy, EARTH, GRASS, name.endswith("top"), 11)
            case "stone_face_top" | "stone_face": face(s, ox, oy, STONE, PAVE[3:], name.endswith("top"), 12)
            case "rock_face_top" | "rock_face": face(s, ox, oy, ROCK, ROCK[2:], name.endswith("top"), 13, 5)
            case "bank_face_top" | "bank_face": face(s, ox, oy, STONE[:2] + [JSHADOW], STONE[3:], name.endswith("top"), 14)
            case "wood_face_top" | "wood_face": face_wood(s, ox, oy, name.endswith("top"))
            case _: tile_water(s, ox, oy, int(name[-1]))
    return s, at

# --------------------------------------------------------------------------------------------- props
HOUSE_LAYOUT = {  # by width in tiles: timber posts, the door, the lattice windows, the two red lanterns (x in the wall)
    6: {"posts": (0, 22, 42, 52, 72, 94), "door": 44, "windows": (8, 28, 60, 80), "lanterns": (38, 56)},
    4: {"posts": (0, 20, 26, 36, 42, 62), "door": 28, "windows": (6, 48), "lanterns": (22, 40)},
}

def house(s: Sheet, ox: int, oy: int, tw: int = 6) -> None:
    """A riverside house, footprint tw x 3 tiles (tw*16 x 48), walls two levels (32 px), a grey-tiled roof whose ridge
    ends curl up. The sprite is tw*16+8 x 92; the footprint's south-west corner sits at (4, 88). Its roof top is a
    floor two levels up (decision 29: you stand on it and jump off it)."""
    L = HOUSE_LAYOUT[tw]
    FW = tw * T
    W, H, fx, fy = FW + 8, 92, 4, 88
    wall_top = fy - 32
    # Stone base and plaster walls with timber posts.
    s.rect(ox + fx, oy + fy - 4, FW, 4, STONE[1])
    s.rect(ox + fx, oy + fy - 4, FW, 1, STONE[3])
    s.rect(ox + fx, oy + wall_top, FW, 28, PLASTER[1])
    for x in L["posts"]:
        s.rect(ox + fx + x, oy + wall_top, 2, 28, TIMBER[1])
        s.rect(ox + fx + x, oy + wall_top, 1, 28, TIMBER[2])
    s.rect(ox + fx, oy + wall_top + 3, FW, 2, TIMBER[1])
    d = L["door"]
    s.rect(ox + fx + d, oy + wall_top + 8, 8, 20, TIMBER[0])   # the door
    s.rect(ox + fx + d + 1, oy + wall_top + 9, 3, 19, WOOD[1])
    s.rect(ox + fx + d + 4, oy + wall_top + 9, 3, 19, WOOD[2])
    s.put(ox + fx + d + 3, oy + wall_top + 18, GOLD)
    s.put(ox + fx + d + 4, oy + wall_top + 18, GOLD)
    for wx in L["windows"]:   # lattice windows
        s.rect(ox + fx + wx, oy + wall_top + 10, 10, 9, TIMBER[0])
        for i in range(1, 9):
            for j in range(1, 8):
                if i % 3 and j % 3: s.put(ox + fx + wx + i, oy + wall_top + 10 + j, c("C9A15E"))
    # Two red lanterns under the eaves by the door.
    for lx in L["lanterns"]:
        s.ellipse(ox + fx + lx + 1, oy + wall_top + 10, 2.6, 3.2, c("C8483A"))
        s.put(ox + fx + lx, oy + wall_top + 9, c("F08A62"))
        s.put(ox + fx + lx + 1, oy + wall_top + 13, GOLD)
    # Roof: the footprint's top (48 deep) raised by the walls, 4 px of eave overhang, a ridge 8 px above.
    top, eave = 2, wall_top + 2
    ridge = top + 12
    for j in range(top, eave + 1):
        inset = max(0, 4 - (j - top)) if j < ridge else 0
        for i in range(inset, W - inset):
            if j < ridge:   # the north slope, foreshortened and in shade
                col = ROOF[1] if (i // 3) % 2 else ROOF[2]
            else:           # the south slope, lit: tile courses every 4 px, ridged columns every 3
                k = j - ridge
                col = ROOF[3] if (i // 3) % 2 else ROOF[2]
                if k % 4 == 3: col = ROOF[1]
                if k % 4 == 0 and (i // 3) % 2: col = ROOF[4]
            s.put(ox + i, oy + j, col)
    s.rect(ox + 2, oy + ridge - 1, W - 4, 2, ROOF[0])            # the ridge beam
    s.rect(ox + 2, oy + ridge - 2, W - 4, 1, ROOF[3])
    for end, dd in ((1, -1), (W - 2, 1)):                       # upturned ridge ends
        for k in range(5):
            s.put(ox + end + dd * (k // 2), oy + ridge - 2 - k, ROOF[0] if k else GOLD)
    s.rect(ox, oy + eave, W, 2, ROOF[0])                          # the eave's edge and its shadow on the wall
    s.rect(ox + fx, oy + eave + 2, FW, 2, c("8E8672"))
    s.outline(ox, oy, W, H)

def willow(s: Sheet, ox: int, oy: int) -> None:
    """A river willow, trunk footprint 1 x 1; 48 x 64 with the trunk base at (16, 62)."""
    s.rect(ox + 21, oy + 36, 6, 26, WOOD[1])
    s.rect(ox + 21, oy + 36, 2, 26, WOOD[2])
    s.rect(ox + 19, oy + 60, 10, 2, WOOD[0])
    s.ellipse(ox + 24, oy + 62, 9, 2, c("071015", 90))
    for k, (cx, cy, r) in enumerate(((24, 18, 17), (12, 26, 10), (36, 26, 10), (24, 30, 13))):
        s.ellipse(ox + cx, oy + cy, r, r * 0.8, GRASS[1] if k != 0 else GRASS[2])
    for i in range(4, 45):                                          # hanging fronds
        if h01(i, 0, 21) < 0.5:
            ln = 8 + int(h01(i, 1, 21) * 18)
            for j in range(22, min(58, 22 + ln)):
                s.put(ox + i, oy + j, GRASS[2] if j % 5 else GRASS[3])
    for k in range(30):
        s.put(ox + 8 + int(h01(k, 7, 22) * 32), oy + 6 + int(h01(k, 8, 22) * 20), GRASS[4])
    s.outline(ox, oy, 48, 64)

def lantern(s: Sheet, ox: int, oy: int) -> None:
    """A stone lantern post, footprint 1 x 1; 16 x 32 with its base at (0, 30)."""
    s.rect(ox + 5, oy + 22, 6, 8, STONE[2])
    s.rect(ox + 5, oy + 22, 2, 8, STONE[3])
    s.rect(ox + 3, oy + 20, 10, 2, STONE[1])
    s.rect(ox + 4, oy + 12, 8, 8, STONE[2])
    s.rect(ox + 6, oy + 14, 4, 4, GOLD)
    s.rect(ox + 7, oy + 15, 2, 2, PGOLD)
    s.rect(ox + 2, oy + 9, 12, 3, ROOF[1])
    s.rect(ox + 5, oy + 7, 6, 2, ROOF[2])
    s.outline(ox, oy, 16, 32)

def barrel(s: Sheet, ox: int, oy: int) -> None:
    """A barrel, footprint 1 x 1; 16 x 20 with its base at (0, 18)."""
    s.ellipse(ox + 8, oy + 13, 6, 5, WOOD[2])
    s.rect(ox + 2, oy + 7, 12, 7, WOOD[2])
    s.rect(ox + 2, oy + 7, 3, 7, WOOD[3])
    s.ellipse(ox + 8, oy + 7, 6, 3, WOOD[3])
    s.ellipse(ox + 8, oy + 7, 4, 2, WOOD[1])
    for y in (9, 14):
        s.rect(ox + 2, oy + y, 12, 1, BRONZE)
    s.outline(ox, oy, 16, 20)

def crates(s: Sheet, ox: int, oy: int) -> None:
    """Two stacked crates, footprint 2 x 1; 32 x 30 with the base at (0, 28)."""
    for bx, by, w, h in ((1, 12, 15, 16), (16, 14, 15, 14), (8, 1, 14, 13)):
        s.rect(ox + bx, oy + by, w, h, WOOD[3])
        s.rect(ox + bx, oy + by, w, 3, WOOD[4])
        s.rect(ox + bx + 1, oy + by + 4, w - 2, h - 5, WOOD[2])
        for k in range(h - 5):
            s.put(ox + bx + 1 + k * (w - 3) // max(1, h - 6), oy + by + 4 + k, WOOD[1])
    s.outline(ox, oy, 32, 30)

def notice(s: Sheet, ox: int, oy: int) -> None:
    """A notice board, footprint 2 x 1; 32 x 32 with the base at (0, 30)."""
    for x in (4, 26):
        s.rect(ox + x, oy + 6, 2, 24, TIMBER[1])
    s.rect(ox + 2, oy + 4, 28, 3, ROOF[2])
    s.rect(ox + 5, oy + 8, 22, 14, WOOD[2])
    for k, (px_, py_) in enumerate(((7, 10), (15, 9), (20, 13))):
        s.rect(ox + px_, oy + py_, 6, 7, PAPER)
        s.rect(ox + px_ + 1, oy + py_ + 2, 4, 1, INK if k != 1 else RED)
    s.outline(ox, oy, 32, 32)

def reeds(s: Sheet, ox: int, oy: int) -> None:
    """Reeds at the water's edge (no collision); 16 x 20 with the base at (0, 18)."""
    for k in range(6):
        x = 2 + k * 2 + int(h01(k, 0, 31) * 2)
        top = 3 + int(h01(k, 1, 31) * 7)
        for y in range(top, 18):
            s.put(ox + x, oy + y, GRASS[3] if y < top + 3 else GRASS[2])
        s.rect(ox + x, oy + top - 2, 1, 3, EARTH[1])
    s.outline(ox, oy, 16, 20)

def boat(s: Sheet, ox: int, oy: int) -> None:
    """A moored sampan on the water (no collision); 48 x 20 with its keel line at (0, 18)."""
    for j in range(6, 16):
        inset = max(0, abs(j - 11) - 1) * 2
        s.rect(ox + 2 + inset, oy + j, 44 - inset * 2, 1, WOOD[1] if j > 12 else WOOD[2])
    s.rect(ox + 4, oy + 8, 40, 2, WOOD[3])
    s.rect(ox + 16, oy + 2, 16, 6, ROOF[2])          # the woven canopy
    s.rect(ox + 16, oy + 2, 16, 1, ROOF[4])
    s.rect(ox + 6, oy + 16, 36, 1, WATER[4])
    s.outline(ox, oy, 48, 20)

# kind: (draw, sprite w, h, footprint w, h in tiles, origin = the footprint's south-west corner in the sprite, solid)
PROPS = {
    "house": (house, 104, 92, 6, 3, [4, 88], True),
    "willow": (willow, 48, 64, 1, 1, [16, 62], True),
    "lantern": (lantern, 16, 32, 1, 1, [0, 30], True),
    "barrel": (barrel, 16, 20, 1, 1, [0, 18], True),
    "crates": (crates, 32, 30, 2, 1, [0, 28], True),
    "notice": (notice, 32, 32, 2, 1, [0, 30], True),
    "reeds": (reeds, 16, 20, 1, 1, [0, 18], False),
    "boat": (boat, 48, 20, 3, 1, [0, 18], False),
    "storehouse": (lambda s, ox, oy: house(s, ox, oy, 4), 72, 92, 4, 3, [4, 88], True),
}
# Phase 2 (decision 29): props whose top is a floor you stand on, in levels over their ground.
TOPS = {"house": 2, "storehouse": 2, "crates": 1}

def build_props() -> tuple[Sheet, dict]:
    s = Sheet(256, 192)
    at, x, y, row_h = {}, 0, 0, 0
    for kind, (draw, w, h, fw, fh, origin, solid) in PROPS.items():
        if x + w > s.w:
            x, y, row_h = 0, y + row_h, 0
        draw(s, x, y)
        at[kind] = {"rect": [x, y, w, h], "footprint": [fw, fh], "origin": origin, "solid": solid}
        if kind in TOPS: at[kind]["top"] = TOPS[kind]
        x, row_h = x + w, max(row_h, h)
    return s, at

# --------------------------------------------------------------------------------------------- the placeholder body
CELL_W, CELL_H, FOOT = 32, 48, (16, 46)
BODY_ANIMS = {"idle": 2, "walk": 4, "jump": 3, "dash": 2, "strike": 2}   # strike (Phase 2): wind-up, then the arm out
SKIN, SKIN_D, HAIR = c("E3B48C"), c("B9855F"), c("1B1614")

def body_frame(s: Sheet, ox: int, oy: int, facing: str, anim: str, f: int) -> None:
    """A plain stand-in figure ~38 px tall: topknot, jade robe with a gold sash, dark trousers. Not final art."""
    fx, fy = ox + FOOT[0], oy + FOOT[1]
    bob = {"idle": (0, 1), "walk": (0, 1, 0, 1), "jump": (2, -1, 3), "dash": (1, 1), "strike": (0, 0)}[anim][f]
    lean = 2 if anim == "dash" and facing == "e" else 0
    stride = {"walk": (3, 0, -3, 0), "dash": (4, 4)}.get(anim, (0,) * 4)[f]
    tuck = anim == "jump" and f == 1
    # Legs (trousers and shoes), then the robe, arms, head.
    for side in (-1, 1):
        if facing == "e":
            lx = fx - 2 + (stride if side > 0 else -stride)
        else:
            lx = fx + side * 3 - 1
        ly = -(stride * side) // 3 if facing != "e" and anim == "walk" else 0
        leg_h = 6 if tuck else 9
        s.rect(lx, fy - leg_h - 1 + ly, 3, leg_h, c("2A2F36"))
        s.rect(lx - (1 if facing == "e" else 0), fy - 2 + ly - (3 if tuck else 0), 4, 2, INK)
    top = fy - 30 + bob
    robe_bottom = fy - 7 + (bob if anim == "jump" else 0)
    for j in range(top + 8, robe_bottom):
        half = 5 + (j - top - 8) // 5
        x0 = fx - half + lean
        for i in range(x0, fx + half + lean):
            col = JADE if i < fx + lean + (1 if facing != "n" else 3) else JSHADOW
            s.put(i, j, col)
    s.rect(fx - 5 + lean, top + 15, 10, 2, GOLD)                            # the sash
    if facing != "n":
        s.rect(fx - 1 + lean, top + 8, 2, 7, BJADE if facing == "s" else JADE)   # the robe's collar
    arm_dy = -5 if anim == "jump" and f == 0 else 0
    for side in (-1, 1):
        if facing == "e" and side < 0: continue
        if anim == "strike" and side > 0:   # the striking arm, drawn below
            continue
        ax = fx + side * 6 + lean if facing != "e" else fx + 2 - stride // 2 + lean
        s.rect(ax - 1, top + 9 + arm_dy, 2, 8, JSHADOW if side > 0 else JADE)
        s.rect(ax - 1, top + 17 + arm_dy, 2, 2, SKIN)
    if anim == "strike":   # f 0 draws the arm back, f 1 thrusts it out along the facing, the palm open
        if facing == "e":
            if f == 0:
                s.rect(fx - 5, top + 10, 6, 2, JSHADOW)
                s.rect(fx - 7, top + 10, 2, 2, SKIN)
            else:
                s.rect(fx + 2, top + 11, 9, 2, JSHADOW)
                s.rect(fx + 11, top + 10, 2, 4, SKIN)
        elif facing == "s":
            s.rect(fx + 5, top + (5 if f == 0 else 12), 2, 7 if f == 0 else 10, JSHADOW)
            s.rect(fx + 4, top + (3 if f == 0 else 22), 4, 2, SKIN)
        else:
            s.rect(fx + 5, top + (8 if f == 0 else 1), 2, 7 if f == 0 else 9, JSHADOW)
            s.rect(fx + 5, top + (15 if f == 0 else 0), 2, 2, SKIN)
    hx, hy = fx + lean + (1 if facing == "e" else 0), top + 3
    s.ellipse(hx, hy + 1, 4.6, 4.8, SKIN)
    if facing == "s":
        s.rect(hx - 4, hy - 4, 9, 3, HAIR)
        s.put(hx - 2, hy + 1, INK)
        s.put(hx + 1, hy + 1, INK)
    elif facing == "e":
        s.rect(hx - 5, hy - 4, 7, 4, HAIR)
        s.rect(hx - 5, hy - 1, 3, 4, HAIR)
        s.put(hx + 2, hy + 1, INK)
        s.put(hx + 4, hy + 2, SKIN_D)
    else:
        s.ellipse(hx, hy + 0.5, 4.6, 4.6, HAIR)
    s.rect(hx - 1, hy - 7, 3, 3, HAIR)                                        # the topknot
    s.put(hx, hy - 8, GOLD)
    if anim == "dash":   # speed streaks behind the body
        for k in range(3):
            y = top + 12 + k * 5
            if facing == "e":
                s.rect(fx - 13, y, 6 - k, 1, BJADE)
            else:
                s.rect(fx - 8 + k * 6, robe_bottom + 1 + (k % 2), 2, 1, BJADE)

def build_body() -> tuple[Sheet, dict]:
    cols = sum(BODY_ANIMS.values())
    s = Sheet(cols * CELL_W, 3 * CELL_H)
    frames = {}
    for r, facing in enumerate(("s", "e", "n")):
        col = 0
        for anim, n in BODY_ANIMS.items():
            frames.setdefault(anim, {})[facing] = [[(col + f) * CELL_W, r * CELL_H] for f in range(n)]
            for f in range(n):
                body_frame(s, (col + f) * CELL_W, r * CELL_H, facing, anim, f)
                s.outline((col + f) * CELL_W, r * CELL_H, CELL_W, CELL_H)
            col += n
    return s, {"placeholder": True, "cell": [CELL_W, CELL_H], "foot": list(FOOT), "frames": frames,
               "note": "PLACEHOLDER body for the Phase 1 controller; the layered set is Phase 5"}

# --------------------------------------------------------------------------------------------- PLACEHOLDER foes (Phase 2)
FOE_CELL, FOE_FOOT = (32, 24), (16, 21)
FOE_ANIMS = {"idle": 2, "walk": 2, "windup": 1, "attack": 1, "hurt": 1}
FOES = ("mudshell_crab", "reedtail_rat", "wild_boarlet")

def _lit(col, hurt: bool):
    """A hurt frame flashes pale: each colour half-way to paper."""
    return tuple((a + b) // 2 for a, b in zip(col[:3], PAPER[:3])) + (col[3],) if hurt else col

def foe_frame(s: Sheet, ox: int, oy: int, species: str, anim: str, f: int) -> None:
    """Stand-in foes seen from the three-quarter view, facing east (west mirrors): a mud crab, a reed rat and a boarlet
    at the size of their side-view sheets (crab 20 x 13, rat 22 x 11, boarlet 26 x 15). Not final art (Phase 3/5)."""
    fx, fy = ox + FOE_FOOT[0], oy + FOE_FOOT[1]
    bob = (0, 1)[f] if anim == "idle" else 0
    step = (1, -1)[f] if anim == "walk" else 0
    lunge = {"windup": -2, "attack": 3}.get(anim, 0)
    h = anim == "hurt"
    L = lambda col: _lit(col, h)
    cx = fx + lunge
    if species == "mudshell_crab":
        for k in range(3):   # three legs a side, stepping
            for side in (-1, 1):
                s.rect(cx - 6 + k * 4 + (step if (k + (side > 0)) % 2 else -step), fy - 3 + (1 if side > 0 else -1), 2, 2, L(EARTH[0]))
        s.ellipse(cx, fy - 6 + bob, 8, 5, L(c("5A4633")))
        s.ellipse(cx - 1, fy - 7 + bob, 6, 3, L(c("7C6446")))
        s.rect(cx - 3, fy - 9 + bob, 4, 1, L(c("9C8260")))
        claw_y = -3 if anim == "windup" else 0
        reach = 2 if anim == "attack" else 0
        for dy in (-9, -3):
            s.ellipse(cx + 9 + reach, fy + dy + claw_y + bob, 2.6, 2.2, L(c("8A5A3E")))
            s.put(cx + 11 + reach, fy + dy + claw_y + bob, L(INK))
        s.put(cx + 4, fy - 11 + bob, L(INK))
        s.put(cx + 6, fy - 10 + bob, L(INK))
    elif species == "reedtail_rat":
        for i in range(7):   # the tail, curling back
            s.put(cx - 8 - i, fy - 5 - (i * i) // 12 + (step if i > 3 else 0), L(c("B98E7A")))
        for k, dx in enumerate((-4, 3)):
            s.rect(cx + dx + (step if k else -step), fy - 2, 2, 2, L(c("2A2320")))
        s.ellipse(cx - 1, fy - 5 + bob, 7, 4, L(c("6E6258")))
        s.ellipse(cx - 2, fy - 6 + bob, 5, 2, L(c("8A7E72")))
        s.ellipse(cx + 6, fy - 6 + bob, 3.5, 3, L(c("7A6E62")))
        s.put(cx + 5, fy - 10 + bob, L(c("C99A8E")))
        s.put(cx + 7, fy - 7 + bob, L(INK))
        s.put(cx + 10, fy - 6 + bob, L(c("D98A8A")))
        if anim == "attack":
            s.put(cx + 10, fy - 4 + bob, L(PAPER))
    else:   # wild_boarlet
        for k, dx in enumerate((-7, -3, 4, 8)):
            s.rect(cx + dx + (step if k % 2 else -step), fy - 3, 2, 3, L(c("2B1E16")))
        s.ellipse(cx - 1, fy - 8 + bob, 10, 6, L(c("6B4A30")))
        for i in (-6, -2, 2):   # a young boar's stripes
            s.rect(cx + i, fy - 12 + bob, 2, 6, L(c("8C6A46")))
        s.ellipse(cx + 8, fy - 8 + bob, 4, 4, L(c("5E4029")))
        s.rect(cx + 11, fy - 8 + bob, 2, 3, L(c("A77A62")))
        s.put(cx + 11, fy - 5 + bob, L(PAPER))          # the tusk
        s.put(cx + 9, fy - 10 + bob, L(INK))
        s.put(cx + 6, fy - 13 + bob, L(c("4A3222")))   # the ear
        if anim == "windup":
            for i in range(3):
                s.put(cx - 12 - i * 2, fy - 2, L(EARTH[2]))   # pawing the ground

def build_foes() -> tuple[Sheet, dict]:
    cols = sum(FOE_ANIMS.values())
    s = Sheet(cols * FOE_CELL[0], len(FOES) * FOE_CELL[1])
    species = {}
    for r, sp in enumerate(FOES):
        col = 0
        for anim, n in FOE_ANIMS.items():
            species.setdefault(sp, {})[anim] = [[(col + f) * FOE_CELL[0], r * FOE_CELL[1]] for f in range(n)]
            for f in range(n):
                foe_frame(s, (col + f) * FOE_CELL[0], r * FOE_CELL[1], sp, anim, f)
                s.outline((col + f) * FOE_CELL[0], r * FOE_CELL[1], FOE_CELL[0], FOE_CELL[1])
            col += n
    return s, {"placeholder": True, "cell": list(FOE_CELL), "foot": list(FOE_FOOT), "species": species,
               "note": "PLACEHOLDER foes for the Phase 2 fights (east drawn, west mirrored); the top-down creature sheets are Phase 3/5"}

def main() -> None:
    tiles, tile_at = build_tiles()
    props, prop_at = build_props()
    body, body_at = build_body()
    foes, foes_at = build_foes()
    tiles.save(ROOT / "art/topdown/proto_tiles.png")
    props.save(ROOT / "art/topdown/proto_props.png")
    body.save(ROOT / "art/topdown/placeholder_body.png")
    foes.save(ROOT / "art/topdown/placeholder_foes.png")
    manifest = {"schema_version": 1, "tile": T, "tiles": tile_at, "props": prop_at, "body": body_at, "foes": foes_at}
    out = ROOT / "data/topdown/proto_tileset.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print("tiles %dx%d, props %dx%d, body %dx%d" % (tiles.w, tiles.h, props.w, props.h, body.w, body.h))

if __name__ == "__main__":
    main()
