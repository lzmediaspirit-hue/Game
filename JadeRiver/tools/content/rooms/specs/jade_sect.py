"""E1 room specs: the Jade Sect's grounds, Gate Street, the training yard, the East Terrace, the Herb Terraces, Elder
Hu's peak (docs/architecture/room_engine.md).

Migrated from tools/data/topdown_rooms.py's hand functions; each compiles to its layout byte for byte. The
terrain, the ways, the door paths and the doorways are the engine's; the props and the foliage were placed by
hand, piece by piece, and stay pinned (no rule reproduces them)."""
from content.rooms.spec import room
from content.rooms.specs.shared import weapon_hall


# Gate Street, the Jade Sect's front: the road up from Stoneford through the sect's banners onto the plaza inside
# the gate (the steward, the teleport stone, the shrine); the three halls in a row on rising terraces, the Weapon
# Hall, the Alchemy Hall and the Library, their roofs a level apart (the rooftop thief's run from the crates, the
# chest on the Library's roof); the service dorm and its sleeping porch; the notice board and the deacon by the way
# east to the Pavilion Rooftops; a scholar's garden pond; and the mountain behind.
JA_GATE_STREET = room(
    "ja_gate_street", size=(64, 32),
    bands=[
        ("mountain", 0, 3, dict(level=3, paint="r")),  # the mountain behind the sect
        ("gate_street", 12, 7, dict(level=0, paint="p")),  # Gate Street
    ],
    features=[
        ("plaza", (3, 19, 14, 4), dict(level=0, paint="p")),  # the plaza inside the gate
        ("road", (8, 23, 3, 9), dict(paint="d")),  # the road up from Stoneford
        ("alchemy_terrace", (22, 4, 8, 8), dict(level=1, paint="s")),  # the Alchemy Hall's terrace
        ("library_terrace", (30, 3, 8, 9), dict(level=2, paint="s")),  # the Library's terrace
        ("porch", (42, 9, 6, 2), dict(level=0, paint="w")),  # its sleeping porch
        ("pond", (44, 24, 12, 5), dict(water=True)),  # the scholar's pond
        ("path", (11, 26, 33, 2), dict(paint="d")),
        ("flowers", (19, 22, 5, 2), dict(level=0, paint="f")),
        ("flowers_2", (30, 22, 6, 2), dict(level=0, paint="f")),
        ("flowers_3", (22, 29, 7, 2), dict(level=0, paint="f")),
        ("flowers_4", (36, 29, 5, 2), dict(level=0, paint="f")),
    ],
    stairs=[(25, 10, 2, 2, 0, 1), (33, 8, 2, 4, 0, 2)],
    paths=[("weapon_hall", 12, "p")],
    ways={
        "stoneford": ("s", 9),
        "east": ("e", 15),
        "weapon_hall": ("door", "weapon_hall"),
        "alchemy_hall": ("door", "alchemy_hall"),
        "library": ("door", "library"),
    },
    spawn=(9, 27),
    anchors={
        "shrine_ja": (4.5, 13), "stone_ja": (13, 20),
        "array_ja_gate": (8, 21),  # decision 42: the transfer array at the head of the road, by the steward
        "board_ja": (60, 13), "siege_gong_ja": (54, 17), "npc_jade_steward": (7, 16), "npc_jade_deacon": (57, 15),
        "npc_jade_disciple_a": (29, 15), "npc_jade_disciple_b": (40, 17), "dorm_bed_ja": (46, 10),
        "sweep_ja_0": (20, 15), "sweep_ja_1": (27, 17),
        "sweep_ja_2": (11, 22),  # the grey stain by the gate
        "chest_mission_hall": (35, 5),  # on the Library's roof
        "thief_ja": (15, 14),
    },
    routes=dict(thief_ja=[[15, 14, 0.0], [12.5, 8, 0.6], [15.5, 7, 0.5], [20.5, 7, 0.6], [23.5, 6, 0.5], [28.5, 6, 0.6],
                          [31.5, 5, 0.5], [36.5, 5, 0.6]]),
    pins={"props": [   # hand-placed, piece by piece
        # the Weapon Hall (roof 2)
        ("hall", 14, 6, "weapon_hall"),
        # the Alchemy Hall (roof 3), a hop up from the Weapon Hall's
        ("hall", 22, 5, "alchemy_hall"),
        # the Library (roof 4), a hop up again
        ("hall", 30, 4, "library"),
        # onto the Weapon Hall's roof
        ("crates", 12, 8),
        # the service dorm
        ("house", 42, 6), ("lotus", 46, 25), ("lotus", 51, 26), ("boulder", 27, 23), ("boulder", 28, 24),
        ("boulder", 38, 23), ("boulder", 41, 29), ("pine", 17, 29), ("pine", 33, 21), ("pine", 1, 5), ("pine", 10, 4),
        ("shrub", 24, 23), ("shrub", 35, 24), ("shrub", 30, 29), ("shrub", 52, 5), ("shrub", 54, 6),
        ("lantern", 16, 10), ("lantern", 19, 10), ("lantern", 2, 11), ("lantern", 7, 11), ("banner_jade", 7, 24),
        ("banner_jade", 11, 24), ("lantern_red", 7, 28), ("lantern_red", 11, 28), ("pine", 4, 2), ("pine", 20, 1),
        ("pine", 45, 1), ("pine", 56, 2), ("bamboo", 57, 9), ("bamboo", 59, 10), ("bamboo", 58, 22),
        ("willow", 42, 23), ("boulder", 3, 21), ("shrub", 49, 10), ("shrub", 38, 13), ("tree_pine", 5, 8),
        ("tree_plum", 61, 6), ("tree_pine", 50, 4), ("bush_wide", 38, 4), ("bush", 13, 10), ("bush_azalea", 55, 10),
        ("tree_plum", 18, 25), ("tree_pine", 1, 25), ("tree_maple", 39, 29), ("tree_willow", 57, 28),
        ("tree_peach", 26, 31), ("bamboo_grove", 61, 25), ("tree_camphor", 3, 31), ("hedge_3", 13, 28),
        ("hedge_2", 33, 28), ("bush_azalea", 43, 23), ("bush", 25, 24), ("rock_small", 21, 30),
        ("tall_grass", 46, 30), ("ferns", 30, 25), ("lotus_pads", 49, 27), ("cattails", 44, 26),
    ]})


