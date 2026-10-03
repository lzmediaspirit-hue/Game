"""E1 room specs: Stoneford: the gate, Market Street, Artisan Row and the Fairground (docs/architecture/room_engine.md).

Migrated from tools/data/topdown_rooms.py's hand functions; each compiles to its layout byte for byte. The
terrain, the ways, the door paths and the doorways are the engine's; the props and the foliage were placed by
hand, piece by piece, and stay pinned (no rule reproduces them)."""
from content.rooms.spec import room
from content.rooms.specs.shared import trial_yard


# Stoneford Gate: the paved street in from the Willow Path under the town wall, the gap in the wall where the
# Quarry Road climbs north, the County Hall's door, the gate guard, and a canal along the south.
SF_GATE = room(
    "sf_gate", size=(56, 26),
    bands=[
        ("town_wall", 0, 4, dict(level=3, paint="l")),  # the town wall
        ("canal", 22, 4, dict(water=True)),  # the canal
    ],
    features=[
        ("quarry_road", (15, 0, 3, 4), dict(level=0, paint="d")),  # the Quarry Road through it
        ("path", (15, 4, 3, 9), dict(paint="d")),
        ("street", (0, 12, 56, 5), dict(level=0, paint="p")),  # the street
    ],
    ways={
        "east": ("e", 14),
        "west": ("w", 14),
        "quarry_road": ("n", 16, dict(arrive=3)),
        "county_hall_door": ("door", "county_hall"),
    },
    spawn=(52, 14),
    anchors={
        "shrine_sf_gate": (43, 11), "sign_sf_gate": (52, 17), "npc_guard_hou": (29, 11), "npc_foreman_dong": (13, 10),
        "npc_adventurer_kai": (37, 18), "tide_gong": (22, 10),
    },
    pins={"props": [   # hand-placed, piece by piece
        # the County Hall
        ("house", 46, 6, "county_hall"), ("lantern", 14, 4), ("lantern", 18, 4), ("lantern_red", 26, 11),
        ("lantern_red", 32, 11), ("willow", 6, 6), ("willow", 36, 6), ("barrel", 40, 8), ("crates", 8, 18),
        ("reeds", 4, 21), ("reeds", 20, 21), ("reeds", 34, 21), ("reeds", 50, 21), ("tree_camphor", 25, 7),
        ("tree_maple", 3, 8), ("bamboo_grove", 41, 4), ("bush_wide", 9, 5), ("bush", 20, 5), ("hedge_3", 30, 6),
        ("bush_azalea", 53, 8), ("bush", 34, 9), ("bush", 1, 5), ("tree_willow", 8, 20), ("tree_willow", 19, 20),
        ("tree_willow", 44, 20), ("bush_azalea", 25, 18), ("bush", 31, 19), ("tall_grass", 12, 20),
        ("tall_grass", 35, 20), ("rock_small", 49, 19), ("cattails", 12, 22), ("cattails", 28, 22),
        ("cattails", 40, 22), ("cattails", 52, 22),
    ]})


# Market Street: the stalls and the teleport stone on the paved street, three houses in a row whose roofs the
# rooftop thief runs over (crates at the west end, a tile's jump between each), the notice boards, and the arch
# north to the Beast Trial Grove.
SF_MARKET = room(
    "sf_market", size=(56, 28),
    bands=[
        ("rock", 0, 3, dict(level=2, paint="r")),
        ("street", 12, 9, dict(level=0, paint="p")),  # the street and the square round the stone
        ("water", 24, 4, dict(water=True)),
    ],
    features=[
        ("grove_path", (49, 0, 3, 12), dict(paint="d")),  # the path to the Grove's arch
        ("path", (49, 0, 3, 3), dict(level=0, paint="d")),
    ],
    ways={"east": ("e", 16), "west": ("w", 16), "grove": ("n", 50)},
    spawn=(52, 16),
    anchors={
        "stone_sf": (37, 18), "board_sf": (20, 13), "arena_sf": (46, 13), "auction_sf": (16, 19),
        "storage_sf": (27, 13), "exchange_sf": (54, 13), "npc_storekeeper_fang": (13, 13),
        "npc_auntie_rong": (32, 13), "npc_keeper_shi": (41, 13), "npc_courier_lin": (47, 19),
        "npc_tailor_xun": (26, 18), "npc_adventurer_su": (6, 18), "npc_old_pan": (54, 19),
        "board_sf_tower": (20, 7),  # up on the third roof
        "gutter_shard": (13, 7),  # in the second roof's gutter
        "thief_sf": (9, 13),
    },
    routes=dict(thief_sf=[[9, 13, 0.0], [2, 10, 0.6], [5, 8, 0.5], [9, 8, 0.4], [11, 8, 0.4], [16, 8, 0.5], [18, 8, 0.4],
                          [22, 8, 0.5]]),
    pins={"props": [   # hand-placed, piece by piece
        ("house", 3, 7), ("house", 10, 7), ("house", 17, 7),
        # the way onto the first roof
        ("crates", 1, 9), ("storehouse", 26, 7), ("storehouse", 38, 7), ("crates", 12, 22), ("crates", 22, 22),
        ("crates", 30, 22), ("crates", 44, 22), ("barrel", 24, 12), ("barrel", 36, 12), ("lantern_red", 48, 12),
        ("lantern_red", 52, 12), ("willow", 33, 4), ("willow", 45, 4), ("tree_camphor", 7, 4), ("tree_plum", 24, 4),
        ("tree_maple", 38, 4), ("tree_peach", 55, 6), ("bush", 16, 5), ("bush_azalea", 1, 5), ("bush", 30, 5),
        ("bush_wide", 42, 9), ("bush", 23, 10), ("bush_azalea", 35, 10), ("bush", 2, 22), ("bush_azalea", 9, 22),
        ("bush", 18, 23), ("tall_grass", 26, 23), ("bush_wide", 34, 22), ("bush", 41, 23), ("bush_azalea", 50, 22),
        ("cattails", 5, 24), ("cattails", 20, 24), ("cattails", 37, 24), ("cattails", 53, 24),
    ]})


