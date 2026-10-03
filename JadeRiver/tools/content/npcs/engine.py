"""The NPC engine (decision 45, audit 45 §6.3; docs/architecture/npc_engine.md): the people of the world as specs,
compiled into every place the game reads them from.

    python3 tools/content/npcs/engine.py --check      # the engine's gate (tools/run_tests.sh, Test.ps1)
    python3 tools/content/npcs/engine.py --list       # every person, their home and their work
    python3 tools/content/npcs/engine.py --show ID    # one person: the row, the places, the spots resolved

A spec (specs/<zone>.py `NPCS`, spec.py) writes:
- the person's npcs.json row, look and voice included (story.py's `npcs()` takes `rows()`, places its one-off rows
  among them and adds what other tables keep: relations.py's hearts and gifts, technique_hand.py's lost-art trees);
- their work at each place in life.json (topdown_life.py takes `work()` and `extras()`; it resolves the spots named
  by anchors, spots.py, on the built layout and checks every spot and leg);
- for a placement the engine makes itself (`place(..., anchor=...)`): the side-view room's object (world.py's
  Room.build takes `objects(room)`) and the top-down room's anchor (the room engine takes `anchors(room)`).
Deterministic: no randomness; a spot an anchor names is chosen by a hash of the room and the person.
"""
import copy
import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, "..", ".."))
ROOT = os.path.abspath(os.path.join(TOOLS, ".."))
DATA = os.path.join(ROOT, "data")
for _p in (os.path.join(TOOLS, "data"), TOOLS):
    if _p not in sys.path:
        sys.path.append(_p)

if __name__ == "__main__" and not __package__:
    # Run as a script: the package's own module runs the command line, so the specs and the CLI share one compile.
    from content.npcs import engine as _engine
    raise SystemExit(_engine.main())

from .spec import DROP, HEAD, KEYS, SpecError  # noqa: E402
from . import spots as SPOTS  # noqa: E402


class State:
    """Every spec, in the order of the zones and of each module's lists."""

    def __init__(self, npcs, extras):
        self.npcs, self.extras = list(npcs), list(extras)
        self.by_id = {}
        for s in self.npcs + self.extras:
            if s["id"] in self.by_id:
                raise SpecError("%s is written twice" % s["id"])
            self.by_id[s["id"]] = s


_STATE = None


def load(zones=None):
    """The specs of `zones` (specs.ZONES by default), in order."""
    from .specs import ZONES
    npcs, extras = [], []
    for z in zones or ZONES:
        mod = importlib.import_module("content.npcs.specs." + z)
        npcs += getattr(mod, "NPCS", [])
        extras += getattr(mod, "EXTRAS", [])
    return State(npcs, extras)


def state():
    global _STATE
    if _STATE is None:
        _STATE = load()
    return _STATE


def reset():
    global _STATE
    _STATE = None


# ------------------------------------------------------------------------------------------------ npcs.json
def row(s):
    """A person's npcs.json row: the head (id, name, title, outfit, lines, barks, services), the keys in KEYS' order,
    the lines to a hidden realm, then the spec's pins."""
    r = {"id": s["id"], "name": s["name"], "title": s["title"], "outfit": s["look"], "lines": s["lines"], "barks": s["barks"],
         "services": s["services"]}
    for k in KEYS:
        if k in s["keys"]:
            r[k] = s["keys"][k]
    if s["concealed"]:
        r["concealed_lines"] = s["concealed"]
    for k, v in s["row"].items():
        if v is DROP:
            r.pop(k, None)
        else:
            r[k] = v
    return copy.deepcopy(r)


def rows(hand=(), st=None):
    """Every person's row in the specs' order, and the hand rows (`(row, after)`: a one-off placed after the row of
    `after`, or at the end) among them."""
    out = [row(s) for s in (st or state()).npcs]
    for r, after in hand:
        ids = [x["id"] for x in out]
        if r["id"] in ids:
            raise SpecError("%s has a spec and a hand row" % r["id"])
        if after is None:
            out.append(r)
        elif after not in ids:
            raise SpecError("the hand row %s is placed after %s, which no row is" % (r["id"], after))
        else:
            out.insert(ids.index(after) + 1, r)
    return out


