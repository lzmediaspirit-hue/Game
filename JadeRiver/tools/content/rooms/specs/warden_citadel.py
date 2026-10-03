"""E1 room specs (R9, Act III's chapter 20): the Star Warden Citadel, the Wardens' fortress-town on the Field's central
island (docs/architecture/room_engine.md, "The star field's end (R9)"). The Citadel Gate under the great wall, its
Wardens' Hall and its Observatory's tower, the skiffs' piers on the brink; the Wardens' Hall itself, the Observatory, and
the Presence Court where the Wardens spar. The Wardens' white granite and flagstones (R5's Tidebreak Bastion is theirs
too), star lanterns and banners of indigo and gold, the stone Wardens on their plinths, a fallen star in its cage over
the gate court; the cloud sea under the island's brink. A wall that must read as one runs east and west (R5)."""
from content.rooms.spec import room
from content.rooms.specs.story import flights, stair_with_cheeks

WALL = dict(level=5, paint="s", wall=True)        # the Citadel's great wall along every room's north edge
HALL_WALLS = dict(high=5, low=1, paint="s")       # the interiors' granite, five levels, the front a low sill


# The Citadel Gate: the Wardens' gate court under the great wall, between its two towers. The Wardens' Hall stands at the
# wall's foot, its door down a granite walk to the road; the Observatory is the tall tower in the wall east of the court,
# its door sunk in its foot; a fallen star burns in its cage on the court's dais, the gate shrine beside it, stone
# Wardens and the Wardens' banners along the wall. The road runs east to west through the court: west to the Presence
# Court, east between two bastions with their ballistae (the Warden line) to the Orbit Ruins. South of the road a plaza
# with the teleport stone and the gardens, then the island's brink, three piers out over the cloud sea: the skiff to
# Lanternfall Harbor in the west, the skiffs to the Ashen Reach and the Tidebreak Bastion in the middle.
WC_CITADEL_GATE = room(
    "wc_citadel_gate", size=(72, 28), biome="citadel",
    bands=[("wall", 0, 5, WALL),
           ("court", 5, 8, dict(level=0, paint="p")),
           ("road", 13, 4, dict(paint="s", walk=True)),
           ("plaza", 17, 5, dict(level=0, paint="p")),
           ("rim", 22, 6, dict(level=0, paint="r", wavy="n"))],
    features=[("tower", (1, 0, 7, 7), dict(level=6, paint="s", wall=True)),
              ("tower_2", (63, 0, 8, 7), dict(level=6, paint="s", wall=True)),
              ("observatory", (40, 2, 10, 7), dict(level=6, paint="t", wall=True)),   # its tower, out from the wall
              ("doorway", (44, 6, 2, 3), dict(level=0, paint="p")),                  # its door, sunk in its foot
              ("dais", (32, 6, 6, 4), dict(level=1, paint="s")),                     # the caged star's dais
              ("bastion", (58, 8, 5, 5), dict(level=3, paint="s", wall=True)),       # the Warden line's bastions
              ("bastion_2", (58, 17, 5, 5), dict(level=3, paint="s", wall=True)),
              ("garden", (13, 17, 11, 5), dict(paint="g", wavy="s")),
              ("garden_2", (41, 17, 12, 5), dict(paint="g", wavy="s")),
              ("pier", (9, 21, 3, 7), dict(level=0, paint="w")),                     # the skiffs' piers
              ("pier_2", (27, 21, 3, 7), dict(level=0, paint="w")),
              ("pier_3", (35, 21, 3, 7), dict(level=0, paint="w"))],
    stairs="auto",
    ways={"skiff": ("s", 10, dict(arrive=4)), "west": ("w", "road"),
          "hall_door": ("door", "wardens_hall", dict(path=(13, "s"))),
          "observatory_door": dict(at=(44.5, 6), dir="n", arrive=(44.5, 10), span=2),
          "ash_skiff": ("s", 28, dict(arrive=4)), "tide_skiff": ("s", 36, dict(arrive=4)), "east": ("e", "road")},
    spawn="skiff",
    anchors={"sign_wc": "walk.n@14", "shrine_wc_gate": "court@39", "stone_star_citadel": "plaza@55"},
    props=[("hall", 22, 5, "wardens_hall"), ("lantern_cage", 34, 7), ("warden_statue", 23, 9), ("warden_statue", 28, 9),
           ("warden_statue", 42, 9), ("warden_statue", 47, 9), ("warden_banner", 12, 5), ("warden_banner", 18, 5),
           ("warden_banner", 52, 5), ("warden_banner", 56, 5), ("star_lantern", 32, 10), ("star_lantern", 37, 10),
           {"kind": "star_lantern", "along": "road", "every": 9, "row": 12, "start": 4},
           {"kind": "star_lantern", "along": "road", "every": 9, "row": 17, "start": 8},
           ("ballista", 59, 9), ("ballista", 59, 18), ("star_lantern", 8, 21), ("star_lantern", 12, 21),
           ("star_lantern", 26, 21), ("star_lantern", 30, 21), ("star_lantern", 34, 21), ("star_lantern", 38, 21),
           ("post", 9, 27), ("post", 11, 27), ("post", 27, 27), ("post", 29, 27), ("post", 35, 27), ("post", 37, 27),
           ("crates", 5, 18), ("barrel", 7, 19), ("sacks", 31, 18), ("barrel", 32, 19), ("crates", 64, 18),
           ("weapon_rack", 64, 9), ("barrel", 67, 10)],
    flora={"court": dict(density=0.1), "plaza": dict(density=0.1), "garden": dict(density=0.9),
           "garden_2": dict(density=0.9), "rim": {"kinds": ["rock_mossy", "star_crystal", "rock_small", "bush"], "density": 0.4}})


