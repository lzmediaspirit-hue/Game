"""S03 realm ladder, S05 major-realm requirements, S29 Qi point needs, S49 lifespans (display only)."""
from common import entries, req, c

# (realm id, display, sub-level count, levels per sub-level, first Level, energy, T minutes per Level,
#  consolidation seconds after the major breakthrough into it)
REALMS = [
    ("bone_forging", "Bone Forging", 9, 1, 1, "body", 32, 60),
    ("qi_kindling", "Qi Kindling", 9, 1, 10, "primal_qi", 53, 180),
    ("qi_unfurling", "Qi Unfurling", 9, 1, 19, "primal_qi", 47, 300),
    ("heart_tempering", "Heart Tempering", 9, 1, 28, "primal_qi", 67, 420),
    ("cloud_stride", "Cloud Stride", 9, 1, 37, "true_qi", 80, 600),
    ("spirit_awakening", "Spirit Awakening", 9, 1, 46, "true_qi", 87, 900),
    ("heaven_glimpse", "Heaven Glimpse", 3, 3, 55, "true_qi", 100, 1200),
    ("sage", "Sage", 3, 3, 64, "sage_qi", 1050, 1800),
    ("sage_sovereign", "Sage Sovereign", 3, 3, 73, "sage_qi", 200, 2400),
    ("will_manifest", "Will Manifest", 3, 3, 82, "sage_qi", 333, 3000),
    ("sphere_lord", "Sphere Lord", 3, 3, 91, "sage_qi", 333, 3600),
    ("law_touching", "Law Touching", 3, 3, 100, "law_qi", 400, 5400),
    ("monarch", "Monarch", 3, 3, 109, "monarch_qi", 400, 7200),
]
ADVANCED = [("half_heaven_monarch", "Half-Heaven Monarch", 118), ("dao_sigil", "Dao Sigil", 119),
            ("heavens_threshold", "Heaven's Threshold", 120)]

MAJOR = {
    "bone_forging": ("mortal", None, req(
        c("method_learned", "material", True, "npc:lu_boatman", text="Learn a cultivation method"),
        c("body_level_at_least", "structure", False, "room:wp_west", value=1))),
    "qi_kindling": ("bone_forging_9", None, req(
        c("qi_full", "energy", False, "action:meditate"),
        c("body_level_at_least", "structure", False, "room:wp_west", value=9),
        c("method_supports", "material", True, "page:cultivation.methods"))),
    "qi_unfurling": ("qi_kindling_9", "heavens_cleansing", req(
        c("technique_tier_at_least", "understanding", False, "page:techniques", technique="any", tier=3),
        c("body_level_at_least", "structure", False, "room:wp_west", value=18),
        c("event_passed", "environment", True, "room:cp_cleansing_summit", event="heavens_cleansing"),
        c("method_supports", "material", True, "page:cultivation.methods"))),
    "heart_tempering": ("qi_unfurling_9", None, req(
        c("qi_full", "energy", False, "action:meditate"),
        c("body_level_at_least", "structure", False, "room:wg_gorge_mouth", value=27),
        c("method_supports", "material", True, "page:cultivation.methods"))),
    "cloud_stride": ("heart_tempering_9", "heart_trial", req(
        c("event_passed", "understanding", True, "room:si_trial_of_reflections", event="heart_trial"),
        c("item_owned", "material", True, "recipe:qi_refining_pill", item="qi_refining_pill", count=1, consume=True),
        c("method_supports", "material", True, "page:cultivation.methods"))),
    "spirit_awakening": ("cloud_stride_9", None, req(
        c("purity_at_least", "energy", True, "page:cultivation.seclusion", grade=6),
        c("item_owned", "material", True, "recipe:mind_lake_opening_pill", item="mind_lake_opening_pill", count=1, consume=True),
        c("method_supports", "material", True, "page:cultivation.methods"))),
    "heaven_glimpse": ("spirit_awakening_9", None, req(
        c("dao_tier_at_least", "understanding", True, "page:cultivation.dao", dao="any", tier=4),
        c("zone_supports", "environment", True, "page:world_map", realm="heaven_glimpse_1"),
        c("method_supports", "material", True, "page:cultivation.methods"))),
    "sage": ("heaven_glimpse_3", None, req(
        c("purity_at_least", "energy", True, "page:cultivation.seclusion", grade=3),
        c("item_owned", "material", True, "recipe:sage_condensing_pill", item="sage_condensing_pill", count=1, consume=True),
        c("zone_supports", "environment", True, "page:world_map", realm="sage_1"))),
    "sage_sovereign": ("sage_3", None, req(
        c("qi_full", "energy", False, "action:meditate"),
        c("dao_tier_at_least", "understanding", True, "page:cultivation.dao", dao="any", tier=5),
        c("method_supports", "material", True, "page:cultivation.methods"))),
    "will_manifest": ("sage_sovereign_3", "presence_trial", req(
        c("soul_at_least", "structure", True, "page:cultivation", value=1500),
        c("event_passed", "understanding", True, "page:cultivation", event="presence_trial"))),
    "sphere_lord": ("will_manifest_3", None, req(
        c("presence_level_at_least", "understanding", True, "page:cultivation", value=5),
        c("item_owned", "material", True, "page:inventory", item="sphere_comprehension_stone", count=1, consume=True))),
    "law_touching": ("sphere_lord_3", None, req(
        c("law_affinity_at_least", "environment", True, "page:world_map", law="any", value=1, count=1),
        c("item_owned", "material", True, "page:inventory", item="law_condensing_pill", count=1, consume=True),
        c("item_owned", "material", True, "page:inventory", item="law_touching_pill", count=1, consume=True))),
    "monarch": ("law_touching_3", None, req(
        c("law_affinity_at_least", "understanding", True, "page:world_map", law="any", value=3, count=2),
        c("zone_supports", "environment", True, "page:world_map", realm="monarch_1"),
        c("item_owned", "material", False, "page:inventory", item="monarch_condensing_pill", count=1, consume=True))),
    "half_heaven_monarch": ("monarch_3", None, req(
        c("flag_set", "understanding", True, "page:cultivation", flag="heavenly_dao_insight"))),
    "inner_heaven": ("heavens_threshold", "inner_world_forming", req(
        c("powers_refined_at_least", "structure", True, "page:cultivation", value=7),
        c("qi_full", "energy", True, "action:meditate"),
        c("room_safe", "environment", True, "page:world_map"),
        c("item_owned", "material", False, "page:inventory", item="sigil_anchor_pill", count=1, consume=True))),
}


