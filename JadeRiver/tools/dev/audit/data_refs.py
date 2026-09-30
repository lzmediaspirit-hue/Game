#!/usr/bin/env python3
"""Audit 45: which data tables and data fields the game reads (read-only).

Usage: python3 tools/dev/audit/data_refs.py [--json OUT] [--quiet]

Tables: every data/*.json (ContentDB loads each one at boot unless LEGACY_FILES) plus data/topdown/*.json.
A table is read by the game when its name is a string literal in scripts/ (ContentDB.all("x"), entry("x", id),
config("x"), tables["x"], a path "res://data/x.json"). Tests and tools are counted apart. The writer is the
tools/ module that names "<table>.json".

Fields: for each table, the keys used in its entries (top level and one level down). A key is read when it is a
string literal or a `.key` attribute token anywhere in scripts/. Keys read nowhere in scripts/ are "unread" (medium
confidence: generic code may iterate a dictionary; tests and tools are listed so a key only a check reads shows).
"""
import json
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
STR_RX = re.compile(r'"((?:\\.|[^"\\\n])*)"')
ATTR_RX = re.compile(r"\.([A-Za-z_]\w*)")
ID_RX = re.compile(r"[A-Za-z_]\w*")


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def collect(folder, exts):
    out = {}
    for dp, dns, fns in os.walk(os.path.join(ROOT, folder)):
        dns[:] = [d for d in dns if d not in ("__pycache__",)]
        for fn in fns:
            if fn.endswith(exts):
                p = os.path.join(dp, fn)
                out[rel(p)] = open(p, encoding="utf-8", errors="replace").read()
    return out


def main():
    out = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    quiet = "--quiet" in sys.argv
    game = collect("scripts", (".gd",))
    tests = collect("tests", (".gd",))
    tools_gd = collect("tools", (".gd",))
    tools_py = collect("tools", (".py",))

    def strings_and_attrs(texts):
        s = defaultdict(int)
        a = defaultdict(int)
        ids = defaultdict(int)
        for t in texts.values():
            for m in STR_RX.finditer(t):
                s[m.group(1)] += 1
            for m in ATTR_RX.finditer(t):
                a[m.group(1)] += 1
            for m in ID_RX.finditer(t):
                ids[m.group(0)] += 1
        return s, a, ids

    g_s, g_a, g_ids = strings_and_attrs(game)
    t_s, t_a, _ = strings_and_attrs(tests)
    tg_s, tg_a, _ = strings_and_attrs(tools_gd)
    legacy = re.search(r"LEGACY_FILES := \[([^\]]*)\]", game.get("scripts/core/content_db.gd", ""))
    legacy = set(re.findall(r'"([^"]+)"', legacy.group(1))) if legacy else set()

    tables = []
    for folder in ("data", "data/topdown"):
        d = os.path.join(ROOT, folder)
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".json"):
                continue
            p = os.path.join(d, fn)
            r = rel(p)
            name = fn[:-5]
            try:
                data = json.load(open(p, encoding="utf-8"))
            except Exception as e:
                tables.append({"table": r, "error": str(e)})
                continue
            entries = data.get("entries") if isinstance(data, dict) else None
            n_entries = len(entries) if isinstance(entries, list) else 0
            # How the game names it.
            path_forms = [r, "res://" + r, fn]
            game_refs = g_s.get(name, 0) + sum(g_s.get(f, 0) for f in path_forms)
            if folder == "data/topdown" and os.path.exists(os.path.join(ROOT, "data", "rooms", fn)):
                game_refs += 1   # TopdownRoom.load_room(id): DIR + id + ".json" for a room of data/rooms/
            test_refs = t_s.get(name, 0) + sum(t_s.get(f, 0) for f in path_forms)
            tool_refs = tg_s.get(name, 0)
            writers = sorted(m for m, t in tools_py.items() if fn in t or ('"%s"' % name) in t and "write" in t)[:5]
            # Fields.
            # Field names only: the keys of list-table rows (and their nested dicts) that recur in 3+ rows. The keys of
            # config tables are mostly ids (an id-keyed map), so only list tables are scanned for fields.
            keys = defaultdict(int)
            rows = entries if isinstance(entries, list) else []
            for row in rows:
                if not isinstance(row, dict):
                    continue
                for k, v in row.items():
                    keys[k] += 1
                    if isinstance(v, dict) and len(v) < 40:
                        for k2 in v:
                            if isinstance(k2, str) and not re.match(r"^[\d.]+$", k2):
                                keys[k + "." + k2] += 1
            keys = {k: n for k, n in keys.items() if n >= 3 or "." not in k and n >= 1 and len(rows) <= 3}
            unread = []
            for k, n in keys.items():
                leaf = k.split(".")[-1]
                if leaf in ("id", "schema_version", "entries", "defaults", "_comment", "note", "notes", "_note"):
                    continue
                if g_s.get(leaf, 0) or g_a.get(leaf, 0) or g_ids.get(leaf, 0):
                    continue
                unread.append({"key": k, "rows": n, "tests": t_s.get(leaf, 0) + t_a.get(leaf, 0),
                               "tools_gd": tg_s.get(leaf, 0) + tg_a.get(leaf, 0)})
            tables.append({
                "table": r, "bytes": os.path.getsize(p), "entries": n_entries,
                "boot_loaded": folder == "data" and fn not in legacy,
                "game_refs": game_refs, "test_refs": test_refs, "tools_gd_refs": tool_refs, "writers": writers,
                "keys": len(keys), "unread_keys": sorted(unread, key=lambda x: -x["rows"]),
            })
    unused = [t for t in tables if "error" not in t and t["game_refs"] == 0]
    summary = {
        "tables": len(tables), "bytes": sum(t.get("bytes", 0) for t in tables),
        "not_named_by_game": len(unused), "not_named_bytes": sum(t["bytes"] for t in unused),
        "unread_keys": sum(len(t.get("unread_keys", [])) for t in tables),
    }
    result = {"summary": summary, "tables": tables}
    if out:
        with open(out, "w") as fh:
            json.dump(result, fh, indent=1)
    if not quiet:
        print(json.dumps(summary))
        print("\nTables the game code never names (ContentDB still loads the data/*.json ones at boot):")
        for t in unused:
            print("  %-40s %8d B entries=%4d tests=%d tools=%d writers=%s" % (t["table"], t["bytes"], t["entries"], t["test_refs"], t["tools_gd_refs"], t["writers"][:2]))
        print("\nUnread keys per table (top 10 tables):")
        for t in sorted(tables, key=lambda t: -len(t.get("unread_keys", [])))[:25]:
            ks = t.get("unread_keys", [])
            if ks:
                print("  %-36s %3d: %s" % (t["table"], len(ks), ", ".join("%s(%d)" % (k["key"], k["rows"]) for k in ks[:10])))


if __name__ == "__main__":
    main()
