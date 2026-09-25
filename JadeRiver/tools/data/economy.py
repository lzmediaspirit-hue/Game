"""Economy and system tables (S20-S26, S33, S34, S39, Part 8):
shops, currencies, recipes, fish, sects, sect_ranks, account_rules, idle_tasks, companions,
pets, pet_traits, achievements, titles, emotes, mission_templates, sect_buildings, sect_levels,
expeditions, disciples, strings/en.json.
"""
import json
import os

from common import DATA, write, entries


def realm(r):
    return {"kind": "realm_at_least", "realm": r}


def unlocked(s):
    return {"kind": "unlock", "system": s}


def all_of(*c):
    return {"all": list(c)}


def shops():
    def s(i, **kw):
        d = {"item": i}
        d.update(kw)
        return d
    rows = [
        {"id": "old_ma", "name": "Old Ma's Store", "currency": "silver_tael", "buys_all": True,
         "stock": [s("herbal_tea", price=6), s("rice_ball", price=4), s("rice", price=2), s("bamboo_rod", requires=all_of(realm("bone_forging_8"))),
                   s("bonding_offering_common", requires=all_of(realm("qi_unfurling_5")))],
         "rotation": {"count": 1, "pool": [s("willow_moss"), s("boar_hide"), s("river_mud"), s("cloth")]}},
        {"id": "granny_liu", "name": "Granny Liu's Herb Hut", "currency": "silver_tael",
         "stock": [s("herbal_tea"), s("willow_salve"), s("revival_talisman"), s("purging_pill", requires=all_of(realm("qi_kindling_2"))),
                   s("calm_incense", requires=all_of(realm("qi_unfurling_9")))]},
        {"id": "stoneford_general", "name": "Stoneford General Store", "currency": "silver_tael", "buys_all": True,
         "stock": [s("herbal_tea"), s("lotus_root_tea"), s("rice_ball"), s("rice"), s("return_charm"), s("herb_sickle", requires=all_of(realm("bone_forging_4"))),
                   s("iron_pickaxe", requires=all_of(realm("bone_forging_5"))), s("bamboo_gourd"), s("escape_talisman"), s("fish_bait"),
                   s("fuel_crystal_low", requires=all_of(realm("heart_tempering_1")))],
         "rotation": {"count": 1, "pool": [s("bamboo_rod"), s("lantern_wick"), s("clay_pot")]}},
        {"id": "stoneford_tea", "name": "Stoneford Tea House", "currency": "silver_tael",
         "stock": [s("lotus_root_tea"), s("jade_carp_congee"), s("rice_ball")],
         "rotation": {"count": 1, "pool": [s("ember_pepper_stew"), s("toad_oil_dumplings"), s("riverfish_soup")]}},
        {"id": "mei_qing", "name": "Mei Qing's Stall", "currency": "silver_tael",
         "stock": [s("willow_moss"), s("riverreed_ginseng_10"), s("healing_pill"), s("qi_restoration_pill"), s("qi_gathering_pill"),
                   s("recipe_scroll", learn="healing_pill"), s("pearl", price=40, requires=all_of(realm("heart_tempering_5"))),
                   s("mist_lotus", price=35, requires=all_of(realm("heart_tempering_5"))),
                   s("cloudtop_orchid", price=120, requires=all_of(realm("cloud_stride_5")))],
         "rotation": {"count": 1, "pool": [s("clear_mind_pill"), s("foundation_guard_pill"), s("bone_strengthening_pill")]}},
        {"id": "mei_qing_recipes", "name": "Mei Qing's Recipe Box", "currency": "silver_tael",
         "stock": [s("recipe_scroll", learn="qi_refining_pill", price=800, requires=all_of(realm("heart_tempering_5")))]},
        {"id": "stoneford_smith", "name": "Stoneford Smith", "currency": "silver_tael", "buys_all": True,
         "stock": [s("training_jian"), s("training_spear"), s("training_gauntlets"), s("training_short_blade"), s("training_staff"), s("training_bow"),
                   s("iron_jian", requires=all_of(realm("qi_kindling_1"))), s("iron_spear", requires=all_of(realm("qi_kindling_1"))),
                   s("iron_gauntlets", requires=all_of(realm("qi_kindling_1"))), s("iron_short_blade", requires=all_of(realm("qi_kindling_1"))),
                   s("iron_staff", requires=all_of(realm("qi_kindling_1"))), s("iron_bow", requires=all_of(realm("qi_kindling_1"))),
                   s("bamboo_hat"), s("cotton_robe"), s("cotton_trousers"), s("cloth_boots"), s("copper_ore"), s("riverstone")],
         "rotation": {"count": 1, "pool": [s("jadeiron_jian"), s("jadeiron_spear"), s("jadeiron_robe"), s("jadeiron_gourd")]}},
        {"id": "tinkerer", "name": "Tinkerer's Workshop", "currency": "silver_tael",
         "stock": [s("iron_pickaxe"), s("herb_sickle"), s("bamboo_rod"), s("clay_pot"), s("drying_rack", requires=all_of(realm("qi_kindling_8"))),
                   s("spirit_wood", price=30, requires=all_of(realm("cloud_stride_5"))), s("puppet_core", price=300, requires=all_of(realm("cloud_stride_5")))]},
        {"id": "gu_trade_house", "name": "Trade House", "currency": "silver_tael",
         "stock": [s("appraisers_loupe", requires=all_of(realm("qi_kindling_6"))), s("dusty_curio", price=20, requires=all_of(realm("qi_kindling_6"))),
                   s("spirit_stone_shard"), s("manual_page", price=400), s("blank_plate", price=60, requires=all_of(realm("heart_tempering_5")))],
         "rotation": {"count": 1, "pool": [s("jadeiron_hat"), s("cloudsilk_robe"), s("jadeiron_gourd")]}},
        {"id": "jade_sect", "name": "Jade Sect Mission Hall", "currency": "contribution",
         "requires": {"all": [{"kind": "training_sect", "sect": "jade_sect"}]},
         "stock": [s("manual_rain_of_reeds", requires=all_of({"kind": "sect_rank_at_least", "rank": "outer_disciple"})),
                   s("healing_pill"), s("qi_restoration_pill"), s("cleansing_pill", requires=all_of(realm("qi_kindling_9"))),
                   s("foundation_guard_pill", requires=all_of(realm("qi_unfurling_1"))), s("clear_mind_pill"), s("revival_talisman"),
                   s("bonding_offering_earth", requires=all_of(realm("qi_unfurling_5"))), s("fuel_crystal_low", requires=all_of(realm("heart_tempering_1"))),
                   s("jade_current_robe", requires=all_of({"kind": "sect_rank_at_least", "rank": "inner_disciple"})),
                   s("manual_stonebody_canon", price=300, requires=all_of({"kind": "sect_rank_at_least", "rank": "inner_disciple"})),
                   s("manual_willow_breath_art", price=300, requires=all_of({"kind": "sect_rank_at_least", "rank": "inner_disciple"})),
                   s("manual_emberheart_sutra", price=300, requires=all_of({"kind": "sect_rank_at_least", "rank": "inner_disciple"})),
                   s("manual_tidal_sovereign_scripture", price=800, requires=all_of({"kind": "sect_rank_at_least", "rank": "core_disciple"}))],
         "rotation": {"count": 1, "pool": [s("manual_page")]}},
        {"id": "cloud_sect", "name": "Cloud Sect Mission Hall", "currency": "contribution",
         "requires": {"all": [{"kind": "training_sect", "sect": "cloud_sect"}]},
         "stock": [s("manual_ember_burst", requires=all_of({"kind": "sect_rank_at_least", "rank": "outer_disciple"})),
                   s("healing_pill"), s("qi_restoration_pill"), s("cleansing_pill", requires=all_of(realm("qi_kindling_9"))),
                   s("foundation_guard_pill", requires=all_of(realm("qi_unfurling_1"))), s("clear_mind_pill"), s("revival_talisman"),
                   s("bonding_offering_earth", requires=all_of(realm("qi_unfurling_5"))), s("fuel_crystal_low", requires=all_of(realm("heart_tempering_1"))),
                   s("cloudpiercing_robe", requires=all_of({"kind": "sect_rank_at_least", "rank": "inner_disciple"})),
                   s("manual_stonebody_canon", price=300, requires=all_of({"kind": "sect_rank_at_least", "rank": "inner_disciple"})),
                   s("manual_willow_breath_art", price=300, requires=all_of({"kind": "sect_rank_at_least", "rank": "inner_disciple"})),
                   s("manual_emberheart_sutra", price=300, requires=all_of({"kind": "sect_rank_at_least", "rank": "inner_disciple"})),
                   s("manual_nine_winds_canon", price=800, requires=all_of({"kind": "sect_rank_at_least", "rank": "core_disciple"}))],
         "rotation": {"count": 1, "pool": [s("manual_page")]}},
        {"id": "old_pan", "name": "Old Pan's Wares", "currency": "spirit_stone",
         "stock": [s("dusty_curio", price=1)], "rotation": {"count": 3, "pool": [s("torn_manual", price=5, requires=all_of(realm("spirit_awakening_6"))), s("riverreed_ginseng_100", price=4), s("manual_page", price=6), s("spirit_egg", price=12,
                   requires=all_of(realm("heart_tempering_5"))), s("mist_lotus", price=3), s("clear_mind_pill", price=3), s("spirit_jade", price=8)]}},
        {"id": "greyreed", "name": "Greyreed Trade Post", "currency": "silver_tael", "buys_all": True,
         "stock": [s("rice"), s("rice_ball"), s("cleansing_pill"), s("purging_pill"), s("grey_hide")]},
        {"id": "hermit", "name": "Hermit Yao's Offerings", "currency": "silver_tael",
         "stock": [s("bonding_offering_common"), s("roast_fish"), s("fish_bait")]},
    ]
    entries("shops", rows)


