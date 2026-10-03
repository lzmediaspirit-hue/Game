"""E1 room specs (R4, the peaks): Mist Peak, west of the Sky Ledges (docs/architecture/room_engine.md). The Misty
Slopes, the Forgotten Monastery (the Nine-Bough Jade Tree; A Wider Sky's heaven insight stone; the Monastery Gate's
lost art) and the Ascension Gate, where the Gate Guardian ends Act I. Mist lies in the slopes' wet hollows (paint `m`,
TopdownAtmosphere's mist); the monastery's halls stand as broken walls (`shape="ruin"`)."""
from content.rooms.spec import room

# The Misty Slopes: the trail along the mountain's flank in the soul-mist. Above it a grassy shelf under grey cliffs and
# a rock knoll where two chests wait; below it the slope falls in two steps toward the clouds, its hollows wet and
# misty, a seep pool among the reeds where the mist's insight stone stands; pines and grey dead trees throughout.
MP_MISTY_SLOPES = room(
    "mp_misty_slopes", size=(72, 30), biome="mist_peak", level=1,
    bands=[("crown", 0, 4, dict(level=5, paint="r", wall=True)),
           ("slope", 4, 9, dict(level=2, wavy="s", flights=[10, 46])),
           ("trail", 14, 3, dict(paint="d", walk=True)),
           ("brink", 23, 7, dict(level=0)),
           ("meadow", 17, 7, dict(level=1, wavy="s"))],
    features=[("knoll", (19, 4, 13, 6), dict(level=3, paint="r", shape="round")),
              ("hollow_w", (3, 18, 16, 6), dict(paint="m", shape="round")),
              ("mere", (27, 20, 20, 8), dict(paint="m", shape="round")),
              ("hollow_e", (55, 20, 14, 8), dict(paint="m", shape="round")),
              ("seep", (30, 24, 14, 6), dict(water=True, shape="round"))],
    stairs="auto",
    ways={"east": ("e", "trail"), "west": ("w", "trail")},
    spawn="east",
    anchors={"herb_1": "slope@5", "ore_2": "wall_foot@55", "jar_3": "slope@10", "crate_4": "slope@15",
             "rare_soulbell_ms": "slope.back@40", "chest_ledge_mv_1": "knoll@22", "chest_cloud_mv": "knoll@28",
             "jar_5": "verge.s@35", "crate_6": "verge.n@51", "jar_7": "verge.s@66", "insight_mist": "mere@30",
             "rift_tear": "brink@46", "spirit_fruit_tree": "meadow@22", "swarm_silk_moth": "hollow_w@11",
             "trail_cloud_marmot": "meadow@49"},
    flora={"slope": dict(density=0.45), "meadow": dict(density=0.4), "brink": dict(density=0.4),
           "seep": ["cattails", "tall_grass", "ferns"]},
    foes="auto")

