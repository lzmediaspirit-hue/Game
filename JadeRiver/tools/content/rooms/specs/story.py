"""E1 room specs (R5): the story's own rooms, instanced for one character each (docs/architecture/room_engine.md): Gu's
Warehouse off Artisan Row, the Trial of Reflections on Elder Hu's peak, the Siege of Two Sects before the Jade Sect's
gate, the Sect War at the Alliance Gate and the Presence Trial above the Nine Peaks' Trial Hall. Each is laid out for
its event: an arena with clear fighting ground, a wall and its gate for the siege, the Gate's line for the war, the
trials' own shapes. A line that must read as a wall runs east and west, so its face shows (a wall running north and
south is only its top, seen from above). Their events' spawn cells (`event`) are written where each wave comes from."""
from content.rooms.spec import room


def octagon(name, x, y, w, h, cut, opts):
    """A floor shaped as an octagon in the rect, its corners cut `cut` cells each way: rects laid one over another, so it
    stays exactly symmetric (a round shape wears with the room's seed)."""
    return [(name if k == 0 else "%s_%d" % (name, k + 1), (x + cut - k, y + k, w - 2 * (cut - k), h - 2 * k), dict(opts))
            for k in range(cut + 1)]


def stair_with_cheeks(x, y, w, frm, to, paint="w"):
    """A flight `w` wide rising north at (x, y) from level `frm` to `to` (two rows a level), with a cheek a level over its
    head on each side (R3: a body walking off a flight's side stalls; the cheeks keep it on the flight). Returns the
    cheeks (features) and the flight (a stair)."""
    h = 2 * (to - frm)
    return ([("cheek", (x - 1, y, 1, h), dict(level=to + 1, paint=paint)), ("cheek", (x + w, y, 1, h), dict(level=to + 1, paint=paint))],
            (x, y, w, h, frm, to, paint))


def flights(*made):
    """The cheeks and the flights of several stair_with_cheeks, as (features, stairs)."""
    return [f for m in made for f in m[0]], [m[1] for m in made]


# Gu's Warehouse: Elder Gu's private store behind the trade house, a long flagstone floor under lamplight. The goods stand
# in stacks a body can climb (crates) between the aisles where his bandits keep watch; a loft of boards runs along the
# north wall from the west stair to the east one, the catwalk between them over the floor (the side view's stealth
# route under the roof), and Gu's strongbox sits on the strongroom's dais at the east loft's end. Gu keeps his office on
# a floor of boards in the east: his desk, his cabinet and his screen, the open floor before them where he makes his stand.
_WH = flights(stair_with_cheeks(5, 6, 2, 0, 2), stair_with_cheeks(35, 7, 2, 0, 2), stair_with_cheeks(40, 3, 2, 2, 3))
SI_GUS_WAREHOUSE = room(
    "si_gus_warehouse", size=(44, 20), base="p", walls=dict(high=4),
    features=[("office", (32, 9, 11, 10), dict(paint="w")),                 # Gu's office, its floor of boards
              ("loft_w", (1, 1, 11, 5), dict(level=2, paint="w")),           # the west loft
              ("catwalk", (12, 1, 22, 2), dict(level=2, paint="w")),         # the catwalk along the north wall
              ("loft_e", (34, 1, 9, 6), dict(level=2, paint="w")),           # the east loft
              ("vault", (38, 1, 5, 2), dict(level=3, paint="w"))]            # the strongroom's dais
             + _WH[0],
    stairs=_WH[1],
    ways={"entry": ("s", 3.5)},
    spawn="entry",
    anchors={"gus_vault": (40.5, 1)},
    props=[("crates", 1, 1), ("sacks", 3, 1), ("barrel", 4, 1), ("crates", 8, 1), ("sacks", 10, 1),
           ("crates", 14, 8), ("crates", 16, 8), ("crates", 14, 9), ("sacks", 16, 9), ("barrel", 17, 9),
           ("crates", 22, 12), ("crates", 24, 12), ("barrel", 22, 13), ("sacks", 23, 13), ("crates", 24, 13),
           ("crates", 12, 15), ("sacks", 14, 15), ("barrel", 15, 15), ("crates", 20, 7), ("crates", 22, 7),
           ("sacks", 24, 7), ("crates", 27, 7), ("barrel", 29, 7),
           ("desk", 38, 11), ("cabinet", 41, 8), ("screen", 39, 8), ("lantern_red", 33, 10), ("lantern_red", 42, 13),
           ("weapon_rack", 26, 17), ("lantern_red", 9, 7), ("lantern_red", 20, 4), ("lantern_red", 30, 4),
           ("sacks", 1, 12), ("sacks", 1, 13), ("barrel", 1, 17), ("crates", 8, 17), ("barrel", 42, 17),
           ("crates", 29, 17), ("sacks", 31, 17), ("pot_bonsai", 33, 17)],
    foes=["auto", [(37, 14)]])                                                # the bandits on the floor, Gu at his office


