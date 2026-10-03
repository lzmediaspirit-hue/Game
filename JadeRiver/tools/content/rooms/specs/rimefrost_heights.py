"""E1 room specs (R6): Rimefrost Heights, the snowline over the Thunderhorn Plains (docs/architecture/room_engine.md,
"Act II's first zones (R6)"). Grey rock under fresh snow (decision 44's `snow`, laid over the whole room), the trails
trodden to packed snow (`snowpack`), frost pines and dead trees standing out of it, boulders glazed with ice; the
`rimefrost` biome. Chapter 12: the grey pilgrim caught on Frostpine Climb, the hermit's cave found on the summit (Frost
and Silence)."""
from content.rooms.spec import room

CRAGS = dict(level=6, paint="r", wall=True, wavy=True)   # the heights' crags, snow on their crowns
SHELF = dict(level=2, paint="r", shape="round")           # a rock shelf the snow apes keep, a flight up its face
# The flora: frost pines and dead trees on the shelves and slopes, boulders and small rocks at the crags' foot and along
# the trails (no grass: it is under the snow).
SLOPE = dict(kinds=["tree_pine", "tree_pine", "dead_tree", "boulder", "rock_small"], density=0.4)


def snowed(w, h, *trails):
    """The heights' ground: fresh snow over every floor, packed snow along the trails (their own wavy cells)."""
    return {"snow": [(0, 0, w, h)], "snowpack": list(trails)}


# Frostpine Climb: the trail up from the Lightning Scar climbs the mountain's flank in three tiers, a flight between
# each: along the lowest tier (the signpost, the stoat's trail and the cricket swarm in the snow below the trees), up to
# the middle tier and east along it under the frost pines (the herb and a jar on its west shoulder), and up again to the
# high tier, where the grey pilgrim stands, and east along the crags' foot (the stormsteel vein) to the Snow Ape Ledges.
RF_FROSTPINE_CLIMB = room(
    "rf_frostpine_climb", size=(72, 28), biome="rimefrost",
    bands=[("lower", 18, 10, dict(level=0, paint="r")),
           ("middle", 11, 8, dict(level=1, paint="r", wavy=True)),
           ("upper", 3, 9, dict(level=2, paint="r", wavy=True)),
           ("crags", 0, 4, CRAGS)],
    features=[("landing_1", (19, 15, 7, 4), dict(level=1, paint="r")),
              ("landing_2", (43, 7, 7, 5), dict(level=2, paint="r")),
              ("trail_low", (0, 20, 26, 3), dict(paint="d", walk=True, wavy=True)),
              ("trail_mid", (20, 13, 30, 3), dict(paint="d", walk=True, wavy=True)),
              ("trail_high", (44, 5, 28, 3), dict(paint="d", walk=True, wavy=True))],
    stairs=[(21, 19, 3, 2, 0, 1), (45, 12, 3, 2, 1, 2)],
    ways={"west": ("w", 21), "east": ("e", 6)},
    spawn="west",
    anchors={"sign_rf": "trail_low.n@4", "trail_frost_stoat": "lower@10", "herb_1": "middle@13", "jar_3": "middle@17",
             "journal_frostpine": "lower@28", "jar_4": "upper@32", "swarm_frost_cricket": "lower@34",
             "chest_cloud_mv": "upper@40", "jar_5": "lower@46", "npc_grey_pilgrim": "trail_high@51", "ore_2": "wall_foot@55",
             "jar_6": "middle@62"},
    props=[("ice_rock", 30, 24), ("ice_rock", 57, 22), ("ice_rock", 12, 14), ("ice_rock", 66, 15)],
    flora={"lower": dict(SLOPE, density=0.32), "middle": SLOPE, "upper": SLOPE, "landing_1": [], "landing_2": []},
    ground=snowed(72, 28, "trail_low", "trail_mid", "trail_high"),
    foes="auto")