# ------------------------------------------------------------------------------------------------ life.json
def work(st=None):
    """{room: {object id: {loop, spots | auto}}}: each person's work at each place (spots may be anchors, which
    topdown_life.py resolves with `resolve_spots`)."""
    out = {}
    for s in (st or state()).npcs:
        for p in s["at"]:
            if p["work"]:
                if p["oid"] in out.get(p["room"], {}):
                    raise SpecError("%s: %s works there twice" % (p["room"], p["oid"]))
                out.setdefault(p["room"], {})[p["oid"]] = copy.deepcopy(p["work"])
    return out


def extras(st=None):
    """{room: [{id, outfit, loop, spots}]}: the figures at work, in the specs' order."""
    out = {}
    for e in (st or state()).extras:
        w = e["work"]
        out.setdefault(e["room"], []).append({"id": e["id"], "outfit": copy.deepcopy(e["look"]), "loop": w["loop"],
                                              "spots": copy.deepcopy(w["spots"])})
    return out


def resolve_spots(rid, who, d, g, spots, home=None):
    """A worker's spots with their anchors resolved on the room's layout `d` (its Grid `g`): spots.py."""
    return SPOTS.resolve(SPOTS.Room(rid, d, g), who, spots, home)


# ------------------------------------------------------------------------------------------------ the rooms
def _placed(rid, st=None):
    return [(s, p) for s in (st or state()).npcs for p in s["at"] if p["room"] == rid and p["anchor"] is not None]


def anchors(rid, st=None):
    """{object id: anchor} of the people the engine places in room `rid` itself (the room engine lays them out after
    the room spec's own anchors)."""
    return {p["oid"]: tuple(p["anchor"]) if isinstance(p["anchor"], list) else p["anchor"] for _, p in _placed(rid, st)}


def objects(rid, bounds=None, st=None):
    """The side-view room's objects for the people the engine places in room `rid` (world.py's Room.build adds them
    after the room's own): each at its `side` point, or at its anchor's column across the room (`bounds`, the room's
    [x, y, w, h]) on the ground line."""
    out = []
    for s, p in _placed(rid, st):
        at = p["side"] or side_point(p["anchor"], rid, bounds)
        o = {"id": p["oid"], "type": "npc", "at": list(at), "npc": s["id"]}
        o.update(copy.deepcopy(p["obj"]))
        out.append(o)
    return out


def side_point(anchor, rid, bounds):
    """A side-view point for a top-down anchor: its column across the room (TopdownRoom.from_side, inverted), on the
    ground line four fifths down the room's bounds."""
    from content.rooms.specs import all_specs
    b = bounds or [0, 480, 1280, 480]
    spec = next((r for r in all_specs() if r["id"] == rid), None)
    if spec is None:
        raise SpecError("%s: no room spec to place a person in" % rid)
    w = spec["size"][0]
    if isinstance(anchor, (list, tuple)):
        col = float(anchor[0])
    elif "@" in str(anchor):
        col = float(str(anchor).split("@", 1)[1].split(",")[0])
    else:
        col = (w - 1) / 2.0
    f = min(1.0, max(0.0, (col + 0.5 - 1.5) / max(1.0, w - 3.0)))
    return [int(round(b[0] + f * b[2])), int(round(b[1] + 0.8 * b[3]))]


