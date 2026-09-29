"""Redesign Phase 4 (docs/redesign_top_down_plan.md, "As built: Phase 4", both parts): the tutorial area's rooms and
chapter 2's stretch (both sects' Entry Trials and grounds, the Marsh Edge) redrawn for the top-down world, one layout per
room in data/topdown/<room id>.json, read by TopdownRoom (scripts/topdown).

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

Deterministic: `python3 tools/data/topdown_rooms.py` writes the files, `--check` proves they are current. Each layout
is checked as it is built: every object, NPC, portal and spawn of its side-view room is placed on a cell a body can
stand on (or, for a thing on the water, within reach of one), and each is reached on foot from every way in (walking,
stairs, drops and a jump one level up, the TopdownMotor's rules; tests/topdown_tutorial.gd repeats it in the game);
every way is reached by auto-path's own rules too (no running jump over a gap), so the tracker's go button crosses it.
"""
import json
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "data", "topdown")
ROOMS = os.path.join(ROOT, "data", "rooms")
TILESET = json.load(open(os.path.join(OUT, "proto_tileset.json")))
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
        return out


# -------------------------------------------------------------------- the rules a body walks by (TopdownRoom's)
class Grid:
    def __init__(self, d):
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

    def level(self, x, y):
        if not (0 <= x < self.w and 0 <= y < self.h):
            return SOLID
        if self.top[y][x] is not None:
            return self.top[y][x]
        if self.solid[y][x]:
            return SOLID
        return self.lv[y][x]

    def floor(self, x, y):
        """A cell's floor at its centre in units (None where no body stands)."""
        lv = self.level(x, y)
        if lv in (SOLID, WATER):
            return None
        s = self.stair[y][x] if 0 <= x < self.w and 0 <= y < self.h else None
        if s:
            k = ((s["y"] + s["h"]) * 32.0 - (y + 0.5) * 32.0) / (s["h"] * 32.0)
            return (s["from"] + (s["to"] - s["from"]) * k) * 32.0
        return lv * 32.0

    def reach(self, start, gaps=True):
        """Every cell a body reaches on foot from `start`: walking, stairs, drops, a jump one level up, and (`gaps`) a
        running jump over one tile. Without `gaps` it is what auto-path walks (TopdownRoom.find_path)."""
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
                if h1 - h0 > 32.5:
                    continue
                seen.add((nx, ny))
                q.append((nx, ny))
            # A running jump over one tile to a floor no higher: over water or a drop (a gap between roofs).
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if gaps else ():
                mx, my, nx, ny = cx + dx, cy + dy, cx + 2 * dx, cy + 2 * dy
                if (nx, ny) in seen:
                    continue
                h1 = self.floor(nx, ny)
                hm = self.floor(mx, my)
                gap = self.level(mx, my) == WATER or (hm is not None and hm < h0 - 8.0)
                if h1 is None or h1 - h0 > 8.0 or not gap:
                    continue
                seen.add((nx, ny))
                q.append((nx, ny))
        return seen


def side(rid):
    return json.load(open(os.path.join(ROOMS, rid + ".json")))


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
    starts = [cell(d["spawn"])]
    for pid, p in d["portals"].items():
        a = p.get("arrive")
        if a is None:
            v = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0)}[p["dir"]]
            a = [p["at"][0] - v[0] * 1.5, p["at"][1] - v[1] * 1.5]
        starts.append(cell(a))
        c = cell(p["at"])
        if g.floor(*c) is None:
            errs.append("portal %s at %s: no floor" % (pid, str(c)))
        v = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0)}[p["dir"]]
        bx, by = c[0] + v[0], c[1] + v[1]
        hb, hc = g.floor(bx, by), g.floor(*c)
        if hb is not None and hc is not None and hb - hc <= 32.5:
            errs.append("portal %s: walking out (%s) is not stopped by a wall, the water or the room's edge" % (pid, p["dir"]))
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
        stand = [q for q in near if abs(g.floor(*q) - alt) <= 48]
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
    if errs:
        raise SystemExit("%s:\n  " % lay.id + "\n  ".join(errs))


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
DECOR = json.load(open(os.path.join(OUT, "decor.json")))


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
    v = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0)}[p["dir"]]
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
        path = os.path.join(ROOT, "data", "scenes.json")
        _SCENES = json.load(open(path)).get("entries", []) if os.path.exists(path) else []
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
                if kind in WADING and water:
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
def fishers_hut():
    """Aunt Ping's hut: a wooden floor inside plastered walls, the loft over the east end up a short stair, Aunt Ping
    by the hearth, the tea on the table, the door in the front wall."""
    r = Layout("lf_fishers_hut", 20, 13, 0, "w")
    r.walls(0, 0, 20, 13)
    r.rect(9, 12, 2, 1, 0, "w")                   # the doorway in the front sill
    r.rect(13, 1, 6, 2, 2, "w")                   # the loft
    r.stair(13, 3, 2, 2, 0, 2, "w")
    r.prop("crates", 9, 6)                        # the table (a floor one level up)
    r.prop("barrel", 1, 1)
    r.prop("barrel", 2, 1)
    r.prop("lantern", 1, 10)
    r.prop("lantern", 18, 10)
    r.green(("pot_orchid", 1, 5), ("pot_bonsai", 18, 8))   # foliage (decision 40): Aunt Ping's potted plants
    r.spawn = [4, 4]
    r.at("npc_aunt_ping", 6, 6)
    r.at("tea_table", 9.5, 6)
    r.at("net", 16, 5)
    r.at("lu_float", 15, 1)
    r.at("tea_loft", 17, 1)
    r.way("exit", 9.5, 12, "s", [9.5, 10.5], 2)
    return r


def village(rid="lf_village", night=False):
    """Lotus Ferry: Home Lane in the west (the Fisher's Hut, Granny Liu's hut, the West Gate), the paved square in the
    middle (Uncle Guo's stump and dummy, the shrine, the spring, the board, Old Ma's store, the hall and the Ferry Inn
    whose roofs the kite is caught on), the Ferry Docks in the east (the pier, Lu's boat, the watch-tower and its bell,
    the East Gate), a grassy terrace behind the houses and the river along the south."""
    w = 48 if night else 72
    r = Layout(rid, w, 40, 0, "g")
    r.rect(0, 0, w, 10, 1, "g")                   # the terrace behind the houses
    r.rect(0, 0, w, 3, 2, "r")                    # rock above it
    r.water(0, 34, w, 6)                          # the river
    r.rect(0, 32, w, 2, 0, "d")                   # the towpath along the bank
    r.hline(0, w - 1, 20, 3, "d")                 # the lane through the village
    r.rect(22, 15, 26, 15, 0, "p")                # the square's paving
    r.stair(12, 8, 3, 2, 0, 1, "s")               # up to the terrace from Home Lane
    r.stair(33, 8, 3, 2, 0, 1, "s")               # and from the square
    for x in (3, 20, 27, 41):
        r.prop("willow", x, 5)
    r.prop("bamboo", 8, 4)
    r.prop("bamboo", 9, 5)
    hut = r.prop("house", 4, 11)                  # the Fisher's Hut: door at x 6-7
    r.prop("crates", 10, 13)                      # the way onto its roof
    granny = r.prop("house", 15, 11)              # Granny Liu's Herb Hut: door at x 17-18
    store = r.prop("storehouse", 38, 11)          # Old Ma's Store: door at x 39-40
    for b in (hut, granny):
        r.door_path(b, 20)                        # a path from each door down to the lane
    r.door_path(store, 15, "p")
    r.rect(1, 23, 4, 2, None, "f")                # flower beds along Home Lane
    r.rect(9, 24, 5, 2, None, "f")
    r.rect(1, 12, 2, 2, None, "f")
    r.prop("lantern", 23, 15)
    r.prop("lantern", 46, 15)
    r.prop("barrel", 36, 13)
    r.prop("bamboo", 19, 25)
    r.prop("bamboo", 20, 26)
    for x in (2, 8, 14, 26, 33, 44):
        r.prop("reeds", x, 33)
    r.prop("lotus", 10, 36)
    r.prop("lotus", 30, 37)
    # Foliage (decision 40): big trees along the terrace and round the square, bushes against the houses, a fence and
    # flowers along Home Lane, willows and tall grass by the river, lotus pads on it.
    r.green(("tree_camphor", 24, 6), ("tree_plum", 30, 5), ("tree_maple", 46, 6), ("tree_camphor", 53, 5),
            ("tree_ribbons", 61, 6), ("tree_willow", 68, 5), ("bamboo_grove", 0, 4), ("bamboo_grove", 36, 4),
            ("bush", 16, 9), ("bush_azalea", 22, 9), ("bush_wide", 38, 9), ("bush", 50, 9), ("bush_azalea", 57, 9),
            ("hedge_2", 1, 9), ("bush", 64, 9),
            ("tree_camphor", 29, 12), ("bush_wide", 32, 13), ("bush_azalea", 26, 13), ("bush", 43, 12),
            ("bush_azalea", 45, 13), ("bush_wide", 62, 12), ("bush", 60, 14),
            ("bush_azalea", 2, 15), ("bush", 10, 15), ("bush_azalea", 14, 15), ("bush", 21, 17),
            ("fence_4", 5, 23), ("fence_3", 14, 23), ("tree_peach", 17, 27), ("tree_willow", 4, 29),
            ("tall_grass", 1, 26), ("tall_grass", 7, 30), ("ferns", 12, 26), ("rock_mossy", 20, 30),
            ("tree_willow", 40, 31), ("tall_grass", 26, 30), ("bush_wide", 30, 30), ("tall_grass", 35, 31),
            ("tree_camphor", 51, 17), ("bush", 49, 15), ("bush_azalea", 57, 15), ("rock_small", 63, 19),
            ("lotus_pads", 18, 35), ("lotus_pads", 40, 36), ("lotus_pads", 3, 37), ("cattails", 24, 34), ("cattails", 46, 34), ("cattails", 12, 34))
    if night:
        r.spawn = [30, 22]
        r.at("hut_refuge", 6.5, 15)
        r.at("npc_ping_night", 8.5, 16.5)          # Aunt Ping at the hut's door with her lamp
        r.at("npc_dou_night", 44, 25)
        r.at("npc_granny_night", 18, 23)
        r.at("npc_ma_night", 38, 18)
        # The Hollow Night's event (world.py, in its order): two minnows about each villager; the river's minnows up the
        # bank; the lane's schools from both ends once the villagers are in; the eel rising mid-river off the square.
        r.event = {"fixed": [[42, 26.5], [46, 26], [16, 25], [20.5, 24.5], [36, 20], [40.5, 20]],
                   "waves": [[[5, 31], [15, 32], [25, 31], [35, 32], [44, 31]],
                             [[1, 20.5], [1.5, 22], [46.5, 20.5], [46, 22], [24, 31], [32, 31]]],
                   "timed": [[30, 36.5]]}
        return r
    hall = r.prop("house", 48, 11)                # the village hall
    inn = r.prop("house", 55, 11)                 # the Ferry Inn, a tile's jump beyond the hall
    r.prop("crates", 46, 13)                      # the way onto the hall's roof
    r.rect(48, 24, 24, 8, 0, "w")                 # the docks' boards
    r.rect(58, 34, 3, 4, 0, "w")                  # the pier
    r.prop("boat", 61, 36)
    r.rect(66, 15, 4, 5, 3, "s")                  # the watch-tower's top
    r.stair(66, 20, 2, 4, 0, 3, "s")
    r.prop("lantern_red", 50, 24)
    r.prop("lantern_red", 70, 24)
    r.prop("barrel", 63, 25)
    r.prop("crates", 64, 30)
    r.spawn = [8, 17]
    r.door("hut_door", hut)
    r.door("granny_door", granny)
    r.door("store_door", store)
    r.way("west_gate", 0, 21, "w", [2, 21], 3)
    r.way("east_gate", 71, 21, "e", [69, 21], 3)
    r.way("boat", 60, 36, "e", [59, 36], 1.5)
    r.at("sign_home", 2, 18)
    r.at("pings_ladle", 8, 11)                    # on the Fisher's Hut's roof
    r.at("npc_aunt_ping_lane", 11, 17)
    r.at("npc_washer_mei", 14, 31)
    r.at("spring_village", 24, 26)
    r.at("shrine_village", 26, 16)
    r.at("npc_uncle_guo", 30, 22)
    r.at("stump_guo", 31, 26)
    r.at("dummy_guo", 34, 26)
    r.at("board_village", 36, 16)
    r.at("storage_village", 43, 16)
    r.at("npc_little_dou", 44, 24)
    r.at("cook_village", 46, 28)
    r.at("kite", 58, 12)                          # on the Ferry Inn's roof
    r.at("npc_shen_lian_npc", 52, 27)
    r.at("npc_lu_boatman", 56, 28)
    r.at("npc_fisher_wen", 64, 28)
    r.at("fish_docks", 59, 37)
    r.at("tower_bell", 68, 16)
    r.at("gull_nest", 69, 15)
    return r


