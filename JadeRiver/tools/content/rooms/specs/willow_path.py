"""E1 room specs: The Willow Path: the road west from Lotus Ferry to Stoneford (docs/architecture/room_engine.md).

Migrated from tools/data/topdown_rooms.py's hand functions; each compiles to its layout byte for byte. The
terrain, the ways, the door paths and the doorways are the engine's; the props and the foliage were placed by
hand, piece by piece, and stay pinned (no rule reproduces them)."""
from content.rooms.spec import room


# Willow Path East: the road west out of Lotus Ferry under the willows and plum trees, a knoll where Old Pan sets
# up, a meadow terrace to the north, a stream to the south, and the boarlets rooting along the verges.
WP_EAST = room(
    "wp_east", size=(64, 26),
    bands=[
        ("rock", 0, 2, dict(level=2, paint="r")),
        ("terrace", 2, 5, dict(level=1, paint="f")),  # the meadow terrace
        ("road", 12, 3, dict(paint="d")),  # the road
        ("stream", 21, 5, dict(water=True)),  # the stream
    ],
    features=[
        ("knoll", (27, 8, 8, 3), dict(level=1, paint="g")),  # the knoll
    ],
    stairs=[(44, 7, 3, 2, 0, 1), (8, 7, 3, 2, 0, 1), (30, 11, 2, 1, 0, 1)],
    ways={"east": ("e", 13), "west": ("w", 13)},
    spawn=(60, 13),
    anchors={
        "npc_old_pan_wp": (31, 9), "pan_spot": (34, 13), "herb_1": (33, 16), "jar_2": (48, 4), "crate_3": (33, 18),
        "jar_4": (52, 17), "sign_wp": (60, 11), "note_lu": (57, 11),
    },
    foes=[[(10, 15), (20, 16), (26, 17), (44, 15), (51, 16)]],
    ground={"sand": [(9, 20, 16, 1), (34, 20, 18, 1), (16, 19, 5, 1), (42, 19, 4, 1)]},
    pins={"props": [   # hand-placed, piece by piece
        ("willow", 5, 3), ("willow", 16, 3), ("willow", 38, 3), ("willow", 54, 3), ("shrub", 22, 4), ("shrub", 60, 4),
        ("reeds", 4, 20), ("reeds", 12, 20), ("reeds", 25, 20), ("reeds", 36, 20), ("reeds", 47, 20),
        ("reeds", 58, 20), ("incense", 50, 10), ("tree_plum", 11, 5), ("tree_camphor", 27, 4), ("tree_peach", 33, 5),
        ("tree_plum", 51, 5), ("tree_maple", 60, 6), ("bush_wide", 1, 6), ("bush_azalea", 14, 6), ("bush", 20, 6),
        ("bush", 41, 6), ("bush_azalea", 57, 6), ("fence_4", 13, 11), ("fence_3", 36, 11), ("bush", 5, 10),
        ("bush_azalea", 47, 10), ("tree_willow", 8, 19), ("tree_peach", 22, 19), ("tree_willow", 40, 19),
        ("tree_plum", 55, 19), ("tall_grass", 14, 19), ("tall_grass", 30, 19), ("tall_grass", 47, 19),
        ("rock_small", 17, 16), ("rock_mossy", 55, 15), ("cattails", 2, 21), ("cattails", 19, 21),
        ("cattails", 33, 21), ("cattails", 50, 21), ("lotus_pads", 26, 23), ("lotus_pads", 45, 24),
    ]})


# Willow Path West: the road on to Stoneford past the training stumps and lifting stones, the pine ridge where the
# toads sit, a rock pillar with a chest on top, the shrine and the Spirit Fruit tree by the western end, and a lotus pond
# to the south. S12c: the pillar is the side view's pine top, a path above (S43): two levels over the meadow, no crates
# or step up to it, so only the Cloud Ladder Step's second jump climbs onto it.
WP_WEST = room(
    "wp_west", size=(64, 30),
    bands=[
        ("rock", 0, 3, dict(level=2, paint="r")),
        ("road", 14, 3, dict(paint="d")),  # the road
        ("pond", 26, 4, dict(water=True)),  # the pond
    ],
    features=[
        ("pine_ridge", (0, 3, 26, 6), dict(level=1, paint="g")),  # the pine ridge
        ("pine_top", (40, 6, 3, 3), dict(level=2, paint="r")),  # the rock pillar, a path above (the double jump's)
        ("training_ground", (14, 18, 12, 4), dict(level=0, paint="d")),  # the training ground
    ],
    stairs=[(8, 9, 3, 2, 0, 1)],
    ways={"east": ("e", 15), "west": ("w", 15)},
    spawn=(60, 15),
    anchors={
        "herb_1": (4, 6), "herb_2": (48, 23), "jar_3": (9, 4), "jar_4": (14, 4), "jar_5": (32, 12), "jar_6": (43, 24),
        "jar_7": (57, 18), "stump_0": (17, 19), "stump_1": (20, 20), "stump_2": (23, 19), "lift_1": (30, 19),
        "lift_2": (33, 22), "shrine_wp": (58, 12), "sign_wpw": (3, 12), "temper_copper_wp_west": (39, 21),
        "chest_pine_top": (41, 7), "rift_tear": (35, 17), "first_fruit_tree": (52, 11), "swarm_glowfly": (44, 20),
        "trail_mist_hare": (19, 23),
    },
    foes=[[(22, 17), (18, 23), (28, 17), (37, 18), (45, 17), (42, 22)], [(15, 5), (17, 6), (19, 5)], [(4, 21)]],
    ground={"sand": [(12, 25, 26, 1), (14, 24, 8, 1), (40, 25, 8, 1)]},
    pins={"props": [   # hand-placed, piece by piece
        ("bamboo", 3, 4), ("bamboo", 21, 4), ("willow", 30, 8), ("willow", 50, 8),
        ("willow", 60, 8), ("shrub", 12, 5), ("lantern", 56, 11), ("lotus", 10, 27), ("lotus", 36, 28),
        ("reeds", 2, 25), ("reeds", 20, 25), ("reeds", 44, 25), ("reeds", 58, 25), ("tree_pine", 6, 4),
        ("tree_pine", 23, 7), ("tree_pine", 1, 7), ("tree_maple", 35, 10), ("tree_camphor", 46, 9), ("bush", 4, 8),
        ("bush_wide", 14, 8), ("bush", 19, 8), ("bush_azalea", 24, 8), ("bush", 27, 5), ("bush_azalea", 38, 4),
        ("bush_wide", 61, 5), ("fence_4", 20, 13), ("fence_3", 44, 13), ("tree_willow", 7, 23), ("tree_peach", 9, 19),
        ("tree_willow", 27, 25), ("tree_plum", 53, 21), ("bamboo_grove", 60, 24), ("tall_grass", 1, 20),
        ("tall_grass", 10, 24), ("tall_grass", 26, 22), ("tall_grass", 50, 24), ("rock_mossy", 33, 24),
        ("cattails", 6, 26), ("cattails", 24, 26), ("cattails", 47, 26), ("cattails", 55, 26), ("lotus_pads", 20, 27),
        ("lotus_pads", 50, 28),
    ]})


ROOMS = [WP_EAST, WP_WEST]
