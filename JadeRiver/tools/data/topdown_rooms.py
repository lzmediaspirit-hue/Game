"""Redesign Phase 4 (docs/redesign_top_down_plan.md, "As built: Phase 4", both parts): the rooms of the world redrawn for
the top-down world, one layout per room in data/topdown/<room id>.json, read by TopdownRoom (scripts/topdown). Each room
is a spec of the room engine (E1, audit 45 §6.1: tools/content/rooms/, docs/architecture/room_engine.md) compiled to the
`Layout` below; this module keeps the Layout, the walking rules (`Grid`), the checks and the build.

A layout keeps its side-view room's id and every id in it: the World authority takes the room's definition (NPCs,
objects, portals and their rules, foes, events) from data/rooms/ and only the places from here (TopdownRoom.merge_def):
  levels / paint / stairs / props   the height grid and its tiles (the Phase 1-2 format; tile set data/topdown/
                                    proto_tileset.json, drawn by tools/art/topdown/)
  spawn                             where a new character wakes, or anyone arrives without a way in
  place     object id -> [x, y]     cells (fractions allowed) for every NPC and object of the side-view room
  portals   portal id -> {at, dir, arrive, span}: the doorway or edge cell, the way it is walked into (n, s, e, w),
                                    the cell arrived on, and its width in tiles
  spawns    one list of cells per side-view spawn, in order;  event {wave, fixed}: a room event's spawn cells
  routes    object id -> [[x, y, s], ...]: a rooftop thief's run
  areas     [{kind, rect, ...}]: a hazard's areas in cells (the poison mist's pools; TopdownRoom.merge_def)
  traverse  [{kind, id, ...}]: T1, the side view's rafts, updrafts and climbable faces on the grid (TopdownTraverse;
                                    docs/architecture/topdown_mechanics.md), each held to the grid by check_traverse
  stage     event id -> [[x, y], ...]: T1, the cells a room event's side-view points are set at (WorldRoomEvents)

Deterministic: `python3 tools/data/topdown_rooms.py` writes the files, `--check` proves they are current. Each layout
is checked as it is built: every object, NPC, portal and spawn of its side-view room is placed on a cell a body can
stand on (or, for a thing on the water, within reach of one), and each is reached on foot from every way in (walking,
stairs, drops and a jump one level up, the TopdownMotor's rules; tests/topdown_tutorial.gd repeats it in the game);
every way is reached by auto-path's own rules too (no running jump over a gap), so the tracker's go button crosses it.
The Grid takes its step and its jump from data/movement.json, and `--check` holds it to the game's own grid on every
layout, cell for cell (`parity`, through tools/data/grid_parity.tscn; the command line: tools/data/README.md).
"""
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from collections import deque

import common
from common import ROOT, emit, run_cli
import topdown_life as LIFE   # decision 43, the living world: furnishings, stations and vistas (its own module)

OUT = os.path.join(ROOT, "data", "topdown")
ROOMS = os.path.join(ROOT, "data", "rooms")
TILESET = common.read("proto_tileset", OUT)
SOLID = 99
WATER = -1
# Where the door art sits in a building prop's footprint (columns from its west cell; the doorway is the row under it).
DOORS = {"house": (2, 3), "storehouse": (1, 2), "hall": (3, 4)}


