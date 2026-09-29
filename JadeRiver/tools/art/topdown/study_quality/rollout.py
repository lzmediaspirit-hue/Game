"""Decision 42's rollout: the before and after pairs in docs/redesign/feedback/character_quality/rollout/, from the shots
tools/dev/topdown_capture.gd takes in the game (`-- --quality --quality-tag=before`, then `after` once the sheets are
rebuilt), the same instant each time.

  <shot>.png      the whole view, before over after (the world at x2)
  <shot>_x3.png   round the people, before over after, at x3 of the shot (x6 of the world's art px)
  03_fight_combo.png  the three cuts frame by frame round the body, before over after

Usage: python3 tools/art/topdown/study_quality/rollout.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[4]
DIR = ROOT / "docs/redesign/feedback/character_quality/rollout"
SHOTS = {"01_village_square": "The village square (Lotus Ferry): the player, Uncle Guo, Washer Mei, Little Dou, Shen Lian",
         "02_jade_gate_street": "Jade Gate Street: the player, Deacon Rui, Disciple Yue, Steward Wei, Disciple Hao",
         "03_fight": "A fight on the square with the jian: the rising cut",
         "04_gestures": "The story's gestures: the player and Shen Lian salute, Guo kneels, Mei points, Dou starts back"}
INK = (7, 16, 21, 255)
TEXT = (232, 225, 207, 255)
SUB = (175, 201, 209, 255)


def _font(size: int, bold: bool = False):
    for name in ("NotoSerif-Bold.ttf" if bold else "NotoSerif-Regular.ttf",
                 "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"):
        for d in ("/usr/share/fonts/truetype/noto", "/usr/share/fonts/truetype/dejavu"):
            try:
                return ImageFont.truetype("%s/%s" % (d, name), size)
            except OSError:
                pass
    return ImageFont.load_default()


def _board(title: str, rows: list, vertical: bool) -> Image.Image:
    """Images under their labels, one above the other (`vertical`) or side by side."""
    pad, head, lab = 12, 40, 26
    ws = [im.width for _, im in rows]
    hs = [im.height for _, im in rows]
    if vertical:
        W = max(ws) + 2 * pad
        H = head + sum(h + lab + pad for h in hs) + pad
    else:
        W = sum(ws) + pad * (len(rows) + 1)
        H = head + lab + max(hs) + 2 * pad
    W = max(W, int(ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(title, font=_font(20, True))) + 2 * pad)
    out = Image.new("RGBA", (W, H), INK)
    d = ImageDraw.Draw(out)
    d.text((pad, 10), title, font=_font(20, True), fill=TEXT)
    x, y = pad, head
    for label, im in rows:
        d.text((x, y + 2), label, font=_font(16), fill=SUB)
        out.alpha_composite(im.convert("RGBA"), (x, y + lab))
        if vertical:
            y += lab + im.height + pad
        else:
            x += im.width + pad
    return out


def _crop(im: Image.Image, pts: list, k: int = 3) -> Image.Image:
    """The box round the feet `pts` (x2 screen px), a body's height above and some room round, at xk."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1 = int(min(xs)) - 60, int(max(xs)) + 60
    y0, y1 = int(min(ys)) - 110, int(max(ys)) + 24
    if x1 - x0 < 420:                       # a lone body (the fight): room for what it fights
        x0, x1 = (x0 + x1) // 2 - 210, (x0 + x1) // 2 + 210
    w, h = x1 - x0, y1 - y0
    # a 16:9 box at least
    if w < h * 16 / 9:
        grow = int(h * 16 / 9) - w
        x0 -= grow // 2
        x1 = x0 + int(h * 16 / 9)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(im.width, x1), min(im.height, y1)
    c = im.crop((x0, y0, x1, y1))
    return c.resize((c.width * k, c.height * k), Image.NEAREST)


def main() -> int:
    before, after = DIR / "before", DIR / "after"
    boxes = json.loads((after / "boxes.json").read_text())
    for name, title in SHOTS.items():
        a, b = Image.open(before / (name + ".png")), Image.open(after / (name + ".png"))
        _board(title + " · the world at x2", [("Before: the figure as it was", a), ("After: drawn better (decision 42, B)", b)],
               True).save(DIR / (name + ".png"))
        bx = boxes.get(name, {})
        pts = [bx["player"]] + list(bx.get("people", {}).values())
        _board(title + " · x3 (x6 of the world's art px)", [("Before", _crop(a, pts)), ("After", _crop(b, pts))],
               True).save(DIR / (name + "_x3.png"))
    a, b = Image.open(before / "03_fight_combo.png"), Image.open(after / "03_fight_combo.png")
    _board("The jian's three cuts in the fight, frame by frame (the world at x2)", [("Before", a), ("After", b)], True).save(
        DIR / "03_fight_combo.png")
    old = json.loads((before / "boxes.json").read_text())
    for name in SHOTS:
        a, b = old.get(name, {}).get("texture_mb"), boxes.get(name, {}).get("texture_mb")
        if a and b:
            print("%-22s texture memory %.1f MB before, %.1f MB after (%+.1f MB)" % (name, a, b, b - a))
    print("rollout boards in", DIR.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
