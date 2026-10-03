"""E1 room specs (R7, Act II's chapter 13): the Gale Canyons, down the Presence Terrace's road east of Nine Peaks
(docs/architecture/room_engine.md, "Nine Peaks to the Tomb of Sunscar (R7)"). The Canyon Mouth's toll, the Kite Winds,
the Harpy Roosts and the Windbridge over the chasm to Ironroot Hold. Red-rock canyons (`canyon`): walls of layered
sandstone over a floor of red earth, the trail a sandy wash, hoodoos and sandstone boulders, grey trees the wind
killed, prayer flags snapping on the gusts. The side view's ledges and pinnacles are mesas and shelves here, plank
steps up each."""
from content.rooms.spec import room

WALL = dict(level=5, wall=True, wavy="s")   # the canyon's north wall, five levels of layered sandstone


def rim(y=22, xs=(0, 15, 32, 49), w=(18, 22, 21, 24)):
    """The canyon's low south rim: humps of sandstone a level over the floor, each a round shape cut by the room's
    edge, so its lip arcs and never runs ruled."""
    return [("rim", (x, y + (k % 2), ww, 11), dict(level=1, shape="round")) for k, (x, ww) in enumerate(zip(xs, w))]


# The Canyon Mouth: where the road down from the Presence Terrace enters the canyons. The tollkeeper's house and the
# Alliance's barrier stand at the west end of the trail; north of it the sandstone ledges climb under the wall to a mesa
# where two chests wait, the ore vein at the wall's foot; south of the trail the red floor runs to a low rim of
# sandstone among hoodoos.
GC_CANYON_MOUTH = room(
    "gc_canyon_mouth", size=(72, 28), biome="canyon",
    bands=[("ledges", 3, 9, dict(level=1, wavy="s", flights=[16, 48])),
           ("cliff", 0, 4, WALL),
           ("trail", 13, 3, dict(walk=True)),
           ("floor", 16, 12, dict(level=0))],
    features=[("mesa", (20, 3, 11, 6), dict(level=2, shape="round", flights=[25])),
              ("shelf", (42, 3, 10, 6), dict(level=2, shape="round", flights=[47]))] + rim(),
    stairs="auto",
    ways={"west": ("w", "trail"), "east": ("e", "trail")},
    spawn="west",
    anchors={"npc_tollkeeper_bai": "verge.s@9", "jar_2": "ledges@16", "chest_ledge_mv_1": "mesa@24",
             "chest_cloud_mv": "mesa@27", "ore_1": "wall_foot@36", "jar_4": "verge.s@45", "crate_3": "shelf@47",
             "crate_5": "floor@64"},
    props=[("storehouse", 2, 6), ("banner_jade", 7, 12), ("banner_cloud", 13, 12), ("post", 7, 16), ("post", 13, 16),
           ("prayer_flags", 32, 18), ("prayer_flags", 55, 9), ("lantern", 6, 9)],
    flora={"ledges": dict(density=0.3), "floor": dict(density=0.28), "rim": dict(density=0.4)},
    foes="auto")


# The Kite Winds: the trail climbs onto a shelf high on the canyon's north wall, where the updrafts lift the wind kites.
# Above it the wall's ledges and two sandstone pinnacles (a jar on the first, a crate on the higher); south of it the
# shelf's lip, prayer flags snapping along it, and a long drop to the red floor of the canyon far below.
GC_KITE_WINDS = room(
    "gc_kite_winds", size=(72, 28), biome="canyon",
    bands=[("floor", 19, 9, dict(level=0)),
           ("lip", 10, 9, dict(level=2, wavy="s")),
           ("ledges", 3, 10, dict(level=3, wavy="s", flights=[50])),
           ("cliff", 0, 4, dict(WALL, level=7)),
           ("trail", 14, 3, dict(level=2, walk=True))],
    features=[("pinnacle_w", (12, 3, 9, 6), dict(level=4, shape="round", flights=[16])),
              ("pinnacle_e", (32, 3, 10, 6), dict(level=5, shape="round", flights=[37])),
              ("butte", (46, 22, 14, 9), dict(level=1, shape="round"))] + rim(25, (0, 20, 58), (16, 18, 16)),
    stairs="auto",
    ways={"west": ("w", "trail"), "east": ("e", "trail")},
    spawn="west",
    anchors={"jar_1": "pinnacle_w@16", "crate_2": "pinnacle_e@37", "journal_kites": "verge.s@34", "jar_3": "ledges@44",
             "crate_4": "verge.n@64"},
    props=[("prayer_flags", 6, 17), ("prayer_flags", 25, 16), ("prayer_flags", 47, 17), ("prayer_flags", 62, 16)],
    flora={"ledges": dict(density=0.3), "lip": dict(density=0.3), "floor": dict(density=0.34)},
    foes="auto")


