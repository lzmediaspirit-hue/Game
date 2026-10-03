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
import math
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
# The kinds of the foliage kit by how they grow (TopdownRoom's tile set): a tree's canopy may hide what stands north of
# it; a walk-through plant never blocks.
TREES = sorted(k for k, v in TR.TILESET["props"].items() if v.get("canopy"))
WALK_THROUGH = sorted(k for k, v in TR.TILESET["props"].items() if v.get("foliage") and not v.get("solid", True))
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

    @property
    def x1(self):
        return self.x + self.w

    @property
    def y1(self):
        return self.y + self.h

    def mid_row(self):
        return self.y + self.h // 2

    def cells(self):
        return [(x, y) for y in range(self.y, self.y1) for x in range(self.x, self.x1)]

    def role(self):
        return "water" if self.water else "walk" if self.walk else "wall" if self.wall else "ground"


class Build:
    """One room's compile: the spec in, the Layout out (`run`)."""

    def __init__(self, spec):
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
        self.notes = []           # what the engine decided, for --show

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
        if opts.get("water"):
            self.lay.water(x, y, w, h)
        else:
            self.lay.rect(x, y, w, h, opts.get("level"), opts.get("paint"))
        if name in self.regions and kind == "feature":
            name = "%s_%d" % (name, sum(1 for k in self.regions if k.split("_")[0] == name))
        r = Region(name, x, y, w, h, opts, kind)
        if r.level is None:
            r.level = self.lay.lv[min(self.h - 1, y + h // 2)][min(self.w - 1, x + w // 2)]
        self.regions.setdefault(name, r)

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
        """A way at the north or south edge: a path `width` wide from the edge to the nearest walk band, through every
        band between at the walk's level (a wall is cut down to it: a gorge)."""
        width, paint = (cut, "d") if isinstance(cut, int) else cut
        walks = [r for r in self.regions.values() if r.walk]
        if not walks:
            raise SpecError("%s: a cut needs a walk band" % self.id)
        x0 = int(pos) - width // 2
        if d == "n":
            walk = min(walks, key=lambda r: r.y)
            y0, y1 = 0, walk.y
        else:
            walk = max(walks, key=lambda r: r.y1)
            y0, y1 = walk.y1, self.h
        lv = walk.level
        for y in range(y0, y1):
            for x in range(x0, x0 + width):
                if self.lay.lv[y][x] == WATER:
                    continue
                cur = self.lay.lv[y][x]
                if cur > lv:
                    hit = [r for r in self.regions.values() if r.x <= x < r.x1 and r.y <= y < r.y1]
                    if any(r.wall for r in hit) or not hit:
                        self.lay.lv[y][x] = lv
                self.lay.pt[y][x] = paint

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
        side = {o["id"]: o for o in TR.side(self.id).get("objects", [])}
        spec = self.spec.get("anchors", {})
        g = self.grid()
        reach = self.reached(g)
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
        if missing and not self.spec.get("anchors_optional"):
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
        if "@" in expr:
            expr, c = expr.split("@", 1)
            col = float(c)
        side, off = None, 0
        head, _, tail = expr.partition(".")
        if tail:
            side, off = tail[0], int(tail[1:] or 1)
            if side not in "ns" and tail != "top":
                raise SpecError("%s: anchor %r: a side is n or s (n2, s2: two rows off)" % (self.id, expr))
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
            if side == "t":                         # .top: the feature's middle first
                cells = sorted(r.cells(), key=lambda c: (abs(c[0] - (r.x + (r.w - 1) / 2.0)) + abs(c[1] - (r.y + (r.h - 1) / 2.0)), c))
                return cells, col, True
            if side == "n":
                cells = [(x, r.y - off) for x in range(r.x, r.x1)]
            elif side == "s":
                cells = [(x, r.y1 + off - 1) for x in range(r.x, r.x1)]
            elif col is not None and r.kind == "band":
                cells = [(x, r.mid_row()) for x in range(r.x, r.x1)] + r.cells()
            else:
                cells = r.cells()
        return [c for c in cells if 0 <= c[0] < W and 0 <= c[1] < H], col, False

    def _resolve(self, oid, expr, obj, g, reach, lanes, taken):
        cells, col, centre = self.candidates(expr)
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
                key = (pref, -spread, h01(x, y, self.seed))
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
        wanted = []
        for r in self.regions.values():
            if r.wall or r.water or r.level is None or r.level <= 0:
                continue
            on = [c for c in self.cells.values() if r.x <= c[0] < r.x1 and r.y <= c[1] < r.y1]
            if not on and not (r.kind == "band" and r.h >= 3):
                continue
            wanted.append((r, on))
        for r, on in wanted:
            below = self.lay.lv[r.y1][min(self.w - 1, r.x + r.w // 2)] if r.y1 < self.h else None
            if below is None or below == WATER or below >= r.level:
                continue
            rise = r.level - below
            width = 3 if r.w >= 8 else 2
            depth = 2 * rise
            xs = [c[0] for c in on] or [r.x + r.w // 2]
            want = sorted(xs)[len(xs) // 2]
            spots = sorted(range(r.x + 1, r.x1 - width), key=lambda x: (abs(x + width // 2 - want), x))
            for x in spots:
                cells = [(xx, yy) for yy in range(r.y1, r.y1 + depth) for xx in range(x, x + width)]
                if any(not (0 <= yy < self.h) or self.lay.lv[yy][xx] != below or (xx, yy) in taken
                       or (xx, yy) in lanes for xx, yy in cells):
                    continue
                foot = [(xx, r.y1 + depth) for xx in range(x, x + width)]
                if any(not (0 <= yy < self.h) or self.lay.lv[yy][xx] not in (below,) for xx, yy in foot):
                    continue
                self.lay.stair(x, r.y1, width, depth, below, r.level, self.stair_paint)
                self.notes.append("stair up onto %s at %d,%d" % (r.name, x, r.y1))
                break
            else:
                self.notes.append("no stair up onto %s (no room under it)" % r.name)

    # ================================================================ 6. the foes
    def foes(self):
        if "foes" in self.pins:
            self.lay.spawns = [[list(c) for c in lst] for lst in self.pins["foes"]]
            return
        f = self.spec.get("foes")
        if f is None:
            return
        if f != "auto" and not isinstance(f, dict):
            self.lay.spawns = [[list(c) for c in lst] for lst in f]
            return
        side = TR.side(self.id)
        width = float(side.get("bounds", [0, 0, 1280])[2]) or 1280.0
        g = self.grid()
        reach = self.reached(g)
        lanes = self.lanes()
        taken = self._prop_cells()
        ways = [TR.cell(p["at"]) for k, p, _ in self.ways.values() if k != "door"] + self.starts()
        shrines = [c for oid, c in self.cells.items() if self._type(side, oid) in SHRINE_TYPES]
        objects = list(self.cells.values())
        open_cells = [c for c in sorted(reach) if c not in lanes and c not in taken and not g.stair[c[1]][c[0]]
                      and g.floor(*c) is not None and g.floor(*c) <= 0.0 + 1e-6 or False]
        verges = set(self.candidates("verge")[0]) if any(r.walk for r in self.regions.values()) else set(open_cells)
        used = []
        out = []
        for k, sp in enumerate(side.get("spawns", [])):
            pts = []
            for i, p in enumerate(sp.get("points", [])):
                tx = float(p[0]) / width * self.w
                pool = [c for c in open_cells if c in verges] if not sp.get("boss") else open_cells
                best, key = None, None
                for c in pool:
                    if any(max(abs(c[0] - q[0]), abs(c[1] - q[1])) < 4 for q in ways):
                        continue
                    if any(max(abs(c[0] - q[0]), abs(c[1] - q[1])) < 3 for q in shrines):
                        continue
                    if any(max(abs(c[0] - q[0]), abs(c[1] - q[1])) < 2 for q in objects + used):
                        continue
                    kk = (abs(c[0] - tx) + 0.6 * abs(c[1] - (self.h / 2.0 if sp.get("boss") else c[1])),
                          h01(c[0], c[1], self.seed + 7 * k + i))
                    if key is None or kk < key:
                        best, key = c, kk
                if best is None:
                    raise SpecError("%s: spawn %d (%s) point %d finds no cell on the verges" % (self.id, k, sp.get("enemy"), i))
                used.append(best)
                pts.append([best[0], best[1]])
            out.append(pts)
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
        """The flora: for each band (its pool, or the biome's for its role), the cells along its edges, visited in the
        order of a hash of the room's seed and the cell (dart throwing, a Poisson disc), each piece kept clear of every
        other by its kind's spacing and placed only where the foliage kit's rules hold and nothing it blocks is cut off."""
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
            pool = spec.get(r.name, pools.get(r.role()))
            if not pool:
                continue
            for habitat, cells in self._strips(r):
                kinds = [k for k in pool if _habitat(k) == habitat]
                if not kinds or not cells:
                    continue
                cols = len({c[0] for c in cells})
                want = max(1, int(round(density * cols / 2.0 / (1.6 if habitat == "water" else 1.0))))
                order = sorted(cells, key=lambda c: h01(c[0], c[1], self.seed + len(r.name)))
                got = 0
                for i, (x, y) in enumerate(order):
                    if got >= want:
                        break
                    kind = kinds[int(h01(x, y, self.seed + 3) * len(kinds)) % len(kinds)]
                    if not self._fits_flora(kind, x, y, clear, walks, lanes, spots, placed):
                        continue
                    idx = self._prop(kind, x, y)
                    if idx is None:
                        continue
                    if TR.TILESET["props"][kind].get("solid", True) and not self._still_reached():
                        self.lay.props.pop()
                        continue
                    placed.append((kind, x, y))
                    got += 1
        self.notes.append("flora: %d pieces" % (len(self.lay.props) - n_before))

    def _strips(self, r):
        """The cells along a band's edges where its flora grows, by habitat: `water` (the open water), `shallow` (the
        water by the bank), `land` (the bank, a terrace's lip and back, a road's verges)."""
        W, H = self.w, self.h
        lv = self.lay.lv
        if r.water:
            shallow, deep, bank = [], [], []
            for (x, y) in r.cells():
                if lv[y][x] != WATER:
                    continue
                land = [q for q in _ring(x, y, 1, W, H) if lv[q[1]][q[0]] != WATER]
                (shallow if land else deep).append((x, y))
            for y in (r.y - 1, r.y - 2, r.y1, r.y1 + 1):
                if 0 <= y < H:
                    bank += [(x, y) for x in range(r.x, r.x1) if lv[y][x] != WATER]
            deep = [c for c in deep if all(lv[q[1]][q[0]] == WATER for q in _ring(c[0], c[1], 2, W, H))]
            return [("land", bank), ("shallow", shallow), ("water", deep)]
        if r.walk:
            rows = [r.y - 1, r.y - 2, r.y1, r.y1 + 1]
            return [("land", [(x, y) for y in rows if 0 <= y < H for x in range(r.x, r.x1)])]
        if r.wall:
            rows = [r.y1, r.y1 + 1]
            return [("land", [(x, y) for y in rows if 0 <= y < H for x in range(r.x, r.x1)])]
        rows = list(range(r.y, r.y1))
        return [("land", [(x, y) for y in rows for x in range(r.x, r.x1)])]

    def _fits_flora(self, kind, x, y, clear, walks, lanes, spots, placed):
        art = TR.TILESET["props"][kind]
        fw, fh = art["footprint"]
        taken = self._prop_cells()
        cls = _spacing_class(kind)
        gap = SPACING[cls]
        for k, px, py in placed:
            other = SPACING[_spacing_class(k)]
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
                if kind in TR.WADING and water:
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
        if c:
            base = self.lay.lv[y + fh - 1][x]
            sw = (x * 16, (y + fh) * 16 - max(0, base) * 16)
            box = (sw[0] + c["at"][0] + c["box"][0], sw[1] + c["at"][1] + c["box"][1], c["box"][2], c["box"][3])
            key = (y + fh) * 16 + 0.5
            for oid, rr, k in spots:
                if k < key and rr[0] < box[0] + box[2] and box[0] < rr[0] + rr[2] and rr[1] < box[1] + box[3] and box[1] < rr[1] + rr[3]:
                    return False
        return True

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
            return [(r.x, r.y - 1, r.w, 1), (r.x, r.y1, r.w, 1)]
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
        for oid, c in self.cells.items():
            self.lay.at(oid, c[0], c[1])
        self.set_ways()
        if self.spec.get("event"):
            self.lay.event = self.spec["event"]
        if self.spec.get("routes"):
            self.lay.routes = dict(self.spec["routes"])
        if self.spec.get("areas"):
            self.lay.areas = [dict(a) for a in self.spec["areas"]]

    # ================================================================
    def run(self):
        self.walls()
        self.bands()
        self.features()
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


def _ring(x, y, n, W, H):
    return [(xx, yy) for yy in range(y - n, y + n + 1) for xx in range(x - n, x + n + 1)
            if (xx, yy) != (x, y) and 0 <= xx < W and 0 <= yy < H]


def _habitat(kind):
    if kind in TR.ON_WATER or kind == "lotus":
        return "water"
    if kind in TR.WADING:
        return "shallow"
    return "land"


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


def compile_verbose(spec):
    b = Build(spec)
    lay = b.run()
    return lay, b.notes
