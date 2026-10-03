"""E1 room specs: the Cloud Sect's grounds, the Cliff Stair, the Sword Court, the Array Court, Elder Sung's peak
(docs/architecture/room_engine.md).

Migrated from tools/data/topdown_rooms.py's hand functions; each compiles to its layout byte for byte. The
terrain, the ways, the door paths and the doorways are the engine's; the props and the foliage were placed by
hand, piece by piece, and stay pinned (no rule reproduces them)."""
from content.rooms.spec import room
from content.rooms.specs.shared import weapon_hall


# The Cliff Stair, the Cloud Sect's approach: the road up from Stoneford between the sect's banners into the lower
# court (the steward, the teleport stone, the Cloud Steps' starting stone, the shrine, the service dorm and its porch,
# the notice board and the deacon), the grand stair up the cliff to its landing, a rock ledge above it, and the top
# ledge where the Cloud Library's cliff door opens and the Cloud Steps' bell hangs.
CM_CLIFF_STAIR = room(
    "cm_cliff_stair", size=(56, 34),
    bands=[
        ("crown", 0, 2, dict(level=6, paint="r")),  # the cliff's crown
    ],
    features=[
        ("cliff_face", (0, 2, 34, 4), dict(level=5, paint="r")),  # the cliff face behind the landing
        ("rock", (34, 2, 6, 3), dict(level=5, paint="r")),
        ("rock_2", (52, 2, 4, 8), dict(level=5, paint="r")),
        ("landing", (16, 6, 18, 8), dict(level=2, paint="s")),  # the landing
        ("ledge", (34, 5, 6, 6), dict(level=3, paint="r")),  # the ledge above the landing
        ("top_ledge", (40, 2, 12, 6), dict(level=4, paint="r")),  # the top ledge
        ("lower_court", (3, 18, 50, 11), dict(level=0, paint="p")),  # the lower court
        ("road", (8, 29, 3, 5), dict(paint="d")),  # the road up from Stoneford
        ("porch", (38, 15, 6, 2), dict(level=0, paint="w")),  # its porch
        ("flowers", (44, 14, 5, 2), dict(level=0, paint="f")),
        ("flowers_2", (2, 14, 8, 2), dict(level=0, paint="f")),
        ("flowers_3", (30, 30, 10, 2), dict(level=0, paint="f")),
    ],
    stairs=[
        (23, 14, 4, 4, 0, 2),  # the grand stair
    ],
    ways={"stoneford": ("s", 9), "east": ("e", 23), "library": ("door", "library")},
    spawn=(9, 31),
    anchors={
        "shrine_cm": (14, 19), "stone_cm": (13, 24),
        "array_cm_gate": (9, 25),  # decision 42: the transfer array by the steward and the stone
        "board_cm": (46, 20), "siege_gong_cm": (51, 26), "npc_cloud_steward": (7, 21), "npc_cloud_deacon": (48, 22),
        "npc_cloud_disciple_a": (22, 22), "dorm_bed_cm": (42, 16), "sweep_cm_0": (18, 24), "sweep_cm_1": (30, 25),
        "sweep_cm_2": (11, 27),  # the grey stain by the gate
        "cloud_steps_bell": (49, 5),  # the Cloud Steps' finish, on the top ledge
        "cloud_steps_stone": (5, 26),
    },
    ground={"snow": [(0, 0, 56, 6), (52, 6, 4, 1), (40, 2, 12, 6)], "snowpack": [(44, 5, 7, 1), (46, 6, 2, 2)]},
    pins={"props": [   # hand-placed, piece by piece
        # the Cloud Library's cliff door
        ("storehouse", 44, 2, "library"),
        # the service dorm
        ("house", 38, 12), ("banner_cloud", 6, 29), ("banner_cloud", 12, 29), ("lantern", 17, 12),
        ("lantern", 32, 12), ("lantern", 22, 16), ("lantern", 27, 16), ("pine", 3, 8), ("pine", 11, 10),
        ("pine", 54, 13), ("pine", 2, 30), ("boulder", 6, 12), ("boulder", 47, 11), ("boulder", 51, 30),
        ("tree_pine", 13, 7), ("bush", 1, 11), ("tree_pine", 51, 10), ("bush_wide", 36, 7), ("bush", 53, 16),
        ("tree_pine", 20, 32), ("tree_maple", 44, 32), ("tree_plum", 27, 32), ("bush", 14, 30),
        ("bush_azalea", 39, 29), ("tall_grass", 49, 32), ("rock_small", 35, 32),
    ]})


