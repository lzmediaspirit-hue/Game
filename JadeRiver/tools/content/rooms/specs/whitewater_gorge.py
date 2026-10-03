"""E1 room specs (R2): Whitewater Gorge, west of Bend Shore (docs/architecture/room_engine.md). The river runs white
between grey rock walls (`rapids`: rocks breaking the stream), pines cling to the ledges, and the road keeps to the
gorge's floor: the Gorge Mouth where it leaves the Bend, the Rapids Terraces (and the cave behind their waterfall), and
the Echo Cliffs, high over the river, where the way on to Crane Cliffs waits for wings."""
from content.rooms.spec import room

CLIFF = dict(level=4, paint="r", wall=True)   # the gorge's wall, four levels of grey rock
# Its foot wanders (laid after the terrace under it, which reaches a row into it, so no pit opens between them).
CLIFF_FOOT = dict(CLIFF, wavy=True)


# The Gorge Mouth: where the river leaves Deepwater Bend between the gorge's walls. The road runs west along the gorge's
# floor under a ledge of pines; a stream falls over the north wall and crosses the road under a plank bridge on its way
# to the river; the wayside shrine stands at the road's west end, Chief Yan Bo's sparring post by the water.
WG_GORGE_MOUTH = room(
    "wg_gorge_mouth", size=(56, 26), biome="gorge",
    bands=[("ledge", 3, 7, dict(level=1, paint="g", wavy=True)),
           ("cliff", 0, 4, CLIFF_FOOT),
           ("road", 10, 3, dict(level=0, paint="d", walk=True)),
           ("floor", 13, 5, dict(level=0, paint="g")),
           ("river", 18, 8, dict(water=True, wavy=True, rapids=0.022))],
    features=[("step", (6, 4, 9, 3), dict(level=2, paint="r")), ("cleft", (25, 0, 7, 4), CLIFF),
              ("stream", (27, 4, 3, 6), dict(water=True)), ("stream", (27, 13, 3, 5), dict(water=True)),
              ("bridge", (26, 9, 5, 5), dict(level=0, paint="w"))],
    stairs="auto",
    ways={"east": ("e", "road"), "west": ("w", "road")},
    spawn="east",
    anchors={"herb_1": "step@8", "jar_3": "step@13", "ore_2": "wall_foot@43", "shrine_wg": "verge.n@5",
             "spar_gorge_chief": "floor@35", "crate_4": "verge.s@23", "jar_5": "verge.n@48"},
    props=[("waterfall", 27, 4)],
    flora={"ledge": dict(density=0.5), "floor": dict(density=0.4)},
    ground={"sand": ["river.bank"]},
    foes="auto")


# The Rapids Terraces: the gorge opens over three terraces stepping down to the rapids. A waterfall pours over the north
# wall into its pool on the upper terrace, and behind it a cave runs into the rock (hidden till found). The road runs
# along the lowest terrace; below it a strand of sand and the river breaking white over its rocks.
WG_RAPIDS_TERRACES = room(
    "wg_rapids_terraces", size=(72, 28), biome="gorge",
    bands=[("upper", 3, 6, dict(level=2, paint="g")),
           ("middle", 8, 4, dict(level=1, paint="g", wavy=True)),
           ("cliff", 0, 4, CLIFF_FOOT),
           ("road", 14, 3, dict(level=0, paint="d", walk=True)),
           ("strand", 17, 2, dict(level=0, paint="a", wavy=True)),
           ("river", 19, 9, dict(water=True, wavy=True, rapids=0.022))],
    features=[("cleft", (31, 0, 9, 4), CLIFF), ("pool", (34, 4, 4, 3), dict(water=True))],
    stairs="auto",
    ways={"east": ("e", "road"), "west": ("w", "road"), "cave": dict(at=(33, 4), dir="n", arrive=(33, 6), span=2)},
    spawn="east",
    anchors={"herb_1": "middle@16", "jar_5": "middle@20", "rare_ginseng_rt": "upper@24", "herb_2": "upper@40",
             "crate_6": "upper@39", "ore_3": "wall_foot@45", "ore_4": "wall_foot@64", "mine_rapids_terrace_vein": "upper@59",
             "jar_7": "verge.n@29", "crate_8": "verge.n@43", "jar_9": "verge.s@55", "crate_10": "verge.n@65",
             "earth_vent_wg": "strand@25", "fish_11": "water@50", "rift_tear": "verge.s@40", "spirit_fruit_tree": "strand@14"},
    props=[("waterfall", 34, 4)],
    flora={"upper": dict(density=0.45), "middle": dict(density=0.45)},
    # T2 (docs/architecture/topdown_mechanics.md): the rapids' current hazard's areas (the strand's shallows, the white
    # water) and the side view's current over the white water, pulling a swimmer downstream.
    areas=[{"kind": "shallows", "rect": [11, 17, 31, 2], "current": -45}, {"kind": "shallows", "rect": [58, 17, 3, 2], "current": -45},
           {"kind": "current", "rect": [42, 19, 16, 9], "current": -75}],
    traverse=[("current", "rapids_current", dict(rect=(42, 19, 16, 9), push=(-91, 0)))],
    foes="auto")


