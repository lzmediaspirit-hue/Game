"""Top-down redesign, Phase 3 (decision 32): build the real character for the top-down view.

The side-view character (data/parts.json: the body, the creator's hair styles, the starting clothes, the gauntlets and
the early weapons, with every dye and hair colour) redrawn for the 3/4 view by tools/art/topdown/figure/: a posed 3D
doll ray-cast at 1 art px per pixel, cel-shaded in the side view's colours and outlined as docs/redesign/art_bible.md §4
asks. Every layer is cast from the same poses of the unclothed body (AGENTS.md rules 1-4), in S, SE, E, NE and N (the
west facings mirror), for every action in figure/actions.py.

Writes (nearest neighbour, no metadata, byte-identical on every build):
  art/topdown/character/<cat>_<item>[__<variant>].png  one sheet per item and dye / hair colour: every frame of every
                                                       section, trimmed and packed (identical frames share a rect)
  data/topdown/character.json                          the manifest the game's compositor reads (TopdownFigure):
                                                       actions, facings, bands, z, and per item and section one rect
                                                       [x, y, w, h, ox, oy] per frame (offset from the feet), with an
                                                       explicit hidden entry wherever a section is absent
With --review it also renders docs/redesign/phase3/character/ (the body sheet, an outfit sheet per facing, the weapon,
hair and dye sheets and the tutorial villagers).

Usage: python3 tools/art/topdown/build_character.py [--review] [--check]
  --check  builds twice in memory and fails unless both builds are byte-identical
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from figure import actions as A  # noqa: E402
from figure import items as I  # noqa: E402
from figure import palettes as P  # noqa: E402
from figure import raster  # noqa: E402
from figure.frame import cast_all  # noqa: E402
from figure.geom import DIRS, MIRROR  # noqa: E402
from figure.render import BANDS  # noqa: E402

ART_DIR = "art/topdown/character"
MANIFEST = "data/topdown/character.json"
SHEET_W = 512
REASON = {
    "back": "Nothing of this layer is behind the chest in this action and facing",
    "front": "Nothing of this layer is in front of the chest in this action and facing",
    "mid": "This layer shows only in its back or front section in this action and facing",
    "head": "The head is drawn in this section in every frame",
}


def frame_list() -> list:
    """Every drawn frame in catalog order: (action, facing, index)."""
    out = []
    for name, spec in A.CATALOG.items():
        n, lock = spec[0], spec[6]
        for d in ([lock] if lock else DIRS):
            for i in range(n):
                out.append((name, d, i))
    return out


def _trim(L) -> tuple | None:
    """A band layer cut to what it draws: (x0, y0, mat, tone, out, out_mat)."""
    on = (L.mat >= 0) | (L.out > 0)
    if not on.any():
        return None
    ys, xs = np.nonzero(on)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    return (int(x0), int(y0), L.mat[y0:y1, x0:x1].copy(), L.tone[y0:y1, x0:x1].copy(), L.out[y0:y1, x0:x1].copy(),
            L.out_mat[y0:y1, x0:x1].copy())


def _colour(piece, mats, palette, line_tone) -> np.ndarray:
    _, _, mat, tone, out, out_mat = piece
    L = raster.Layer.__new__(raster.Layer)
    L.mat, L.tone, L.out, L.out_mat = mat, tone, out, out_mat
    from figure.render import colourize
    return colourize(L, mats, palette, line_tone)


def _pack(pieces: dict) -> tuple:
    """Shelf-pack the unique pieces (key -> piece) into SHEET_W: key -> (x, y), and the sheet's height."""
    order = sorted(pieces, key=lambda k: (-pieces[k][2].shape[0], -pieces[k][2].shape[1], k))
    pos = {}
    x = y = row_h = 0
    for k in order:
        h, w = pieces[k][2].shape
        if x + w > SHEET_W:
            x, y = 0, y + row_h + 1
            row_h = 0
        pos[k] = (x, y)
        x += w + 1
        row_h = max(row_h, h)
    return pos, y + row_h


def png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False)
    return buf.getvalue()


def cast_everything(items: list) -> tuple:
    """Every item's trimmed pieces per band and frame: {key: {band: [piece key or None per frame]}}, {key: {piece
    key: piece}}."""
    frames = frame_list()
    per = {it.key: {b: [] for b in BANDS} for it in items}
    uniq = {it.key: {} for it in items}
    poses = {name: A.poses(name) for name in A.CATALOG}
    for name, d, i in frames:
        cr = cast_all(poses[name][i], d, items)
        for it in items:
            L, _ = cr[it.key]
            for b in BANDS:
                pc = _trim(L[b])
                if pc is None:
                    per[it.key][b].append(None)
                    continue
                h = hashlib.sha1()
                for a in pc[2:]:
                    h.update(a.tobytes())
                    h.update(str(a.shape).encode())
                k = h.hexdigest()[:16]
                uniq[it.key].setdefault(k, pc)
                per[it.key][b].append((k, pc[0] - raster.AX, pc[1] - raster.AY))
    return frames, per, uniq


