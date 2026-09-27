"""Act III · The Lantern Star Field (v1.2, docs/act3_design.md). Every room here is in zone lantern_star_field; field rooms
ask for Starsea Endurance. world.build() calls build() after the Expanse; zone_json(), teleport_stones() and voyages() in
world.py read ZONE, STONES and VOYAGES from here.

Phase A: the Lantern Run from the Starsea Launch, Lanternfall Harbor and the Drifting Shoals.
Phase B: Blackmast Haven (Admiral Voss) and the Wyrmnest Isles (the Hollowed brood, the last star-wyrm egg).
Phase D: the Ashen Reach (General Kharn) and the Tidebreak Front (the Hollow Tide battle).
Phase E: the Nebula Deep (the Leviathan) and the Lantern Heart (the first lantern's flame).
Phase C: the Star Warden Citadel (the Wardens, the Observatory, the Presence Court) and the Orbit Ruins (gravity switches,
Gravity Golems and Orbit Moths, the Orbit Hermit who teaches the Space Dao).
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
    {"id": "star_citadel", "name": "Star Warden Citadel", "room": "wc_citadel_gate", "at": [2900, 880], "fee_shards": 1, "zone": "lantern_star_field"},
]

# Regions in map order; the ones a later phase builds are shown as planned.
REGIONS = [
    {"id": "lanternfall_harbor", "name": "Lanternfall Harbor", "levels": [0, 0], "map": [0.80, 0.64]},
    {"id": "drifting_shoals", "name": "Drifting Shoals", "levels": [82, 87], "attunement": 20, "map": [0.64, 0.74]},
    {"id": "blackmast_haven", "name": "Blackmast Haven", "levels": [85, 90], "attunement": 30, "map": [0.46, 0.82]},
    {"id": "wyrmnest_isles", "name": "Wyrmnest Isles", "levels": [85, 93], "attunement": 40, "map": [0.70, 0.30]},
    {"id": "warden_citadel", "name": "Star Warden Citadel", "levels": [0, 0], "map": [0.50, 0.48]},
    {"id": "orbit_ruins", "name": "Orbit Ruins", "levels": [88, 93], "attunement": 50, "map": [0.34, 0.30]},
    {"id": "ashen_reach", "name": "Ashen Reach", "levels": [88, 96], "attunement": 60, "map": [0.22, 0.66]},
    {"id": "tidebreak_front", "name": "Tidebreak Front", "levels": [90, 99], "attunement": 70, "map": [0.12, 0.40]},
    {"id": "nebula_deep", "name": "Nebula Deep", "levels": [94, 99], "attunement": 80, "map": [0.30, 0.10]},
    {"id": "lantern_heart", "name": "The Lantern Heart", "levels": [97, 99], "attunement": 90, "map": [0.52, 0.14]},
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
    # v1.2 · Phase C: the Wardens' skiff to their Citadel (chapter 20).
    r.portal("warden_skiff", "door", [2230, 704], "wc_citadel_gate", "skiff", press_up=True, label="Warden skiff to the Citadel",
             requires=w.any_of(w.qactive("the_citadel"), w.qdone("the_citadel")),
             locked_text="The Wardens' skiff. It carries Wardens, and those the Wardens have asked for.")
    r.npc("warden_xiao", [2050, 800], facing=-1)
    r.edge("east", "east", "lh_harbor_market", "west", y=850)

    r = w.town("lh_harbor_market", "Harbor Market", "lanternfall_harbor", 3, backdrop="lantern_harbor", material="stone", tint="#cfc2a8",
               music="lantern_harbor", spawn_point=[300, 820], qi=1.6, idle=["gather"], lantern=True, **LS)
    r.building("star_chandlery", "village_store", 620, front=690,
               door=("lh_star_chandlery", "entry", "chandlery_door", {"label": "Star Chandlery"}))
    r.building("tidelight_inn", "village_house", 1480, front=690,
               door=("lh_tidelight_inn", "entry", "inn_door", {"label": "Tidelight Inn"}))
    r.building("harbor_warehouse", "warehouse", 3300, front=690)
    for x, flip in ((1000, False), (2300, True), (2750, False)):
        r.decor("market_stall", [x, 780], flip=flip)
    r.decor("lantern_string", [1000, 560], layer="back")
    r.decor("lantern_string", [2500, 560], layer="back")
    lantern_posts(r, [260, 1900, 3050])
    r.decor("barrel", [3080, 740])
    r.obj("stone_lanternfall", "teleport_stone", [2100, 880], stone="lanternfall")
    r.obj("board_lh", "notice_board", [820, 700])
    r.obj("storage_lh", "storage_chest", [1220, 710], requires=w.all_of(w.unlock("storage")), locked_text="The storehouse is locked.")
    r.obj("exchange_lh", "inspect", [2000, 720], prop="counter",
          text="The harbour exchange: Spirit Stones for Sage Crystals, Sage Crystals for Star Jade, at the Wardens' rate.",
          open_page="exchange", requires=w.all_of(w.unlock("currency_exchange")), locked_text="The exchange clerk ignores you.")
    r.npc("clerk_yu", [1860, 800], facing=1)
    r.npc("peddler_ning", [1000, 830], facing=1)
    r.npc("apothecary_sang", [2300, 830], facing=-1)
    r.npc("smith_ou", [2750, 830], facing=1)
    r.obj("sign_lh_market", "signpost", [3660, 870], text="East: the Drifting Shoals (Lv 82-87, Starsea Endurance 20-28) · West: the Arrival Quay.")
    r.edge("west", "west", "lh_arrival_quay", "east", y=850)
    r.edge("east", "east", "dr_jellyfish_shallows", "west", y=850, ptype="sealed",
           requires=w.any_of(w.qactive("salt_of_the_stars"), w.qdone("salt_of_the_stars")),
           locked_text="A Star Warden at the gate: \"The Shoals thin the blood of anyone the stars don't know yet. See Warden Xiao first.\"")
    # v1.2 · Phase E: the stair to the Lantern Heart, where Lu's notes point (chapter 22).
    r.portal("lantern_stair", "door", [3600, 704], "lt_wick_gate", "stair", press_up=True, label="The stair to the Lantern Heart",
             requires=w.all_of(w.any_of(w.qactive("lus_lantern"), w.qdone("lus_lantern")), {"kind": "flag_set", "flag": "lus_notes_found"}),
             locked_text="A stair climbing into the light of the great lantern. It is not for anyone who does not know the way.")

    r = w.interior("lh_star_chandlery", "Star Chandlery", "lanternfall_harbor", wall="wall_wood", music="lantern_harbor", qi=1.8,
                   rtype="insight", lantern=True, **LS)
    r.decor("scroll_rack", [200, 690])
    r.decor("herb_drawers", [1100, 690])
    r.decor("star_lantern_post", [420, 700])
    r.decor("star_lantern_post", [880, 700])
    r.decor("table", [640, 760])
    r.obj("furnace_lh", "alchemy_furnace", [980, 760], requires=w.all_of(w.unlock("alchemy")), locked_text="Chandler Shu's furnace. She makes lamp oil in it, mostly.")
    r.npc("chandler_shu", [760, 760], facing=-1)
    r.npc("lanternwright_han", [420, 760], facing=1)   # v1.2 · Phase C: the Confucian path
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
    r.obj("insight_star", "insight_stone", [1760, 740], element="metal", requires=w.all_of(w.unlock("insight_sites")),
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


def citadel():
    """Phase C · the Star Warden Citadel: the Wardens' fortress-town on the Field's central island (safe)."""
    w = _w()
    base = dict(backdrop="warden_citadel", material="stone", tint="#d8d4c8", music="lantern_harbor", ambience="wind_ambience", qi=2.0,
                lantern=True, **LS)
    r = w.town("wc_citadel_gate", "Citadel Gate", "warden_citadel", 3, spawn_point=[600, 820], **base)
    r.decor("warden_statue", [300, 650], layer="back")
    r.decor("warden_statue", [3500, 650], layer="back", flip=True)
    r.decor("paifang_gate", [900, 660], layer="back")
    lantern_posts(r, [1150, 2050, 3150])
    r.decor("star_ballista", [3300, 700], flip=True)
    r.decor("lantern_cage", [2500, 640], layer="back")
    r.building("wardens_hall", "village_house", 1440, front=690,
               door=("wc_wardens_hall", "entry", "hall_door", {"label": "Wardens' Hall"}))
    r.decor("pagoda", [2400, 690], layer="back")
    r.portal("observatory_door", "door", [2400, 704], "wc_observatory", "entry", press_up=True, label="Observatory")
    r.portal("skiff", "door", [560, 704], "lh_arrival_quay", "warden_skiff", press_up=True, label="Skiff to Lanternfall Harbor")
    # v1.2 · Phase D: the Wardens' skiffs to the fronts (chapter 21).
    r.portal("ash_skiff", "door", [1680, 704], "ar_cinder_fields", "skiff", press_up=True, label="Warden skiff to the Ashen Reach",
             requires=w.any_of(w.qactive("cinder_fields"), w.qdone("cinder_fields")),
             locked_text="The skiff to the Ashen Reach. It sails with orders, and you have none yet.")
    r.portal("tide_skiff", "door", [1790, 704], "tf_tidebreak_bastion", "skiff", press_up=True, label="Warden skiff to the Tidebreak Bastion",
             requires=w.any_of(w.qactive("the_tide_breaks"), w.qdone("the_tide_breaks")),
             locked_text="The skiff to the Tidebreak Bastion. The Commander has not sent you to the wall. Yet.")
    r.obj("shrine_wc_gate", "shrine", [1900, 700])
    r.obj("stone_star_citadel", "teleport_stone", [2900, 880], stone="star_citadel")
    r.obj("sign_wc", "signpost", [760, 860],
          text="The Star Warden Citadel. West: the Presence Court. East, past the Warden line: the Orbit Ruins (Lv 88-93, Starsea Endurance 50-56).")
    r.edge("west", "west", "wc_presence_court", "east", y=850)
    r.edge("east", "east", "or_tumbling_stair", "west", y=850, ptype="sealed",
           requires=w.any_of(w.qactive("the_orbit_ruins"), w.qdone("the_orbit_ruins")),
           locked_text="A Warden bars the way: \"The Ruins turn under your feet. The Commander sends people there, not the other way round.\"")

    r = w.interior("wc_wardens_hall", "Wardens' Hall", "warden_citadel", wall="wall_stone", floor="floor_stone", music="lantern_harbor", qi=2.1,
                   lantern=True, **LS)
    r.decor("warden_statue", [260, 650], layer="back")
    r.decor("star_chart_table", [700, 760])
    r.decor("scroll_rack", [1060, 690])
    r.npc("warden_commander_yao", [860, 760], facing=-1)
    r.portal("entry", "door", [120, 700], "wc_citadel_gate", "hall_door", press_up=True, label="Citadel Gate")

    r = w.interior("wc_observatory", "Observatory", "warden_citadel", wall="wall_stone", floor="floor_stone", music="lantern_harbor", qi=2.4,
                   rtype="insight", lantern=True, **LS)
    r.decor("star_chart_table", [420, 760])
    r.decor("scroll_rack", [1100, 690])
    # The great scope (chapter 20): a Presence of level 5 looking into it sees the shape of its own Sphere.
    r.obj("great_scope", "inspect", [800, 740], prop="observatory_scope", set_flag="observed_sphere",
          text="You put your eye to the bronze and your Will to the stars. Among them, very small, turns a world that is shaped like you.",
          visible_if=w.all_of(w.qactive("the_observatory")), hidden_if=w.all_of(w.flag("observed_sphere")))
    r.decor("observatory_scope", [800, 740], hidden_if=w.all_of(w.qactive("the_observatory")))
    r.npc("stargazer_ming", [560, 760], facing=1)
    r.portal("entry", "door", [120, 700], "wc_citadel_gate", "observatory_door", press_up=True, label="Citadel Gate")

    r = w.town("wc_presence_court", "Presence Court", "warden_citadel", 2, spawn_point=[2200, 820], **base)
    for x in (700, 1300, 1900):
        r.decor("pressure_pillar", [x, 660], layer="back")
    r.decor("warden_statue", [300, 650], layer="back")
    lantern_posts(r, [1000, 1600])
    r.npc("shen_lian_warden", [1300, 800], facing=1, visible_if=w.any_of(w.qactive("the_aspirant"), w.qdone("the_aspirant")))
    r.npc("presence_master_ruo", [900, 780], facing=1)
    r.obj("sign_wc_court", "signpost", [2300, 860], text="The Presence Court. Wardens spar here with their Presence held, and their Spheres, once they have them.")
    r.edge("east", "east", "wc_citadel_gate", "west", y=850)


def orbit_scenery(r, stones=3):
    for i in range(stones):
        r.decor("orbit_stone", [500 + i * int((r.w - 1000) / max(1, stones - 1)), 640 - 40 * (i % 2)], layer="back")


def orbit_ruins():
    """Phase C · the Orbit Ruins: an observatory-temple of the first Wardens, broken and turning in the dark (Endurance 50-56).
    Jade switches lighten the gravity of their halls (low_gravity volumes, 0.45 of the fall)."""
    w = _w()
    ruins = dict(backdrop="orbit_ruins", material="stone", tint="#c8c4d8", music="star_field", ambience="wind_ambience", element="star",
                 gather_tier="lantern_mid", qi=2.0, loot="jar_lantern", trees=("orbit_stone", "star_crystal"), ledge="rock_ledge", **LS)
    r = w.field("or_tumbling_stair", "Tumbling Stair", "orbit_ruins", 3, [88, 90],
                spawns=[("orbit_moth", 3, [88, 89], 14), ("gravity_golem", 1, [88, 90], 20)], jars=4, attunement_required=50,
                platforms=[(900, 650, 300, 110), (2000, 640, 320, 200), (3000, 650, 280, 110)], spawn_point=[400, 820], **ruins)
    orbit_scenery(r, 3)
    r.obj("shrine_or_stair", "shrine", [700, 700])
    # A switch at the foot of the stair lightens the whole middle of the room.
    r.obj("switch_stair", "gravity_switch", [1500, 700])
    r.volume("low_gravity", [1300, 620, 1400, 340], alt=[-10, 700], switch="switch_stair", gravity=0.45, vid="lowg_stair")
    r.edge("west", "west", "wc_citadel_gate", "east", y=850)
    r.edge("east", "east", "or_orbit_garden", "west", y=850)

    r = w.field("or_orbit_garden", "Orbit Garden", "orbit_ruins", 3, [89, 91],
                spawns=[("orbit_moth", 4, [89, 91], 14)], herbs=("star_lotus", "star_lotus"), jars=4, attunement_required=52,
                platforms=[(1100, 650, 300, 110), (2400, 640, 320, 200)], **ruins)
    orbit_scenery(r, 4)
    r.npc("orbit_hermit", [1700, 790], facing=-1)
    r.obj("switch_garden", "gravity_switch", [3060, 720])
    r.volume("low_gravity", [2600, 620, 900, 340], alt=[-10, 700], switch="switch_garden", gravity=0.45, vid="lowg_garden")
    r.edge("west", "west", "or_tumbling_stair", "east", y=850)
    r.edge("east", "east", "or_golem_foundry", "west", y=850)

    r = w.field("or_golem_foundry", "Golem Foundry", "orbit_ruins", 3, [90, 92],
                spawns=[("gravity_golem", 3, [90, 92], 20), ("orbit_moth", 2, [90, 91], 14)], ores=("driftglass", "driftglass"), jars=4,
                chest="chest_lantern", attunement_required=54, platforms=[(900, 650, 300, 110), (2100, 640, 320, 200)], **ruins)
    orbit_scenery(r, 3)
    r.decor("flame_basin", [1600, 700])
    r.edge("west", "west", "or_orbit_garden", "east", y=850)
    r.portal("hall", "door", [3500, 704], "or_inverted_hall", "entry", press_up=True, label="Inverted Hall",
             requires=w.any_of(w.qactive("the_orbit_ruins"), w.qdone("the_orbit_ruins")),
             locked_text="A doorway that opens onto the ceiling of the room beyond. You would rather have a reason to go in.")

    # The Inverted Hall: no flying here (the stars hold the air still). Its high gallery (400) is out of reach of any
    # jump (a double jump tops out near 300); with the eastern switch down the air is light enough to carry one there.
    r = w.Room("or_inverted_hall", "Inverted Hall", "dungeon", "orbit_ruins", 2, backdrop="orbit_ruins", material="stone", tint="#b8b4d0",
               music="dungeon", levels=[92, 93], safe=False, qi=2.3, spawn_point=[220, 820], attunement_required=56, element="star",
               no_flight=True, **LS)
    r.spawn("gravity_golem", [[1500, 840]], 1, respawn=300, level=[93, 93], elite=True)
    r.spawn("orbit_moth", r.points(2), 2, respawn=40, level=[92, 93])
    orbit_scenery(r, 3)
    r.obj("switch_hall_a", "gravity_switch", [700, 700])
    r.obj("switch_hall_b", "gravity_switch", [2000, 700])
    r.volume("low_gravity", [400, 620, 900, 340], alt=[-10, 800], switch="switch_hall_a", gravity=0.45, vid="lowg_hall_a")
    r.volume("low_gravity", [1300, 620, 1000, 340], alt=[-10, 800], switch="switch_hall_b", gravity=0.45, vid="lowg_hall_b")
    r.surface("gallery_low", [900, 650, 320, 60], 100, kind="rock_ledge")
    r.surface("gallery_high", [1500, 630, 360, 60], 400, kind="rock_ledge", optional=True)
    r.chest([1680, 660], loot="chest_lantern", level=93, alt=400, surface="gallery_high", oid="chest_gallery")
    r.portal("entry", "door", [140, 700], "or_golem_foundry", "hall", press_up=True, label="Golem Foundry")


def ashen_reach():
    """Phase D · the Ashen Reach: cinder plains where the Ashborn legions of Ash Queen Seralet camp under General Kharn
    (Endurance 60-66). Reached by the Wardens' second skiff from the Citadel Gate."""
    w = _w()
    ash = dict(backdrop="ashen_reach", material="stone", tint="#c4a894", music="ashen_war", ambience="wind_ambience", element="fire",
               gather_tier="lantern_high", qi=2.1, loot="jar_lantern", trees=("rock_large", "ash_pyre"), ledge="rock_ledge", **LS)
    r = w.field("ar_cinder_fields", "Cinder Fields", "ashen_reach", 3, [88, 91],
                spawns=[("ashborn_raider", 4, [88, 90], 16), ("hollow_drone", 1, [88, 90], 20)], ores=("driftglass",), jars=4,
                attunement_required=60, platforms=[(1000, 650, 300, 100), (2200, 640, 320, 200)], spawn_point=[400, 820], **ash)
    r.decor("cinder_tent", [2800, 660], layer="back")
    r.decor("ashborn_banner", [2500, 662])
    r.decor("ash_pyre", [1700, 700])
    r.portal("skiff", "door", [260, 704], "wc_citadel_gate", "ash_skiff", press_up=True, label="Warden skiff to the Citadel")
    r.obj("shrine_ar_fields", "shrine", [620, 700])
    r.npc("warden_hu_jin", [820, 790], facing=1)
    r.edge("east", "east", "ar_ashborn_palisade", "west", y=850)

    r = w.field("ar_ashborn_palisade", "Ashborn Palisade", "ashen_reach", 3, [90, 93],
                spawns=[("ashborn_raider", 4, [90, 92], 16), ("ashborn_pyre_keeper", 1, [91, 93], 40)], jars=4, attunement_required=62,
                platforms=[(900, 650, 300, 100), (2100, 640, 320, 200), (3000, 650, 280, 100)], **ash)
    r.decor("stockade_wall", [1500, 660], layer="back")
    r.decor("ashborn_banner", [1200, 662])
    r.decor("ashborn_banner", [2700, 662])
    r.edge("west", "west", "ar_cinder_fields", "east", y=850)
    r.edge("east", "east", "ar_war_camp", "west", y=850)

    r = w.field("ar_war_camp", "War Camp", "ashen_reach", 3, [91, 94],
                spawns=[("ashborn_raider", 3, [91, 93], 16), ("ashborn_pyre_keeper", 1, [92, 94], 40)], jars=4, chest="chest_lantern",
                attunement_required=64, platforms=[(1100, 650, 300, 100), (2300, 640, 320, 200)], **ash)
    for x in (700, 1900, 3000):
        r.decor("cinder_tent", [x, 660], layer="back")
    r.decor("ash_pyre", [2500, 700])
    r.obj("shrine_ar_camp", "shrine", [400, 700])
    r.npc("ashborn_envoy_veyla", [1500, 790], facing=-1)
    r.edge("west", "west", "ar_ashborn_palisade", "east", y=850)
    r.edge("east", "east", "ar_kharns_pyre", "west", y=850, ptype="sealed",
           requires=w.any_of(w.qactive("kharns_pyre"), w.qdone("kharns_pyre")),
           locked_text="Ashborn guards cross their glaives: \"The General receives no one. Not yet.\"")

    # Kharn's Pyre: the General's own fire, where the Ashborn burn their dead. He fights here, and kneels here.
    r = w.Room("ar_kharns_pyre", "Kharn's Pyre", "boss_arena", "ashen_reach", 2, backdrop="ashen_reach", material="stone", tint="#b89480",
               music="boss", levels=[92, 92], safe=False, qi=2.3, spawn_point=[260, 820], dungeon_exit="ar_war_camp", attunement_required=66,
               element="fire", **LS)
    r.spawn("general_kharn", [[1500, 840]], 1, respawn=86400, level=[92, 92], boss=True)
    r.decor("ash_pyre", [1800, 700], layer="back")
    r.decor("ashborn_banner", [900, 662])
    r.decor("ashborn_banner", [2200, 662])
    r.edge("west", "west", "ar_war_camp", "east", y=850)


