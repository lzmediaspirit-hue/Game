"""The top-down sheet builders' shared parts (decision 45, audit DUP-12): packing sprites into a sheet's rows, a PNG's
bytes, and the command line every builder has (build, --check, write, --review).

  pack(sizes, width, gap, row_gap)   shelf packing: each (w, h) left to right with `gap` px between, a new row (`row_gap`
                                     px lower) when the next one no longer fits; returns the places and the sheet's height
  png_bytes(img)                     a PIL image as PNG bytes, no metadata, unoptimised (byte-identical on every build)
  run(argv, build, script, review)   the command line: build every output in memory; --check builds twice and fails
                                     unless both builds agree and the files on disk are current; otherwise writes them
                                     (their size and sha1 printed) and, with --review, renders the review images
"""
from __future__ import annotations

import hashlib
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def pack(sizes: list, width: int, gap: int = 1, row_gap: int = 0) -> tuple[list, int]:
    places, x, y, row_h = [], 0, 0, 0
    for w, h in sizes:
        if x + w > width:
            x, y, row_h = 0, y + row_h + row_gap, 0
        places.append((x, y))
        x, row_h = x + w + gap, max(row_h, h)
    return places, y + row_h


def png_bytes(img) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False)
    return buf.getvalue()


def run(argv: list, build, script: str, review=None, width: int = 28) -> int:
    outputs = build()
    if "--check" in argv:
        again = build()
        bad = [p for p in outputs if outputs[p] != again[p]]
        stale = [p for p in outputs if not (ROOT / p).exists() or (ROOT / p).read_bytes() != outputs[p]]
        for p in bad:
            print("NOT deterministic:", p)
        for p in stale:
            print("stale (run %s):" % script, p)
        return 1 if bad or stale else 0
    for path, data in outputs.items():
        out = ROOT / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        print("%-*s %8d bytes  sha1 %s" % (width, path, len(data), hashlib.sha1(data).hexdigest()[:12]))
    if "--review" in argv and review is not None:
        review(outputs)
    return 0
