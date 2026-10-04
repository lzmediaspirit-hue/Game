"""E1 room specs (R8): Lanternfall Harbor, the harbour town on a floating island under the Field's great lantern star,
where the Lantern Run makes port (docs/architecture/room_engine.md). Chapter 17's The Lantern Run and Crystal and Jade
(the Arrival Quay, the Harbor Market's exchange), and the town's insides: the Star Chandlery and the Tidelight Inn.
Boardwalks run along the quays; piers stand out into the harbour's starlit water, the town's paved yards and its
tiled roofs behind them under the island's hill; star lanterns line the waterfront, the town's red lanterns the street."""
from content.rooms.spec import room
from content.rooms.specs.story import flights, stair_with_cheeks

# The Arrival Quay: where the skiffs of the Lantern Run come in. A boardwalk quay along the harbour, the paved yard behind
# it under the hill with the harbour office and a warehouse, the shrine in a little garden; the quay's front over the
# water where the harbourmaster keeps his eye on the moorings. The Starsea pier at the west, the dock at its end; the
# crane on its jetty in the middle; the Wardens' pier at the east, their skiff to the Citadel at its tip. East along the
# quay, the Harbor Market.
LH_ARRIVAL_QUAY = room(
    "lh_arrival_quay", size=(48, 28), biome="lantern_harbor", level=1,
    bands=[("hill", 0, 3, dict(level=4, paint="r", wall=True, wavy="s")),
           ("yard", 3, 7, dict(level=1, paint="p")),
           ("quay", 10, 3, dict(paint="w", walk=True)),
           ("front", 13, 3, dict(level=1, paint="p")),
           ("harbour", 16, 12, dict(water=True))],
    features=[("pier", (3, 15, 5, 13), dict(level=1, paint="w")),                  # the Starsea pier
              ("jetty", (18, 15, 7, 4), dict(level=1, paint="w")),                 # the crane's jetty
              ("pier_2", (39, 15, 5, 13), dict(level=1, paint="w")),               # the Wardens' pier
              ("garden", (30, 3, 9, 5), dict(paint="g", shape="round"))],
    ways={"east": ("e", "quay"), "warden_skiff": ("s", 41)},
    spawn=(13, 11),
    anchors={"dock_lantern": "pier.front@5", "npc_harbormaster_lin": "front@22", "shrine_lh_quay": "garden@34",
             "npc_warden_xiao": "front@38", "sign_lh_quay": "front@45"},
    props=[("storehouse", 3, 4), ("house", 10, 4), ("harbor_crane", 19, 16), ("crates", 22, 14), ("sacks", 24, 14),
           ("barrel", 25, 14), ("crates", 15, 8), ("sacks", 17, 8), ("lantern_red", 9, 9), ("lantern_red", 18, 9),
           ("lantern_red", 27, 9), ("lantern_red", 40, 9), ("star_lantern", 8, 15), ("star_lantern", 2, 15),
           ("star_lantern", 38, 15), ("star_lantern", 44, 15), ("post", 3, 27), ("post", 7, 27), ("post", 39, 27),
           ("post", 43, 27), ("boat", 9, 22), ("boat", 32, 24), ("pot_bonsai", 28, 4), ("pot_orchid", 46, 4)],
    flora={"garden": {"kinds": ["tree_plum", "bush_azalea", "bush", "tall_grass"], "density": 0.9},
           "harbour": {"kinds": ["lotus_pads", "cattails"], "density": 0.25}, "yard": dict(density=0.0)},
    foes="auto")


