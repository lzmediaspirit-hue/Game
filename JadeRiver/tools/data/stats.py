"""S10/S11/S12/S13/S14/S29 constants: stats.json, curves.json, elements, statuses, weapon families,
grades, affixes, sets, injuries, failures, origins, methods."""
from common import write, entries
from realms import energy_at

STAT_LIST = [
    # id, group, cap (value or reduction), format
    ("max_hp", "pool", None, "int"), ("max_qi", "pool", None, "int"), ("max_soul", "pool", None, "int"),
    ("body", "attribute", None, "int"), ("agility", "attribute", None, "int"), ("essence", "attribute", None, "int"),
    ("spirit", "attribute", None, "int"), ("insight", "attribute", None, "int"), ("fortune", "attribute", None, "int"),
    ("physical_attack", "offense", None, "int"), ("qi_attack", "offense", None, "int"), ("soul_attack", "offense", None, "int"),
    ("accuracy", "offense", None, "int"), ("crit_chance", "offense", 0.75, "percent"), ("crit_damage", "offense", 3.0, "percent"),
    ("attack_speed", "offense", 0.5, "percent"), ("penetration", "offense", 0.4, "percent"), ("pressure", "offense", None, "int"),
    ("elemental_power", "offense", 1.5, "percent"),
    ("physical_defense", "defense", None, "int"), ("qi_resistance", "defense", None, "int"), ("soul_defense", "defense", None, "int"),
    ("evasion", "defense", None, "int"), ("guard", "defense", 0.8, "percent"), ("elemental_resistance", "defense", 0.75, "percent"),
    ("tenacity", "defense", 0.6, "percent"), ("will", "defense", None, "int"), ("hollow_ward", "defense", 0.8, "percent"),
    ("move_speed", "movement", 0.4, "percent"), ("climb_speed", "movement", 0.5, "percent"), ("flight_speed", "movement", None, "int"),
    ("hp_regen", "recovery", None, "percent"), ("qi_regen", "recovery", None, "percent"), ("soul_regen", "recovery", None, "percent"),
    ("accumulation_rate", "cultivation", None, "percent"), ("insight_rate", "cultivation", None, "percent"),
    ("toxicity_tolerance", "cultivation", None, "int"), ("injury_recovery", "cultivation", None, "percent"),
    ("gathering_power", "world", None, "percent"), ("mining_power", "world", None, "percent"),
    ("crafting_control", "world", None, "percent"), ("crafting_perception", "world", None, "percent"),
    ("sense_radius", "world", None, "int"), ("drop_rate", "world", 1.0, "percent"), ("coin_find", "world", 1.0, "percent"),
    ("taming_chance", "world", 0.9, "percent"), ("technique_cost", "offense", 0.3, "percent"),
    ("mastery_gain", "cultivation", None, "percent"), ("fist_attack", "offense", None, "percent"),
    ("attunement_bonus", "world", None, "int"),
    # S48 body ladder and physiques: knockback taken is cut by this share; flight QI cost moves by this share.
    ("knockback_resistance", "defense", 0.9, "percent"), ("flight_qi", "movement", 0.5, "percent"),
    # S48 Inner Arts: the dodge cooldown moves by this share (Swallow's Breath).
    ("dodge_cooldown", "movement", 0.5, "percent"),
    # S48 vows: healing received moves by this share (Mercy).
    ("healing_received", "recovery", 1.0, "percent"),
    # P7b (item_plan §3.1): the archetype stats, percent with no cap. Pet damage adds to the animal's strike (PetAuthority),
    # array power to an Array Plate's time and the killing array's blow, melody power to the melody's slow and heals, the
    # bell's ring and Clear Heart Melody (CombatAuthority).
    ("pet_damage", "offense", None, "percent"), ("array_power", "offense", None, "percent"), ("melody_power", "offense", None, "percent"),
    # P12 (research §6.3): the one additive damage bucket (damage%, with elemental power beside it and boss damage against
    # elites and bosses), and final damage, a product of its sources (base 1, each source a pct_mul).
    ("damage_pct", "offense", None, "percent"), ("boss_damage", "offense", None, "percent"), ("final_damage", "offense", None, "mult"),
]


# S14 affixes: the random pools by slot (LootRules), and the fixed affixes of named pieces (tools/data/gear.py).
AFFIXES = [
    {"id": "attack_pct", "slots": ["weapon"], "stat": "physical_attack", "op": "pct_add", "range": [0.03, 0.08]},
    {"id": "crit", "slots": ["weapon", "hat"], "stat": "crit_chance", "op": "flat", "range": [0.01, 0.03]},
    {"id": "crit_damage", "slots": ["weapon"], "stat": "crit_damage", "op": "flat", "range": [0.05, 0.15]},
    {"id": "penetration", "slots": ["weapon"], "stat": "penetration", "op": "flat", "range": [0.02, 0.05]},
    {"id": "accuracy", "slots": ["weapon", "hat"], "stat": "accuracy", "op": "flat", "range": [3, 10], "per_level": 0.3},
    {"id": "hp_pct", "slots": ["robe", "trousers"], "stat": "max_hp", "op": "pct_add", "range": [0.03, 0.07]},
    {"id": "body", "slots": ["robe", "trousers"], "stat": "body", "op": "flat", "range": [1, 4], "per_level": 0.1},
    {"id": "agility", "slots": ["trousers", "boots"], "stat": "agility", "op": "flat", "range": [1, 4], "per_level": 0.1},
    {"id": "spirit", "slots": ["hat"], "stat": "spirit", "op": "flat", "range": [1, 4], "per_level": 0.1},
    {"id": "insight", "slots": ["hat"], "stat": "insight", "op": "flat", "range": [1, 4], "per_level": 0.1},
    {"id": "tenacity", "slots": ["hat", "trousers"], "stat": "tenacity", "op": "flat", "range": [0.02, 0.05]},
    {"id": "move_speed", "slots": ["boots"], "stat": "move_speed", "op": "pct_add", "range": [0.02, 0.05]},
    {"id": "guard", "slots": ["robe"], "stat": "guard", "op": "flat", "range": [0.02, 0.05]},
    {"id": "evasion", "slots": ["boots", "trousers"], "stat": "evasion", "op": "flat", "range": [2, 8], "per_level": 0.3},
    {"id": "toxicity_tolerance", "slots": ["gourd"], "stat": "toxicity_tolerance", "op": "flat", "range": [3, 8]},
    {"id": "coin_find", "slots": ["gourd"], "stat": "coin_find", "op": "flat", "range": [0.03, 0.08]},
    # P7b (item_plan §3.1): Qi and soul damage on weapons (G9), Essence, knockback and max Soul in the random pools; the
    # archetype affixes only on named pieces (`named_only`), as their fixed affixes.
    {"id": "qi_attack_pct", "slots": ["weapon"], "stat": "qi_attack", "op": "pct_add", "range": [0.03, 0.08]},
    {"id": "soul_attack_pct", "slots": ["weapon", "hat"], "stat": "soul_attack", "op": "pct_add", "range": [0.03, 0.08]},
    {"id": "essence", "slots": ["robe", "hat"], "stat": "essence", "op": "flat", "range": [1, 4], "per_level": 0.1},
    {"id": "knockback", "slots": ["robe", "boots"], "stat": "knockback_resistance", "op": "flat", "range": [0.03, 0.08]},
    {"id": "max_soul_pct", "slots": ["hat", "robe"], "stat": "max_soul", "op": "pct_add", "range": [0.03, 0.07]},
    {"id": "taming", "slots": ["hat", "gourd"], "stat": "taming_chance", "op": "flat", "range": [0.02, 0.05], "named_only": True},
    {"id": "craft_control", "slots": ["hat", "gourd"], "stat": "crafting_control", "op": "flat", "range": [0.02, 0.05], "named_only": True},
    {"id": "pet_damage", "slots": ["weapon", "gourd"], "stat": "pet_damage", "op": "flat", "range": [0.03, 0.08], "named_only": True},
    {"id": "array_power", "slots": ["weapon", "gourd", "talisman"], "stat": "array_power", "op": "flat", "range": [0.05, 0.12], "named_only": True},
    {"id": "melody_power", "slots": ["weapon", "gourd", "talisman"], "stat": "melody_power", "op": "flat", "range": [0.05, 0.12], "named_only": True},
]


# P12 Might (docs/research/stat_scaling_research.md §6.2): the realm's power step, on the player's attacks, max HP and
# defences and on every monster of the same Level. ×1.30 a great realm, 60% of it at the major breakthrough (×1.17) and
# the rest over the realm's other eight Levels; Bone Forging climbs only to ×1.05 (it keeps today's numbers), so the
# first step, at Qi Kindling 1, is ×1.30. The advanced states are ×1.10 each, Inner Heaven's nine ranks ×1.18 each
# (60% at the rank-up) and World Genesis +2% a Level past 166. Max Qi and max Soul never take Might.
MIGHT = {"step": 1.30, "major_share": 0.6, "body_top": 1.05, "levels_per_realm": 9, "advanced_from": 118, "advanced": 1.10,
         "inner_from": 121, "inner_levels": 5, "inner_rank": 1.18, "genesis_from": 166, "genesis_per_level": 0.02, "top_level": 200,
         "stats": ["max_hp", "physical_attack", "qi_attack", "soul_attack", "physical_defense", "qi_resistance", "soul_defense"]}


def might(lv):
    """Might at a Level (the table GDScript reads is this function from Level 0 to `top_level`)."""
    m, share, per = MIGHT["step"], MIGHT["major_share"], MIGHT["levels_per_realm"]
    if lv <= 1:
        return 1.0
    if lv <= per:
        return MIGHT["body_top"] ** ((lv - 1) / (per - 1))
    if lv < MIGHT["advanced_from"]:
        idx, stage = divmod(lv - 1, per)
        return m ** idx * m ** ((1 - share) * stage / (per - 1))
    if lv < MIGHT["inner_from"]:
        return might(MIGHT["advanced_from"] - 1) * MIGHT["advanced"] ** (lv - MIGHT["advanced_from"] + 1)
    if lv < MIGHT["genesis_from"]:
        rank, step = divmod(lv - MIGHT["inner_from"], MIGHT["inner_levels"])
        r = MIGHT["inner_rank"]
        return might(MIGHT["inner_from"] - 1) * r ** (rank + share) * r ** ((1 - share) * step / (MIGHT["inner_levels"] - 1))
    return might(MIGHT["genesis_from"] - 1) * m ** share * (1 + MIGHT["genesis_per_level"]) ** (lv - MIGHT["genesis_from"])