def currencies():
    write("currencies.json", {
        "currencies": [
            {"id": "silver_tael", "name": "Silver Taels", "icon": "coin_silver", "scope": "account", "everyday": True},
            {"id": "spirit_stone", "name": "Spirit Stones", "icon": "spirit_stone", "scope": "account"},
            {"id": "contribution", "name": "Contribution", "icon": "contribution", "scope": "character"},
            {"id": "sage_crystal", "name": "Sage Crystals", "icon": "spirit_stone", "scope": "account", "planned": True},
        ],
        "exchange": {"silver_tael>spirit_stone": 0.01, "spirit_stone>silver_tael": 100},
        "spread": 0.2,
    })


def recipes():
    R = []

    def r(rid, craft, inputs, outputs, grade="plain", **kw):
        d = {"id": rid, "craft": craft, "grade": grade, "inputs": [{"item": i, "count": n} for i, n in inputs],
             "outputs": [{"item": i, "count": n} for i, n in outputs]}
        d.update(kw)
        R.append(d)
    # Alchemy (Part 8)
    A = [("healing_pill", "common", [("riverreed_ginseng_10", 1), ("willow_moss", 2)], 120),
         ("qi_restoration_pill", "common", [("willow_moss", 2), ("leech_oil", 1)], 120),
         ("qi_gathering_pill", "common", [("riverreed_ginseng_10", 2), ("moss", 2)], 180),
         ("bone_strengthening_pill", "common", [("tortoise_plate", 1), ("boar_hide", 1), ("riverreed_ginseng_10", 1)], 180),
         ("purging_pill", "common", [("willow_moss", 3), ("river_mud", 1)], 120),
         ("viper_antidote", "common", [("venom_sac", 1), ("willow_moss", 1)], 90),
         ("tiger_blood_pill", "common", [("thorn_hide", 1), ("ember_pepper", 2)], 180),
         ("cleansing_pill", "common", [("mist_lotus", 1), ("jade_scale", 2), ("riverreed_ginseng_100", 1)], 300),
         ("foundation_guard_pill", "earth", [("serpent_core", 1), ("riverreed_ginseng_100", 2), ("guardian_stone", 1)], 600),
         ("clear_mind_pill", "earth", [("mist_lotus", 1), ("jade_scale", 1), ("willow_moss", 2)], 300),
         ("meridian_reversal_pill", "earth", [("prayer_beads", 2), ("mist_lotus", 1)], 300),
         ("method_conversion_pill", "earth", [("manual_page", 1), ("jade_scale", 2), ("mist_lotus", 1)], 300),
         ("qi_refining_pill", "earth", [("pearl", 2), ("mist_lotus", 2), ("serpent_core", 1)], 600),
         ("soul_soothing_pill", "heaven", [("mirror_dust", 2), ("soul_wax", 1), ("mist_lotus", 1)], 600),
         ("mind_lake_opening_pill", "heaven", [("cloud_feather", 3), ("mist_lotus", 2), ("cloudtop_orchid", 1)], 900),
         ("sage_condensing_pill", "mystic", [("roc_feather", 2), ("jade_core", 1), ("soulbell_flower", 2)], 1200)]
    for pid, grade, inputs, t in A:
        r(pid, "alchemy", inputs, [(pid, 1)], grade, time_s=t)
    # Cooking (Part 8) incl. pet foods and bonding offerings
    C = [("herbal_tea", [("willow_moss", 1)], True), ("rice_ball", [("rice", 1)], True), ("riverfish_soup", [("river_minnow", 2)], False),
         ("boar_bone_broth", [("tough_meat", 2)], False), ("ember_pepper_stew", [("ember_pepper", 2), ("tough_meat", 1)], False),
         ("lotus_root_tea", [("mist_lotus", 1)], False), ("toad_oil_dumplings", [("toad_oil", 1), ("rice", 1)], False),
         ("cloudtop_orchid_broth", [("cloudtop_orchid", 1), ("tough_meat", 2)], False), ("jade_carp_congee", [("jade_carp_fish", 1), ("rice", 1)], False),
         ("roast_fish", [("river_minnow", 2)], False), ("ember_pepper_broth", [("ember_pepper", 1), ("tough_meat", 1)], False),
         ("bonding_offering_common", [("tough_meat", 1), ("rice", 1)], False), ("bonding_offering_earth", [("jade_carp_fish", 1), ("mist_lotus", 1)], False),
         ("bonding_offering_heaven", [("mist_trout", 2), ("cloudtop_orchid", 1)], False)]
    for cid, inputs, default in C:
        r(cid, "cooking", inputs, [(cid, 1)], "plain", default=default, pet_food=cid in ("roast_fish", "ember_pepper_broth"))
    # Forge blueprints (weapons per family and armour per slot, per grade)
    bands = {"common": ("iron", "copper_ore", "riverstone", "boar_hide"), "earth": ("jadeiron", "jadeiron", "riverstone", "jade_scale"),
             "heaven": ("cloudsteel", "cloudsteel_ore", "jadeiron", "cloud_feather"), "mystic": ("mistjade", "mystic_ore", "cloudsteel_ore", "roc_feather")}
    for grade, (prefix, metal, second, binder) in bands.items():
        for fam in ["gauntlets", "jian", "spear", "short_blade", "staff", "bow"]:
            r("%s_%s" % (prefix, fam), "smithing", [(metal, 6), (second, 3 if grade == "common" else 4), (binder, 2)], [("%s_%s" % (prefix, fam), 1)], grade)
    armour = {"common": ("cotton", "cloth_boots"), "earth": ("jadeiron", None), "heaven": ("cloudsilk", None), "mystic": ("mistjade", None)}
    for grade, (prefix, boots) in armour.items():
        metal = bands[grade][1]
        binder = bands[grade][3]
        for slot in ["hat", "robe", "trousers", "boots"]:
            out = "%s_%s" % (prefix, slot)
            if grade == "common":
                out = {"hat": "bamboo_hat", "robe": "cotton_robe", "trousers": "cotton_trousers", "boots": "cloth_boots"}[slot]
            r("bp_" + out, "smithing", [(metal, 3), (binder, 4)], [(out, 1)], grade)
    # Qi jades, fuel crystals, blank plate, revival talisman
    for jade, extra in [("body_jade", ("tortoise_plate", 1)), ("swift_jade", ("frog_leg", 2)), ("essence_jade", ("leech_oil", 2)),
                        ("spirit_jade", ("mirror_dust", 1)), ("insight_jade", ("talisman_paper", 2))]:
        r(jade, "smithing", [("jadeiron", 3), extra, ("spirit_stone_shard", 1)], [(jade, 1)], "earth")
    r("fuel_crystal_low", "smithing", [("spirit_stone_shard", 2)], [("fuel_crystal_low", 1)], "common", default=True)
    r("fuel_crystal_mid", "smithing", [("fuel_crystal_low", 10)], [("fuel_crystal_mid", 1)], "earth")
    r("array_plate", "formations", [("blank_plate", 1), ("formation_stone", 1)], [("array_plate", 1)], "earth")
    r("revival_talisman", "formations", [("talisman_paper", 2), ("ink", 1), ("mist_lotus", 1)], [("revival_talisman", 1)], "earth")
    entries("recipes", R)
    return {x["id"] for x in R}


