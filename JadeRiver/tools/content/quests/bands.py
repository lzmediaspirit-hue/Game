"""E5, the quest engine's band table (docs/architecture/quest_engine.md, "The band table"): what a side quest pays at
its tier.

Decision 45 made every quest pay a fixed amount of cultivation, its kind's share of the need of the stage at its own
tier (story.py quest_tiers; curves.json quest_cultivation), where it used to pay a share of the player's own stage. A band
is a run of Levels with one need, so a band's cultivation is one number: the side quest's share of that need, rounded as
a reward (realms.cultivation, phase 1's rule). A band also names the money a side quest pays there: silver taels in Act
I, spirit stones in Act II, sage crystals in Act III. A quest pays the band of its tier: `experience()` is what quest_tiers
writes as its `cultivation`, `pay()` the currency reward the engine writes.

BANDS: (band, first Level, currency, amount); a band runs to the Level before the next one's first.
  - The cultivation is not written here: it follows the curves (QUEST_CULTIVATION) and realms.json, so it cannot drift
    from what quest_tiers pays. The early Bone Forging stages are a band each, as their needs climb (600 to 1,600).
  - The amounts were set from the hand side quests of each band, their middle value, and rise between them where no
    hand quest stood (docs/architecture/quest_engine.md lists every quest that pays otherwise). balance_sim shows what
    a band's side quests pay an hour of their ten minutes' detour against what an hour of play earns at their tier.
"""
import os
import sys

_DATA_TOOLS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data"))
if _DATA_TOOLS not in sys.path:
    sys.path.append(_DATA_TOOLS)

TAELS, STONES, CRYSTALS = "silver_tael", "spirit_stone", "sage_crystal"

BANDS = [
    ("mortal", 0, TAELS, 30),
    ("bone_forging_1", 1, TAELS, 30),
    ("bone_forging_2", 2, TAELS, 40),
    ("bone_forging_3", 3, TAELS, 40),
    ("bone_forging_4", 4, TAELS, 60),
    ("bone_forging", 5, TAELS, 90),
    ("qi_kindling", 10, TAELS, 120),
    ("qi_unfurling", 19, TAELS, 200),
    ("heart_tempering", 28, TAELS, 200),
    ("cloud_stride", 37, TAELS, 250),
    ("spirit_awakening", 46, TAELS, 300),
    ("heaven_glimpse", 55, TAELS, 400),
    ("sage", 64, STONES, 90),
    ("sage_sovereign", 73, STONES, 120),
    ("will_manifest", 82, CRYSTALS, 25),
    ("sphere_lord", 91, CRYSTALS, 30),
    ("law_touching", 100, CRYSTALS, 40),
    ("monarch", 109, CRYSTALS, 50),
    ("heavens_gate", 118, CRYSTALS, 60),
    ("inner_heaven", 121, CRYSTALS, 80),
]

LAST = 165   # the last Level a band holds (World Genesis, 166, has no stage to fill)

# The quest kind (curves.json quest_cultivation) a side quest of a band is paid as: Act II and III pay the smaller share
# their longer stages were tuned for (story.py build: "act2_side").
ACT2_FROM = 64


def qp(band_row):
    return "act2_side" if band_row[1] >= ACT2_FROM else "side"


def band_at(level):
    """The band holding Level `level`."""
    best = BANDS[0]
    for b in BANDS:
        if b[1] <= level:
            best = b
    return best


def levels(band_row):
    """The band's Levels, first to last."""
    i = BANDS.index(band_row)
    last = BANDS[i + 1][1] - 1 if i + 1 < len(BANDS) else LAST
    return range(band_row[1], last + 1)


def experience(band_row, kind=None):
    """The fixed cultivation a side quest of this band pays (phase 1: the kind's share of the band's need)."""
    import realms as R
    from stats import QUEST_CULTIVATION
    share = float(QUEST_CULTIVATION.get(kind or qp(band_row), 0.0))
    return R.cultivation(share, band_row[1]) if share > 0.0 else 0


def pay(band_row):
    """The band's pay: a grant_currency reward."""
    return {"kind": "grant_currency", "currency": band_row[2], "amount": band_row[3]}