def might_block():
    return dict(MIGHT, table=[round(might(lv), 4) for lv in range(MIGHT["top_level"] + 1)])


# P12 the par character (research §6.1 principle 3): a steady cultivator of the jian at every Level, the yardstick the
# monster tables are set from; balance_sim builds it with the real rules and checks it against this table. Rows are
# [from Level, value, ...]: every piece's quality and enhancement (one a `enhance_every` Levels), the weapon and armour
# `weapon_lag` Levels behind their wearer, the Sword Dao's tier, the main art's mastery tier, the weapon's attack affix,
# the sets' damage%, crit chance and damage from affixes, and the main art: its multiplier with grade, a Qi strike, set
# so its hit meets the technique line of docs/technique_plan.md §6.1. Each step lands a Level or more past a major
# breakthrough so a breakthrough is the realm's own step. Meridian points go evenly to the five channels (the first
# channels take the remainder). DPS counts crits and techniques at +60% (`technique_share`). The monster tables: a
# normal foe falls to `hits` par basic hits and its plain blow takes `blow` of par max HP, after par's armour; under
# `from_level` both keep today's polynomials (Bone Forging keeps its numbers).
PAR = {"family": "jian", "origin": "fishers_child", "purity": 9, "weapon_lag": 3, "enhance_every": 12, "enhance_max": 10,
       "channels": ["body", "agility", "essence", "spirit", "insight"],
       "quality": [[1, "common"], [10, "fine"], [40, "superior"], [103, "perfect"]],
       "dao": [[1, 0], [15, 1], [30, 2], [49, 3], [67, 4], [85, 5], [112, 6]],
       "mastery": [[1, 1], [12, 2], [21, 3], [49, 4], [85, 5], [112, 6]],
       "attack_pct": [[1, 0.0], [22, 0.05], [67, 0.08], [103, 0.12]],
       "damage_pct": [[1, 0.0], [42, 0.08], [67, 0.13], [124, 0.20]],
       "crit": [[1, 0.0, 0.0], [40, 0.03, 0.10], [67, 0.05, 0.25], [124, 0.08, 0.50]],
       "art": [[1, 1.0], [19, 1.2], [37, 1.45], [55, 1.95], [64, 1.9], [73, 1.8], [82, 1.75], [91, 1.7], [109, 1.6],
               [121, 1.45], [141, 1.33], [151, 1.25], [166, 1.1]],
       "art_type": "qi", "technique_share": 1.6,
       "hits": 3.5, "blow": [[0, 0.08], [20, 0.06]], "from_level": 10}


def poly(spec, x):
    return spec.get("a", 0) + spec.get("b", 0) * x + spec.get("c", 0) * x * x


def par_step(key, lv):
    """The par schedule's row reached at `lv`: its value, or its values when the row holds several."""
    row = PAR[key][0]
    for r in PAR[key]:
        if lv >= r[0]:
            row = r
    return row[1] if len(row) == 2 else row[1:]