# The Pavilion Rooftops, the Jade Sect's training yard: the yard with its dummies, the hall master and the sparring
# post in a sand ring; the courtyard pine in a raised bed with a herb pot beside it; three pavilions in a row rising a
# level each (crates, the East Entry's roof, the East Step's, and the great Heaven Pavilion's, where the Retreat
# Rooms open and a chest waits); the rear stairs up to the east terrace under the plum shrubs, where crates give a
# second way onto the Heaven Pavilion; a lotus pond; and the mountain behind.
JA_PAVILION_ROOFTOPS = room(
    "ja_pavilion_rooftops", size=(60, 30),
    bands=[
        ("rock", 0, 3, dict(level=3, paint="r")),
        ("training_yard", 11, 12, dict(level=0, paint="p")),  # the training yard
    ],
    features=[
        ("sparring_ring", (22, 15, 10, 6), dict(level=0, paint="d")),  # the sparring ring
        ("pine_bed", (3, 7, 5, 4), dict(level=2, paint="b")),  # the courtyard pine's raised bed
        ("step", (3, 11, 5, 1), dict(level=1, paint="s")),  # its step
        ("east_step_terrace", (22, 4, 8, 7), dict(level=1, paint="s")),  # the East Step's terrace
        ("heaven_pavilion", (30, 3, 12, 7), dict(level=4, paint="t")),  # built on the grid (roof 4)
        ("east_terrace", (42, 4, 14, 6), dict(level=2, paint="s")),  # the east terrace
        ("lotus_pond", (8, 25, 12, 4), dict(water=True)),  # the lotus pond
        ("flowers", (24, 23, 6, 2), dict(level=0, paint="f")),  # flower beds along the yard's south side
        ("flowers_2", (40, 24, 8, 2), dict(level=0, paint="f")),  # flower beds along the yard's south side
    ],
    stairs=[
        (25, 9, 2, 2, 0, 1),
        (48, 10, 3, 4, 0, 2),  # the rear stairs
    ],
    ways={"west": ("w", 16), "east": ("e", 16), "retreat_roof": ("door", "retreat_roof")},
    spawn=(3, 16),
    anchors={
        "roof_chest": (39, 7),  # on the Heaven Pavilion's roof
        "npc_jade_hall_master": (15, 18), "npc_jade_wm_yard": (20, 20), "dummy_jp_0": (8, 16), "dummy_jp_1": (11, 16),
        "spar_jp": (26, 18),
        "herb_pot_pine": (6, 8),  # in the pine's raised bed
    },
    pins={"props": [   # hand-placed, piece by piece
        ("pine", 4, 8),
        # the East Entry (roof 2)
        ("hall", 14, 6),
        # the East Step (roof 3)
        ("hall", 22, 5),
        # the Retreat Rooms' door on its roof
        ("storehouse", 34, 3, "retreat_roof"),
        # up onto the East Entry's roof
        ("crates", 12, 8),
        # from the terrace onto the Heaven Pavilion
        ("crates", 42, 5), ("shrub", 47, 5), ("shrub", 52, 7), ("shrub", 54, 5), ("lotus", 10, 26), ("lotus", 15, 27),
        ("willow", 21, 24), ("banner_jade", 30, 11), ("banner_jade", 41, 11), ("lantern", 13, 11),
        ("lantern", 46, 13), ("lantern", 52, 13), ("pine", 6, 1), ("pine", 24, 1), ("pine", 50, 2),
        ("bamboo", 56, 23), ("bamboo", 58, 24), ("bamboo", 3, 24), ("tree_pine", 10, 5), ("bush", 1, 5),
        ("bush_azalea", 8, 9), ("tree_plum", 56, 6), ("tree_plum", 27, 27), ("tree_maple", 36, 28),
        ("tree_pine", 46, 28), ("tree_peach", 52, 27), ("tree_willow", 6, 28), ("bush_wide", 32, 24),
        ("bush", 22, 26), ("bush_azalea", 49, 24), ("tall_grass", 40, 27), ("rock_mossy", 20, 28),
        ("lotus_pads", 12, 25), ("cattails", 19, 25),
    ]})


