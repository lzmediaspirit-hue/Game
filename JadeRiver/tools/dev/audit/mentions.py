#!/usr/bin/env python3
"""Audit 45: for each file given (or each tools/dev, tests and tools/art script by default), how many docs, code files
and runners name it by stem, and the date of its last commit (read-only; runs `git log` in this checkout).

Usage: python3 tools/dev/audit/mentions.py [--json OUT] [paths...]
"""
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def corpus(folders, exts):
    out = {}
    for f in folders:
        for dp, dns, fns in os.walk(os.path.join(ROOT, f)):
            dns[:] = [d for d in dns if d not in ("__pycache__", "audit", ".godot")]
            for fn in fns:
                if fn.endswith(exts):
                    p = os.path.join(dp, fn)
                    out[os.path.relpath(p, ROOT)] = open(p, encoding="utf-8", errors="replace").read()
    return out


def last_commit(path):
    try:
        r = subprocess.run(["git", "log", "-1", "--format=%cs|%s", "--", path], cwd=ROOT, capture_output=True, text=True, timeout=60)
        return r.stdout.strip()[:90]
    except Exception:
        return ""


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    if out in args:
        args.remove(out)
    if not args:
        for f in ("tools/dev", "tests"):
            for fn in sorted(os.listdir(os.path.join(ROOT, f))):
                if fn.endswith((".gd", ".py")):
                    args.append(f + "/" + fn)
    docs = corpus(["docs"], (".md",))
    docs.update({k: v for k, v in corpus(["."], (".md",)).items() if not k.startswith("docs")})
    code = corpus(["scripts", "tests", "tools"], (".gd", ".py", ".sh", ".ps1", ".tscn"))
    code.update({k: v for k, v in corpus(["."], (".ps1", ".sh")).items()})
    rows = []
    for p in args:
        stem = os.path.splitext(os.path.basename(p))[0]
        own = {p, os.path.splitext(p)[0] + ".tscn"}
        d = sorted(k for k, v in docs.items() if stem in v)
        c = sorted(k for k, v in code.items() if stem in v and k not in own)
        rows.append({"path": p, "lines": open(os.path.join(ROOT, p), encoding="utf-8", errors="replace").read().count("\n"),
                     "docs": len(d), "docs_sample": d[:3], "code": c[:6], "last": last_commit(p)})
    if out:
        json.dump(rows, open(out, "w"), indent=1)
    for r in rows:
        print("%5d docs=%-3d code=%-2d %-44s %s | %s" % (r["lines"], r["docs"], len(r["code"]), r["path"], r["last"], r["code"][:3]))


if __name__ == "__main__":
    main()
