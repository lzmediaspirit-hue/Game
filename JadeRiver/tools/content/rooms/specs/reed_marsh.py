"""E1 room specs: The Reed Marsh: the Marsh Edge (docs/architecture/room_engine.md).

Migrated from tools/data/topdown_rooms.py's hand functions; each compiles to its layout byte for byte. The
terrain, the ways, the door paths and the doorways are the engine's; the props and the foliage were placed by
hand, piece by piece, and stay pinned (no rule reproduces them)."""
from content.rooms.spec import room


# The Marsh Edge, the Reed Marsh's first field: the path east from the Reed Shallows over wet meadow and two
# boardwalks across the channels, open water to the north with the stilt platforms standing in it (the reed platform
# and the net platform where the frogs sit, the stilt hut, the lookout) up their wooden stairs, lower stilts on the
# meadow, the south pools with reeds, lotus and the fishing spot, and the grey patches where the Hollowing has drained
# the reeds, dead trees over them.
RM_MARSH_EDGE = room(
    "rm_marsh_edge", size=(64, 30), base="m",
    bands=[
        ("open_water", 0, 6, dict(water=True)),  # the open marsh water
        ("south_pools", 23, 7, dict(water=True)),  # the south pools
    ],
    features=[
        ("channel", (24, 6, 2, 17), dict(water=True)),  # the channels between them
        ("channel_2", (46, 6, 2, 17), dict(water=True)),
        # bays and meanders, so no shore runs straight for long
        ("bay", (7, 6, 5, 1), dict(water=True)),
        ("bay_2", (20, 6, 3, 2), dict(water=True)),
        ("bay_3", (43, 6, 2, 1), dict(water=True)),
        ("bay_4", (57, 6, 4, 2), dict(water=True)),
        ("bay_5", (26, 8, 1, 3), dict(water=True)),
        ("bay_6", (23, 18, 1, 3), dict(water=True)),
        ("bay_7", (45, 18, 1, 3), dict(water=True)),
        # a spit and an islet in the south pools, dry sand (decision 44)
        ("spit", (10, 23, 4, 2), dict(level=0, paint="a")),
        ("spit_2", (40, 23, 5, 1), dict(level=0, paint="a")),
        ("spit_3", (50, 25, 3, 2), dict(level=0, paint="a")),
        ("path", (0, 13, 64, 3), dict(paint="d")),  # the path along the marsh
        ("boardwalk", (24, 13, 2, 3), dict(level=0, paint="w")),  # its boardwalks over the channels
        ("boardwalk_2", (46, 13, 2, 3), dict(level=0, paint="w")),
        ("reed_platform", (12, 2, 6, 4), dict(level=2, paint="w")),  # the reed platform (x 12-17, y 2-5)
        ("stilt_hut", (27, 1, 7, 6), dict(level=2, paint="w")),  # the stilt hut's platform (x 27-33, y 1-6)
        ("net_platform", (38, 2, 6, 4), dict(level=2, paint="w")),  # the net platform
        ("lookout", (50, 1, 6, 5), dict(level=2, paint="w")),  # the lookout
        ("stilts", (3, 7, 5, 3), dict(level=1, paint="w")),  # low stilts on the meadow: west, by the pool, east
        ("stilts_2", (19, 19, 4, 3), dict(level=1, paint="w")),
        ("stilts_3", (57, 18, 4, 3), dict(level=1, paint="w")),
        ("jetty", (28, 22, 3, 1), dict(level=0, paint="w")),  # a jetty into the south pool
    ],
    stairs=[(14, 6, 2, 4, 0, 2, "w"), (32, 7, 2, 4, 0, 2, "w"), (40, 6, 2, 4, 0, 2, "w"), (52, 6, 2, 4, 0, 2, "w")],
    ways={"west": ("w", 14), "east": ("e", 14)},
    spawn=(3, 14),
    anchors={
        "herb_1": (33, 4),  # on the stilt hut's platform
        "herb_2": (53, 3),  # on the lookout
        "herb_3": (57, 16),
        "jar_4": (16, 3),  # on the reed platform
        "jar_5": (42, 3),  # on the net platform
        "jar_6": (38, 17), "jar_7": (44, 11), "jar_8": (60, 16), "fish_9": (29, 24), "grey_patch_0": (14, 17),
        "grey_patch_1": (30, 19), "grey_patch_2": (49, 17), "rift_tear": (36, 16), "spirit_fruit_tree": (21, 16),
        "swarm_glowfly": (41, 19), "trail_jade_frog": (9, 17),
        "array_marsh": (4, 17),  # decision 42: the watch post
        "npc_watcher_bo": (3, 20), "npc_mei_qing_marsh": (5, 20), "npc_watcher_su": (8, 19),
        "npc_elder_hu_marsh": (16, 12),  # where the mentor comes down
        "npc_elder_sung_marsh": (16, 12),
    },
    foes=[[(13, 3), (16, 4)], [(10, 16), (21, 12), (35, 18), (54, 16)], [(54, 2)], [(43, 20)],
        [(19, 16), (33, 17), (44, 16)], [(39, 3), (42, 4)]],
    pins={"props": [   # hand-placed, piece by piece
        # the hut
        ("storehouse", 28, 1), ("dead_tree", 11, 18), ("dead_tree", 29, 17), ("dead_tree", 50, 19),
        ("grey_reeds", 13, 19), ("grey_reeds", 15, 18), ("grey_reeds", 31, 20), ("grey_reeds", 28, 20),
        ("grey_reeds", 48, 19), ("grey_reeds", 51, 17), ("reeds", 1, 22), ("reeds", 6, 22), ("reeds", 10, 22),
        ("reeds", 20, 22), ("reeds", 35, 22), ("reeds", 42, 22), ("reeds", 55, 22), ("reeds", 60, 22),
        ("reeds", 4, 6), ("reeds", 19, 6), ("reeds", 36, 6), ("reeds", 44, 6), ("reeds", 58, 6), ("lotus", 8, 26),
        ("lotus", 38, 25), ("lotus", 54, 27), ("lotus", 21, 3), ("lotus", 58, 2), ("willow", 36, 10),
        ("willow", 60, 9), ("boulder", 9, 10), ("shrub", 44, 10), ("banner_jade", 1, 19), ("banner_cloud", 7, 21),
        ("lantern", 10, 20), ("tree_willow", 19, 11), ("tree_willow", 57, 11), ("bush", 1, 9), ("bush_wide", 9, 12),
        ("ferns", 31, 10), ("tall_grass", 5, 10), ("tall_grass", 28, 11), ("tall_grass", 51, 11),
        ("tall_grass", 11, 21), ("tall_grass", 37, 21), ("tall_grass", 55, 21), ("log", 17, 21),
        ("rock_small", 43, 21), ("cattails", 2, 5), ("cattails", 9, 5), ("cattails", 22, 5), ("cattails", 45, 5),
        ("cattails", 62, 5), ("cattails", 5, 23), ("cattails", 16, 23), ("cattails", 33, 23), ("cattails", 52, 23),
        ("cattails", 60, 23), ("lotus_pads", 5, 2), ("lotus_pads", 40, 26), ("lotus_pads", 20, 27),
    ]})


ROOMS = [RM_MARSH_EDGE]
