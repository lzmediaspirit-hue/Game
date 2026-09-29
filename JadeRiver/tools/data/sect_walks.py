"""Decision 42 ("There should be less monotone walking between places in the sect quest"): every trip the sect stretch's
quests ask for, from the sect choice to the end-of-prototype gate, measured on the top-down layouts, and the rule they
are held to (docs/redesign/feedback/sect_walking.md).

A trip goes from one stop of the stretch to the next: a giver, a step's place, a hand-in. Each is walked the way the
tracker's go button walks it: the rooms by the fewest ways (WorldRules.route, the sect's transfer arrays among them as
they are for auto-path, once the token knows both ends), and inside each room the auto-path's own path on the height
grid (TopdownRoom.find_path: eight directions, stairs, a hop up a level). Its seconds are those of plain walking at the
sprint pace (decision 42's sprint default: movement.json's topdown `sprint`, 216, about 1.4x the walk); an array's step, a way's fade and a scene's cuts
are not counted.

The itinerary of each sect is written out below, stop by stop, and checked against the data it names: every stop's
person or thing stands in that room of the built data, a giver or hand-in stop is that quest's own person, and every
quest of the stretch has its stops. A "wayside" stop is something on the way that is no quest's step (a spar offered,
two elders overheard, a gardener's favour: a staged scene of data/scenes.json plays there): the player may pass it by,
but a walk that holds one is not a plain walk.

The rule (`--check`, run by tools/run_tests.sh):
  - no plain walk between two stops is longer than PLAIN_MAX_S;
  - no immediate back-and-forth: a trip straight back to the room the trip before it came from, both at least
    BACK_MIN_S long (a long walk out for one thing, and back).

  python3 tools/data/sect_walks.py              the trip tables of both sects (markdown)
  python3 tools/data/sect_walks.py --before     the same for the stretch as it was before decision 42 (build 108)
  python3 tools/data/sect_walks.py --check      the rule, and every stop against the data
"""
import heapq
import json
import math
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA = os.path.join(ROOT, "data")
sys.path.insert(0, HERE)
from topdown_rooms import Grid, WATER  # noqa: E402

TILE = 32.0
SPRINT_K = 1.4        # decision 42: the body sprints by default, about 1.4x the walk (when movement.json names no sprint)
PLAIN_MAX_S = 35.0    # the longest plain walk a step may ask for (build 108: 12 of 30 trips past it, up to 118 s)
BACK_MIN_S = 20.0     # a trip out and straight back, both at least this long, is a back-and-forth
SECT_NAMES = {"jade_sect": "The Jade Sect", "cloud_sect": "The Cloud Sect"}


def _load(path):
    return json.load(open(path, encoding="utf-8"))


def pace():
    """Tiles a second at the sprint pace."""
    td = _load(os.path.join(DATA, "movement.json"))["topdown"]
    return float(td.get("sprint", float(td["walk"]) * SPRINT_K)) / TILE


