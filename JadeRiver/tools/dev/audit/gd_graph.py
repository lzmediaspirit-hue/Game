#!/usr/bin/env python3
"""Audit 45: a read-only GDScript reference graph and dead-code scan.

Usage: python3 tools/dev/audit/gd_graph.py [--json OUT] [--quiet]

What it does, all by text analysis (nothing is run, nothing in the project is written):
  * tokenizes every .gd file (comments and strings split out), records its class_name, extends, funcs, signals,
    consts, member vars, enums and inner classes;
  * collects every string literal in the code, every string in data/**/*.json and every path/method/signal in
    .tscn/.godot files, so string-based calls (call("x"), has_method("x"), Callable(o, "x"), connect("x"),
    data-driven names such as unlocks.json "count": ["quest", "done_count"]) count as references;
  * builds the script graph (res:// paths, preload/load, class_name tokens) from the roots (project.godot
    autoloads + main scene; the test suites in tools/run_tests.sh; every other .tscn/.gd under tests/ and tools/);
  * reports scripts nothing reaches, and functions/signals/consts/vars whose name appears nowhere but their own
    definition, split by where the remaining uses are (game code, tests, tools).

Confidence rules (written to the JSON per finding):
  high   - the name occurs nowhere else in any .gd/.tscn/.json/.py/.sh file, and matches no dynamic prefix.
  medium - it occurs only in tests/tools (the game never calls it), or only as a string in data.
  low    - the name is shared with another definition (polymorphism), or matches a dynamic-call prefix.
"""
import json
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SKIP_DIRS = {".godot", ".git", "__pycache__", "docs"}

# Godot callbacks and base-class hooks the engine (or our own base classes, by name) invoke.
VIRTUALS = {
    "_ready", "_process", "_physics_process", "_draw", "_input", "_unhandled_input", "_unhandled_key_input",
    "_gui_input", "_notification", "_init", "_enter_tree", "_exit_tree", "_get_minimum_size", "_to_string",
    "_has_point", "_can_drop_data", "_drop_data", "_get_drag_data", "_make_custom_tooltip", "_get", "_set",
    "_get_property_list", "_shortcut_input", "_validate_property", "_iter_init", "_iter_next", "_iter_get",
    "_run", "_initialize", "_finalize", "_integrate_forces", "_get_configuration_warnings", "_draw_style",
    "_get_draw_rect", "_get_minimum_size", "_test_mask", "_property_can_revert", "_property_get_revert",
}
# Names built at runtime: prefix -> the file that builds them (found by grep for call("x" + ...)).
DYNAMIC_PREFIXES = {
    ("scripts/presentation/moment_view.gd", "_draw_"): "moment_view.gd:512 call(\"_draw_\" + kind)",
    ("tests/valley_run.gd", "sec_"): "valley_run.gd:54 call(\"sec_\" + s)",
    ("tests/prologue_run.gd", "sec_"): "valley_run.gd extends prologue_run.gd; call(\"sec_\" + s)",
}

TOKEN_RX = re.compile(
    r'(?P<tq>"""(?:.|\n)*?""")|(?P<str>"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\')|(?P<com>#[^\n]*)|'
    r'(?P<sname>&"(?:\\.|[^"\\\n])*")|(?P<np>\^"(?:\\.|[^"\\\n])*")|(?P<id>[A-Za-z_]\w*)|(?P<nl>\n)'
)
DEF_FUNC = re.compile(r"^(\s*)(static\s+)?func\s+([A-Za-z_]\w*)")
DEF_SIGNAL = re.compile(r"^(\s*)signal\s+([A-Za-z_]\w*)")
DEF_CONST = re.compile(r"^(\s*)(?:static\s+)?const\s+([A-Za-z_]\w*)")
DEF_VAR = re.compile(r"^(\s*)(?:@\w+(?:\([^)]*\))?\s+)*(?:static\s+)?var\s+([A-Za-z_]\w*)")
DEF_ENUM = re.compile(r"^(\s*)enum\s+([A-Za-z_]\w*)")
DEF_CLASS = re.compile(r"^(\s*)class\s+([A-Za-z_]\w*)")
CLASS_NAME = re.compile(r"^class_name\s+([A-Za-z_]\w*)", re.M)
EXTENDS = re.compile(r"^extends\s+(\"[^\"]+\"|[A-Za-z_][\w.]*)", re.M)
RES_PATH = re.compile(r"res://[A-Za-z0-9_./%-]+")


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def walk(exts):
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for fn in fns:
            if os.path.splitext(fn)[1] in exts:
                yield os.path.join(dp, fn)


