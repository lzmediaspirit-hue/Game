"""Top-down redesign, Phase 3 (decision 32; decision 37 asks for the full set): build the real character for the
top-down view.

The side-view character (data/parts.json: the body, the creator's hair styles, the clothes, hats and capes, and the
weapon families, with every dye and hair colour) redrawn for the 3/4 view by tools/art/topdown/figure/: a posed 3D
doll ray-cast at 1 art px per pixel, cel-shaded in the side view's colours and outlined as docs/redesign/art_bible.md §4
asks. Every layer is cast from the same poses of the unclothed body (AGENTS.md rules 1-4), in S, SE, E, NE and N (the
west facings mirror), for every action in figure/actions.py.

The character is drawn in layer sets (figure/sets/: body, hair, shirt, pants, shoes, hat, cape, weapon_<family>), each
built on its own into its own files, so sets can be drawn in parallel (docs/redesign/phase3/character/HOWTO.md).

Writes (nearest neighbour, no metadata, byte-identical on every build):
  data/topdown/character.json            the index every set shares: actions, facings, bands, z order, dyes, hair
                                         colours, the action catalogue's signature, and the full set's gate
  data/topdown/character/<set>.json      a set's items: per item and section one rect [x, y, w, h, ox, oy] per frame
                                         (offset from the feet), an explicit hidden entry wherever a section is
                                         absent, its sheets, and the game items (data/artifacts.json) that wear it
  art/topdown/character/<cat>_<item>[__<variant>].png  one sheet per item and dye / hair colour: every frame of every
                                         section, trimmed and packed (identical frames share a rect)
The game's compositor (TopdownFigure) reads the index and every set built for its catalogue.
With --review it also renders docs/redesign/phase3/character/ (review_character.py) from what is on disk.

Usage: python3 tools/art/topdown/build_character.py [--only <set>[,<set>...]] [--review] [--check] [--list]
  --only   builds only those sets (the body is always cast, for the other layers' outlines, but only written with it)
  --check  builds twice in memory and fails unless both builds are byte-identical
  --list   lists the sets, their items, and what is still pending
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
from figure import raster, sets  # noqa: E402
from figure.frame import cast_all  # noqa: E402
from figure.geom import DIRS, MIRROR  # noqa: E402
from figure.render import BANDS, colourize  # noqa: E402

ART_DIR = "art/topdown/character"
MANIFEST = "data/topdown/character.json"
SET_DIR = "data/topdown/character"
SHEET_W = 512
REASON = {
    "back": "Nothing of this layer is behind the chest in this action and facing",
    "front": "Nothing of this layer is in front of the chest in this action and facing",
    "mid": "This layer shows only in its back or front section in this action and facing",
    "head": "The head is drawn in this section in every frame",
}
# The game's equipment slots and the parts.json category each slot's look is (InventoryAuthority.WARDROBE_CATEGORY).
WARDROBE = {"robe": "shirt", "trousers": "pants", "boots": "shoes", "weapon": "weapon", "hat": "hat", "cape": "cape"}


def frame_list() -> list:
    """Every drawn frame in catalogue order: (action, facing, index)."""
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


def _dumps(d: dict) -> bytes:
    return (json.dumps(d, sort_keys=True, separators=(",", ":")) + "\n").encode()


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


def index(frames: list) -> dict:
    """The index every set shares. `catalog` signs the action catalogue and the frame layout: a set built for another
    one is stale, and the game and the tests refuse it until it is built again."""
    starts = {}
    for idx, (name, d, i) in enumerate(frames):
        if i == 0:
            starts.setdefault(name, {})[d] = idx
    actions = {}
    for name, (n, fps, loop, hit, label, _fn, lock) in A.CATALOG.items():
        entry = {"frames": n, "fps": fps, "loop": loop, "hit": -1 if hit is None else hit, "label": label,
                 "start": starts[name]}
        if lock:
            entry["facing"] = lock
            entry["redirect"] = {d: lock for d in DIRS + list(MIRROR) if d != lock}
        actions[name] = entry
    man = {
        "schema_version": 2,
        "note": "Top-down character (decision 32), built by tools/art/topdown/build_character.py; do not edit by hand. "
                "The items are in the sets, " + SET_DIR + "/<set>.json.",
        "canvas": [raster.W, raster.H], "anchor": [raster.AX, raster.AY],
        "dirs": DIRS, "mirror": MIRROR, "frames": len(frames),
        "bands": list(BANDS), "order": I.ORDER,
        "actions": actions, "action_order": list(A.CATALOG), "aliases": A.ALIASES, "stand_ins": A.STAND_INS,
        "dyes": ["none"] + P.dye_names(), "hair_colors": P.HAIR_NAMES,
        "sets_dir": "res://" + SET_DIR + "/",
        "full_set": sets.FULL_SET, "pending": sets.pending(),
    }
    man["catalog"] = hashlib.sha1(_dumps({k: man[k] for k in ("canvas", "anchor", "dirs", "mirror", "frames", "bands",
                                                              "actions")})).hexdigest()[:16]
    return man


def artifacts() -> dict:
    """{(category, look): [the game items (data/artifacts.json) that wear it]}."""
    data = json.loads((ROOT / "data/artifacts.json").read_text())["entries"]
    out: dict = {}
    for a in (data.values() if isinstance(data, dict) else data):
        cat = WARDROBE.get(str(a.get("slot", "")))
        look = str(a.get("appearance", "none"))
        if cat and look != "none":
            out.setdefault((cat, look), []).append(str(a["id"]))
    return {k: sorted(v) for k, v in out.items()}


def build_all(kinds: list | None = None) -> dict:
    """Every output of the sets named (all when None), as bytes keyed by path, with the index."""
    found = sets.discover()
    kinds = list(found) if kinds is None else kinds
    items = I.catalog(sorted(set(kinds) | {"body"}))
    frames, per, uniq = cast_everything(items)
    man = index(frames)
    worn = artifacts()
    outputs = {MANIFEST: _dumps(man)}
    by_set: dict = {k: {} for k in kinds}
    for it in items:
        if it.kind not in by_set:
            continue
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
                for d, st in man["actions"][name]["start"].items():
                    if all(seq[st + j] is None for j in range(spec[0])):
                        hidden["%s/%s" % (name, d)] = REASON[b]
            sections.append({"band": b, "z": I.z_of(it.cat, b), "rects": rects, "hidden": hidden})
        by_set[it.kind].setdefault(it.cat, {})[it.name] = {"label": it.label, "sheets": sheets, "sections": sections,
                                                           "artifacts": worn.get((it.cat, it.name), [])}
    for kind, cats in by_set.items():
        outputs["%s/%s.json" % (SET_DIR, kind)] = _dumps({
            "schema_version": 1, "set": kind, "catalog": man["catalog"],
            "note": "A layer set of the top-down character (tools/art/topdown/figure/sets/%s.py), built by "
                    "tools/art/topdown/build_character.py --only %s; do not edit by hand." % (kind, kind),
            "items": cats})
    return outputs


def check_sources() -> list:
    """The side view is the source of truth: the hair colours, dyes and looks must match data/parts.json, and a weapon
    family's set must draw exactly the looks weapon_families.json gives that family."""
    parts = json.loads((ROOT / "data/parts.json").read_text())
    bad = []
    names = [c["name"] for c in parts["_colors"]["hair"]]
    if names != P.HAIR_NAMES:
        bad.append("hair colours differ from parts.json: %s" % names)
    if parts["_dyes"]["order"] != ["none"] + P.dye_names():
        bad.append("dyes differ from parts.json: %s" % parts["_dyes"]["order"])
    fams = json.loads((ROOT / "data/weapon_families.json").read_text())["entries"]
    fams = {str(f["id"]): f for f in (fams.values() if isinstance(fams, dict) else fams)}
    seen: dict = {}
    for kind, mod in sets.discover().items():
        its = mod.items(I.labels())
        for it in its:
            if it.name not in parts.get(it.cat, {}):
                bad.append("%s draws %s:%s, which parts.json does not have" % (kind, it.cat, it.name))
            if it.key in seen:
                bad.append("%s and %s both draw %s" % (seen[it.key], kind, it.key))
            seen[it.key] = kind
        fam = getattr(mod, "FAMILY", None)
        if fam is not None:
            want = sorted(x for x in fams.get(fam, {}).get("appearance", []) if x != "none")
            if sorted(it.name for it in its) != want:
                bad.append("%s draws %s; weapon family %s wears %s" % (kind, sorted(it.name for it in its), fam, want))
    return bad


