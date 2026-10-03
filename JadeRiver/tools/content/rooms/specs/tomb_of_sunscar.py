"""E1 room specs (R7, Act II's chapter 14): the Tomb of Sunscar, under the Worm Sea's sand
(docs/architecture/room_engine.md, "Nine Peaks to the Tomb of Sunscar (R7)"). The Sealed Gate's bronze doors, the Hall
of Sand Kings, the Mirror Crypt (Lu's page) and the Tomb King's throne. Halls of warm flagstones (`p`) inside walls of
cut sandstone (the sand's own layered faces, `tomb`), sand drifted in through the cracks along them, pillars, statues of
the sand kings, braziers still burning; spike traps' pressure plates in the aisles (the side view's spike_traps strike
near the body wherever it walks; the plates are their tell)."""
from content.rooms.spec import room

WALLS = dict(high=4, low=1, paint="a")   # cut sandstone, four levels, the front a low sill


def pillars(xs, y, level=4):
    """A row of sandstone pillars a cell each; `level` a list: a lower one has crumbled."""
    lv = level if isinstance(level, list) else [level]
    return [("pillar", (x, y, 1, 1), dict(level=lv[i % len(lv)], paint="a", wall=True)) for i, x in enumerate(xs)]


def drifts(*rects):
    """Sand blown in through the cracks: round drifts over the flagstones (sand creeps over paving), a level never
    raised."""
    return [("drift", r, dict(paint="g", shape="round")) for r in rects]


def plates(*cells):
    """The spike traps' pressure plates in the floor."""
    return [("spike_plate", x, y) for x, y in cells]


# The Sealed Gate: the tomb's first hall, where the stair down from the Worm Sea's portal comes in through the west wall.
# A gallery runs along the north wall a level and two up (the jars, a crate and the chest the robbers never reached),
# pillars down the hall, sand drifted in its corners; the robbers' tablet of the dry wells by the stair, and at the east
# wall the bronze doors under the sun lock, two sand kings either side of them.
TS_SEALED_GATE = room(
    "ts_sealed_gate", size=(56, 24), biome="tomb", walls=WALLS,
    features=[("aisle", (1, 11, 54, 3), dict(paint="p", walk=True)),
              ("gallery", (8, 1, 26, 5), dict(level=1, paint="p", flights=[12])),
              ("loft", (24, 1, 10, 3), dict(level=2, paint="p", flights=[28]))]
             + drifts((1, 16, 12, 8), (40, 17, 15, 7), (1, 1, 7, 6))
             + pillars(range(10, 50, 8), 9, [4, 4, 2, 4, 4]) + pillars(range(10, 50, 8), 15, [4, 4, 4, 3, 4]),
    stairs="auto",
    ways={"west": ("w", 12), "east": ("e", 12)},
    spawn="west",
    anchors={"jar_1": "gallery@14", "lost_tablet_of_dry_wells": "aisle.s2@17", "crate_2": "loft@26",
             "chest_ledge_mv_1": "loft@31", "jar_3": "aisle.n@35", "crate_4": "aisle.s@46", "tomb_gate": (51, 10)},
    props=[("king_statue", 51, 7), ("king_statue", 51, 15), ("brazier", 49, 9), ("brazier", 49, 15),
           ("brazier", 3, 9), ("brazier", 3, 15), ("king_statue", 36, 1), ("king_statue", 44, 1)]
          + plates((20, 12), (29, 11), (38, 13), (25, 18), (44, 19)),
    flora={"drift": ["ribcage", "red_rock"], "density": 0.3},
    foes="auto")


# The Hall of Sand Kings: the tomb's long nave. Five sand kings stand along the north wall between the alcoves of their
# grave goods, raised a level and two over the floor (the jar, the crates, the chests); a sarcophagus on its dais in the
# middle of the nave, colonnades either side of the aisle, the snare glyphs cut in the floor before the dais, the pill
# recipe's tablet in the east, sand drifted along the south wall; the plates of the spike traps in the aisle.
TS_HALL_OF_SAND_KINGS = room(
    "ts_hall_of_sand_kings", size=(72, 24), biome="tomb", walls=WALLS,
    features=[("aisle", (1, 12, 70, 3), dict(paint="p", walk=True)),
              ("alcove_w", (12, 1, 8, 4), dict(level=1, paint="p", flights=[15])),
              ("alcove_mid", (36, 1, 9, 4), dict(level=2, paint="p", flights=[40])),
              ("alcove_e", (60, 1, 8, 4), dict(level=1, paint="p", flights=[63])),
              ("dais", (24, 6, 10, 4), dict(level=1, paint="p", flights=[30]))]
             + drifts((1, 18, 16, 6), (24, 19, 20, 5), (52, 18, 19, 6), (1, 1, 6, 6))
             + pillars(range(6, 70, 7), 10, [4, 4, 4, 2, 4, 4, 4, 4, 3, 4]) + pillars(range(6, 70, 7), 16, [4, 3, 4, 4, 4, 4, 2, 4, 4, 4]),
    stairs="auto",
    ways={"west": ("w", 13), "east": ("e", 13)},
    spawn="west",
    anchors={"jar_1": "alcove_w@16", "lost_sand_glyph_snare": "aisle.s@31", "chest_5": "alcove_mid@38",
             "chest_ledge_mv_1": "alcove_mid@42", "crate_2": "verge.n@47", "jar_3": "aisle.s@49",
             "page_sovereign_settling_pill_2": "aisle.s@57", "crate_4": "alcove_e@64"},
    props=[("sarcophagus", 28, 7), ("king_statue", 9, 2), ("king_statue", 22, 2), ("king_statue", 33, 2),
           ("king_statue", 48, 2), ("king_statue", 57, 2), ("brazier", 25, 6), ("brazier", 33, 6), ("brazier", 2, 10),
           ("brazier", 69, 10), ("brazier", 2, 16), ("brazier", 69, 16)]
          + plates((12, 13), (21, 12), (39, 14), (46, 12), (60, 13), (35, 20)),
    flora={"drift": ["ribcage", "red_rock"], "density": 0.3},
    foes="auto")


