"""E1 room specs (R9, Act III's chapter 20): the Orbit Ruins, the first Wardens' observatory-temple broken and turning in
the dark past the Citadel's Warden line (docs/architecture/room_engine.md, "The star field's end (R9)"). The Tumbling
Stair, the Orbit Garden where the Orbit Hermit keeps his star lotus, the Golem Foundry and the Inverted Hall behind it.
Floors and broken rings of dressed granite on the island's grey rock, chunks of masonry floating over their rune rings,
star crystals grown out of the rock; each jade gravity switch stands in its own ring of stone, gravity plates set in
the floor round it where the side view's switch lightens the air (the low gravity itself is still the side view's).
The island's brink falls away south to the cloud sea, as the Citadel's does."""
import math

from content.rooms.spec import room

CLIFF = dict(level=4, paint="r", wall=True, wavy="s")   # the island's rock rising behind every room


def ring(name, cx, cy, ro, ri, level, gaps=(), paint="s"):
    """A ring of dressed stone round (cx, cy): the cells between radius `ri` and `ro`, raised to `level`, broken where
    their angle (degrees, 0 east, 90 south) falls in one of `gaps`; laid as row runs, each a feature of the ring's name
    (ring, ring_2, ...)."""
    def broken(x, y):
        a = math.degrees(math.atan2(y + 0.5 - cy, x + 0.5 - cx))
        return any(a0 <= a <= a1 or a0 <= a + 360 <= a1 for a0, a1 in gaps)
    out = []
    for y in range(int(cy - ro) - 1, int(cy + ro) + 2):
        run = None
        for x in range(int(cx - ro) - 1, int(cx + ro) + 3):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            on = ri <= d <= ro and not broken(x, y)
            if on and run is None:
                run = x
            elif not on and run is not None:
                out.append((name, (run, y, x - run, 1), dict(level=level, paint=paint)))
                run = None
    return out


def plates(cx, cy, r=2):
    """The gravity plates round a switch at (cx, cy): one at each of the four sides, `r` cells off."""
    return [("gravity_plate", cx + dx, cy + dy) for dx, dy in ((-r, 0), (r, 0), (0, -r), (0, r))]


def stones(*cells):
    """Masonry floating over its rune ring."""
    return [("orbit_stone", x, y) for x, y in cells]


# The Tumbling Stair: where the Warden line opens onto the Ruins, the old processional way runs east under the island's
# rock. North of it the temple's grand stair lies broken into three landings, a level, two and a level up, tumbled
# blocks between them; south of it the first jade switch stands in its broken ring on a round granite floor, its plates
# round it, the side view's lightened air over the middle of the room; a second ring, broken further, hangs over the
# brink in the east. Masonry floats over its rune rings along the brink and under the rock.
OR_TUMBLING_STAIR = room(
    "or_tumbling_stair", size=(72, 28), biome="orbit_ruins",
    bands=[("cliff", 0, 4, CLIFF),
           ("road", 13, 3, dict(paint="s", walk=True)),
           ("brink", 23, 5, dict(level=0, wavy="n"))],
    features=[("landing", (11, 5, 10, 6), dict(level=1, paint="s", flights=[16])),
              ("landing_2", (31, 4, 12, 7), dict(level=2, paint="s", flights=[37])),
              ("landing_3", (50, 5, 10, 6), dict(level=1, paint="s", flights=[55])),
              ("block", (24, 6, 2, 2), dict(level=2, paint="s")),                   # the stair's tumbled blocks
              ("block_2", (27, 9, 2, 1), dict(level=1, paint="s")),
              ("block_3", (45, 6, 2, 2), dict(level=2, paint="s")),
              ("block_4", (47, 9, 1, 1), dict(level=1, paint="s")),
              ("plaza", (25, 16, 10, 10), dict(paint="p", shape="round"))]
             + ring("ring", 30, 21, 6.2, 4.8, 1, gaps=[(-125, -55), (20, 55), (150, 170)])
             + ring("ring_e", 62, 21, 5.6, 4.2, 2, gaps=[(-160, -20), (60, 200)]),
    stairs="auto",
    ways={"west": ("w", "road"), "east": ("e", "road")},
    spawn="west",
    anchors={"shrine_or_stair": "verge.s@8", "jar_1": "landing@16", "crate_2": "landing_2@38", "switch_stair": (30, 21),
             "jar_3": "verge.n@44", "lost_inverted_stair_kick": "verge.s@47", "lost_lamp_that_circles_the_dark": "verge.s@55",
             "crate_4": "verge.n@63"},
    props=plates(30, 21) + stones((4, 19), (16, 20), (42, 20), (21, 7), (63, 7), (67, 24), (45, 25), (9, 25)),
    flora={"cliff": dict(density=0.45), "brink": dict(density=0.45), "plaza": [], "density": 0.28},
    foes="auto")