def village_night():
    """Lotus Ferry at Night: Home Lane and the square as by day, the hut's door open, the villagers out in the lane
    and the Hollow things coming up out of the river."""
    return village("lf_village_night", True)


def old_ma_store():
    """Old Ma's Store: the counter across the shop with Old Ma behind it, the soup jars up in the loft, the sacks by the
    west wall with the old net under the shelf."""
    r = Layout("lf_old_ma_store", 18, 12, 0, "w")
    r.walls(0, 0, 18, 12)
    r.rect(8, 11, 2, 1, 0, "w")
    r.rect(1, 1, 5, 2, 2, "w")                    # the loft
    r.stair(4, 3, 2, 2, 0, 2, "w")
    r.prop("crates", 10, 5)                       # the counter
    r.prop("crates", 12, 5)
    r.prop("barrel", 1, 7)
    r.prop("barrel", 1, 8)
    r.prop("barrel", 16, 1)
    r.prop("lantern", 16, 9)
    r.green(("pot_bonsai", 16, 4), ("pot_orchid", 7, 1))   # foliage (decision 40): potted plants
    r.spawn = [8, 9]
    r.at("npc_old_ma", 12, 3)
    r.at("soup_loft", 2, 1)
    r.at("old_net_floor", 3, 9)
    r.way("exit", 8.5, 11, "s", [8.5, 9.5], 2)
    return r


def granny_liu_hut():
    """Granny Liu's Herb Hut: her table by the hearth, the family altar (the shrine) by the east wall, the herb loft over
    the west end with its jars and a bundle of willow moss."""
    r = Layout("lf_granny_liu_hut", 18, 12, 0, "w")
    r.walls(0, 0, 18, 12)
    r.rect(8, 11, 2, 1, 0, "w")
    r.rect(1, 1, 6, 2, 2, "w")                    # the herb loft
    r.stair(5, 3, 2, 2, 0, 2, "w")
    r.prop("crates", 8, 6)                        # her table
    r.prop("incense", 15, 4)
    r.prop("barrel", 16, 1)
    r.prop("barrel", 16, 2)
    r.prop("lantern", 1, 9)
    r.green(("pot_orchid", 16, 8), ("pot_bonsai", 12, 1))  # foliage (decision 40): potted plants
    r.spawn = [8, 9]
    r.at("npc_granny_liu", 6, 6)
    r.at("shrine_granny", 14, 5)
    r.at("jar_1", 1, 1)
    r.at("jar_2", 2, 1)
    r.at("moss_bundle", 4, 1)
    r.way("exit", 8.5, 11, "s", [8.5, 9.5], 2)
    return r


def lu_boat():
    """Lu's Boat: the deck on the river at night, the gangway back to the docks, the spring's breath at the bow where
    the first breakthrough is made, Lu by the cabin and the star mat on its roof."""
    r = Layout("lf_lu_boat", 24, 14, WATER, "~")
    r.rect(3, 4, 18, 6, 0, "w")                   # the deck
    r.rect(0, 6, 3, 2, 0, "w")                    # the gangway
    r.prop("storehouse", 14, 4)                   # the cabin
    r.prop("crates", 12, 6)                       # up onto its roof
    r.prop("lantern_red", 3, 4)
    r.prop("lantern_red", 20, 9)
    r.prop("barrel", 20, 4)
    r.prop("lotus", 1, 11)
    r.prop("lotus", 18, 1)
    r.prop("lotus", 8, 12)
    # Foliage (decision 40): a potted pine on the deck, lotus pads round the boat.
    r.green(("pot_bonsai", 19, 8), ("lotus_pads", 4, 1), ("lotus_pads", 12, 11), ("lotus_pads", 21, 11))
    r.spawn = [7, 8]
    r.at("npc_lu_boat", 10, 8)
    r.at("boat_spring", 7, 7)
    r.at("star_mat", 16, 4)
    r.way("deck", 0, 6.5, "w", [2, 6.5], 2)
    return r


def reed_shallows():
    """The Reed Shallows: a grassy shore under a rock ridge, the path from the East Gate along it, the crabs on the
    flats, the rats round the herbs in the middle, Old Snapper by the far herbs, the jetty to fish from and the river."""
    r = Layout("lf_reed_shallows", 64, 30, 0, "g")
    r.rect(0, 0, 64, 4, 2, "r")                   # the rock ridge
    r.rect(0, 4, 64, 5, 1, "g")                   # the grassy bank above the flats
    r.stair(20, 9, 3, 2, 0, 1, "s")
    r.stair(50, 9, 3, 2, 0, 1, "s")
    r.hline(0, 63, 13, 3, "d")                    # the path along the shore
    r.water(0, 23, 64, 7)                         # the river
    r.rect(26, 22, 3, 3, 0, "w")                  # the jetty
    r.rect(40, 21, 8, 2, 0, "d")                  # a sandbar
    for x in (3, 9, 15, 33, 37, 45, 52, 58):
        r.prop("reeds", x, 22)
    r.prop("reeds", 30, 21)
    r.prop("willow", 12, 5)
    r.prop("willow", 48, 5)
    r.prop("shrub", 30, 6)
    r.prop("shrub", 60, 6)
    r.prop("lotus", 34, 25)
    r.prop("lotus", 54, 26)
    # Foliage (decision 40): trees along the grassy bank under the ridge, bushes on its lip, rocks and tall grass on
    # the flats (kept open for the crabs), cattails in the shallows, lotus pads out on the river.
    r.green(("tree_camphor", 5, 6), ("tree_willow", 25, 6), ("tree_maple", 35, 5), ("bamboo_grove", 43, 4),
            ("tree_plum", 56, 6), ("bush", 2, 8), ("bush_wide", 8, 8), ("bush", 15, 8), ("bush_azalea", 27, 8),
            ("bush", 33, 8), ("bush_wide", 54, 8), ("bush_azalea", 61, 8), ("bush", 8, 11), ("ferns", 57, 11),
            ("rock_mossy", 6, 19), ("tall_grass", 15, 21), ("rock_small", 24, 18), ("tall_grass", 50, 21),
            ("rock_small", 58, 18), ("cattails", 5, 23), ("cattails", 12, 23), ("cattails", 21, 23), ("cattails", 31, 23),
            ("cattails", 48, 23), ("cattails", 57, 23), ("lotus_pads", 14, 25), ("lotus_pads", 44, 27), ("lotus_pads", 60, 24))
    r.spawn = [3, 14]
    r.way("west", 0, 14, "w", [2, 14], 3)
    r.way("east", 63, 14, "e", [61, 14], 3)
    r.at("jar_1", 40, 6)
    r.at("jar_2", 47, 7)
    r.at("jar_3", 39, 11)
    r.at("jar_4", 58, 16)
    r.at("jar_5", 61, 20)
    r.at("herb_6", 17, 11)
    r.at("herb_7", 44, 12)
    r.at("herb_8", 55, 17)
    r.at("fish_9", 27, 24)
    r.at("rift_tear", 35, 18)
    r.at("swarm_glowfly", 41, 19)
    r.at("trail_jade_frog", 11, 19)
    r.spawns = [[[13, 17], [22, 20], [30, 18], [36, 20], [42, 16], [48, 20]],
                [[27, 11], [33, 12], [38, 13], [43, 10]],
                [[55, 20]]]
    return r


