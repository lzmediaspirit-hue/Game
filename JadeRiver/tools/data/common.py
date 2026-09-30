"""Shared helpers for the Jade River data builders (tools/data/README.md).

The game reads only the JSON files in data/. These builders are an authoring aid: they keep formula-driven tables
(realm ladder, equipment bands, rooms) consistent. Run `python3 tools/data/build_data.py` from the JadeRiver folder.

- The way out: every generated file leaves by `emit` (`write` and `entries` for a table, `clear` for a folder whose
  every file a build makes). The run decides what that means: written (only when it changed), or with --check compared
  with the file on disk. `run_cli` is the command line every generator module shares.
- The way in: `read` and `rows`, a table of data/ as the builders read it back.
- The constructors the tables share: requirements (`realm`, `qdone`, `flag`, ...), `c` for a gate's condition, `titled`.
"""
import argparse
import importlib
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = os.path.join(ROOT, "data")
# Tables the game never reads, only the checks and the tools (balance_sim's pacing table, the legendary chains' record,
# the art bible's review room): out of data/, which ContentDB loads whole and the export ships (audit 45).
TESTS_DATA = os.path.join(ROOT, "tests", "data")
SCHEMA_VERSION = 1


# -------------------------------------------------------------------- the run: what emit() does with a file
class Run:
    """What this run does with the files the builders make. `run_cli` sets it; a build called from Python without it
    writes, as it always did. `check`: compare each file with the one on disk instead of writing it. `only`: the outputs
    the run touches (a file's name without .json, or its path under data/ or JadeRiver/), all when empty."""

    def __init__(self, check=False, only=()):
        self.check = check
        self.only = {o.strip() for part in only for o in part.split(",") if o.strip()}
        self.made = set()     # every output the builds made, touched or not
        self.touched = 0      # outputs the run compared or wrote
        self.stale = []       # --check: outputs whose file is missing or differs, or a file no build makes any more
        self.written = []     # --write: outputs whose file changed
        self.removed = []     # --write: files of a clear() folder no build makes any more
        self.owned = []       # (folder, suffix): folders whose every such file a build makes (clear)


RUN = Run()


def rel(path):
    """A path as the messages give it: from JadeRiver/."""
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def selected(path):
    """Does the run touch this output (--only)?"""
    if not RUN.only:
        return True
    r = rel(path)
    names = {r, os.path.splitext(r)[0], os.path.basename(r), os.path.splitext(os.path.basename(r))[0]}
    if r.startswith("data/"):
        names |= {r[5:], os.path.splitext(r[5:])[0]}
    return bool(names & RUN.only)


def emit(path, text):
    """The one way a generated file leaves: `text` (the file's whole content) written to `path` when it differs from
    the file there, or with --check compared with it (a difference, or no file, is stale). Returns the path."""
    path = os.path.abspath(path)
    RUN.made.add(path)
    if not selected(path):
        return path
    RUN.touched += 1
    have = None
    if os.path.exists(path):
        with open(path, encoding="utf-8", newline="") as f:
            have = f.read()
    if have == text:
        return path
    if RUN.check:
        RUN.stale.append(rel(path))
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    RUN.written.append(rel(path))
    return path


def write(name, payload, folder=DATA):
    """A table as the game reads it: `schema_version` first, one space of indent, the text as it is (UTF-8)."""
    body = dict(payload)
    body.setdefault("schema_version", SCHEMA_VERSION)
    ordered = {"schema_version": body.pop("schema_version")}
    ordered.update(body)
    return emit(os.path.join(folder, name), json.dumps(ordered, indent=1, ensure_ascii=False) + "\n")


def entries(name, rows, folder=DATA, **extra):
    """A list table: its rows under `entries` (each with its own `id`, none twice), its constants beside them."""
    if not name.endswith(".json"):
        name += ".json"
    ids = set()
    for r in rows:
        assert "id" in r, (name, r)
        assert r["id"] not in ids, (name, "duplicate", r["id"])
        ids.add(r["id"])
    payload = {"entries": rows}
    payload.update(extra)
    return write(name, payload, folder)


def clear(folder, suffix=".json"):
    """A build makes every file of `folder` that ends in `suffix` ("" for every file): one it no longer makes (a room or
    a dialogue tree renamed away) goes when the build is done (`settle`), and --check calls it stale."""
    RUN.owned.append((os.path.abspath(folder), suffix))


def settle():
    """After a build: the files of its `clear` folders it did not make are removed (--write) or stale (--check). With
    --only nothing is removed: the run did not make the rest."""
    owned, RUN.owned = RUN.owned, []
    if RUN.only:
        return
    for folder, suffix in owned:
        if not os.path.isdir(folder):
            continue
        for f in sorted(os.listdir(folder)):
            path = os.path.join(folder, f)
            if not f.endswith(suffix) or path in RUN.made or not os.path.isfile(path):
                continue
            if RUN.check:
                RUN.stale.append(rel(path) + " (no build makes it)")
            else:
                os.remove(path)
                RUN.removed.append(rel(path))


