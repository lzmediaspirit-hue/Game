"""Redesign Phase 4 (docs/redesign_top_down_plan.md, "As built: Phase 4"): the tutorial area's rooms redrawn for the
top-down world, one layout per room in data/topdown/<room id>.json, read by TopdownRoom (scripts/topdown).

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
stairs, drops and a jump one level up, the TopdownMotor's rules; tests/topdown_tutorial.gd repeats it in the game).
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
DOORS = {"house": (2, 3), "storehouse": (1, 2)}


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

    def reach(self, start):
        """Every cell a body reaches on foot from `start`: walking, stairs, drops, a jump one level up."""
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
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
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
    if ev.get("wave") and len(d.get("event", {}).get("wave", [])) == 0:
        errs.append("event wave not placed")
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
    for pid, p in d["portals"].items():
        c = cell(p["at"])
        for i, r in enumerate(reached):
            if c not in r:
                errs.append("portal %s: not reached from start %s" % (pid, str(starts[i])))
    for k, pts in enumerate(d["spawns"]):
        for q in pts:
            c = cell(q)
            if g.floor(*c) is None:
                errs.append("spawn %d point %s: no floor" % (k, str(c)))
    if errs:
        raise SystemExit("%s:\n  " % lay.id + "\n  ".join(errs))


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
    r.prop("lantern", 23, 15)
    r.prop("lantern", 46, 15)
    r.prop("barrel", 36, 13)
    for x in (2, 8, 14, 26, 33, 44):
        r.prop("reeds", x, 33)
    if night:
        r.spawn = [30, 22]
        r.at("hut_refuge", 6.5, 15)
        r.at("npc_dou_night", 44, 25)
        r.at("npc_granny_night", 18, 23)
        r.at("npc_ma_night", 38, 18)
        r.event = {"wave": [[5, 31], [15, 32], [25, 31], [35, 32], [44, 31]], "fixed": [[36, 36]]}
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
    """Old Ma's Store: the counter across the shop with Old Ma behind it, the sandals up in the loft, the sacks by the
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
    r.spawn = [8, 9]
    r.at("npc_old_ma", 12, 3)
    r.at("sandals_loft", 2, 1)
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
    r.spawns = [[[11, 17], [18, 23], [28, 17], [37, 18], [45, 17], [42, 22]],
                [[15, 5], [17, 6], [19, 5]],
                [[37, 21]]]
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


LAYOUTS = [fishers_hut, village, village_night, old_ma_store, granny_liu_hut, lu_boat, reed_shallows, willow_path_east,
           willow_path_west, stoneford_gate, stoneford_market, artisan_row, fairground]


def build(check_only=False):
    stale = []
    for make in LAYOUTS:
        lay = make()
        d = lay.dict()
        check(lay, d)
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
    if stale:
        raise SystemExit("stale top-down layouts (run tools/data/topdown_rooms.py): " + ", ".join(stale))


if __name__ == "__main__":
    build("--check" in sys.argv)
