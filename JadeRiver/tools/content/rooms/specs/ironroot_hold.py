"""E1 room specs (R7, Act II's chapter 13): Ironroot Hold, the clan's mountain past the Gale Canyons' Windbridge
(docs/architecture/room_engine.md, "Nine Peaks to the Tomb of Sunscar (R7)"). The Hold Gate's palisade and watch tower
before the mountain's door, the Clan Hearth in the cavern under it (its forge, its anvil, the desert road south), the
Ancestor Hall's iron-root tablets (`iron_hold`: grey rock, the iron-root trees' roots breaking out of it, pines on its
ledges; forges and braziers inside)."""
from content.rooms.spec import room


# The Hold Gate: the clan's mountain stands across the north, and its gatehouse at the foot of the cliff is the door into
# the Clan Hearth. The canyon's trail comes in from the Windbridge in the west through a gap in a line of stakes, past
# the wayside shrine; the trampled yard before the gatehouse where the warden tests newcomers, braziers and the clan's
# banners at its door, a watch tower of timber over the yard, the timber wall along its south side; pines and the
# iron-root trees' roots on the ledges either side.
IR_HOLD_GATE = room(
    "ir_hold_gate", size=(56, 28), biome="iron_hold",
    bands=[("cliff", 0, 7, dict(level=6, paint="r", wall=True, wavy="s")),
           ("trail", 14, 3, dict(paint="d", walk=True, w=26)),
           ("ground", 17, 6, dict(level=0)),
           ("wall", 23, 2, dict(level=2, paint="w", wall=True, x=12, w=40)),
           ("foot", 25, 3, dict(level=0))],
    features=[("ledge_w", (0, 5, 17, 8), dict(level=2, shape="round")),
              ("ledge_e", (41, 5, 15, 8), dict(level=2, shape="round")),
              ("yard", (14, 8, 30, 15), dict(paint="d", shape="round")),
              ("tower", (40, 13, 4, 4), dict(level=2, paint="w", flights=[41]))],
    stairs="auto",
    ways={"west": ("w", "trail"), "east": ("door", "gatehouse", dict(path=(14, "d")))},
    spawn="west",
    anchors={"shrine_ir": "trail.s@6", "npc_ironroot_warden": (24, 17)},
    # The line of stakes the trail comes through, the gatehouse and what stands round its yard.
    props=[("post", 12, y) for y in list(range(9, 14)) + list(range(17, 23))]
          + [("hall", 24, 8, "gatehouse"), ("brazier", 22, 11), ("brazier", 33, 11), ("banner_jade", 21, 9),
             ("banner_jade", 34, 9), ("weapon_rack", 17, 18), ("post", 29, 20), ("post", 33, 19), ("woodpile", 37, 21),
             ("crates", 36, 11), ("barrel", 38, 11)],
    flora={"ledge_w": dict(density=0.5), "ledge_e": dict(density=0.5), "ground": dict(density=0.3),
           "foot": dict(density=0.4), "yard": []},
    foes="auto")


# The Clan Hearth: the great cavern under the mountain where the clan lives round its fire. Flagstones round the hearth
# fire and the Matriarch's seat; the longhouse against the north wall, the clan forge beside it (its door opens on the
# Ancestor Hall in the rock), its anvil and hearths before it where the smith works; the passage from the Hold Gate in
# the west out east to the desert road; iron-root roots breaking out of the cavern's walls, braziers and stores.
IR_CLAN_HEARTH = room(
    "ir_clan_hearth", size=(56, 28), biome="iron_hold", level=4,
    features=[("front", (0, 20, 56, 8), dict(level=1, paint="r")),           # the cavern's low front
              ("cavern", (1, 2, 54, 22), dict(level=0, paint="d", shape="round")),
              ("passage", (0, 12, 56, 3), dict(level=0, paint="d", walk=True)),
              ("hearth", (16, 6, 22, 14), dict(level=0, paint="p", shape="round"))],
    ways={"west": ("w", 13), "desert_road": ("e", 13), "hall_door": ("door", "forge_house", dict(path=(12, "p")))},
    spawn="west",
    anchors={"npc_matriarch_tie": (22, 9), "anvil_ir": (31, 9), "npc_clan_smith_gang": (33, 10)},
    props=[("storehouse", 10, 5), ("house", 34, 3, "forge_house"), ("forge", 29, 6), ("forge", 41, 7),
           ("stove", 25, 16), ("brazier", 22, 16), ("brazier", 29, 16), ("brazier", 18, 11), ("brazier", 36, 11),
           ("weapon_rack", 20, 6), ("mat", 21, 7), ("woodpile", 44, 9), ("crates", 6, 8), ("barrel", 8, 9),
           ("sacks", 14, 7), ("water_jar", 27, 6), ("lantern", 3, 11), ("lantern", 3, 15), ("lantern", 52, 11),
           ("lantern", 52, 15)],
    flora={"cavern": ["roots", "boulder", "rock_small", "roots"], "front": ["roots", "rock_small"], "density": 0.24})


# The Ancestor Hall: a hall of dark timber cut into the rock behind the forge. The rows of iron-root tablets on the
# altar at the back, incense either side; the roots of the clan's first tree breaking through the back wall's corners;
# lanterns and the clan's banners down the walls.
IR_ANCESTOR_HALL = room(
    "ir_ancestor_hall", size=(24, 14), base="w", walls=dict(high=5),
    features=[("dais", (6, 1, 12, 4), dict(level=1, paint="w")),            # the altar's dais
              ("cheek", (10, 5, 1, 2), dict(level=2, paint="w")),           # its steps' cheeks, a level over it
              ("cheek_2", (13, 5, 1, 2), dict(level=2, paint="w"))],
    stairs=[(11, 5, 2, 2, 0, 1, "w")],
    ways={"entry": ("s", 4.5)},
    spawn="entry",
    anchors={"ancestral_tablets": (11.5, 2)},
    props=[("roots", 1, 1), ("roots", 21, 1), ("incense", 8, 2), ("incense", 15, 2), ("lantern", 6, 4),
           ("lantern", 17, 4), ("banner_jade", 4, 1), ("banner_jade", 19, 1), ("brazier", 1, 6), ("brazier", 22, 6),
           ("mat", 10, 8), ("lantern", 2, 12), ("lantern", 7, 12), ("pot_bonsai", 21, 12)])

ROOMS = [IR_HOLD_GATE, IR_CLAN_HEARTH, IR_ANCESTOR_HALL]
