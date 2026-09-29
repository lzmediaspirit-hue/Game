"""The study's review images (decision 42), from the shots study_capture.gd took in the game.

Usage: python3 tools/art/topdown/study_quality/compose.py [--shots DIR]

Writes docs/redesign/feedback/character_quality/:
  01_village_square.png, 02_jade_gate_street.png   each scene four ways at 1280x720, A B over C D, labelled
  01_village_square_x3.png, 02_jade_gate_street_x3.png   the same, cut round the player and the villagers, x3
  03_run_attack_s.gif, 03_run_attack_se.gif   the player's run and rising cut, A B C D side by side, at 14 fps
  03_run_attack_strip_s.png, 03_run_attack_strip_se.png   the same frames laid out, x2
  04_phone_1080p.png   what a phone 1080 px tall shows, one device px to one px: the view is scaled x1.5 by the
                       game's canvas stretch, so the world's art px are 3 device px and C's figure px 1.5
Every scale is nearest neighbour; nothing is resampled otherwise.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = ROOT / "docs/redesign/feedback/character_quality"
OPTS = ["A", "B", "C", "D"]
LABEL = {
    "A": "A · today: 38 px, the world's density",
    "B": "B · same size, drawn better: 38 px",
    "C": "C · double density: 76 px over the world at x2",
    "D": "D · larger figure: 48 px, the world's density",
}
SCENES = {"01_village_square": "The village square (Lotus Ferry)", "02_jade_gate_street": "Jade Gate Street"}
BG = (7, 16, 21)
INK = (232, 225, 207)
DIM = (150, 164, 160)
GAP = 12


def font(size: int, pixel: bool = False):
    return ImageFont.truetype(str(ROOT / ("art/fonts/PixelifySans.ttf" if pixel else "art/fonts/SourceSerif4.ttf")), size)


def board(title: str, panels: list, cols: int, note: str = "") -> Image.Image:
    """Panels [(label, image)] in a grid under a title, each at its own size (nearest only)."""
    cw = max(p[1].width for p in panels)
    chh = max(p[1].height for p in panels)
    rows = (len(panels) + cols - 1) // cols
    head = 56 if not note else 84
    lab = 34
    W = cols * cw + (cols + 1) * GAP
    H = head + rows * (chh + lab) + (rows + 1) * GAP
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((GAP, 12), title, fill=INK, font=font(28))
    if note:
        d.text((GAP, 50), note, fill=DIM, font=font(18))
    for i, (label, p) in enumerate(panels):
        x = GAP + (i % cols) * (cw + GAP)
        y = head + GAP + (i // cols) * (chh + lab + GAP)
        d.text((x, y + 2), label, fill=INK, font=font(22))
        im.paste(p.convert("RGB"), (x, y + lab))
    return im


def closeup_rect(b: dict, k: int = 3) -> tuple:
    """The x`k` cut round the player and the villagers, in the 1280x720 shot."""
    xs = [v[0] for v in b["people"].values()] + [b["player"][0]]
    ys = [v[1] for v in b["people"].values()] + [b["player"][1]]
    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) - 42 + max(ys) + 4) / 2
    cw, ch = 1280 // k // 2, 720 // k // 2
    x0 = int(round((cx - b["camera"][0]) * 2 + 640 - cw))
    y0 = int(round((cy - b["camera"][1]) * 2 + 360 - ch))
    return x0, y0, x0 + 2 * cw, y0 + 2 * ch


def x(im: Image.Image, k: float) -> Image.Image:
    return im.resize((int(round(im.width * k)), int(round(im.height * k))), Image.NEAREST)


def scenes(shots: Path, boxes: dict) -> None:
    for sc, title in SCENES.items():
        have = [o for o in OPTS if (shots / ("%s_%s.png" % (sc, o))).exists()]
        full = [(LABEL[o], Image.open(shots / ("%s_%s.png" % (sc, o)))) for o in have]
        board(title + " · in the game at 1280x720, the same instant four ways", full, 2,
              "The world is 640x360 shown x2 in every option; only the characters change.").save(OUT / (sc + ".png"))
        r = closeup_rect(boxes[sc])
        cut = [(LABEL[o] + " · x3", x(Image.open(shots / ("%s_%s.png" % (sc, o))).crop(r), 3)) for o in have]
        board(title + " · x3 round the player and the villagers", cut, 2,
              "x3 of the 1280x720 view (x6 of the world's art px): one world px is 6 px here, one of C's figure px 3.").save(
            OUT / (sc + "_x3.png"))


def _frame(shots: Path, o: str, act: str, row: str, i: int) -> Image.Image:
    im = Image.open(shots / ("strip_%s_%s_%s_%d.png" % (o, act, row, i)))
    return im.crop((45, 80, 195, 230))           # 150x150 round the feet (the feet at 120, 200), at 1280x720


def strips(shots: Path) -> None:
    have = [o for o in OPTS if (shots / ("strip_%s_run_s_0.png" % o)).exists()]
    seq = [("run", 8), ("swing_1", 6)]
    k = 2
    fw, fh = 150 * k, 150 * k
    lab = 30
    for row in ("s", "se"):
        frames, durs = [], []
        order = [("run", i) for _ in range(3) for i in range(8)] + [("swing_1", i) for i in range(6)]
        for act, i in order:
            im = Image.new("RGB", (len(have) * fw + (len(have) + 1) * GAP, fh + lab + 2 * GAP), BG)
            d = ImageDraw.Draw(im)
            for n, o in enumerate(have):
                xx = GAP + n * (fw + GAP)
                d.text((xx, GAP), o + (" · run" if act == "run" else " · rising cut") + " · " + row.upper(), fill=INK,
                       font=font(20))
                im.paste(x(_frame(shots, o, act, row, i), k).convert("RGB"), (xx, GAP + lab))
            frames.append(im)
            durs.append(70 if not (act == "swing_1" and i == 5) else 500)
        pal = [f.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
        pal[0].save(OUT / ("03_run_attack_%s.gif" % row), save_all=True, append_images=pal[1:], duration=durs, loop=0,
                    optimize=False, disposal=1)
        # The strip: per option a row, the run's eight frames then the cut's six, x2.
        cols = sum(n for _, n in seq)
        head = 56
        W = 150 + cols * (fw + 4) + GAP
        H = head + len(have) * (fh + GAP) + GAP
        im = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(im)
        d.text((GAP, 12), "The player's run (8 frames, 14 fps) and the jian's rising cut (6 frames), facing %s, in the "
               "game at 1280x720, shown x2" % row.upper(), fill=INK, font=font(26))
        y = head
        for o in have:
            d.text((GAP, y + fh // 2 - 14), LABEL[o].split(" · ")[0], fill=INK, font=font(30))
            xx = 150
            for act, n in seq:
                for i in range(n):
                    im.paste(x(_frame(shots, o, act, row, i), k).convert("RGB"), (xx, y))
                    xx += fw + 4
            y += fh + GAP
        im.save(OUT / ("03_run_attack_strip_%s.png" % row))


def phone(shots: Path, boxes: dict) -> None:
    """The 1080p phone: the game's 1280x720 canvas stretched x1.5 (canvas_items, aspect kept). A, B, D: the 640x360
    view x3; C: its 1280x720 view x1.5, so its figure px fall on one or two device px by turns."""
    sc = "01_village_square"
    b = boxes[sc]
    have = [o for o in OPTS if (shots / ("%s_%s.png" % (sc, o))).exists()]
    panels = []
    for o in have:
        im = Image.open(shots / ("%s_%s.png" % (sc, o)))
        if o == "C":
            dev = x(im, 1.5)
        else:
            dev = x(im.resize((640, 360), Image.NEAREST), 3)
        cx = (b["player"][0] - b["camera"][0]) * 3 + 960
        cy = (b["player"][1] - b["camera"][1]) * 3 + 540
        panels.append((LABEL[o].split(" · ")[0] + " on a 1080 px phone, 1:1 device px",
                       dev.crop((int(cx - 320), int(cy - 175), int(cx + 320), int(cy + 150)))))
    board("On the phone: device pixels 1:1 (a 1080 px tall screen, where the game draws each world px as 3x3)", panels, 2,
          "C's figure px are 1.5 device px there, so they alternate 1 and 2 px; A, B and D stay whole (3x3).").save(
        OUT / "04_phone_1080p.png")


def main(argv: list) -> int:
    shots = HERE / "build/shots"
    if "--shots" in argv:
        shots = Path(argv[argv.index("--shots") + 1])
    OUT.mkdir(parents=True, exist_ok=True)
    boxes = json.loads((shots / "boxes.json").read_text())
    scenes(shots, boxes)
    strips(shots)
    phone(shots, boxes)
    for f in sorted(OUT.iterdir()):
        print(f.name, f.stat().st_size)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
