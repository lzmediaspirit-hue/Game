"""The item engine's row templates: one function a kind, from a member's resolved fields to its row as the game reads it
(items.json, artifacts.json). The key order is the game's tables' own: a template writes keys in the order the rows
have always had them, and a spec's `row` pins land last (a pinned key that exists keeps its place).

`item()` and `artifact()` are the two row constructors every module uses (items.py re-exports them).
"""
from common import titled

from .curves import MID_ILV
from .dsl import DROP


def item(id, type, grade="plain", stack=99, desc="", name=None, icon=None, **extra):
    row = {"id": id, "name": name or titled(id), "type": type, "grade": grade, "ilv": extra.pop("ilv", MID_ILV.get(grade, 5)),
           "stack": stack, "icon": icon or id, "desc": desc}
    row.update(extra)
    return row


ENERGY = {"plain": "none", "common": "primal_qi", "earth": "primal_qi", "heaven": "true_qi", "mystic": "true_qi", "spirit": "sage_qi",
          "sage": "sage_qi", "sovereign": "sage_qi", "will": "sage_qi"}
SOCKETS = {"plain": 0, "common": 0, "earth": 1, "heaven": 1, "mystic": 2, "spirit": 2, "sage": 3, "sovereign": 3, "will": 3}


def artifact(id, slot, grade, name, appearance, family=None, ilv=None, icon=None, **extra):
    row = {"id": id, "name": name, "slot": slot, "grade": grade, "ilv": ilv or MID_ILV[grade], "appearance": appearance,
           "energy_type": ENERGY[grade], "sockets": SOCKETS[grade], "icon": icon or id, "type": "equipment", "stack": 1}
    if family:
        row["family"] = family
    row.update(extra)
    return row


def _given(m, key):
    return key in m and m[key] is not DROP


def _base(m):
    """The fields every item() row takes from its member: stack, name, icon and a pinned ilv."""
    kw = {}
    if _given(m, "ilv"):
        kw["ilv"] = m["ilv"]
    return kw


def _mark(m, extra, listed=False):
    """A source mark (wiki.py MARKS: story, system, later) is the row's `source`, after the kind's own keys (in a list
    on equipment, as its authored source hints are)."""
    mark = m.get("_mark")
    if mark:
        extra["source"] = [mark] if listed else mark


# ------------------------------------------------------------------------------------------------------------- pills
# S44: the Pill Soul a recipe's group carries unless the pill names its own (grades.json pill.soul).
SOUL_BY_GROUP = {"healing": "mend_meridians", "restoration": "mend_meridians", "buff": "iron_skin", "utility": "steady_heart"}


def pill(m):
    p = {"mark": m["mark"], "toxicity": m["toxicity"]}
    if m.get("cause", None) is not DROP:
        p["cause"] = m.get("cause")
    p["group"] = m["group"]
    extra = _base(m)
    extra["pill"] = p
    extra["use"] = m.get("use", [])
    soul = m.get("soul")
    if soul is not DROP:
        extra["soul_effect"] = soul or SOUL_BY_GROUP.get(m["group"], "steady_heart")
    extra.update(m.get("extra") or {})
    _mark(m, extra)
    if m.get("resist"):
        extra["family"] = m["resist"]   # S44 lifetime resistance (accumulation, body, insight, soul, support)
    return item(m["id"], "pill", m["grade"], m.get("stack", 99), m["desc"], name=m.get("name"), icon=m.get("_icon"), **extra)


# ------------------------------------------------------------------------------------------------------------- herbs
NATURE_TEXT = {"hot": " A hot herb: it drives the Extraction band up.", "cold": " A cold herb: it draws the Extraction band down.",
               "neutral": ""}


def raw_family(effects):
    """A raw herb counts toward the family of what it builds up (S44)."""
    kinds = {e["kind"] for e in effects}
    for kind, fam in (("add_progress", "accumulation"), ("add_body_xp", "body"), ("add_soul", "soul"), ("add_insight", "insight")):
        if kind in kinds:
            return fam
    return ""


def herb_id(stem, age, young_age=False):
    """A herb's id by its family and age: the ten-year herb is the family's own id (ginseng says its age at ten too)."""
    return "%s_%d" % (stem, age) if (age != 10 or young_age) else stem


def herb_name(stem, age, young_age=False):
    return "%s (%s yr)" % (titled(stem), "{:,}".format(age)) if (age != 10 or young_age) else titled(stem)


def cult_text(n):
    return "+{:,} cultivation".format(n)