def tidebreak():
    """Phase D · the Tidebreak Front: the Wardens' last fortress against the Hollow Tide, and the grey beyond it
    (Endurance 70-76). Reached by the Wardens' third skiff from the Citadel Gate."""
    w = _w()
    r = w.town("tf_tidebreak_bastion", "Tidebreak Bastion", "tidebreak_front", 3, backdrop="tidebreak_front", material="stone", tint="#c0c4cc",
               music="hollow_tide", ambience="wind_ambience", spawn_point=[400, 820], qi=2.1, lantern=True, attunement_required=70, **LS)
    r.decor("bastion_wall", [1900, 650], layer="back")
    r.decor("lantern_cage", [1300, 640], layer="back")
    lantern_posts(r, [800, 1700, 2600])
    r.portal("skiff", "door", [240, 704], "wc_citadel_gate", "tide_skiff", press_up=True, label="Warden skiff to the Citadel")
    r.obj("shrine_tf_bastion", "shrine", [560, 700])
    r.obj("tide_horn", "rite_circle", [2200, 880], event="hollow_tide_battle", prop="small_bell",
          visible_if=w.any_of(w.qactive("the_tide_breaks"), w.qdone("the_tide_breaks")),
          text="The Bastion's great bell. Ring it and the Wardens take the wall: the Tide comes, and the lantern must not go out.")
    r.npc("warden_captain_duan", [1500, 790], facing=-1)
    r.npc("quartermaster_bai", [1000, 790], facing=1)
    r.npc("tinker_mei", [2800, 790], facing=-1)
    r.edge("east", "east", "tf_greyfall_breach", "west", y=850)

    grey = dict(backdrop="tidebreak_front", material="stone", tint="#a8acb4", music="hollow_tide", ambience="wind_ambience", element="none",
                gather_tier="lantern_high", qi=2.2, loot="jar_lantern", trees=("rock_large", "drone_hive"), ledge="rock_ledge", **LS)
    r = w.field("tf_greyfall_breach", "Greyfall Breach", "tidebreak_front", 3, [90, 94],
                spawns=[("hollow_drone", 4, [90, 93], 14), ("hollowed_wyrmling", 2, [91, 94], 20)], jars=4, attunement_required=72,
                platforms=[(1000, 650, 300, 100), (2200, 640, 320, 200)], **grey)
    # Chapter 22: Shen Lian holds the Breach; the Greyfall stand is fought here.
    r.npc("shen_lian_breach", [1700, 790], facing=1, visible_if=w.all_of(w.qactive("greyfall"), {"kind": "flag_not_set", "flag": "shen_lian_taken"}))
    r.obj("greyfall_stand", "rite_circle", [1500, 880], event="greyfall_stand", prop="small_bell",
          visible_if=w.all_of(w.qactive("greyfall"), {"kind": "flag_not_set", "flag": "shen_lian_taken"}),
          text="The Breach's warning bell. Ring it and the Tide comes all at once.")
    r.edge("west", "west", "tf_tidebreak_bastion", "east", y=850)
    r.edge("east", "east", "tf_hollow_wake", "west", y=850)

    r = w.field("tf_hollow_wake", "Hollow Wake", "tidebreak_front", 3, [93, 97],
                spawns=[("hollow_drone", 5, [93, 96], 14), ("hollowed_wyrmling", 2, [94, 97], 20)], jars=4, attunement_required=74,
                platforms=[(900, 650, 300, 100), (2000, 640, 320, 200), (3000, 650, 280, 100)], **grey)
    r.edge("west", "west", "tf_greyfall_breach", "east", y=850)
    r.edge("east", "east", "tf_drone_hive", "west", y=850)

    r = w.field("tf_drone_hive", "Drone Hive", "tidebreak_front", 3, [95, 99],
                spawns=[("hollow_drone", 6, [95, 99], 12)], jars=4, chest="chest_lantern", attunement_required=76,
                platforms=[(1100, 650, 300, 100), (2300, 640, 320, 200)], **grey)
    for x in (900, 1900, 2900):
        r.decor("drone_hive", [x, 690], layer="back")
    r.edge("west", "west", "tf_hollow_wake", "east", y=850)
    r.edge("east", "east", "nd_nebula_verge", "west", y=850, ptype="sealed",
           requires=w.any_of(w.qactive("lus_lantern"), w.qdone("lus_lantern")),
           locked_text="Beyond the hive the dark thins into a nebula that runs like a sea. You have no reason to swim it yet.")

    # The Tide battle (instanced): waves of drones and wyrmlings from both sides; the great lantern must stay lit.
    r = w.Room("si_tide_battle", "The Tide Breaks", "story", "tidebreak_front", 3, backdrop="tidebreak_front", material="stone", tint="#b8bcc4",
               music="hollow_tide", instanced=True, safe=False, spawn_point=[1900, 820], levels=[92, 94], dungeon_exit="", no_flight=True,
               event={"id": "hollow_tide_battle", "duration": 150,
                      "lantern": {"object": "great_lantern", "light": 100, "drain_per_foe": 3.0, "drain_radius": 180, "relight": 4.0,
                                  "relight_radius": 120},
                      "waves": [{"enemy": "hollow_drone", "every_s": 5, "max": 4, "points": [[300, 800], [3500, 800]], "level": 92},
                                {"enemy": "hollowed_wyrmling", "every_s": 11, "max": 2, "first_s": 20, "points": [[400, 880], [3400, 880]], "level": 93}],
                      "on_complete": [{"kind": "event_passed", "event": "hollow_tide_battle"}, {"kind": "grant_item", "item": "star_shard", "count": 12},
                                      {"kind": "grant_item", "item": "drone_shell", "count": 3}],
                      "on_timeout": []}, **LS)
    r.decor("bastion_wall", [1900, 650], layer="back")
    r.obj("great_lantern", "inspect", [1900, 760], prop="lantern_cage",
          text="The Bastion's great lantern. While it burns, the Tide cannot cross the wall.")
    r.portal("exit", "door", [140, 700], "tf_tidebreak_bastion", "skiff", press_up=True, label="Leave")


