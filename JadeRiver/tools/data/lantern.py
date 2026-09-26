"""Act III · The Lantern Star Field (v1.2, docs/act3_design.md). Every room here is in zone lantern_star_field; field rooms
ask for Starsea Endurance. world.build() calls build() after the Expanse; zone_json(), teleport_stones() and voyages() in
world.py read ZONE, STONES and VOYAGES from here.

Phase A: the Lantern Run from the Starsea Launch, Lanternfall Harbor and the Drifting Shoals.
Phase B: Blackmast Haven (Admiral Voss) and the Wyrmnest Isles (the Hollowed brood, the last star-wyrm egg).
"""

LS = {"zone": "lantern_star_field"}
# Rooms under a lit lantern (the harbour, the hulks) draw the Hollowing out four times as fast (S28, stats.hollowing).


def _w():
    import world
    return world


# Starsea routes of the Lantern Star Field (S18): the Lantern Run and its way home.
VOYAGES = [
    {"id": "lantern_run", "name": "The Lantern Run", "from": "sw_starsea_launch", "to": "lh_arrival_quay", "to_portal": "",
     "chart": "star_chart_lantern", "crossing": "ss_lantern_crossing", "base_s": 90},
    {"id": "lantern_run_home", "name": "The Lantern Run (home)", "from": "lh_arrival_quay", "to": "sw_starsea_launch", "to_portal": "",
     "chart": "star_chart_lantern", "crossing": "ss_lantern_crossing", "base_s": 90},
]

STONES = [
    {"id": "lanternfall", "name": "Lanternfall Harbor", "room": "lh_harbor_market", "at": [2100, 880], "fee_shards": 1, "zone": "lantern_star_field"},
]

# Regions in map order; the ones a later phase builds are shown as planned.
REGIONS = [
    {"id": "lanternfall_harbor", "name": "Lanternfall Harbor", "levels": [0, 0], "map": [0.80, 0.64]},
    {"id": "drifting_shoals", "name": "Drifting Shoals", "levels": [82, 87], "attunement": 20, "map": [0.64, 0.74]},
    {"id": "blackmast_haven", "name": "Blackmast Haven", "levels": [85, 90], "attunement": 30, "map": [0.46, 0.82]},
    {"id": "wyrmnest_isles", "name": "Wyrmnest Isles", "levels": [85, 93], "attunement": 40, "map": [0.70, 0.30]},
    {"id": "warden_citadel", "name": "Star Warden Citadel", "levels": [0, 0], "map": [0.50, 0.48], "planned": True},
    {"id": "orbit_ruins", "name": "Orbit Ruins", "levels": [88, 93], "attunement": 50, "map": [0.34, 0.30], "planned": True},
    {"id": "ashen_reach", "name": "Ashen Reach", "levels": [88, 96], "attunement": 60, "map": [0.22, 0.66], "planned": True},
    {"id": "tidebreak_front", "name": "Tidebreak Front", "levels": [90, 99], "attunement": 70, "map": [0.12, 0.40], "planned": True},
    {"id": "nebula_deep", "name": "Nebula Deep", "levels": [94, 99], "attunement": 80, "map": [0.30, 0.10], "planned": True},
    {"id": "lantern_heart", "name": "The Lantern Heart", "levels": [97, 99], "attunement": 90, "map": [0.52, 0.14], "planned": True},
    {"id": "lantern_crossing", "name": "The Lantern Run", "levels": [81, 83], "map": [0.94, 0.86], "hidden": True},
]


def zone(rooms):
    return {
        "id": "lantern_star_field", "tier": 3, "name": "Lantern Star Field", "level_range": [82, 99], "ceiling": "sphere_lord_3",
        "laws": ["fire", "metal", "space", "star"], "currency": {"everyday": "sage_crystal", "high": "star_jade"},
        # Loot coins are counted in taels; the Field pays them in Sage Crystals at this rate (S21).
        "coin_scale": 0.005, "qi_density": [1.5, 2.5],
        # Starsea Endurance 20 -> 90 (Part 3 zone row): four jades of fifteen levels, each level worth 1.5.
        "attunement": {"stat": "starsea_endurance", "name": "Starsea Endurance", "shard": "star_shard", "required": [20, 90],
                       "unlock": "starsea_endurance", "jade_max": 15, "jade_value": 1.5, "cost": {"base": 1, "per_level": 1},
                       "jades": [{"id": "tide", "name": "Tide Jade"}, {"id": "comet", "name": "Comet Jade"},
                                 {"id": "wick", "name": "Wick Jade"}, {"id": "void", "name": "Void Jade"}]},
        "panorama": "lantern_harbor", "start_room": "lh_arrival_quay", "rooms": rooms, "regions": REGIONS,
        "exit": {"room": "lh_arrival_quay", "to_zone": "azure_expanse"},
    }


