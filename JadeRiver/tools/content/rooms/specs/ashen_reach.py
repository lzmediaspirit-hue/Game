"""E1 room specs (R9, Act III's chapter 21): the Ashen Reach, the cinder plains where the Ashborn legions of Ash Queen
Seralet camp under General Kharn, reached by the Wardens' second skiff from the Citadel Gate (docs/architecture/
room_engine.md, "The star field's end (R9)"). The Cinder Fields where the Wardens land, the Ashborn Palisade, the War
Camp and Kharn's Pyre. A burnt plain of dark earth (R7's `earth` over all), dunes of grey ash rising from it (rock),
drifts of ash and beds of embers, charred trees; the trodden track across it (sand's paint: trodden ash); the
Ashborn's war tents of dark hide, their ember-red banners, pyres burning; a timber palisade (planks, as the Mudwater
stockade's). The island's brink falls away south to the cloud sea, as the Citadel's does."""
from content.rooms.spec import room

RIDGE = dict(level=5, paint="r", wall=True, wavy="s")   # the ash cliffs along every room's north edge, past a hop
TRACK = dict(paint="a", walk=True)                       # the trodden track (the plain's earth kept off it)


def dunes(*specs):
    """Dunes of ash on the plain: (rect, level) each, round, grey."""
    return [("dune", r, dict(level=lv, paint="r", shape="round")) for r, lv in specs]


def banners(*cells):
    return [("ashborn_banner", x, y) for x, y in cells]


# The Cinder Fields: where the Wardens' skiff puts in, on the plain's west edge. A paved landing at the head of the pier,
# the shrine and Warden Hu Jin behind a barricade of crates, star lanterns and the Wardens' banner; the track runs east
# across the burnt plain between dunes of ash (a jar and a crate left on their tops, the driftglass vein at the cliff's
# foot), past the pyre the raiders lit, to the Ashborn's forward camp of tents and banners in the east.
AR_CINDER_FIELDS = room(
    "ar_cinder_fields", size=(72, 28), biome="ashen",
    bands=[("ridge", 0, 4, RIDGE),
           ("road", 13, 3, TRACK),
           ("brink", 23, 5, dict(level=0, wavy="n"))],
    features=dunes(((14, 4, 12, 7), 1), ((35, 3, 15, 8), 1), ((22, 18, 11, 5), 1), ((52, 17, 12, 6), 1))
             + [("crest", (39, 4, 7, 5), dict(level=2, paint="r", shape="round")),
                ("landing", (1, 17, 12, 6), dict(level=0, paint="s")),
                ("pier", (3, 22, 3, 6), dict(level=0, paint="w"))],
    stairs="auto",
    ways={"skiff": ("s", 4, dict(arrive=4)), "east": ("e", "road")},
    spawn="skiff",
    anchors={"shrine_ar_fields": (9, 19), "npc_warden_hu_jin": (6, 17), "jar_2": "dune@19", "journal_cinders": "verge.s@31",
             "ore_1": "wall_foot@34", "crate_3": "crest@42", "jar_4": "verge.s@45", "crate_5": "verge.n@63"},
    props=[("crates", 13, 17), ("barrel", 13, 18), ("crates", 13, 20), ("barrel", 1, 16), ("star_lantern", 2, 21),
           ("star_lantern", 7, 21), ("warden_banner", 11, 16), ("post", 3, 27), ("post", 5, 27), ("ash_pyre", 29, 9),
           ("cinder_tent", 54, 4), ("cinder_tent", 63, 7)] + banners((52, 9), (60, 11), (68, 4), (48, 6)),
    flora={"dune": dict(density=0.5), "crest": [], "ridge": dict(density=0.4), "landing": [], "density": 0.32},
    ground={"earth": ["*", "-road"]},
    foes="auto")


# The Ashborn Palisade: the Ashborn's timber wall across the plain. The track comes in from the west along its south
# face, turns north through its gate between two gate towers (braziers and banners at the gate), and runs east inside
# it under the ash cliffs; inside, the Ashborn's tents, a watch tower (a jar on it) and a lookout's platform where the
# raiders keep their chest; pyre keepers tend a pyre by the gate.
AR_ASHBORN_PALISADE = room(
    "ar_ashborn_palisade", size=(72, 28), biome="ashen",
    bands=[("ridge", 0, 3, RIDGE),
           ("palisade", 11, 2, dict(level=3, paint="w", wall=True)),
           ("road", 17, 3, dict(TRACK, w=34)),
           ("brink", 23, 5, dict(level=0, wavy="n"))],
    features=[("gate", (30, 11, 4, 2), dict(level=0, paint="a")),
              ("gatehouse", (27, 10, 3, 3), dict(level=4, paint="w", wall=True)),
              ("gatehouse_2", (34, 10, 3, 3), dict(level=4, paint="w", wall=True)),
              ("road_n", (30, 7, 4, 13), TRACK),
              ("road_e", (30, 7, 42, 3), TRACK),
              ("tower", (13, 3, 6, 4), dict(level=1, paint="w", flights=[16])),
              ("platform", (40, 3, 9, 3), dict(level=2, paint="w", flights=[44]))]
             + dunes(((8, 20, 12, 4), 1), ((44, 16, 14, 6), 1)),
    stairs="auto",
    ways={"west": ("w", 18), "east": ("e", 8)},
    spawn="west",
    anchors={"jar_1": "tower@16", "chest_cloud_mv": "platform@42", "crate_2": "platform@46", "jar_3": "verge.s@46",
             "crate_4": "road_e.n@63"},
    props=[("brazier", 29, 13), ("brazier", 34, 13), ("ash_pyre", 23, 8), ("cinder_tent", 3, 4), ("cinder_tent", 52, 3),
           ("cinder_tent", 60, 3)] + banners((26, 13), (37, 13), (21, 4), (50, 8), (12, 14), (58, 14))
          + [("embers", 25, 9), ("embers", 21, 10), ("crates", 7, 8), ("barrel", 9, 8)],
    flora={"dune": dict(density=0.5), "tower": [], "platform": [], "density": 0.3},
    ground={"earth": ["*", "-road", "-road_n", "-road_e", "-gate"]},
    foes="auto")


