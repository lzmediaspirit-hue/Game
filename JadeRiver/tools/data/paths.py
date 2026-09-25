"""S48 cultivation paths, heart and heaven: body_tiers.json and physiques.json.

The body ladder names what body_level already measures: each tier opens at a body level, is passed by a
Temper trial (a room event at a training ground, see world.py set_pieces) and a medicinal bath (S44), and
gives a lasting gift. Physiques are earned by deeds, never rolled or bought, and each has a drawback.
Gifts are stat modifiers in the StatRules format, applied by StatRules.rebuild.
"""
from common import entries


def mod(stat, value, op="pct_add", **cond):
    m = {"stat": stat, "op": op, "value": value}
    if cond:
        m["condition"] = cond
    return m


def body_tiers():
    rows = [
        {"id": "copper", "name": "Copper Body", "need": 18, "trial": "copper_body_trial", "bath": "copper_body_bath",
         "trial_text": "Stumps and stones on Willow Path West: three minutes of charging beasts without falling below half your HP.",
         "gift_text": "+5% Physical Defense. Body techniques may spend HP when your QI runs short.",
         "modifiers": [mod("physical_defense", 0.05)], "flags": ["hp_techniques"], "teaches": []},
        {"id": "iron", "name": "Iron Body", "need": 36, "trial": "iron_body_trial", "bath": "marrow_washing_bath",
         "trial_text": "Pilgrim Stairs: break five Stone Guardians in a single run before the incense burns down.",
         "gift_text": "+10% knockback resistance.",
         "modifiers": [mod("knockback_resistance", 0.10, "flat")], "flags": [], "teaches": ["jade_marrow_bath"]},
        {"id": "jade", "name": "Jade Body", "need": 54, "trial": "jade_body_trial", "bath": "jade_marrow_bath",
         "trial_text": "The pole trial (Sword Court or East Terrace): ninety seconds on the plum-blossom poles. Touch the ground for more than two seconds and it is over.",
         "gift_text": "Injuries heal 1.5 times as fast.",
         "modifiers": [mod("injury_recovery", 0.5, "flat")], "flags": [], "teaches": ["golden_body_bath"]},
        {"id": "gold", "name": "Gold Body", "need": 72, "trial": "gold_body_trial", "bath": "golden_body_bath",
         "trial_text": "The Lightning Scar in the Azure Expanse: three minutes under the storm among the thunderhorns, never below half your HP.",
         "gift_text": "Immune to Qi Seal.",
         "modifiers": [], "flags": ["qi_seal_immune"], "teaches": []},
    ]
    entries("body_tiers", rows)
    return rows


def physiques():
    rows = [
        {"id": "jade_bone", "name": "Jade Bone Physique", "earned": "flawless_cleansing",
         "earned_text": "Pass Heaven's Cleansing without being struck once.",
         "gift_text": "+10% max HP, +10% toxicity tolerance.", "drawback_text": "−5% Qi Resistance.",
         "modifiers": [mod("max_hp", 0.10), mod("toxicity_tolerance", 0.10), mod("qi_resistance", -0.05)]},
        {"id": "yin_vessel", "name": "Yin Vessel", "earned": "falls_pool_nights", "count": 10,
         "earned_text": "Meditate at the Falls Pool through ten nights.",
         "gift_text": "+15% Yin power, +10% Water power.", "drawback_text": "−10% Fire power.",
         "modifiers": [mod("elemental_power", 0.15, "flat", element="yin"), mod("elemental_power", 0.10, "flat", element="water"),
                       mod("elemental_power", -0.10, "flat", element="fire")]},
        {"id": "ember_heart", "name": "Ember Heart", "earned": "fire_pills", "count": 50,
         "earned_text": "Refine fifty Fire pills.",
         "gift_text": "+15% Fire power.", "drawback_text": "−10% Water power.",
         "modifiers": [mod("elemental_power", 0.15, "flat", element="fire"), mod("elemental_power", -0.10, "flat", element="water")]},
        {"id": "stone_marrow", "name": "Stone Marrow", "earned": "early_copper", "before": "qi_unfurling_3",
         "earned_text": "Reach Copper Body before Qi Unfurling 3.",
         "gift_text": "+15% Physical Defense.", "drawback_text": "−5% move speed.",
         "modifiers": [mod("physical_defense", 0.15), mod("move_speed", -0.05)]},
        {"id": "cloud_lung", "name": "Cloud Lung", "earned": "air_metres", "count": 10000,
         "earned_text": "Glide or fly ten kilometres in all.",
         "gift_text": "+10% flight speed, flight costs 10% less QI.", "drawback_text": "−5% max HP.",
         "modifiers": [mod("flight_speed", 0.10), mod("flight_qi", -0.10, "flat"), mod("max_hp", -0.05)]},
        {"id": "hollow_touched", "name": "Hollow-Touched", "earned": "hollowing_full", "milestone": "v1.2",
         "earned_text": "Survive being wholly Hollowed.",
         "gift_text": "+20% Hollow Ward.", "drawback_text": "Heart-demon gains are 1.5 times as large.",
         "modifiers": [mod("hollow_ward", 0.20, "flat")], "heart_demon_mult": 1.5},
    ]
    entries("physiques", rows)
    return rows