class World:
    def __init__(self, arrays=True):
        self.arrays = arrays
        self.keyed = set()       # the array nodes the token knows (WorldAuthority.array_attuned)
        self._side = {}
        self._lay = {}
        self._grid = {}
        self._nodes = None

    def side(self, rid):
        if rid not in self._side:
            p = os.path.join(DATA, "rooms", rid + ".json")
            self._side[rid] = _load(p) if os.path.exists(p) else {}
        return self._side[rid]

    def layout(self, rid):
        if rid not in self._lay:
            p = os.path.join(DATA, "topdown", rid + ".json")
            d = _load(p) if os.path.exists(p) else None
            self._lay[rid] = d if d and "portals" in d and "id" in d else None
        return self._lay[rid]

    def grid(self, rid):
        if rid not in self._grid:
            self._grid[rid] = Grid(self.layout(rid))
        return self._grid[rid]

    # ------------------------------------------------------------ places
    def cell(self, rid, at):
        """A stop's cell: an object or NPC placement by id, "way:<id>" (the way's cell), "arrive:<id>" (where one
        arrives by it), "spawn", or [x, y]; the nearest cell a body stands on, at the thing's own height if it can."""
        lay = self.layout(rid)
        if isinstance(at, (list, tuple)):
            p = at
        elif at == "spawn":
            p = lay["spawn"]
        elif at.startswith("way:"):
            p = lay["portals"][at[4:]]["at"]
        elif at.startswith("arrive:"):
            w = lay["portals"][at[7:]]
            p = w.get("arrive") or _arrive(w)
        else:
            p = lay["place"][at]
        c = (int(math.floor(p[0] + 0.5)), int(math.floor(p[1] + 0.5)))
        return self._standable(rid, c)

    def _standable(self, rid, c):
        g = self.grid(rid)
        if g.floor(*c) is not None:
            return c
        for r in range(1, 6):
            best = None
            for y in range(c[1] - r, c[1] + r + 1):
                for x in range(c[0] - r, c[0] + r + 1):
                    if g.floor(x, y) is None:
                        continue
                    d = (x - c[0]) ** 2 + (y - c[1]) ** 2
                    if best is None or d < best[0] or (d == best[0] and g.floor(x, y) > g.floor(*best[1])):
                        best = (d, (x, y))
            if best:
                return best[1]
        return c

    def has(self, rid, at):
        lay = self.layout(rid)
        if lay is None:
            return False
        if isinstance(at, (list, tuple)) or at == "spawn":
            return True
        if at.startswith("way:") or at.startswith("arrive:"):
            return at.split(":", 1)[1] in lay["portals"]
        return at in lay["place"]

    def thing(self, rid, at):
        """The side-view room's object a place names ({} for a cell or a way)."""
        for o in self.side(rid).get("objects", []):
            if o["id"] == at:
                return o
        return {}

    # ------------------------------------------------------------ the path in a room
    def path(self, rid, a, b):
        """The auto-path's way between two cells (TopdownRoom.find_path's rules, a running hop over a one-tile gap
        allowed as the tutorial's climbs need it): its length in tiles, along the cells."""
        g = self.grid(rid)
        if a == b:
            return 0.0
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        cost_to = {a: 0.0}
        dist = {a: 0.0}
        q = [(0.0, a)]
        while q:
            _, cur = heapq.heappop(q)
            if cur == b:
                return dist[cur]
            h0 = g.floor(*cur)
            for dx, dy in dirs:
                nx = (cur[0] + dx, cur[1] + dy)
                h1 = g.floor(*nx)
                if h1 is None:
                    continue
                if dx and dy:
                    sx, sy = g.floor(cur[0] + dx, cur[1]), g.floor(cur[0], cur[1] + dy)
                    if sx is None or sy is None or sx > h0 + 8.0 or sy > h0 + 8.0:
                        continue
                step = 1.414 if dx and dy else 1.0
                cost = step
                rise = h1 - h0
                stairs = g.stair[nx[1]][nx[0]] or g.stair[cur[1]][cur[0]]
                if rise > (16.5 if stairs else 8.0):
                    if rise > 32.5:
                        continue
                    cost += 2.0
                self._relax(cost_to, dist, q, cur, nx, cost, step, b)
            for dx, dy in dirs[:4]:
                mx, nx = (cur[0] + dx, cur[1] + dy), (cur[0] + 2 * dx, cur[1] + 2 * dy)
                h1, hm = g.floor(*nx), g.floor(*mx)
                gap = g.level(*mx) == WATER or (hm is not None and hm < h0 - 8.0)
                if h1 is None or h1 - h0 > 8.0 or not gap:
                    continue
                self._relax(cost_to, dist, q, cur, nx, 3.0, 2.0, b)
        return float("inf")

    @staticmethod
    def _relax(cost_to, dist, q, cur, nx, cost, step, b):
        ng = cost_to[cur] + cost
        if ng < cost_to.get(nx, float("inf")):
            cost_to[nx] = ng
            dist[nx] = dist[cur] + step
            heapq.heappush(q, (ng + math.hypot(nx[0] - b[0], nx[1] - b[1]), nx))

    # ------------------------------------------------------------ the rooms between
    def nodes(self):
        """Every transfer array in the world, in room order: [(room, object)]."""
        if self._nodes is None:
            self._nodes = []
            for f in sorted(os.listdir(os.path.join(DATA, "rooms"))):
                rid = f[:-5]
                for o in self.side(rid).get("objects", []):
                    if o.get("type") == "transfer_array":
                        self._nodes.append((rid, o))
        return self._nodes

    def ways(self, rid, sect):
        """A room's ways out to rooms on the grid: its portals open at this stretch, then (with `arrays`) its transfer
        array's links to the other nodes of the sect's network the token knows: [(way, to room, arrival, array)]."""
        out = []
        if self.layout(rid) is None:
            return out
        for p in self.side(rid).get("portals", []):
            to = str(p.get("to", ""))
            if not to or self.layout(to) is None or not _open(p.get("requires"), sect):
                continue
            if self.side(to).get("sect") not in (None, "", sect):
                continue
            out.append((p["id"], to, "arrive:" + str(p.get("to_portal", "")), False))
        if self.arrays:
            for o in self.side(rid).get("objects", []):
                if o.get("type") != "transfer_array" or o.get("network", "") not in ("", sect) or o["id"] not in self.keyed:
                    continue
                for rid2, o2 in self.nodes():
                    if rid2 != rid and o2.get("network", "") in ("", sect) and o2["id"] in self.keyed:
                        out.append((o["id"], rid2, o2["id"], True))
        return out

    def route(self, a, b, sect):
        """The fewest ways from room a to room b (WorldRules.route): [(room, way, to, arrival, array)]."""
        if a == b:
            return []
        prev = {a: None}
        q = deque([a])
        while q:
            r = q.popleft()
            for wid, to, arrive, arr in self.ways(r, sect):
                if to in prev:
                    continue
                prev[to] = (r, wid, to, arrive, arr)
                if to == b:
                    out = []
                    at = b
                    while at != a:
                        out.insert(0, prev[at])
                        at = prev[at][0]
                    return out
                q.append(to)
        return None

    def trip(self, a, b, sect):
        """From stop a to stop b ((room, place) each): [(room, tiles)] walked, and the arrays taken."""
        ra, pa = a
        rb, pb = b
        rt = self.route(ra, rb, sect)
        if rt is None:
            raise SystemExit("no way from %s to %s for the %s" % (ra, rb, sect))
        legs = []
        here = self.cell(ra, pa)
        room = ra
        arrays = 0
        for (r, wid, to, arrive, arr) in rt:
            legs.append((r, self.path(r, here, self.cell(r, wid if arr else "way:" + wid))))
            arrays += 1 if arr else 0
            room = to
            here = self.cell(to, arrive)
        legs.append((room, self.path(room, here, self.cell(rb, pb))))
        return legs, arrays