# ------------------------------------------------------------------------------------------------ checks
def _json(*parts):
    path = os.path.join(DATA, *parts)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_specs(errs, st=None):
    """Every spec resolves: its look's parts, hair colour and dyes; its dialogue tree and shops; each place's room, its
    object there (for a room on the grid, placed in the layout) and its loop; each extra's room and loop; each spot
    anchor's grammar."""
    import topdown_life as LIFE
    st = st or state()
    parts = _json("parts.json")
    char = _json("topdown", "character.json")
    dyes = set(char["dyes"])
    shops = {r["id"] for r in _json("shops.json")["entries"]}
    for s in st.npcs + st.extras:
        who = s["id"]
        o = s["look"]
        for cat in ("body", "hair", "shirt", "pants", "shoes", "hat", "cape", "weapon"):
            if o.get(cat) not in parts.get(cat, {}):
                errs.append("%s: no %s %r in data/parts.json" % (who, cat, o.get(cat)))
        if not 0 <= int(o.get("hair_color", 0)) < len(char["hair_colors"]):
            errs.append("%s: hair colour %s of %d" % (who, o.get("hair_color"), len(char["hair_colors"])))
        for k in ("shirt_dye", "pants_dye"):
            if k in o and o[k] not in dyes:
                errs.append("%s: no dye %r" % (who, o[k]))
        works = [p["work"] for p in s.get("at", []) if p["work"]] + ([s["work"]] if s["kind"] == "extra" else [])
        for w in works:
            if w["loop"] not in LIFE.LOOPS:
                errs.append("%s: no loop %r (topdown_life.LOOPS)" % (who, w["loop"]))
            for sp in w.get("spots", []):
                if SPOTS.is_anchor(sp):
                    try:
                        SPOTS.parse(sp)
                    except SPOTS.SpotError as e:
                        errs.append("%s: %s" % (who, e))
        if s["kind"] == "extra":
            if _json("topdown", s["room"] + ".json") is None:
                errs.append("%s: an extra in %s, which has no top-down layout" % (who, s["room"]))
            continue
        tree = s["keys"].get("tree")
        if tree and _json("dialogue", tree + ".json") is None:
            errs.append("%s: no dialogue tree %s (data/dialogue)" % (who, tree))
        for sv in s["services"]:
            if sv.startswith("shop:") and sv[5:] not in shops:
                errs.append("%s: no shop %s (data/shops.json)" % (who, sv[5:]))
        for k in ("service_labels", "service_unlocks"):
            for sv in s["keys"].get(k, {}):
                if sv not in s["services"]:
                    errs.append("%s: %s names %s, which is not among its services" % (who, k, sv))
        for p in s["at"]:
            side = _json("rooms", p["room"] + ".json")
            where = "%s in %s" % (who, p["room"])
            if side is None:
                errs.append(where + ": no such room (data/rooms)")
                continue
            obj = next((x for x in side["objects"] if x["id"] == p["oid"]), None)
            if obj is None or obj.get("type") != "npc" or obj.get("npc") != who:
                errs.append(where + ": the room has no object %s for them (world.py, or the engine's own: anchor=)" % p["oid"])
            lay = _json("topdown", p["room"] + ".json")
            if lay is not None and p["oid"] not in lay["place"]:
                errs.append(where + ": the layout does not place %s (run tools/data/topdown_rooms.py)" % p["oid"])
            if p["work"] and lay is None:
                errs.append(where + ": work in a room with no top-down layout")
    return errs


def _strip(row, keys):
    return {k: v for k, v in row.items() if k in keys}


def check_built(errs, st=None):
    """The built data holds every person as the engine writes them: each row's keys (npcs.json; story.py adds the
    hearts, the gifts and a lost art's tree), each place's work and each extra (life.json, its anchors resolved as the
    engine resolves them now)."""
    import topdown_rooms as TR
    st = st or state()
    built = {r["id"]: r for r in _json("npcs.json")["entries"]}
    order = [r["id"] for r in _json("npcs.json")["entries"]]
    mine = [s["id"] for s in st.npcs]
    if [i for i in order if i in set(mine)] != mine:
        errs.append("data/npcs.json does not list the specs' people in the specs' order (run build_data.py)")
    for s in st.npcs:
        want = row(s)
        have = built.get(s["id"])
        if have is None:
            errs.append("%s: not in data/npcs.json (run build_data.py)" % s["id"])
            continue
        got = _strip(have, want)
        if got != want or list(got) != list(want):
            errs.append("%s: data/npcs.json does not hold the engine's row (run build_data.py)" % s["id"])
    life = _json("topdown", "life.json")["rooms"]
    for rid, ws in work(st).items():
        lay = _json("topdown", rid + ".json")
        if lay is None:
            continue
        g = TR.Grid(lay)
        for oid, w in ws.items():
            have = life.get(rid, {}).get("work", {}).get(oid)
            if have is None or have["loop"] != w["loop"]:
                errs.append("%s %s: life.json does not hold its work (run build_data.py)" % (rid, oid))
                continue
            if "spots" in w:
                try:
                    want = resolve_spots(rid, oid, lay, g, w["spots"], lay["place"].get(oid))
                except SPOTS.SpotError as e:
                    errs.append(str(e))
                    continue
                if have["spots"] != want:
                    errs.append("%s %s: life.json's spots are not the engine's (run build_data.py)" % (rid, oid))
    for rid, xs in extras(st).items():
        have = [e["id"] for e in life.get(rid, {}).get("extras", [])]
        if [e["id"] for e in xs] != have[:len(xs)]:
            errs.append("%s: life.json's extras are not the engine's, first and in order (run build_data.py)" % rid)
    return errs


