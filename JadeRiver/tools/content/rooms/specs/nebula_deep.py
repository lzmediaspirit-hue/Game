"""E1 room specs (R9, Act III's chapter 22): the Nebula Deep, the drowned sky past the Drone Hive where the nebula runs
like a sea (docs/architecture/room_engine.md, "The star field's end (R9)"). The Nebula Verge, the Eel Currents, the Crab
Grottoes where Lu left his star notes, and the Leviathan's Maw. Reefs of dark rock round the nebula's luminous water
(the grid's water: the nebula's own glow is a paint the kit does not have), the trodden way along them pale nebula sand
(sand's paint), coral trees with their pink and cyan crowns and nebula coral on the reefs, star crystals, void crabs'
cast shells, islets of coral out on the water; the reef cliffs along the north."""
from content.rooms.spec import room

REEF = dict(level=4, paint="r", wall=True, wavy="s")   # the reef cliffs along the north, past a hop from any rise
WAY = dict(paint="a", walk=True)                       # the way of pale nebula sand


def islets(*rects):
    """Islets of reef out on the nebula, round, a coral tree or two on each (their flora), reached by no one."""
    return [("islet", r, dict(level=0, paint="r", shape="round")) for r in rects]


# The Nebula Verge: where the grey of the Drone Hive gives out and the dark thins into the nebula. The way comes in from
# the hive in the west over grey rock, dead trees and grey reeds still about it, and runs east along the shore, the
# nebula's water opening to the south with islets of coral on it, coral growing thicker eastward; two reef rises north of
# the way (a jar and a crate on them), the star lotus at the water's edge, the shrine by the way where the grey ends.
ND_NEBULA_VERGE = room(
    "nd_nebula_verge", size=(72, 28), biome="nebula",
    bands=[("reef", 0, 3, REEF),
           ("road", 12, 3, WAY),
           ("nebula", 20, 8, dict(water=True, wavy="n"))],
    features=[("grey", (0, 3, 15, 17), dict(level=0, paint="r")),
              ("rise", (15, 3, 10, 6), dict(level=1, paint="r", shape="round")),
              ("rise_2", (37, 3, 11, 7), dict(level=2, paint="r", shape="round")),
              ("inlet", (28, 16, 12, 6), dict(water=True, shape="round")),
              ("inlet_2", (56, 15, 10, 7), dict(water=True, shape="round"))]
             + islets((44, 22, 6, 4), (22, 23, 5, 4), (62, 24, 6, 3)),
    stairs="auto",
    ways={"west": ("w", "road"), "east": ("e", "road")},
    spawn="west",
    anchors={"shrine_nd_verge": "verge.s@11", "jar_2": "rise@19", "herb_1": "bank@37", "crate_3": "rise_2@42",
             "jar_4": "verge.s@46", "crate_5": "verge.s@62"},
    props=[("void_shell", 50, 17), ("star_crystal", 33, 6), ("star_crystal", 53, 5)],
    flora={"grey": {"kinds": ["dead_tree", "grey_reeds", "rock_small", "grey_reeds", "dead_tree"], "density": 0.45},
           "rise": dict(density=0.4), "rise_2": dict(density=0.4), "reef": dict(density=0.5),
           "islet": {"kinds": ["coral_tree", "nebula_coral"], "density": 1.2}, "nebula": ["coral_tree", "nebula_coral"],
           "inlet": ["nebula_coral", "coral_tree"], "inlet_2": ["nebula_coral", "coral_tree"], "density": 0.32},
    foes="auto")


# The Eel Currents: three channels of the nebula run north to south across the reef to the open water, the way crossing
# each on a causeway of sand; the eels hunt the reefs between. A reef rise and a stack of rock either side of the middle
# channel, the jar, the crate and the chest left on them.
ND_EEL_CURRENTS = room(
    "nd_eel_currents", size=(72, 28), biome="nebula",
    bands=[("reef", 0, 3, REEF),
           ("nebula", 22, 6, dict(water=True, wavy="n"))],
    features=[("channel", (12, 2, 5, 21), dict(water=True, wavy=True)),
              ("channel_2", (35, 2, 6, 21), dict(water=True, wavy=True)),
              ("channel_3", (55, 2, 5, 21), dict(water=True, wavy=True)),
              ("road", (0, 12, 72, 3), dict(level=0, **WAY)),
              ("rise", (18, 3, 9, 6), dict(level=1, paint="r", shape="round")),
              ("stack", (28, 3, 6, 5), dict(level=2, paint="r", flights=[30])),
              ("rise_2", (42, 3, 9, 6), dict(level=2, paint="r", shape="round"))]
             + islets((22, 23, 5, 3), (46, 23, 6, 4)),
    stairs="auto",
    ways={"west": ("w", "road"), "east": ("e", "road")},
    spawn="west",
    anchors={"jar_1": "rise@21", "chest_cloud_mv": "stack@31", "crate_2": "rise_2@45", "jar_3": "verge.s@46",
             "crate_4": "verge.n@64"},
    props=[("void_shell", 8, 18), ("void_shell", 64, 17), ("star_crystal", 52, 6)],
    flora={"rise": dict(density=0.4), "rise_2": dict(density=0.4), "stack": [], "reef": dict(density=0.5),
           "islet": {"kinds": ["coral_tree", "nebula_coral"], "density": 1.2},
           "channel": ["nebula_coral", "coral_tree"], "nebula": ["coral_tree", "nebula_coral"], "density": 0.34},
    foes="auto")


