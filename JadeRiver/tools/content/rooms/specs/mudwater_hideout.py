"""E1 room specs: the Mudwater Hideout, north of the Caravan Road (docs/architecture/room_engine.md). Chapter 3's
dungeon: the bandits' stockade, the tunnels under the hill, the loot cave and Big Toad Tan's den."""
from content.rooms.spec import room

# The Stockade: the bandits' yard of trampled earth inside a timber palisade under the hill, the gate in from the
# Caravan Road in the west, a watchtower at each end of the yard (the key on the west one's top), the barracks and the
# store, and the tunnel into the hill in the east.
MH_STOCKADE = room(
    "mh_stockade", size=(56, 28), biome="stockade", base="g",
    bands=[("hill", 0, 4, dict(level=3, paint="r", wall=True)),
           ("yard", 4, 20, dict(level=0, paint="d")),
           ("palisade", 24, 2, dict(level=2, paint="w", wall=True))],
    features=[("palisade_w", (0, 4, 2, 20), dict(level=2, paint="w")),
              ("gate", (0, 11, 2, 5), dict(level=0, paint="d")),
              ("hill_e", (51, 4, 5, 20), dict(level=3, paint="r")),
              ("tunnel", (51, 12, 5, 4), dict(level=0, paint="d")),
              ("track", (2, 12, 49, 4), dict(walk=True)),
              ("weeds", (2, 20, 49, 4), dict(paint="g")),
              ("tower_w", (8, 5, 5, 4), dict(level=2, paint="w")),
              ("tower_e", (40, 5, 5, 4), dict(level=2, paint="w"))],
    stairs="auto",
    ways={"west": ("w", 13), "east": ("e", 13)},
    spawn="west",
    anchors={"tower_key": "tower_w@9", "chest_ledge_mv_1": "tower_w@11", "chest_6": "tower_e@42", "jar_1": "track.n@17",
             "crate_2": "track.n@36", "jar_3": "track.s@6", "crate_4": "track.s@28", "jar_5": "track.s@48"},
    props=[("house", 17, 5), ("storehouse", 27, 5), ("lantern_red", 15, 10), ("lantern_red", 33, 10),
           ("barrel", 24, 8), ("crates", 31, 9), ("barrel", 46, 6), ("weapon_rack", 4, 6), ("post", 22, 17),
           ("post", 25, 18), ("crates", 3, 18), ("barrel", 48, 17), ("sacks", 47, 18)],
    flora={"weeds": dict(density=0.45)},
    foes=["auto", "auto", "auto:tower_w", "auto:tower_e"])


# The Tunnels: the bandits' track through the hill from the stockade to the loot cave, three caverns worn round by the
# water, the middle one with a rock ledge where the archers keep the chest, seep pools, and three vents where the marsh
# gas pools (poison mist).
MH_TUNNELS = room(
    "mh_tunnels", size=(56, 28), biome="cave", level=4,
    features=[("west_gallery", (0, 8, 19, 11), dict(level=0, paint="d", shape="round")),
              ("cavern", (13, 3, 30, 22), dict(level=0, paint="d", shape="round")),
              ("east_gallery", (38, 6, 18, 14), dict(level=0, paint="d", shape="round")),
              ("track", (0, 12, 56, 3), dict(level=0, paint="d", walk=True)),
              ("ledge", (22, 4, 12, 4), dict(level=1, paint="r")),
              ("seep", (17, 16, 6, 4), dict(water=True, shape="round")),
              ("seep_2", (33, 16, 5, 3), dict(water=True, shape="round"))],
    stairs="auto",
    ways={"west": ("w", 13), "east": ("e", 13)},
    spawn="west",
    anchors={"chest_7": "ledge@30", "jar_4": "ledge@25", "ore_1": "east_gallery.back@48", "jar_2": "track.s@24",
             "crate_3": "track.n@37", "crate_5": "track.n@8", "jar_6": "track.s2@49"},
    props=[("lantern", 5, 11), ("lantern", 18, 11), ("lantern", 30, 15), ("lantern", 44, 11), ("barrel", 12, 16),
           ("crates", 42, 16)],
    areas=[{"kind": "poison_mist", "rect": [11, 15, 4, 3]}, {"kind": "poison_mist", "rect": [27, 16, 4, 3]},
           {"kind": "poison_mist", "rect": [40, 9, 4, 3]}],
    # T2 (docs/architecture/topdown_mechanics.md): the side view's two spike pits across the track, each laid over with
    # three rotten planks that are the track's floor: a foot that lingers on one sends it down into the pit, and the
    # pit's spikes strike the body that falls in (it is back on its last safe spot); the planks are back in five seconds.
    traverse=[("crumble", "plank_%s_crumble" % p, dict(rect=(x, 12, 2, 3), level=0, under="pit"))
              for p, x in (("a0", 19), ("a1", 21), ("a2", 23), ("b0", 33), ("b1", 35), ("b2", 37))]
             + [("hazard", "spike_pit_a", dict(rect=(19, 12, 6, 3))), ("hazard", "spike_pit_b", dict(rect=(33, 12, 6, 3)))],
    foes=["auto:ledge", "auto", "auto", "auto"])


