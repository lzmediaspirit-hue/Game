"""E1 room specs (R7, Act II's chapter 14): the Sunscar Desert, down the Clan Hearth's desert road
(docs/architecture/room_engine.md, "Nine Peaks to the Tomb of Sunscar (R7)"). The Glass Dunes, the Scorpion Flats, the
Oasis of Bones and the Worm Sea, where the Tomb of Sunscar's portal lies half drowned in the sand. Decision 44's sand
over everything (`desert`), the caravan track trodden red earth through it; dunes and sandstone outcrops rise a level or
two over the floor, cactus, scrub and bleached bones on them, palms and reeds only round the oasis's water."""
from content.rooms.spec import room


def dunes(*shapes, level=1, crests=True):
    """Dunes: round humps of sand `level` levels over the floor, each a shape (x, y, w, h), laid again under one name;
    on each (`crests`) its crest a level higher, half its size and drawn toward its north (the wind's side), so a dune
    reads as a swell and not a table."""
    out = [("dune", r, dict(level=level, shape="round")) for r in shapes]
    if crests:
        out += [("dune_top", (x + w // 4, y + 1, w // 2, max(3, h // 2)), dict(level=level + 1, shape="round"))
                for x, y, w, h in shapes]
    return out


RIDGE = dict(level=4, wall=True, wavy="s")   # the sandstone ridge along a room's north edge


# The Glass Dunes: the desert road from Ironroot comes down out of the rocks in the west and runs east between the dunes,
# the sun striking glints off the sand-glass. A sandstone ridge along the north (the sunglass ore at its foot), dunes
# under it where the ember cactus grows and the jars and a chest are left on their crests; the spirit lode and a sand
# fox's trail among the dunes south of the road, Lu's page by it, a giant's ribs half sunk in the sand.
SD_GLASS_DUNES = room(
    "sd_glass_dunes", size=(72, 28), biome="desert",
    bands=[("ridge", 0, 4, RIDGE),
           ("road", 13, 3, dict(walk=True))],
    features=dunes((4, 4, 22, 8), (48, 4, 16, 8), (6, 18, 20, 8), (44, 18, 22, 8))
             + [("crest", (29, 3, 15, 6), dict(level=2, shape="round", flights=[36]))],
    stairs="auto",
    ways={"west": ("w", "road"), "east": ("e", "road")},
    spawn="west",
    anchors={"sign_sd": "verge.n@6", "herb_1": "dune@15", "jar_4": "dune@20", "jar_5": "crest@35",
             "chest_ledge_mv_1": "crest@39", "herb_2": "verge.s@35", "trail_sand_fox": "dune_3@21",
             "mine_glass_dunes_lode": (28, 20), "swarm_ember_locust": "verge.n@44", "jar_6": "verge.s@46",
             "journal_dunes": "dune_4@52", "ore_3": "wall_foot@61", "jar_7": "verge.n@65"},
    props=[("ribcage", 30, 21), ("ribcage", 8, 10)],
    flora={"dune": dict(density=0.32), "crest": dict(density=0.3), "density": 0.2},
    foes="auto")


# The Scorpion Flats: a pan of baked sand between low ridges where the sandstorm scorpions hunt. A sandstone outcrop
# stands out of the flats north of the track (the ember cactus, a jar and the chest on its top, a plank stair up it), a
# shrine's shade by the track, an earth vent smoking in the west, the ore at the ridge's foot; dunes to the south.
SD_SCORPION_FLATS = room(
    "sd_scorpion_flats", size=(72, 28), biome="desert",
    bands=[("ridge", 0, 3, dict(RIDGE, level=3)),
           ("road", 14, 3, dict(walk=True))],
    features=[("outcrop", (22, 3, 16, 7), dict(level=2, shape="round", flights=[30])),
              ("rock", (1, 3, 8, 6), dict(level=1, shape="round", flights=[4]))]
             + dunes((40, 20, 20, 7), (4, 20, 16, 7), (60, 4, 12, 8)),
    stairs="auto",
    ways={"west": ("w", "road"), "east": ("e", "road")},
    spawn="west",
    anchors={"jar_5": "rock@4", "earth_vent_sd": "verge.s@13", "herb_1": "outcrop@26", "jar_4": "outcrop@29",
             "chest_8": "outcrop@33", "swarm_ember_locust": "verge.s@32", "ore_2": "wall_foot@41",
             "shrine_sd_flats": "verge.n@45", "jar_6": "verge.s@46", "trail_sand_fox": "verge.s@52",
             "ore_3": "wall_foot@58", "jar_7": "verge.s@62"},
    props=[("ribcage", 48, 8), ("ribcage", 14, 24)],
    flora={"outcrop": dict(density=0.3), "dune": dict(density=0.3), "density": 0.16},
    foes="auto")


# The Oasis of Bones: the desert's one water, a round pool in a ring of grass and reeds under date palms, the bones of
# old beasts bleaching on the dunes round it. The keeper's yurt and cooking fire in the west, the shrine and the Qi
# spring at the pool's north edge, the bone-reader's mat in the east by the teleport stone; the track between them.
SD_OASIS_OF_BONES = room(
    "sd_oasis_of_bones", size=(56, 28), biome="desert",
    bands=[("ridge", 0, 3, dict(RIDGE, level=3)),
           ("road", 10, 3, dict(walk=True))],
    features=[("green", (14, 12, 28, 15), dict(shape="round")),
              ("pool", (19, 15, 18, 9), dict(water=True, shape="round"))]
             + dunes((0, 3, 12, 7), (44, 3, 12, 7), (1, 19, 12, 7), (44, 19, 12, 7)),
    stairs="auto",
    ways={"west": ("w", "road"), "east": ("e", "road")},
    spawn="west",
    anchors={"npc_oasis_keeper_meng": "verge.s@10", "lost_oasis_mirage": "verge.s@16", "shrine_oasis": "verge.n@26",
             "spring_oasis": (30, 14), "page_sovereign_settling_pill_4": "verge.s@39",
             "npc_bone_reader_xiu": "verge.n@43", "stone_sunscar": "verge.s@47"},
    props=[("yurt", 4, 13), ("stove", 8, 16), ("water_jar", 10, 16), ("ribcage", 6, 5), ("ribcage", 46, 22),
           ("palm", 17, 15), ("palm", 38, 15), ("palm", 15, 21), ("palm", 40, 21), ("palm", 22, 25), ("palm", 34, 24),
           ("mat", 41, 7), ("incense", 44, 6)],
    flora={"pool": dict(kinds=["palm", "tall_grass", "cattails", "lotus_pads"], density=0.5),
           "green": ["palm", "tall_grass", "bush"], "dune": dict(density=0.3), "density": 0.2},
    ground={"sand": ["*", "-green"], "earth": ["walk"]},
    foes="auto")


# The Worm Sea: the dunes roll on east like a sea, the dune worms swimming under them, quicksand in three hollows; the
# track runs out to the Tomb of Sunscar, a stepped portal half drowned in a mound of sand in the north-east, sand kings
# of stone either side of its door. A ridge of sandstone along the north (the ore at its foot), the crests where the
# jars and the chest wait, the ribs of dead worms bleaching on the sand.
SD_WORM_SEA = room(
    "sd_worm_sea", size=(72, 28), biome="desert",
    bands=[("ridge", 0, 3, dict(RIDGE, level=3)),
           ("road", 14, 3, dict(walk=True, w=66))],
    features=dunes((18, 3, 16, 9), (40, 19, 18, 7), (2, 19, 14, 7), (2, 3, 12, 8))
             + [("crest", (34, 3, 14, 7), dict(level=2, shape="round", flights=[40])),
                ("mound", (56, 0, 16, 11), dict(level=3, shape="round")),
                ("portal", (61, 5, 9, 6), dict(level=3, paint="p")),           # the portal's dressed stone in the mound
                ("doorway", (64, 8, 2, 3), dict(level=0, paint="p")),          # its door, sunk in the sand
                ("approach", (60, 11, 12, 6), dict(walk=True))],
    stairs="auto",
    ways={"west": ("w", "road"), "tomb": dict(at=(64.5, 8), dir="n", arrive=(64.5, 12), span=2)},
    spawn="west",
    anchors={"herb_1": "dune@26", "jar_3": "dune@30", "jar_4": "crest@37", "chest_ledge_mv_1": "crest@42",
             "swarm_ember_locust": "verge.s@45", "jar_5": "verge.s@48", "ore_2": "wall_foot@54", "jar_6": "verge.s@62"},
    props=[("king_statue", 62, 11), ("king_statue", 68, 11), ("brazier", 61, 13), ("brazier", 69, 13),
           ("ribcage", 22, 22), ("ribcage", 50, 9), ("ribcage", 8, 13)],
    flora={"dune": dict(density=0.3), "crest": dict(density=0.3), "mound": ["dry_scrub", "red_rock"], "density": 0.16},
    areas=[{"kind": "quicksand", "rect": r} for r in ([14, 18, 4, 3], [30, 21, 4, 3], [50, 17, 4, 3])],
    foes="auto")

ROOMS = [SD_GLASS_DUNES, SD_SCORPION_FLATS, SD_OASIS_OF_BONES, SD_WORM_SEA]
