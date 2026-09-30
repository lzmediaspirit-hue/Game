#!/usr/bin/env python3
"""Audit 45: copy-paste detection across the .gd code and the .py generators (read-only).

Usage: python3 tools/dev/audit/dupes.py [--json OUT] [--window N] [--mode exact|shape] [--ext .gd|.py] [--quiet]

Lines are normalised (indentation, trailing comments and blank/comment-only lines dropped). In "shape" mode every
identifier becomes I, every number N and every string S, so a copy with renamed variables still matches. Windows
of N consecutive normalised lines are hashed; a hash seen in two places is a clone seed, and seeds that continue
line by line are merged into one clone region. Trivial lines (a lone "else:", "pass", "return", "}") don't count
toward a window's weight, so boilerplate doesn't dominate.
"""
import hashlib
import json
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TRIVIAL = {"else:", "pass", "return", "}", "{", "]", ")", "continue", "break", "try:", "finally:", "@staticmethod"}
STR = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')
NUM = re.compile(r"\b\d+(?:\.\d+)?\b")
IDS = re.compile(r"\b[A-Za-z_]\w*\b")
KEYWORDS = {"if", "elif", "else", "for", "in", "while", "return", "func", "def", "var", "const", "and", "or", "not",
            "match", "true", "false", "null", "None", "True", "False", "self", "static", "class", "extends", "await",
            "break", "continue", "pass", "import", "from", "as", "lambda", "with", "is", "range", "len", "str", "int",
            "float", "Vector2", "Color", "Rect2", "draw_rect", "draw_line", "draw_circle", "draw_string", "np", "min",
            "max", "abs", "append", "get", "has"}


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def norm(line, mode, ext):
    c = "#"
    s = line.strip()
    if not s or s.startswith(c):
        return None
    # drop a trailing comment outside strings (approximate: only if no quote after the #)
    i = s.find(" #")
    if i >= 0 and '"' not in s[i:] and "'" not in s[i:]:
        s = s[:i].rstrip()
    if ext == ".py" and (s.startswith(('"""', "'''"))):
        return None
    if mode == "shape":
        s = STR.sub("S", s)
        s = NUM.sub("N", s)
        s = IDS.sub(lambda m: m.group(0) if m.group(0) in KEYWORDS else "I", s)
    return s


def main():
    args = sys.argv
    out = args[args.index("--json") + 1] if "--json" in args else None
    win = int(args[args.index("--window") + 1]) if "--window" in args else 8
    mode = args[args.index("--mode") + 1] if "--mode" in args else "exact"
    exts = [args[args.index("--ext") + 1]] if "--ext" in args else [".gd", ".py"]
    quiet = "--quiet" in args
    files = {}
    for dp, dns, fns in os.walk(ROOT):
        top = dp == ROOT
        dns[:] = [d for d in dns if d not in (".godot", ".git", "__pycache__", "audit") and not (top and d in ("docs", "art", "data"))]
        for fn in fns:
            ext = os.path.splitext(fn)[1]
            if ext in exts:
                p = os.path.join(dp, fn)
                lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
                seq = []
                for i, ln in enumerate(lines, 1):
                    n = norm(ln, mode, ext)
                    if n is not None:
                        seq.append((n, i))
                files[rel(p)] = seq
    index = defaultdict(list)
    for path, seq in files.items():
        for k in range(len(seq) - win + 1):
            chunk = [s for s, _ in seq[k:k + win]]
            weight = sum(1 for s in chunk if s not in TRIVIAL and len(s) > 6)
            if weight < win * 0.75:
                continue
            h = hashlib.md5("\n".join(chunk).encode()).hexdigest()
            index[h].append((path, k))
    # Merge seeds into regions: for each pair of places (a, b), extend while the next window also matches.
    pairs = defaultdict(set)   # (pathA, pathB) -> set of (ka, kb)
    for h, locs in index.items():
        if len(locs) < 2 or len(locs) > 12:
            continue
        for i in range(len(locs)):
            for j in range(i + 1, len(locs)):
                a, b = locs[i], locs[j]
                if a[0] == b[0] and abs(a[1] - b[1]) < win:
                    continue
                if (a[0], a[1]) > (b[0], b[1]):
                    a, b = b, a
                pairs[(a[0], b[0])].add((a[1], b[1]))
    regions = []
    for (pa, pb), seeds in pairs.items():
        seeds = sorted(seeds)
        used = set()
        for ka, kb in seeds:
            if (ka, kb) in used:
                continue
            n = 0
            while (ka + n, kb + n) in seeds:
                used.add((ka + n, kb + n))
                n += 1
            la0 = files[pa][ka][1]
            la1 = files[pa][min(ka + n + win - 2, len(files[pa]) - 1)][1]
            lb0 = files[pb][kb][1]
            lb1 = files[pb][min(kb + n + win - 2, len(files[pb]) - 1)][1]
            regions.append({"a": "%s:%d-%d" % (pa, la0, la1), "b": "%s:%d-%d" % (pb, lb0, lb1),
                            "lines": n + win - 1, "same_file": pa == pb,
                            "sample": files[pa][ka][0][:110]})
    regions.sort(key=lambda r: -r["lines"])
    # Per file pair totals.
    by_pair = defaultdict(int)
    for r in regions:
        by_pair[(r["a"].split(":")[0], r["b"].split(":")[0])] += r["lines"]
    summary = {"mode": mode, "window": win, "files": len(files), "regions": len(regions),
               "duplicated_lines": sum(r["lines"] for r in regions)}
    result = {"summary": summary, "regions": regions[:400],
              "by_pair": [{"a": a, "b": b, "lines": n} for (a, b), n in sorted(by_pair.items(), key=lambda kv: -kv[1])[:150]]}
    if out:
        with open(out, "w") as fh:
            json.dump(result, fh, indent=1)
    if not quiet:
        print(json.dumps(summary))
        print("\nTop file pairs by duplicated lines:")
        for x in result["by_pair"][:60]:
            print("  %5d  %s  <->  %s" % (x["lines"], x["a"], x["b"]))
        print("\nLongest regions:")
        for r in regions[:50]:
            print("  %4d  %s  <->  %s   | %s" % (r["lines"], r["a"], r["b"], r["sample"]))


if __name__ == "__main__":
    main()
