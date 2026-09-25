"""Dev tool (Part 7 · Strings gate): move player-facing text out of GDScript into
tools/data/ui_strings.json, replacing each literal with Tx.t("key").

    python3 tools/dev/extract_strings.py --dry-run   # list what would move
    python3 tools/dev/extract_strings.py             # rewrite scripts, update ui_strings.json

Only the player-facing scripts in SCOPE are touched. A literal moves when it reads like
text (words with a space, or a capitalised word) and is not an id, a path, a technical
token, a dictionary key, a comparison operand, a match arm, part of a const or a
function signature, or inside print/assert. Lines it cannot rewrite (consts) are
reported for hand conversion. tests/contract_tests keeps new literals out afterwards.
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "tools", "data", "ui_strings.json")

SCOPE = [
    ("scripts/ui/pages", "ui"), ("scripts/ui/page.gd", "ui.page"), ("scripts/hud.gd", "hud"), ("scripts/shell", "shell"),
    ("scripts/main.gd", "main"), ("scripts/world.gd", "world_view"), ("scripts/player.gd", "player"),
    ("scripts/presentation/enemy_view.gd", "view"), ("scripts/presentation/loot_view.gd", "view"),
    ("scripts/presentation/portal_view.gd", "view"), ("scripts/presentation/npc_view.gd", "view"),
    ("scripts/simulation/authority", "sim"), ("scripts/core/requirement_rules.gd", "req"), ("scripts/core/unlock_service.gd", "unlock_text"),
]
TECH = {"UI", "SFX", "Music", "Ambience", "Master", "MobileHUD", "Room", "HUD"}
LIT = re.compile(r'(?<![&^\w])"((?:[^"\\]|\\.)*)"')


def files():
    for path, prefix in SCOPE:
        full = os.path.join(ROOT, path)
        if os.path.isdir(full):
            for f in sorted(os.listdir(full)):
                if f.endswith(".gd"):
                    yield os.path.join(full, f), prefix
        else:
            yield full, prefix


def key_prefix(path, prefix):
    base = os.path.basename(path)[:-3]
    if prefix == "ui":
        return "ui." + base.replace("_page", "")
    if prefix == "sim":
        return "sim." + base.replace("_authority", "")
    return prefix


def unescape(s):
    out, i = [], 0
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s):
            nxt = s[i + 1]
            out.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\", "'": "'"}.get(nxt, "\\" + nxt))
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def is_text(s):
    raw = unescape(s)
    if raw.strip() in TECH or not raw.strip():
        return False
    if raw.startswith(("res:", "user:", "--", "#")) or ("/" in raw and " " not in raw):
        return False
    if re.fullmatch(r"[a-z0-9_.:%\-]+", raw):
        return False
    if not re.search(r"[A-Za-z]{2,}", raw):
        return False
    return " " in raw.strip() or bool(re.match(r"[A-Z]", raw.strip()))


def skip_line(line):
    st = line.strip()
    if st.startswith("#") or re.match(r"\s*(static\s+)?func\s", line):
        return "func"
    if re.match(r"\s*const\s", line):
        return "const"
    if re.search(r"\b(print|prints|printerr|push_warning|push_error|assert)\(", line):
        return "debug"
    return ""


def slug(text, taken, prefix, used_for):
    words = re.findall(r"[a-z0-9]+", unescape(text).lower())
    words = [w for w in words if w not in ("d", "s", "f")][:5]
    base = "_".join(words) or "fmt"
    k = "%s.%s" % (prefix, base)
    n = 2
    while k in taken and taken[k] != unescape(text):
        k = "%s.%s_%d" % (prefix, base, n)
        n += 1
    return k


def main():
    dry = "--dry-run" in sys.argv
    table = json.load(open(OUT)) if os.path.exists(OUT) else {}
    reverse = {}
    for k, v in table.items():
        reverse.setdefault(v, []).append(k)
    moved, consts = 0, []
    for path, prefix in files():
        kp = key_prefix(path, prefix)
        src = open(path).read().split("\n")
        changed = False
        const_depth = 0   # inside a multi-line const literal
        for i, line in enumerate(src):
            why = skip_line(line)
            code = LIT.sub('""', line)
            if why == "const" or const_depth > 0:
                if const_depth > 0: why = "const"
                const_depth += code.count("{") + code.count("[") + code.count("(") - code.count("}") - code.count("]") - code.count(")")
                const_depth = max(0, const_depth)
            hits = []
            in_lists = [(x.start(), x.end()) for x in re.finditer(r"\bin\s*\[[^\]]*\]", line)]
            for m in LIT.finditer(line):
                if any(a <= m.start() < b for a, b in in_lists):
                    continue   # membership tests compare ids, not text
                s = m.group(1)
                if not is_text(s):
                    continue
                after = line[m.end():].lstrip()
                before = line[:m.start()].rstrip()
                if after.startswith(":") and not after.startswith(":="):
                    continue   # dictionary key or match arm
                if before.endswith(("==", "!=")) or after.startswith(("==", "!=")):
                    continue
                if before.endswith(" in") or re.search(r"\bin\s*\[$", before):
                    continue
                if why == "const":
                    consts.append("%s:%d %s" % (os.path.relpath(path, ROOT), i + 1, unescape(s)))
                    continue
                if why:
                    continue
                hits.append(m)
            if not hits:
                continue
            new = line
            for m in reversed(hits):
                text = unescape(m.group(1))
                existing = [k for k in reverse.get(text, []) if k.startswith(kp + ".")]
                k = existing[0] if existing else slug(m.group(1), table, kp, text)
                table[k] = text
                reverse.setdefault(text, []).append(k)
                new = new[:m.start()] + 'Tx.t("%s")' % k + new[m.end():]
                moved += 1
                if dry:
                    print("%s:%d  %s  =  %s" % (os.path.relpath(path, ROOT), i + 1, k, json.dumps(text, ensure_ascii=False)))
            src[i] = new
            changed = True
        if changed and not dry:
            open(path, "w").write("\n".join(src))
    if not dry:
        json.dump(dict(sorted(table.items())), open(OUT, "w"), indent=1, ensure_ascii=False)
        open(OUT, "a").write("\n")
    print("moved %d literals, %d keys; %d const literals to convert by hand" % (moved, len(table), len(consts)))
    for c in consts:
        print("  const:", c)


if __name__ == "__main__":
    main()
