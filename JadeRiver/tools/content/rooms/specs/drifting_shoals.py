"""E1 room specs (R8): the Drifting Shoals, shallows of starlight pooled between low islets east of Lanternfall Harbor
(docs/architecture/room_engine.md). Chapter 17's Salt of the Stars (the Jellyfish Shallows), Will Manifest (the Moored
Hulks) and A Presence of One's Own (the Sparrow Reefs), and the Driftglass Bank on the lanes to Blackmast Haven. The
shallows are a floor a body wades (`h`, R2's); deep pools of the starsea lie in them and along the rooms' edges, the
islets are pale rock in rims of sand, driftglass and star crystals stand on them, reefs and banks rise a level or more."""
from content.rooms.spec import room
from content.rooms.specs.skysea import hull



def islet(name, x, y, w, h, rim=2, opts=None):
    """An islet in the shallows: a rim of sand round a core of pale rock, both round, the core `rim` cells in from the
    sand's edge (its anchors and flora name the core); `opts` raise the core (a level, a flight)."""
    core = dict(level=0, paint="r", shape="round")
    core.update(opts or {})
    return [(name + "_sand", (x, y, w, h), dict(paint="a", shape="round")),
            (name, (x + rim, y + rim, w - 2 * rim, h - 2 * rim), core)]


# The Jellyfish Shallows: east of the harbour the street's boards give out on the west islet, and the way on wades the
# shallows from islet to islet, the star jellyfish drifting over them. The middle islet holds a crag of rock (the two
# chests on its top), its star lotus on the sand; a small islet south of the way holds Lu's journal page; deep pools of
# the starsea break the shallows north and south, and the east islet runs on to the Moored Hulks.
DR_JELLYFISH_SHALLOWS = room(
    "dr_jellyfish_shallows", size=(64, 28), biome="star_shoals", base="h",
    bands=[("deep", 0, 4, dict(water=True, wavy=True)),
           ("deep_s", 24, 4, dict(water=True, wavy=True))],
    features=islet("islet_w", -6, 4, 22, 20, opts=dict(level=0))
             + [("rise_w", (2, 6, 8, 5), dict(level=1, paint="r", shape="round"))]
             + islet("islet", 19, 4, 18, 11)
             + [("crag", (24, 5, 8, 5), dict(level=2, paint="r", shape="round", flights=[28]))]
             + islet("islet_s", 33, 16, 12, 7)
             + islet("islet_e", 47, 6, 22, 18)
             + [("pool", (12, 18, 14, 6), dict(water=True, shape="round")),
                ("pool_2", (39, 3, 9, 6), dict(water=True, shape="round")),
                ("path", (0, 14, 64, 3), dict(walk=True))],          # south of the crag's flight
    stairs="auto",
    ways={"west": ("w", "path"), "east": ("e", "path")},
    spawn="west",
    anchors={"sign_dr_shallows": "path.n@4", "jar_2": "rise_w@6", "jar_3": "islet_w@13", "swarm_starwing_mote": "path.s@22",
             "chest_ledge_mv_1": "crag@27", "chest_cloud_mv": "crag@30", "herb_1": "islet@33", "jar_4": "path.n@40",
             "journal_jellyfish": "islet_s@39", "jar_5": "islet_e@57"},
    props=[("star_lantern", 2, 11), ("star_lantern", 2, 16), ("driftglass", 46, 11), ("star_crystal", 61, 9)],
    flora={"islet_w": dict(density=0.4), "islet": dict(density=0.45), "islet_s": dict(density=0.5),
           "islet_e": dict(density=0.4), "crag": dict(density=0.3), "rise_w": dict(density=0.3),
           "deep": {"kinds": ["lotus_pads"], "density": 0.2}, "pool": {"kinds": ["lotus_pads", "cattails"], "density": 0.4}},
    foes="auto")


# The Moored Hulks: two old hulls beached on an islet in the shallows, where Old Bo keeps house. The west hulk's deck is
# his: the shrine at its stern and his planters lashed to the boards; he cooks on the islet between the hulks, star
# lanterns round the camp. The way wades on east and west; the pier at the east end runs out to the deep water, where
# the sky-skiff for the Wyrmnest Isles is moored.
DR_MOORED_HULKS = room(
    "dr_moored_hulks", size=(48, 28), biome="star_shoals", base="h",
    bands=[("deep", 0, 3, dict(water=True, wavy=True)),
           ("deep_s", 23, 5, dict(water=True, wavy="n"))],
    features=islet("islet", 2, 3, 44, 19)
             + hull("hulk", 4, 3, 13, 7, dict(level=2, paint="w", flights=[12]), bow=6)
             + hull("hull_e", 30, 4, 9, 6, dict(level=2, paint="w", flights=[34]), bow=4, stern=2)
             + [("cabin", (4, 3, 5, 4), dict(level=3, paint="w")),                  # Old Bo's cabin at the stern
                ("path", (0, 14, 48, 3), dict(walk=True)),
                ("pier", (40, 17, 4, 11), dict(level=1, paint="w"))],
    stairs="auto",
    ways={"west": ("w", "path"), "east": ("e", "path"), "wyrm_skiff": ("s", 42)},
    spawn="west",
    anchors={"shrine_dr_hulks": "hulk@11", "bed_dr_0": "hulk@15", "bed_dr_1": "hulk@18", "npc_hulk_keeper_bo": "path.n@25"},
    props=[("stove", 23, 10), ("water_jar", 26, 10), ("barrel", 21, 10), ("crates", 22, 17), ("sacks", 24, 17),
           ("star_lantern", 12, 12), ("star_lantern", 30, 12), ("lantern_red", 20, 12), ("lantern_red", 39, 12),
           ("star_lantern", 39, 17), ("star_lantern", 44, 17), ("post", 40, 27), ("post", 43, 27), ("boat", 44, 25),
           ("black_mast", 13, 8), ("broken_mast", 35, 8), ("driftglass", 4, 19)],
    flora={"islet": dict(density=0.3), "deep": {"kinds": ["lotus_pads"], "density": 0.2}},
    foes="auto")


