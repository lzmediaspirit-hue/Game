#!/usr/bin/env python3
"""Audit 45: run the SceneTree test scripts that no suite runs, each with a time limit, and report whether each still
parses and finishes (read-only: the scripts write only under user:// or print).

The default list is tests/README.md's "Other scripts here": the side-view tests, and two review renders that need a
window (headless, they run to the time limit). S2 deleted the broken and window-only scripts the audit ran
(docs/architecture/audit_45.md section 3.3). A named script that is not on disk is reported, not run, and fails the run.

Usage: GODOT=/path/to/godot python3 tools/dev/audit/run_legacy.py [--json OUT] [script.gd ...]
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT = ["combo_tests", "landing_matrix", "map_generation", "movement_v07", "room_gates",
           "gauntlet_review", "weapon_combo_outlines"]


def main():
    godot = os.environ.get("GODOT", "godot")
    out = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    names = [a for a in sys.argv[1:] if not a.startswith("--") and a != out] or DEFAULT
    rows = []
    missing = 0
    for n in names:
        path = "tests/%s.gd" % n if not n.endswith(".gd") else n
        if not os.path.isfile(os.path.join(ROOT, path)):
            missing += 1
            rows.append({"script": path, "exit": "missing", "errors": [], "tail": []})
            print("%-34s missing: no such script" % path)
            continue
        try:
            r = subprocess.run([godot, "--headless", "--path", ROOT, "-s", path], capture_output=True, text=True, timeout=180)
            text = r.stdout + r.stderr
            code = r.returncode
        except subprocess.TimeoutExpired as e:
            text = (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
            code = "timeout"
        errs = [ln.strip() for ln in text.splitlines() if re.search(r"SCRIPT ERROR|Parse Error|Invalid call|Nonexistent function|Invalid access", ln)]
        tail = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith(("WARNING", "   at:", "     at:"))][-3:]
        rows.append({"script": path, "exit": code, "errors": errs[:4], "tail": tail})
        print("%-34s exit=%s errors=%d %s" % (path, code, len(errs), (errs[:1] or tail[-1:])))
    if out:
        json.dump(rows, open(out, "w"), indent=1)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