# The East Terrace: the Mission Hall with its row of training stumps and the Temper drum, the formation elder at
# her table, the physician, the arena master and his sparring post, the abode terrace up its stairs against the cliff
# (a cave abode's door between stone lanterns), the Retreat Rooms, and the cliff with its pines behind.
JA_EAST_TERRACE = room(
    "ja_east_terrace", size=(60, 30),
    bands=[
        ("cliff", 0, 4, dict(level=5, paint="r")),  # the cliff the abodes are cut into
        ("paving", 11, 12, dict(level=0, paint="p")),
    ],
    features=[
        ("abode_terrace", (24, 4, 17, 5), dict(level=2, paint="s")),  # the abode terrace
        ("flowers", (14, 24, 8, 2), dict(level=0, paint="f")),
        ("flowers_2", (38, 24, 7, 2), dict(level=0, paint="f")),
    ],
    stairs=[(31, 9, 3, 4, 0, 2)],
    paths=[("retreat", 11, "p")],
    ways={
        "west": ("w", 16),
        "east": ("e", 16),
        "abode": ("door", "abode"),
        "retreat": ("door", "retreat"),
    },
    spawn=(3, 16),
    anchors={
        "npc_jade_formation_elder": (22, 14), "npc_jade_physician": (34, 17), "npc_arena_master": (48, 15),
        "formation_table_ja": (19, 16), "arena_ja": (53, 18), "temper_jade_ja_east_terrace": (16, 17),
    },
    pins={"props": [   # hand-placed, piece by piece
        # the Mission Hall
        ("hall", 5, 6),
        # a step up onto its roof
        ("crates", 13, 8),
        # training stumps
        ("post", 5, 12),
        # training stumps
        ("post", 7, 13),
        # training stumps
        ("post", 9, 12),
        # training stumps
        ("post", 11, 13),
        # training stumps
        ("post", 13, 12),
        # training stumps
        ("post", 15, 13),
        # a cave abode's door, against the cliff
        ("storehouse", 34, 4, "abode"), ("lantern", 25, 7), ("lantern", 39, 7),
        # the Retreat Rooms
        ("hall", 45, 6, "retreat"), ("banner_jade", 29, 11), ("banner_jade", 36, 11), ("pine", 8, 2), ("pine", 20, 1),
        ("pine", 50, 2), ("bamboo", 56, 9), ("bamboo", 57, 10), ("bamboo", 2, 24), ("shrub", 20, 25),
        ("shrub", 33, 26), ("shrub", 46, 25), ("willow", 27, 23), ("tree_camphor", 18, 7), ("tree_plum", 54, 5),
        ("bush", 42, 7), ("bush_azalea", 1, 9), ("bush", 22, 9), ("tree_pine", 6, 27), ("tree_maple", 12, 28),
        ("tree_camphor", 29, 28), ("tree_plum", 38, 27), ("tree_peach", 50, 27), ("tree_pine", 57, 26),
        ("bush", 23, 24), ("bush_wide", 45, 24), ("tall_grass", 16, 27), ("rock_mossy", 33, 29),
    ]})


