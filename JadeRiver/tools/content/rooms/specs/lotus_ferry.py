"""E1 room specs: Lotus Ferry and the Reed Shallows, the prologue's village, its houses and the river shore east of it
(docs/architecture/room_engine.md).

Migrated from tools/data/topdown_rooms.py's hand functions; each compiles to its layout byte for byte. The
terrain, the ways, the door paths and the doorways are the engine's; the props and the foliage were placed by
hand, piece by piece, and stay pinned (no rule reproduces them)."""
from content.rooms.spec import room, variant


# Aunt Ping's hut: a wooden floor inside plastered walls, the loft over the east end up a short stair, Aunt Ping
# by the hearth, the tea on the table, the door in the front wall.
LF_FISHERS_HUT = room(
    "lf_fishers_hut", size=(20, 13), base="w", walls=True,
    features=[
        ("loft", (13, 1, 6, 2), dict(level=2, paint="w")),  # the loft
    ],
    stairs=[(13, 3, 2, 2, 0, 2, "w")],
    ways={"exit": ("s", 9.5)},
    spawn=(4, 4),
    anchors={
        "npc_aunt_ping": (6, 6), "tea_table": (9.5, 6), "net": (16, 5), "lu_float": (15, 1), "tea_loft": (17, 1),
    },
    # T2 (docs/architecture/topdown_mechanics.md): the side view's loft ladder, sealed until The Runaway Kite is done,
    # is a sealed hatch over the loft's flight.
    traverse=[("hatch", "loft_ladder", dict(rect=(13, 3, 2, 2)))],
    pins={"props": [   # hand-placed, piece by piece
        # the table (a floor one level up)
        ("crates", 9, 6), ("barrel", 1, 1), ("barrel", 2, 1), ("lantern", 1, 10), ("lantern", 18, 10),
        # foliage (decision 40): Aunt Ping's potted plants
        ("pot_orchid", 1, 5), ("pot_bonsai", 18, 8),
    ]})


