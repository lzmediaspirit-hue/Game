"""Economy and system tables (S20-S26, S33, S34, S39, Part 8):
shops, currencies, recipes, fish, sects, sect_ranks, account_rules, idle_tasks, companions,
pets, pet_traits, achievements, titles, emotes, mission_templates, sect_buildings, sect_levels,
expeditions, disciples, strings/en.json.
"""
import json
import math
import os

from common import DATA, write, entries


def realm(r):
    return {"kind": "realm_at_least", "realm": r}


def unlocked(s):
    return {"kind": "unlock", "system": s}


def flag(f):
    return {"kind": "flag_set", "flag": f}


def all_of(*c):
    return {"all": list(c)}


def shops():
    def s(i, **kw):
        d = {"item": i}
        d.update(kw)
        return d

    def technique_stock(sect_id):
        # The library techniques (Part 8 sources library_1..3, and the Cloud library's own): taught by the Mission Hall
        # from their realm, for contribution, the higher floors by sect rank.
        rank = {"library_1": "outer_disciple", "library_2": "inner_disciple", "library_3": "core_disciple", "cloud_library": "inner_disciple"}
        price = {"library_1": 60, "library_2": 150, "library_3": 300, "cloud_library": 150}
        out = []
        for t in json.load(open(os.path.join(DATA, "techniques.json")))["entries"]:
            src = str(t.get("source", ""))
            if src not in rank or (src == "cloud_library" and sect_id != "cloud_sect"):
                continue
            out.append(s("technique_manual", learn=t["id"], price=price[src],
                         requires=all_of(realm(t["unlock"]), {"kind": "sect_rank_at_least", "rank": rank[src]},
                                         {"kind": "reputation_at_least", "value": 0})))
        # S48 the Buddhist path: the Golden Body, lent to the upright who have earned merit.
        out.append(s("technique_manual", learn="golden_body", price=400,
                     requires=all_of(realm("heart_tempering_3"), {"kind": "alignment_at_least", "value": 20},
                                     {"kind": "merit_at_least", "value": 50}, {"kind": "reputation_at_least", "value": 0})))
        return out

    def inner_art_stock():
        # S48 Inner Arts: every Mission Hall teaches all eight, each from its realm, for contribution.
        from paths import inner_arts
        return [s("inner_art_manual", learn=a["id"], price=a["price"], requires=all_of(realm(a["realm"]))) for a in inner_arts(write=False)
                if not a.get("legacy")]
    rows = [
        {"id": "old_ma", "name": "Old Ma's Store", "currency": "silver_tael", "buys_all": True,
         "stock": [s("herbal_tea", price=6), s("rice_ball", price=4), s("rice", price=2), s("bamboo_rod", requires=all_of(realm("bone_forging_8"))),
                   s("bonding_offering_common", requires=all_of(realm("qi_unfurling_5"))),
                   s("sealing_gourd", price=900, requires=all_of(realm("spirit_awakening_1")))],
         "rotation": {"count": 1, "pool": [s("willow_moss"), s("boar_hide"), s("river_mud"), s("cloth")]}},
        {"id": "granny_liu", "name": "Granny Liu's Herb Hut", "currency": "silver_tael",
         "stock": [s("herbal_tea"), s("willow_salve"), s("revival_talisman"), s("purging_pill", requires=all_of(realm("qi_kindling_2"))),
                   s("calm_incense", requires=all_of(realm("qi_unfurling_9"))),
                   # S45 seeds (Part 8): the common three, for the garden beds.
                   s("willow_moss_seed", price=6), s("ember_pepper_seed", price=14), s("riverreed_ginseng_seed", price=20)]},
        {"id": "stoneford_general", "name": "Stoneford General Store", "currency": "silver_tael", "buys_all": True,
         "stock": [s("cinnabar", price=8), s("herbal_tea"), s("lotus_root_tea"), s("rice_ball"), s("rice"), s("return_charm"), s("herb_sickle", requires=all_of(realm("bone_forging_4"))),
                   s("spirit_spade", price=900, requires=all_of(realm("cloud_stride_1"))), s("rice_wine", price=12),
                   s("iron_pickaxe", requires=all_of(realm("bone_forging_5"))), s("bamboo_gourd"), s("escape_talisman"), s("fish_bait"),
                   s("fuel_crystal_low", requires=all_of(realm("heart_tempering_1")))],
         "rotation": {"count": 1, "pool": [s("bamboo_rod"), s("lantern_wick"), s("clay_pot")]}},
        {"id": "stoneford_tea", "name": "Stoneford Tea House", "currency": "silver_tael",
         "stock": [s("lotus_root_tea"), s("jade_carp_congee"), s("rice_ball"), s("jasmine_dew_tea", price=30), s("guqin", price=450)],
         "rotation": {"count": 1, "pool": [s("ember_pepper_stew"), s("toad_oil_dumplings"), s("riverfish_soup")]}},
        {"id": "mei_qing", "name": "Mei Qing's Stall", "currency": "silver_tael",
         "stock": [s("willow_moss"), s("riverreed_ginseng_10"), s("healing_pill"), s("qi_restoration_pill"), s("qi_gathering_pill"),
                   s("recipe_scroll", learn="healing_pill"), s("pearl", price=40, requires=all_of(realm("heart_tempering_5"))),
                   s("mist_lotus", price=35, requires=all_of(realm("heart_tempering_5"))),
                   s("cloudtop_orchid", price=120, requires=all_of(realm("cloud_stride_5")))],
         "rotation": {"count": 1, "pool": [s("clear_mind_pill"), s("foundation_guard_pill"), s("bone_strengthening_pill")]}},
        {"id": "mei_qing_recipes", "name": "Mei Qing's Recipe Box", "currency": "silver_tael",
         "stock": [s("recipe_scroll", learn="qi_gathering_pill", price=120, requires=all_of(realm("qi_kindling_3"))),
                   s("recipe_scroll", learn="bone_strengthening_pill", price=120, requires=all_of(realm("qi_kindling_3"))),
                   s("recipe_scroll", learn="viper_antidote", price=80, requires=all_of(realm("qi_kindling_3"))),
                   s("recipe_scroll", learn="tiger_blood_pill", price=150, requires=all_of(realm("qi_kindling_5"))),
                   s("recipe_scroll", learn="qi_refining_pill", price=800, requires=all_of(realm("heart_tempering_5")))]},
        # S44 / Part 8: the Alchemist Guild's shop opens to a Guild Adept: Earth recipes and the Jadeiron Furnace blueprint.
        {"id": "alchemist_guild", "name": "Alchemist Guild", "currency": "silver_tael",
         "stock": [s("recipe_scroll", learn="foundation_guard_pill", price=600, requires=all_of(flag("guild_alchemy_adept"))),
                   s("recipe_scroll", learn="clear_mind_pill", price=500, requires=all_of(flag("guild_alchemy_adept"))),
                   s("recipe_scroll", learn="meridian_reversal_pill", price=700, requires=all_of(flag("guild_alchemy_adept"))),
                   s("recipe_scroll", learn="jadeiron_furnace", price=900, requires=all_of(flag("guild_alchemy_adept"))),
                   s("mist_lotus", price=35, requires=all_of(flag("guild_alchemy_adept"))),
                   s("jade_scale", price=30, requires=all_of(flag("guild_alchemy_adept"))),
                   s("recipe_scroll", learn="storm_blood_pill", price=2400, requires=all_of(flag("guild_alchemy_expert"), realm("heaven_glimpse_1")))]},
        {"id": "stoneford_smith", "name": "Stoneford Smith", "currency": "silver_tael", "buys_all": True,
         "stock": [s("training_jian"), s("training_spear"), s("training_gauntlets"), s("training_short_blade"), s("training_staff"), s("training_bow"),
                   s("iron_jian", requires=all_of(realm("qi_kindling_1"))), s("iron_spear", requires=all_of(realm("qi_kindling_1"))),
                   s("iron_gauntlets", requires=all_of(realm("qi_kindling_1"))), s("iron_short_blade", requires=all_of(realm("qi_kindling_1"))),
                   s("iron_staff", requires=all_of(realm("qi_kindling_1"))), s("iron_bow", requires=all_of(realm("qi_kindling_1"))),
                   # S47 v1.1 families: the heavy sabre, the fan and the flute.
                   s("training_heavy_sabre"), s("training_fan"), s("training_flute"),
                   s("iron_heavy_sabre", requires=all_of(realm("qi_kindling_1"))), s("iron_fan", requires=all_of(realm("qi_kindling_1"))),
                   s("iron_flute", requires=all_of(realm("qi_kindling_1"))),
                   # S47 imitation relics: the smith copies a relic only once it has been seen whole.
                   s("recipe_scroll", learn="moonshadow_jian", price=2400, requires=all_of({"kind": "flag_set", "flag": "bound:moonlit_blade"})),
                   s("recipe_scroll", learn="drowsing_edge", price=2400, requires=all_of({"kind": "flag_set", "flag": "bound:sleeping_blade"})),
                   s("bamboo_hat"), s("cotton_robe"), s("cotton_trousers"), s("cloth_boots"), s("copper_ore"), s("riverstone")],
         "rotation": {"count": 1, "pool": [s("jadeiron_jian"), s("jadeiron_spear"), s("jadeiron_robe"), s("jadeiron_gourd"),
                                           s("jadeiron_heavy_sabre"), s("jadeiron_fan"), s("jadeiron_flute")]}},
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
                                      s("jade_gourd_vessel", price=180, requires=all_of(realm("cloud_stride_1"))),
                   s("jade_current_robe", requires=all_of({"kind": "sect_rank_at_least", "rank": "inner_disciple"})),
                   s("manual_stonebody_canon", price=300, requires=all_of({"kind": "sect_rank_at_least", "rank": "inner_disciple"})),
                   s("manual_willow_breath_art", price=300, requires=all_of({"kind": "sect_rank_at_least", "rank": "inner_disciple"})),
                   s("manual_emberheart_sutra", price=300, requires=all_of({"kind": "sect_rank_at_least", "rank": "inner_disciple"})),
                   s("manual_tidal_sovereign_scripture", price=800, requires=all_of({"kind": "sect_rank_at_least", "rank": "core_disciple"}))] + inner_art_stock()
                  + technique_stock("jade_sect"),
         "rotation": {"count": 1, "pool": [s("manual_page")]}},
        {"id": "cloud_sect", "name": "Cloud Sect Mission Hall", "currency": "contribution",
         "requires": {"all": [{"kind": "training_sect", "sect": "cloud_sect"}]},
         "stock": [s("manual_ember_burst", requires=all_of({"kind": "sect_rank_at_least", "rank": "outer_disciple"})),
                   s("healing_pill"), s("qi_restoration_pill"), s("cleansing_pill", requires=all_of(realm("qi_kindling_9"))),
                   s("foundation_guard_pill", requires=all_of(realm("qi_unfurling_1"))), s("clear_mind_pill"), s("revival_talisman"),
                   s("bonding_offering_earth", requires=all_of(realm("qi_unfurling_5"))), s("fuel_crystal_low", requires=all_of(realm("heart_tempering_1"))),
                                      s("cloud_puff_vessel", price=180, requires=all_of(realm("cloud_stride_1"))),
                   s("cloudpiercing_robe", requires=all_of({"kind": "sect_rank_at_least", "rank": "inner_disciple"})),
                   s("manual_stonebody_canon", price=300, requires=all_of({"kind": "sect_rank_at_least", "rank": "inner_disciple"})),
                   s("manual_willow_breath_art", price=300, requires=all_of({"kind": "sect_rank_at_least", "rank": "inner_disciple"})),
                   s("manual_emberheart_sutra", price=300, requires=all_of({"kind": "sect_rank_at_least", "rank": "inner_disciple"})),
                   s("manual_nine_winds_canon", price=800, requires=all_of({"kind": "sect_rank_at_least", "rank": "core_disciple"})),
                   # S49 alignment: the abbots keep their incense for the upright.
                   s("calm_heart_incense", price=60, requires=all_of({"kind": "alignment_at_least", "value": 20}))] + inner_art_stock()
                  + technique_stock("cloud_sect"),
         "rotation": {"count": 1, "pool": [s("manual_page")]}},
        {"id": "old_pan", "name": "Old Pan's Wares", "currency": "spirit_stone",
         "stock": [s("dusty_curio", price=1)], "rotation": {"count": 3, "pool": [s("torn_manual", price=5, requires=all_of(realm("spirit_awakening_6"))), s("riverreed_ginseng_100", price=4, sealed=True), s("manual_page", price=6), s("spirit_egg", price=12,
                   requires=all_of(realm("heart_tempering_5"))), s("mist_lotus", price=3), s("clear_mind_pill", price=3), s("spirit_jade", price=8)]}},
        {"id": "greyreed", "name": "Greyreed Trade Post", "currency": "silver_tael", "buys_all": True,
         "stock": [s("rice"), s("rice_ball"), s("marsh_mist_tea", price=30), s("cleansing_pill"), s("purging_pill"), s("grey_hide"),
                   s("willow_moss_seed", price=6), s("ember_pepper_seed", price=14), s("riverreed_ginseng_seed", price=20)]},
        {"id": "hermit", "name": "Hermit Yao's Beast Hall", "currency": "silver_tael",
         "stock": [s("taming_cauldron", price=200, requires=all_of(realm("heart_tempering_1"))), s("bonding_offering_common"), s("roast_fish"), s("fish_bait"), s("maple_leaf_vessel", price=600, requires=all_of(realm("cloud_stride_1"))),
                   s("purifying_offering", price=60, requires=all_of(realm("qi_unfurling_7"))), s("beast_revival_pill", price=45),
                   s("beast_essence_blood", price=600, requires=all_of(realm("heart_tempering_1"))),
                   s("pet_book_iron_hide", price=400, requires=all_of(realm("qi_unfurling_1"))),
                   s("pet_book_deep_pockets", price=900, requires=all_of(realm("heart_tempering_1"))),
                   s("beast_bag_reed", price=150, requires=all_of(realm("qi_unfurling_7"))), s("beast_bag_hide", price=900, requires=all_of(realm("heart_tempering_1"))),
                   s("beast_bag_cloud", price=2400, requires=all_of(realm("cloud_stride_1")))]},
        # Act II · Cloudgate Port and the Thunderhorn Plains. Spirit Stone prices come from tael prices at the exchange rate.
        {"id": "alliance_factor", "name": "Alliance Factor's Hall", "currency": "spirit_stone", "discount": {"flag": "path_alliance", "pct": 0.1},
         "stock": [s("stormsteel_jian"), s("stormsteel_spear"), s("stormsteel_gauntlets"), s("stormsteel_short_blade"), s("stormsteel_staff"),
                   s("stormsteel_bow"), s("stormsilk_hat"), s("stormsilk_robe"), s("stormsilk_trousers"), s("stormsilk_boots"),
                   s("stormsteel_gourd", requires=all_of(realm("sage_1")))],
         "rotation": {"count": 1, "pool": [s("storm_shard", price=4), s("spirit_stone_mid", price=12)]}},
        {"id": "port_peddler", "name": "Peddler Gou's Packs", "currency": "spirit_stone", "buys_all": True,
         "stock": [s("healing_pill"), s("qi_restoration_pill"), s("return_charm"), s("escape_talisman"), s("rice_ball"), s("revival_talisman"),
                   s("thunderhead_tea", price=3),
                   s("fuel_crystal_mid", requires=all_of(realm("sage_1")))],
         "rotation": {"count": 2, "pool": [s("clear_mind_pill"), s("soul_soothing_pill"), s("manual_page", price=6), s("spirit_egg", price=14)]}},
        {"id": "stormsteel_smith", "name": "Hong's Stormsteel Forge", "currency": "spirit_stone", "buys_all": True,
         "stock": [s("stormsteel_ore"), s("mystic_ore"),
                   s("recipe_scroll", learn="stormsteel_jian", price=40, requires=all_of(realm("sage_1"))),
                   s("recipe_scroll", learn="stormsteel_spear", price=40, requires=all_of(realm("sage_1"))),
                   s("recipe_scroll", learn="stormsteel_gauntlets", price=40, requires=all_of(realm("sage_1"))),
                   s("recipe_scroll", learn="stormsteel_short_blade", price=40, requires=all_of(realm("sage_1"))),
                   s("recipe_scroll", learn="stormsteel_staff", price=40, requires=all_of(realm("sage_1"))),
                   s("recipe_scroll", learn="stormsteel_bow", price=40, requires=all_of(realm("sage_1"))),
                   s("recipe_scroll", learn="bp_stormsilk_robe", price=40, requires=all_of(realm("sage_1")))]},
        {"id": "port_apothecary", "name": "Apothecary Wu's Cabinet", "currency": "spirit_stone",
         "stock": [s("soulbell_flower"), s("cloudtop_orchid"), s("mist_lotus"), s("healing_pill"), s("qi_restoration_pill"),
                   s("recipe_scroll", learn="storm_blood_pill", price=30)],
         "rotation": {"count": 1, "pool": [s("jade_core", price=20), s("roc_feather", price=12)]}},
        {"id": "wayfarers_inn", "name": "Wayfarers' Inn Kitchen", "currency": "spirit_stone",
         "stock": [s("rice_ball"), s("herbal_tea"), s("jade_carp_congee"), s("cloudtop_orchid_broth"), s("thunderhorn_stew")]},
        {"id": "condensing_hall", "name": "Condensing Hall Stores", "currency": "spirit_stone",
         "stock": [s("clear_mind_pill"), s("soul_soothing_pill"), s("calm_incense"), s("sage_condensing_pill", price=90, requires=all_of(realm("heaven_glimpse_3"))),
                   s("sovereign_settling_pill", price=120, requires=all_of(realm("sage_sovereign_1")))]},
        # Phase E · the Shipwrights' Yard: sky ink for charts; timber, plates and plumes for hulls.
        {"id": "navigator", "name": "Navigator Sun's Charts", "currency": "spirit_stone",
         "stock": [s("sky_ink", price=30), s("clear_mind_pill"), s("recipe_scroll", learn="star_chart_lantern", price=400,
                                                                   requires=all_of(realm("sage_sovereign_3")))]},
        {"id": "shipwright", "name": "Lao's Slipway Stores", "currency": "spirit_stone", "buys_all": True,
         "stock": [s("spirit_wood", price=40), s("formation_stone"), s("stormsteel_ore")]},
        {"id": "oasis_keeper", "name": "Oasis of Bones Stores", "currency": "spirit_stone", "buys_all": True,
         "stock": [s("herbal_tea"), s("rice_ball"), s("viper_antidote"), s("qi_restoration_pill"), s("storm_blood_pill"), s("cactus_water", price=12),
                   s("tough_meat")]},
        # A back-room market (gap report G1 karma): every purchase is a small sin.
        {"id": "free_market", "name": "Broker Mu's Back Room", "currency": "spirit_stone", "black_market": True,
         "requires": {"all": [{"kind": "flag_set", "flag": "path_independent"}]},
         "stock": [s("manual_page", price=5), s("torn_manual", price=24), s("storm_blood_pill"), s("spirit_egg", price=36),
                   # S49 alignment: what Broker Mu keeps under the counter for the shadowed.
                   s("soul_core_mid", price=45, requires=all_of({"kind": "alignment_at_most", "value": -20})),
                   s("beast_essence_blood", price=25, requires=all_of({"kind": "alignment_at_most", "value": -20}))],
         "rotation": {"count": 2, "pool": [s("sage_condensing_pill", price=80), s("mirror_eye", price=70), s("jade_core", price=18),
                                           s("sentinel_core", price=30), s("frost_lotus", price=9)]}},
        # Part 8 (S49 karma): the Caravan Road's night peddler. +5 sin a purchase (karma.json "night_peddler").
        {"id": "night_peddler", "name": "Peddler Shao's Mat", "currency": "silver_tael", "black_market": True,
         "requires": {"all": [{"kind": "time_of_day", "phases": ["night"]}]},
         "stock": [s("manual_page", price=45), s("torn_manual", price=160), s("iron_needles", price=24), s("viper_smoke_pill", price=35),
                   s("bonding_offering_common", price=60), s("spirit_egg", price=900, requires=all_of(realm("qi_unfurling_1"))),
                   # S48 the Poison path: the peddler's copies of two poison arts.
                   s("technique_manual", learn="venom_needles", price=420, requires=all_of(realm("qi_unfurling_1"))),
                   s("technique_manual", learn="miasma_palm", price=900, requires=all_of(realm("heart_tempering_1"))),
                   # S48 the Blood path: only for those who lean demonic.
                   s("technique_manual", learn="crimson_palm", price=600, requires=all_of(realm("heart_tempering_1"), {"kind": "alignment_at_most", "value": -20})),
                   s("technique_manual", learn="blood_river_slash", price=1400, requires=all_of(realm("heart_tempering_5"), {"kind": "alignment_at_most", "value": -20})),
                   s("technique_manual", learn="sanguine_lotus", price=3200, requires=all_of(realm("cloud_stride_1"), {"kind": "alignment_at_most", "value": -20}))]},
        {"id": "ironroot_clan", "name": "Ironroot Clan Forge", "currency": "spirit_stone", "buys_all": True,
         "discount": {"flag": "clan_ironroot", "pct": 0.15},
         "stock": [s("stormsteel_jian"), s("stormsteel_spear"), s("stormsteel_gauntlets"), s("stormsteel_staff"), s("stormsilk_robe"),
                   s("stormsilk_boots"), s("stormsteel_ore"), s("bone_strengthening_pill"),
                   s("recipe_scroll", learn="nine_sword_array", price=60),
                   s("thunderhorn_stew", requires=all_of({"kind": "flag_set", "flag": "clan_ironroot"})),
                   # Sage grade for kin who have become Sovereigns: sunsteel and sunsilk, worked with Sunscar glass.
                   s("sunsteel_jian", requires=all_of({"kind": "flag_set", "flag": "clan_ironroot"}, realm("sage_sovereign_1"))),
                   s("sunsteel_spear", requires=all_of({"kind": "flag_set", "flag": "clan_ironroot"}, realm("sage_sovereign_1"))),
                   s("sunsteel_gauntlets", requires=all_of({"kind": "flag_set", "flag": "clan_ironroot"}, realm("sage_sovereign_1"))),
                   s("sunsteel_staff", requires=all_of({"kind": "flag_set", "flag": "clan_ironroot"}, realm("sage_sovereign_1"))),
                   s("sunsilk_robe", requires=all_of({"kind": "flag_set", "flag": "clan_ironroot"}, realm("sage_sovereign_1"))),
                   s("sunsilk_boots", requires=all_of({"kind": "flag_set", "flag": "clan_ironroot"}, realm("sage_sovereign_1")))]},
        {"id": "herders_camp", "name": "Herders' Camp", "currency": "spirit_stone", "buys_all": True,
         "stock": [s("tough_meat"), s("thunderhorn_stew"), s("bonding_offering_heaven"), s("storm_blood_pill")]},
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
         ("sage_condensing_pill", "mystic", [("roc_feather", 2), ("jade_core", 1), ("soulbell_flower", 2)], 1200),
         ("storm_blood_pill", "mystic", [("spark_pelt", 1), ("storm_shard", 2), ("soulbell_flower", 1)], 900),
         ("sovereign_settling_pill", "sage", [("ember_cactus", 2), ("worm_glass_tooth", 1), ("frost_lotus", 1)], 1500)]
    for pid, grade, inputs, t in A:
        r(pid, "alchemy", inputs, [(pid, 1)], grade, time_s=t)
    # Cooking (Part 8) incl. pet foods and bonding offerings
    C = [("herbal_tea", [("willow_moss", 1)], True), ("rice_ball", [("rice", 1)], True), ("riverfish_soup", [("river_minnow", 2)], False),
         ("boar_bone_broth", [("tough_meat", 2)], False), ("ember_pepper_stew", [("ember_pepper", 2), ("tough_meat", 1)], False),
         ("lotus_root_tea", [("mist_lotus", 1)], False), ("toad_oil_dumplings", [("toad_oil", 1), ("rice", 1)], False),
         ("cloudtop_orchid_broth", [("cloudtop_orchid", 1), ("tough_meat", 2)], False), ("jade_carp_congee", [("jade_carp_fish", 1), ("rice", 1)], False),
         ("roast_fish", [("river_minnow", 2)], False), ("ember_pepper_broth", [("ember_pepper", 1), ("tough_meat", 1)], False),
         ("bonding_offering_common", [("tough_meat", 1), ("rice", 1)], False), ("bonding_offering_earth", [("jade_carp_fish", 1), ("mist_lotus", 1)], False),
         ("bonding_offering_heaven", [("mist_trout", 2), ("cloudtop_orchid", 1)], False),
         ("thunderhorn_stew", [("tough_meat", 2), ("thunder_horn", 1)], False),
         ("cactus_water", [("ember_cactus", 1)], False)]
    for cid, inputs, default in C:
        r(cid, "cooking", inputs, [(cid, 1)], "plain", default=default, pet_food=cid in ("roast_fish", "ember_pepper_broth"))
    # Forge blueprints (weapons per family and armour per slot, per grade)
    bands = {"common": ("iron", "copper_ore", "riverstone", "boar_hide"), "earth": ("jadeiron", "jadeiron", "riverstone", "jade_scale"),
             "heaven": ("cloudsteel", "cloudsteel_ore", "jadeiron", "cloud_feather"), "mystic": ("mistjade", "mystic_ore", "cloudsteel_ore", "roc_feather"),
             "spirit": ("stormsteel", "stormsteel_ore", "mystic_ore", "spark_pelt"),
             "sage": ("sunsteel", "sunglass_ore", "stormsteel_ore", "scorpion_stinger")}
    for grade, (prefix, metal, second, binder) in bands.items():
        for fam in ["gauntlets", "jian", "spear", "short_blade", "staff", "bow", "heavy_sabre", "fan", "flute"]:
            r("%s_%s" % (prefix, fam), "smithing", [(metal, 6), (second, 3 if grade == "common" else 4), (binder, 2)], [("%s_%s" % (prefix, fam), 1)], grade)
    armour = {"common": ("cotton", "cloth_boots"), "earth": ("jadeiron", None), "heaven": ("cloudsilk", None), "mystic": ("mistjade", None),
              "spirit": ("stormsilk", None), "sage": ("sunsilk", None)}
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
    # Throwables (S47, Part 8): forged by the handful.
    r("iron_needles", "smithing", [("riverstone", 1), ("beetle_shell", 1)], [("iron_needles", 20)], "common", default=True)
    r("flying_knives", "smithing", [("jadeiron", 1)], [("flying_knives", 10)], "earth", default=True)
    r("thunderclap_pellet", "smithing", [("ore_dust", 2), ("ember_pepper", 1), ("lantern_wick", 1)], [("thunderclap_pellet", 3)], "common", default=True)
    # The Bright Mirror: a forge blueprint learned at Heart Tempering 1 (S47, Part 8).
    r("bright_mirror", "smithing", [("jadeiron", 6), ("pearl", 2)], [("bright_mirror", 1)], "earth")
    # S47 the sword swarm: the Nine Swords Array, a heaven-grade blueprint sold by the Ironroot Clan.
    r("nine_sword_array", "smithing", [("cloudsteel_ore", 9), ("jadeiron", 9), ("refining_essence", 6)], [("nine_sword_array", 1)], "heaven",
      requires_ranks={"smithing": "expert"})
    # Furnaces (S44, Part 8): forged whole at the forge, worn in the furnace slot.
    r("jadeiron_furnace", "smithing", [("jadeiron", 8), ("riverstone", 6), ("crab_shell", 4)], [("jadeiron_furnace", 1)], "earth",
      requires_ranks={"smithing": "adept"})   # the blueprint is sold by the Alchemist Guild (Part 8)
    r("cloudsteel_furnace", "smithing", [("cloudsteel_ore", 8), ("cloud_feather", 4), ("serpent_scale", 4)], [("cloudsteel_furnace", 1)],
      "heaven", default=True, requires_ranks={"smithing": "expert"})
    r("mistjade_furnace", "smithing", [("mystic_ore", 6), ("roc_feather", 4), ("vulture_plume", 4)], [("mistjade_furnace", 1)], "mystic",
      default=True, requires_ranks={"smithing": "master"})
    r("array_plate", "formations", [("blank_plate", 1), ("formation_stone", 1)], [("array_plate", 1)], "earth")
    # S47 imitation relics (v1.1): Expert smiths copy a boss relic's gift at 60%, with no spirit.
    r("moonshadow_jian", "smithing", [("cloudsteel_ore", 8), ("refining_essence", 4), ("mist_lotus", 2)], [("moonshadow_jian", 1)], "heaven",
      requires_ranks={"smithing": "expert"})
    r("drowsing_edge", "smithing", [("cloudsteel_ore", 8), ("refining_essence", 4), ("stormsteel_ore", 2)], [("drowsing_edge", 1)], "heaven",
      requires_ranks={"smithing": "expert"})
    r("killing_array_plate", "formations", [("blank_plate", 1), ("formation_stone", 1), ("ore_dust", 2)], [("killing_array_plate", 1)], "earth")
    r("binding_array_plate", "formations", [("blank_plate", 1), ("formation_stone", 1), ("willow_moss", 2)], [("binding_array_plate", 1)], "earth")
    # S47: the Revival Talisman moves to the talisman craft (Part 8), with the rest of Old Scribe Bai's recipes.
    T = [("flame_talisman", "common", [("talisman_paper", 1), ("cinnabar", 1), ("ember_pepper", 1)]),
         ("thunder_talisman", "earth", [("spirit_paper", 1), ("beast_blood_ink", 1), ("storm_feather", 1)]),
         ("iron_wall_talisman", "common", [("talisman_paper", 1), ("cinnabar", 1), ("beetle_shell", 2)]),
         ("wind_step_talisman", "common", [("talisman_paper", 1), ("cinnabar", 1), ("vulture_plume", 1)]),
         ("veil_talisman", "earth", [("spirit_paper", 1), ("restoration_ink", 1), ("tiny_hollow_shard", 1)]),
         ("binding_talisman", "earth", [("spirit_paper", 1), ("beast_blood_ink", 1), ("viper_fang", 1)]),
         ("revival_talisman", "common", [("talisman_paper", 1), ("cinnabar", 1), ("snapper_claw", 1)]),
         ("lightning_rod_talisman", "heaven", [("spirit_paper", 1), ("beast_blood_ink", 1), ("cloudsteel_ore", 1)])]
    for tid, grade, inputs in T:
        r(tid, "talisman", inputs, [(tid, 1)], grade, traced=True)
    r("beast_blood_ink", "talisman", [("hound_fang", 2), ("rat_tail", 2)], [("beast_blood_ink", 1)], "earth")
    r("spirit_paper", "talisman", [("talisman_paper", 1), ("mist_lotus", 1)], [("spirit_paper", 1)], "earth")
    # S16 star charts (Sage 3): 40 XP per route. Vessels need a smith's rank; the sloop a formation master's too.
    r("star_chart_wreck", "star_charting", [("star_reading", 4), ("sky_ink", 2)], [("star_chart_wreck", 1)], "sage", default=True, xp=40)
    r("star_chart_lantern", "star_charting", [("star_reading", 8), ("sky_ink", 4)], [("star_chart_lantern", 1)], "sage", xp=40)
    r("cloud_skiff", "shipwright", [("spirit_wood", 6), ("stormsteel_ore", 4), ("formation_stone", 2), ("harpy_plume", 3)], [("cloud_skiff", 1)],
      "sage", default=True, xp=60, requires_ranks={"smithing": "adept"})
    r("storm_sloop", "shipwright", [("spirit_wood", 10), ("comet_iron", 6), ("formation_stone", 4), ("kite_silk", 4)], [("storm_sloop", 1)],
      "sage", xp=90, requires_ranks={"smithing": "adept", "formations": "adept"})
    # S44 / Part 8 new forms. Oils, the poison pill, the draught and the incense are Mei Qing's common knowledge; the baths
    # come with the Bath station (Qi Unfurling 1); the Qi Flow Pill is the Alchemist Guild's Expert reward.
    r("qi_flow_pill", "alchemy", [("riverreed_ginseng_100", 1), ("jade_scale", 2), ("leech_oil", 1)], [("qi_flow_pill", 1)], "earth")
    r("viper_smoke_pill", "alchemy", [("venom_sac", 2), ("viper_fang", 1), ("river_mud", 1)], [("viper_smoke_pill", 1)], "common", default=True)
    r("viper_oil", "alchemy", [("venom_sac", 1), ("toad_oil", 1)], [("viper_oil", 1)], "common", default=True)
    r("ember_oil", "alchemy", [("ember_pepper", 2), ("toad_oil", 1)], [("ember_oil", 1)], "common", default=True)
    r("riverreed_draught", "alchemy", [("riverreed_ginseng_10", 1), ("river_minnow", 1)], [("riverreed_draught", 1)], "common", default=True, liquid=True)
    r("copper_body_bath", "alchemy", [("tortoise_plate", 2), ("mole_claw", 2), ("willow_moss", 4)], [("copper_body_bath", 1)], "common")
    r("beast_revival_pill", "alchemy", [("riverreed_ginseng_10", 2), ("tough_meat", 1), ("willow_moss", 1)], [("beast_revival_pill", 1)], "common")
    # S46 pet gear at the forge.
    r("bone_collar", "smithing", [("boar_hide", 2), ("mole_claw", 2)], [("bone_collar", 1)], "common", default=True)
    r("scale_talisman", "smithing", [("serpent_scale", 2), ("jade_scale", 2)], [("scale_talisman", 1)], "earth", default=True)
    r("reed_saddle", "smithing", [("cloth", 3), ("boar_hide", 2)], [("reed_saddle", 1)], "common", default=True)
    r("beast_marrow_washing_pill", "alchemy", [("riverreed_ginseng_100", 1), ("tough_meat", 3), ("mist_lotus", 1)], [("beast_marrow_washing_pill", 1)], "earth")
    r("marrow_washing_bath", "alchemy", [("riverreed_ginseng_100", 1), ("hound_fang", 3), ("ape_fur", 2), ("mist_lotus", 1)], [("marrow_washing_bath", 1)], "earth")
    # S48 body ladder: each body tier teaches the next tier's bath (Iron → Jade, Jade → Gold).
    r("jade_marrow_bath", "alchemy", [("cloudtop_orchid", 1), ("jade_scale", 3), ("guardian_stone", 2), ("mist_lotus", 2)], [("jade_marrow_bath", 1)], "heaven")
    r("golden_body_bath", "alchemy", [("frost_lotus", 1), ("thunder_horn", 2), ("snow_ape_hide", 2), ("cloudtop_orchid", 2)], [("golden_body_bath", 1)], "mystic")
    # S48 Core Forging: this pill needs a Heavenly Flame under the furnace; Elder Hu and Elder Sung teach it at Heart Tempering 9.
    r("heavenly_flame_pill", "alchemy", [("ember_pepper", 3), ("riverreed_ginseng_100", 1), ("serpent_core", 1)], [("heavenly_flame_pill", 1)], "earth",
      fire="heavenly_flame")
    r("calm_heart_incense", "alchemy", [("prayer_beads", 1), ("lantern_wick", 2), ("mist_lotus", 1)], [("calm_heart_incense", 1)], "earth", default=True)
    # S44 experimentation: hidden recipes of herbs alone, found by putting the right herbs in together.
    r("sunfire_pill", "alchemy", [("riverreed_ginseng_10", 1), ("ember_pepper", 1)], [("sunfire_pill", 1)], "common", hidden=True)
    r("stillwater_pill", "alchemy", [("mist_lotus", 1), ("soulbell_flower", 1), ("willow_moss", 1)], [("stillwater_pill", 1)], "earth", hidden=True)
    r("cloudstep_pill", "alchemy", [("cloudtop_orchid", 1), ("willow_moss", 2)], [("cloudstep_pill", 1)], "heaven", hidden=True)
    # S44 element affinity: a furnace of a pill's element adds 5% to its quality roll (the Nine-Dragon Cauldron is Water).
    PILL_ELEMENT = {"healing_pill": "wood", "qi_restoration_pill": "water", "qi_gathering_pill": "earth", "bone_strengthening_pill": "earth",
                    "purging_pill": "water", "viper_antidote": "wood", "tiger_blood_pill": "fire", "cleansing_pill": "water",
                    "foundation_guard_pill": "earth", "clear_mind_pill": "water", "meridian_reversal_pill": "metal",
                    "method_conversion_pill": "metal", "qi_refining_pill": "water", "soul_soothing_pill": "water",
                    "mind_lake_opening_pill": "water", "sage_condensing_pill": "metal", "storm_blood_pill": "wood",
                    "sovereign_settling_pill": "fire", "qi_flow_pill": "earth", "viper_smoke_pill": "wood", "viper_oil": "wood",
                    "ember_oil": "fire", "riverreed_draught": "water", "copper_body_bath": "earth", "marrow_washing_bath": "water",
                    "calm_heart_incense": "wood", "jade_marrow_bath": "water", "golden_body_bath": "metal", "heavenly_flame_pill": "fire", "sunfire_pill": "fire", "stillwater_pill": "water", "cloudstep_pill": "wood"}
    # S44 ancient recipes: split into pages across dungeons and secret realms (the pages are placed in world.py).
    ANCIENT = {"method_conversion_pill": 3, "sovereign_settling_pill": 4}
    ROLES = ["principal", "minister", "assistant", "envoy"]
    for x in R:
        if x["craft"] == "alchemy":
            x["element"] = PILL_ELEMENT.get(x["id"], "earth")
            # S44 recipe roles follow the recipe's order: Principal, Minister, Assistant, Envoy.
            x["roles"] = ROLES[:len(x["inputs"])]
            if x["id"] in ANCIENT:
                x["fragments"] = ANCIENT[x["id"]]
    entries("recipes", R)
    herb_conflicts()
    guilds()
    return {x["id"] for x in R}


