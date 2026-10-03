"""E1, the room engine's command line (docs/architecture/room_engine.md). Run from JadeRiver/:

  python3 tools/content/rooms/build.py [--write | --check] [--only ROOM]   build the layouts (topdown_rooms.py's run:
                                                                           every spec, the checks, life.json, --check's
                                                                           grid parity with the game when GODOT is set)
  python3 tools/content/rooms/build.py --show ROOM      a room compiled, drawn in text: its levels, its map (props,
                                                        anchors, ways, foes) and what the engine decided
  python3 tools/content/rooms/build.py --new ROOM       a side-view room's first spec: its size, ways, every object's
                                                        anchor and its foes, to shape by hand (docs: "Converting a
                                                        side-view room")
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (TOOLS, os.path.join(TOOLS, "data")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import common  # noqa: E402
import topdown_rooms as TR  # noqa: E402
from content.rooms import engine, specs  # noqa: E402

MARKS = {"tree": "T", "foliage": "*", "walk": "'", "building": "H", "other": "o"}
PAINT = {"g": ",", "f": ";", "m": ",", "b": ";", "d": ".", "p": ":", "s": ":", "w": "=", "r": "^", "l": "#", "t": "^",
         "a": "_", "n": "-", "k": "-"}


def find(rid):
    for s in specs.all_specs():
        if s["id"] == rid:
            return s
    raise SystemExit("no spec for %s (tools/content/rooms/specs/)" % rid)


def show(rid):
    spec = find(rid)
    b = engine.Build(spec)
    lay = b.run()
    w, h = lay.w, lay.h
    grid = [[PAINT.get(lay.pt[y][x], "?") if lay.lv[y][x] != TR.WATER else "~" for x in range(w)] for y in range(h)]
    for s in lay.stairs:
        for y in range(s["y"], s["y"] + s["h"]):
            for x in range(s["x"], s["x"] + s["w"]):
                grid[y][x] = "%"
    for p in lay.props:
        art = TR.TILESET["props"][p["kind"]]
        fw, fh = art["footprint"]
        mark = "T" if art.get("canopy") else "H" if "top" in art and fw >= 4 else "*" if art.get("foliage") and art.get("solid", True) \
            else "'" if not art.get("solid", True) else "o"
        for y in range(p["y"], p["y"] + fh):
            for x in range(p["x"], p["x"] + fw):
                if 0 <= x < w and 0 <= y < h:
                    grid[y][x] = mark
    for lst in lay.spawns:
        for q in lst:
            c = TR.cell(q)
            grid[c[1]][c[0]] = "x"
    for pid, p in lay.portals.items():
        c = TR.cell(p["at"])
        grid[c[1]][c[0]] = {"n": "^", "s": "v", "e": ">", "w": "<"}[p["dir"]]
    keys = {}
    for i, (oid, at) in enumerate(lay.place.items()):
        c = TR.cell(at)
        ch = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"[i % 36]
        keys[ch] = (oid, at)
        grid[c[1]][c[0]] = ch
    print("%s (%d x %d)    levels" % (rid, w, h))
    tens = "".join(str(x // 10) if x % 10 == 0 else " " for x in range(w))
    print("    " + tens + "    " + tens)
    for y in range(h):
        lv = "".join("~" if v == TR.WATER else str(v) for v in lay.lv[y])
        print("%3d " % y + "".join(grid[y]) + "    " + lv)
    print("\n    " + "  ".join("%s %s %s" % (k, o, list(a)) for k, (o, a) in list(keys.items())))
    print("    ways: " + ", ".join("%s %s %s" % (pid, p["dir"], p["at"]) for pid, p in lay.portals.items()))
    print("    key: T tree  * bush, rock, fence  ' walk-through plant  H building  o prop  %% stair  x foe  ~ water  "
          ", meadow  ; flowers  . path  : paving or granite  = boards  ^ rock  # wall  _ sand")
    for n in b.notes:
        print("    " + n)


def new(rid):
    """A first spec for a side-view room: the size by its screens, a road band through the middle, a way for each
    portal (an edge on the road, a door or a north way for the rest), an anchor for every object, its foes "auto"."""
    side = TR.side(rid)
    width = float(side.get("bounds", [0, 0, 1280])[2])
    screens = max(1, int(round(width / 1280.0)))
    w = 24 + 16 * screens
    h = 28 if screens > 1 else 24
    road = h // 2 - 1
    biome = {"cave": "cave", "marsh": "river_shore"}.get(side.get("backdrop", ""), "valley_road")
    lines = ['%s = room(' % rid.upper(), '    "%s", size=(%d, %d), biome="%s",' % (rid, w, h, biome),
             '    bands=[("ridge", 0, 3, dict(level=2, paint="r", wall=True)),',
             '           ("bank", 3, %d, dict(level=1)),' % (road - 6),
             '           ("road", %d, 3, dict(paint="d", walk=True)),' % road,
             '           ("stream", %d, 4, dict(water=True))],' % (h - 4),
             '    stairs="auto",', '    ways={']
    for p in side.get("portals", []):
        x = float(p.get("at", [0])[0]) / width * w
        if p.get("type") in ("edge", "sealed", "gate") and float(p["at"][0]) < 200:
            way = '("w", "road")'
        elif p.get("type") in ("edge", "sealed", "gate") and float(p["at"][0]) > width - 200:
            way = '("e", "road")'
        else:
            way = '("n", %d, dict(cut=3))' % int(round(x))
        lines.append('        "%s": %s,   # %s to %s' % (p["id"], way, p.get("type", ""), p.get("to", "")))
    lines += ['    },', '    anchors={']
    for o in side.get("objects", []):
        x = float(o.get("at", [0])[0]) / width * w
        guess = engine.AUTO_BY_TYPE.get(o.get("type", ""), "auto")
        lines.append('        "%s": "%s@%d",   # %s' % (o["id"], guess, int(round(x)), o.get("type", "")))
    lines += ['    },', '    foes="auto")', '# side view: %s, %d spawns: %s' % (
        side.get("name"), len(side.get("spawns", [])), ", ".join("%s x%d" % (s.get("enemy"), len(s.get("points", [])))
                                                                for s in side.get("spawns", [])))]
    print("\n".join(lines))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="build.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--show", metavar="ROOM")
    ap.add_argument("--new", metavar="ROOM")
    args, rest = ap.parse_known_args(argv)
    if args.show:
        return show(args.show)
    if args.new:
        return new(args.new)
    return common.run_cli(TR.build, rest, name="topdown_rooms", doc=TR.__doc__)


if __name__ == "__main__":
    raise SystemExit(main())