def _arrive(w):
    v = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0)}[w["dir"]]
    return [w["at"][0] - v[0] * 1.5, w["at"][1] - v[1] * 1.5]


def _open(req, sect):
    """A way's lock at the sect stretch (Bone Forging 2-7, the Entry Trial under way or done): the chosen sect's road
    and trial and the realm doors of the stretch open; the rest shut (retreats, abodes, the Trial Tower past the gate,
    the quarry and the caravan road for their realms)."""
    if not req:
        return True
    for r in req.get("all", []):
        k = r.get("kind")
        if k == "training_sect" and r.get("sect") != sect:
            return False
        if k == "realm_at_least" and r.get("realm") not in ("bone_forging_2", "bone_forging_3"):
            return False
        if k in ("unlock", "flag_set") and r.get("system", r.get("flag")) not in ("night_survived",):
            return False
        if k in ("quest_done", "quest_accepted") and r.get("quest") not in ("entry_trial", "crab_trouble", "the_river_token"):
            return False
        if k == "quest_active" and r.get("quest") != "entry_trial":
            return False
    return True


# ==================================================================== the itineraries
def stop(quest, what, room, place, wayside=False, keys=(), person=""):
    """A stop of the stretch: `keys` are the array nodes the token knows from here on (the lesson, the mentor's peak);
    `person` the quest's giver or hand-in the stop is (checked against the quest's data)."""
    return {"quest": quest, "what": what, "room": room, "place": place, "wayside": wayside, "keys": tuple(keys), "person": person}