# The War Camp: the Ashborn legion's camp on the plain, its tents in rows either side of the avenue, the great pyre
# burning by the avenue where they burn their dead, a parley ground of scorched stone ringed by banners where the
# envoy Veyla waits; a lookout's platform with the camp's chests, the camp shrine by the west gate; the avenue's east
# end barred by two timber bastions, braziers and the guards' banners: Kharn's Pyre beyond.
AR_WAR_CAMP = room(
    "ar_war_camp", size=(72, 28), biome="ashen",
    bands=[("ridge", 0, 3, RIDGE),
           ("avenue", 13, 4, TRACK),
           ("brink", 24, 4, dict(level=0, wavy="n"))],
    features=[("parley", (20, 7, 16, 6), dict(paint="s", shape="round")),
              ("platform", (28, 2, 10, 4), dict(level=3, paint="w", flights=[33])),
              ("bastion", (63, 6, 5, 6), dict(level=3, paint="w", wall=True)),
              ("bastion_2", (63, 18, 5, 5), dict(level=3, paint="w", wall=True))]
             + dunes(((16, 3, 9, 4), 1), ((40, 3, 9, 4), 1)),
    stairs="auto",
    ways={"west": ("w", "avenue"), "east": ("e", "avenue")},
    spawn="west",
    anchors={"shrine_ar_camp": "verge.s@7", "jar_1": "dune@21", "chest_5": "platform@31", "chest_cloud_mv": "platform@35",
             "npc_ashborn_envoy_veyla": (28, 10), "crate_2": "dune_2@44", "jar_3": "verge.s@45", "crate_4": "verge.n@60"},
    props=[("cinder_tent", 4, 5), ("cinder_tent", 50, 6), ("cinder_tent", 56, 9), ("cinder_tent", 10, 18),
           ("cinder_tent", 26, 19), ("cinder_tent", 50, 18), ("ash_pyre", 44, 10), ("brazier", 62, 12),
           ("brazier", 62, 17)] + banners((19, 8), (36, 8), (21, 12), (35, 12), (60, 11), (60, 18), (2, 12))
          + [("embers", 42, 11), ("embers", 47, 11), ("crates", 16, 18), ("barrel", 18, 18), ("weapon_rack", 39, 18)],
    flora={"dune": dict(density=0.4), "parley": [], "platform": [], "density": 0.28},
    ground={"earth": ["*", "-avenue"]},
    foes="auto")


# Kharn's Pyre: the General's own fire, where the Ashborn burn their dead: a round floor of scorched stone under the ash
# cliffs, the great pyre burning on its dais at its north edge, a flight up the dais's face; the Ashborn's banners in a
# ring round the floor, braziers, embers drifting. Kharn waits on the floor before his pyre; the track comes in from the
# war camp in the west.
AR_KHARNS_PYRE = room(
    "ar_kharns_pyre", size=(56, 28), biome="ashen",
    bands=[("ridge", 0, 4, RIDGE),
           ("brink", 24, 4, dict(level=0, wavy="n"))],
    features=[("floor", (8, 5, 40, 19), dict(paint="s", shape="round")),
              ("dais", (21, 3, 14, 5), dict(level=2, paint="s", flights=[28])),
              ("track", (0, 13, 12, 3), TRACK)],
    stairs="auto",
    ways={"west": ("w", "track")},
    spawn="west",
    props=[("ash_pyre", 27, 4), ("ash_pyre", 24, 5), ("ash_pyre", 30, 5), ("ash_pyre", 25, 3), ("ash_pyre", 29, 3),
           ("brazier", 21, 6), ("brazier", 34, 6), ("ashborn_banner", 22, 3), ("ashborn_banner", 33, 3)]
          + banners((12, 8), (43, 8), (9, 15), (46, 15), (14, 21), (41, 21))
          + [("embers", 18, 9), ("embers", 37, 10), ("embers", 24, 18), ("embers", 33, 16), ("ash_drift", 15, 12),
             ("ash_drift", 38, 19)],
    flora={"floor": [], "dais": [], "density": 0.3},
    ground={"earth": ["*", "-track"]},
    foes="auto")

ROOMS = [AR_CINDER_FIELDS, AR_ASHBORN_PALISADE, AR_WAR_CAMP, AR_KHARNS_PYRE]
