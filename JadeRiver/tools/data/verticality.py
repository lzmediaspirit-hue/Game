"""S43 rule 14: the verticality pass (Build Prompt v2, Part 8 room verticality catalogue).

Runs over every built room after the movement pass and brings it to the verticality rules that
tools/data/room_lint.py checks:
  - standard heights: natural ledges in 100s, built decks in 88s (roofs keep their art and get ladders);
  - landings at least 80 wide and 60 deep (shallow platforms grow into the back of the room);
  - wide field, path and town rooms get a raised route of chained tiers across 40% of the width;
  - every required raised tier has two ways up (a jump, a ladder, rope or vine, a step block);
  - a third of gathering nodes and 30% of breakables sit on raised tiers; chests on the highest tier;
  - reward ledges out of the room band's reach become "later" ledges for a named art (Paths Above).
Rooms marked vertical="authored" were built by hand to their catalogue row and are left alone.
"""
import math

STD_BLOCKS = (40, 60, 80, 110)
NATURAL = {"rock_ledge", "branch", "cloud", "tree_branch"}
BUILT = {"balcony", "deck"}
WALKWAYS = {"bridge", "rope_bridge", "walkway"}
BREAKABLES = {"jar", "crate", "wine_jar"}
NODES = {"herb_patch", "ore_vein"}
LINT_TYPES = {"field", "path", "town"}
LATER_ART = [("double_jump", 202), ("wall_step", 370), ("flight", 340)]


def band(level):
    """(required rise, required gap, flight) for a room whose lowest level is `level` (S43 reach table)."""
    rise = 160 if level >= 24 else 100
    gap = 300 if level >= 24 else (250 if level >= 16 else 150)
    return rise, gap, level >= 37


class T:
    """A raised surface or block, as the pass sees it."""

    def __init__(self, d, block=False):
        self.d = d
        self.block = block

    @property
    def id(self): return self.d["id"]

    @property
    def rect(self): return self.d["rect"]

    @property
    def h(self): return float(self.d.get("top", self.d.get("height", 0)))

    @property
    def x0(self): return self.rect[0]

    @property
    def x1(self): return self.rect[0] + self.rect[2]

    @property
    def y0(self): return self.rect[1]

    @property
    def y1(self): return self.rect[1] + self.rect[3]

    def gap_to(self, o):
        dx = max(0, max(self.x0, o.x0) - min(self.x1, o.x1))
        dy = max(0, max(self.y0, o.y0) - min(self.y1, o.y1))
        return math.hypot(dx, dy)

    def later(self):
        return self.d.get("later") or self.d.get("optional")


def tiers(r, include_blocks=True):
    out = []
    for s in r.d["surfaces"]:
        if s.get("stratum") == "ground" or s.get("kind") in ("ladder", "stairs", "ramp"):
            continue
        out.append(T(s, block=s.get("kind") == "support"))
    if include_blocks:
        for b in r.d.get("blocks", []):
            if float(b.get("top", 0)) <= 110:
                out.append(T(b, block=True))
    return out


def ground_tiers(r):
    return [T(s) for s in r.d["surfaces"] if s.get("stratum") == "ground" and float(s.get("height", 0)) <= 0.5]


def _objects_on(r, t, alt):
    x0, y0, x1, y1 = t.x0, t.y0 - 12, t.x1, t.y1 + 12
    return [o for o in r.d["objects"] if x0 <= o["at"][0] <= x1 and y0 <= o["at"][1] <= y1 and abs(float(o.get("alt", 0)) - alt) < 1.0]


def _clear(r, x, y, radius, ignore=()):
    pts = [p["at"] for p in r.d["portals"] if "at" in p] + [o["at"] for o in r.d["objects"] if o["id"] not in ignore] + [r.d["spawn_point"]]
    for sp in r.d["spawns"]:
        pts += sp["points"]
    return all(math.hypot(x - a[0], y - a[1]) >= radius for a in pts)


def _climbable_near(r, x, y, radius=50):
    for c in r.d.get("climbables", []):
        if math.hypot(c["at"][0] - x, c["at"][1] - y) < radius:
            return True
    return False