def nebula_deep():
    """Phase E · the Nebula Deep: the drowned sky past the Drone Hive, where the nebula runs like a sea (Endurance 80-84).
    The Nebula Leviathan swims in its Maw."""
    w = _w()
    neb = dict(backdrop="nebula_deep", material="stone", tint="#b8b0d8", music="star_field", ambience="wind_ambience", element="water",
               gather_tier="lantern_high", qi=2.4, loot="jar_lantern", trees=("nebula_coral", "star_crystal"), ledge="rock_ledge", **LS)
    r = w.field("nd_nebula_verge", "Nebula Verge", "nebula_deep", 3, [94, 96],
                spawns=[("nebula_eel", 3, [94, 95], 14), ("void_crab", 2, [94, 96], 18)], herbs=("star_lotus",), jars=4, attunement_required=80,
                platforms=[(1000, 650, 300, 100), (2200, 640, 320, 200)], spawn_point=[400, 820], **neb)
    for x in (800, 1900, 3000):
        r.decor("nebula_coral", [x, 690], layer="back")
    r.obj("shrine_nd_verge", "shrine", [600, 700])
    r.edge("west", "west", "tf_drone_hive", "east", y=850)
    r.edge("east", "east", "nd_eel_currents", "west", y=850)

    r = w.field("nd_eel_currents", "Eel Currents", "nebula_deep", 3, [95, 97],
                spawns=[("nebula_eel", 5, [95, 97], 14)], jars=4, attunement_required=82,
                platforms=[(900, 650, 300, 100), (2100, 640, 320, 200), (3000, 650, 280, 100)], **neb)
    r.edge("west", "west", "nd_nebula_verge", "east", y=850)
    r.edge("east", "east", "nd_crab_grottoes", "west", y=850)

    r = w.field("nd_crab_grottoes", "Crab Grottoes", "nebula_deep", 3, [96, 98],
                spawns=[("void_crab", 4, [96, 98], 18), ("nebula_eel", 1, [96, 97], 20)], ores=("driftglass",), jars=4, chest="chest_lantern",
                attunement_required=84, platforms=[(1100, 650, 300, 100), (2300, 640, 320, 200)], **neb)
    # Lu's star notes, wedged in a crab-shell where he left them (chapter 22).
    r.obj("lus_star_notes", "inspect", [2600, 740], prop="scroll_rack", set_flag="lus_notes_found",
          visible_if=w.any_of(w.qactive("lus_lantern"), w.qdone("lus_lantern")),
          text="A bundle of star notes in Lu's hand, wrapped in oilcloth: 'The lanterns were all lit from one. Follow the stair above the harbour.'")
    r.edge("west", "west", "nd_eel_currents", "east", y=850)
    r.edge("east", "east", "nd_leviathans_maw", "west", y=850)

    # The Maw: the Leviathan's hunting ground (a field boss, back every 45 minutes).
    r = w.Room("nd_leviathans_maw", "Leviathan's Maw", "field", "nebula_deep", 3, backdrop="nebula_deep", material="stone", tint="#a8a0cc",
               music="boss", levels=[97, 99], safe=False, qi=2.5, spawn_point=[300, 820], attunement_required=84, element="water",
               no_flight=True, **LS)
    r.spawn("nebula_leviathan", [[2200, 800]], 1, respawn=2700, level=[99, 99], field_boss=True, boss=True)
    r.decor("nebula_coral", [1200, 690], layer="back")
    r.decor("nebula_coral", [3200, 690], layer="back")
    r.edge("west", "west", "nd_crab_grottoes", "east", y=850)