# The Harbor Market: the town's street of boards between its yards and the waterfront. North of the street, under the
# hill, the Star Chandlery and the Tidelight Inn with their doors, the warehouse at the east end, and between them the
# stalls: Peddler Ning's silks, Apothecary Sang's jars, Smith Ou at his forge; the notice board, the storehouse chest and
# the exchange counter, where Clerk Yu changes Spirit Stones for Sage Crystals. South of it the waterfront: the teleport
# stone among star lanterns, the harbour beyond. The stair to the Lantern Heart climbs into the hill at the east end; the
# street goes on east to the Drifting Shoals and west to the Arrival Quay.
LH_HARBOR_MARKET = room(
    "lh_harbor_market", size=(64, 28), biome="lantern_harbor", level=1,
    bands=[("hill", 0, 3, dict(level=4, paint="r", wall=True, wavy="s")),
           ("yard", 3, 8, dict(level=1, paint="p")),
           ("street", 11, 3, dict(paint="w", walk=True)),
           ("front", 14, 5, dict(level=1, paint="p")),
           ("harbour", 19, 9, dict(water=True))],
    features=[("stair_head", (57, 3, 7, 4), dict(level=2, paint="s")),             # the stair's landing in the hill
              ("jetty", (24, 18, 6, 6), dict(level=1, paint="w")),
              ("jetty_2", (46, 18, 5, 5), dict(level=1, paint="w"))],
    stairs="auto",
    ways={"west": ("w", "street"), "east": ("e", "street"), "chandlery_door": ("door", "chandlery", dict(path=(11, "p"))),
          "inn_door": ("door", "inn", dict(path=(11, "p"))), "lantern_stair": ("n", 60, dict(cut=3))},
    spawn="west",
    anchors={"board_lh": "yard@6", "npc_peddler_ning": "street.n@20", "storage_lh": "yard@30",
             "exchange_lh": "street.n2@34", "npc_clerk_yu": "street.n@32", "npc_apothecary_sang": "street.n@41",
             "npc_smith_ou": "street.n@49", "stone_lanternfall": "front@36", "sign_lh_market": "front@61"},
    props=[("house", 9, 5, "chandlery"), ("hall", 21, 5, "inn"), ("storehouse", 52, 5),
           ("lantern_stall", 15, 9), ("lantern_stall", 37, 9), ("forge", 45, 9), ("weapon_rack", 50, 9),
           ("lantern_red", 8, 10), ("lantern_red", 19, 10), ("lantern_red", 30, 10), ("lantern_red", 44, 10),
           ("lantern_red", 56, 10), ("star_lantern", 4, 18), ("star_lantern", 14, 18), ("star_lantern", 33, 18),
           ("star_lantern", 40, 18), ("star_lantern", 55, 18), ("barrel", 56, 8), ("barrel", 57, 9), ("crates", 47, 6),
           ("sacks", 3, 8), ("water_jar", 18, 6), ("pot_bonsai", 15, 6), ("pot_orchid", 32, 4), ("pot_bonsai", 35, 6),
           ("boat", 31, 22), ("boat", 52, 21), ("post", 24, 23), ("post", 29, 23), ("post", 46, 22), ("post", 50, 22)],
    flora={"harbour": {"kinds": ["lotus_pads", "cattails"], "density": 0.25}, "yard": dict(density=0.0),
           "front": dict(density=0.0), "stair_head": dict(density=0.0)},
    foes="auto")


# The Star Chandlery: Chandler Shu's shop of lamp oil and star lanterns, boards underfoot. Her shelves of scrolls and
# drawers of wicks and oils along the back wall, her work table under two star lanterns, the furnace she makes her oil
# in at the east; Lanternwright Han at his own bench in the west, and the ancestral altar by the door.
LH_STAR_CHANDLERY = room(
    "lh_star_chandlery", size=(24, 14), base="w", walls=dict(high=4),
    ways={"entry": ("s", 3.5)},
    spawn="entry",
    anchors={"furnace_lh": (18.5, 5), "npc_chandler_shu": (14, 7), "npc_lanternwright_han": (8, 7),
             "ancestral_altar": (5, 10)},
    props=[("scroll_shelf", 1, 1), ("scroll_shelf", 3, 1), ("apothecary", 11, 1), ("apothecary", 13, 1),
           ("cabinet", 21, 1), ("star_lantern", 9, 2), ("star_lantern", 16, 2), ("desk", 11, 5), ("desk", 6, 4),
           ("water_jar", 21, 6), ("sacks", 22, 9), ("sacks", 22, 10), ("lantern_red", 1, 12), ("lantern_red", 22, 12),
           ("pot_orchid", 7, 1), ("herb_baskets", 17, 9), ("mortar", 19, 9)])


# The Tidelight Inn: a common room of boards, three tea tables with their cushions, Innkeeper Fei behind her counter
# by the wine jars, a folding screen before the kitchen's stove; a flight up to the gallery along the north wall where
# the guests' beds stand behind screens, the side view's loft.
_INN = flights(stair_with_cheeks(19, 4, 2, 0, 2))
LH_TIDELIGHT_INN = room(
    "lh_tidelight_inn", size=(24, 14), base="w", walls=dict(high=4),
    features=[("gallery", (8, 1, 15, 3), dict(level=2, paint="w"))] + _INN[0],
    stairs=_INN[1],
    ways={"entry": ("s", 3.5)},
    spawn="entry",
    anchors={"npc_innkeeper_fei": (9, 6)},
    props=[("desk", 8, 5), ("desk", 10, 5), ("water_jar", 13, 5), ("water_jar", 14, 5), ("stove", 1, 1), ("screen", 1, 3),
           ("cabinet", 4, 1), ("tea_table", 5, 9), ("mat", 5, 10), ("tea_table", 11, 9), ("mat", 11, 10),
           ("tea_table", 16, 10), ("mat", 16, 11), ("bed", 10, 1), ("bed", 14, 1), ("screen", 12, 1), ("bed", 18, 1),
           ("lantern_red", 1, 12), ("lantern_red", 22, 12), ("lantern_red", 7, 7), ("pot_bonsai", 22, 5)])

ROOMS = [LH_ARRIVAL_QUAY, LH_HARBOR_MARKET, LH_STAR_CHANDLERY, LH_TIDELIGHT_INN]
