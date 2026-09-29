"""The numbers behind the study's costs (docs/redesign/feedback/character_quality.md): for the player's outfit over the
study's 52 frames (idle, walk, run, the rising cut; S and SE), the time to cast and the texture each option packs,
against today's pipeline on the same frames, and today's full set on disk.

Usage: python3 tools/art/topdown/study_quality/stats.py
"""
from __future__ import annotations

import glob
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
from figure.frame import cast_all  # noqa: E402
from figure.render import BANDS  # noqa: E402

import build_study as BS  # noqa: E402
import draw  # noqa: E402
import looks  # noqa: E402
import options as O  # noqa: E402

ROOT = HERE.parents[3]


def _area(uniq: dict) -> int:
    return sum(int(h) * int(w) for h, w in uniq.values())


def today(keys: list, frames: list) -> dict:
    items = [it for it in I.catalog(["body", "hair", "shirt", "pants", "shoes", "weapon_jian"]) if it.key in keys]
    uniq: dict = {}
    t = time.time()
    for name, d, i in frames:
        cr = cast_all(A.poses(name)[i], d, items)
        for it in items:
            L, _ = cr[it.key]
            for b in BANDS:
                on = (L[b].mat >= 0) | (L[b].out > 0)
                if not on.any():
                    continue
                ys, xs = np.nonzero(on)
                sub = L[b].mat[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
                h = hashlib.sha1(sub.tobytes() + L[b].tone[ys.min():ys.max() + 1, xs.min():xs.max() + 1].tobytes()).hexdigest()
                uniq[(it.key, h)] = sub.shape
    return {"seconds": round(time.time() - t, 2), "texels": _area(uniq)}


def study(opt: str, keys: list, frames: list) -> dict:
    mk, face, _ = O.OPTIONS[opt]
    g = mk()
    g.face = face
    its = looks.study_items({k: 1 for k in keys}, set(keys))
    uniq: dict = {}
    t = time.time()
    for name, d, i in frames:
        cr = draw.cast_frame(g, A.poses(name)[i], d, [its[k] for k in keys])
        for k in keys:
            res, c = cr[k]
            for b in BANDS:
                pc = BS._trim(res[b], c.mats)
                if pc is None:
                    continue
                uniq[(k, BS._hash(pc[2], pc[3]))] = pc[2].mat.shape
    return {"seconds": round(time.time() - t, 2), "texels": _area(uniq)}


def disk() -> dict:
    tot = 0
    per: dict = {}
    for f in glob.glob(str(ROOT / "art/topdown/character/*.png")):
        w, h = Image.open(f).size
        tot += w * h
        per[Path(f).stem] = w * h
    outfit = ["body_light", "hair_topknot__0", "shirt_disciple__none", "pants_loose__none", "shoes_slippers", "weapon_sword"]
    return {"sheets": len(per), "texels": tot, "rgba8_mb": round(tot * 4 / 1e6, 1),
            "player_outfit_texels": sum(per.get(k, 0) for k in outfit),
            "player_outfit_rgba8_mb": round(sum(per.get(k, 0) for k in outfit) * 4 / 1e6, 2),
            "frames_per_item": json.loads((ROOT / "data/topdown/character.json").read_text())["frames"]}


def main() -> int:
    keys = [k for k, _ in BS.keys_of(O.PLAYER)]
    frames = BS.frame_list()
    out = {"frames": len(frames), "items": keys, "A": today(keys, frames)}
    for o in O.OPTIONS:
        out[o] = study(o, keys, frames)
    base = out["A"]["texels"]
    for o in ["A"] + list(O.OPTIONS):
        out[o]["texels_vs_A"] = round(out[o]["texels"] / base, 2)
        out[o]["seconds_vs_A"] = round(out[o]["seconds"] / out["A"]["seconds"], 1)
    out["today_on_disk"] = disk()
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