# ------------------------------------------------------------------ 1. standard heights and landings
def normalize(r):
    by = r.d["bounds"][1]
    # A tier reached by an authored ladder or rope keeps the height its catalogue row gives it (the library floors at
    # 120 and 240, the Caravan Road ledge at 120), and a moving surface keeps its own: snapping either would leave the
    # climbable's top or the mover's path at the old height.
    climb_tops = {c.get("top") for c in r.d.get("climbables", [])} | {c.get("bottom") for c in r.d.get("climbables", [])}
    moving = {m.get("surface") for m in r.d.get("movers", [])}
    for s in r.d["surfaces"]:
        if s.get("stratum") != "platform" or s.get("kind") in ("ladder", "support", "roof") or s.get("later"):
            continue
        keep = s["id"] in climb_tops or s["id"] in moving
        old = float(s["height"])
        new = old
        if keep:
            pass
        elif s["kind"] in NATURAL and (old < 300 or s["kind"] != "cloud"):
            new = max(100, int(round(old / 100.0)) * 100)
        elif s["kind"] in BUILT:
            new = max(88, int(round(old / 88.0)) * 88)
        if new != old:
            t = T(s)
            for o in _objects_on(r, t, old):
                o["alt"] = new
            s["height"] = new
        x, y, w, h = s["rect"]
        if h < 60:
            grow = 70 - h
            s["rect"] = [x, y - grow if y - grow >= by + 10 else y, w, 70]
        if w < 80 and not s.get("later"):
            s["rect"][2] = 80


# ------------------------------------------------------------------ 2. reach and later ledges
def reachable(r, rise, gap):
    """Tier ids reachable from the ground with the band's limits, ladders and movers."""
    all_t = tiers(r) + ground_tiers(r)
    by_id = {t.id: t for t in all_t}
    seen = {t.id for t in ground_tiers(r)}
    todo = [by_id[i] for i in seen]
    climb = {}
    for c in r.d.get("climbables", []):
        climb.setdefault(c.get("bottom") or "ground", []).append(c.get("top", ""))
        climb.setdefault(c.get("top", ""), []).append(c.get("bottom") or "ground")
    movers = {m["surface"] for m in r.d.get("movers", [])}
    while todo:
        a = todo.pop()
        for b in all_t:
            if b.id in seen:
                continue
            ok = False
            if b.h <= a.h - 8:
                ok = a.gap_to(b) <= max(gap, 70) or (min(a.y1, b.y1) - max(a.y0, b.y0) > 0 and min(a.x1, b.x1) - max(a.x0, b.x0) > 0)
            elif b.h - a.h <= rise + 0.5 and a.gap_to(b) <= gap:
                ok = True
            if not ok and b.id in climb.get(a.id, []):
                ok = True
            if not ok and b.id in movers and a.gap_to(b) <= gap:
                ok = True
            if ok:
                seen.add(b.id)
                todo.append(b)
    return seen


def mark_later(r, rise, gap, flight):
    """Reward ledges (a chest on them, or built as flight ledges) out of the band's reach become 'later'."""
    if flight:
        return   # from Cloud Stride 1 anything below the ceiling is in reach
    seen = reachable(r, rise, gap)
    all_t = tiers(r)
    for t in all_t:
        if t.block or t.id in seen or t.later():
            continue
        rewards = [o for o in _objects_on(r, t, t.h) if o["type"] in ("chest", "pickup")]
        is_reward = bool(rewards) or t.d.get("kind") == "cloud" or t.id.endswith("_mv_1")
        if not is_reward:
            continue
        below = max([u.h for u in all_t if u.id in seen and u.h < t.h and u.gap_to(t) <= 300 and not u.block] + [0.0])
        above = t.h - below
        for art, art_rise in LATER_ART:
            if art == "double_jump" and rise >= 160:
                continue
            if art == "flight" and flight:
                continue
            limit = 202 if rise >= 160 else 122
            if limit < above <= art_rise:
                t.d["later"] = art
                break


