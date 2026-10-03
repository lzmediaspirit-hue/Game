"""E1, the room engine: the spec a room is written in (docs/architecture/room_engine.md).

A spec is a Python literal made by `room(id, **keys)`, kept in tools/content/rooms/specs/<zone>.py. It names the room's
shape and where its things go; the engine (engine.py) compiles it to the layout the game reads (data/topdown/<id>.json,
the same `Layout.dict()` tools/data/topdown_rooms.py always wrote). Coordinates are cells, x east and y south; a rect
is (x, y, w, h). Every key but `size` may be left out.

  size      (w, h) in cells
  biome     the flora pools, verges and stair paint a generated room draws from (biomes.py)
  base      the ground under everything: a paint ("g" meadow, "w" planks, "p" paving, "s" granite, "d" path, "m" marsh,
            "r" rock, "~" water) and `level` its height (0)
  walls     an interior: True, or {high, low, paint, rect}: the back and side walls `high` levels up, the front a low
            sill; a way on the sill cuts its doorway
  bands     [(name, y, h, {level, paint, water, walk, wall, x, w})]: strata from the north, the room's width each (or
            from `x`, `w` wide); `walk` marks the main walk (a road), `wall` a cliff no one climbs; laid in order
  features  [(name, (x, y, w, h), {level, paint, water, rise})]: raised, sunk or painted shapes laid over the bands in
            order; `rise: (from, to)` makes it a flight of stairs rising north
  stairs    [(x, y, w, h, from, to[, paint])] laid after the features, and/or "auto": a flight wherever a walk crosses a
            level edge, and up onto every raised shape something stands on
  ways      {portal id: way}, in the order the layout lists them:
              ("e", row) ("w", row) ("n", col) ("s", col)   an edge way (or an interior's doorway in its sill); a band's
                                                            name for row or col takes its middle; {span, arrive, cut}
              ("door", prop name)                           the doorway of a building prop; {path: row | (row, paint) |
                                                            "auto", arrive}: a path from the door down to a lane
              {at, dir, arrive, span}                        a way anywhere (a gangway onto a boat)
  paths     [(prop name, row[, paint])]: a path two cells wide from a building's door down to a lane at `row` ("auto":
            the first walk band below it); a door way may carry its own ({path: ...})
  props     [(kind, x, y[, name]) | {kind, along, every, row}]: pieces placed as written (named ones a door can open
            into), or a row of one kind along a band
  flora     {band: [kinds] | {kinds, density}, "density": d}: the foliage along each band's edges (the biome's pool
            for its role where the spec names none), seeded by the room's id (a Poisson disc), clear of every anchor,
            way, lane, walk and foe; trees to a band's back, bushes on its lip, none on a road's shoulder
  ground    {"sand" | "snow" | "snowpack": [rect | band name]}: decision 44's sand and snow, laid after the flora
  spawn     (x, y) or a way's id: where a new character wakes (default: the first way's arrival)
  anchors   {object id: (x, y) | "anchor"}: every NPC and object of the side-view room; an anchor resolves to a cell:
              "road@34"   a band at a column (its middle row)       "road.n@60" "road.s"   the row north or south of it
              "den.back"  a band's or a feature's own first row     "den.front"            its last row (n2, s2: two off)
              "knoll"     a feature's top, its middle cell          "verge" "verge.s@40"   beside the walk band
              "bank"      the land along the water                  "water"                the water (a fishing spot)
              "door:hut"  in front of a building's door             "near:herb_1"          a few cells from another
              "auto"      anywhere reached; each kind ranked by reach from every way and by distance from the others
  foes      "auto", or one entry per side-view spawn: its cells, "auto" (its points on the verges, or the open ground,
            each at the column its side-view point stands at), or "auto:<anchor>" (on the cells an anchor names: a
            tower's top); clear of shrines, ways and lanes
  event     {wave, fixed, waves, timed}: a room event's cells;  routes {object id: [[x, y, s], ...]}: a rooftop run
  areas     [{kind, rect, ...}]: a hazard's areas in cells (the poison mist's pools)
  pins      the hand's last word, never the JSON's: {object id: (x, y)}, "spawn", "stairs", "foes", "props" (the whole
            ordered list, hand-placed), "flora" (the scatter, hand-placed), "add": [(kind, x, y)] more pieces, "drop":
            [(x, y)] scattered pieces taken out where they cover the cell
"""

KEYS = ("size", "biome", "base", "level", "walls", "bands", "features", "stairs", "ways", "paths", "props", "flora", "ground",
        "spawn", "anchors", "foes", "event", "routes", "areas", "pins")
PIN_KEYS = ("spawn", "stairs", "foes", "props", "flora", "add", "drop")


def room(rid, **kw):
    """A room's spec: its id and the keys above (anything else is a typo)."""
    unknown = sorted(set(kw) - set(KEYS))
    if unknown:
        raise ValueError("room %s: unknown key%s %s (the spec's keys: %s)" % (rid, "s" if len(unknown) > 1 else "",
                                                                             ", ".join(unknown), ", ".join(KEYS)))
    if "size" not in kw:
        raise ValueError("room %s: no size" % rid)
    stray = sorted(k for k in kw.get("pins", {}) if k not in PIN_KEYS and k not in kw.get("anchors", {}))
    if stray:
        raise ValueError("room %s: pins %s are neither %s nor an anchor's id" % (rid, ", ".join(stray), ", ".join(PIN_KEYS)))
    out = {"id": rid}
    out.update(kw)
    return out


def variant(spec, rid, **kw):
    """Another room drawn from `spec` (the village at night from the village): its keys, these replaced."""
    out = dict(spec)
    out.update(kw)
    out["id"] = rid
    return room(rid, **{k: v for k, v in out.items() if k != "id"})
