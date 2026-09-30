"""Decision 43: build the top-down foes (art bible §8 "Foes"; tools/art/topdown/creatures.py and creature/), a sheet a
species, and the manifest the room view reads.

Writes (1 art px = 1 px of the 640x360 world viewport, nearest neighbour, no metadata, byte-identical on every build):
  art/topdown/foes/<species>.png   a row per drawn facing (S, SE, E, NE, N), the frames of every action along it in
                                   the species' own cell; <species>_elite.png its elite's, in the elite's cell
  data/topdown/foes.json           the index: per species its sheet, cell, feet, blob shadow, label height and each
                                   action's frames, rate and loop (TopdownRoom.load_room lays it in as the tile set's
                                   `foes`)
With --review it also renders into docs/redesign/feedback/monsters/sheets/ each species' sheet at x3 on a meadow tone,
labelled (and its elite's), each species facing SE playing its whole catalogue at the game's rates as a
GIF at x4 (its elite beside it), and every species' tell side by side (tells_x4.png).

Usage: python3 tools/art/topdown/build_foes.py [--jobs N] [--review] [--check] [--only sp1,sp2]
  --check  builds twice in memory and fails unless both builds are byte-identical
  --only   builds and reviews only those species and writes nothing but their review images (for iterating)
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from PIL import Image  # noqa: E402

import creatures  # noqa: E402

MANIFEST = "data/topdown/foes.json"
FOES_DIR = "art/topdown/foes"
REVIEW = ROOT / "docs/redesign/feedback/monsters/sheets"


def png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False)
    return buf.getvalue()


def build_all(jobs: int, only=None) -> tuple[dict, dict]:
    sheets, man = creatures.build(jobs, only)
    out = {p: png_bytes(im) for p, im in sheets.items()}
    out[MANIFEST] = (json.dumps(man, indent=1, sort_keys=True) + "\n").encode()
    return out, sheets


def _sheet(sheets: dict, look: dict) -> Image.Image:
    return sheets[look["atlas"][len("res://"):]]


def _cell(sheet: Image.Image, look: dict, action: str, facing: str, i: int) -> Image.Image:
    at = look["actions"][action]["frames"][facing][i]
    cw, ch = look["cell"]
    return sheet.crop((at[0], at[1], at[0] + cw, at[1] + ch))


def review(sheets: dict, man: dict) -> None:
    """Each species' sheet at x3 (`<species>_x3.png`, an elite's `<species>_elite_x3.png`): a row per facing, the actions'
    names over their columns."""
    from PIL import ImageDraw, ImageFont
    REVIEW.mkdir(parents=True, exist_ok=True)
    try:
        head = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except OSError:
        head = ImageFont.load_default()
    z, lw, th = 3, 120, 24
    for sp, block in man["species"].items():
        for label, look in [("", block)] + [(v, block[v]) for v in ("elite", "awakened") if v in block]:
            sheet = _sheet(sheets, look)
            cw, ch = look["cell"]
            order = creatures.REGISTRY[sp].actions()
            n = sum(len(look["actions"][a]["frames"]["s"]) for a in order)
            out = Image.new("RGBA", (lw + n * cw * z, th + len(man["dirs"]) * ch * z), (22, 30, 34, 255))
            dr = ImageDraw.Draw(out)
            x = lw
            for a in order:
                k = len(look["actions"][a]["frames"]["s"])
                dr.text((x + 4, 4), "%s (%d, %d fps)" % (a, k, look["actions"][a]["fps"]), font=head, fill=(232, 225, 207, 255))
                x += k * cw * z
            for r, d in enumerate(man["dirs"]):
                c = 0
                for a in order:
                    for i in range(len(look["actions"][a]["frames"][d])):
                        tone = (99, 150, 76, 255) if (r + c) % 2 else (92, 140, 70, 255)
                        cell = Image.new("RGBA", (cw, ch), tone)
                        cell.alpha_composite(_cell(sheet, look, a, d, i))
                        out.alpha_composite(cell.resize((cw * z, ch * z), Image.NEAREST), (lw + c * cw * z, th + r * ch * z))
                        c += 1
                dr.text((6, th + r * ch * z + ch * z // 2 - 8), ("%s %s" % (label, d.upper())).strip(), font=head,
                        fill=(232, 225, 207, 255))
            out.save(REVIEW / ("%s%s_x3.png" % (sp, "_" + label if label else "")))
    anims(sheets, man)
    print("review images in", REVIEW.relative_to(ROOT))


def anims(sheets: dict, man: dict) -> None:
    """Each species facing SE at x4 on a meadow tone, playing its whole catalogue at the game's rates (the loops twice),
    as a GIF (`<species>_se.gif`, the elite's beside it where it has one, their feet on one line); and the tells side by
    side, every species' wind-up held on its last frame, their feet on one line (`tells_x4.png`)."""
    z = 4
    tells = []
    for sp, block in man["species"].items():
        looks = [block] + [block[v] for v in ("elite", "awakened") if v in block]
        base = max(lk["foot"][1] for lk in looks)
        h = base + max(lk["cell"][1] - lk["foot"][1] for lk in looks)
        w = sum(lk["cell"][0] for lk in looks)
        frames, durations = [], []
        for a in creatures.REGISTRY[sp].actions():
            act = looks[0]["actions"][a]
            n = len(act["frames"]["se"])
            for _ in range(2 if act["loop"] else 1):
                for i in range(n):
                    im = Image.new("RGBA", (w, h), (92, 140, 70, 255))
                    x = 0
                    for lk in looks:
                        im.alpha_composite(_cell(_sheet(sheets, lk), lk, a, "se", i), (x, base - lk["foot"][1]))
                        x += lk["cell"][0]
                    frames.append(im.resize((w * z, h * z), Image.NEAREST).convert("RGB"))
                    hold = 400 if not act["loop"] and i == n - 1 else 0
                    durations.append(int(round(1000.0 / act["fps"] / 10.0)) * 10 + hold)
        frames[0].save(REVIEW / ("%s_se.gif" % sp), save_all=True, append_images=frames[1:], duration=durations, loop=0,
                       optimize=False, disposal=1)
        tells.append((_cell(_sheet(sheets, block), block, "windup", "se", -1), block["foot"][1]))
    w = sum(t.width for t, _ in tells) + 4 * (len(tells) - 1)
    base = max(fy for _, fy in tells)
    h = base + max(t.height - fy for t, fy in tells)
    strip = Image.new("RGBA", (w, h), (92, 140, 70, 255))
    x = 0
    for t, fy in tells:
        strip.alpha_composite(t, (x, base - fy))       # every foot on one line
        x += t.width + 4
    strip.resize((w * z, h * z), Image.NEAREST).save(REVIEW / "tells_x4.png")


def main(argv: list[str]) -> int:
    jobs = 1
    only = None
    for i, a in enumerate(argv):
        if a == "--jobs":
            jobs = int(argv[i + 1])
        if a == "--only":
            only = set(argv[i + 1].split(","))
    outputs, sheets = build_all(jobs, only)
    man = json.loads(outputs[MANIFEST])
    if only is not None:
        review(sheets, man)
        return 0
    if "--check" in argv:
        again, _ = build_all(jobs)
        bad = [p for p in outputs if outputs[p] != again.get(p)]
        for p in bad:
            print("NOT deterministic:", p)
        if bad:
            return 1
    # Sheets of species no longer drawn go.
    keep = {ROOT / p for p in outputs}
    for old in sorted((ROOT / FOES_DIR).glob("*.png")):
        if old not in keep:
            old.unlink()
            imp = old.with_suffix(".png.import")
            if imp.exists():
                imp.unlink()
    for path, data in outputs.items():
        out = ROOT / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        size = ""
        if path.endswith(".png"):
            im = sheets[path]
            size = "%dx%d" % im.size
        print("%-40s %9s %8d bytes  sha1 %s" % (path, size, len(data), hashlib.sha1(data).hexdigest()[:12]))
    if "--review" in argv:
        review(sheets, man)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