class Layout:
    def __init__(self, rid, w, h, level=0, paint="g"):
        self.id = rid
        self.w = w
        self.h = h
        self.lv = [[level] * w for _ in range(h)]
        self.pt = [[paint] * w for _ in range(h)]
        self.stairs = []
        self.props = []
        self.place = {}
        self.portals = {}
        self.spawns = []
        self.event = {}
        self.routes = {}
        self.areas = []
        self.traverse = []   # T1: the side view's rafts, updrafts and climbable faces on the grid
        self.stage = {}      # T1: event id -> the cells a room event's side-view points are set at
        self.spawn = [w // 2, h // 2]

    # ---------------------------------------------------------------- drawing
    def rect(self, x, y, w, h, level=None, paint=None):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if 0 <= xx < self.w and 0 <= yy < self.h:
                    if level is not None:
                        self.lv[yy][xx] = level
                    if paint is not None:
                        self.pt[yy][xx] = paint
        return self

    def water(self, x, y, w, h):
        return self.rect(x, y, w, h, WATER, "~")

    def hline(self, x0, x1, y, width, paint, level=None):
        return self.rect(min(x0, x1), y, abs(x1 - x0) + 1, width, level, paint)

    def vline(self, x, y0, y1, width, paint, level=None):
        return self.rect(x, min(y0, y1), width, abs(y1 - y0) + 1, level, paint)

    def stair(self, x, y, w, h, frm, to, paint="s"):
        """A flight rising from its south edge (level `frm`) to its north edge (`to`)."""
        self.stairs.append({"x": x, "y": y, "w": w, "h": h, "from": frm, "to": to})
        return self.rect(x, y, w, h, frm, paint)

    def prop(self, kind, x, y):
        assert kind in TILESET["props"], kind
        p = {"kind": kind, "x": x, "y": y}
        if kind in DOORS:
            p["door"] = list(DOORS[kind])   # the columns its door art stands in (TopdownRoom.entrance)
        self.props.append(p)
        return len(self.props) - 1

    def green(self, *items):
        """Terrain v2's foliage and decor (art bible "Foliage and decor"): the big pieces, (kind, x, y) each, hand-placed
        to frame the room's paths and edges; a piece past the room's east edge is left out (a narrower variant of a
        room, the village at night). The ground cover between them is the room view's scatter."""
        for kind, x, y in items:
            fw = TILESET["props"][kind]["footprint"][0]
            if x + fw <= self.w:
                self.prop(kind, x, y)
        return self

    def sand(self, *rects):
        """Decision 44 (art bible "Sand and snow"): sand over the ground of these rects ((x, y, w, h) each) where it is
        meadow, marsh, flowers or a path; never on planks, paving or granite, nor under a plant of the foliage kit (it
        grows on meadow), so it is laid after the room's green. Its edges are the tiles' own: grass creeps over it, it
        creeps over the path, and it darkens where it meets the water."""
        return self._repaint(rects, "a", "gfmd")

    def snow(self, *rects, paint="n"):
        """Decision 44: fresh (`n`) or packed (`k`) snow over the rock, meadow, path, granite or fresh snow of these rects,
        never under a plant of the foliage kit; fresh snow creeps over what it meets on its level."""
        return self._repaint(rects, paint, "rgfdsn")

    def _repaint(self, rects, paint, over):
        plants = set()
        for p in self.props:
            if p["kind"] in FOLIAGE:
                fw, fh = TILESET["props"][p["kind"]]["footprint"]
                plants.update((x, y) for y in range(p["y"], p["y"] + fh) for x in range(p["x"], p["x"] + fw))
        for x0, y0, w, h in rects:
            for y in range(y0, y0 + h):
                for x in range(x0, x0 + w):
                    if (0 <= x < self.w and 0 <= y < self.h and self.pt[y][x] in over and (x, y) not in plants
                            and self.lv[y][x] != WATER):
                        self.pt[y][x] = paint
        return self

    def walls(self, x, y, w, h, high=3, low=1, paint="l"):
        """An interior's walls round a floor: the back wall `high` (its face three tiles), the sides as high, the front
        a low sill so it hides little."""
        self.rect(x, y, w, 1, high, paint)
        self.rect(x, y, 1, h, high, paint)
        self.rect(x + w - 1, y, 1, h, high, paint)
        self.rect(x, y + h - 1, w, 1, low, paint)
        return self

    # ---------------------------------------------------------------- the side-view room's things
    def at(self, oid, x, y):
        self.place[oid] = [x, y]

    def way(self, pid, x, y, d, arrive=None, span=None):
        p = {"at": [x, y], "dir": d}
        if arrive is not None:
            p["arrive"] = arrive
        if span is not None:
            p["span"] = span
        self.portals[pid] = p

    def door_path(self, prop_index, to_row, paint="d"):
        """A path two tiles wide from a building's doorway down to a lane at `to_row` (drawn before the doorway's
        way is set, so a path always leads to a door)."""
        p = self.props[prop_index]
        c0, c1 = DOORS[p["kind"]]
        fh = TILESET["props"][p["kind"]]["footprint"][1]
        return self.rect(p["x"] + c0, p["y"] + fh, c1 - c0 + 1, to_row - (p["y"] + fh), None, paint)

    def door(self, pid, prop_index, arrive_rows=1.5):
        """A way into a building prop, in the doorway under its door art, walked into northward."""
        p = self.props[prop_index]
        c0, c1 = DOORS[p["kind"]]
        fp = TILESET["props"][p["kind"]]["footprint"]
        x = p["x"] + (c0 + c1) / 2.0
        y = p["y"] + fp[1]
        self.way(pid, x, y, "n", [x, y + arrive_rows - 1.0], 2)

    # ---------------------------------------------------------------- output
    def dict(self):
        rows = ["".join("~" if v == WATER else str(v) for v in r) for r in self.lv]
        paint = ["".join(r) for r in self.pt]
        out = {"id": self.id, "name": side(self.id)["name"], "size": [self.w, self.h], "spawn": self.spawn,
               "levels": rows, "paint": paint, "stairs": self.stairs, "props": self.props,
               "place": self.place, "portals": self.portals, "spawns": self.spawns}
        if self.event:
            out["event"] = self.event
        if self.routes:
            out["routes"] = self.routes
        if self.areas:
            out["areas"] = self.areas
        if self.traverse:
            out["traverse"] = self.traverse
        if self.stage:
            out["stage"] = self.stage
        return out


# -------------------------------------------------------------------- the rules a body walks by (TopdownRoom's)
# The grid's measures are TopdownRoom's: a cell 32 units wide, a level 32 high. How far a body steps and climbs is the
# TopdownMotor's, read from data/movement.json `topdown` as the game reads it, so the rooms' checks follow the data.
# `parity` (run by --check) holds this Grid to the game's own TopdownRoom and TopdownRoute on every layout.
TILE = 32.0                        # TopdownRoom.TILE
LEVEL = 32.0                       # TopdownRoom.LEVEL
MOVE = common.read("movement")["topdown"]
STEP = float(MOVE["step_up"])      # the most a body walks up without a jump; a drop past it is a gap a running jump clears
# The most a jump climbs, in whole levels: its apex (TopdownMotor.apex(), impulse squared over twice the gravity) and
# the mantle; with the half unit TopdownRoute.find allows over it (one level today: 32.5).
HOP = LEVEL * math.floor((MOVE["impulse"] ** 2 / (2.0 * MOVE["gravity"]) + MOVE["mantle"]) / LEVEL) + 0.5
STAIR_STEP = LEVEL / 2.0 + 0.5     # up or down a stair along its rise without a hop (TopdownRoute.step_rise)
REACH_ALT = 48.0                   # a thing answers a body within this height of it (WorldAuthority.REACH_ALT)
DIRS = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0)}   # a way's direction, walked out of the room


