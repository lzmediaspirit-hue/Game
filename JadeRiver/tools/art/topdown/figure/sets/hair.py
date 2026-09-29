"""The creator's six hair styles (parts.json `hair`), after the side-view sheets, in the six hair colours
(parts.json `_colors.hair`), cast by figure/kinds/hair.py:

  short_knot  Sage knot      a round bun on the crown's back, jade ribbon, gold pin
  topknot     Daoist knot    a tall knot on the crown, jade ribbon and gold pin, one long lock down the back
  ponytail    Jade tail      a low tail tied at the nape with a jade band, to the shoulder blades
  high_pony   Sky ponytail   a high tail tied at the crown's back with a jade ribbon, sweeping down the back
  long_tied   Long silk tie  a fringe, and one long tail bound with gold and jade rings to the waist
  flowing     Flowing tail   a fringe, a tall loop on the crown and a long fall of hair to the waist
"""
from __future__ import annotations

from .. import palettes as P
from ..items import Item
from ..kinds import hair as K
from ..render import Look

KIND = "hair"

STYLES = {
    "short_knot": {"pieces": [
        ("knot", {"id": "bun", "at": (-2.4, 0.0, 6.9), "radii": (2.8, 2.8, 2.5), "strands": 8}),
        ("ribbon", {"from": "bun", "at": (0.2, 0, -1.6), "radii": (2.85, 2.85, 0.8)}),
        ("pin", {"from": "bun", "a": (2.1, -3.6, 0.7), "b": (2.1, 3.4, 0.7), "r": (0.5, 0.45)})]},
    "topknot": {"pieces": [
        ("knot", {"id": "knot", "at": (-1.2, 0.0, 8.3), "radii": (2.5, 2.4, 3.2), "strands": 7}),
        ("ribbon", {"from": "knot", "at": (0.1, 0, -2.2), "radii": (2.6, 2.5, 0.8)}),
        ("pin", {"from": "knot", "a": (2.0, -3.4, 0.6), "b": (2.0, 3.2, 0.6), "r": (0.5, 0.45)}),
        ("tail", {"from": "knot", "at": (-1.6, 0, 0.4), "dir": (0.9, -0.4), "length": 13.0, "r": (1.05, 0.7), "segs": 6,
                  "stiff": 0.5})]},
    "ponytail": {"pieces": [
        ("lump", {"id": "tie", "at": (-5.8, 0.0, -2.2), "radii": (1.5, 1.7, 1.5)}),
        ("ribbon", {"from": "tie", "at": (-0.6, 0, 0), "radii": (0.9, 1.75, 1.25)}),
        ("tail", {"from": "tie", "at": (-0.9, 0, -0.4), "dir": (0.5, -1.0), "length": 10.5, "r": (1.45, 0.8), "segs": 5,
                  "stiff": 0.6})]},
    "high_pony": {"pieces": [
        ("lump", {"id": "tie", "at": (-4.9, 0.0, 4.6), "radii": (1.6, 1.8, 1.7)}),
        ("ribbon", {"from": "tie", "at": (-0.5, 0, 0.1), "radii": (1.0, 1.9, 1.4)}),
        ("tail", {"from": "tie", "at": (-1.2, 0, 0.3), "dir": (1.0, 0.35), "length": 14.0, "r": (2.0, 0.9), "segs": 7,
                  "stiff": 0.72, "rings": [(0.08, "ribbon")]})]},
    "long_tied": {"fringe": True, "pieces": [
        ("lump", {"id": "tie", "at": (-5.7, 0.0, -1.2), "radii": (1.6, 2.0, 1.8)}),
        ("tail", {"from": "tie", "at": (-0.8, 0, -0.5), "dir": (0.35, -1.0), "length": 17.0, "r": (1.55, 1.0), "segs": 8,
                  "stiff": 0.6, "rings": [(0.02, "ribbon"), (0.3, "pin"), (0.55, "ribbon"), (0.8, "pin")]})]},
    "flowing": {"fringe": True, "pieces": [
        ("knot", {"id": "loop", "at": (-1.0, 0.0, 8.4), "radii": (1.5, 1.35, 2.9), "strands": 6}),
        ("ribbon", {"from": "loop", "at": (0.1, 0, -2.2), "radii": (1.6, 1.5, 0.65)}),
        ("pin", {"from": "loop", "a": (0.4, -2.6, -0.8), "b": (0.4, 2.5, -0.8), "r": (0.45, 0.4)}),
        # the fall: a wide flat sheet of hair from the back of the head to the waist
        ("tail", {"at": (-4.4, 0, 1.0), "dir": (0.3, -1.0), "length": 18.0, "r": (3.4, 2.3), "segs": 8, "stiff": 0.55,
                  "k": 0.42, "part": "fall"})]},
}

# How each style reads at 38 px (decision 42; kinds/hair.py): the cap's broad locks, and the loose locks that break its
# round silhouette and frame the face, in the head's frame (forward, right, up): the temple strands (kinds/hair.TEMPLE,
# or a longer one where a fringe falls to the jaw), and forelocks over the brow.
TUNE = {
    "topknot": {"locks": 7, "loose": [K.TEMPLE, ((4.9, -1.9, 4.6), (5.9, -2.9, 1.5), 0.95, 0.25),
                                      ((5.0, 1.2, 4.6), (6.0, 2.0, 1.9), 0.85, 0.25)]},
    "short_knot": {"locks": 8, "loose": [K.TEMPLE, ((4.9, -2.4, 4.3), (5.8, -2.9, 2.0), 0.9, 0.2),
                                         ((5.2, -0.2, 4.6), (6.0, 0.3, 2.3), 0.9, 0.2),
                                         ((5.0, 2.2, 4.4), (5.8, 2.9, 2.2), 0.85, 0.2)]},
    "ponytail": {"locks": 7, "loose": [K.TEMPLE, ((5.0, -1.4, 4.5), (5.8, -2.3, 2.2), 0.85, 0.2),
                                       ((5.1, 1.6, 4.4), (5.8, 2.4, 2.3), 0.8, 0.2)]},
    "high_pony": {"locks": 7, "loose": [K.TEMPLE, ((5.0, -1.4, 4.5), (5.8, -2.3, 2.2), 0.85, 0.2),
                                        ((5.1, 1.6, 4.4), (5.8, 2.4, 2.3), 0.8, 0.2)]},
    "long_tied": {"locks": 9, "loose": [((1.6, -5.8, 2.2), (2.2, -6.4, -5.0), 1.15, 0.35)]},
    "flowing": {"locks": 9, "loose": [((1.6, -5.8, 2.2), (2.2, -6.4, -5.4), 1.2, 0.35)]},
}
for _st, _t in TUNE.items():
    STYLES[_st].update(_t)


def items(L: dict) -> list:
    pal = {str(i): {"hair": P.HAIR[i], "ribbon": P.RIBBON, "pin": P.GOLD} for i in range(len(P.HAIR))}
    return [Item("hair", st, L["hair"][st], lambda sk, spec=spec: K.solids(sk, spec),
                 Look(highlight=("hair", "pin", "ribbon"), line_tone={"hair": 0}), pal, ["hair", "ribbon", "pin"])
            for st, spec in STYLES.items()]