# The Sparrow Reefs: reefs of rock stand out of the shallows here, the comet sparrows nesting on them. The way wades
# between them; the west reef climbs a level (a jar), the high reef in the middle two and a third on its stack (the
# chest), the east reef two (a jar); Lu's journal page lies on a sandbar under the stack, the star geckos' trail on the
# west islet.
DR_SPARROW_REEFS = room(
    "dr_sparrow_reefs", size=(64, 28), biome="star_shoals", base="h",
    bands=[("deep", 0, 3, dict(water=True, wavy=True)),
           ("deep_s", 24, 4, dict(water=True, wavy=True))],
    features=islet("islet_w", -4, 3, 16, 20)
             + islet("reef", 12, 3, 14, 10, opts=dict(level=1, flights=[18]))
             + islet("reef_mid", 26, 3, 12, 9, opts=dict(level=2, flights=[33]))
             + [("stack", (28, 4, 5, 3), dict(level=3, paint="r", flights=[30]))]
             + islet("reef_e", 37, 3, 14, 10, opts=dict(level=2, flights=[43]))
             + islet("bar", 24, 15, 12, 7)
             + islet("islet_e", 50, 5, 18, 18)
             + [("pool", (6, 18, 12, 6), dict(water=True, shape="round")),
                ("pool_2", (42, 18, 8, 6), dict(water=True, shape="round")),
                ("path", (0, 15, 64, 3), dict(walk=True))],          # south of the reefs' flights
    stairs="auto",
    ways={"west": ("w", "path"), "east": ("e", "path")},
    spawn="west",
    anchors={"trail_star_gecko": "islet_w@5", "jar_1": "reef@17", "chest_cloud_mv": "stack@30", "journal_reefs": "bar@29",
             "swarm_starwing_mote": "path.s@36", "jar_2": "reef_e@42", "jar_3": "reef_e@46", "jar_4": "islet_e@56"},
    props=[("star_crystal", 21, 5), ("star_crystal", 47, 4), ("driftglass", 9, 8), ("driftglass", 58, 18)],
    flora={"islet_w": dict(density=0.45), "reef": dict(density=0.4), "reef_mid": dict(density=0.3),
           "reef_e": dict(density=0.4), "bar": dict(density=0.5), "islet_e": dict(density=0.4),
           "deep": {"kinds": ["lotus_pads"], "density": 0.2}, "pool": {"kinds": ["lotus_pads", "cattails"], "density": 0.4}},
    foes="auto")


# The Driftglass Bank: a long bank of rock and grit where the tides leave their glass, the shallows round it. A ridge of
# glass-veined rock along the north (its two veins of driftglass ore at the foot), and on it the glass crags (three
# chests on the high one); the lens of driftglass the tides set upright stands in the middle of the bank, the insight
# stone. The way runs the length of the bank east toward the lanes to Blackmast Haven.
DR_DRIFTGLASS_BANK = room(
    "dr_driftglass_bank", size=(64, 28), biome="star_shoals", base="h",
    bands=[("ridge", 0, 4, dict(level=3, paint="r", wall=True, wavy="s")),
           ("deep_s", 24, 4, dict(water=True, wavy=True))],
    features=islet("flat", -4, 4, 72, 19, rim=2)
             + [("rise", (2, 4, 10, 6), dict(level=1, paint="r", shape="round", flights=[7])),
                ("ledge", (18, 4, 10, 5), dict(level=2, paint="r", shape="round", flights=[23])),
                ("crag", (33, 3, 10, 6), dict(level=3, paint="r", shape="round", flights=[38])),
                ("lens", (26, 10, 7, 5), dict(paint="a", shape="round")),
                ("pool", (46, 18, 10, 5), dict(water=True, shape="round")),
                ("path", (0, 15, 64, 3), dict(walk=True))],          # south of the crags' flights
    stairs="auto",
    ways={"west": ("w", "path"), "east": ("e", "path")},
    spawn="west",
    anchors={"herb_1": "rise@5", "jar_4": "rise@9", "trail_star_gecko": "path.s@18", "jar_5": "ledge@23",
             "insight_star": "lens@29", "ore_2": "wall_foot@31", "jar_6": "path.s@33", "chest_9": "crag@35",
             "chest_cloud_mv": "crag@38", "chest_ledge_mv_1": "crag@41", "jar_7": "path.n@45", "swarm_starwing_mote": "path.s@44",
             "ore_3": "wall_foot@53", "jar_8": "flat@58"},
    props=[("star_crystal", 14, 4), ("star_crystal", 45, 5), ("star_crystal", 61, 4), ("driftglass", 25, 14),
           ("driftglass", 33, 14)],
    flora={"flat": dict(density=0.45), "rise": dict(density=0.3), "ledge": dict(density=0.3), "crag": dict(density=0.3),
           "ridge": {"kinds": ["star_crystal", "driftglass", "rock_mossy"], "density": 0.5},
           "pool": {"kinds": ["lotus_pads", "cattails"], "density": 0.4}},
    foes="auto")

ROOMS = [DR_JELLYFISH_SHALLOWS, DR_MOORED_HULKS, DR_SPARROW_REEFS, DR_DRIFTGLASS_BANK]
