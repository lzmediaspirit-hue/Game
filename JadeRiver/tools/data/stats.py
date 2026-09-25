"""S10/S11/S12/S13/S14/S29 constants: stats.json, curves.json, elements, statuses, weapon families,
grades, affixes, sets, injuries, failures, origins, methods."""
from common import write, entries

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
]


def build():
    write("stats.json", {
        "pools": {
            "hp": {"a": 50, "b": 20, "c": 0.9, "from_level": 0},
            "qi": {"a": 20, "b": 8, "c": 0.5, "from_realm": "bone_forging_7"},
            "soul": {"a": 100, "b": 10, "c": 0.4, "offset": 46, "from_realm": "spirit_awakening_1"},
        },
        "regen_per_s": {"hp": 0.005, "qi": 0.0075, "soul": 0.00375, "combat_delay_s": 5, "meditate_mult": 8, "rest_mult": 4},
        "attributes": {"base": 5, "per_level": 1, "body_per_body_level": 1, "essence_per_purity_grade": 3,
                       "spirit_per_soul_points": 0.1, "insight_per_dao_tier": 2, "essence_per_capacity": 10},
        "attribute_effects": {
            "body": {"max_hp_pct": 0.01, "physical_defense": 0.5, "body_weapon_attack_pct": 0.003, "toxicity_tolerance": 0.1},
            "agility": {"move_speed_pct": 0.001, "attack_speed": 0.002, "crit_chance": 0.001, "accuracy": 1.0, "evasion": 0.5},
            "essence": {"max_qi_pct": 0.01, "qi_attack_pct": 0.005, "technique_cost": 0.001, "qi_resistance": 0.3, "qi_regen": 0.005},
            "spirit": {"max_soul_pct": 0.01, "soul_defense": 0.5, "soul_attack_pct": 0.005, "sense_radius_pct": 0.01, "will": 1.0, "tenacity": 0.002},
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
        "move": {"base": 205, "sprint": 1.7, "sprint_after_s": 2.0, "cap_pct": 0.4, "attack_factor": 0.3, "guard_factor": 0.5,
                 "shallows_factor": 0.7},
        # S14 binding (Spirit Awakening 3): a found relic's stats stay sealed until it is bound (a channel by
        # grade, broken by a hit); its Artifact Spirit wakes through a soul contest (Spirit against strength).
        "binding": {"unlock": "binding", "seconds": {"plain": 4, "common": 6, "earth": 12, "heaven": 20, "mystic": 30},
                    "spirit_chance": [0.1, 0.9], "spirit_cooldown_s": 60, "soul_injury": 1},
        # S18 flight (Cloud Stride 1): QI per second is a share of the pool (with a floor); take off needs a
        # little QI in hand. Climb in px/s, ceiling in px of altitude.
        "flight": {"unlock": "flight", "qi_pct_per_s": 0.02, "qi_min_per_s": 2.0, "start_qi_pct": 0.1, "climb": 220, "ceiling": 340},
        # S18: A_dealt = min(cap, floor + slope x attunement / required); A_taken = 1 + max(0, 1 - attunement / required)
        "attunement": {"floor": 0.3, "slope": 0.7, "cap": 1.1},
        "crit": {"base": 0.05, "per_agility": 0.001, "per_fortune": 0.0005, "cap": 0.75, "damage_base": 1.5, "damage_cap": 3.0,
                 "tenacity_divisor": 4},
        "hit": {"base": 1.1, "k": 0.35, "floor": 0.55, "cap": 1.0},
        "defence": {"k_flat": 100, "k_level": 15, "cap": 0.75},
        "realm_gap": {"up_per_realm": 0.25, "up_cap": 1.0, "down_per_realm": 0.20, "down_max_reduction": 0.60},
        "energy_multiplier": {"none": 1.0, "body": 1.0, "primal_qi": 1.0, "true_qi": 1.3, "sage_qi": 1.7, "law_qi": 2.2,
                              "monarch_qi": 2.8, "heavenforce": 3.5},
        "purity_bonus_per_grade": 0.025,
        "kill_gap_factor": [{"min_diff": 5, "mult": 1.2}, {"min_diff": -4, "mult": 1.0}, {"min_diff": -9, "mult": 0.5},
                            {"min_diff": -999, "mult": 0.1}],
        "technique_cost": {"per_level": 0.04, "composure_zero_factor": 1.5, "mastery_cost_per_tier": -0.05,
                           "mastery_damage_per_tier": 0.08, "dao_damage_per_tier": 0.05},
        "cp": {"hp_div": 10, "attack_weight": 0.5, "defence_div": 4},
        "equipment": {"weapon_attack": {"a": 8, "b": 3, "c": 0.12}, "armour_defence": {"a": 4, "b": 1.5, "c": 0.05},
                      "enhance_per_level": 0.05, "fist_weapon_pct": 0.6,
                      "slot_share": {"robe": 0.4, "trousers": 0.3, "boots": 0.15, "hat": 0.15},
                      "energy_type_penalty": 0.5},
        "mob": {"hp": {"a": 30, "b": 15, "c": 1.1}, "attack": {"a": 5, "b": 2.2, "c": 0.1}, "accuracy": {"a": 10, "b": 3},
                "evasion_pct": 0.3, "agile_evasion_pct": 0.6,
                "roles": {"normal": {"hp": 1, "attack": 1, "defence": 0.8}, "elite": {"hp": 6, "attack": 1.5, "defence": 1.2},
                          "field_boss": {"hp": 40, "attack": 2, "defence": 1.5}, "dungeon_boss": {"hp": 80, "attack": 2.2, "defence": 1.5},
                          "story_boss": {"hp": 20, "attack": 1.6, "defence": 1.2}, "event": {"hp": 0.4, "attack": 0.8, "defence": 0.5},
                          "trial": {"hp": 3, "attack": 0.7, "defence": 1.0}},
                "own_element_resistance": 0.3, "overcome_element_resistance": 0.15},
        "combat": {"hitstop": 0.05, "hitstop_crit": 0.1, "knockback_light": 20, "knockback_heavy": 80, "flinch_pct": 0.2,
                   "flinch_s": 0.4, "leash": 600, "shrine_sanctuary": 240, "threat_heal": 1.5, "spawn_protection_s": 1.5, "depth_band": 26,
                   "auto_turn_range": 160, "backlash_stun_s": 1.0, "backlash_qi_pct": 0.05, "dodge_distance": 140,
                   "dodge_invuln_s": 0.25, "dodge_cooldown_s": 2.5, "parry_stagger_s": 0.8, "parry_stagger_boss_s": 0.3,
                   "combo_window_s": 0.5, "steadfast_s": 8, "vulnerable": 0.2, "shock": 0.2, "status_duration_tenacity": 0.5},
        "death": {"progress_loss": 0.10, "wake_hp": 0.5, "talisman_hp": 0.3, "talisman_invuln_s": 5, "talisman_cooldown_s": 300},
        "toxicity": {"tolerance_base": 30, "drain_per_min": 1, "meditate_drain_mult": 2, "repeat_window_s": 300,
                     "repeat_factor": 0.5},
        "hollowing": {"valley_cap": 49, "decay_per_min": 1, "meditate_mult": 3},
        "composure": {"max": 100, "recover_per_s": 10, "recover_delay_s": 3, "meditate_full_s": 5},
        "grade_bands": [["plain", 1, 9], ["common", 10, 18], ["earth", 19, 36], ["heaven", 37, 54], ["mystic", 55, 63],
                        ["spirit", 64, 72], ["sage", 73, 81], ["sovereign", 82, 90], ["will", 91, 99], ["sphere", 100, 108],
                        ["law", 109, 120], ["monarch", 121, 140], ["inner_heaven", 141, 165]],
        "stats": [{"id": s, "group": g, "cap": cap, "format": f} for (s, g, cap, f) in STAT_LIST],
    })

    # S38 balance simulator: how an active hour is spent, and the Part 4 pacing table it must meet (±15%).
    write("balance.json", {
        "schema_version": 1,
        # A normal mixed session (S29 "about 100 QP per active minute" with quests): the rest is travel,
        # dialogue, crafting, shops and the sect, which earn no realm progress themselves.
        "mix": {"fight": 0.35, "meditate": 0.25, "other": 0.4},
        "kills_per_min": 6,
        "dailies_per_hour": 1.0,
        "prologue_hours": 0.5,
        "stability": "stable",
        # Where a mixed session sits to cultivate: mostly the field rooms it fights in (1.0), sometimes Lu's
        # boat (1.4), the mentor's peak (1.6) or, later, a hidden spring (2.2).
        "density": {"bone_forging": 1.2, "qi_kindling": 1.25, "qi_unfurling": 1.3, "heart_tempering": 1.4, "cloud_stride": 1.4,
                    "spirit_awakening": 1.45, "heaven_glimpse": 1.5},
        "method": {"bone_forging": "riverbreath_fragment", "qi_kindling": "jade_current_scripture", "qi_unfurling": "jade_current_scripture",
                   "heart_tempering": "cloudpiercing_canon", "cloud_stride": "willow_breath_art", "spirit_awakening": "willow_breath_art",
                   "heaven_glimpse": "tidal_sovereign_scripture"},
        "tolerance": 0.15,
        # S39 checks: [Level, the next upgrade, the spec's taels per hour there]; affordable within 1-2 h (±25%).
        "upgrades": [[15, "iron_jian", 850], [25, "jadeiron_robe", 1700]], "afford_hours": [0.75, 2.5],
        "act_end": "heaven_glimpse_3", "act_end_hours": 65,
        "pacing": [["bone_forging_1", 0.5], ["qi_kindling_1", 5], ["qi_unfurling_1", 13], ["heart_tempering_1", 20],
                   ["cloud_stride_1", 30], ["spirit_awakening_1", 42], ["heaven_glimpse_1", 55]],
    })
    write("curves.json", {
        "qp_minutes": "see realms.json accumulate_needed = 100 x target minutes per Level",
        "kill_qp": 22, "kill_role_mult": {"normal": 1, "elite": 6, "field_boss": 40, "dungeon_boss": 80, "story_boss": 40, "event": 0.5, "trial": 2},
        "meditation_qp_per_min": 60, "meditation_body_stage_factor": 0.3, "body_stage_until": "bone_forging_6",
        "qi_spring_mult": 2, "training_qp_per_min": 40, "training_body_xp_per_min": 20,
        "quest_qp_pct": {"guided": 0.15, "main": 0.25, "side": 0.10, "daily": 0.05, "prologue": 0.0},
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
        "profession_xp": {"craft_per_grade": 10, "fine_bonus": 0.5, "gather": 10, "mine": 10, "fish": 12, "cook": 8},
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
                   "hollow_wood": "wood"},
        "neutral": ["space", "time", "soul", "life_death", "hollow", "none"],
        "cycle_advantage": 1.3, "cycle_disadvantage": 0.75, "yin_yang": 1.3, "fed_bonus": 0.1, "method_affinity_bonus": 0.1,
        "colors": {"water": "#32bed1", "wood": "#67d67a", "fire": "#f08a3c", "earth": "#c9a060", "metal": "#d8dde0",
                   "wind": "#cfe8e6", "thunder": "#e8d24c", "soul": "#9b78d1", "hollow": "#87949a", "none": "#e8e1cf",
                   "ice": "#a8e0f0"},
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
        {"id": "spawn_protection", "resist": "none", "invulnerable": True, "icon": "spawn_protection"},
    ])

    entries("weapon_families.json", [
        {"id": "fists", "appearance": ["none"], "range": [0.9, 1.1], "hits_per_s": 1.4, "reach": 46, "crit": 0.05,
         "scales": ["body", "agility"], "guard": 0.30, "parry_s": 0.18, "dao": "fist", "hud_glyph": "fist",
         "third_hit_bonus": 0.2, "depth": 30, "altitude": [0, 90],
         "combo": [{"action": "punch_1", "duration": 0.42, "hit_at": 0.2, "mult": 1.0},
                   {"action": "punch_2", "duration": 0.45, "hit_at": 0.22, "mult": 1.0},
                   {"action": "punch_3", "duration": 0.55, "hit_at": 0.28, "mult": 1.2, "knockback": 20}]},
        {"id": "gauntlets", "appearance": ["none"], "range": [0.9, 1.1], "hits_per_s": 1.4, "reach": 50, "crit": 0.05,
         "scales": ["body", "agility"], "guard": 0.30, "parry_s": 0.18, "dao": "fist", "hud_glyph": "fist",
         "third_hit_bonus": 0.2, "depth": 30, "altitude": [0, 90],
         "combo": [{"action": "punch_1", "duration": 0.42, "hit_at": 0.2, "mult": 1.0},
                   {"action": "punch_2", "duration": 0.45, "hit_at": 0.22, "mult": 1.0},
                   {"action": "punch_3", "duration": 0.55, "hit_at": 0.28, "mult": 1.2, "knockback": 20}]},
        {"id": "jian", "appearance": ["sword"], "range": [0.85, 1.15], "hits_per_s": 1.1, "reach": 78, "crit": 0.03,
         "scales": ["agility", "essence"], "guard": 0.40, "parry_s": 0.25, "dao": "sword", "hud_glyph": "jian", "depth": 30,
         "altitude": [0, 110], "qi_arc_discount": 0.1,
         "combo": [{"action": "swing_1", "duration": 0.55, "hit_at": 0.26, "mult": 1.0},
                   {"action": "swing_2", "duration": 0.6, "hit_at": 0.28, "mult": 1.05},
                   {"action": "swing_3", "duration": 0.72, "hit_at": 0.36, "mult": 1.25, "knockback": 20}]},
        {"id": "spear", "appearance": ["spear"], "range": [0.8, 1.2], "hits_per_s": 0.9, "reach": 116, "crit": 0.0,
         "scales": ["body", "agility"], "guard": 0.35, "parry_s": 0.18, "dao": "spear", "hud_glyph": "spear", "depth": 26,
         "altitude": [0, 100], "penetration": 0.10, "line_targets": 2,
         "combo": [{"action": "thrust_1", "duration": 0.6, "hit_at": 0.3, "mult": 1.0},
                   {"action": "thrust_2", "duration": 0.65, "hit_at": 0.32, "mult": 1.05},
                   {"action": "thrust_3", "duration": 0.8, "hit_at": 0.42, "mult": 1.3, "knockback": 40}]},
        {"id": "short_blade", "appearance": ["dagger"], "range": [0.7, 1.3], "hits_per_s": 1.3, "reach": 52, "crit": 0.10,
         "scales": ["agility", "fortune"], "guard": 0.25, "parry_s": 0.15, "dao": "blade", "hud_glyph": "short_blade", "depth": 28,
         "altitude": [0, 90], "backstab": 1.5,
         "combo": [{"action": "thrust_1", "duration": 0.42, "hit_at": 0.2, "mult": 1.0},
                   {"action": "thrust_2", "duration": 0.45, "hit_at": 0.22, "mult": 1.0},
                   {"action": "thrust_3", "duration": 0.55, "hit_at": 0.3, "mult": 1.2}]},
        {"id": "staff", "appearance": ["staff"], "range": [0.9, 1.1], "hits_per_s": 0.8, "reach": 96, "crit": 0.0,
         "scales": ["body", "essence"], "guard": 0.50, "parry_s": 0.20, "dao": "staff", "hud_glyph": "staff", "depth": 32,
         "altitude": [0, 110], "knockback_every_hit": 30, "qi_attack_bonus": 0.1,
         "combo": [{"action": "thrust_1", "duration": 0.66, "hit_at": 0.34, "mult": 1.0, "knockback": 30},
                   {"action": "thrust_2", "duration": 0.7, "hit_at": 0.36, "mult": 1.05, "knockback": 30},
                   {"action": "thrust_3", "duration": 0.85, "hit_at": 0.45, "mult": 1.3, "knockback": 60}]},
        {"id": "bow", "appearance": ["bow"], "range": [0.75, 1.25], "hits_per_s": 0.9, "reach": 480, "crit": 0.05,
         "scales": ["agility", "insight"], "guard": 0.0, "parry_s": 0.0, "dao": "bow", "hud_glyph": "bow", "depth": 26,
         "altitude": [20, 110], "ranged": True, "projectile_speed": 620,
         "combo": [{"action": "bow", "duration": 1.1, "hit_at": 0.55, "mult": 1.0, "projectile": "arrow"}]},
    ])

    write("grades.json", {
        "order": ["plain", "common", "earth", "heaven", "mystic", "spirit", "sage", "sovereign", "will", "sphere", "law", "monarch", "inner_heaven"],
        "qualities": {"flawed": {"mult": 0.8, "affixes": 0}, "common": {"mult": 1.0, "affixes": 0}, "fine": {"mult": 1.1, "affixes": 1},
                      "superior": {"mult": 1.2, "affixes": 2}, "perfect": {"mult": 1.3, "affixes": 3}, "relic": {"mult": 1.35, "affixes": 3}},
        "quality_order": ["flawed", "common", "fine", "superior", "perfect", "relic"],
        "quality_colors": {"flawed": "#9aa3a3", "common": "#e8e1cf", "fine": "#67d67a", "superior": "#5aa7e8", "perfect": "#b07ce8",
                           "relic": "#e5b84c", "pill_grain": "#e5b84c", "pill_halo": "#e8764c", "pill_soul": "#f2e6ff"},
        "grade_colors": {"plain": "#b9b2a0", "common": "#e8e1cf", "earth": "#67d67a", "heaven": "#6fb8f0", "mystic": "#b07ce8"},
        "pill_qualities": {"flawed": 0.5, "common": 1.0, "fine": 1.2, "superior": 1.4, "perfect": 1.6, "pill_grain": 1.8, "pill_halo": 2.0, "pill_soul": 2.2},
        # S15 pill qualities: toxicity multipliers, the odds of a rare quality on a perfect run
        # (times 1 + furnace bonus + 0.1 per Alchemy Dao tier), Halo growth in dense-Qi seclusion,
        # and the unique effects a Pill Soul may carry.
        "pill": {
            "toxicity": {"flawed": 1.5, "pill_grain": 0.5},
            "rare": {"pill_grain": 0.2, "pill_halo": 0.06, "pill_soul": 0.015},
            "halo": {"min_density": 2.0, "per_hour": 0.05, "cap": 0.5},
            "soul": {"chance": 0.5, "effects": [
                {"id": "clear_mind", "kind": "add_modifier", "stat": "insight", "op": "flat", "value": 10, "duration": 1800, "source": "pill_soul"},
                {"id": "steady_heart", "kind": "add_composure", "amount": 25},
                {"id": "mend_meridians", "kind": "cure_injury", "injury": "meridian", "max_severity": 2},
                {"id": "iron_skin", "kind": "add_modifier", "stat": "physical_defense", "op": "pct_add", "value": 0.1, "duration": 1800, "source": "pill_soul"},
            ]},
        },
        "sockets": {"plain": 0, "common": 0, "earth": 1, "heaven": 1, "mystic": 2},
        "wear_level": {"plain": 0, "common": 10, "earth": 19, "heaven": 37, "mystic": 55},
    })

    entries("affixes.json", [
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
    ])

    entries("sets.json", [
        {"id": "jade_current", "pieces": ["jade_current_hat", "jade_current_robe", "jade_current_trousers", "jade_current_boots"],
         "bonuses": {"2": [{"stat": "max_qi", "op": "pct_add", "value": 0.05}], "4": [{"stat": "elemental_power", "op": "flat", "value": 0.1, "condition": {"element": "water"}}]}},
        {"id": "cloudpiercing", "pieces": ["cloudpiercing_hat", "cloudpiercing_robe", "cloudpiercing_trousers", "cloudpiercing_boots"],
         "bonuses": {"2": [{"stat": "move_speed", "op": "pct_add", "value": 0.05}], "4": [{"stat": "elemental_power", "op": "flat", "value": 0.1, "condition": {"element": "wind"}}]}},
        {"id": "mudwater", "pieces": ["mudwater_cleaver", "mudwater_robe"], "bonuses": {"2": [{"stat": "coin_find", "op": "flat", "value": 0.1}]}},
        {"id": "drowned_abbot", "pieces": ["drowned_hat", "drowned_robe", "drowned_boots"],
         "bonuses": {"2": [{"stat": "soul_defense", "op": "pct_add", "value": 0.1}], "3": [{"stat": "qi_resistance", "op": "pct_add", "value": 0.1}]}},
        {"id": "crane", "pieces": ["crane_robe", "crane_trousers", "crane_boots"],
         "bonuses": {"2": [{"stat": "flight_speed", "op": "pct_add", "value": 0.05}], "3": [{"stat": "flight_speed", "op": "pct_add", "value": 0.1}]}},
    ])

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

    entries("origins.json", [
        {"id": "fishers_child", "bonus": {"body": 3, "essence": 2}, "element_nudge": "water"},
        {"id": "scholars_heir", "bonus": {"insight": 5}, "element_nudge": ""},
        {"id": "temple_foundling", "bonus": {"spirit": 5}, "element_nudge": ""},
        {"id": "smiths_apprentice", "bonus": {"body": 3, "insight": 2}, "element_nudge": "metal"},
    ])

    entries("methods.json", [
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
    ])


if __name__ == "__main__":
    build()