# S49 lifespan as flavour: the most years each great realm lets a body live. Shown on the Character page with the
# character's age; longevity treasures add to it. There is no death clock (Part 1).
MAX_YEARS = {"mortal": 80, "bone_forging": 100, "qi_kindling": 120, "qi_unfurling": 150, "heart_tempering": 200,
             "cloud_stride": 300, "spirit_awakening": 500, "heaven_glimpse": 800, "sage": 1200, "sage_sovereign": 2000,
             "will_manifest": 3000, "sphere_lord": 5000, "law_touching": 8000, "monarch": 12000, "half_heaven_monarch": 20000,
             "dao_sigil": 30000, "heavens_threshold": 50000, "inner_heaven": 100000, "world_genesis": 0}


# Bone Forging front-loaded (docs/research/player_motivation.md §3.2): 600 / 900 / 1,200 / 1,600 progress for Bone
# Forging 1-4, so the story's own fights carry the first hour to Bone Forging 4; Bone Forging 5-9 take the rest, so Qi
# Kindling 1 still lands at about 5 hours (balance_sim's pacing row).
BONE_FORGING_T = [6, 9, 12, 16, 31, 31, 31, 31, 31]


def need(level, t_minutes):
    return 100 * t_minutes


def level_of(key):
    """The first Level of a realm key (mortal 0, bone_forging_4 4, heavens_threshold 120, world_genesis 166)."""
    if key == "mortal":
        return 0
    if key == "world_genesis":
        return 166
    for rid, _, level in ADVANCED:
        if key == rid:
            return level
    if key.startswith("inner_heaven_"):
        return 121 + (int(key.rsplit("_", 1)[1]) - 1) * 5
    for rid, _, _, per, first, _, _, _ in REALMS:
        if key.startswith(rid + "_") and key[len(rid) + 1:].isdigit():
            return first + (int(key[len(rid) + 1:]) - 1) * per
    raise KeyError(key)


def energy_at(level):
    """The energy a character of this Level cultivates, as the ladder below gives it (P12's par character reads it)."""
    if level >= 121:
        return "heavenforce"
    if level >= ADVANCED[0][2]:
        return "monarch_qi"
    energy = "none"
    for _, _, _, _, first, e, _, _ in REALMS:
        if level >= first:
            energy = e
    return energy


