"""Dev tool (P4 · docs/ui_style_guide.md): measure the UI against the style guide. Read-only: it prints and writes nothing.

    python3 tools/dev/ui_style_audit.py                 # every section
    python3 tools/dev/ui_style_audit.py contrast fills  # named sections only
    python3 tools/dev/ui_style_audit.py --root DIR      # measure another copy of JadeRiver/ (an export of a branch)

Sections:
    tokens     the UiKit colour constants (scripts/ui/ui_kit.gd) and the grade and quality colours (data/grades.json)
    fills      the HD kit's panel fills under text, sampled from art/ui/hd/*.png inside each asset's nine-slice centre
    contrast   the WCAG 2 contrast ratio of every text colour on the page fills and of each label on its own fill, and
               lighter variants of the failing colours (same hue and saturation, lightness raised until 4.5:1 on the
               lightest page fill)
    literals   hex colour literals in scripts/ui/pages/ and scripts/hud.gd, each with the nearest token
    sizes      text asked for under UiKit.MIN_SIZE by a literal size
    windows    every page's frame_rect against the standard window sizes
    icons      pixel icons drawn at a size off the allowed set (the file 1:1, a native re-render, or twice the file)
    rows       list() row pitches off the 8 px grid
    plurals    strings that print a count before a plural noun and have no "_one" form
    durations  the duration formats in use

The pass marks are the guide's: 4.5:1 for text under 20 px, 3:1 for text of 20 px and more. A fill that is not opaque
is composited over INK (the page dim over the world is close to it). Text drawn with UiKit.draw_outlined carries a 3-4 px
ink outline and is measured against INK, not against the fill.
"""
from __future__ import annotations

import colorsys
import glob
import json
import os
import re
import sys

sys.dont_write_bytecode = True  # keep the repo free of __pycache__

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = UI_KIT = HUD = ""
PAGES: list = []


def set_root(path: str) -> None:
    global ROOT, UI_KIT, PAGES, HUD
    ROOT = os.path.normpath(path)
    UI_KIT = os.path.join(ROOT, "scripts", "ui", "ui_kit.gd")
    PAGES = sorted(glob.glob(os.path.join(ROOT, "scripts", "ui", "pages", "*.gd")))
    HUD = os.path.join(ROOT, "scripts", "hud.gd")