def _sect(sect):
    j = sect == "jade_sect"
    return {
        "tag": "ja" if j else "cm",
        "gate": "ja_gate_street" if j else "cm_cliff_stair", "steward": "npc_jade_steward" if j else "npc_cloud_steward",
        "hall": "ja_weapon_hall" if j else "cm_weapon_hall", "master": "npc_jade_weapon_master" if j else "npc_cloud_weapon_master",
        "dummy": "dummy_wh_0" if j else "dummy_cwh_0",
        "peak": "ja_elder_hu_peak" if j else "cm_elder_sung_peak", "mentor": "npc_elder_hu" if j else "npc_elder_sung",
        "mentor_npc": "elder_hu" if j else "elder_sung",
        "trial": "sf_trial_jade" if j else "sf_trial_cloud", "recruiter": "npc_recruiter_qing_lan" if j else "npc_recruiter_mo_yun",
        "sweep": "sweep_ja_%d" if j else "sweep_cm_%d",
        "yard": "ja_pavilion_rooftops" if j else "cm_sword_court", "spar": "spar_jp" if j else "spar_cm",
        "hall_master": "npc_jade_hall_master" if j else "npc_cloud_hall_master"}


def _to_the_hall(s):
    return [
        stop("The Recruitment Fair", "the sect chosen", "sf_fairground", s["recruiter"]),
        stop("Entry Trial", "the trial bell", s["trial"], "trial_bell"),
        stop("Entry Trial", "the Trial Puppet", s["trial"], [29, 16]),
        stop("Fish-Gutting Fists", "Shen Lian", "sf_fairground", "npc_shen_lian", person="shen_lian"),
        stop("A Disciple's Chores (side)", "the steward", s["gate"], s["steward"]),
        stop("A Disciple's Chores (side)", "the first spot", s["gate"], s["sweep"] % 0),
        stop("A Disciple's Chores (side)", "the second spot", s["gate"], s["sweep"] % 1),
        stop("A Disciple's Chores (side)", "the grey stain", s["gate"], s["sweep"] % 2),
        stop("A Disciple's Chores (side)", "hand in", s["gate"], s["steward"]),
        stop("The Weapon Hall", "the weapon master", s["hall"], s["master"]),
        stop("The Weapon Hall", "the dummies", s["hall"], s["dummy"]),
        stop("The Weapon Hall", "hand in", s["hall"], s["master"])]