class Grid:
    """A layout as a body walks it: each cell's level and floor, its props' footprints and tops, its stairs, and the
    cells `solids` (x, y, w, h each) block as well (a place's sight: PlaceRules.solids, which the game's grid adds)."""

    def __init__(self, d, solids=()):
        self.w, self.h = d["size"]
        self.lv = [[WATER if ch == "~" else int(ch) for ch in r] for r in d["levels"]]
        self.solid = [[False] * self.w for _ in range(self.h)]
        self.top = [[None] * self.w for _ in range(self.h)]
        self.stair = [[None] * self.w for _ in range(self.h)]
        for s in d["stairs"]:
            for yy in range(s["y"], s["y"] + s["h"]):
                for xx in range(s["x"], s["x"] + s["w"]):
                    self.stair[yy][xx] = s
        for p in d["props"]:
            art = TILESET["props"][p["kind"]]
            fw, fh = art["footprint"]
            base = self.lv[p["y"] + fh - 1][p["x"]]
            if not art.get("solid", True):
                continue
            for yy in range(p["y"], p["y"] + fh):
                for xx in range(p["x"], p["x"] + fw):
                    if 0 <= xx < self.w and 0 <= yy < self.h:
                        self.solid[yy][xx] = True
                        if "top" in art:
                            self.top[yy][xx] = base + art["top"]
        for x, y, w, h in solids:
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    self.solid[yy][xx] = True

    def level(self, x, y):
        if not (0 <= x < self.w and 0 <= y < self.h):
            return SOLID
        if self.top[y][x] is not None:
            return self.top[y][x]
        if self.solid[y][x]:
            return SOLID
        return self.lv[y][x]

    def floor(self, x, y):
        """A cell's floor at its centre in units (None where no body stands): TopdownRoom.cell_floor."""
        lv = self.level(x, y)
        if lv in (SOLID, WATER):
            return None
        s = self.stair[y][x] if 0 <= x < self.w and 0 <= y < self.h else None
        if s:
            k = ((s["y"] + s["h"]) * TILE - (y + 0.5) * TILE) / (s["h"] * TILE)
            return (s["from"] + (s["to"] - s["from"]) * k) * LEVEL
        return lv * LEVEL

    def reach(self, start, gaps=True):
        """Every cell a body reaches on foot from `start`: walking, stairs, drops, a jump up to HOP, and (`gaps`) a
        running jump over one tile. Without `gaps` it is what auto-path walks (TopdownRoute.reach; `parity`)."""
        seen = {start}
        q = deque([start])
        while q:
            cx, cy = q.popleft()
            h0 = self.floor(cx, cy)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cx + dx, cy + dy
                if (nx, ny) in seen:
                    continue
                h1 = self.floor(nx, ny)
                if h1 is None:
                    continue
                if h1 - h0 > HOP:
                    continue
                seen.add((nx, ny))
                q.append((nx, ny))
            # A running jump over one tile to a floor no higher than a step: over water or a drop (a gap between roofs).
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if gaps else ():
                mx, my, nx, ny = cx + dx, cy + dy, cx + 2 * dx, cy + 2 * dy
                if (nx, ny) in seen:
                    continue
                h1 = self.floor(nx, ny)
                hm = self.floor(mx, my)
                gap = self.level(mx, my) == WATER or (hm is not None and hm < h0 - STEP)
                if h1 is None or h1 - h0 > STEP or not gap:
                    continue
                seen.add((nx, ny))
                q.append((nx, ny))
        return seen


def arrive(p):
    """Where a way sets a body down coming in: its `arrive`, else a cell and a half in from its doorway or edge."""
    a = p.get("arrive")
    if a is None:
        v = DIRS[p["dir"]]
        a = [p["at"][0] - v[0] * 1.5, p["at"][1] - v[1] * 1.5]
    return a


def starts_of(d):
    """The cells a body comes into a layout at: its spawn, then where each way sets it down (the reach checks' starts)."""
    return [cell(d["spawn"])] + [cell(arrive(p)) for p in d["portals"].values()]


def side(rid):
    return common.read(rid, ROOMS)


