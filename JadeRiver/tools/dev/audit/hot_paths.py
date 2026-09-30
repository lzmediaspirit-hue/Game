#!/usr/bin/env python3
"""Audit 45: allocation and lookup counts inside the per-frame functions of the game code (read-only).

Usage: python3 tools/dev/audit/hot_paths.py [--json OUT] [--top N]

A per-frame function is _process, _physics_process, _draw, tick (authorities), and every function whose name starts
with _draw/draw_ (called from _draw). In each, it counts what allocates or scans on every call:
  dict/array literals ({...}, [...] assigned or passed), .duplicate(, .keys()/.values(), .filter(/.map(/.sort,
  string formatting (% [ / % str / "..." % ), Tx.t( and ContentDB.* lookups, get_children(), nested for loops
  (a for inside a for: a candidate O(n^2)), and load( calls. The score weighs them; it is a map of where to look,
  not a verdict.
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
FRAME_FUNCS = re.compile(r"^(_process|_physics_process|_draw|tick|_draw_\w+|draw_\w+|_tick_\w+|advance)$")
PATTERNS = {
    "duplicate": (re.compile(r"\.duplicate\("), 3),
    "keys_values": (re.compile(r"\.(keys|values)\(\)"), 2),
    "filter_map_sort": (re.compile(r"\.(filter|map|sort_custom|sort)\("), 3),
    "format": (re.compile(r"\"\s*%\s*[\[\w(]"), 1),
    "tx": (re.compile(r"\bTx\.(t|plural)\("), 1),
    "contentdb": (re.compile(r"\bContentDB\.\w+\("), 1),
    "get_children": (re.compile(r"get_children\(\)"), 2),
    "load": (re.compile(r"(?<![\w.])load\(|ResourceLoader\.load\("), 5),
    "dict_literal": (re.compile(r"[=(,:]\s*\{\s*\"?\w"), 1),
    "new_obj": (re.compile(r"\b[A-Z]\w+\.new\("), 3),
}


def funcs(text):
    lines = text.splitlines()
    cur = None
    for i, ln in enumerate(lines, 1):
        m = re.match(r"^(static\s+)?func\s+(\w+)", ln)
        if m:
            if cur:
                yield cur
            cur = {"name": m.group(2), "line": i, "body": []}
            continue
        if cur is not None:
            if ln.strip() and not ln.startswith(("\t", " ", "#")):
                yield cur
                cur = None
            else:
                cur["body"].append(ln)
    if cur:
        yield cur


def nested_fors(body):
    n = 0
    stack = []
    for ln in body:
        s = ln.lstrip("\t")
        ind = len(ln) - len(s)
        while stack and stack[-1] >= ind:
            stack.pop()
        if re.match(r"for\s+\w+\s+in\s+", s):
            if stack:
                n += 1
            stack.append(ind)
    return n


def main():
    out = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 40
    rows = []
    for dp, dns, fns in os.walk(os.path.join(ROOT, "scripts")):
        for fn in fns:
            if not fn.endswith(".gd"):
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, ROOT)
            for f in funcs(open(p, encoding="utf-8").read()):
                if not FRAME_FUNCS.match(f["name"]):
                    continue
                code = "\n".join(ln for ln in f["body"] if not ln.strip().startswith("#"))
                counts = {k: len(rx.findall(code)) for k, (rx, _) in PATTERNS.items()}
                counts["nested_for"] = nested_fors(f["body"])
                score = sum(counts[k] * w for k, (_, w) in PATTERNS.items()) + counts["nested_for"] * 4
                rows.append({"where": "%s:%d" % (rel, f["line"]), "func": f["name"], "lines": len(f["body"]),
                             "score": score, "counts": {k: v for k, v in counts.items() if v}})
    rows.sort(key=lambda r: -r["score"])
    if out:
        json.dump(rows, open(out, "w"), indent=1)
    for r in rows[:top]:
        print("%4d %4d  %-58s %-22s %s" % (r["score"], r["lines"], r["where"], r["func"], r["counts"]))


if __name__ == "__main__":
    main()