def fish():
    rows = [
        {"id": "river_minnow", "item": "river_minnow", "spots": ["village_docks", "reed_shallows", "marsh_edge"], "weight": 60},
        {"id": "reed_perch", "item": "reed_perch", "spots": ["village_docks", "reed_shallows", "marsh_edge"], "weight": 35},
        {"id": "jade_carp", "item": "jade_carp_fish", "spots": ["bend_shore", "mirror_lake"], "weight": 50},
        {"id": "river_eel", "item": "river_eel", "spots": ["bend_shore"], "weight": 30},
        {"id": "mist_trout", "item": "mist_trout", "spots": ["falls_pool", "mirror_lake"], "weight": 50},
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
        # S20: Elder at Sage or higher; the Elder's token comes at Sage Sovereign 1 (the token upgrade).
        {"id": "elder", "name": "Elder", "requires": all_of(realm("sage_sovereign_1"))},
    ]
    write("sect_ranks.json", {"order": [x["id"] for x in ranks], "ranks": ranks})
    sect_roles()


def sect_roles():
    """S48 sect role variants (v0.9): each sect's signature line has a damage and a support variant, and a tree of
    three branches of five nodes bought with contribution. The support variant's healing grows with the crafts you
    have ranked up (profession_rank_up: sect roles scale)."""
    def mod(stat, value, op="pct_add"):
        return {"stat": stat, "op": op, "value": value}
    entries("sect_roles", [
        {"id": "jade_sect", "signature": ["flowing_palm", "palm_wave", "rising_tide"],
         "variants": {
             "damage": {"name": "Surging Tide", "desc": "The Jade signature arts strike 25% harder.", "mult": 0.25},
             "support": {"name": "Mending Current", "desc": "The Jade signature arts heal you and every ally within 220 by 4% of their health, and slow each foe they hit by 20% for two seconds.",
                         "heal_pct": 0.04, "radius": 220, "slow": {"id": "slow", "chance": 1.0, "power": 0.2, "duration_s": 2}}}},
        {"id": "cloud_sect", "signature": ["jade_thrust", "spear_lance", "dragon_tail_sweep"],
         "variants": {
             "damage": {"name": "Piercing Peak", "desc": "The Cloud signature arts strike 20% harder, reach one more foe and pierce 10% more armour.",
                        "mult": 0.2, "extra_targets": 1, "penetration": 0.1},
             "support": {"name": "Guarding Cloud", "desc": "The Cloud signature arts wrap you in a shield of 8% of your health for 4 s and heal allies within 220 by 3%.",
                         "shield_pct": 0.08, "shield_s": 4, "heal_pct": 0.03, "radius": 220, "allies_only": True}}},
    ], role_rank="outer_disciple", switch_cost=50, profession_scaling=0.05, profession_cap=0.5,
        tree={"branches": [
            {"id": "edge", "name": {"jade_sect": "Rushing Edge", "cloud_sect": "Peak Edge"}, "nodes": [
                {"cost": 60, "desc": "+3% attack", "mods": [mod("physical_attack", 0.03), mod("qi_attack", 0.03)]},
                {"cost": 120, "desc": "+3% attack", "mods": [mod("physical_attack", 0.03), mod("qi_attack", 0.03)]},
                {"cost": 200, "rank": "inner_disciple", "desc": "+10% crit damage", "mods": [mod("crit_damage", 0.1, "flat")]},
                {"cost": 320, "rank": "inner_disciple", "desc": "Signature arts ready 1 s sooner", "flags": {"signature_cooldown": -1.0}},
                {"cost": 480, "rank": "core_disciple", "desc": "Signature arts +15% damage", "flags": {"signature_mult": 0.15}}]},
            {"id": "lotus", "name": {"jade_sect": "Still Lotus", "cloud_sect": "Temple Lotus"}, "nodes": [
                {"cost": 60, "desc": "+5% healing received", "mods": [mod("healing_received", 0.05, "flat")]},
                {"cost": 120, "desc": "+10% QI recovery", "mods": [mod("qi_regen", 0.1)]},
                {"cost": 200, "rank": "inner_disciple", "desc": "+5% healing received", "mods": [mod("healing_received", 0.05, "flat")]},
                {"cost": 320, "rank": "inner_disciple", "desc": "The support variant heals half again as much", "flags": {"support_heal_mult": 0.5}},
                {"cost": 480, "rank": "core_disciple", "desc": "Signature arts cost 20% less QI", "flags": {"signature_cost": -0.2}}]},
            {"id": "root", "name": {"jade_sect": "Deep Root", "cloud_sect": "Mountain Root"}, "nodes": [
                {"cost": 60, "desc": "+4% max HP", "mods": [mod("max_hp", 0.04)]},
                {"cost": 120, "desc": "+5% Physical Defense", "mods": [mod("physical_defense", 0.05)]},
                {"cost": 200, "rank": "inner_disciple", "desc": "+5% Qi Resistance", "mods": [mod("qi_resistance", 0.05)]},
                {"cost": 320, "rank": "inner_disciple", "desc": "+5% Tenacity", "mods": [mod("tenacity", 0.05, "flat")]},
                {"cost": 480, "rank": "core_disciple", "desc": "Guard blocks 10% more", "mods": [mod("guard", 0.10)]}]},
        ]})