def fish():
    rows = [
        {"id": "river_minnow", "item": "river_minnow", "spots": ["village_docks", "reed_shallows", "marsh_edge"], "weight": 60},
        {"id": "reed_perch", "item": "reed_perch", "spots": ["village_docks", "reed_shallows", "marsh_edge"], "weight": 35},
        {"id": "jade_carp", "item": "jade_carp_fish", "spots": ["bend_shore"], "weight": 50},
        {"id": "river_eel", "item": "river_eel", "spots": ["bend_shore"], "weight": 30},
        {"id": "mist_trout", "item": "mist_trout", "spots": ["falls_pool"], "weight": 50},
        {"id": "rapids_salmon", "item": "rapids_salmon", "spots": ["rapids"], "weight": 50},
        {"id": "moon_carp", "item": "moon_carp", "spots": ["any"], "weight": 8, "time": ["night"]},
    ]
    entries("fish", rows)


def sects():
    entries("sects", [
        {"id": "jade_sect", "name": "Jade Sect", "full_name": "Jade Sect Academy", "element": "water", "methods": ["jade_current_scripture"],
         "token": "jade_token", "color": "#2C9E8F", "hub": "ja_gate_street", "emblem": "jade"},
        {"id": "cloud_sect", "name": "Cloud Sect", "full_name": "Cloud Sect Monastery", "element": "wind", "methods": ["cloudpiercing_canon"],
         "token": "cloud_token", "color": "#AFC9D1", "hub": "cm_cliff_stair", "emblem": "cloud"},
    ])
    ranks = [
        {"id": "service_disciple", "name": "Service Disciple"},
        {"id": "outer_disciple", "name": "Outer Disciple", "requires": all_of(realm("bone_forging_4"))},
        {"id": "inner_disciple", "name": "Inner Disciple", "requires": all_of(realm("qi_unfurling_1"))},
        {"id": "core_disciple", "name": "Core Disciple", "requires": all_of(realm("cloud_stride_1"), {"kind": "flag_set", "flag": "tournament_top8"})},
        {"id": "personal_disciple", "name": "Personal Disciple", "requires": all_of(realm("spirit_awakening_5"))},
        {"id": "deacon", "name": "Deacon", "requires": all_of(realm("heaven_glimpse_1"))},
    ]
    write("sect_ranks.json", {"order": [x["id"] for x in ranks], "ranks": ranks})