# The Wardens' Hall: the Commander's hall of granite under the wall. Warden-Commander Yao stands at the great chart
# table in the middle of the floor; the Commander's granite seat on its dais against the back wall between the
# Wardens' banners, a flight up its middle; a stone Warden in the corner, the scroll racks of the Wardens' reports down
# the east wall, the weapon racks down the west, star lanterns at the door.
_hall_cheeks, _hall_stairs = flights(stair_with_cheeks(13, 5, 2, 0, 1, "s"))
WC_WARDENS_HALL = room(
    "wc_wardens_hall", size=(28, 16), base="p", walls=HALL_WALLS,
    features=[("dais", (6, 1, 16, 4), dict(level=1, paint="s"))] + _hall_cheeks,
    stairs=_hall_stairs,
    ways={"entry": ("s", 13.5)},
    spawn="entry",
    anchors={"npc_warden_commander_yao": (16, 9)},
    props=[("trial_seat", 13, 2), ("warden_banner", 7, 1), ("warden_banner", 20, 1), ("star_lantern", 10, 3),
           ("star_lantern", 17, 3), ("star_chart_table", 12, 9), ("warden_statue", 1, 2), ("scroll_shelf", 24, 3),
           ("scroll_shelf", 24, 6), ("desk", 24, 10), ("weapon_rack", 1, 6), ("weapon_rack", 1, 9),
           ("star_lantern", 9, 14), ("star_lantern", 18, 14), ("mat", 3, 12), ("pot_bonsai", 26, 13)])


