#!/usr/bin/env python3
"""Build the technique FX sheets: art/fx/<form>.png (and <form>_bolt.png for thrown forms) and data/fx_art.json.

    python3 tools/art/fx/build_fx.py                 # every form
    python3 tools/art/fx/build_fx.py strike wave     # some forms (the manifest keeps the others' entries)
    python3 tools/art/fx/build_fx.py --review DIR    # also write the review sheets there
    python3 tools/art/fx/build_fx.py --verify        # rebuild in memory and compare with the files on disk

One sheet per form: columns are frames, rows are band x element (three richness bands for the vfx tiers 1-2,
3-4 and 5-7, eleven elements each, in elements.ELEMENTS order: row = band * 11 + element). Drawn at art
resolution and upscaled x2 with nearest neighbour (docs/art-contracts.md). Deterministic: a rebuild is
byte-identical. Godot's --import writes the .import files.

Review sheets (--review DIR, the default is the session scratchpad's fx_review/):
  forms_band<b>_1x.png / _2x.png   every form (rows) x element (columns) at the impact frame, in-game size and 2x
  strip_<form>.png                 every frame (columns) x element (rows) of the middle band at 2x, the motion
  bolts_2x.png                     the four projectile loops, every element
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import elements as E  # noqa: E402
from forms import FORMS, ORDER  # noqa: E402
from fxpix import Canvas, upscale  # noqa: E402

PROJECT = HERE.parents[2]
ART_DIR = PROJECT / "art" / "fx"
MANIFEST = PROJECT / "data" / "fx_art.json"
DEFAULT_REVIEW = Path("/tmp/claude-0/-home-user-Game/13461237-7857-505a-bd3b-55d18a20fe2c/scratchpad/fx_review")
SCALE = 2
BANDS = [[1, 2], [3, 4], [5, 6, 7]]
BG_DARK = (10, 32, 39)
BG_EARTH = (138, 122, 88)


# ------------------------------------------------------------------------------------------ rendering
def render_frames(spec: dict, band: int, el: str) -> list[np.ndarray]:
    """Every frame of one animation as an RGBA art-resolution array."""
    w, h = spec["cell"]
    n = spec["frames"]
    lut = np.array(E.palette(el), np.uint8)
    canvases = []
    for f in range(n):
        cv = Canvas(w, h)
        spec["draw"](cv, f, n, band, el)
        if el == "time" and f >= 1:
            cv.ghost(canvases[f - 1], dx=-2)   # time: the echo of the frame before, a step behind, half there
        cv.clean()
        canvases.append(cv)
    return [lut[cv.idx] for cv in canvases]


def build_sheet(spec: dict) -> tuple[Image.Image, dict]:
    """The sheet of one animation spec (a form or its bolt): rows = band x element, columns = frames."""
    w, h = spec["cell"]
    n = spec["frames"]
    rows = len(BANDS) * len(E.ELEMENTS)
    sheet = np.zeros((rows * h * SCALE, n * w * SCALE, 4), np.uint8)
    frames = {}
    for b in range(len(BANDS)):
        for ei, el in enumerate(E.ELEMENTS):
            fr = render_frames(spec, b, el)
            frames[(b, el)] = fr
            r = b * len(E.ELEMENTS) + ei
            for f, img in enumerate(fr):
                big = upscale(img, SCALE)
                sheet[r * h * SCALE:(r + 1) * h * SCALE, f * w * SCALE:(f + 1) * w * SCALE] = big
    return Image.fromarray(sheet, "RGBA"), frames


def save_png(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.info.clear()
    img.save(path, format="PNG", optimize=False, compress_level=9)


def png_bytes(img: Image.Image) -> bytes:
    import io
    buf = io.BytesIO()
    img.info.clear()
    img.save(buf, format="PNG", optimize=False, compress_level=9)
    return buf.getvalue()


def manifest_entry(form: str, spec: dict) -> dict:
    w, h = spec["cell"]
    ax, ay = spec["anchor"]
    row = {"file": "res://art/fx/%s.png" % form, "cell": [w * SCALE, h * SCALE], "anchor": [ax * SCALE, ay * SCALE],
           "frames": spec["frames"], "fps": spec["fps"], "impact": spec["impact"], "span": spec["span"] * SCALE,
           "at": spec["at"], "size": spec["size"]}
    if spec.get("fit"):
        row["fit"] = True
    if "bolt" in spec:
        b = spec["bolt"]
        bw, bh = b["cell"]
        bx, by = b["anchor"]
        row["bolt"] = {"file": "res://art/fx/%s_bolt.png" % form, "cell": [bw * SCALE, bh * SCALE], "anchor": [bx * SCALE, by * SCALE],
                       "frames": b["frames"], "fps": b["fps"]}
    return row


def write_manifest(entries: dict) -> None:
    data = {"schema_version": 1, "scale": SCALE, "elements": list(E.ELEMENTS), "bands": BANDS,
            "element_of": {"none": "formless", "ice": "water", "tide": "water", "lava": "fire", "crystal": "earth", "sand": "earth",
                           "star": "metal", "blade": "metal", "hollow": "formless", "life_death": "soul"},
            "forms": {k: entries[k] for k in sorted(entries)}}
    MANIFEST.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")


# ------------------------------------------------------------------------------------------ review
def _font():
    for name in ("DejaVuSansMono.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, 11)
        except OSError:
            continue
    return ImageFont.load_default()


def _composite(img: np.ndarray, bg) -> np.ndarray:
    a = img[..., 3:4].astype(np.int32)
    rgb = img[..., :3].astype(np.int32)
    out = (rgb * a + np.array(bg, np.int32) * (255 - a)) // 255
    return out.astype(np.uint8)


def review_forms(all_frames: dict, out_dir: Path, band: int, zoom: int) -> Path:
    """Rows = forms, columns = elements, the impact frame of each, on the dark and the earthy backgrounds."""
    font = _font()
    forms = [f for f in ORDER if f in all_frames]
    cw = max(FORMS[f]["cell"][0] for f in forms) * zoom
    ch = max(FORMS[f]["cell"][1] for f in forms) * zoom
    pad = 4
    label_w = 64
    panel_w = label_w + len(E.ELEMENTS) * (cw + pad)
    panel_h = 18 + len(forms) * (ch + pad)
    W, H = panel_w, 20 + 2 * panel_h
    im = Image.new("RGB", (W, H), (24, 26, 30))
    dr = ImageDraw.Draw(im)
    dr.text((6, 4), "technique FX  band %d (vfx tiers %s)  impact frame  %dx" % (band + 1, "-".join(map(str, BANDS[band])), zoom // 2), fill=(230, 225, 205), font=font)
    for bi, bg in enumerate((BG_DARK, BG_EARTH)):
        oy = 20 + bi * panel_h
        dr.rectangle([0, oy, W, oy + panel_h - 2], fill=bg)
        col = (240, 235, 215) if bi == 0 else (25, 22, 18)
        for ei, el in enumerate(E.ELEMENTS):
            dr.text((label_w + ei * (cw + pad) + 2, oy + 2), el, fill=col, font=font)
        for ri, form in enumerate(forms):
            ry = oy + 18 + ri * (ch + pad)
            dr.text((4, ry + ch // 2 - 6), form, fill=col, font=font)
            spec = FORMS[form]
            for ei, el in enumerate(E.ELEMENTS):
                img = all_frames[form][(band, el)][spec["impact"]]
                comp = _composite(img, bg)
                big = np.repeat(np.repeat(comp, zoom, 0), zoom, 1)
                x = label_w + ei * (cw + pad) + (cw - big.shape[1]) // 2
                y = ry + (ch - big.shape[0]) // 2
                im.paste(Image.fromarray(big, "RGB"), (x, y))
    return save_review(im, out_dir / ("forms_band%d_%dx.png" % (band + 1, zoom // 2)))


def save_review(im: Image.Image, out: Path) -> Path:
    """A review PNG in 256 colours (the sheets use far fewer, so nothing is lost) to keep docs/mockups small."""
    out.parent.mkdir(parents=True, exist_ok=True)
    im.convert("P", palette=Image.ADAPTIVE, colors=256).save(out, optimize=True)
    return out


def review_strip(form: str, frames: dict, out_dir: Path, band: int = 1, zoom: int = 4) -> Path:
    """Every frame across, every element down, at 2x on the dark background: the motion of one form."""
    font = _font()
    spec = FORMS[form]
    w, h = spec["cell"]
    n = spec["frames"]
    cw, ch = w * zoom, h * zoom
    pad = 3
    label_w = 60
    panel_w = label_w + n * (cw + pad)
    panel_h = 16 + len(E.ELEMENTS) * (ch + pad)
    im = Image.new("RGB", (panel_w, 18 + panel_h), (24, 26, 30))
    dr = ImageDraw.Draw(im)
    dr.text((4, 3), "%s  %d frames at %d fps, impact %d, cell %dx%d art px, anchor %s, band %d, %dx" % (
        form, n, spec["fps"], spec["impact"], w, h, spec["anchor"], band + 1, zoom // 2), fill=(230, 225, 205), font=font)
    for bi, bg in enumerate((BG_DARK,)):
        oy = 18 + bi * panel_h
        dr.rectangle([0, oy, panel_w, oy + panel_h - 2], fill=bg)
        col = (240, 235, 215) if bi == 0 else (25, 22, 18)
        for f in range(n):
            dr.text((label_w + f * (cw + pad) + 2, oy + 2), "f%d%s" % (f, "*" if f == spec["impact"] else ""), fill=col, font=font)
        for ei, el in enumerate(E.ELEMENTS):
            ry = oy + 16 + ei * (ch + pad)
            dr.text((4, ry + ch // 2 - 6), el, fill=col, font=font)
            for f in range(n):
                comp = _composite(frames[(band, el)][f], bg)
                big = np.repeat(np.repeat(comp, zoom, 0), zoom, 1)
                x = label_w + f * (cw + pad)
                im.paste(Image.fromarray(big, "RGB"), (x, ry))
                # the anchor
                ax, ay = spec["anchor"]
                dr.rectangle([x + ax * zoom - 1, ry + ay * zoom - 1, x + ax * zoom + 1, ry + ay * zoom + 1], outline=(228, 88, 88))
    return save_review(im, out_dir / ("strip_%s.png" % form))


def review_bolts(bolt_frames: dict, out_dir: Path, zoom: int = 4) -> Path:
    font = _font()
    forms = [f for f in ORDER if f in bolt_frames]
    if not forms:
        return out_dir
    cw, ch = 48 * zoom, 24 * zoom
    pad = 3
    label_w = 60
    n = 4
    panel_w = label_w + len(forms) * (n * (cw + pad) + 8)
    panel_h = 16 + len(E.ELEMENTS) * (ch + pad)
    im = Image.new("RGB", (panel_w, 18 + 2 * panel_h), (24, 26, 30))
    dr = ImageDraw.Draw(im)
    dr.text((4, 3), "projectile loops (bolt sheets), band 2, %dx: %s" % (zoom // 2, ", ".join(forms)), fill=(230, 225, 205), font=font)
    for bi, bg in enumerate((BG_DARK, BG_EARTH)):
        oy = 18 + bi * panel_h
        dr.rectangle([0, oy, panel_w, oy + panel_h - 2], fill=bg)
        col = (240, 235, 215) if bi == 0 else (25, 22, 18)
        for ei, el in enumerate(E.ELEMENTS):
            ry = oy + 16 + ei * (ch + pad)
            dr.text((4, ry + ch // 2 - 6), el, fill=col, font=font)
            for fi, form in enumerate(forms):
                for f in range(n):
                    comp = _composite(bolt_frames[form][(1, el)][f], bg)
                    big = np.repeat(np.repeat(comp, zoom, 0), zoom, 1)
                    x = label_w + fi * (n * (cw + pad) + 8) + f * (cw + pad)
                    im.paste(Image.fromarray(big, "RGB"), (x, ry))
                    if ei == 0:
                        dr.text((x + 2, oy + 2), "%s f%d" % (form, f), fill=col, font=font)
    return save_review(im, out_dir / "bolts_2x.png")


# ------------------------------------------------------------------------------------------ main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("forms", nargs="*", help="form ids (default: all)")
    ap.add_argument("--review", metavar="DIR", nargs="?", const=str(DEFAULT_REVIEW), default=None, help="write review sheets to DIR")
    ap.add_argument("--no-write", action="store_true", help="render only; write no sheet and no manifest")
    ap.add_argument("--verify", action="store_true", help="rebuild in memory and compare with the files on disk (exit 1 on a difference)")
    args = ap.parse_args(argv)
    ids = args.forms or ORDER
    bad = [i for i in ids if i not in FORMS]
    if bad:
        print("unknown forms:", ", ".join(bad))
        return 2
    entries = {}
    if MANIFEST.exists():
        entries = json.loads(MANIFEST.read_text(encoding="utf-8")).get("forms", {})
    all_frames, bolt_frames = {}, {}
    differ = []
    for form in ids:
        spec = FORMS[form]
        sheet, frames = build_sheet(spec)
        all_frames[form] = frames
        outputs = [(ART_DIR / ("%s.png" % form), sheet)]
        if "bolt" in spec:
            bsheet, bframes = build_sheet(spec["bolt"])
            bolt_frames[form] = bframes
            outputs.append((ART_DIR / ("%s_bolt.png" % form), bsheet))
        for path, img in outputs:
            if args.verify:
                if not path.exists() or path.read_bytes() != png_bytes(img):
                    differ.append(path.name)
            elif not args.no_write:
                save_png(img, path)
        entries[form] = manifest_entry(form, spec)
        print("%-8s %dx%d px, %d frames%s" % (form, sheet.width, sheet.height, spec["frames"], ", bolt" if "bolt" in spec else ""))
    if args.verify:
        want = json.dumps({"forms": {k: entries[k] for k in sorted(entries)}}, indent=2)["forms"] if False else None
        current = json.loads(MANIFEST.read_text(encoding="utf-8")).get("forms", {}) if MANIFEST.exists() else {}
        if {k: entries[k] for k in ids} != {k: current.get(k) for k in ids}:
            differ.append(MANIFEST.name)
        if differ:
            print("DIFFERS:", ", ".join(differ))
            return 1
        print("verified: every sheet and the manifest are byte-identical to a fresh build")
        return 0
    if not args.no_write:
        write_manifest(entries)
        print("wrote", MANIFEST.relative_to(PROJECT))
    if args.review:
        out_dir = Path(args.review)
        out_dir.mkdir(parents=True, exist_ok=True)
        for b in range(len(BANDS)):
            review_forms(all_frames, out_dir, b, 2)
            review_forms(all_frames, out_dir, b, 4)
        for form in ids:
            review_strip(form, all_frames[form], out_dir)
        review_bolts(bolt_frames, out_dir)
        print("review sheets in", out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
