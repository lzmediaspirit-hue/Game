#!/usr/bin/env python3
"""Audit 45: player-facing string keys (data/strings/en.json) that nothing asks for (read-only).

Usage: python3 tools/dev/audit/strings_refs.py [--json OUT]

A key is asked for when it is a string literal in scripts/ (Tx.t("hud.new"), ContentDB.text(...)), a string in
data/**/*.json (rows name their text keys), or when a composed form could build it: a literal ending in "." or "_"
that prefixes it ("hud.caption." + id, "realm." + key, "%s_%d" formats are matched by their literal prefix). Keys
under a prefix only composed code can reach are reported apart (medium confidence), keys no prefix covers as
unasked (high confidence).
"""
import glob
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def main():
    out = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    en = json.load(open(os.path.join(ROOT, "data", "strings", "en.json"), encoding="utf-8")).get("strings", {})
    lits = Counter()
    prefixes = set()
    for f in glob.glob(os.path.join(ROOT, "scripts", "**", "*.gd"), recursive=True) + \
            glob.glob(os.path.join(ROOT, "tests", "*.gd")):
        text = open(f, encoding="utf-8").read()
        for m in re.finditer(r'"([^"\n]*)"', text):
            s = m.group(1)
            lits[s] += 1
            base = s.split("%")[0]
            if "%" in s and len(base) >= 3:
                prefixes.add(base)
            elif s.endswith((".", "_")) and len(s) >= 3:
                prefixes.add(s)
    for f in glob.glob(os.path.join(ROOT, "data", "**", "*.json"), recursive=True):
        if f.endswith(os.path.join("strings", "en.json")):
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        st = [d]
        while st:
            x = st.pop()
            if isinstance(x, dict):
                for k, v in x.items():
                    lits[k] += 1
                    st.append(v)
            elif isinstance(x, list):
                st.extend(x)
            elif isinstance(x, str):
                lits[x] += 1
    direct, composed, none = [], [], []
    for k in en:
        if lits[k]:
            direct.append(k)
        elif k.endswith("_one") and (lits[k[:-4]] or any(k[:-4].startswith(p) for p in prefixes)):
            composed.append(k)   # Tx.plural(key, n) asks for key + "_one" when n is 1
        elif any(k.startswith(p) for p in prefixes):
            composed.append(k)
        else:
            none.append(k)
    by_ns = Counter(k.split(".")[0] for k in none)
    result = {"keys": len(en), "direct": len(direct), "composed_only": len(composed), "unasked": len(none),
              "unasked_by_namespace": dict(by_ns.most_common()), "unasked_sample": none[:80]}
    if out:
        json.dump(result, open(out, "w"), indent=1)
    print(json.dumps({k: v for k, v in result.items() if k != "unasked_sample"}, indent=1))
    print(none[:60])


if __name__ == "__main__":
    main()
