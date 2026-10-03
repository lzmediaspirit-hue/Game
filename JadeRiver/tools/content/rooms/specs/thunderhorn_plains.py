"""E1 room specs (R6): the Thunderhorn Plains, east of Cloudgate Port (docs/architecture/room_engine.md, "Act II's first
zones (R6)"). Open storm grass under a low rocky ridge, the herds' trails braided across it in trampled earth, rocks
the storms split and menhirs the lightning cracked, few trees; the `storm_plains` biome. Chapter 11's Storm in the
Blood and Horns for the Furnace are hunted here, chapter 12's grey buyer tracked across the Lightning Scar."""
from content.rooms.spec import room

RIDGE = dict(level=3, paint="r", wall=True, wavy=True)     # the plains' low rocky ridge to the north
RISE = dict(level=1, paint="g", wavy=True)                   # the grassy rise under it
TRAIL = dict(level=0, paint="d", walk=True, wavy=True)       # the herders' trail, east to west
HERD = dict(paint="d", wavy=True)                            # a herd's trail, trampled into the grass
OUTCROP = dict(level=2, paint="r", shape="round")            # a storm-split outcrop, a ledge on it
# Every raised shape is climbed by R4's `flights` (the flight ends at the ground below, its cheeks closed by boulders):
# auto-path's steering is never sent along a step from its side.


# The Stormgrass Verge: the plains' edge out of the port. The trail runs east under the rise, a rocky outcrop over it
# with the ledge chests, menhirs on the rise; south of the trail the grass rolls away, two herds' trails across it and
# a scorched ring where the lightning struck, the insect swarm and the hedgehog's trail in the long grass.
TP_STORMGRASS_VERGE = room(
    "tp_stormgrass_verge", size=(72, 28), biome="storm_plains",
    bands=[("rise", 3, 8, dict(RISE, flights=[34])),
           ("ridge", 0, 4, RIDGE),
           ("trail", 12, 3, TRAIL),
           ("grass", 15, 13, dict(level=0, paint="g"))],
    features=[("outcrop", (37, 3, 10, 5), dict(OUTCROP, flights=[42])),
              ("herd_trail", (16, 19, 30, 3), HERD), ("herd_trail", (40, 23, 32, 3), HERD),
              ("scorch", (54, 16, 8, 5), dict(paint="d", shape="round"))],
    stairs="auto",
    ways={"west": ("w", "trail"), "east": ("e", "trail")},
    spawn="west",
    anchors={"sign_tp_verge": "trail.n@4", "jar_2": "rise@16", "trail_thunder_hedgehog": "grass@21",
             "ore_1": "wall_foot@34", "chest_ledge_mv_1": "outcrop@40", "chest_cloud_mv": "outcrop@44",
             "swarm_thunder_mantis": "grass@41", "jar_4": "verge.s@44", "jar_3": "rise@50", "journal_verge": "grass@48",
             "jar_5": "grass@62"},
    props=[("menhir", 12, 6), ("menhir", 29, 7), ("menhir", 57, 18), ("boulder", 59, 17), ("boulder", 25, 22),
           ("boulder", 26, 23), ("boulder", 66, 21)],
    flora={"rise": dict(density=0.45), "grass": dict(density=0.32), "scorch": dict(kinds=["dead_tree", "rock_small"])},
    foes="auto")


# The Herders' Camp: the plains' one rest. The herders' three yurts on the trampled earth north of the trail, their
# cook fire, haystacks and the fish-drying rack, the wayside shrine; south of the trail the two plots they let inside a
# fence, and the paddock's rails out on the grass.
TP_HERDERS_CAMP = room(
    "tp_herders_camp", size=(56, 28), biome="storm_plains",
    bands=[("rise", 3, 3, RISE),
           ("ridge", 0, 4, RIDGE),
           ("camp", 6, 7, dict(level=0, paint="g")),
           ("trail", 13, 3, TRAIL),
           ("pasture", 16, 12, dict(level=0, paint="g"))],
    features=[("yard", (6, 7, 42, 6), dict(paint="d", shape="round")),
              ("plot", (20, 18, 12, 4), dict(paint="d"))],
    ways={"west": ("w", "trail"), "east": ("e", "trail")},
    spawn="west",
    anchors={"shrine_tp_camp": "camp@19", "npc_herder_suo": (34, 11), "npc_herder_a_lan": "verge.s@44",
             "bed_tp_0": (23, 19), "bed_tp_1": (28, 19)},
    props=[("yurt", 8, 7), ("yurt", 22, 6), ("yurt", 38, 7), ("cook_fire", 31, 10), ("haystack", 26, 10),
           ("haystack", 14, 11), ("drying_rack", 44, 10), ("woodpile", 34, 8), ("chop_block", 36, 9),
           ("fence_4", 19, 17), ("fence_4", 29, 17), ("fence_3", 19, 22), ("fence_4", 22, 22), ("fence_3", 29, 22),
           ("haystack", 41, 21), ("haystack", 44, 22), ("haystack", 48, 20),
           ("menhir", 52, 8)],
    flora={"rise": dict(density=0.45), "camp": [], "pasture": dict(density=0.3), "plot": []})


