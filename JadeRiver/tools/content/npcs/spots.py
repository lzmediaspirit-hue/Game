"""E3, the NPC engine: work spots named by anchors, resolved on a room's layout (docs/architecture/npc_engine.md).

A worker's spots used to be cells written by hand beside the tub, the anvil or the bank they work at. An anchor names
what the spot is beside instead, so a moved building, tub or shore moves its workers with it. topdown_life.py's build
resolves each one on the built layout (data/topdown/<room>.json) as it writes life.json, and its checks hold the
result to the same rules as a hand spot (on the person's floor, within the leash, every leg walked clear):

  "home"            the person's own spot
  "water_edge"      a bank spot beside open water, facing it
  "by:<prop kind>"  beside a prop of that kind (wash_tub, forge, woodpile, net_rack...), facing it
  "near:<oid>"      beside another thing of the room (a shrine, a board, a well), facing it
  "open"            a free spot round the person, as far from the others as the leash allows, facing out

each with, optionally and in this order, "@x" or "@x,y" (the point to look round: the person's own spot by default),
">dir" (the facing kept) and ":steps" (the loop's steps at that spot). "auto:<anchor>" reads as "<anchor>".

A spot is a cell's centre (an integer point) on the person's floor, within the leash less 0.4 of a tile of their own
spot (an extra's first spot is its home and has no leash), at least a tile from it, off every way's lane, a tile clear
of every other thing of the room, never on a stair, a tile from every spot already chosen, and walked to in a straight
line from the spot before it (the last back to the first). Among those that fit its anchor, the nearest to the point it
looks round wins, then a hash of the room and the person: deterministic, the seed is the ids.
"""
import math
import re

FACINGS = ("n", "ne", "e", "se", "s", "sw", "w", "nw")
SPOT = re.compile(r"^(?:auto:)?(home|water_edge|open|by:[a-z0-9_]+|near:[a-z0-9_]+)"
                  r"(?:@(-?\d+(?:\.\d+)?)(?:,(-?\d+(?:\.\d+)?))?)?(?:>(n|ne|e|se|s|sw|w|nw))?(?::([a-z0-9_]+))?$")
MARGIN = 0.4      # how far inside the leash a resolved spot stays (topdown_life.auto_spots keeps the same)
SEARCH = 6        # how far round its point an extra's first spot looks, in cells


class SpotError(ValueError):
    pass


def parse(expr):
    """An anchor's parts: (kind, arg, at (x, y | None) or None, facing or None, steps or None)."""
    m = SPOT.match(expr)
    if not m:
        raise SpotError("work spot %r: an anchor is home, water_edge, open, by:<prop kind> or near:<thing>, then "
                        "@x[,y], >facing, :steps" % expr)
    head, x, y, facing, steps = m.groups()
    kind, _, arg = head.partition(":")
    at = None if x is None else (float(x), None if y is None else float(y))
    return kind, arg, at, facing, steps


def is_anchor(spot):
    return isinstance(spot, str)


