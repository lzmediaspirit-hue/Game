"""The layer sets of the top-down character (decision 32; decision 37 asks for the full set). Each module here is one
set, built on its own and written to its own files, so sets can be drawn in parallel without touching each other:

  data/topdown/character/<KIND>.json               its items: sections, rects, sheets, and the game items that wear
                                                   each look (`artifacts`)
  art/topdown/character/<cat>_<item>[__<variant>].png  its sheets

A set module declares:
  KIND            the set's name (its file names): body, hair, shirt, pants, shoes, hat, cape, weapon_<family>
  items(labels)   its items (figure.items.Item), each cast by a generator in figure/kinds/ from the set's own specs

Build one set with `python3 tools/art/topdown/build_character.py --only <KIND>`; docs/redesign/phase3/character/HOWTO.md
says how to add one. A module whose name starts with "_" is not a set.
"""
from __future__ import annotations

import importlib
import pkgutil

# The full set (decision 37): every look the game's data can put on a character has its layers, so this is on and
# data_validation's coverage check fails for any look or action without one.
FULL_SET = True

# What is still to draw while FULL_SET is off, by batch (HOWTO.md): the coverage check fails for any missing look or
# stand-in action that is not listed here. The bow batch, the last, emptied it: a new look must now be drawn with it.
PENDING: dict = {}


def discover() -> dict:
    """{KIND: module} for every set module here, in name order."""
    out = {}
    for info in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
        if info.name.startswith("_"):
            continue
        mod = importlib.import_module(__name__ + "." + info.name)
        out[mod.KIND] = mod
    return out


def pending() -> list:
    return sorted(x for batch in PENDING.values() for x in batch)