set_root(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

BODY, LARGE = 4.5, 3.0
GRID = 8

# Colours drawn as text that are not UiKit tokens (the hex literals of I5), with what they colour. Empty since the P4
# apply step 1 made every one a token (RED_TEXT, WARNING, SKY, HUD_LABEL, PAPER_INK...); an old export measured with
# --root still has them as literals, and the literals section lists them.
LITERAL_TEXT: dict = {}

# The fills any text colour is drawn on (pages, cards, rows, slots, toasts, pills): a text colour must pass on the
# lightest of these. (`tooltip` is in the kit but drawn nowhere; the realm badge carries one label, below.)
PAGE_FILLS = ["major_window", "minor_panel", "slot", "toast", "currency_pill"]

# Fills that carry one label colour each, at the size it is drawn (px after UiKit.size_for; Cormorant is 1.2x). A fill
# ending "@ink" carries words drawn with the 2 px ink outline (UiKit.draw_inked, decision 10 option C): they are
# measured on INK, and the face alone is printed beside them.
LABEL_PAIRS = [
    ("PALE_GOLD", "title_plaque@ink", 41, "page title, Page._draw (layout 34), inked"),
    ("PALE_GOLD", "title_plaque@ink", 31, "dialogue speaker, dialogue_page.gd (layout 26), inked"),
    ("PALE_GOLD", "tab:selected", 20, "selected tab, Page._draw_tabs"),
    ("PAPER", "tab", 20, "tab, Page._draw_tabs"),
    ("HOLLOW", "tab:disabled", 20, "locked tab, Page._draw_tabs (disabled)"),
    ("PALE_GOLD", "button_primary@ink", 22, "primary label, Page.btn (steps down to 14), inked"),
    ("PALE_GOLD", "button_primary@ink", 14, "primary label stepped down to MIN_SIZE, inked"),
    ("PALE_GOLD", "button_primary:pressed@ink", 22, "primary label, pressed, inked"),
    ("HOLLOW", "button_primary:disabled@ink", 22, "disabled primary label, Page.btn (disabled), inked"),
    ("PAPER", "button_secondary", 22, "secondary label, Page.btn"),
    ("PAPER", "button_secondary", 14, "secondary label stepped down to MIN_SIZE"),
    ("PAPER", "button_secondary:pressed", 22, "secondary label, pressed"),
    ("HOLLOW", "button_secondary:disabled", 22, "disabled secondary label (disabled)"),
    ("PALE_GOLD", "minimap_frame:header", 14, "room name, hud.gd _draw_minimap"),
    ("PALE_GOLD", "realm_badge", 38, "level on the Cultivation badge (layout 32, Cormorant)"),
    ("PALE_GOLD", "currency_pill", 18, "silver, Page.currency_pill and the HUD pill"),
    ("BRIGHT_JADE", "currency_pill", 18, "spirit stones, the HUD pill"),
    ("PAPER_INK", "dialogue_box", 20, "dialogue words, dialogue_page.gd"),
    ("HOLLOW", "minor_panel:disabled", 20, "a disabled row's text (disabled)"),
    ("PAPER", "minor_panel:disabled", 20, "a disabled row's name"),
]


# ------------------------------------------------------------------ colour maths
def hex_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_hex(c) -> str:
    return "#%02x%02x%02x" % tuple(int(round(v)) for v in c[:3])


def lum(c) -> float:
    def ch(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = c[:3]
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def ratio(a, b) -> float:
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def lighten_to(c, bg, target: float) -> tuple:
    """`c` with its HLS lightness raised (hue and saturation kept) until it reaches `target` on `bg`."""
    h, l, s = colorsys.rgb_to_hls(*[v / 255.0 for v in c])
    while ratio(c, bg) < target and l < 1.0:
        l = min(1.0, l + 0.002)
        c = tuple(round(v * 255) for v in colorsys.hls_to_rgb(h, l, s))
    return c


def grade(r: float) -> str:
    return "pass" if r >= BODY else ("20px+" if r >= LARGE else "FAIL")


# ------------------------------------------------------------------ sources
def read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def rel(path: str) -> str:
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def tokens() -> dict:
    """UiKit colour constants: name -> (hex, line)."""
    out = {}
    for i, ln in enumerate(read(UI_KIT).splitlines(), 1):
        m = re.match(r'const ([A-Z_]+) := Color\("([0-9a-fA-F]{6})"\)', ln)
        if m: out[m.group(1)] = (m.group(2).lower(), i)
    return out


def grades() -> dict:
    g = json.loads(read(os.path.join(ROOT, "data", "grades.json")))
    return {"grade": g.get("grade_colors", {}), "quality": g.get("quality_colors", {}), "order": g.get("order", [])}


def ui_kit_plate() -> tuple:
    """UiKit.PLATE as (r, g, b, a): the plate under words over the world."""
    m = re.search(r"const PLATE := Color\(([0-9.]+), ([0-9.]+), ([0-9.]+), ([0-9.]+)\)", read(UI_KIT))
    return tuple(float(v) for v in m.groups()) if m else (0.02, 0.06, 0.075, 0.55)


def ui_kit_int(name: str) -> int:
    m = re.search(r"const %s := (\d+)" % name, read(UI_KIT))
    return int(m.group(1)) if m else 0


# ------------------------------------------------------------------ fills
def sample(asset: str, state: str = "normal") -> dict:
    """The fill under text: the texels inside the nine-slice centre (the middle row where the centre has no height),
    composited over INK. Returns the mean, the lightest (95th luminance percentile) and the darkest (5th)."""
    kit = json.loads(read(os.path.join(ROOT, "data", "ui_assets_hd.json")))
    k = int(kit.get("scale", 3))
    e = kit[asset]
    img = np.asarray(Image.open(os.path.join(ROOT, e[state].replace("res://", ""))).convert("RGBA")).astype(float)
    h, w = img.shape[:2]
    ml, mt, mr, mb = [int(m) * k for m in e["margins"]]
    # The title plaque has no vertical centre (HdStyleBox scales it to its rect's height): its title covers the face
    # from about a fifth to seven tenths of the height.
    y0, y1 = (mt, h - mb) if h - mb > mt else (int(h * 0.2), int(h * 0.7))
    x0, x1 = (ml, w - mr) if w - mr > ml else (w // 2 - 1, w // 2 + 1)
    return _stats(img[y0:y1, x0:x1])


def _stats(px: np.ndarray) -> dict:
    ink = np.array(hex_rgb("071015"), float)
    a = px[..., 3:4] / 255.0
    rgb = (px[..., :3] * a + ink * (1 - a)).reshape(-1, 3)
    ls = np.array([lum(c) for c in rgb[:: max(1, len(rgb) // 4000)]])
    order = np.argsort(ls)
    sub = rgb[:: max(1, len(rgb) // 4000)]
    return {"mean": tuple(rgb.mean(axis=0)), "light": tuple(sub[order[int(len(order) * 0.95)]]),
            "dark": tuple(sub[order[int(len(order) * 0.05)]]), "alpha": float(a.mean())}


def tinted(f: dict, tint, alpha: float, behind) -> dict:
    """A derived state (UiKit.DERIVED_TINT): the normal fill modulated by `tint` at `alpha` over `behind`."""
    t = np.array(tint, float)
    b = np.array(behind, float)
    return {k: tuple(np.array(v) * t * alpha + b * (1 - alpha)) if k != "alpha" else v for k, v in f.items()}


def fills() -> dict:
    out = {}
    for spec in ["major_window", "minor_panel", "slot", "slot:selected", "slot:disabled", "tab", "tab:selected",
                 "button_primary", "button_primary:pressed", "button_primary:disabled", "button_secondary",
                 "button_secondary:pressed", "button_secondary:disabled", "title_plaque", "toast", "tooltip",
                 "currency_pill", "realm_badge", "dialogue_box", "bar_shell"]:
        a, _, s = spec.partition(":")
        out[spec] = sample(a, s or "normal")
    # The minimap's header band (22 px) holds the room name; the nine-slice centre is the map body.
    img = np.asarray(Image.open(os.path.join(ROOT, "art", "ui", "hd", "minimap_frame__normal.png")).convert("RGBA")).astype(float)
    out["minimap_frame:header"] = _stats(img[3 * 4:3 * 20, 3 * 24:-3 * 24])
    out["minimap_frame"] = sample("minimap_frame")
    win = out["major_window"]["mean"]
    out["minor_panel:disabled"] = tinted(out["minor_panel"], (0.5, 0.56, 0.58), 0.8, win)
    out["tab:disabled"] = tinted(out["tab"], (0.5, 0.56, 0.58), 0.8, win)
    return out


# ------------------------------------------------------------------ sections
def sec_tokens(tk, gr):
    print("## Tokens\n")
    print("| Token | Hex | ui_kit.gd line |\n|---|---|---|")
    for n, (h, i) in tk.items(): print("| `%s` | `#%s` | %d |" % (n, h, i))
    print("\nMIN_SIZE %d, DISPLAY_MIN %d, PIXEL_NUMERALS_MIN %d" % (ui_kit_int("MIN_SIZE"), ui_kit_int("DISPLAY_MIN"), ui_kit_int("PIXEL_NUMERALS_MIN")))
    missing = [g for g in gr["order"] if g not in gr["grade"]]
    print("\nGrades with no colour in grades.json (drawn as the #e8e1cf fallback): %s\n" % (", ".join(missing) or "none"))


def sec_fills(fl):
    print("## Fills under text (sampled, over INK)\n")
    print("| Fill | Mean | Lightest (p95) | Darkest (p5) | Alpha |\n|---|---|---|---|---|")
    for k, f in fl.items():
        print("| %s | `%s` | `%s` | `%s` | %.2f |" % (k, rgb_hex(f["mean"]), rgb_hex(f["light"]), rgb_hex(f["dark"]), f["alpha"]))
    print()


def text_colours(tk, gr) -> dict:
    out = {n: h for n, (h, _) in tk.items()}
    for n, (h, _) in LITERAL_TEXT.items(): out[n] = h
    for g, h in gr["grade"].items(): out["grade:" + g] = h.lstrip("#")
    for q, h in gr["quality"].items(): out["quality:" + q] = h.lstrip("#")
    return out


def sec_contrast(tk, gr, fl):
    cols = text_colours(tk, gr)
    ref = max((fl[f]["light"] for f in PAGE_FILLS), key=lum)
    ink = hex_rgb(tk["INK"][0])
    print("## Contrast on the page fills (lightest texel; `pass` 4.5:1, `20px+` 3:1 only, `FAIL` under 3:1)\n")
    print("| Colour | " + " | ".join(PAGE_FILLS) + " | on INK (outlined) |")
    print("|---" * (len(PAGE_FILLS) + 2) + "|")
    for n, h in cols.items():
        c = hex_rgb(h)
        cells = ["%.2f %s" % (ratio(c, fl[f]["light"]), grade(ratio(c, fl[f]["light"]))) for f in PAGE_FILLS]
        print("| %s `#%s` | %s | %.2f |" % (n, h, " | ".join(cells), ratio(c, ink)))
    print("\nThe lightest page fill (the reference for every text colour): `%s`\n" % rgb_hex(ref))
    print("### Labels on their own fills, at the size drawn\n")
    print("| Colour | Fill | Size | Lightest | Mean | Needs | Result | Where |\n|---|---|---|---|---|---|---|---|")
    for n, f, px, where in LABEL_PAIRS:
        c = hex_rgb(cols[n])
        need = LARGE if px >= 20 else BODY
        face = f.replace("@ink", "")
        if f.endswith("@ink"):
            lo = mid = ratio(c, ink)
            where += " (the face alone: %.2f)" % ratio(c, fl[face]["light"])
        else:
            lo, mid = ratio(c, fl[face]["light"]), ratio(c, fl[face]["mean"])
        res = "pass" if lo >= need else ("mean only" if mid >= need else "FAIL")
        print("| %s | %s | %d | %.2f | %.2f | %.1f | %s | %s |" % (n, f, px, lo, mid, need, res, where))
    # The guide proposes the 4.8:1 variant: a margin for anti-aliasing and the Small text size.
    print("\n### Text colours under 4.5:1 on the reference fill, and variants that pass (hue and saturation kept)\n")
    print("| Colour | Now | Ratio | 4.5:1 variant | Ratio | 4.8:1 variant (proposed) | Ratio |\n|---|---|---|---|---|---|---|")
    for n, h in cols.items():
        if n in ("INK", "RIVER_NIGHT", "DEEP_TEAL", "JADE_SHADOW", "PAPER_INK", "BAR_TROUGH"): continue   # fills, and ink for paper
        if n in ("JADE", "BRONZE", "RED", "SOUL", "HP", "BLOOD", "HEART"): continue   # fills only (§1.4 rule 2)
        c = hex_rgb(h)
        r = ratio(c, ref)
        if r >= BODY: continue
        v, v8 = lighten_to(c, ref, BODY), lighten_to(c, ref, 4.8)
        print("| %s | `#%s` | %.2f | `%s` | %.2f | `%s` | %.2f |" % (n, h, r, rgb_hex(v), ratio(v, ref), rgb_hex(v8), ratio(v8, ref)))
    # Translucent plates over the world: the HUD tracker (hud.gd _draw_tracker) and the nameplate (UiKit.draw_nameplate).
    print()
    plate = ui_kit_plate()
    for name, rgba in (("tracker plate (PLATE)", plate), ("nameplate (PLATE)", plate)):
        plate = np.array(rgba[:3]) * 255
        for bgn, bg in (("white", (255, 255, 255)), ("mid grey", (128, 128, 128))):
            over = tuple(plate * rgba[3] + np.array(bg, float) * (1 - rgba[3]))
            print("- %s (alpha %.2f) over %s: MIST %.2f, PAPER %.2f, GOLD %.2f" % (name, rgba[3], bgn, ratio(hex_rgb(tk["MIST"][0]), over),
                  ratio(hex_rgb(tk["PAPER"][0]), over), ratio(hex_rgb(tk["GOLD"][0]), over)))
        need = next(a / 100 for a in range(40, 101) if ratio(hex_rgb(tk["MIST"][0]), tuple(plate * a / 100 + 255 * (1 - a / 100))) >= BODY)
        print("  - alpha at which MIST reaches 4.5:1 over white: %.2f" % need)
    print()


def _nearest_token(h: str, tk: dict) -> tuple:
    c = np.array(hex_rgb(h), float)
    best = min(tk.items(), key=lambda kv: float(np.linalg.norm(np.array(hex_rgb(kv[1][0]), float) - c)))
    return best[0], float(np.linalg.norm(np.array(hex_rgb(best[1][0]), float) - c))


def sec_literals(tk):
    print("## Hex colour literals (I5)\n")
    print("| File:line | Literal | Nearest token | Distance |\n|---|---|---|---|")
    n = 0
    floats = {}
    for path in PAGES + [HUD]:
        for i, ln in enumerate(read(path).splitlines(), 1):
            for m in re.finditer(r'Color\("#?([0-9a-fA-F]{6})"\)', ln):
                tname, d = _nearest_token(m.group(1).lower(), tk)
                print("| `%s:%d` | `#%s` | %s | %.0f |" % (os.path.basename(path), i, m.group(1).lower(), tname, d))
                n += 1
            k = len(re.findall(r"Color\(\s*\d*\.\d+\s*,", ln))
            if k: floats[os.path.basename(path)] = floats.get(os.path.basename(path), 0) + k
    print("\n%d hex literals. Float Color() literals: %s\n" % (n, ", ".join("%s %d" % kv for kv in sorted(floats.items(), key=lambda kv: -kv[1]))))


def sec_sizes():
    lo = ui_kit_int("MIN_SIZE")
    print("## Text asked for under MIN_SIZE (%d) by a literal size\n" % lo)
    pat = re.compile(r"\b(text|draw_text|draw_outlined|para|fit)\((?:[^()]|\([^()]*(?:\([^()]*\))*[^()]*\))*?,\s*(\d{1,2})\s*(?:,|\))")
    for path in PAGES + [HUD, os.path.join(ROOT, "scripts", "ui", "page.gd")]:
        for i, ln in enumerate(read(path).splitlines(), 1):
            for m in pat.finditer(ln):
                size = int(m.group(2))
                if 0 < size < lo and re.search(r",\s*%d\s*,\s*(UiKit\.|Color|lc\b|col\b|\w*_col\b)" % size, ln):
                    print("- `%s:%d` %s at %d" % (os.path.basename(path), i, m.group(1), size))
                    break
    print()


# The standard windows (docs/ui_style_guide.md §2): x, y, w, h, centred on the 1280 x 720 canvas.
STANDARD = {"full": (64, 32, 1152, 656), "large": (128, 56, 1024, 608), "medium": (256, 72, 768, 576),
            "small": (288, 152, 704, 416), "confirm": (384, 248, 512, 224), "dialogue": (48, 464, 1184, 232)}


def standard_for(w: int, h: int) -> str:
    """The smallest standard window that holds a w x h page, shrinking it by 32 px at most on a side."""
    for name in ("small", "medium", "large", "full"):
        sw, sh = STANDARD[name][2:]
        if sw >= w - 32 and sh >= h - 32: return name
    return "full"


def sec_windows():
    print("## Windows (I13)\n")
    print("| Page | Now | Standard | Change |\n|---|---|---|---|")
    for path in PAGES:
        src = read(path)
        m = re.search(r"frame_rect = Rect2\((\d+), (\d+), (\d+), (\d+)\)", src)
        if not m: continue   # the full window, page.gd's default frame_rect
        r = tuple(int(v) for v in m.groups())
        name = "dialogue" if os.path.basename(path) == "dialogue_page.gd" else standard_for(r[2], r[3])
        s = STANDARD[name]
        line = src[:m.start()].count("\n") + 1
        print("| `%s:%d` | %d×%d at %d,%d | %s %d×%d at %d,%d | %+d w, %+d h |" % (os.path.basename(path), line, r[2], r[3], r[0], r[1],
              name, s[2], s[3], s[0], s[1], s[2] - r[2], s[3] - r[3]))
    full = [p for p in PAGES if "frame_rect = Rect2(" not in read(p)]
    print("\nThe full window (page.gd's default frame_rect): %d pages.\n" % len(full))


# Sizes a pixel icon may be drawn at (the guide's §8, Style A): its file 1:1, a native re-render (items @32, techniques
# @48), or twice the file. "any" is a call that may draw any kind of icon.
ALLOWED = {"item": (32, 64, 128), "technique": (48, 64, 128), "glyph": (32, 64), "status": (24, 48)}


def _size_row(place: str, size: int, kind: str) -> tuple:
    ok = size in ALLOWED[kind] if kind in ALLOWED else any(size in v for v in ALLOWED.values())
    return (place, size, kind, "ok" if ok else "off")


def _args(src: str, i: int) -> list:
    """The top-level arguments of the call whose "(" is at src[i]."""
    depth, cur, out = 0, "", []
    for ch in src[i:]:
        if ch in "([": depth += 1
        elif ch in ")]": depth -= 1
        if depth == 0: break
        if ch == "," and depth == 1:
            out.append(cur.strip())
            cur = ""
        elif depth >= 1 and not (depth == 1 and ch == "("): cur += ch
    return out + [cur.strip()]


def _rect_width(expr: str):
    """The literal width of a `Rect2(...)` expression, or None when it is computed."""
    if not expr.startswith("Rect2("): return None
    a = _args(expr, expr.index("("))
    size = a[1] if len(a) == 2 else (a[2] if len(a) == 4 else "")
    m = re.fullmatch(r"Vector2\((\d+), \d+\)", size) or re.fullmatch(r"(\d+)", size)
    return int(m.group(1)) if m else None


def sec_icons():
    print("## Icon draw sizes (I2)\n")
    print("Allowed: items and equipment %s; techniques %s; HUD glyphs %s; status and markers %s.\n"
          % (ALLOWED["item"], ALLOWED["technique"], ALLOWED["glyph"], ALLOWED["status"]))
    rows = []
    for path in PAGES:
        src = read(path)
        base = os.path.basename(path)
        for call, shrink, kind in (("slot_box(", 12, "item"), ("icon_at(", 0, "any")):   # slot_box draws in rect.grow(-6)
            for m in re.finditer(re.escape(call), src):
                if src[max(0, m.start() - 5):m.start()].endswith("func "): continue
                w = _rect_width(_args(src, m.end() - 1)[0])
                if w is not None:
                    rows.append(_size_row("%s:%d %s%s" % (base, src[:m.start()].count("\n") + 1, call.rstrip("("),
                                          " %d" % w if shrink else ""), w - shrink, kind))
        for m in re.finditer(r"draw_texture_rect\(\w+, Rect2\([^)]*, (\d+), (\d+)\)", src):
            rows.append(_size_row("%s:%d draw_texture_rect" % (base, src[:m.start()].count("\n") + 1), int(m.group(1)), "any"))
    hud = read(HUD)
    func = ""
    for i, ln in enumerate(hud.splitlines(), 1):
        if ln.startswith("func "): func = ln[5:ln.find("(")]
        m = re.search(r"\bglyph\((.+), (\d+)(?:, [^,()]*(?:\([^()]*\))?[^,()]*)?\)\s*$", ln)
        if m and "func glyph" not in ln:
            # The status stack passes status icon ids (`ic`); every other glyph() is a HUD glyph.
            rows.append(_size_row("hud.gd:%d glyph" % i, int(m.group(2)), "status" if m.group(1).startswith("ic,") else "glyph"))
        m = re.search(r"draw_texture_rect\((\w+), Rect2\(\w+ - Vector2\((\d+), \2\), Vector2\((\d+), \3\)\)", ln)
        if m:
            kind = "any" if m.group(1) == "motif" else ("technique" if func == "draw_skill_slot" else "item")
            rows.append(_size_row("hud.gd:%d %s" % (i, m.group(1)), int(m.group(3)), kind))
    off = [r for r in rows if r[3] == "off"]
    print("| Place | Drawn at | Kind | |\n|---|---|---|---|")
    for r in off: print("| `%s` | %d | %s | %s |" % r)
    print("\n%d literal icon sizes found, %d off the allowed sizes (slot_box calls with a computed rect are not counted).\n" % (len(rows), len(off)))


def sec_rows():
    print("## list() row pitches off the %d px grid (I8), rounded up so no row gets shorter\n" % GRID)
    pat = re.compile(r'\blist\("[^"]+",.*?,\s*([0-9]+(?:\.[0-9]+)?)\s*,\s*func')
    for path in PAGES:
        for i, ln in enumerate(read(path).splitlines(), 1):
            m = pat.search(ln)
            if m and float(m.group(1)) % GRID:
                v = float(m.group(1))
                print("- `%s:%d` %g → %d" % (os.path.basename(path), i, v, -(-int(v) // GRID) * GRID))
    print()


def sec_plurals():
    s = json.loads(read(os.path.join(ROOT, "data", "strings", "en.json"))).get("strings", {})
    pat = re.compile(r"%d\s+(?:[A-Za-z\-]+\s+){0,2}([A-Za-z][a-z]+s)\b")
    hits = [(k, v) for k, v in sorted(s.items()) if isinstance(v, str) and not k.endswith("_one") and pat.search(v) and (k + "_one") not in s]
    have = sum(1 for k in s if k.endswith("_one"))
    print("## Plurals (I12): %d keys have a `_one` form; %d print a count before a plural noun without one\n" % (have, len(hits)))
    for k, v in hits: print("- `%s`: %s" % (k, v))
    print()


def sec_durations():
    print("## Duration formats in use (I14)\n")
    s = json.loads(read(os.path.join(ROOT, "data", "strings", "en.json"))).get("strings", {})
    for k in ("ui.span_dh", "ui.span_hm", "ui.span_m", "ui.span_s", "ui.clock_days", "ui.posts.days", "ui.posts.hours_minutes",
              "ui.posts.minutes", "ui.welcome.dh_02dm", "ui.welcome.minutes", "ui.auction.closes_in", "ui.techniques.qi_ds",
              "sim.combat.talisman_recovering_ds", "sim.progression.your_mind_needs_rest_ds"):
        print("- `%s`: %s" % (k, s.get(k, "(missing)")))
    print("\nCallers:")
    pat = re.compile(r'UiKit\.(span|clock)\(|func _dur|func _hours_text|hours_minutes"|posts\.days"|posts\.minutes"|dh_02dm"|'
                     r'closes_in"|_ds"\)|"%d:%02d"|%\.1f s')
    for path in sorted(glob.glob(os.path.join(ROOT, "scripts", "**", "*.gd"), recursive=True)):
        for i, ln in enumerate(read(path).splitlines(), 1):
            if pat.search(ln) and "static func" not in ln:
                print("- `%s:%d`: %s" % (rel(path), i, ln.strip()[:110]))
    print()


SECTIONS = ["tokens", "fills", "contrast", "literals", "sizes", "windows", "icons", "rows", "plurals", "durations"]


def main(argv) -> int:
    if "--root" in argv:
        i = argv.index("--root")
        set_root(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    unknown = [a for a in argv if a not in SECTIONS]
    if unknown:
        print("unknown section(s): %s; sections are %s" % (", ".join(unknown), ", ".join(SECTIONS)))
        return 2
    want = argv or SECTIONS
    tk = tokens()
    gr = grades()
    fl = fills() if {"fills", "contrast"} & set(want) else {}
    for s in want:
        if s == "tokens": sec_tokens(tk, gr)
        elif s == "fills": sec_fills(fl)
        elif s == "contrast": sec_contrast(tk, gr, fl)
        elif s == "literals": sec_literals(tk)
        elif s == "sizes": sec_sizes()
        elif s == "windows": sec_windows()
        elif s == "icons": sec_icons()
        elif s == "rows": sec_rows()
        elif s == "plurals": sec_plurals()
        elif s == "durations": sec_durations()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