def build():
    rows = []
    rows.append({"id": "mortal", "key": "mortal", "realm": "mortal", "realm_index": 0, "sub": 0,
                 "name": "Mortal", "level": 0, "levels": 1, "energy": "none",
                 "accumulate_needed": need(0, 5), "consolidation_s": 0, "major": False,
                 "next": "bone_forging_1"})
    for index, (rid, name, subs, per, first, energy, t, consolidation) in enumerate(REALMS, start=1):
        for sub in range(1, subs + 1):
            key = "%s_%d" % (rid, sub)
            level = first + (sub - 1) * per
            e = energy
            if rid == "bone_forging":
                e = "primal_qi" if sub >= 7 else "none"
            t_here = BONE_FORGING_T[sub - 1] if rid == "bone_forging" else t
            qp = sum(need(level + k, t_here) for k in range(per))
            row = {"id": key, "key": key, "realm": rid, "realm_index": index, "sub": sub,
                   "name": "%s %d" % (name, sub), "level": level, "levels": per, "energy": e,
                   "accumulate_needed": qp, "consolidation_s": consolidation if sub == 1 else 0,
                   "major": sub == 1, "order_style": per > 1}
            rows.append(row)
    idx = len(REALMS) + 1
    for rid, name, level in ADVANCED:
        rows.append({"id": rid, "key": rid, "realm": rid, "realm_index": idx, "sub": 0, "name": name,
                     "level": level, "levels": 1, "energy": "monarch_qi",
                     "accumulate_needed": need(level, 400), "consolidation_s": 7200, "major": True,
                     "order_style": False})
        idx += 1
    for sub in range(1, 10):
        key = "inner_heaven_%d" % sub
        level = 121 + (sub - 1) * 5
        rows.append({"id": key, "key": key, "realm": "inner_heaven", "realm_index": idx, "sub": sub,
                     "name": "Inner Heaven %d" % sub, "level": level, "levels": 5, "energy": "heavenforce",
                     "accumulate_needed": sum(need(level + k, 400) for k in range(5)),
                     "consolidation_s": 10800 if sub == 1 else 0, "major": sub == 1, "order_style": True})
    rows.append({"id": "world_genesis", "key": "world_genesis", "realm": "world_genesis",
                 "realm_index": idx + 1, "sub": 0, "name": "World Genesis", "level": 166, "levels": 1,
                 "energy": "heavenforce", "accumulate_needed": 0, "consolidation_s": 0, "major": True,
                 "order_style": False, "genesis": True})
    for row in rows:
        row["max_years"] = MAX_YEARS[row["realm"]]   # 0: without end
    # Link each sub-level to the next and attach the major requirement to the key BEFORE it.
    for i, row in enumerate(rows):
        row["next"] = rows[i + 1]["key"] if i + 1 < len(rows) else ""
    by_key = {r["key"]: r for r in rows}
    for target, (source, event, requirements) in MAJOR.items():
        first = target if target in by_key else "%s_1" % target
        by_key[source]["major_breakthrough"] = {"to": first, "event": event, "requirements": requirements}
        if source == "mortal":
            by_key[source]["major_breakthrough"]["guaranteed"] = True
    # Advanced states chain: hhm -> dao_sigil -> heavens_threshold are accumulation plus flags.
    by_key["half_heaven_monarch"]["major_breakthrough"] = {"to": "dao_sigil", "event": None, "requirements": req(
        c("powers_refined_at_least", "structure", True, "page:cultivation", value=1))}
    by_key["dao_sigil"]["major_breakthrough"] = {"to": "heavens_threshold", "event": None, "requirements": req(
        c("powers_refined_at_least", "structure", True, "page:cultivation", value=5))}
    by_key["inner_heaven_9"]["major_breakthrough"] = {"to": "world_genesis", "event": "genesis", "requirements": req(
        c("flag_set", "understanding", True, "page:cultivation", flag="genesis_requirements_met"))}
    entries("realms.json", rows)
    _LADDER.clear()
    _LADDER.extend(rows)
    return rows


# Decision 45: fixed cultivation rewards. Quests, pills, cores, herbs and events pay a number set when the data is built,
# from the need of the stage at their own tier (a quest's Level, an item's grade band), never a share of the stage the
# player happens to be in when the reward lands.
_LADDER = []


def ladder():
    """The ladder's rows in order (this module's build, or data/realms.json once it is built)."""
    if not _LADDER:
        import json
        import os
        from common import DATA
        with open(os.path.join(DATA, "realms.json")) as f:
            _LADDER.extend(json.load(f)["entries"])
    return _LADDER


def key_at_level(level):
    """The sub-level holding Level `level`: the last key whose first Level is at or under it."""
    best = "mortal"
    for row in ladder():
        if int(row["level"]) <= level:
            best = row["key"]
    return best


def need_at_level(level):
    """The need of the sub-level holding Level `level` (an order's whole need, as the bar shows it)."""
    return next(int(r["accumulate_needed"]) for r in ladder() if r["key"] == key_at_level(level))


def round_reward(x):
    """A reward as the game says it: two significant figures, at least 10 ("+120 cultivation", "+4,200")."""
    import math
    if x <= 0:
        return 0
    step = 10 ** max(1, int(math.floor(math.log10(x))) - 1)
    return int(max(10, math.floor(x / step + 0.5) * step))   # half away from zero, as ProgressionRules.round_reward


def cultivation(share, level):
    """`share` of the need at Level `level`, rounded as a reward."""
    return round_reward(share * need_at_level(level))


if __name__ == "__main__":
    build()