# ------------------------------------------------------------------ 3. a raised route across wide rooms
def route_span(r, rise, gap):
    req = [t for t in tiers(r, include_blocks=False) if not t.later() and t.h >= 1]
    best = 0
    seen = set()
    for t in req:
        if t.id in seen:
            continue
        comp = [t]
        seen.add(t.id)
        i = 0
        while i < len(comp):
            a = comp[i]
            for b in req:
                if b.id not in seen and abs(b.h - a.h) <= rise + 0.5 and a.gap_to(b) <= gap:
                    seen.add(b.id)
                    comp.append(b)
            i += 1
        best = max(best, max(c.x1 for c in comp) - min(c.x0 for c in comp))
    return best


def _band_free(r, x0, x1, y0, y1, pad=30):
    """Nothing in the back band between x0 and x1 that a tier would cover: doors and gates, people and
    stations, other tiers, buildings and blocks. Jars, herbs and ore on the ground may sit under a tier."""
    for p in r.d["portals"]:
        if "at" in p and x0 - pad - 60 <= p["at"][0] <= x1 + pad + 60 and p["at"][1] < y1 + 60:
            return False
    for o in r.d["objects"]:
        if o["type"] in BREAKABLES or o["type"] in NODES or o["type"] == "chest":
            continue
        if x0 - pad <= o["at"][0] <= x1 + pad and o["at"][1] < y1 + 40 and float(o.get("alt", 0)) == 0:
            return False
    for s in r.d["surfaces"]:
        if s.get("stratum") == "ground":
            continue
        a, b = s["rect"][0], s["rect"][0] + s["rect"][2]
        if not (x1 + pad < a or x0 - pad > b):
            return False
    for b in r.d.get("blocks", []):
        bx, bw = b["rect"][0], b["rect"][2]
        if not (x1 + pad < bx or x0 - pad > bx + bw):
            return False
    return True


def _under(sc, x0, x1, front):
    """Back-row scenery (a tree, a rock) standing where a new tier goes. Standable props (crates, stumps) and
    anything whose base is in front of the tier stay."""
    fx, fy, fw, fd = sc["footprint"]
    return not sc.get("standable") and not (x1 < fx or x0 > fx + fw) and fy + fd < front


def add_route(r, rise, gap):
    """Chain tiers across the back of the room until a raised route spans 40% of the width."""
    w = r.w
    if route_span(r, rise, gap) >= 0.4 * w:
        return 0
    town = r.d["type"] == "town"
    material = r.d.get("material", "")
    # Painted platform art: rock shelves on stone, snow and sand; leafy branches elsewhere; timber balconies in towns.
    kind = "balcony" if town else ("rock_ledge" if material in ("stone", "slate", "rock", "snow", "sand", "floor_stone", "earth") else "tree_branch")
    heights = (88, 176, 264) if town else (100, 200, 300)
    width, step = (220, 90) if town else (240, 100)
    step = min(step, gap - 10)
    y0 = 636
    depth = 70
    added = 0
    chain = []
    x = 180
    n = 0
    while x + width < w - 180:
        if _band_free(r, x, x + width, y0, y0 + depth):
            # Match the nearest tier already in jumping distance (a roof, the last tier placed), one step up or down.
            probe = T({"id": "_probe", "rect": [x, y0, width, depth], "height": 0})
            near = [t for t in tiers(r, include_blocks=False) if not t.later() and t.gap_to(probe) <= gap]
            prev = max(near, key=lambda t: t.x1).h if near else 0.0
            ok = [c for c in heights if abs(c - prev) <= rise and c <= prev + rise]
            h = next((c for c in ok if c != prev), ok[0] if ok else heights[0])
            sid = "route_%d" % n
            # Back-row trees and rocks under the new tier give way to it.
            r.d["scenery"] = [sc for sc in r.d.get("scenery", []) if not _under(sc, x - 20, x + width + 20, y0 + depth + 20)]
            r.surface(sid, [x, y0, width, depth], h, kind=kind)
            chain.append((x, h))
            n += 1
            added += 1
            if route_span(r, rise, gap) >= 0.42 * w:
                break
            x += width + step
        else:
            # An obstacle breaks the chain; continue past it, starting a new chain at ground reach.
            if chain and x - (chain[-1][0] + width) > gap:
                chain = []
            x += 60
    if route_span(r, rise, gap) < 0.4 * w:
        added += bridge_gaps(r, rise, gap)
    return added