# Artisan Row: the forge at the west end, the tinkers and scribes along the paved street, Elder Gu's warehouse
# with its door, the guild hall's board at the east end, a house whose roof hides the tinkerer's lost gear.
SF_ARTISAN_ROW = room(
    "sf_artisan_row", size=(56, 28),
    bands=[
        ("rock", 0, 3, dict(level=2, paint="r")),
        ("paving", 12, 7, dict(level=0, paint="p")),
        ("water", 24, 4, dict(water=True)),
    ],
    ways={"east": ("e", 15), "west": ("w", 15), "warehouse_door": ("door", "warehouse")},
    spawn=(52, 15),
    anchors={
        "anvil_sf": (16, 13), "furnace_sf": (52, 12), "npc_smith_bao": (13, 13), "npc_tinkerer_yu": (21, 17),
        "npc_old_scribe_bai": (42, 17), "npc_elder_gu": (27, 13), "npc_madam_hua": (29, 17), "npc_mei_qing": (48, 17),
        "npc_apprentice_tao": (37, 17), "npc_array_master_ren": (34, 13), "npc_guildmaster_tang": (53, 17),
        "guild_board": (54, 13), "tinkerers_gear": (43, 5), "crate_1": (18, 12), "crate_2": (19, 13),
    },
    pins={"props": [   # hand-placed, piece by piece
        # the smithy
        ("house", 6, 6),
        # Gu's warehouse
        ("storehouse", 30, 6, "warehouse"), ("house", 40, 5),
        # the way onto that roof
        ("crates", 38, 7),
        # the guild hall
        ("house", 47, 6), ("barrel", 14, 11), ("barrel", 15, 11), ("lantern", 25, 11), ("lantern", 36, 11),
        ("willow", 22, 4), ("reeds", 8, 23), ("reeds", 26, 23), ("reeds", 44, 23), ("tree_maple", 17, 9),
        ("tree_plum", 26, 9), ("tree_camphor", 2, 8), ("bush", 13, 10), ("bush_azalea", 36, 10), ("bush", 54, 10),
        ("bush_wide", 20, 5), ("tree_willow", 5, 23), ("tree_camphor", 16, 23), ("tree_willow", 30, 23),
        ("tree_peach", 41, 23), ("tree_willow", 51, 23), ("bush", 10, 21), ("tall_grass", 22, 21),
        ("bush_azalea", 36, 20), ("tall_grass", 46, 21), ("rock_small", 26, 20), ("cattails", 12, 24),
        ("cattails", 34, 24), ("cattails", 47, 24),
    ]})