def lantern_posts(r, xs, y=662):
    for x in xs:
        r.decor("star_lantern_post", [x, y])


def lanternfall():
    w = _w()
    # --- Lanternfall Harbor: a harbour town on a drifting island, under the biggest lantern star in the Field.
    r = w.town("lh_arrival_quay", "Arrival Quay", "lanternfall_harbor", 2, backdrop="lantern_harbor", material="wood", tint="#c9b89a",
               music="lantern_harbor", ambience="wind_ambience", spawn_point=[700, 820], qi=1.6, lantern=True, **LS)
    r.obj("dock_lantern", "starsea_dock", [260, 700], route="lantern_run_home", prop="cloud_skiff")
    r.decor("mooring_post", [120, 700])
    r.decor("mooring_post", [420, 700])
    r.decor("harbor_crane", [900, 640], layer="back")
    r.decor("lantern_cage", [1500, 650], layer="back")
    r.decor("star_buoy", [560, 720])
    r.decor("crate", [1180, 720])
    r.decor("sack_pile", [1260, 730])
    lantern_posts(r, [1000, 1900, 2350])
    r.obj("shrine_lh_quay", "shrine", [1700, 700])
    r.obj("sign_lh_quay", "signpost", [2380, 860],
          text="Lanternfall Harbor. East: the Harbor Market. Beyond the market, the Drifting Shoals. The skiffs at the pier sail home to the Starsea Launch.")
    r.npc("harbormaster_lin", [1100, 780], facing=1)
    r.npc("warden_xiao", [2050, 800], facing=-1)
    r.edge("east", "east", "lh_harbor_market", "west", y=850)

    r = w.town("lh_harbor_market", "Harbor Market", "lanternfall_harbor", 3, backdrop="lantern_harbor", material="stone", tint="#cfc2a8",
               music="lantern_harbor", spawn_point=[300, 820], qi=1.6, idle=["gather"], lantern=True, **LS)
    r.building("star_chandlery", "village_store", 620, front=690, door_dx=30,
               door=("lh_star_chandlery", "entry", "chandlery_door", {"label": "Star Chandlery"}))
    r.building("tidelight_inn", "village_house", 1480, front=690, door_dx=40,
               door=("lh_tidelight_inn", "entry", "inn_door", {"label": "Tidelight Inn"}))
    r.building("harbor_warehouse", "warehouse", 3300, front=690)
    for x, flip in ((1000, False), (2300, True), (2750, False)):
        r.decor("market_stall", [x, 780], flip=flip)
    r.decor("lantern_string", [1000, 560], layer="back")
    r.decor("lantern_string", [2500, 560], layer="back")
    lantern_posts(r, [260, 1900, 3050])
    r.decor("barrel", [3080, 740])
    r.obj("stone_lanternfall", "teleport_stone", [2100, 880], stone="lanternfall")
    r.obj("board_lh", "notice_board", [800, 700])
    r.obj("storage_lh", "storage_chest", [1220, 710], requires=w.all_of(w.unlock("storage")), locked_text="The storehouse is locked.")
    r.obj("exchange_lh", "inspect", [2000, 720], prop="counter",
          text="The harbour exchange: Spirit Stones for Sage Crystals, Sage Crystals for Star Jade, at the Wardens' rate.",
          open_page="exchange", requires=w.all_of(w.unlock("currency_exchange")), locked_text="The exchange clerk ignores you.")
    r.npc("clerk_yu", [1960, 780], facing=1)
    r.npc("peddler_ning", [1000, 830], facing=1)
    r.npc("apothecary_sang", [2300, 830], facing=-1)
    r.npc("smith_ou", [2750, 830], facing=1)
    r.obj("sign_lh_market", "signpost", [3700, 860], text="East: the Drifting Shoals (Lv 82-87, Starsea Endurance 20-28) · West: the Arrival Quay.")
    r.edge("west", "west", "lh_arrival_quay", "east", y=850)
    r.edge("east", "east", "dr_jellyfish_shallows", "west", y=850, ptype="sealed",
           requires=w.any_of(w.qactive("salt_of_the_stars"), w.qdone("salt_of_the_stars")),
           locked_text="A Star Warden at the gate: \"The Shoals thin the blood of anyone the stars don't know yet. See Warden Xiao first.\"")

    r = w.interior("lh_star_chandlery", "Star Chandlery", "lanternfall_harbor", wall="wall_wood", music="lantern_harbor", qi=1.8,
                   rtype="insight", lantern=True, **LS)
    r.decor("scroll_rack", [200, 690])
    r.decor("herb_drawers", [1100, 690])
    r.decor("star_lantern_post", [420, 700])
    r.decor("star_lantern_post", [880, 700])
    r.decor("table", [640, 760])
    r.obj("furnace_lh", "alchemy_furnace", [980, 760], requires=w.all_of(w.unlock("alchemy")), locked_text="Chandler Shu's furnace. She makes lamp oil in it, mostly.")
    r.npc("chandler_shu", [760, 760], facing=-1)
    r.portal("entry", "door", [120, 700], "lh_harbor_market", "chandlery_door", press_up=True, label="Harbor Market")

    r = w.interior("lh_tidelight_inn", "Tidelight Inn", "lanternfall_harbor", wall="wall_wood", music="lantern_harbor", qi=1.6,
                   rtype="rest", lantern=True, **LS)
    for x in (300, 700, 1000):
        r.decor("table", [x, 760])
        r.decor("cushion", [x - 50, 790])
    r.decor("wine_jar", [140, 700])
    r.decor("counter", [520, 700])
    r.decor("screen_folding", [860, 690])
    r.npc("innkeeper_fei", [520, 730], facing=1)
    r.portal("entry", "door", [120, 700], "lh_harbor_market", "inn_door", press_up=True, label="Harbor Market")


