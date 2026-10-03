"""E1 room specs: Deepwater Bend, west of the Caravan Road (docs/architecture/room_engine.md). Chapter 3's Gu's Cargo
ends here; the ford to the Serpent's Shallows and the Drowned Shrine's steps go down into the river."""
from content.rooms.spec import room

# Bend Shore: the shore path along the river where it bends, woods on the rise under the bluff, the river's bay in the
# west with a jetty and the moored sampan, the sand ford out to the Serpent's Shallows, and in the east the stone steps
# down into the water where the Drowned Shrine's roof will surface.
DW_BEND_SHORE = room(
    "dw_bend_shore", size=(64, 30), biome="river_shore",
    bands=[("bluff", 0, 3, dict(level=2, paint="r", wall=True)),
           ("woods", 3, 6, dict(level=1)),
           ("path", 10, 3, dict(paint="d", walk=True)),
           ("shore", 13, 9, dict(level=0)),
           ("river", 22, 8, dict(water=True, wavy=True))],
    features=[("bay", (5, 18, 24, 7), dict(water=True, shape="round")),
              ("jetty", (16, 18, 3, 3), dict(level=0, paint="w")),
              ("ford", (30, 20, 3, 10), dict(level=0, paint="a")),
              ("steps", (52, 20, 3, 7), dict(level=0, paint="s"))],
    stairs="auto",
    ways={"east": ("e", "path"), "west": ("w", "path"), "shallows": ("s", 31),
          "shrine": dict(at=(53, 26), dir="s", arrive=(53, 24), span=3)},
    spawn="east",
    anchors={"chest_sampan": "jetty@16", "rare_ginseng_bs": "jetty@18", "herb_1": "woods.front@16",
             "herb_2": "bank@47", "jar_3": "path.s@13", "jar_4": "path.s@40", "jar_5": "path.n@32", "jar_6": "shore@45",
             "jar_7": "path.n@60", "fish_8": "water@40", "rift_tear": "shore@35", "spirit_fruit_tree": "shore@24",
             "swarm_jade_scarab": "bank@58", "trail_reed_ferret": "shore@9"},
    props=[("boat", 19, 20), ("lantern", 51, 21), ("lantern", 55, 21)],
    flora={"woods": dict(density=0.5)},
    ground={"sand": ["river.bank", "bay.bank"]},
    foes=["auto:bank", "auto:shore", "auto:bank", "auto:shore", "auto:shore"])

# R2 --------------------------------------------------------------------------------------------------------------
# The Serpent's Shallows: south of Bend Shore's ford, where the river spreads wide and shallow over its sandy bed (`h`,
# a floor under water a body wades) and the Riverbed Serpent hunts. The ford's path comes down the willow bank to a
# strand of sand; three rocks stand out of the shallows (the King's nest on the east one, the old ginseng on the middle
# one); sandbars and deep runs break the wading floor; the river flows on deep along the south.
DW_SERPENTS_SHALLOWS = room(
    "dw_serpents_shallows", size=(72, 28), biome="river_shore",
    bands=[("bank", 0, 5, dict(level=1)),
           ("strand", 7, 3, dict(paint="a", walk=True, wavy=True)),
           ("shallows", 10, 12, dict(paint="h", wavy=True)),
           ("river", 22, 6, dict(water=True, wavy=True))],
    features=[("bar", (3, 13, 9, 4), dict(paint="a", shape="round")), ("bar", (56, 15, 11, 4), dict(paint="a", shape="round")),
              ("run", (21, 16, 9, 6), dict(water=True, shape="round")),
              ("rock_w", (14, 11, 6, 4), dict(level=1, paint="r", shape="round")),
              ("rock_mid", (30, 12, 7, 4), dict(level=1, paint="r", shape="round")),
              ("rock_e", (46, 11, 7, 5), dict(level=1, paint="r", shape="round"))],
    stairs=[(30, 5, 3, 2, 0, 1)],                     # down from the ford's cut; the rocks are a hop up
    ways={"shore": ("n", 31, dict(cut=3)), "east": ("e", 8)},
    spawn="shore",
    anchors={"serpent_nest": "rock_e@49", "rare_ginseng_ss": "rock_mid@33"},
    flora={"bank": dict(density=0.45), "shallows": dict(kinds=["cattails"], density=0.25)},
    ground={"sand": ["river.bank"]},
    foes="auto")

ROOMS = [DW_BEND_SHORE, DW_SERPENTS_SHALLOWS]