# Lotus Ferry: Home Lane in the west (the Fisher's Hut, Granny Liu's hut, the West Gate), the paved square in the
# middle (Uncle Guo's stump and dummy, the shrine, the spring, the board, Old Ma's store, the hall and the Ferry Inn
# whose roofs the kite is caught on), the Ferry Docks in the east (the pier, Lu's boat, the watch-tower and its bell,
# the East Gate), a grassy terrace behind the houses and the river along the south. The village at night is the same
# place cut short east of the square (`VILLAGE_*` are both rooms').
VILLAGE_BANDS = [
    ("terrace", 0, 10, dict(level=1, paint="g")),    # the terrace behind the houses
    ("rock", 0, 3, dict(level=2, paint="r")),        # rock above it
    ("river", 34, 6, dict(water=True)),
    ("towpath", 32, 2, dict(level=0, paint="d")),    # the towpath along the bank
    ("lane", 20, 3, dict(paint="d")),                # the lane through the village
]
VILLAGE_FEATURES = [
    ("square", (22, 15, 26, 15), dict(level=0, paint="p")),   # the square's paving
    ("flowers", (1, 23, 4, 2), dict(paint="f")),              # flower beds along Home Lane
    ("flowers_2", (9, 24, 5, 2), dict(paint="f")),
    ("flowers_3", (1, 12, 2, 2), dict(paint="f")),
]
VILLAGE_STAIRS = [(12, 8, 3, 2, 0, 1), (33, 8, 3, 2, 0, 1)]   # up to the terrace from Home Lane, and from the square
VILLAGE_PATHS = [("hut", 20), ("granny", 20), ("store", 15, "p")]   # from each door down to the lane
# Sand (decision 44): river sand along the waterline from Home Lane's end to the ferry landing, the towpath wandering
# over it; it widens up the bank into the washing beach below Mei's line, a cove further east and the ferry landing's
# sand under the docks round the pier's foot. By the West Gate the old embankment stays.
VILLAGE_SAND = {"sand": [(6, 33, 66, 1), (10, 32, 11, 1), (28, 32, 11, 1), (47, 32, 25, 1)]}
VILLAGE_PROPS = [
    ("willow", 3, 5), ("willow", 20, 5), ("willow", 27, 5), ("willow", 41, 5), ("bamboo", 8, 4), ("bamboo", 9, 5),
    ("house", 4, 11, "hut"),                  # the Fisher's Hut: door at x 6-7
    ("crates", 10, 13),                       # the way onto its roof
    ("house", 15, 11, "granny"),              # Granny Liu's Herb Hut: door at x 17-18
    ("storehouse", 38, 11, "store"),          # Old Ma's Store: door at x 39-40
    ("lantern", 23, 15), ("lantern", 46, 15), ("barrel", 36, 13), ("bamboo", 19, 25), ("bamboo", 20, 26),
    ("reeds", 2, 33), ("reeds", 8, 33), ("reeds", 14, 33), ("reeds", 26, 33), ("reeds", 33, 33), ("reeds", 44, 33),
    ("lotus", 10, 36), ("lotus", 30, 37),
    # Foliage (decision 40): big trees along the terrace and round the square, bushes against the houses, a fence and
    # flowers along Home Lane, willows and tall grass by the river, lotus pads on it (a piece past the night's east edge
    # is left out there).
    ("tree_camphor", 24, 6), ("tree_plum", 30, 5), ("tree_maple", 46, 6), ("tree_camphor", 53, 5),
    ("tree_ribbons", 61, 6), ("tree_willow", 68, 5), ("bamboo_grove", 0, 4), ("bamboo_grove", 36, 4),
    ("bush", 16, 9), ("bush_azalea", 22, 9), ("bush_wide", 38, 9), ("bush", 50, 9), ("bush_azalea", 57, 9),
    ("hedge_2", 1, 9), ("bush", 64, 9),
    ("tree_camphor", 29, 12), ("bush_wide", 32, 13), ("bush_azalea", 26, 13), ("bush", 43, 12),
    ("bush_azalea", 45, 13), ("bush_wide", 62, 12), ("bush", 60, 14),
    ("bush_azalea", 2, 15), ("bush", 10, 15), ("bush_azalea", 14, 15), ("bush", 21, 17),
    ("fence_4", 5, 23), ("fence_3", 14, 23), ("tree_peach", 17, 27), ("tree_willow", 4, 29),
    ("tall_grass", 1, 26), ("tall_grass", 7, 30), ("ferns", 12, 26), ("rock_mossy", 20, 30),
    ("tree_willow", 40, 31), ("tall_grass", 26, 30), ("bush_wide", 30, 30), ("tall_grass", 35, 31),
    ("tree_camphor", 51, 17), ("bush", 49, 15), ("bush_azalea", 57, 15), ("rock_small", 63, 19),
    ("lotus_pads", 18, 35), ("lotus_pads", 40, 36), ("lotus_pads", 3, 37), ("cattails", 24, 34), ("cattails", 46, 34),
    ("cattails", 12, 34),
]
LF_VILLAGE = room(
    "lf_village", size=(72, 40),
    bands=VILLAGE_BANDS,
    features=VILLAGE_FEATURES + [
        ("docks", (48, 24, 24, 8), dict(level=0, paint="w")),     # the docks' boards
        ("pier", (58, 34, 3, 4), dict(level=0, paint="w")),
        ("tower", (66, 15, 4, 5), dict(level=3, paint="s")),      # the watch-tower's top
    ],
    stairs=VILLAGE_STAIRS + [(66, 20, 2, 4, 0, 3)],
    paths=VILLAGE_PATHS,
    ways={"hut_door": ("door", "hut"), "granny_door": ("door", "granny"), "store_door": ("door", "store"),
          "west_gate": ("w", 21), "east_gate": ("e", 21),
          "boat": dict(at=(60, 36), dir="e", arrive=(59, 36), span=1.5)},
    spawn=(8, 17),
    anchors={
        "sign_home": (2, 18),
        "pings_ladle": (8, 11),                   # on the Fisher's Hut's roof
        "npc_aunt_ping_lane": (11, 17), "npc_washer_mei": (14, 31), "spring_village": (24, 26),
        "shrine_village": (26, 16), "npc_uncle_guo": (30, 22), "stump_guo": (31, 26), "dummy_guo": (34, 26),
        "board_village": (36, 16), "storage_village": (43, 16), "npc_little_dou": (44, 24), "cook_village": (46, 28),
        "kite": (58, 12),                         # on the Ferry Inn's roof
        "npc_shen_lian_npc": (52, 27), "npc_lu_boatman": (56, 28), "npc_fisher_wen": (64, 28), "fish_docks": (59, 37),
        "tower_bell": (68, 16), "gull_nest": (69, 15),
    },
    ground=VILLAGE_SAND,
    pins={"props": VILLAGE_PROPS + [   # hand-placed, piece by piece
        ("house", 48, 11),                        # the village hall
        ("house", 55, 11),                        # the Ferry Inn, a tile's jump beyond the hall
        ("crates", 46, 13),                       # the way onto the hall's roof
        ("boat", 61, 36), ("lantern_red", 50, 24), ("lantern_red", 70, 24), ("barrel", 63, 25), ("crates", 64, 30),
    ]})


