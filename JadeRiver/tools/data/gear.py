"""P7b (docs/item_plan.md): named gear and sets.

gear.json holds the rules named pieces follow (item_plan §2.1-§2.3, §3.1): each archetype's weapon families, path and
fixed-affix pool; when a path is held; what a named piece's element and a held path add; the six archetype set lines;
and the named counts per archetype and zone the plan targets. sets.json holds every set with its archetype, tier,
element and path. items.build_artifacts tags the named pieces with `tag()`; `line_set()` builds an archetype set's row
from its line.
"""
from common import entries, write
from stats import AFFIXES

AFFIX = {a["id"]: a for a in AFFIXES}

# §1.4, §3.1: the families (and slots) each archetype serves best, the path its pieces answer to, and the affixes its
# named pieces carry fixed (any of these on any slot; the plan's per-slot table picks among them).
ARCHETYPES = {
    "body": {"families": ["gauntlets", "heavy_sabre", "staff", "spear"], "path": "body_ladder",
             "affixes": ["attack_pct", "body", "hp_pct", "knockback", "toxicity_tolerance"]},
    "sword": {"families": ["jian"], "path": "sword_dao", "affixes": ["penetration", "qi_attack_pct", "crit", "essence", "agility", "move_speed"]},
    "alchemist": {"families": ["short_blade"], "slots": ["tool_furnace"], "path": "poison",
                  "affixes": ["crit_damage", "craft_control", "essence", "agility", "evasion", "toxicity_tolerance"]},
    "beast": {"families": ["bow"], "slots": ["pet_collar", "pet_talisman", "pet_saddle"], "path": "beast_taming",
              "affixes": ["pet_damage", "taming", "hp_pct", "agility", "evasion"]},
    "formation": {"families": ["fan", "brush"], "path": "confucian", "affixes": ["qi_attack_pct", "insight", "essence", "tenacity", "evasion", "array_power"]},
    "musician": {"families": ["flute", "bell"], "path": "buddhist", "affixes": ["melody_power", "soul_attack_pct", "max_soul_pct", "tenacity", "evasion"]},
    "general": {"families": [], "path": "", "affixes": []},
}
# §2.2: when the wearer holds a path (StatRules.holds_path). Any one clause is enough; a Dao clause with `dao_until`
# stops counting from that realm (the Confucian path opens at Will Manifest 2, and Formation Dao 3 stands in before it).
PATHS = {
    "body_ladder": {"body_tier": 1},                          # Copper Body or higher
    "sword_dao": {"dao": "sword", "tier": 3},                 # Reliable Execution
    "poison": {"poison_art": True},                           # a poison art known
    "beast_taming": {"dao": "beast_taming", "tier": 2},       # (v1.3: or a Soul Band worn)
    "confucian": {"walks": "confucian", "dao": "formation", "tier": 3, "dao_until": "will_manifest_2"},
    "buddhist": {"vow": True, "dao": "music", "tier": 3},     # a vow held, or Music Dao 3
    "blood": {"walks": "blood"},
}
# §2.1: +2% elemental power of its element for each named piece worn; on its path a signature's fixed affixes count
# half again and a set's 2-piece bonus counts double.
NAMED = {"element_power": 0.02, "path_fixed": 1.5, "path_set_two": 2.0}


def stat(s, op, value):
    return {"stat": s, "op": op, "value": value}


# §3.1: one line of four sets per archetype (tier I valley, II Expanse, III Lantern, IV Frontier). The 2- and 4-piece
# bonuses are the same at every tier; the 6-piece mechanic is a `flag` row whose `tiers` values grow by tier.
LINES = {
    "body": {"2": [stat("max_hp", "pct_add", 0.05)],
             "4": [stat("physical_defense", "pct_add", 0.08), stat("knockback_resistance", "flat", 0.10)],
             "6": [stat("physical_attack", "pct_add", 0.08)],
             "flag": {"flag": "unbroken", "below": 0.3, "shield_s": 5, "cooldown_s": 60, "tiers": {"shield": [0.10, 0.12, 0.14, 0.16]}}},
    "sword": {"2": [stat("crit_chance", "flat", 0.02)], "4": [stat("penetration", "flat", 0.04)], "6": [stat("qi_attack", "pct_add", 0.08)],
              "flag": {"flag": "honed_intent", "fade_mult": 2.0, "tiers": {"stacks": [2, 2, 3, 3]}}},
    "alchemist": {"2": [stat("toxicity_tolerance", "pct_add", 0.20)],
                  "4": [stat("crafting_control", "flat", 0.06), stat("crafting_perception", "flat", 0.06)],
                  "6": [stat("physical_attack", "pct_add", 0.08)],
                  "flag": {"flag": "venom_hand", "threshold": 0.35, "tiers": {"oil_chance": [0.25, 0.28, 0.31, 0.34]}}},
    "beast": {"2": [stat("taming_chance", "flat", 0.05)], "4": [stat("pet_damage", "flat", 0.10)], "6": [stat("physical_attack", "pct_add", 0.08)],
              "flag": {"flag": "kin_bond", "taken": 0.85, "tiers": {"per_band": [0.01, 0.015, 0.02, 0.025]}}},
    "formation": {"2": [stat("qi_attack", "pct_add", 0.05)], "4": [stat("array_power", "flat", 0.15)], "6": [stat("qi_attack", "pct_add", 0.08)],
                  "flag": {"flag": "living_array", "talismans": {"binding": {"id": "root", "power": 1, "duration_s": 1.0},
                                                                 "killing": {"id": "sundered", "power": 1, "duration_s": 4.0},
                                                                 "guard": {"id": "qi_seal", "power": 1, "duration_s": 1.0}},
                           "tiers": {"wider": [0.15, 0.20, 0.25, 0.30]}}},
    "musician": {"2": [stat("soul_attack", "pct_add", 0.05)], "4": [stat("melody_power", "flat", 0.15)], "6": [stat("soul_attack", "pct_add", 0.08)],
                 "flag": {"flag": "sustained_note", "free_s": 3.0, "tiers": {"ally_heal": [0.01, 0.0125, 0.015, 0.0175]}}},
}
# §2.3: named pieces per archetype and zone, P9's six boss signatures included (`p9` is their share, which counts once
# P9 lands). tests/data_validation.gd checks them once the named pieces of item_plan §6 step 8 are in.
TARGETS = {"valley": {"body": 13, "sword": 13, "alchemist": 13, "beast": 12, "formation": 10, "musician": 10, "general": 17},
           "expanse": {"body": 14, "sword": 8, "alchemist": 9, "beast": 8, "formation": 10, "musician": 9, "general": 0},
           "lantern": {"body": 12, "sword": 8, "alchemist": 8, "beast": 8, "formation": 9, "musician": 9, "general": 0}}