# The Herb Terraces: three green terraces stepping up the hillside on grassy banks, a garden bed and herbs on each
# and stairs between them, the gardener at their foot among the bamboo, and the stone stair up through the crags to
# Elder Hu's peak between two lanterns.
JA_HERB_TERRACES = room(
    "ja_herb_terraces", size=(56, 30),
    bands=[
        ("crags", 0, 2, dict(level=5, paint="r")),  # the crags
        ("foot_path", 23, 3, dict(paint="d")),  # the path along the terraces' foot
    ],
    features=[
        ("terrace_1", (8, 15, 32, 5), dict(level=1, paint="g")),  # the first terrace
        ("terrace_2", (8, 9, 32, 6), dict(level=2, paint="g")),  # the second
        ("terrace_3", (8, 2, 32, 7), dict(level=3, paint="g")),  # the third
        ("terrace_path", (10, 16, 28, 2), dict(level=1, paint="d")),  # a path along each terrace
        ("terrace_path_2", (10, 11, 28, 2), dict(level=2, paint="d")),  # a path along each terrace
        ("terrace_path_3", (10, 4, 28, 2), dict(level=3, paint="d")),  # a path along each terrace
        ("peak_stair_head", (44, 0, 3, 9), dict(level=3, paint="s")),  # the peak stair's head, through the crags
        ("path", (44, 15, 3, 8), dict(paint="d")),
    ],
    # S12c: the flight up to the second terrace stands below its edge (its top row beside the first terrace, a step down
    # either side), not cut into it: a body leaving its top row sideways meets no floor a full step up (room_sweep).
    stairs=[(12, 18, 2, 2, 0, 1), (22, 15, 2, 2, 1, 2), (32, 7, 2, 2, 2, 3), (44, 9, 3, 6, 0, 3)],
    ways={"west": ("w", 24), "peak_path": ("n", 45)},
    spawn=(3, 24),
    anchors={
        "bed_0": (18, 17), "bed_1": (28, 12), "bed_2": (36, 6), "herb_1": (11, 17), "herb_2": (30, 5),
        "npc_jade_gardener": (20, 24),
    },
    pins={"props": [   # hand-placed, piece by piece
        ("lantern", 43, 14), ("lantern", 47, 14), ("bamboo", 3, 19), ("bamboo", 4, 21), ("bamboo", 50, 20),
        ("bamboo", 52, 25), ("shrub", 14, 5), ("shrub", 26, 3), ("shrub", 18, 12), ("shrub", 35, 13),
        ("shrub", 28, 17), ("pine", 6, 1), ("pine", 50, 1), ("boulder", 49, 12), ("hedge_3", 15, 19),
        ("hedge_3", 26, 19), ("bush", 36, 19), ("hedge_3", 9, 14), ("bush_azalea", 18, 14), ("hedge_4", 26, 14),
        ("bush", 36, 14), ("hedge_3", 9, 8), ("bush", 20, 8), ("hedge_3", 25, 8), ("bush", 38, 8),
        ("tree_pine", 10, 3), ("tree_plum", 20, 3), ("tree_camphor", 3, 8), ("tree_maple", 4, 14),
        ("tree_pine", 52, 12), ("tree_plum", 51, 5), ("bush", 49, 3), ("tree_pine", 8, 28), ("tree_camphor", 32, 28),
        ("tree_maple", 42, 28), ("tree_peach", 50, 29), ("bush", 26, 27), ("tall_grass", 16, 28),
        ("rock_mossy", 37, 27),
    ]})