# The Loot Cave: a long cave under the hill heaped with what the Mudwater gang has taken off the road (crates, sacks,
# bolts of cloth), a ledge at each end where an archer keeps watch, the chest on the middle ledge, and Lieutenant Kuai
# by the hoard at the east end.
MH_LOOT_CAVE = room(
    "mh_loot_cave", size=(56, 28), biome="cave", level=4,
    features=[("hall", (1, 3, 54, 22), dict(level=0, paint="d", shape="round")),
              ("track", (0, 12, 56, 3), dict(level=0, paint="d", walk=True)),
              ("ledge_w", (8, 5, 9, 4), dict(level=1, paint="r")),
              ("ledge_mid", (22, 4, 8, 4), dict(level=1, paint="r")),
              ("ledge_e", (35, 5, 9, 4), dict(level=1, paint="r")),
              ("hoard", (41, 17, 11, 5), dict(level=0, paint="w")),
              ("pool", (13, 17, 8, 4), dict(water=True, shape="round"))],
    stairs="auto",
    ways={"west": ("w", 13), "east": ("e", 13)},
    spawn="west",
    anchors={"chest_6": "ledge_mid@25", "jar_1": "ledge_w@12", "crate_2": "ledge_e@40", "jar_3": "track.s@6",
             "crate_4": "track.s@31", "jar_5": "track.n@48", "page_method_conversion_pill_1": "track.s2@26"},
    props=[("crates", 42, 18), ("sacks", 45, 18), ("cloth_bolts", 47, 18), ("barrel", 50, 18), ("crates", 43, 20),
           ("sacks", 49, 20), ("water_jar", 51, 20), ("lantern_red", 5, 11), ("lantern_red", 19, 11),
           ("lantern_red", 33, 11), ("lantern_red", 47, 11), ("weapon_rack", 24, 17), ("barrel", 9, 17)],
    foes=["auto", "auto:ledge_w", "auto:hoard", "auto:ledge_e"])


# The Boss Den: Big Toad Tan's cavern, a mud wallow in its middle ringed by marsh weed, his wine jars along the back
# wall, his strongbox by the tunnel back out to the Caravan Road in the east.
MH_BOSS_DEN = room(
    "mh_boss_den", size=(48, 28), biome="cave", level=4,
    features=[("den", (3, 3, 42, 22), dict(level=0, paint="d", shape="round")),
              ("entry", (0, 11, 8, 5), dict(level=0, paint="d", walk=True)),
              ("way_out", (38, 15, 10, 5), dict(level=0, paint="d")),
              ("wallow_bank", (15, 10, 14, 9), dict(paint="m", shape="round")),
              ("wallow", (17, 11, 10, 7), dict(water=True, shape="round"))],
    ways={"west": ("w", 13), "exit": ("e", 17)},
    spawn="west",
    anchors={"toad_wine_0": "den.back@12", "toad_wine_1": "den.back@23", "toad_wine_2": "den.back@34",
             "chest_1": "way_out@43"},
    props=[("lantern_red", 7, 9), ("lantern_red", 7, 17), ("lantern_red", 37, 7), ("lantern_red", 37, 21),
           ("water_jar", 16, 5), ("water_jar", 30, 5)],
    flora={"wallow_bank": ["cattails", "ferns", "tall_grass"], "density": 0.3},
    foes="auto")

ROOMS = [MH_STOCKADE, MH_TUNNELS, MH_LOOT_CAVE, MH_BOSS_DEN]
