"""S43 room lint and reach contract (Build Prompt v2, S43 rules 8 and 14; Part 7 "Room lint").

Run from JadeRiver/ after building the data:  python3 tools/data/room_lint.py [--verbose] [room ...]

Checks every room in data/rooms against the verticality rules:
  tiers     field, path and town rooms two screens wide or more have two tiers above the ground and a raised
            route spanning 40% of the width;
  raised    at least 30% of breakables and one in three gathering nodes sit on raised tiers;
  chests    chests sit on the room's highest tier or on an optional ledge;
  ways      every required raised tier is reachable two ways (jumps from two places, a climbable, stairs, a mover,
            a bridge walked onto from the tier it joins, a moving plank stepped onto from a tier at its height);
  landings  no required landing narrower than 80 or shallower than 60; jump neighbours share 60 of depth;
  heights   jumped-to tiers use the standard heights (built 88s, natural 100s, blocks 40/60/80/110);
  reach     everything required is reachable with the arts of the room's lowest realm (the reach table),
            and every optional ("later") ledge is out of that reach but within its named art's.
Exit code 1 when any room fails.
"""
import glob
import json
import math
import os
import sys

ROOMS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "rooms")
MOVEMENT = os.path.join(os.path.dirname(__file__), "..", "..", "data", "movement.json")

BUILT = {"roof", "balcony", "deck", "awning"}                     # stilt decks (60-120) and scaffolds (90/180) are ladder-reached kit pieces
NATURAL = {"rock_ledge", "ledge", "branch", "cloud", "tree_branch", "canopy"}
WALKWAYS = {"bridge", "rope_bridge", "walkway"}
BLOCK_TOPS = {40, 60, 80, 110}
BREAKABLES = {"jar", "crate", "wine_jar", "urn", "pot"}
NODES = {"herb_patch", "ore_vein"}
LINT_TYPES = {"field", "path", "town"}
# Reach table (S43 rule 8): the lowest level of each band, and what every character in it can do.
BANDS = [  # (first level, required rise, required gap, arts)
    (0, 100, 150, {"jump", "climb", "drop", "mantle", "sprint"}),
    (4, 100, 150, {"plunge"}),
    (5, 100, 150, {"dodge"}),
    (12, 100, 150, {"glide"}),
    (16, 100, 250, {"air_dash"}),
    (24, 160, 300, {"double_jump"}),
    (31, 160, 300, {"wall_step"}),
    (37, 9999, 9999, {"flight"}),
]
# What each later art reaches (rise above the surface it is used from) for "Paths Above" ledges.
ART_RISE = {"double_jump": 202, "wall_step": 370, "flight": 340, "glide": 100, "air_dash": 100}


def band(level):
    rise, gap, arts = 100, 150, set()
    for lv, r, g, a in BANDS:
        if level >= lv:
            rise, gap = r, g
            arts |= a
    return rise, gap, arts


class Surf:
    def __init__(self, sid, rect, h, kind, stratum, block=False, optional=None, rise=0.0, edges=None):
        self.id, self.rect, self.h, self.kind, self.stratum = sid, rect, float(h), kind, stratum
        self.block, self.optional, self.rise = block, optional, rise
        self.edges = edges or {}

    @property
    def x0(self): return self.rect[0]

    @property
    def x1(self): return self.rect[0] + self.rect[2]

    @property
    def y0(self): return self.rect[1]

    @property
    def y1(self): return self.rect[1] + self.rect[3]

    def contains(self, x, y):
        return self.x0 <= x < self.x1 and self.y0 <= y < self.y1

    def gap_to(self, o):
        dx = max(0, max(self.x0, o.x0) - min(self.x1, o.x1))
        dy = max(0, max(self.y0, o.y0) - min(self.y1, o.y1))
        return math.hypot(dx, dy)

    def depth_overlap(self, o):
        return min(self.y1, o.y1) - max(self.y0, o.y0)


def surfaces_of(room):
    out = []
    for s in room.get("surfaces", []):
        if s.get("kind") == "ladder":
            continue
        # A prop's standable top (a crate, a table) is a block, not a tier.
        out.append(Surf(s["id"], s["rect"], s.get("height", 0), s.get("kind", ""), s.get("stratum", "platform"),
                        block=s.get("kind") == "support", optional=s.get("later") or (s.get("optional") and "optional"),
                        rise=float(s.get("rise", 0) or 0)))
    for b in room.get("blocks", []):
        # Blocks over 110 are walls (Wall-Step faces, palisades): nobody is meant to jump onto them.
        if float(b.get("top", 0)) > 110:
            continue
        out.append(Surf(b["id"], b["rect"], b.get("top", 0), "block", "platform", block=True, optional=b.get("later")))
    return out


