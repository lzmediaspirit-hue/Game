"""E1 room specs: Crane Falls, east of the Bamboo Grove (docs/architecture/room_engine.md; R1, the main story's path past
chapter 3). Leaf on the Wind and Listening to the Waterfall are played at the Falls Pool; chapter 4's road climbs on
east to Cleansing Peak."""
from content.rooms.spec import room

# The Falls Pool: Crane Falls comes down through a notch in the cliff into a round pool. Stepping rocks cross it to the
# rock where the mist lotus grows; the insight stone stands on a rock shelf on the west shore, the chest and a lotus
# on the high ledge under the cliff beyond it; a ledge along the cliff's foot leads in behind the falls. The road runs
# south of the pool over the outflow's stone bridge, east to the Pilgrim Stairs, and a gorge climbs north-east into
# the mist toward the Hidden Vale.
CF_FALLS_POOL = room(
    "cf_falls_pool", size=(56, 30), biome="falls",
    bands=[("cliff", 0, 6, dict(level=4, paint="r", wall=True)), ("shore", 6, 15, dict(level=0)),
           ("road", 21, 3, dict(paint="d")), ("meadow", 24, 3, dict(level=0)), ("stream", 27, 3, dict(water=True, wavy=True))],
    features=[("falls", (26, 2, 4, 7), dict(water=True)), ("pool", (16, 8, 26, 12), dict(water=True, shape="round")),
              ("foot_ledge", (19, 6, 7, 2), dict(level=0, paint="s")),
              ("falls_ledge", (4, 6, 10, 3), dict(level=2, paint="r")),
              ("insight_shelf", (10, 12, 6, 3), dict(level=1, paint="r")),
              ("rocks_w", (15, 14, 5, 2), dict(level=1, paint="s")), ("rocks_wm", (20, 13, 2, 2), dict(level=1, paint="s")),
              ("lotus_rock", (22, 11, 4, 4), dict(level=1, paint="r")), ("rocks_em", (26, 13, 3, 2), dict(level=1, paint="s")),
              ("rocks_e", (29, 14, 3, 2), dict(level=1, paint="s")), ("rocks_far", (32, 15, 3, 2), dict(level=1, paint="s")),
              ("rocks_ee", (35, 16, 5, 2), dict(level=1, paint="s")),
              ("outflow", (29, 18, 6, 11), dict(water=True, shape="round")),
              ("bridge", (28, 21, 8, 3), dict(level=0, paint="s")),
              # T1 (docs/architecture/topdown_mechanics.md): the spray ledge beside the falls, up its vine; Leaf on the
              # Wind's glide starts from it, over the falls' spray to the lotus rock.
              ("spray_ledge", (30, 6, 5, 2), dict(level=3, paint="r"))],
    stairs="auto",
    ways={"west": ("w", "road"), "east": ("e", "road"),
          "behind": dict(at=(25, 6), dir="n", arrive=(24, 7), span=2), "vale": ("n", 50, dict(cut=3))},
    spawn="west",
    anchors={"ledge_chest": "falls_ledge@7", "rare_lotus_fp": "falls_ledge@11", "insight_falls": "insight_shelf@13",
             "spring_falls": "meadow@12", "herb_1": "lotus_rock@23", "fish_falls": "water@38", "shrine_falls": "shore@45"},
    flora={"shore": dict(density=0.45), "meadow": dict(density=0.4)},
    ground={"sand": ["stream.bank"]},
    # T1: the falls' spray rises over the pool at the falls' foot (it lifts a body in the air to the spray ledge's
    # height), the vine climbs to the spray ledge, and the rope to the falls ledge's east end.
    traverse=[("updraft", "falls_spray", dict(rect=(26, 7, 4, 5), top=3.5)),
              ("vine", "falls_vine", dict(foot=(34, 8), top=(34, 7))),
              ("rope", "falls_step_rope", dict(foot=(14, 7), top=(13, 7)))],
    pins={"drop": [(35, 7)]},   # T1: the pine that hid the vine
    foes="auto")

# Behind the Falls: the grotto behind the curtain of Crane Falls, its floor worn round by the spray, a still spring in
# its middle with the mindwell lotus at its edge, Lu's journal page on the low ledge in the west, a mist lotus up on
# the high shelf, and east of it the shaft. S12c: the shaft's top is the side view's, a path above (S43): three levels up
# at the head of a shaft two wide between rock five high, so only Wall-Step's kicks off each face in turn climb onto it
# (the Echo Cliffs' shaft), to the chest.
CF_BEHIND_FALLS = room(
    "cf_behind_falls", size=(40, 24), biome="cave", level=4,
    features=[("grotto", (2, 2, 36, 19), dict(level=0, paint="d", shape="round")),
              ("curtain", (0, 20, 40, 4), dict(water=True)), ("mouth", (18, 17, 5, 7), dict(level=0, paint="d")),
              ("ledge_1", (5, 5, 8, 4), dict(level=1, paint="r")), ("shelf", (21, 3, 6, 4), dict(level=2, paint="r")),
              ("shaft_rock", (27, 2, 6, 8), dict(level=5, paint="r", wall=True)),
              ("shaft_top", (29, 3, 2, 2), dict(level=3, paint="r")), ("shaft", (29, 5, 2, 5), dict(level=0, paint="d")),
              ("spring_pool", (13, 9, 10, 6), dict(water=True, shape="round"))],
    stairs="auto",
    ways={"entry": ("s", 20)},
    spawn="entry",
    anchors={"journal_falls": "ledge_1@8", "chest_1": "shaft_top@30", "rare_lotus_bf": "shelf@24",
             "spring_behind": "bank@20", "mindwell_lotus_cf": "bank@14"},
    props=[("mat", 21, 16)],
    flora={"density": 0.3})

ROOMS = [CF_FALLS_POOL, CF_BEHIND_FALLS]
