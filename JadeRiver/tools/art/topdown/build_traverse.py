"""T1 (docs/architecture/topdown_mechanics.md): build the traversal sheet the room view draws the side view's rafts,
climbable faces, updraft spray and the glide's leaf from (tools/art/topdown/traverse.py), and its manifest.

Writes (1 art px = 1 px of the 640x360 world viewport, nearest neighbour, no metadata, byte-identical on every build):
  art/topdown/traverse.png         every sprite, packed in rows (an animated one's frames side by side)
  data/topdown/traverse_art.json   the manifest TopdownTraverseView reads: each sprite's rect, its frames and frame width
With --review it renders docs/architecture/topdown_mechanics/traverse_x4.png: every sprite at x4, a raft on the water
and each climbable on a cliff face three levels high, over the grid's own tiles' colours.

Usage: python3 tools/art/topdown/build_traverse.py [--review] [--check]
  --check  builds twice in memory and fails unless both builds are byte-identical and the files on disk are current
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

from PIL import Image  # noqa: E402

import sheet as SH  # noqa: E402
import traverse  # noqa: E402
from canvas import Img  # noqa: E402
from palette import ROCK2, WATER2  # noqa: E402

SHEET = "art/topdown/traverse.png"
MANIFEST = "data/topdown/traverse_art.json"
SHEET_W = 128


def build_all() -> dict:
    items = traverse.sprites()
    at, height = SH.pack([(img.w, img.h) for img, _, _ in items.values()], SHEET_W)
    sheet = Img(SHEET_W, height)
    table = {}
    for (name, (img, frames, fw)), (px, py) in zip(items.items(), at):
        sheet.paste(img, px, py)
        table[name] = {"rect": [px, py, fw, img.h], "frames": frames}
    manifest = {"schema_version": 1, "sheet": "res://" + SHEET, "sprites": table}
    return {SHEET: SH.png_bytes(sheet.img), MANIFEST: (json.dumps(manifest, indent=1, sort_keys=True) + "\n").encode()}


def review(outputs: dict) -> None:
    out_dir = ROOT / "docs/architecture/topdown_mechanics"
    out_dir.mkdir(parents=True, exist_ok=True)
    man = json.loads(outputs[MANIFEST])
    sheet = Image.open(io.BytesIO(outputs[SHEET])).convert("RGBA")

    def cut(name: str, f: int = 0) -> Image.Image:
        r = man["sprites"][name]["rect"]
        return sheet.crop((r[0] + f * r[2], r[1], r[0] + (f + 1) * r[2], r[1] + r[3]))

    img = Image.new("RGBA", (300, 120), (20, 26, 30, 255))
    # A raft on the water (both frames), and the spray over it.
    for x in range(0, 96):
        for y in range(16, 112):
            img.putpixel((x, y), WATER2[3] if (x // 4 + y // 4) % 5 else WATER2[4])
    img.alpha_composite(cut("raft_2x2", 0), (8, 24))
    img.alpha_composite(cut("raft_2x2", 1), (50, 24))
    for f in range(4):
        img.alpha_composite(cut("spray", f), (8 + f * 20, 64))
    # Each climbable on a face three levels high (48 px) under a lip, over the floor.
    for i, kind in enumerate(("vine", "rope", "ladder", "chain")):
        x0 = 110 + i * 40
        for y in range(8, 64):
            for x in range(x0 - 8, x0 + 24):
                img.putpixel((x, y), ROCK2[4] if y < 16 else ROCK2[2] if (x + y) % 7 else ROCK2[1])
        img.alpha_composite(cut(kind + "_top"), (x0, 16))
        img.alpha_composite(cut(kind + "_mid"), (x0, 32))
        img.alpha_composite(cut(kind + "_foot"), (x0, 48))
    for f in range(2):
        img.alpha_composite(cut("glide", f), (110 + f * 40, 80))
        img.alpha_composite(cut("cloud", f), (200 + f * 40, 84))
    # T2: the rows T1 left, over the floors they stand on.
    t2 = Image.new("RGBA", (300, 130), (20, 26, 30, 255))
    for x in range(0, 300):
        for y in range(0, 130):
            t2.putpixel((x, y), WATER2[3] if y < 30 and x < 130 else (88, 74, 60, 255) if (x // 16 + y // 16) % 2 else (96, 82, 66, 255))
    t2.alpha_composite(cut("driftwood", 0), (4, 6))
    t2.alpha_composite(cut("plank", 0), (60, 6))
    t2.alpha_composite(cut("plank", 1), (96, 6))
    t2.alpha_composite(cut("seal_gate"), (140, 2))
    t2.alpha_composite(cut("drum"), (180, 2))
    t2.alpha_composite(cut("lily"), (220, 4))
    t2.alpha_composite(cut("bamboo"), (260, 2))
    for f in range(2):
        t2.alpha_composite(cut("lantern", f), (4 + f * 40, 40))
    for i, name in enumerate(("pit", "gap", "hole_water")):
        t2.alpha_composite(cut(name), (90 + i * 20, 44))
    for f in range(2):
        t2.alpha_composite(cut("ice", f), (90 + f * 20, 70))
        t2.alpha_composite(cut("ripple", f), (150 + f * 30, 70))
    for f in range(3):
        t2.alpha_composite(cut("wind", f), (220 + f * 16, 72))
    for i, name in enumerate(("boards",)):
        t2.alpha_composite(cut(name, 0), (90, 96))
        t2.alpha_composite(cut(name, 1), (110, 96))
    both = Image.new("RGBA", (300, 250), (20, 26, 30, 255))
    both.alpha_composite(img, (0, 0))
    both.alpha_composite(t2, (0, 120))
    both.resize((both.width * 4, both.height * 4), Image.NEAREST).save(out_dir / "traverse_x4.png")
    print("review image in", (out_dir / "traverse_x4.png").relative_to(ROOT))


def main(argv: list) -> int:
    return SH.run(argv, build_all, "tools/art/topdown/build_traverse.py", review, width=32)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