# Lotus Ferry at Night: Home Lane and the square as by day, the hut's door open, the villagers out in the lane and the
# Hollow things coming up out of the river.
LF_VILLAGE_NIGHT = variant(
    LF_VILLAGE, "lf_village_night", size=(48, 40),
    features=VILLAGE_FEATURES, stairs=VILLAGE_STAIRS, ways={},
    spawn=(30, 22),
    anchors={
        "hut_refuge": (6.5, 15),
        "npc_ping_night": (8.5, 16.5),            # Aunt Ping at the hut's door with her lamp
        "npc_dou_night": (44, 25), "npc_granny_night": (18, 23), "npc_ma_night": (38, 18),
    },
    # The Hollow Night's event (world.py, in its order): two minnows about each villager; the river's minnows up the
    # bank; the lane's schools from both ends once the villagers are in; the eel rising mid-river off the square (and,
    # decision 45, rising there again at once, awake, after a reload once it has woken).
    event={"fixed": [[42, 26.5], [46, 26], [16, 25], [20.5, 24.5], [36, 20], [40.5, 20]],
           "waves": [[[5, 31], [15, 32], [25, 31], [35, 32], [44, 31]],
                     [[1, 20.5], [1.5, 22], [46.5, 20.5], [46, 22], [24, 31], [32, 31]]],
           "timed": [[30, 36.5], [30, 36.5]]},
    pins={"props": VILLAGE_PROPS})


# Old Ma's Store: the counter across the shop with Old Ma behind it, the soup jars up in the loft, the sacks by the
# west wall with the old net under the shelf.
LF_OLD_MA_STORE = room(
    "lf_old_ma_store", size=(18, 12), base="w", walls=True,
    features=[
        ("loft", (1, 1, 5, 2), dict(level=2, paint="w")),  # the loft
    ],
    stairs=[(4, 3, 2, 2, 0, 2, "w")],
    ways={"exit": ("s", 8.5)},
    spawn=(8, 9),
    anchors={
        "npc_old_ma": (12, 3), "soup_loft": (2, 1), "old_net_floor": (3, 9),
    },
    # T2 (docs/architecture/topdown_mechanics.md): the side view's storeroom ladder, sealed until The Runaway Kite is
    # done, is a sealed hatch over the loft's flight.
    traverse=[("hatch", "storeroom_ladder", dict(rect=(4, 3, 2, 2)))],
    pins={"props": [   # hand-placed, piece by piece
        # the counter
        ("crates", 10, 5), ("crates", 12, 5), ("barrel", 1, 7), ("barrel", 1, 8), ("barrel", 16, 1),
        ("lantern", 16, 9),
        # foliage (decision 40): potted plants
        ("pot_bonsai", 16, 4), ("pot_orchid", 7, 1),
    ]})


# Granny Liu's Herb Hut: her table by the hearth, the family altar (the shrine) by the east wall, the herb loft over
# the west end with its jars and a bundle of willow moss.
LF_GRANNY_LIU_HUT = room(
    "lf_granny_liu_hut", size=(18, 12), base="w", walls=True,
    features=[
        ("herb_loft", (1, 1, 6, 2), dict(level=2, paint="w")),  # the herb loft
    ],
    stairs=[(5, 3, 2, 2, 0, 2, "w")],
    ways={"exit": ("s", 8.5)},
    spawn=(8, 9),
    anchors={
        "npc_granny_liu": (6, 6), "shrine_granny": (14, 5), "jar_1": (1, 1), "jar_2": (2, 1), "moss_bundle": (4, 1),
    },
    pins={"props": [   # hand-placed, piece by piece
        # her table
        ("crates", 8, 6), ("incense", 15, 4), ("barrel", 16, 1), ("barrel", 16, 2), ("lantern", 1, 9),
        # foliage (decision 40): potted plants
        ("pot_orchid", 16, 8), ("pot_bonsai", 12, 1),
    ]})


# Lu's Boat: the deck on the river at night, the gangway back to the docks, the spring's breath at the bow where
# the first breakthrough is made, Lu by the cabin and the star mat on its roof.
LF_LU_BOAT = room(
    "lf_lu_boat", size=(24, 14), base="~",
    features=[
        ("deck", (3, 4, 18, 6), dict(level=0, paint="w")),  # the deck
        ("gangway", (0, 6, 3, 2), dict(level=0, paint="w")),  # the gangway
    ],
    ways={"deck": ("w", 6.5, dict(span=2))},
    spawn=(7, 8),
    anchors={
        "npc_lu_boat": (10, 8), "boat_spring": (7, 7), "star_mat": (16, 4),
    },
    pins={"props": [   # hand-placed, piece by piece
        # the cabin
        ("storehouse", 14, 4),
        # up onto its roof
        ("crates", 12, 6), ("lantern_red", 3, 4), ("lantern_red", 20, 9), ("barrel", 20, 4), ("lotus", 1, 11),
        ("lotus", 18, 1), ("lotus", 8, 12), ("pot_bonsai", 19, 8), ("lotus_pads", 4, 1), ("lotus_pads", 12, 11),
        ("lotus_pads", 21, 11),
    ]})


