"""Top-down redesign, Phase 1 (docs/redesign_top_down_plan.md): the placeholder body.

Draws art/topdown/placeholder_body.png, a PLACEHOLDER body in S, E, N (W mirrors E) x idle 2, walk 4, jump 3, dash 2,
at native art resolution (1 art px = 1 px of the 640x360 world viewport, nearest neighbour). Phase 1's tiles and props
were replaced in Phase 3 by tools/art/topdown/build_tiles.py, which writes the atlas, props, manifest and TileSet and
calls build_body() here for the body; running this script runs that build. No randomness: a rebuild is byte-identical.
The body is a stand-in to judge the controller's feel; the layered character set is Phase 5 (AGENTS.md rules 1-4).

Usage: python3 tools/art/build_topdown_proto.py   (same as python3 tools/art/topdown/build_tiles.py)
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image


def c(h: str, a: int = 255) -> tuple:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)

# Palette tokens (docs/art-contracts.md).
INK, JSHADOW, JADE, BJADE, GOLD = c("071015"), c("15514F"), c("2C9E8F"), c("67D6BD"), c("E5B84C")
CLEAR = (0, 0, 0, 0)

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
BODY_ANIMS = {"idle": 2, "walk": 4, "jump": 3, "dash": 2}
SKIN, SKIN_D, HAIR = c("E3B48C"), c("B9855F"), c("1B1614")

def body_frame(s: Sheet, ox: int, oy: int, facing: str, anim: str, f: int) -> None:
    """A plain stand-in figure ~38 px tall: topknot, jade robe with a gold sash, dark trousers. Not final art."""
    fx, fy = ox + FOOT[0], oy + FOOT[1]
    bob = {"idle": (0, 1), "walk": (0, 1, 0, 1), "jump": (2, -1, 3), "dash": (1, 1)}[anim][f]
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
        ax = fx + side * 6 + lean if facing != "e" else fx + 2 - stride // 2 + lean
        s.rect(ax - 1, top + 9 + arm_dy, 2, 8, JSHADOW if side > 0 else JADE)
        s.rect(ax - 1, top + 17 + arm_dy, 2, 2, SKIN)
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
    """The tiles, props, manifest and TileSet are built by tools/art/topdown/build_tiles.py (Phase 3), which draws this
    body through build_body(); running this script runs that build."""
    sys.path.insert(0, str(Path(__file__).resolve().parent / "topdown"))
    import build_tiles
    sys.exit(build_tiles.main(sys.argv[1:]))

if __name__ == "__main__":
    main()
