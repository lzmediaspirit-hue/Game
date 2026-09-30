#!/usr/bin/env python3
"""Audit 45: which files under art/ and data/ nothing names (read-only).

Usage: python3 tools/dev/audit/asset_refs.py [--json OUT] [--quiet]

The corpus is every string in data/**/*.json, every string literal in the .gd code, and every res:// path in
.tscn/.tres/.godot files. Paths are normalised (res:// stripped, the old "art_v12/" prefix mapped to "art/" as
wardrobe.gd does). An asset is:
  path     - its path (or its path without extension) is in the corpus (high confidence it is used);
  stem     - only its file stem (or its stem minus an "@px" or "_N" suffix) is a string in the corpus; the loader
             composes the path from an id (medium: the id is live, the file probably is);
  pattern  - a formatted path in the code ("res://art/ui/maps/%s_map.png") matches it;
  none     - nothing names it (the finding; confidence high when its folder has named siblings, else medium).
Every hit also records WHO names it (game code, tests, tools, data file), so "only the side view names it"
(data/parts.json, scripts/avatar.gd, wardrobe.gd, world.gd) can be told apart from the top-down game.
"""
import json
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
STR_RX = re.compile(r'"((?:\\.|[^"\\\n])*)"')


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def norm(s):
    s = s.replace("\\/", "/")
    if s.startswith("res://"):
        s = s[6:]
    if s.startswith("art_v12/"):
        s = "art/" + s[8:]
    return s


def main():
    out = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    quiet = "--quiet" in sys.argv
    corpus = defaultdict(set)   # normalised string -> sources
    patterns = []               # (regex, source)

    def add(s, src):
        n = norm(s)
        corpus[n].add(src)
        if "%s" in n or "%d" in n:
            rx = "^" + re.escape(n).replace("%s", "[^/]+").replace("%d", r"\d+") + "$"
            patterns.append((re.compile(rx), src))

    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in (".godot", ".git", "__pycache__") and not (dp == ROOT and d in ("docs", "art"))]
        for fn in fns:
            p = os.path.join(dp, fn)
            r = rel(p)
            if fn.endswith(".json") and r.startswith("data/"):
                try:
                    data = json.load(open(p, encoding="utf-8"))
                except Exception:
                    continue
                stack = [data]
                while stack:
                    x = stack.pop()
                    if isinstance(x, dict):
                        for k, v in x.items():
                            add(k, r)
                            stack.append(v)
                    elif isinstance(x, list):
                        stack.extend(x)
                    elif isinstance(x, str):
                        add(x, r)
            elif fn.endswith((".gd", ".tscn", ".tres", ".godot", ".cfg", ".gdshader")):
                t = open(p, encoding="utf-8", errors="replace").read()
                for m in STR_RX.finditer(t):
                    add(m.group(1), r)
    stems = defaultdict(set)
    for s, srcs in corpus.items():
        stems[os.path.basename(s)] |= srcs
        stems[os.path.splitext(os.path.basename(s))[0]] |= srcs

    assets = []
    for top in ("art",):
        for dp, dns, fns in os.walk(os.path.join(ROOT, top)):
            for fn in fns:
                if fn.endswith((".import", ".uid")):
                    continue
                p = os.path.join(dp, fn)
                r = rel(p)
                noext = os.path.splitext(r)[0]
                stem = os.path.splitext(fn)[0]
                srcs = corpus.get(r) or corpus.get(noext) or set()
                how = "path" if srcs else ""
                if not srcs:
                    # a folder named in the corpus with the id composed: art/icons/items/<id>.png
                    for cand in (stem, re.sub(r"@\d+$", "", stem), re.sub(r"_\d+$", "", stem),
                                 re.sub(r"_(0|1|2|3|4|5|6|7|8|9)+_\d+$", "", stem)):
                        if cand in stems:
                            srcs = stems[cand]
                            how = "stem"
                            break
                if not srcs:
                    for rx, src in patterns:
                        if rx.match(r):
                            srcs = {src}
                            how = "pattern"
                            break
                assets.append({"path": r, "bytes": os.path.getsize(p), "how": how or "none",
                               "sources": sorted(srcs)[:6]})
    # Group the unnamed by folder.
    by_dir = defaultdict(lambda: {"files": 0, "bytes": 0, "unnamed": 0, "unnamed_bytes": 0, "how": defaultdict(int),
                                  "sources": defaultdict(int)})
    for a in assets:
        d = os.path.dirname(a["path"])
        g = by_dir[d]
        g["files"] += 1
        g["bytes"] += a["bytes"]
        g["how"][a["how"]] += 1
        for s in a["sources"]:
            g["sources"][s] += 1
        if a["how"] == "none":
            g["unnamed"] += 1
            g["unnamed_bytes"] += a["bytes"]
    summary = {
        "assets": len(assets), "bytes": sum(a["bytes"] for a in assets),
        "unnamed": sum(1 for a in assets if a["how"] == "none"),
        "unnamed_bytes": sum(a["bytes"] for a in assets if a["how"] == "none"),
    }
    result = {"summary": summary,
              "by_dir": {k: {**v, "how": dict(v["how"]), "sources": dict(sorted(v["sources"].items(), key=lambda kv: -kv[1])[:6])}
                         for k, v in sorted(by_dir.items())},
              "unnamed": [a for a in assets if a["how"] == "none"]}
    if out:
        with open(out, "w") as fh:
            json.dump(result, fh, indent=1)
    if not quiet:
        print(json.dumps(summary))
        for k, v in sorted(result["by_dir"].items(), key=lambda kv: -kv[1]["unnamed_bytes"]):
            print("%-40s files=%5d %7.1fMB unnamed=%5d %6.1fMB how=%s top=%s" % (
                k, v["files"], v["bytes"] / 1e6, v["unnamed"], v["unnamed_bytes"] / 1e6, v["how"],
                list(v["sources"].items())[:3]))


if __name__ == "__main__":
    main()