# Elder Hu's Peak: a mountain meadow under the summit crags, Elder Hu by the Qi spring, the insight stone, the
# Heart Trial's circle and the treasure plot; rock ledges stepping up to the Meditation Rock; the pagoda at his cave
# abode's door; and the path back down to the Herb Terraces.
JA_ELDER_HU_PEAK = room(
    "ja_elder_hu_peak", size=(40, 26),
    bands=[
        ("crags", 0, 3, dict(level=5, paint="r")),  # the summit crags
    ],
    features=[
        ("rock", (0, 3, 2, 18), dict(level=3, paint="r")),
        ("rock_2", (38, 3, 2, 23), dict(level=3, paint="r")),
        ("ledge_1", (7, 9, 6, 4), dict(level=1, paint="r")),  # the first ledge
        ("ledge_2", (13, 5, 6, 5), dict(level=2, paint="r")),  # the second
        ("meditation_ledge", (19, 3, 7, 5), dict(level=3, paint="r")),  # the Meditation Rock's ledge
        ("path_down", (5, 14, 2, 12), dict(paint="d")),  # the path down
    ],
    paths=[("abode", 12)],
    ways={"path": ("s", 5.5, dict(arrive=1.5, span=2)), "abode": ("door", "abode")},
    spawn=(6, 22),
    anchors={
        "npc_elder_hu": (24, 13),
        "array_ja_peak": (9, 24),  # decision 42: the peak's transfer array, beside the path's head
        "spring_hu": (14, 16), "insight_hu": (30, 12), "rite_reflection": (20, 19), "plot_hu": (9, 18),
        "meditation_rock": (22, 4),
    },
    ground={"snow": [(0, 0, 40, 3), (0, 3, 2, 4), (38, 3, 2, 4), (19, 3, 7, 2)], "snowpack": [(21, 4, 3, 1)]},
    pins={"props": [   # hand-placed, piece by piece
        # the pagoda at the cave abode's door
        ("storehouse", 31, 5, "abode"), ("incense", 16, 15), ("pine", 3, 8), ("pine", 35, 13), ("pine", 27, 22),
        ("pine", 10, 22), ("boulder", 25, 9), ("boulder", 8, 14), ("boulder", 30, 18), ("boulder", 2, 23),
        ("tree_pine", 3, 11), ("tree_plum", 33, 20), ("tree_maple", 15, 22), ("rock_mossy", 27, 16),
        ("rock_small", 12, 12), ("tall_grass", 20, 24), ("tall_grass", 34, 16), ("ferns", 9, 15), ("bush", 36, 23),
        ("ferns", 23, 10),
    ]})


JA_WEAPON_HALL = weapon_hall("ja_weapon_hall", "banner_jade", "npc_jade_weapon_master", "npc_jade_smith", "anvil_ja",
                             ["dummy_wh_0", "dummy_wh_1"])


ROOMS = [JA_GATE_STREET, JA_WEAPON_HALL, JA_PAVILION_ROOFTOPS, JA_EAST_TERRACE, JA_HERB_TERRACES, JA_ELDER_HU_PEAK]


# ==================================================================================================================== R3
# The sect's insides (E1's batch R3): the Alchemy Hall and the Library off Gate Street, the Retreat Rooms off the East
# Terrace (and down from the Heaven Pavilion's roof), the Cave Abode between the terrace and Elder Hu's peak.

