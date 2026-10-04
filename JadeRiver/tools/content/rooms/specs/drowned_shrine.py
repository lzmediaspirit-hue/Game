"""E1 room specs (R2): the Drowned Shrine, under the river at Deepwater Bend (docs/architecture/room_engine.md). Its
halls are dressed granite round flagstone floors the river half fills (`q`, a floor under shallow water a body wades),
silt drifted along the water's edge, stone lanterns still lit along the dry walks, rubble and ferns where the vaults
came down. From Bend Shore's steps down into the water: the Flooded Gate, the Hall of Lanterns, the Scripture Well (and
its flooded shaft down to the Drowned Grotto) and the Abbot's Sanctum, whose stair climbs back up to the shore."""
from content.rooms.spec import room

# What grows in the shrine's rubble and silt: ferns and mossy stones, thick.
RUBBLE = {"rubble": {"kinds": ["ferns", "rock_mossy", "ferns", "rock_small"], "density": 0.9}}


def granite(high=3):
    """The halls' walls: dressed granite, `high` levels, the front a low sill."""
    return dict(high=high, low=1, paint="s")


def pillars(xs, y, level=3):
    """A row of granite pillars, a cell each (a colonnade along a walk); `level` a list: a lower one is a broken stump."""
    lv = level if isinstance(level, list) else [level]
    return [("pillar", (x, y, 1, 1), dict(level=lv[i % len(lv)], paint="s", wall=True)) for i, x in enumerate(xs)]


def rubble(*rects):
    """Heaps where the vaults fell in: rough rock over the flagstones, ferns and mossy stones in it (RUBBLE)."""
    return [("rubble", r, dict(paint="r", shape="round")) for r in rects]


def silt(y, h=3):
    """The silt the river left along its edge, drifted over the flagstones (sand creeps over paving)."""
    return [("silt", (1, y, 54, h), dict(paint="a", wavy=True))]


# The Flooded Gate: the shrine's gatehouse, where the steps from Bend Shore come down through the north wall. A granite
# causeway runs from them along a colonnade (two of its pillars broken) to the hall's east door; south of it the court
# the river took, a wading floor round the pit where the old gate sank, its two towers still standing in the water;
# the sluice keepers' deck in the east, a granite ledge above it against the north wall.
DS_FLOODED_GATE = room(
    "ds_flooded_gate", size=(56, 26), biome="drowned_shrine", walls=granite(),
    features=[("walk", (1, 8, 54, 3), dict(paint="s", walk=True))] + silt(12)
             + [("court", (1, 14, 54, 11), dict(paint="q", wavy=True)),
                ("sunk_gate", (16, 16, 17, 7), dict(water=True)),
                ("tower", (19, 17, 2, 2), dict(level=2, paint="s", wall=True)),
                ("tower", (28, 17, 2, 2), dict(level=2, paint="s", wall=True)),
                ("deck", (38, 16, 9, 4), dict(level=1, paint="w")),
                # S12c: the side view's ledge_mv_1, a path above (S43): two levels over the walk with no flight up,
                # so only the Cloud Ladder Step's second jump climbs onto it, to the chest.
                ("ledge_mv_1", (47, 1, 8, 4), dict(level=2, paint="s"))]
             + rubble((35, 1, 10, 6), (1, 18, 10, 7), (17, 1, 8, 4))
             + pillars(range(14, 52, 6), 7, [3, 3, 3, 1, 3, 3, 3]) + pillars(range(14, 52, 6), 11, [3, 3, 2, 3, 3, 3, 3]),
    stairs="auto",
    ways={"west": ("n", 7), "east": ("e", 9)},
    spawn="west",
    anchors={"jar_1": "deck@40", "jar_2": "deck@44", "chest_6": "deck@42", "chest_ledge_mv_1": "ledge_mv_1@51",
             "jar_3": (5, 4), "jar_4": "court@12", "jar_5": "walk.s@50", "inscription_ds_flooded_gate_0": "walk.n@10"},
    props=[("lantern", 3, 1), ("lantern", 12, 1), ("lantern", 17, 7), ("lantern", 29, 7), ("lantern", 41, 7),
           ("lantern", 23, 11), ("lantern", 35, 11)],
    flora=RUBBLE,
    # T2 (docs/architecture/topdown_mechanics.md): the side view's three drifting planks ply the sunk gate's water
    # between the court's west and east halves, and its two currents: the drain pulling west along the court's south
    # rows (a body wading there is carried), the flood's pull over the sunk gate (a swimmer is).
    traverse=[("raft", "float_plank_0", dict(at=(16, 19), size=(2, 1), path=[(15, 0)], speed=29, wait_s=1.5, look="plank")),
              ("raft", "float_plank_1", dict(at=(31, 20), size=(2, 1), path=[(-15, 0)], speed=26, wait_s=1.2, look="plank")),
              ("raft", "float_plank_2", dict(at=(16, 21), size=(2, 1), path=[(15, 0)], speed=32, wait_s=1.8, look="plank")),
              ("current", "gate_drain", dict(rect=(1, 22, 54, 3), push=(-60, 0))),
              ("current", "flood_current", dict(rect=(16, 16, 17, 7), push=(-83, 0)))],
    foes="auto")