# The Thunderhorn Flats: the herds' grazing. Wide grass under a low rise, the trail along it, an outcrop over the trail
# with the ledge chests; out on the flats the herds' trails braid between boulder fields and menhirs to the watering
# hole, where the thunderhorns drink.
TP_THUNDERHORN_FLATS = room(
    "tp_thunderhorn_flats", size=(72, 28), biome="storm_plains",
    bands=[("rise", 3, 8, dict(RISE, flights=[50])),
           ("ridge", 0, 4, RIDGE),
           ("trail", 11, 3, TRAIL),
           ("flats", 14, 14, dict(level=0, paint="g"))],
    features=[("outcrop", (12, 3, 11, 5), dict(OUTCROP, flights=[19])),
              ("herd_trail", (0, 17, 28, 3), HERD), ("herd_trail", (22, 15, 26, 3), HERD),
              ("herd_trail", (44, 17, 28, 3), HERD), ("herd_trail", (4, 23, 24, 3), HERD),
              ("herd_trail", (44, 24, 28, 3), HERD),
              ("pool", (27, 19, 17, 8), dict(water=True, shape="round"))],
    stairs="auto",
    ways={"west": ("w", "trail"), "east": ("e", "trail")},
    spawn="west",
    anchors={"jar_2": "rise@5", "chest_ledge_mv_1": "outcrop@15", "chest_cloud_mv": "outcrop@19", "jar_3": "rise@27",
             "swarm_thunder_mantis": "flats@27", "ore_1": "wall_foot@36", "jar_4": "verge.n@44",
             "trail_thunder_hedgehog": "flats@49", "jar_5": "flats@63"},
    props=[("menhir", 9, 6), ("menhir", 40, 15), ("menhir", 60, 22), ("boulder", 14, 21), ("boulder", 15, 22),
           ("boulder", 52, 24), ("boulder", 53, 23), ("boulder", 66, 19)],
    flora={"rise": dict(density=0.45), "flats": dict(density=0.3)},
    foes="auto")


# The Lightning Scar: where the storms come down. A broad burnt swathe across the grass south of the trail, at its heart
# a floor of rock the lightning fused, the glassy insight stone on it; dead trees and cracked menhirs round it, the grey
# buyer's footprints draining the colour from the scorched grass; ledges up the rise for the ore, the jars and the
# chests; the trail east to Rimefrost's snowline (sealed till Sage).
TP_LIGHTNING_SCAR = room(
    "tp_lightning_scar", size=(72, 28), biome="storm_plains",
    bands=[("rise", 3, 8, dict(RISE, flights=[13])),
           ("ridge", 0, 4, RIDGE),
           ("trail", 12, 3, TRAIL),
           ("flats", 15, 13, dict(level=0, paint="g"))],
    features=[("ledge_w", (2, 3, 10, 5), dict(OUTCROP, flights=[5])), ("ledge_m", (22, 3, 9, 5), dict(OUTCROP, flights=[27])),
              ("ledge_e", (38, 3, 11, 5), dict(OUTCROP, flights=[43])),
              ("scar", (14, 16, 44, 11), dict(paint="d", shape="round")),
              ("glass", (29, 18, 13, 6), dict(paint="r", shape="round"))],
    stairs="auto",
    ways={"west": ("w", "trail"), "east": ("e", "trail")},
    spawn="west",
    anchors={"ore_1": "ledge_w@5", "jar_3": "ledge_w@9", "grey_tracks_0": "flats@13", "temper_gold_tp_lightning_scar": "flats@21",
             "jar_4": "ledge_m@27", "grey_tracks_1": "scar@28", "jar_5": "verge.n@33", "insight_thunder": "glass@35",
             "swarm_thunder_mantis": "scar@40", "chest_8": "ledge_e@40", "chest_cloud_mv": "ledge_e@43",
             "chest_ledge_mv_1": "ledge_e@46", "grey_tracks_2": "scar@48", "jar_6": "flats@51", "ore_2": "wall_foot@53",
             "mine_lightning_scar_lode": "flats@58", "jar_7": "flats@63"},
    props=[("menhir", 17, 19), ("menhir", 44, 24), ("menhir", 55, 17), ("menhir", 18, 7), ("boulder", 20, 24),
           ("boulder", 52, 22), ("boulder", 53, 21)],
    flora={"rise": dict(density=0.4), "flats": dict(density=0.3),
           "scar": dict(kinds=["dead_tree", "rock_small", "dead_tree", "boulder"], density=0.35),
           "glass": dict(kinds=["rock_small", "boulder"], density=0.3)},
    foes="auto")

ROOMS = [TP_STORMGRASS_VERGE, TP_HERDERS_CAMP, TP_THUNDERHORN_FLATS, TP_LIGHTNING_SCAR]