# The Harpy Roosts: three sandstone pinnacles rise out of the canyon north of the trail, the harpies' nests of bones
# and dead wood on their tops (the chest on the first, a jar and a crate on the second, the bloodroot ginseng on the
# third), a plank stair up each; the canyon's shrine at the west end, the ore at the wall's foot, an old roost's
# carving on the trail; the red floor and its rim to the south.
GC_HARPY_ROOSTS = room(
    "gc_harpy_roosts", size=(72, 28), biome="canyon",
    bands=[("cliff", 0, 3, dict(WALL, level=6)),
           ("canyon", 3, 14, dict(level=0)),
           ("trail", 17, 3, dict(walk=True)),
           ("floor", 20, 8, dict(level=0))],
    features=[("roost_w", (9, 2, 11, 8), dict(level=4, shape="round", flights=[14])),
              ("roost_mid", (28, 2, 11, 8), dict(level=4, shape="round", flights=[33])),
              ("roost_e", (47, 2, 11, 8), dict(level=4, shape="round", flights=[52]))] + rim(24),
    stairs="auto",
    ways={"west": ("w", "trail"), "east": ("e", "trail")},
    spawn="west",
    anchors={"shrine_gc": "canyon@4", "chest_6": "roost_w@12", "jar_2": "roost_w@17", "crate_3": "roost_mid@31",
             "ore_1": "wall_foot@41", "lost_harpy_roost": "verge.n@43", "jar_4": "verge.s@58",
             "rare_ginseng_hr": "roost_e@52", "crate_5": "floor@63"},
    props=[("ribcage", 11, 4), ("ribcage", 34, 4), ("ribcage", 49, 4), ("dead_tree", 19, 5), ("dead_tree", 29, 5),
           ("dead_tree", 56, 5), ("prayer_flags", 22, 21), ("prayer_flags", 60, 21)],
    flora={"canyon": dict(density=0.3), "floor": dict(density=0.3), "roost_w": ["dry_scrub", "red_rock"],
           "roost_mid": ["dry_scrub", "red_rock"], "roost_e": ["dry_scrub", "red_rock"]},
    foes="auto")


# The Windbridge: the canyon splits under the trail into a chasm a river runs down, and the Windbridge spans it, planks
# on trestles three levels over the water, prayer flags at either end. West of the chasm the shelf the trail comes in
# on, a crag with a chest under the wall; a stair cut down the shelf's south face to the floor of the chasm, where the
# river's crate washed up; east of it the shelf on to Ironroot Hold.
GC_WINDBRIDGE = room(
    "gc_windbridge", size=(72, 28), biome="canyon",
    bands=[("shelf", 3, 17, dict(level=3, wavy="s", flights=[12])),
           ("cliff", 0, 4, dict(WALL, level=7)),
           ("trail", 12, 3, dict(level=3, walk=True)),
           ("floor", 20, 8, dict(level=0))],
    features=[("chasm", (24, -5, 21, 22), dict(level=0, shape="round")),
              ("chasm", (27, 9, 21, 24), dict(level=0, shape="round")),
              ("river", (31, -4, 6, 12), dict(water=True, shape="round")),
              ("river", (32, 4, 6, 12), dict(water=True, shape="round")),
              ("river", (34, 13, 6, 10), dict(water=True, shape="round")),
              ("river", (33, 20, 6, 12), dict(water=True, shape="round")),
              ("crag", (14, 3, 9, 5), dict(level=4, shape="round", flights=[18])),
              ("bridge", (23, 12, 26, 3), dict(level=3, paint="w"))] + rim(24, (0, 52), (18, 22)),
    stairs="auto",
    ways={"west": ("w", "trail"), "east": ("e", "trail")},
    spawn="west",
    anchors={"jar_1": "verge.n@5", "chest_ledge_mv_1": "crag@18", "crate_2": "floor@29", "jar_3": "verge.s@60"},
    props=[("prayer_flags", 20, 11), ("prayer_flags", 49, 11), ("prayer_flags", 20, 15), ("prayer_flags", 49, 15)],
    flora={"shelf": dict(density=0.32), "floor": dict(density=0.3), "river": ["dry_scrub", "cattails", "tall_grass"]},
    foes="auto")

ROOMS = [GC_CANYON_MOUTH, GC_KITE_WINDS, GC_HARPY_ROOSTS, GC_WINDBRIDGE]
