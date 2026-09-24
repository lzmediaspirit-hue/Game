#!/usr/bin/env python3
"""Build Jade River creature sprite sheets.

    python3 tools/art/build_creatures.py                 # every module in creatures/
    python3 tools/art/build_creatures.py mudshell_crab   # only the named creatures
    python3 tools/art/build_creatures.py --no-write ...  # render + review only
    python3 tools/art/build_creatures.py rat --frames idle:0,windup:2 --no-write
                                                         # + close-up of chosen frames

Writes ``art/creatures/<id>.png``, merges ``data/creature_art.json`` and writes review
sheets (``<id>.png`` per creature at 2x zoom, ``all_creatures.png`` at in-game 1x,
``creatures_lineup.png`` scale check next to the player) to the review folder (``--review DIR``).
Exits with status 1 when a contract check fails.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # keep tools/art free of __pycache__ folders

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "creatures"))

import pixel as px  # noqa: E402

DEFAULT_REVIEW = Path("/tmp/claude-0/-home-user-Game/13461237-7857-505a-bd3b-55d18a20fe2c/scratchpad/art_review")
# Optional player composite (2x-zoomed screen image) used as the scale reference.
PLAYER_REF = DEFAULT_REVIEW.parent / "comp_full.png"


def _player_reference():
    """First figure of the player composite, reduced to art resolution (or None)."""
    if not PLAYER_REF.exists():
        return None
    im = np.array(Image.open(PLAYER_REF).convert("RGBA"))
    bg = im[0, 0].copy()
    im[(im == bg).all(-1)] = 0
    art = im[::4, ::4]  # composite is 2x screen = 4x art
    a = art[..., 3] > 0
    cols = np.nonzero(a.any(0))[0]
    if not len(cols):
        return None
    # first connected run of columns = first figure
    end = cols[0]
    while end + 1 < art.shape[1] and a[:, end + 1].any():
        end += 1
    rows = np.nonzero(a[:, cols[0]:end + 1].any(1))[0]
    fig = art[: rows.max() + 1, cols[0]: end + 1]
    return fig


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*", help="creature ids (default: all modules)")
    ap.add_argument("--no-write", action="store_true", help="do not write sheets / manifest")
    ap.add_argument("--review", type=Path, default=DEFAULT_REVIEW, help="review output folder")
    ap.add_argument("--zoom", type=int, default=4, help="review zoom (screen px per art px)")
    ap.add_argument("--frames", default="", help="close-up frames, e.g. idle:0,attack:2 -> <id>_frames.png")
    ap.add_argument("--hollow", action="store_true", help="render the --frames close-up as a Hollow variant")
    args = ap.parse_args(argv)

    ids = args.ids or px.list_creatures()
    failed = False
    cache = {}
    for cid in ids:
        mod = px.load_creature(cid)
        sheet, warns, frames = px.build_creature(mod, write=not args.no_write, manifest=not args.no_write)
        cache[cid] = frames
        cell = mod.SPEC["cell"]
        ok = sheet.size == (cell * 6, cell * 6) and sheet.mode == "RGBA"
        print(f"{cid}: sheet {sheet.size[0]}x{sheet.size[1]} {sheet.mode} {'OK' if ok else 'BAD SIZE'}")
        for w in warns:
            print(f"  ! {w}")
        failed |= (not ok) or bool(warns)
        px.contact_sheet([cid], args.review / f"{cid}.png", zoom=args.zoom, frames_cache=cache)
        if args.frames:
            picks = [tuple(s.split(":")) for s in args.frames.split(",") if s]
            px.frame_strip(cid, picks, args.review / f"{cid}_frames.png", hollow=args.hollow)
    px.contact_sheet(ids, args.review / "all_creatures.png", zoom=2, frames_cache=cache)
    px.lineup(ids, args.review / "creatures_lineup.png", zoom=4, reference=_player_reference())
    print(f"review sheets -> {args.review}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
