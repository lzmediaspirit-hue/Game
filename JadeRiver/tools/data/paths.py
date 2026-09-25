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


def build():
    body_tiers()
    physiques()
