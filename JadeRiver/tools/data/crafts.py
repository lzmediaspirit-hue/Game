"""S16 professions.json and formations.json, plus S25 defence events.

Every number the WorkshopAuthority, PetAuthority (eggs, taming) and SectAuthority
(defence) read lives here: costs, daily limits, timers, result tables and blueprint
effects. Items named here are defined in items.py.
"""
from common import entries, write


def build():
    professions = [
        {"id": "appraisal", "name": "Appraisal", "unlock": "appraisal", "teacher": "elder_gu",
         "tool": "appraisers_loupe", "stations": ["appraiser"],
         # Unknown curios: what they turn out to be (named Rng stream "crafting").
         "results": [{"item": "jade_trinket", "weight": 3}, {"item": "string_of_old_coins", "weight": 4},
                     {"item": "spirit_stone_shard", "weight": 2, "count": 3}, {"item": "fake_jade", "weight": 4},
                     {"item": "manual_page", "weight": 1}],
         "insight_per_use": 2.0, "xp_per_use": 8},
        {"id": "healing", "name": "Healing", "unlock": "healing", "teacher": "jade_physician",
         "tool": "needle_case", "npcs": ["jade_physician", "cloud_physician"],
         "patients_per_day": 5, "qi_cost_pct": 0.15, "contribution": 20, "xp_per_use": 12,
         "ailments": ["a twisted meridian", "Qi deviation", "a cracked rib", "grey fever", "a burned palm"]},
        {"id": "puppetry", "name": "Puppetry", "unlock": "puppetry", "teacher": "tinkerer_yu",
         "npcs": ["tinkerer_yu"], "max_puppets": 2,
         "blueprints": [{"id": "worker_puppet", "name": "Worker Puppet", "job": "mining",
                         "inputs": [{"item": "spirit_wood", "count": 4}, {"item": "puppet_core", "count": 1}],
                         "yield": [{"item": "copper_ore", "per_hour": 3}, {"item": "riverstone", "per_hour": 1}], "cap_hours": 8},
                        {"id": "carrier_puppet", "name": "Carrier Puppet", "job": "herbs",
                         "inputs": [{"item": "spirit_wood", "count": 6}, {"item": "puppet_core", "count": 1}],
                         "yield": [{"item": "willow_moss", "per_hour": 3}, {"item": "ember_pepper", "per_hour": 1}], "cap_hours": 8}],
         "xp_per_use": 20},
        {"id": "research", "name": "Research", "unlock": "research", "teacher": "jade_librarian",
         "npcs": ["jade_librarian", "cloud_librarian"], "inputs": [{"item": "torn_manual", "count": 1}, {"item": "restoration_ink", "count": 1}],
         "results": [{"item": "manual_rain_of_reeds", "weight": 2}, {"item": "manual_ember_burst", "weight": 2},
                     {"item": "manual_page", "weight": 5, "count": 2}, {"item": "manual_page", "weight": 1, "count": 3}],
         "insight_dao": "soul", "insight_per_use": 5.0, "xp_per_use": 25},
        {"id": "teaching", "name": "Teaching", "unlock": "teaching", "teacher": "elder_hu",
         "min_dao_tier": 2, "cooldown_hours": 20, "disciple_levels": 2, "insight_per_use": 8.0, "prestige": 10, "xp_per_use": 30},
        {"id": "formations", "name": "Formations", "unlock": "formations", "teacher": "jade_formation_elder",
         "tool": "formation_kit", "max_active": 2, "xp_per_use": 15},
    ]
    entries("professions", professions)

    formations = [
        {"id": "gathering", "name": "Gathering Formation", "unlock": "formations", "nodes": 3,
         "fuel": "fuel_crystal_low", "fuel_per_node": 1, "hours_per_crystal": 2.0, "max_hours": 24,
         "effect": {"qi_density": 0.5}, "desc": "Thickens the Qi in this room while fuelled."},
        {"id": "protection", "name": "Protection Formation", "unlock": "formations", "nodes": 3,
         "fuel": "fuel_crystal_low", "fuel_per_node": 1, "hours_per_crystal": 1.0, "max_hours": 6,
         "effect": {"defense_pct": 0.15}, "desc": "A barrier: +15% defence while you stay in this room."},
        {"id": "guard", "name": "Guard Formation", "unlock": "guard_formation", "nodes": 5,
         "fuel": "fuel_crystal_low", "fuel_per_node": 1, "hours_per_crystal": 1.0, "max_hours": 6,
         "effect": {"breakthrough_risk_step": -1}, "desc": "Nothing interrupts, nothing surprises: breakthrough risk one step lower."},
        # Library floor 3 blueprints (Spirit Awakening): Restraint slows monsters, Concealment hides you from them.
        {"id": "restraint", "name": "Restraint Formation", "unlock": "advanced_formations", "nodes": 4,
         "fuel": "fuel_crystal_low", "fuel_per_node": 1, "hours_per_crystal": 0.5, "max_hours": 2,
         "effect": {"enemy_slow": 0.3}, "desc": "Binding lines: monsters in this room move 30% slower."},
        {"id": "concealment", "name": "Concealment Formation", "unlock": "advanced_formations", "nodes": 5,
         "fuel": "fuel_crystal_low", "fuel_per_node": 1, "hours_per_crystal": 1.0, "max_hours": 5,
         "effect": {"conceal": 1.0}, "desc": "A veil: monsters here do not notice you unless you strike first."},
    ]
    entries("formations", formations)

    # Eggs (S22): hatch time and what may come out, weighted.
    write("eggs.json", {"schema_version": 1, "hatch_hours": [2, 24], "max_incubating": 1,
                    "species": [{"species": "reed_otter", "weight": 3}, {"species": "ember_fox", "weight": 3},
                                {"species": "jade_crane", "weight": 2}, {"species": "mossback_toad", "weight": 2}]})
    # Taming (S22): chance from offering grade, realm gap and Beast Taming Dao tier.
    write("taming.json", {"schema_version": 1, "hp_below": 0.3, "base": 0.35,
                      "offering_bonus": {"bonding_offering_common": 0.0, "bonding_offering_earth": 0.2, "bonding_offering_heaven": 0.35},
                      "per_level_over": 0.03, "per_level_under": -0.08, "per_dao_tier": 0.05, "min": 0.05, "max": 0.95,
                      "offerings": ["bonding_offering_common", "bonding_offering_earth", "bonding_offering_heaven"]})
    # Defence events (S25): the tutorial raid for "Walls of the Vale", then one every 2-3 days from sect level 6.
    write("defence.json", {"schema_version": 1, "room": "hv_sect_grounds", "from_level": 6, "interval_days": [2, 3],
                       "duration": 60, "waves": [{"enemy": "mudwater_bandit", "every_s": 5, "max": 4},
                                                 {"enemy": "mud_hound", "every_s": 5, "max": 5},
                                                 {"enemy": "hollow_stag", "every_s": 4, "max": 4}],
                       "points": [[300, 860], [1500, 860], [2600, 860]],
                       "prestige_win": 40, "taels_win": 200, "per_disciple_guard": 0.1,
                       "damaged_output": 0.5, "repair_cost_fraction": 0.25})