# The Reed Shallows: a grassy shore under a rock ridge, the path from the East Gate along it, the crabs on the
# flats, the rats round the herbs in the middle, Old Snapper by the far herbs, the jetty to fish from and the river.
LF_REED_SHALLOWS = room(
    "lf_reed_shallows", size=(64, 30),
    bands=[
        ("rock_ridge", 0, 4, dict(level=2, paint="r")),  # the rock ridge
        ("bank", 4, 5, dict(level=1, paint="g")),  # the grassy bank above the flats
        ("path", 13, 3, dict(paint="d")),  # the path along the shore
        ("river", 23, 7, dict(water=True)),  # the river
    ],
    features=[
        ("jetty", (26, 22, 3, 3), dict(level=0, paint="w")),  # the jetty
        ("sandbar", (40, 21, 8, 2), dict(level=0, paint="d")),  # a sandbar
    ],
    stairs=[(20, 9, 3, 2, 0, 1), (50, 9, 3, 2, 0, 1)],
    ways={"west": ("w", 14), "east": ("e", 14)},
    spawn=(3, 14),
    anchors={
        "jar_1": (40, 6), "jar_2": (47, 7), "jar_3": (39, 11), "jar_4": (58, 16), "jar_5": (61, 20),
        "herb_6": (17, 11), "herb_7": (44, 12), "herb_8": (55, 17), "fish_9": (27, 24), "rift_tear": (35, 18),
        "swarm_glowfly": (41, 19), "trail_jade_frog": (11, 19),
    },
    foes=[[(13, 17), (22, 20), (30, 18), (36, 20), (42, 16), (48, 20)], [(27, 11), (33, 12), (38, 13), (43, 10)],
        [(55, 20)]],
    # T2 (docs/architecture/topdown_mechanics.md): the side view's three driftwood logs drift along the shallows off the
    # sandy bank, each boarded from the bank at either end of its drift.
    traverse=[("raft", "driftwood_a", dict(at=(13, 23), size=(3, 1), path=[(5, 0)], speed=20, wait_s=2.0, look="driftwood")),
              ("raft", "driftwood_b", dict(at=(44, 23), size=(3, 1), path=[(-12, 0)], speed=20, wait_s=2.0, look="driftwood")),
              ("raft", "driftwood_c", dict(at=(49, 23), size=(3, 1), path=[(5, 0)], speed=20, wait_s=2.0, look="driftwood"))],
    ground={"sand": [(0, 22, 64, 1), (2, 21, 12, 1), (19, 21, 10, 1), (33, 21, 16, 1), (53, 21, 9, 1), (36, 20, 13, 1),
                     (5, 20, 5, 1)]},
    pins={"props": [   # hand-placed, piece by piece
        ("reeds", 3, 22), ("reeds", 9, 22), ("reeds", 15, 22), ("reeds", 33, 22), ("reeds", 37, 22),
        ("reeds", 45, 22), ("reeds", 52, 22), ("reeds", 58, 22), ("reeds", 30, 21), ("willow", 12, 5),
        ("willow", 48, 5), ("shrub", 30, 6), ("shrub", 60, 6), ("lotus", 34, 25), ("lotus", 54, 26),
        ("tree_camphor", 5, 6), ("tree_willow", 25, 6), ("tree_maple", 35, 5), ("bamboo_grove", 43, 4),
        ("tree_plum", 56, 6), ("bush", 2, 8), ("bush_wide", 8, 8), ("bush", 15, 8), ("bush_azalea", 27, 8),
        ("bush", 33, 8), ("bush_wide", 54, 8), ("bush_azalea", 61, 8), ("bush", 8, 11), ("ferns", 57, 11),
        ("rock_mossy", 6, 19), ("tall_grass", 15, 21), ("rock_small", 24, 18), ("tall_grass", 50, 21),
        ("rock_small", 58, 18), ("cattails", 5, 23), ("cattails", 12, 23), ("cattails", 21, 23), ("cattails", 31, 23),
        ("cattails", 48, 23), ("cattails", 57, 23), ("lotus_pads", 14, 25), ("lotus_pads", 44, 27),
        ("lotus_pads", 60, 24),
    ]})


ROOMS = [LF_FISHERS_HUT, LF_VILLAGE, LF_VILLAGE_NIGHT, LF_OLD_MA_STORE, LF_GRANNY_LIU_HUT, LF_LU_BOAT, LF_REED_SHALLOWS]