# The Trial of Reflections: a granite arena on Elder Hu's peak, every line of it mirrored about the bronze mirror on its
# dais at the north: two granite ledges a step up, one each side, the same flight up each, the lanterns in pairs. You
# come in from the west path; the Reflection waits where your mirror image would stand, inside the arena's east side.
_RF = flights(stair_with_cheeks(17, 7, 2, 0, 1, "s"), stair_with_cheeks(9, 13, 2, 0, 1, "s"), stair_with_cheeks(25, 13, 2, 0, 1, "s"))
SI_TRIAL_OF_REFLECTIONS = room(
    "si_trial_of_reflections", size=(36, 22), biome="mountain",
    bands=[("peak", 0, 22, dict(level=0, paint="r")), ("crags", 0, 3, dict(level=3, paint="r", wall=True, wavy=True))],
    features=octagon("arena", 5, 5, 26, 15, 2, dict(paint="s"))
             + [("approach", (0, 11, 7, 3), dict(paint="s")),
                ("dais", (14, 4, 8, 3), dict(level=1, paint="p")),                 # the mirror's dais
                ("ledge_w", (8, 9, 4, 4), dict(level=1, paint="s")),               # the two ledges, one the other's image
                ("ledge_e", (24, 9, 4, 4), dict(level=1, paint="s"))]
             + _RF[0],
    stairs=_RF[1],
    ways={"exit": ("w", 12)},
    spawn="exit",
    props=[("bronze_mirror", 17, 4), ("incense", 15, 5), ("incense", 20, 5), ("lantern", 7, 7), ("lantern", 28, 7),
           ("lantern", 7, 17), ("lantern", 28, 17), ("incense", 8, 9), ("incense", 27, 9)],
    flora={"peak": dict(density=0.4)},
    event={"fixed": [(28, 12)]})                                              # the Reflection, your image across the arena


# The Presence Trial: the Nine Peaks' trial court on the height above the Trial Hall, an octagon of granite round the
# circle of paving where the one who sits the trial kneels on a mat. Nine seats look down on it in a horseshoe open to
# the south, each on a plinth too high to climb: the ninth, empty, highest in the middle of the arc between its two
# pressure pillars. The phantoms come from the west and the east of the court and from its south; the ninth Presence
# rises before the ninth seat.
_SEATS = [(19, 4), (13, 5), (25, 5), (9, 7), (29, 7), (7, 10), (31, 10), (6, 14), (32, 14)]
SI_PRESENCE_TRIAL = room(
    "si_presence_trial", size=(40, 26), biome="mountain",
    bands=[("peak", 0, 26, dict(level=0, paint="r")), ("crags", 0, 3, dict(level=3, paint="r", wall=True, wavy=True))],
    features=octagon("court", 4, 3, 32, 22, 3, dict(paint="s"))
             + octagon("circle", 15, 10, 10, 8, 2, dict(paint="p"))
             + [("approach", (0, 13, 5, 3), dict(paint="s"))]
             + [("plinth", (x, y, 2, 2), dict(level=3 if k == 0 else 2, paint="s", wall=True)) for k, (x, y) in enumerate(_SEATS)]
             + [("pillar", (x, 4, 1, 1), dict(level=4, paint="s", wall=True)) for x in (17, 22)],
    ways={"exit": ("w", 14)},
    spawn=(20, 15),
    props=[("trial_seat", x, y) for x, y in _SEATS]
          + [("mat", 19, 13), ("incense", 16, 11), ("incense", 23, 11), ("incense", 16, 16), ("incense", 23, 16),
             ("lantern", 8, 20), ("lantern", 31, 20), ("lantern", 12, 23), ("lantern", 27, 23)],
    flora={"peak": dict(density=0.4)},
    event={"waves": [[(8, 18), (31, 18), (20, 21)]],                          # the phantoms: west, east and south
           "timed": [(20, 8)]})                                               # the ninth Presence, before its seat