# The Sword Court: the Sword Hall's two wings along the cliff (the Weapon Hall's door and the Cloud Library's), the
# hall master and the dummies at the west, the plum-blossom poles (timber posts at stepped heights, a tile apart or
# side by side a level up), the sparring post, the Temper drum and the arena master, training stumps and the two sword
# pillars at the east.
CM_SWORD_COURT = room(
    "cm_sword_court", size=(60, 30),
    bands=[
        ("rock", 0, 3, dict(level=4, paint="r")),
        ("court", 10, 13, dict(level=0, paint="p")),  # the court
    ],
    features=[
        ("pole", (38, 15, 1, 1), dict(level=1, paint="w")),  # the plum-blossom poles
        ("pole_2", (40, 15, 1, 1), dict(level=1, paint="w")),  # the plum-blossom poles
        ("pole_3", (41, 15, 1, 1), dict(level=2, paint="w")),  # the plum-blossom poles
        ("pole_4", (43, 15, 1, 1), dict(level=2, paint="w")),  # the plum-blossom poles
        ("pole_5", (44, 15, 1, 1), dict(level=3, paint="w")),  # the plum-blossom poles
        ("pole_6", (46, 15, 1, 1), dict(level=2, paint="w")),  # the plum-blossom poles
        ("pole_7", (48, 15, 1, 1), dict(level=1, paint="w")),  # the plum-blossom poles
        ("pillar", (51, 8, 1, 1), dict(level=5, paint="s")),  # the sword pillars
        ("pillar_2", (56, 8, 1, 1), dict(level=5, paint="s")),  # the sword pillars
        ("flowers", (3, 24, 4, 2), dict(level=0, paint="f")),
        ("flowers_2", (12, 25, 8, 2), dict(level=0, paint="f")),
        ("flowers_3", (28, 24, 9, 2), dict(level=0, paint="f")),
        ("flowers_4", (46, 25, 6, 2), dict(level=0, paint="f")),
    ],
    paths=[("weapon_hall", 10, "p"), ("library", 10, "p")],
    ways={
        "west": ("w", 16),
        "east": ("e", 16),
        "weapon_hall": ("door", "weapon_hall"),
        "library": ("door", "library"),
    },
    spawn=(3, 16),
    anchors={
        "npc_cloud_hall_master": (10, 15), "npc_arena_cm": (47, 20), "dummy_cs_0": (5, 16), "dummy_cs_1": (7, 16),
        "spar_cm": (35, 19), "temper_jade_cm_sword_court": (41, 20),
    },
    pins={"props": [   # hand-placed, piece by piece
        ("hall", 16, 5, "weapon_hall"), ("hall", 24, 5, "library"),
        # onto the Sword Hall's roof
        ("crates", 32, 7), ("post", 50, 17), ("post", 52, 18), ("post", 54, 17), ("post", 56, 18),
        ("banner_cloud", 15, 9), ("banner_cloud", 32, 9), ("pine", 4, 1), ("pine", 37, 1), ("pine", 48, 2),
        ("boulder", 8, 25), ("boulder", 22, 26), ("boulder", 40, 25), ("bamboo", 56, 24), ("bamboo", 57, 25),
        ("tree_pine", 6, 6), ("tree_pine", 40, 5), ("tree_maple", 47, 6), ("bush", 12, 8), ("bush_wide", 34, 4),
        ("tree_pine", 14, 28), ("tree_plum", 31, 28), ("tree_pine", 47, 28), ("bush", 1, 24), ("tall_grass", 24, 28),
        ("bush_azalea", 37, 27), ("rock_small", 53, 28),
    ]})