def willow_path_east():
    """Willow Path East: the road west out of Lotus Ferry under the willows and plum trees, a knoll where Old Pan sets
    up, a meadow terrace to the north, a stream to the south, and the boarlets rooting along the verges."""
    r = Layout("wp_east", 64, 26, 0, "g")
    r.rect(0, 0, 64, 2, 2, "r")
    r.rect(0, 2, 64, 5, 1, "f")                   # the meadow terrace
    r.stair(44, 7, 3, 2, 0, 1, "s")
    r.stair(8, 7, 3, 2, 0, 1, "s")
    r.hline(0, 63, 12, 3, "d")                    # the road
    r.rect(27, 8, 8, 3, 1, "g")                   # the knoll
    r.stair(30, 11, 2, 1, 0, 1, "s")
    r.water(0, 21, 64, 5)                         # the stream
    for x in (5, 16, 38, 54):
        r.prop("willow", x, 3)
    for x in (22, 60):
        r.prop("shrub", x, 4)
    for x in (4, 12, 25, 36, 47, 58):
        r.prop("reeds", x, 20)
    r.prop("incense", 50, 10)
    # Foliage (decision 40): plum and peach trees along the road as its name says, a camphor on the terrace, bushes on
    # its lip, fences along the road's verge, willows and tall grass by the stream.
    r.green(("tree_plum", 11, 5), ("tree_camphor", 27, 4), ("tree_peach", 33, 5), ("tree_plum", 51, 5),
            ("tree_maple", 60, 6), ("bush_wide", 1, 6), ("bush_azalea", 14, 6), ("bush", 20, 6), ("bush", 41, 6),
            ("bush_azalea", 57, 6), ("fence_4", 13, 11), ("fence_3", 36, 11), ("bush", 5, 10), ("bush_azalea", 47, 10),
            ("tree_willow", 8, 19), ("tree_peach", 22, 19), ("tree_willow", 40, 19), ("tree_plum", 55, 19),
            ("tall_grass", 14, 19), ("tall_grass", 30, 19), ("tall_grass", 47, 19), ("rock_small", 17, 16),
            ("rock_mossy", 55, 15), ("cattails", 2, 21), ("cattails", 19, 21), ("cattails", 33, 21), ("cattails", 50, 21),
            ("lotus_pads", 26, 23), ("lotus_pads", 45, 24))
    r.spawn = [60, 13]
    r.way("east", 63, 13, "e", [61, 13], 3)
    r.way("west", 0, 13, "w", [2, 13], 3)
    r.at("npc_old_pan_wp", 31, 9)
    r.at("pan_spot", 34, 13)
    r.at("herb_1", 33, 16)
    r.at("jar_2", 48, 4)
    r.at("crate_3", 33, 18)
    r.at("jar_4", 52, 17)
    r.at("sign_wp", 60, 11)
    r.at("note_lu", 57, 11)
    r.spawns = [[[10, 15], [20, 16], [26, 17], [44, 15], [51, 16]]]
    return r


def willow_path_west():
    """Willow Path West: the road on to Stoneford past the training stumps and lifting stones, the pine ridge where the
    toads sit, a rock pillar with a chest on top (crates, a step, the pillar), the shrine and the Spirit Fruit tree by
    the western end, and a lotus pond to the south."""
    r = Layout("wp_west", 64, 30, 0, "g")
    r.rect(0, 0, 64, 3, 2, "r")
    r.rect(0, 3, 26, 6, 1, "g")                   # the pine ridge
    r.stair(8, 9, 3, 2, 0, 1, "s")
    r.hline(0, 63, 14, 3, "d")                    # the road
    r.rect(42, 4, 3, 3, 3, "r")                   # the rock pillar
    r.rect(40, 5, 2, 2, 2, "r")                   # its step
    r.water(0, 26, 64, 4)                         # the pond
    r.rect(14, 18, 12, 4, 0, "d")                 # the training ground
    r.prop("crates", 38, 6)                       # up to the step
    for x in (3, 21):
        r.prop("bamboo", x, 4)
    for x in (30, 50, 60):
        r.prop("willow", x, 8)
    r.prop("shrub", 12, 5)
    r.prop("lantern", 56, 11)
    r.prop("lotus", 10, 27)
    r.prop("lotus", 36, 28)
    for x in (2, 20, 44, 58):
        r.prop("reeds", x, 25)
    # Foliage (decision 40): great pines on the pine ridge, a maple and a camphor on the meadow under the rock pillar,
    # bushes on the ridge's lip, fences along the road, willows, plum and bamboo by the pond with tall grass and rocks.
    r.green(("tree_pine", 6, 4), ("tree_pine", 23, 7), ("tree_pine", 1, 7), ("tree_maple", 35, 10), ("tree_camphor", 46, 9),
            ("bush", 4, 8), ("bush_wide", 14, 8), ("bush", 19, 8), ("bush_azalea", 24, 8), ("bush", 27, 5),
            ("bush_azalea", 38, 4), ("bush_wide", 61, 5), ("fence_4", 20, 13), ("fence_3", 44, 13),
            ("tree_willow", 7, 23), ("tree_peach", 9, 19), ("tree_willow", 27, 25), ("tree_plum", 53, 21),
            ("bamboo_grove", 60, 24), ("tall_grass", 1, 20), ("tall_grass", 10, 24), ("tall_grass", 26, 22),
            ("tall_grass", 50, 24), ("rock_mossy", 33, 24), ("cattails", 6, 26), ("cattails", 24, 26), ("cattails", 47, 26),
            ("cattails", 55, 26), ("lotus_pads", 20, 27), ("lotus_pads", 50, 28))
    r.spawn = [60, 15]
    r.way("east", 63, 15, "e", [61, 15], 3)
    r.way("west", 0, 15, "w", [2, 15], 3)
    r.at("herb_1", 4, 6)
    r.at("herb_2", 48, 23)
    r.at("jar_3", 9, 4)
    r.at("jar_4", 14, 4)
    r.at("jar_5", 32, 12)
    r.at("jar_6", 43, 24)
    r.at("jar_7", 57, 18)
    r.at("stump_0", 17, 19)
    r.at("stump_1", 20, 20)
    r.at("stump_2", 23, 19)
    r.at("lift_1", 30, 19)
    r.at("lift_2", 33, 22)
    r.at("shrine_wp", 58, 12)
    r.at("sign_wpw", 3, 12)
    r.at("temper_copper_wp_west", 39, 21)
    r.at("chest_pine_top", 43, 5)
    r.at("rift_tear", 35, 17)
    r.at("first_fruit_tree", 52, 11)
    r.at("swarm_glowfly", 44, 20)
    r.at("trail_mist_hare", 19, 23)
    # The herd's elite keeps apart at the west meadow by the willow, where the herd's walk west ends (world.py): the
    # herd's westmost spawns are 14 cells east of it (one at 11,17, 7 cells off, sent two respawned boarlets into the
    # elite's fight and the QA player fell).
    r.spawns = [[[22, 17], [18, 23], [28, 17], [37, 18], [45, 17], [42, 22]],
                [[15, 5], [17, 6], [19, 5]],
                [[4, 21]]]
    return r


def stoneford_gate():
    """Stoneford Gate: the paved street in from the Willow Path under the town wall, the gap in the wall where the
    Quarry Road climbs north, the County Hall's door, the gate guard, and a canal along the south."""
    r = Layout("sf_gate", 56, 26, 0, "g")
    r.rect(0, 0, 56, 4, 3, "l")                   # the town wall
    r.rect(15, 0, 3, 4, 0, "d")                   # the Quarry Road through it
    r.vline(15, 4, 12, 3, "d")
    r.rect(0, 12, 56, 5, 0, "p")                  # the street
    r.water(0, 22, 56, 4)                         # the canal
    hall = r.prop("house", 46, 6)                 # the County Hall
    r.prop("lantern", 14, 4)
    r.prop("lantern", 18, 4)
    r.prop("lantern_red", 26, 11)
    r.prop("lantern_red", 32, 11)
    for x in (6, 36):
        r.prop("willow", x, 6)
    r.prop("barrel", 40, 8)
    r.prop("crates", 8, 18)
    for x in (4, 20, 34, 50):
        r.prop("reeds", x, 21)
    # Foliage (decision 40): a camphor and a maple inside the wall, bamboo against it, bushes and a hedge along the
    # street's north side, willows along the canal with tall grass and cattails.
    r.green(("tree_camphor", 25, 7), ("tree_maple", 3, 8), ("bamboo_grove", 41, 4), ("bush_wide", 9, 5), ("bush", 20, 5),
            ("hedge_3", 30, 6), ("bush_azalea", 53, 8), ("bush", 34, 9), ("bush", 1, 5),
            ("tree_willow", 8, 20), ("tree_willow", 19, 20), ("tree_willow", 44, 20), ("bush_azalea", 25, 18),
            ("bush", 31, 19), ("tall_grass", 12, 20), ("tall_grass", 35, 20), ("rock_small", 49, 19),
            ("cattails", 12, 22), ("cattails", 28, 22), ("cattails", 40, 22), ("cattails", 52, 22))
    r.spawn = [52, 14]
    r.way("east", 55, 14, "e", [53, 14], 3)
    r.way("west", 0, 14, "w", [2, 14], 3)
    r.way("quarry_road", 16, 0, "n", [16, 3], 3)
    r.door("county_hall_door", hall)
    r.at("shrine_sf_gate", 43, 11)
    r.at("sign_sf_gate", 52, 17)
    r.at("npc_guard_hou", 29, 11)
    r.at("npc_foreman_dong", 13, 10)
    r.at("npc_adventurer_kai", 37, 18)
    r.at("tide_gong", 22, 10)
    return r


