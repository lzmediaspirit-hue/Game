"""E1 room specs (R6): Cloudgate Port, the Alliance's sky harbour on a floating island, Act II's door into the Azure
Expanse (docs/architecture/room_engine.md, "Act II's first zones (R6)"). Paved terraces and streets under the island's
crags, plank wharves along its south rim where the airships berth, hanging past the room's edge over the sea of cloud
(topdown_life.VISTAS draws it under the rim); the port's look is the `sky_port` biome. Chapter 11 begins here."""
from content.rooms.spec import room

CRAGS = dict(level=5, paint="r", wall=True, wavy=True)   # the island's crown of rock behind the port
# A lawn in the paving: flowering shrubs and hedges, no tree (a canopy would hang over the walk north of it).
LAWN = dict(kinds=["bush_azalea", "bush", "hedge_2", "rock_small"], density=0.5)


# The Arrival Terrace: where the Ascension Gate sets a valley cultivator down. The gate's archway stands on a granite
# dais against the crags, banners either side, a flight down between two stone lions to the promenade; the toll warden
# waits at its foot. The paved terrace runs east to the market and west to the docks, lanterns along its north edge,
# plum lawns in it; past the rim lawns a lookout juts over the clouds.
AE_LANDING = room(
    "ae_landing", size=(56, 28), biome="sky_port",
    bands=[("upper", 3, 7, dict(level=1, paint="g", wavy=True)),
           ("crags", 0, 4, CRAGS),
           ("terrace", 10, 13, dict(level=0, paint="p")),
           ("road", 14, 3, dict(paint="s", walk=True)),
           ("rim", 23, 5, dict(level=0, paint="g", wavy=True))],
    features=[("dais", (3, 3, 9, 6), dict(level=2, paint="s")),
              ("lawn_w", (15, 18, 12, 5), dict(paint="g", shape="round")),
              ("lawn_e", (36, 18, 12, 5), dict(paint="g", shape="round")),
              ("lookout", (24, 22, 8, 6), dict(paint="s"))],
    stairs=[(6, 9, 3, 4, 0, 2)],
    ways={"gate": dict(at=(7, 3), dir="n", arrive=(7, 5), span=3), "east": ("e", "road"), "west": ("w", "road")},
    spawn="gate",
    anchors={"npc_warden_cao": "road.n@12", "shrine_ae_landing": "verge.n@28", "npc_alliance_guard": "verge.s@37",
             "npc_wanderer_jiang": "verge.n@46", "sign_ae_landing": "road.n@52"},
    props=[("paifang", 5, 3), ("banner_cloud", 4, 4), ("banner_cloud", 10, 4), ("stone_lion", 5, 11),
           ("stone_lion", 9, 11), ("lantern", 22, 10), ("lantern", 33, 10), ("lantern", 44, 10), ("lantern", 24, 26),
           ("lantern", 31, 26)],
    flora={"rim": dict(kinds=["tree_plum", "tree_pine", "bush_azalea", "bush", "rock_mossy"], density=0.45),
           "upper": dict(density=0.5), "terrace": [], "lawn_w": LAWN, "lawn_e": LAWN})

