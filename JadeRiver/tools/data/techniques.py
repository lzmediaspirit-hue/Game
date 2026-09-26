"""S09 techniques, Daos and secret arts (Part 8)."""
from common import entries, titled

FAMILY_ACTION = {"fists": "punch_2", "jian": "swing_3", "spear": "thrust_3", "short_blade": "thrust_1", "staff": "thrust_3",
                 "bow": "bow", "heavy_sabre": "swing_3", "fan": "swing_2", "flute": "attack", "any": None}


def tech(id, unlock, source, family, element, dtype, mult, hits, targets, cd, qi, extra="", **f):
    x_reach = f.pop("reach", None)
    action = f.pop("action", FAMILY_ACTION.get(family))
    row = {"id": id, "name": titled(id), "family": family, "element": element, "damage_type": dtype,
           "mult": list(mult), "hits": hits, "max_targets": targets,
           "hitbox": {"x": [-10, x_reach or {"fists": 70, "jian": 100, "spear": 150, "short_blade": 70, "staff": 120, "bow": 480, "any": 110,
                                             "heavy_sabre": 110, "fan": 180, "flute": 240}[family]],
                      # S43 rule 10: Qi and Soul arcs reach -10..+80 of the user's height; physical techniques the melee band.
                      "depth": f.pop("depth", 30), "alt": [-10, 80] if dtype in ("qi", "soul") else [-30, 60]},
           "windup_s": f.pop("windup", 0.2), "active_s": f.pop("active", 0.2), "cooldown_s": cd, "qi_cost": qi,
           "soul_cost": f.pop("soul", 0), "composure_cost": f.pop("composure", 0), "dao": f.pop("dao", {
               "fists": "fist", "jian": "sword", "spear": "spear", "short_blade": "blade", "staff": "staff", "bow": "bow",
               "heavy_sabre": "blade", "fan": "fan", "flute": "music"}.get(family, element)),
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
             "Dash 120 units and strike with the weight of a tiger. A body technique: from Copper Body it can spend HP when QI runs short.", dash=120, body=True),
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
        # S47 v1.1 families. The heavy sabre: a cleave that breaks armour; the fan: wind that lifts; the flute: notes
        # that confuse (the Music path).
        tech("mountain_cleaver", "qi_kindling_5", "library_1", "heavy_sabre", "metal", "physical", (1.60, 1.90), 1, 3, 5, 12,
             "A two-handed cleave through up to three foes; it always breaks their armour for 4 s.",
             armour_break={"chance": 1.0, "duration_s": 4}),
        tech("gale_fan", "qi_kindling_5", "library_1", "fan", "wind", "qi", (0.90, 1.10), 1, 4, 5, 12,
             "A fan-stroke of wind 180 units long that throws up to four foes into the air.", knockup_s=0.8, depth=50),
        tech("reed_song", "qi_unfurling_1", "after_the_cleansing", "flute", "wood", "qi", (0.55, 0.70), 3, 3, 5, 12,
             "Three notes that seek their mark; each may confuse its target for 1.5 s.",
             projectile={"speed": 460, "range": 320, "count": 3, "seek": True, "art": "note"},
             status={"id": "confusion", "chance": 0.2, "power": 1, "duration_s": 1.5}),
        tech("thunder_dao_arc", "qi_unfurling_1", "after_the_cleansing", "heavy_sabre", "thunder", "qi", (1.10, 1.40), 1, 8, 6, 15,
             "A heavy arc of sabre Qi that rolls 300 units and breaks the armour of all it cuts.",
             projectile={"speed": 520, "range": 300, "count": 1, "pierce": 8}, armour_break={"chance": 1.0, "duration_s": 4}),
        tech("returning_crane_fan", "qi_unfurling_1", "after_the_cleansing", "fan", "wind", "physical", (0.80, 1.00), 2, 8, 6, 14,
             "Throw the fan: it flies 300 units and comes back, cutting and lifting everything it passes, both ways.",
             projectile={"speed": 540, "range": 300, "count": 1, "pierce": 8, "returning": True, "art": "fan"}, knockup_s=0.6),
        tech("clear_heart_melody", "qi_kindling_5", "library_1", "flute", "water", "buff", (0, 0), 0, 0, 20, 16,
             "A calming melody: you and every ally beside you recover 4% of your health a second for 6 s.",
             allies_heal_pct=0.04, allies_heal_s=6, heal_radius=220),
        tech("rising_tide", "qi_kindling_7", "mudwater_manual", "any", "water", "qi", (0.90, 1.20), 1, 8, 8, 16,
             "A wave of Qi strikes all foes within 200 units and slows them 20%.", both_sides=True, reach=200, depth=70,
             status={"id": "slow", "chance": 1.0, "power": 0.2, "duration_s": 2}, action="meditate_burst"),
        tech("palm_wave", "qi_unfurling_1", "after_the_cleansing", "fists", "water", "qi", (1.00, 1.30), 1, 2, 4, 12,
             "A palm of Qi that flies 360 units and pierces one foe.", projectile={"speed": 560, "range": 360, "count": 1, "pierce": 1}),
        tech("crescent_arc", "qi_unfurling_1", "after_the_cleansing", "jian", "wind", "qi", (0.90, 1.20), 1, 8, 5, 14,
             "A crescent of sword Qi that travels 360 units along the depth band.", projectile={"speed": 620, "range": 360, "count": 1, "pierce": 8}),
        tech("spear_lance", "qi_unfurling_1", "after_the_cleansing", "spear", "none", "qi", (1.30, 1.60), 1, 8, 5, 14,
             "A lance of Qi hitting everything in a 300-unit line. +10% penetration.", reach=300, line=True, penetration=0.1),
        # S47 Sword Release, learned when the Sword Dao reaches tier 3: the jian flies on its own for 8 s.
        tech("sword_release", "heart_tempering_1", "sword_dao_3", "jian", "metal", "sword_release", (0.60, 0.60), 1, 1, 12, 20,
             "The jian leaves your hand and strikes on its own for 8 s (60% a strike, 1.5 a second); your hands fight with Qi palms. Use again to call it back.",
             release_s=8.0, strikes_per_s=1.5, seek_radius=420),
        tech("flying_blades", "qi_unfurling_1", "after_the_cleansing", "short_blade", "metal", "qi", (0.50, 0.70), 3, 3, 5, 12,
             "Three seeking blades.", projectile={"speed": 600, "range": 360, "count": 3, "seek": True}),
        tech("earthshaker_wave", "qi_unfurling_1", "after_the_cleansing", "staff", "earth", "qi", (1.10, 1.40), 1, 8, 6, 14,
             "A ground wave that knocks back everything within 300 units ahead.", reach=300, knockback=80, depth=60),
        tech("vine_snare", "qi_unfurling_2", "library_2", "any", "wood", "qi", (0.60, 0.80), 1, 3, 10, 14,
             "Vines root up to three foes for 2 s.", status={"id": "root", "chance": 1.0, "power": 1, "duration_s": 2}, reach=220, depth=60, action="meditate_burst"),
        tech("rain_of_reeds", "qi_unfurling_3", "drowned_shrine_drop", "bow", "wood", "physical", (0.45, 0.60), 5, 5, 8, 18,
             "Five arrows rain on an area.", reach=420, depth=70),
        tech("stone_skin", "qi_unfurling_4", "library_2", "any", "earth", "buff", (0, 0), 0, 0, 20, 18,
             "+30% Physical Defense for 8 s. A body technique: from Copper Body it can spend HP when QI runs short.",
             buff={"stat": "physical_defense", "op": "pct_add", "value": 0.3, "duration": 8}, action="meditate_burst", body=True),
        tech("gale_step", "qi_unfurling_6", "cloud_library", "any", "wind", "movement", (0.6, 0.6), 1, 8, 6, 10,
             "Dash 200 units through enemies, striking all you pass.", dash=200, action="jump"),
        tech("mountain_shaker", "heart_tempering_1", "library_2", "staff", "earth", "physical", (1.20, 1.50), 1, 8, 10, 22,
             "A slam with a 30% chance to stun for 0.8 s; knockback. A body technique: from Copper Body it can spend HP when QI runs short.",
             both_sides=True, reach=140, knockback=80, body=True,
             status={"id": "stun", "chance": 0.3, "power": 1, "duration_s": 0.8}),
        tech("ember_burst", "heart_tempering_3", "gorge_bandit_drop", "any", "fire", "qi", (1.40, 1.70), 1, 8, 9, 20,
             "An explosion of fire within 150 units that burns for 3 s.", both_sides=True, reach=150, depth=60,
             status={"id": "burn", "chance": 1.0, "power": 0.05, "duration_s": 3}, action="meditate_burst"),
        tech("still_water_focus", "heart_tempering_5", "brothers_in_arms", "any", "water", "buff", (0, 0), 0, 0, 25, 15,
             "Your next technique hits its perfect-timing bonus.", buff={"stat": "perfect_timing", "op": "flat", "value": 1, "duration": 10}, action="meditate_burst"),
        tech("shadowstep_cut", "cloud_stride_4", "library_3", "short_blade", "wind", "physical", (2.00, 2.60), 1, 1, 12, 20,
             "Blink behind the target and cut.", blink=True, reach=240),
        tech("cloud_descent", "cloud_stride_3", "above_the_mist", "any", "wind", "physical", (1.60, 2.00), 1, 8, 8, 20,
             "An aerial dive that strikes everything below (flying only).", flying_only=True, both_sides=True, reach=120, depth=60, action="jump"),
        tech("mirror_mind_spike", "spirit_awakening_1", "a_lake_inside", "any", "soul", "soul", (1.50, 1.80), 1, 1, 9, 10,
             "A spike of will that ignores armour; 20% confusion.", soul=15, ignore_armor=True, reach=260,
             status={"id": "confusion", "chance": 0.2, "power": 1, "duration_s": 2}, action="meditate_burst"),
        tech("soul_lantern_ward", "spirit_awakening_5", "the_mentors_gift", "any", "soul", "buff", (0, 0), 0, 0, 30, 0,
             "A ward that absorbs damage equal to 20% max Soul for 6 s.", soul=20, shield_soul_pct=0.2, shield_s=6, action="meditate_burst"),
        # S48 the Soul line (v1.0), taught by the Soul Dao's first three tiers: a lock the eyes of the soul put on a foe,
        # an illusion that draws foes off you, and a search of an elite's soul for its memories and what it hid.
        tech("sense_lock", "spirit_awakening_1", "soul_dao_1", "any", "soul", "soul", (0.60, 0.80), 1, 1, 14, 0,
             "Fix your Spirit Sense on one foe within 420 for 8 s: it cannot evade you or hide from you.",
             soul=10, reach=420, sense_lock_s=8, action="meditate_burst"),
        tech("phantom_double", "spirit_awakening_2", "soul_dao_2", "any", "soul", "illusion", (0, 0), 0, 0, 24, 0,
             "Leave an illusion of yourself where you stand for 6 s (+1 s a Soul Dao tier). Foes within 500 turn on it until it has been struck three times. Bosses see through it.",
             soul=25, illusion_s=6, illusion_hits=3, illusion_radius=500, action="meditate_burst"),
        tech("soul_search", "spirit_awakening_3", "soul_dao_3", "any", "soul", "soul", (0.80, 1.00), 1, 1, 18, 0,
             "A spike into an elite's soul that ignores armour. If it dies within 12 s, you read its memories (a Codex page) and find what it hid (an extra drop).",
             soul=20, reach=220, soul_search_s=12, ignore_armor=True, action="meditate_burst"),
        # S48 the Poison path (v1.1): sold at night on the Caravan Road. Knowing one opens the Poison Body.
        tech("venom_needles", "qi_unfurling_1", "night_peddler", "any", "wood", "physical", (0.40, 0.55), 3, 3, 8, 12,
             "Three seeking needles; each poisons its mark (2% of its health a second for 5 s).",
             projectile={"speed": 600, "range": 340, "count": 3, "seek": True, "art": "needle"},
             status={"id": "poison", "chance": 1.0, "power": 0.02, "duration_s": 5}, poison_path=True, dao="wood"),
        tech("miasma_palm", "heart_tempering_1", "night_peddler", "any", "wood", "qi", (0.50, 0.70), 1, 8, 14, 18,
             "A palm of green miasma that poisons every foe within 160 on both sides (3% of their health a second for 6 s).",
             both_sides=True, reach=160, depth=70, status={"id": "poison", "chance": 1.0, "power": 0.03, "duration_s": 6},
             poison_path=True, action="punch", dao="wood"),
        # S48 costly secret art: the Blood Dao's teacher shows how to burn one's own blood for a fight.
        tech("blood_burning", "sage_sovereign_1", "blood_remembers", "any", "none", "buff", (0, 0), 0, 0, 45, 0,
             "Burn your own blood: +50% attack for 10 s. It costs 30% of your HP and leaves a body injury.",
             buffs=[{"stat": "physical_attack", "op": "pct_add", "value": 0.5, "duration": 10},
                    {"stat": "qi_attack", "op": "pct_add", "value": 0.5, "duration": 10}],
             hp_cost_pct=0.3, injury={"kind": "body", "severity": 1}, secret=True, action="meditate_burst"),
        tech("glimpse_of_heaven", "heaven_glimpse_1", "a_wider_sky", "any", "none", "qi", (2.50, 3.00), 1, 1, 15, 35,
             "Borrow a glimpse of the heavens. Ignores 20% Qi Resistance.", reach=320, ignore_resistance=0.2, action="meditate_burst"),
    ]
    # S48 technique grades: Common, Earth and Heaven (+0 / 10 / 20% to the base multiplier), by the realm that teaches
    # them. Willow Leaf Parry is also the jian's stance (stances.json).
    for t in T:
        realm_of = t["unlock"].rsplit("_", 1)[0]
        t["grade"] = "common" if realm_of in ("qi_kindling", "bone_forging") else ("earth" if realm_of in ("qi_unfurling", "heart_tempering") else "heaven")
        if t["id"] == "willow_leaf_parry":
            t["stance"] = "jian"
    entries("techniques.json", T)

    weapon_dao = {"tiers": ["+3% attack with the family", "Linked techniques -10% QI", "Linked techniques gain their tier-3 effect",
                            "+5% crit with the family; can teach it", "Tier-5 forms of linked techniques"],
                  "effects": [{"attack_pct": 0.03}, {"cost_pct": -0.1}, {"tier3": True}, {"crit": 0.05, "teach": True}, {"tier5": True}]}
    element_dao = {"tiers": ["+5% elemental power", "Element techniques -10% QI", "+10% chance to apply the element's status",
                             "+5% resistance to the element; can teach it", "Element techniques gain area or pierce"],
                   "effects": [{"elemental_power": 0.05}, {"cost_pct": -0.1}, {"status_chance": 0.1}, {"resistance": 0.05, "teach": True}, {"area": True}]}
    daos = []
    for d in ["fist", "sword", "spear", "blade", "staff", "bow", "fan", "music"]:   # fan and music: the v1.1 families
        row = dict({"id": d, "family": "weapon", "valley_cap": 5}, **weapon_dao)
        if d == "sword":   # S47: tier 3 also teaches Sword Release
            row["tiers"] = list(row["tiers"])
            row["tiers"][2] = "Linked techniques gain their tier-3 effect; learn Sword Release"
            row["effects"] = [dict(e) for e in row["effects"]]
            row["effects"][2]["learn_technique"] = "sword_release"
        daos.append(row)
    for d in ["water", "wood", "earth", "wind", "fire", "metal", "thunder"]:
        daos.append(dict({"id": d, "family": "element", "valley_cap": 5 if d in ("water", "wood", "earth", "wind") else 2}, **element_dao))
    # S48 the Soul line: the Soul Dao's first three tiers each teach one of its techniques.
    soul_effects = [dict(e) for e in element_dao["effects"]]
    soul_tiers = list(element_dao["tiers"])
    for i, (tid, word) in enumerate([("sense_lock", "Sense Lock"), ("phantom_double", "Phantom Double"), ("soul_search", "Soul Search")]):
        soul_effects[i]["learn_technique"] = tid
        soul_tiers[i] = "%s; learn %s" % (soul_tiers[i], word)
    daos.append({"id": "soul", "family": "element", "valley_cap": 3, "tiers": soul_tiers, "effects": soul_effects})
    daos.append({"id": "alchemy", "family": "craft", "valley_cap": 5, "tiers": ["+5% quality chance", "-10% ingredient loss on mistakes", "Wider heat band",
                 "Can teach; +1 auto-refine queue slot", "Substitute one ingredient per recipe"], "effects": [{"quality": 0.05}, {}, {"band": 0.1}, {"queue": 1}, {}]})
    daos.append({"id": "formation", "family": "craft", "valley_cap": 5, "tiers": ["+10% formation duration", "-10% fuel", "+1 node", "Can teach; faster placement",
                 "Formations take no damage for the first 10 s"], "effects": [{}, {}, {}, {}, {}]})
    for d in ["refining", "puppetry"]:
        daos.append({"id": d, "family": "craft", "valley_cap": 2, "tiers": ["+5% quality or speed", "-10% materials"], "effects": [{}, {}]})
    # S46 Beast Taming Dao: two tiers in the valley, 3-4 in the Azure Expanse (tame elites; teach it), 5-6 later
    # (tame a Beast King after its trial; write your own contract). Each tier adds 5% to the taming chance.
    daos.append({"id": "beast_taming", "family": "craft", "valley_cap": 2, "zone_caps": {"azure_expanse": 4}, "teach_tier": 4,
                 "tiers": ["+5% taming chance", "+5% taming chance; eggs hatch 10% sooner", "Tame elite beasts",
                           "Can teach Beast Taming to your disciples", "Tame a Beast King after its trial (a later age)",
                           "Write a contract of your own (a later age)"],
                 "effects": [{}, {"hatch": -0.1}, {"tame_elites": True}, {}, {}, {}]})
    # The Azure Expanse's own Laws (five elements, Wind, Thunder) deepen past the valley's caps there (S18 World Laws).
    for d in daos:
        if d["family"] == "element":
            d["zone_caps"] = {"azure_expanse": 5}
    # Rare Daos (v1.1): taught by the Expanse's teachers, four tiers each while Act II lasts; each tier adds its modifiers.
    RARE = {
        "blood": (["+5% max HP", "+40% HP regeneration", "+5% tenacity", "+5% attack; can teach it"],
                  [[{"stat": "max_hp", "value": 0.05}], [{"stat": "hp_regen", "value": 0.4}], [{"stat": "tenacity", "op": "flat", "value": 0.05}],
                   [{"stat": "physical_attack", "value": 0.05}, {"stat": "qi_attack", "value": 0.05}]]),
        "life_death": (["+5% max Soul", "Injuries heal 25% faster", "+10% soul defence", "+5% Hollow Ward; can teach it"],
                       [[{"stat": "max_soul", "value": 0.05}], [{"stat": "injury_recovery", "op": "flat", "value": 0.25}],
                        [{"stat": "soul_defense", "value": 0.1}], [{"stat": "hollow_ward", "op": "flat", "value": 0.05}]]),
        "emotion": (["+10% Will", "+10% insight rate", "+5% soul attack", "+10% Will; can teach it"],
                    [[{"stat": "will", "value": 0.1}], [{"stat": "insight_rate", "op": "flat", "value": 0.1}],
                     [{"stat": "soul_attack", "value": 0.05}], [{"stat": "will", "value": 0.1}]]),
    }
    for d in ["space", "time", "life_death", "blood", "karma", "emotion"]:
        if d in RARE:
            tiers, mods = RARE[d]
            daos.append({"id": d, "family": "rare", "valley_cap": 0, "zone_caps": {"azure_expanse": 4}, "tiers": tiers,
                         "effects": [{} for _ in tiers], "mods": mods, "teacher": True})
        else:
            daos.append({"id": d, "family": "rare", "valley_cap": 0, "tiers": [], "effects": []})
    for d in daos:
        d["name"] = "%s Dao" % titled(d["id"])
    entries("daos.json", daos)

    entries("secret_arts.json", [
        {"id": "dodge_dash", "name": "Dodge Dash", "unlock": "bone_forging_5", "movement_art": "dodge", "desc": "Dash 140 units; 0.25 s invulnerable.",
         "icon": "dodge_dash", "how_to": "Tap Evade; hold it to guard."},
        {"id": "appraisal_eye", "name": "Appraisal Eye", "unlock": "qi_kindling_6", "desc": "Identify items without the loupe.", "icon": "appraisal_eye"},
        {"id": "breath_control", "name": "Breath Control", "unlock": "qi_unfurling_3", "movement_art": "breath_control",
         "desc": "Stay underwater 30 s; swim deep water for 30 s; enter flooded rooms.", "icon": "breath_control",
         "how_to": "Deep water no longer pulls you under at once: you swim for 30 s."},
        # S43 movement arts: each comes with a guided quest and is usable from its acceptance. `movement_art`
        # names what the body can do; `how_to` is the one-line toast the first time it is usable.
        {"id": "plunge", "name": "Plunge", "unlock": "bone_forging_4", "movement": True, "movement_art": "plunge", "quest": "outer_trial",
         "desc": "In the air, pull down and attack: drop at 900 and strike all within 60 for 120% damage and a 0.5 s stun. Cooldown 4 s.",
         "how_to": "In the air: joystick down + Attack.", "icon": "plunge"},
        {"id": "falling_leaf_glide", "name": "Falling Leaf Glide", "unlock": "qi_kindling_3", "movement": True, "movement_art": "glide",
         "quest": "leaf_on_the_wind", "icon": "falling_leaf_glide",
         "desc": "Hold Jump while falling: drift down at 120 a second and 10% faster across. Costs 2 QI a second.",
         "how_to": "Hold Jump while you fall."},
        {"id": "swallow_dart", "name": "Swallow Dart", "unlock": "qi_kindling_7", "movement": True, "movement_art": "air_dash",
         "quest": "swallow_dart", "icon": "swallow_dart",
         "desc": "Evade in the air: dart 140 and hold your height for a breath. Once before you land; shares the dodge's cooldown.",
         "how_to": "In the air: tap Evade."},
        {"id": "cloud_ladder_step", "name": "Cloud Ladder Step", "unlock": "qi_unfurling_6", "movement": True, "movement_art": "double_jump",
         "quest": "cloud_ladder", "icon": "cloud_ladder_step",
         "desc": "Jump again in the air: a second jump of +80 from where you use it, once before you land.",
         "how_to": "In the air: press Jump again."},
        {"id": "water_skimming", "name": "Water Skimming", "unlock": "qi_unfurling_8", "movement": True, "movement_art": "water_skimming",
         "quest": "skipping_stones", "icon": "water_skimming",
         "desc": "Sprint across deep water as if it were stone. Stop for half a second and you sink.",
         "how_to": "Sprint onto deep water and keep running."},
        {"id": "wall_step", "name": "Wall-Step", "unlock": "heart_tempering_4", "movement": True, "movement_art": "wall_step", "quest": "between_two_walls",
         "desc": "Jump while pushing into a wall: kick up 88 and 90 away. Three kicks before you land.", "icon": "wall_step",
         "how_to": "In the air, push into a wall and press Jump."},
        {"id": "concealment", "name": "Concealment", "unlock": "spirit_awakening_2", "desc": "Enemies' aggro range -50% while not attacking.", "icon": "concealment"},
        {"id": "lotus_heart_breathing", "name": "Lotus Heart Breathing", "unlock": "spirit_awakening_5", "desc": "Heal 2% HP per second for 5 s.", "icon": "concealment"},
        {"id": "wind_blink", "name": "Wind Blink", "unlock": "spirit_awakening_5", "desc": "Blink 120 units; cooldown 10 s.", "icon": "dodge_dash"},
    ])


if __name__ == "__main__":
    build()
