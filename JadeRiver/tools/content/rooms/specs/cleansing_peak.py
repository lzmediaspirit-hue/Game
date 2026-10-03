"""E1 room specs: Cleansing Peak, east of Crane Falls (docs/architecture/room_engine.md; R1, the main story's path past
chapter 3). Chapter 4: Toward Cleansing Peak (the Stone Guardians on the Pilgrim Stairs) and The Rite (Heaven's
Cleansing on the summit's rite circle)."""
from content.rooms.spec import room

# The Pilgrim Stairs: the pilgrims' road from Crane Falls along the mountain's foot, the shrine at its start and the
# Temper drum on the meadow, then the great stair up the mountainside in three flights, a terrace after each (a Stone
# Guardian keeps every one), to the high path along the crags east to the summit. Pines on the terraces. The road's
# row is the one the side view's Iron Body trial calls its guardians to (x 600, 1600 and 2200: cells 18, 50 and 68).
CP_PILGRIM_STAIRS = room(
    "cp_pilgrim_stairs", size=(72, 30), biome="mountain",
    bands=[("crags", 0, 6, dict(level=8, paint="r", wall=True)), ("high_path", 2, 4, dict(level=6, paint="s", walk=True, x=33)),
           ("ridge", 6, 7, dict(level=4)), ("shoulder", 13, 8, dict(level=2)), ("foot", 21, 4, dict(level=0)),
           ("road", 25, 3, dict(paint="d", wavy=True)), ("meadow", 28, 2, dict(level=0))],
    features=[("flight_1", (33, 21, 6, 4), dict(rise=(0, 2))), ("flight_2", (33, 13, 6, 4), dict(rise=(2, 4))),
              ("flight_3", (33, 6, 6, 4), dict(rise=(4, 6))),
              ("landing_1", (31, 17, 10, 4), dict(paint="s")), ("landing_2", (31, 10, 10, 3), dict(paint="s"))],
    ways={"west": ("w", 26), "east": ("e", 3)},
    spawn="west",
    anchors={"shrine_cp": "foot@6", "temper_iron_cp_pilgrim_stairs": "foot@24", "jar_1": "verge.n@18",
             "crate_2": "landing_1@39", "jar_3": "high_path@62"},
    props=[("lantern", 32, 24), ("lantern", 39, 24), ("lantern", 32, 16), ("lantern", 39, 16), ("lantern", 32, 9),
           ("lantern", 39, 9)],
    flora={"ridge": dict(density=0.45), "shoulder": dict(density=0.45), "foot": dict(density=0.4)},
    foes=["auto:foot", "auto:landing_1", "auto:landing_2", "auto:high_path"])

# The Cleansing Summit: the peak's flat top above the clouds, a granite plaza with the rite circle in its middle and
# five stone pillars round it, the crags behind. Heaven's Cleansing calls its guardians to the side view's x 300 and
# 1000 on its ground line: cells 9 and 31 of row 26, the summit's south rim.
CP_CLEANSING_SUMMIT = room(
    "cp_cleansing_summit", size=(40, 28), biome="mountain",
    bands=[("crags", 0, 4, dict(level=3, paint="r", wall=True)), ("summit", 4, 24, dict(level=0))],
    features=[("plaza", (7, 6, 26, 17), dict(paint="s", shape="round")),
              ("pillar", (12, 9, 2, 2), dict(level=2, paint="s")), ("pillar_2", (19, 7, 2, 2), dict(level=2, paint="s")),
              ("pillar_3", (26, 9, 2, 2), dict(level=2, paint="s")), ("pillar_4", (13, 17, 2, 2), dict(level=2, paint="s")),
              ("pillar_5", (25, 17, 2, 2), dict(level=2, paint="s"))],
    ways={"west": ("w", 14)},
    spawn="west",
    anchors={"rite_cleansing": (20, 14)},
    props=[("incense", 19, 12), ("incense", 21, 12)],
    flora={"summit": dict(density=0.35)})

ROOMS = [CP_PILGRIM_STAIRS, CP_CLEANSING_SUMMIT]