# The Port Market: the town's street of dressed stone east from the Arrival Terrace. North of it, under the crags, the
# Alliance factors' hall, the Wayfarers' Inn (its door the way in), a teahouse and the port's two warehouses, the
# hawkers' stalls between them and the notice board, the storehouse and the exchange counter; south of it the square
# round the Cloudgate teleport stone between two flower lawns, and the rim, where a sky sailor waits by an airship at
# the lookout pier. At the street's east end the town gate (the gate guard's, sealed till Storm in the Blood) opens on
# the Thunderhorn Plains.
AE_PORT_MARKET = room(
    "ae_port_market", size=(72, 28), biome="sky_port",
    bands=[("upper", 3, 3, dict(level=1, paint="g", wavy=True)),
           ("crags", 0, 4, CRAGS),
           ("yard", 6, 5, dict(level=0, paint="p")),
           ("street", 11, 4, dict(paint="s", walk=True)),
           ("square", 15, 7, dict(level=0, paint="p")),
           ("rim", 22, 6, dict(level=0, paint="g", wavy=True))],
    features=[("garden_w", (7, 16, 15, 5), dict(paint="g", shape="round")),
              ("garden_e", (43, 16, 15, 5), dict(paint="g", shape="round")),
              ("gate_n", (66, 4, 6, 7), dict(level=3, paint="l")),
              ("gate_s", (66, 15, 6, 6), dict(level=3, paint="l")),
              ("pier", (61, 20, 6, 8), dict(paint="w"))],
    ways={"west": ("w", "street"), "east": ("e", "street"),
          "inn_door": ("door", "inn", dict(path=(11, "s")))},
    spawn="west",
    anchors={"npc_factor_ruan": (13, 10), "board_ae": "yard@15", "storage_ae": "yard@22",
             "npc_peddler_gou": (18, 8), "stone_cloudgate": "square@35", "exchange_ae": "yard@37",
             "npc_smith_hong": (40, 8), "npc_apothecary_wu": (51, 8), "npc_sky_sailor_pei": "pier@64",
             "sign_ae_market": "street.n@62"},
    props=[("storehouse", 9, 7, "factors_hall"), ("house", 24, 7, "inn"), ("house", 43, 7),
           ("storehouse", 54, 7), ("storehouse", 59, 7),
           ("market_stall", 17, 9), ("market_stall", 39, 9), ("market_stall", 50, 9),
           ("banner_cloud", 5, 9), ("banner_cloud", 64, 9), ("banner_cloud", 64, 15),
           ("lantern_red", 14, 10), ("lantern_red", 31, 10), ("lantern_red", 49, 10), ("lantern_red", 31, 15),
           ("lantern_red", 41, 15), ("sacks", 58, 10), ("barrel", 63, 10), ("crates", 53, 10),
           ("sky_ship", 57, 27)],
    flora={"rim": dict(kinds=["tree_plum", "tree_pine", "bush_azalea", "bush", "rock_mossy"], density=0.45),
           "upper": dict(density=0.5), "yard": [], "square": [], "garden_w": LAWN, "garden_e": LAWN})

# The Wayfarers' Inn: a planked common room. The innkeeper's counter against the back wall, wine jars and a cabinet
# behind it, a painted screen; three tea tables with their cushions, the free broker at the far one; the door in the
# south wall back to the Port Market.
AE_WAYFARERS_INN = room(
    "ae_wayfarers_inn", size=(24, 14), base="w", walls=dict(high=4),
    ways={"entry": ("s", 4.5)},
    spawn="entry",
    anchors={"npc_innkeeper_tang": (9.5, 2), "npc_broker_mu": (19, 9)},
    props=[("counter", 8, 3), ("water_jar", 6, 1), ("water_jar", 7, 1), ("cabinet", 11, 1), ("screen", 15, 1),
           ("lantern_red", 1, 1), ("lantern_red", 22, 1), ("tea_table", 4, 7), ("mat", 4, 8), ("tea_table", 12, 7),
           ("mat", 12, 8), ("tea_table", 18, 7), ("mat", 18, 8), ("water_jar", 1, 11), ("sacks", 22, 11),
           ("pot_bonsai", 22, 5), ("lantern_red", 1, 6)])


# The Condensing Hall: the Alliance's hall for breakthroughs off the Skydock, a granite floor under tall walls.
# Alchemist Fen's furnace on its dais at the back, her drawers of herbs and the scroll shelves beside it, banners of
# the Alliance, the incense burner and two meditation mats on the floor; the door to the Skydock in the south wall.
AE_CONDENSING_HALL = room(
    "ae_condensing_hall", size=(24, 14), base="s", walls=dict(high=4),
    features=[("dais", (14, 1, 8, 4), dict(level=1, paint="p")),           # the furnace's dais
              ("cheek", (16, 5, 1, 2), dict(level=2, paint="p")),          # its steps' cheeks, a level over the dais
              ("cheek_2", (19, 5, 1, 2), dict(level=2, paint="p"))],
    stairs=[(17, 5, 2, 2, 0, 1)],
    ways={"entry": ("s", 4.5)},
    spawn="entry",
    anchors={"furnace_ae": (18, 3), "npc_alchemist_fen": (13, 6)},
    props=[("apothecary", 20, 1), ("apothecary", 14, 1), ("scroll_shelf", 2, 1), ("scroll_shelf", 4, 1),
           ("banner_cloud", 8, 1), ("banner_cloud", 11, 1), ("lantern", 14, 4), ("lantern", 21, 4), ("incense", 9, 7),
           ("mat", 6, 9), ("mat", 11, 9), ("lantern", 1, 12), ("lantern", 22, 12), ("pot_orchid", 1, 5),
           ("water_jar", 22, 8)])