def account_rules():
    def acc(r):
        return {"all": [{"kind": "account_realm", "realm": r}]}
    slots = [
        {"slot": 2, "requires": acc("bone_forging_5")}, {"slot": 3, "requires": acc("qi_kindling_1")},
        {"slot": 4, "requires": acc("qi_unfurling_1")}, {"slot": 5, "requires": acc("heart_tempering_1")},
        {"slot": 6, "requires": acc("cloud_stride_1")}, {"slot": 7, "requires": acc("spirit_awakening_1")},
        {"slot": 8, "requires": acc("heaven_glimpse_1")}, {"slot": 9, "requires": {"all": [{"kind": "sect_level", "level": 5}]}},
        {"slot": 10, "requires": acc("sage_1")}, {"slot": 11, "requires": {"all": [{"kind": "sect_level", "level": 10}]}},
        {"slot": 12, "requires": acc("will_manifest_1")},
    ]
    write("account_rules.json", {
        "slots": slots,
        "new_start": {"room": "lf_fishers_hut", "x": 330, "y": 780},
        "skip_start": {"room": "sf_fairground", "x": 3500, "y": 820, "realm": "bone_forging_2",
                       "quests_done": ["morning_tide", "a_quiet_river", "the_runaway_kite", "mas_delivery", "grannys_remedy", "fists_first",
                                       "a_quiet_river_return", "crab_trouble", "evening_on_the_river", "the_hollow_night", "the_river_token",
                                       "the_willow_path"],
                       "flags": ["night_survived", "prologue_done", "dou_safe", "granny_safe", "ma_safe"],
                       "effects": [{"kind": "grant_item", "item": "river_token", "count": 1}, {"kind": "grant_item", "item": "plain_straw_hat", "count": 1},
                                   {"kind": "grant_item", "item": "herbal_tea", "count": 5}]},
        "skip_prologue_allowed": True,
        "name_max": 24,
        "creator": {"hair": ["short_knot", "topknot", "ponytail", "high_pony", "long_tied", "flowing"], "hair_color": 6,
                    "robe": ["disciple", "vneck", "cardigan", "scholar", "sleeveless"], "trousers": ["loose", "straight", "cuffed", "scholar", "martial"],
                    "shoes": ["slippers", "folded", "boots"]},
    })


