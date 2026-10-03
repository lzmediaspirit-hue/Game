"""E1 room specs (R4, the peaks): Summit Ridge, past the Forgotten Monastery's west gate (docs/architecture/room_engine.md).
The snow line: the Windswept Ridge and the Frozen Shrine (Beyond the Valley ends here, at Lu's map; the frost shrine's
lost art, the summit's moneychanger). The biome's snow covers every floor and the walks are trodden to packed snow
(decision 44); Act II's Rimefrost Heights takes the same ground."""
from content.rooms.spec import room

# The Windswept Ridge: a knife-edge crest under the last peaks, the trail of packed snow along it. North of the crest a
# snowfield a step down lies at the cliffs' feet (the ore veins); on the crest three wind-carved tors (the jars and,
# on the highest, the chest); south of it the ridge falls in two snowy steps toward the clouds. Dead trees bent by the
# wind, boulders, a few pines.
SR_WINDSWEPT_RIDGE = room(
    "sr_windswept_ridge", size=(72, 30), biome="snowfield", level=1,
    bands=[("crown", 0, 3, dict(level=6, paint="r", wall=True)),
           ("north_field", 3, 10, dict(level=2)),
           ("drop", 23, 7, dict(level=0)),
           ("flank", 17, 8, dict(level=1, wavy="s")),
           ("crest", 10, 10, dict(level=3, wavy=True, flights=[14, 54])),
           ("trail", 15, 3, dict(paint="d", walk=True))],
    features=[("tor_w", (16, 9, 8, 5), dict(level=4, shape="round")),
              ("tor", (25, 9, 9, 5), dict(level=4, shape="round")),
              ("tor_e", (37, 9, 8, 5), dict(level=4, shape="round"))],
    stairs="auto",
    ways={"east": ("e", "trail"), "west": ("w", "trail")},
    spawn="east",
    anchors={"ore_1": "wall_foot@14", "ore_2": "wall_foot@55", "jar_3": "tor_w@20", "chest_cloud_mv": "tor.top",
             "jar_4": "tor_e@40", "jar_5": "verge.s@44", "jar_6": "north_field@62", "rift_tear": "flank@40",
             "spirit_fruit_tree": "flank@24"},
    flora={"crest": dict(density=0.34), "flank": dict(density=0.34)},
    foes="auto")

# The Frozen Shrine: an old shrine court on the summit's shoulder, paved stone the snow never settles on. The frost
# shrine's altar at the back of the court (its lost art), the moneychanger's altar and the chest on it, stone lanterns
# at its corners; the shrine itself, where a traveller prays, at the terrace's east end by the trail; Lu's journal page
# on the trail's edge; the ledges of the terrace either side (the ore, the jars), and the snowy slope under the trail.
SR_FROZEN_SHRINE = room(
    "sr_frozen_shrine", size=(56, 30), biome="snowfield", level=1,
    bands=[("crown", 0, 4, dict(level=6, paint="r", wall=True)),
           ("terrace", 4, 9, dict(level=2, wavy="s", flights=[8, 47])),
           ("path", 14, 3, dict(paint="d", walk=True)),
           ("drop", 23, 7, dict(level=0)),
           ("flank", 17, 7, dict(level=1, wavy="s"))],
    features=[("court", (15, 5, 25, 7), dict(level=3, paint="p", flights=[27]))],
    stairs="auto",
    ways={"east": ("e", "path"), "west": ("w", "path")},
    spawn="east",
    anchors={"ore_1": "wall_foot@7", "jar_2": "terrace@11", "jar_3": "terrace@45", "jar_4": "verge.s@11",
             "jar_5": "verge.s@53", "shrine_frozen": "terrace@51", "lost_frost_shrine": "court.back@27",
             "exchange_summit": "court@33", "chest_ledge_mv_1": "court@21", "rare_soulbell_fs": "terrace@4",
             "journal_frozen": "verge.s@38", "rift_tear": "flank@31", "spirit_fruit_tree": "flank@20"},
    props=[("lantern", 16, 5), ("lantern", 38, 5), ("lantern", 16, 10), ("lantern", 38, 10), ("incense", 29, 5)],
    flora={"terrace": dict(density=0.34), "flank": dict(density=0.34)},
    foes="auto")

ROOMS = [SR_WINDSWEPT_RIDGE, SR_FROZEN_SHRINE]