def cell(p):
    """The cell a layout point's ground point falls in (TopdownRoom.cell_of(cell_point(p)))."""
    return (int((p[0] + 0.5) // 1), int((p[1] + 0.5) // 1))


def check(lay, d):
    """Every thing of the side-view room placed where a body can stand or reach, and reached from every way in."""
    s = side(lay.id)
    g = Grid(d)
    errs = []
    for o in s.get("objects", []):
        if o["id"] not in d["place"]:
            errs.append("object %s not placed" % o["id"])
    for p in s.get("portals", []):
        if p["id"] not in d["portals"]:
            errs.append("portal %s not placed" % p["id"])
    if len(d["spawns"]) != len(s.get("spawns", [])):
        errs.append("spawns: %d lists for %d side-view spawns" % (len(d["spawns"]), len(s.get("spawns", []))))
    ev = s.get("event", {})
    lay_ev = d.get("event", {})
    if ev.get("wave") and len(lay_ev.get("wave", [])) == 0:
        errs.append("event wave not placed")
    # Every wave, fixed and timed spawn of the event has its cells, in the side view's order (TopdownRoom.merge_def).
    for key, lay_key in (("waves", "waves"), ("fixed_spawns", "fixed"), ("timed_spawns", "timed")):
        if len(ev.get(key, [])) != len(lay_ev.get(lay_key, [])) and (ev.get(key) or lay_ev.get(lay_key)):
            errs.append("event %s: %d placed for %d" % (key, len(lay_ev.get(lay_key, [])), len(ev.get(key, []))))
    for pid, p in d["portals"].items():
        c = cell(p["at"])
        if g.floor(*c) is None:
            errs.append("portal %s at %s: no floor" % (pid, str(c)))
        v = DIRS[p["dir"]]
        bx, by = c[0] + v[0], c[1] + v[1]
        hb, hc = g.floor(bx, by), g.floor(*c)
        if hb is not None and hc is not None and hb - hc <= HOP:
            errs.append("portal %s: walking out (%s) is not stopped by a wall, the water or the room's edge" % (pid, p["dir"]))
    starts = starts_of(d)
    for st in starts:
        if g.floor(*st) is None:
            errs.append("start %s has no floor" % str(st))
    reached = [g.reach(st) for st in starts if g.floor(*st) is not None]
    things = {o["id"]: o for o in s.get("objects", [])}
    for oid, at in d["place"].items():
        c = cell(at)
        o = things.get(oid, {})
        near = [(x, y) for y in range(c[1] - 3, c[1] + 4) for x in range(c[0] - 3, c[0] + 4)
                if g.floor(x, y) is not None and (x - c[0]) ** 2 + (y - c[1]) ** 2 <= 9]
        if g.floor(*c) is None and o.get("type") not in ("fishing_spot", "rift_tear", "insect_swarm"):
            errs.append("object %s at %s: no floor (level %s)" % (oid, str(c), g.level(*c)))
        alt = g.floor(*c) if g.floor(*c) is not None else 0.0
        stand = [q for q in near if abs(g.floor(*q) - alt) <= REACH_ALT]
        for i, r in enumerate(reached):
            if not any(q in r for q in stand):
                errs.append("object %s at %s: not reached from start %s" % (oid, str(c), str(starts[i])))
    # Every way is reached from every way in by what auto-path walks (no running jump over a gap), so the tracker's go
    # button can take the body through the room.
    walked = [g.reach(st, False) for st in starts if g.floor(*st) is not None]
    for pid, p in d["portals"].items():
        c = cell(p["at"])
        for i, r in enumerate(walked):
            if c not in r:
                errs.append("portal %s: not reached by auto-path from start %s" % (pid, str(starts[i])))
    for k, pts in enumerate(d["spawns"]):
        for q in pts:
            c = cell(q)
            if g.floor(*c) is None:
                errs.append("spawn %d point %s: no floor" % (k, str(c)))
    errs += list(dict.fromkeys(check_foliage(lay, d, g)))
    errs += LIFE.check_furnish(lay.id, d, g, clear_cells(d))   # decision 43: furnishings and stations
    errs += list(dict.fromkeys(check_traverse(s, d, g, walked)))
    if errs:
        raise SystemExit("%s:\n  " % lay.id + "\n  ".join(errs))


# -------------------------------------------------------------------- T1: the side view's traversal on the grid
# docs/architecture/topdown_mechanics.md. A layout's `traverse` puts the side view's movers, updrafts and climbables on
# the grid (TopdownTraverse reads it), each under its side-view id; `stage` sets a room event's side-view points on
# cells (WorldRoomEvents). Neither changes what the Grid walks: a raft, an updraft or a climb is a way more, never the
# only one (auto-path and every reach check above walk the room without them).
CLIMBABLES = ("vine", "ladder", "rope", "chain")


def raft_cells(r, off):
    """The cells a raft covers with its north-west corner at its rest cell plus `off` (fractions: every cell it
    touches)."""
    w, h = r.get("size", [2, 2])
    x, y = r["at"][0] + off[0], r["at"][1] + off[1]
    return [(cx, cy) for cy in range(math.floor(y), math.ceil(y + h - 1e-6)) for cx in range(math.floor(x), math.ceil(x + w - 1e-6))]


def raft_samples(r):
    """The raft's offsets along its whole run, every quarter cell: its rest, the path's points, and back to the rest for
    a loop (a pingpong or a trigger trip comes back along the same way)."""
    pts = [(0.0, 0.0)] + [(float(q[0]), float(q[1])) for q in r.get("path", [])]
    if r.get("mode", "pingpong") == "loop":
        pts.append((0.0, 0.0))
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(math.ceil(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 4)))
        out += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(1, n + 1)]
    return out