def check_rooms(errs, st=None):
    """A placement the engine makes is in the side-view room (world.py) and placed in the layout (the room engine), and
    the room spec does not place it too."""
    from content.rooms.specs import all_specs
    st = st or state()
    specs = {r["id"]: r for r in all_specs()}
    for s in st.npcs:
        for p in s["at"]:
            if p["anchor"] is None:
                continue
            spec = specs.get(p["room"])
            if spec is None:
                errs.append("%s: placed by the engine in %s, which has no room spec" % (s["id"], p["room"]))
            elif p["oid"] in spec.get("anchors", {}):
                errs.append("%s: %s is anchored by its room spec and by the engine" % (s["id"], p["oid"]))
    return errs


def deterministic(errs):
    """Two compiles write the same bytes."""
    def dump():
        st = state()
        return json.dumps([rows(st=st), work(st), extras(st), {r: anchors(r, st) for r in sorted({p["room"] for s in st.npcs for p in s["at"]})}],
                          sort_keys=True)
    a = dump()
    reset()
    if a != dump():
        errs.append("two compiles differ: the engine is not deterministic")
    return errs


def where(s):
    if s["kind"] == "extra":
        return s["room"]
    return ", ".join("%s%s%s" % (p["room"], "" if p["oid"] == "npc_" + s["id"] else " (%s)" % p["oid"],
                                 " [%s]" % p["work"]["loop"] if p["work"] else "") for p in s["at"]) or "-"


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="engine.py", description=__doc__.strip().split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="the gate: the specs, determinism, the built data, the rooms, tests.py")
    ap.add_argument("--list", action="store_true", help="every person, their places and their work")
    ap.add_argument("--show", metavar="ID", help="one person: the row, the places, the spots resolved")
    args = ap.parse_args(argv)
    st = state()
    if args.list:
        for s in st.npcs + st.extras:
            print("%-22s %-6s %s" % (s["id"], s["kind"], where(s)))
        return 0
    if args.show:
        return show(args.show, st)
    errs = []
    deterministic(errs)
    check_specs(errs)
    check_built(errs)
    check_rooms(errs)
    from . import tests
    ran, failed = tests.run()
    errs += failed
    if errs:
        print("npc engine:\n  " + "\n  ".join(errs), file=sys.stderr)
        return 1
    st = state()
    places = [p for s in st.npcs for p in s["at"]]
    print("npc engine: %d people, %d extras, %d places (%d at work, %d placed by the engine); %d tests; the specs, "
          "determinism, the built data and the rooms hold" % (len(st.npcs), len(st.extras), len(places),
                                                               sum(1 for p in places if p["work"]),
                                                               sum(1 for p in places if p["anchor"] is not None), ran))
    return 0


def show(who, st):
    import topdown_rooms as TR
    s = st.by_id.get(who)
    if s is None:
        print("no spec %s" % who, file=sys.stderr)
        return 1
    if s["kind"] == "npc":
        print(json.dumps(row(s), indent=1, ensure_ascii=False))
    print("places:" if s["kind"] == "npc" else "works:")
    for p in s.get("at", []) or [dict(room=s["room"], oid=s["id"], work=s["work"], anchor=None)]:
        lay = _json("topdown", p["room"] + ".json")
        line = "  %s %s" % (p["room"], p["oid"])
        if p["anchor"] is not None:
            line += " anchor %r" % (p["anchor"],)
        if lay is not None and p["oid"] in lay["place"]:
            line += " at %s" % (lay["place"][p["oid"]],)
        print(line)
        w = p["work"]
        if w and lay is not None:
            if "spots" in w:
                home = lay["place"].get(p["oid"]) if s["kind"] == "npc" else None
                try:
                    got = resolve_spots(p["room"], p["oid"], lay, TR.Grid(lay), w["spots"], home)
                except SPOTS.SpotError as e:
                    got = "error: %s" % e
                print("    %s: %s -> %s" % (w["loop"], w["spots"], got))
            else:
                print("    %s: auto %d" % (w["loop"], w["auto"]))
    return 0