def before(sect):
    """The stretch as it was before decision 42 (build 108): Strange Tracks at the marsh and back to the mentor, The
    Humming Token out to the marsh and back, Mei Qing's Errand from Artisan Row to the marsh and back, Grey at the Edges
    at the mentor, the Level hunt, The First Current at the Lotus Ferry, and the two lessons inside the prototype."""
    s = _sect(sect)
    return _to_the_hall(s) + [
        stop("Strange Tracks", "the first grey patch", "rm_marsh_edge", "grey_patch_0"),
        stop("Strange Tracks", "the second", "rm_marsh_edge", "grey_patch_1"),
        stop("Strange Tracks", "the third", "rm_marsh_edge", "grey_patch_2"),
        stop("Strange Tracks", "hand in to the mentor", s["peak"], s["mentor"]),
        stop("The Humming Token", "the Hollowed Boarlets", "rm_marsh_edge", [33, 17]),
        stop("The Humming Token", "hand in to the mentor", s["peak"], s["mentor"]),
        stop("Mei Qing's Errand", "Mei Qing", "sf_artisan_row", "npc_mei_qing"),
        stop("Mei Qing's Errand", "reed frogs (moss), boarlets (hides)", "rm_marsh_edge", [33, 17]),
        stop("Mei Qing's Errand", "hand in", "sf_artisan_row", "npc_mei_qing"),
        stop("Grey at the Edges", "report to the mentor", s["peak"], s["mentor"]),
        stop("(the Level)", "hunt to Bone Forging 7", "rm_marsh_edge", [33, 17]),
        stop("The First Current", "Lu", "lf_village", "npc_lu_boatman"),
        stop("The First Current", "the Qi spring", "lf_village", "spring_village"),
        stop("The First Current", "hand in", "lf_village", "npc_lu_boatman"),
        stop("Eyes for Qi (lesson)", "the mentor", s["peak"], s["mentor"]),
        stop("Eyes for Qi (lesson)", "meditate, moss", "lf_reed_shallows", [30, 14]),
        stop("Eyes for Qi (lesson)", "hand in", s["peak"], s["mentor"]),
        stop("Outer Trial (lesson)", "three spars", s["yard"], s["spar"]),
        stop("Outer Trial (lesson)", "hand in to the mentor", s["peak"], s["mentor"])]


def after(sect):
    """The stretch now: the Weapon Hall done, the steward shows the gate's transfer array (the token knows it and the
    Marsh Edge's watch post); Strange Tracks, The Humming Token (the mentor comes down to the marsh for it) and Mei Qing's
    Errand (at the watch post) all at the marsh; Grey at the Edges the first walk up through the grounds with something
    on the way in each room (the mentor then keys his peak's array); the hunt, The First Current and the lessons by the
    arrays (the Outer Trial handed in to the hall master in the yard where it is won)."""
    s = _sect(sect)
    t = s["tag"]
    j = sect == "jade_sect"
    up = [
        stop("(on the way)", "the hall master offers a spar", s["yard"], s["spar"], wayside=True),
        stop("(on the way)", "two elders overheard on the terrace", "ja_east_terrace", "npc_jade_formation_elder", wayside=True),
        stop("Tea for the Elder (side, on the way)", "the gardener's favour", "ja_herb_terraces", "npc_jade_gardener", wayside=True,
             person="jade_gardener")] if j else [
        stop("(on the way)", "the hall master offers a spar", s["yard"], s["spar"], wayside=True),
        stop("Tea for the Elder (side, on the way)", "the gardener's favour", "cm_array_court", "npc_cloud_gardener", wayside=True,
             person="cloud_gardener"),
        stop("(on the way)", "two elders overheard in the court", "cm_array_court", "npc_cloud_formation_elder", wayside=True)]
    hall = _to_the_hall(s)
    hall[-1] = dict(hall[-1], keys=("array_%s_gate" % t, "array_marsh"))
    return hall + [
        stop("Strange Tracks", "the steward's lesson: the gate's transfer array", s["gate"], "array_%s_gate" % t),
        stop("Strange Tracks", "the first grey patch (by the array)", "rm_marsh_edge", "grey_patch_0"),
        stop("Strange Tracks", "the second", "rm_marsh_edge", "grey_patch_1"),
        stop("Strange Tracks", "the third: the token hums", "rm_marsh_edge", "grey_patch_2"),
        stop("The Humming Token", "the Hollowed Boarlets, here", "rm_marsh_edge", [33, 17]),
        stop("The Humming Token", "hand in: the mentor comes down", "rm_marsh_edge", "npc_%s_marsh" % s["mentor_npc"], person=s["mentor_npc"]),
        stop("Mei Qing's Errand", "Mei Qing at the watch post", "rm_marsh_edge", "npc_mei_qing_marsh", person="mei_qing"),
        stop("Mei Qing's Errand", "reed frogs (moss), boarlets (hides)", "rm_marsh_edge", [33, 17]),
        stop("Mei Qing's Errand", "hand in at the watch post", "rm_marsh_edge", "npc_mei_qing_marsh", person="mei_qing"),
    ] + up + [
        stop("Grey at the Edges", "report to the mentor (and the tea)", s["peak"], s["mentor"], keys=("array_%s_peak" % t,),
             person=s["mentor_npc"]),
        stop("(the Level)", "hunt to Bone Forging 7", "rm_marsh_edge", [33, 17]),
        stop("The First Current", "Lu", "lf_village", "npc_lu_boatman", person="lu_boatman"),
        stop("The First Current", "the Qi spring", "lf_village", "spring_village"),
        stop("The First Current", "hand in", "lf_village", "npc_lu_boatman", person="lu_boatman"),
        stop("Eyes for Qi (lesson)", "the mentor", s["peak"], s["mentor"], person=s["mentor_npc"]),
        stop("Eyes for Qi (lesson)", "meditate, moss", "lf_reed_shallows", [30, 14]),
        stop("Eyes for Qi (lesson)", "hand in", s["peak"], s["mentor"], person=s["mentor_npc"]),
        stop("Outer Trial (lesson)", "three spars", s["yard"], s["spar"]),
        stop("Outer Trial (lesson)", "hand in to the hall master", s["yard"], s["hall_master"],
             person=("jade" if j else "cloud") + "_hall_master")]


