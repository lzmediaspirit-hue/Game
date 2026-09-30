"""The tools the villagers work with (decision 44): the held-tool rig, cast by figure/kinds/tool.py from the same poses
as the body, so each tool is in the hands on every frame of its action and facing. A tool is not a wardrobe look (it is
in no parts.json category): TopdownWork gives a worker the tools of their loop (data/topdown/life.json `tools`), and
the figure wears them in its `tool` slot.

Each tool draws only in the actions that hold it (ACTIONS; figure/work.py poses them, actions.CARRY carries four of
them in the idle and walk poses); every other action has an explicit hidden entry for it. The colours are the §14
world's (tools/art/topdown/palette.py: its wood, bamboo, reed, stone and clay ramps, five steps each), shaded and
outlined by the figure's own rules (render.py), in nearest neighbour.
"""
from __future__ import annotations

import sys
from pathlib import Path

from .. import palettes as P
from ..items import Item
from ..kinds import tool as K
from ..render import BLADE_EDGE, Look

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))    # tools/art/topdown
import palette as W  # noqa: E402  the §14 world palette

KIND = "tool"
CAT = "tool"

# The actions each tool is drawn in (the rest hide it): its work actions, and the idle and walk poses for the four a
# worker carries about (actions.CARRY).
ACTIONS = {
    "broom": ["work_sweep", "idle", "walk"],
    "pole": ["work_carry"],
    "washing": ["work_carry", "work_hang"],
    "rod": ["work_rod", "work_cast", "idle", "walk"],
    "ladle": ["work_stir"],
    "pestle": ["work_grind"],
    "axe": ["work_chop", "idle", "walk"],
    "hammer": ["work_hammer"],
    "herbs": ["work_pick", "idle", "walk"],
    "net": ["work_mend"],
}
LABELS = {"broom": "Broom", "pole": "Shoulder pole and baskets", "washing": "Washing", "rod": "Fishing rod",
          "ladle": "Ladle and pot", "pestle": "Pestle and mortar", "axe": "Axe", "hammer": "Hammer and tongs",
          "herbs": "Herb basket", "net": "Fishing net"}


def five(r7: list, lo: int = 1) -> list:
    """Five steps (deep, shadow, base, light, highlight) of a seven-step §14 ramp, from step `lo`."""
    return [r7[lo], r7[lo + 1], r7[lo + 2], r7[lo + 3], r7[min(lo + 4, len(r7) - 1)]]


BAMBOO = P.ramp("4a3a1c", "74602e", "a08848", "c8ae68", "e6d196")                 # dried bamboo: poles, rods, handles
GRIP = P.ramp("2a1c14", "3f2a1c", "5a3e28", "7a5a38", "9a774b")                 # a rod's wrapped butt
REED = [W.REED[0], W.REED[1], W.REED[2], W.REED[3], W.REED[4]]                   # the broom's dried twigs
REED_DARK = [W.REED[0], W.REED[0], W.REED[1], W.REED[2], W.REED[3]]
HAFT = five(W.WOOD2, 1)                                                          # ash hafts, the pestle
CORD = P.ramp("2e2418", "4a3a26", "6e5a3c", "927c56", "b09a72")                  # hemp cord and rope
WICKER = five(W.WOOD, 2)
WICKER_DARK = five(W.WOOD, 1)
GRAIN = P.ramp("6e5a3a", "9a8256", "c2aa76", "dcc796", "efe0b6")                 # husked grain in the baskets
IRON = P.ramp("141620", "262a38", "3e4456", "5c6478", "8a93a6")                  # forged iron, dark and cool
EDGE = P.ramp("3e4456", "5c6478", "8a93a6", "b8c0cc", "e2e8ee")                  # a ground edge, a hammer's face
CLAY = five(W.DIRT2, 1)                                                          # the pot
CLAY_RIM = five(W.DIRT2, 2)
BROTH = P.ramp("3a2418", "5a3a22", "7a5430", "9a7040", "b08a58")
STONE = five(W.PAVE2, 2)                                                         # the mortar
STONE_RIM = five(W.PAVE2, 2)[1:] + [W.PAVE2[6]]
HOLLOW = P.ramp("1e1a22", "2a2330", "3a3240", "4a3f44", "5a4f54")
LINEN = five(W.PLASTER2, 1)                                                      # the washing
LINEN_FOLD = five(W.PLASTER2, 0)
CLOTH_BLUE = five(W.STONE2, 1)
HERB = five(W.LEAF, 1)
HERB_LIGHT = five(W.LEAF, 2)
TWINE = P.ramp("5a4c32", "7e6c48", "a8946a", "c8b48a", "e2d2ac")                # the net's pale hemp twine
MESH = P.ramp("2a2a26", "3a3830", "524c3e", "6a624e", "827860")                  # the shade seen through its holes
CORK = P.ramp("5a2a14", "8a4020", "b85a2e", "d8804a", "eeaa74")
SHUTTLE = BAMBOO
FLOAT = P.ramp("3a1026", "661a2e", "bd3b3c", "d95b49", "ee8b6b")                # the float's red lacquer (§14 RED2)
LINE = P.ramp("8a9ea0", "a9bcbc", "c9d6d2", "e3ece6", "f2f7f2") + [P.c("000000", 0)]   # the fishing line: pale, flat
HOT = P.ramp("8a2a14", "c24a1c", "f07a2a", "ffb04a", "ffe08a")                   # the hot bar (glow)