def auction():
    """S21 · the NPC auction house at the Auction Pavilion (Nine Peaks, Sage 1): rare lots, NPC bidders."""
    def lot(item, start, count=1, weight=1.0):
        return {"item": item, "count": count, "start": start, "weight": weight}
    write("auction.json", {
        "schema_version": 1,
        "lots_open": 4, "duration_h": [2, 6], "min_increment": 0.1,
        # An NPC's hidden limit is the opening price times this range; its bid drifts up to this share of the limit.
        "npc_limit": [1.4, 2.6], "npc_drift": 0.6,
        # The house premium on top of a winning bid, by the path the character chose at the Hall of Nine.
        "premium": {"none": 0.10, "alliance": 0.08, "independent": 0.04},
        "bidders": ["Madam Qiu of the Fifth Peak", "the Ironroot Steward", "a veiled buyer", "Merchant Fan", "an Alliance quartermaster"],
        "pool": [lot("sage_condensing_pill", 70, weight=0.6), lot("spirit_egg", 40), lot("torn_manual", 30), lot("jade_core", 24, 2),
                 lot("mirror_eye", 80, weight=0.5), lot("frost_lotus", 30, 3), lot("stormsteel_ore", 35, 10), lot("clear_mind_pill", 20, 3),
                 lot("fuel_crystal_mid", 30, 5), lot("spirit_stone_mid", 60, 5, weight=0.7), lot("storm_blood_pill", 25, 3),
                 lot("sentinel_core", 40, 2, weight=0.7), lot("manual_page", 18, 5)],
        # S49 Part 8: the valley's own auction day, on Market Street every Saturday (calendar "auction_day"): rare
        # seeds, recipe scrolls (taught when the hammer falls) and eggs, for Spirit Stones. Every lot closes with the day.
        "valley": {"calendar": "auction_day", "lots_open": 5, "duration_h": [3, 9], "npc_limit": [1.3, 2.2],
                   "premium": {"none": 0.06, "alliance": 0.06, "independent": 0.06},
                   "bidders": ["Madam Hua's steward", "Old Pan", "a Stoneford herbalist", "a Jade Sect deacon", "a caravan master"],
                   "pool": [lot("cloudtop_orchid_seed", 14, 2), lot("soulbell_flower_seed", 20), lot("riverreed_ginseng_seed", 8, 3),
                            lot("mist_lotus_seed", 6, 4), lot("spirit_egg", 18), lot("rare_spirit_egg", 45, weight=0.4),
                            dict(lot("recipe_scroll", 16, weight=0.8), learn="foundation_guard_pill"),
                            dict(lot("recipe_scroll", 12, weight=0.8), learn="cloudtop_orchid_broth"),
                            dict(lot("recipe_scroll", 20, weight=0.6), learn="clear_mind_pill"),
                            lot("manual_page", 8, 3), lot("longevity_peach", 30, weight=0.5)]},
    })


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