# The Hall of Lanterns: the shrine's long nave, its paper lanterns still burning in two rows along the granite aisle.
# Galleries climb the north wall west to east, each a level higher (the west gallery, the rest where the scribes
# read, the loft where the chest was hidden); the river lies over the south half of the floor, its pools deep.
DS_HALL_OF_LANTERNS = room(
    "ds_hall_of_lanterns", size=(56, 26), biome="drowned_shrine", walls=granite(4),
    features=[("aisle", (1, 11, 54, 3), dict(paint="s", walk=True))] + silt(15)
             + [("flood", (1, 17, 54, 8), dict(paint="q", wavy=True)),
                ("pool", (7, 19, 11, 5), dict(water=True, shape="round")),
                ("pool", (36, 18, 13, 6), dict(water=True, shape="round")),
                ("gallery", (2, 1, 11, 4), dict(level=1, paint="s")),
                ("rest", (23, 1, 11, 3), dict(level=2, paint="p")),
                ("loft", (44, 1, 10, 2), dict(level=3, paint="p"))]
             + rubble((14, 1, 8, 6), (34, 1, 9, 6)),
    stairs="auto",
    ways={"west": ("w", 12), "east": ("e", 12)},
    spawn="west",
    anchors={"jar_1": "gallery@10", "inscription_ds_hall_of_lanterns_1": "gallery@5", "jar_2": "rest@31",
             "inscription_ds_hall_of_lanterns_2": "rest@26", "chest_6": "loft@50",
             "inscription_ds_hall_of_lanterns_0": "aisle.n@11", "inscription_ds_hall_of_lanterns_3": "aisle.n@41",
             "jar_3": "flood@15", "jar_4": "aisle.s@35", "jar_5": "flood@50", "lost_drowned_archer": "flood@27"},
    props=[{"kind": "lantern_red", "along": "aisle", "every": 7, "row": 10, "start": 4},
           {"kind": "lantern_red", "along": "aisle", "every": 7, "row": 14, "start": 7}],
    flora=RUBBLE,
    # T2 (docs/architecture/topdown_mechanics.md): the side view's five great lanterns hang from the vault over the
    # rubble between the galleries, their lids decks a body rides: swinging east and west or going round, a level up
    # from the gallery to the rest, then on from the rest toward the loft a level over it. Two rocks of the rubble that
    # stood under their sweep are taken out.
    traverse=[("lantern", "lantern_0", dict(at=(13, 1), size=(2, 2), level=1, mode="swing", length=3, amp_deg=25, period_s=3.2)),
              ("lantern", "lantern_1", dict(at=(16, 1), size=(2, 2), level=1, mode="circle", radius=0.75, period_s=4.4)),
              ("lantern", "lantern_2", dict(at=(19.5, 1), size=(2, 2), level=2, mode="swing", length=3.5, amp_deg=25,
                                            period_s=3.2, phase_deg=180)),
              ("lantern", "lantern_3", dict(at=(35.5, 1), size=(2, 2), level=2, mode="swing", length=3.5, amp_deg=25,
                                            period_s=3.2, phase_deg=90)),
              ("lantern", "lantern_4", dict(at=(41, 1), size=(2, 2), level=2, mode="circle", radius=0.75, period_s=4.4,
                                            phase_deg=180))],
    pins={"drop": [(16, 1), (17, 4)]},
    foes=["auto", "auto:gallery", "auto:rest", "auto"])


# The Scripture Well: a round shaft sunk through the shrine's floor to the river's own water, ringed by the ledges the
# monks read on: the rim against the north wall where the sutra chest stands, a ledge a level up in the west and one in
# the north-east corner. South of it the floor where Lu's trial is held, the river over its south end; beside the east
# ledge the flooded shaft drops to the Drowned Grotto. (The flights stand clear of the ways across the hall: auto-path's
# steering never crosses a flight from its side.)
DS_SCRIPTURE_WELL = room(
    "ds_scripture_well", size=(56, 26), biome="drowned_shrine", walls=granite(4),
    features=[("floor", (1, 15, 54, 3), dict(paint="p", walk=True))] + silt(18, 2)
             + [("flood", (1, 20, 54, 5), dict(paint="q", wavy=True)),
                ("rim", (18, 1, 20, 3), dict(level=2, paint="s")),
                ("ledge_w", (11, 6, 6, 3), dict(level=1, paint="s")),
                ("ledge_e", (49, 1, 6, 4), dict(level=1, paint="s")),
                ("well", (20, 5, 16, 9), dict(water=True, shape="round")),
                ("shaft", (42, 2, 4, 4), dict(water=True))]
             + rubble((1, 1, 9, 6), (47, 8, 8, 6)),
    stairs="auto",
    ways={"west": ("w", 16), "east": ("e", 16), "grotto": dict(at=(43.5, 6), dir="n", arrive=(43.5, 7.5), span=2)},
    spawn="west",
    anchors={"chest_6": "rim@25", "inscription_ds_scripture_well_0": "rim@31", "jar_2": "ledge_w@15",
             "inscription_ds_scripture_well_2": "ledge_w@12", "jar_1": "ledge_e@53", "inscription_ds_scripture_well_1": "ledge_e@50",
             "rite_riverbreath": (28, 15), "lost_scripture_well": "floor.n@22", "page_method_conversion_pill_2": "floor.n@34",
             "jar_3": "floor.n@6", "jar_4": "flood@44", "jar_5": "floor.s@51"},
    props=[("lantern", 9, 14), ("lantern", 46, 14), ("lantern", 23, 14), ("lantern", 33, 14), ("lantern", 41, 2),
           ("lantern", 46, 2)],
    flora=RUBBLE,
    event={"wave": [(21, 17), (35, 17)]},   # the Riverbreath Trial's drowned rise either side of the ring
    foes=["auto:rim", "auto:ledge_e", "auto"])