def stoneford_market():
    """Market Street: the stalls and the teleport stone on the paved street, three houses in a row whose roofs the
    rooftop thief runs over (crates at the west end, a tile's jump between each), the notice boards, and the arch
    north to the Beast Trial Grove."""
    r = Layout("sf_market", 56, 28, 0, "g")
    r.rect(0, 0, 56, 3, 2, "r")
    r.rect(0, 12, 56, 9, 0, "p")                  # the street and the square round the stone
    r.vline(49, 0, 11, 3, "d")                    # the path to the Grove's arch
    r.rect(49, 0, 3, 3, 0, "d")
    r.water(0, 24, 56, 4)
    houses = [r.prop("house", 3, 7), r.prop("house", 10, 7), r.prop("house", 17, 7)]
    r.prop("crates", 1, 9)                        # the way onto the first roof
    r.prop("storehouse", 26, 7)
    r.prop("storehouse", 38, 7)
    for x in (12, 22, 30, 44):
        r.prop("crates", x, 22)
    r.prop("barrel", 24, 12)
    r.prop("barrel", 36, 12)
    r.prop("lantern_red", 48, 12)
    r.prop("lantern_red", 52, 12)
    r.prop("willow", 33, 4)
    r.prop("willow", 45, 4)
    # Foliage (decision 40): trees behind the row of houses under the ridge, bushes between the buildings, and along
    # the canal bushes, tall grass and cattails (the street itself stays open for the stalls).
    r.green(("tree_camphor", 7, 4), ("tree_plum", 24, 4), ("tree_maple", 38, 4), ("tree_peach", 55, 6), ("bush", 16, 5),
            ("bush_azalea", 1, 5), ("bush", 30, 5), ("bush_wide", 42, 9), ("bush", 23, 10), ("bush_azalea", 35, 10),
            ("bush", 2, 22), ("bush_azalea", 9, 22), ("bush", 18, 23), ("tall_grass", 26, 23), ("bush_wide", 34, 22),
            ("bush", 41, 23), ("bush_azalea", 50, 22), ("cattails", 5, 24), ("cattails", 20, 24), ("cattails", 37, 24),
            ("cattails", 53, 24))
    r.spawn = [52, 16]
    r.way("east", 55, 16, "e", [53, 16], 3)
    r.way("west", 0, 16, "w", [2, 16], 3)
    r.way("grove", 50, 0, "n", [50, 2], 3)
    r.at("stone_sf", 37, 18)
    r.at("board_sf", 20, 13)
    r.at("arena_sf", 46, 13)
    r.at("auction_sf", 16, 19)
    r.at("storage_sf", 27, 13)
    r.at("exchange_sf", 54, 13)
    r.at("npc_storekeeper_fang", 13, 13)
    r.at("npc_auntie_rong", 32, 13)
    r.at("npc_keeper_shi", 41, 13)
    r.at("npc_courier_lin", 47, 19)
    r.at("npc_tailor_xun", 26, 18)
    r.at("npc_adventurer_su", 6, 18)
    r.at("npc_old_pan", 54, 19)
    r.at("board_sf_tower", 20, 7)                 # up on the third roof
    r.at("gutter_shard", 13, 7)                   # in the second roof's gutter
    r.at("thief_sf", 9, 13)
    r.routes["thief_sf"] = [[9, 13, 0.0], [2, 10, 0.6], [5, 8, 0.5], [9, 8, 0.4], [11, 8, 0.4], [16, 8, 0.5], [18, 8, 0.4], [22, 8, 0.5]]
    return r


def artisan_row():
    """Artisan Row: the forge at the west end, the tinkers and scribes along the paved street, Elder Gu's warehouse
    with its door, the guild hall's board at the east end, a house whose roof hides the tinkerer's lost gear."""
    r = Layout("sf_artisan_row", 56, 28, 0, "g")
    r.rect(0, 0, 56, 3, 2, "r")
    r.rect(0, 12, 56, 7, 0, "p")
    r.water(0, 24, 56, 4)
    r.prop("house", 6, 6)                         # the smithy
    warehouse = r.prop("storehouse", 30, 6)       # Gu's warehouse
    r.prop("house", 40, 5)
    r.prop("crates", 38, 7)                       # the way onto that roof
    r.prop("house", 47, 6)                        # the guild hall
    r.prop("barrel", 14, 11)
    r.prop("barrel", 15, 11)
    r.prop("lantern", 25, 11)
    r.prop("lantern", 36, 11)
    r.prop("willow", 22, 4)
    for x in (8, 26, 44):
        r.prop("reeds", x, 23)
    # Foliage (decision 40): trees in the gaps between the workshops, willows and camphors along the canal south of the
    # street, bushes and tall grass between them.
    r.green(("tree_maple", 17, 9), ("tree_plum", 26, 9), ("tree_camphor", 2, 8), ("bush", 13, 10), ("bush_azalea", 36, 10),
            ("bush", 54, 10), ("bush_wide", 20, 5), ("tree_willow", 5, 23), ("tree_camphor", 16, 23), ("tree_willow", 30, 23),
            ("tree_peach", 41, 23), ("tree_willow", 51, 23), ("bush", 10, 21), ("tall_grass", 22, 21), ("bush_azalea", 36, 20),
            ("tall_grass", 46, 21), ("rock_small", 26, 20), ("cattails", 12, 24), ("cattails", 34, 24), ("cattails", 47, 24))
    r.spawn = [52, 15]
    r.way("east", 55, 15, "e", [53, 15], 3)
    r.way("west", 0, 15, "w", [2, 15], 3)
    r.door("warehouse_door", warehouse)
    r.at("anvil_sf", 16, 13)
    r.at("furnace_sf", 52, 12)
    r.at("npc_smith_bao", 13, 13)
    r.at("npc_tinkerer_yu", 21, 17)
    r.at("npc_old_scribe_bai", 42, 17)
    r.at("npc_elder_gu", 27, 13)
    r.at("npc_madam_hua", 29, 17)
    r.at("npc_mei_qing", 48, 17)
    r.at("npc_apprentice_tao", 37, 17)
    r.at("npc_array_master_ren", 34, 13)
    r.at("npc_guildmaster_tang", 53, 17)
    r.at("guild_board", 54, 13)
    r.at("tinkerers_gear", 43, 5)
    r.at("crate_1", 18, 12)
    r.at("crate_2", 19, 13)
    return r


def fairground():
    """Stoneford Fairground: the two recruiters on their stages, the Jade and Cloud trial halls and the Trial Tower
    along the north side (lanterns strung on their roofs), the sect roads leaving north, Shen Lian's spar post and the
    stalls, the Caravan Road barred to the west."""
    r = Layout("sf_fairground", 72, 30, 0, "g")
    r.rect(0, 0, 72, 3, 2, "r")
    r.rect(0, 13, 72, 9, 0, "p")                  # the fair
    r.vline(7, 0, 12, 3, "d")                     # the road to the Jade Sect
    r.rect(7, 0, 3, 3, 0, "d")
    r.vline(43, 0, 12, 3, "d")                    # the stair road to the Cloud Sect
    r.rect(43, 0, 3, 3, 0, "d")
    r.water(0, 26, 72, 4)
    jade = r.prop("house", 13, 6)                 # the Jade trial hall
    tower = r.prop("storehouse", 26, 6)           # the Trial Tower
    cloud = r.prop("house", 31, 6)                # the Cloud trial hall
    r.prop("crates", 19, 8)                       # onto the Jade hall's roof
    r.prop("crates", 24, 8)                       # onto the tower's roof
    r.rect(15, 11, 6, 2, 1, "w")                  # Qing Lan's stage
    r.stair(17, 13, 2, 1, 0, 1, "w")
    r.rect(31, 11, 6, 2, 1, "w")                  # Mo Yun's stage
    r.stair(33, 13, 2, 1, 0, 1, "w")
    for x in (12, 22, 38, 50, 60):
        r.prop("lantern_red", x, 12)
    r.prop("willow", 3, 5)
    r.prop("willow", 56, 5)
    r.prop("bamboo", 64, 4)
    r.prop("bamboo", 66, 5)
    r.prop("crates", 40, 22)
    r.prop("barrel", 47, 22)
    for x in (5, 25, 45, 65):
        r.prop("reeds", x, 25)
    # Foliage (decision 40): the fair's wishing tree hung with prayer ribbons, a camphor and a peach on the east meadow,
    # trees west of the Jade road, bushes by the halls, willows and tall grass along the canal.
    r.green(("tree_ribbons", 60, 9), ("tree_camphor", 51, 6), ("tree_peach", 69, 8), ("tree_camphor", 2, 9),
            ("bush", 11, 10), ("bush_azalea", 38, 9), ("bush_wide", 47, 11), ("bush", 23, 11), ("bush_azalea", 70, 4),
            ("tree_willow", 6, 25), ("tree_willow", 22, 25), ("tree_camphor", 36, 25), ("tree_willow", 55, 25),
            ("tree_peach", 66, 24), ("bush", 14, 23), ("tall_grass", 29, 23), ("bush_azalea", 44, 24), ("tall_grass", 60, 23),
            ("cattails", 12, 26), ("cattails", 32, 26), ("cattails", 49, 26), ("cattails", 63, 26))
    r.spawn = [68, 17]
    r.way("east", 71, 17, "e", [69, 17], 3)
    r.way("west", 0, 17, "w", [2, 17], 3)
    r.door("trial_jade", jade)
    r.door("tower", tower)
    r.door("trial_cloud", cloud)
    r.way("jade_road", 8, 0, "n", [8, 3], 3)
    r.way("cloud_road", 44, 0, "n", [44, 3], 3)
    r.at("npc_recruiter_qing_lan", 18, 11)
    r.at("npc_recruiter_mo_yun", 34, 11)
    r.at("npc_shen_lian", 49, 17)
    r.at("npc_wen_zhao", 57, 16)
    r.at("npc_fair_vendor_he", 41, 18)
    r.at("npc_adventurer_rui", 62, 18)
    r.at("spar_sf", 53, 18)
    r.at("tower_board_sf", 30, 12)
    r.at("fair_lantern_0", 28, 6)                 # on the tower's roof
    r.at("fair_lantern_1", 16, 6)                 # on the Jade hall's roof
    r.at("fair_lantern_2", 35, 6)                 # on the Cloud hall's roof, a tile's jump from the tower's
    return r


# ==================================================================== chapter 2's stretch: the trials, the sects, the marsh
# docs/redesign_top_down_plan.md "As built: Phase 4, second part": the rooms the story visits from the sect choice to the
# first steps of chapter 2, for both sects a player can join (Jade and Cloud).
def trial_yard(rid, banner):
    """The walled yard of an Entry Trial behind its trial hall on the Fairground: the gateway back in the south wall
    between the sect's banners, stone lanterns round a sand ring where the Trial Puppet steps out once the bell has
    rung. The climb to the bell is each sect's own (trial_jade, trial_cloud)."""
    r = Layout(rid, 40, 24, 0, "p")
    r.walls(0, 0, 40, 24, 2, 1)
    r.rect(19, 23, 2, 1, 0, "p")                  # the gateway back to the Fairground
    r.rect(1, 18, 7, 5, 0, "g")                   # lawns in the front corners
    r.rect(32, 21, 7, 2, 0, "g")
    r.rect(2, 20, 4, 2, 0, "f")
    r.rect(21, 11, 16, 10, 0, "s")                # the granite apron round the ring
    r.rect(22, 12, 14, 8, 0, "d")                 # the sand ring
    r.rect(18, 12, 3, 11, 0, "s")                 # the walk from the gateway
    for x in (17, 22):
        r.prop(banner, x, 21)
    for x, y in ((21, 11), (36, 11), (21, 20), (36, 20)):
        r.prop("lantern", x, y)
    r.prop("pine", 2, 19)
    r.prop("pine", 37, 21)
    r.prop("shrub", 6, 21)
    r.prop("barrel", 1, 13)
    r.prop("barrel", 1, 14)
    # Foliage (decision 40): bushes on the front lawns, potted plants along the yard's front.
    r.green(("bush_azalea", 4, 18), ("ferns", 1, 21), ("bush", 33, 21), ("pot_bonsai", 14, 22), ("pot_orchid", 26, 22))
    r.spawn = [19.5, 20]
    r.way("entry", 19.5, 23, "s", [19.5, 21.5], 2)
    r.spawns = [[[29, 16]]]
    return r


