"""E1 room specs: Stonewall Quarry, up the Quarry Road north of Stoneford Gate (docs/architecture/room_engine.md; batch
R3): the rim where Foreman Dong's crews work the upper face, the lower pit under it, and the collapsed tunnel off the
pit's floor."""
from content.rooms.spec import room

# The Quarry Rim: the quarry's upper face cut in benches behind the working yard, the crews' timber scaffold on the
# bench where the pebble imps throw, ore at the face's foot; the haul road east down to the pit, the Quarry Road up from
# Stoneford Gate through the pines, a spoil heap, the foreman's shed and the crews' stacks.
SQ_QUARRY_RIM = room(
    "sq_quarry_rim", size=(56, 28), biome="quarry",
    bands=[("face", 0, 4, dict(level=4, paint="r", wall=True)),
           ("bench", 4, 5, dict(level=2, paint="r")),
           ("yard", 9, 8, dict(level=0, paint="d")),
           ("road", 17, 3, dict(paint="d", walk=True)),
           ("hillside", 20, 8, dict(level=0, paint="g"))],
    features=[("scaffold", (27, 4, 14, 2), dict(level=3, paint="w")),
              ("quarry_road", (12, 20, 3, 8), dict(paint="d")),
              ("spoil", (40, 21, 9, 4), dict(level=1, paint="r", shape="round")),
              ("cheek", (27, 6, 1, 2), dict(level=4, paint="w")),            # the scaffold ladder's posts
              ("cheek_2", (31, 6, 1, 2), dict(level=4, paint="w"))],
    stairs="auto",
    ways={"south": ("s", 13), "east": ("e", "road")},
    spawn="south",
    anchors={"ore_1": "wall_foot@9", "ore_2": "wall_foot@22", "ore_3": "wall_foot@46", "jar_4": "bench@11",
             "crate_5": "scaffold@28", "jar_6": "verge.s@29", "crate_7": "verge.n@39", "jar_8": "verge.n@49",
             "npc_dong_rim": "road.n@10", "rift_tear": "yard@31", "spirit_fruit_tree": "hillside@24",
             "trail_mist_hare": "hillside@32"},
    props=[("storehouse", 2, 9), ("crates", 7, 11), ("barrel", 9, 11), ("woodpile", 14, 10), ("sacks", 20, 10),
           ("crates", 39, 10), ("barrel", 41, 10), ("lantern", 11, 20), ("lantern", 15, 20)],
    flora={"hillside": dict(density=0.34)},
    foes=["auto", "auto:scaffold", "auto", "auto"],
    # T2 (docs/architecture/topdown_mechanics.md): the side view's crane lift, a basket in the yard under the bench that
    # a body stepping in sets off, up to the bench and back down.
    traverse=[("lift", "crane_lift", dict(at=(16, 9), path=[(0, 0, 2)], speed=45, wait_s=2.0, mode="trigger"))],
    pins={"stairs": [(26, 9, 3, 4, 0, 2), (28, 6, 3, 2, 2, 3)]})


# The Lower Pit: the quarry's floor under the rim, its walls cut in two benches up to the north rim (the chest left on
# the high one), ore at their feet and the spirit seam in the floor, a rainwater pool, the haul road in from the rim,
# and the old tunnel's mouth in the north-east face.
SQ_LOWER_PIT = room(
    "sq_lower_pit", size=(56, 28), biome="quarry",
    bands=[("rim", 0, 3, dict(level=5, paint="r", wall=True)),
           ("bench_2", 3, 4, dict(level=3, paint="r")),
           ("bench_1", 7, 4, dict(level=1, paint="r")),
           ("floor", 11, 6, dict(level=0, paint="d")),
           ("road", 17, 3, dict(paint="d", walk=True)),
           ("floor_s", 20, 5, dict(level=0, paint="r")),
           ("south_lip", 25, 3, dict(level=1, paint="r"))],                  # the pit's low south lip
    features=[("pool", (33, 20, 10, 4), dict(water=True, shape="round"))],
    stairs="auto",
    ways={"west": ("w", "road"), "tunnel": ("n", 52, dict(cut=3))},
    spawn="west",
    anchors={"chest_11": "bench_2@4", "jar_5": "bench_2@9", "crate_6": "bench_1@12", "ore_1": "bench_1.back@24",
             "ore_3": "wall_foot@17", "ore_4": "wall_foot@44", "ore_2": "road.s@15", "mine_lower_pit_seam": "floor@26",
             "jar_7": "verge.n@22", "crate_8": "verge.s@31", "jar_9": "verge.s@46", "crate_10": "bench_1@49",
             "pit_shard": "floor_s@40", "rift_tear": "floor@35", "spirit_fruit_tree": "floor_s@19"},
    props=[("crates", 6, 13), ("barrel", 8, 13), ("woodpile", 28, 21), ("crates", 47, 12), ("sacks", 49, 12),
           ("post", 50, 3), ("post", 54, 3), ("boulder", 49, 4), ("boulder", 55, 5),   # the old adit's timbers
           ("lantern", 50, 16), ("lantern", 54, 16)],
    flora={"floor_s": dict(density=0.3)},
    # T3 (docs/architecture/topdown_mechanics.md): the side view's cracked slab on the pit's floor, a level over it, the
    # spirit stone shards sealed under it until a Plunge breaks it open.
    traverse=[("crack", "cracked_slab", dict(rect=(40, 13, 4, 2), level=1))],
    pins={"pit_shard": (41, 13)},
    foes="auto")


# The Collapsed Tunnel: an old working off the pit, its adit up from the mouth in the south, the gallery heaped with
# fallen rock, the ledge where the crews left a chest, the cracked wall at the east end with a spirit seam behind it,
# the old marks cut in a boulder, and Lu's journal page among the props.
SQ_COLLAPSED_TUNNEL = room(
    "sq_collapsed_tunnel", size=(40, 24), biome="cave", level=4,
    features=[("front", (0, 13, 40, 11), dict(level=1, paint="r")),          # the low rock of its front: nothing hidden
              ("gallery", (2, 3, 36, 15), dict(level=0, paint="d", shape="round")),
              ("adit", (5, 15, 4, 9), dict(level=0, paint="d", walk=True)),
              ("track", (4, 11, 34, 3), dict(level=0, paint="d", walk=True)),
              ("ledge", (15, 4, 12, 4), dict(level=2, paint="r")),
              ("rubble_w", (5, 5, 7, 5), dict(level=1, paint="r", shape="round")),
              ("rubble_e", (28, 6, 7, 4), dict(level=2, paint="r", shape="round"))],
    stairs="auto",
    ways={"entry": ("s", 6.5, dict(span=2))},
    spawn="entry",
    anchors={"chest_7": "ledge@18", "crate_4": "ledge@22", "jar_3": "ledge@25", "ore_1": "gallery.back@13",
             "ore_2": "gallery.back@27", "jar_5": "track.s@19", "crate_6": "track.s@33",
             "journal_tunnel": "track.n@35", "cracked_wall": (37, 12), "ore_wall_seam": (37, 12),
             "lost_quarry_marks": (28, 15)},
    props=[("lantern", 4, 10), ("lantern", 14, 10), ("lantern", 27, 10), ("crates", 9, 15), ("barrel", 11, 15)],
    flora={"density": 0.22},
    foes="auto")

ROOMS = [SQ_QUARRY_RIM, SQ_LOWER_PIT, SQ_COLLAPSED_TUNNEL]