# The Abbot's Sanctum: the shrine's heart, where the Drowned Abbot keeps his vigil. Four bells hang on the platforms
# along the north wall, a step up each (their short flights clear of the walk before them), a colonnade before them; the sleeping blade lies on the altar's dais in
# the east, the sealed vault beside it; the river stands round the sanctum's south and west. The stair in the
# north-east corner climbs back to Bend Shore.
DS_ABBOTS_SANCTUM = room(
    "ds_abbots_sanctum", size=(56, 26), biome="drowned_shrine", walls=granite(4),
    features=[("nave", (1, 12, 54, 3), dict(paint="s", walk=True))] + silt(16, 2)
             + [("flood", (1, 17, 54, 8), dict(paint="q", wavy=True)),
                ("flood_w", (1, 2, 6, 10), dict(paint="q", shape="round")),
                ("bell_0", (8, 1, 7, 3), dict(level=1, paint="s")), ("bell_1", (20, 1, 7, 3), dict(level=1, paint="s")),
                ("bell_2", (32, 1, 7, 3), dict(level=1, paint="s")), ("bell_3", (44, 1, 7, 3), dict(level=1, paint="s")),
                ("dais", (38, 16, 9, 3), dict(level=1, paint="s")),
                ("vault", (49, 16, 6, 6), dict(level=1, paint="s"))]
             + rubble((15, 18, 9, 7)) + pillars(range(9, 50, 6), 9, [3, 3, 3, 2, 3, 3, 3]),
    stairs="auto",
    ways={"west": ("w", 13), "exit": ("n", 53)},
    spawn="west",
    anchors={"small_bell_0": "bell_0@11", "small_bell_1": "bell_1@23", "small_bell_2": "bell_2@35", "small_bell_3": "bell_3@47",
             "sleeping_blade_altar": "dais@42", "vault": "vault@52", "journal_vault": "vault@50",
             "lost_surfacing_bell": "nave.s2@17"},
    props=[("lantern", 12, 9), ("lantern", 24, 9), ("lantern", 30, 9), ("lantern", 42, 9), ("incense", 40, 16),
           ("incense", 45, 16)],
    flora=RUBBLE,
    # T2 (docs/architecture/topdown_mechanics.md): the side view's flood: on the Drowned Abbot's phase the river rises a
    # level over the sanctum's floor (the bell galleries and the dais stay dry) and falls back after its hold.
    traverse=[("flood", "sanctum_flood", dict(rect=(1, 4, 54, 21), top=1))],
    foes="auto")


# The Drowned Grotto: the cave the flooded shaft drops into, under the river's bed. The shaft comes down in the north
# west; a bar of wet sand runs east between pools, the rest of the floor under the water's skin; a ledge of rock stands
# in the middle where the chest lies, mist lotus on its brink; two pockets of air rise where the rock is hollow.
DS_DROWNED_GROTTO = room(
    "ds_drowned_grotto", size=(56, 26), biome="grotto", level=4,
    features=[("cavern", (1, 2, 54, 19), dict(level=0, paint="h", shape="round")),
              ("shaft", (2, 0, 6, 9), dict(level=0, paint="a")),
              ("bed", (2, 10, 50, 3), dict(level=0, paint="a", walk=True, wavy=True)),
              ("sands", (13, 13, 24, 6), dict(level=0, paint="a", shape="round")),
              ("pool", (4, 13, 11, 6), dict(water=True, shape="round")),
              ("pool", (37, 13, 12, 7), dict(water=True, shape="round")),
              ("ledge", (24, 3, 11, 5), dict(level=1, paint="r"))],
    stairs="auto",
    ways={"entry": ("n", 4)},
    spawn="entry",
    anchors={"chest_grotto": "ledge@32", "herb_1": "ledge@26", "air_pocket_0": "sands@20", "air_pocket_1": "bed.s@37",
             "herb_2": "cavern@48"},
    props=[("lantern", 9, 9), ("lantern", 44, 9)],
    foes="auto")

ROOMS = [DS_FLOODED_GATE, DS_HALL_OF_LANTERNS, DS_SCRIPTURE_WELL, DS_ABBOTS_SANCTUM, DS_DROWNED_GROTTO]