# The Observatory: a round hall of granite under the open dome, the great scope's dais against the back wall, the
# armillary of the heavens on it beside the scope's mount (the scope itself is the side view's, set up for The
# Observatory); Stargazer Ming at the chart tables below it, the lens of far seeing on its stand by the east wall, scroll
# racks of star charts round the walls, star lanterns, the Wardens' banners at the door.
_obs_cheeks, _obs_stairs = flights(stair_with_cheeks(13, 6, 2, 0, 1, "s"))
# Its cheeks two levels over the dais, not one: from the dais a cheek a level up is a hop, and a body that hopped onto
# it (the great scope's spot is beside the stair's head) stalled coming off (rules_tests' route tour).
_obs_cheeks = [(n, r, dict(o, level=3)) for n, r, o in _obs_cheeks]
WC_OBSERVATORY = room(
    "wc_observatory", size=(28, 16), base="p", walls=HALL_WALLS,
    features=[("floor", (3, 1, 22, 14), dict(paint="s", shape="round")),
              ("dais", (7, 1, 14, 5), dict(level=1, paint="s"))] + _obs_cheeks,
    stairs=_obs_stairs,
    ways={"entry": ("s", 13.5)},
    spawn="entry",
    anchors={"great_scope": (15, 3), "npc_stargazer_ming": (9, 10), "lost_lens_of_far_seeing": (23, 10)},
    props=[("star_globe", 9, 3), ("star_lantern", 7, 1), ("star_lantern", 20, 1), ("star_chart_table", 4, 9),
           ("star_chart_table", 18, 10), ("scroll_shelf", 1, 1), ("scroll_shelf", 3, 1), ("scroll_shelf", 22, 1),
           ("scroll_shelf", 24, 1), ("desk", 1, 5), ("star_lantern", 9, 7), ("star_lantern", 18, 7),
           ("warden_banner", 9, 14), ("warden_banner", 18, 14), ("star_crystal", 25, 6), ("pot_orchid", 1, 13)])


# The Presence Court: the Citadel's west end, where the Wardens spar with their Presence held. A round court of granite
# in the middle of the paving, the three pressure pillars standing round its north rim, their glyphs lit while a Presence
# presses on it; Presence Master Ruo watches from its west side, and Shen Lian waits on it for the aspirant. A terrace
# under the wall's west tower with a stone Warden looking down on the court, gardens either side, the road in from the
# Citadel Gate in the east; the island's brink to the south over the cloud sea.
WC_PRESENCE_COURT = room(
    "wc_presence_court", size=(56, 28), biome="citadel",
    bands=[("wall", 0, 5, WALL),
           ("court", 5, 17, dict(level=0, paint="p")),
           ("road", 14, 3, dict(paint="s", walk=True, x=40)),
           ("rim", 22, 6, dict(level=0, paint="r", wavy="n"))],
    features=[("tower", (0, 0, 9, 7), dict(level=6, paint="s", wall=True)),
              ("terrace", (1, 7, 9, 9), dict(level=2, paint="s", flights=[5])),
              ("arena", (14, 6, 26, 15), dict(paint="s", shape="round")),
              ("garden", (42, 5, 13, 6), dict(paint="g", wavy="s")),
              ("garden_2", (2, 18, 10, 4), dict(paint="g", wavy="n")),
              ("garden_3", (42, 18, 12, 4), dict(paint="g", wavy="n"))],
    stairs="auto",
    ways={"east": ("e", "road")},
    spawn="east",
    anchors={"npc_presence_master_ruo": (17, 13), "npc_shen_lian_warden": (27, 14), "sign_wc_court": "walk.n@52"},
    props=[("pressure_pillar", 18, 8), ("pressure_pillar", 27, 6), ("pressure_pillar", 36, 8), ("warden_statue", 5, 8),
           ("warden_banner", 11, 5), ("warden_banner", 40, 5), ("star_lantern", 3, 8), ("star_lantern", 8, 8),
           ("star_lantern", 15, 19), ("star_lantern", 38, 19), ("star_lantern", 44, 13), ("star_lantern", 44, 17),
           ("weapon_rack", 12, 18), ("mat", 31, 18)],
    flora={"court": dict(density=0.08), "garden": dict(density=0.9), "garden_2": dict(density=0.9),
           "garden_3": dict(density=0.9), "terrace": [],
           "rim": {"kinds": ["rock_mossy", "star_crystal", "rock_small", "bush"], "density": 0.4}})

ROOMS = [WC_CITADEL_GATE, WC_WARDENS_HALL, WC_OBSERVATORY, WC_PRESENCE_COURT]
