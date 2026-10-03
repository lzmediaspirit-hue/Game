"""E1 room specs (R9): a vessel's deck on the Starsea, the crossing's own room while a voyage is under way
(docs/architecture/room_engine.md, "The star field's end (R9)"). The Wreck Run's crossing from Cloudgate's Shipwrights'
Yard to the Skyport Wreck; the Lantern Run's is the same kind of deck (`lantern_crossing.py`). A skiff's hull of planks
on the sea, its bulwark a level up all round it (the rail's face shows inboard on the north side and outboard over the
sea on the south), the bow tapering to its point in the east and the stern's corners cut, the quarterdeck raised a
level at the stern with the deckhouse on it, two masts down the middle; the sea all round it (the vista's water). The
crossing has no way in or out: the voyage sets the body down on the deck and takes it off at the far pier, and its
waves board over the bow, where the side view's foes come from."""
from content.rooms.spec import room

W, H = 64, 24          # the room
X0, BOW, X1 = 5, 52, 58  # the stern's column, where the bow begins to taper, past its point
TOP, BOT = 5, 18       # the waist's first and last rows (its rails)


def hull_rows(x):
    """The hull's first and last row in column x: the waist's full beam, the stern's corners cut a row, the bow
    narrowing a row each side every column until its point is two rows wide."""
    if x <= X0:
        return TOP + 1, BOT - 1
    if x < BOW:
        return TOP, BOT
    k = x - BOW + 1
    mid = (TOP + BOT) // 2
    return min(mid, TOP + k), max(mid + 1, BOT - k)


def hull():
    """The hull as features, column by column: its planks at level 0 and the bulwark, a level up, on its edge."""
    out = []
    for x in range(X0, X1):
        t, b = hull_rows(x)
        out.append(("hull", (x, t, 1, b - t + 1), dict(level=0, paint="w")))
    for x in range(X0, X1):
        t, b = hull_rows(x)
        pt, pb = hull_rows(x - 1) if x > X0 else (t, b)
        nt, nb = hull_rows(x + 1) if x < X1 - 1 else (t, b)
        # the rail along the edge: a cell on each side, and down the bow's diagonal the cells its step leaves open
        north = range(t, max(t, nt) + 1) if x >= BOW else [t]
        south = range(min(b, nb), b + 1) if x >= BOW else [b]
        for y in sorted(set(north) | set(south)):
            out.append(("bulwark", (x, y, 1, 1), dict(level=1, paint="w")))
        if x == X0 or x == X1 - 1:
            out.append(("bulwark", (x, t, 1, b - t + 1), dict(level=1, paint="w")))
    return out


def deck(rid, props, waves, spawn=(22, 12)):
    """A skiff's deck on the Starsea (above): `props` dress it; `waves` are the crossing event's cells, wave by wave.
    The quarterdeck (level 1) fills the stern's north half, its own rail a level up, a flight up its south face (its
    cheeks closed by barrels)."""
    return room(
        rid, size=(W, H), biome="starsea",
        features=hull() + [("quarterdeck", (X0, TOP, 11, 7), dict(level=1, paint="w", flights=[11])),
                           ("rail", (X0, TOP, 11, 1), dict(level=2, paint="w")),
                           ("rail_2", (X0, TOP, 1, 7), dict(level=2, paint="w"))],
        stairs="auto",
        spawn=spawn,
        props=props,
        event={"waves": waves})


# The Wreck Run's skiff, weathered by the Starsea's wind: the mainmast and the foremast with their sails furled, cargo
# lashed down the waist (crates, barrels, sacks), lanterns at the quarterdeck's rail and the bow. The pirates come over
# the bow; the wind kites ride the wind down onto the forward waist.
SS_STARSEA_CROSSING = deck(
    "ss_starsea_crossing",
    props=[("storehouse", 7, 6), ("mast", 27, 11), ("mast", 43, 11), ("star_lantern", 14, 6), ("star_lantern", 6, 16),
           ("star_lantern", 53, 7), ("star_lantern", 53, 16), ("crates", 18, 6), ("barrel", 20, 6), ("crates", 33, 16),
           ("barrel", 35, 16), ("sacks", 22, 16), ("barrel", 23, 16), ("crates", 46, 6), ("sacks", 48, 6)],
    waves=[[(54, 11), (53, 13)],                                       # the starsea pirates, over the bow
           [(47, 9), (49, 14)]])                                      # the wind kites, onto the forward waist

ROOMS = [SS_STARSEA_CROSSING]