def list_sets() -> None:
    found = sets.discover()
    labels = I.labels()
    for kind, mod in found.items():
        print("%-20s %s" % (kind, ", ".join("%s:%s" % (it.cat, it.name) for it in mod.items(labels))))
    print("pending (full set %s):" % ("on" if sets.FULL_SET else "off"))
    for batch, what in sets.PENDING.items():
        print("  %-18s %s" % (batch, ", ".join(what)))


def main(argv: list) -> int:
    if "--list" in argv:
        list_sets()
        return 0
    bad = check_sources()
    for b in bad:
        print("SOURCE MISMATCH:", b)
    if bad:
        return 1
    found = sets.discover()
    kinds = None
    for a in argv:
        if a.startswith("--only"):
            v = a.split("=", 1)[1] if "=" in a else argv[argv.index(a) + 1]
            kinds = [k for k in v.split(",") if k]
            unknown = [k for k in kinds if k not in found]
            if unknown:
                print("no such set: %s (sets: %s)" % (", ".join(unknown), ", ".join(found)))
                return 1
    outputs = build_all(kinds)
    if "--check" in argv:
        again = build_all(kinds)
        diff = [p for p in outputs if outputs[p] != again.get(p)]
        for p in diff:
            print("NOT deterministic:", p)
        if diff:
            return 1
    total = 0
    for path, data in sorted(outputs.items()):
        out = ROOT / path
        out.parent.mkdir(parents=True, exist_ok=True)
        if not out.exists() or out.read_bytes() != data:
            out.write_bytes(data)
        total += len(data)
    _clean(found if kinds is None else None)
    print("%d files, %d bytes; index sha1 %s" % (len(outputs), total, hashlib.sha1(outputs[MANIFEST]).hexdigest()[:12]))
    if "--review" in argv:
        import review_character
        review_character.review(review_character.load_built())
    return 0


def _clean(found: dict | None) -> None:
    """Remove what no set on disk draws any more: a sheet no set names; on a full build, a set that is gone."""
    set_dir = ROOT / SET_DIR
    if found is not None:
        for f in set_dir.glob("*.json"):
            if f.stem not in found:
                f.unlink()
    named = set()
    for f in set_dir.glob("*.json"):
        for cat in json.loads(f.read_text())["items"].values():
            for it in cat.values():
                named.update(Path(p).name for p in it["sheets"].values())
    for old in (ROOT / ART_DIR).glob("*.png"):
        if old.name not in named:
            old.unlink()
            imp = old.with_suffix(".png.import")
            if imp.exists():
                imp.unlink()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
