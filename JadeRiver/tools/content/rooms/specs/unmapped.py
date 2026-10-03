"""E1 room specs (R4, the peaks): the rooms on no map (docs/architecture/room_engine.md). The Hidden Grotto, a fortune's
fall from behind Crane Falls: one way out, a rope up the cleft it was found by."""
from content.rooms.spec import room

# The Hidden Grotto: a round cave under the falls, its floor of slate round a still spring pool, a rock ledge at its
# east end where the chest waits, an earlier finder's bones and the moon-carved scholar's rock; the cleft in the west
# wall with the rope back up.
HG_HIDDEN_GROTTO = room(
    "hg_hidden_grotto", size=(40, 24), biome="cave", level=4,
    features=[("grotto", (2, 3, 36, 19), dict(level=0, paint="d", shape="round")),
              ("cleft", (2, 6, 6, 8), dict(level=0, paint="d")),
              ("ledge", (26, 5, 10, 6), dict(level=1, paint="r", shape="round")),
              ("pool", (8, 13, 13, 7), dict(water=True, shape="round"))],
    stairs="auto",
    ways={"way_up": dict(at=(4, 6), dir="n", arrive=(4, 8), span=2)},
    spawn="way_up",
    anchors={"grotto_chest": "ledge.top", "grotto_bones": "grotto@21", "lost_grotto_moon": "grotto@14"},
    flora={"pool": ["cattails", "ferns"], "density": 0.3},
    foes="auto")

ROOMS = [HG_HIDDEN_GROTTO]
