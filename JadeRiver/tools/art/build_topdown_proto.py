"""Top-down redesign, Phases 1-2 (docs/redesign_top_down_plan.md): the placeholder body and foes.

Draws, at native art resolution (1 art px = 1 px of the 640x360 world viewport, nearest neighbour):
  art/topdown/placeholder_foes.png PLACEHOLDER foes (Phase 2): crab, rat, boarlet, E (W mirrors) x idle, walk, windup, attack, hurt
The Phase 1-2 placeholder body is gone: the player is the real character (Phase 3, tools/art/topdown/build_character.py).
The tiles, props, manifest and TileSet moved to tools/art/topdown/build_tiles.py in Phase 3 (docs/redesign/art_bible.md),
which calls build_foes() here; running this script runs that build. Everything is original to Jade
River. No randomness: noise comes from a coordinate hash, and the PNGs carry no metadata, so a rebuild is byte-identical.
The foes are stand-ins until the creature sheets.

Usage: python3 tools/art/build_topdown_proto.py   (same as python3 tools/art/topdown/build_tiles.py)
"""
from __future__ import annotations

import sys
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
    """The tiles, props, manifest and TileSet are built by tools/art/topdown/build_tiles.py (Phase 3), which draws the
    foes through build_foes(); running this script runs that build."""
    sys.path.insert(0, str(Path(__file__).resolve().parent / "topdown"))
    import build_tiles
    sys.exit(build_tiles.main(sys.argv[1:]))

if __name__ == "__main__":
    main()
