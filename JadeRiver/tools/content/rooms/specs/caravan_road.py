"""E1 room specs: the Caravan Road, west of Stoneford's Fairground (docs/architecture/room_engine.md). Chapter 3's
road: Bandits on the Road, the turn-off north to the Mudwater Hideout, and on west to Deepwater Bend."""
from content.rooms.spec import room

# The Caravan Road: the wide dirt road west from the Fairground through the hills, the hillside under the ridge with
# a rock outcrop where the bandits stacked their crates, the track north through a notch in the ridge to the Mudwater
# Hideout's stockade (a sign at its foot warns travellers off), the broken carts by the road and a creek to the south.
CR_CARAVAN_ROAD = room(
    "cr_caravan_road", size=(72, 30), biome="valley_road",
    bands=[("ridge", 0, 3, dict(level=3, paint="r", wall=True)),
           ("hillside", 3, 6, dict(level=1)),
           ("road", 12, 4, dict(paint="d", walk=True)),
           ("meadow", 16, 8, dict(level=0)),
           ("creek", 25, 5, dict(water=True))],
    features=[("outcrop", (27, 4, 8, 3), dict(level=2, paint="r")),
              ("cart_east", (42, 9, 6, 3), dict(paint="d")),
              ("cart_west", (14, 16, 7, 3), dict(paint="d"))],
    stairs="auto",
    ways={"east": ("e", "road"), "west": ("w", "road"), "hideout": ("n", 56, dict(cut=3))},
    spawn="east",
    anchors={"crate_7": "outcrop@29", "crate_8": "outcrop@32", "herb_1": "hillside@6", "ore_2": "ridge.s1@51",
             "jar_3": "verge.s@8", "crate_4": "cart_east@44", "jar_5": "verge.s@45", "crate_6": "verge.n@64",
             "sign_cr": "road.n@60", "npc_peddler_shao": "cart_west@17"},
    props=[("crates", 15, 17), ("barrel", 19, 18), ("crates", 45, 10), ("barrel", 47, 9)],   # the broken carts' loads
    flora={"hillside": dict(density=0.42)},
    ground={"sand": ["creek.bank"]},
    foes="auto")

ROOMS = [CR_CARAVAN_ROAD]