def second_tier(r, rise, gap):
    """A wide room with raised tiers all at one height gets a higher ledge beside one of them (S43: two tiers)."""
    req = [t for t in tiers(r, include_blocks=False) if not t.later() and t.h >= 60]
    if len({round(t.h) for t in req}) != 1:
        return 0
    base = max(req, key=lambda t: t.x1 - t.x0)
    natural = base.d.get("kind") in NATURAL
    h = base.h + (100 if natural else 88)
    if h - base.h > rise:
        return 0
    for t in sorted(req, key=lambda t: -(t.x1 - t.x0)):
        for x in (t.x1 + 80, t.x0 - 80 - 200):
            if x < 150 or x + 200 > r.w - 150:
                continue
            if _band_free(r, x, x + 200, t.y0, t.y1, pad=10):
                r.surface("upper_%s" % t.id, [int(x), int(t.y0), 200, max(70, int(t.y1 - t.y0))], t.h + (h - base.h),
                          kind=t.d.get("kind", "rock_ledge"))
                return 1
    return 0


def _components(r, rise, gap):
    req = [t for t in tiers(r, include_blocks=False) if not t.later() and t.h >= 1]
    comps, seen = [], set()
    for t in req:
        if t.id in seen:
            continue
        comp = [t]
        seen.add(t.id)
        i = 0
        while i < len(comp):
            a = comp[i]
            for b in req:
                if b.id not in seen and abs(b.h - a.h) <= rise + 0.5 and a.gap_to(b) <= gap:
                    seen.add(b.id)
                    comp.append(b)
            i += 1
        comps.append(comp)
    return comps


def bridge_gaps(r, rise, gap, longest=520):
    """Rope bridges between neighbouring roofs and ledges too far apart to jump (a street, a ravine).
    A bridge hangs at the lower tier's height, so it is one jump from the higher; it spans the gap only."""
    added = 0
    for n in range(12):
        if route_span(r, rise, gap) >= 0.42 * r.w:
            break
        comps = sorted(_components(r, rise, gap), key=lambda c: min(t.x0 for t in c))
        best = None
        for i, ca in enumerate(comps):
            for cb in comps[i + 1:]:
                for a in ca:
                    for b in cb:
                        lo, hi = (a, b) if a.x1 <= b.x0 else (b, a)
                        g = hi.x0 - lo.x1
                        overlap = min(a.y1, b.y1) - max(a.y0, b.y0)
                        if not (gap < g <= longest) or overlap < 40 or abs(a.h - b.h) > rise + 0.5:
                            continue
                        y0 = max(a.y0, b.y0)
                        # Nothing raised hangs in the gap already.
                        if any(t.x1 > lo.x1 and t.x0 < hi.x0 and min(t.y1, y0 + 70) - max(t.y0, y0) > 0
                               for t in tiers(r) if t.id not in (a.id, b.id)):
                            continue
                        gain = max(t.x1 for t in ca + cb) - min(t.x0 for t in ca + cb)
                        if best is None or (gain, -g) > (best[0], -best[1]):
                            best = (gain, g, lo, hi, y0, max(60, min(overlap, 70)))
        if best is None:
            break
        _, g, lo, hi, y0, depth = best
        h = min(lo.h, hi.h)
        x0, x1 = lo.x1, hi.x0
        r.d["scenery"] = [sc for sc in r.d.get("scenery", []) if not _under(sc, x0 - 10, x1 + 10, y0 + depth + 20)]
        r.surface("bridge_%d" % n, [int(x0), int(y0), int(x1 - x0), int(depth)], h, kind="rope_bridge")
        added += 1
    return added