def shoals_scenery(r, glass=3, buoys=2):
    """Starlit shallows between low islets: driftglass on the rocks, buoys, a lantern cage far off."""
    w = _w()
    w.back_trees(r, ("driftglass_cluster", "rock_large", "driftglass_cluster"), step=640)
    for i in range(glass):
        x = int(r.w * (i + 0.6) / max(1, glass)) + r.rng.randint(-120, 120)
        r.decor("driftglass_cluster", [x, 900], flip=bool(i % 2))
    for i in range(buoys):
        r.decor("star_buoy", [700 + i * 1300, 930])
    r.decor("lantern_cage", [r.w - 700, 640], layer="back")


def drifting_shoals():
    w = _w()
    shoals = dict(backdrop="star_shoals", material="sand", tint="#b8b4d8", music="star_field", ambience="wind_ambience", element="star",
                  gather_tier="lantern_low", qi=1.7, loot="jar_lantern", trees=("driftglass_cluster", "rock_large"), **LS)
    r = w.field("dr_jellyfish_shallows", "Jellyfish Shallows", "drifting_shoals", 3, [82, 84],
                spawns=[("star_jellyfish", 5, [82, 84]), ("comet_sparrow", 1, [82, 83])], herbs=("star_lotus",), jars=4,
                attunement_required=20, **shoals)
    shoals_scenery(r)
    # The starlit shallows: slow wading between the islets (S43 water_shallow).
    r.area("shallows", [900, 860, 1400, 120])
    r.obj("sign_dr_shallows", "signpost", [220, 860], text="The Drifting Shoals. West: Lanternfall Harbor · East: the Moored Hulks.")
    r.edge("west", "west", "lh_harbor_market", "east", y=850)
    r.edge("east", "east", "dr_moored_hulks", "west", y=850)

    r = w.Room("dr_moored_hulks", "Moored Hulks", "rest", "drifting_shoals", 2, backdrop="star_shoals", material="wood", tint="#b8a58a",
               music="star_field", ambience="wind_ambience", element="star", qi=1.8, spawn_point=[400, 820], idle=["gather"], lantern=True, **LS)
    r.decor("moored_hulk", [900, 640], layer="back")
    r.decor("moored_hulk", [1900, 650], layer="back", flip=True)
    r.decor("star_buoy", [1400, 930])
    r.decor("barrel", [1200, 720])
    r.decor("crate", [1280, 730])
    r.decor("cooking_pot", [1650, 800])
    lantern_posts(r, [700, 2100])
    r.obj("shrine_dr_hulks", "shrine", [1000, 700])
    r.npc("hulk_keeper_bo", [1560, 780], facing=-1)
    for i, x in enumerate([1080, 1240]):
        r.obj("bed_dr_%d" % i, "garden_bed", [x, 900], field_grade="high", requires=w.all_of(w.unlock("herb_garden")),
              locked_text="Old Bo's planters, lashed to the deck. Beds are for those who keep a garden.")
    r.edge("west", "west", "dr_jellyfish_shallows", "east", y=850)
    r.edge("east", "east", "dr_sparrow_reefs", "west", y=850)

    r = w.field("dr_sparrow_reefs", "Sparrow Reefs", "drifting_shoals", 3, [84, 86],
                spawns=[("comet_sparrow", 4, [84, 86], 14), ("star_jellyfish", 2, [84, 85])], jars=4, attunement_required=24,
                platforms=[(1000, 660, 280, 110), (2200, 650, 300, 160)], ledge="rock_ledge", **shoals)
    shoals_scenery(r, glass=2, buoys=1)
    r.edge("west", "west", "dr_moored_hulks", "east", y=850)
    r.edge("east", "east", "dr_driftglass_bank", "west", y=850)

    r = w.field("dr_driftglass_bank", "Driftglass Bank", "drifting_shoals", 3, [85, 87],
                spawns=[("star_jellyfish", 3, [85, 87]), ("comet_sparrow", 3, [85, 87], 14)], ores=("driftglass", "driftglass"), herbs=("star_lotus",),
                jars=5, chest="chest_lantern", attunement_required=28, **shoals)
    shoals_scenery(r, glass=5, buoys=1)
    r.obj("insight_star", "insight_stone", [1900, 720], element="metal", requires=w.all_of(w.unlock("insight_sites")),
          locked_text="A lens of driftglass the tides have set upright. The stars in it do not match the sky.")
    r.edge("west", "west", "dr_sparrow_reefs", "east", y=850)
    r.edge("east", "east", "bm_blackmast_docks", "west", y=850, ptype="sealed",
           requires=w.any_of(w.qactive("the_pursers_ledger"), w.qdone("the_pursers_ledger")),
           locked_text="Beyond the bank the lanes run to Blackmast Haven. The Wardens send nobody there without a reason.")
    # The Moored Hulks keep a sky-skiff for the Wyrmnest Isles, once the tamer there has asked for you.
    hulks = ROOMS()["dr_moored_hulks"]
    hulks.decor("sky_ship", [2200, 640], layer="back", flip=True)
    hulks.portal("wyrm_skiff", "door", [2250, 704], "wn_nest_cliffs", "skiff", press_up=True, label="Skiff to the Wyrmnest Isles",
                 requires=w.any_of(w.qdone("the_admiral"), w.qactive("star_tier_beasts"), w.qdone("star_tier_beasts")),
                 locked_text="Old Bo: \"The nest islands? Not while the pirates hold the lanes. Deal with the Admiral first.\"")


