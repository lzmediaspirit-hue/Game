#!/usr/bin/env python3
"""Audit 45: the largest functions of .gd files (read-only).

Usage: python3 tools/dev/audit/funcs.py N file.gd [file.gd ...]
Prints each file's function count and its N largest functions as name@line(lines).
"""
import re
import sys


def funcs(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    out = []
    cur = None
    for i, ln in enumerate(lines, 1):
        m = re.match(r"^(static\s+)?func\s+(\w+)", ln)
        if m:
            if cur:
                out.append(cur)
            cur = [m.group(2), i, i]
        elif cur and ln.strip() and not ln.startswith(("\t", " ", "#")):
            out.append(cur)
            cur = None
        elif cur:
            cur[2] = i
    if cur:
        out.append(cur)
    return out


def main():
    n = int(sys.argv[1])
    for p in sys.argv[2:]:
        fs = sorted(funcs(p), key=lambda f: -(f[2] - f[1]))
        print(p, len(fs), "funcs; largest:", ", ".join("%s@%d(%d)" % (f[0], f[1], f[2] - f[1] + 1) for f in fs[:n]))


if __name__ == "__main__":
    main()
