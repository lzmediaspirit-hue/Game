#!/usr/bin/env python3
"""Audit 45: a read-only scan of the Python generators under tools/ (AST, nothing is imported or run).

Usage: python3 tools/dev/audit/py_graph.py [--json OUT] [--quiet]

Per module: lines, entry point (`if __name__ == "__main__"`), what it imports (resolved to files under tools/),
who imports it, dynamic loaders (build_data.MODULES, importlib by name, spec_from_file_location), and what writes
into data/ or art/ (open(..., "w"), json.dump, Image.save, wave writes). Top-level functions and classes whose
name occurs nowhere else in tools/ (and in no string) are listed as unreferenced.

Roots: modules with an entry point that something runs (tools/run_tests.sh, *.ps1, *.sh, a README, another
module's subprocess call, build_data.MODULES), plus every module with an entry point (a CLI a person runs).
"""
import ast
import json
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TOOLS = os.path.join(ROOT, "tools")


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def py_files():
    for dp, dns, fns in os.walk(TOOLS):
        dns[:] = [d for d in dns if d != "__pycache__"]
        for fn in fns:
            if fn.endswith(".py"):
                yield os.path.join(dp, fn)


def main():
    out = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    quiet = "--quiet" in sys.argv
    mods = {}
    by_stem = defaultdict(list)
    for p in py_files():
        r = rel(p)
        src = open(p, encoding="utf-8", errors="replace").read()
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            mods[r] = {"error": str(e), "lines": src.count("\n") + 1}
            continue
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    imports.add(a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(("." * node.level) + node.module)
                    for a in node.names:
                        imports.add(("." * node.level) + node.module + "." + a.name)
                else:
                    for a in node.names:
                        imports.add("." * node.level + a.name)
        top = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                end = getattr(node, "end_lineno", node.lineno)
                top.append({"name": node.name, "line": node.lineno, "lines": end - node.lineno + 1,
                            "kind": "class" if isinstance(node, ast.ClassDef) else "def",
                            "decorated": bool(node.decorator_list)})
        names = defaultdict(int)
        strings = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                names[node.id] += 1
            elif isinstance(node, ast.Attribute):
                names[node.attr] += 1
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                strings.add(node.value)
                for w in re.findall(r"[A-Za-z_]\w*", node.value):
                    strings.add(w)
            elif isinstance(node, ast.alias):
                names[(node.asname or node.name).split(".")[-1]] += 1
        writes = sorted(set(re.findall(r"""["'](?:\.\./)*((?:data|art|docs)/[^"'\s{}]*)""", src)))[:12]
        mods[r] = {
            "lines": src.count("\n") + 1,
            "main": "__name__" in src and "__main__" in src,
            "imports": sorted(imports),
            "top": top,
            "names": dict(names),
            "strings": strings,
            "writes": writes,
            "subprocess": sorted(set(re.findall(r"tools/[\w/]+\.py", src))),
        }
        by_stem[os.path.splitext(os.path.basename(r))[0]].append(r)

    # Resolve imports to files: by stem, preferring the same folder, then a sys.path folder named in the file.
    imported_by = defaultdict(set)
    for r, m in mods.items():
        if "imports" not in m:
            continue
        here = os.path.dirname(r)
        for imp in m["imports"]:
            if imp.startswith("."):   # a relative import resolves against the package folder, not by stem
                lvl = len(imp) - len(imp.lstrip("."))
                base = here
                for _ in range(lvl - 1):
                    base = os.path.dirname(base)
                path = base + "/" + "/".join(imp.lstrip(".").split("."))
                for c in (path + ".py", path + "/__init__.py"):
                    if c in mods and c != r:
                        imported_by[c].add(r)
                continue
            parts = imp.lstrip(".").split(".")
            for i in range(len(parts), 0, -1):
                stem = parts[i - 1]
                cands = by_stem.get(stem, [])
                if not cands:
                    continue
                pkg = "/".join(parts[:i - 1])
                best = [c for c in cands if os.path.dirname(c) == here] or \
                       [c for c in cands if pkg and os.path.dirname(c).endswith(pkg)] or \
                       [c for c in cands if c.endswith("/" + "/".join(parts[:i]) + ".py")] or cands
                for c in best[:1]:
                    if c != r:
                        imported_by[c].add(r)
                break
            # package imports: "figure.sets" -> figure/sets/__init__.py
            pk = "/".join(imp.lstrip(".").split("."))
            for c in mods:
                if c.endswith("/" + pk + "/__init__.py") and c != r:
                    imported_by[c].add(r)
    # Dynamic loaders.
    dyn = {}
    bd = open(os.path.join(TOOLS, "data", "build_data.py")).read()
    mm = re.search(r"MODULES = \[([^\]]*)\]", bd)
    build_modules = re.findall(r'"(\w+)"', mm.group(1)) if mm else []
    for s in build_modules:
        for c in by_stem.get(s, []):
            if c.startswith("tools/data/"):
                imported_by[c].add("tools/data/build_data.py (MODULES)")
                dyn[c] = "build_data.MODULES"
    # tools/art/pixel.py loads tools/art/creatures/<id>.py by path; creatures.py loads creature.<module>;
    # figure/sets/__init__.py loads every module in the folder.
    for c in mods:
        if c.startswith("tools/art/creatures/"):
            imported_by[c].add("tools/art/pixel.py (spec_from_file_location)")
            dyn[c] = "pixel.py creature loader"
        if c.startswith("tools/art/topdown/figure/sets/") and not c.endswith("__init__.py"):
            imported_by[c].add("tools/art/topdown/figure/sets/__init__.py (pkgutil)")
            dyn[c] = "figure.sets auto-import"
        if c.startswith("tools/art/topdown/creature/") and not c.endswith("__init__.py"):
            dyn.setdefault(c, "creatures.py importlib creature.<module>")
    # Everything that names a tool from outside Python.
    outside = ""
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in (".godot", ".git", "__pycache__") and not (dp == ROOT and d in ("art", "data"))]
        for fn in fns:
            if fn.endswith((".sh", ".ps1", ".md", ".gd", ".py")):
                try:
                    outside += open(os.path.join(dp, fn), encoding="utf-8", errors="replace").read() + "\n"
                except OSError:
                    pass
    named_outside = {}
    for c in mods:
        base = os.path.basename(c)
        tail = "/".join(c.split("/")[-2:])
        named_outside[c] = outside.count(tail) + (outside.count(base) if base not in ("__init__.py",) else 0)

    # Cross-module name use for top-level defs.
    all_names = defaultdict(int)
    all_strings = set()
    for r, m in mods.items():
        for n, k in m.get("names", {}).items():
            all_names[n] += k
        all_strings |= m.get("strings", set())
    unref = []
    for r, m in mods.items():
        for d in m.get("top", []):
            n = d["name"]
            if n.startswith("__") or d.get("decorated"):
                continue   # a decorator registers it by id (@sfx("hit"), @music(...), @icon(...))
            uses = all_names.get(n, 0)
            if uses == 0 and n not in all_strings:
                if n in ("main", "build", "build_items", "build_artifacts", "check", "run", "cli"):
                    continue
                unref.append({"path": r, **d})
    modules = []
    for r, m in sorted(mods.items()):
        modules.append({
            "path": r, "lines": m["lines"], "main": m.get("main", False),
            "imported_by": sorted(imported_by.get(r, [])), "dynamic": dyn.get(r, ""),
            "named_outside": named_outside.get(r, 0), "writes": m.get("writes", []),
        })
    orphans = [x for x in modules if not x["imported_by"] and not x["main"] and not x["dynamic"]
               and not x["path"].endswith("__init__.py")]
    cli_only = [x for x in modules if not x["imported_by"] and x["main"] and x["named_outside"] <= 1]
    result = {
        "summary": {
            "modules": len(modules), "lines": sum(x["lines"] for x in modules),
            "orphan_modules": len(orphans), "orphan_lines": sum(x["lines"] for x in orphans),
            "cli_modules_named_nowhere": len(cli_only), "cli_lines": sum(x["lines"] for x in cli_only),
            "unreferenced_top_defs": len(unref), "unreferenced_top_lines": sum(x["lines"] for x in unref),
        },
        "orphans": orphans, "cli_named_nowhere": cli_only, "unreferenced_defs": unref, "modules": modules,
    }
    if out:
        with open(out, "w") as fh:
            json.dump(result, fh, indent=1)
    if not quiet:
        print(json.dumps(result["summary"], indent=1))
        print("\nModules nothing imports and with no entry point:")
        for x in orphans:
            print("  %5d %s" % (x["lines"], x["path"]))
        print("\nCLI modules nothing imports and nothing names (a person may still run them):")
        for x in cli_only:
            print("  %5d %s named=%d" % (x["lines"], x["path"], x["named_outside"]))
        print("\nUnreferenced top-level defs:")
        for x in unref:
            print("  %s:%d %s (%d lines)" % (x["path"], x["line"], x["name"], x["lines"]))


if __name__ == "__main__":
    main()