def ROOMS():
    return _w().ROOMS


def blackmast():
    """Phase B · Blackmast Haven: a pirate harbour in the dark between islands (Starsea Endurance 30-36)."""
    w = _w()
    haven = dict(backdrop="blackmast_haven", material="wood", tint="#b8a58a", music="star_field", ambience="wind_ambience", element="metal",
                 gather_tier="lantern_mid", qi=1.8, loot="jar_lantern", trees=("barrel", "crate", "sack_pile"), front=("barrel",), **LS)
    r = w.field("bm_blackmast_docks", "Blackmast Docks", "blackmast_haven", 3, [85, 87],
                spawns=[("starsea_pirate", 4, [85, 87]), ("pirate_gunner", 2, [85, 86], 14)], jars=4, attunement_required=30,
                spawn_point=[420, 820], **haven)
    r.obj("shrine_bm_docks", "shrine", [700, 700])
    r.decor("moored_hulk", [1600, 640], layer="back")
    for x in (400, 1300, 2900):
        r.decor("pirate_banner", [x, 662])
    r.decor("powder_keg", [2100, 730])
    r.decor("pirate_cannon", [2500, 720], flip=True)
    r.npc("deckhand_mo", [1000, 800], facing=1, visible_if=w.any_of(w.qactive("the_pursers_ledger"), w.qdone("the_pursers_ledger")))
    r.obj("sign_bm", "signpost", [560, 860], text="Blackmast Haven. East: the Gunners' Battery, and past it the Admiral's flagship.")
    r.edge("west", "west", "dr_driftglass_bank", "east", y=850)
    r.edge("east", "east", "bm_gunners_battery", "west", y=850)

    r = w.field("bm_gunners_battery", "Gunners' Battery", "blackmast_haven", 3, [87, 89],
                spawns=[("pirate_gunner", 4, [87, 89], 14), ("starsea_pirate", 2, [87, 88])], jars=4, attunement_required=33,
                platforms=[(900, 650, 300, 100), (2100, 640, 300, 176)], ledge="deck", **haven)
    # Three cannons to spike (chapter 18): each one silenced stays silent.
    for i, x in enumerate((700, 1700, 2900)):
        r.obj("cannon_%d" % i, "inspect", [x, 720], prop="pirate_cannon", set_flag="cannon_spiked_%d" % i,
              text="You drive a spike of comet iron into the touch-hole. This one will not fire again.",
              visible_if=w.all_of(w.qactive("gunners_battery")), hidden_if=w.all_of(w.flag("cannon_spiked_%d" % i)))
    r.decor("powder_keg", [1300, 730])
    r.decor("powder_keg", [2400, 730])
    r.portal("cove", "hidden", [2600, 700], "bm_smugglers_cove", "entry", press_up=True, label="Smugglers' Cove")
    r.edge("west", "west", "bm_blackmast_docks", "east", y=850)
    r.edge("east", "east", "bm_flagship_deck", "west", y=850, ptype="sealed",
           requires=w.any_of(w.qactive("the_admiral"), w.qdone("the_admiral")),
           locked_text="The gangway to the flagship is drawn up. Silence the battery first.")

    r = w.Room("bm_smugglers_cove", "Smugglers' Cove", "secret", "blackmast_haven", 2, backdrop="blackmast_haven", material="wood",
               tint="#a89878", music="dungeon", levels=[88, 90], safe=False, qi=1.9, spawn_point=[260, 820], attunement_required=34, **LS)
    r.spawn("starsea_pirate", r.points(2), 2, respawn=60, level=[88, 90])
    for x in (700, 1500):
        r.decor("crate", [x, 720])
        r.decor("sack_pile", [x + 80, 730])
    r.decor("powder_keg", [1100, 730])
    r.chest([2000, 900], loot="chest_lantern", level=89)
    r.npc("gu_the_purser", [1700, 780], facing=-1, visible_if=w.all_of(w.qactive("gunners_battery")))
    r.portal("entry", "door", [140, 700], "bm_gunners_battery", "cove", press_up=True, label="Gunners' Battery")

    r = w.Room("bm_flagship_deck", "Flagship Deck", "boss_arena", "blackmast_haven", 2, backdrop="blackmast_haven", material="wood",
               tint="#b8a58a", music="boss", levels=[90, 90], safe=False, spawn_point=[220, 820], dungeon_exit="bm_gunners_battery",
               attunement_required=36, **LS)
    r.decor("broken_mast", [1300, 690])
    r.decor("pirate_banner", [700, 662])
    r.decor("pirate_banner", [2100, 662], flip=True)
    r.decor("pirate_cannon", [2300, 720], flip=True)
    r.spawn("admiral_voss", [[1700, 840]], 1, respawn=86400, level=[90, 90], boss=True)
    r.chest([2300, 900], loot="chest_lantern", level=90, requires=w.all_of(w.qdone("the_admiral")),
            locked_text="The Admiral's strongbox. Not while he stands on his deck.")
    r.edge("west", "west", "bm_gunners_battery", "east", y=850)


