"""Act III · The Lantern Star Field (v1.2, docs/act3_design.md). Every room here is in zone lantern_star_field; field rooms
ask for Starsea Endurance. world.build() calls build() after the Expanse; zone_json(), teleport_stones() and voyages() in
world.py read ZONE, STONES and VOYAGES from here.

Phase A: the Lantern Run from the Starsea Launch, Lanternfall Harbor and the Drifting Shoals.
"""

LS = {"zone": "lantern_star_field"}


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
    {"id": "blackmast_haven", "name": "Blackmast Haven", "levels": [85, 90], "attunement": 30, "map": [0.46, 0.82], "planned": True},
    {"id": "wyrmnest_isles", "name": "Wyrmnest Isles", "levels": [85, 93], "attunement": 40, "map": [0.70, 0.30], "planned": True},
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
               music="lantern_harbor", ambience="wind_ambience", spawn_point=[700, 820], qi=1.6, **LS)
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
               music="lantern_harbor", spawn_point=[300, 820], qi=1.6, idle=["gather"], **LS)
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
                   rtype="insight", **LS)
    r.decor("scroll_rack", [200, 690])
    r.decor("herb_drawers", [1100, 690])
    r.decor("star_lantern_post", [420, 700])
    r.decor("star_lantern_post", [880, 700])
    r.decor("table", [640, 760])
    r.obj("furnace_lh", "alchemy_furnace", [980, 760], requires=w.all_of(w.unlock("alchemy")), locked_text="Chandler Shu's furnace. She makes lamp oil in it, mostly.")
    r.npc("chandler_shu", [760, 760], facing=-1)
    r.portal("entry", "door", [120, 700], "lh_harbor_market", "chandlery_door", press_up=True, label="Harbor Market")

    r = w.interior("lh_tidelight_inn", "Tidelight Inn", "lanternfall_harbor", wall="wall_wood", music="lantern_harbor", qi=1.6,
                   rtype="rest", **LS)
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
               music="star_field", ambience="wind_ambience", element="star", qi=1.8, spawn_point=[400, 820], idle=["gather"], **LS)
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
    crossing()
