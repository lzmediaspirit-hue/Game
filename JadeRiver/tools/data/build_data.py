"""Build every data/*.json file from the authoring modules (tools/data/README.md). Run from JadeRiver/:

    python3 tools/data/build_data.py [--write | --check] [--only NAME[,NAME]] [MODULE ...]

Every module of MODULES runs its `build()`, in this order (a later one reads what an earlier one wrote), or only the
MODULEs named. A full build writes the item and monster wikis after (tools/dev/wiki.py). The top-down layouts are their
own run: python3 tools/data/topdown_rooms.py.
"""
import importlib
import os
import runpy
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

MODULES = ["realms", "stats", "combat_feel", "sound", "legends", "posts", "items", "gear", "herbs", "techniques", "enemies", "world", "story", "economy", "crafts", "paths", "relations", "living_world", "moments", "scenes", "contract", "places", "tutorials", "topdown_life", "cues"]


def main(argv=None):
    ap = common.parser("build_data", __doc__)
    ap.add_argument("modules", nargs="*", metavar="MODULE", help="only these modules (they still run in MODULES' order)")
    args = ap.parse_args(argv)
    unknown = [m for m in args.modules if m not in MODULES]
    if unknown:
        ap.error("no module %s (MODULES: %s)" % (", ".join(unknown), ", ".join(MODULES)))
    common.begin(args.check, args.only)
    for name in MODULES:
        if args.modules and name not in args.modules:
            continue
        try:
            importlib.import_module(name).build()
        except SystemExit as e:
            if isinstance(e.code, int) or e.code is None:
                raise
            print(e.code, file=sys.stderr)
            return 1
        common.settle()
        if not args.check:
            print("built", name)
    if not (args.modules or args.only or args.check):   # P7a: the item and monster wikis follow a full build
        runpy.run_path(os.path.join(os.path.dirname(__file__), "..", "dev", "wiki.py"), run_name="__main__")
    return common.finish("build_data")


if __name__ == "__main__":
    sys.exit(main())
