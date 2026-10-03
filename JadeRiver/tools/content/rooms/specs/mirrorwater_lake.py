"""E1 room specs (R6): Mirrorwater Lake, reached by the sky-ship from Cloudgate's Skydock (docs/architecture/room_engine.md,
"Act II's first zones (R6)"). Wide still water under the sky, the north shore's willows and maples mirrored in it (a
water band's `mirror`: the engine lays each one's reflection), islands and pale strands, lotus lanterns afloat; the
`mirror_lake` biome. Chapter 12's The Mirror Remembers: the ferry in at the Reedless Shore, the Mirror Shallows (the
Thousand-Eye Toad's hollow off them), the Sentinel Causeway out to the Lake Shrine and its bronze mirror."""
from content.rooms.spec import room

BLUFF = dict(level=2, paint="r", wall=True, wavy=True)        # the lake's north bluff, rock under turf
LAKE = dict(water=True, wavy=True, mirror=True)               # the still water: its north shore mirrored in it
KNOLL = dict(level=1, paint="g", shape="round")               # a grassy knoll on the shore, a flight up its face
PATH = dict(level=0, paint="d", walk=True, wavy=True)         # the shore path
# The north shore along the water: willows and maples (the water mirrors them), bushes and rocks between; the water's
# own: grass on the bank, lotus out on it (no reeds: the Reedless Shore's lake).
WATERSIDE = dict(kinds=["tree_willow", "tree_maple", "tree_willow", "rock_mossy"], density=0.3)
WATER = dict(kinds=["tree_willow", "tree_maple", "tall_grass", "lotus_pads"], density=0.5)


# The Reedless Shore: where the lake ferry sets down. The sky-ship hangs over the water at the end of its jetty; the
# shore path runs east under the knolls (the jars and the ledge chest on them) past the signpost, willows and maples
# along the water mirrored in it, a pale strand at its edge, the fishing spot off it, lotus lanterns drifting out on
# the lake round a willow islet.
ML_REEDLESS_SHORE = room(
    "ml_reedless_shore", size=(72, 28), biome="mirror_lake",
    bands=[("shore", 3, 4, dict(level=0, paint="g")),
           ("bluff", 0, 4, BLUFF),
           ("path", 7, 3, PATH),
           ("waterside", 10, 8, dict(level=0, paint="g")),
           ("lake", 17, 11, LAKE)],
    features=[("knoll_w", (11, 2, 10, 5), KNOLL), ("knoll_e", (33, 2, 11, 5), KNOLL),
              ("jetty", (6, 14, 4, 8), dict(level=0, paint="w")),
              ("islet", (43, 20, 14, 7), dict(level=0, paint="g", shape="round"))],
    stairs="auto",
    ways={"ferry": dict(at=(7, 21), dir="s", arrive=(7, 19), span=2), "east": ("e", "path")},
    spawn="ferry",
    anchors={"sign_ml": "path.n@13", "jar_1": "knoll_w@16", "fish_5": "water@32", "jar_2": "knoll_e@36",
             "chest_ledge_mv_1": "knoll_e@40", "jar_3": "verge.s@45", "jar_4": "verge.s@63"},
    props=[("sky_ship", 2, 21), ("lantern", 5, 13), ("lantern", 10, 13), ("lotus_lantern", 19, 20),
           ("lotus_lantern", 27, 23), ("lotus_lantern", 38, 19), ("lotus_lantern", 58, 24), ("lotus_lantern", 64, 20)],
    flora={"shore": dict(density=0.4), "knoll_w": dict(density=0.45), "knoll_e": dict(density=0.45), "jetty": [], "waterside": WATERSIDE, "lake": WATER,
           "islet": dict(kinds=["tree_willow", "bush", "rock_mossy"], density=0.6)},
    ground={"sand": ["lake.bank"]},
    pins={"add": [("tree_willow", 16, 16), ("tree_maple", 24, 16), ("tree_willow", 37, 16), ("tree_willow", 57, 16)]},
    foes="auto")


