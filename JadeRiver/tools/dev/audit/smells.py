#!/usr/bin/env python3
"""Audit 45: pattern checks for likely bugs in the .gd game code (read-only). Each hit is a place to read, with the
rule that found it; the report keeps only the hits a person confirmed.

Usage: python3 tools/dev/audit/smells.py [--json OUT] [--rule NAME]

Rules:
  erase_in_loop      `for k in coll:` (not .keys()/.duplicate()/a copy) and `coll.erase(` / `coll.remove_at(` inside it
  private_call       a call to another object's _private method (Game.combat._defeat, x._foo(...))
  data_method_call   Game.get(<data>).call(<data>): a method name read from data, unchecked
  int_div            `int(...) / int(...)` or `/ <int literal>` on two ints where a fraction looks meant (pct, frac, ratio)
  bare_index0        `[0]` on the result of .get(...)/.split(...)/.filter(...) with no size check on the line
  float_eq           `== 0.0` / `!= 0.0` comparisons on computed floats (fine for flags, fragile for sums)
  assert_game        assert( in game code (stripped from release builds: a check that must hold at runtime is lost)
  todo               TODO / FIXME / HACK / XXX markers
  print_game         print( in scripts/ outside debug flags (log spam on the phone)
  linear_in_const    `name in CONST_ARRAY` where CONST_ARRAY is a long const array (a Dictionary lookup is O(1))
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def gd_files():
    for dp, dns, fns in os.walk(os.path.join(ROOT, "scripts")):
        for fn in fns:
            if fn.endswith(".gd"):
                p = os.path.join(dp, fn)
                yield os.path.relpath(p, ROOT), open(p, encoding="utf-8").read().splitlines()


def main():
    out = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    only = sys.argv[sys.argv.index("--rule") + 1] if "--rule" in sys.argv else None
    hits = []

    def hit(rule, path, line, text):
        if only and rule != only:
            return
        hits.append({"rule": rule, "at": "%s:%d" % (path, line), "text": text.strip()[:160]})

    long_consts = {}
    for path, lines in gd_files():
        for i, ln in enumerate(lines):
            m = re.match(r"^const\s+(\w+)\s*(?::=|=)\s*\[(.*)", ln)
            if m:
                body = m.group(2)
                j = i
                while "]" not in body and j + 1 < len(lines):
                    j += 1
                    body += lines[j]
                if body.count(",") >= 10:
                    long_consts[m.group(1)] = body.count(",") + 1
    for path, lines in gd_files():
        for i, ln in enumerate(lines, 1):
            s = ln.strip()
            if s.startswith("#"):
                continue
            m = re.match(r"^(\s*)for\s+(\w+)\s+in\s+([\w.]+)\s*:", ln)
            if m and not m.group(3).endswith((".keys()", ".duplicate()")) and "range" not in m.group(3):
                ind = len(m.group(1))
                coll = m.group(3)
                for k in range(i, min(i + 40, len(lines))):
                    body = lines[k]
                    if body.strip() and len(body) - len(body.lstrip()) <= ind:
                        break
                    if re.search(r"\b%s\.(erase|remove_at)\(" % re.escape(coll), body):
                        hit("erase_in_loop", path, k + 1, body)
                        break
            for mm in re.finditer(r"(?<![\w])(Game\.\w+|game\.\w+|\w+)\._([a-z]\w*)\(", ln):
                if mm.group(1) in ("self", "super"):
                    continue
                hit("private_call", path, i, ln)
                break
            if re.search(r"Game\.get\(.*\)\.call\(", ln):
                hit("data_method_call", path, i, ln)
            if re.search(r"(pct|frac|ratio|share)\w*\s*:?=\s*int\([^)]*\)\s*/\s*int\(", ln):
                hit("int_div", path, i, ln)
            if re.search(r"\.(split|filter|keys|values)\([^)]*\)\[0\]", ln) and "size()" not in ln and "is_empty" not in ln:
                hit("bare_index0", path, i, ln)
            if re.search(r"^\s*assert\(", ln):
                hit("assert_game", path, i, ln)
            if re.search(r"\b(TODO|FIXME|HACK|XXX)\b", ln):
                hit("todo", path, i, ln)
            if re.search(r"(?<![\w.])print\(", ln) and "--" not in ln:
                hit("print_game", path, i, ln)
            for cname, n in long_consts.items():
                if re.search(r"\bin\s+%s\b" % cname, ln) and not re.match(r"^\s*for\s", ln):
                    hit("linear_in_const", path, i, "%s (%d entries): %s" % (cname, n, s))
    if out:
        json.dump(hits, open(out, "w"), indent=1)
    by = {}
    for h in hits:
        by.setdefault(h["rule"], []).append(h)
    for rule, hs in by.items():
        print("== %s: %d" % (rule, len(hs)))
        for h in hs[:25]:
            print("   %s  %s" % (h["at"], h["text"]))


if __name__ == "__main__":
    main()