def herb(m):
    raw = m.get("raw")
    extra = _base(m)
    if raw:
        extra["use"] = raw["use"]
        extra["raw"] = {"toxicity": raw["toxicity"]}
        fam = raw_family(raw["use"])
        if fam:
            extra["family"] = fam
    extra["nature"] = m["nature"]
    extra["roles"] = m["roles"]
    extra["herb"] = {"family": m["_stem"], "age": m["tier"]}
    # Decision 45: a root eaten raw for Qi says its fixed cultivation.
    gain = sum(int(e.get("amount", 0)) for e in (raw["use"] if raw else []) if e["kind"] == "add_progress")
    eat = (" Can be eaten raw in need (%s): weak, and hard on the meridians." % cult_text(gain) if gain else
           " Can be eaten raw in need: weak, and hard on the meridians.") if raw else ""
    extra.update(m.get("extra") or {})
    _mark(m, extra)
    return item(m["id"], "herb", m["grade"], m.get("stack", 99), m["desc"] + NATURE_TEXT[m["nature"]] + eat, name=m.get("name"),
                icon=m.get("_icon"), **extra)


def seed(m, s):
    """The seed row of a herb family (S45): `s` is the family's seed=dict(grade, desc[, id])."""
    return item(m["id"], "seed", s["grade"], 99, s["desc"] + " Plant it in a garden bed.", seed={"family": m["_stem"]})


# ------------------------------------------------------------------------------------------- ores and creature parts
def ore(m):
    extra = _base(m)
    extra.update(m.get("extra") or {})
    _mark(m, extra)
    return item(m["id"], m.get("type", "ore"), m["grade"], m.get("stack", 99), m["desc"], name=m.get("name"), icon=m.get("_icon"), **extra)


def part(m):
    extra = _base(m)
    extra.update(m.get("extra") or {})
    _mark(m, extra)
    return item(m["id"], m.get("type", "beast_part"), m["grade"], m.get("stack", 99), m["desc"], name=m.get("name"), icon=m.get("_icon"),
                **extra)


# --------------------------------------------------------------------------------------------------------------- gear
def weapon(m):
    extra = {}
    if _given(m, "ilv"):
        extra["ilv"] = m["ilv"]
    extra.update(m.get("extra") or {})
    if m.get("attribute"):
        extra["attribute_req"] = {m["attribute"]: m["attribute_req"]}
    return artifact(m["id"], "weapon", m["grade"], m["name"], m["appearance"], m["_stem"], icon=m.get("_icon"), **extra)


def armour(m):
    extra = {}
    if _given(m, "ilv"):
        extra["ilv"] = m["ilv"]
    if m.get("dye"):
        extra["dye"] = m["dye"]
    extra.update(m.get("extra") or {})
    return artifact(m["id"], m["slot"], m["grade"], m["name"], m["appearance"], icon=m.get("_icon"), **extra)


def gourd(m):
    extra = {"gourd": {"bag": m["bag"], "quick": m["quick"]}}
    if _given(m, "ilv"):
        extra["ilv"] = m["ilv"]
    extra.update(m.get("extra") or {})
    _mark(m, extra, listed=True)
    return artifact(m["id"], "gourd", m["grade"], m["name"], "none", icon=m.get("_icon"), **extra)


def pet_gear(m):
    """A spirit animal's piece on the P7b ladder (item_plan §2.9, G5): its stats and the text they fill."""
    return artifact(m["id"], m["slot"], m["grade"], m["name"], "none", icon=m.get("_icon"), sockets=0, energy_type="none", pet_gear=m["stats"],
                    desc=m["desc"])


def furnace(m):
    """A furnace on the P7b ladder (G6): heat stability, batch, filter and yield by grade."""
    return artifact(m["id"], "tool_furnace", m["grade"], m["name"], "none", icon=m.get("_icon"), desc=m["desc"], furnace=m["stats"], sockets=0,
                    energy_type="none")


KINDS = {"pill": pill, "herb": herb, "ore": ore, "part": part, "weapon": weapon, "armour": armour, "gourd": gourd, "pet_gear": pet_gear,
         "furnace": furnace}
# The table a kind's rows go to, and its default section (the block of that table a host places).
TABLE = {"pill": "items", "herb": "items", "ore": "items", "part": "items", "weapon": "artifacts", "armour": "artifacts",
         "gourd": "artifacts", "pet_gear": "artifacts", "furnace": "artifacts"}
SECTION = {"pill": "pills", "herb": "herbs", "ore": "ores", "part": "parts.valley", "weapon": "weapons", "armour": "armour",
           "gourd": "gourds", "pet_gear": "pet_gear", "furnace": "furnaces"}
