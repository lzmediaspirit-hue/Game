"""E1 room specs (R8): the Wyrmnest Isles, tall cliff islands of pale eggshell rock over the cloud sea, where the
star-wyrms nest and a Hollowed brood has gone grey (docs/architecture/room_engine.md). Chapter 19's Star-Tier Beasts
(the Nest Cliffs, where Tamer Qiu keeps watch), A Hollowed Brood (the Eggshell Terraces' grey puddles) and The Last
Egg (the Guardian's Crown and the Hatching Cave under it). Turf over pale rock, spires standing out of it, star crystals,
the great nests of whole branches on the ledges and the crowns, old bones and eggshells strewn about; the rock falls
away past every south edge into the cloud sea. The side view's ledges (110 to 320 units) are terraces and crags."""
from content.rooms.spec import room

# The Nest Cliffs: where the skiff from the Moored Hulks puts in, at the end of a timber pier out over the brink at the
# west. The path climbs east along the isle's shoulder under the nest cliffs; on their ledges the nests, a jar on the
# low one, a crate on the high one; Tamer Qiu by the shrine near the pier, watching the guardians; the journal page by
# an old nest on the path; spires and star crystals in the turf.
WN_NEST_CLIFFS = room(
    "wn_nest_cliffs", size=(64, 30), biome="wyrmnest", level=1,
    bands=[("cliffs", 0, 4, dict(level=6, paint="r", wall=True, wavy="s")),
           ("ledges", 4, 7, dict(level=2, paint="r", wavy="s", flights=[12, 52])),
           ("path", 14, 3, dict(paint="d", walk=True)),
           ("brink", 25, 5, dict(level=0, paint="r")),
           ("slope", 17, 9, dict(level=1, paint="r", wavy="s"))],
    features=[("ledge", (16, 4, 10, 5), dict(level=3, paint="r", shape="round", flights=[20])),
              ("ledge_2", (35, 4, 11, 5), dict(level=3, paint="r", shape="round", flights=[40])),
              ("turf", (10, 17, 14, 7), dict(paint="g", shape="round")),            # the turf in the lee of the rock
              ("turf_2", (31, 18, 16, 6), dict(paint="g", shape="round")),
              ("turf_3", (51, 19, 12, 5), dict(paint="g", shape="round")),
              ("pier", (3, 17, 5, 13), dict(level=1, paint="w"))],
    stairs="auto",
    ways={"skiff": ("s", 5), "east": ("e", "path")},
    spawn=(6, 22),
    anchors={"npc_tamer_qiu": "verge.s@10", "shrine_wn_cliffs": "verge.n@13", "jar_2": "ledge@19", "journal_nests": "path.s@28",
             "herb_1": "ledges@31", "crate_3": "ledge_2@39", "jar_4": "verge.s@42", "crate_5": "slope@56"},
    props=[("wyrm_nest", 21, 5), ("wyrm_nest", 41, 5), ("wyrm_nest", 27, 18), ("star_crystal", 30, 9), ("wyrm_skull", 47, 20),
           ("wyrm_ribs", 14, 21), ("post", 3, 29), ("post", 7, 29), ("star_lantern", 2, 17), ("star_lantern", 8, 17)],
    flora={"ledges": dict(density=0.4), "slope": dict(density=0.36), "brink": dict(density=0.4)},
    foes="auto")


# The Eggshell Terraces: the brood's terraces east of the cliffs, stepping up north from the path in pale rock, strewn
# with the shells of hatched eggs; two great nests on the upper terrace, gone grey, and on the high one the two chests.
# South of the path the Hollowed brood's grey puddles drink the colour from the turf.
WN_EGGSHELL_TERRACES = room(
    "wn_eggshell_terraces", size=(64, 30), biome="wyrmnest", level=1,
    bands=[("cliffs", 0, 3, dict(level=6, paint="r", wall=True, wavy="s")),
           ("upper", 3, 6, dict(level=3, paint="r", wavy="s", flights=[10, 50])),
           ("terrace", 9, 4, dict(level=2, wavy="s", flights=[30])),
           ("path", 14, 3, dict(paint="d", walk=True)),
           ("brink", 26, 4, dict(level=0, paint="r")),
           ("slope", 17, 10, dict(level=1, paint="r", wavy="s"))],
    features=[("crown", (18, 3, 10, 4), dict(level=4, paint="r", shape="round", flights=[22])),
              ("turf", (44, 18, 16, 7), dict(paint="g", shape="round")),
              ("turf_2", (0, 22, 12, 5), dict(paint="g", shape="round")),
              ("grey", (8, 19, 8, 5), dict(paint="h", shape="round")),           # the Hollowed brood's grey puddles
              ("grey_2", (21, 20, 8, 5), dict(paint="h", shape="round")),
              ("grey_3", (35, 19, 9, 5), dict(paint="h", shape="round"))],
    stairs="auto",
    ways={"west": ("w", "path"), "east": ("e", "path")},
    spawn="west",
    anchors={"jar_1": "terrace@5", "crate_2": "upper@14", "chest_ledge_mv_1": "crown.front@21", "chest_cloud_mv": "crown@25",
             "jar_3": "verge.n@41", "crate_4": "terrace@55"},
    props=[("wyrm_nest", 31, 4), ("wyrm_nest", 43, 4), ("wyrm_skull", 54, 20), ("wyrm_ribs", 47, 22), ("rock_spire", 4, 22),
           ("rock_spire", 60, 23)],
    flora={"upper": {"kinds": ["eggshell", "bone_pile", "rock_small", "tall_grass", "eggshell"], "density": 0.45},
           "terrace": {"kinds": ["eggshell", "rock_small", "tall_grass", "bone_pile", "star_crystal"], "density": 0.4},
           "slope": dict(density=0.32), "brink": dict(density=0.36), "grey": {"kinds": [], "density": 0.0}},
    areas=[{"kind": "hollow_puddle", "rect": [10, 20, 4, 3]}, {"kind": "hollow_puddle", "rect": [23, 21, 4, 3]},
           {"kind": "hollow_puddle", "rect": [37, 20, 5, 3]}],
    foes="auto")


