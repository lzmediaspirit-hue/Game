"""E1, the room engine's own checks (docs/architecture/room_engine.md; a gate of tools/run_tests.sh and Test.ps1).
Run from JadeRiver/:  python3 tools/content/rooms/test_engine.py [--verbose]

  determinism   every spec compiles to the same layout twice, and a room's scatter is its id's (another id, another)
  round trip    every spec compiles to its data/topdown/<id>.json byte for byte (with LIFE.dress and LIFE.extend)
  anchors       every anchor kind resolves on a sample room (a cliff, a terrace, a road, a meadow, a pond, a river, a
                knoll, a house with a door) to the cell its rule names, a pin overrides the engine, "auto" by type
  pins          "drop" takes a scattered piece out, "add" puts one in, a pinned spawn and foes win
  walks         in every room the engine lays out (its flora and anchors its own), auto-path (no running jump) reaches
                every thing from every way in, and every way

Prints "room_engine: N checks, M failures" and exits 1 on a failure.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (TOOLS, os.path.join(TOOLS, "data")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import topdown_life as LIFE  # noqa: E402
import topdown_rooms as TR  # noqa: E402
from content.rooms import engine, specs  # noqa: E402
from content.rooms.spec import room  # noqa: E402

CHECKS = [0, 0]
VERBOSE = "--verbose" in sys.argv


def check(ok, what):
    CHECKS[0] += 1
    if not ok:
        CHECKS[1] += 1
        print("FAIL: " + what)
    elif VERBOSE:
        print("ok: " + what)


def text_of(spec):
    lay = engine.compile_room(spec)
    LIFE.dress(lay)
    d = lay.dict()
    LIFE.extend(lay.id, d)
    body = {"schema_version": 1}
    body.update(d)
    return json.dumps(body, indent=1, ensure_ascii=False) + "\n"


# ------------------------------------------------------------------ determinism and the round trip
def determinism_and_round_trip(all_specs):
    for s in all_specs:
        a, b = text_of(s), text_of(s)
        check(a == b, "%s: compiles to the same layout twice" % s["id"])
        path = os.path.join(TR.OUT, s["id"] + ".json")
        have = open(path, encoding="utf-8").read() if os.path.exists(path) else None
        check(have == a, "%s: round trip, the spec compiles to data/topdown/%s.json byte for byte" % (s["id"], s["id"]))
    # The seed is the id: the same spec under another id scatters its flora otherwise.
    gen = [s for s in all_specs if "props" not in s.get("pins", {}) and s.get("biome")]
    if gen:
        s = gen[0]
        one = engine.Build(s).run().props
        other = engine.Build(dict(s, id=s["id"] + "_twin"), side=engine.Build(s).side).run().props
        check(one != other, "%s: the scatter is seeded by the room's id (a twin under another id differs)" % s["id"])


# ------------------------------------------------------------------ every anchor kind on a sample room
SIDE = {"name": "Sample", "bounds": [0, 480, 2560, 480],
        "objects": [{"id": o, "type": t} for o, t in (
            ("o_cell", "jar"), ("o_band", "npc"), ("o_north", "signpost"), ("o_south", "jar"), ("o_verge", "herb_patch"),
            ("o_verge_s", "crate"), ("o_bank", "herb_patch"), ("o_water", "fishing_spot"), ("o_door", "npc"),
            ("o_near", "jar"), ("o_top", "chest"), ("o_back", "jar"), ("o_front", "jar"), ("o_auto", "jar"),
            ("o_auto_ore", "ore_vein"), ("o_pinned", "jar"), ("o_terrace", "jar"))],
        "spawns": [{"enemy": "wild_boarlet", "points": [[400, 800], [1400, 800], [2200, 800]]},
                   {"enemy": "wild_boarlet", "points": [[1300, 700]], "elite": True}]}
SAMPLE = room(
    "e1_sample", size=(48, 28), biome="valley_road",
    bands=[("cliff", 0, 3, dict(level=2, paint="r", wall=True)),
           ("terrace", 3, 5, dict(level=1, paint="f")),
           ("road", 11, 3, dict(paint="d", walk=True)),
           ("meadow", 14, 8, dict(level=0)),
           ("river", 23, 5, dict(water=True))],
    features=[("knoll", (30, 16, 6, 3), dict(level=1)),
              ("pond", (6, 16, 8, 5), dict(water=True, shape="round"))],
    stairs="auto",
    ways={"east": ("e", "road"), "west": ("w", "road"), "hut": ("door", "hut", dict(path="auto")),
          "north": ("n", 40, dict(cut=3))},
    props=[("house", 18, 4, "hut"), {"kind": "lantern", "along": "road", "every": 12, "row": 10}],
    anchors={"o_cell": (2, 12), "o_band": "road@20", "o_north": "road.n@30", "o_south": "road.s@24",
             "o_verge": "verge@10", "o_verge_s": "verge.s@44", "o_bank": "bank@20", "o_water": "water@26",
             "o_door": "door:hut", "o_near": "near:o_band", "o_top": "knoll.top", "o_back": "meadow.back@38",
             "o_front": "meadow.front@40", "o_auto": "auto", "o_auto_ore": "auto", "o_pinned": "road@8",
             "o_terrace": "terrace@6"},
    foes="auto",
    pins={"o_pinned": (5, 18)})


def anchors():
    b = engine.Build(SAMPLE, side=SIDE)
    lay = b.run()
    at = {k: tuple(v) for k, v in lay.place.items()}
    r = b.regions
    check(set(at) == {o["id"] for o in SIDE["objects"]}, "sample: every object of the side view has its cell (%d)" % len(at))
    check(list(at) == list(SAMPLE["anchors"]), "sample: the places are written in the spec's order")
    check(at.get("o_cell") == (2, 12), "a cell written out is the cell (%s)" % str(at.get("o_cell")))
    check(at.get("o_band") == (20, r["road"].mid_row()), "road@20: the band's middle row at column 20 (%s)" % str(at.get("o_band")))
    check(at.get("o_north") == (30, r["road"].y - 1), "road.n@30: the row north of the road (%s)" % str(at.get("o_north")))
    check(at.get("o_south") == (24, r["road"].y1), "road.s@24: the row south of it (%s)" % str(at.get("o_south")))
    v = at.get("o_verge", (0, 0))
    check(r["road"].y - 3 <= v[1] < r["road"].y or r["road"].y1 <= v[1] < r["road"].y1 + 3, "verge: beside the road (%s)" % str(v))
    v = at.get("o_verge_s", (0, 0))
    check(r["road"].y1 <= v[1] < r["road"].y1 + 3, "verge.s: south of the road (%s)" % str(v))
    bk = at.get("o_bank", (0, 0))
    check(lay.lv[bk[1]][bk[0]] != TR.WATER and any(lay.lv[y][x] == TR.WATER for x, y in engine._ring(bk[0], bk[1], 1, lay.w, lay.h)),
          "bank: land beside the water (%s)" % str(bk))
    wa = at.get("o_water", (0, 0))
    check(lay.lv[wa[1]][wa[0]] == TR.WATER, "water: on the water, a fishing spot (%s)" % str(wa))
    hut = lay.props[b.named["hut"]]
    dr = at.get("o_door", (0, 0))
    check(hut["y"] + 3 <= dr[1] <= hut["y"] + 5 and hut["x"] - 1 <= dr[0] <= hut["x"] + 6, "door:hut: in front of the house (%s)" % str(dr))
    nb, n = at.get("o_band", (0, 0)), at.get("o_near", (99, 99))
    check(2 <= max(abs(nb[0] - n[0]), abs(nb[1] - n[1])) <= 4, "near:o_band: two to four cells from it (%s)" % str(n))
    kn = r["knoll"]
    check(kn.x <= at.get("o_top", (0, 0))[0] < kn.x1 and kn.y <= at.get("o_top", (0, 0))[1] < kn.y1, "knoll.top: on the knoll (%s)" % str(at.get("o_top")))
    check(at.get("o_back", (0, 0))[1] == r["meadow"].y, "meadow.back: the meadow's first row (%s)" % str(at.get("o_back")))
    check(at.get("o_front", (0, 0))[1] == r["meadow"].y1 - 1, "meadow.front: its last row (%s)" % str(at.get("o_front")))
    ore = at.get("o_auto_ore", (0, 0))
    check(r["cliff"].y1 <= ore[1] <= r["cliff"].y1 + 1, "auto for an ore vein: at the cliff's foot (%s)" % str(ore))
    check(at.get("o_pinned") == (5, 18), "a pin overrides the anchor (%s)" % str(at.get("o_pinned")))
    te = at.get("o_terrace", (0, 0))
    check(r["terrace"].y <= te[1] < r["terrace"].y1, "terrace@6: on the terrace (%s)" % str(te))
    # The rest of the sample: the stairs, the door's path, the cut north, the foes, the flora.
    check(any(s["to"] == 1 for s in lay.stairs), "stairs auto: a flight up onto the terrace or the knoll (%d)" % len(lay.stairs))
    check(lay.pt[hut["y"] + 3][hut["x"] + 2] == "d", "the door's path runs down from the doorway")
    check(all(lay.lv[y][40] != 2 for y in range(0, 3)), "the north way's cut goes through the cliff")
    check(len(lay.spawns) == 2 and [len(s) for s in lay.spawns] == [3, 1], "foes auto: a list a spawn, a cell a point (%s)" % lay.spawns)
    walk = {c for c in r["road"].cells()}
    check(not any(tuple(q) in walk for lst in lay.spawns for q in lst), "foes auto: none on the road")
    check(any(p["kind"] in engine.TREES for p in lay.props), "flora: trees scattered")
    lamps = [(p["x"], p["y"]) for p in lay.props if p["kind"] == "lantern"]
    check(len(lamps) >= 3 and all(y == 10 for x, y in lamps), "props by rule: a lantern every 12 cells along the road's north side (%s)" % lamps)
    errs = walks(b, lay)
    check(not errs, "sample: auto-path reaches every thing and way (%s)" % errs[:3])
    return b, lay


def pins(b, lay):
    flora = [p for p in lay.props if p["kind"] in TR.FOLIAGE]
    victim = flora[0]
    spec = dict(SAMPLE, pins=dict(SAMPLE["pins"], drop=[(victim["x"], victim["y"])], add=[("rock_small", 2, 20)],
                                  spawn=(3, 12), foes=[[(9, 15)], [(20, 16)]]))
    lay2 = engine.Build(spec, side=SIDE).run()
    check(not any(p["kind"] == victim["kind"] and p["x"] == victim["x"] and p["y"] == victim["y"] for p in lay2.props),
          "pins drop: the scattered %s at %d,%d is taken out" % (victim["kind"], victim["x"], victim["y"]))
    check(any(p["kind"] == "rock_small" and (p["x"], p["y"]) == (2, 20) for p in lay2.props), "pins add: the piece is put in")
    check(lay2.spawn == [3, 12], "pins spawn: the spawn is the pinned cell")
    check(lay2.spawns == [[[9, 15]], [[20, 16]]], "pins foes: the foes are the pinned cells")


# ------------------------------------------------------------------ the walks
def walks(b, lay):
    """Auto-path (no running jump) reaches a cell beside every thing (within three, at its height) and every way, from
    the spawn and every way in; the stricter rule the engine lays its own rooms by."""
    d = {"size": [lay.w, lay.h], "levels": ["".join("~" if v == TR.WATER else str(v) for v in row) for row in lay.lv],
         "stairs": lay.stairs, "props": lay.props, "spawn": lay.spawn, "portals": lay.portals}
    g = TR.Grid(d)
    starts = [TR.cell(lay.spawn)] + [TR.cell(TR.arrive(p)) for p in lay.portals.values()]
    errs = []
    for st in starts:
        if g.floor(*st) is None:
            errs.append("start %s has no floor" % str(st))
            continue
        r = g.reach(st, False)
        for oid, at in lay.place.items():
            c = TR.cell(at)
            alt = g.floor(*c) if g.floor(*c) is not None else 0.0
            near = [q for q in engine._ring(c[0], c[1], 3, lay.w, lay.h) + [c] if (q[0] - c[0]) ** 2 + (q[1] - c[1]) ** 2 <= 9
                    and g.floor(*q) is not None and abs(g.floor(*q) - alt) <= TR.REACH_ALT]
            if not any(q in r for q in near):
                errs.append("%s from %s" % (oid, str(st)))
        for pid, p in lay.portals.items():
            if TR.cell(p["at"]) not in r:
                errs.append("way %s from %s" % (pid, str(st)))
    return errs


def room_walks(all_specs):
    for s in all_specs:
        if "props" in s.get("pins", {}):
            continue        # a hand-placed room: topdown_rooms.check holds it as it always did
        b = engine.Build(s)
        lay = b.run()
        errs = walks(b, lay)
        check(not errs, "%s: auto-path reaches its %d things and %d ways from every way in (%s)"
              % (s["id"], len(lay.place), len(lay.portals), errs[:3]))


def main():
    all_specs = specs.all_specs()
    determinism_and_round_trip(all_specs)
    b, lay = anchors()
    pins(b, lay)
    room_walks(all_specs)
    print("room_engine: %d checks, %d failures" % (CHECKS[0], CHECKS[1]))
    return 1 if CHECKS[1] else 0


if __name__ == "__main__":
    raise SystemExit(main())
