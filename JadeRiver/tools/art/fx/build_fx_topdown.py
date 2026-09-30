#!/usr/bin/env python3
"""Build the top-down FX sheets (decision 38): art/fx/topdown/*.png and data/fx_topdown.json.

    python3 tools/art/fx/build_fx_topdown.py               # every sheet
    python3 tools/art/fx/build_fx_topdown.py --check       # build twice in memory: byte-identical, and equal to disk
    python3 tools/art/fx/build_fx_topdown.py --review DIR  # also the review strips (docs/redesign/phase5/combat/)
    python3 tools/art/fx/build_fx_topdown.py --only strike,melee_jian   # some sheets (the manifest keeps the rest)

The look rule (decision 38): the feel (timing, hit-stop, smears, impacts, camera kick, knockback) follows the reference
game; the look is wuxia and xianxia in the element language of elements.py and the art bible's palette.

Every sheet is drawn at art resolution (1 art px = 1 px of the 640x360 world viewport), nearest neighbour, on the
ground plane of the world's 3/4 view (plane.py), in the five drawn directions (E, SE, S, NE, N; W, SW, NW mirror):

  form_<form>[_<dir>].png   a technique form (topdown_forms.py): frames across, band x element down (33 rows); a round
                            form has one sheet, a directed one a sheet per drawn direction
  bolt_<form>[_<dir>].png   a thrown form's projectile loop
  melee_<family>.png        a weapon family's smears (topdown_melee.py): frames across, move x direction down
  common.png                guard, parry, a foe's blow, the Plunge's landing, a charge, a foe's tell
  impact_<dir>.png          the marks a blow leaves: weight x element down
  dust.png                  a dash's, a skid's, a landing's and a step's dust
  story_<art>.png           a story art (story_arts.py, decision 45): the first boss's waking and the elders' arts, one
                            row of frames in the art's own palette

Each sheet is cropped to what its frames draw; the manifest gives its cell and the anchor (the floor point the game
places on the effect's anchor). Deterministic: no randomness, PNGs without metadata.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import elements as E  # noqa: E402
import topdown_melee as M  # noqa: E402
from fxpix import INK, Canvas  # noqa: E402
from plane import ANGLE, DIRS, MIRROR, Plane  # noqa: E402
from topdown_forms import TD_FORMS, TD_ORDER  # noqa: E402
from story_arts import STORY, STORY_ORDER, palette as story_palette  # noqa: E402

PROJECT = HERE.parents[2]
ART_DIR = PROJECT / "art" / "fx" / "topdown"
MANIFEST = PROJECT / "data" / "fx_topdown.json"
BANDS = [[1, 2], [3, 4], [5, 6, 7]]
LOOK_RULE = ("Decision 38: only the feel and technique come from the reference game (timing, hit-stop, smears, impact "
             "readability, camera kick, knockback). The look of every attack and skill stays wuxia/xianxia: sword-light arcs and "
             "qi trails, ink-brush strokes, flowing silk and robe motion, jade and gold qi, elemental Dao imagery (water ripples, "
             "wind petals and leaves, thunder talismans, fire lotus, earth stone, metal sword-qi), palm prints, sword formations "
             "and calligraphic impact marks; never sci-fi, tech or generic fantasy. The element language is "
             "tools/art/fx/elements.py and the palette the art bible's.")
MELEE_CANVAS_PAD = 34
PAD = 24


# ------------------------------------------------------------------------------------------ jobs
def jobs() -> list:
    """Every sheet: (name, kind, arg). Directed forms give one job per drawn direction."""
    out = []
    for form in TD_ORDER:
        s = TD_FORMS[form]
        for d in (DIRS if s["dirs"] else [None]):
            out.append(("form_%s%s" % (form, "_" + d if d else ""), "form", (form, d)))
        if "bolt" in s:
            for d in (DIRS if s["bolt"]["dirs"] else [None]):
                out.append(("bolt_%s%s" % (form, "_" + d if d else ""), "bolt", (form, d)))
    for fam in M.FAMILIES:
        out.append(("melee_%s" % fam, "melee", fam))
    out.append(("common", "common", None))
    for d in DIRS:
        out.append(("impact_%s" % d, "impact", d))
    out.append(("dust", "dust", None))
    for name in STORY_ORDER:
        out.append(("story_%s" % name, "story", name))
    return out


def _render(canvas, anchor, d, draw, n, lut, ghost=False) -> list:
    """Every frame of one animation (a row) as RGBA arrays on the full canvas."""
    w, h = canvas
    ax, ay = anchor
    prev = None
    out = []
    for f in range(n):
        cv = Canvas(w, h)
        draw(Plane(cv, ax, ay, d or "e"), f, n)
        if ghost and prev is not None:
            cv.ghost(prev, dx=-2)   # time: the echo of the frame before, a step behind, half there
        cv.rim(INK)
        cv.clean()
        prev = cv
        out.append(lut[cv.idx])
    return out


def render(job) -> dict:
    """One sheet's rows (lists of RGBA frames on its canvas), its canvas anchor and the facts the manifest needs."""
    name, kind, arg = job
    rows, meta = [], {}
    if kind in ("form", "bolt"):
        form, d = arg
        s = TD_FORMS[form] if kind == "form" else TD_FORMS[form]["bolt"]
        # a margin round the drawer's canvas, so nothing it throws is cut; the crop takes it back
        canvas = (s["canvas"][0] + 2 * PAD, s["canvas"][1] + 2 * PAD)
        anchor, n = (s["anchor"][0] + PAD, s["anchor"][1] + PAD), s["frames"]
        for b in range(len(BANDS)):
            for el in E.ELEMENTS:
                lut = np.array(E.palette(el), np.uint8)
                rows.append(_render(canvas, anchor, d, lambda pl, f, nn, b=b, el=el: s["draw"](pl, f, nn, b, el), n, lut, ghost=el == "time"))
    elif kind == "melee":
        fam = arg
        r = M.FAMILIES[fam]["r"]
        side = int(2 * (r * 1.4 + MELEE_CANVAS_PAD))
        canvas, anchor, n = (side, side + 48), (side // 2, side // 2 + 48), M.SMEAR
        lut = np.array(M.palette(M.FAMILIES[fam]["qi"]), np.uint8)
        for move in M.MOVES:
            for d in DIRS:
                rows.append(_render(canvas, anchor, d, lambda pl, f, nn, move=move: M.draw_move(pl, f, fam, move), n, lut))
    elif kind == "common":
        canvas, anchor = (128, 136), (64, 84)
        n = max(v[1] for v in M.COMMON.values())
        for mark, (draw, frames, fps, impact, loop, directed, pal) in M.COMMON.items():
            lut = np.array(M.palette(pal), np.uint8)
            for d in (DIRS if directed else [None]):
                fr = _render(canvas, anchor, d, lambda pl, f, nn, draw=draw, frames=frames: draw(pl, f, frames), frames, lut)
                rows.append(fr + [np.zeros_like(fr[0])] * (n - frames))
    elif kind == "impact":
        d = arg
        canvas, anchor, n = (104, 104), (52, 52), M.IMPACT_FRAMES
        for weight in M.WEIGHTS:
            for el in E.ELEMENTS:
                lut = np.array(E.palette(el), np.uint8)
                rows.append(_render(canvas, anchor, d, lambda pl, f, nn, weight=weight, el=el: M.draw_impact(pl, f, nn, weight, el), n, lut, ghost=el == "time"))
    elif kind == "dust":
        canvas, anchor, n = (80, 64), (40, 40), M.DUST_FRAMES
        lut = np.array(M.palette("dust"), np.uint8)
        for dk, directed in M.DUST.items():
            for d in (DIRS if directed else [None]):
                rows.append(_render(canvas, anchor, d, lambda pl, f, nn, dk=dk: M.draw_dust(pl, f, nn, dk), n, lut))
    elif kind == "story":
        st = STORY[arg]
        canvas = (st["canvas"][0] + 2 * PAD, st["canvas"][1] + 2 * PAD)
        anchor = (st["anchor"][0] + PAD, st["anchor"][1] + PAD)
        lut = np.array(story_palette(st["palette"]), np.uint8)
        rows.append(_render(canvas, anchor, None, lambda pl, f, nn: st["draw"](pl, f, nn), st["frames"], lut))
    return {"name": name, "kind": kind, "arg": arg, "rows": rows, "anchor": anchor}


def crop(sheet: dict) -> tuple:
    """The sheet image cropped to what its frames draw (a 1 px margin), and its cell and anchor after the crop."""
    rows = sheet["rows"]
    alpha = np.zeros(rows[0][0].shape[:2], bool)
    for row in rows:
        for fr in row:
            alpha |= fr[..., 3] > 0
    ys, xs = np.nonzero(alpha)
    if len(xs) == 0:
        y0, y1, x0, x1 = 0, 1, 0, 1
    else:
        y0, y1 = max(0, ys.min() - 1), min(alpha.shape[0], ys.max() + 2)
        x0, x1 = max(0, xs.min() - 1), min(alpha.shape[1], xs.max() + 2)
    cw, ch = x1 - x0, y1 - y0
    n = max(len(r) for r in rows)
    img = np.zeros((ch * len(rows), cw * n, 4), np.uint8)
    for ri, row in enumerate(rows):
        for fi, fr in enumerate(row):
            img[ri * ch:(ri + 1) * ch, fi * cw:(fi + 1) * cw] = fr[y0:y1, x0:x1]
    ax, ay = sheet["anchor"]
    return Image.fromarray(img, "RGBA"), [int(cw), int(ch)], [int(ax - x0), int(ay - y0)]


def png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.info.clear()
    img.save(buf, format="PNG", optimize=False, compress_level=9)
    return buf.getvalue()


def build(job) -> dict:
    s = render(job)
    img, cell, anchor = crop(s)
    return {"name": s["name"], "kind": s["kind"], "arg": s["arg"], "png": png_bytes(img), "cell": cell, "anchor": anchor,
            "rows": len(s["rows"]), "frames": max(len(r) for r in s["rows"]), "review": s if REVIEW else None}


REVIEW = False


def build_all(names=None, workers=4) -> list:
    todo = [j for j in jobs() if names is None or j[0] in names]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(build, todo))