def lantern_heart():
    """Phase E · the Lantern Heart: the secret realm above Lanternfall Harbor, where the first lantern still burns
    (Endurance 90). Reached by the stair Lu's notes point to."""
    w = _w()
    heart = dict(backdrop="lantern_heart", material="stone", tint="#e0c8a0", music="lantern_heart", ambience="wind_ambience", element="fire",
                 gather_tier="lantern_high", qi=2.6, loot="jar_lantern", trees=("wick_pillar", "star_crystal"), ledge="rock_ledge",
                 rtype="secret", **LS)
    r = w.field("lt_wick_gate", "Wick Gate", "lantern_heart", 2, [97, 98],
                spawns=[("hollow_drone", 3, [97, 98], 14), ("hollowed_wyrmling", 2, [97, 98], 20)], jars=3, attunement_required=90,
                platforms=[(900, 650, 300, 100), (1800, 640, 320, 200)], spawn_point=[300, 820], **heart)
    r.decor("wick_pillar", [600, 660], layer="back")
    r.decor("wick_pillar", [2200, 660], layer="back")
    r.portal("stair", "door", [180, 704], "lh_harbor_market", "lantern_stair", press_up=True, label="Harbor Market")
    r.obj("shrine_lt_gate", "shrine", [420, 700])
    r.edge("east", "east", "lt_hall_of_burning_stars", "west", y=850)

    r = w.field("lt_hall_of_burning_stars", "Hall of Burning Stars", "lantern_heart", 3, [98, 99],
                spawns=[("hollow_drone", 4, [98, 99], 14), ("hollowed_wyrmling", 2, [98, 99], 20)], jars=3, chest="chest_lantern",
                attunement_required=90, platforms=[(1000, 650, 300, 100), (2200, 640, 320, 200), (3000, 650, 280, 100)], **heart)
    for x in (700, 1700, 2700):
        r.decor("wick_pillar", [x, 660], layer="back")
    r.decor("flame_basin", [1400, 700])
    r.edge("west", "west", "lt_wick_gate", "east", y=850)
    r.edge("east", "east", "lt_flame_heart", "west", y=850)

    # The Flame Heart: the cage of the first lantern. Safe; the flame answers one who carries Lu's notes.
    r = w.Room("lt_flame_heart", "Flame Heart", "secret", "lantern_heart", 2, backdrop="lantern_heart", material="stone", tint="#f0d8a8",
               music="lantern_heart", levels=[0, 0], safe=True, qi=3.0, spawn_point=[300, 820], attunement_required=90, lantern=True, **LS)
    r.decor("lantern_cage", [1280, 640], layer="back")
    r.decor("flame_basin", [900, 700])
    r.decor("flame_basin", [1660, 700])
    r.obj("heart_flame", "inspect", [1280, 760], prop="flame_basin", set_flag="heart_flame_taken",
          visible_if=w.any_of(w.qactive("lus_lantern"), w.qdone("lus_lantern")),
          text="The first lantern's flame. A spark of it leans toward you, the way it must once have leaned toward Lu.")
    r.edge("west", "west", "lt_hall_of_burning_stars", "east", y=850)


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
    citadel()
    ashen_reach()
    tidebreak()
    nebula_deep()
    lantern_heart()
    orbit_ruins()
    crossing()
