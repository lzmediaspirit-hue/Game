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


# R1: the Reed Marsh past the Marsh Edge, the main story's way east (generated rooms: the engine's terrain, anchors,
# stairs, foes and flora).

# The Grey Pools: the marsh the Hollowing has drunk grey. The path east from the Marsh Edge between grey pools, the
# deep one with a jetty and a moored raft (the chest), dead trees and grey reeds; the reed bank under the lily ledge,
# and a boardwalk north over the channel to Greyreed Hamlet; hollow puddles on the path's verges.
RM_GREY_POOLS = room(
    "rm_grey_pools", size=(60, 30), biome="grey_marsh",
    bands=[("hamlet_bank", 0, 2, dict(level=1, paint="m")), ("channel", 2, 4, dict(water=True, wavy=True)),
           ("reedbank", 6, 5, dict(level=1, paint="m", wavy=True)), ("path", 13, 3, dict(paint="d")), ("flats", 16, 9, dict(level=0)),
           ("deeps", 25, 5, dict(water=True, wavy=True))],
    features=[("bridge", (29, 1, 3, 6), dict(level=1, paint="w")), ("lily_ledge", (44, 5, 9, 5), dict(level=2, paint="r", shape="round")),
              ("grey_pool", (8, 17, 22, 10), dict(water=True, shape="round")),
              ("jetty", (19, 17, 2, 6), dict(level=0, paint="w")),
              ("pool_east", (40, 18, 13, 8), dict(water=True, shape="round"))],
    stairs="auto",
    ways={"west": ("w", "path"), "east": ("e", "path"), "hamlet": ("n", 30, dict(cut=(3, "w")))},
    spawn="west",
    anchors={"jar_2": "reedbank@5", "jar_5": "reedbank@36", "jar_8": "lily_ledge@47", "chest_moored_raft": "jetty.front@19",
             "jar_3": "verge.s@33", "jar_4": "verge.s@37", "jar_6": "verge@53", "herb_1": "flats@40",
             "swarm_reed_cicada": "pool_east.n@45", "mine_grey_pools_seep": "flats@53", "rift_tear": "flats@33",
             "spirit_fruit_tree": "reedbank@13"},
    props=[("boat", 21, 22), ("lantern", 28, 7), ("lantern", 32, 7)],
    flora={"reedbank": dict(density=0.4)},
    areas=[{"kind": "hollow_puddle", "rect": r} for r in ([9, 11, 3, 2], [20, 11, 3, 2], [28, 16, 3, 2], [36, 11, 3, 2],
                                                           [50, 11, 3, 2])],
    foes=["auto:flats", "auto", "auto:flats"])

# The Sunken Causeway: the old paved causeway across the open marsh, sunk in two places and laid over with planks, reed
# isles either side, a boardwalk north to the hermit's stilt house, the broken pillar's plinth on the east isle (two
# jars on it), and the east shore where the signpost points on to the Whispering Bamboo.
RM_SUNKEN_CAUSEWAY = room(
    "rm_sunken_causeway", size=(60, 30), biome="reed_marsh",
    bands=[("north_water", 0, 12, dict(water=True, wavy=True)), ("south_water", 16, 14, dict(water=True, wavy=True)),
           ("causeway", 12, 4, dict(level=0, paint="p", walk=True))],
    features=[("west_shore", (-6, 5, 14, 21), dict(level=0, paint="m", shape="round")),
              ("isle_nw", (9, 5, 14, 8), dict(level=0, paint="m", shape="round")),
              ("pillar_isle", (42, 3, 14, 10), dict(level=0, paint="m", shape="round")),
              ("plinth", (46, 6, 6, 3), dict(level=1, paint="s")),
              ("isle_s", (20, 15, 16, 8), dict(level=0, paint="m", shape="round")),
              ("east_shore", (53, 4, 14, 22), dict(level=0, paint="m", shape="round")),
              ("boardwalk", (29, 0, 3, 12), dict(level=0, paint="w")),
              ("sunk_w", (15, 12, 4, 4), dict(paint="w")), ("sunk_e", (37, 12, 3, 4), dict(paint="w"))],
    stairs="auto",
    ways={"west": ("w", "causeway"), "east": ("e", "causeway"), "stilts": ("n", 30)},
    spawn="west",
    anchors={"herb_1": "isle_s@29", "jar_2": "isle_nw@12", "jar_3": "isle_s@24", "jar_4": "east_shore@55",
             "jar_5": "plinth@47", "jar_6": "plinth@50", "sign_rm": "causeway.n@56"},
    props=[("lantern", 28, 10), ("lantern", 32, 10)],
    flora={"causeway": ["cattails", "reeds"], "isle_nw": dict(density=0.45), "isle_s": dict(density=0.4)},
    foes=["auto", "auto:bank"])

# The Hermit's Stilt House: Hermit Yao's house on its deck over the north of his pond, the ladder down at its west end
# where he keeps, stepping stones out to the rock where the mist lotus grows, the still spring in the reeds to the
# west, his shrine on the east bank, and the boardwalk down to the Sunken Causeway.
RM_HERMIT_STILT_HOUSE = room(
    "rm_hermit_stilt_house", size=(40, 24), biome="reed_marsh",
    bands=[("north", 0, 5, dict(level=0)), ("meadow", 5, 19, dict(level=0))],
    features=[("pond", (10, 6, 20, 12), dict(water=True, shape="round")),
              ("deck", (8, 1, 22, 5), dict(level=2, paint="w")),
              ("rock", (19, 9, 3, 3), dict(level=1, paint="r")),
              ("stones", (20, 12, 1, 3), dict(level=0, paint="s")), ("stones_2", (21, 14, 1, 4), dict(level=0, paint="s")),
              ("reedbed", (28, 17, 11, 6), dict(water=True, shape="round")),
              ("spring", (1, 14, 6, 5), dict(water=True, shape="round")),
              ("boardwalk", (19, 18, 3, 6), dict(level=0, paint="w"))],
    stairs=[(8, 6, 2, 4, 0, 2, "w")],
    ways={"stairs": ("s", 20)},
    spawn="stairs",
    anchors={"hermit_mat": "deck.front@20", "hermit_tea": "deck.front@25", "npc_hermit_yao": (10, 11),
             "pond_lotus": "rock@20", "spring_hermit": "spring.n@4", "shrine_hermit": "meadow@34", "herb_1": "meadow@37"},
    props=[("house", 15, 1), ("lantern", 10, 4), ("lantern", 28, 4), ("drying_rack", 22, 2), ("fish_basket", 9, 1)],
    flora={"meadow": dict(density=0.4)})

ROOMS = [RM_MARSH_EDGE, RM_GREY_POOLS, RM_SUNKEN_CAUSEWAY, RM_HERMIT_STILT_HOUSE]