# The Orbit Garden: the Orbit Hermit's garden in the ruins, a lawn inside a great broken ring of stone north of the way,
# star lotus and plum blossom in it, his mat and tea table by its open south side where he sits; a raised floor of the
# old temple in the east where a crate was left, the second jade switch in its ring south of the way with its plates;
# masonry floating all round, star crystals in the rock.
OR_ORBIT_GARDEN = room(
    "or_orbit_garden", size=(72, 28), biome="orbit_ruins",
    bands=[("cliff", 0, 3, CLIFF),
           ("road", 15, 3, dict(paint="s", walk=True)),
           ("brink", 23, 5, dict(level=0, wavy="n"))],
    features=[("garden", (15, 4, 20, 10), dict(level=0, paint="g", shape="round"))]
             + ring("ring", 25, 9.5, 6.6, 5.1, 2, gaps=[(50, 130), (195, 215), (-60, -40)])
             + [("floor", (42, 5, 11, 6), dict(level=2, paint="s", flights=[47])),
                ("floor_2", (4, 5, 7, 6), dict(level=1, paint="s", flights=[7])),
                ("plaza", (53, 18, 9, 9), dict(paint="p", shape="round"))]
             + ring("ring_2", 57, 22, 5.4, 4.0, 1, gaps=[(-130, -50), (100, 130)]),
    stairs="auto",
    ways={"west": ("w", "road"), "east": ("e", "road")},
    spawn="west",
    anchors={"herb_1": (21, 8), "jar_3": (28, 7), "npc_orbit_hermit": (25, 12), "crate_4": "floor@46",
             "jar_5": "verge.s@44", "lost_lamp_on_a_tether": "verge.n@52", "herb_2": "verge.s@49", "switch_garden": (57, 22),
             "crate_6": "verge.n@64"},
    props=[("mat", 21, 12), ("tea_table", 27, 12)] + plates(57, 22)
          + stones((3, 19), (12, 20), (38, 6), (38, 20), (66, 7), (68, 19), (31, 24), (8, 25)),
    flora={"garden": {"kinds": ["tree_plum", "bush_azalea", "tall_grass", "ferns", "star_crystal", "tree_plum"], "density": 0.7},
           "cliff": dict(density=0.45), "brink": dict(density=0.45), "plaza": [], "density": 0.28},
    foes="auto")