def fates():
    """Breakthrough fates (S48, Part 8): after each major breakthrough three distinct cards are drawn on the
    breakthrough stream and one is chosen. `modifiers` last for life; `realm_modifiers` until the next great realm;
    `effects` apply once, at the choice; `next` is spent by the next tribulation or breakthrough."""
    rows = [
        {"id": "thunder_tempered", "name": "Thunder-Tempered Meridians", "weight": 10,
         "gift_text": "+10% Thunder power.", "cost_text": "+5 heart demon.",
         "modifiers": [mod("elemental_power", 0.10, "flat", element="thunder")], "effects": [{"kind": "add_heart_demon", "amount": 5}]},
        {"id": "hungry_dantian", "name": "Hungry Dantian", "weight": 10,
         "gift_text": "+8% accumulation this realm.", "cost_text": "Pill resistance +1 in every family.",
         "realm_modifiers": [mod("accumulation_rate", 0.08, "flat")], "effects": [{"kind": "add_pill_resistance", "amount": 1}]},
        {"id": "quiet_heart", "name": "Quiet Heart", "weight": 10,
         "gift_text": "Heart demon -15.", "cost_text": "-5% insight this realm.",
         "realm_modifiers": [mod("insight_rate", -0.05, "flat")], "effects": [{"kind": "add_heart_demon", "amount": -15}]},
        {"id": "bone_of_the_river", "name": "Bone of the River", "weight": 10,
         "gift_text": "+3 Body.", "cost_text": "-3 Agility.",
         "modifiers": [mod("body", 3, "flat"), mod("agility", -3, "flat")]},
        {"id": "lucky_star", "name": "Lucky Star", "weight": 3, "rare": True,
         "gift_text": "+5 Fortune this realm.", "cost_text": "None.",
         "realm_modifiers": [mod("fortune", 5, "flat")]},
        {"id": "debt_of_heaven", "name": "Debt of Heaven", "weight": 8,
         "gift_text": "Purity one grade better.", "cost_text": "The next heavenly tribulation brings 2 more bolts.",
         "requires": {"all": [{"kind": "realm_at_least", "realm": "cloud_stride_1"}]},
         "effects": [{"kind": "add_purity_grade", "amount": 1}], "next": {"tribulation_bolts": 2}},
        {"id": "wandering_eye", "name": "Wandering Eye", "weight": 8,
         "gift_text": "One hidden way shows itself in each room you enter.", "cost_text": "-10% Sense radius.",
         "modifiers": [mod("sense_radius", -0.10)], "flags": ["reveal_hidden"],
         "requires": {"all": [{"kind": "realm_at_least", "realm": "spirit_awakening_1"}]}},
        {"id": "iron_will", "name": "Iron Will", "weight": 10,
         "gift_text": "+10 Will.", "cost_text": "-5% move speed this realm.",
         "modifiers": [mod("will", 10, "flat")], "realm_modifiers": [mod("move_speed", -0.05)]},
        {"id": "fox_spirits_favour", "name": "Fox Spirit's Favour", "weight": 8, "available": False,
         "gift_text": "Your next pet egg hatches with +10 purity.", "cost_text": "-5% max QI this realm.",
         "realm_modifiers": [mod("max_qi", -0.05)], "note": "Offered once pets have purity (S46)."},
        {"id": "scar_of_failure", "name": "Scar of Failure", "weight": 8,
         "gift_text": "+10% success on your next breakthrough.", "cost_text": "You start this realm Unstable.",
         "effects": [{"kind": "set_stability", "word": "unstable"}], "next": {"breakthrough_bonus": 0.10}},
        {"id": "blood_memory", "name": "Blood Memory", "weight": 8,
         "gift_text": "+5% crit chance.", "cost_text": "Heart demon +1 for every streak of 10 kills.",
         "modifiers": [mod("crit_chance", 0.05, "flat")], "flags": ["streak_heart_demon"]},
        {"id": "dao_echo", "name": "Dao Echo", "weight": 8,
         "gift_text": "+20% insight in your strongest Dao.", "cost_text": "-10% insight in every other Dao.",
         "flags": ["dao_echo"], "requires": {"all": [{"kind": "unlock", "system": "dao_tree"}]}},
    ]
    entries("fates", rows, offer=3, streak={"kills": 10, "window_s": 10.0})
    return rows