def trial_jade():
    """The Jade Sect's Entry Trial: the climb to the trial bell runs over three roofs along the north wall (crates onto
    the first roof, a tile's running jump to the second and up its ridge, another jump to the third) and up onto the
    bell tower's top; racks of training weapons stand along the east wall."""
    r = trial_yard("sf_trial_jade", "banner_jade")
    r.rect(3, 5, 7, 4, 2, "t")                    # the first roof (x 3-9, y 5-8)
    r.prop("crates", 5, 9)                        # onto it
    r.rect(11, 3, 7, 6, 2, "t")                   # the second roof, a tile's jump east
    r.rect(15, 3, 3, 3, 3, "t")                   # its ridge, a level up
    r.rect(19, 2, 6, 5, 3, "t")                   # the third roof, a tile's jump from the ridge
    r.rect(25, 1, 4, 5, 4, "s")                   # the bell tower's top
    for x in (31, 34):
        r.prop("weapon_rack", x, 1)
    r.at("trial_bell", 26.5, 3)
    return r


def trial_cloud():
    """The Cloud Sect's Entry Trial: the climb runs up rock ledges out of the cliff behind the yard (the first ledge,
    the one above it, a plank walk over the cliff pool a tile's jump across, and the top ledge where the bell hangs)."""
    r = trial_yard("sf_trial_cloud", "banner_cloud")
    r.rect(1, 1, 38, 2, 5, "r")                   # the cliff behind the yard
    r.rect(6, 9, 6, 3, 1, "r")                    # the first ledge (x 6-11, y 9-11)
    r.rect(6, 3, 6, 6, 2, "r")                    # the ledge above it
    r.water(12, 3, 6, 6)                          # the cliff pool (x 12-17, y 3-8)
    r.rect(13, 5, 5, 2, 2, "w")                   # the plank walk over it, a tile's jump from the ledge
    r.rect(18, 3, 7, 5, 3, "r")                   # the top ledge
    r.prop("lotus", 14, 8)
    r.prop("boulder", 30, 4)
    r.prop("boulder", 4, 13)
    r.at("trial_bell", 22, 4)
    return r


def jade_gate_street():
    """Gate Street, the Jade Sect's front: the road up from Stoneford through the sect's banners onto the plaza inside
    the gate (the steward, the teleport stone, the shrine); the three halls in a row on rising terraces, the Weapon
    Hall, the Alchemy Hall and the Library, their roofs a level apart (the rooftop thief's run from the crates, the
    chest on the Library's roof); the service dorm and its sleeping porch; the notice board and the deacon by the way
    east to the Pavilion Rooftops; a scholar's garden pond; and the mountain behind."""
    r = Layout("ja_gate_street", 64, 32, 0, "g")
    r.rect(0, 0, 64, 3, 3, "r")                   # the mountain behind the sect
    r.rect(0, 12, 64, 7, 0, "p")                  # Gate Street
    r.rect(3, 19, 14, 4, 0, "p")                  # the plaza inside the gate
    r.vline(8, 23, 31, 3, "d")                    # the road up from Stoneford
    r.rect(22, 4, 8, 8, 1, "s")                   # the Alchemy Hall's terrace
    r.rect(30, 3, 8, 9, 2, "s")                   # the Library's terrace
    r.stair(25, 10, 2, 2, 0, 1)
    r.stair(33, 8, 2, 4, 0, 2)
    wh = r.prop("hall", 14, 6)                    # the Weapon Hall (roof 2)
    al = r.prop("hall", 22, 5)                    # the Alchemy Hall (roof 3), a hop up from the Weapon Hall's
    lb = r.prop("hall", 30, 4)                    # the Library (roof 4), a hop up again
    r.door_path(wh, 12, "p")
    r.prop("crates", 12, 8)                       # onto the Weapon Hall's roof
    r.prop("house", 42, 6)                        # the service dorm
    r.rect(42, 9, 6, 2, 0, "w")                   # its sleeping porch
    r.water(44, 24, 12, 5)                        # the scholar's pond
    for x, y in ((46, 25), (51, 26)):
        r.prop("lotus", x, y)
    # The scholar's garden south of the street: a path from the road to the pond between flower beds and a rockery.
    r.hline(11, 43, 26, 2, "d")
    for x, y, w in ((19, 22, 5), (30, 22, 6), (22, 29, 7), (36, 29, 5)):
        r.rect(x, y, w, 2, 0, "f")
    for x, y in ((27, 23), (28, 24), (38, 23), (41, 29)):
        r.prop("boulder", x, y)
    for x, y in ((17, 29), (33, 21), (1, 5), (10, 4)):
        r.prop("pine", x, y)
    for x, y in ((24, 23), (35, 24), (30, 29), (52, 5), (54, 6)):
        r.prop("shrub", x, y)
    for x, y in ((16, 10), (19, 10), (2, 11), (7, 11)):
        r.prop("lantern", x, y)
    for x in (7, 11):
        r.prop("banner_jade", x, 24)
    for x in (7, 11):
        r.prop("lantern_red", x, 28)
    for x, y in ((4, 2), (20, 1), (45, 1), (56, 2)):
        r.prop("pine", x, y)
    for x, y in ((57, 9), (59, 10), (58, 22)):
        r.prop("bamboo", x, y)
    r.prop("willow", 42, 23)
    r.prop("boulder", 3, 21)
    r.prop("shrub", 49, 10)
    r.prop("shrub", 38, 13)
    # Foliage (decision 40): great pines and a plum by the gate and the dorm, the scholar's garden south of the street
    # planted with plum, peach, maple, willow and bamboo round its beds and pond, hedges along its path.
    r.green(("tree_pine", 5, 8), ("tree_plum", 61, 6), ("tree_pine", 50, 4), ("bush_wide", 38, 4), ("bush", 13, 10),
            ("bush_azalea", 55, 10),
            ("tree_plum", 18, 25), ("tree_pine", 1, 25), ("tree_maple", 39, 29), ("tree_willow", 57, 28), ("tree_peach", 26, 31),
            ("bamboo_grove", 61, 25), ("tree_camphor", 3, 31), ("hedge_3", 13, 28), ("hedge_2", 33, 28),
            ("bush_azalea", 43, 23), ("bush", 25, 24), ("rock_small", 21, 30), ("tall_grass", 46, 30), ("ferns", 30, 25),
            ("lotus_pads", 49, 27), ("cattails", 44, 26))
    r.spawn = [9, 27]
    r.way("stoneford", 9, 31, "s", [9, 29], 3)
    r.way("east", 63, 15, "e", [61, 15], 3)
    r.door("weapon_hall", wh)
    r.door("alchemy_hall", al)
    r.door("library", lb)
    r.at("shrine_ja", 4.5, 13)
    r.at("stone_ja", 13, 20)
    r.at("board_ja", 60, 13)
    r.at("siege_gong_ja", 54, 17)
    r.at("npc_jade_steward", 7, 16)
    r.at("npc_jade_deacon", 57, 15)
    r.at("npc_jade_disciple_a", 29, 15)
    r.at("npc_jade_disciple_b", 40, 17)
    r.at("dorm_bed_ja", 46, 10)
    r.at("sweep_ja_0", 20, 15)
    r.at("sweep_ja_1", 27, 17)
    r.at("sweep_ja_2", 11, 22)                    # the grey stain by the gate
    r.at("chest_mission_hall", 35, 5)             # on the Library's roof
    r.at("thief_ja", 15, 14)
    r.routes["thief_ja"] = [[15, 14, 0.0], [12.5, 8, 0.6], [15.5, 7, 0.5], [20.5, 7, 0.6], [23.5, 6, 0.5], [28.5, 6, 0.6],
                            [31.5, 5, 0.5], [36.5, 5, 0.6]]
    return r


def weapon_hall(rid, banner, master, smith, anvil, dummies):
    """A sect's Weapon Hall and Forge: racks of training weapons along the back wall between the sect's banners, the
    weapon master before them, the sparring ring a level up in the west (boards and a step) with its two dummies, the
    smith and the anvil at the forge in the east, and the door in the front wall back out."""
    r = Layout(rid, 24, 14, 0, "s")
    r.walls(0, 0, 24, 14)
    r.rect(11, 13, 2, 1, 0, "s")                  # the doorway in the front sill
    r.rect(2, 7, 7, 4, 1, "w")                    # the sparring ring
    r.stair(4, 11, 3, 1, 0, 1, "w")
    for x in (2, 5, 8):
        r.prop("weapon_rack", x, 1)
    for x in (12, 15):
        r.prop(banner, x, 1)
    r.prop("crates", 19, 1)
    r.prop("barrel", 21, 1)
    r.prop("barrel", 22, 2)
    r.prop("lantern", 1, 11)
    r.prop("lantern", 22, 11)
    r.green(("pot_bonsai", 1, 6), ("pot_orchid", 22, 6), ("pot_bonsai", 17, 1))   # foliage (decision 40): potted plants
    r.spawn = [11.5, 11]
    r.at(master, 10, 5)
    r.at(smith, 17, 5)
    r.at(anvil, 19, 7)
    r.at(dummies[0], 4, 8)
    r.at(dummies[1], 7, 8)
    r.way("exit", 11.5, 13, "s", [11.5, 11.5], 2)
    return r


def jade_weapon_hall():
    return weapon_hall("ja_weapon_hall", "banner_jade", "npc_jade_weapon_master", "npc_jade_smith", "anvil_ja",
                       ["dummy_wh_0", "dummy_wh_1"])


def cloud_weapon_hall():
    return weapon_hall("cm_weapon_hall", "banner_cloud", "npc_cloud_weapon_master", "npc_cloud_smith", "anvil_cm",
                       ["dummy_cwh_0", "dummy_cwh_1"])