# The Mirror Shallows: the lake's shallow margin, a pebbled bed under clear water a body wades through, islets of turf
# in it, the deep water beyond with its lotus lanterns. The shore path runs east along the turf under the bluff, the
# knolls with the jars and the ledge chest; in the bluff, among willows, the dark mouth of Toad's Hollow.
ML_MIRROR_SHALLOWS = room(
    "ml_mirror_shallows", size=(72, 28), biome="mirror_lake",
    bands=[("shore", 3, 10, dict(level=0, paint="g")),
           ("bluff", 0, 4, BLUFF),
           ("path", 9, 3, PATH),
           ("shallows", 13, 9, dict(level=0, paint="h", wavy=True)),
           ("lake", 21, 7, LAKE)],
    features=[("knoll_w", (2, 3, 9, 5), KNOLL), ("knoll_m", (13, 3, 10, 5), KNOLL),
              ("mouth", (34, 2, 4, 3), dict(level=0, paint="d")),
              ("isle_w", (22, 14, 9, 5), dict(level=0, paint="g", shape="round")),
              ("isle_e", (50, 15, 10, 5), dict(level=0, paint="g", shape="round"))],
    stairs="auto",
    ways={"west": ("w", "path"), "east": ("e", "path"), "hollow": dict(at=(35, 2), dir="n", arrive=(35, 4), span=2)},
    spawn="west",
    anchors={"jar_1": "knoll_w@6", "jar_2": "knoll_m@16", "chest_ledge_mv_1": "knoll_m@19", "jar_3": "verge.n@44",
             "jar_4": "shallows@64"},
    props=[("lotus_lantern", 9, 23), ("lotus_lantern", 21, 25), ("lotus_lantern", 36, 23), ("lotus_lantern", 49, 24),
           ("lotus_lantern", 62, 23), ("lotus_pads", 14, 24), ("lotus_pads", 30, 22), ("lotus_pads", 44, 25),
           ("lotus_pads", 57, 22), ("rock_mossy", 31, 3), ("rock_mossy", 38, 3)],
    flora={"shore": dict(density=0.4), "knoll_w": dict(density=0.45), "knoll_m": dict(density=0.45), "mouth": [],
           "isle_w": dict(kinds=["tree_willow", "bush", "rock_mossy", "tall_grass"], density=0.6),
           "isle_e": dict(kinds=["tree_maple", "bush", "rock_mossy", "tall_grass"], density=0.6)},
    pins={"add": [("tree_willow", 17, 21), ("tree_maple", 26, 21), ("tree_willow", 58, 19)]},
    foes="auto")


# The Sentinel Causeway: a causeway of dressed granite straight across the lake, four bastions along it where its stone
# lanterns stand (mirrored in the water), plank bridges from them out to the islets with the jars and the chests; the
# far north shore's willows over the water, the open lake to the south. The river sentinels keep it.
ML_SENTINEL_CAUSEWAY = room(
    "ml_sentinel_causeway", size=(72, 28), biome="mirror_lake",
    bands=[("far_shore", 0, 6, dict(level=0, paint="g", wavy=True)),
           ("lake_n", 6, 7, dict(LAKE, wavy="n")),
           ("lake_s", 16, 12, dict(LAKE, wavy=False)),
           ("causeway", 13, 3, dict(level=0, paint="s", walk=True))],
    features=[("bastion_1", (8, 12, 6, 5), dict(level=0, paint="s")), ("bastion_2", (24, 12, 6, 5), dict(level=0, paint="s")),
              ("bastion_3", (42, 12, 6, 5), dict(level=0, paint="s")), ("bastion_4", (58, 12, 6, 5), dict(level=0, paint="s")),
              ("islet_w", (12, 6, 9, 5), dict(level=0, paint="g", shape="round")),
              ("islet_m", (25, 5, 10, 6), dict(level=0, paint="g", shape="round")),
              ("bridge_w", (15, 10, 2, 3), dict(level=0, paint="w")), ("bridge_m", (27, 10, 2, 3), dict(level=0, paint="w")),
              ("islet_s", (44, 20, 10, 5), dict(level=0, paint="g", shape="round"))],
    ways={"west": ("w", "causeway"), "east": ("e", "causeway")},
    spawn="west",
    anchors={"jar_1": "islet_w@15", "chest_5": "islet_m@27", "chest_ledge_mv_1": "islet_m@31", "jar_2": "islet_m@29",
             "jar_3": "bastion_3@45", "jar_4": "bastion_4@62"},
    props=[("lantern", 8, 16), ("lantern", 13, 16), ("lantern", 24, 16), ("lantern", 29, 16), ("lantern", 42, 16),
           ("lantern", 47, 16), ("lantern", 58, 16), ("lantern", 63, 16), ("lotus_lantern", 5, 21), ("lotus_lantern", 19, 24),
           ("lotus_lantern", 36, 20), ("lotus_lantern", 60, 22), ("lotus_lantern", 38, 8), ("lotus_lantern", 52, 9),
           ("lotus_pads", 3, 9), ("lotus_pads", 46, 7), ("lotus_pads", 30, 23)],
    flora={"far_shore": dict(kinds=["tree_willow", "tree_maple", "bush", "tall_grass", "rock_mossy"], density=0.5),
           "islet_w": dict(kinds=["bush", "rock_mossy", "tall_grass"], density=0.5),
           "islet_m": dict(kinds=["tree_willow", "bush", "tall_grass"], density=0.5),
           "islet_s": dict(kinds=["tree_willow", "bush", "rock_mossy"], density=0.6),
           "causeway": [], "bastion": [], "bridge": []},
    pins={"add": [("tree_willow", 9, 4), ("tree_maple", 44, 5), ("tree_willow", 49, 5), ("tree_willow", 55, 4),
                  ("tree_maple", 64, 5)]},
    foes="auto")