def tribulations():
    """Heavenly tribulation (S48, Part 8): 3 bolts into Spirit Awakening, 6 into Heaven Glimpse, 9 into Sage, then
    waves of 9 (2 into Sage Sovereign, one more for each great realm after). +1 bolt per 25 heart demon and per 100
    sin. Damage is 20% of max HP x (1 + sin / 500) x (1 + heart demon / 200); guarding halves it; cover does not help."""
    ladder = ["cloud_stride_9", "spirit_awakening_9", "heaven_glimpse_3", "sage_3", "sage_sovereign_3", "will_manifest_3", "sphere_lord_3",
              "law_touching_3", "monarch_3", "half_heaven_monarch", "dao_sigil", "heavens_threshold", "inner_heaven_9"]
    rows = []
    for i, frm in enumerate(ladder):
        bolts = [3, 6, 9][i] if i < 3 else 9
        waves = 1 if i < 3 else i - 1
        rows.append({"id": frm, "from": frm, "bolts": bolts, "waves": waves})
    entries("tribulations", rows, per_heart_demon=25, per_sin=100, damage_pct=0.20, sin_div=500, heart_div=200, guard=0.5,
            warn_s=1.0, radius=80, depth=45, gap_s=[0.7, 1.4], wave_pause_s=3.0, first_s=2.0, spread=60,
            survive_hp=0.1)
    return rows


def inner_arts(write=True):
    """Inner Arts (S48, Part 8): passive arts learned from manuals, worn in slots (2 at Qi Unfurling 1, 3 at Heart
    Tempering 1, 4 at Spirit Awakening 1). A weapon-linked art (`family`) works only with that weapon in hand."""
    rows = [
        {"id": "riverflow_circulation", "name": "Riverflow Circulation", "desc": "+10% QI regeneration.",
         "modifiers": [mod("qi_regen", 0.10)], "price": 150, "realm": "qi_unfurling_1"},
        {"id": "iron_shirt", "name": "Iron Shirt", "desc": "+8% Physical Defense.",
         "modifiers": [mod("physical_defense", 0.08)], "price": 150, "realm": "qi_unfurling_1"},
        {"id": "swallows_breath", "name": "Swallow's Breath", "desc": "Dodge cooldown 15% shorter.",
         "modifiers": [mod("dodge_cooldown", -0.15, "flat")], "price": 200, "realm": "qi_unfurling_1"},
        {"id": "sword_heart", "name": "Sword Heart", "desc": "Jian only: Sword Intent builds to 12 instead of 10.",
         "family": "jian", "flags": {"sword_intent_max": 12}, "price": 400, "realm": "heart_tempering_1"},
        {"id": "stone_root", "name": "Stone Root", "desc": "Guard blocks 10% more.",
         "modifiers": [mod("guard", 0.10)], "price": 200, "realm": "qi_unfurling_1"},
        {"id": "clear_lake", "name": "Clear Lake", "desc": "+10% insight.",
         "modifiers": [mod("insight_rate", 0.10, "flat")], "price": 300, "realm": "heart_tempering_1"},
        {"id": "hunters_patience", "name": "Hunter's Patience", "desc": "Bow only: the draw is 10% quicker.",
         "family": "bow", "modifiers": [mod("attack_speed", 0.10, "flat")], "price": 200, "realm": "qi_unfurling_1"},
        {"id": "ember_channel", "name": "Ember Channel", "desc": "Fire techniques cost 10% less QI.",
         "modifiers": [mod("technique_cost", 0.10, "flat", element="fire")], "price": 300, "realm": "heart_tempering_1"},
    ]
    if write:
        entries("inner_arts", rows, slots=[["qi_unfurling_1", 2], ["heart_tempering_1", 3], ["spirit_awakening_1", 4]])
    return rows