def idle_tasks():
    entries("idle_tasks", [
        {"id": "rest", "name": "Rest", "desc": "Recover and keep a little progress."},
        {"id": "seclusion", "name": "Seclusion", "desc": "Cultivate while away.", "requires": all_of(unlocked("seclusion"))},
        {"id": "train", "name": "Train", "desc": "Temper the body at training stumps.", "requires": all_of(unlocked("idle_tasks"))},
        {"id": "hunt", "name": "Hunt", "desc": "Hunt this room's monsters at a quarter of the loot.", "requires": all_of(unlocked("idle_tasks"))},
        {"id": "gather", "name": "Gather", "desc": "Gather this room's nodes.", "requires": all_of(unlocked("herb_gathering"))},
    ])


def companions():
    rows = [
        {"id": "lan_yue", "name": "Lan Yue", "role": "healer", "weapon": "staff", "element": "water", "outfit_npc": "lan_yue"},
        {"id": "tie_niu", "name": "Tie Niu", "role": "brawler", "weapon": "gauntlets", "element": "earth", "outfit_npc": "tie_niu"},
        {"id": "qiu_feng", "name": "Qiu Feng", "role": "archer", "weapon": "bow", "element": "wood", "outfit_npc": "qiu_feng"},
        {"id": "bai_ling", "name": "Bai Ling", "role": "formation", "weapon": "jian", "element": "wind", "outfit_npc": "bai_ling"},
    ]
    npcs = {n["id"]: n for n in json.load(open(os.path.join(DATA, "npcs.json")))["entries"]}
    for r in rows:
        r["outfit"] = npcs[r["outfit_npc"]]["outfit"]
    entries("companions", rows)


def pets():
    rows = [
        {"id": "reed_otter", "name": "Reed Otter", "art": "reed_otter", "element": "water", "strength_role": "gatherer", "starter": True,
         "skills": ["Splash", "Reed Dive", "Otter Current", "River Gift"], "favourite_foods": ["roast_fish", "riverfish_soup"],
         "branches": ["River Otter Sage", "Tide Otter"], "inherit_owner": {"hatchling": 0.2, "juvenile": 0.35, "adult": 0.5}},
        {"id": "ember_fox", "name": "Ember Fox", "art": "ember_fox", "element": "fire", "strength_role": "combat", "starter": True,
         "skills": ["Ember Bite", "Flare", "Fox Fire", "Nine Embers"], "favourite_foods": ["roast_fish", "ember_pepper_broth"],
         "branches": ["Twin-Tail Fox", "Hearth Fox"], "inherit_owner": {"hatchling": 0.25, "juvenile": 0.4, "adult": 0.55}},
        {"id": "jade_crane", "name": "Jade Crane", "art": "jade_crane_chick", "element": "wind", "strength_role": "mount", "starter": True,
         "skills": ["Wing Buffet", "Crane Call", "Cloud Lift", "Sky Dance"], "favourite_foods": ["mist_trout", "lotus_root_tea"],
         "branches": ["Cloud Crane", "Sage Crane"], "inherit_owner": {"hatchling": 0.2, "juvenile": 0.35, "adult": 0.5}},
        {"id": "mossback_toad", "name": "Mossback Toad", "art": "mossback_toad", "element": "wood", "strength_role": "gatherer", "tame": True,
         "skills": ["Tongue Lash", "Moss Shield", "Herb Sense", "Garden Back"], "favourite_foods": ["frog_leg", "rice_ball"], "branches": ["Moss Sage Toad", "Thorn Toad"]},
        {"id": "ironclaw_mole", "name": "Ironclaw Mole", "art": "ironclaw_mole", "element": "earth", "strength_role": "gatherer", "tame": True,
         "skills": ["Dig", "Ore Sense", "Tunnel Rush", "Gem Find"], "favourite_foods": ["tough_meat", "boar_bone_broth"], "branches": ["Gem Mole", "Burrow Guard"]},
        {"id": "bamboo_monkey", "name": "Bamboo Monkey", "art": "bamboo_monkey", "element": "wood", "strength_role": "combat", "tame": True,
         "skills": ["Shoot Toss", "Pickpocket", "Vine Swing", "Monkey Chaos"], "favourite_foods": ["bamboo_shoot", "rice_ball"], "branches": ["Monkey Thief", "Staff Monkey"]},
        {"id": "mist_wolf", "name": "Mist Wolf", "art": "mist_wolf", "element": "soul", "strength_role": "combat", "tame": True,
         "skills": ["Mist Bite", "Howl", "Fog Step", "Moon Hunt"], "favourite_foods": ["tough_meat", "riverfish_soup"], "branches": ["Fog Wolf", "Moon Wolf"]},
    ]
    entries("pets", rows)
    entries("pet_traits", [
        {"id": "deep_diver", "name": "Deep Diver", "effect": "+30% fishing"}, {"id": "stormborn", "name": "Stormborn", "effect": "+15% thunder damage"},
        {"id": "keen_nose", "name": "Keen Nose", "effect": "+10% herb yield"}, {"id": "iron_hide", "name": "Iron Hide", "effect": "+10% defence"},
        {"id": "quick_paws", "name": "Quick Paws", "effect": "+10% attack speed"}, {"id": "lucky_find", "name": "Lucky Find", "effect": "+5% drop rate"},
        {"id": "calm_spirit", "name": "Calm Spirit", "effect": "+5% Resonance"}, {"id": "loyal", "name": "Loyal", "effect": "+1 bond per day"},
    ])


