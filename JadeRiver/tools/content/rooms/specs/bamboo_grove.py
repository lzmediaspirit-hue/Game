"""E1 room specs: the Bamboo Grove, east of the Sunken Causeway (docs/architecture/room_engine.md; R1, the main story's
path past chapter 3). Two Hands Full is played in the Thicket Heart; chapter 4's road east runs through both rooms."""
from content.rooms.spec import room

# The Whispering Bamboo: the path east from the marsh winds through tall bamboo, the grove climbing north to a bamboo
# hill with three rock knolls in it (jars on the west one, the chest on the east one's top), and falling south to a
# still pond where the cicadas sing and a ferret's trail runs.
BG_WHISPERING_BAMBOO = room(
    "bg_whispering_bamboo", size=(60, 30), biome="bamboo",
    bands=[("hill", 0, 4, dict(level=2, paint="g")), ("grove_n", 4, 8, dict(level=1, paint="g")),
           ("path", 13, 3, dict(paint="d", wavy=True)), ("grove_s", 16, 14, dict(level=0))],
    features=[("knoll_w", (8, 5, 7, 3), dict(level=2, paint="r")), ("knoll_mid", (23, 4, 7, 4), dict(level=2, paint="r")),
              ("knoll_e", (37, 5, 7, 3), dict(level=2, paint="r")),
              ("pond", (16, 20, 16, 8), dict(water=True, shape="round"))],
    stairs="auto",
    ways={"west": ("w", 14), "east": ("e", 14)},
    spawn="west",
    anchors={"herb_1": "grove_n@4", "jar_4": "grove_n@7", "jar_5": "knoll_w@11", "chest_bamboo_top": "knoll_e@40",
             "jar_6": "knoll_mid@26", "herb_3": "grove_n@50", "jar_8": "verge.n@44", "jar_9": "verge.s@53",
             "herb_2": "bank@31", "jar_7": "verge.s@35", "swarm_reed_cicada": "pond.n@24", "trail_reed_ferret": "grove_s@44",
             "rift_tear": "grove_s@36", "spirit_fruit_tree": "grove_s@10"},
    flora={"hill": dict(density=0.55), "grove_n": dict(density=0.6), "grove_s": dict(density=0.5)},
    foes="auto")

# The Thicket Heart: the grove's densest part, thorn thickets either side of the path, and the canopy decks the hunters
# built up in the bamboo, low and high by turns, with ladders: jars on the low ones, the beast nests on the two high
# ones (the chest on the east one), the hundred-year ember pepper on the middle high deck. The thornback boars keep the
# clearing south of the path.
BG_THICKET_HEART = room(
    "bg_thicket_heart", size=(60, 30), biome="bamboo",
    bands=[("thicket_n", 0, 12, dict(level=0)), ("path", 13, 3, dict(paint="d", wavy=True)),
           ("thicket_s", 16, 14, dict(level=0))],
    features=[("canopy_west", (2, 7, 7, 3), dict(level=1, paint="w")), ("canopy_high_west", (11, 3, 8, 4), dict(level=2, paint="w")),
              ("canopy_mid", (21, 7, 7, 3), dict(level=1, paint="w")), ("route_2", (30, 3, 8, 4), dict(level=2, paint="w")),
              ("canopy_east", (39, 7, 7, 3), dict(level=1, paint="w")), ("canopy_high_east", (48, 3, 9, 4), dict(level=2, paint="w")),
              ("clearing", (20, 18, 22, 9), dict(paint="d", shape="round"))],
    stairs="auto",
    ways={"west": ("w", 14), "east": ("e", 14)},
    spawn="west",
    anchors={"jar_3": "canopy_west@5", "beast_nest_0": "canopy_high_west@14", "jar_4": "canopy_mid@24",
             "rare_pepper_th": "route_2@33", "herb_1": "canopy_east@42", "beast_nest_1": "canopy_high_east@53",
             "chest_8": "canopy_high_east@50", "herb_2": "thicket_s@47", "jar_5": "verge.s@30", "jar_6": "verge.s@41",
             "jar_7": "verge.n@56", "swarm_jade_scarab": "thicket_s@15", "rift_tear": "clearing@33",
             "spirit_fruit_tree": "clearing@25"},
    flora={"thicket_n": dict(density=0.6), "thicket_s": dict(density=0.6)},
    areas=[{"kind": "thorns", "rect": r} for r in ([12, 11, 4, 2], [27, 16, 4, 2], [44, 11, 4, 2], [52, 16, 4, 2])],
    foes="auto")

ROOMS = [BG_WHISPERING_BAMBOO, BG_THICKET_HEART]
