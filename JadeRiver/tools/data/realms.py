"""S03 realm ladder, S05 major-realm requirements, S29 Qi point needs."""
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
    ("sage", "Sage", 3, 3, 64, "sage_qi", 267, 1800),
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


def need(level, t_minutes):
    return 100 * t_minutes


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
            t_here = t
            if rid == "bone_forging" and sub == 1:
                t_here = 12
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
    # Link each sub-level to the next and attach the major requirement to the key BEFORE it.
    for i, row in enumerate(rows):
        row["next"] = rows[i + 1]["key"] if i + 1 < len(rows) else ""
    by_key = {r["key"]: r for r in rows}
    for target, (source, event, requirements) in MAJOR.items():
        first = target if target in by_key else "%s_1" % target
        by_key[source]["major_breakthrough"] = {"to": first, "event": event, "requirements": requirements}
    # Advanced states chain: hhm -> dao_sigil -> heavens_threshold are accumulation plus flags.
    by_key["half_heaven_monarch"]["major_breakthrough"] = {"to": "dao_sigil", "event": None, "requirements": req(
        c("powers_refined_at_least", "structure", True, "page:cultivation", value=1))}
    by_key["dao_sigil"]["major_breakthrough"] = {"to": "heavens_threshold", "event": None, "requirements": req(
        c("powers_refined_at_least", "structure", True, "page:cultivation", value=5))}
    by_key["inner_heaven_9"]["major_breakthrough"] = {"to": "world_genesis", "event": "genesis", "requirements": req(
        c("flag_set", "understanding", True, "page:cultivation", flag="genesis_requirements_met"))}
    entries("realms.json", rows)
    return rows


if __name__ == "__main__":
    build()