# ------------------------------------------------------------------ 4. two ways up
def ways(r, t, rise, gap):
    out = []
    movers = {m["surface"] for m in r.d.get("movers", [])}
    for o in tiers(r) + ground_tiers(r):
        if o.id == t.id or o.later():
            continue
        if abs(o.h - t.h) <= 8 and not o.block and o.gap_to(t) <= 60 and (WALKWAYS & {o.d.get("kind"), t.d.get("kind")} and o.gap_to(t) <= 2 or t.id in movers):
            out.append("walk:" + o.id)
            continue
        if o.h >= t.h - 8:
            continue
        if t.h - o.h <= rise + 0.5 and o.gap_to(t) <= gap:
            out.append("jump:" + o.id)
    for c in r.d.get("climbables", []):
        if c.get("top") == t.id:
            out.append("climb:" + c["id"])
    if t.id in {m["surface"] for m in r.d.get("movers", [])}:
        out.append("mover")
    return out


def _climb_kind(t):
    k = t.d.get("kind", "")
    if k in ("rock_ledge", "cloud"):
        return "rope"
    if k in ("branch", "tree_branch", "pole", "canopy"):
        return "vine"
    return "ladder"


def add_climbable(r, t, n):
    """A ladder, rope or vine from the ground to the tier's front edge, clear of doors and other climbables."""
    front = t.y1
    cx = (t.x0 + t.x1) / 2
    narrow = t.x1 - t.x0 < 140
    for dx in (0, -40, 40, -80, 80, -120, 120, -160, 160, -200, 200, -240, 240):
        x = int(cx + dx)
        if x < t.x0 + 16 or x > t.x1 - 16:
            continue
        if _climbable_near(r, x, front + 35, 30 if narrow else 50) or not _clear(r, x, front + 35, 40):
            continue
        r.ladder("%s_%s_%d" % (t.id, _climb_kind(t), n), x, front, int(t.h), kind=_climb_kind(t), bottom="ground", top=t.id)
        return True
    return False