# The Mirror Crypt: the sand king's own crypt, the sarcophagus on a round dais under four bronze mirrors on their stands
# that throw the braziers' light onto it; Lu's journal page left at its foot; the seal-breaker's carving and the dust
# veil's in the floor round it, a side chamber a level up in the north-west where the chest was hidden, the pill recipe's
# tablet by the west door; sand along the walls.
TS_MIRROR_CRYPT = room(
    "ts_mirror_crypt", size=(56, 24), biome="tomb", walls=WALLS,
    features=[("aisle", (1, 11, 54, 3), dict(paint="p", walk=True)),
              ("crypt", (16, 3, 24, 18), dict(paint="p", shape="round")),
              ("dais", (23, 5, 10, 4), dict(level=1, paint="p", flights=[28])),
              ("chamber", (3, 1, 11, 5), dict(level=2, paint="p", flights=[9]))]
             + drifts((1, 16, 12, 8), (43, 15, 12, 9), (44, 1, 11, 6)),
    stairs="auto",
    ways={"west": ("w", 12), "east": ("e", 12)},
    spawn="west",
    anchors={"page_sovereign_settling_pill_1": "aisle.s@12", "jar_1": "chamber@6", "chest_ledge_mv_1": "chamber@11",
             "lost_crypt_seal": "crypt@23", "journal_tomb": (28, 12), "crate_2": "aisle.s2@29",
             "lost_throne_dust_veil": "crypt@33", "jar_3": "aisle.n@46"},
    props=[("sarcophagus", 27, 6), ("bronze_mirror", 20, 5), ("bronze_mirror", 35, 5), ("bronze_mirror", 19, 15),
           ("bronze_mirror", 36, 15), ("brazier", 23, 4), ("brazier", 32, 4), ("brazier", 2, 9), ("brazier", 53, 9),
           ("king_statue", 41, 1), ("king_statue", 16, 1)]
          + plates((8, 12), (15, 13), (41, 12), (48, 13)),
    flora={"drift": ["ribcage", "red_rock"], "density": 0.3},
    foes="auto")


# The Throne of the Tomb King: a round hall under a dome, the king's sun throne on its dais against the north wall, a
# ring of braziers round the floor where he rises; the Grey Pilgrim waits by the west door; the king's grave goods
# behind the dais in the east, the scorpion script and the king's own carving in the floor; the old exit stair up to
# the Worm Sea in the east wall.
TS_THRONE = room(
    "ts_throne", size=(56, 24), biome="tomb", walls=WALLS,
    features=[("aisle", (1, 12, 54, 3), dict(paint="p", walk=True)),
              ("hall", (7, 3, 42, 20), dict(paint="a", shape="round")),         # the sand floor where he rises
              ("dais", (22, 1, 14, 5), dict(level=1, paint="p", flights=[29])),
              ("vault", (44, 1, 11, 5), dict(level=1, paint="p", flights=[50]))]
             + drifts((1, 17, 9, 7), (47, 17, 8, 7), (1, 1, 6, 5))
             + pillars((8, 15, 41, 48), 5, 4) + pillars((8, 15, 41, 48), 20, [4, 3, 4, 2]),
    stairs="auto",
    ways={"west": ("w", 13), "exit": ("e", 8)},
    spawn="west",
    anchors={"npc_grey_pilgrim_tomb": "aisle.n@10", "lost_the_king_who_waits": "hall@20", "lost_scorpion_script": "hall@39",
             "chest_1": "vault@51"},
    props=[("sun_throne", 27, 2), ("brazier", 23, 1), ("brazier", 34, 1), ("brazier", 14, 9), ("brazier", 41, 9),
           ("brazier", 14, 17), ("brazier", 41, 17), ("king_statue", 20, 1), ("king_statue", 37, 1)],
    flora={"drift": ["ribcage", "red_rock"], "density": 0.3},
    foes="auto")

ROOMS = [TS_SEALED_GATE, TS_HALL_OF_SAND_KINGS, TS_MIRROR_CRYPT, TS_THRONE]