def facing_to(dx, dy):
    """The facing nearest a direction (x east, y south)."""
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return "s"
    ang = math.degrees(math.atan2(dy, dx))
    return ("e", "se", "s", "sw", "w", "nw", "n", "ne")[int(((ang + 22.5) % 360) // 45)]


class Room:
    """A room's layout as its workers' spots read it."""

    def __init__(self, rid, d, g):
        import topdown_rooms as TR
        import topdown_life as LIFE
        self.TR, self.LIFE = TR, LIFE
        self.id, self.d, self.g = rid, d, g
        self.lanes = LIFE.blocked_cells(d)

    def cell(self, p):
        return self.TR.cell(p)

    def floor(self, p):
        return self.LIFE.floor_at(self.g, p)

    def water(self, c):
        x, y = c
        return 0 <= x < self.g.w and 0 <= y < self.g.h and self.g.lv[y][x] == self.TR.WATER

    def footprints(self, kind):
        out = []
        for p in self.d["props"]:
            if p["kind"] == kind:
                fw, fh = self.TR.TILESET["props"][kind]["footprint"]
                out.append([(x, y) for y in range(p["y"], p["y"] + fh) for x in range(p["x"], p["x"] + fw)])
        return out


def resolve(room, who, spots, home=None):
    """The spots of one worker (`who`, an object id or an extra's id) in `room` (a Room), anchors resolved: a list of
    [x, y, facing(, steps)]. `home` is the person's own spot; None for an extra, whose first spot is its home."""
    LIFE = room.LIFE
    out = []
    seed = LIFE.seed_of(room.id + who)
    others = [room.cell(at) for k, at in room.d["place"].items() if k != who]
    leash = LIFE.LEASH - MARGIN
    floor = room.floor(home) if home is not None else None
    for i, s in enumerate(spots):
        if not is_anchor(s):
            out.append(list(s))
            if home is None and i == 0:
                home, floor = s, room.floor(s)
            continue
        kind, arg, at, facing, steps = parse(s)
        where = "%s %s: work spot %r" % (room.id, who, s)
        if kind == "home":
            if home is None:
                raise SpotError(where + ": an extra has no home but its first spot")
            spot = [home[0], home[1], facing or "s"]
        else:
            centre = home if at is None else (at[0], at[1] if at[1] is not None else (home[1] if home is not None else None))
            if centre is None:
                raise SpotError(where + ": an extra's first spot names the point it looks round (@x or @x,y)")
            prev = out[-1] if out else home
            last = i == len(spots) - 1 and i > 0
            spot = _best(room, where, kind, arg, centre, home, floor, prev, out, others, leash, seed, last)
            if facing:
                spot[2] = facing
        if steps:
            spot.append(steps)
        if home is None:
            home, floor = spot, room.floor(spot)
        out.append(spot)
    return out


def _candidates(room, centre, home, floor, leash):
    """The integer points a spot may take: round the person's own spot within the leash (or, for an extra's first spot,
    within SEARCH of its point; a column alone searches every row)."""
    g = room.g
    if home is not None:
        hx, hy = int(round(home[0])), int(round(home[1]))
        pts = [(hx + dx, hy + dy) for dy in range(-3, 4) for dx in range(-3, 4)]
        return [p for p in pts if 1.0 <= math.hypot(p[0] - home[0], p[1] - home[1]) <= leash]
    cx = int(round(centre[0]))
    if centre[1] is None:
        return [(x, y) for y in range(g.h) for x in range(max(0, cx - SEARCH), min(g.w, cx + SEARCH + 1))]
    cy = int(round(centre[1]))
    return [(x, y) for y in range(max(0, cy - SEARCH), min(g.h, cy + SEARCH + 1))
            for x in range(max(0, cx - SEARCH), min(g.w, cx + SEARCH + 1))]


def _best(room, where, kind, arg, centre, home, floor, prev, chosen, others, leash, seed, last):
    LIFE, g = room.LIFE, room.g
    from lib.pix import h01
    targets = None
    if kind == "by":
        prints = room.footprints(arg)
        if not prints:
            raise SpotError(where + ": the room has no %s" % arg)
        targets = [c for fp in prints for c in fp]
    elif kind == "near":
        if arg not in room.d["place"]:
            raise SpotError(where + ": the room places no %s" % arg)
        targets = [room.cell(room.d["place"][arg])]
    best, best_key = None, None
    for p in _candidates(room, centre, home, floor, leash):
        c = room.cell(p)
        f = room.floor(p)
        if f is None or (floor is not None and abs(f - floor) > 8.0):
            continue
        if not (0 <= c[0] < g.w and 0 <= c[1] < g.h) or g.stair[c[1]][c[0]] or c in room.lanes:
            continue
        if any(max(abs(c[0] - o[0]), abs(c[1] - o[1])) < 2 for o in others if not (kind == "near" and o == targets[0])):
            continue
        if any(math.hypot(p[0] - q[0], p[1] - q[1]) < 1.0 for q in chosen):
            continue
        if prev is not None and floor is not None and not LIFE.walkable(g, prev, p, floor):
            continue
        if last and not LIFE.walkable(g, p, chosen[0], floor):
            continue
        aim = None
        if kind == "water_edge":
            wet = [(c[0] + dx, c[1] + dy) for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1)) if room.water((c[0] + dx, c[1] + dy))]
            if not wet:
                continue
            aim = (sum(w[0] for w in wet) / len(wet) - c[0], sum(w[1] for w in wet) / len(wet) - c[1])
            rank = 0.0
        elif kind in ("by", "near"):
            d = min(max(abs(c[0] - t[0]), abs(c[1] - t[1])) for t in targets)
            if d < 1 or d > (2 if kind == "near" else 1):
                continue
            t = min(targets, key=lambda q: (math.hypot(q[0] - c[0], q[1] - c[1]), q))
            aim = (t[0] - c[0], t[1] - c[1])
            rank = float(d)
        else:   # open: as far from the person and the spots chosen as the leash allows
            ref = [home] + chosen if home is not None else chosen
            rank = -min([math.hypot(p[0] - q[0], p[1] - q[1]) for q in ref] + [3.0])
            aim = (p[0] - home[0], p[1] - home[1]) if home is not None else (0.0, 1.0)
        dist = abs(p[0] - centre[0]) if centre[1] is None else math.hypot(p[0] - centre[0], p[1] - centre[1])
        key = (rank, round(dist, 6), h01(seed, p[0], p[1]))
        if best_key is None or key < best_key:
            best, best_key = [p[0], p[1], facing_to(*aim)], key
    if best is None:
        raise SpotError(where + ": no spot fits (on the person's floor, within the leash, clear of the lanes and the other "
                        "things, walked to from the spot before it)")
    return best