ITINERARY = {"before": before, "after": after}
# The quests of the stretch: each has its stops in the itinerary (the lessons inside the prototype are its last).
STRETCH = ["Entry Trial", "Fish-Gutting Fists", "The Weapon Hall", "Strange Tracks", "The Humming Token", "Mei Qing's Errand",
           "Grey at the Edges", "The First Current", "Eyes for Qi (lesson)", "Outer Trial (lesson)"]


# ==================================================================== measuring
def measure(sect, stops, world):
    v = pace()
    rows = []
    world.keyed = set(stops[0]["keys"])
    for i in range(1, len(stops)):
        a, b = stops[i - 1], stops[i]
        legs, arrays = world.trip((a["room"], a["place"]), (b["room"], b["place"]), sect)
        world.keyed |= set(b["keys"])
        tiles = sum(t for _, t in legs)
        rows.append({"i": i, "quest": b["quest"], "what": b["what"], "from": a["room"], "to": b["room"], "rooms": [r for r, _ in legs],
                     "tiles": tiles, "s": tiles / v, "arrays": arrays, "wayside": b["wayside"]})
    return rows


def back_and_forth(rows):
    """Trips straight back to the room the trip before came from, both long: [(i, j, from, to)]."""
    out = []
    for k in range(1, len(rows)):
        a, b = rows[k - 1], rows[k]
        if a["to"] != a["from"] and b["to"] == a["from"] and a["s"] >= BACK_MIN_S and b["s"] >= BACK_MIN_S:
            out.append((a["i"], b["i"], a["from"], a["to"]))
    return out


def room_name(world, rid):
    return str(world.side(rid).get("name", rid))


def table(rows, world):
    lines = ["| # | Quest | To | Rooms walked | Plain walk |", "|---|---|---|---|---|"]
    for r in rows:
        rooms = r["rooms"]
        n = len(rooms)
        route = " → ".join(room_name(world, x) for x in rooms) if n <= 3 else "%s → … (%d rooms) → %s" % (
            room_name(world, rooms[0]), n - 2, room_name(world, rooms[-1]))
        if r["arrays"]:
            route += " (by array)"
        what = r["what"] + (" *(on the way)*" if r["wayside"] and "on the way" not in r["quest"] else "")
        lines.append("| %d | %s | %s | %s | %.0f s |" % (r["i"], r["quest"], what, route, r["s"]))
    lines.append("")
    lines.append(summary(rows, world))
    return "\n".join(lines)


