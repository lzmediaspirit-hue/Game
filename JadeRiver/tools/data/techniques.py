"""S09 techniques, Daos and secret arts (Part 8)."""
from common import entries, titled

FAMILY_ACTION = {"fists": "punch_2", "jian": "swing_3", "spear": "thrust_3", "short_blade": "thrust_1", "staff": "thrust_3",
                 "bow": "bow", "any": None}


def tech(id, unlock, source, family, element, dtype, mult, hits, targets, cd, qi, extra="", **f):
    x_reach = f.pop("reach", None)
    action = f.pop("action", FAMILY_ACTION.get(family))
    row = {"id": id, "name": titled(id), "family": family, "element": element, "damage_type": dtype,
           "mult": list(mult), "hits": hits, "max_targets": targets,
           "hitbox": {"x": [-10, x_reach or {"fists": 70, "jian": 100, "spear": 150, "short_blade": 70, "staff": 120, "bow": 480, "any": 110}[family]],
                      "depth": f.pop("depth", 30), "alt": [0, 110]},
           "windup_s": f.pop("windup", 0.2), "active_s": f.pop("active", 0.2), "cooldown_s": cd, "qi_cost": qi,
           "soul_cost": f.pop("soul", 0), "composure_cost": f.pop("composure", 0), "dao": f.pop("dao", {
               "fists": "fist", "jian": "sword", "spear": "spear", "short_blade": "blade", "staff": "staff", "bow": "bow"}.get(family, element)),
           "unlock": unlock, "source": source, "desc": extra, "action": action, "icon": id,
           "mastery": {"dmg_per_tier": 0.08, "cost_per_tier": -0.05}}
    row.update(f)
    return row


