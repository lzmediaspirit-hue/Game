"""The item engine's curves: what a tier is worth (docs/architecture/item_engine.md, "Curves").

A family names its tiers by grade; every number a tier carries comes from here unless the spec pins it:
- `MID_ILV`: the Level an item of a grade is pitched at, the middle of the grade's band. An item's `ilv` is it, and
  through it the game's price (LootRules.value_of: 1 + 0.4 x ilv^1.5, by type, x4 to buy).
- `cultivation(share, grade)`: decision 45's fixed cultivation: `share` of the need of the stage at MID_ILV, rounded as
  a reward (realms.cultivation, which reads the realm ladder, curves.json's minutes per Level).
- `SPEED`: what a cultivation-speed item of a grade adds to `accumulation_rate`, and for how long.
- `PILL_TOXICITY`: a pill's toxicity by grade, for a family that does not set its own;
- `RECIPE_TIME`: an alchemy recipe's brewing time by grade, likewise.
A curve is read in a spec as `curve("name")` (the tier's value) or `curve("name", key)`.
"""

GRADES = ["plain", "common", "earth", "heaven", "mystic", "spirit", "sage", "sovereign", "will", "sphere", "law", "monarch"]
MID_ILV = {"plain": 5, "common": 14, "earth": 27, "heaven": 45, "mystic": 59, "spirit": 68, "sage": 77, "sovereign": 86, "will": 95, "sphere": 104}
# The grade's name as an item's text says it ("a Heaven-grade pill").
GRADE_NAME = {g: g.capitalize() for g in GRADES}

# Decision 45's cultivation-speed ladder: (accumulation_rate bonus, minutes). Plain and Common are the two incense
# sticks (Granny Liu's +30% for 10 minutes, Stoneford's Deep Current +50% for 15), Earth the Qi Flow Pill (+20% for an
# hour, with its debt). From Heaven a Streams Pill adds a tenth more for each grade above Earth, for 45 minutes: the
# bonus-minutes a use gives (bonus x minutes: the minutes of sitting it saves, near enough) climb 3, 7.5, 12, then
# 13.5, 18, 22.5, 27, 31.5, so each rung adds more Qi to a sitting at its own realm than the rung below at its own
# (balance_sim's speed ladder), while a stage there takes ever longer to sit through.
SPEED = {"plain": (0.3, 10), "common": (0.5, 15), "earth": (0.2, 60),
         "heaven": (0.3, 45), "mystic": (0.4, 45), "spirit": (0.5, 45), "sage": (0.6, 45), "sovereign": (0.7, 45)}
# A pill's toxicity by grade when its family sets none: the lifting pills of the grade sit about here.
PILL_TOXICITY = {"plain": 4, "common": 6, "earth": 8, "heaven": 8, "mystic": 10, "spirit": 10, "sage": 12, "sovereign": 12,
                 "will": 14, "law": 20, "monarch": 25}
# An alchemy recipe's brewing time in seconds by grade when its family sets none (the pills of the grade sit about here).
RECIPE_TIME = {"plain": 60, "common": 180, "earth": 300, "heaven": 600, "mystic": 900, "spirit": 900, "sage": 1200, "sovereign": 1200,
               "will": 1800}


def grade_index(grade):
    return GRADES.index(grade)


def ilv(grade):
    return MID_ILV.get(grade, 5)


def cultivation(share, grade):
    """`share` of the need of the stage at the middle of `grade`'s band: the fixed cultivation of decision 45."""
    import realms
    return realms.cultivation(share, ilv(grade))


def cult_text(n):
    """How an item's text says its cultivation: "+420 cultivation"."""
    return "+{:,} cultivation".format(n)


def speed(grade):
    """(bonus, seconds) of a cultivation-speed item of `grade`."""
    bonus, minutes = SPEED[grade]
    return bonus, minutes * 60


def value(name, grade, key=None):
    """A curve's value at `grade` (a spec's `curve(name)`)."""
    if name == "ilv":
        return ilv(grade)
    if name == "speed":
        b, s = speed(grade)
        return {"bonus": b, "seconds": s, "minutes": s // 60, "pct": int(round(b * 100))}[key or "bonus"]
    if name == "toxicity":
        return PILL_TOXICITY[grade]
    if name == "recipe_time":
        return RECIPE_TIME[grade]
    if name == "cultivation":
        return cultivation(key, grade)
    raise KeyError("no curve %s" % name)