P9_SHARE = {"valley": {"body": 2}, "expanse": {"formation": 1, "alchemist": 1}, "lantern": {"body": 2}}

# The general sets (§1.5, §3.4): no archetype stat, the valley's, tier I.
SETS = [
    {"id": "jade_current", "pieces": ["jade_current_hat", "jade_current_robe", "jade_current_trousers", "jade_current_boots"], "element": "water",
     "bonuses": {"2": [stat("max_qi", "pct_add", 0.05)], "4": [dict(stat("elemental_power", "flat", 0.1), condition={"element": "water"})]}},
    {"id": "cloudpiercing", "pieces": ["cloudpiercing_hat", "cloudpiercing_robe", "cloudpiercing_trousers", "cloudpiercing_boots"], "element": "wind",
     "bonuses": {"2": [stat("move_speed", "pct_add", 0.05)], "4": [dict(stat("elemental_power", "flat", 0.1), condition={"element": "wind"})]}},
    {"id": "mudwater", "pieces": ["mudwater_cleaver", "mudwater_robe"], "bonuses": {"2": [stat("coin_find", "flat", 0.1)]}},
    {"id": "drowned_abbot", "pieces": ["drowned_hat", "drowned_robe", "drowned_boots"],
     "bonuses": {"2": [stat("soul_defense", "pct_add", 0.1)], "3": [stat("qi_resistance", "pct_add", 0.1)]}},
    {"id": "crane", "pieces": ["crane_robe", "crane_trousers", "crane_boots"],
     "bonuses": {"2": [stat("flight_speed", "pct_add", 0.05)], "3": [stat("flight_speed", "pct_add", 0.1)]}},
]


def fixed_affix(aid, ilv):
    """A named piece's fixed affix: rolled at the top third of the affix's range (its middle, so the data is exact)."""
    a = AFFIX[aid]
    lo, hi = a["range"]
    return {"id": aid, "stat": a["stat"], "op": a["op"], "value": round(lo + (hi - lo) * 5 / 6 + a.get("per_level", 0) * ilv, 3)}


def tag(archetype, zone, element="", fixed=(), ilv=0):
    """A named piece's `named` tags (§2.1): the archetype it serves and the zone of its source; the element its +2%
    elemental power follows; its fixed affixes, which its archetype's path strengthens."""
    d = {"archetype": archetype, "zone": zone}
    if element:
        d["element"] = element
    if fixed:
        d["path"] = ARCHETYPES[archetype]["path"]
        d["fixed"] = [fixed_affix(a, ilv) for a in fixed]
    return d


def line_set(set_id, line, tier, element, pieces):
    """An archetype set's row from its line (§3.1) at tier 1-4."""
    ln = LINES[line]
    flag = {k: v for k, v in ln["flag"].items() if k != "tiers"}
    flag.update({k: v[tier - 1] for k, v in ln["flag"]["tiers"].items()})
    return {"id": set_id, "pieces": pieces, "archetype": line, "tier": tier, "element": element, "path": ARCHETYPES[line]["path"],
            "bonuses": {"2": ln["2"], "4": ln["4"], "6": ln["6"] + [flag]}}


def build():
    write("gear.json", {"named": NAMED, "archetypes": ARCHETYPES, "paths": PATHS, "lines": LINES, "targets": TARGETS, "p9_share": P9_SHARE})
    rows = [dict({"id": s["id"], "archetype": "general", "tier": 1, "element": "", "path": ""}, **s) for s in SETS]
    entries("sets.json", rows)


if __name__ == "__main__":
    build()