def achievements():
    A = [
        {"id": "fleet_footed", "name": "Fleet-Footed", "desc": "Win the race to the tower", "event": "quest_completed", "match": {"quest": "race_to_the_tower"}, "title": "fleet_footed"},
        {"id": "crab_catcher", "name": "Crab Catcher", "desc": "Defeat 100 Mudshell Crabs", "event": "actor_defeated", "match": {"def": "mudshell_crab"}, "count": 100, "title": "shore_warden"},
        {"id": "first_current", "name": "First Current", "desc": "Reach Bone Forging 7", "event": "realm_changed", "match": {"realm_at_least": "bone_forging_7"},
         "rewards": [{"kind": "grant_item", "item": "qi_gathering_pill", "count": 1}]},
        {"id": "iron_fist", "name": "Iron Fist", "desc": "Reach Qi Kindling 1 without equipping a weapon", "event": "realm_changed",
         "match": {"realm_at_least": "qi_kindling_1", "no_weapon": True, "to": "qi_kindling_1"}, "title": "iron_fist"},
        {"id": "steady_hands", "name": "Steady Hands", "desc": "Refine a Perfect pill", "event": "craft_completed", "match": {"craft": "alchemy", "quality": "perfect"}, "title": "steady_hands"},
        {"id": "deep_roots", "name": "Deep Roots", "desc": "Reach Mining Adept", "event": "profession_rank_up", "match": {"craft": "mining", "rank": "adept"}, "title": "stonebreaker"},
        {"id": "untouched", "name": "Untouched", "desc": "Defeat a dungeon boss without being gravely wounded", "event": "boss_defeated", "match": {"clean": True}, "title": "untouched"},
        {"id": "collector", "name": "Collector", "desc": "Fill 10 collection cards", "event": "collection_card_filled", "count": 10, "title": "collector"},
        {"id": "traveller", "name": "Traveller", "desc": "Visit every valley room", "event": "room_entered", "match": {"all_valley_rooms": True}, "title": "wanderer"},
        {"id": "patient_heart", "name": "Patient Heart", "desc": "Pass the Heart Trial on the first try", "event": "event_passed", "match": {"event": "heart_trial", "first_try": True}, "title": "still_water"},
        {"id": "friend_of_beasts", "name": "Friend of Beasts", "desc": "Bond 3 spirit animals", "event": "pet_bonded", "count": 3, "title": "beast_friend"},
        {"id": "valley_champion", "name": "Valley Champion", "desc": "Win the Valley Tournament", "event": "tournament_won", "title": "valley_champion"},
    ]
    entries("achievements", A)
    T = [
        {"id": "fleet_footed", "name": "Fleet-Footed", "modifiers": [{"stat": "move_speed", "op": "pct_add", "value": 0.01}]},
        {"id": "shore_warden", "name": "Shore Warden", "modifiers": [{"stat": "physical_defense", "op": "pct_add", "value": 0.01}]},
        {"id": "iron_fist", "name": "Iron Fist", "modifiers": [{"stat": "fist_attack", "op": "pct_add", "value": 0.01}]},
        {"id": "steady_hands", "name": "Steady Hands", "modifiers": [{"stat": "crafting_control", "op": "pct_add", "value": 0.01}]},
        {"id": "stonebreaker", "name": "Stonebreaker", "modifiers": [{"stat": "mining_power", "op": "pct_add", "value": 0.01}]},
        {"id": "untouched", "name": "Untouched", "modifiers": [{"stat": "evasion", "op": "pct_add", "value": 0.01}]},
        {"id": "collector", "name": "Collector", "modifiers": [{"stat": "drop_rate", "op": "pct_add", "value": 0.01}]},
        {"id": "wanderer", "name": "Wanderer", "modifiers": [{"stat": "move_speed", "op": "pct_add", "value": 0.01}]},
        {"id": "still_water", "name": "Still Water", "modifiers": [{"stat": "composure_regen", "op": "pct_add", "value": 0.01}]},
        {"id": "beast_friend", "name": "Beast Friend", "modifiers": [{"stat": "taming_chance", "op": "pct_add", "value": 0.01}]},
        {"id": "valley_champion", "name": "Valley Champion", "modifiers": [{"stat": "physical_attack", "op": "pct_add", "value": 0.01}]},
        {"id": "guos_student", "name": "Guo's Student", "modifiers": [{"stat": "fist_attack", "op": "pct_add", "value": 0.01}]},
        {"id": "big_sibling", "name": "Big Sibling", "modifiers": [{"stat": "max_hp", "op": "pct_add", "value": 0.01}]},
    ]
    entries("titles", T)
    entries("emotes", [
        {"id": "bow", "name": "Bow", "pose": "idle"}, {"id": "wave", "name": "Wave", "pose": "idle"},
        {"id": "meditate", "name": "Sit", "pose": "meditate"}, {"id": "cheer", "name": "Cheer", "pose": "jump"},
        {"id": "salute", "name": "Fist salute", "pose": "punch_1"},
    ])


