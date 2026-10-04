"""E1 room specs (R8): the shapes the sky-sea zones share (the Skyport Wreck, Lanternfall Harbor, the Drifting Shoals,
Blackmast Haven, the Wyrmnest Isles; docs/architecture/room_engine.md). Not a zone: it lists no rooms."""


def hull(name, x, y, length, beam, opts, bow=6, stern=0):
    """A ship's deck seen from above, as features: a rect `length` long and `beam` wide from (x, y), its bow tapering
    east over `bow` columns (two at a time, a row narrower each side at each step, each a rect laid after the last, so
    the hull keeps its middle row) and, with `stern`, its stern rounding west the same way. The first rect is `name`
    (the anchors and its `flights` name it); the bow's and the stern's steps take `name_2`, `name_3`... and no flights.
    A deck reads as a ship where its pointed bow and its south face (the hull's side) show."""
    steps = dict(opts)
    steps.pop("flights", None)
    out = [(name, (x, y, length, beam), dict(opts))]
    for i in range(bow // 2):
        w = beam - 2 * (i + 1)
        if w <= 0:
            break
        out.append((name, (x + length + 2 * i, y + i + 1, 2, w), dict(steps)))
    for i in range(stern // 2):
        w = beam - 2 * (i + 1)
        if w <= 0:
            break
        out.append((name, (x - 2 * (i + 1), y + i + 1, 2, w), dict(steps)))
    return out
