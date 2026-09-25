"""Build every data/*.json file from the authoring modules. Run from JadeRiver/: python3 tools/data/build_data.py"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
MODULES = ["realms", "stats", "items", "techniques", "enemies", "world", "story", "economy", "crafts"]

if __name__ == "__main__":
    only = sys.argv[1:]
    for name in MODULES:
        if only and name not in only:
            continue
        mod = importlib.import_module(name)
        for fn in ("build", "build_items", "build_artifacts"):
            if hasattr(mod, fn):
                getattr(mod, fn)()
        print("built", name)
