#!/usr/bin/env python3
"""Audit 45: read-only inventory of the project (lines, files, functions per area).

Usage: python3 tools/dev/audit/inventory.py [--json OUT]
Prints a table per area and the largest files. Nothing in the project is written.
"""
import json
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SKIP_DIRS = {".godot", ".git", "__pycache__", "audit"}   # audit: these scans themselves
CODE_EXT = {".gd", ".py", ".sh", ".ps1", ".gdshader", ".tscn"}

FUNC_GD = re.compile(r"^\s*(?:static\s+)?func\s+([A-Za-z_]\w*)")
FUNC_PY = re.compile(r"^\s*def\s+([A-Za-z_]\w*)")


def area_of(rel):
    parts = rel.split("/")
    if parts[0] == "scripts":
        if len(parts) == 2:
            return "scripts/(root: side-view world, player, hud)"
        if parts[1] == "simulation" and len(parts) > 3:
            return "scripts/simulation/" + parts[2]
        if parts[1] == "ui" and len(parts) > 3:
            return "scripts/ui/pages"
        return "scripts/" + parts[1]
    if parts[0] == "tools":
        if len(parts) == 2:
            return "tools/(root)"
        if parts[1] == "art" and len(parts) > 3:
            sub = parts[2]
            if sub == "topdown" and len(parts) > 4 and parts[3] in ("figure", "creature"):
                return "tools/art/topdown/" + parts[3]
            return "tools/art/" + sub
        return "tools/" + parts[1]
    if parts[0] == "tests":
        return "tests"
    return parts[0]


def walk(root):
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for fn in fns:
            yield os.path.join(dp, fn)


def main():
    out = None
    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
    per_area = defaultdict(lambda: {"files": 0, "lines": 0, "funcs": 0, "ext": defaultdict(int)})
    files = []
    for path in walk(ROOT):
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        if rel.startswith(("docs/", "art/", "data/")):
            continue
        ext = os.path.splitext(rel)[1]
        if ext not in CODE_EXT:
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        lines = text.count("\n") + (0 if text.endswith("\n") or not text else 1)
        rx = FUNC_GD if ext == ".gd" else FUNC_PY if ext == ".py" else None
        funcs = len([1 for ln in text.splitlines() if rx and rx.match(ln)]) if rx else 0
        a = area_of(rel)
        per_area[a]["files"] += 1
        per_area[a]["lines"] += lines
        per_area[a]["funcs"] += funcs
        per_area[a]["ext"][ext] += 1
        files.append({"path": rel, "lines": lines, "funcs": funcs, "area": a})
    files.sort(key=lambda f: -f["lines"])
    # Non-code assets: count per top folder.
    assets = {}
    for top in ("art", "data", "docs"):
        n = 0
        size = 0
        by_ext = defaultdict(int)
        for path in walk(os.path.join(ROOT, top)):
            n += 1
            size += os.path.getsize(path)
            by_ext[os.path.splitext(path)[1]] += 1
        assets[top] = {"files": n, "bytes": size, "by_ext": dict(sorted(by_ext.items(), key=lambda kv: -kv[1])[:12])}
    result = {
        "areas": {k: {**v, "ext": dict(v["ext"])} for k, v in sorted(per_area.items())},
        "largest": files[:60],
        "assets": assets,
        "totals": {
            "gd_files": sum(1 for f in files if f["path"].endswith(".gd")),
            "gd_lines": sum(f["lines"] for f in files if f["path"].endswith(".gd")),
            "py_files": sum(1 for f in files if f["path"].endswith(".py")),
            "py_lines": sum(f["lines"] for f in files if f["path"].endswith(".py")),
        },
    }
    if out:
        with open(out, "w") as fh:
            json.dump(result, fh, indent=1)
    print("%-52s %6s %8s %6s" % ("area", "files", "lines", "funcs"))
    for k, v in sorted(per_area.items(), key=lambda kv: -kv[1]["lines"]):
        print("%-52s %6d %8d %6d" % (k, v["files"], v["lines"], v["funcs"]))
    print("\nTotals:", result["totals"])
    print("\nLargest files:")
    for f in files[:40]:
        print("%6d %4d  %s" % (f["lines"], f["funcs"], f["path"]))
    print("\nAssets:", json.dumps({k: {"files": v["files"], "MB": round(v["bytes"] / 1e6, 1)} for k, v in assets.items()}))


if __name__ == "__main__":
    main()
