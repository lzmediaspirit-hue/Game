"""E1 room specs (R4, the peaks): the Crane Cliffs, west of Whitewater Gorge's Echo Cliffs on the way up to Mist Peak
(docs/architecture/room_engine.md). Cloud Stride's fields: Wings of Cloud (the cranes of the Cliff Faces) and Above
the Mist (the hawks of the Sky Ledges). The side view's climbs (ropes, updrafts, crags at 200 to 900 units) are
terraces and flights of stairs here, rising north up the mountain."""
from content.rooms.spec import room

# The Cliff Faces: a trail along the foot of a sheer mountain face, the cloud sea below it to the south. Under the
# cliff the crane ledges, a shelf of bare rock and turf two levels up, and on it three crags that step higher eastward
# (the orchid on the first, the cloudsteel crate on the second, the chest on the highest); south of the trail an
# alpine meadow of pines and mossy boulders ends at a rocky brink over the clouds.
CC_CLIFF_FACES = room(
    "cc_cliff_faces", size=(72, 30), biome="high_mountain", level=1,
    bands=[("crown", 0, 4, dict(level=6, paint="r", wall=True)),
           ("ledges", 4, 9, dict(level=3, paint="r", wavy="s", flights=[14, 40])),
           ("path", 14, 3, dict(paint="d", walk=True)),
           ("brink", 23, 7, dict(level=0)),
           ("meadow", 17, 7, dict(level=1, wavy="s"))],
    features=[("crag_mid", (30, 4, 9, 4), dict(level=4, paint="r", shape="round")),
              ("crag_e", (43, 4, 9, 4), dict(level=4, paint="r", shape="round")),
              ("crag_top", (53, 4, 8, 4), dict(level=5, paint="r", shape="round"))],
    stairs="auto",
    ways={"east": ("e", "path"), "west": ("w", "path")},
    spawn="east",
    anchors={"jar_3": "ledges@12", "ore_2": "wall_foot@26", "herb_1": "crag_mid@35", "crate_4": "crag_e@48",
             "chest_crag_600": "crag_top.top", "jar_5": "verge.n@44", "crate_6": "verge.s@62", "rift_tear": "brink@40",
             "spirit_fruit_tree": "meadow@22"},
    flora={"ledges": dict(density=0.5), "meadow": dict(density=0.36), "brink": dict(density=0.4)},
    foes="auto")

# The Sky Ledges: the mountain's shoulder above the Cliff Faces, where the trail turns west for Mist Peak. North of the
# trail the shelves climb in round steps toward the summit in the north-east, a flight up each (the orchids, the
# cloudsteel and the crate on the way, the chest on the summit over the clouds); the alpine meadow and its brink under
# the trail, as on the Cliff Faces.
CC_SKY_LEDGES = room(
    "cc_sky_ledges", size=(56, 32), biome="high_mountain", level=1,
    bands=[("crown", 0, 3, dict(level=8, paint="r", wall=True)),
           ("ledges", 3, 13, dict(level=2, wavy="s", flights=[9, 26])),
           ("path", 17, 3, dict(paint="d", walk=True)),
           ("brink", 26, 6, dict(level=0)),
           ("meadow", 20, 7, dict(level=1, wavy="s"))],
    features=[("shoulder", (17, 3, 46, 11), dict(level=3, paint="r", shape="round")),
              ("spur", (30, 3, 34, 10), dict(level=4, paint="r", shape="round")),
              ("summit", (42, 3, 17, 6), dict(level=5, paint="r", shape="round"))],
    stairs="auto",
    ways={"east": ("e", "path"), "west": ("w", "path")},
    spawn="east",
    anchors={"rare_orchid_sl": "ledges@12", "herb_2": "shoulder@24", "ore_3": "wall_foot@30", "herb_1": "spur@35",
             "jar_4": "spur@40", "ore_cloudsteel_high": "summit@44", "crate_5": "summit@48",
             "chest_cloud_900": "summit.front@53", "jar_6": "verge.s@34", "crate_7": "verge.s@46", "rift_tear": "meadow@30",
             "spirit_fruit_tree": "meadow@16", "swarm_silk_moth": "brink@22", "trail_cloud_marmot": "meadow@42"},
    flora={"ledges": dict(density=0.45), "meadow": dict(density=0.36), "brink": dict(density=0.4)},
    foes="auto")

ROOMS = [CC_CLIFF_FACES, CC_SKY_LEDGES]