# S46 Beast Tide: once a real week at Stoneford Gate, three waves of rank 2-5 beasts (their Level follows yours,
# between 10 and 45). Hold for 90 seconds: cores, an egg (a Cloud Stag egg from Cloud Stride 1, once) and Spirit Soil.
BEAST_TIDE = {
    "room": "sf_gate", "realm": "qi_unfurling_1", "every_days": 7, "duration": 90,
    "waves": [{"enemy": "tide_crab", "first_s": 2, "every_s": 5, "max": 3, "until_s": 30, "level": "player", "level_offset": -4, "level_min": 10, "level_max": 45,
               "points": [[300, 860], [2200, 860]]},
              {"enemy": "wild_boarlet", "first_s": 30, "every_s": 6, "max": 3, "until_s": 60, "level": "player", "level_offset": -2, "level_min": 10, "level_max": 45,
               "points": [[300, 860], [2200, 860]]},
              {"enemy": "mud_hound", "first_s": 60, "every_s": 5, "max": 4, "level": "player", "level_offset": 0, "level_min": 10, "level_max": 45,
               "points": [[300, 860], [2200, 860]]}],
    "rewards": {"cores": 3, "egg": "spirit_egg", "stag_egg": "cloud_stag_egg", "stag_realm": "cloud_stride_1", "soil": 1}}


# S46 Beast Arena (Stoneford Market Street): a ladder of ten NPC tamers. Challenge the rank above you, five fights a
# day, in 1v1 (your active animal) or 3v3 (it and two more beside you or in the bag). Rewards by rank each week.
def _t(species, level, rarity="common", stage="juvenile"):
    return {"species": species, "level": level, "rarity": rarity, "stage": stage}


