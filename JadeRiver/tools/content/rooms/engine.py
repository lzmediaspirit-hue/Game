"""E1, the room engine (docs/architecture/room_engine.md; audit 45 §6.1): a room's spec (spec.py) compiled to the
layout the game reads, the `Layout` of tools/data/topdown_rooms.py, which writes it to data/topdown/<id>.json and checks
it as it always did. No game code reads anything new.

The steps, in order (each one's rules are its function's):
  1. lay the ground: the base, an interior's walls and doorways, the bands, the features, the stairs written out
  2. place the props written out (and the pinned list, hand-placed)
  3. the ways: door paths, cuts through the bands for a way at the north or south edge
  4. resolve the anchors to cells, ranked by reach from every way and by distance from the others
  5. stairs "auto": a flight wherever a walk crosses a level edge, and up onto a raised shape something stands on
  6. the foes' spawns on the verges, clear of shrines, ways and lanes
  7. the props a rule lays (a row along a band), then the flora: a seeded Poisson disc along each band's edges, clear
     of every anchor, way, lane, walk and foe
  8. the sand and the snow; the spawn, the places, the ways, the spawns, the event, the routes and the areas
LIFE.dress and LIFE.extend and the checks follow in topdown_rooms.build. Deterministic: the seed is the room's id, and
every choice is a hash of it and a cell (lib.pix.h01), never Python's random.
"""
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (TOOLS, os.path.join(TOOLS, "data")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import topdown_rooms as TR  # noqa: E402  the Layout DSL, the Grid and its rules
from lib.pix import h01  # noqa: E402  the one coordinate hash (audit 45, DUP-03)
from content.rooms import biomes as BIOMES  # noqa: E402

DIRS = TR.DIRS
WATER = TR.WATER
# The trees of the foliage kit (TopdownRoom's tile set): a canopy that may hide what stands north of it.
TREES = sorted(k for k, v in TR.TILESET["props"].items() if v.get("canopy"))
# How far apart two scattered pieces of a class stand at least (cells; two of different classes, 0.6 of it).
SPACING = {"tree": 5, "solid": 3, "soft": 2, "water": 3}
# The objects a side-view room has, by type: where an anchor of that type goes when the spec says "auto".
AUTO_BY_TYPE = {"herb_patch": "verge", "ore_vein": "wall_foot", "jar": "verge", "crate": "verge", "chest": "verge",
                "fishing_spot": "water", "signpost": "walk.n", "npc": "verge", "shrine": "verge", "pickup": "verge",
                "inspect": "verge", "wine_jar": "verge"}
SHRINE_TYPES = ("shrine", "teleport_stone", "transfer_array", "qi_spring")


class SpecError(Exception):
    pass


def seed_of(rid):
    """The room's seed: its id."""
    return zlib.crc32(rid.encode("utf-8")) & 0x7FFFFFFF


class Region:
    """A band or a feature as the anchors and the flora read it: its rect, level, paint and role."""

    def __init__(self, name, x, y, w, h, opts, kind):
        self.name, self.x, self.y, self.w, self.h = name, x, y, w, h
        self.opts = opts
        self.kind = kind          # band | feature
        self.water = bool(opts.get("water"))
        self.walk = bool(opts.get("walk")) or (kind == "band" and name in ("road", "path", "street", "lane"))
        self.wall = bool(opts.get("wall"))
        self.level = WATER if self.water else opts.get("level")
        self.shape = None         # a round shape's cells (None: the whole rect)

    @property
    def x1(self):
        return self.x + self.w

    @property
    def y1(self):
        return self.y + self.h

    def mid_row(self):
        return self.y + self.h // 2

    def cells(self):
        if self.shape is not None:
            return list(self.shape)
        return [(x, y) for y in range(self.y, self.y1) for x in range(self.x, self.x1)]

    def bottom(self, x):
        """The last row the shape covers in column x (None where it covers none)."""
        ys = [c[1] for c in self.cells() if c[0] == x]
        return max(ys) if ys else None

    def top(self, x):
        """The first row the shape covers in column x (None where it covers none)."""
        ys = [c[1] for c in self.cells() if c[0] == x]
        return min(ys) if ys else None

    def beside(self, k):
        """The cells k rows outside its edges, column by column (k = 1: the row along it), north then south."""
        out = []
        for x in range(self.x, self.x1):
            t, b = self.top(x), self.bottom(x)
            if t is not None:
                out += [(x, t - k), (x, b + k)]
        return out

    def role(self):
        return "water" if self.water else "walk" if self.walk else "wall" if self.wall else "ground"


class Build:
    """One room's compile: the spec in, the Layout out (`run`)."""

    def __init__(self, spec, side=None):
        self.spec = spec
        self.id = spec["id"]
        self.seed = seed_of(self.id)
        self.w, self.h = spec["size"]
        self.pins = dict(spec.get("pins", {}))
        self.biome = BIOMES.get(spec.get("biome", ""))
        base = spec.get("base", self.biome["base"])
        self.lay = TR.Layout(self.id, self.w, self.h, WATER if base == "~" else spec.get("level", 0), base)
        self.base = base
        self.regions = {}
        self.named = {}
        self.interior = None
        self.ways = {}            # portal id -> the way's dict, before it is set on the layout (lanes for the anchors)
        self.cells = {}           # anchor id -> resolved cell
        self.stair_paint = self.biome["stair"]
        self.cuts = []            # the paths cut to a north or south way: (dir, x0, width, walk band)
        self.climbed = set()      # the regions a flight climbs onto
        self.notes = []           # what the engine decided, for --show
        self.side = side if side is not None else (TR.side(self.id) if os.path.exists(os.path.join(TR.ROOMS, self.id + ".json")) else {})

    # ================================================================ 1. the ground
    def walls(self):
        w = self.spec.get("walls")
        if not w:
            return
        w = {} if w is True else dict(w)
        x, y, ww, hh = w.get("rect", (0, 0, self.w, self.h))
        self.lay.walls(x, y, ww, hh, w.get("high", 3), w.get("low", 1), w.get("paint", "l"))
        self.interior = (x, y, ww, hh)
        # Each way on a wall: its doorway, two cells wide, cut down to the floor (as the hand cut each one).
        for pid, way in self.spec.get("ways", {}).items():
            if isinstance(way, tuple) and way[0] in DIRS:
                d, pos = way[0], self._pos(way[0], way[1])
                lv = 0 if self.base != "~" else WATER
                if d in "ns":
                    row = y if d == "n" else y + hh - 1
                    self.lay.rect(int(pos - 0.5), row, 2, 1, lv, self.base)
                else:
                    col = x if d == "w" else x + ww - 1
                    self.lay.rect(col, int(pos - 0.5), 1, 2, lv, self.base)

    def bands(self):
        for name, y, h, opts in self.spec.get("bands", []):
            x = opts.get("x", 0)
            w = opts.get("w", self.w - x)
            self._lay(name, x, y, w, h, opts, "band")

    def features(self):
        for name, (x, y, w, h), opts in self.spec.get("features", []):
            if "rise" in opts:
                frm, to = opts["rise"]
                self.lay.stair(x, y, w, h, frm, to, opts.get("paint", self.stair_paint))
                continue
            self._lay(name, x, y, w, h, opts, "feature")

    def _lay(self, name, x, y, w, h, opts, kind):
        shape = None
        if opts.get("wavy"):
            shape = self._wavy(x, y, w, h, len(self.regions))
        if opts.get("shape") == "round":
            shape = self._round(x, y, w, h, len(self.regions))
        if shape is not None:
            for cx, cy in shape:
                if opts.get("water"):
                    self.lay.water(cx, cy, 1, 1)
                else:
                    self.lay.rect(cx, cy, 1, 1, opts.get("level"), opts.get("paint"))
        elif opts.get("water"):
            self.lay.water(x, y, w, h)
        else:
            self.lay.rect(x, y, w, h, opts.get("level"), opts.get("paint"))
        if name in self.regions:
            k = 2
            while "%s_%d" % (name, k) in self.regions:
                k += 1
            name = "%s_%d" % (name, k)
        if opts.get("water") and opts.get("rapids"):
            self._rapids(shape or [(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)], opts["rapids"],
                         len(self.regions))
        r = Region(name, x, y, w, h, opts, kind)
        r.shape = shape
        if r.level is None:
            c = (shape or [(min(self.w - 1, x + w // 2), min(self.h - 1, y + h // 2))])[len(shape or [0]) // 2]
            r.level = self.lay.lv[c[1]][c[0]]
        self.regions[name] = r

    def _wavy(self, x, y, w, h, salt):
        """A band whose edges wander (`wavy`): each edge inside the room moves a row in or out along its length, by a
        smooth noise of the room's seed (a value every five columns, eased between), so a shore or a terrace's lip is
        never a ruled line."""
        def wander(xx, k):
            i, f = divmod(xx / 5.0, 1.0)
            a = h01(int(i), k, self.seed + 17 * salt)
            b = h01(int(i) + 1, k, self.seed + 17 * salt)
            v = a + (b - a) * (f * f * (3 - 2 * f))
            return -1 if v < 0.33 else (1 if v > 0.67 else 0)
        out = []
        for xx in range(x, x + w):
            top = y + (wander(xx, 1) if y > 0 else 0)
            bot = y + h - 1 + (wander(xx, 2) if y + h < self.h else 0)
            out += [(xx, yy) for yy in range(max(0, top), min(self.h, bot + 1))]
        return sorted(out, key=lambda c: (c[1], c[0]))

    def _round(self, x, y, w, h, salt):
        """A round shape in its rect (a cavern, a pond): the ellipse the rect holds, its edge worn by the room's seed so
        no two are alike, then smoothed three times (a cell is in where five of the nine round it are), so no lone spur
        or pit is left."""
        cx, cy = x + w / 2.0, y + h / 2.0
        rx, ry = w / 2.0, h / 2.0
        cells = [(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w) if 0 <= xx < self.w and 0 <= yy < self.h]
        shape = set()
        for xx, yy in cells:
            d = ((xx + 0.5 - cx) / rx) ** 2 + ((yy + 0.5 - cy) / ry) ** 2
            wear = (h01(xx // 2, yy // 2, self.seed + 31 * salt) - 0.5) * 0.45
            if d <= 1.0 + wear:
                shape.add((xx, yy))
        for _ in range(3):
            shape = {c for c in cells if sum((c[0] + dx, c[1] + dy) in shape for dx in (-1, 0, 1) for dy in (-1, 0, 1)) >= 5}
        return sorted(shape, key=lambda c: (c[1], c[0]))

    def _rapids(self, cells, dens, salt):
        """R2: a water band's rapids (`rapids`: the share of its cells that break the stream): rocks of a cell or two,
        each standing in open water (two cells of water all round, so none joins the bank), three cells apart at least,
        picked in the order of a hash of the room's seed and the cell; a boulder sits on each cell of it, the water's
        shore foam round it makes the river white. Nothing stands on them: the rocks are no floor anyone reaches."""
        water = {c for c in cells if 0 <= c[0] < self.w and 0 <= c[1] < self.h and self.lay.lv[c[1]][c[0]] == WATER}
        want = int(round(len(water) * dens))
        rocks = []
        for c in sorted(water, key=lambda c: h01(c[0], c[1], self.seed + 23 * salt)):
            if len(rocks) >= want:
                break
            if any(max(abs(c[0] - q[0]), abs(c[1] - q[1])) < 3 for q in rocks):
                continue
            two = h01(c[0], c[1], self.seed + 29 * salt) < 0.45
            body = [c, (c[0] + 1, c[1])] if two else [c]
            if all(q in water for b in body for q in [b] + _ring(b[0], b[1], 2, self.w, self.h)) and \
                    all(0 < q[0] < self.w - 1 for q in body):
                rocks.append(c)
                for b in body:
                    self.lay.rect(b[0], b[1], 1, 1, 0, "r")
                    self.lay.prop("boulder", b[0], b[1])
        self.notes.append("rapids: %d rocks" % len(rocks))

    def rubble(self):
        """A cave's walls stand in their own rubble (a biome's `rubble`): every floor cell of earth by a wall two levels
        or more above it is rock, where the cave's ferns and rocks grow; the walks keep their earth."""
        if not self.biome.get("rubble"):
            return
        walk = {c for r in self.regions.values() if r.walk for c in r.cells()}
        lv = self.lay.lv
        hits = []
        for yy in range(self.h):
            for xx in range(self.w):
                if self.lay.pt[yy][xx] != "d" or lv[yy][xx] == WATER or (xx, yy) in walk:
                    continue
                if any(lv[q[1]][q[0]] != WATER and lv[q[1]][q[0]] >= lv[yy][xx] + 2 for q in _ring(xx, yy, 1, self.w, self.h)):
                    hits.append((xx, yy))
        for xx, yy in hits:
            self.lay.pt[yy][xx] = "r"

    def stairs(self):
        st = self.pins.get("stairs", self.spec.get("stairs", []))
        if st == "auto":
            return
        for s in st:
            if s == "auto":
                continue
            x, y, w, h, frm, to = s[:6]
            self.lay.stair(x, y, w, h, frm, to, s[6] if len(s) > 6 else self.stair_paint)

    def auto_stairs_wanted(self):
        st = self.spec.get("stairs", [])
        return "stairs" not in self.pins and (st == "auto" or (isinstance(st, list) and "auto" in st))

    # ================================================================ 2. the props written out
    def place_props(self):
        items = self.pins.get("props")
        if items is None:
            items = [p for p in self.spec.get("props", []) if isinstance(p, tuple)]
        for p in items:
            self._prop(*p)

    def _prop(self, kind, x, y, name=None):
        fw = TR.TILESET["props"][kind]["footprint"][0]
        if x + fw > self.w:
            return None           # a piece past the room's east edge is left out (a narrower variant of a room)
        i = self.lay.prop(kind, x, y)
        if name:
            self.named[name] = i
        return i

    # ================================================================ 3. the ways
    def _pos(self, d, pos):
        """A way's row (east, west) or column (north, south): a number, or a band's name for its middle."""
        if isinstance(pos, str):
            r = self.regions.get(pos)
            if r is None:
                raise SpecError("%s: a way names no band %r" % (self.id, pos))
            return r.mid_row() if d in "ew" else r.x + r.w // 2
        return pos

    def way_defs(self):
        """Every way's {at, dir, arrive, span}, in the spec's order, and the paths and cuts they make."""
        for path in self.spec.get("paths", []):
            if path[0] not in self.named:
                raise SpecError("%s: a path leads from no prop named %r" % (self.id, path[0]))
            self._door_path(self.named[path[0]], path[1] if len(path) == 2 or path[1] == "auto" else (path[1], path[2]))
        for pid, way in self.spec.get("ways", {}).items():
            if isinstance(way, dict):
                p = {"at": list(way["at"]), "dir": way["dir"]}
                if "arrive" in way:
                    p["arrive"] = list(way["arrive"])
                if "span" in way:
                    p["span"] = way["span"]
                self.ways[pid] = ("free", p, None)
            elif way[0] == "door":
                opts = way[2] if len(way) > 2 else {}
                if way[1] not in self.named:
                    raise SpecError("%s: way %s opens into no prop named %r" % (self.id, pid, way[1]))
                path = opts.get("path")
                if path is not None:
                    self._door_path(self.named[way[1]], path)
                self.ways[pid] = ("door", self.named[way[1]], opts.get("arrive", 1.5))
            elif way[0] in DIRS:
                opts = way[2] if len(way) > 2 else {}
                d = way[0]
                pos = self._pos(d, way[1])
                inner = self.interior is not None
                n = opts.get("arrive", 1.5 if inner else 2)
                span = opts.get("span", 2 if inner else 3)
                if d == "e":
                    at, arr = [self.w - 1, pos], [self.w - 1 - n, pos]
                elif d == "w":
                    at, arr = [0, pos], [n, pos]
                elif d == "n":
                    at, arr = [pos, 0], [pos, n]
                else:
                    at, arr = [pos, self.h - 1], [pos, self.h - 1 - n]
                if opts.get("cut"):
                    self._cut(d, pos, opts["cut"])
                self.ways[pid] = ("edge", {"at": at, "dir": d, "arrive": arr, "span": span}, None)
            else:
                raise SpecError("%s: way %s: %r is no way" % (self.id, pid, way))

    def _door_path(self, idx, path):
        if path == "auto":
            row = self._walk_row_below(idx)
            paint = "d"
        elif isinstance(path, tuple):
            row, paint = path
        else:
            row, paint = path, "d"
        self.lay.door_path(idx, row, paint)

    def _walk_row_below(self, idx):
        p = self.lay.props[idx]
        fh = TR.TILESET["props"][p["kind"]]["footprint"][1]
        y0 = p["y"] + fh
        walks = sorted(r.y for r in self.regions.values() if r.walk and r.y >= y0)
        if not walks:
            raise SpecError("%s: a door path \"auto\" from %s finds no walk band below it" % (self.id, p["kind"]))
        return walks[0]

    def _cut(self, d, pos, cut):
        """A way at the north or south edge: a path `width` wide from the nearest walk band out to the edge. It keeps the
        level of each band it crosses, a wall cut down to the level before it (a gorge); where it climbs a level edge,
        stairs "auto" lay a flight under it (`self.cuts`)."""
        width, paint = (cut, "d") if isinstance(cut, int) else cut
        walks = [r for r in self.regions.values() if r.walk]
        if not walks:
            raise SpecError("%s: a cut needs a walk band" % self.id)
        x0 = int(pos) - width // 2
        if d == "n":
            walk = min(walks, key=lambda r: r.y)
            rows = range(walk.y - 1, -1, -1)
        else:
            walk = max(walks, key=lambda r: r.y1)
            rows = range(walk.y1, self.h)
        cur = walk.level
        for y in rows:
            hit = [r for r in self.regions.values() if r.x <= x0 < r.x1 and r.y <= y < r.y1 and not r.walk]
            wall = any(r.wall for r in hit)
            for x in range(x0, x0 + width):
                if self.lay.lv[y][x] == WATER:
                    continue
                if wall:
                    self.lay.lv[y][x] = cur
                self.lay.pt[y][x] = paint
            if not wall and self.lay.lv[y][x0] != WATER:
                cur = self.lay.lv[y][x0]
        self.cuts.append((d, x0, width, walk))

    def set_ways(self):
        for pid, (kind, a, b) in self.ways.items():
            if kind == "door":
                self.lay.door(pid, a, b)
            else:
                p = a
                self.lay.way(pid, p["at"][0], p["at"][1], p["dir"], p.get("arrive"), p.get("span"))

    def lanes(self):
        out = set()
        for kind, a, b in self.ways.values():
            p = self._door_way(a, b) if kind == "door" else a
            out.update(TR.portal_lane(p))
        return out

    def _door_way(self, idx, rows):
        p = self.lay.props[idx]
        c0, c1 = TR.DOORS[p["kind"]]
        fp = TR.TILESET["props"][p["kind"]]["footprint"]
        x = p["x"] + (c0 + c1) / 2.0
        y = p["y"] + fp[1]
        return {"at": [x, y], "dir": "n", "arrive": [x, y + rows - 1.0], "span": 2}

    def starts(self):
        out = []
        for kind, a, b in self.ways.values():
            p = self._door_way(a, b) if kind == "door" else a
            out.append(TR.cell(TR.arrive(p)))
        return out

    # ================================================================ the grid as it stands
    def snapshot(self):
        lv = ["".join("~" if v == WATER else str(v) for v in r) for r in self.lay.lv]
        return {"size": [self.w, self.h], "levels": lv, "paint": ["".join(r) for r in self.lay.pt],
                "stairs": self.lay.stairs, "props": self.lay.props}

    def grid(self):
        return TR.Grid(self.snapshot())

    def reached(self, g=None, gaps=False):
        """The cells every start reaches by what auto-path walks (the strictest of the checks' rules)."""
        g = g or self.grid()
        out = None
        for st in self.starts():
            if g.floor(*st) is None:
                continue
            r = g.reach(st, gaps)
            out = r if out is None else out & r
        return out or set()

    # ================================================================ 4. the anchors
    def anchors(self):
        side = {o["id"]: o for o in self.side.get("objects", [])}
        spec = self.spec.get("anchors", {})
        g = self.grid()
        reach = self.reached(g)
        if self.auto_stairs_wanted():
            # A raised shape gets its flight once something stands on it (auto_stairs, after this): its cells count as
            # reached here, and the checks hold the room to it once the flights are laid.
            for r in self.regions.values():
                if not (r.wall or r.water or r.walk) and (r.level or 0) > 0:
                    # Only its cells still at its level (R2: a cliff laid over a terrace's edge is no part of it).
                    reach = reach | {c for c in r.cells() if g.floor(*c) is not None and self.lay.lv[c[1]][c[0]] == r.level}
        lanes = self.lanes()
        taken = self._prop_cells()
        # The cells written out first (and the pinned ones), then each anchor in the spec's order.
        for oid, a in spec.items():
            pin = self.pins.get(oid)
            if pin is not None:
                self.cells[oid] = tuple(pin)
            elif isinstance(a, tuple):
                self.cells[oid] = a
        for oid, a in spec.items():
            if oid in self.cells:
                continue
            if a == "auto":
                a = AUTO_BY_TYPE.get(side.get(oid, {}).get("type", ""), "auto")
            self.cells[oid] = self._resolve(oid, a, side.get(oid, {}), g, reach, lanes, taken)
        missing = [o for o in side if o not in self.cells and o not in spec]
        if missing:
            raise SpecError("%s: the side-view room's %s %s no anchor (tools/content/rooms/build.py --new %s lists "
                            "every id)" % (self.id, ", ".join(missing), "has" if len(missing) == 1 else "have", self.id))

    def _prop_cells(self):
        out = set()
        for p in self.lay.props:
            fw, fh = TR.TILESET["props"][p["kind"]]["footprint"]
            out.update((x, y) for y in range(p["y"], p["y"] + fh) for x in range(p["x"], p["x"] + fw))
        return out

    def candidates(self, expr):
        """The cells an anchor expression names, and the column it prefers (None: anywhere)."""
        col = None
        primary = set()           # the cells the expression names first (a band's middle row): the rest fall back
        if "@" in expr:
            expr, c = expr.split("@", 1)
            col = float(c)
        side, off = None, 0
        head, _, tail = expr.partition(".")
        if tail in ("top", "back", "front"):
            side = tail
        elif tail:
            side, off = tail[0], tail[1:]
            if side not in "ns" or not (off == "" or off.isdigit()):
                raise SpecError("%s: anchor %r: after the dot n or s (n2, s2: two rows off), back, front or top" % (self.id, expr))
            off = int(off or 1)
        cells = []
        W, H = self.w, self.h
        if head == "auto":
            cells = [(x, y) for y in range(H) for x in range(W)]
        elif head in ("verge", "walk"):
            walks = [r for r in self.regions.values() if r.walk]
            if not walks:
                raise SpecError("%s: anchor %r: no walk band" % (self.id, expr))
            for r in walks:
                if head == "walk" and not side:
                    cells += r.cells()
                    continue
                rows = []
                if side in (None, "n"):
                    rows += list(range(r.y - (off if side else 3), r.y)) if side is None else [r.y - off]
                if side in (None, "s"):
                    rows += list(range(r.y1, r.y1 + 3)) if side is None else [r.y1 + off - 1]
                cells += [(x, y) for y in rows for x in range(r.x, r.x1) if 0 <= y < H]
        elif head == "bank":
            cells = [(x, y) for y in range(H) for x in range(W)
                     if self.lay.lv[y][x] != WATER and any(self.lay.lv[yy][xx] == WATER for xx, yy in _ring(x, y, 1, W, H))]
        elif head == "water":
            cells = [(x, y) for y in range(H) for x in range(W)
                     if self.lay.lv[y][x] == WATER and any(self.lay.lv[yy][xx] != WATER for xx, yy in _ring(x, y, 2, W, H))]
        elif head == "wall_foot":
            walls = [r for r in self.regions.values() if r.wall]
            cells = [(x, r.y1 + k) for r in walls for k in (0, 1) for x in range(r.x, r.x1) if r.y1 + k < H]
            if not cells:
                return self.candidates("verge" + ("@%g" % col if col is not None else ""))
        elif head.startswith("door:"):
            name = head[5:]
            if name not in self.named:
                raise SpecError("%s: anchor %r names no prop" % (self.id, expr))
            p = self.lay.props[self.named[name]]
            fw, fh = TR.TILESET["props"][p["kind"]]["footprint"]
            y = p["y"] + fh + 1
            cells = [(x, yy) for yy in (y, y + 1) for x in (p["x"] - 1, p["x"], p["x"] + fw - 1, p["x"] + fw)]
        elif head.startswith("near:"):
            other = self.cells.get(head[5:])
            if other is None:
                raise SpecError("%s: anchor %r: %s is not placed before it" % (self.id, expr, head[5:]))
            cells = [(x, y) for x, y in _ring(int(other[0]), int(other[1]), 4, W, H)
                     if max(abs(x - other[0]), abs(y - other[1])) >= 2]
        else:
            r = self.regions.get(head)
            if r is None:
                raise SpecError("%s: anchor %r names no band or feature (%s)" % (self.id, expr, ", ".join(self.regions)))
            if side == "top":                       # its middle first
                cells = sorted(r.cells(), key=lambda c: (abs(c[0] - (r.x + (r.w - 1) / 2.0)) + abs(c[1] - (r.y + (r.h - 1) / 2.0)), c))
                return cells, col, True, set()
            if side in ("back", "front"):           # its own first or last row (a round shape's, column by column)
                cells = []
                for x in range(r.x, r.x1):
                    ys = [c[1] for c in r.cells() if c[0] == x]
                    if ys:
                        cells.append((x, min(ys) if side == "back" else max(ys)))
            elif side == "n":
                cells = [(x, r.y - off) for x in range(r.x, r.x1)]
            elif side == "s":
                cells = [(x, r.y1 + off - 1) for x in range(r.x, r.x1)]
            elif col is not None and r.kind == "band":
                primary = {(x, r.mid_row()) for x in range(r.x, r.x1)}
                cells = r.cells()
            else:
                cells = r.cells()
        return [c for c in cells if 0 <= c[0] < W and 0 <= c[1] < H], col, False, primary

    def _resolve(self, oid, expr, obj, g, reach, lanes, taken):
        cells, col, centre, primary = self.candidates(expr)
        water_ok = expr.startswith("water") or obj.get("type") in ("fishing_spot",)
        others = list(self.cells.values())
        way_cells = [TR.cell(p["at"]) for k, p, _ in self.ways.values() if k != "door"]
        best, best_key = None, None
        for i, c in enumerate(cells):
            x, y = c
            if c in taken or c in lanes or g.stair[y][x]:
                continue
            fl = g.floor(x, y)
            if fl is None:
                if not (water_ok and self.lay.lv[y][x] == WATER):
                    continue
                if not any(q in reach and abs((g.floor(*q) or 0.0)) <= TR.REACH_ALT for q in _ring(x, y, 2, self.w, self.h)):
                    continue
            elif c not in reach:
                continue
            near = min([max(abs(x - o[0]), abs(y - o[1])) for o in others] + [9])
            if near < 2:
                continue
            ways = min([max(abs(x - o[0]), abs(y - o[1])) for o in way_cells] + [9])
            if ways < 3:
                continue
            if centre:
                key = (i,)
            else:
                spread = min(near, 6) + 0.5 * min(ways, 6)
                pref = abs(x - col) if col is not None else 0.0
                key = (pref, c not in primary, -spread, h01(x, y, self.seed))
            if best_key is None or key < best_key:
                best, best_key = c, key
            if centre:
                break
        if best is None:
            raise SpecError("%s: anchor %s %r finds no free cell a body reaches from every way" % (self.id, oid, expr))
        self.notes.append("%s %s -> %s" % (oid, expr, best))
        return best

    # ================================================================ 5. stairs "auto"
    def auto_stairs(self):
        """A flight up onto every raised band or feature that an anchor stands on, or that a way's cut climbs onto,
        on its south face: as wide as the walk (3, or 2 on a shape under 8 cells), two rows a level, at the column
        nearest what stands on it; never on the water, a lane, a prop or an anchor."""
        lanes = self.lanes()
        taken = self._prop_cells() | {(int(c[0]), int(c[1])) for c in self.cells.values()}
        for d, x0, width, walk in self.cuts:
            if d != "n":
                continue
            # Up the path from the walk: a flight on the lower side of every edge it climbs (its top row against the
            # edge), as wide as the path.
            for y in range(walk.y - 1, 0, -1):
                lo, hi = self.lay.lv[y][x0], self.lay.lv[y - 1][x0]
                if lo == WATER or hi == WATER or hi <= lo:
                    continue
                depth = 2 * (hi - lo)
                cells = [(xx, yy) for yy in range(y, y + depth) for xx in range(x0, x0 + width)]
                if all(yy < self.h and self.lay.lv[yy][xx] == lo for xx, yy in cells):
                    self.lay.stair(x0, y, width, depth, lo, hi, self.stair_paint)
                    self.notes.append("stair up the cut at %d,%d" % (x0, y))
                else:
                    self.notes.append("no room for a flight under the cut's edge at %d,%d" % (x0, y))
                for r in self.regions.values():
                    if r.x <= x0 < r.x1 and r.y <= y - 1 < r.y1:
                        self.climbed.add(r.name)
        wanted = []
        for r in self.regions.values():
            if r.wall or r.water or r.level is None or r.level <= 0:
                continue
            mine = set(r.cells())
            on = [c for c in self.cells.values() if (int(c[0] + 0.5), int(c[1] + 0.5)) in mine]
            if not on and not (r.kind == "band" and r.h >= 3):
                continue
            wanted.append((r, on))
        # R2: a flight stands off the walks (a road) where it can: the walk along it would cross the flight from its
        # side, which auto-path's steering cannot (it stalls against the cheek); and its foot on its landing's own level
        # where it can (a step lower shows the flight's front as a slot). Where no spot is so (a tower over a narrow
        # yard), the nearest spot as before.
        walks = {c for q in self.regions.values() if q.walk for c in q.cells()}
        for r, on in wanted:
            if r.name in self.climbed:
                continue
            width = 3 if r.w >= 8 else 2
            xs = [c[0] for c in on] or [r.x + r.w // 2]
            want = sorted(xs)[len(xs) // 2]
            spots = sorted(range(r.x, r.x1 - width + 1), key=lambda x: (abs(x + width // 2 - want), x))
            flight = self._flight(r, spots, width, taken, lanes, walks, 0) or self._flight(r, spots, width, taken, lanes, walks) \
                or self._flight(r, spots, width, taken, lanes, set())
            if flight:
                self.lay.stair(*flight, self.stair_paint)
                self.notes.append("stair up onto %s at %d,%d" % (r.name, flight[0], flight[1]))
            else:
                self.notes.append("no stair up onto %s (no room under it)" % r.name)

    def _flight(self, r, spots, width, taken, lanes, walks, drop=1):
        """The first spot (x, y, w, h, from, to) where a flight up onto `r` fits, its cells off `walks`, its foot at most
        `drop` levels under its landing; None if none."""
        for x in spots:
            # The flight's top row lies against the shape's south edge, the same row under every column of it.
            bottoms = {r.bottom(xx) for xx in range(x, x + width)}
            if len(bottoms) != 1 or None in bottoms:
                continue
            top = bottoms.pop() + 1
            if top >= self.h:
                continue
            below = self.lay.lv[top][x]
            if below == WATER or below >= r.level:
                continue
            depth = 2 * (r.level - below)
            cells = [(xx, yy) for yy in range(top, top + depth) for xx in range(x, x + width)]
            if any(not (0 <= yy < self.h) or self.lay.lv[yy][xx] != below or (xx, yy) in taken
                   or (xx, yy) in lanes or (xx, yy) in walks for xx, yy in cells):
                continue
            # Its foot stands on the ground it leads down to: no higher, and a step at most lower.
            foot = [(xx, top + depth) for xx in range(x, x + width)]
            if any(not (0 <= yy < self.h) or self.lay.lv[yy][xx] == WATER or not below - drop <= self.lay.lv[yy][xx] <= below
                   or (xx, yy) in taken for xx, yy in foot):
                continue
            return (x, top, width, depth, below, r.level)
        return None

    # ================================================================ 6. the foes
    def foes(self):
        """The foes' spawn points, one list per side-view spawn in its order: written out (a list of cells), or "auto"
        (each point on the verges, at the column its side-view point stands at across the room), or "auto:<anchor>"
        (on the cells an anchor names: a tower's top, the bank); never within 4 cells of a way, 3 of a shrine or 2 of
        anything else placed, always where a body reaches from every way."""
        if "foes" in self.pins:
            self.lay.spawns = [[list(c) for c in lst] for lst in self.pins["foes"]]
            return
        f = self.spec.get("foes")
        if f is None:
            return
        side = self.side
        sv = side.get("spawns", [])
        plan = ["auto"] * len(sv) if f == "auto" else list(f)
        if len(plan) != len(sv) and any(isinstance(p, str) for p in plan):
            raise SpecError("%s: foes lists %d spawns, the side-view room has %d" % (self.id, len(plan), len(sv)))
        out = [[list(c) for c in p] if not isinstance(p, str) else None for p in plan]
        if all(o is not None for o in out):
            self.lay.spawns = out
            return
        width = float(side.get("bounds", [0, 0, 1280])[2]) or 1280.0
        g = self.grid()
        reach = self.reached(g)
        lanes = self.lanes()
        taken = self._prop_cells()
        ways = [TR.cell(p["at"]) for k, p, _ in self.ways.values() if k != "door"] + self.starts()
        shrines = [c for oid, c in self.cells.items() if self._type(side, oid) in SHRINE_TYPES]
        objects = list(self.cells.values())
        used = [tuple(c) for lst in out if lst for c in lst]
        stairs = {(xx, yy) for st in self.lay.stairs for yy in range(st["y"] - 1, st["y"] + st["h"] + 1)
                  for xx in range(st["x"] - 1, st["x"] + st["w"] + 1)}
        open_cells = [c for c in sorted(reach) if c not in lanes and c not in taken and c not in stairs
                      and g.floor(*c) is not None]
        has_walk = any(r.walk for r in self.regions.values())
        verges = set(self.candidates("verge")[0]) if has_walk else set(open_cells)
        for k, sp in enumerate(sv):
            if out[k] is not None:
                continue
            hint = plan[k][5:] if plan[k].startswith("auto:") else ""
            if hint:
                pool = [c for c in self.candidates(hint)[0] if c in reach and c not in lanes and c not in taken]
            elif sp.get("boss"):
                pool = open_cells
            else:
                pool = [c for c in open_cells if c in verges]
            pts = []
            for i, p in enumerate(sp.get("points", [])):
                tx = float(p[0]) / width * self.w
                best, key = None, None
                for c in pool:
                    near = lambda qs, n: any(max(abs(c[0] - q[0]), abs(c[1] - q[1])) < n for q in qs)
                    if near(ways, 4) or near(shrines, 3) or near(objects, 2) or near(used, 3):
                        continue
                    kk = (abs(c[0] - tx) + (0.6 * abs(c[1] - self.h / 2.0) if sp.get("boss") else 0.0),
                          h01(c[0], c[1], self.seed + 7 * k + i))
                    if key is None or kk < key:
                        best, key = c, kk
                if best is None:
                    raise SpecError("%s: spawn %d (%s) point %d finds no free cell%s" % (self.id, k, sp.get("enemy"), i,
                                                                                    " on " + hint if hint else ""))
                used.append(best)
                pts.append([best[0], best[1]])
            out[k] = pts
        self.lay.spawns = out

    @staticmethod
    def _type(side, oid):
        for o in side.get("objects", []):
            if o["id"] == oid:
                return o.get("type", "")
        return ""

    # ================================================================ 7. props by rule, the flora
    def rule_props(self):
        if "props" in self.pins:
            return
        for p in self.spec.get("props", []):
            if not isinstance(p, dict):
                continue
            r = self.regions.get(p["along"])
            if r is None:
                raise SpecError("%s: props along %r: no such band" % (self.id, p["along"]))
            row = p.get("row", r.y)
            every = p.get("every", 10)
            x = r.x + p.get("start", every // 2)
            while x < r.x1:
                if self._fits_any(p["kind"], x, row):
                    self._prop(p["kind"], x, row)
                x += every

    def _fits_any(self, kind, x, y):
        fw, fh = TR.TILESET["props"][kind]["footprint"]
        taken = self._prop_cells()
        lanes = self.lanes()
        anchors = {(int(c[0] + 0.5), int(c[1] + 0.5)) for c in self.cells.values()}
        for yy in range(y, y + fh):
            for xx in range(x, x + fw):
                if not (0 <= xx < self.w and 0 <= yy < self.h) or (xx, yy) in taken or (xx, yy) in lanes or (xx, yy) in anchors:
                    return False
                if self.lay.lv[yy][xx] == WATER or any(s["x"] <= xx < s["x"] + s["w"] and s["y"] <= yy < s["y"] + s["h"] for s in self.lay.stairs):
                    return False
        return True

    def flora(self):
        if "props" in self.pins:
            return
        if "flora" in self.pins:
            for p in self.pins["flora"]:
                self._prop(*p)
        elif self.spec.get("flora") is not None or self.spec.get("biome"):
            self._scatter()
        for p in self.pins.get("add", []):
            self._prop(*p)
        drop = [tuple(c) for c in self.pins.get("drop", [])]
        if drop:
            keep = []
            for p in self.lay.props:
                fw, fh = TR.TILESET["props"][p["kind"]]["footprint"]
                hit = any(p["x"] <= x < p["x"] + fw and p["y"] <= y < p["y"] + fh for x, y in drop)
                if not hit or p.get("fixed"):
                    keep.append(p)
            self.lay.props = keep

    def _scatter(self):
        """The flora: for each band (its pool in the spec, else the biome's for its role) the strips along its edges
        (`_strips`), each cut into equal stretches and one piece tried in each, at the first cell of the stretch in the
        order of a hash of the room's seed and the cell where its kind fits (a Poisson disc kept even along the edge,
        as the hand placed them): kept clear of every other piece by its kind's spacing, on the ground the foliage kit
        says it grows on, and only where nothing it blocks is cut off."""
        pools = dict(self.biome["flora"])
        spec = dict(self.spec.get("flora") or {})
        density = spec.pop("density", self.biome["density"])
        lanes = self.lanes()
        d = self._dict_for_check()
        clear = TR.clear_cells(d)
        walks = TR.scene_walks(self.id, d)
        g = self.grid()
        spots = self._spots(d, g)
        placed = []
        n_before = len(self.lay.props)
        for r in sorted(self.regions.values(), key=lambda r: (r.y, r.x)):
            # A shape laid again under the same name (rubble, rubble_2, ...; R2) shares the pool its name is given.
            pool = spec.get(r.name, spec.get(r.name.rstrip("0123456789").rstrip("_") if r.name[-1:].isdigit() else r.name,
                                             pools.get(r.role())))
            dens = density
            if isinstance(pool, dict):          # {kinds, density}: a band's own pool and how thick it lies
                dens = pool.get("density", density)
                pool = pool.get("kinds", pools.get(r.role()))
            if not pool or dens <= 0:
                continue
            for k, (habitat, cells, gap) in enumerate(self._strips(r)):
                kinds = [kk for kk in pool if _fits_habitat(kk, habitat)]
                if not kinds or not cells:
                    continue
                xs = sorted({c[0] for c in cells})
                x0, x1 = xs[0], xs[-1] + 1
                want = max(1, int(round((x1 - x0) / float(gap) * dens / 0.3)))
                salt = self.seed + 101 * k + len(r.name)
                # The stretches' ends wander (a third of a stretch either way) and one in seven stays empty, so the
                # pieces never stand in a row like a fence.
                ends = [x0] + sorted(x0 + (x1 - x0) * (i + (h01(i, k, salt + 9) - 0.5) * 0.66) / want
                                     for i in range(1, want)) + [x1]
                for i in range(want):
                    lo, hi = int(ends[i]), int(ends[i + 1])
                    if h01(i, k, salt + 13) < 0.14:
                        continue
                    seg = sorted((c for c in cells if lo <= c[0] < hi), key=lambda c: h01(c[0], c[1], salt))
                    trees = [kk for kk in kinds if kk in TREES]
                    rest = [kk for kk in kinds if kk not in TREES] or trees
                    for (x, y) in seg:
                        # Where trees grow (a meadow's back, the bank behind the water) six pieces in ten are trees, as
                        # the hand set them, at a cliff's foot four; the rest bushes, rocks and grass. A biome's
                        # `tree_share` sets the six (a grove's bamboo stands thicker), the foot two thirds of it.
                        share = self.biome.get("tree_share", 0.6)
                        share = (0.4 if share == 0.6 else share * 2.0 / 3.0) if habitat == "foot" else share
                        pick = trees if trees and h01(x, y, salt + 5) < share else rest
                        kind = pick[int(h01(x, y, salt + 3) * len(pick)) % len(pick)]
                        if not self._fits_flora(kind, x, y, clear, walks, lanes, spots, placed):
                            continue
                        if self._prop(kind, x, y) is None:
                            continue
                        if TR.TILESET["props"][kind].get("solid", True) and not self._still_reached():
                            self.lay.props.pop()
                            continue
                        placed.append((kind, x, y))
                        break
        self.notes.append("flora: %d pieces" % (len(self.lay.props) - n_before))

    def _strips(self, r):
        """Where a band's flora grows, as (habitat, cells, spacing along it): a meadow's or a terrace's `back` (trees
        among bushes) and its `lip` along the south edge (bushes, grass, rocks: nothing that hides what stands below
        it); a cliff's `foot`; a road's `verge` each side (no tree on a road's shoulder); the water's `bank_back`
        (willows), its `bank` (grass, reeds), its `shallow` cells by the land (cattails) and the open `water` (lotus); a
        floor under shallow water (R2: `q`, `h`) is `shallow` all over."""
        W, H = self.w, self.h
        lv = self.lay.lv

        def rows(ys, x0=r.x, x1=r.x1):
            return [(x, y) for y in ys if 0 <= y < H for x in range(x0, x1)]
        if r.water:
            shallow, deep = [], []
            for (x, y) in r.cells():
                if lv[y][x] != WATER:
                    continue
                land = [q for q in _ring(x, y, 1, W, H) if lv[q[1]][q[0]] != WATER]
                (shallow if land else deep).append((x, y))
            deep = [c for c in deep if all(lv[q[1]][q[0]] == WATER for q in _ring(c[0], c[1], 2, W, H))]
            land = lambda cs: [c for c in cs if 0 <= c[1] < H and lv[c[1]][c[0]] != WATER]
            return [("bank_back", land(r.beside(2)), 7), ("bank", land(r.beside(1)), 6),
                    ("shallow", shallow, 7), ("water", deep, 9)]
        if r.opts.get("paint") in TR.FLOODED:
            return [("shallow", [c for c in r.cells() if lv[c[1]][c[0]] != WATER], 7)]   # R2: a wading floor's reeds
        if r.walk:
            return [("verge", rows([r.y - 2, r.y - 1, r.y1, r.y1 + 1]), 7)]
        if r.wall:
            return [("foot", rows([r.y1, r.y1 + 1]), 5)]
        if r.h <= 3:
            return [("lip", rows(range(r.y, r.y1)), 5)]
        return [("back", rows(range(r.y, r.y1 - 2)), 6), ("lip", rows([r.y1 - 2, r.y1 - 1]), 6)]

    def _fits_flora(self, kind, x, y, clear, walks, lanes, spots, placed):
        art = TR.TILESET["props"][kind]
        fw, fh = art["footprint"]
        if len({self.lay.lv[yy][xx] for yy in range(y, y + fh) for xx in range(x, x + fw)
                if 0 <= xx < self.w and 0 <= yy < self.h}) > 1:
            return False          # a piece stands on one level: never astride an edge (it would float)
        taken = self._prop_cells()
        cls = _spacing_class(kind)
        gap = self._gap(cls)
        for k, px, py in placed:
            other = self._gap(_spacing_class(k))
            if max(abs(px - x), abs(py - y)) < max(gap, other) * (1.0 if cls == _spacing_class(k) else 0.6):
                return False
        for yy in range(y, y + fh):
            for xx in range(x, x + fw):
                if not (0 <= xx < self.w and 0 <= yy < self.h) or (xx, yy) in taken or (xx, yy) in clear or (xx, yy) in lanes:
                    return False
                water = self.lay.lv[yy][xx] == WATER
                if kind in TR.ON_WATER:
                    if not water:
                        return False
                    continue
                if kind in TR.WADING and (water or self.lay.pt[yy][xx] in TR.FLOODED):
                    continue
                if water or any(s["x"] <= xx < s["x"] + s["w"] and s["y"] <= yy < s["y"] + s["h"] for s in self.lay.stairs):
                    return False
                if kind not in TR.ANYWHERE and self.lay.pt[yy][xx] not in TR.PLANTED:
                    return False
                if art.get("solid", True) and (xx, yy) in walks:
                    return False
                # A solid piece keeps a cell off a walk, so the road reads clear.
                if art.get("solid", True) and kind not in TREES and any(
                        self.lay.pt[q[1]][q[0]] in "dps" and self.lay.lv[q[1]][q[0]] == self.lay.lv[yy][xx]
                        for q in ((xx, yy - 1), (xx, yy + 1)) if 0 <= q[1] < self.h) and not kind.startswith("fence"):
                    return False
        c = art.get("canopy")
        if c and any(self.lay.pt[q[1]][q[0]] in "dp" for q in _ring(x, y, 1, self.w, self.h)):
            return False          # a tree stands back from a road or a yard's edge
        if c:
            base = self.lay.lv[y + fh - 1][x]
            sw = (x * 16, (y + fh) * 16 - max(0, base) * 16)
            box = (sw[0] + c["at"][0] + c["box"][0], sw[1] + c["at"][1] + c["box"][1], c["box"][2], c["box"][3])
            key = (y + fh) * 16 + 0.5
            for oid, rr, k in spots:
                if k < key and rr[0] < box[0] + box[2] and box[0] < rr[0] + rr[2] and rr[1] < box[1] + box[3] and box[1] < rr[1] + rr[3]:
                    return False
        return True

    def _gap(self, cls):
        """How far apart two scattered pieces of a class stand (SPACING; a biome's `tree_gap` for its trees)."""
        return self.biome.get("tree_gap", SPACING["tree"]) if cls == "tree" else SPACING[cls]

    def _spots(self, d, g):
        """What a canopy may not hide (topdown_rooms.check_foliage's rule): every placed thing and every way's lane."""
        spots = []
        for oid, at in d["place"].items():
            c = TR.cell(at)
            fl = g.floor(*c)
            lv = (fl or 0.0) / 32.0
            feet = ((at[0] + 0.5) * 16, (at[1] + 0.5) * 16 - lv * 16)
            key = (c[1] + 1) * 16 + 0.25 if lv > 0 else (at[1] + 0.5) * 16
            spots.append((oid, (feet[0] - 6, feet[1] - 34, 12, 34), key))
        for pid, p in d["portals"].items():
            for c in TR.portal_lane(p):
                if 0 <= c[0] < g.w and 0 <= c[1] < g.h:
                    lv = max(0.0, (g.floor(*c) or 0.0) / 32.0)
                    spots.append(("way " + pid, (c[0] * 16, c[1] * 16 - lv * 16, 16, 16), (c[1] + 0.5) * 16))
        return spots

    def _dict_for_check(self):
        d = self.snapshot()
        d["spawn"] = list(self._spawn_cell())
        d["place"] = {oid: list(c) for oid, c in self.cells.items()}
        portals = {}
        for pid, (kind, a, b) in self.ways.items():
            portals[pid] = self._door_way(a, b) if kind == "door" else a
        d["portals"] = portals
        d["spawns"] = self.lay.spawns
        d["event"] = self.spec.get("event", {})
        return d

    def _still_reached(self):
        g = self.grid()
        reach = self.reached(g, gaps=False)
        for oid, c in self.cells.items():
            cc = TR.cell(c)
            near = [q for q in _ring(cc[0], cc[1], 3, self.w, self.h) if (q[0] - cc[0]) ** 2 + (q[1] - cc[1]) ** 2 <= 9]
            if not any(q in reach for q in near):
                return False
        for kind, a, b in self.ways.values():
            p = self._door_way(a, b) if kind == "door" else a
            if TR.cell(p["at"]) not in reach:
                return False
        return True

    # ================================================================ 8. sand and snow, the rest
    def ground(self):
        for paint, rects in self.spec.get("ground", {}).items():
            rr = []
            for r in rects:
                if isinstance(r, str):
                    rr += self._ground_rects(r)
                else:
                    rr.append(r)
            if paint == "sand":
                self.lay.sand(*rr)
            elif paint == "snow":
                self.lay.snow(*rr)
            elif paint == "snowpack":
                self.lay.snow(*rr, paint="k")
            else:
                raise SpecError("%s: ground %r is not sand, snow or snowpack" % (self.id, paint))

    def _ground_rects(self, name):
        """A band's name as ground: `stream.bank` the row along the water each side (its sand), else the band's rect."""
        head, _, tail = name.partition(".")
        r = self.regions.get(head)
        if r is None:
            raise SpecError("%s: ground names no band %r" % (self.id, name))
        if tail == "bank":
            return [(x, y, 1, 1) for x, y in r.beside(1)]
        return [(r.x, r.y, r.w, r.h)]

    def _spawn_cell(self):
        sp = self.pins.get("spawn", self.spec.get("spawn"))
        if sp is None:
            starts = self.starts()
            return starts[0] if starts else (self.w // 2, self.h // 2)
        if isinstance(sp, str):
            kind, a, b = self.ways[sp]
            p = self._door_way(a, b) if kind == "door" else a
            return TR.cell(TR.arrive(p))
        return tuple(sp)

    def finish(self):
        self.lay.spawn = list(self._spawn_cell())
        for oid in self.spec.get("anchors", {}):
            c = self.cells[oid]
            self.lay.at(oid, c[0], c[1])
        self.set_ways()
        if self.spec.get("event"):
            self.lay.event = self.spec["event"]
        if self.spec.get("routes"):
            self.lay.routes = dict(self.spec["routes"])
        if self.spec.get("areas"):
            self.lay.areas = [dict(a) for a in self.spec["areas"]]
        if self.spec.get("traverse"):
            self.lay.traverse = self.traverse_rows()
        if self.spec.get("stage"):
            self.lay.stage = self.stage_cells()

    # ================================================================ T1: the side view's traversal and set pieces
    # docs/architecture/topdown_mechanics.md: a raft, an updraft and a climbable face on the grid, and where a room event
    # the side view calls to its own points sets its foes. topdown_rooms.check_traverse holds each to the grid.
    TRAVERSE_KEYS = {"raft": ("at", "size", "path", "speed", "wait_s", "mode", "level"), "updraft": ("rect", "top", "speed"),
                     "bounce": ("rect", "speed"),
                     "vine": ("foot", "top"), "ladder": ("foot", "top"), "rope": ("foot", "top"), "chain": ("foot", "top")}

    def traverse_rows(self):
        out = []
        for row in self.spec["traverse"]:
            kind, tid, opts = row if len(row) == 3 else (row[0], row[1], {})
            keys = self.TRAVERSE_KEYS.get(kind)
            if keys is None:
                raise SpecError("%s: traverse %r: a raft, an updraft, a bounce, a vine, a ladder, a rope or a chain" % (self.id, kind))
            stray = sorted(set(opts) - set(keys))
            if stray:
                raise SpecError("%s: traverse %s %s: unknown key %s (%s)" % (self.id, kind, tid, ", ".join(stray), ", ".join(keys)))
            r = {"kind": kind, "id": tid}
            for k in keys:
                if k in opts:
                    r[k] = _listed(opts[k])
            out.append(r)
        return out

    def stage_cells(self):
        """Each stage point: a cell as written, or an anchor expression resolved as an anchor is (reached from every way,
        off the lanes, the stairs and the props, two cells from every thing and three from a way)."""
        g = self.grid()
        reach = self.reached(g)
        lanes = self.lanes()
        taken = self._prop_cells()
        out = {}
        for eid, pts in self.spec["stage"].items():
            cells = []
            for i, q in enumerate(pts):
                c = q if isinstance(q, (tuple, list)) else self._resolve("stage %s %d" % (eid, i), q, {}, g, reach, lanes, taken)
                cells.append([c[0], c[1]])
            out[eid] = cells
        return out

    # ================================================================
    def run(self):
        self.walls()
        self.bands()
        self.features()
        self.rubble()
        self.stairs()
        self.place_props()
        self.way_defs()
        self.anchors()
        if self.auto_stairs_wanted():
            self.auto_stairs()
        self.foes()
        self.rule_props()
        self.flora()
        self.ground()
        self.finish()
        return self.lay


def _listed(v):
    """A spec value as the layout's JSON writes it: tuples as lists, all the way down."""
    if isinstance(v, (tuple, list)):
        return [_listed(q) for q in v]
    return v


def _ring(x, y, n, W, H):
    return [(xx, yy) for yy in range(y - n, y + n + 1) for xx in range(x - n, x + n + 1)
            if (xx, yy) != (x, y) and 0 <= xx < W and 0 <= yy < H]


def _fits_habitat(kind, habitat):
    """Does a kind of the foliage kit grow in this strip (`Build._strips`)?"""
    art = TR.TILESET["props"][kind]
    canopy = bool(art.get("canopy"))
    if habitat == "water":
        return kind in TR.ON_WATER or kind == "lotus"
    if habitat == "shallow":
        return kind in TR.WADING
    if kind in TR.ON_WATER or kind == "lotus" or kind in TR.WADING:
        return False
    if habitat in ("lip", "verge", "bank"):
        return not canopy
    return True


def _spacing_class(kind):
    art = TR.TILESET["props"][kind]
    if art.get("canopy"):
        return "tree"
    if kind in TR.ON_WATER:
        return "water"
    return "solid" if art.get("solid", True) else "soft"


def compile_room(spec):
    """A spec (spec.room) compiled to its Layout."""
    return Build(spec).run()
