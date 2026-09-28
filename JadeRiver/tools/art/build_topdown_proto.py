"""Top-down redesign (docs/redesign_top_down_plan.md): the prototype's art entry point from Phases 1-2.

The Phases 1-2 placeholders are gone: the body is the real character (Phase 3, tools/art/topdown/build_character.py)
and the foes are drawn by tools/art/topdown/creatures.py. The tiles, props, foes, manifest and TileSet are built by
tools/art/topdown/build_tiles.py (docs/redesign/art_bible.md); running this script runs that build.

Usage: python3 tools/art/build_topdown_proto.py [--review] [--check]   (same as python3 tools/art/topdown/build_tiles.py)
"""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent / "topdown"))
    import build_tiles
    sys.exit(build_tiles.main(sys.argv[1:]))


if __name__ == "__main__":
    main()
