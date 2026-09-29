#!/usr/bin/env python3
"""How much the audio weighs in the APK: the imported files Godot packs for art/audio (QOA samples for the WAVs,
Ogg Vorbis streams for the loops), from each .import's `path`, after a `godot --headless --import`.

    python3 tools/audio/apk_size.py            # totals by kind and format
    python3 tools/audio/apk_size.py -v         # + the ten largest
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sizes():
    out = []
    for imp in sorted((ROOT / "art" / "audio").rglob("*.import")):
        m = re.search(r'path="res://(.*?)"', imp.read_text(encoding="utf-8"))
        if not m:
            continue
        dest = ROOT / m.group(1)
        src = Path(str(imp)[:-len(".import")])
        out.append((src.relative_to(ROOT).as_posix(), dest.stat().st_size if dest.exists() else -1, src.stat().st_size if src.exists() else 0))
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    rows = sizes()
    missing = [r[0] for r in rows if r[1] < 0]
    groups = {}
    for name, packed, src in rows:
        kind = name.split("/")[2] + (" loops" if name.endswith(".ogg") else "")
        g = groups.setdefault(kind, [0, 0, 0])
        g[0] += 1
        g[1] += max(packed, 0)
        g[2] += src
    for kind, (n, packed, src) in sorted(groups.items()):
        print(f"{kind:12} {n:4} files  {packed / 1e6:6.2f} MB in the APK  ({src / 1e6:6.2f} MB of sources)")
    total = sum(max(r[1], 0) for r in rows)
    print(f"{'total':12} {len(rows):4} files  {total / 1e6:6.2f} MB in the APK  ({sum(r[2] for r in rows) / 1e6:6.2f} MB of sources)")
    if missing:
        print(f"not imported yet: {len(missing)} (run godot --headless --import)")
    if "-v" in argv:
        for name, packed, _ in sorted(rows, key=lambda r: -r[1])[:10]:
            print(f"  {packed / 1e3:8.1f} KB  {name}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