# Stoneford Fairground: the two recruiters on their stages, the Jade and Cloud trial halls and the Trial Tower
# along the north side (lanterns strung on their roofs), the sect roads leaving north, Shen Lian's spar post and the
# stalls, the Caravan Road barred to the west.
SF_FAIRGROUND = room(
    "sf_fairground", size=(72, 30),
    bands=[
        ("rock", 0, 3, dict(level=2, paint="r")),
        ("fair", 13, 9, dict(level=0, paint="p")),  # the fair
        ("water", 26, 4, dict(water=True)),
    ],
    features=[
        ("jade_road", (7, 0, 3, 13), dict(paint="d")),  # the road to the Jade Sect
        ("path", (7, 0, 3, 3), dict(level=0, paint="d")),
        ("cloud_road", (43, 0, 3, 13), dict(paint="d")),  # the stair road to the Cloud Sect
        ("path_2", (43, 0, 3, 3), dict(level=0, paint="d")),
        ("stage_qing_lan", (15, 11, 6, 2), dict(level=1, paint="w")),  # Qing Lan's stage
        ("stage_mo_yun", (31, 11, 6, 2), dict(level=1, paint="w")),  # Mo Yun's stage
    ],
    stairs=[(17, 13, 2, 1, 0, 1, "w"), (33, 13, 2, 1, 0, 1, "w")],
    ways={
        "east": ("e", 17),
        "west": ("w", 17),
        "trial_jade": ("door", "trial_jade"),
        "tower": ("door", "tower"),
        "trial_cloud": ("door", "trial_cloud"),
        "jade_road": ("n", 8, dict(arrive=3)),
        "cloud_road": ("n", 44, dict(arrive=3)),
    },
    spawn=(68, 17),
    anchors={
        "npc_recruiter_qing_lan": (18, 11), "npc_recruiter_mo_yun": (34, 11), "npc_shen_lian": (49, 17),
        "npc_wen_zhao": (57, 16), "npc_fair_vendor_he": (41, 18), "npc_adventurer_rui": (62, 18), "spar_sf": (53, 18),
        "tower_board_sf": (30, 12),
        "fair_lantern_0": (28, 6),  # on the tower's roof
        "fair_lantern_1": (16, 6),  # on the Jade hall's roof
        "fair_lantern_2": (35, 6),  # on the Cloud hall's roof, a tile's jump from the tower's
    },
    pins={"props": [   # hand-placed, piece by piece
        # the Jade trial hall
        ("house", 13, 6, "trial_jade"),
        # the Trial Tower
        ("storehouse", 26, 6, "tower"),
        # the Cloud trial hall
        ("house", 31, 6, "trial_cloud"),
        # onto the Jade hall's roof
        ("crates", 19, 8),
        # onto the tower's roof
        ("crates", 24, 8), ("lantern_red", 12, 12), ("lantern_red", 22, 12), ("lantern_red", 38, 12),
        ("lantern_red", 50, 12), ("lantern_red", 60, 12), ("willow", 3, 5), ("willow", 56, 5), ("bamboo", 64, 4),
        ("bamboo", 66, 5), ("crates", 40, 22), ("barrel", 47, 22), ("reeds", 5, 25), ("reeds", 25, 25),
        ("reeds", 45, 25), ("reeds", 65, 25), ("tree_ribbons", 60, 9), ("tree_camphor", 51, 6), ("tree_peach", 69, 8),
        ("tree_camphor", 2, 9), ("bush", 11, 10), ("bush_azalea", 38, 9), ("bush_wide", 47, 11), ("bush", 23, 11),
        ("bush_azalea", 70, 4), ("tree_willow", 6, 25), ("tree_willow", 22, 25), ("tree_camphor", 36, 25),
        ("tree_willow", 55, 25), ("tree_peach", 66, 24), ("bush", 14, 23), ("tall_grass", 29, 23),
        ("bush_azalea", 44, 24), ("tall_grass", 60, 23), ("cattails", 12, 26), ("cattails", 32, 26),
        ("cattails", 49, 26), ("cattails", 63, 26),
    ]})


# The Jade Sect's Entry Trial: the climb to the trial bell runs over three roofs along the north wall (crates onto the
# first roof, a tile's running jump to the second and up its ridge, another jump to the third) and up onto the bell
# tower's top; racks of training weapons stand along the east wall.
SF_TRIAL_JADE = trial_yard(
    "sf_trial_jade", "banner_jade",
    features=[
        ("roof_1", (3, 5, 7, 4), dict(level=2, paint="t")),        # the first roof (x 3-9, y 5-8)
        ("roof_2", (11, 3, 7, 6), dict(level=2, paint="t")),       # the second roof, a tile's jump east
        ("ridge", (15, 3, 3, 3), dict(level=3, paint="t")),        # its ridge, a level up
        ("roof_3", (19, 2, 6, 5), dict(level=3, paint="t")),       # the third roof, a tile's jump from the ridge
        ("bell_tower", (25, 1, 4, 5), dict(level=4, paint="s")),   # the bell tower's top
    ],
    props=[("crates", 5, 9), ("weapon_rack", 31, 1), ("weapon_rack", 34, 1)],   # crates onto the first roof
    bell=(26.5, 3))


# The Cloud Sect's Entry Trial: the climb runs up rock ledges out of the cliff behind the yard (the first ledge, the
# one above it, a plank walk over the cliff pool a tile's jump across, and the top ledge where the bell hangs).
SF_TRIAL_CLOUD = trial_yard(
    "sf_trial_cloud", "banner_cloud",
    features=[
        ("cliff", (1, 1, 38, 2), dict(level=5, paint="r")),        # the cliff behind the yard
        ("ledge_1", (6, 9, 6, 3), dict(level=1, paint="r")),       # the first ledge (x 6-11, y 9-11)
        ("ledge_2", (6, 3, 6, 6), dict(level=2, paint="r")),       # the ledge above it
        ("pool", (12, 3, 6, 6), dict(water=True)),                 # the cliff pool (x 12-17, y 3-8)
        ("planks", (13, 5, 5, 2), dict(level=2, paint="w")),       # the plank walk over it, a jump from the ledge
        ("top_ledge", (18, 3, 7, 5), dict(level=3, paint="r")),
    ],
    props=[("lotus", 14, 8), ("boulder", 30, 4), ("boulder", 4, 13)],
    bell=(22, 4))


ROOMS = [SF_GATE, SF_MARKET, SF_ARTISAN_ROW, SF_FAIRGROUND, SF_TRIAL_JADE, SF_TRIAL_CLOUD]