BEAST_ARENA = {
    "schema_version": 1, "fights_per_day": 5, "unranked": 11,
    "tamers": [
        {"id": "farmhand_qiao", "name": "Farmhand Qiao", "rank": 10, "solo": [_t("reed_otter", 18)], "trio": [_t("reed_otter", 16), _t("mossback_toad", 16), _t("reed_otter", 15)]},
        {"id": "herb_girl_yan", "name": "Herb-girl Yan", "rank": 9, "solo": [_t("mossback_toad", 22)], "trio": [_t("mossback_toad", 20), _t("reed_otter", 20), _t("ember_fox", 19)]},
        {"id": "ferry_boy_pu", "name": "Ferry-boy Pu", "rank": 8, "solo": [_t("reed_otter", 26, "fine")], "trio": [_t("reed_otter", 24, "fine"), _t("jade_crane", 23), _t("mossback_toad", 23)]},
        {"id": "hunter_dai", "name": "Hunter Dai", "rank": 7, "solo": [_t("mud_hound", 30, "fine")], "trio": [_t("mud_hound", 28, "fine"), _t("mist_wolf", 27), _t("ember_fox", 27)]},
        {"id": "bamboo_sister_wen", "name": "Bamboo Sister Wen", "rank": 6, "solo": [_t("bamboo_monkey", 34, "fine", "adult")],
         "trio": [_t("bamboo_monkey", 32, "fine", "adult"), _t("green_viper", 31, "fine"), _t("mossback_toad", 31, "fine")]},
        {"id": "caravan_guard_ruo", "name": "Caravan Guard Ruo", "rank": 5, "solo": [_t("ironclaw_mole", 38, "rare", "adult")],
         "trio": [_t("ironclaw_mole", 36, "rare", "adult"), _t("mud_hound", 35, "fine", "adult"), _t("cleansed_boarlet", 35, "fine", "adult")]},
        {"id": "old_tamer_kuai", "name": "Old Tamer Kuai", "rank": 4, "solo": [_t("mist_wolf", 42, "rare", "adult")],
         "trio": [_t("mist_wolf", 40, "rare", "adult"), _t("mist_vulture", 39, "rare", "adult"), _t("ember_fox", 39, "fine", "adult")]},
        {"id": "lady_feng_qiu", "name": "Lady Feng Qiu", "rank": 3, "solo": [_t("ember_fox", 46, "rare", "adult")],
         "trio": [_t("ember_fox", 44, "rare", "adult"), _t("jade_crane", 43, "rare", "adult"), _t("green_viper", 43, "rare", "adult")]},
        {"id": "beastmaster_tian", "name": "Beastmaster Tian", "rank": 2, "solo": [_t("jade_crane", 50, "epic", "adult")],
         "trio": [_t("jade_crane", 48, "epic", "adult"), _t("mist_wolf", 47, "rare", "adult"), _t("pale_stag", 47, "rare", "adult")]},
        {"id": "jing_mo", "name": "Jing Mo, the Hermit's Rival", "rank": 1, "solo": [_t("mist_wolf", 55, "epic", "awakened")],
         "trio": [_t("mist_wolf", 53, "epic", "awakened"), _t("ember_fox", 52, "epic", "adult"), _t("mud_hound", 52, "rare", "adult")]},
    ],
    # Weekly rewards by the rank held when the week turns (Spirit Stones plus an item for the top three).
    "rewards": [{"ranks": [1, 1], "spirit_stone": 30, "item": "beast_essence_blood"}, {"ranks": [2, 3], "spirit_stone": 15, "item": "beast_marrow_washing_pill"},
                {"ranks": [4, 6], "spirit_stone": 8}, {"ranks": [7, 10], "spirit_stone": 3}],
    # The auto-battle (PetRules.battle): stats from Level, rarity, growth and aptitude; one strike every 1.6 s (faster
    # with speed); an awakened skill every 12 s; at most 60 s, then the side with more health left wins.
    "battle": {"hp_base": 60, "hp_per_level": 12, "atk_base": 8, "atk_per_level": 2.2, "interval": 1.6, "max_s": 60.0, "step_s": 0.2,
               "variance": 0.1, "skill_every": 12.0, "stage_bonus": {"hatchling": 0.9, "juvenile": 1.0, "adult": 1.1, "awakened": 1.2, "sovereign": 1.3}},
    # S46 Beast Trial Grove: once a day the animals fight ten beasts while their keeper rallies them (the keeper's own
    # blows do no harm there). The first clear gives the Guardian Spirit skill book.
    "grove": {"room": "sf_beast_grove", "duration": 150, "count": 10, "level_offset": -2, "level_min": 10, "level_max": 60,
              "waves": [{"enemy": "wild_boarlet", "first_s": 2, "every_s": 5, "max": 2, "points": [[1300, 860], [1800, 860]]},
                        {"enemy": "mud_hound", "first_s": 20, "every_s": 7, "max": 2, "points": [[1300, 860], [1800, 860]]},
                        {"enemy": "tide_crab", "first_s": 40, "every_s": 8, "max": 1, "points": [[1300, 860], [1800, 860]]}],
              "rally": {"mult": 1.25, "seconds": 5.0, "cd": 8.0},
              "first": "pet_book_guardian_spirit",
              "pool": [{"item": "beast_essence_blood", "weight": 3}, {"item": "beast_marrow_washing_pill", "weight": 3},
                       {"item": "pet_book_iron_hide", "weight": 2}, {"item": "pet_book_frenzy", "weight": 1}, {"item": "pet_book_thunder_roar", "weight": 1}]},
}