# The Golem Foundry: where the first Wardens made their gravity golems, under the rock. A paved foundry floor north of
# the way, the forges and the great flame basin that fired the golems' cores, husks of the broken golems lying about; a
# ledge at the rock's foot (the driftglass in its seam) and a high casting gallery a level and three up, where the chests
# were left; in the east the Inverted Hall's house of dressed stone, its door sunk in its foot. South of the way the brink.
OR_GOLEM_FOUNDRY = room(
    "or_golem_foundry", size=(72, 28), biome="orbit_ruins",
    bands=[("cliff", 0, 5, dict(CLIFF, level=5)),
           ("floor", 5, 9, dict(level=0, paint="p")),
           ("road", 14, 3, dict(paint="s", walk=True)),
           ("brink", 23, 5, dict(level=0, wavy="n"))],
    features=[("ledge", (12, 4, 10, 5), dict(level=1, paint="r", flights=[18])),
              ("gallery", (27, 4, 14, 6), dict(level=3, paint="s", flights=[34])),
              ("hall_house", (60, 2, 11, 9), dict(level=5, paint="s", wall=True)),   # the Inverted Hall's house
              ("doorway", (64, 8, 2, 3), dict(level=0, paint="p"))],
    stairs="auto",
    ways={"west": ("w", "road"), "hall": dict(at=(64.5, 8), dir="n", arrive=(64.5, 12), span=2)},
    spawn="west",
    anchors={"ore_1": "ledge@17", "jar_3": "ledge@21", "chest_7": "gallery@32", "chest_cloud_mv": "gallery@36",
             "crate_4": "floor@44", "lost_orbit_stone_sling": "verge.s@21", "jar_5": "verge.s@44",
             "journal_foundry": "verge.s@47", "ore_2": "wall_foot@54", "crate_6": "verge.s@63"},
    props=[("flame_basin", 29, 11), ("forge", 5, 6), ("forge", 46, 6), ("anvil", 8, 7), ("anvil", 49, 7),
           ("golem_husk", 22, 11), ("golem_husk", 51, 11), ("golem_husk", 9, 19), ("golem_husk", 40, 20),
           ("star_lantern", 62, 11), ("star_lantern", 67, 11), ("crates", 56, 6), ("barrel", 58, 7)]
          + stones((14, 20), (31, 21), (56, 20), (4, 24), (66, 24)),
    flora={"floor": dict(density=0.1), "cliff": dict(density=0.45), "brink": dict(density=0.45), "density": 0.28},
    foes="auto")


# The Inverted Hall: the temple's hall where the stars hold the air still (no flying). Its two jade switches stand in
# rings of stone either end of the floor, their plates round them; a low gallery a level up and a high gallery three up
# along the back wall (the side view's high gallery out of any jump's reach until the air is light; on the grid a flight
# climbs it), the chest on the high one; masonry hangs in the air down the hall's middle, pillars down either side.
def _pillars(xs, y, levels):
    return [("pillar", (x, y, 1, 1), dict(level=levels[i % len(levels)], paint="s", wall=True)) for i, x in enumerate(xs)]


OR_INVERTED_HALL = room(
    "or_inverted_hall", size=(56, 24), base="p", biome="orbit_ruins", walls=dict(high=5, low=1, paint="s"),
    features=[("aisle", (1, 11, 54, 3), dict(paint="s", walk=True)),
              ("gallery_low", (15, 1, 10, 4), dict(level=1, paint="s", flights=[20])),
              ("gallery_high", (31, 1, 11, 4), dict(level=3, paint="s", flights=[36]))]
             + _pillars(range(7, 52, 8), 8, [5, 3, 5, 5, 2, 5]) + _pillars(range(7, 52, 8), 16, [5, 5, 4, 5, 5, 3])
             + ring("ring", 15, 19, 3.6, 2.2, 1, gaps=[(-115, -65)]) + ring("ring_2", 44, 19, 3.6, 2.2, 1, gaps=[(-115, -65)]),
    stairs="auto",
    ways={"entry": ("w", 12)},
    spawn="entry",
    anchors={"switch_hall_a": (15, 19), "switch_hall_b": (44, 19), "chest_gallery": "gallery_high@37",
             "lost_upside_down_staff": "aisle.n@19", "lost_gravity_knot": "aisle.s@25"},
    props=plates(15, 19, 1) + plates(44, 19, 1) + stones((23, 5), (28, 18), (48, 5), (5, 18))
          + [("star_lantern", 2, 9), ("star_lantern", 2, 15), ("star_crystal", 53, 2), ("star_crystal", 1, 1)],
    flora={"density": 0.2},
    foes="auto")

ROOMS = [OR_TUMBLING_STAIR, OR_ORBIT_GARDEN, OR_GOLEM_FOUNDRY, OR_INVERTED_HALL]