# The Forgotten Monastery: a ruined monastery on a terrace under the cliffs. The upper terrace's paving holds the broken
# walls of the main hall (the chest and a formation stone inside), the west wing with its raised floor of boards and
# the east gate; a grand stair climbs to the hall from the lower court the road crosses, a gallery of boards stands
# before the terrace, and under it, behind the hall and the west wing, the hidden stair and cellar open in the
# retaining wall. South of the court the old garden runs wild: the Nine-Bough Jade Tree, the heaven insight stone,
# dead trees and misty hollows.
MP_FORGOTTEN_MONASTERY = room(
    "mp_forgotten_monastery", size=(72, 30), biome="mist_peak", level=1,
    bands=[("crown", 0, 4, dict(level=6, paint="r", wall=True)),
           ("terrace", 4, 9, dict(level=3, paint="p", flights=[17, 57])),
           ("garden", 22, 8, dict(level=0)),
           ("court", 13, 9, dict(level=1, paint="p", wavy="s")),
           ("road", 16, 3, dict(paint="p", walk=True))],
    features=[("hall", (27, 5, 18, 7), dict(shape="ruin", level=5)), ("west_wing", (5, 5, 13, 6), dict(shape="ruin", level=5)),
              ("east_gate", (51, 5, 12, 6), dict(shape="ruin", level=5, door="w")),
              ("floor_w", (19, 6, 5, 4), dict(level=4, paint="w")), ("gallery", (45, 13, 6, 2), dict(level=2, paint="w")),
              ("moss_w", (1, 13, 14, 7), dict(paint="g", shape="round")), ("moss_e", (56, 13, 15, 7), dict(paint="g", shape="round")),
              ("moss_t", (44, 5, 8, 6), dict(paint="g", shape="round")),
              ("hollow", (20, 23, 18, 7), dict(paint="m", shape="round"))],
    stairs=["auto", (34, 13, 4, 4, 1, 3)],
    ways={"east": ("e", "road"), "west": ("w", "road"),
          "hidden_cellar": dict(at=(9, 13), dir="n", arrive=(9, 15), span=2),
          "hidden_stair": dict(at=(42, 13), dir="n", arrive=(42, 15), span=2)},
    spawn="east",
    anchors={"herb_1": "west_wing@14", "ore_2": "wall_foot@66", "jar_3": "floor_w@21", "jar_4": "gallery@47",
             "jar_5": "east_gate@55", "jar_6": "verge.s@26", "jar_7": "verge.s@52", "jar_8": "verge.s@65",
             "chest_9": "hall@31", "heaven_insight": "garden@14", "nine_bough_tree": "garden@54",
             "page_method_conversion_pill_3": "garden@66", "formation_remnant_0": "west_wing@8",
             "formation_remnant_1": "hall@40", "formation_remnant_2": "east_gate@59", "rift_tear": "garden@40",
             "spirit_fruit_tree": "garden@28", "swarm_silk_moth": "hollow@24", "lost_monastery_gate": "verge.n@30"},
    props=[("lantern", 32, 12), ("lantern", 39, 12), ("lantern", 23, 19), ("lantern", 49, 19), ("log", 61, 14),
           ("boulder", 25, 14), ("boulder", 26, 14)],
    flora={"terrace": dict(density=0.3), "garden": dict(density=0.45)},
    foes="auto")

# The Ascension Gate: the top of the world. A round arena paved in the snow at the peak, four plinths round it where
# the cloud platforms were, a dais under the last cliff with a grand stair, and on it the way up through the cliff to
# the Azure Expanse, barred until the Gate Guardian falls; the road from the Frozen Shrine comes in from the east.
MP_ASCENSION_GATE = room(
    "mp_ascension_gate", size=(72, 30), biome="snowfield", level=1,
    bands=[("crown", 0, 4, dict(level=7, paint="r", wall=True)),
           ("summit", 4, 26, dict(level=1)),
           ("approach", 16, 3, dict(paint="p", walk=True, x=56))],
    features=[("arena", (12, 7, 48, 22), dict(level=1, paint="p", shape="round")),
              ("dais", (27, 4, 18, 6), dict(level=3, paint="p")),
              ("plinth_nw", (18, 11, 3, 3), dict(level=2, paint="p")), ("plinth_sw", (17, 21, 3, 3), dict(level=2, paint="p")),
              ("plinth_ne", (51, 11, 3, 3), dict(level=2, paint="p")), ("plinth_se", (52, 21, 3, 3), dict(level=2, paint="p"))],
    stairs=[(34, 10, 4, 4, 1, 3)],
    ways={"east": ("e", "approach"), "ascend": dict(at=(36, 4), dir="n", arrive=(36, 6), span=3)},
    spawn="east",
    props=[("lantern", 33, 4), ("lantern", 39, 4), ("lantern", 27, 13), ("lantern", 44, 13), ("lantern", 13, 17),
           ("lantern", 58, 17)],
    foes="auto")

ROOMS = [MP_MISTY_SLOPES, MP_FORGOTTEN_MONASTERY, MP_ASCENSION_GATE]