# The Alchemy Hall: a granite hall round the sect's bronze furnace on its dais (two lanterns at its back corners, the
# sect's banners behind it), Mei Qing at her drawers of herbs, the recipe shelf up on the loft in the west.
JA_ALCHEMY_HALL = room(
    "ja_alchemy_hall", size=(26, 16), base="s", walls=dict(high=4),
    features=[("loft", (1, 1, 7, 4), dict(level=2, paint="w")),            # the recipe loft
              ("cheek", (4, 5, 1, 4), dict(level=3, paint="w")),           # the flights' cheeks, a level over their heads
              ("cheek_2", (7, 5, 1, 4), dict(level=3, paint="w")),
              ("dais", (10, 4, 6, 4), dict(level=1, paint="p")),           # the furnace's dais
              ("cheek_3", (11, 8, 1, 2), dict(level=2, paint="p")),
              ("cheek_4", (14, 8, 1, 2), dict(level=2, paint="p"))],
    stairs=[(5, 5, 2, 4, 0, 2, "w"), (12, 8, 2, 2, 0, 1, "s")],
    ways={"exit": ("s", 12.5)},
    spawn="exit",
    anchors={"furnace_ja": (12.5, 5), "recipe_shelf": (3.5, 1), "npc_mei_qing_sect": (19, 7)},
    props=[("scroll_shelf", 1, 1), ("scroll_shelf", 5, 1), ("banner_jade", 10, 1), ("banner_jade", 15, 1),
           ("apothecary", 17, 1), ("apothecary", 19, 1), ("cabinet", 22, 1), ("lantern", 10, 4), ("lantern", 15, 4),
           ("drying_rack", 22, 5), ("mortar", 21, 8), ("herb_baskets", 24, 8), ("water_jar", 24, 3), ("sacks", 1, 9),
           ("sacks", 1, 10), ("desk", 4, 11), ("lantern", 1, 13), ("lantern", 24, 13), ("pot_bonsai", 8, 1),
           ("pot_orchid", 24, 11)])


# The Library: shelves of the sect's manuals up two galleries in the west (the middle grade on the first, the deeper
# arts on the second, under the roof), the librarian at her desk below them, reading desks, and the ancestral altar
# before a painted screen in the east, and the shelves of the lower grade in aisles beside it.
JA_LIBRARY = room(
    "ja_library", size=(28, 16), base="s", walls=dict(high=6),
    features=[("gallery", (1, 1, 9, 9), dict(level=2, paint="w")),          # the first gallery
              ("upper_gallery", (1, 1, 9, 3), dict(level=3, paint="w")),   # the second, under the roof
              ("cheek", (6, 4, 1, 2), dict(level=4, paint="w")),           # the flights' cheeks, a level over their heads
              ("cheek_2", (9, 4, 1, 2), dict(level=4, paint="w")),
              ("cheek_3", (6, 10, 1, 4), dict(level=3, paint="w")),
              ("cheek_4", (9, 10, 1, 4), dict(level=3, paint="w"))],
    stairs=[(7, 4, 2, 2, 2, 3, "w"), (7, 10, 2, 4, 0, 2, "w")],
    # T2 (docs/architecture/topdown_mechanics.md): the side view's floor ladders, sealed by sect rank (an Outer Disciple
    # for the first gallery, an Inner Disciple for the second), are sealed hatches over the two flights.
    traverse=[("hatch", "floor_2_ladder", dict(rect=(7, 10, 2, 4))), ("hatch", "floor_3_ladder", dict(rect=(7, 4, 2, 2)))],
    ways={"exit": ("s", 14.5)},
    spawn="exit",
    anchors={"floor_3_shelves": (4, 2), "floor_2_shelves": (4, 5), "npc_jade_librarian": (14, 6),
             "ancestral_altar": (22, 3)},
    props=[("scroll_shelf", 1, 1), ("scroll_shelf", 3, 1), ("scroll_shelf", 5, 1), ("scroll_shelf", 1, 4),
           ("scroll_shelf", 3, 4), ("scroll_shelf", 11, 1), ("scroll_shelf", 13, 1), ("scroll_shelf", 15, 1),
           ("desk", 13, 7), ("desk", 12, 11), ("desk", 16, 11), ("screen", 21, 1), ("incense", 19, 3),
           ("incense", 25, 3), ("banner_jade", 18, 1), ("banner_jade", 26, 1), ("scroll_shelf", 20, 8),
           ("scroll_shelf", 24, 8), ("lantern", 10, 1), ("lantern", 1, 13), ("lantern", 26, 13), ("pot_bonsai", 22, 8),
           ("pot_orchid", 26, 6)])