# ------------------------------------------------------------------------------------------ manifest
def _res(name: str) -> str:
    return "res://art/fx/topdown/%s.png" % name


def manifest(built: list, old: dict) -> dict:
    flat = dict(old.get("_sheets", {}))
    for b in built:
        flat[b["name"]] = {"file": _res(b["name"]), "cell": b["cell"], "anchor": b["anchor"]}
    forms = {}
    for form in TD_ORDER:
        s = TD_FORMS[form]
        e = {"frames": s["frames"], "fps": s["fps"], "impact": s["impact"], "span": s["span"], "at": s["at"], "layer": s["layer"],
             "size": s["size"], "dirs": s["dirs"],
             "sheets": {d: flat.get("form_%s_%s" % (form, d)) for d in DIRS} if s["dirs"] else {"all": flat.get("form_%s" % form)}}
        if "bolt" in s:
            b = s["bolt"]
            e["bolt"] = {"frames": b["frames"], "fps": b["fps"], "dirs": b["dirs"],
                         "sheets": {d: flat.get("bolt_%s_%s" % (form, d)) for d in DIRS} if b["dirs"] else {"all": flat.get("bolt_%s" % form)}}
        forms[form] = e
    common_marks, row = {}, 0
    for mark, (_, frames, fps, impact, loop, directed, pal) in M.COMMON.items():
        common_marks[mark] = {"row": row, "frames": frames, "fps": fps, "impact": impact, "loop": loop, "dirs": directed, "qi": pal}
        row += len(DIRS) if directed else 1
    dust_kinds, row = {}, 0
    for dk, directed in M.DUST.items():
        dust_kinds[dk] = {"row": row, "dirs": directed}
        row += len(DIRS) if directed else 1
    return {
        "schema_version": 1,
        "look_rule": LOOK_RULE,
        "_note": "Built by tools/art/fx/build_fx_topdown.py; never edit by hand. Sheets are at art resolution (1 art px = 1 px of the "
                 "640x360 world). Directed sheets: E, SE, S, NE, N drawn, W/SW/NW mirror. A form's rows are band * 11 + element; a "
                 "family's move * 5 + direction; an impact sheet's weight * 11 + element.",
        "dirs": DIRS, "mirror": MIRROR, "angles_deg": {d: round(a * 57.29577951308232) for d, a in ANGLE.items()},
        "elements": list(E.ELEMENTS), "bands": BANDS,
        "forms": forms,
        "melee": {"moves": M.MOVES, "frames": M.SMEAR, "fps": M.SMEAR_FPS, "impact": M.SMEAR_IMPACT,
                  "families": {fam: dict(flat.get("melee_%s" % fam) or {}, kind=v["kind"], qi=v["qi"], scale=v["scale"], reach_px=v["r"])
                               for fam, v in M.FAMILIES.items()}},
        "common": dict(flat.get("common") or {}, marks=common_marks),
        "impact": {"weights": M.WEIGHTS, "frames": M.IMPACT_FRAMES, "fps": M.IMPACT_FPS, "impact": 0,
                   "sheets": {d: flat.get("impact_%s" % d) for d in DIRS}},
        "dust": dict(flat.get("dust") or {}, frames=M.DUST_FRAMES, fps=M.DUST_FPS, kinds=dust_kinds),
        # Decision 45: the story's own arts (story_arts.py), played by the staged scenes' `art` step (TopdownFx.story).
        "story": {"arts": {name: {"sheet": flat.get("story_%s" % name), "frames": STORY[name]["frames"], "fps": STORY[name]["fps"],
                                  "impact": STORY[name]["impact"], "layer": STORY[name]["layer"], "north": STORY[name]["north"]}
                           for name in STORY_ORDER}},
        "_sheets": {k: flat[k] for k in sorted(flat)},
    }