def pavilion_rooftops():
    """The Pavilion Rooftops, the Jade Sect's training yard: the yard with its dummies, the hall master and the sparring
    post in a sand ring; the courtyard pine in a raised bed with a herb pot beside it; three pavilions in a row rising a
    level each (crates, the East Entry's roof, the East Step's, and the great Heaven Pavilion's, where the Retreat
    Rooms open and a chest waits); the rear stairs up to the east terrace under the plum shrubs, where crates give a
    second way onto the Heaven Pavilion; a lotus pond; and the mountain behind."""
    r = Layout("ja_pavilion_rooftops", 60, 30, 0, "g")
    r.rect(0, 0, 60, 3, 3, "r")
    r.rect(0, 11, 60, 12, 0, "p")                 # the training yard
    r.rect(22, 15, 10, 6, 0, "d")                 # the sparring ring
    r.rect(3, 7, 5, 4, 2, "b")                    # the courtyard pine's raised bed
    r.rect(3, 11, 5, 1, 1, "s")                   # its step
    r.prop("pine", 4, 8)
    r.prop("hall", 14, 6)                         # the East Entry (roof 2)
    r.rect(22, 4, 8, 7, 1, "s")                   # the East Step's terrace
    r.stair(25, 9, 2, 2, 0, 1)
    r.prop("hall", 22, 5)                         # the East Step (roof 3)
    r.rect(30, 3, 12, 7, 4, "t")                  # the Heaven Pavilion, built on the grid (roof 4)
    retreat = r.prop("storehouse", 34, 3)         # the Retreat Rooms' door on its roof
    r.prop("crates", 12, 8)                       # up onto the East Entry's roof
    r.rect(42, 4, 14, 6, 2, "s")                  # the east terrace
    r.stair(48, 10, 3, 4, 0, 2)                   # the rear stairs
    r.prop("crates", 42, 5)                       # from the terrace onto the Heaven Pavilion
    for x, y in ((47, 5), (52, 7), (54, 5)):
        r.prop("shrub", x, y)
    r.water(8, 25, 12, 4)                         # the lotus pond
    for x, y, w in ((24, 23, 6), (40, 24, 8)):
        r.rect(x, y, w, 2, 0, "f")                # flower beds along the yard's south side
    r.prop("lotus", 10, 26)
    r.prop("lotus", 15, 27)
    r.prop("willow", 21, 24)
    for x in (30, 41):
        r.prop("banner_jade", x, 11)
    for x, y in ((13, 11), (46, 13), (52, 13)):
        r.prop("lantern", x, y)
    for x, y in ((6, 1), (24, 1), (50, 2)):
        r.prop("pine", x, y)
    for x, y in ((56, 23), (58, 24), (3, 24)):
        r.prop("bamboo", x, y)
    # Foliage (decision 40): a pine and bushes west of the pavilions, trees along the yard's south edge round the
    # lotus pond and the flower beds, a plum on the east terrace.
    r.green(("tree_pine", 10, 5), ("bush", 1, 5), ("bush_azalea", 8, 9), ("tree_plum", 56, 6),
            ("tree_plum", 27, 27), ("tree_maple", 36, 28), ("tree_pine", 46, 28), ("tree_peach", 52, 27), ("tree_willow", 6, 28),
            ("bush_wide", 32, 24), ("bush", 22, 26), ("bush_azalea", 49, 24), ("tall_grass", 40, 27), ("rock_mossy", 20, 28),
            ("lotus_pads", 12, 25), ("cattails", 19, 25))
    r.spawn = [3, 16]
    r.way("west", 0, 16, "w", [2, 16], 3)
    r.way("east", 59, 16, "e", [57, 16], 3)
    r.door("retreat_roof", retreat)
    r.at("roof_chest", 39, 7)                     # on the Heaven Pavilion's roof
    r.at("npc_jade_hall_master", 15, 18)
    r.at("npc_jade_wm_yard", 20, 20)
    r.at("dummy_jp_0", 8, 16)
    r.at("dummy_jp_1", 11, 16)
    r.at("spar_jp", 26, 18)
    r.at("herb_pot_pine", 6, 8)                   # in the pine's raised bed
    return r


def east_terrace():
    """The East Terrace: the Mission Hall with its row of training stumps and the Temper drum, the formation elder at
    her table, the physician, the arena master and his sparring post, the abode terrace up its stairs against the cliff
    (a cave abode's door between stone lanterns), the Retreat Rooms, and the cliff with its pines behind."""
    r = Layout("ja_east_terrace", 60, 30, 0, "g")
    r.rect(0, 0, 60, 4, 5, "r")                   # the cliff the abodes are cut into
    r.rect(0, 11, 60, 12, 0, "p")
    r.prop("hall", 5, 6)                          # the Mission Hall
    r.prop("crates", 13, 8)                       # a step up onto its roof
    for x, y in ((5, 12), (7, 13), (9, 12), (11, 13), (13, 12), (15, 13)):
        r.prop("post", x, y)                      # training stumps
    r.rect(24, 4, 17, 5, 2, "s")                  # the abode terrace
    r.stair(31, 9, 3, 4, 0, 2)
    abode = r.prop("storehouse", 34, 4)           # a cave abode's door, against the cliff
    for x in (25, 39):
        r.prop("lantern", x, 7)
    retreat = r.prop("hall", 45, 6)               # the Retreat Rooms
    r.door_path(retreat, 11, "p")
    for x in (29, 36):
        r.prop("banner_jade", x, 11)
    for x, y in ((8, 2), (20, 1), (50, 2)):
        r.prop("pine", x, y)
    for x, y in ((56, 9), (57, 10), (2, 24)):
        r.prop("bamboo", x, y)
    for x, y in ((20, 25), (33, 26), (46, 25)):
        r.prop("shrub", x, y)
    r.prop("willow", 27, 23)
    for x, y, w in ((14, 24, 8), (38, 24, 7)):
        r.rect(x, y, w, 2, 0, "f")
    # Foliage (decision 40): a camphor between the Mission Hall and the abode terrace, a plum by the Retreat Rooms, and
    # along the yard's south edge pines, a maple, a plum and a peach over the flower beds.
    r.green(("tree_camphor", 18, 7), ("tree_plum", 54, 5), ("bush", 42, 7), ("bush_azalea", 1, 9), ("bush", 22, 9),
            ("tree_pine", 6, 27), ("tree_maple", 12, 28), ("tree_camphor", 29, 28), ("tree_plum", 38, 27), ("tree_peach", 50, 27),
            ("tree_pine", 57, 26), ("bush", 23, 24), ("bush_wide", 45, 24), ("tall_grass", 16, 27), ("rock_mossy", 33, 29))
    r.spawn = [3, 16]
    r.way("west", 0, 16, "w", [2, 16], 3)
    r.way("east", 59, 16, "e", [57, 16], 3)
    r.door("abode", abode)
    r.door("retreat", retreat)
    r.at("npc_jade_formation_elder", 22, 14)
    r.at("npc_jade_physician", 34, 17)
    r.at("npc_arena_master", 48, 15)
    r.at("formation_table_ja", 19, 16)
    r.at("arena_ja", 53, 18)
    r.at("temper_jade_ja_east_terrace", 16, 17)
    return r


def herb_terraces():
    """The Herb Terraces: three green terraces stepping up the hillside on grassy banks, a garden bed and herbs on each
    and stairs between them, the gardener at their foot among the bamboo, and the stone stair up through the crags to
    Elder Hu's peak between two lanterns."""
    r = Layout("ja_herb_terraces", 56, 30, 0, "g")
    r.rect(0, 0, 56, 2, 5, "r")                   # the crags
    r.rect(8, 15, 32, 5, 1, "g")                  # the first terrace
    r.rect(8, 9, 32, 6, 2, "g")                   # the second
    r.rect(8, 2, 32, 7, 3, "g")                   # the third
    for y, lv in ((16, 1), (11, 2), (4, 3)):
        r.hline(10, 37, y, 2, "d", lv)            # a path along each terrace
    r.stair(12, 18, 2, 2, 0, 1)
    r.stair(22, 13, 2, 2, 1, 2)
    r.stair(32, 7, 2, 2, 2, 3)
    r.rect(44, 0, 3, 9, 3, "s")                   # the peak stair's head, through the crags
    r.stair(44, 9, 3, 6, 0, 3)
    r.hline(0, 55, 23, 3, "d")                    # the path along the terraces' foot
    r.vline(44, 15, 22, 3, "d")
    for x in (43, 47):
        r.prop("lantern", x, 14)
    for x, y in ((3, 19), (4, 21), (50, 20), (52, 25)):
        r.prop("bamboo", x, y)
    for x, y in ((14, 5), (26, 3), (18, 12), (35, 13), (28, 17)):
        r.prop("shrub", x, y)
    for x, y in ((6, 1), (50, 1)):
        r.prop("pine", x, y)
    r.prop("boulder", 49, 12)
    # Foliage (decision 40): hedges and bushes along each terrace's lip, a pine and a plum on the top terrace, a camphor
    # and a maple west of the terraces, a pine by the peak stair, and trees over the meadow below the foot path.
    r.green(("hedge_3", 15, 19), ("hedge_3", 26, 19), ("bush", 36, 19), ("hedge_3", 9, 14), ("bush_azalea", 18, 14),
            ("hedge_4", 26, 14), ("bush", 36, 14), ("hedge_3", 9, 8), ("bush", 20, 8), ("hedge_3", 25, 8), ("bush", 38, 8),
            ("tree_pine", 10, 3), ("tree_plum", 20, 3), ("tree_camphor", 3, 8), ("tree_maple", 4, 14), ("tree_pine", 52, 12),
            ("tree_plum", 51, 5), ("bush", 49, 3), ("tree_pine", 8, 28), ("tree_camphor", 32, 28), ("tree_maple", 42, 28),
            ("tree_peach", 50, 29), ("bush", 26, 27), ("tall_grass", 16, 28), ("rock_mossy", 37, 27))
    r.spawn = [3, 24]
    r.way("west", 0, 24, "w", [2, 24], 3)
    r.way("peak_path", 45, 0, "n", [45, 2], 3)
    r.at("bed_0", 18, 17)
    r.at("bed_1", 28, 12)
    r.at("bed_2", 36, 6)
    r.at("herb_1", 11, 17)
    r.at("herb_2", 30, 5)
    r.at("npc_jade_gardener", 20, 24)
    return r