def add_step(r, t, rise, n):
    """A step block in front of the tier: a crate stack or boulder one jump below it."""
    need = t.h - rise
    top = next((b for b in STD_BLOCKS if b >= need and b <= 100), None)
    if top is None:
        return False
    kind = "rock" if t.d.get("kind") in ("rock_ledge", "branch", "tree_branch") else "crate"
    for x in (t.x1 - 70, t.x0 + 10, (t.x0 + t.x1) // 2 - 30):
        y = t.y1 + 12
        if not _clear(r, x + 30, y + 25, 70) or _climbable_near(r, x + 30, y + 25, 60):
            continue
        if any(not (x + 60 < b["rect"][0] or x > b["rect"][0] + b["rect"][2] or y + 50 < b["rect"][1] or y > b["rect"][1] + b["rect"][3])
               for b in r.d.get("blocks", [])):
            continue
        r.solid("%s_step_%d" % (t.id, n), [int(x), int(y), 60, 50], top, kind=kind)
        return True
    return False


def add_step_ledge(r, t, rise, n):
    """A lower ledge beside a high natural tier, one jump below it (on the 100 grid)."""
    h = math.ceil((t.h - min(rise, 100)) / 100.0) * 100
    if h < 100 or h >= t.h:
        return False
    kind = t.d.get("kind", "rock_ledge")
    for x in (t.x0 - 160 - 60, t.x1 + 60):
        if x < 150 or x + 160 > r.w - 150:
            continue
        if _band_free(r, x, x + 160, t.y0, t.y1, pad=10):
            r.surface("%s_step_ledge_%d" % (t.id, n), [int(x), int(t.y0), 160, max(70, int(t.y1 - t.y0))], h, kind=kind)
            return True
    return False


def two_ways(r, rise, gap):
    for sweep in range(3):   # a step ledge added for one tier needs its own second way
        _two_ways(r, rise, gap, sweep * 100)


def _two_ways(r, rise, gap, n):
    for t in tiers(r, include_blocks=False):
        if t.later() or t.block:
            continue
        # A roof off the 88 grid is reached by ladder (S43: ladder-reached surfaces may use any height).
        if t.d.get("kind") == "roof" and round(t.h) % 88 != 0 and not any(x.startswith("climb") for x in ways(r, t, rise, gap)):
            n += 1
            add_climbable(r, t, n)
        for attempt in range(4):
            w = ways(r, t, rise, gap)
            if len(w) >= 2:
                break
            n += 1
            has_climb = any(x.startswith("climb") for x in w)
            if not has_climb and add_climbable(r, t, n):
                continue
            if add_step(r, t, rise, n):
                continue
            if t.d.get("kind") in NATURAL and add_step_ledge(r, t, rise, n):
                continue
            add_climbable(r, t, n + 100)


# ------------------------------------------------------------------ 5. things worth climbing for
def _spots(r, t, count, taken):
    """Up to `count` places on a tier, each at least 40 from anything already there."""
    out = []
    y = int((t.y0 + t.y1) / 2)
    cands = list(range(int(t.x0) + 30, int(t.x1) - 29, 10))
    while len(out) < count and cands:
        best = max(cands, key=lambda x: min([abs(x - a) for a in taken + out] + [9999]))
        if min([abs(best - a) for a in taken + out] + [9999]) < 40:
            break
        out.append(best)
    return [(x, y) for x in out]


def lift_objects(r):
    req = [t for t in tiers(r, include_blocks=False) if not t.later() and t.h > 0 and (t.x1 - t.x0) >= 80]
    if not req:
        return
    taken = {t.id: [o["at"][0] for o in _objects_on(r, t, t.h)] for t in req}
    story_keys = ("hidden_if", "visible_if", "set_flag", "event", "npc", "quest")
    plain = lambda o: not any(k in o for k in story_keys) and (float(o.get("alt", 0)) == 0 or o["type"] == "chest") and (
        "requires" not in o or o["type"] in NODES)

    def lift(kinds, share):
        objs = [o for o in r.d["objects"] if o["type"] in kinds]
        if len(objs) < 2:
            return
        need = math.ceil(share * len(objs)) - sum(1 for o in objs if float(o.get("alt", 0)) > 0)
        i = 0
        for o in [o for o in objs if plain(o)]:
            if need <= 0:
                break
            t = req[i % len(req)]
            i += 1
            spots = _spots(r, t, 1, taken[t.id])
            if not spots:
                continue
            o["at"] = [spots[0][0], spots[0][1]]
            o["alt"] = int(t.h)
            taken[t.id].append(spots[0][0])
            need -= 1

    lift(BREAKABLES, 0.3)
    lift(NODES, 1.0 / 3.0)
    tops = [t for t in tiers(r, include_blocks=False) if not t.later() and t.h > 0 and (t.x1 - t.x0) >= 80]
    top = max(tops, key=lambda t: (t.h, t.x1 - t.x0))
    taken.setdefault(top.id, [o["at"][0] for o in _objects_on(r, top, top.h)])
    for o in r.d["objects"]:
        if o["type"] != "chest" or float(o.get("alt", 0)) >= top.h - 1 or not plain(o):
            continue
        on_later = any(t.later() for t in tiers(r, include_blocks=False) if _objects_on(r, t, float(o.get("alt", 0))) and o in _objects_on(r, t, float(o.get("alt", 0))))
        if on_later:
            continue
        spots = _spots(r, top, 1, taken[top.id])
        if spots:
            o["at"] = [spots[0][0], spots[0][1]]
            o["alt"] = int(top.h)
            if "surface" in o:
                o["surface"] = top.id
            taken[top.id].append(spots[0][0])


def run(rooms):
    stats = {"rooms": 0, "route_tiers": 0}
    for rid, r in rooms.items():
        d = r.d
        if d.get("vertical") == "authored":
            continue
        stats["rooms"] += 1
        rise, gap, flight = band(int(d.get("level_range", [0, 0])[0] or 0))
        normalize(r)
        if d["type"] in LINT_TYPES and r.w >= 2560 and not d.get("instanced") and d.get("vertical") != "grows":
            stats["route_tiers"] += add_route(r, rise, gap) + second_tier(r, rise, gap)
        mark_later(r, rise, gap, flight)
        two_ways(r, rise, gap)
        lift_objects(r)
    print("verticality pass:", stats)