# The Snow Ape Ledges: a snowfield under the crags where the trail crosses east. North of it the slope rises to the
# apes' rock shelves, flights up their faces: the west shelf with the herb, a jar and the chest, the east one with the
# rare ginseng and a jar; the stormsteel vein at the crags' foot between them. South of the trail the snowfield, frost
# pines and ice-glazed boulders, the cricket swarm and the stoat's trail.
RF_SNOW_APE_LEDGES = room(
    "rf_snow_ape_ledges", size=(72, 28), biome="rimefrost",
    bands=[("slope", 3, 9, dict(level=1, paint="r", wavy=True)),
           ("crags", 0, 4, CRAGS),
           ("trail", 12, 3, dict(level=0, paint="d", walk=True, wavy=True)),
           ("field", 15, 13, dict(level=0, paint="r"))],
    features=[("shelf_w", (14, 3, 15, 6), SHELF), ("shelf_e", (37, 3, 11, 6), SHELF)],
    stairs="auto",
    ways={"west": ("w", "trail"), "east": ("e", "trail")},
    spawn="west",
    anchors={"herb_1": "shelf_w@17", "jar_3": "shelf_w@21", "chest_cloud_mv": "shelf_w@25", "trail_frost_stoat": "field@29",
             "jar_4": "shelf_e@40", "rare_ginseng_sa": "shelf_e@44", "jar_5": "field@44", "swarm_frost_cricket": "field@47",
             "ore_2": "wall_foot@54", "jar_6": "slope@63"},
    props=[("ice_rock", 8, 20), ("ice_rock", 33, 23), ("ice_rock", 58, 19), ("ice_rock", 66, 24)],
    flora={"slope": SLOPE, "field": dict(SLOPE, density=0.34), "shelf_w": dict(kinds=["boulder", "rock_small"], density=0.3),
           "shelf_e": dict(kinds=["boulder", "rock_small"], density=0.3)},
    ground=snowed(72, 28, "trail"),
    foes="auto")


# Rimefrost Summit: the heights' top above the clouds. The trail comes in from the west past the wayside shrine onto a
# broad snowy plateau: rock outcrops with the frost lotuses, the jars and the chest, the insight stone glazed with ice
# on the highest, the star-sighting stone at the south rim over the sea of cloud; in the crags' north face the cleft of
# the hermit's ice cave, hidden till found.
RF_RIMEFROST_SUMMIT = room(
    "rf_rimefrost_summit", size=(56, 28), biome="rimefrost",
    bands=[("crags", 0, 4, CRAGS),
           ("trail", 13, 3, dict(level=0, paint="d", walk=True, wavy=True, w=24)),
           ("plateau", 16, 12, dict(level=0, paint="r"))],
    features=[("outcrop_w", (17, 3, 13, 7), SHELF), ("crown", (30, 6, 9, 6), dict(level=2, paint="r", shape="round")),
              ("outcrop_e", (39, 9, 10, 6), dict(level=1, paint="r", shape="round")),
              ("cleft", (46, 2, 5, 3), dict(level=0, paint="r")),
              ("rim", (24, 22, 18, 6), dict(paint="s"))],
    stairs="auto",
    ways={"west": ("w", "trail"), "ice_cave": dict(at=(48, 2), dir="n", arrive=(48, 4), span=2)},
    spawn="west",
    anchors={"shrine_rf_summit": "trail.n@6", "swarm_frost_cricket": "plateau@15", "herb_1": "outcrop_w@21",
             "jar_3": "outcrop_w@26", "jar_4": "verge.s@28", "insight_frost": "crown.top", "sight_rimefrost": "rim@33",
             "herb_2": "outcrop_e@41", "chest_6": "outcrop_e@44", "jar_5": "plateau@48"},
    props=[("ice_rock", 9, 22), ("ice_rock", 44, 20), ("ice_rock", 13, 8), ("lantern", 24, 22), ("lantern", 41, 22)],
    flora={"plateau": dict(SLOPE, density=0.34), "outcrop_w": SLOPE, "crown": [], "outcrop_e": SLOPE, "cleft": [], "rim": []},
    ground=snowed(56, 28, "trail"),
    foes="auto")


# The Hermit's Ice Cave: a cave of blue ice behind the summit's cleft, its low front sill, the way in up from the south.
# Its floor packed snow, the rock round it under fresh snow; the hermit Shuang sits at its heart on a mat by his
# incense, the Qi spring welling under the ice in the west, icicled boulders round the walls.
RF_HERMITS_ICE_CAVE = room(
    "rf_hermits_ice_cave", size=(32, 18), biome="rimefrost", level=4,
    features=[("front", (0, 12, 32, 6), dict(level=1, paint="r")),
              ("cavern", (2, 2, 28, 13), dict(level=0, paint="k", shape="round")),
              ("adit", (14, 12, 4, 6), dict(level=0, paint="k"))],
    ways={"entry": ("s", 16)},
    spawn="entry",
    anchors={"spring_ice": (8, 9), "npc_hermit_shuang": (16, 6)},
    props=[("mat", 15, 7), ("incense", 18, 5), ("ice_rock", 5, 5), ("ice_rock", 23, 4), ("ice_rock", 26, 9),
           ("ice_rock", 5, 11), ("lantern", 12, 4), ("lantern", 20, 4), ("boulder", 9, 4), ("boulder", 27, 6),
           ("boulder", 22, 12), ("boulder", 7, 12)],
    flora={"cavern": [], "front": [], "adit": []},
    ground={"snow": [(0, 0, 32, 18)]})

ROOMS = [RF_FROSTPINE_CLIMB, RF_SNOW_APE_LEDGES, RF_RIMEFROST_SUMMIT, RF_HERMITS_ICE_CAVE]
