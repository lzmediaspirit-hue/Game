"""Shared helpers for the Jade River data builders.

The game reads only the JSON files in data/. These builders are an authoring aid:
they keep formula-driven tables (realm ladder, equipment bands, rooms) consistent.
Run `python3 tools/data/build_data.py` from the JadeRiver folder.
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = os.path.join(ROOT, "data")
SCHEMA_VERSION = 1


def write(name, payload, folder=DATA):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name)
    body = dict(payload)
    body.setdefault("schema_version", SCHEMA_VERSION)
    ordered = {"schema_version": body.pop("schema_version")}
    ordered.update(body)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ordered, f, indent=1, ensure_ascii=False)
        f.write("\n")
    return path


def entries(name, rows, **extra):
    ids = set()
    for r in rows:
        assert "id" in r, (name, r)
        assert r["id"] not in ids, (name, "duplicate", r["id"])
        ids.add(r["id"])
    payload = {"entries": rows}
    payload.update(extra)
    return write(name, payload)


def req(*conds, any_of=False):
    return {"any" if any_of else "all": list(conds)}


def c(kind, cause=None, hard=True, fix=None, **fields):
    d = {"kind": kind}
    d.update(fields)
    if cause:
        d["cause"] = cause
    if hard is not None:
        d["hard"] = hard
    if fix:
        d["fix"] = fix
    return d


def titled(snake):
    small = {"of", "the", "and", "in", "to", "a", "on"}
    words = snake.split("_")
    return " ".join(w if (i and w in small) else w.capitalize() for i, w in enumerate(words))