# The Crab Grottoes: the reef cliff along the north is hollowed into grottoes where the void crabs lair, their cast
# shells strewn at the mouths. Lu's star notes lie wedged in a shell in the third grotto; a chest and a crate on a ledge
# of the cliff between them; the driftglass vein in the rock; tide pools of the nebula on the reef floor, the open
# water south of the way.
ND_CRAB_GROTTOES = room(
    "nd_crab_grottoes", size=(72, 28), biome="nebula",
    bands=[("reef", 0, 6, dict(REEF, level=5)),
           ("road", 13, 3, WAY),
           ("nebula", 22, 6, dict(water=True, wavy="n"))],
    features=[("grotto", (8, 1, 7, 6), dict(level=0, paint="a", shape="round")),
              ("grotto_2", (24, 1, 8, 7), dict(level=0, paint="a", shape="round")),
              ("grotto_3", (46, 1, 8, 7), dict(level=0, paint="a", shape="round")),
              ("grotto_4", (60, 2, 7, 5), dict(level=0, paint="a", shape="round")),
              ("ledge", (36, 4, 8, 4), dict(level=2, paint="r", flights=[39])),
              ("pool", (14, 17, 8, 4), dict(water=True, shape="round")),
              ("pool_2", (52, 17, 9, 4), dict(water=True, shape="round"))]
             + islets((30, 23, 6, 4), (64, 24, 5, 3)),
    stairs="auto",
    ways={"west": ("w", "road"), "east": ("e", "road")},
    spawn="west",
    anchors={"jar_2": "grotto@11", "journal_grottoes": "grotto_2@28", "ore_1": "wall_foot@34", "chest_6": "ledge@38",
             "crate_3": "ledge@42", "lus_star_notes": (49, 4), "jar_4": "verge.s@45", "crate_5": "verge.s@64"},
    props=[("void_shell", 51, 3), ("void_shell", 26, 3), ("void_shell", 11, 9), ("void_shell", 62, 9),
           ("void_shell", 40, 18), ("star_crystal", 47, 2), ("star_crystal", 64, 3)],
    flora={"grotto": ["nebula_coral", "star_crystal"], "ledge": [], "reef": dict(density=0.45),
           "pool": ["nebula_coral"], "pool_2": ["nebula_coral"], "islet": {"kinds": ["coral_tree", "nebula_coral"], "density": 1.2},
           "nebula": ["coral_tree", "nebula_coral"], "density": 0.32},
    foes="auto")


# The Leviathan's Maw: the nebula opens into a great round lagoon, the Leviathan's hunting ground (no flying). The way
# comes in from the grottoes along the west reef and runs out over a causeway to the shoal in the lagoon's middle, where
# the Leviathan surfaces; coral trees thick on the reefs round it, islets in the lagoon, a ledge of the west reef where a
# chest waits.
ND_LEVIATHANS_MAW = room(
    "nd_leviathans_maw", size=(72, 28), biome="nebula",
    bands=[("reef", 0, 3, REEF)],
    features=[("maw", (24, 3, 46, 24), dict(water=True, shape="round")),
              ("shoal", (40, 8, 18, 12), dict(level=0, paint="a", shape="round")),
              ("road", (0, 12, 42, 3), dict(level=0, **WAY)),
              ("ledge", (13, 3, 8, 5), dict(level=2, paint="r", flights=[16]))]
             + islets((30, 4, 6, 4), (60, 4, 6, 4), (29, 20, 7, 4), (60, 19, 6, 5)),
    stairs="auto",
    ways={"west": ("w", "road")},
    spawn="west",
    anchors={"chest_ledge_mv_1": "ledge@17"},
    props=[("void_shell", 52, 16), ("void_shell", 8, 20), ("star_crystal", 44, 10), ("star_crystal", 55, 11)],
    flora={"shoal": ["nebula_coral", "star_crystal"], "ledge": [], "reef": dict(density=0.5),
           "islet": {"kinds": ["coral_tree", "nebula_coral"], "density": 1.2},
           "maw": ["coral_tree", "nebula_coral"], "density": 0.34},
    foes="auto")

ROOMS = [ND_NEBULA_VERGE, ND_EEL_CURRENTS, ND_CRAB_GROTTOES, ND_LEVIATHANS_MAW]