def elder_hu_peak():
    """Elder Hu's Peak: a mountain meadow under the summit crags, Elder Hu by the Qi spring, the insight stone, the
    Heart Trial's circle and the treasure plot; rock ledges stepping up to the Meditation Rock; the pagoda at his cave
    abode's door; and the path back down to the Herb Terraces."""
    r = Layout("ja_elder_hu_peak", 40, 26, 0, "g")
    r.rect(0, 0, 40, 3, 5, "r")                   # the summit crags
    r.rect(0, 3, 2, 18, 3, "r")
    r.rect(38, 3, 2, 23, 3, "r")
    r.rect(7, 9, 6, 4, 1, "r")                    # the first ledge
    r.rect(13, 5, 6, 5, 2, "r")                   # the second
    r.rect(19, 3, 7, 5, 3, "r")                   # the Meditation Rock's ledge
    abode = r.prop("storehouse", 31, 5)           # the pagoda at the cave abode's door
    r.door_path(abode, 12)
    r.vline(5, 14, 25, 2, "d")                    # the path down
    r.prop("incense", 16, 15)
    for x, y in ((3, 8), (35, 13), (27, 22), (10, 22)):
        r.prop("pine", x, y)
    for x, y in ((25, 9), (8, 14), (30, 18), (2, 23)):
        r.prop("boulder", x, y)
    # Foliage (decision 40): a great pine and a plum on the mountain meadow, mossy rocks, tall grass and ferns.
    r.green(("tree_pine", 3, 11), ("tree_plum", 33, 20), ("tree_maple", 15, 22), ("rock_mossy", 27, 16), ("rock_small", 12, 12),
            ("tall_grass", 20, 24), ("tall_grass", 34, 16), ("ferns", 9, 15), ("bush", 36, 23), ("ferns", 23, 10))
    r.spawn = [6, 22]
    r.way("path", 5.5, 25, "s", [5.5, 23.5], 2)
    r.door("abode", abode)
    r.at("npc_elder_hu", 24, 13)
    r.at("spring_hu", 14, 16)
    r.at("insight_hu", 30, 12)
    r.at("rite_reflection", 20, 19)
    r.at("plot_hu", 9, 18)
    r.at("meditation_rock", 22, 4)
    return r


def cloud_cliff_stair():
    """The Cliff Stair, the Cloud Sect's approach: the road up from Stoneford between the sect's banners into the lower
    court (the steward, the teleport stone, the Cloud Steps' starting stone, the shrine, the service dorm and its porch,
    the notice board and the deacon), the grand stair up the cliff to its landing, a rock ledge above it, and the top
    ledge where the Cloud Library's cliff door opens and the Cloud Steps' bell hangs."""
    r = Layout("cm_cliff_stair", 56, 34, 0, "g")
    r.rect(0, 0, 56, 2, 6, "r")                   # the cliff's crown
    r.rect(0, 2, 34, 4, 5, "r")                   # the cliff face behind the landing
    r.rect(34, 2, 6, 3, 5, "r")
    r.rect(52, 2, 4, 8, 5, "r")
    r.rect(16, 6, 18, 8, 2, "s")                  # the landing
    r.stair(23, 14, 4, 4, 0, 2)                   # the grand stair
    r.rect(34, 5, 6, 6, 3, "r")                   # the ledge above the landing
    r.rect(40, 2, 12, 6, 4, "r")                  # the top ledge
    lib = r.prop("storehouse", 44, 2)             # the Cloud Library's cliff door
    r.rect(3, 18, 50, 11, 0, "p")                 # the lower court
    r.vline(8, 29, 33, 3, "d")                    # the road up from Stoneford
    r.prop("house", 38, 12)                       # the service dorm
    r.rect(38, 15, 6, 2, 0, "w")                  # its porch
    for x, y, w in ((44, 14, 5), (2, 14, 8), (30, 30, 10)):
        r.rect(x, y, w, 2, 0, "f")
    for x in (6, 12):
        r.prop("banner_cloud", x, 29)
    for x, y in ((17, 12), (32, 12), (22, 16), (27, 16)):
        r.prop("lantern", x, y)
    for x, y in ((3, 8), (11, 10), (54, 13), (2, 30)):
        r.prop("pine", x, y)
    for x, y in ((6, 12), (47, 11), (51, 30)):
        r.prop("boulder", x, y)
    # Foliage (decision 40): great pines on the meadows west and east of the landing, pines, a maple and a plum along the
    # lower court's south edge, bushes by the dorm.
    r.green(("tree_pine", 13, 7), ("bush", 1, 11), ("tree_pine", 51, 10), ("bush_wide", 36, 7), ("bush", 53, 16),
            ("tree_pine", 20, 32), ("tree_maple", 44, 32), ("tree_plum", 27, 32), ("bush", 14, 30), ("bush_azalea", 39, 29),
            ("tall_grass", 49, 32), ("rock_small", 35, 32))
    r.spawn = [9, 31]
    r.way("stoneford", 9, 33, "s", [9, 31], 3)
    r.way("east", 55, 23, "e", [53, 23], 3)
    r.door("library", lib)
    r.at("shrine_cm", 14, 19)
    r.at("stone_cm", 13, 24)
    r.at("board_cm", 46, 20)
    r.at("siege_gong_cm", 51, 26)
    r.at("npc_cloud_steward", 7, 21)
    r.at("npc_cloud_deacon", 48, 22)
    r.at("npc_cloud_disciple_a", 22, 22)
    r.at("dorm_bed_cm", 42, 16)
    r.at("sweep_cm_0", 18, 24)
    r.at("sweep_cm_1", 30, 25)
    r.at("sweep_cm_2", 11, 27)                    # the grey stain by the gate
    r.at("cloud_steps_bell", 49, 5)               # the Cloud Steps' finish, on the top ledge
    r.at("cloud_steps_stone", 5, 26)
    return r


def sword_court():
    """The Sword Court: the Sword Hall's two wings along the cliff (the Weapon Hall's door and the Cloud Library's), the
    hall master and the dummies at the west, the plum-blossom poles (timber posts at stepped heights, a tile apart or
    side by side a level up), the sparring post, the Temper drum and the arena master, training stumps and the two sword
    pillars at the east."""
    r = Layout("cm_sword_court", 60, 30, 0, "g")
    r.rect(0, 0, 60, 3, 4, "r")
    r.rect(0, 10, 60, 13, 0, "p")                 # the court
    wh = r.prop("hall", 16, 5)
    lib = r.prop("hall", 24, 5)
    r.door_path(wh, 10, "p")
    r.door_path(lib, 10, "p")
    r.prop("crates", 32, 7)                       # onto the Sword Hall's roof
    for x, lv in ((38, 1), (40, 1), (41, 2), (43, 2), (44, 3), (46, 2), (48, 1)):
        r.rect(x, 15, 1, 1, lv, "w")              # the plum-blossom poles
    for x in (51, 56):
        r.rect(x, 8, 1, 1, 5, "s")                # the sword pillars
    for x, y in ((50, 17), (52, 18), (54, 17), (56, 18)):
        r.prop("post", x, y)
    for x in (15, 32):
        r.prop("banner_cloud", x, 9)
    for x, y in ((4, 1), (37, 1), (48, 2)):
        r.prop("pine", x, y)
    for x, y in ((8, 25), (22, 26), (40, 25)):
        r.prop("boulder", x, y)
    for x, y, w in ((3, 24, 4), (12, 25, 8), (28, 24, 9), (46, 25, 6)):
        r.rect(x, y, w, 2, 0, "f")
    for x, y in ((56, 24), (57, 25)):
        r.prop("bamboo", x, y)
    # Foliage (decision 40): pines and a maple along the cliff's foot, and along the court's south edge pines and a plum
    # among the flower beds and rocks.
    r.green(("tree_pine", 6, 6), ("tree_pine", 40, 5), ("tree_maple", 47, 6), ("bush", 12, 8), ("bush_wide", 34, 4),
            ("tree_pine", 14, 28), ("tree_plum", 31, 28), ("tree_pine", 47, 28), ("bush", 1, 24), ("tall_grass", 24, 28),
            ("bush_azalea", 37, 27), ("rock_small", 53, 28))
    r.spawn = [3, 16]
    r.way("west", 0, 16, "w", [2, 16], 3)
    r.way("east", 59, 16, "e", [57, 16], 3)
    r.door("weapon_hall", wh)
    r.door("library", lib)
    r.at("npc_cloud_hall_master", 10, 15)
    r.at("npc_arena_cm", 47, 20)
    r.at("dummy_cs_0", 5, 16)
    r.at("dummy_cs_1", 7, 16)
    r.at("spar_cm", 35, 19)
    r.at("temper_jade_cm_sword_court", 41, 20)
    return r


def array_court():
    """The Array Court: the array dais a step up in the middle with the formation elder at her table and a stone lantern
    at each corner (the formation's nodes), the physician, the monastery furnace, the rope ledge against the cliff, the
    Retreat Rooms, the garden beds with the gardener, and the gorge path up to Elder Sung's peak."""
    r = Layout("cm_array_court", 60, 30, 0, "g")
    r.rect(0, 0, 60, 3, 4, "r")
    r.rect(0, 10, 60, 13, 0, "p")
    r.rect(20, 12, 15, 5, 1, "s")                 # the array dais
    r.stair(26, 17, 3, 1, 0, 1)
    for x, y in ((20, 12), (34, 12), (20, 16), (34, 16)):
        r.prop("lantern", x, y)
    r.rect(40, 3, 7, 6, 2, "r")                   # the rope ledge
    r.rect(41, 9, 2, 1, 1, "r")                   # a step up to it
    retreat = r.prop("hall", 48, 5)
    r.door_path(retreat, 10, "p")
    r.rect(57, 0, 3, 10, 0, "d")                  # the gorge path to the peak
    r.rect(4, 24, 14, 3, 0, "d")                  # the garden's beds
    r.rect(3, 23, 16, 1, 0, "f")
    for x in (19, 34):
        r.prop("banner_cloud", x, 21)
    for x, y in ((6, 1), (30, 1)):
        r.prop("pine", x, y)
    for x, y in ((2, 20), (24, 26), (44, 25), (53, 26)):
        r.prop("bamboo", x, y)
    r.prop("boulder", 38, 5)
    # Foliage (decision 40): a pine, a maple and a plum under the cliff, bamboo at its west end, and trees over the
    # court's south edge beside the garden beds.
    r.green(("tree_pine", 8, 6), ("tree_maple", 18, 5), ("tree_plum", 28, 6), ("bush", 35, 8), ("bamboo_grove", 0, 4),
            ("tree_pine", 30, 28), ("tree_camphor", 40, 28), ("tree_peach", 49, 28), ("bush_wide", 20, 26), ("tall_grass", 35, 26),
            ("bush_azalea", 56, 24))
    r.spawn = [3, 16]
    r.way("west", 0, 16, "w", [2, 16], 3)
    r.way("east", 59, 16, "e", [57, 16], 3)
    r.way("peak_path", 58, 0, "n", [58, 2], 3)
    r.door("retreat", retreat)
    r.at("npc_cloud_formation_elder", 26, 13)
    r.at("formation_table_cm", 29, 14)
    r.at("npc_cloud_physician", 38, 18)
    r.at("furnace_cm", 45, 12)
    r.at("bed_cm_0", 7, 25)
    r.at("bed_cm_1", 10, 25)
    r.at("bed_cm_2", 13, 25)
    r.at("npc_cloud_gardener", 16, 21)
    return r