def pets():
    rows = [
        # S48 the puppet caster: one combat puppet from Cloud Stride 5, built at the tinkerer's bench. A construct: it
        # takes a pet slot and fights beside you, but it neither eats, bonds, breeds, fuses nor grows; it is repaired.
        {"id": "combat_puppet", "name": "Combat Puppet", "art": "trial_puppet", "element": "none", "strength_role": "combat", "construct": True,
         "skills": ["Iron Palm", "Guard Frame", "Counterweight", "Overdrive"], "favourite_foods": [], "branches": [],
         "inherit_owner": {"hatchling": 0.35, "juvenile": 0.35, "adult": 0.35}, "family": "construct",
         "movement": {"jump": 300, "climb": False, "fly": False, "drop": True}},
        {"id": "reed_otter", "name": "Reed Otter", "art": "reed_otter", "element": "water", "strength_role": "gatherer", "starter": True,
         "skills": ["Splash", "Reed Dive", "Otter Current", "River Gift"], "favourite_foods": ["roast_fish", "riverfish_soup"],
         "branches": ["River Otter Sage", "Tide Otter"], "inherit_owner": {"hatchling": 0.2, "juvenile": 0.3, "adult": 0.35}},
        {"id": "ember_fox", "name": "Ember Fox", "art": "ember_fox", "element": "fire", "strength_role": "combat", "starter": True,
         "skills": ["Ember Bite", "Flare", "Fox Fire", "Nine Embers"], "favourite_foods": ["roast_fish", "ember_pepper_broth"],
         "branches": ["Twin-Tail Fox", "Hearth Fox"], "inherit_owner": {"hatchling": 0.25, "juvenile": 0.32, "adult": 0.4},
         "mount": {"art": "ember_fox", "scale": 1.3, "lift": 0, "saddle": 40}},
        {"id": "jade_crane", "name": "Jade Crane", "art": "jade_crane_chick", "element": "wind", "strength_role": "mount", "starter": True,
         "skills": ["Wing Buffet", "Crane Call", "Cloud Lift", "Sky Dance"], "favourite_foods": ["mist_trout", "lotus_root_tea"],
         "branches": ["Cloud Crane", "Sage Crane"], "inherit_owner": {"hatchling": 0.2, "juvenile": 0.3, "adult": 0.35},
         "mount": {"art": "cloudwing_crane", "scale": 1.0, "lift": 34, "saddle": 44, "flying": True}},
        {"id": "mossback_toad", "name": "Mossback Toad", "art": "mossback_toad", "element": "wood", "strength_role": "gatherer", "tame": True,
         "skills": ["Tongue Lash", "Moss Shield", "Herb Sense", "Garden Back"], "favourite_foods": ["frog_leg", "rice_ball"], "branches": ["Moss Sage Toad", "Thorn Toad"]},
        {"id": "ironclaw_mole", "name": "Ironclaw Mole", "art": "ironclaw_mole", "element": "earth", "strength_role": "gatherer", "tame": True,
         "skills": ["Dig", "Ore Sense", "Tunnel Rush", "Gem Find"], "favourite_foods": ["tough_meat", "boar_bone_broth"], "branches": ["Gem Mole", "Burrow Guard"]},
        {"id": "bamboo_monkey", "name": "Bamboo Monkey", "art": "bamboo_monkey", "element": "wood", "strength_role": "combat", "tame": True,
         "skills": ["Shoot Toss", "Pickpocket", "Vine Swing", "Monkey Chaos"], "favourite_foods": ["bamboo_shoot", "rice_ball"], "branches": ["Monkey Thief", "Staff Monkey"]},
        {"id": "mist_wolf", "name": "Mist Wolf", "art": "mist_wolf", "element": "soul", "strength_role": "combat", "tame": True,
         "skills": ["Mist Bite", "Howl", "Fog Step", "Moon Hunt"], "favourite_foods": ["tough_meat", "riverfish_soup"], "branches": ["Fog Wolf", "Moon Wolf"],
         "mount": {"art": "mist_wolf", "scale": 0.9, "lift": 0, "saddle": 50}},
        # S46: demonic beasts, tamed with a Purifying Offering, and Hollowed ones, tamed once cleansed.
        {"id": "green_viper", "name": "Green Viper", "art": "green_viper", "element": "wood", "strength_role": "combat", "tame": True, "nature": "demonic",
         "skills": ["Venom Fang", "Coil", "Shed Skin", "Emerald Strike"], "favourite_foods": ["frog_leg", "tough_meat"], "branches": ["Jade Serpent", "Thorn Viper"]},
        {"id": "mud_hound", "name": "Mud Hound", "art": "mud_hound", "element": "earth", "strength_role": "combat", "tame": True, "nature": "demonic",
         "skills": ["Mud Bite", "Bay", "Wallow", "Pack Hunt"], "favourite_foods": ["tough_meat", "boar_bone_broth"], "branches": ["Iron Hound", "Marsh Hound"]},
        {"id": "mist_vulture", "name": "Mist Vulture", "art": "mist_vulture", "element": "wind", "strength_role": "gatherer", "tame": True, "nature": "demonic",
         "skills": ["Carrion Dive", "Updraft", "Keen Eye", "Wake Circle"], "favourite_foods": ["tough_meat", "roast_fish"], "branches": ["Storm Vulture", "Grey Warden"]},
        {"id": "cleansed_boarlet", "name": "Cleansed Boarlet", "art": "wild_boarlet", "element": "earth", "strength_role": "combat", "tame": True, "nature": "hollowed",
         "skills": ["Charge", "Root Up", "Bristle", "Second Wind"], "favourite_foods": ["rice_ball", "boar_bone_broth"], "branches": ["Iron Boar", "Thorn Boar"]},
        {"id": "pale_stag", "name": "Pale Stag", "art": "hollow_stag", "element": "soul", "strength_role": "cultivation", "tame": True, "nature": "hollowed",
         "skills": ["Antler Sweep", "Pale Call", "Moonstep", "Stillness"], "favourite_foods": ["lotus_root_tea", "rice_ball"], "branches": ["Moon Stag", "Ghost Stag"]},
        # S46 mount-only species: they carry you and never fight. The ox walks x1.5 (jump 530, no climbing); the stag
        # walks x1.6 and jumps 600 (an apex of about 157).
        {"id": "riverstone_ox", "name": "Riverstone Ox", "art": "riverstone_ox", "element": "earth", "strength_role": "mount", "tame": True, "mount_only": True,
         "skills": ["Steady Hoof", "Ford the River", "Stone Back", "Long Road"], "favourite_foods": ["rice_ball", "bamboo_shoot"], "branches": ["Mountain Ox", "River Ox"],
         "mount": {"art": "riverstone_ox", "scale": 1.35, "lift": 0, "saddle": 50, "speed": 1.5}},
        {"id": "cloud_stag", "name": "Cloud Stag", "art": "cloud_stag", "element": "wind", "strength_role": "mount", "mount_only": True,
         "skills": ["Cloud Step", "Wind Leap", "Sky Call", "Heaven's Stride"], "favourite_foods": ["lotus_root_tea", "mist_trout"], "branches": ["Sky Stag", "Mist Stag"],
         "mount": {"art": "cloud_stag", "scale": 1.1, "lift": 0, "saddle": 60, "speed": 1.6}},
    ]
    # Breeding pairs two Adults of one family (S22).
    family = {"reed_otter": "river", "mossback_toad": "river", "ember_fox": "hound", "mist_wolf": "hound",
              "ironclaw_mole": "burrow", "bamboo_monkey": "burrow", "jade_crane": "wing",
              "green_viper": "river", "mud_hound": "hound", "mist_vulture": "wing", "cleansed_boarlet": "burrow", "pale_stag": "hound",
              "riverstone_ox": "hoof", "cloud_stag": "hoof"}
    # S43 rule 12: how each animal follows along the navigation graph (ground mounts jump at 530; none climb).
    jumps = {"reed_otter": 430, "ember_fox": 530, "jade_crane": 530, "mossback_toad": 600, "ironclaw_mole": 0, "bamboo_monkey": 600, "mist_wolf": 530,
             "green_viper": 0, "mud_hound": 530, "mist_vulture": 530, "cleansed_boarlet": 430, "pale_stag": 600,
             "riverstone_ox": 530, "cloud_stag": 600}
    # S46 bloodline: at 50 purity an ancestral skill awakens (a heavy strike every 12 s in a fight; the free cast
    # of an Equal Contract); at 90 the animal changes form (+10% to every stat, a larger, tinted body).
    ancestry = {
        "reed_otter": ("Ancestral Tide", "Tide-Mother Otter", "#9fe0ff"),
        "ember_fox": ("Nine-Tail Flame", "Nine-Tail Fox", "#ffc070"),
        "jade_crane": ("Thousand-League Wing", "Azure Sky Crane", "#a8f0e0"),
        "mossback_toad": ("Moon-Swallowing Croak", "Jade Moon Toad", "#c8f0a0"),
        "ironclaw_mole": ("Earth Vein Burrow", "Mountain-Moving Mole", "#e0c890"),
        "bamboo_monkey": ("Hundred Staff Storm", "Cloud-Staff Ape", "#f0e0a0"),
        "mist_wolf": ("Moon-Devouring Howl", "Heaven-Howl Wolf", "#d8d0ff"),
        "green_viper": ("Emerald Flood Coil", "Jade Flood Serpent", "#90f0b0"),
        "mud_hound": ("Earth-Shaking Bay", "Stone Lion Hound", "#e8c8a0"),
        "mist_vulture": ("Storm-Cleaving Dive", "Thunder Roc", "#c0d8ff"),
        "cleansed_boarlet": ("Mountain Charge", "Ancient Iron Boar", "#d0c0b0"),
        "pale_stag": ("White Moon Antler", "Moon-Crowned Stag", "#f0f0ff"),
        "riverstone_ox": ("Riverbed Stampede", "Mountain-Bearing Ox", "#e0d8c0"),
        "cloud_stag": ("Sky-Treading Leap", "Heavenly Cloud Stag", "#e8f4ff"),
    }
    for r in rows:
        if r.get("construct"):
            continue  # A construct has no blood to awaken and keeps its own family and movement.
        sk, form, tint = ancestry[r["id"]]
        r["bloodline_skill"] = {"name": sk, "mult": 2.5}
        r["form_change"] = {"name": form, "scale": 1.15, "tint": tint}
        r["family"] = family[r["id"]]
        r["movement"] = {"jump": jumps[r["id"]], "climb": r["id"] == "bamboo_monkey", "fly": False, "drop": True}
    entries("pets", rows)
    write("beast_arena.json", BEAST_ARENA)
    # S46 pet skill books: what a learned skill adds (read by the pet authority, combat and the herb nodes) and where
    # its book is found. Guardian Spirit's book waits in the Beast Trial Grove.
    entries("pet_skill_books", [
        {"id": "iron_hide", "name": "Iron Hide", "effect": "+10% defence", "bonus": {"pet_damage_taken": -0.10}, "source": "Beast Hall shop"},
        {"id": "frenzy", "name": "Frenzy", "effect": "+15% attack speed for 6 s after a kill", "frenzy": {"speed": 0.15, "seconds": 6.0}, "source": "Mudwater Boss Den"},
        {"id": "deep_pockets", "name": "Deep Pockets", "effect": "+1 bag row while active", "bag_slots": 6, "source": "Beast Hall shop"},
        {"id": "herb_whisper", "name": "Herb Whisper", "effect": "Shows ripening timers within 400 units", "whisper": 400, "source": "Falls Pool chest"},
        {"id": "thunder_roar", "name": "Thunder Roar", "effect": "Stun ring, 1 s", "roar": {"radius": 130, "stun_s": 1.0, "every_s": 15.0}, "source": "Stormwing Hawk elite"},
        {"id": "guardian_spirit", "name": "Guardian Spirit", "effect": "Absorbs one hit on the owner every 30 s", "guard_every_s": 30.0, "source": "Beast Trial Grove"},
    ])
    # Three hidden traits per animal, revealed at Juvenile, Awakened and Sovereign. `bonus` is what a revealed
    # trait of the active animal adds (read by the system that owns that number).
    entries("pet_traits", [
        {"id": "deep_diver", "name": "Deep Diver", "effect": "+30% time to strike a bite", "bonus": {"fish_chance": 0.3}},
        {"id": "stormborn", "name": "Stormborn", "effect": "+15% pet damage", "bonus": {"pet_damage": 0.15}},
        {"id": "keen_nose", "name": "Keen Nose", "effect": "+10% herb yield", "bonus": {"herb_yield": 0.1}},
        {"id": "iron_hide", "name": "Iron Hide", "effect": "Takes 10% less damage", "bonus": {"pet_damage_taken": -0.1}},
        {"id": "quick_paws", "name": "Quick Paws", "effect": "+10% pet damage", "bonus": {"pet_damage": 0.1}},
        {"id": "lucky_find", "name": "Lucky Find", "effect": "+5% drop chance", "bonus": {"drop_chance": 0.05}},
        {"id": "calm_spirit", "name": "Calm Spirit", "effect": "+5% Resonance", "bonus": {"resonance": 0.05}},
        {"id": "loyal", "name": "Loyal", "effect": "+50% bond from food", "bonus": {"bond_gain": 0.5}},
    ])
    # S22 stages: every gate (level, hearts, owner realm) must be met. Inherit = share of the owner's attack;
    # resonance = accumulation bonus while in the Cultivation role (from Spirit Awakening 1).
    write("pet_growth.json", {"schema_version": 1, "traits_per_pet": 3, "role_match_bonus": 0.25, "hungry_mult": 0.7,
                              # S22 Mount role: walk x1.5 (ground mounts from Cloud Stride 1); flying mounts carry you at
                              # half the flight QI from Cloud Stride 5; a blow of 15% HP throws you off for 10 s.
                              "mount_unlock": "mounts", "mount_speed": 1.5, "flying_mount_realm": "cloud_stride_5",
                              "flying_mount_qi": 0.5, "dismount_hp_pct": 0.15, "dismount_s": 10,
                              "resonance_unlock": "spirit_awakening_1", "hp_share": 0.4, "retreat_s": 60,
                              # S46 depth. Bloodline purity 0-100 is rolled by rarity; growth (0.8-1.3) and per-stat
                              # aptitude (0.8-1.2) are hidden until Juvenile; learned-skill slots open by stage; 1% of
                              # hatchlings wear a colour variant.
                              "purity": {"common": [5, 15], "fine": [15, 30], "rare": [30, 45], "epic": [45, 60], "primordial": [60, 80]},
                              "growth": [0.8, 1.3], "aptitude": {"stats": ["hp", "attack", "defence", "speed"], "range": [0.8, 1.2]},
                              "skill_slots": {"hatchling": 0, "juvenile": 2, "adult": 3, "awakened": 4, "sovereign": 4, "primordial": 4},
                              "colour_variant": 0.01,
                              # Grievous Wound: three knockouts in five minutes leave the animal at 80% until it rests at
                              # the Beast Hall or the Beast Pavilion, or takes a Beast Revival Pill.
                              "grievous": {"knockouts": 3, "window_s": 300, "mult": 0.8},
                              # Bloodline awakenings: the ancestral skill at 50 purity, the form change at 90; every point
                              # of purity strengthens revealed traits by 0.2%. Essence blood adds 10.
                              "awakening": {"skill_at": 50, "form_at": 90, "trait_per_purity": 0.002, "skill_cd": 12.0,
                                            "form_bonus": 0.10, "essence_blood": 10},
                              # Suppression (the Pressure contest): an animal's bloodline tier (rarity step + awakenings)
                              # against a wild beast's (rank / 2, +1 elite, +2 boss). Above it: Fear and +10% taming.
                              "suppression": {"rank_div": 2, "elite": 1, "boss": 2, "fear_s": 2.0, "tame_bonus": 0.10,
                                              "reach": 260, "every_s": 1.0},
                              # Contracts. Equal: offered at 10 hearts, one per character, forever: Resonance flows both
                              # ways (the owner's meditation feeds the animal, whatever its role) and one free skill
                              # cast a fight. Blood: sealed with essence blood, +15% stats, a knockout bruises your soul.
                              "contracts": {"equal": {"hearts": 10, "free_cast_mult": 2.5, "resonance_share": 0.5, "calm_s": 5.0,
                                                      "xp_per_tick": 0.5},
                                            "blood": {"stats": 0.15, "item": "beast_essence_blood", "soul_injury": 1}},
                              # Command capacity tied to Soul: animals that fight beside you at once.
                              "command": [{"realm": "", "count": 1}, {"realm": "spirit_awakening_1", "count": 2}, {"realm": "sage_1", "count": 3}],
                              # Incubation input, once of each kind per egg: drip your own essence blood (-10% max HP for
                              # 24 h, +10 purity), a beast core to steer its element, or Beast Essence Blood to reroll one
                              # hidden trait. Animals you hatch yourself start at 3 hearts.
                              # S46 rarity at tame and hatch (bred eggs keep their own): a wild beast is mostly Common, an elite
                              # finer; a plain egg now and then Rare; a Beast King's nest egg is Rare or better.
                              "rarity_roll": {"tame": {"common": 70, "fine": 22, "rare": 7, "epic": 1},
                                              "tame_elite": {"fine": 55, "rare": 35, "epic": 10},
                                              "egg": {"common": 65, "fine": 25, "rare": 8, "epic": 2},
                                              "rare": {"rare": 75, "epic": 22, "primordial": 3}},
                              # Swapping animals: anywhere you are safe (a town, a sect, a rest stop, home), and in the field
                              # only from your Spirit Beast Bag, never in a fight.
                              "safe_rooms": ["town", "sect", "rest", "home", "interior"], "combat_reach": 600,
                              # The Pavilion Feeding Trough (Beast Pavilion 1+): each day it feeds hungry animals from storage.
                              "trough": {"pavilion": "beast_pavilion", "level": 1},
                              "incubation": {"blood": {"purity": 10, "max_hp_pct": -0.10, "hours": 24}, "reroll_item": "beast_essence_blood",
                                             "hatch_hearts": 3},
                              # Fusion (at the Beast Hall): the kept animal gets a 30% chance at each of the other's traits
                              # and learned skills, plus half of its purity above its own. Locked animals are never fused.
                              "fusion": {"trait_chance": 0.3, "skill_chance": 0.3, "purity_share": 0.5, "max_traits": 5},
                              # Pet gear: each enhancement level adds 10% of the piece's base.
                              "gear": {"slots": ["pet_collar", "pet_talisman", "pet_saddle"], "per_enhance": 0.1},
                              # Pet breakthroughs from Awakened on: a chance raised by purity and support items (cores of
                              # its element, essence blood; three at most); a failure costs a heart or a Grievous Wound.
                              # Pet Core Formation (Adult to Awakened) rolls a core grade from points; it adds to every stat.
                              "breakthrough": {"from": "awakened", "base": 0.55, "per_purity": 0.002, "cap": 0.95, "max_support": 3,
                                               "support": {"low": 0.05, "mid": 0.10, "high": 0.15, "peak": 0.20, "beast_essence_blood": 0.15},
                                               "fail_heart_share": 0.5},
                              "core_grades": [{"id": "cracked", "name": "Cracked Core", "min": 0, "bonus": 0.0},
                                              {"id": "common", "name": "Common Core", "min": 35, "bonus": 0.05},
                                              {"id": "fine", "name": "Fine Core", "min": 60, "bonus": 0.10},
                                              {"id": "flawless", "name": "Flawless Core", "min": 85, "bonus": 0.18}],
                              "core_points": {"per_purity": 0.5, "per_growth": 60, "per_support": 8, "roll": 20},
                              # Beast cores (rank 2+ at 2% a rank) by tier: the XP a pet of their element gains devouring
                              # one, and what the Core Exchange pays in Spirit Stones (capped at 60 a day).
                              "cores": {"min_rank": 2, "chance_per_rank": 0.02, "tiers": {"low": [2, 3], "mid": [4, 5], "high": [6, 7], "peak": [8, 9]},
                                        "xp": {"low": 60, "mid": 200, "high": 600, "peak": 1500},
                                        "price": {"low": 1, "mid": 3, "high": 8, "peak": 20}, "daily_cap": 60},
                              # S22 rarity scales the animal's strength; breeding (Heaven Glimpse 1, Beast Pavilion 4) pairs
                              # two Adults of one family for 24 h, then the egg hatches in 2-24 h. The child takes the
                              # higher rarity, may step up one, mixes its parents' traits and may carry a new one.
                              "rarities": [{"id": "common", "name": "Common", "power": 1.0}, {"id": "fine", "name": "Fine", "power": 1.1},
                                           {"id": "rare", "name": "Rare", "power": 1.25}, {"id": "epic", "name": "Epic", "power": 1.45},
                                           {"id": "primordial", "name": "Primordial", "power": 1.7}],
                              "breeding": {"unlock": "pet_breeding", "pavilion": "beast_pavilion", "pavilion_level": 4, "stage": "adult",
                                           "hours": 24, "hatch_hours": [2, 24], "rarity_step": 0.2, "mutation": 0.2,
                                           "bred_rarity_cap": "epic"},
                              "stages": [
                                  {"id": "hatchling", "name": "Hatchling", "inherit": 0.2, "resonance": 0.0},
                                  {"id": "juvenile", "name": "Juvenile", "level": 15, "bond": 3, "realm": "heart_tempering_1", "reveal_trait": True, "inherit": 0.3, "resonance": 0.05},
                                  {"id": "adult", "name": "Adult", "level": 35, "bond": 5, "realm": "spirit_awakening_1", "branch": True, "inherit": 0.35, "resonance": 0.1},
                                  {"id": "awakened", "name": "Awakened", "level": 55, "bond": 7, "realm": "sage_1", "reveal_trait": True, "inherit": 0.4, "resonance": 0.2},
                                  {"id": "sovereign", "name": "Sovereign", "level": 75, "bond": 9, "realm": "sphere_lord_1", "reveal_trait": True, "inherit": 0.4, "resonance": 0.3},
                                  {"id": "primordial", "name": "Primordial", "level": 95, "bond": 10, "realm": "inner_heaven_1", "primordial_only": True, "inherit": 0.4, "resonance": 0.3}]})