# The Echo Cliffs: the gorge's narrows, the road on a shelf high over the river. North of it the cliff climbs in ledges,
# a level a ledge, to the two rock walls the vultures nest between; south of it the shelf's lip and a long drop to the
# white water. The way west to Crane Cliffs is a ledge only wings can follow.
WG_ECHO_CLIFFS = room(
    "wg_echo_cliffs", size=(56, 26), biome="gorge", level=3,
    bands=[("cliff", 0, 3, dict(level=7, paint="r", wall=True)),
           ("road", 14, 3, dict(paint="d", walk=True)),
           ("shelf", 17, 2, dict(level=3, paint="g")),
           ("brink", 19, 2, dict(level=3, paint="r")),
           ("river", 21, 5, dict(water=True, wavy=True, rapids=0.03))],
    features=[("ledge_0", (4, 7, 10, 4), dict(level=4, paint="r")),
              ("ledge_1", (16, 5, 9, 5), dict(level=5, paint="r")),
              ("wall_w", (27, 3, 3, 8), dict(level=7, paint="r", wall=True)),
              ("wall_e", (32, 3, 3, 8), dict(level=7, paint="r", wall=True)),
              ("ledge_3", (40, 6, 10, 4), dict(level=5, paint="r")),
              # T2 (docs/architecture/topdown_mechanics.md): the vultures' nest at the shaft's head, three levels over its
              # floor: Wall-Step kicks up between the two walls to it (Between Two Walls).
              ("nest", (30, 3, 2, 2), dict(level=6, paint="r"))],
    stairs="auto",
    ways={"east": ("e", "road"), "west": ("w", "road")},
    spawn="east",
    anchors={"ore_1": "ledge_0@6", "jar_3": "ledge_0@12", "crate_4": "ledge_1@18", "crate_6": "ledge_3@47",
             "ore_2": "verge.n@42", "jar_5": "verge.s@36", "lost_echo_cliff": "verge.n@38", "rift_tear": "road@31",
             "spirit_fruit_tree": "shelf@20"},
    flora={"shelf": dict(density=0.45)},
    foes=["auto", "auto:ledge_1", "auto"])


# The Waterfall Cave: the cave behind the Rapids Terraces' waterfall. The way in comes up from the falls' pool in the
# south; a floor of wet sand, the shallows over its east half; ledges a level and two up along the north wall (the
# journal page and the chest on the high one), a second fall pouring through a cleft in the north-east into a pool, and
# beside it the inner cache that fills when the falls thin.
WG_WATERFALL_CAVE = room(
    "wg_waterfall_cave", size=(40, 22), biome="grotto", level=4,
    features=[("cave", (1, 3, 38, 15), dict(level=0, paint="a", shape="round")),
              ("shallows", (20, 6, 18, 12), dict(level=0, paint="h", shape="round")),
              ("adit", (4, 16, 5, 6), dict(level=0, paint="a", walk=True)),
              ("ledge_low", (5, 4, 8, 4), dict(level=1, paint="r")),
              ("ledge_high", (14, 3, 9, 3), dict(level=2, paint="r")),
              ("ledge_east", (31, 9, 6, 3), dict(level=1, paint="r")),
              ("pool", (26, 4, 5, 4), dict(water=True))],
    stairs="auto",
    ways={"entry": ("s", 6)},
    spawn="entry",
    anchors={"cave_lotus": "ledge_low@8", "journal_cave": "ledge_high@16", "chest_1": "ledge_high@20",
             "cave_shard_vein": "ledge_east@34", "cave_inner_cache": "shallows@32"},
    props=[("waterfall", 27, 4)],
    foes="auto")

ROOMS = [WG_GORGE_MOUTH, WG_RAPIDS_TERRACES, WG_ECHO_CLIFFS, WG_WATERFALL_CAVE]