def build():
    T = [
        # The first technique every disciple learns: a free-hand palm, so it works whatever the weapon.
        tech("flowing_palm", "qi_kindling_1", "training_hall_jade", "any", "water", "physical", (1.10, 1.30), 2, 1, 3, 8,
             "Two flowing palm strikes with the free hand; any weapon. Tier 3: slows the target by 20% for 2 s.",
             tier3={"status": {"id": "slow", "chance": 1.0, "power": 0.2, "duration_s": 2}}, action="punch", dao="fist", reach=80),
        tech("jade_thrust", "qi_kindling_1", "training_hall_cloud", "spear", "none", "physical", (1.40, 1.70), 1, 2, 4, 10,
             "A piercing thrust that hits two foes in a line. Tier 5: becomes a Qi lance.", line=True),
        tech("cloudpiercing_stroke", "qi_kindling_1", "training_hall", "jian", "wind", "physical", (1.20, 1.50), 1, 2, 3.5, 9,
             "A rising cut in a wide arc. Tier 3: +10% crit.", tier3={"crit": 0.1}),
        tech("reedcutter_slash", "qi_kindling_1", "training_hall", "short_blade", "wood", "physical", (1.30, 1.60), 1, 1, 3, 8,
             "A quick slash with a 20% chance to bleed for 3 s.", status={"id": "bleed", "chance": 0.2, "power": 0.05, "duration_s": 3}),
        tech("riverstone_sweep", "qi_kindling_1", "training_hall", "staff", "earth", "physical", (1.00, 1.30), 1, 6, 4, 10,
             "A heavy sweep that strikes everything in front and knocks it back.", knockback=80),
        tech("twin_reed_shot", "qi_kindling_1", "training_hall", "bow", "wood", "physical", (0.70, 0.90), 2, 1, 3, 8,
             "Two arrows at once. Tier 3: a third arrow.", projectile={"speed": 680, "range": 480, "count": 2}),
        tech("tiger_rush", "qi_kindling_5", "library_1", "fists", "none", "physical", (1.50, 1.80), 1, 1, 6, 12,
             "Dash 120 units and strike with the weight of a tiger.", dash=120),
        tech("willow_leaf_parry", "qi_kindling_5", "library_1", "jian", "wood", "stance", (2.0, 2.0), 1, 1, 8, 10,
             "Enter a stance: the next parry within 2 s counters for 200%.", stance_s=2.0),
        tech("dragon_tail_sweep", "qi_kindling_5", "library_1", "spear", "none", "physical", (1.10, 1.40), 1, 6, 6, 12,
             "A 180-degree sweep that hits all nearby foes.", both_sides=True, reach=130),
        tech("shadow_flick", "qi_kindling_5", "library_1", "short_blade", "none", "physical", (0.90, 1.20), 1, 1, 5, 10,
             "Backstep, then throw a knife 300 units.", dash=-60, projectile={"speed": 700, "range": 300, "count": 1}),
        tech("bell_toll_strike", "qi_kindling_5", "library_1", "staff", "metal", "physical", (1.30, 1.60), 1, 1, 7, 14,
             "A ringing blow with a 25% chance to stun for 0.6 s.", status={"id": "stun", "chance": 0.25, "power": 1, "duration_s": 0.6}),
        tech("pinning_arrow", "qi_kindling_5", "library_1", "bow", "none", "physical", (1.20, 1.50), 1, 1, 7, 12,
             "An arrow that roots the target for 1.5 s.", projectile={"speed": 700, "range": 480, "count": 1},
             status={"id": "root", "chance": 1.0, "power": 1, "duration_s": 1.5}),
        tech("rising_tide", "qi_kindling_7", "mudwater_manual", "any", "water", "qi", (0.90, 1.20), 1, 8, 8, 16,
             "A wave of Qi strikes all foes within 200 units and slows them 20%.", both_sides=True, reach=200, depth=70,
             status={"id": "slow", "chance": 1.0, "power": 0.2, "duration_s": 2}, action="meditate_burst"),
        tech("palm_wave", "qi_unfurling_1", "after_the_cleansing", "fists", "water", "qi", (1.00, 1.30), 1, 2, 4, 12,
             "A palm of Qi that flies 360 units and pierces one foe.", projectile={"speed": 560, "range": 360, "count": 1, "pierce": 1}),
        tech("crescent_arc", "qi_unfurling_1", "after_the_cleansing", "jian", "wind", "qi", (0.90, 1.20), 1, 8, 5, 14,
             "A crescent of sword Qi that travels 360 units along the depth band.", projectile={"speed": 620, "range": 360, "count": 1, "pierce": 8}),
        tech("spear_lance", "qi_unfurling_1", "after_the_cleansing", "spear", "none", "qi", (1.30, 1.60), 1, 8, 5, 14,
             "A lance of Qi hitting everything in a 300-unit line. +10% penetration.", reach=300, line=True, penetration=0.1),
        tech("flying_blades", "qi_unfurling_1", "after_the_cleansing", "short_blade", "metal", "qi", (0.50, 0.70), 3, 3, 5, 12,
             "Three seeking blades.", projectile={"speed": 600, "range": 360, "count": 3, "seek": True}),
        tech("earthshaker_wave", "qi_unfurling_1", "after_the_cleansing", "staff", "earth", "qi", (1.10, 1.40), 1, 8, 6, 14,
             "A ground wave that knocks back everything within 300 units ahead.", reach=300, knockback=80, depth=60),
        tech("vine_snare", "qi_unfurling_2", "library_2", "any", "wood", "qi", (0.60, 0.80), 1, 3, 10, 14,
             "Vines root up to three foes for 2 s.", status={"id": "root", "chance": 1.0, "power": 1, "duration_s": 2}, reach=220, depth=60, action="meditate_burst"),
        tech("rain_of_reeds", "qi_unfurling_3", "drowned_shrine_drop", "bow", "wood", "physical", (0.45, 0.60), 5, 5, 8, 18,
             "Five arrows rain on an area.", reach=420, depth=70),
        tech("stone_skin", "qi_unfurling_4", "library_2", "any", "earth", "buff", (0, 0), 0, 0, 20, 18,
             "+30% Physical Defense for 8 s.", buff={"stat": "physical_defense", "op": "pct_add", "value": 0.3, "duration": 8}, action="meditate_burst"),
        tech("gale_step", "qi_unfurling_6", "cloud_library", "any", "wind", "movement", (0.6, 0.6), 1, 8, 6, 10,
             "Dash 200 units through enemies, striking all you pass.", dash=200, action="jump"),
        tech("mountain_shaker", "heart_tempering_1", "library_2", "staff", "earth", "physical", (1.20, 1.50), 1, 8, 10, 22,
             "A slam with a 30% chance to stun for 0.8 s; knockback.", both_sides=True, reach=140, knockback=80,
             status={"id": "stun", "chance": 0.3, "power": 1, "duration_s": 0.8}),
        tech("ember_burst", "heart_tempering_3", "gorge_bandit_drop", "any", "fire", "qi", (1.40, 1.70), 1, 8, 9, 20,
             "An explosion of fire within 150 units that burns for 3 s.", both_sides=True, reach=150, depth=60,
             status={"id": "burn", "chance": 1.0, "power": 0.05, "duration_s": 3}, action="meditate_burst"),
        tech("still_water_focus", "heart_tempering_5", "mentor", "any", "water", "buff", (0, 0), 0, 0, 25, 15,
             "Your next technique hits its perfect-timing bonus.", buff={"stat": "perfect_timing", "op": "flat", "value": 1, "duration": 10}, action="meditate_burst"),
        tech("shadowstep_cut", "cloud_stride_4", "library_3", "short_blade", "wind", "physical", (2.00, 2.60), 1, 1, 12, 20,
             "Blink behind the target and cut.", blink=True, reach=240),
        tech("cloud_descent", "cloud_stride_3", "above_the_mist", "any", "wind", "physical", (1.60, 2.00), 1, 8, 8, 20,
             "An aerial dive that strikes everything below (flying only).", flying_only=True, both_sides=True, reach=120, depth=60, action="jump"),
        tech("mirror_mind_spike", "spirit_awakening_1", "mentor", "any", "soul", "soul", (1.50, 1.80), 1, 1, 9, 10,
             "A spike of will that ignores armour; 20% confusion.", soul=15, ignore_armor=True, reach=260,
             status={"id": "confusion", "chance": 0.2, "power": 1, "duration_s": 2}, action="meditate_burst"),
        tech("soul_lantern_ward", "spirit_awakening_5", "mentor_secret", "any", "soul", "buff", (0, 0), 0, 0, 30, 0,
             "A ward that absorbs damage equal to 20% max Soul for 6 s.", soul=20, buff={"stat": "shield_soul_pct", "op": "flat", "value": 0.2, "duration": 6}, action="meditate_burst"),
        tech("glimpse_of_heaven", "heaven_glimpse_1", "a_wider_sky", "any", "none", "qi", (2.50, 3.00), 1, 1, 15, 35,
             "Borrow a glimpse of the heavens. Ignores 20% Qi Resistance.", reach=320, ignore_resistance=0.2, action="meditate_burst"),
    ]
    entries("techniques.json", T)

    weapon_dao = {"tiers": ["+3% attack with the family", "Linked techniques -10% QI", "Linked techniques gain their tier-3 effect",
                            "+5% crit with the family; can teach it", "Tier-5 forms of linked techniques"],
                  "effects": [{"attack_pct": 0.03}, {"cost_pct": -0.1}, {"tier3": True}, {"crit": 0.05, "teach": True}, {"tier5": True}]}
    element_dao = {"tiers": ["+5% elemental power", "Element techniques -10% QI", "+10% chance to apply the element's status",
                             "+5% resistance to the element; can teach it", "Element techniques gain area or pierce"],
                   "effects": [{"elemental_power": 0.05}, {"cost_pct": -0.1}, {"status_chance": 0.1}, {"resistance": 0.05, "teach": True}, {"area": True}]}
    daos = []
    for d in ["fist", "sword", "spear", "blade", "staff", "bow"]:
        daos.append(dict({"id": d, "family": "weapon", "valley_cap": 5}, **weapon_dao))
    for d in ["water", "wood", "earth", "wind", "fire", "metal", "thunder"]:
        daos.append(dict({"id": d, "family": "element", "valley_cap": 5 if d in ("water", "wood", "earth", "wind") else 2}, **element_dao))
    daos.append({"id": "soul", "family": "element", "valley_cap": 3, "tiers": element_dao["tiers"], "effects": element_dao["effects"]})
    daos.append({"id": "alchemy", "family": "craft", "valley_cap": 5, "tiers": ["+5% quality chance", "-10% ingredient loss on mistakes", "Wider heat band",
                 "Can teach; +1 auto-refine queue slot", "Substitute one ingredient per recipe"], "effects": [{"quality": 0.05}, {}, {"band": 0.1}, {"queue": 1}, {}]})
    daos.append({"id": "formation", "family": "craft", "valley_cap": 5, "tiers": ["+10% formation duration", "-10% fuel", "+1 node", "Can teach; faster placement",
                 "Formations take no damage for the first 10 s"], "effects": [{}, {}, {}, {}, {}]})
    for d in ["refining", "puppetry", "beast_taming"]:
        daos.append({"id": d, "family": "craft", "valley_cap": 2, "tiers": ["+5% quality or speed", "-10% materials"], "effects": [{}, {}]})
    for d in ["space", "time", "life_death", "blood", "karma", "emotion"]:
        daos.append({"id": d, "family": "rare", "valley_cap": 0, "tiers": [], "effects": []})
    for d in daos:
        d["name"] = "%s Dao" % titled(d["id"])
    entries("daos.json", daos)

    entries("secret_arts.json", [
        {"id": "dodge_dash", "name": "Dodge Dash", "unlock": "bone_forging_5", "desc": "Dash 140 units; 0.25 s invulnerable.", "icon": "dodge_dash"},
        {"id": "appraisal_eye", "name": "Appraisal Eye", "unlock": "qi_kindling_6", "desc": "Identify items without the loupe.", "icon": "appraisal_eye"},
        {"id": "breath_control", "name": "Breath Control", "unlock": "qi_unfurling_3", "desc": "Stay underwater 30 s; enter flooded rooms.", "icon": "breath_control"},
        {"id": "wall_step", "name": "Wall-Step", "unlock": "heart_tempering_4", "desc": "One kick off a wall per jump.", "icon": "wall_step"},
        {"id": "concealment", "name": "Concealment", "unlock": "spirit_awakening_2", "desc": "Enemies' aggro range -50% while not attacking.", "icon": "concealment"},
        {"id": "lotus_heart_breathing", "name": "Lotus Heart Breathing", "unlock": "spirit_awakening_5", "desc": "Heal 2% HP per second for 5 s.", "icon": "concealment"},
        {"id": "wind_blink", "name": "Wind Blink", "unlock": "spirit_awakening_5", "desc": "Blink 120 units; cooldown 10 s.", "icon": "dodge_dash"},
    ])


if __name__ == "__main__":
    build()