# The Siege of Two Sects: the wall across the valley before the Jade Sect, its gate on the road north between two
# towers, a tower at each end; the sects' camp south of it behind the wall, flights up to the wall-walk on either side
# of the gate, their banners along the wall's foot; north of it the valley the Hollow has turned grey, where the
# boarlets come in waves and the Behemoth stands on the road. The way back to the gate street is the road south.
_SG = flights(stair_with_cheeks(10, 15, 3, 0, 2, "s"), stair_with_cheeks(43, 15, 3, 0, 2, "s"))
SI_SIEGE = room(
    "si_siege", size=(56, 32), biome="valley_road",
    bands=[("valley", 0, 12, dict(level=0)),
           ("wall", 12, 3, dict(level=2, paint="s")),
           ("camp", 15, 17, dict(level=0))],
    features=[("scar", (6, 3, 12, 6), dict(paint="m", shape="round")),          # where the Hollow drank the valley
              ("scar_2", (38, 1, 14, 7), dict(paint="m", shape="round")),
              ("yard", (6, 18, 44, 12), dict(paint="d", shape="round")),        # the camp's trampled earth
              ("road", (26, 0, 4, 32), dict(paint="d", walk=True)),
              ("gate", (26, 12, 4, 3), dict(level=0, paint="d")),              # the gateway through the wall
              ("tower_w", (21, 10, 5, 6), dict(level=3, paint="s")),             # the gate's towers
              ("tower_e", (30, 10, 5, 6), dict(level=3, paint="s")),
              ("tower_far_w", (1, 11, 4, 5), dict(level=3, paint="s")),          # and one at each end of the wall
              ("tower_far_e", (51, 11, 4, 5), dict(level=3, paint="s"))]
             + _SG[0],
    stairs=_SG[1],
    ways={"exit": ("s", 28)},
    spawn="exit",
    props=[("banner_jade", 6, 16), ("banner_cloud", 8, 16), ("banner_jade", 19, 16), ("banner_cloud", 36, 16),
           ("banner_jade", 47, 16), ("banner_cloud", 49, 16), ("banner_jade", 23, 10), ("banner_cloud", 32, 10),
           ("weapon_rack", 14, 19), ("weapon_rack", 39, 19), ("crates", 18, 19), ("barrel", 20, 19), ("sacks", 21, 20),
           ("crates", 34, 20), ("barrel", 36, 20), ("stove", 11, 25), ("water_jar", 14, 25), ("sacks", 15, 25),
           ("mat", 18, 26), ("crates", 38, 25), ("barrel", 40, 25), ("sacks", 41, 25), ("mat", 44, 24),
           ("lantern", 24, 18), ("lantern", 31, 18), ("lantern", 24, 26), ("lantern", 31, 26)],
    flora={"valley": {"kinds": ["dead_tree", "grey_reeds", "stump", "log", "tall_grass", "dead_tree"], "density": 0.4},
           "scar": {"kinds": ["grey_reeds", "dead_tree"], "density": 0.5},
           "camp": {"kinds": ["bush", "bush_azalea", "tall_grass", "rock_small", "bush"], "density": 0.35}},
    pins={"add": [("tree_camphor", 2, 21), ("tree_plum", 4, 28), ("tree_camphor", 53, 22), ("tree_plum", 54, 28)]},
    event={"wave": [(12, 5), (27.5, 2), (44, 6)],                             # the boarlets, out of the grey
           "fixed": [(28, 6)]})                                               # the Behemoth on the road


