"""Build the study's sheets (decision 42) in the game's own format, so the game's compositor draws them.

Usage: python3 tools/art/topdown/study_quality/build_study.py [B C D] [--out DIR]

For each option it writes into DIR/<option>/ (default tools/art/topdown/study_quality/build/, which carries its own
.gitignore and .gdignore, so neither git nor Godot's importer sees it):
  index.json                  the index (actions, facings, anchor) with the items folded in, as TopdownFigure.manifest()
                              reads them: per item, one section per band with its z and one rect [x, y, w, h, ox, oy]
                              per frame; sheets named res://study_quality/<option>/<file>, keys the capture puts
                              into Wardrobe's texture cache
  <cat>_<look>__<variant>.png  one sheet per item and variant (hair colour, dye) the scenes wear
Nothing of the game's (art/, data/) is read for output or written.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from figure import actions as A  # noqa: E402
from figure import items as I  # noqa: E402
from figure.geom import MIRROR  # noqa: E402

import draw  # noqa: E402
import hifi  # noqa: E402
import looks  # noqa: E402
import options as O  # noqa: E402

ROOT = HERE.parents[3]
SHEET_W = 1024


def npc_outfits() -> dict:
    data = json.loads((ROOT / "data/npcs.json").read_text())["entries"]
    by = {str(e["id"]): e for e in data}
    return {n: dict(by[n]["outfit"]) for n in O.NPCS}


def keys_of(outfit: dict) -> list:
    """[(item key, variant)] an outfit wears, as TopdownFigure picks a sheet (hair colour, dye, else the original)."""
    out = []
    for cat in ("body", "shoes", "pants", "shirt", "cape", "hair", "hat", "weapon"):
        name = str(outfit.get(cat, "none"))
        if name in ("none", ""):
            continue
        var = "none"
        if cat == "hair":
            var = str(int(outfit.get("hair_color", 0)))
        elif cat in ("shirt", "pants"):
            var = str(outfit.get(cat + "_dye", "none"))
        out.append((cat + "_" + name, var))
    return out


def frame_list() -> list:
    out = []
    for name, dirs in O.ACTIONS.items():
        n = A.CATALOG[name][0]
        for d in dirs:
            for i in range(n):
                out.append((name, d, i))
    return out


def _trim(R, mats):
    on = (R.mat >= 0) | (R.out > 0)
    if not on.any():
        return None
    ys, xs = np.nonzero(on)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    sub = hifi.Res.__new__(hifi.Res)
    for k in ("mat", "tone", "rim", "bounce", "out", "out_mat", "alpha"):
        setattr(sub, k, getattr(R, k)[y0:y1, x0:x1].copy())
    return int(x0), int(y0), sub, tuple(mats)


def _hash(sub, mats) -> str:
    h = hashlib.sha1()
    for k in ("mat", "tone", "rim", "bounce", "out", "out_mat", "alpha"):
        a = getattr(sub, k)
        h.update(a.tobytes())
        h.update(str(a.shape).encode())
    h.update("|".join(mats).encode())
    return h.hexdigest()[:16]


def _pack(pieces: dict) -> tuple:
    order = sorted(pieces, key=lambda k: (-pieces[k][2].mat.shape[0], -pieces[k][2].mat.shape[1], k))
    pos = {}
    x = y = row_h = 0
    for k in order:
        h, w = pieces[k][2].mat.shape
        if x + w > SHEET_W:
            x, y = 0, y + row_h + 1
            row_h = 0
        pos[k] = (x, y)
        x += w + 1
        row_h = max(row_h, h)
    return pos, y + row_h


def build(opt: str, out_dir: Path) -> dict:
    t0 = time.time()
    mk, face, label = O.OPTIONS[opt]
    g = mk()
    g.face = face
    outfits = {"player": O.PLAYER}
    outfits.update(npc_outfits())
    variants: dict = {}
    acts: dict = {}
    for who, o in outfits.items():
        for key, var in keys_of(o):
            variants.setdefault(key, set()).add(var)
            acts.setdefault(key, set()).update(O.ACTIONS if who == "player" else O.NPC_ACTIONS)
    for k in variants:
        if k.startswith("hair_"):          # the compositor picks a hair colour by its index among all six
            variants[k] = {str(i) for i in range(6)}
    tuned = {k for k, _ in keys_of(O.PLAYER)}
    items = looks.study_items(acts, tuned)
    missing = sorted(set(acts) - set(items))
    if missing:
        raise SystemExit("no such items: %s" % missing)
    frames = frame_list()
    poses = {name: A.poses(name) for name in O.ACTIONS}
    per = {k: {b: [] for b in hifi.BANDS} for k in items}
    uniq = {k: {} for k in items}
    for name, d, i in frames:
        who = [items[k] for k in items if name in acts[k] or items[k].cat == "body"]
        cr = draw.cast_frame(g, poses[name][i], d, who)
        for k in items:
            for b in hifi.BANDS:
                if k not in cr or name not in acts[k]:
                    per[k][b].append(None)
                    continue
                res, caster = cr[k]
                pc = _trim(res[b], caster.mats)
                if pc is None:
                    per[k][b].append(None)
                    continue
                h = _hash(pc[2], pc[3])
                uniq[k].setdefault(h, pc)
                per[k][b].append((h, pc[0] - g.AX, pc[1] - g.AY))
    dst = out_dir / opt
    dst.mkdir(parents=True, exist_ok=True)
    for f in dst.glob("*.png"):
        f.unlink()
    cat_items: dict = {}
    total_px = 0
    for k, it in items.items():
        pieces = uniq[k]
        pos, height = _pack(pieces)
        sheets = {}
        for var in sorted(variants[k]):
            if var not in it.palettes:
                var_use = "none" if "none" in it.palettes else sorted(it.palettes)[0]
            else:
                var_use = var
            p7 = draw.pal7(it, var_use)
            img = np.zeros((max(1, height), SHEET_W, 4), dtype=np.uint8)
            for hk, (x0, y0, sub, mats) in pieces.items():
                x, y = pos[hk]
                a = hifi.colourize(sub, list(mats), p7, {"hair": 1, "cloth": 1, "skin": 2})
                hh, ww = a.shape[:2]
                img[y:y + hh, x:x + ww] = a
            fname = "%s__%s.png" % (k, var_use)
            Image.fromarray(img, "RGBA").save(dst / fname, optimize=False)
            total_px += img.shape[0] * img.shape[1]
            sheets[var_use] = "res://study_quality/%s/%s" % (opt, fname)
        sections = []
        for b in hifi.BANDS:
            seq = per[k][b]
            if all(s is None for s in seq):
                continue
            rects = []
            for s in seq:
                if s is None:
                    rects += [0, 0, 0, 0, 0, 0]
                else:
                    hk, ox, oy = s
                    x, y = pos[hk]
                    hh, ww = pieces[hk][2].mat.shape
                    rects += [x, y, ww, hh, ox, oy]
            sections.append({"band": b, "z": I.z_of(it.cat, b), "rects": rects, "hidden": {}})
        cat_items.setdefault(it.cat, {})[it.name] = {"label": it.label, "sheets": sheets, "sections": sections,
                                                     "artifacts": []}
    starts: dict = {}
    for idx, (name, d, i) in enumerate(frames):
        if i == 0:
            starts.setdefault(name, {})[d] = idx
    actions = {}
    for name in O.ACTIONS:
        n, fps, loop, hit, lab, _fn, _lock = A.CATALOG[name]
        actions[name] = {"frames": n, "fps": fps, "loop": loop, "hit": -1 if hit is None else hit, "label": lab,
                         "start": starts[name]}
    index = {
        "schema_version": 2, "study": opt, "label": label, "density": O.DENSITY[opt],
        "note": "Decision 42's quality study (tools/art/topdown/study_quality/); not the game's.",
        "canvas": [g.W, g.H], "anchor": [g.AX, g.AY], "dirs": O.DIRS, "mirror": MIRROR, "frames": len(frames),
        "bands": list(hifi.BANDS), "order": I.ORDER, "actions": actions, "action_order": list(O.ACTIONS),
        "aliases": {}, "stand_ins": [], "catalog": "study-" + opt, "items": cat_items,
    }
    (dst / "index.json").write_text(json.dumps(index, sort_keys=True, separators=(",", ":")) + "\n")
    stats = {"option": opt, "frames": len(frames), "items": len(items), "sheet_px": total_px,
             "seconds": round(time.time() - t0, 1)}
    print(json.dumps(stats))
    return stats


def main(argv: list) -> int:
    out = HERE / "build"
    if "--out" in argv:
        out = Path(argv[argv.index("--out") + 1])
    opts = [a for a in argv if a in O.OPTIONS] or list(O.OPTIONS)
    out.mkdir(parents=True, exist_ok=True)
    (out / ".gdignore").write_text("")
    (out / ".gitignore").write_text("*\n")
    for o in opts:
        build(o, out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