def achievements():
    A = [
        {"id": "fleet_footed", "name": "Fleet-Footed", "desc": "Win the race to the tower", "event": "quest_completed", "match": {"quest": "race_to_the_tower"}, "title": "fleet_footed"},
        {"id": "crab_catcher", "name": "Crab Catcher", "desc": "Defeat 100 Mudshell Crabs", "event": "actor_defeated", "match": {"def": "mudshell_crab"}, "count": 100, "title": "shore_warden"},
        {"id": "first_current", "name": "First Current", "desc": "Reach Bone Forging 7", "event": "realm_changed", "match": {"realm_at_least": "bone_forging_7"},
         "rewards": [{"kind": "grant_item", "item": "qi_gathering_pill", "count": 1}]},
        {"id": "iron_fist", "name": "Iron Fist", "desc": "Reach Qi Kindling 1 without equipping a weapon", "event": "realm_changed",
         "match": {"realm_at_least": "qi_kindling_1", "no_weapon": True, "to": "qi_kindling_1"}, "title": "iron_fist"},
        {"id": "steady_hands", "name": "Steady Hands", "desc": "Refine a Perfect pill", "event": "craft_completed", "match": {"craft": "alchemy", "quality": "perfect"}, "title": "steady_hands"},
        {"id": "grain_of_heaven", "name": "Grain of Heaven", "desc": "Refine a Pill Grain", "event": "craft_completed", "match": {"craft": "alchemy", "quality": "pill_grain"},
         "rewards": [{"kind": "grant_item", "item": "spirit_stone_mid", "count": 3}]},
        {"id": "the_furnace_breathes", "name": "The Furnace Breathes", "desc": "Refine a Pill Soul", "event": "craft_completed", "match": {"craft": "alchemy", "quality": "pill_soul"},
         "rewards": [{"kind": "grant_item", "item": "spirit_stone_mid", "count": 10}]},
        {"id": "deep_roots", "name": "Deep Roots", "desc": "Reach Mining Adept", "event": "profession_rank_up", "match": {"craft": "mining", "rank": "adept"}, "title": "stonebreaker"},
        {"id": "untouched", "name": "Untouched", "desc": "Defeat a dungeon boss without being gravely wounded", "event": "boss_defeated", "match": {"clean": True}, "title": "untouched"},
        {"id": "collector", "name": "Collector", "desc": "Fill 10 collection cards", "event": "collection_card_filled", "count": 10, "title": "collector"},
        {"id": "traveller", "name": "Traveller", "desc": "Visit every valley room", "event": "room_entered", "match": {"all_valley_rooms": True}, "title": "wanderer"},
        {"id": "patient_heart", "name": "Patient Heart", "desc": "Pass the Heart Trial on the first try", "event": "event_passed", "match": {"event": "heart_trial", "first_try": True}, "title": "still_water"},
        {"id": "friend_of_beasts", "name": "Friend of Beasts", "desc": "Bond 3 spirit animals", "event": "pet_bonded", "count": 3, "title": "beast_friend"},
        {"id": "valley_champion", "name": "Valley Champion", "desc": "Win the Valley Tournament", "event": "tournament_won", "title": "valley_champion"},
        # Act II · the Azure Expanse
        {"id": "beyond_the_gate", "name": "Beyond the Gate", "desc": "Reach Sage 1 in the Azure Expanse", "event": "realm_changed",
         "match": {"realm_at_least": "sage_1"}, "title": "sage_born"},
        {"id": "weasel_wrangler", "name": "Weasel Wrangler", "desc": "Defeat 100 Spark Weasels", "event": "actor_defeated",
         "match": {"def": "spark_weasel"}, "count": 100, "title": "storm_herder"},
        {"id": "thousand_eyes_closed", "name": "Thousand Eyes Closed", "desc": "Silence the Thousand-Eye Toad", "event": "actor_defeated",
         "match": {"def": "thousand_eye_toad"}, "rewards": [{"kind": "grant_item", "item": "spirit_stone_mid", "count": 5}]},
        {"id": "the_king_sleeps", "name": "The King Sleeps", "desc": "Defeat the Tomb King of Sunscar", "event": "actor_defeated",
         "match": {"def": "tomb_king"}, "title": "sunscar_victor"},
        {"id": "cast_off", "name": "Cast Off", "desc": "Cross the Starsea in a vessel you built", "event": "voyage_arrived", "title": "starsea_sailor"},
        {"id": "the_gate_holds", "name": "The Gate Holds", "desc": "Win the sect war at the Alliance Gate", "event": "event_passed",
         "match": {"event": "sect_war"}, "title": "gate_defender"},
        {"id": "eight_seats_bowed", "name": "Eight Seats Bowed", "desc": "Pass the Presence Trial", "event": "event_passed",
         "match": {"event": "presence_trial"}, "title": "presence_bearer"},
    ]
    entries("achievements", A)
    T = [
        {"id": "fleet_footed", "name": "Fleet-Footed", "modifiers": [{"stat": "move_speed", "op": "pct_add", "value": 0.01}]},
        {"id": "sage_born", "name": "Sage-Born", "modifiers": [{"stat": "accumulation_rate", "op": "flat", "value": 0.01}]},
        {"id": "storm_herder", "name": "Storm Herder", "modifiers": [{"stat": "attunement_bonus", "op": "flat", "value": 1}]},
        {"id": "alliance_envoy", "name": "Alliance Envoy", "modifiers": [{"stat": "attunement_bonus", "op": "flat", "value": 2}]},
        {"id": "free_cultivator", "name": "Free Cultivator", "modifiers": [{"stat": "drop_rate", "op": "pct_add", "value": 0.03}]},
        {"id": "ironroot_kin", "name": "Ironroot Kin", "modifiers": [{"stat": "max_hp", "op": "pct_add", "value": 0.04}]},
        {"id": "seal_keeper", "name": "Keeper of the Sun Seal", "modifiers": [{"stat": "qi_attack", "op": "pct_add", "value": 0.03}]},
        {"id": "sunscar_sealer", "name": "Sealer of Sunscar", "modifiers": [{"stat": "max_soul", "op": "pct_add", "value": 0.05}]},
        {"id": "sunscar_victor", "name": "Kingsbane of Sunscar", "modifiers": [{"stat": "essence", "op": "flat", "value": 3}]},
        {"id": "starsea_sailor", "name": "Starsea Sailor", "modifiers": [{"stat": "spirit", "op": "flat", "value": 3}]},
        {"id": "gate_defender", "name": "Defender of the Alliance Gate", "modifiers": [{"stat": "physical_defense", "op": "pct_add", "value": 0.03}]},
        {"id": "ledger_burner", "name": "The Ledger's Ashes", "modifiers": [{"stat": "will", "op": "pct_add", "value": 0.03}]},
        {"id": "ledger_returner", "name": "Bearer of Old Debts", "modifiers": [{"stat": "fortune", "op": "flat", "value": 3}]},
        {"id": "presence_bearer", "name": "Bearer of Presence", "modifiers": [{"stat": "will", "op": "pct_add", "value": 0.05}]},
        {"id": "starsea_voyager", "name": "Voyager of the Starsea", "modifiers": [{"stat": "attunement_bonus", "op": "flat", "value": 2}]},
        {"id": "shore_warden", "name": "Shore Warden", "modifiers": [{"stat": "physical_defense", "op": "pct_add", "value": 0.01}]},
        {"id": "iron_fist", "name": "Iron Fist", "modifiers": [{"stat": "fist_attack", "op": "pct_add", "value": 0.01}]},
        {"id": "steady_hands", "name": "Steady Hands", "modifiers": [{"stat": "crafting_control", "op": "pct_add", "value": 0.01}]},
        {"id": "stonebreaker", "name": "Stonebreaker", "modifiers": [{"stat": "mining_power", "op": "pct_add", "value": 0.01}]},
        {"id": "untouched", "name": "Untouched", "modifiers": [{"stat": "evasion", "op": "pct_add", "value": 0.01}]},
        {"id": "collector", "name": "Collector", "modifiers": [{"stat": "drop_rate", "op": "pct_add", "value": 0.01}]},
        {"id": "wanderer", "name": "Wanderer", "modifiers": [{"stat": "move_speed", "op": "pct_add", "value": 0.01}]},
        {"id": "still_water", "name": "Still Water", "modifiers": [{"stat": "will", "op": "pct_add", "value": 0.02}]},
        {"id": "beast_friend", "name": "Beast Friend", "modifiers": [{"stat": "taming_chance", "op": "pct_add", "value": 0.01}]},
        {"id": "valley_champion", "name": "Valley Champion", "modifiers": [{"stat": "physical_attack", "op": "pct_add", "value": 0.01}]},
        {"id": "guos_student", "name": "Guo's Student", "modifiers": [{"stat": "fist_attack", "op": "pct_add", "value": 0.01}]},
        {"id": "big_sibling", "name": "Big Sibling", "modifiers": [{"stat": "max_hp", "op": "pct_add", "value": 0.01}]},
        {"id": "rivals_respect", "name": "Rival's Respect", "modifiers": [{"stat": "crit_chance", "op": "flat", "value": 0.01}]},
        # S49 the mortal kingdom: the county's thanks.
        {"id": "friend_of_the_county", "name": "Friend of the County", "modifiers": [{"stat": "coin_find", "op": "pct_add", "value": 0.02}]},
        {"id": "benefactor_of_stoneford", "name": "Benefactor of Stoneford", "modifiers": [{"stat": "coin_find", "op": "pct_add", "value": 0.04}]},
        # S49: sworn siblings share a title.
        {"id": "sworn_sibling", "name": "Sworn Sibling", "modifiers": [{"stat": "max_hp", "op": "pct_add", "value": 0.02}]},
        # S44 Alchemist Guild badges.
        {"id": "guild_adept", "name": "Guild Adept", "modifiers": [{"stat": "crafting_control", "op": "flat", "value": 0.02}]},
        {"id": "guild_expert", "name": "Guild Expert", "modifiers": [{"stat": "crafting_control", "op": "flat", "value": 0.04}]},
    ]
    entries("titles", T)
    # S34: six emotes from the start and more from achievements, played from the Menu wheel. `pose` is an
    # avatar action, `tilt` leans the body (radians), `bob` bounces it, `text` is the speech bubble.
    entries("emotes", [
        {"id": "bow", "name": "Bow", "pose": "idle", "tilt": 0.32, "text": "(bows)", "seconds": 1.6},
        {"id": "wave", "name": "Wave", "pose": "idle", "bob": True, "text": "Hey there!", "seconds": 1.6},
        {"id": "cheer", "name": "Cheer", "pose": "jump", "text": "Hooray!", "seconds": 1.4},
        {"id": "salute", "name": "Fist salute", "pose": "punch_1", "text": "(fist-and-palm salute)", "seconds": 1.6},
        {"id": "laugh", "name": "Laugh", "pose": "idle", "bob": True, "text": "Ha ha ha!", "seconds": 1.8},
        {"id": "meditate", "name": "Sit", "pose": "meditate", "text": "...", "seconds": 3.0},
        {"id": "champion", "name": "Champion", "pose": "punch_2", "text": "Undefeated!", "seconds": 1.8, "achievement": "valley_champion"},
        {"id": "beast_call", "name": "Beast Call", "pose": "idle", "bob": True, "text": "Awoooo!", "seconds": 1.8, "achievement": "friend_of_beasts"},
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
    # S20 weekly mission (Part 8): finish 20 daily missions or defeat a field boss; 150 contribution.
    write("weekly_mission.json", {"schema_version": 1, "name": "Sect Service", "dailies": 20, "role": "field_boss",
                                  "contribution": 150, "taels_base": 100, "taels_per_level": 10})


def sect_tables():
    B = [("sect_hall", "Sect Hall", 800, "riverstone", 20, 1), ("treasury", "Treasury", 500, "copper_ore", 20, 1),
         ("meditation_pavilion", "Meditation Pavilion", 500, "riverstone", 20, 1), ("guest_house", "Guest House", 600, "boar_hide", 10, 2),
         ("mission_hall", "Mission Hall", 600, "copper_ore", 15, 2), ("alchemy_hall", "Alchemy Hall", 900, "willow_moss", 20, 3),
         ("forge", "Forge", 900, "copper_ore", 30, 3), ("herb_terraces", "Herb Terraces", 700, "willow_moss", 15, 4),
         ("beast_pavilion", "Beast Pavilion", 700, "tough_meat", 15, 4), ("library", "Library", 1000, "talisman_paper", 10, 5),
         ("formation_array", "Formation Array", 1200, "formation_stone", 10, 6), ("ancestral_shrine", "Ancestral Shrine", 1500, "jade_core", 1, 7),
         # S18/S25 zone outpost (v1.1): a waystation in the Azure Expanse that lends every member its Storm Ward.
         ("expanse_outpost", "Expanse Outpost", 2500, "stormsteel_ore", 6, 8)]
    # What each level gives. A building damaged in a lost raid gives defence.damaged_output of it until repaired.
    OUTPUT = {"treasury": {"taels_per_level": 20},
              "meditation_pavilion": {"idle_rate_per_level": 0.1, "idle_cap_hours": [[2, 4], [4, 8], [5, 12]]},
              "guest_house": {"disciples_base": 2, "disciples_per_level": 1},
              "expanse_outpost": {"attunement_per_level": 1.0, "zone": "azure_expanse", "requires_realm": "sage_1"}}
    MAX = {"expanse_outpost": 5}
    entries("sect_buildings", [dict({"id": b, "name": n, "base_cost": c, "material": m, "material_count": k, "sect_level": lv, "max_level": MAX.get(b, 10)},
                                    **({"output": OUTPUT[b]} if b in OUTPUT else {}))
                               for b, n, c, m, k, lv in B])
    write("sect_levels.json", {"prestige_building": 20, "levels": [{"level": n, "prestige": int(round(200 * n ** 1.8))} for n in range(1, 21)]})
    entries("expeditions", beast_tide=BEAST_TIDE, rows=[
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
        # Beyond the gate: only a sect with an Expanse Outpost can send disciples this far.
        {"id": "thunderhorn_plains", "name": "Thunderhorn Plains", "hours": [4, 8], "danger_level": 9, "requires_building": "expanse_outpost",
         "rewards": [{"item": "storm_shard", "count": 6}, {"item": "thunder_horn", "count": 1}, {"coins": 400}]},
        {"id": "gale_canyons", "name": "Gale Canyons", "hours": [8], "danger_level": 11, "requires_building": "expanse_outpost",
         "rewards": [{"item": "stormsteel_ore", "count": 3}, {"item": "kite_silk", "count": 2}, {"item": "storm_shard", "count": 8}]},
        {"id": "sunscar_desert", "name": "Sunscar Desert", "hours": [8], "danger_level": 12, "requires_building": "expanse_outpost",
         "rewards": [{"item": "sunglass_ore", "count": 2}, {"item": "ember_cactus", "count": 2}, {"item": "storm_shard", "count": 8}]},
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
        "event.heavens_cleansing": "Heaven's Cleansing", "event.riverbreath_trial": "The Riverbreath Trial", "event.heart_trial": "The Heart Trial", "event.hollow_night": "The Hollow Night",
        "event.copper_body_trial": "Copper Body Trial", "event.iron_body_trial": "Iron Body Trial", "event.jade_body_trial": "Jade Body Trial",
        "event.gold_body_trial": "Gold Body Trial", "event.trial_of_reflections": "The Trial of Reflections",
        "event.siege_of_two_sects": "Siege of Two Sects", "event.sect_war": "Sect War: the Alliance Gate", "event.presence_trial": "The Presence Trial",
        "event.mine_assault": "Taking the Mine", "event.mine_defence": "Holding the Mine",
        "event.starsea_crossing": "The Starsea Crossing",
        "flag.night_survived": "Survived the night",
        "ui.begin": "Begin", "ui.continue": "Continue", "ui.new_game": "New Game", "ui.settings": "Settings", "ui.back": "Back",
        "ui.unaffiliated": "Unaffiliated", "ui.locked": "Locked",
    })
    for u in json.load(open(os.path.join(DATA, "unlocks.json")))["entries"]:
        S["unlock." + u["id"]] = u.get("label", u["id"])
    # Interface text (pages, HUD, shell, messages from the authorities), read through Tx.t(key).
    ui = json.load(open(os.path.join(os.path.dirname(__file__), "ui_strings.json")))
    for k in ui:
        assert k not in S, "ui string key clashes with a generated key: " + k
    S.update(ui)
    write("en.json", {"strings": S}, folder=os.path.join(DATA, "strings"))


def guilds():
    """S44 guilds.json: the Alchemist Guild's rank exams, commissions and shop (the Formation and Artifact guilds follow
    in S49). A zone's daily income target is Level x 60 taels an hour for three hours of play (S39's worked example:
    about 850 an hour at Level 15, 1,700 at Level 25); commissions pay at most a fifth of it a day."""
    rows = [{"id": "alchemist", "craft": "alchemy", "name": "Alchemist Guild", "hall": "sf_artisan_row", "master": "guildmaster_tang",
             "shop": "alchemist_guild",
             "ranks": [{"id": "adept", "recipe": "healing_pill", "count": 5, "quality": "fine", "time_s": 180, "title": "guild_adept",
                        "flag": "guild_alchemy_adept", "rewards": [], "pay_mult": 1.2},
                       {"id": "expert", "recipe": "foundation_guard_pill", "count": 3, "quality": "superior", "time_s": 300,
                        "title": "guild_expert", "flag": "guild_alchemy_expert", "rewards": [{"kind": "learn_recipe", "recipe": "qi_flow_pill"}],
                        "pay_mult": 1.5}],
             "commissions": {"per_day": 3, "count": [1, 3], "contribution_per_tael": 0.1, "income_per_level_hour": 60, "play_hours": 3,
                             "cap_share": 0.2}}]
    entries("guilds", rows)


def herb_conflicts():
    """S44 herb_conflicts.json: pairs that blow the furnace when they meet in one batch (a substitute or an
    experiment): a minor body injury, 10 furnace durability, and the batch is lost."""
    rows = [{"id": "ember_pepper+mist_lotus", "herbs": ["ember_pepper", "mist_lotus"],
             "text": "Ember Pepper's heat and Mist Lotus's cold fight inside the furnace."},
            {"id": "ember_pepper+cloudtop_orchid", "herbs": ["ember_pepper", "cloudtop_orchid"],
             "text": "Ember Pepper scorches Cloudtop Orchid until the furnace cracks."},
            {"id": "soulbell_flower+venom_sac", "herbs": ["venom_sac", "soulbell_flower"],
             "text": "Venom sours Soulbell Flower's clear tone into a shriek the furnace cannot hold."}]
    entries("herb_conflicts", rows)


def talismans():
    """S47 talismans.json: what each talisman does (at its own grade, not the user's stats) and the stroke path that
    is traced to write it (points in a unit square; smoothness and pace along it set the quality)."""
    circle = [[round(0.5 + 0.36 * math.cos(a * math.pi / 6), 3), round(0.5 + 0.36 * math.sin(a * math.pi / 6), 3)] for a in range(13)]
    rows = [
        {"id": "flame_talisman", "kind": "attack", "grade": "common", "power": 1.8, "element": "fire", "radius": 80, "range": 300,
         "strokes": [[0.25, 0.9], [0.4, 0.45], [0.5, 0.7], [0.6, 0.2], [0.75, 0.9]]},
        {"id": "thunder_talisman", "kind": "attack", "grade": "earth", "power": 2.4, "element": "thunder", "radius": 90, "range": 320,
         "status": {"id": "shock", "chance": 1.0, "power": 1, "duration_s": 3}, "strokes": [[0.62, 0.05], [0.35, 0.5], [0.62, 0.5], [0.38, 0.95]]},
        {"id": "iron_wall_talisman", "kind": "defence", "grade": "common", "shield_pct": 0.2, "duration_s": 6,
         "strokes": [[0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8], [0.2, 0.25]]},
        {"id": "wind_step_talisman", "kind": "movement", "grade": "common", "effect": "free_dodge", "duration_s": 60,
         "strokes": [[0.5, 0.5], [0.7, 0.42], [0.72, 0.7], [0.38, 0.78], [0.25, 0.4], [0.55, 0.15], [0.9, 0.28]]},
        {"id": "veil_talisman", "kind": "movement", "grade": "earth", "effect": "veil", "duration_s": 10,
         "strokes": [[0.08, 0.5], [0.3, 0.3], [0.5, 0.5], [0.7, 0.3], [0.92, 0.5]]},
        {"id": "binding_talisman", "kind": "sealing", "grade": "earth", "status": {"id": "root", "chance": 1.0, "power": 1, "duration_s": 2}, "range": 260,
         "strokes": [[0.2, 0.8], [0.5, 0.2], [0.8, 0.8], [0.2, 0.45], [0.8, 0.45]]},
        {"id": "revival_talisman", "kind": "revival", "grade": "common", "strokes": circle},
        {"id": "lightning_rod_talisman", "kind": "tribulation", "grade": "heaven", "strokes": [[0.5, 0.05], [0.5, 0.95], [0.28, 0.72], [0.72, 0.72]]},
    ]
    entries("talismans", rows, base_power={"plain": 40, "common": 90, "earth": 260, "heaven": 700, "mystic": 1600, "spirit": 3200, "sage": 6000},
            quality_mult={"flawed": 0.8, "common": 1.0, "fine": 1.1, "superior": 1.2, "perfect": 1.3},
            trace={"tolerance": 0.09, "break_at": 0.24, "min_s": 0.6, "max_s": 5.0})


def forge_upkeep():
    """S47 gear upkeep. Salvage returns by grade (Part 8, extended past Mystic with the zone metals); the same
    metal is what an enhancement of that grade eats. Pity, essence, Inherit and reroll costs."""
    rows = [
        {"id": "plain", "metal": "copper_ore", "returns": [{"item": "copper_ore", "count": 1}]},
        {"id": "common", "metal": "riverstone", "returns": [{"item": "riverstone", "count": 2}, {"item": "refining_essence", "count": 1}]},
        {"id": "earth", "metal": "jadeiron", "returns": [{"item": "jadeiron", "count": 2}, {"item": "refining_essence", "count": 3}]},
        {"id": "heaven", "metal": "cloudsteel_ore", "returns": [{"item": "cloudsteel_ore", "count": 2}, {"item": "refining_essence", "count": 6}]},
        {"id": "mystic", "metal": "mystic_ore", "returns": [{"item": "mystic_ore", "count": 1}, {"item": "refining_essence", "count": 10}]},
        {"id": "spirit", "metal": "stormsteel_ore", "returns": [{"item": "stormsteel_ore", "count": 2}, {"item": "refining_essence", "count": 12}]},
        {"id": "sage", "metal": "sunglass_ore", "returns": [{"item": "sunglass_ore", "count": 2}, {"item": "refining_essence", "count": 16}]},
    ]
    entries("salvage", rows)
    write("forge_upkeep.json", {
        "pity_step": 0.05,              # each failed enhancement adds 5% to the next attempt on that item
        "furnace_band_per_level": 0.01,  # S44: each enhancement level steadies a furnace's heat by 1%
        "furnace_affinity": 0.05,       # S44: a furnace of the pill's element adds 5% to the quality roll
        "beast_fire_min_rank": 2,       # S44: Beast Fire burns a core of rank 2 or more
        "nature_shift": 0.08,           # S44: each hot herb moves the Extraction band up 8% of the bar; each cold one down
        "substitute_tier": 5,           # S44: the Alchemy Dao tier that lets one herb stand in for another
        "blast_durability": 10,         # S44: a furnace blast costs the furnace 10 durability
        "deduce_per_page": 0.2, "deduce_per_tier": 0.1, "deduce_cap": 0.95,   # S44 Deduce odds
        # S44 pill tribulation: 3 bolts (+2 a grade above Heaven, at most 9), a shield window either side of each strike,
        # a 10% chance to rise a tier when every bolt is held; the Pill Soul's flight and its catch window.
        "tribulation": {"bolts": 3, "per_grade": 2, "max": 9, "first_s": 1.2, "gap_min_s": 0.7, "gap_max_s": 1.3, "window_s": 0.22,
                        "rise_chance": 0.1, "soul_min_s": 1.0, "soul_max_s": 1.6, "soul_window_s": 0.2},
        "risky_from": 5,                # attempts from +5 to +6 upward can fail
        "fail_step": 0.12,              # base chance falls 12% a level from there
        "essence_step": 0.025,          # each Refining Essence fed into an attempt adds 2.5%...
        "essence_max": 4,               # ...up to four per attempt
        "inherit_loss": 2,              # Inherit moves N - 2 levels
        "inherit_stones_per_level": 2,  # 2 Spirit Stones (Low) a level moved
        "reroll_essence": [1, 2, 3, 5, 8, 10, 12, 14, 16, 18, 20, 22, 24],   # by grade index
        "reroll_taels": 60,             # x (grade index + 1)
        "lock_mult": 2,                 # a locked affix doubles the reroll cost
    })


def build():
    shops()
    forge_upkeep()
    talismans()
    auction()
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
    for x in json.load(open(os.path.join(DATA, "auction.json")))["pool"]:
        if x["item"] not in items:
            errs.append("auction %s" % x["item"])
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
