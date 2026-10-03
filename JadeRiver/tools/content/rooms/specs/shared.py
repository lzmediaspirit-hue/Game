"""E1 room specs: the shapes two rooms share, one for each sect (docs/architecture/room_engine.md): the Entry Trial's
walled yard and a sect's Weapon Hall. Each returns a room's spec; the zone's module adds what is its sect's own."""
from content.rooms.spec import room


def trial_yard(rid, banner, features, props, bell):
    """The walled yard of an Entry Trial behind its trial hall on the Fairground: the gateway back in the south wall
    between the sect's banners, stone lanterns round a sand ring where the Trial Puppet steps out once the bell has
    rung. The climb to the bell is each sect's own (`features`, `props`, the `bell`'s cell)."""
    return room(
        rid, size=(40, 24), base="p", walls=dict(high=2, low=1),
        features=[
            ("lawn", (1, 18, 7, 5), dict(level=0, paint="g")),          # lawns in the front corners
            ("lawn_2", (32, 21, 7, 2), dict(level=0, paint="g")),
            ("flowers", (2, 20, 4, 2), dict(level=0, paint="f")),
            ("apron", (21, 11, 16, 10), dict(level=0, paint="s")),      # the granite apron round the ring
            ("ring", (22, 12, 14, 8), dict(level=0, paint="d")),        # the sand ring
            ("walk", (18, 12, 3, 11), dict(level=0, paint="s")),        # the walk from the gateway
        ] + features,
        ways={"entry": ("s", 19.5)},
        spawn=(19.5, 20),
        anchors={"trial_bell": bell},
        foes=[[(29, 16)]],
        pins={"props": [   # hand-placed, piece by piece
            (banner, 17, 21), (banner, 22, 21), ("lantern", 21, 11), ("lantern", 36, 11), ("lantern", 21, 20),
            ("lantern", 36, 20), ("pine", 2, 19), ("pine", 37, 21), ("shrub", 6, 21), ("barrel", 1, 13),
            ("barrel", 1, 14),
            # Foliage (decision 40): bushes on the front lawns, potted plants along the yard's front.
            ("bush_azalea", 4, 18), ("ferns", 1, 21), ("bush", 33, 21), ("pot_bonsai", 14, 22), ("pot_orchid", 26, 22),
        ] + props})


def weapon_hall(rid, banner, master, smith, anvil, dummies):
    """A sect's Weapon Hall and Forge: racks of training weapons along the back wall between the sect's banners, the
    weapon master before them, the sparring ring a level up in the west (boards and a step) with its two dummies, the
    smith and the anvil at the forge in the east, and the door in the front wall back out."""
    return room(
        rid, size=(24, 14), base="s", walls=True,
        features=[("ring", (2, 7, 7, 4), dict(level=1, paint="w"))],   # the sparring ring
        stairs=[(4, 11, 3, 1, 0, 1, "w")],
        ways={"exit": ("s", 11.5)},
        spawn=(11.5, 11),
        anchors={master: (10, 5), smith: (17, 5), anvil: (19, 7), dummies[0]: (4, 8), dummies[1]: (7, 8)},
        pins={"props": [   # hand-placed, piece by piece
            ("weapon_rack", 2, 1), ("weapon_rack", 5, 1), ("weapon_rack", 8, 1), (banner, 12, 1), (banner, 15, 1),
            ("crates", 19, 1), ("barrel", 21, 1), ("barrel", 22, 2), ("lantern", 1, 11), ("lantern", 22, 11),
            ("pot_bonsai", 1, 6), ("pot_orchid", 22, 6), ("pot_bonsai", 17, 1),   # foliage (decision 40): potted plants
        ]})