# The Array Court: the array dais a step up in the middle with the formation elder at her table and a stone lantern
# at each corner (the formation's nodes), the physician, the monastery furnace, the rope ledge against the cliff, the
# Retreat Rooms, the garden beds with the gardener, and the gorge path up to Elder Sung's peak.
CM_ARRAY_COURT = room(
    "cm_array_court", size=(60, 30),
    bands=[
        ("rock", 0, 3, dict(level=4, paint="r")),
        ("paving", 10, 13, dict(level=0, paint="p")),
    ],
    features=[
        ("array_dais", (20, 12, 15, 5), dict(level=1, paint="s")),  # the array dais
        ("rope_ledge", (40, 3, 7, 6), dict(level=2, paint="r")),  # the rope ledge
        ("step", (41, 9, 2, 1), dict(level=1, paint="r")),  # a step up to it
        ("gorge_path", (57, 0, 3, 10), dict(level=0, paint="d")),  # the gorge path to the peak
        ("garden_beds", (4, 24, 14, 3), dict(level=0, paint="d")),  # the garden's beds
        ("flowers", (3, 23, 16, 1), dict(level=0, paint="f")),
    ],
    stairs=[(26, 17, 3, 1, 0, 1)],
    paths=[("retreat", 10, "p")],
    ways={
        "west": ("w", 16),
        "east": ("e", 16),
        "peak_path": ("n", 58),
        "retreat": ("door", "retreat"),
    },
    spawn=(3, 16),
    anchors={
        "npc_cloud_formation_elder": (26, 13), "formation_table_cm": (29, 14), "npc_cloud_physician": (38, 18),
        "furnace_cm": (45, 12), "bed_cm_0": (7, 25), "bed_cm_1": (10, 25), "bed_cm_2": (13, 25),
        "npc_cloud_gardener": (16, 21),
    },
    pins={"props": [   # hand-placed, piece by piece
        ("lantern", 20, 12), ("lantern", 34, 12), ("lantern", 20, 16), ("lantern", 34, 16),
        ("hall", 48, 5, "retreat"), ("banner_cloud", 19, 21), ("banner_cloud", 34, 21), ("pine", 6, 1),
        ("pine", 30, 1), ("bamboo", 2, 20), ("bamboo", 24, 26), ("bamboo", 44, 25), ("bamboo", 53, 26),
        ("boulder", 38, 5), ("tree_pine", 8, 6), ("tree_maple", 18, 5), ("tree_plum", 28, 6), ("bush", 35, 8),
        ("bamboo_grove", 0, 4), ("tree_pine", 30, 28), ("tree_camphor", 40, 28), ("tree_peach", 49, 28),
        ("bush_wide", 20, 26), ("tall_grass", 35, 26), ("bush_azalea", 56, 24),
    ]})


# Elder Sung's Peak: the summit crags over a mountain tarn; the west ledge and the west peak, the rope bridge along
# the tarn's edge to the far peak where Elder Sung stands; below, the Qi spring, the insight stone, the Heart Trial's
# circle and the treasure plot on the meadow; the pagoda at his cave abode's door; the path back down.
CM_ELDER_SUNG_PEAK = room(
    "cm_elder_sung_peak", size=(40, 28),
    bands=[
        ("crags", 0, 2, dict(level=6, paint="r")),  # the summit crags
    ],
    features=[
        ("tarn", (10, 2, 18, 5), dict(water=True)),  # the tarn
        ("stream_out", (10, 9, 18, 2), dict(water=True)),  # the stream out of it, under the bridge's south side
        ("west_ledge", (5, 11, 5, 3), dict(level=1, paint="r")),  # the west ledge
        ("west_peak", (5, 2, 5, 9), dict(level=2, paint="r")),  # the west peak
        ("rope_bridge", (10, 7, 18, 2), dict(level=2, paint="w")),  # the rope bridge
        ("far_peak", (28, 2, 7, 8), dict(level=3, paint="r")),  # the far peak
        ("rock", (35, 2, 5, 10), dict(level=4, paint="r")),
        ("path_down", (5, 15, 2, 13), dict(paint="d")),  # the path down
    ],
    paths=[("abode", 20)],
    ways={"path": ("s", 5.5, dict(arrive=1.5, span=2)), "abode": ("door", "abode")},
    spawn=(6, 24),
    anchors={
        "npc_elder_sung": (31, 5),  # on the far peak
        "array_cm_peak": (11, 26),  # decision 42: the peak's transfer array, beside the path's head
        "spring_sung": (12, 18), "insight_sung": (22, 15), "rite_reflection_cm": (18, 21), "plot_sung": (8, 20),
    },
    ground={"snow": [(0, 0, 40, 2), (35, 2, 5, 7), (28, 2, 7, 2)]},
    pins={"props": [   # hand-placed, piece by piece
        ("storehouse", 33, 13, "abode"), ("lotus", 12, 4), ("lotus", 20, 3), ("lotus", 16, 9), ("lotus", 23, 10),
        ("incense", 14, 16), ("pine", 2, 12), ("pine", 29, 21), ("pine", 37, 18), ("pine", 9, 24), ("boulder", 2, 17),
        ("boulder", 26, 13), ("boulder", 19, 25), ("boulder", 36, 25), ("tree_pine", 15, 26), ("tree_plum", 33, 24),
        ("tree_maple", 25, 22), ("rock_mossy", 24, 18), ("tall_grass", 10, 14), ("tall_grass", 28, 26),
        ("ferns", 20, 13), ("bush", 1, 20), ("rock_small", 16, 11), ("cattails", 11, 10), ("lotus_pads", 20, 5),
    ]})


CM_WEAPON_HALL = weapon_hall("cm_weapon_hall", "banner_cloud", "npc_cloud_weapon_master", "npc_cloud_smith", "anvil_cm",
                             ["dummy_cwh_0", "dummy_cwh_1"])


ROOMS = [CM_CLIFF_STAIR, CM_SWORD_COURT, CM_WEAPON_HALL, CM_ARRAY_COURT, CM_ELDER_SUNG_PEAK]