def wyrmnest():
    """Phase B · the Wyrmnest Isles: cliff islands of star-wyrm nests, guarded, and grey with a Hollowed brood (Endurance 40-48)."""
    w = _w()
    isles = dict(backdrop="wyrmnest_isles", material="stone", tint="#d8d0c0", music="star_field", ambience="wind_ambience", element="earth",
                 gather_tier="lantern_mid", qi=1.9, loot="jar_lantern", trees=("star_crystal", "rock_large"), ledge="rock_ledge", **LS)
    r = w.field("wn_nest_cliffs", "Nest Cliffs", "wyrmnest_isles", 3, [85, 88],
                spawns=[("comet_sparrow", 3, [85, 87], 14), ("nest_guardian", 2, [86, 88], 20)], herbs=("star_lotus",), jars=4,
                attunement_required=40, platforms=[(1100, 650, 300, 110), (2300, 640, 320, 200)], spawn_point=[400, 820], **isles)
    r.decor("wyrm_nest", [1250, 640], layer="back")
    r.decor("star_crystal", [1800, 700])
    r.decor("sky_ship", [400, 640], layer="back")
    r.obj("shrine_wn_cliffs", "shrine", [800, 700])
    r.npc("tamer_qiu", [560, 800], facing=1)
    r.portal("skiff", "door", [260, 704], "dr_moored_hulks", "wyrm_skiff", press_up=True, label="Skiff to the Moored Hulks")
    r.edge("east", "east", "wn_eggshell_terraces", "west", y=850)

    r = w.field("wn_eggshell_terraces", "Eggshell Terraces", "wyrmnest_isles", 3, [88, 91],
                spawns=[("hollowed_wyrmling", 5, [88, 91], 14), ("nest_guardian", 1, [89, 90], 20)], jars=4, attunement_required=44,
                hazards=["hollow_puddle"], **isles)
    r.decor("wyrm_nest", [900, 650], layer="back")
    r.decor("wyrm_nest", [2500, 650], layer="back", flip=True)
    for i, x in enumerate((700, 1500, 2300)):
        r.area("hollow_puddle", [x - 90, 880, 180, 60])
    r.edge("west", "west", "wn_nest_cliffs", "east", y=850)
    r.edge("east", "east", "wn_guardians_crown", "west", y=850)

    r = w.field("wn_guardians_crown", "Guardian's Crown", "wyrmnest_isles", 3, [90, 93],
                spawns=[("nest_guardian", 3, [90, 93], 20), ("hollowed_wyrmling", 2, [90, 92], 14)], herbs=("star_lotus", "star_lotus"),
                jars=5, chest="chest_lantern", attunement_required=48, platforms=[(1400, 640, 360, 200)], **isles)
    r.decor("star_crystal", [900, 700])
    r.decor("star_crystal", [2600, 700])
    r.decor("wyrm_nest", [1580, 440], layer="back")
    r.edge("west", "west", "wn_eggshell_terraces", "east", y=850)
    r.portal("cave", "door", [3500, 704], "wn_hatching_cave", "entry", press_up=True, label="Hatching Cave",
             requires=w.any_of(w.qactive("the_last_egg"), w.qdone("the_last_egg")),
             locked_text="A warm draught breathes out of the cave. The guardians do not let strangers in.")

    r = w.Room("wn_hatching_cave", "Hatching Cave", "dungeon", "wyrmnest_isles", 2, backdrop="cave", material="stone", tint="#c8b8a0",
               music="dungeon", levels=[92, 93], safe=False, qi=2.2, spawn_point=[220, 820], attunement_required=48, element="earth", **LS)
    r.spawn("nest_guardian", [[1500, 840]], 1, respawn=600, level=[93, 93], elite=True)
    r.decor("wyrm_nest", [1800, 660], layer="back")
    r.decor("star_crystal", [900, 700])
    r.decor("star_crystal", [2200, 700])
    r.obj("last_egg", "pickup", [1850, 880], item="wyrm_egg", count=1, prop="wyrm_egg", set_flag="wyrm_egg_taken",
          visible_if=w.all_of(w.qactive("the_last_egg")), hidden_if=w.all_of(w.flag("wyrm_egg_taken")))
    r.portal("entry", "door", [140, 700], "wn_guardians_crown", "cave", press_up=True, label="Guardian's Crown")