def par_row(lv, fam, origin):
    """The par character at a Level with the rules' formulas (StatRules.rebuild, CombatRules.resolve, combat_power);
    the constants written in code there (the weapon's 0.8% and 0.4% a point, the robe's HP and Qi resistance, the hat's
    soul defence) are repeated here."""
    c, fx, eq = CORE, CORE["attribute_effects"], CORE["equipment"]
    m = might(lv)
    pts = sum([r["points"] for r in c["meridian_points_per_level"] if lv_ >= r["from_level"]][-1] for lv_ in range(1, lv + 1))
    chans = PAR["channels"]
    meridians = {k: pts // len(chans) + (1 if i < pts % len(chans) else 0) for i, k in enumerate(chans)}
    attr = {k: c["attributes"]["base"] + c["attributes"]["per_level"] * lv + meridians[k] for k in chans}
    attr["fortune"] = c["attributes"]["base"]
    for k, v in origin.get("bonus", {}).items():
        attr[k] += v
    dao = par_step("dao", lv)
    attr["insight"] += c["attributes"]["insight_per_dao_tier"] * dao
    ilv = max(1, lv - PAR["weapon_lag"])
    gear = QUALITIES[par_step("quality", lv)]["mult"] * (1 + eq["enhance_per_level"] * min(PAR["enhance_max"], lv // PAR["enhance_every"]))
    s1, s2 = fam["scales"]
    watk = poly(eq["weapon_attack"], ilv) * gear * (1 + 0.008 * attr[s1] + 0.004 * attr[s2])
    attack = watk * (1 + par_step("attack_pct", lv)) * m
    qi_attack = watk * (1 + fx["essence"]["qi_attack_pct"] * attr["essence"]) * (1 + fam.get("qi_attack_bonus", 0.0)) * m
    arm = poly(eq["armour_defence"], ilv) * gear
    defence = (fx["body"]["physical_defense"] * attr["body"] + arm * sum(eq["slot_share"].values())) * m
    qi_res = (fx["essence"]["qi_resistance"] * attr["essence"] + arm * 0.2) * m
    soul_def = (fx["spirit"]["soul_defense"] * attr["spirit"] + arm * 0.3) * m
    hp_pct = c["meridian_gates"]["body"]["25"]["value"] if meridians["body"] >= 25 else 0.0
    hp =(poly(c["pools"]["hp"], lv) * (1 + fx["body"]["max_hp_pct"] * attr["body"]) + 5 * ilv * gear) * (1 + hp_pct) * m
    cr = c["crit"]
    crit_add, crit_dmg_add = par_step("crit", lv)
    crit = min(cr["cap"], cr["base"] + fx["agility"]["crit_chance"] * attr["agility"] + fx["fortune"]["crit_chance"] * attr["fortune"]
               + fam["crit"] + crit_add)
    crit_dmg = min(cr["damage_cap"], cr["damage_base"] + crit_dmg_add)
    k = (c["defence"]["k_flat"] + c["defence"]["k_level"] * lv) * m   # a same-Level normal foe's armour
    foe_def = poly(eq["armour_defence"], lv) * c["mob"]["roles"]["normal"]["defence"] * m
    cut = lambda d: min(c["defence"]["cap"], d / (d + k))
    tc, dmg = c["technique_cost"], par_step("damage_pct", lv)
    combo = sum(s["mult"] for s in fam["combo"]) / len(fam["combo"])
    basic = attack * combo * (1 + tc["dao_damage_per_tier"] * dao) * (1 + dmg) * (1 - cut(foe_def))
    energy = energy_at(lv)
    edge = c["qi_edge"][energy] + (c["qi_edge_per_purity"] * (9 - PAR["purity"]) if energy == "true_qi" else 0.0)
    technique = (qi_attack * par_step("art", lv) * (1 + tc["dao_damage_per_tier"] * dao + tc["mastery_damage_per_tier"] * (par_step("mastery", lv) - 1))
                 * edge * (1 + dmg) * (1 - cut(foe_def * 0.6)))
    crit_factor = 1 + crit * (crit_dmg - 1)
    swings = len(fam["combo"]) / sum(s["duration"] for s in fam["combo"])
    aspd = fam["hits_per_s"] * (1 + min(0.5, fx["agility"]["attack_speed"] * attr["agility"]))
    cp = hp / c["cp"]["hp_div"] + attack * aspd * crit_factor * c["cp"]["attack_weight"] + (defence + qi_res + soul_def) / c["cp"]["defence_div"]
    return {"level": lv, "might": round(m, 4), "attack": round(attack), "qi_attack": round(qi_attack), "max_hp": round(hp),
            "physical_defense": round(defence), "crit_chance": round(crit, 3), "crit_damage": round(crit_dmg, 3),
            "basic": round(basic), "technique": round(technique), "technique_crit": round(technique * crit_dmg),
            "dps": round(basic * crit_factor * swings * PAR["technique_share"]), "cp": round(cp),
            "armour_cut": round(cut(defence), 4)}


def par_block(families, origins):
    fam = next(f for f in families if f["id"] == PAR["family"])
    origin = next(o for o in origins if o["id"] == PAR["origin"])
    return dict(PAR, table=[par_row(lv, fam, origin) for lv in range(MIGHT["top_level"] + 1)])


def mob_tables(par):
    """A normal foe's HP and attack by Level from the par table (research §6.2 rules behind the monster columns)."""
    mob = CORE["mob"]
    hp, attack = [], []
    for row in par["table"]:
        lv = row["level"]
        if lv < PAR["from_level"]:
            hp.append(round(poly(mob["hp"], lv), 1))
            attack.append(round(poly(mob["attack"], lv), 1))
            continue
        hp.append(round(max(poly(mob["hp"], lv), PAR["hits"] * row["basic"])))
        share = [b for b in PAR["blow"] if lv >= b[0]][-1][1]
        attack.append(round(share * row["max_hp"] / (1 - row["armour_cut"])))
    return {"hp_table": hp, "attack_table": attack}


# The stat constants the par model (below) reads as the rules do; build() writes them into stats.json unchanged.
CORE = {
    "pools": {
        "hp": {"a": 50, "b": 20, "c": 0.9, "from_level": 0},
        "qi": {"a": 20, "b": 8, "c": 0.5, "from_realm": "bone_forging_7"},
        "soul": {"a": 100, "b": 10, "c": 0.4, "offset": 46, "from_realm": "spirit_awakening_1"},
    },
    "attributes": {"base": 5, "per_level": 1, "body_per_body_level": 1, "essence_per_purity_grade": 3,
                   "spirit_per_soul_points": 0.1, "insight_per_dao_tier": 2, "essence_per_capacity": 10},
    "attribute_effects": {
        "body": {"max_hp_pct": 0.01, "physical_defense": 0.5, "body_weapon_attack_pct": 0.003, "toxicity_tolerance": 0.1, "knockback_resistance": 0.002},
        "agility": {"move_speed_pct": 0.001, "attack_speed": 0.002, "crit_chance": 0.001, "accuracy": 1.0, "evasion": 0.5},
        "essence": {"max_qi_pct": 0.01, "qi_attack_pct": 0.005, "technique_cost": 0.001, "qi_resistance": 0.3, "qi_regen": 0.005},
        "spirit": {"max_soul_pct": 0.01, "soul_defense": 0.5, "soul_attack_pct": 0.005, "sense_radius_pct": 0.01, "will": 1.0, "tenacity": 0.002,
                   "crafting_perception": 0.001},
        "insight": {"insight_rate": 0.005, "mastery_gain": 0.003, "accuracy": 0.5, "crafting_control": 0.002},
        "fortune": {"drop_rate": 0.002, "coin_find": 0.003, "crit_chance": 0.0005},
    },
    "meridian_points_per_level": [{"from_level": 1, "points": 2}, {"from_level": 55, "points": 3}, {"from_level": 121, "points": 4}],
    "meridian_gates": {
        "body": {"25": {"stat": "max_hp", "op": "pct_add", "value": 0.05}, "50": {"flag": "knockback_immune_attacking"}, "100": {"flag": "survive_lethal"}},
        "agility": {"25": {"flag": "dodge_cooldown_20"}, "50": {"flag": "dodge_second_charge"}, "100": {"flag": "move_keeps_cultivate"}},
        "essence": {"25": {"flag": "first_technique_free"}, "50": {"flag": "flight_qi_20"}, "100": {"flag": "projectile_pierce"}},
        "spirit": {"25": {"flag": "sense_cost_25"}, "50": {"flag": "fear_immune_weaker"}, "100": {"flag": "soul_ignore_20"}},
        "insight": {"25": {"flag": "extra_reroll"}, "50": {"flag": "insight_sites_double"}, "100": {"flag": "extra_dao_effect"}},
    },
    "crit": {"base": 0.05, "per_agility": 0.001, "per_fortune": 0.0005, "cap": 0.75, "damage_base": 1.5, "damage_cap": 3.0,
             "tenacity_divisor": 4},
    "defence": {"k_flat": 100, "k_level": 15, "cap": 0.75},
    # P12 (research §6.3): Might carries the realm's power; the energy keeps a small edge on Qi and Soul damage only,
    # True Qi +1% for each purity grade better than 9.
    "qi_edge": {"none": 1.0, "body": 1.0, "primal_qi": 1.0, "true_qi": 1.10, "sage_qi": 1.15, "law_qi": 1.20, "monarch_qi": 1.25,
                "heavenforce": 1.30},
    "qi_edge_per_purity": 0.01,
    "technique_cost": {"per_level": 0.04, "composure_zero_factor": 1.5, "mastery_cost_per_tier": -0.05,
                       "mastery_damage_per_tier": 0.08, "dao_damage_per_tier": 0.05},
    "cp": {"hp_div": 10, "attack_weight": 0.5, "defence_div": 4},
    "equipment": {"weapon_attack": {"a": 8, "b": 3, "c": 0.12}, "armour_defence": {"a": 4, "b": 1.5, "c": 0.05},
                  "enhance_per_level": 0.05, "fist_weapon_pct": 0.6,
                  "slot_share": {"robe": 0.4, "trousers": 0.3, "boots": 0.15, "hat": 0.15},
                  "energy_type_penalty": 0.5},
    "mob": {"hp": {"a": 30, "b": 15, "c": 1.1}, "attack": {"a": 5, "b": 2.2, "c": 0.1}, "accuracy": {"a": 10, "b": 3},
            "evasion_pct": 0.3, "agile_evasion_pct": 0.6,
            # P12: a boss's plain blow takes 15% of par HP (x2.5 a normal foe's 6%); its health comes from its par time.
            "roles": {"normal": {"hp": 1, "attack": 1, "defence": 0.8}, "elite": {"hp": 6, "attack": 1.5, "defence": 1.2},
                      "field_boss": {"hp": 40, "attack": 2.5, "defence": 1.5}, "dungeon_boss": {"hp": 80, "attack": 2.5, "defence": 1.5},
                      "story_boss": {"hp": 20, "attack": 2.5, "defence": 1.2}, "event": {"hp": 0.4, "attack": 0.8, "defence": 0.5},
                      "trial": {"hp": 3, "attack": 0.7, "defence": 1.0}},
            "own_element_resistance": 0.3, "overcome_element_resistance": 0.15},
    # S48 technique grades: the base multiplier's bonus by grade.
    "technique_grades": {"common": 0.0, "earth": 0.10, "heaven": 0.20},
}
QUALITIES = {"flawed": {"mult": 0.8, "affixes": 0}, "common": {"mult": 1.0, "affixes": 0}, "fine": {"mult": 1.1, "affixes": 1},
             "superior": {"mult": 1.2, "affixes": 2}, "perfect": {"mult": 1.3, "affixes": 3}, "relic": {"mult": 1.35, "affixes": 3}}


def build():
    families = [
        {"id": "fists", "appearance": ["none"], "range": [0.9, 1.1], "hits_per_s": 1.4, "reach": 46, "crit": 0.05,
         "scales": ["body", "agility"], "guard": 0.30, "parry_s": 0.18, "dao": "fist", "hud_glyph": "fist",
         "third_hit_bonus": 0.2, "depth": 30, "altitude": [-30, 60],
         "combo": [{"action": "punch_1", "duration": 0.42, "hit_at": 0.2, "mult": 1.0},
                   {"action": "punch_2", "duration": 0.45, "hit_at": 0.22, "mult": 1.0},
                   {"action": "punch_3", "duration": 0.55, "hit_at": 0.28, "mult": 1.2, "knockback": 20}]},
        {"id": "gauntlets", "appearance": ["none"], "range": [0.9, 1.1], "hits_per_s": 1.4, "reach": 50, "crit": 0.05,
         "scales": ["body", "agility"], "guard": 0.30, "parry_s": 0.18, "dao": "fist", "hud_glyph": "fist",
         "third_hit_bonus": 0.2, "depth": 30, "altitude": [-30, 60],
         "combo": [{"action": "punch_1", "duration": 0.42, "hit_at": 0.2, "mult": 1.0},
                   {"action": "punch_2", "duration": 0.45, "hit_at": 0.22, "mult": 1.0},
                   {"action": "punch_3", "duration": 0.55, "hit_at": 0.28, "mult": 1.2, "knockback": 20}]},
        {"id": "jian", "appearance": ["sword"], "range": [0.85, 1.15], "hits_per_s": 1.1, "reach": 78, "crit": 0.03,
         "scales": ["agility", "essence"], "guard": 0.40, "parry_s": 0.25, "dao": "sword", "hud_glyph": "jian", "depth": 30,
         "altitude": [-30, 60], "qi_arc_discount": 0.1,
         "combo": [{"action": "swing_1", "duration": 0.55, "hit_at": 0.26, "mult": 1.0},
                   {"action": "swing_2", "duration": 0.6, "hit_at": 0.28, "mult": 1.05},
                   {"action": "swing_3", "duration": 0.72, "hit_at": 0.36, "mult": 1.25, "knockback": 20}]},
        {"id": "spear", "appearance": ["spear"], "range": [0.8, 1.2], "hits_per_s": 0.9, "reach": 116, "crit": 0.0,
         "scales": ["body", "agility"], "guard": 0.35, "parry_s": 0.18, "dao": "spear", "hud_glyph": "spear", "depth": 26,
         "altitude": [-30, 60], "penetration": 0.10, "line_targets": 2,
         "combo": [{"action": "thrust_1", "duration": 0.6, "hit_at": 0.3, "mult": 1.0},
                   {"action": "thrust_2", "duration": 0.65, "hit_at": 0.32, "mult": 1.05},
                   {"action": "thrust_3", "duration": 0.8, "hit_at": 0.42, "mult": 1.3, "knockback": 40}]},
        {"id": "short_blade", "appearance": ["dagger"], "range": [0.7, 1.3], "hits_per_s": 1.3, "reach": 52, "crit": 0.10,
         "scales": ["agility", "fortune"], "guard": 0.25, "parry_s": 0.15, "dao": "blade", "hud_glyph": "short_blade", "depth": 28,
         "altitude": [-30, 60], "backstab": 1.5,
         "combo": [{"action": "thrust_1", "duration": 0.42, "hit_at": 0.2, "mult": 1.0},
                   {"action": "thrust_2", "duration": 0.45, "hit_at": 0.22, "mult": 1.0},
                   {"action": "thrust_3", "duration": 0.55, "hit_at": 0.3, "mult": 1.2}]},
        {"id": "staff", "appearance": ["staff"], "range": [0.9, 1.1], "hits_per_s": 0.8, "reach": 96, "crit": 0.0,
         "scales": ["body", "essence"], "guard": 0.50, "parry_s": 0.20, "dao": "staff", "hud_glyph": "staff", "depth": 32,
         "altitude": [-30, 60], "knockback_every_hit": 30, "qi_attack_bonus": 0.1,
         "combo": [{"action": "thrust_1", "duration": 0.66, "hit_at": 0.34, "mult": 1.0, "knockback": 30},
                   {"action": "thrust_2", "duration": 0.7, "hit_at": 0.36, "mult": 1.05, "knockback": 30},
                   {"action": "thrust_3", "duration": 0.85, "hit_at": 0.45, "mult": 1.3, "knockback": 60}]},
        # S47 v1.1: the heavy sabre (fills the Blade Dao beside the short blade): slow, a cleave that hits three, and
        # an edge that breaks armour.
        {"id": "heavy_sabre", "appearance": ["sabre"], "range": [0.8, 1.25], "hits_per_s": 0.75, "reach": 92, "crit": 0.04,
         "scales": ["body", "agility"], "guard": 0.45, "parry_s": 0.18, "dao": "blade", "hud_glyph": "sabre", "depth": 34,
         "altitude": [-30, 60], "line_targets": 3, "armour_break": {"chance": 0.3, "duration_s": 4},
         "combo": [{"action": "swing_1", "duration": 0.72, "hit_at": 0.36, "mult": 1.1},
                   {"action": "swing_2", "duration": 0.78, "hit_at": 0.38, "mult": 1.15},
                   {"action": "swing_3", "duration": 0.95, "hit_at": 0.5, "mult": 1.5, "knockback": 40, "armour_break": 1.0}]},
        # The fan: mid-range wind, and on the third stroke a returning throw that lifts what it strikes.
        {"id": "fan", "appearance": ["fan"], "range": [0.85, 1.15], "hits_per_s": 1.1, "reach": 140, "crit": 0.05,
         "scales": ["agility", "insight"], "guard": 0.3, "parry_s": 0.2, "dao": "fan", "hud_glyph": "fan", "depth": 36,
         "altitude": [-30, 80], "line_targets": 2,
         "combo": [{"action": "swing_1", "duration": 0.5, "hit_at": 0.24, "mult": 1.0},
                   {"action": "swing_2", "duration": 0.55, "hit_at": 0.26, "mult": 1.0},
                   {"action": "swing_3", "duration": 0.7, "hit_at": 0.34, "mult": 1.2,
                    "throw": {"speed": 520, "range": 280, "art": "fan", "knockup_s": 0.8}}]},
        # The flute (the Music path): a note flies at the tap; hold Attack to channel a melody aura that slows and
        # confuses foes near you and heals your allies, paid for in Composure.
        {"id": "flute", "appearance": ["flute"], "range": [0.9, 1.1], "hits_per_s": 1.0, "reach": 240, "crit": 0.03,
         "scales": ["insight", "essence"], "guard": 0.25, "parry_s": 0.15, "dao": "music", "hud_glyph": "flute", "depth": 30,
         "altitude": [0, 90], "ranged": True, "projectile_speed": 460, "projectile_art": "note", "damage_type": "qi",
         "channel": {"radius": 220, "tick_s": 0.5, "composure_per_s": 8, "hold_s": 0.35, "slow": {"power": 0.3, "duration_s": 1.2},
                     "confusion_chance": 0.08, "confusion_s": 1.5, "ally_heal_pct": 0.02, "self_heal_pct": 0.01,
                     "move_factor": 0.5, "min_composure": 5},
         "combo": [{"action": "attack", "duration": 0.6, "hit_at": 0.3, "mult": 0.9, "projectile": "note"}]},
        # v1.2 the brush (the Brush Dao): a scholar's writing brush, quick and short, striking with Qi. Each technique
        # used with it writes a talisman onto what it strikes, by the technique's element (one per foe, 4 s).
        {"id": "brush", "appearance": ["brush"], "range": [0.9, 1.1], "hits_per_s": 1.2, "reach": 110, "crit": 0.06,
         "scales": ["insight", "agility"], "guard": 0.3, "parry_s": 0.2, "dao": "brush", "hud_glyph": "brush", "depth": 32,
         "altitude": [-30, 70], "damage_type": "qi",
         "talisman": {"duration_s": 4.0, "by_element": {
             "fire": {"id": "burn", "power": 0.006}, "water": {"id": "slow", "power": 0.3}, "wood": {"id": "root", "power": 1, "duration_s": 1.5},
             "metal": {"id": "sundered", "power": 1}, "earth": {"id": "vulnerable", "power": 1}, "thunder": {"id": "shock", "power": 1, "duration_s": 0.6},
             "wind": {"id": "slow", "power": 0.2}, "none": {"id": "qi_seal", "power": 1, "duration_s": 2.0}}},
         "combo": [{"action": "swing_1", "duration": 0.46, "hit_at": 0.22, "mult": 0.95},
                   {"action": "swing_2", "duration": 0.5, "hit_at": 0.24, "mult": 1.0},
                   {"action": "swing_3", "duration": 0.62, "hit_at": 0.3, "mult": 1.25}]},
        # v1.2 the bell (the Music Dao): a Warden's hand-bell. Its strikes ring out on both sides; it supports more than
        # it harms (soul damage, a light touch).
        {"id": "bell", "appearance": ["bell"], "range": [0.9, 1.1], "hits_per_s": 0.9, "reach": 160, "crit": 0.02,
         "scales": ["essence", "insight"], "guard": 0.35, "parry_s": 0.2, "dao": "music", "hud_glyph": "bell", "depth": 60,
         "altitude": [-30, 90], "damage_type": "soul", "ring": True, "line_targets": 6,
         "combo": [{"action": "swing_1", "duration": 0.6, "hit_at": 0.3, "mult": 0.7},
                   {"action": "swing_2", "duration": 0.6, "hit_at": 0.3, "mult": 0.7},
                   {"action": "swing_3", "duration": 0.75, "hit_at": 0.38, "mult": 0.95}]},
        {"id": "bow", "appearance": ["bow"], "range": [0.75, 1.25], "hits_per_s": 0.9, "reach": 480, "crit": 0.05,
         "scales": ["agility", "insight"], "guard": 0.0, "parry_s": 0.0, "dao": "bow", "hud_glyph": "bow", "depth": 26,
         "altitude": [20, 110], "ranged": True, "projectile_speed": 620,
         "combo": [{"action": "bow", "duration": 1.1, "hit_at": 0.55, "mult": 1.0, "projectile": "arrow"}]},
    ]
    # S47 weapon awakening (v1.1): a +10 weapon of Heaven grade or better, awakened at a forge, strikes on its own every
    # so many blows (a legend has its own skill instead). Bare fists have no weapon to awaken.
    awakened = {
        "gauntlets": {"name": "Thunder Knuckles", "every_hits": 12, "mult": 1.8, "damage_type": "physical", "element": "earth", "shape": "ring", "reach": 150},
        "jian": {"name": "Sword Light", "every_hits": 12, "mult": 1.8, "damage_type": "qi", "element": "metal", "art": "flying_sword", "reach": 320},
        "spear": {"name": "Piercing Light", "every_hits": 12, "mult": 2.0, "damage_type": "physical", "element": "metal", "art": "flying_sword", "reach": 360},
        "short_blade": {"name": "Shadow Twin", "every_hits": 10, "mult": 1.4, "damage_type": "physical", "element": "none", "art": "flying_sword", "reach": 280},
        "staff": {"name": "Sweeping Gale", "every_hits": 12, "mult": 1.8, "damage_type": "physical", "element": "wind", "shape": "ring", "reach": 170},
        "heavy_sabre": {"name": "Cleaving Wave", "every_hits": 14, "mult": 2.4, "damage_type": "physical", "element": "metal", "art": "sand_crescent", "reach": 300},
        "fan": {"name": "Gale Leaf", "every_hits": 12, "mult": 1.8, "damage_type": "qi", "element": "wind", "art": "sand_crescent", "reach": 320},
        "flute": {"name": "Echoing Note", "every_hits": 12, "mult": 1.6, "damage_type": "soul", "element": "none", "art": "note", "reach": 320},
        "brush": {"name": "Flying Script", "every_hits": 12, "mult": 1.7, "damage_type": "qi", "element": "none", "art": "sand_crescent", "reach": 300},
        "bell": {"name": "Resounding Peal", "every_hits": 12, "mult": 1.3, "damage_type": "soul", "element": "none", "shape": "ring", "reach": 220},
        "bow": {"name": "Twin Arrow", "every_hits": 10, "mult": 1.2, "damage_type": "physical", "element": "none", "art": "arrow", "reach": 420, "count": 2},
    }
    for f in families:
        if f["id"] in awakened: f["awakened"] = awakened[f["id"]]
    entries("weapon_families.json", families)

    # B10: each origin has its name and a line for the creator (the id showed as "Fishers Child", no description).
    origins = [
        {"id": "fishers_child", "name": "Fisher's Child", "bonus": {"body": 3, "essence": 2}, "element_nudge": "water",
         "desc": "Raised among the river's fishing boats: +3 Body and +2 Essence, and a leaning toward water."},
        {"id": "scholars_heir", "name": "Scholar's Heir", "bonus": {"insight": 5}, "element_nudge": "",
         "desc": "Heir to a house of books and ink: +5 Insight."},
        {"id": "temple_foundling", "name": "Temple Foundling", "bonus": {"spirit": 5}, "element_nudge": "",
         "desc": "Left at a temple gate and raised on its chants: +5 Spirit."},
        {"id": "smiths_apprentice", "name": "Smith's Apprentice", "bonus": {"body": 3, "insight": 2}, "element_nudge": "metal",
         "desc": "Raised at the forge's bellows: +3 Body and +2 Insight, and a leaning toward metal."},
    ]
    entries("origins.json", origins)

    par = par_block(families, origins)
    write("stats.json", {
        "might": might_block(),
        "par": par,
        **CORE,
        "mob": dict(CORE["mob"], **mob_tables(par)),
        "regen_per_s": {"hp": 0.005, "qi": 0.0075, "soul": 0.00375, "combat_delay_s": 5, "meditate_mult": 8, "rest_mult": 4},
        "move": {"base": 205, "sprint": 1.7, "sprint_after_s": 2.0, "cap_pct": 0.4, "attack_factor": 0.3, "guard_factor": 0.5,
                 "shallows_factor": 0.7},
        # S14 binding (Spirit Awakening 3): a found relic's stats stay sealed until it is bound (a channel by
        # grade, broken by a hit); its Artifact Spirit wakes through a soul contest (Spirit against strength).
        "binding": {"unlock": "binding", "seconds": {"plain": 4, "common": 6, "earth": 12, "heaven": 20, "mystic": 30},
                    "spirit_chance": [0.1, 0.9], "spirit_cooldown_s": 60, "soul_injury": 1},
        # S47 Artifact Spirit depth (v1.0). Affinity 0-100 grows by use (a point per 25 hits landed with the relic in
        # hand) and gifts (3 a day; the favourite counts double); at 30 the spirit will answer a contest at its own
        # resting place. Affinity raises the spirit's gift and skill by up to half again. Devouring weaker gear of the
        # same family grows the spirit (levels 1-5, +10% each). Below its control demand in Spirit, an awake spirit
        # gives half its gift and no skill (it refuses a weak owner).
        "artifact_spirit": {"hits_per_point": 25, "gifts": {"refining_essence": 10, "cloudsteel_ore": 4, "jadeiron": 2, "mist_lotus": 6},
                            "favourite_mult": 2, "gifts_per_day": 3, "wake_affinity": 30, "affinity_bonus": 0.5,
                            "devour_xp": {"plain": 2, "common": 4, "earth": 8, "heaven": 16}, "devour_affinity": 2,
                            "levels": [10, 30, 60, 100, 150], "per_level": 0.1, "weak_share": 0.5,
                            "bark_cooldown_s": 40, "kill_bark_chance": 0.25, "low_hp_pct": 0.25},
        # Natural treasures (Part 5, Spirit Awakening 8): the Evergreen Heart Tree bears its first fruit a day
        # after planting, then one per season; the Nine-Bough Jade Tree gives a share of the strongest Dao's
        # gap to its next tier (at least `min_insight`), once per realm stage, only at an Understanding bottleneck.
        "treasures": {"unlock": "natural_treasures", "season_days": 7, "first_fruit_h": 24, "fruit_invuln_s": 3,
                      "jade_tree_share": 0.75, "jade_tree_min_insight": 500},
        # S18 flight (Cloud Stride 1): QI per second is a share of the pool (with a floor); take off needs a
        # little QI in hand. Climb in px/s, ceiling in px of altitude.
        "flight": {"unlock": "flight", "qi_pct_per_s": 0.02, "qi_min_per_s": 2.0, "start_qi_pct": 0.1, "climb": 220, "ceiling": 340,
                   "no_flight_types": ["interior", "sect", "dungeon"]},
        # S18: A_dealt = min(cap, floor + slope x attunement / required); A_taken = 1 + max(0, 1 - attunement / required)
        "attunement": {"floor": 0.3, "slope": 0.7, "cap": 1.1},
        "hit": {"base": 1.1, "k": 0.35, "floor": 0.55, "cap": 1.0},
        "realm_gap": {"up_per_realm": 0.25, "up_cap": 1.0, "down_per_realm": 0.20, "down_max_reduction": 0.60},
        # P12 (research §6.3 and technique_plan §6.2): a share of the target's health (poison, burns and the like) takes
        # at most this much of the caster's attack a second from an elite or a boss.
        "hp_share_cap": {"attack_per_s": 0.6, "roles": ["elite", "field_boss", "dungeon_boss", "story_boss"]},
        "kill_gap_factor": [{"min_diff": 5, "mult": 1.2}, {"min_diff": -4, "mult": 1.0}, {"min_diff": -9, "mult": 0.5},
                            {"min_diff": -999, "mult": 0.1}],
        # S47: the flying sword's palms, Sword Intent and self-detonation.
        "sword_release": {"palm_mult": 0.8},
        # S47 the sword swarm (v1.1): 3 swords at Sword Dao 5, 9 with the Nine Swords Array, 36 at Original Application
        # with it; one sword for each 10 Spirit (control demand). They strike in turn; each hits softer the more there are.
        "sword_swarm": {"counts": [3, 9, 36], "spirit_per_sword": 10, "duration_s": 12.0, "strike_every_s": 1.2, "mult_total": 0.9,
                        "seek_radius": 420, "orbit": 46},
        "sword_intent": {"max": 10, "fade_s": 3.0, "pen_per_stack": 0.01, "fear_chance": 0.1},
        "detonation": {"base": 1.5, "per_grade": 0.75, "radius": 180},
        "natal": {"per_level": 0.02, "xp_levels": [50, 200, 450, 800, 1250, 1800, 2450, 3200, 4050, 5000], "xp_per_ore": 20,
                  "xp_per_kill_level": 1.0, "xp_per_technique": 2.0, "demand_base": 10, "demand_per_level": 5,
                  "overcharge_chance": 0.05},
        "combat": {"hitstop": 0.05, "hitstop_crit": 0.1, "knockback_light": 20, "knockback_heavy": 80, "flinch_pct": 0.2,
                   "flinch_s": 0.4, "leash": 600, "shrine_sanctuary": 240, "sight_depth": 100, "sight_aggro_cap": 2, "threat_heal": 1.5, "spawn_protection_s": 1.5, "depth_band": 26,
                   "auto_turn_range": 160, "backlash_stun_s": 1.0, "backlash_qi_pct": 0.05, "dodge_distance": 140, "wind_blink_distance": 120, "wind_blink_cooldown_s": 10,
                   "dodge_invuln_s": 0.25, "dodge_cooldown_s": 2.5, "parry_stagger_s": 0.8, "parry_stagger_boss_s": 0.3,
                   "combo_window_s": 0.5, "steadfast_s": 8, "vulnerable": 0.2, "shock": 0.2, "status_duration_tenacity": 0.5},
        "death": {"progress_loss": 0.10, "wake_hp": 0.5, "talisman_hp": 0.3, "talisman_invuln_s": 5, "talisman_cooldown_s": 300},
        "toxicity": {"tolerance_base": 30, "drain_per_min": 1, "meditate_drain_mult": 2, "repeat_window_s": 300,
                     "repeat_factor": 0.5},
        # S28 Hollow Tide: held under half in the valley and the Expanse; the Lantern Star Field lets it fill. At half the
        # burden starts (techniques cost more, Composure drains); at full the seizure (control lost, allies turn, back to 80).
        "hollowing": {"valley_cap": 49, "decay_per_min": 1, "meditate_mult": 3, "zone_caps": {"lantern_star_field": 100},
                      "burden_at": 50, "cost_mult": 1.25, "composure_drain_per_s": 2.0,
                      "seizure_at": 100, "seizure_s": 3.0, "turn_s": 10.0, "after_seizure": 80, "lantern_mult": 4},
        # Gap report G1 · what pills cost over a life. An accumulation pill works at 1 / (1 + 0.25 x doses of its
        # family); every major breakthrough forgets one dose. A support pill stops helping a breakthrough after
        # two failed attempts at it. Above 30% of a great realm's QP from pills the foundation is hollow; 5% of
        # toxicity stays as residue (-1% accumulation per 10, at most -10%). Settle foundation drains both.
        "pill_life": {"resistance_step": 0.25, "support_fail_limit": 2, "hollow_share": 0.30, "settle_show_share": 0.20, "residue_share": 0.05,
                      "residue_step": 10, "residue_step_pct": 0.01, "residue_cap_pct": 0.10,
                      "settle_share_per_h": 0.05, "settle_residue_per_h": 5, "doses_per_count": 5},
        # The heart-demon meter (S48): 25 points are one risk step at a major breakthrough and one more Heart Demon
        # at the Reflection. +1 per 10 sin; meditation drains 1 per 5 minutes; passing the Heart Trial clears 30.
        "heart_demon": {"step": 25, "method_switch": 10, "forced_breakthrough": 5, "forced_supports": 2, "death": 3,
                        "per_sin": 0.1, "meditate_drain_per_min": 0.2, "heart_trial": -30},
        # S48 named roots (shown on the Aptitude tab once elements are revealed, Bone Forging 7): an element counts at
        # +5% or more. Mutated when the strongest counting element is Thunder, Ice or Wind; Heavenly when exactly one
        # element is above +10%; Mixed with 4 or more counting; True with 2-3; Faint otherwise.
        "roots": {"counts_at": 0.05, "heavenly_above": 0.10, "mutated": ["thunder", "ice", "wind"], "mixed_from": 4, "true_from": 2},
        # S48 Core Forging (Heart Tempering 9 -> Cloud Stride 1): each preparation point met counts at 80% on the
        # breakthrough stream; the starting purity grade is 9 minus the points counted, floor 5; a flawless Heaven's
        # Cleansing is one more point, floor 4. The Heavenly Flame Pill counts within an hour of taking it.
        "core_forging": {"start": 9, "chance": 0.8, "floor": 5, "flawless_floor": 4, "pill": "heavenly_flame_pill", "pill_window_s": 3600,
                         "yin_times": ["evening", "night"], "yang_times": ["morning", "day"]},
        # S48 epiphany: a rare flash while insight comes in (Contemplate or varied combat): 0.2% a tick, weighted by
        # Insight; 60 s at five times the insight, a chance of a free mastery step, then 2 hours of play before another.
        "epiphany": {"chance": 0.002, "insight_weight": 0.01, "buff_s": 60, "insight_mult": 5.0, "mastery_chance": 0.25, "cooldown_s": 7200,
                     "contexts": ["contemplate", "insight_stone", "tech", "kill"]},
        # S48 Killing Intent: +1 a kill within 10 s of the last, up to 10, +1% crit each; at 10, weaker foes nearby hesitate.
        # S28 v1.2 Presence (Will Manifest 1): Pressure = (5 + Level) x (1 + per_level x Presence level) + the pressure stat;
        # a foe's Will = (5 + its Level) x its role's factor. Experience from holding it over pressed foes (x2 in a clash)
        # and from kills made while they are pressed; levels 1-10 at these totals.
        "presence": {"per_level": 0.06, "radius_base": 220, "radius_per_level": 12, "soul_per_s_pct": 0.0025,
                     "role_will": {"normal": 1.0, "elite": 1.15, "boss": 1.3},
                     "xp_per_s": 1.0, "clash_xp_mult": 2.0, "kill_xp": 3.0,
                     "xp_levels": [0, 60, 150, 280, 450, 660, 910, 1200, 1530, 1900]},
        # S28 v1.2 the Sphere (Sphere Lord 1): a circle of the strongest combat Dao's element. It costs Qi while held,
        # works on the foes inside once a second, feeds techniques of its element (or the element it generates) by a
        # tenth, and meets a foe's Sphere where they overlap: the weaker one breaks (a meridian injury for the player).
        # v1.2 Phase D · the Copperjaw Beetle swarm (the Copperjaw Box): fed ore, it grows by the hour online or off;
        # released, it chews every foe near you for 8 s, harder the bigger it is (log of the population). Wood resists.
        "swarm": {"start_pop": 50, "min_pop": 50, "max_pop": 5000, "growth_per_h": 0.08, "shrink_per_h": 0.02, "food_per_h": 1,
                  "queen_chance_per_h": 0.01, "queen_growth": 1.5, "queen_bite": 1.25, "bite_k": 0.12, "radius": 220,
                  "duration_s": 8, "tick_s": 1.0, "cooldown_s": 30, "wood_factor": 0.5, "max_settle_h": 720,
                  "ore_food": {"copper_ore": 1, "riverstone": 2, "jadeiron": 3, "cloudsteel_ore": 4, "mystic_ore": 5,
                               "stormsteel_ore": 6, "sunglass_ore": 7, "driftglass": 8, "drone_shell": 10}},
        "sphere": {"qi_per_s_pct": 0.004, "radius_base": 160, "radius_per_tier": 20, "tier6_radius": 40, "power_per_tier": 0.08,
                   "tier6_power": 0.1, "fed_bonus": 0.1, "break_cooldown_s": 30, "injury_severity": 1, "pet_bonus": 0.1, "tick_s": 1.0,
                   "foe_loss": 0.1,
                   # A weapon Dao's Sphere takes the weapon's nature; the jian's Sword Dao is the Sword Domain.
                   "dao_element": {"sword": "sword", "blade": "metal", "spear": "metal", "fist": "earth", "staff": "earth",
                                   "bow": "wind", "fan": "wind", "music": "soul", "space": "space"},
                   "elements": {
                       "water": {"slow": 0.2, "terrain": {"water": {"slow": 0.35, "freeze": True}}},
                       "fire": {"burn_pct": 0.01, "terrain": {"grass": {"burn_pct": 0.02}}},
                       "earth": {"vulnerable": True, "terrain": {"stone": {"root_s": 0.5}}},
                       "wood": {"regen_pct": 0.01, "terrain": {"grass": {"regen_pct": 0.015}}},
                       "metal": {"cut_pct": 0.12},
                       "sword": {"cut_pct": 0.18, "domain": True},
                       "wind": {"speed": 0.15},
                       "thunder": {"shock_pct": 0.4, "shock_every": 2},
                       "soul": {"will_down": 0.15},
                       "space": {"pen": 0.15},
                       "star": {"cut_pct": 0.1, "crit": 0.05}}},
        "sect_master": {"stipend": 300},   # v1.2 S20: contribution a day for the seat
        "killing_intent": {"window_s": 10.0, "max": 10, "crit_per_stack": 0.01, "hesitate_s": 0.5, "radius": 520},
        # S48 the Poison Body (v1.1): past half your toxicity tolerance, a known poison art turns each hit's toxicity
        # into poison on the foe (one point a hit, at most once per foe per half second).
        "poison_body": {"threshold": 0.5, "toxicity_per_hit": 1.0, "power": 0.02, "duration_s": 4.0, "per_foe_s": 0.5},
        # S10 meridian gates: a fight begins after this long without a blow (Essence 25: its first technique is free).
        # S48 paths as layers (v1.1). The Blood path is an opt-in for the demonic side: techniques paid in blood,
        # lifesteal by the Blood Dao, a blood-essence meter fed by kills that pays those costs first, a doubled heart
        # demon, and the orthodox sect's regard falling. The Buddhist path: merit milestones calm the heart for
        # vow-keepers, and healing an ally is merit (a few times a day).
        "paths": {"blood": {"min_realm": "heart_tempering_1", "alignment_at_most": -20, "take_alignment": -10, "take_reputation": -20,
                            "use_reputation": -1, "leave_heart_demon": 10, "heart_demon_mult": 2.0, "lifesteal_base": 0.03,
                            "lifesteal_per_tier": 0.01, "blood_art_lifesteal_mult": 2.0, "essence_kill": 10, "essence_elite": 25,
                            "essence_boss": 50, "essence_max": 100, "essence_decay_after_s": 20.0, "essence_decay_per_s": 2.0},
                  "buddhist": {"merit_milestone": 100, "milestone_heart_demon": -10, "heal_ally_daily": 5},
                  # v1.2 the Confucian path (S48): the upright's written word. Righteous Qi +25% against Hollow and demonic foes.
                  "confucian": {"min_realm": "will_manifest_2", "alignment_at_least": 20, "take_alignment": 5, "leave_heart_demon": 10,
                                "righteous": 0.25}},
        "gates": {"fight_gap_s": 8.0, "sense_cost_mult": 0.75, "flight_qi_mult": 0.8, "soul_ignore": 0.2, "insight_site_mult": 2.0},
        # S48 nascent-soul escape: from Sage a grave wound costs 5% of the stage instead of 10%.
        "soul_escape": {"from": "sage_1", "progress_loss": 0.05},
        # S48 false realm: Concealment can show a realm up to two great realms lower.
        "false_realm": {"max_steps": 2},
        # Bandit ambushes on the roads (S48): the chance per entry, x2 while a false realm shows, never past `reach`
        # levels above the gang, and a cooldown between them.
        "ambush": {"chance": 0.06, "concealed_mult": 2.0, "reach": 8, "cooldown_s": 900, "offset": 360},
        "qi_deviation": {"duration_s": 600, "elements": ["water", "wood", "fire", "earth", "metal"]},
        # S48 body ladder: body techniques spend HP when QI is short (Copper Body), never below this share; P12: the same
        # share of max HP as the share of max QI the technique costs (Might scales HP, not QI).
        "body_path": {"hp_share_per_qi_share": 1.0, "hp_floor": 0.2, "air_metre_px": 50},
        # S17 hazards: below the answer an effect falls off to half; answered, pushes and statuses stop
        # and a strike still deals this share of its damage.
        "hazard": {"partial": 0.5, "answered_damage": 0.35, "shelter_radius": 220, "flyer_push": 1.5},
        "composure": {"max": 100, "recover_per_s": 10, "recover_delay_s": 3, "meditate_full_s": 5},
        "grade_bands": [["plain", 1, 9], ["common", 10, 18], ["earth", 19, 36], ["heaven", 37, 54], ["mystic", 55, 63],
                        ["spirit", 64, 72], ["sage", 73, 81], ["sovereign", 82, 90], ["will", 91, 99], ["sphere", 100, 108],
                        ["law", 109, 120], ["monarch", 121, 140], ["inner_heaven", 141, 165]],
        "stats": [{"id": s, "group": g, "cap": cap, "format": f} for (s, g, cap, f) in STAT_LIST],
    })

    # S43 traversal: every movement constant in one place. The solver's constants must match these
    # (data_validation checks it), and the room lint and reach tests read them.
    write("movement.json", {
        "schema_version": 1,
        "jump": {"impulse": 530, "gravity": 1150, "substep_s": 1 / 120, "apex": 122, "coyote_s": 0.10, "buffer_s": 0.12},
        "double_jump": {"impulse": 430, "apex_from_ground": 202},
        "wall_step": {"kick_speed": 450, "away": 90, "kicks": 3, "reach": 12, "shaft": [60, 160]},
        "mantle": {"rise": 24, "reach": 16, "time_s": 0.2},
        "drop_through": {"ignore_s": 0.25, "axis_y": 0.7, "axis_x": 0.3},
        "climb": {"speed": 160, "stat_cap": 0.5, "hold_s": 0.3, "reach": 28, "sideways_max": 0.3, "rope_jump_bonus": 0.2},
        "plunge": {"speed": 900, "radius": 60, "mult": 1.2, "stun_s": 0.5, "cooldown_s": 4.0},
        "glide": {"fall": 120, "drift": 1.1, "qi_per_s": 2.0},
        "air_dash": {"distance": 140, "hold_s": 0.25},
        "dodge": {"distance": 140, "invuln_s": 0.25, "cooldown_s": 2.5},
        "sprint": {"factor": 1.7, "after_s": 2.0},
        "attack_move": {"ground": 0.3, "air": 0.8, "air_mult": 1.1},
        "falls": {"void_below_lowest": 250, "hp_cost_pct": 0.05, "safe_after_s": 0.3, "safe_edge": 24, "fade_s": 0.3},
        "water": {"shallow_factor": 0.7, "swim_factor": 0.6, "sink_factor": 0.3, "sink_s": 1.0, "sink_depth": 40, "swim_s": 30,
                  "skim_min_speed": 60, "skim_still_s": 0.5},
        "updraft": {"speed": 220, "ease": 3.0},
        "wind": {"cycle_s": 4.0, "strong_s": 1.5, "calm": 0.3, "edge": 48, "edge_factor": 1.5},
        "bounce": {"speed": 700, "apex": 213},
        "crumble": {"break_s": 0.8, "return_s": 5.0},
        "combat_bands": {"melee": [-30, 60], "qi_arc": [-10, 80], "projectile_launch": 58},
        "heights": {"jump_one": 100, "jump_two": 176, "flight_ledge": 300, "blocks": [40, 60, 80, 110], "built": 88, "natural": 100},
        "flight": {"ceiling": 340, "climb": 220},
        # S43 rule 13: room cameras follow the support, lead by a quarter of the velocity, settle in 0.4 s.
        "camera": {"look_ahead": 0.25, "y_min": 180, "y_max": 600, "settle_s": 0.4, "fall_follow": 100, "look_down": 60,
                   "look_down_after_s": 0.5, "look_down_drop": 150},
        # Each movement art, the secret art that grants it and the realm band that first has it (S43 rule 7).
        "arts": [
            {"art": "jump", "realm": "prologue"}, {"art": "climb", "realm": "prologue"}, {"art": "drop_through", "realm": "prologue"},
            {"art": "mantle", "realm": "prologue"}, {"art": "sprint", "realm": "prologue"},
            {"art": "plunge", "secret_art": "plunge", "realm": "bone_forging_4"},
            {"art": "dodge", "secret_art": "dodge_dash", "realm": "bone_forging_5"},
            {"art": "glide", "secret_art": "falling_leaf_glide", "realm": "qi_kindling_3"},
            {"art": "air_dash", "secret_art": "swallow_dart", "realm": "qi_kindling_7"},
            {"art": "double_jump", "secret_art": "cloud_ladder_step", "realm": "qi_unfurling_6"},
            {"art": "water_skimming", "secret_art": "water_skimming", "realm": "qi_unfurling_8"},
            {"art": "wall_step", "secret_art": "wall_step", "realm": "heart_tempering_4"},
            {"art": "flight", "realm": "cloud_stride_1"},
        ],
    })

    # S38 balance simulator: how an active hour is spent, and the Part 4 pacing table it must meet (±15%).
    write("balance.json", {
        "schema_version": 1,
        # A normal mixed session (S29 "about 100 QP per active minute" with quests): the rest is travel,
        # dialogue, crafting, shops and the sect, which earn no realm progress themselves.
        "mix": {"fight": 0.35, "meditate": 0.25, "other": 0.4},
        "kills_per_min": 6,
        "dailies_per_hour": 1.0,
        # Active minutes an optional side quest costs on top of the mixed session (guided and main quests
        # lie on the path the session already walks).
        "quest_minutes": {"side": 10},
        "prologue_hours": 0.5,
        "stability": "stable",
        # Where a mixed session sits to cultivate: mostly the field rooms it fights in (1.0), sometimes Lu's
        # boat (1.4), the mentor's peak (1.6) or, later, a hidden spring (2.2).
        "density": {"bone_forging": 1.2, "qi_kindling": 1.25, "qi_unfurling": 1.3, "heart_tempering": 1.4, "cloud_stride": 1.4,
                    "spirit_awakening": 1.45, "heaven_glimpse": 1.5, "sage": 1.6},
        "method": {"bone_forging": "riverbreath_fragment", "qi_kindling": "jade_current_scripture", "qi_unfurling": "jade_current_scripture",
                   "heart_tempering": "cloudpiercing_canon", "cloud_stride": "willow_breath_art", "spirit_awakening": "willow_breath_art",
                   "heaven_glimpse": "tidal_sovereign_scripture", "sage": "tidal_sovereign_scripture"},
        "tolerance": 0.15,
        # S39 checks: [Level, the next upgrade, the spec's taels per hour there]; affordable within 1-2 h (±25%).
        "upgrades": [[15, "iron_jian", 850], [25, "jadeiron_robe", 1700]], "afford_hours": [0.75, 2.5],
        "act_end": "heaven_glimpse_3", "act_end_hours": 65,
        # P12 (research §6.2, §6.7 check 1): the par character's basic and technique hits (before crits) at these Levels;
        # the par character built with the real rules must land within ±15% and ±20%. Level 120 waits for v1.3's
        # weapons (a Will-grade jian carries the energy penalty there).
        "par_targets": {"1": [12, 12], "10": [68, 63], "30": [832, 1246], "60": [11000, 39500], "80": [41500, 154000],
                        "99": [136000, 527000], "108": [246000, 999000]},
        "par_tolerance": [0.15, 0.20],
        # Act II so far (v1.1 phases A-B reach Sage 3): the sim plays on to this stage.
        "sim_end": "sage_sovereign_1",
        "pacing": [["bone_forging_1", 0.5], ["qi_kindling_1", 5], ["qi_unfurling_1", 13], ["heart_tempering_1", 20],
                   ["cloud_stride_1", 30], ["spirit_awakening_1", 42], ["heaven_glimpse_1", 55], ["sage_1", 70], ["sage_sovereign_1", 110]],
        # P7b (item_plan §4.4): the equipment an hour of hunting drops, by grade (balance_sim `_drops`): each target is
        # [value, tolerance]; every region at least `region_floor`; each archetype's usable share inside `usable_share`;
        # an archetype set's slowest drop piece within `set_hours` of its band's hunting hours (`band_hours` × the fight share).
        "drops": {"kills_per_hour": 360, "elite_kills_per_slot": 20, "elite_share_cap": 0.33, "hours_per_region": 20,
                  "targets": {"pieces": [6.0, 0.30], "fine_up": [1.4, 0.30], "superior_up": [0.45, 0.35], "perfect": [0.08, 0.50]},
                  "region_floor": 3.0, "usable_share": [0.6, 0.85],
                  "band_hours": {"plain": 4.5, "common": 8, "earth": 17, "heaven": 25, "mystic": 15, "spirit": 40},
                  "set_hours": [0.3, 0.8]},
    })
    write("curves.json", {
        "qp_minutes": "see realms.json accumulate_needed = 100 x target minutes per Level",
        "kill_qp": 22, "kill_role_mult": {"normal": 1, "elite": 6, "field_boss": 40, "dungeon_boss": 80, "story_boss": 40, "event": 0.5, "trial": 2},
        "meditation_qp_per_min": 60, "meditation_body_stage_factor": 0.3, "body_stage_until": "bone_forging_6",
        "qi_spring_mult": 2, "training_qp_per_min": 40, "training_body_xp_per_min": 20,
        "quest_qp_pct": {"guided": 0.15, "main": 0.25, "side": 0.10, "daily": 0.05, "prologue": 0.0, "act2_main": 0.08, "act2_side": 0.04},
        "stability_factor": {"unstable": 0.7, "settling": 0.85, "stable": 1.0, "solid": 1.1},
        "stability_order": ["unstable", "settling", "stable", "solid"],
        "stability_step_s": 120,
        "risk_words": ["low", "moderate", "high", "severe"],
        "risk_success": {"low": 0.95, "moderate": 0.75, "high": 0.5, "severe": 0.25},
        "stored_qi_cap_stages": 1.0, "ceiling_stored_qi_mult": 0.25,
        "body_xp_per_level": 40, "kill_body_xp": 1, "kill_body_xp_per_5_levels": 1,
        "mastery_points": 100, "mastery_tiers": 6, "mastery_manual_from_tier": 4,
        "dao_tiers": [100, 300, 800, 2000, 5000, 12000],
        "dao_tier_names": ["observation", "imitation", "reliable_execution", "explanation", "adaptation", "original_application"],
        "insight_repeat_factor": 0.2, "insight_repeat_window_s": 60, "insight_stone_per_min": 20, "contemplate_offline_per_min": 5,
        "profession_ranks": [["apprentice", 0], ["adept", 1000], ["expert", 5000], ["master", 20000], ["grandmaster", 60000]],
        "profession_xp": {"craft_per_grade": 10, "fine_bonus": 0.5, "gather": 10, "mine": 10, "fish": 12, "cook": 8, "observe": 15},
        # Alchemy and forge mini-game: a strike this far from the band centre scores 0; three strikes per craft.
        "craft_step": {"tolerance": 0.3, "steps": 3, "perfect": 0.85, "good": 0.5},
        "purity_points_per_grade": 100, "purity_meditate_per_hour": 10, "purity_offline_per_hour": 25,
        "soul_meditate_per_hour": 10, "soul_offline_per_hour": 20,
        "offline_factor": 0.1, "offline_cap_h": 12, "retreat_cap_h": 16, "formation_cap_h": 24,
        "offline_temper_body_xp_per_min": 10, "offline_heal_mult": 1.0,
        "idle_material_factor": 0.25, "idle_cap_h": 12, "ancestral_guidance": 1.5,
        "pet_xp": {"per_level_pow": 1.5, "base": 20},
        "prestige": {"base": 200, "pow": 1.8},
        "contribution": {"daily": 20, "weekly": 150},
        "resets": {"daily_hour": 4},
        "time_of_day": {"day_minutes": 48},
        "meditation": {"settle_s": 1.0, "hp_mult": 8, "qi_mult": 8, "soul_mult": 8, "injury_heal_mult": 3,
                       "backlash_on_hit": True, "hold_page_s": 0.6},
        "injuries": {"natural_heal_s": {"minor": 600, "moderate": 1800, "severe": 3600}, "unstable_slow": 1.5},
        "bottleneck_hint_minutes": 20,
        "method_switch": {"progress_cost": 0.3, "unstable_s": 600, "pill_factor": 0.5},
        "failure_loss": {"energy_instability": [0.1, 0.3], "weak_foundation": [0.2, 0.4], "insufficient_comprehension": [0.1, 0.1],
                         "bodily_failure": [0.0, 0.0], "soul_injury": [0.0, 0.0], "resource_mismatch": [0.0, 0.0], "interruption": [0.0, 0.0]},
    })

    write("elements.json", {
        "generating": ["wood", "fire", "earth", "metal", "water"],
        "overcomes": {"wood": "earth", "earth": "water", "water": "fire", "fire": "metal", "metal": "wood"},
        "parent": {"ice": "water", "tide": "water", "thunder": "wood", "wind": "wood", "lava": "fire", "crystal": "earth",
                   "sand": "earth", "star": "metal", "blade": "metal", "hollow_water": "water", "hollow_earth": "earth",
                   "hollow_wood": "wood", "hollow_fire": "fire", "hollow_metal": "metal"},
        "neutral": ["space", "time", "soul", "life_death", "hollow", "none"],
        "cycle_advantage": 1.3, "cycle_disadvantage": 0.75, "yin_yang": 1.3, "fed_bonus": 0.1, "method_affinity_bonus": 0.1,
        "colors": {"water": "#32bed1", "wood": "#67d67a", "fire": "#f08a3c", "earth": "#c9a060", "metal": "#d8dde0",
                   "wind": "#cfe8e6", "thunder": "#e8d24c", "soul": "#9b78d1", "hollow": "#87949a", "none": "#e8e1cf",
                   "ice": "#a8e0f0", "star": "#f3e3a6", "space": "#8f7ae0"},
    })

    entries("status_effects.json", [
        {"id": "stun", "resist": "tenacity", "cc": True, "blocks": ["move", "attack"], "icon": "stun"},
        {"id": "slow", "resist": "tenacity", "cc": True, "move_mult": True, "icon": "slow"},
        {"id": "root", "resist": "tenacity", "cc": True, "blocks": ["move"], "icon": "root"},
        {"id": "knockback", "resist": "body", "cc": True, "icon": "stun"},
        {"id": "burn", "resist": "fire", "dot": True, "stops_regen": True, "icon": "burn"},
        {"id": "poison", "resist": "poison", "dot": True, "toxicity": 1, "icon": "poison"},
        {"id": "bleed", "resist": "tenacity", "dot": True, "while_moving": True, "icon": "bleed"},
        {"id": "freeze", "resist": "water", "cc": True, "blocks": ["move", "attack"], "breaks_on_hit": True, "icon": "freeze"},
        {"id": "shock", "resist": "wood", "next_hit_taken": 0.2, "icon": "shock"},
        {"id": "qi_seal", "resist": "essence", "blocks": ["technique"], "icon": "qi_seal"},
        {"id": "confusion", "resist": "spirit", "cc": True, "reverse_controls": True, "icon": "confusion"},
        {"id": "fear", "resist": "will", "cc": True, "flee": True, "icon": "fear"},
        {"id": "vulnerable", "resist": "tenacity", "damage_taken": 0.2, "icon": "vulnerable"},
        {"id": "qi_backlash", "resist": "none", "cc": True, "blocks": ["move", "attack"], "icon": "stun"},
        {"id": "exhausted", "resist": "none", "attack_mult": -0.2, "icon": "exhausted"},
        # S28 v1.2: at 100% Hollowing the Tide takes the body for a moment.
        {"id": "hollow_seizure", "resist": "none", "cc": True, "blocks": ["move", "attack", "technique"], "icon": "hollowing"},
        {"id": "spawn_protection", "resist": "none", "invulnerable": True, "icon": "spawn_protection"},
        # S47 Veil Talisman: monsters that have not found you pass you by.
        {"id": "veiled", "resist": "none", "icon": "confusion"},
        # S44 weapon oils: while one is on the blade, each hit may carry its status to the foe.
        {"id": "viper_oil", "resist": "none", "icon": "poison", "buff": True, "oil": {"status": "poison", "chance": 0.2, "power": 0.02, "duration_s": 4}},
        {"id": "ember_oil", "resist": "none", "icon": "burn", "buff": True, "oil": {"status": "burn", "chance": 0.2, "power": 0.02, "duration_s": 4}},
        # S48 Qi Deviation: after a failed breakthrough at Severe risk or on a Poor method, each technique strikes with a
        # random element for 10 minutes.
        {"id": "qi_deviation", "resist": "none", "icon": "qi_deviation", "scramble_element": True},
        # S47 v1.1 weapon families: the heavy sabre breaks armour (hits ignore a quarter of its defence); the fan's
        # wind throws a foe into the air, helpless until it lands.
        {"id": "sundered", "resist": "tenacity", "icon": "vulnerable", "pierce_defence": 0.25},
        {"id": "launched", "resist": "body", "cc": True, "blocks": ["move", "attack"], "icon": "stun", "lift": 46},
        # S48 the Soul line: Sense Lock (no evasion, no hiding) and Soul Search (its death gives up its memories).
        {"id": "sense_locked", "resist": "spirit", "icon": "sense_locked", "never_miss": True, "reveals": True},
        {"id": "soul_searched", "resist": "spirit", "icon": "injury_soul"},
    ])


    write("grades.json", {
        "order": ["plain", "common", "earth", "heaven", "mystic", "spirit", "sage", "sovereign", "will", "sphere", "law", "monarch", "inner_heaven"],
        "qualities": QUALITIES,
        "quality_order": ["flawed", "common", "fine", "superior", "perfect", "relic"],
        "quality_colors": {"flawed": "#9aa3a3", "common": "#e8e1cf", "fine": "#67d67a", "superior": "#5aa7e8", "perfect": "#b07ce8",
                           "relic": "#e5b84c", "pill_grain": "#e5b84c", "pill_halo": "#e8764c", "pill_soul": "#f2e6ff",
                           "rare": "#5aa7e8", "epic": "#b07ce8", "primordial": "#e5b84c"},
        "grade_colors": {"plain": "#b9b2a0", "common": "#e8e1cf", "earth": "#67d67a", "heaven": "#6fb8f0", "mystic": "#b07ce8",
                         "spirit": "#5ee0e8", "sage": "#d8c27a", "sovereign": "#e8a24c", "will": "#f3e3a6", "sphere": "#8f7ae0",
                         # P7b: the grades past Sphere; no red (red is the game's danger colour).
                         "law": "#a8c4ff", "monarch": "#e6b3f2", "inner_heaven": "#f4f7ff"},
        "pill_qualities": {"flawed": 0.5, "common": 1.0, "fine": 1.2, "superior": 1.4, "perfect": 1.6, "pill_grain": 1.8, "pill_halo": 2.0, "pill_soul": 2.2},
        # S15 pill qualities: toxicity multipliers, the odds of a rare quality on a perfect run
        # (times 1 + furnace bonus + 0.1 per Alchemy Dao tier), Halo growth in dense-Qi seclusion,
        # and the unique effects a Pill Soul may carry.
        "pill": {
            "toxicity": {"flawed": 1.5, "pill_grain": 0.5},
            "rare": {"pill_grain": 0.2, "pill_halo": 0.06, "pill_soul": 0.015},
            # A Pill Halo grows 1% a day in a storage chest in a room of Qi density 2 or more, to +20% (S44).
            "halo": {"min_density": 2.0, "per_day": 0.01, "cap": 0.2},
            # The fire under the furnace (S15 "rare fire"): it widens the strike band and decides how far a
            # perfect run can climb. Charcoal stops at Perfect; Earth Fire (vent rooms) and Beast Fire (a core per
            # batch) reach Grain; a Heavenly Flame, absorbed for good, reaches Halo and Soul. So does a named furnace.
            "fires": {"charcoal": {"band": 0.0, "rare": []},
                      "earth_fire": {"band": 0.10, "rare": ["pill_grain"], "needs": "earth_vent"},
                      "beast_fire": {"band": 0.15, "rare": ["pill_grain"], "consumes": "core"},
                      "heavenly_flame": {"band": 0.20, "rare": ["pill_grain", "pill_halo", "pill_soul"], "needs": "flame"}},
            # Pill marks: 0-9 gold lines by quality; each adds 2% to the pill's effect. Pills never decay.
            "marks": {"per_line": 0.02, "ranges": {"flawed": [0, 0], "common": [0, 1], "fine": [1, 2], "superior": [2, 4], "perfect": [4, 6],
                                                   "pill_grain": [6, 7], "pill_halo": [8, 8], "pill_soul": [9, 9]}},
            # Each recipe's Pill Soul carries one of these, named by its soul_effect (S44); it always applies.
            "soul": {"effects": [
                {"id": "clear_mind", "kind": "add_modifier", "stat": "insight", "op": "flat", "value": 10, "duration": 1800, "source": "pill_soul"},
                {"id": "steady_heart", "kind": "add_composure", "amount": 25},
                {"id": "mend_meridians", "kind": "cure_injury", "injury": "meridian", "max_severity": 2},
                {"id": "iron_skin", "kind": "add_modifier", "stat": "physical_defense", "op": "pct_add", "value": 0.1, "duration": 1800, "source": "pill_soul"},
            ]},
        },
        "sockets": {"plain": 0, "common": 0, "earth": 1, "heaven": 1, "mystic": 2, "spirit": 2, "sage": 3, "sovereign": 3, "will": 3,
                    "sphere": 3, "law": 3},
        "wear_level": {"plain": 0, "common": 10, "earth": 19, "heaven": 37, "mystic": 55, "spirit": 64, "sage": 73, "sovereign": 82,
                       "will": 91, "sphere": 100, "law": 109},
        # P7b (item_plan §4.1): the equipment roll. A drop's quality from its source's floor (shares of flawed, common,
        # fine, superior, perfect; each Fortune point moves the roll `fortune_shift` toward the best); `weapon_share` of
        # rolls make a weapon while weapons are open (`family_bias` of those in the family in hand), the rest one of the
        # four armour slots; a normal foe spawned as an elite rolls once more at `elite_extra`; a named row drops at its
        # source's floor raised to `named_floor`; a loot table holds at most `named_rows` rows of each kind (named,
        # elite_named); the item Level is the foe's ±`level_spread`, capped at the top Level of the highest grade with
        # banded bases. The pool is banded bases only: no named, set, relic, legend or imitation piece, no pet gear, and
        # none of `pool_skip_slots`.
        "drop": {"quality": {"flawed": [0.55, 0.30, 0.12, 0.03, 0.0], "common": [0.0, 0.50, 0.30, 0.15, 0.05],
                             "fine": [0.0, 0.0, 0.50, 0.35, 0.15], "superior": [0.0, 0.0, 0.0, 0.70, 0.30]},
                 "fortune_shift": 0.001, "weapon_share": 0.4, "family_bias": 0.3333, "level_spread": 2,
                 "elite_extra": {"chance": 0.08, "min_quality": "common"}, "named_floor": "common", "named_rows": 2,
                 "pool_skip_slots": ["gourd", "cape", "talisman", "tool_furnace"]},
    })

    entries("affixes.json", AFFIXES)

    entries("injuries.json", [
        {"id": "body", "effects": [{"stat": "max_hp", "op": "pct_add", "per_severity": -0.08}, {"stat": "move_speed", "op": "pct_add", "per_severity": -0.05}],
         "treatments": ["healing_pill", "willow_salve"], "icon": "injury_body"},
        {"id": "meridian", "effects": [{"stat": "qi_regen", "op": "pct_add", "per_severity": -0.25}, {"stat": "technique_cost", "op": "flat", "per_severity": -0.1}],
         "treatments": ["qi_restoration_pill"], "icon": "injury_meridian"},
        {"id": "soul", "effects": [{"stat": "max_soul", "op": "pct_add", "per_severity": -0.1}], "treatments": ["soul_soothing_pill"], "icon": "injury_soul"},
    ])

    entries("failures.json", [
        {"id": "energy_instability", "cause": "energy", "loss": [0.1, 0.3], "injury": {"kind": "meridian", "severity": 1}, "recovery": "Rest, restoration pill"},
        {"id": "weak_foundation", "cause": "structure", "loss": [0.2, 0.4], "stability": "unstable", "recovery": "Consolidate first"},
        {"id": "insufficient_comprehension", "cause": "understanding", "loss": [0.1, 0.1], "cooldown_s": 300, "recovery": "Dao practice, trial"},
        {"id": "bodily_failure", "cause": "structure_body", "loss": [0.0, 0.0], "injury": {"kind": "body", "severity": 2}, "recovery": "Healing pill, rest"},
        {"id": "soul_injury", "cause": "soul", "loss": [0.0, 0.0], "injury": {"kind": "soul", "severity": 2}, "recovery": "Soul nourishment", "from_realm": "spirit_awakening_1"},
        {"id": "resource_mismatch", "cause": "material", "loss": [0.0, 0.0], "injury": {"kind": "meridian", "severity": 1}, "item_lost": True, "recovery": "Correct material"},
        {"id": "interruption", "cause": "interruption", "loss": [0.0, 0.0], "injury": {"kind": "body", "severity": 1}, "items_lost": True, "recovery": "Retreat room, guard formation"},
    ])


    methods = [
        {"id": "riverbreath_fragment", "grade": "common", "ceiling": "bone_forging_9", "affinity": "water", "rate": 1.0, "capacity": 1.0, "source": "lu_boatman",
         "fragment": True, "desc": "Lu's half-remembered method. A full scripture replaces it without cost."},
        {"id": "jade_current_scripture", "grade": "common", "ceiling": "heart_tempering_9", "affinity": "water", "rate": 1.0, "capacity": 1.1, "source": "jade_sect"},
        {"id": "cloudpiercing_canon", "grade": "common", "ceiling": "heart_tempering_9", "affinity": "wind", "rate": 1.15, "capacity": 0.95, "source": "cloud_sect"},
        {"id": "stonebody_canon", "grade": "earth", "ceiling": "spirit_awakening_9", "affinity": "earth", "rate": 1.05, "capacity": 1.0, "body_growth": 0.1, "source": "library_2"},
        {"id": "willow_breath_art", "grade": "earth", "ceiling": "spirit_awakening_9", "affinity": "wood", "rate": 1.1, "capacity": 1.05, "source": "library_2"},
        {"id": "emberheart_sutra", "grade": "earth", "ceiling": "spirit_awakening_9", "affinity": "fire", "rate": 1.2, "capacity": 0.95, "source": "library_2"},
        {"id": "tidal_sovereign_scripture", "grade": "heaven", "ceiling": "sage_sovereign_3", "affinity": "water", "rate": 1.15, "capacity": 1.15, "source": "library_3_jade"},
        {"id": "nine_winds_canon", "grade": "heaven", "ceiling": "sage_sovereign_3", "affinity": "wind", "rate": 1.25, "capacity": 1.05, "source": "library_3_cloud"},
        {"id": "riverbreath_complete", "grade": "heaven", "ceiling": "sage_sovereign_3", "affinity": "water", "rate": 1.2, "capacity": 1.2, "source": "drowned_shrine"},
    ]
    # S48: each method leans Yin or Yang (Core Forging reads it against the hour): water and earth are Yin; wind, wood and fire Yang.
    for m in methods:
        m["yin_yang"] = {"water": "yin", "earth": "yin", "metal": "yin"}.get(m["affinity"], "yang")
    entries("methods.json", methods)


if __name__ == "__main__":
    build()