# The Guardian's Crown: the isle's crown, where the nest guardians keep the old brood's ground. The path comes in from
# the west under the crown of rock in the middle, the great nest on its top among star crystals (the chests the
# guardians keep); a ledge east of it holds a crate; the cave's mouth opens in the cliff at the east end, into the
# Hatching Cave.
WN_GUARDIANS_CROWN = room(
    "wn_guardians_crown", size=(64, 30), biome="wyrmnest", level=1,
    bands=[("cliffs", 0, 4, dict(level=6, paint="r", wall=True, wavy="s")),
           ("shoulder", 4, 7, dict(level=2, paint="r", wavy="s", flights=[8])),
           ("path", 14, 3, dict(paint="d", walk=True)),
           ("brink", 25, 5, dict(level=0, paint="r")),
           ("slope", 17, 9, dict(level=1, paint="r", wavy="s"))],
    features=[("crown", (20, 3, 16, 7), dict(level=3, paint="r", shape="round", flights=[24])),
              ("turf", (8, 17, 15, 7), dict(paint="g", shape="round")),
              ("turf_2", (36, 18, 15, 6), dict(paint="g", shape="round")),
              ("summit", (25, 3, 9, 5), dict(level=4, paint="r", shape="round", flights=[31])),
              ("ledge", (38, 4, 9, 5), dict(level=3, paint="r", shape="round", flights=[42])),
              ("cliff_e", (53, 0, 11, 4), dict(level=6, paint="r", wall=True)),   # the cliff the cave opens in
              ("mouth", (56, 2, 4, 9), dict(level=1, paint="d"))],               # the cave mouth, a cleft in the cliff
    stairs="auto",
    ways={"west": ("w", "path"), "cave": dict(at=(58, 2), dir="n", arrive=(58, 4), span=2)},
    spawn="west",
    anchors={"herb_1": "crown@22", "jar_3": "crown@34", "chest_8": "summit.front@26", "chest_cloud_mv": "summit.front@33",
             "crate_4": "ledge@41", "jar_5": "verge.s@33", "crate_6": "slope@44", "herb_2": "verge.n@48", "jar_7": "slope@57"},
    props=[("wyrm_nest", 27, 5), ("star_crystal", 23, 4), ("star_crystal", 35, 7), ("star_crystal", 15, 18),
           ("star_crystal", 43, 21), ("wyrm_skull", 50, 7), ("rock_spire", 11, 6), ("rock_spire", 52, 21),
           ("wyrm_ribs", 6, 21), ("bone_pile", 54, 11), ("bone_pile", 61, 12), ("rock_spire", 54, 6), ("rock_spire", 61, 6), ("boulder", 55, 4), ("boulder", 60, 4)],
    flora={"shoulder": dict(density=0.4), "slope": dict(density=0.34), "brink": dict(density=0.4),
           "crown": {"kinds": ["star_crystal", "bone_pile", "tall_grass", "rock_small"], "density": 0.35}},
    foes="auto")


# The Hatching Cave: a warm cave under the crown, where the last of the star-wyrms' eggs is kept. Its floor of rock
# round a raised hollow in the middle, the great nest on it and the egg beside it, the Brood Guardian before it; star
# crystals grown out of the walls give the light; old shells and bones along the walls, a chest on a ledge at the west.
WN_HATCHING_CAVE = room(
    "wn_hatching_cave", size=(44, 24), biome="cave", level=4,
    features=[("front", (0, 15, 44, 9), dict(level=1, paint="r")),               # the cave's low front, nothing hidden
              ("cave", (2, 2, 40, 19), dict(level=0, paint="d", shape="round")),
              ("passage", (0, 11, 10, 3), dict(level=0, paint="d", walk=True)),
              ("hollow", (22, 4, 14, 9), dict(level=1, paint="r", shape="round", flights=[28])),
              ("ledge", (8, 3, 9, 5), dict(level=1, paint="r", shape="round", flights=[12]))],
    stairs="auto",
    ways={"entry": ("w", 12)},
    spawn="entry",
    anchors={"chest_ledge_mv_1": "ledge@12", "lost_wyrm_egg": "cave@17", "last_egg": "hollow@32"},
    props=[("wyrm_nest", 28, 7), ("star_crystal", 5, 4), ("star_crystal", 38, 5), ("star_crystal", 20, 3),
           ("star_crystal", 39, 13), ("eggshell", 19, 9), ("eggshell", 36, 14), ("bone_pile", 14, 16),
           ("wyrm_skull", 30, 16)],
    flora={"cave": {"kinds": ["eggshell", "bone_pile", "rock_small", "star_crystal"], "density": 0.25}},
    foes=[[(33, 15)]])

ROOMS = [WN_NEST_CLIFFS, WN_EGGSHELL_TERRACES, WN_GUARDIANS_CROWN, WN_HATCHING_CAVE]