def build_all() -> dict:
    items = I.catalog()
    frames, per, uniq = cast_everything(items)
    outputs = {}
    starts = {}
    for idx, (name, d, i) in enumerate(frames):
        if i == 0:
            starts.setdefault(name, {})[d] = idx
    man_items: dict = {}
    for it in items:
        pieces = uniq[it.key]
        pos, height = _pack(pieces)
        sheets = {}
        for var in it.variants():
            img = np.zeros((max(1, height), SHEET_W, 4), dtype=np.uint8)
            for k, pc in pieces.items():
                x, y = pos[k]
                a = _colour(pc, it.mats, it.palettes[var], it.look.line_tone)
                hh, ww = a.shape[:2]
                img[y:y + hh, x:x + ww] = a
            fname = "%s/%s%s.png" % (ART_DIR, it.key, "" if var == "none" and len(it.variants()) == 1 else "__" + var)
            outputs[fname] = png_bytes(Image.fromarray(img, "RGBA"))
            sheets[var] = "res://" + fname
        sections = []
        for b in BANDS:
            seq = per[it.key][b]
            if all(s is None for s in seq):
                continue
            rects = []
            for s in seq:
                if s is None:
                    rects += [0, 0, 0, 0, 0, 0]
                else:
                    k, ox, oy = s
                    x, y = pos[k]
                    hh, ww = pieces[k][2].shape
                    rects += [x, y, ww, hh, ox, oy]
            hidden = {}
            for name, spec in A.CATALOG.items():
                for d, st in starts[name].items():
                    if all(seq[st + j] is None for j in range(spec[0])):
                        hidden["%s/%s" % (name, d)] = REASON[b]
            sections.append({"band": b, "z": I.z_of(it.cat, b), "rects": rects, "hidden": hidden})
        man_items.setdefault(it.cat, {})[it.name] = {"label": it.label, "sheets": sheets, "sections": sections}
    actions = {}
    for name, (n, fps, loop, hit, label, _fn, lock) in A.CATALOG.items():
        entry = {"frames": n, "fps": fps, "loop": loop, "hit": -1 if hit is None else hit, "label": label,
                 "start": starts[name]}
        if lock:
            entry["facing"] = lock
            entry["redirect"] = {d: lock for d in DIRS + list(MIRROR) if d != lock}
        actions[name] = entry
    manifest = {
        "schema_version": 1,
        "note": "Top-down character (decision 32), built by tools/art/topdown/build_character.py; do not edit by hand.",
        "canvas": [raster.W, raster.H], "anchor": [raster.AX, raster.AY],
        "dirs": DIRS, "mirror": MIRROR, "frames": len(frames),
        "bands": list(BANDS), "order": I.ORDER,
        "actions": actions, "action_order": list(A.CATALOG), "aliases": A.ALIASES,
        "dyes": ["none"] + P.dye_names(), "hair_colors": P.HAIR_NAMES,
        "items": man_items,
    }
    outputs[MANIFEST] = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return outputs


def check_sources() -> list:
    """The side view is the source of truth: the hair colours and dyes must match data/parts.json."""
    parts = json.loads((ROOT / "data/parts.json").read_text())
    bad = []
    names = [c["name"] for c in parts["_colors"]["hair"]]
    if names != P.HAIR_NAMES:
        bad.append("hair colours differ from parts.json: %s" % names)
    if parts["_dyes"]["order"] != ["none"] + P.dye_names():
        bad.append("dyes differ from parts.json: %s" % parts["_dyes"]["order"])
    return bad


def main(argv: list) -> int:
    bad = check_sources()
    for b in bad:
        print("SOURCE MISMATCH:", b)
    if bad:
        return 1
    outputs = build_all()
    if "--check" in argv:
        again = build_all()
        diff = [p for p in outputs if outputs[p] != again.get(p)]
        for p in diff:
            print("NOT deterministic:", p)
        if diff:
            return 1
    out_dir = ROOT / ART_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    keep = {Path(p).name for p in outputs if p.startswith(ART_DIR)}
    for old in out_dir.glob("*.png"):
        if old.name not in keep:
            old.unlink()
            imp = old.with_suffix(".png.import")
            if imp.exists():
                imp.unlink()
    total = 0
    for path, data in sorted(outputs.items()):
        out = ROOT / path
        out.parent.mkdir(parents=True, exist_ok=True)
        if not out.exists() or out.read_bytes() != data:
            out.write_bytes(data)
        total += len(data)
    print("%d files, %d bytes; manifest sha1 %s" % (len(outputs), total, hashlib.sha1(outputs[MANIFEST]).hexdigest()[:12]))
    if "--review" in argv:
        import review_character
        review_character.review(outputs)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
