"""Dev tool (P3 mockups): render the HTML mockups in docs/mockups/src/ to 1280 x 720 PNGs, and compose the
figures they place in the world.

    python3 tools/dev/render_mockups.py                      # every src/*.html -> docs/mockups/<name>.png
    python3 tools/dev/render_mockups.py 01_hud_fight 03_hub  # only these (names with or without .html)
    python3 tools/dev/render_mockups.py --list               # the mockups and whether each PNG is older than its source

    # A figure: an avatar frame composed from data/parts.json layer sheets exactly as scripts/avatar.gd draws it
    python3 tools/dev/render_mockups.py figure OUT.png --outfit '{"hair": "topknot", "shirt": "scholar", ...}' \
        [--action idle] [--frame 0] [--facing 1] [--tint "#d4b2a4"]
    python3 tools/dev/render_mockups.py figure OUT.png --enemy general_kharn [--action thrust_1 --frame 3 --facing -1]
    python3 tools/dev/render_mockups.py figure OUT.png --npc peddler_ning     (or --companion lan_yue)
    # A creature frame from art/creatures (data/creature_art.json), re-canvassed the same way
    python3 tools/dev/render_mockups.py creature OUT.png reed_otter [--action idle] [--frame 0] [--facing 1]

Figures and creatures come out as 384 x 384 PNGs with the feet at (192, 254), so the kit's .k-fig class places them
by their feet. OUT paths are relative to the working directory; put them in docs/mockups/assets/.

Rendering uses headless Chromium (the CHROME environment variable overrides the binary). Every PNG is checked to be
exactly 1280 x 720. No network: the pages link the kit and the art by relative path.
"""
import glob
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MOCK = os.path.join(ROOT, "docs", "mockups")
SRC = os.path.join(MOCK, "src")
CHROME = os.environ.get("CHROME", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
# Full Chromium's new headless mode keeps 87 px of the window for its (invisible) toolbar, so a 1280 x 720 window
# gives a 1280 x 633 page. The headless shell next to it has no toolbar; it is used when present, and otherwise the
# window is made taller by the toolbar and the screenshot cropped back to 1280 x 720.
SHELL = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"
TOOLBAR = 87
W, H = 1280, 720
CANVAS = 384                 # figure canvas; a 256 cell sits at (64, 64), a 384 cell at (0, 0)
FEET = (192, 254)            # the avatar origin inside the canvas (avatar.gd draws a 256 cell at (-128, -190))
CATEGORIES = ["body", "cape", "shoes", "pants", "shirt", "hair", "hat", "weapon"]


# ------------------------------------------------------------------ rendering
def render(name):
    html = os.path.join(SRC, name if name.endswith(".html") else name + ".html")
    if not os.path.exists(html):
        sys.exit("no such mockup: %s" % html)
    out = os.path.join(MOCK, os.path.basename(html)[:-5] + ".png")
    shell = "CHROME" not in os.environ and os.path.exists(SHELL)
    binary = SHELL if shell else CHROME
    height = H if shell else H + TOOLBAR
    if os.path.exists(out):
        os.remove(out)
    with tempfile.TemporaryDirectory() as prof:
        cmd = [binary, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
               "--force-device-scale-factor=1", "--user-data-dir=" + prof, "--virtual-time-budget=3000",
               "--window-size=%d,%d" % (W, height), "--screenshot=" + out, "file://" + html]
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
    if not os.path.exists(out):
        sys.exit("render failed for %s:\n%s" % (name, r.stderr[-2000:]))
    from PIL import Image
    im = Image.open(out)
    if im.size != (W, H):
        im.crop((0, 0, W, H)).save(out)
    size = Image.open(out).size
    if size != (W, H):
        sys.exit("%s is %dx%d, not %dx%d" % (out, size[0], size[1], W, H))
    print("%s  %dx%d" % (os.path.relpath(out, ROOT), size[0], size[1]))


# Mockups kept as the record of a decision and never re-rendered: 00b previewed the option B button faces, whose PNGs
# went once option C was chosen (roadmap §6 decision 10).
RECORDS = {"00b_button_faces"}


def all_names():
    return sorted(n for n in (os.path.basename(p)[:-5] for p in glob.glob(os.path.join(SRC, "*.html"))) if n not in RECORDS)


def list_mockups():
    for n in all_names():
        png = os.path.join(MOCK, n + ".png")
        html = os.path.join(SRC, n + ".html")
        state = "missing" if not os.path.exists(png) else ("stale" if os.path.getmtime(png) < os.path.getmtime(html) else "ok")
        print("%-32s %s" % (n, state))


# ------------------------------------------------------------------ figures (scripts/avatar.gd, compose.py)
def _parts():
    return json.load(open(os.path.join(ROOT, "data", "parts.json")))


def _tex(path, cache={}):
    from PIL import Image
    # parts.json names some sheets by an old folder; the baked sheets all live in art/ (compose.py does the same)
    p = os.path.join(ROOT, "art", path[len("res://art/"):]) if path.startswith("res://art/") else os.path.join(ROOT, "art", os.path.basename(path))
    if p not in cache:
        cache[p] = Image.open(p).convert("RGBA")
    return cache[p]


def _sheet_index(parts, category, outfit, count):
    index = 0
    if category == "hair":
        index = int(outfit.get("hair_color", 0))
    elif category in ("shirt", "pants"):
        order = parts["_dyes"]["order"]
        d = outfit.get(category + "_dye", "none")
        index = max(0, order.index(d) if d in order else -1)
    return max(0, min(index, count - 1))


def compose(outfit, action="idle", frame=0, facing=1, tint=None):
    """One avatar frame on a transparent 384 x 384 canvas, feet at FEET; layers sorted by z as avatar.gd does."""
    from PIL import Image
    parts = _parts()
    entries = []
    for category in CATEGORIES:
        item = parts[category].get(outfit.get(category, "none"), {})
        for layer in item.get("layers", []):
            anim = layer["animations"].get(action)
            if anim is None:
                sys.exit("missing pose: %s / %s" % (category, action))
            if not anim or anim.get("hidden"):
                continue
            sheets = anim["sheets"]
            entries.append((int(anim.get("z", layer["z"])), int(anim.get("cell", 256)),
                            _tex(sheets[_sheet_index(parts, category, outfit, len(sheets))])))
    entries.sort(key=lambda e: e[0])
    img = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    row = 0 if facing < 0 else 1
    for _, cell, tex in entries:
        frames = max(1, tex.width // cell)
        f = frame % frames
        src = tex.crop((f * cell, row * cell, (f + 1) * cell, (row + 1) * cell))
        off = (CANVAS - cell) // 2
        img.alpha_composite(src, (off, off))
    if tint:
        img = _tint(img, tint)
    return img


def _tint(img, hex_colour):
    """Multiply RGB by a colour, as a CanvasItem modulate does."""
    from PIL import Image
    h = hex_colour.lstrip("#")
    m = tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    r, g, b, a = img.split()
    r = r.point(lambda v: int(v * m[0]))
    g = g.point(lambda v: int(v * m[1]))
    b = b.point(lambda v: int(v * m[2]))
    return Image.merge("RGBA", (r, g, b, a))


def _entry(file, id_):
    data = json.load(open(os.path.join(ROOT, "data", file)))
    rows = data.get("entries", data)
    for e in rows if isinstance(rows, list) else rows.values():
        if isinstance(e, dict) and e.get("id") == id_:
            return e
    sys.exit("no %s in data/%s" % (id_, file))


def creature(cid, action="idle", frame=0, facing=1, tint=None):
    """One creature frame re-canvassed to 384 x 384 with its anchor on FEET (creature_sprite.gd draws at -anchor)."""
    from PIL import Image
    art = json.load(open(os.path.join(ROOT, "data", "creature_art.json")))
    e = art[cid]
    a = e["actions"].get(action, e["actions"]["idle"])
    cell = int(e["cell"])
    tex = _tex(e["file"])
    f = frame % max(1, int(a.get("frames", 1)))
    src = tex.crop((f * cell, int(a["row"]) * cell, (f + 1) * cell, (int(a["row"]) + 1) * cell))
    if facing < 0:
        src = src.transpose(Image.FLIP_LEFT_RIGHT)
        ax = cell - int(e["anchor"][0])
    else:
        ax = int(e["anchor"][0])
    img = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    img.alpha_composite(src, (FEET[0] - ax, FEET[1] - int(e["anchor"][1])))
    return _tint(img, tint) if tint else img


def _opt(args, name, default=None):
    if name in args:
        i = args.index(name)
        v = args[i + 1]
        del args[i:i + 2]
        return v
    return default


def figure_cmd(args):
    out = args.pop(0)
    action = _opt(args, "--action", "idle")
    frame = int(_opt(args, "--frame", "0"))
    facing = int(_opt(args, "--facing", "1"))
    tint = _opt(args, "--tint")
    enemy = _opt(args, "--enemy")
    npc = _opt(args, "--npc")
    companion = _opt(args, "--companion")
    raw = _opt(args, "--outfit")
    if companion:
        outfit = dict(_entry("companions.json", companion)["outfit"])
    elif enemy:
        outfit = dict(_entry("enemies.json", enemy)["art"]["avatar"])
        tint = tint or outfit.get("tint")
    elif npc:
        outfit = dict(_entry("npcs.json", npc)["outfit"])
    else:
        outfit = json.loads(raw)
    compose(outfit, action, frame, facing, tint).save(out)
    print(out)


def creature_cmd(args):
    out = args.pop(0)
    cid = args.pop(0)
    action = _opt(args, "--action", "idle")
    frame = int(_opt(args, "--frame", "0"))
    facing = int(_opt(args, "--facing", "1"))
    tint = _opt(args, "--tint")
    creature(cid, action, frame, facing, tint).save(out)
    print(out)


def main():
    args = sys.argv[1:]
    if args and args[0] == "figure":
        return figure_cmd(args[1:])
    if args and args[0] == "creature":
        return creature_cmd(args[1:])
    if args and args[0] == "--list":
        return list_mockups()
    for n in (args or all_names()):
        render(n)


if __name__ == "__main__":
    main()
