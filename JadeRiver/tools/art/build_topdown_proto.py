"""Top-down redesign, Phases 1-2 (docs/redesign_top_down_plan.md): the placeholder body.

Draws, at native art resolution (1 art px = 1 px of the 640x360 world viewport, nearest neighbour):
  art/topdown/placeholder_body.png PLACEHOLDER body: S, E, N (W mirrors E) x idle 2, walk 4, jump 3, dash 2, strike 2
The tiles, props, foes, manifest and TileSet are built by tools/art/topdown/build_tiles.py (Phase 3,
docs/redesign/art_bible.md), which calls build_body() here; running this script runs that build. Everything is original
to Jade River. No randomness: noise comes from a coordinate hash, and the PNGs carry no metadata, so a rebuild is
byte-identical. The body is a stand-in; the layered character set is Phase 5 (AGENTS.md rules 1-4).

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

def main() -> None:
    """The tiles, props, foes, manifest and TileSet are built by tools/art/topdown/build_tiles.py (Phase 3), which draws
    the body through build_body(); running this script runs that build."""
    sys.path.insert(0, str(Path(__file__).resolve().parent / "topdown"))
    import build_tiles
    sys.exit(build_tiles.main(sys.argv[1:]))

if __name__ == "__main__":
    main()