# The Sect War at the Alliance Gate: the pass under the Nine Peaks where the comet sails' junk has run aground against
# the cliff's edge in the north, its deck a long hull two levels over the rock, gangways down from it. The forecourt of
# the Gate between the junk and the Alliance's line: a parapet of granite a step high across the pass with its gap on
# the road, banners and racks along it; behind it the Gate's two great pillars and the road south out of the pass. The
# pirates and the turncoat disciples come down the gangways; Comet Captain Rao drops from the rail between them.
_SW = flights(stair_with_cheeks(19, 9, 3, 0, 2, "w"), stair_with_cheeks(38, 9, 3, 0, 2, "w"))
SI_SECT_WAR = room(
    "si_sect_war", size=(60, 30), biome="mountain",
    bands=[("pass", 0, 30, dict(level=0, paint="r"))],
    features=[("deck", (12, 0, 34, 9), dict(level=2, paint="w")),              # the junk's deck, its hull's side
              ("bow", (46, 1, 4, 7), dict(level=2, paint="w")), ("bow_2", (50, 2, 3, 5), dict(level=2, paint="w")),
              ("bow_3", (53, 3, 2, 3), dict(level=2, paint="w")),
              ("stern", (8, 0, 4, 8), dict(level=3, paint="w")),               # the stern castle, a level higher
              ("forecourt", (6, 13, 48, 6), dict(paint="p", shape="round")),
              ("road", (27, 9, 6, 21), dict(paint="p", walk=True)),
              ("line", (3, 20, 22, 2), dict(level=1, paint="s")),               # the Alliance's line, its gap on the road
              ("line_2", (35, 20, 22, 2), dict(level=1, paint="s")),
              ("pillar", (24, 25, 2, 2), dict(level=4, paint="s", wall=True)),   # the Gate's two great pillars
              ("pillar_2", (34, 25, 2, 2), dict(level=4, paint="s", wall=True))]
             + _SW[0],
    stairs=_SW[1],
    ways={"exit": ("s", 30)},
    spawn="exit",
    props=[("post", 17, 3), ("post", 30, 2), ("post", 41, 3), ("crates", 14, 5), ("barrel", 16, 6), ("crates", 34, 5),
           ("barrel", 44, 4), ("crates", 24, 1), ("lantern_red", 12, 7), ("lantern_red", 45, 7), ("lantern_red", 26, 7),
           ("lantern_red", 33, 7), ("barrel", 9, 2),
           ("banner_jade", 6, 20), ("banner_cloud", 13, 20), ("banner_jade", 20, 20), ("banner_cloud", 39, 20),
           ("banner_jade", 46, 20), ("banner_cloud", 53, 20), ("weapon_rack", 9, 22), ("weapon_rack", 48, 22),
           ("banner_jade", 23, 25), ("banner_cloud", 36, 25), ("lantern", 26, 27), ("lantern", 33, 27)],
    flora={"pass": {"kinds": ["rock_small", "rock_mossy", "tall_grass", "bush", "rock_small"], "density": 0.3}},
    pins={"add": [("tree_pine", 2, 6), ("tree_pine", 5, 12), ("tree_pine", 57, 11), ("tree_pine", 55, 15),
                  ("tree_pine", 3, 26), ("tree_pine", 56, 26)]},
    event={"waves": [[(20, 12), (39, 12), (29, 10)],                          # the pirates, down the gangways
                     [(13, 14), (46, 14)]],                                   # the turncoat disciples
           "timed": [(30, 13)]})                                              # Comet Captain Rao, off the rail


ROOMS = [SI_GUS_WAREHOUSE, SI_TRIAL_OF_REFLECTIONS, SI_PRESENCE_TRIAL, SI_SIEGE, SI_SECT_WAR]