def elder_sung_peak():
    """Elder Sung's Peak: the summit crags over a mountain tarn; the west ledge and the west peak, the rope bridge along
    the tarn's edge to the far peak where Elder Sung stands; below, the Qi spring, the insight stone, the Heart Trial's
    circle and the treasure plot on the meadow; the pagoda at his cave abode's door; the path back down."""
    r = Layout("cm_elder_sung_peak", 40, 28, 0, "g")
    r.rect(0, 0, 40, 2, 6, "r")                   # the summit crags
    r.water(10, 2, 18, 5)                         # the tarn
    r.water(10, 9, 18, 2)                         # the stream out of it, under the bridge's south side
    r.rect(5, 11, 5, 3, 1, "r")                   # the west ledge
    r.rect(5, 2, 5, 9, 2, "r")                    # the west peak
    r.rect(10, 7, 18, 2, 2, "w")                  # the rope bridge
    r.rect(28, 2, 7, 8, 3, "r")                   # the far peak
    r.rect(35, 2, 5, 10, 4, "r")
    abode = r.prop("storehouse", 33, 13)
    r.door_path(abode, 20)
    r.vline(5, 15, 27, 2, "d")                    # the path down
    for x, y in ((12, 4), (20, 3), (16, 9), (23, 10)):
        r.prop("lotus", x, y)
    r.prop("incense", 14, 16)
    for x, y in ((2, 12), (29, 21), (37, 18), (9, 24)):
        r.prop("pine", x, y)
    for x, y in ((2, 17), (26, 13), (19, 25), (36, 25)):
        r.prop("boulder", x, y)
    # Foliage (decision 40): a great pine and a plum on the meadow under the peaks, rocks, tall grass and ferns.
    r.green(("tree_pine", 15, 26), ("tree_plum", 33, 24), ("tree_maple", 25, 22), ("rock_mossy", 24, 18), ("tall_grass", 10, 14), ("tall_grass", 28, 26),
            ("ferns", 20, 13), ("bush", 1, 20), ("rock_small", 16, 11), ("cattails", 11, 10), ("lotus_pads", 20, 5))
    r.spawn = [6, 24]
    r.way("path", 5.5, 27, "s", [5.5, 25.5], 2)
    r.door("abode", abode)
    r.at("npc_elder_sung", 31, 5)                 # on the far peak
    r.at("spring_sung", 12, 18)
    r.at("insight_sung", 22, 15)
    r.at("rite_reflection_cm", 18, 21)
    r.at("plot_sung", 8, 20)
    return r


def marsh_edge():
    """The Marsh Edge, the Reed Marsh's first field: the path east from the Reed Shallows over wet meadow and two
    boardwalks across the channels, open water to the north with the stilt platforms standing in it (the reed platform
    and the net platform where the frogs sit, the stilt hut, the lookout) up their wooden stairs, lower stilts on the
    meadow, the south pools with reeds, lotus and the fishing spot, and the grey patches where the Hollowing has drained
    the reeds, dead trees over them."""
    r = Layout("rm_marsh_edge", 64, 30, 0, "m")
    r.water(0, 0, 64, 6)                          # the open marsh water
    r.water(0, 23, 64, 7)                         # the south pools
    r.water(24, 6, 2, 17)                         # the channels between them
    r.water(46, 6, 2, 17)
    for x, y, w, h in ((7, 6, 5, 1), (20, 6, 3, 2), (43, 6, 2, 1), (57, 6, 4, 2), (26, 8, 1, 3), (23, 18, 1, 3), (45, 18, 1, 3)):
        r.water(x, y, w, h)                       # bays and meanders, so no shore runs straight for long
    for x, y, w, h in ((10, 23, 4, 2), (40, 23, 5, 1), (50, 25, 3, 2)):
        r.rect(x, y, w, h, 0, "m")                # a spit and an islet in the south pools
    r.hline(0, 63, 13, 3, "d")                    # the path along the marsh
    r.rect(24, 13, 2, 3, 0, "w")                  # its boardwalks over the channels
    r.rect(46, 13, 2, 3, 0, "w")
    r.rect(12, 2, 6, 4, 2, "w")                   # the reed platform (x 12-17, y 2-5)
    r.stair(14, 6, 2, 4, 0, 2, "w")
    r.rect(27, 1, 7, 6, 2, "w")                   # the stilt hut's platform (x 27-33, y 1-6)
    r.prop("storehouse", 28, 1)                   # the hut
    r.stair(32, 7, 2, 4, 0, 2, "w")
    r.rect(38, 2, 6, 4, 2, "w")                   # the net platform
    r.stair(40, 6, 2, 4, 0, 2, "w")
    r.rect(50, 1, 6, 5, 2, "w")                   # the lookout
    r.stair(52, 6, 2, 4, 0, 2, "w")
    r.rect(3, 7, 5, 3, 1, "w")                    # low stilts on the meadow: west, by the pool, east
    r.rect(19, 19, 4, 3, 1, "w")
    r.rect(57, 18, 4, 3, 1, "w")
    r.rect(28, 22, 3, 1, 0, "w")                  # a jetty into the south pool
    for x, y in ((11, 18), (29, 17), (50, 19)):
        r.prop("dead_tree", x, y)
    for x, y in ((13, 19), (15, 18), (31, 20), (28, 20), (48, 19), (51, 17)):
        r.prop("grey_reeds", x, y)
    for x in (1, 6, 10, 20, 35, 42, 55, 60):
        r.prop("reeds", x, 22)
    for x in (4, 19, 36, 44, 58):
        r.prop("reeds", x, 6)
    for x, y in ((8, 26), (38, 25), (54, 27), (21, 3), (58, 2)):
        r.prop("lotus", x, y)
    r.prop("willow", 36, 10)
    r.prop("willow", 60, 9)
    r.prop("boulder", 9, 10)
    r.prop("shrub", 44, 10)
    # Foliage (decision 40): a great willow on the west meadow, cattails in the shallows along every shore, patches of
    # tall grass and a fallen log on the meadows, lotus pads on the open water; round the dead trees the Hollowing has
    # drained the ground (their `blight`: no ground cover grows there).
    r.green(("tree_willow", 19, 11), ("tree_willow", 57, 11), ("bush", 1, 9), ("bush_wide", 9, 12), ("ferns", 31, 10),
            ("tall_grass", 5, 10), ("tall_grass", 28, 11), ("tall_grass", 51, 11), ("tall_grass", 6, 20),
            ("tall_grass", 37, 21), ("tall_grass", 55, 21), ("log", 17, 21), ("rock_small", 43, 21),
            ("cattails", 2, 5), ("cattails", 9, 5), ("cattails", 22, 5), ("cattails", 45, 5), ("cattails", 62, 5),
            ("cattails", 5, 23), ("cattails", 16, 23), ("cattails", 33, 23), ("cattails", 52, 23), ("cattails", 60, 23),
            ("lotus_pads", 5, 2), ("lotus_pads", 40, 26), ("lotus_pads", 20, 27))
    r.spawn = [3, 14]
    r.way("west", 0, 14, "w", [2, 14], 3)
    r.way("east", 63, 14, "e", [61, 14], 3)
    r.at("herb_1", 33, 4)                         # on the stilt hut's platform
    r.at("herb_2", 53, 3)                         # on the lookout
    r.at("herb_3", 57, 16)
    r.at("jar_4", 16, 3)                          # on the reed platform
    r.at("jar_5", 42, 3)                          # on the net platform
    r.at("jar_6", 38, 17)
    r.at("jar_7", 44, 11)
    r.at("jar_8", 60, 16)
    r.at("fish_9", 29, 24)
    r.at("grey_patch_0", 14, 17)
    r.at("grey_patch_1", 30, 19)
    r.at("grey_patch_2", 49, 17)
    r.at("rift_tear", 36, 16)
    r.at("spirit_fruit_tree", 21, 16)
    r.at("swarm_glowfly", 41, 19)
    r.at("trail_jade_frog", 9, 17)
    # The elite frog keeps to the lookout (a level up from the path it cannot see from there), guarding its moss: an
    # optional fight, not one the path walks into (world.py).
    r.spawns = [[[13, 3], [16, 4]],
                [[10, 16], [21, 12], [35, 18], [54, 16]],
                [[54, 2]],
                [[43, 20]],
                [[19, 16], [33, 17], [44, 16]],
                [[39, 3], [42, 4]]]
    return r


LAYOUTS = [fishers_hut, village, village_night, old_ma_store, granny_liu_hut, lu_boat, reed_shallows, willow_path_east,
           willow_path_west, stoneford_gate, stoneford_market, artisan_row, fairground,
           trial_jade, trial_cloud, jade_gate_street, jade_weapon_hall, pavilion_rooftops, east_terrace, herb_terraces,
           elder_hu_peak, cloud_cliff_stair, sword_court, cloud_weapon_hall, array_court, elder_sung_peak, marsh_edge]


def build(check_only=False):
    stale = []
    failed = []
    for make in LAYOUTS:
        lay = make()
        d = lay.dict()
        try:
            check(lay, d)
        except SystemExit as e:
            failed.append(str(e))
            continue
        path = os.path.join(OUT, lay.id + ".json")
        body = {"schema_version": 1}
        body.update(d)
        text = json.dumps(body, indent=1, ensure_ascii=False) + "\n"
        if check_only:
            if not os.path.exists(path) or open(path, encoding="utf-8").read() != text:
                stale.append(lay.id)
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print("built", lay.id)
    if failed:
        raise SystemExit("\n".join(failed))
    if stale:
        raise SystemExit("stale top-down layouts (run tools/data/topdown_rooms.py): " + ", ".join(stale))


if __name__ == "__main__":
    build("--check" in sys.argv)