PALETTE = {"bamboo": BAMBOO, "grip": GRIP, "twig": REED, "twig_dark": REED_DARK, "haft": HAFT, "cord": CORD,
           "wicker": WICKER, "wicker_dark": WICKER_DARK, "rim": WICKER, "grain": GRAIN, "iron": IRON, "edge": EDGE,
           "tongs": IRON, "clay": CLAY, "clay_rim": CLAY_RIM, "broth": BROTH, "stone": STONE, "stone_rim": STONE_RIM,
           "hollow": HOLLOW, "linen": LINEN, "linen_fold": LINEN_FOLD,
           "cloth_blue": CLOTH_BLUE, "herb": HERB, "herb_light": HERB_LIGHT, "twine": TWINE, "mesh": MESH,
           "cork": CORK, "shuttle": SHUTTLE, "float": FLOAT, "line": LINE, "hot": HOT}

# How each material resolves and takes the light (render.MATS; these override it for the tools): a handle, a rod and
# a cord are lines (a pixel wide and unbroken), the twigs and the wicker are cloth-like (lit, not glossy), iron keeps a
# cool rim, the fishing line and the hot bar are light (flat, no ink).
MATS = {
    "bamboo": {"hi": True, "line": True, "weight": 1.4},
    "grip": {"line": True, "weight": 1.5},
    "haft": {"hi": True, "line": True, "weight": 1.4},
    "cord": {"line": True, "weight": 1.2},
    "twig": {"hi": True, "weight": 1.1},
    "twig_dark": {"weight": 1.1},
    "wicker": {"hi": True, "weight": 1.2},
    "wicker_dark": {"weight": 1.2},
    "rim": {"hi": True, "weight": 1.4},
    "grain": {"hi": True},
    "iron": {"hi": True, "glossy": True, "rim": 0.08, "weight": 1.3},
    "edge": dict(BLADE_EDGE["edge"], rim=0.08),
    "tongs": {"line": True, "weight": 1.3, "rim": 0.08},
    "clay": {"hi": True},
    "clay_rim": {"hi": True, "weight": 1.3},
    "broth": {},
    "stone": {"hi": True},
    "stone_rim": {"hi": True, "weight": 1.3},
    "hollow": {"weight": 1.2},
    "linen": {"hi": True},
    "linen_fold": {},
    "cloth_blue": {"hi": True, "weight": 1.3},
    "herb": {"hi": True},
    "herb_light": {"hi": True, "weight": 1.2},
    "twine": {"hi": True},
    "mesh": {},
    "cork": {"hi": True, "weight": 1.6},
    "shuttle": {"hi": True, "line": True, "weight": 1.4},
    "float": {"hi": True, "glossy": True, "weight": 2.0},
}


def items(L: dict) -> list:
    look = Look(glow=("line", "hot"), flat={"line": 3, "hot": 3}, line_tone={"line": 5, "hot": 2},
                ink=("bamboo", "grip", "haft", "iron", "edge", "twig", "wicker", "clay", "stone", "float"),
                mats=MATS)
    out = []
    for name in ACTIONS:
        it = Item(CAT, name, LABELS[name], (lambda sk, n=name: K.solids(sk, n)), look, {"none": PALETTE},
                  list(PALETTE))
        it.actions = ACTIONS[name]
        out.append(it)
    return out