def missions():
    def opt(name, obj, lo=0, hi=999):
        return {"name": name, "objective": obj, "min_level": lo, "max_level": hi}
    rows = [
        {"id": "hunt", "name": "Hunt", "options": [
            opt("Thin the boarlets", {"kind": "kill", "enemy": "wild_boarlet", "count": 8, "text": "Defeat Wild Boarlets"}, 0, 5),
            opt("Quarry pests", {"kind": "kill", "enemy": "rock_beetle", "count": 8, "text": "Defeat Rock Beetles"}, 3, 9),
            opt("Marsh leeches", {"kind": "kill", "enemy": "marsh_leech", "count": 8, "text": "Defeat Marsh Leeches"}, 4, 11),
            opt("Grey beasts", {"kind": "kill", "enemy": "hollowed_boarlet", "count": 8, "text": "Defeat Hollowed Boarlets"}, 7, 14),
            opt("Monkey business", {"kind": "kill", "enemy": "bamboo_monkey", "count": 8, "text": "Defeat Bamboo Monkeys"}, 10, 17),
            opt("Bandit patrol", {"kind": "kill", "enemy": "mudwater_bandit", "count": 8, "text": "Defeat Mudwater Bandits"}, 14, 22),
            opt("Shore crabs", {"kind": "kill", "enemy": "tide_crab", "count": 8, "text": "Defeat Tide Crabs"}, 19, 27),
            opt("Rapids watch", {"kind": "kill", "enemy": "rapids_lizard", "count": 8, "text": "Defeat Rapids Lizards"}, 27, 37),
            opt("Cliff hawks", {"kind": "kill", "enemy": "stormwing_hawk", "count": 6, "text": "Defeat Stormwing Hawks"}, 37, 47),
            opt("Wolves in the mist", {"kind": "kill", "enemy": "mist_wolf", "count": 6, "text": "Defeat Mist Wolves"}, 45, 70)]},
        {"id": "gather", "name": "Gather", "requires": all_of(unlocked("herb_gathering")), "options": [
            opt("Willow Moss", {"kind": "gather_node", "item": "willow_moss", "count": 5, "text": "Gather Willow Moss"}, 0, 20),
            opt("Ember Peppers", {"kind": "gather_node", "item": "ember_pepper", "count": 5, "text": "Gather Ember Peppers"}, 10, 30),
            opt("Mist Lotus", {"kind": "gather_node", "item": "mist_lotus", "count": 3, "text": "Gather Mist Lotus"}, 19, 70)]},
        {"id": "mine", "name": "Mine", "requires": all_of(unlocked("mining")), "options": [
            opt("Copper for the forge", {"kind": "gather_node", "item": "copper_ore", "count": 6, "text": "Mine Copper"}, 0, 20),
            opt("Jadeiron", {"kind": "gather_node", "item": "jadeiron", "count": 4, "text": "Mine Jadeiron"}, 12, 70)]},
        {"id": "deliver", "name": "Deliver", "options": [
            opt("Rice for the kitchen", {"kind": "deliver", "item": "rice_ball", "count": 3, "text": "Deliver Rice Balls"}, 0, 70),
            opt("Teas for the infirmary", {"kind": "deliver", "item": "herbal_tea", "count": 3, "text": "Deliver Herbal Teas"}, 0, 70)]},
        {"id": "craft", "name": "Craft", "requires": all_of(unlocked("cooking")), "options": [
            opt("Kitchen duty", {"kind": "craft", "craft": "cooking", "count": 3, "text": "Cook three dishes"}, 0, 70)]},
        {"id": "spar", "name": "Spar", "options": [
            opt("Sparring practice", {"kind": "win_spar", "count": 1, "text": "Win a spar"}, 0, 70)]},
    ]
    entries("mission_templates", rows)