def read(name, folder=DATA):
    """A table of data/ (or of `folder`) as a builder reads it back: `name` with or without .json."""
    if not name.endswith(".json"):
        name += ".json"
    with open(os.path.join(folder, name), encoding="utf-8") as f:
        return json.load(f)


def rows(name, folder=DATA):
    """A list table's rows."""
    return read(name, folder)["entries"]


# -------------------------------------------------------------------- the command line every generator shares
def fail(what, errs):
    """A build's own check failed: its problems, one a line (run_cli prints them and exits 1)."""
    if errs:
        raise SystemExit("%s:\n  %s" % (what, "\n  ".join(errs)))


def parser(prog, doc=None):
    ap = argparse.ArgumentParser(prog=prog, description=(doc or "").strip().split("\n\n")[0] or None,
                                 epilog="Exit code: 0 written or current, 1 a check failed or a file is stale, 2 a usage "
                                        "error. More: tools/data/README.md.")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="build and write the files that changed (the default)")
    mode.add_argument("--check", action="store_true", help="build in memory; fail unless every file on disk is current")
    ap.add_argument("--only", action="append", default=[], metavar="NAME[,NAME]",
                    help="touch only these outputs: a file's name without .json, or its path under data/ (the build's "
                         "own checks still run whole)")
    return ap


def begin(check=False, only=()):
    """Start a run (run_cli and build_data.py do): RUN afresh, in place, so a module holding it sees the same run."""
    RUN.__init__(check, only)
    return RUN


def finish(name, note=None):
    """End a run: a line that says what it did, and its exit code."""
    settle()
    if RUN.only and not RUN.touched:
        print("%s: --only %s names none of its outputs" % (name, ",".join(sorted(RUN.only))), file=sys.stderr)
        return 1
    if RUN.check:
        if RUN.stale:
            print("%s: not current (run python3 tools/data/%s.py): %s" % (name, name, ", ".join(RUN.stale)), file=sys.stderr)
            return 1
        print("%s: %d file%s current%s" % (name, RUN.touched, "" if RUN.touched == 1 else "s", "; " + note if note else ""))
        return 0
    print("%s: %d of %d file%s written%s%s" % (name, len(RUN.written), RUN.touched, "" if RUN.touched == 1 else "s",
                                               ", %d removed (%s)" % (len(RUN.removed), ", ".join(RUN.removed)) if RUN.removed else "",
                                               "; " + note if note else ""))
    return 0


def run_cli(build, argv=None, name=None, doc=None):
    """The command line of a generator module (tools/data/README.md):

        python3 tools/data/<module>.py [--write | --check] [--only NAME[,NAME]]

    `build()` makes the module's files through `emit` (`write`, `entries`) and runs its own checks, raising
    SystemExit(message) (or `fail`) when one fails; it may return a short note for the last line. Returns the exit code:
    0 written or current, 1 a check failed or a file is stale (2, a usage error, argparse's own)."""
    main = sys.modules.get("__main__")
    name = name or os.path.splitext(os.path.basename(getattr(main, "__file__", "") or "build"))[0]
    args = parser(name, doc if doc is not None else getattr(main, "__doc__", None)).parse_args(argv)
    begin(args.check, args.only)
    if getattr(build, "__module__", None) == "__main__":
        # Run as a script the module is __main__, and a module it imports that imports it back gets a second copy (the
        # rooms lantern.py adds through `import world` would miss world.py's own): build with the copy they all share.
        build = getattr(importlib.import_module(name), build.__name__)
    try:
        note = build()
    except SystemExit as e:
        if isinstance(e.code, int) or e.code is None:
            raise
        print(e.code, file=sys.stderr)
        return 1
    return finish(name, note if isinstance(note, str) else None)


# -------------------------------------------------------------------- the constructors the tables share
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


# Requirement constructors (the conditions quests, unlocks, rooms and shops are gated by).
def realm(r):
    return {"kind": "realm_at_least", "realm": r}


def qdone(q):
    return {"kind": "quest_done", "quest": q}


def qactive(q):
    return {"kind": "quest_active", "quest": q}


def qaccepted(q):
    """Taken on, under way or done."""
    return {"kind": "quest_accepted", "quest": q}


def flag(f):
    return {"kind": "flag_set", "flag": f}


def noflag(f):
    return {"kind": "flag_not_set", "flag": f}


def unlocked(s):
    return {"kind": "unlock", "system": s}


def sect(s):
    return {"kind": "training_sect", "sect": s}


def all_of(*conds):
    return {"all": list(conds)}


def any_of(*conds):
    return {"any": list(conds)}


def titled(snake):
    small = {"of", "the", "and", "in", "to", "a", "on"}
    words = snake.split("_")
    return " ".join(w if (i and w in small) else w.capitalize() for i, w in enumerate(words))
