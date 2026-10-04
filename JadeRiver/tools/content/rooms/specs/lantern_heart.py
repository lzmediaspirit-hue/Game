"""E1 room specs (R9, Act III's chapter 22): the Lantern Heart, the secret realm above Lanternfall Harbor where the
first lantern still burns, reached by the stair Lu's notes point to (docs/architecture/room_engine.md, "The star field's
end (R9)"). The Wick Gate at the stair's head, the Hall of Burning Stars and the Flame Heart. Halls of warm flagstones
inside walls of golden sandstone (R7's tomb walls, `a`), bronze wick pillars burning down their aisles, great flame
basins, star crystals grown out of the old rock in the corners; at the heart, the first lantern's star in its cage."""
from content.rooms.spec import room

WALLS = dict(high=5, low=1, paint="a")   # golden sandstone, five levels, the front a low sill


def wicks(xs, *rows):
    """Wick pillars down an aisle: one at each column on each row."""
    return [("wick_pillar", x, y) for y in rows for x in xs]


# The Wick Gate: the stair from the Harbor Market comes up through the west wall into the Heart's first court. Its
# processional way runs east between two rows of wick pillars to the gate, a pair of sandstone towers either side of the
# way, flame basins burning before them; a gallery a level up along the north wall where a jar was left, the shrine
# inside the stair's head, star crystals grown in the court's corners.
LT_WICK_GATE = room(
    "lt_wick_gate", size=(56, 24), base="p", biome="lantern_heart", walls=WALLS,
    features=[("way", (1, 11, 54, 3), dict(paint="s", walk=True)),
              ("gallery", (14, 1, 12, 4), dict(level=1, paint="p", flights=[20])),
              ("tower", (38, 6, 4, 4), dict(level=5, paint="a", wall=True)),            # the gate's two towers
              ("tower_2", (38, 15, 4, 4), dict(level=5, paint="a", wall=True)),
              ("bed", (1, 1, 6, 5), dict(paint="r", shape="round")),
              ("bed_2", (48, 18, 7, 5), dict(paint="r", shape="round"))],
    stairs="auto",
    ways={"stair": ("w", 12), "east": ("e", 12)},
    spawn="stair",
    anchors={"shrine_lt_gate": "way.n@8", "jar_1": "gallery@20", "crate_2": "way.s@28", "jar_3": "way.s2@47"},
    props=wicks((12, 18, 24, 30), 9, 15) + [("flame_basin", 35, 9), ("flame_basin", 35, 15), ("flame_basin", 43, 9),
                                            ("flame_basin", 43, 15), ("warden_lamp", 2, 9), ("warden_lamp", 2, 15),
                                            ("flame_basin", 38, 8), ("flame_basin", 38, 17)],          # the towers' beacons
    flora={"bed": ["crystal_cluster"], "bed_2": ["crystal_cluster"], "gallery": [], "density": 0.6},
    foes="auto")


# The Hall of Burning Stars: the Heart's long hall, two colonnades of wick pillars burning down its aisle, flame basins
# on their daises between them; a low gallery along the north wall in the west (a jar) and a high one in the east (the
# hall's chest), the burning-star bell's stand by the east door, star crystals in the corners.
LT_HALL_OF_BURNING_STARS = room(
    "lt_hall_of_burning_stars", size=(72, 24), base="p", biome="lantern_heart", walls=WALLS,
    features=[("aisle", (1, 11, 70, 3), dict(paint="s", walk=True)),
              ("gallery", (14, 1, 10, 4), dict(level=1, paint="p", flights=[19])),
              ("gallery_2", (36, 1, 12, 4), dict(level=2, paint="p", flights=[42])),
              ("dais", (24, 16, 6, 3), dict(level=1, paint="s")),
              ("dais_2", (50, 16, 6, 3), dict(level=1, paint="s")),
              ("bed", (1, 1, 7, 5), dict(paint="r", shape="round")),
              ("bed_2", (63, 18, 8, 5), dict(paint="r", shape="round"))],
    stairs="auto",
    ways={"west": ("w", 12), "east": ("e", 12)},
    spawn="west",
    anchors={"jar_1": "gallery@19", "crate_2": "aisle.s2@34", "chest_4": "gallery_2@42", "lost_burning_star_bell": "aisle.n@53",
             "jar_3": "aisle.s@59"},
    props=wicks(range(8, 68, 8), 9, 15) + [("flame_basin", 26, 16), ("flame_basin", 52, 16), ("flame_basin", 26, 6),
                                          ("flame_basin", 56, 6), ("warden_lamp", 2, 9), ("warden_lamp", 2, 15),
                                          ("warden_lamp", 69, 9), ("warden_lamp", 69, 15)],
    flora={"bed": ["crystal_cluster"], "bed_2": ["crystal_cluster"], "gallery": [], "gallery_2": [], "density": 0.6},
    foes="auto")


# The Flame Heart: the cage of the first lantern. A round chamber under the golden walls, a ring of wick pillars round its
# floor; in its middle, on a round dais a level up, the first lantern's star burns in its bronze cage, a great flame
# basin either side of it and the flame that answers Lu's notes before it; a ledge in the north-west where a chest was
# left, star crystals grown in the chamber's corners.
LT_FLAME_HEART = room(
    "lt_flame_heart", size=(56, 24), base="r", biome="lantern_heart", walls=dict(WALLS, high=6),
    features=[("chamber", (6, 1, 44, 22), dict(paint="p", shape="round")),
              ("dais", (21, 6, 14, 8), dict(level=1, paint="s", shape="round", flights=[28])),
              ("ledge", (1, 1, 9, 5), dict(level=2, paint="p", flights=[5])),
              ("bed", (47, 1, 8, 5), dict(paint="r", shape="round")),
              ("bed_2", (1, 18, 7, 5), dict(paint="r", shape="round")),
              ("bed_3", (48, 18, 7, 5), dict(paint="r", shape="round"))],
    stairs="auto",
    ways={"west": ("w", 12)},
    spawn="west",
    anchors={"heart_flame": (28, 15), "chest_ledge_mv_1": "ledge@6"},
    props=[("lantern_cage", 27, 9), ("flame_basin", 22, 9), ("flame_basin", 32, 9)]
          + [("wick_pillar", x, y) for x, y in ((14, 4), (41, 4), (11, 11), (44, 11), (14, 18), (41, 18), (20, 21), (35, 21))]
          + [("warden_lamp", 2, 9), ("warden_lamp", 2, 15)],
    flora={"bed": ["crystal_cluster"], "bed_2": ["crystal_cluster"], "bed_3": ["crystal_cluster"], "ledge": [], "chamber": [],
           "dais": [], "density": 0.7})

ROOMS = [LT_WICK_GATE, LT_HALL_OF_BURNING_STARS, LT_FLAME_HEART]