def crossing():
    """The Lantern Run's deck under the open Starsea (instanced): the voyage lasts as long as the vessel takes to cross."""
    w = _w()
    r = w.Room("ss_lantern_crossing", "The Lantern Run", "story", "lantern_crossing", 3, backdrop="starsea", material="wood", tint="#b8a58a",
               music="starsea", ambience="wind_ambience", instanced=True, safe=False, crossing=True, levels=[81, 83],
               spawn_point=[900, 820], hazards=["star_wind"], no_flight=True, dungeon_exit="",
               event={"id": "starsea_crossing", "duration": 90,
                      "waves": [{"enemy": "comet_sparrow", "every_s": 11, "max": 2, "first_s": 8, "points": [[3300, 780], [3500, 820]], "level": 82},
                                {"enemy": "star_jellyfish", "every_s": 16, "max": 2, "first_s": 20, "points": [[2800, 760], [3200, 800]], "level": 82}],
                      "on_complete": [{"kind": "voyage_arrive"}]}, **LS)
    r.decor("sky_ship", [3300, 600], layer="back", flip=True)
    r.decor("broken_mast", [1500, 690])
    r.decor("lantern_cage", [2600, 640], layer="back")
    for x in (600, 2400):
        r.decor("crate", [x, 720])
    r.decor("rope", [1200, 690])
    r.decor("barrel", [2000, 720])


def build():
    lanternfall()
    drifting_shoals()
    blackmast()
    wyrmnest()
    crossing()