def check_traverse(s, d, g, walked):
    errs = []
    side_movers = {str(m.get("surface", "")) for m in s.get("movers", [])}
    side_volumes = {str(v.get("id", "")): v for v in s.get("volumes", [])}
    side_climbs = {str(c.get("id", "")) for c in s.get("climbables", [])}
    covered = {}
    for p in d["props"]:
        fw, fh = TILESET["props"][p["kind"]]["footprint"]
        for yy in range(p["y"], p["y"] + fh):
            for xx in range(p["x"], p["x"] + fw):
                covered[(xx, yy)] = p["kind"]
    for r in d.get("traverse", []):
        kind, tid = r["kind"], r["id"]
        if kind == "raft":
            if tid not in side_movers:
                errs.append("raft %s: no mover of that surface in the side-view room" % tid)
            level = float(r.get("level", 0)) * LEVEL
            for off in raft_samples(r):
                for c in raft_cells(r, off):
                    if not (0 <= c[0] < g.w and 0 <= c[1] < g.h) or g.lv[c[1]][c[0]] != WATER:
                        errs.append("raft %s covers %s, not open water" % (tid, str(c)))
                    elif c in covered:
                        errs.append("raft %s runs over a %s at %s" % (tid, covered[c], str(c)))
            ends = [(0.0, 0.0)]   # where it waits: its rest, and the far end of a pingpong or a trigger's trip
            if r.get("mode", "pingpong") != "loop" and r.get("path"):
                ends.append(tuple(r["path"][-1]))
            for off in ends:
                cells = set(raft_cells(r, off))
                beside = {(cx + dx, cy + dy) for cx, cy in cells for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))} - cells
                if not any(g.floor(*q) is not None and abs(g.floor(*q) - level) <= STEP and any(q in w for w in walked) for q in beside):
                    errs.append("raft %s at offset %s: no landing a body walks onto it from" % (tid, str(off)))
        elif kind == "updraft":
            v = side_volumes.get(tid, {})
            if str(v.get("kind", "")) != "updraft":
                errs.append("updraft %s: no updraft volume of that id in the side-view room" % tid)
            x, y, w, h = r["rect"]
            if x < 0 or y < 0 or x + w > g.w or y + h > g.h or float(r.get("top", 0)) <= 0:
                errs.append("updraft %s: its rect %s is outside the room or it lifts nowhere" % (tid, str(r["rect"])))
        elif kind == "lift":
            if tid not in side_movers:
                errs.append("lift %s: no mover of that surface in the side-view room" % tid)
            base = float(r.get("level", 0))
            path = r.get("path", [])
            ends = [(0.0, 0.0, base)] + ([] if not path else [(float(path[-1][0]), float(path[-1][1]), base + float(path[-1][2]) if len(path[-1]) > 2 else base)])
            for c in raft_cells(r, (0.0, 0.0)):
                fl = g.floor(*c) if 0 <= c[0] < g.w and 0 <= c[1] < g.h else None
                if fl is None or fl > base * LEVEL + 0.5:
                    errs.append("lift %s: its cell %s at rest is no floor under its deck" % (tid, str(c)))
            for dx, dy, lv in ends:
                cells = set(raft_cells(r, (dx, dy)))
                beside = {(cx + ex, cy + ey) for cx, cy in cells for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1))} - cells
                if not any(g.floor(*q) is not None and abs(g.floor(*q) - lv * LEVEL) <= STEP for q in beside):
                    errs.append("lift %s: no landing at its level %g at offset %s" % (tid, lv, str((dx, dy))))
        elif kind in ("crumble", "current", "flood"):
            want = {"crumble": "crumble", "current": "current", "flood": "rising_water"}[kind]
            v = side_volumes.get(tid, {})
            if str(v.get("kind", "")) != want:
                errs.append("%s %s: no %s volume of that id in the side-view room" % (kind, tid, want))
            x, y, w, h = r["rect"]
            if x < 0 or y < 0 or x + w > g.w or y + h > g.h:
                errs.append("%s %s: its rect %s is outside the room" % (kind, tid, str(r["rect"])))
            elif kind == "crumble" and any(g.floor(xx, yy) is not None and g.floor(xx, yy) >= float(r.get("level", 0)) * LEVEL
                                           for yy in range(y, y + h) for xx in range(x, x + w)):
                errs.append("crumble %s: its boards at level %s lie over no pit" % (tid, r.get("level", 0)))
        elif kind == "bounce":
            v = side_volumes.get(tid, {})
            if str(v.get("kind", "")) != "bounce":
                errs.append("bounce %s: no bounce volume of that id in the side-view room" % tid)
            x, y, w, h = r["rect"]
            cells = [(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)]
            floors = {g.floor(*c) for c in cells}
            if None in floors or len(floors) != 1 or not any(c in wk for c in cells for wk in walked):
                errs.append("bounce %s: its cells %s are not one floor a body reaches" % (tid, str(r["rect"])))
        elif kind in CLIMBABLES:
            if tid not in side_climbs:
                errs.append("%s %s: no climbable of that id in the side-view room" % (kind, tid))
            foot, top = tuple(r["foot"]), tuple(r["top"])
            ff, ft = g.floor(*foot), g.floor(*top)
            if abs(foot[0] - top[0]) + abs(foot[1] - top[1]) != 1:
                errs.append("%s %s: its foot %s and top %s are not side by side" % (kind, tid, str(foot), str(top)))
            elif ff is None or ft is None or ft - ff < LEVEL:
                errs.append("%s %s: its top %s is not a level or more over its foot %s" % (kind, tid, str(top), str(foot)))
            elif not all(foot in w for w in walked):
                errs.append("%s %s: its foot %s is not reached on foot from every way in" % (kind, tid, str(foot)))
    lanes = {c for p in d["portals"].values() for c in portal_lane(p)}
    for eid, cells in d.get("stage", {}).items():
        for q in cells:
            c = cell(q)
            if g.floor(*c) is None or not all(c in w for w in walked) or c in lanes:
                errs.append("stage %s: %s is not open ground reached from every way, off the ways' lanes" % (eid, str(c)))
    return errs