def summary(rows, world):
    total = sum(r["s"] for r in rows)
    long_ = [r for r in rows if r["s"] > PLAIN_MAX_S]
    bf = back_and_forth(rows)
    rooms = sum(len(r["rooms"]) for r in rows)
    return ("Total plain walking %.0f s (%.1f min) over %d trips and %d rooms walked; %d trips over %.0f s; the longest %.0f s; "
            "back-and-forth: %s." % (total, total / 60.0, len(rows), rooms, len(long_), PLAIN_MAX_S, max(r["s"] for r in rows),
                                     ", ".join("%d-%d (%s ↔ %s)" % (x[0], x[1], room_name(world, x[2]), room_name(world, x[3])) for x in bf) or "none"))


# ==================================================================== the check
def check_data(sect, stops, world):
    """Every stop's person or thing stands where the itinerary says, a stop marked with a person is that quest's giver or
    hand-in, and every quest of the stretch has its stops."""
    errs = []
    quests = {q["name"]: q for q in _load(os.path.join(DATA, "quests.json"))["entries"]}
    scenes = _load(os.path.join(DATA, "scenes.json"))["entries"]
    for st in stops:
        where = "%s: %s (%s)" % (sect, st["what"], st["quest"])
        if not world.has(st["room"], st["place"]):
            errs.append("%s: %s is not placed in %s" % (where, st["place"], st["room"]))
            continue
        o = world.thing(st["room"], st["place"]) if isinstance(st["place"], str) else {}
        if st["person"]:
            if o.get("npc") != st["person"]:
                errs.append("%s: %s in %s is not %s" % (where, st["place"], st["room"], st["person"]))
            name = st["quest"].split(" (")[0]
            q = quests.get(name) or quests.get(st["quest"])
            if q is not None:
                who = set(q.get("giver_any", [q.get("giver")])) | set(q.get("hand_in_any", [q.get("hand_in")]))
                if st["person"] not in who:
                    errs.append("%s: %s neither gives nor takes %s" % (where, st["person"], name))
        if st["wayside"] and not any(sc["room"] == st["room"] and (sc.get("requires", {}).get("all", []) and any(
                c.get("sect") == sect for c in sc["requires"]["all"] if c.get("kind") == "training_sect")) for sc in scenes):
            errs.append("%s: nothing staged for it in %s (data/scenes.json)" % (where, st["room"]))
        for k in st["keys"]:
            if not any(o2["id"] == k for _, o2 in world.nodes()):
                errs.append("%s: no transfer array %s" % (where, k))
    have = {st["quest"] for st in stops}
    for name in STRETCH:
        if name not in have:
            errs.append("%s: no stop of %s" % (sect, name))
    for name in [n.split(" (")[0] for n in STRETCH]:
        if name not in quests:
            errs.append("%s: quest %s is not in the data" % (sect, name))
    return errs


def check(world):
    errs = []
    for sect in SECT_NAMES:
        stops = after(sect)
        errs += check_data(sect, stops, world)
        rows = measure(sect, stops, world)
        for r in rows:
            if r["s"] > PLAIN_MAX_S:
                errs.append("%s: trip %d (%s: %s) is %.0f s of plain walking (%s), more than %.0f s with nothing on the way"
                            % (sect, r["i"], r["quest"], r["what"], r["s"], " → ".join(r["rooms"]), PLAIN_MAX_S))
        for x in back_and_forth(rows):
            errs.append("%s: trips %d and %d go from %s to %s and straight back" % (sect, x[0], x[1], x[2], x[3]))
    return errs


def main(argv):
    if "--check" in argv:
        errs = check(World())
        if errs:
            raise SystemExit("sect_walks:\n  " + "\n  ".join(errs))
        print("sect_walks: both sects' stretches hold (no plain walk over %.0f s, no back-and-forth)" % PLAIN_MAX_S)
        return
    mode = "before" if "--before" in argv else "after"
    world = World(arrays=(mode != "before"))
    for sect in SECT_NAMES:
        rows = measure(sect, ITINERARY[mode](sect), world)
        print("### %s (%s)\n" % (SECT_NAMES[sect], mode))
        print(table(rows, world))
        print()


if __name__ == "__main__":
    main(sys.argv[1:])