def read(p):
    with open(p, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def tokenize(text):
    """Returns (identifier tokens with line numbers, string literals with line numbers)."""
    ids = []
    strs = []
    line = 1
    for m in TOKEN_RX.finditer(text):
        k = m.lastgroup
        v = m.group(k)
        if k == "nl":
            line += 1
            continue
        if k == "id":
            ids.append((v, line))
        elif k in ("str", "sname", "np"):
            s = v[2:-1] if k in ("sname", "np") else v[1:-1]
            strs.append((s, line))
        elif k == "tq":
            strs.append((v[3:-3], line))
        line += v.count("\n")
    return ids, strs


def area(path):
    if path.startswith("scripts/"):
        return "game"
    if path.startswith("tests/"):
        return "tests"
    if path.startswith("tools/"):
        return "tools"
    return "other"


class GdFile:
    def __init__(self, path, text):
        self.path = path
        self.text = text
        self.class_name = (CLASS_NAME.search(text) or [None, None])[1]
        ext = EXTENDS.search(text)
        self.extends = ext.group(1).strip('"') if ext else ""
        self.ids, self.strs = tokenize(text)
        self.funcs = []
        self.signals = []
        self.consts = []
        self.vars = []
        self.enums = []
        self.classes = []
        self.lines = text.count("\n") + 1
        cur_func = None
        for i, ln in enumerate(text.splitlines(), 1):
            m = DEF_FUNC.match(ln)
            if m:
                cur_func = {"name": m.group(3), "line": i, "static": bool(m.group(2)), "indent": len(m.group(1)), "end": i}
                self.funcs.append(cur_func)
                continue
            if cur_func is not None and ln.strip() and not ln.startswith((" ", "\t")) and not ln.startswith("#"):
                cur_func = None
            if cur_func is not None:
                cur_func["end"] = i
            for rx, bucket in ((DEF_SIGNAL, self.signals), (DEF_CONST, self.consts), (DEF_ENUM, self.enums),
                               (DEF_CLASS, self.classes)):
                mm = rx.match(ln)
                if mm:
                    bucket.append({"name": mm.group(2), "line": i, "indent": len(mm.group(1))})
            mv = DEF_VAR.match(ln)
            if mv and len(mv.group(1)) == 0:
                self.vars.append({"name": mv.group(2), "line": i, "indent": 0})
        self.res_paths = set(RES_PATH.findall(text))


def main():
    out = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    quiet = "--quiet" in sys.argv
    gd = {}
    for p in walk({".gd"}):
        r = rel(p)
        gd[r] = GdFile(r, read(p))
    # Everything else that can name a script, method or signal.
    other_text = {}
    for p in walk({".tscn", ".tres", ".godot", ".cfg", ".py", ".sh", ".ps1", ".gdshader"}):
        other_text[rel(p)] = read(p)
    json_strings = defaultdict(set)   # string -> data files it appears in
    for p in walk({".json"}):
        r = rel(p)
        try:
            data = json.loads(read(p))
        except Exception:
            continue
        stack = [data]
        while stack:
            x = stack.pop()
            if isinstance(x, dict):
                for k, v in x.items():
                    json_strings[k].add(r)
                    stack.append(v)
            elif isinstance(x, list):
                stack.extend(x)
            elif isinstance(x, str):
                json_strings[x].add(r)

    # Identifier occurrences per name, per file.
    id_count = defaultdict(lambda: defaultdict(int))
    str_count = defaultdict(lambda: defaultdict(int))
    for f in gd.values():
        for name, _ in f.ids:
            id_count[name][f.path] += 1
        for s, _ in f.strs:
            str_count[s][f.path] += 1
    other_tokens = defaultdict(lambda: defaultdict(int))
    word = re.compile(r"[A-Za-z_]\w*")
    for r, t in other_text.items():
        for w in word.findall(t):
            other_tokens[w][r] += 1

    # --------------------------------------------------------------- script graph
    class_to_file = {f.class_name: f.path for f in gd.values() if f.class_name}
    edges = defaultdict(set)
    all_paths = set(gd) | {r for r in other_text if r.endswith((".tscn", ".tres"))}

    def path_targets(res_paths):
        out_ = set()
        for rp in res_paths:
            q = rp[len("res://"):]
            if "%" in q:   # a formatted path: every file it can match
                rx = re.compile("^" + re.escape(q).replace("%s", ".+").replace("%d", r"\d+") + "$")
                out_ |= {x for x in all_paths if rx.match(x)}
            elif q in all_paths:
                out_.add(q)
        return out_

    for f in gd.values():
        edges[f.path] |= path_targets(f.res_paths)
        names = {n for n, _ in f.ids}
        for cn, target in class_to_file.items():
            if cn in names and target != f.path:
                edges[f.path].add(target)
        if f.extends in class_to_file:
            edges[f.path].add(class_to_file[f.extends])
    for r, t in other_text.items():
        if r.endswith((".tscn", ".tres", ".godot")):
            edges[r] |= path_targets(set(RES_PATH.findall(t)))

    proj = other_text.get("project.godot", "")
    game_roots = {"project.godot"}
    edges["project.godot"] = path_targets(set(RES_PATH.findall(proj)))
    suites = re.search(r"suites=\(([^)]*)\)", other_text.get("tools/run_tests.sh", ""))
    test_roots = {"tests/%s.tscn" % s for s in (suites.group(1).split() if suites else [])}
    tool_roots = {r for r in all_paths if r.startswith(("tools/", "tests/")) and r.endswith(".tscn")} - test_roots
    # Standalone scripts run with --script (extends SceneTree/MainLoop) are their own roots.
    for f in gd.values():
        if f.extends in ("SceneTree", "MainLoop") and not f.path.startswith("scripts/"):
            tool_roots.add(f.path)

    def reach(roots):
        seen = set()
        stack = list(roots)
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            stack.extend(edges.get(x, ()))
        return seen

    r_game = reach(game_roots)
    r_test = reach(test_roots)
    r_tool = reach(tool_roots)
    scripts_report = []
    for path, f in sorted(gd.items()):
        where = []
        if path in r_game:
            where.append("game")
        if path in r_test:
            where.append("suites")
        if path in r_tool:
            where.append("tools/non-suite tests")
        refs = sorted(x for x, tg in edges.items() if path in tg and x != path)
        scripts_report.append({"path": path, "lines": f.lines, "reached_from": where, "referenced_by": refs,
                               "references": sorted(edges.get(path, ()))})
    unreached = [s for s in scripts_report if not s["reached_from"]]
    game_code_not_in_game = [s for s in scripts_report if s["path"].startswith("scripts/") and "game" not in s["reached_from"]]
    nonsuite_tests = [s for s in scripts_report if s["path"].startswith("tests/") and "suites" not in s["reached_from"]]

    # Orphan .uid files (a .gd.uid with no .gd).
    orphan_uids = []
    for p in walk({".uid"}):
        r = rel(p)
        if not os.path.exists(p[:-4]):
            orphan_uids.append(r)

    # --------------------------------------------------------------- symbol scan
    def uses_of(name, own_path, def_count):
        by_area = defaultdict(int)
        for p, n in id_count.get(name, {}).items():
            by_area[area(p)] += n
        # subtract the definitions themselves
        own_area = area(own_path)
        by_area[own_area] -= def_count
        strings = defaultdict(int)
        for p, n in str_count.get(name, {}).items():
            strings[area(p)] += n
        data = sorted(json_strings.get(name, ()))
        other = {p: n for p, n in other_tokens.get(name, {}).items() if not p.endswith(".py")}
        return {k: v for k, v in by_area.items() if v > 0}, dict(strings), data, other

    all_defs = defaultdict(list)   # name -> [(kind, path, line)]
    for f in gd.values():
        for kind, bucket in (("func", f.funcs), ("signal", f.signals), ("const", f.consts), ("var", f.vars),
                             ("enum", f.enums), ("class", f.classes)):
            for d in bucket:
                all_defs[d["name"]].append((kind, f.path, d["line"]))

    findings = []
    for f in gd.values():
        for kind, bucket in (("func", f.funcs), ("signal", f.signals), ("const", f.consts), ("var", f.vars),
                             ("enum", f.enums), ("class", f.classes)):
            for d in bucket:
                name = d["name"]
                if kind == "func" and name in VIRTUALS:
                    continue
                ndefs_here = sum(1 for k, p, _ in all_defs[name] if p == f.path)
                # every def of this name in the same area is a token too
                defs_same_area = sum(1 for k, p, _ in all_defs[name] if area(p) == area(f.path))
                ids, strs, data, other = uses_of(name, f.path, 0)
                # subtract all definitions of the name, per area
                for k, p, _ in all_defs[name]:
                    a = area(p)
                    ids[a] = ids.get(a, 0) - 1
                ids = {k: v for k, v in ids.items() if v > 0}
                shared = len(all_defs[name]) > 1
                dyn = [pfx for (fp, pfx) in DYNAMIC_PREFIXES if fp == f.path and name.startswith(pfx)]
                other_refs = {p: n for p, n in other.items() if not p.endswith(".py") or True}
                used_game = ids.get("game", 0) + strs.get("game", 0) + (1 if data else 0)
                used_any = sum(ids.values()) + sum(strs.values()) + len(data) + sum(other_refs.values())
                if used_any == 0 and not dyn:
                    conf = "low" if shared else "high"
                    status = "unreferenced"
                elif used_any == 0 and dyn:
                    conf = "low"
                    status = "unreferenced_but_dynamic_prefix"
                elif f.path.startswith("scripts/") and used_game == 0 and not dyn:
                    conf = "medium" if not shared else "low"
                    status = "not_used_by_game"
                else:
                    continue
                if kind == "var" and name.startswith("_") is False and status == "not_used_by_game":
                    pass
                end = d["line"]
                if kind == "func":
                    end = next((x["end"] for x in f.funcs if x["line"] == d["line"]), d["line"])
                findings.append({
                    "kind": kind, "name": name, "path": f.path, "line": d["line"], "end": end,
                    "lines": end - d["line"] + 1, "status": status, "confidence": conf,
                    "shared_name": shared, "uses": {"ids": ids, "strings": strs, "data": data[:5],
                                                     "other": dict(list(other_refs.items())[:5])},
                })

    # Private functions (leading underscore): used only in their own file, its ancestors (a base class calling a hook)
    # or its descendants, or by name in a string. Shared names elsewhere do not hide these.
    parent = {}
    for f in gd.values():
        e = f.extends
        if e.startswith("res://"):
            parent[f.path] = e[len("res://"):]
        elif e in class_to_file:
            parent[f.path] = class_to_file[e]
    children = defaultdict(set)
    for c, p_ in parent.items():
        children[p_].add(c)

    def family(path):
        fam = {path}
        x = path
        while x in parent:
            x = parent[x]
            fam.add(x)
        stack = [path]
        while stack:
            y = stack.pop()
            for c in children.get(y, ()):
                if c not in fam:
                    fam.add(c)
                    stack.append(c)
        return fam

    seen_keys = {(x["path"], x["line"]) for x in findings}
    for f in gd.values():
        fam = family(f.path)
        for d in f.funcs:
            name = d["name"]
            if not name.startswith("_") or name in VIRTUALS or (f.path, d["line"]) in seen_keys:
                continue
            if [1 for (fp, pfx) in DYNAMIC_PREFIXES if fp == f.path and name.startswith(pfx)]:
                continue
            n_in_family = sum(id_count.get(name, {}).get(q, 0) for q in fam)
            defs_in_family = sum(1 for k, p_, _ in all_defs[name] if p_ in fam)
            dotted = re.compile(r"\.%s\b" % re.escape(name))
            ext_dotted = [q for q, g in gd.items() if q not in fam and dotted.search(g.text)]
            as_string = sum(str_count.get(name, {}).values()) + len(json_strings.get(name, ()))
            if n_in_family - defs_in_family <= 0 and not ext_dotted and as_string == 0:
                findings.append({
                    "kind": "func", "name": name, "path": f.path, "line": d["line"], "end": d["end"],
                    "lines": d["end"] - d["line"] + 1, "status": "unreferenced_private", "confidence": "high",
                    "shared_name": len(all_defs[name]) > 1, "uses": {"family": sorted(fam)[:4]},
                })

    # Signals: emitted / connected.
    sig_report = []
    for f in gd.values():
        for d in f.signals:
            name = d["name"]
            emit_rx = re.compile(r"\b%s\.emit\b|emit_signal\(\s*[&]?\"%s\"" % (name, name))
            conn_rx = re.compile(r"\b%s\.connect\b|connect\(\s*[&]?\"%s\"|signal=\"%s\"|\b%s\.is_connected\b" % (name, name, name, name))
            emits = [p for p, g in gd.items() if emit_rx.search(g.text)]
            conns = [p for p, g in gd.items() if conn_rx.search(g.text)] + [r for r, t in other_text.items() if conn_rx.search(t)]
            if not emits or not conns:
                sig_report.append({"name": name, "path": f.path, "line": d["line"], "emitted_in": emits, "connected_in": conns})

    # Autoload usage per file (tangle metric).
    autoloads = re.findall(r"^(\w+)=\"\*res://", proj, re.M)
    auto_use = {}
    for f in gd.values():
        names = defaultdict(int)
        for n, _ in f.ids:
            if n in autoloads:
                names[n] += 1
        if names:
            auto_use[f.path] = dict(names)
    # Cross-authority calls: game.<authority>. inside authorities.
    auth_names = ["combat", "progression", "enemies", "world", "inventory", "quest", "economy", "accounts", "crafting",
                  "training", "mail", "achievements", "pets", "companions", "sect", "workshop", "relations", "calendar",
                  "field", "posts", "tutorials"]
    cross = defaultdict(lambda: defaultdict(int))
    rx_cross = re.compile(r"\bgame\.(%s)\.(\w+)" % "|".join(auth_names))
    rx_game = re.compile(r"\bGame\.(%s)\.(\w+)" % "|".join(auth_names))
    for f in gd.values():
        for m in rx_cross.finditer(f.text):
            cross[f.path][m.group(1)] += 1
        for m in rx_game.finditer(f.text):
            cross[f.path]["Game." + m.group(1)] += 1

    summary = {
        "gd_files": len(gd),
        "unreached_scripts": len(unreached),
        "unreached_lines": sum(s["lines"] for s in unreached),
        "game_scripts_not_reached_from_game": len(game_code_not_in_game),
        "nonsuite_tests": len(nonsuite_tests),
        "nonsuite_test_lines": sum(s["lines"] for s in nonsuite_tests),
        "orphan_uids": len(orphan_uids),
        "findings_by_status": {},
    }
    for x in findings:
        k = "%s/%s/%s" % (x["kind"], x["status"], x["confidence"])
        summary["findings_by_status"][k] = summary["findings_by_status"].get(k, 0) + 1
    dead_func_lines = sum(x["lines"] for x in findings if x["kind"] == "func" and x["status"] in ("unreferenced", "unreferenced_private") and x["path"].startswith("scripts/"))
    summary["unreferenced_game_func_lines"] = dead_func_lines
    summary["not_used_by_game_func_lines"] = sum(x["lines"] for x in findings if x["kind"] == "func" and x["status"] == "not_used_by_game")
    result = {
        "summary": summary,
        "unreached_scripts": unreached,
        "game_scripts_not_reached_from_game": game_code_not_in_game,
        "nonsuite_tests": nonsuite_tests,
        "orphan_uids": orphan_uids,
        "symbols": sorted(findings, key=lambda x: (x["path"], x["line"])),
        "signals": sig_report,
        "autoload_use": auto_use,
        "cross_authority": {k: dict(v) for k, v in cross.items()},
        "scripts": scripts_report,
        "dynamic_prefixes": {"%s:%s" % k: v for k, v in DYNAMIC_PREFIXES.items()},
    }
    if out:
        with open(out, "w") as fh:
            json.dump(result, fh, indent=1)
    if not quiet:
        print(json.dumps(summary, indent=1))
        print("\nUnreached scripts:")
        for s in unreached:
            print("  %5d  %s" % (s["lines"], s["path"]))
        print("\nscripts/ not reached from the game roots:")
        for s in game_code_not_in_game:
            print("  %5d  %s  %s" % (s["lines"], s["path"], s["reached_from"]))
        print("\nOrphan uids:", orphan_uids)
        print("\nSignals never emitted or never connected:")
        for s in sig_report:
            print("  %s:%d %s emit=%s conn=%s" % (s["path"], s["line"], s["name"], s["emitted_in"][:2], s["connected_in"][:2]))


if __name__ == "__main__":
    main()