# -------------------------------------------------------------------- Terrain v2's third part: foliage and decor
# docs/redesign/art_bible.md "Foliage and decor": the big pieces (trees, bamboo, bushes, hedges, fences, rocks, a log, a
# wayside shrine, potted plants, tall grass, cattails, ferns, lotus pads) are hand-placed per room, framing its paths and
# edges; the ground cover between them is the room view's scatter (TopdownFoliage). A tree's trunk blocks, its canopy
# does not; a walk-through plant never blocks.
FOLIAGE = {k for k, v in TILESET["props"].items() if v.get("foliage")}
PLANTED = set("gfbmr")                    # what a plant or a garden piece stands on: meadow, flowers, bed, marsh, rock
ANYWHERE = {"pot_bonsai", "pot_orchid"}   # a potted plant stands on any floor (a hall's, a deck, the paving)
ON_WATER = {"lotus_pads"}
WADING = {"cattails"}                     # stands on the land it grows on or in the shallows
FLOODED = {k for k, v in TILESET["paint"].items() if v.get("flood")}   # R2: floors under shallow water (a wading plant's)
DECOR = common.read("decor", OUT)


def clear_cells(d):
    """The cells the room view keeps clear of ground cover (TopdownFoliage.clear_cells, the same rules): round the
    spawn, every spot, each way out's lane, the heads and feet of the stairs and the foes' spawn points."""
    ring = DECOR["clear"]
    out = set()

    def add(c, n):
        for y in range(c[1] - n, c[1] + n + 1):
            for x in range(c[0] - n, c[0] + n + 1):
                out.add((x, y))
    add(cell(d["spawn"]), ring["spawn"])
    for at in d["place"].values():
        add(cell(at), ring["place"])
    for p in d["portals"].values():
        for c in portal_lane(p):
            add(c, ring["portal"])
    for st in d["stairs"]:
        for x in range(st["x"] - 1, st["x"] + st["w"] + 1):
            out.add((x, st["y"] + st["h"]))
            out.add((x, st["y"] - 1))
    lay_ev = d.get("event", {})
    foes = [q for lst in d.get("spawns", []) for q in lst] + lay_ev.get("wave", []) + lay_ev.get("fixed", []) + \
        [q for lst in lay_ev.get("waves", []) for q in lst] + lay_ev.get("timed", [])
    for q in foes:
        add(cell(q), ring["foe"])
    return out