def dumps(d: dict) -> str:
    return json.dumps(d, indent=1, sort_keys=False) + "\n"


# ------------------------------------------------------------------------------------------ review
def _font(size=11):
    for name in ("DejaVuSansMono.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


BG = (138, 122, 88)         # the path's earth under it, as in the game
BG_GRASS = (68, 143, 67)


def _on(img: np.ndarray, bg) -> np.ndarray:
    a = img[..., 3:4].astype(np.int32)
    return ((img[..., :3].astype(np.int32) * a + np.array(bg, np.int32) * (255 - a)) // 255).astype(np.uint8)


def _grid(title: str, cells: list, labels_x: list, labels_y: list, zoom: int, bg, anchor=None) -> Image.Image:
    """cells[row][col] = an RGBA frame; a labelled grid at `zoom`, the anchor marked red."""
    font = _font()
    ch, cw = cells[0][0].shape[:2]
    lw, pad, top = 70, 3, 30
    W = lw + len(cells[0]) * (cw * zoom + pad)
    Hh = top + len(cells) * (ch * zoom + pad)
    im = Image.new("RGB", (W, Hh), (24, 26, 30))
    dr = ImageDraw.Draw(im)
    dr.text((4, 3), title, fill=(230, 225, 205), font=font)
    for ci, lab in enumerate(labels_x):
        dr.text((lw + ci * (cw * zoom + pad) + 2, 17), lab, fill=(200, 196, 180), font=font)
    for ri, row in enumerate(cells):
        y = top + ri * (ch * zoom + pad)
        dr.text((3, y + ch * zoom // 2 - 6), labels_y[ri], fill=(200, 196, 180), font=font)
        for ci, fr in enumerate(row):
            x = lw + ci * (cw * zoom + pad)
            big = np.repeat(np.repeat(_on(fr, bg), zoom, 0), zoom, 1)
            im.paste(Image.fromarray(big, "RGB"), (x, y))
            if anchor is not None:
                ax, ay = anchor
                dr.rectangle([x + ax * zoom - 1, y + ay * zoom - 1, x + ax * zoom + 1, y + ay * zoom + 1], outline=(228, 60, 60))
    return im


def _crop_rows(s: dict, keep: list) -> tuple:
    """The rows `keep` of a rendered sheet cropped to their own union."""
    rows = [s["rows"][i] for i in keep]
    alpha = np.zeros(rows[0][0].shape[:2], bool)
    for row in rows:
        for fr in row:
            alpha |= fr[..., 3] > 0
    ys, xs = np.nonzero(alpha)
    y0, y1, x0, x1 = max(0, ys.min() - 2), ys.max() + 3, max(0, xs.min() - 2), xs.max() + 3
    ax, ay = s["anchor"]
    return [[fr[y0:y1, x0:x1] for fr in row] for row in rows], (ax - x0, ay - y0)


def save(im: Image.Image, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    im.convert("P", palette=Image.ADAPTIVE, colors=256).save(out, optimize=True)


def review(built: list, out: Path) -> list:
    """Strips for review: each form's motion in its five directions (one element each, the elements rotating over the
    forms), every form at its contact frame in every element, each family's moves, the impacts, the common marks and the
    dust, all on the path's earth at x2."""
    by = {b["name"]: b["review"] for b in built if b["review"]}
    written = []
    els = E.ELEMENTS
    band = 1
    # 1. motion strips: rows = the directions, frames across
    for i, form in enumerate(TD_ORDER):
        s = TD_FORMS[form]
        el = els[i % len(els)]
        ei = band * len(els) + els.index(el)
        if s["dirs"]:
            parts = [by.get("form_%s_%s" % (form, d)) for d in DIRS]
            if any(p is None for p in parts):
                continue
            cells = []
            for p in parts:
                c, _ = _crop_rows(p, [ei])
                cells.append(c[0])
            h = max(c[0].shape[0] for c in cells)
            w = max(c[0].shape[1] for c in cells)
            cells = [[_pad(fr, w, h) for fr in row] for row in cells]
            labels = DIRS
        else:
            p = by.get("form_%s" % form)
            if p is None:
                continue
            c, _ = _crop_rows(p, [band * len(els) + els.index(e) for e in ("fire", "water", "metal", "thunder", "wind")])
            cells, labels = c, ["fire", "water", "metal", "thunder", "wind"]
        im = _grid("%s (%s): %d frames at %d fps, contact on frame %d, band 2, %s, x2, drawn directions %s" % (
            form, el if s["dirs"] else "five elements", s["frames"], s["fps"], s["impact"], "on the path's earth",
            "E SE S NE N (W SW NW mirror)" if s["dirs"] else "round"),
            cells, ["f%d%s" % (k, "*" if k == s["impact"] else "") for k in range(s["frames"])], labels, 2, BG)
        path = out / ("form_%02d_%s.png" % (i + 1, form))
        save(im, path)
        written.append(path)
    # 2. every form at its contact frame, every element (direction SE for directed forms)
    cells, labels = [], []
    for form in TD_ORDER:
        s = TD_FORMS[form]
        p = by.get("form_%s_se" % form) if s["dirs"] else by.get("form_%s" % form)
        if p is None:
            continue
        c, _ = _crop_rows(p, [band * len(els) + k for k in range(len(els))])
        cells.append([row[s["impact"]] for row in c])
        labels.append(form)
    if cells:
        h = max(r[0].shape[0] for r in cells)
        w = max(r[0].shape[1] for r in cells)
        cells = [[_pad(fr, w, h) for fr in row] for row in cells]
        save(_grid("every form x element at its contact frame (SE for directed forms), band 2, x1", cells, els, labels, 1, BG), out / "forms_by_element.png")
        written.append(out / "forms_by_element.png")
    # 3. families: rows = moves (E), frames across, and step 1 in all five directions
    for fam in M.FAMILIES:
        p = by.get("melee_%s" % fam)
        if p is None:
            continue
        rows_e = [mi * len(DIRS) + DIRS.index("se") for mi in range(len(M.MOVES))]
        rows_d = [DIRS.index(d) for d in DIRS]
        c, anchor = _crop_rows(p, rows_e + rows_d)
        im = _grid("%s (%s, %s qi): its moves toward SE, then step 1 in E SE S NE N; %d frames at %d fps, contact on frame %d, x2" % (
            fam, M.FAMILIES[fam]["kind"], M.FAMILIES[fam]["qi"], M.SMEAR, M.SMEAR_FPS, M.SMEAR_IMPACT), c,
            ["f%d%s" % (k, "*" if k == M.SMEAR_IMPACT else "") for k in range(M.SMEAR)], [m for m in M.MOVES] + ["1 %s" % d for d in DIRS], 2, BG, anchor)
        path = out / ("melee_%s.png" % fam)
        save(im, path)
        written.append(path)
    # 4. impacts: weight x element toward SE
    p = by.get("impact_se")
    if p is not None:
        c, _ = _crop_rows(p, list(range(len(M.WEIGHTS) * len(els))))
        save(_grid("impact marks toward SE: light, heavy, finisher x the eleven elements, x2", c, ["f%d" % k for k in range(M.IMPACT_FRAMES)],
                   ["%s %s" % (w[:3], e) for w in M.WEIGHTS for e in els], 2, BG), out / "impacts.png")
        written.append(out / "impacts.png")
    p = by.get("common")
    if p is not None:
        keep, labs, row = [], [], 0
        for mark, v in M.COMMON.items():
            keep.append(row + (DIRS.index("se") if v[5] else 0))
            labs.append(mark)
            row += len(DIRS) if v[5] else 1
        c, anchor = _crop_rows(p, keep)
        save(_grid("guard, parry, a foe's blow (SE), the Plunge's landing, a charge, a foe's tell, x2", c, ["f%d" % k for k in range(len(c[0]))], labs, 2, BG_GRASS, anchor),
             out / "common.png")
        written.append(out / "common.png")
    for name in STORY_ORDER:
        p = by.get("story_%s" % name)
        if p is None:
            continue
        st = STORY[name]
        c, anchor = _crop_rows(p, [0])
        save(_grid("%s (decision 45): %d frames at %d fps, its blow on frame %d, %s, x2" % (name, st["frames"], st["fps"], st["impact"],
                   "flat under the bodies" if st["layer"] == "floor" else "upright over its target"),
                   c, ["f%d%s" % (k, "*" if k == st["impact"] else "") for k in range(st["frames"])], [name], 2, (38, 52, 66), anchor),
             out / ("story_%s.png" % name))
        written.append(out / ("story_%s.png" % name))
    p = by.get("dust")
    if p is not None:
        c, anchor = _crop_rows(p, list(range(len(p["rows"]))))
        labs = ["%s %s" % (k, d) for k, dd in M.DUST.items() for d in (DIRS if dd else ["-"])]
        save(_grid("dust on the path's earth and on grass: dash and skid in five directions, landing, step, x2", c, ["f%d" % k for k in range(M.DUST_FRAMES)], labs, 2, BG_GRASS, anchor),
             out / "dust.png")
        written.append(out / "dust.png")
    return written


def _pad(fr: np.ndarray, w: int, h: int) -> np.ndarray:
    out = np.zeros((h, w, 4), np.uint8)
    y, x = (h - fr.shape[0]) // 2, (w - fr.shape[1]) // 2
    out[y:y + fr.shape[0], x:x + fr.shape[1]] = fr
    return out


# ------------------------------------------------------------------------------------------ main
def main(argv=None) -> int:
    global REVIEW
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", default="", help="comma-separated sheet names (default: all)")
    ap.add_argument("--check", action="store_true", help="build twice in memory; fail unless both builds and the files on disk agree")
    ap.add_argument("--review", metavar="DIR", default=None, help="write the review strips to DIR")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args(argv)
    names = set(n for n in args.only.split(",") if n) or None
    known = {j[0] for j in jobs()}
    if names and names - known:
        print("unknown sheets:", ", ".join(sorted(names - known)))
        return 2
    REVIEW = bool(args.review)
    built = build_all(names, args.workers)
    old = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    man = dumps(manifest(built, old))
    if args.check:
        again = build_all(names, args.workers)
        differ = [a["name"] for a, b in zip(built, again) if a["png"] != b["png"] or a["cell"] != b["cell"]]
        differ += [b["name"] for b in built if (ART_DIR / (b["name"] + ".png")).read_bytes() != b["png"]] if ART_DIR.exists() else ["art/fx/topdown"]
        if names is None and (not MANIFEST.exists() or MANIFEST.read_text(encoding="utf-8") != man):
            differ.append(MANIFEST.name)
        if differ:
            print("DIFFERS:", ", ".join(sorted(set(differ))))
            return 1
        print("checked: %d sheets and the manifest are byte-identical over two builds and to the files on disk" % len(built))
        return 0
    ART_DIR.mkdir(parents=True, exist_ok=True)
    for b in built:
        (ART_DIR / (b["name"] + ".png")).write_bytes(b["png"])
    MANIFEST.write_text(man, encoding="utf-8")
    total = sum(len(b["png"]) for b in built)
    print("wrote %d sheets (%.1f MB) and %s" % (len(built), total / 1e6, MANIFEST.relative_to(PROJECT)))
    if args.review:
        for p in review(built, Path(args.review)):
            print("review", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