# The Lake Shrine: the island at the causeway's end. The causeway lands at a granite landing with the wayside shrine;
# the island's round plaza of granite under its willows, the shrine hall at its north, the archway before the bronze
# mirror's altar in the middle, the insight stone in the east; Lu's journal page by the water on the island's south
# shore; lotus lanterns on the still water all round.
ML_LAKE_SHRINE = room(
    "ml_lake_shrine", size=(56, 28), biome="mirror_lake", base="~",
    bands=[("lake", 0, 28, LAKE)],
    features=[("island", (11, 1, 43, 26), dict(level=0, paint="g", shape="round")),
              ("plaza", (17, 4, 31, 19), dict(paint="s", shape="round")),
              ("causeway", (0, 13, 14, 3), dict(level=0, paint="s", walk=True)),
              ("landing", (2, 11, 7, 7), dict(level=0, paint="s"))],
    ways={"west": ("w", 14)},
    spawn="west",
    anchors={"shrine_ml": (5, 12), "mirror_altar": (32, 14), "insight_mirror": "plaza@43", "journal_lake": "island.front@33"},
    props=[("hall", 28, 4, "shrine_hall"), ("paifang", 30, 20), ("lantern", 26, 6), ("lantern", 38, 6),
           ("lantern", 21, 13), ("lantern", 43, 17), ("incense", 31, 11), ("incense", 34, 11), ("lantern", 2, 11),
           ("lantern", 8, 11), ("lotus_lantern", 3, 5), ("lotus_lantern", 6, 22), ("lotus_lantern", 13, 25),
           ("lotus_lantern", 52, 2), ("lotus_lantern", 54, 22), ("lotus_pads", 8, 2), ("lotus_pads", 2, 24)],
    flora={"island": dict(kinds=["tree_willow", "tree_maple", "bush_azalea", "bush", "rock_mossy"], density=0.5),
           "plaza": [], "causeway": [], "landing": [], "lake": dict(kinds=["lotus_pads"], density=0.2)},
    pins={"add": [("tree_willow", 12, 17), ("tree_willow", 16, 20), ("tree_maple", 50, 20)]})


# Toad's Hollow: a sunken hollow behind the Mirror Shallows' bluff, walled in rock and willows, its floor wet turf
# round a dark pool where the Thousand-Eye Toad lairs; a ledge over the pool with the chest, the toad's nest on the east
# bank. The way out west, back down to the shallows.
ML_TOADS_HOLLOW = room(
    "ml_toads_hollow", size=(56, 28), biome="mirror_lake", level=2,
    bands=[("rocks", 0, 22, dict(level=2, paint="r")), ("front", 22, 6, dict(level=1, paint="r"))],
    features=[("hollow", (3, 2, 50, 23), dict(level=0, paint="m", shape="round")),
              ("entry", (0, 12, 8, 3), dict(level=0, paint="d", walk=True)),
              ("ledge", (24, 3, 9, 4), dict(level=1, paint="r", shape="round")),
              ("pool", (17, 11, 18, 8), dict(water=True, shape="round", mirror=True))],
    stairs=[(27, 7, 3, 2, 0, 1)],
    ways={"entry": ("w", 13)},
    spawn="entry",
    anchors={"chest_ledge_mv_1": "ledge@28", "toad_nest": "hollow@48"},
    props=[("lotus_lantern", 22, 14), ("lotus_lantern", 30, 16), ("lotus_pads", 25, 12), ("lotus_pads", 20, 15),
           ("rock_mossy", 40, 18), ("rock_mossy", 11, 8)],
    flora={"rocks": dict(kinds=["tree_willow", "rock_mossy", "bush_wide"], density=0.3), "front": dict(kinds=["rock_mossy", "bush"], density=0.3),
           "hollow": dict(kinds=["tree_willow", "tall_grass", "bush", "rock_mossy", "ferns"], density=0.45),
           "entry": [], "ledge": [], "pool": dict(kinds=["tall_grass", "lotus_pads"], density=0.3)},
    foes="auto")

ROOMS = [ML_REEDLESS_SHORE, ML_MIRROR_SHALLOWS, ML_SENTINEL_CAUSEWAY, ML_LAKE_SHRINE, ML_TOADS_HOLLOW]