def portal_lane(p):
    """A way out's lane: the cells from its doorway or edge cell in to where one arrives, as wide as its span."""
    at = cell(p["at"])
    v = DIRS[p["dir"]]
    arrive = cell(p["arrive"]) if "arrive" in p else (at[0] - v[0] * 2, at[1] - v[1] * 2)
    half = int(-(-float(p.get("span", 2)) * 0.5 // 1))
    side = (abs(v[1]), abs(v[0]))
    steps = max(abs(arrive[0] - at[0]), abs(arrive[1] - at[1]))
    return [(at[0] - v[0] * k + side[0] * s, at[1] - v[1] * k + side[1] * s) for k in range(steps + 2) for s in range(-half, half + 1)]


_SCENES = None


def scene_walks(rid, d):
    """The cells the staged scenes (data/scenes.json) walk their people along in this room: no trunk or bush there."""
    global _SCENES
    if _SCENES is None:
        _SCENES = common.rows("scenes") if os.path.exists(os.path.join(common.DATA, "scenes.json")) else []
    out = set()
    for sc in _SCENES:
        if sc.get("room") != rid:
            continue
        pos = {}
        for name, a in sc.get("actors", {}).items():
            if "at" in a:
                pos[name] = tuple(a["at"])
            elif a.get("object") in d["place"]:
                pos[name] = tuple(d["place"][a["object"]])
        for st in sc.get("steps", []):
            if st.get("do") != "move" or st.get("actor") not in pos:
                continue
            for to in st["to"]:
                if isinstance(to, dict):
                    break          # decision 45: beside something where it stands (where the fight is): no fixed walk
                a, b = pos[st["actor"]], tuple(to)
                n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 2) + 1
                for k in range(n + 1):
                    t = k / n
                    out.add(cell((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)))
                pos[st["actor"]] = b
    return out


def check_foliage(lay, d, g):
    """The foliage kit's rules: each piece on ground it grows on (a lotus pad on the water), off the paths and every
    kept-clear cell (the spawn, spots, ways' lanes, stairs), off the scenes' walks and other props; a tree's canopy
    never hides a person, a thing or a way behind it."""
    errs = []
    clear = clear_cells(d)
    walks = scene_walks(lay.id, d)
    taken = {}
    for i, p in enumerate(d["props"]):
        fw, fh = TILESET["props"][p["kind"]]["footprint"]
        for y in range(p["y"], p["y"] + fh):
            for x in range(p["x"], p["x"] + fw):
                if (x, y) in taken and (p["kind"] in FOLIAGE or taken[(x, y)] in FOLIAGE):
                    errs.append("%s at %s overlaps %s" % (p["kind"], str((x, y)), taken[(x, y)]))
                taken[(x, y)] = p["kind"]
    spots = []
    for oid, at in d["place"].items():
        c = cell(at)
        fl = g.floor(*c)
        lv = (fl or 0.0) / 32.0
        feet = ((at[0] + 0.5) * 16, (at[1] + 0.5) * 16 - lv * 16)
        key = (c[1] + 1) * 16 + 0.25 if lv > 0 else (at[1] + 0.5) * 16
        spots.append((oid, (feet[0] - 6, feet[1] - 34, 12, 34), key))
    for pid, p in d["portals"].items():
        for c in portal_lane(p):
            if 0 <= c[0] < g.w and 0 <= c[1] < g.h:
                lv = max(0.0, (g.floor(*c) or 0.0) / 32.0)
                spots.append(("way " + pid, (c[0] * 16, c[1] * 16 - lv * 16, 16, 16), (c[1] + 0.5) * 16))
    for p in d["props"]:
        kind = p["kind"]
        if kind not in FOLIAGE:
            continue
        art = TILESET["props"][kind]
        fw, fh = art["footprint"]
        for y in range(p["y"], p["y"] + fh):
            for x in range(p["x"], p["x"] + fw):
                where = "%s at %s" % (kind, str((x, y)))
                if not (0 <= x < g.w and 0 <= y < g.h):
                    errs.append(where + ": outside the room")
                    continue
                water = g.lv[y][x] == WATER
                if kind in ON_WATER:
                    if not water:
                        errs.append(where + ": a water plant on land")
                    continue
                if kind in WADING and (water or d["paint"][y][x] in FLOODED):
                    continue
                if water or g.stair[y][x]:
                    errs.append(where + ": on the water or the stairs")
                elif kind not in ANYWHERE and d["paint"][y][x] not in PLANTED:
                    errs.append(where + ": on '%s' (a path, paving or a built floor)" % d["paint"][y][x])
                if (x, y) in clear:
                    errs.append(where + ": on a kept-clear cell (the spawn, a spot, a way's lane or a stair's head or foot)")
                if art.get("solid", True) and (x, y) in walks:
                    errs.append(where + ": on a staged scene's walk")
        c = art.get("canopy")
        if not c:
            continue
        base = g.lv[p["y"] + fh - 1][p["x"]]
        sw = (p["x"] * 16, (p["y"] + fh) * 16 - max(0, base) * 16)
        bx = sw[0] + c["at"][0] + c["box"][0]
        by = sw[1] + c["at"][1] + c["box"][1]
        box = (bx, by, c["box"][2], c["box"][3])
        key = (p["y"] + fh) * 16 + 0.5
        for oid, r, k in spots:
            if k < key and r[0] < box[0] + box[2] and box[0] < r[0] + r[2] and r[1] < box[1] + box[3] and box[1] < r[1] + r[3]:
                errs.append("%s at %s: its canopy hides %s" % (kind, str((p["x"], p["y"])), oid))
    return errs


# ==================================================================== the rooms
# E1 (audit 45 §6.1): every room is a spec of the room engine, tools/content/rooms/specs/<zone>.py, compiled to its Layout
# by tools/content/rooms/engine.py (docs/architecture/room_engine.md). A hand function returning a Layout may still be
# listed here (a review room, a one-off); none is today.
LAYOUTS = []


# -------------------------------------------------------------------- audit 45: the Grid against the game's own
def godot():
    """The Godot the parity asks: $GODOT (tools/run_tests.sh passes it on), else `godot` on the PATH; None if neither."""
    exe = os.environ.get("GODOT") or "godot"
    return exe if os.path.isfile(exe) else shutil.which(exe)


def place_solids():
    """The cells data/places.json's places block, by room (PlaceRules.solids: the game's grid blocks them too)."""
    out = {}
    for r in common.rows("places"):
        out.setdefault(r["room"], []).extend(r.get("solid", []))
    return out


def parity(exe=None):
    """The grid's walking rules exist twice, here and in the game (TopdownRoom, TopdownRoute), so the rooms' checks run
    without Godot. This holds them together (audit 45, DUP-10): tools/data/grid_parity.tscn reads every layout of
    data/topdown/ as the game does, and each must match this Grid cell for cell: every cell's floor (a wall, the water or
    its height, the places' solid cells blocked), and from the spawn and every way in the cells auto-path reaches (the
    tracker's go button: TopdownRoute.reach against Grid.reach without gaps). Without a Godot it says it did not run."""
    exe = exe or godot()
    if exe is None:
        return "grid parity with the game not run: no Godot (set GODOT)"
    solids = place_solids()
    grids, ask = {}, {}
    for f in sorted(os.listdir(OUT)):
        d = common.read(f, OUT) if f.endswith(".json") else {}
        if "levels" in d and "portals" in d:
            g = grids[d["id"]] = Grid(d, solids.get(d["id"], ()))
            ask[d["id"]] = [list(st) for st in starts_of(d) if g.floor(*st) is not None]
    with tempfile.TemporaryDirectory() as tmp:
        q, a = os.path.join(tmp, "ask.json"), os.path.join(tmp, "answer.json")
        with open(q, "w", encoding="utf-8") as f:
            json.dump({"rooms": ask}, f)
        run = subprocess.run([exe, "--headless", "--path", ROOT, "res://tools/data/grid_parity.tscn", "--", q, a],
                             capture_output=True, text=True, timeout=1200)
        if run.returncode != 0 or not os.path.exists(a):
            raise SystemExit("grid parity: tools/data/grid_parity.tscn did not answer (%s, exit %d):\n%s"
                             % (exe, run.returncode, "\n".join((run.stdout + run.stderr).strip().splitlines()[-12:])))
        game = common.read(a, tmp)
    errs = []
    for rid, g in grids.items():
        mine = game.get(rid, {})
        if mine.get("size") != [g.w, g.h]:
            errs.append("%s: the game reads it %s, the Grid %s" % (rid, mine.get("size"), [g.w, g.h]))
            continue
        off = [(x, y) for y in range(g.h) for x in range(g.w)
               if (g.floor(x, y) is None) != (mine["floor"][y][x] is None)
               or (g.floor(x, y) is not None and abs(g.floor(x, y) - mine["floor"][y][x]) > 1e-3)]
        if off:
            errs.append("%s: %d cells stand otherwise in the game, first %s (Grid %s, game %s)"
                        % (rid, len(off), off[0], g.floor(*off[0]), mine["floor"][off[0][1]][off[0][0]]))
        for st, bits in zip(ask[rid], mine["reach"]):
            ours = g.reach(tuple(st), False)
            theirs = {(k % g.w, k // g.w) for k, ch in enumerate(bits) if ch == "1"}
            if ours != theirs:
                errs.append("%s from %s: auto-path reaches %d cells the Grid does not %s, the Grid %d it does not %s"
                            % (rid, st, len(theirs - ours), sorted(theirs - ours)[:4], len(ours - theirs), sorted(ours - theirs)[:4]))
    common.fail("grid parity (tools/data/grid_parity.tscn against topdown_rooms.Grid)", errs)
    return "grid parity with the game: %d layouts, %d starts, every cell" % (len(grids), sum(len(v) for v in ask.values()))


def layouts():
    """Every room's Layout: the room engine's specs compiled (E1, tools/content/rooms/: one spec a room, grouped by zone in
    specs/), after the hand functions still left here."""
    tools = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if tools not in sys.path:
        sys.path.append(tools)
    from content.rooms import engine, specs   # imported here: the engine imports this module for its Layout
    made = set()
    for make in LAYOUTS:
        lay = make()
        made.add(lay.id)
        yield lay
    for spec in specs.all_specs():
        if spec["id"] not in made:
            try:
                yield engine.compile_room(spec)
            except engine.SpecError as e:
                raise SystemExit(str(e))


def build():
    failed = []
    for lay in layouts():
        LIFE.dress(lay)            # decision 43 (tools/data/topdown_life.py): an interior's furnishings, a station's props
        d = lay.dict()
        LIFE.extend(lay.id, d)     # and the land past the room's edge the camera may show
        try:
            check(lay, d)
        except SystemExit as e:
            failed.append(str(e))
            continue
        body = {"schema_version": 1}
        body.update(d)
        emit(os.path.join(OUT, lay.id + ".json"), json.dumps(body, indent=1, ensure_ascii=False) + "\n")
    if failed:
        raise SystemExit("\n".join(failed))
    LIFE.build()                   # decision 43: data/topdown/life.json, its work spots checked on these layouts
    if common.RUN.check:
        return parity()            # audit 45: the game walks the layouts as this Grid does


if __name__ == "__main__":
    raise SystemExit(run_cli(build))