def ground_level(s):
    return s.stratum == "ground" and s.h <= 0.5 and s.rise == 0


def raised(s):
    return s.h > 0.5 and not ground_level(s)


def lint_room(room, verbose=False):
    rid = room["id"]
    problems = []
    rtype = room.get("type", "")
    width = room["bounds"][2]
    lv0 = int(room.get("level_range", [0, 0])[0] or 0)
    req_rise, req_gap, arts = band(lv0)
    surfs = surfaces_of(room)
    by_id = {s.id: s for s in surfs}
    climb_to = {}
    for c in room.get("climbables", []):
        climb_to.setdefault(c.get("top", ""), []).append(c)
        if c.get("bottom"):
            climb_to.setdefault(c["bottom"], []).append(c)
    mover_ids = {m["surface"] for m in room.get("movers", [])}
    stairs = [s for s in surfs if s.kind in ("stairs", "ramp")]

    # Jump edges with the band's required limits (a required tier must be reachable within them).
    def jump_ok(a, b, rise_lim, gap_lim):
        rise = b.h - a.h
        if rise > rise_lim + 0.5:
            return False
        gap = a.gap_to(b)
        if rise <= -8:   # dropping down: fine from any open edge
            return gap <= max(gap_lim, 70)
        return gap <= gap_lim

    raised_s = [s for s in surfs if raised(s)]
    required = [s for s in raised_s if not s.optional]
    tiers_req = [s for s in required if not s.block]
    ways = {}
    for s in tiers_req:
        w = []
        for o in surfs:
            if o is s:
                continue
            # A bridge or walkway joined to a tier at its own height is walked onto.
            if abs(o.h - s.h) <= 8 and not o.block and not o.optional and (o.gap_to(s) <= 2 and (o.kind in WALKWAYS or s.kind in WALKWAYS) or s.id in mover_ids and o.gap_to(s) <= 60):
                w.append("walk:" + o.id)
                continue
            if o.h >= s.h - 8:
                continue
            if jump_ok(o, s, req_rise, req_gap):
                w.append("jump:" + o.id)
        w += ["climb:" + c["id"] for c in climb_to.get(s.id, [])]
        if s.id in mover_ids:
            w.append("mover")
        for st in stairs:
            if st.gap_to(s) <= 4:
                w.append("stairs:" + st.id)
        ways[s.id] = w

    # Reach: flood fill from the ground with the band's limits (climbables and movers count).
    start = [s for s in surfs if ground_level(s)]
    seen = {s.id for s in start}
    todo = list(start)
    while todo:
        a = todo.pop()
        for b in surfs:
            if b.id in seen:
                continue
            ok = jump_ok(a, b, req_rise, req_gap) if b.h > a.h - 8 else a.gap_to(b) <= max(req_gap, 70) or a.depth_overlap(b) > 0
            if not ok:
                for c in climb_to.get(b.id, []):
                    if c.get("bottom", "ground") == a.id or c.get("top") == a.id:
                        ok = True
            if ok:
                seen.add(b.id)
                todo.append(b)
    for s in tiers_req:
        if s.id not in seen:
            problems.append("reach: required tier %s (%d) is out of the band's reach (rise %d, gap %d)" % (s.id, s.h, req_rise, req_gap))
    # Later ledges must be out of the band's reach, and within their art's.
    for s in raised_s:
        if not s.optional or s.optional == "optional":
            continue
        below = max((o.h for o in surfs if o is not s and o.id in seen and not o.optional and o.h < s.h and o.gap_to(s) <= 300), default=0)
        limit = 202 if req_rise >= 160 else 122
        if s.h - below <= limit:
            problems.append("later: %s (%d) is only %d above reachable ground: not out of the band's reach" % (s.id, s.h, s.h - below))
        art_rise = ART_RISE.get(s.optional, 9999)
        if s.h - below > art_rise:
            problems.append("later: %s needs %d, beyond %s (%d)" % (s.id, s.h - below, s.optional, art_rise))

    if rtype in LINT_TYPES and width >= 2560 and not room.get("instanced") and room.get("vertical") != "grows":
        tiers = sorted({round(s.h) for s in tiers_req if s.h >= 60})
        if len(tiers) < 2:
            problems.append("tiers: only %s above the ground (needs two)" % tiers)
        # The longest raised route: surfaces chained by the band's jumps (or climbables), x-extent.
        best = 0
        comp_seen = set()
        for s in tiers_req:
            if s.id in comp_seen:
                continue
            comp = [s]
            comp_seen.add(s.id)
            i = 0
            while i < len(comp):
                a = comp[i]
                for b in tiers_req:
                    if b.id not in comp_seen and (jump_ok(a, b, req_rise, req_gap) or jump_ok(b, a, req_rise, req_gap)) and a.gap_to(b) <= req_gap:
                        comp_seen.add(b.id)
                        comp.append(b)
                i += 1
            span = sum(c.rect[2] for c in comp) if len(comp) == 1 else max(c.x1 for c in comp) - min(c.x0 for c in comp)
            best = max(best, span)
        if best < 0.4 * width:
            problems.append("route: the longest raised route spans %d of %d (needs 40%%)" % (best, width))
    # A bounce pad (a drum, a lily pad, a bent bamboo) is a block that throws you; its own top can be any height.
    bouncers = {s.id for s in surfs if s.block and any(v.get("kind") == "bounce" and v["rect"] == list(s.rect) for v in room.get("volumes", []))}
    for s in required:
        if s.block:
            if round(s.h) not in BLOCK_TOPS and s.id not in bouncers and not any(w.startswith("climb") or w == "mover" for w in ways.get(s.id, [])):
                problems.append("heights: block %s top %d is not 40/60/80/110" % (s.id, s.h))
            continue
        jumped_only = not any(not w.startswith("jump") for w in ways.get(s.id, []))
        if jumped_only:
            if s.kind in BUILT and round(s.h) % 88 != 0:
                problems.append("heights: built tier %s at %d is not a multiple of 88" % (s.id, s.h))
            if s.kind in NATURAL and round(s.h) % 100 != 0:
                problems.append("heights: natural tier %s at %d is not a multiple of 100" % (s.id, s.h))
        if s.rect[2] < 80 or s.rect[3] < 60:
            problems.append("landings: %s is %dx%d (needs 80 wide, 60 deep)" % (s.id, s.rect[2], s.rect[3]))
        if len(ways.get(s.id, [])) < 2:
            problems.append("ways: %s has %d way(s) up %s" % (s.id, len(ways.get(s.id, [])), ways.get(s.id, [])))
    objs = room.get("objects", [])
    brk = [o for o in objs if o.get("type") in BREAKABLES]
    if len(brk) >= 3 and sum(1 for o in brk if float(o.get("alt", 0)) > 0) < 0.3 * len(brk):
        problems.append("raised: %d of %d breakables are raised (needs 30%%)" % (sum(1 for o in brk if float(o.get("alt", 0)) > 0), len(brk)))
    nodes = [o for o in objs if o.get("type") in NODES]
    if len(nodes) >= 2 and sum(1 for o in nodes if float(o.get("alt", 0)) > 0) * 3 < len(nodes):
        problems.append("raised: %d of %d gathering nodes are raised (needs one in three)" % (sum(1 for o in nodes if float(o.get("alt", 0)) > 0), len(nodes)))
    top = max((s.h for s in tiers_req), default=0)
    for o in objs:
        # Story chests (a vault behind a boss, a gated strongbox) are behind their own challenge.
        if o.get("type") != "chest" or any(k in o for k in ("requires", "hidden_if", "visible_if")):
            continue
        alt = float(o.get("alt", 0))
        on = [s for s in surfs if s.contains(o["at"][0], o["at"][1]) and abs(s.h - alt) < 1]
        if not (alt >= top - 1 or any(s.optional for s in on) or o.get("challenge")):
            problems.append("chests: %s at %d is below the highest tier (%d)" % (o["id"], alt, top))
    return problems


def main(args):
    verbose = "--verbose" in args
    only = [a for a in args if not a.startswith("--")]
    failed = 0
    total = 0
    for f in sorted(glob.glob(os.path.join(ROOMS_DIR, "*.json"))):
        room = json.load(open(f))
        if only and room["id"] not in only:
            continue
        total += 1
        probs = lint_room(room, verbose)
        if probs:
            failed += 1
            if verbose or only:
                print(room["id"], "(%s, level %s)" % (room.get("type"), room.get("level_range")))
                for p in probs:
                    print("   ", p)
    print("room_lint: %d rooms, %d failing" % (total, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
