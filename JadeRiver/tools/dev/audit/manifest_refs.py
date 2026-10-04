#!/usr/bin/env python3
"""Audit 45: manifest entries (an id that points at art or audio) that nothing names (read-only).

Usage: python3 tools/dev/audit/manifest_refs.py [--json OUT]

Every file under art/ is named by a manifest (asset_refs.py), so the dead weight sits one level up: a manifest id
no data row, no script string and no composed key names. The corpus is every string (and key) in data/**/*.json
except the manifest itself, plus every string literal in scripts/. An id also counts as named when a composed form
in the code could build it: a script string that is a prefix of the id and ends in "_", ":" or "/" (the loaders
build "hud_" + x, "base:" + el ...). Reported per manifest: ids, unnamed ids, and the bytes of the files only those
ids point at.
"""
import glob
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
def _files(v):
    """Every res:// path under a manifest entry."""
    out = []
    st = [v]
    while st:
        y = st.pop()
        if isinstance(y, dict):
            st.extend(y.values())
        elif isinstance(y, list):
            st.extend(y)
        elif isinstance(y, str) and y.startswith("res://"):
            out.append(y)
    return out


def _entries(d):
    return {k: _files(v) for k, v in d.items() if k not in ("schema_version", "scale", "elements", "bands")}


MANIFESTS = {
    "icon_manifest": lambda d: {k.split("@")[0]: [v] for k, v in d.items() if isinstance(v, str)},
    "prop_art": _entries,
    "creature_art": _entries,
    "fx_art": lambda d: _entries(d.get("fx", {})) if isinstance(d.get("fx"), dict) else {},
    "ui_assets": _entries,
    "ui_assets_hd": _entries,
}


def strings_of(x, out):
    st = [x]
    while st:
        y = st.pop()
        if isinstance(y, dict):
            for k, v in y.items():
                out[k] += 1
                st.append(v)
        elif isinstance(y, list):
            st.extend(y)
        elif isinstance(y, str):
            out[y] += 1


def main():
    out_path = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    data = {}
    for f in glob.glob(os.path.join(ROOT, "data", "**", "*.json"), recursive=True):
        try:
            data[os.path.relpath(f, ROOT)] = json.load(open(f, encoding="utf-8"))
        except Exception:
            pass
    code = Counter()
    prefixes = set()
    for f in glob.glob(os.path.join(ROOT, "scripts", "**", "*.gd"), recursive=True):
        for m in re.finditer(r'"([^"\n]*)"', open(f, encoding="utf-8").read()):
            s = m.group(1)
            code[s] += 1
            if s.endswith(("_", ":", "/")) and len(s) >= 3:
                prefixes.add(s)
            elif "%" in s and len(s.split("%")[0]) >= 3:
                prefixes.add(s.split("%")[0])   # "hud_ring_%d" % size
    result = {}
    for name, fn in MANIFESTS.items():
        path = "data/%s.json" % name
        if path not in data:
            continue
        corpus = Counter(code)
        for p, d in data.items():
            if p != path:
                strings_of(d, corpus)
        try:
            ids = fn(data[path])
        except Exception as e:
            result[name] = {"error": str(e)}
            continue
        unnamed = []
        for i in sorted(ids):
            if corpus[i]:
                continue
            if any(i.startswith(pf) or ("hud_" + i) in corpus for pf in prefixes if i.startswith(pf)):
                continue
            unnamed.append(i)
        size = 0
        for i in unnamed:
            for v in ids[i]:
                fp = os.path.join(ROOT, str(v).replace("res://", ""))
                if v and os.path.isfile(fp):
                    size += os.path.getsize(fp)
        result[name] = {"ids": len(ids), "unnamed": len(unnamed), "unnamed_bytes": size, "sample": unnamed[:40]}
    if out_path:
        json.dump(result, open(out_path, "w"), indent=1)
    for k, v in result.items():
        print("%-14s %s" % (k, {kk: vv for kk, vv in v.items() if kk != "sample"}))
        print("   ", v.get("sample", [])[:25])


if __name__ == "__main__":
    main()