# The Skydock: the island's south rim where the airships berth. Under the crags the Condensing Hall (its door the way
# in); the quay of planks east to the Arrival Terrace and west to the Shipwrights' Yard; the wharf below it, the
# dockmaster's cargo stacked on it, and two piers out to the rim where the lake ferry and the Nine Peaks ship hang
# over the clouds, their gangways the ways aboard, mooring posts beside them.
AE_SKYDOCK = room(
    "ae_skydock", size=(56, 28), biome="sky_port",
    bands=[("upper", 3, 4, dict(level=1, paint="g", wavy=True)),
           ("crags", 0, 4, CRAGS),
           ("yard", 7, 6, dict(level=0, paint="p")),
           ("quay", 13, 3, dict(paint="w", walk=True)),
           ("wharf", 16, 5, dict(level=0, paint="w")),
           ("rim", 21, 7, dict(level=0, paint="r", wavy=True))],
    features=[("pier_w", (13, 20, 5, 8), dict(paint="w")), ("pier_e", (35, 20, 5, 8), dict(paint="w"))],
    ways={"east": ("e", "quay"), "west": ("w", "quay"),
          "hall_door": ("door", "condensing", dict(path=(13, "s"))),
          "lake_ferry": dict(at=(15, 27), dir="s", arrive=(15, 25), span=2),
          "peaks_ferry": dict(at=(37, 27), dir="s", arrive=(37, 25), span=2)},
    spawn="east",
    anchors={"npc_sky_sailor_ning": "pier_w@14", "npc_dockmaster_fu": "wharf@25"},
    props=[("hall", 41, 7, "condensing"), ("storehouse", 4, 8), ("storehouse", 20, 8), ("lantern", 40, 9), ("lantern", 49, 9), ("banner_cloud", 8, 10),
           ("banner_cloud", 30, 10), ("crates", 26, 17), ("sacks", 28, 17), ("crates", 21, 19), ("barrel", 23, 19),
           ("sacks", 46, 18), ("barrel", 47, 18), ("post", 12, 26), ("post", 18, 26), ("post", 34, 26),
           ("post", 40, 26), ("sky_ship", 10, 27), ("sky_ship", 32, 27)],
    flora={"rim": dict(kinds=["rock_mossy", "bush", "rock_small", "bush_azalea"], density=0.4), "upper": dict(density=0.5),
           "yard": [], "wharf": []})


# The Shipwrights' Yard: the island's west end, where the port's ships are built and the Starsea skiffs put out. The
# skiff pier at the west rim, Shipwright Lao's slipway down to the edge with a hull fitting out at its foot, timber
# and rope by it; east of it the navigators' terrace, raised a step, with Navigator Sun's chart table, the armillary
# sphere and the star-sighting stone; the quay east to the Skydock.
AE_SHIPYARD = room(
    "ae_shipyard", size=(56, 28), biome="sky_port",
    bands=[("upper", 3, 4, dict(level=1, paint="g", wavy=True)),
           ("crags", 0, 4, CRAGS),
           ("yard", 7, 6, dict(level=0, paint="p")),
           ("quay", 13, 3, dict(paint="w", walk=True)),
           ("rim", 16, 12, dict(level=0, paint="r", wavy=True))],
    features=[("skiff_pier", (3, 15, 6, 13), dict(paint="w")), ("slip", (17, 15, 11, 13), dict(paint="w")),
              ("terrace", (35, 17, 16, 6), dict(level=0, paint="s"))],
    ways={"east": ("e", "quay")},
    spawn="east",
    anchors={"dock_cloudgate": (5, 24), "slip_cloudgate": "slip@22", "npc_shipwright_lao": "slip@26",
             "npc_navigator_sun": "quay.s@33", "chart_table_cloudgate": "terrace@38", "sight_cloudgate": "terrace@48"},
    props=[("post", 2, 26), ("post", 9, 26), ("sky_ship", 17, 27), ("woodpile", 29, 17), ("woodpile", 29, 19),
           ("crates", 14, 17), ("sacks", 14, 18), ("armillary", 43, 18), ("lantern", 35, 17), ("lantern", 50, 17),
           ("banner_cloud", 10, 10), ("lantern_red", 30, 12), ("crates", 46, 11)],
    flora={"rim": dict(kinds=["tree_pine", "rock_mossy", "bush", "rock_small"], density=0.4), "upper": dict(density=0.5),
           "yard": []})

ROOMS = [AE_LANDING, AE_PORT_MARKET, AE_WAYFARERS_INN, AE_SKYDOCK, AE_CONDENSING_HALL, AE_SHIPYARD]