# The Retreat Rooms: a hushed hall of grey stone, the meditation dais in the middle (the seclusion mat between two
# cushions, painted screens at its back corners), the cedar bath in an alcove of screens in the west, a tea corner in
# the east by the door up to the Heaven Pavilion's roof.
JA_RETREAT = room(
    "ja_retreat", size=(28, 14), base="s", walls=dict(high=4),
    features=[("dais", (9, 1, 10, 6), dict(level=1, paint="w")),           # the meditation dais
              ("cheek", (12, 7, 1, 2), dict(level=2, paint="w")),          # its steps' cheeks, a level over the dais
              ("cheek_2", (15, 7, 1, 2), dict(level=2, paint="w")),
              ("bath_floor", (1, 1, 7, 5), dict(level=0, paint="w"))],     # the bath's boards
    stairs=[(13, 7, 2, 2, 0, 1, "w")],
    ways={"exit": ("s", 8.5), "roof": ("e", 7.5)},
    spawn="exit",
    anchors={"mat_ja_retreat": (13.5, 4), "bath_ja_retreat": (4, 3)},
    props=[("screen", 9, 1), ("screen", 17, 1), ("banner_jade", 11, 1), ("banner_jade", 16, 1), ("incense", 13, 1),
           ("mat", 10, 4), ("mat", 16, 4), ("lantern", 9, 6), ("lantern", 18, 6), ("stove", 1, 1), ("water_jar", 6, 1),
           ("screen", 1, 6), ("screen", 5, 6), ("cabinet", 21, 1), ("scroll_shelf", 23, 1), ("tea_table", 22, 10),
           ("mat", 22, 11), ("lantern", 1, 12), ("lantern", 26, 12), ("pot_bonsai", 26, 1), ("pot_orchid", 20, 6)])


# The Cave Abode: a cavern in the mountain between the East Terrace and Elder Hu's peak, the passage through it from
# one door to the other; the Qi spring by a seep pool, the cedar bath beside it, the treasure plot; the dressed floor
# of the living cave (the seclusion mat on it, the stone bed in its alcove, shelves, a screen); garden beds of dark
# earth in the east.
JA_CAVE_ABODE = room(
    "ja_cave_abode", size=(40, 24), biome="cave", level=4,
    features=[("front", (0, 14, 40, 10), dict(level=1, paint="r")),          # the cave's low front, nothing hidden behind it
              ("cavern", (2, 2, 36, 20), dict(level=0, paint="d", shape="round")),
              ("passage", (0, 11, 40, 3), dict(level=0, paint="d", walk=True)),
              ("hall_floor", (21, 4, 11, 6), dict(level=0, paint="s")),        # the living cave's dressed floor
              ("garden", (27, 15, 9, 4), dict(level=0, paint="g")),            # the abode's garden earth
              ("seep", (7, 14, 8, 5), dict(water=True, shape="round"))],
    ways={"exit": ("w", 12), "terrace": ("e", 12)},
    spawn="exit",
    anchors={"spring_ja_cave_abode": (16, 16), "bath_ja_cave_abode": (20, 17), "plot_ja_cave_abode": (11, 7),
             "mat_ja_cave_abode": (26, 7), "bed_ja_cave_abode": (30, 5), "bed_0_ja_cave_abode": (29, 16),
             "bed_1_ja_cave_abode": (33, 16)},
    props=[("scroll_shelf", 21, 4), ("screen", 23, 4), ("incense", 26, 5), ("lantern", 21, 9), ("lantern", 31, 9),
           ("lantern", 6, 10), ("lantern", 6, 14), ("lantern", 37, 10), ("lantern", 37, 14), ("water_jar", 23, 17),
           ("herb_baskets", 35, 17), ("pot_orchid", 32, 4)],
    flora={"density": 0.18})

ROOMS += [JA_ALCHEMY_HALL, JA_LIBRARY, JA_RETREAT, JA_CAVE_ABODE]   # R3