def sect_tables():
    B = [("sect_hall", "Sect Hall", 800, "riverstone", 20, 1), ("treasury", "Treasury", 500, "copper_ore", 20, 1),
         ("meditation_pavilion", "Meditation Pavilion", 500, "riverstone", 20, 1), ("guest_house", "Guest House", 600, "boar_hide", 10, 2),
         ("mission_hall", "Mission Hall", 600, "copper_ore", 15, 2), ("alchemy_hall", "Alchemy Hall", 900, "willow_moss", 20, 3),
         ("forge", "Forge", 900, "copper_ore", 30, 3), ("herb_terraces", "Herb Terraces", 700, "willow_moss", 15, 4),
         ("beast_pavilion", "Beast Pavilion", 700, "tough_meat", 15, 4), ("library", "Library", 1000, "talisman_paper", 10, 5),
         ("formation_array", "Formation Array", 1200, "formation_stone", 10, 6), ("ancestral_shrine", "Ancestral Shrine", 1500, "jade_core", 1, 7)]
    entries("sect_buildings", [{"id": b, "name": n, "base_cost": c, "material": m, "material_count": k, "sect_level": lv, "max_level": 10}
                               for b, n, c, m, k, lv in B])
    write("sect_levels.json", {"prestige_building": 20, "levels": [{"level": n, "prestige": int(round(200 * n ** 1.8))} for n in range(1, 21)]})
    entries("expeditions", [
        {"id": "willow_path", "name": "Willow Path", "hours": [1, 4, 8], "danger_level": 1,
         "rewards": [{"item": "willow_moss", "count": 3}, {"item": "boar_hide", "count": 2}, {"coins": 60}]},
        {"id": "stonewall_quarry", "name": "Stonewall Quarry", "hours": [1, 4, 8], "danger_level": 1,
         "rewards": [{"item": "copper_ore", "count": 4}, {"item": "riverstone", "count": 3}, {"item": "jadeiron", "count": 1, "min_hours": 8}]},
        {"id": "reed_marsh", "name": "Reed Marsh", "hours": [4, 8], "danger_level": 3,
         "rewards": [{"item": "leech_oil", "count": 3}, {"item": "hollow_shard", "count": 1}]},
        {"id": "bamboo_grove", "name": "Bamboo Grove", "hours": [4, 8], "danger_level": 3,
         "rewards": [{"item": "ember_pepper", "count": 3}, {"item": "bamboo_shoot", "count": 3}, {"item": "manual_page", "count": 1, "chance": 0.2}]},
        {"id": "deepwater_bend", "name": "Deepwater Bend", "hours": [4, 8], "danger_level": 5,
         "rewards": [{"item": "jade_scale", "count": 2}, {"item": "pearl", "count": 1}, {"item": "riverreed_ginseng_100", "count": 1, "chance": 0.3}]},
        {"id": "whitewater_gorge", "name": "Whitewater Gorge", "hours": [8], "danger_level": 5,
         "rewards": [{"item": "jadeiron", "count": 3}, {"item": "mist_lotus", "count": 2}]},
        {"id": "mist_peak", "name": "Mist Peak", "hours": [8], "danger_level": 8,
         "rewards": [{"item": "soulbell_flower", "count": 2}, {"item": "soul_wax", "count": 1}, {"item": "spirit_egg", "count": 1, "chance": 0.1}]},
    ])
    write("disciples.json", {
        "traits": ["green_thumb", "strong_back", "keen_eye", "steady_hands", "brave", "night_owl", "loyal", "fast_learner"],
        "trait_names": {"green_thumb": "Green Thumb", "strong_back": "Strong Back", "keen_eye": "Keen Eye", "steady_hands": "Steady Hands",
                        "brave": "Brave", "night_owl": "Night Owl", "loyal": "Loyal", "fast_learner": "Fast Learner"},
        "names": ["Wei", "Lin", "Hao", "Ming", "Jun", "Rui", "Xiu", "Ning", "Bo", "An", "Yun", "Fei", "Ping", "Qiao", "Lan", "Tao"],
    })


def strings():
    realms = json.load(open(os.path.join(DATA, "realms.json")))["entries"]
    S = {}
    for r in realms:
        S["realm." + r["key"]] = r["name"]
    S.update({
        "currency.silver_tael": "Silver Taels", "currency.spirit_stone": "Spirit Stones", "currency.contribution": "Contribution",
        "failure.backlash": "Qi backlash", "failure.injury": "Meridian injury", "failure.setback": "Setback",
        "event.heavens_cleansing": "Heaven's Cleansing", "event.heart_trial": "The Heart Trial", "event.hollow_night": "The Hollow Night",
        "flag.night_survived": "Survived the night",
        "ui.begin": "Begin", "ui.continue": "Continue", "ui.new_game": "New Game", "ui.settings": "Settings", "ui.back": "Back",
        "ui.unaffiliated": "Unaffiliated", "ui.locked": "Locked",
    })
    for u in json.load(open(os.path.join(DATA, "unlocks.json")))["entries"]:
        S["unlock." + u["id"]] = u.get("label", u["id"])
    write("en.json", {"strings": S}, folder=os.path.join(DATA, "strings"))


def build():
    shops()
    currencies()
    rec = recipes()
    fish()
    sects()
    account_rules()
    idle_tasks()
    companions()
    pets()
    achievements()
    missions()
    sect_tables()
    strings()
    # Cross-check every referenced item exists.
    items = {e["id"] for e in json.load(open(os.path.join(DATA, "items.json")))["entries"]}
    items |= {e["id"] for e in json.load(open(os.path.join(DATA, "artifacts.json")))["entries"]}
    errs = []
    for sh in json.load(open(os.path.join(DATA, "shops.json")))["entries"]:
        for s in sh["stock"] + sh.get("rotation", {}).get("pool", []):
            if s["item"] not in items:
                errs.append("shop %s %s" % (sh["id"], s["item"]))
    for r in json.load(open(os.path.join(DATA, "recipes.json")))["entries"]:
        for x in r["inputs"] + r["outputs"]:
            if x["item"] not in items:
                errs.append("recipe %s %s" % (r["id"], x["item"]))
    for f in json.load(open(os.path.join(DATA, "fish.json")))["entries"]:
        if f["item"] not in items:
            errs.append("fish %s" % f["item"])
    # Quest recipes must exist.
    for q in json.load(open(os.path.join(DATA, "quests.json")))["entries"]:
        for e in q.get("rewards", []) + q.get("on_accept", []):
            if e["kind"] == "learn_recipe" and e["recipe"] not in rec:
                errs.append("quest %s recipe %s" % (q["id"], e["recipe"]))
    assert not errs, "\n".join(errs)
    print("recipes:", len(rec))


if __name__ == "__main__":
    build()