def stances():
    """Stances (S48, Part 8): one toggle per weapon family, set on the Techniques page; it holds only with that
    weapon in hand. Willow Leaf Parry, the jian's, keeps its technique as well."""
    rows = [
        {"id": "willow_leaf_parry", "family": "jian", "name": "Willow Leaf Parry", "desc": "A parry counters for 200%. Attacks 10% slower.",
         "modifiers": [mod("attack_speed", -0.10, "flat")], "flags": {"parry_counter": 2.0}},
        {"id": "iron_horse", "family": "gauntlets", "name": "Iron Horse", "desc": "Nothing knocks you back; 20% slower on foot.",
         "modifiers": [mod("move_speed", -0.20)], "flags": {"knockback_immune": True}},
        {"id": "coiled_dragon", "family": "spear", "name": "Coiled Dragon", "desc": "+15% reach.", "flags": {"reach_mult": 1.15}},
        {"id": "low_shadow", "family": "short_blade", "name": "Low Shadow", "desc": "+10% crit chance on a foe's back.",
         "flags": {"backstab_crit": 0.10}},
        {"id": "mountain_root", "family": "staff", "name": "Mountain Root", "desc": "Guard blocks 10% more.", "modifiers": [mod("guard", 0.10)]},
        {"id": "still_draw", "family": "bow", "name": "Still Draw", "desc": "+15% damage while you stand still.", "flags": {"still_damage": 0.15}},
    ]
    entries("stances", rows)
    return rows


def combos():
    """Combo pairs (S48, Part 8): technique A, then B within a second, and B carries a follow-up."""
    rows = [
        {"id": "palm_into_rush", "first": "flowing_palm", "second": "tiger_rush", "effect": {"kind": "shockwave", "mult": 0.6, "radius": 120},
         "desc": "Flowing Palm, then Tiger Rush: a shockwave follows the rush."},
        {"id": "stroke_into_arc", "first": "cloudpiercing_stroke", "second": "crescent_arc", "effect": {"kind": "extra_target", "value": 1, "range": 1.15},
         "desc": "Cloudpiercing Stroke, then Crescent Arc: the arc reaches one foe more and 15% further."},
        {"id": "thrust_into_sweep", "first": "jade_thrust", "second": "dragon_tail_sweep", "effect": {"kind": "pull", "value": 90},
         "desc": "Jade Thrust, then Dragon Tail Sweep: the sweep pulls its targets in."},
        {"id": "slash_into_flick", "first": "reedcutter_slash", "second": "shadow_flick", "effect": {"kind": "bleed", "power": 0.02, "duration_s": 4},
         "desc": "Reedcutter Slash, then Shadow Flick: the bleed is laid fresh."},
        {"id": "sweep_into_toll", "first": "riverstone_sweep", "second": "bell_toll_strike", "effect": {"kind": "stun", "bonus_s": 0.3},
         "desc": "Riverstone Sweep, then Bell Toll Strike: the toll stuns for certain, 0.3 s longer."},
        {"id": "shot_into_pin", "first": "twin_reed_shot", "second": "pinning_arrow", "effect": {"kind": "root", "bonus_s": 0.5},
         "desc": "Twin Reed Shot, then Pinning Arrow: the root holds 0.5 s longer."},
    ]
    entries("combos", rows, window_s=1.0)
    return rows


def build():
    body_tiers()
    physiques()
    fates()
    tribulations()
    inner_arts()
    stances()
    combos()
