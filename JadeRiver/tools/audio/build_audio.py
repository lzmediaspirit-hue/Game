#!/usr/bin/env python3
"""Build Jade River music loops and sound effects (deterministic numpy synthesis).

    python3 tools/audio/build_audio.py                    # build everything
    python3 tools/audio/build_audio.py title hit coin     # rebuild only these ids
    python3 tools/audio/build_audio.py --review DIR       # + spectrogram PNGs
    python3 tools/audio/build_audio.py --check            # only verify the WAVs on disk

Writes 16-bit PCM mono 22050 Hz WAVs to art/audio/music/<id>.wav and
art/audio/sfx/<id>.wav, and data/audio.json (the manifest always lists every id;
an existing "rooms" mapping is preserved). Prints peak / RMS / loop-seam checks and
exits with status 1 if a check fails.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.dont_write_bytecode = True  # keep tools/audio free of __pycache__
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402

import synth as sy  # noqa: E402
from music import MUSIC  # noqa: E402
from sfx import SFX  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MUSIC_DIR = ROOT / "art" / "audio" / "music"
SFX_DIR = ROOT / "art" / "audio" / "sfx"
MANIFEST = ROOT / "data" / "audio.json"

MUSIC_VOLUME_DB = -6
SFX_VOLUME_DB = -4
SFX_PEAK_DB = -3.0
MUSIC_LEN = (32.0, 48.0)


# ---------------------------------------------------------------- rendering

def render(kind, aid):
    """Render one asset -> (int16 pcm, is_loop, info dict)."""
    t0 = time.time()
    info = {}
    if kind == "music":
        x, info["stats"] = MUSIC[aid]()
        loop = True
    else:
        fn, loop = SFX[aid]
        x = np.asarray(fn(sy.rng_for("sfx", aid)), dtype=float)
        if loop:
            x = x - x.mean()
        else:
            x = sy.filt(x, sy.highpass(20.0, 0.7))[:len(x)]   # remove DC without touching the ends
            x = sy.fades(x, 0.001, 0.012)
        x = x * (sy.undb(SFX_PEAK_DB) / max(sy.peak(x), 1e-12))
    info["secs"] = time.time() - t0
    return sy.to_pcm16(x), loop, info


def _job(args):
    kind, aid = args
    pcm, loop, info = render(kind, aid)
    return kind, aid, pcm, loop, info


# ---------------------------------------------------------------- checks

def analyse(pcm, loop):
    x = pcm.astype(float) / 32768.0
    d = np.abs(np.diff(x))
    res = {
        "len": len(x) / sy.SR,
        "peak_db": sy.db(sy.peak(x)),
        "rms_db": sy.db(sy.rms(x)),
        "clipped": int(np.sum(np.abs(pcm.astype(int)) >= 32767)),
        "nan": bool(np.isnan(x).any()),
        "p999": float(np.percentile(d, 99.9)) if len(d) else 0.0,
    }
    if loop:
        jump = abs(x[-1] - x[0])
        k = sy.nsamp(0.015)
        res["seam"] = jump
        res["seam_ok"] = bool(jump <= max(res["p999"], 1e-4))
        res["seam_rms_db"] = sy.db(sy.rms(x[:k]) / max(sy.rms(x[-k:]), 1e-12))
    else:
        res["edge"] = max(abs(x[0]), abs(x[-1]))
        res["seam_ok"] = bool(res["edge"] < 0.01)
    return res


def problems(kind, aid, a, loop):
    errs = []
    if a["nan"]:
        errs.append("NaN")
    if a["clipped"]:
        errs.append(f"{a['clipped']} clipped samples")
    if not a["seam_ok"]:
        errs.append("loop seam jump" if loop else "non-zero start/end")
    if loop and abs(a["seam_rms_db"]) > 6.0:
        errs.append(f"seam level step {a['seam_rms_db']:+.1f} dB")
    if kind == "music" and not (MUSIC_LEN[0] <= a["len"] <= MUSIC_LEN[1]):
        errs.append(f"length {a['len']:.1f}s outside {MUSIC_LEN}")
    if kind == "music" and a["rms_db"] < -26.0:
        errs.append("very quiet")
    if kind == "sfx" and not loop and abs(a["peak_db"] - SFX_PEAK_DB) > 0.5:
        errs.append("peak not at -3 dBFS")
    return errs


# ---------------------------------------------------------------- review images

def _cmap(v):
    anchors = np.array([[0, 0, 4], [40, 11, 84], [101, 21, 110], [159, 42, 99], [212, 72, 66],
                        [245, 125, 21], [250, 193, 39], [252, 255, 164]], dtype=float)
    v = np.clip(v, 0, 1) * (len(anchors) - 1)
    i = np.minimum(v.astype(int), len(anchors) - 2)
    f = (v - i)[..., None]
    return (anchors[i] * (1 - f) + anchors[i + 1] * f).astype(np.uint8)


def _spec_img(x, width, height, fmin=40.0, win=1024, hop=256, floor=-80.0):
    x = np.asarray(x, dtype=float)
    if len(x) < win:
        x = np.concatenate([x, np.zeros(win - len(x))])
    nfr = 1 + (len(x) - win) // hop
    idx = np.arange(win)[None, :] + hop * np.arange(nfr)[:, None]
    S = np.abs(np.fft.rfft(x[idx] * np.hanning(win), axis=1)) + 1e-9
    freqs = np.geomspace(fmin, sy.NYQ * 0.98, height)
    bins = freqs / (sy.SR / win)
    b0 = np.floor(bins).astype(int)
    fr = bins - b0
    S = S[:, b0] * (1 - fr) + S[:, np.minimum(b0 + 1, S.shape[1] - 1)] * fr
    cols = np.linspace(0, nfr, width + 1).astype(int)
    img = np.stack([S[cols[c]:max(cols[c + 1], cols[c] + 1)].max(axis=0) for c in range(width)], axis=1)
    L = 20 * np.log10(img / 1.0)
    L = (L - L.max() - floor) / (-floor)
    return _cmap(L[::-1])


def review_music(path, aid, pcm):
    from PIL import Image, ImageDraw
    x = pcm.astype(float) / 32768.0
    W, H, E = 1400, 360, 70
    spec = _spec_img(x, W, H)
    seam_len = sy.nsamp(3.0)
    seam = np.concatenate([x[-seam_len:], x[:seam_len]])
    sspec = _spec_img(seam, 300, H)
    im = Image.new("RGB", (W + 320, H + E + 40), (18, 18, 22))
    im.paste(Image.fromarray(spec), (0, E + 30))
    im.paste(Image.fromarray(sspec), (W + 20, E + 30))
    dr = ImageDraw.Draw(im)
    # envelope strip: peak (dim) + rms (bright) per column
    edges = np.linspace(0, len(x), W + 1).astype(int)
    for c in range(W):
        seg = x[edges[c]:max(edges[c + 1], edges[c] + 1)]
        pk = float(np.max(np.abs(seg)))
        r = float(np.sqrt(np.mean(seg * seg)))
        dr.line([(c, E + 25 - int(pk * E)), (c, E + 25)], fill=(70, 90, 110))
        dr.line([(c, E + 25 - int(r * E)), (c, E + 25)], fill=(150, 220, 200))
    s_edges = np.linspace(0, len(seam), 301).astype(int)
    for c in range(300):
        seg = seam[s_edges[c]:max(s_edges[c + 1], s_edges[c] + 1)]
        pk = float(np.max(np.abs(seg)))
        dr.line([(W + 20 + c, E + 25 - int(pk * E)), (W + 20 + c, E + 25)], fill=(150, 220, 200))
    dr.line([(W + 170, 25), (W + 170, E + H + 30)], fill=(255, 60, 60))
    for f in (100, 1000, 5000):
        y = E + 30 + int((1 - np.log(f / 40.0) / np.log(sy.NYQ * 0.98 / 40.0)) * (H - 1))
        dr.text((4, y - 6), f"{f}Hz", fill=(200, 200, 200))
    for s in range(0, int(len(x) / sy.SR) + 1, 5):
        xx = int(s * sy.SR / len(x) * W)
        dr.line([(xx, E + 26), (xx, E + 30)], fill=(200, 200, 200))
        dr.text((xx + 2, E + H + 30), f"{s}s", fill=(160, 160, 160))
    a = analyse(pcm, True)
    dr.text((4, 4), f"{aid}  {a['len']:.1f}s  peak {a['peak_db']:.1f} dBFS  rms {a['rms_db']:.1f} dBFS  "
                    f"seam jump {a['seam']:.4f} (p99.9 step {a['p999']:.4f})", fill=(240, 240, 240))
    dr.text((W + 20, 4), "seam: last 3 s | first 3 s", fill=(240, 240, 240))
    im.save(path)


def review_sfx(path, items):
    from PIL import Image, ImageDraw
    cw, ch, cols = 280, 150, 6
    rows = -(-len(items) // cols)
    im = Image.new("RGB", (cols * cw, rows * (ch + 18)), (18, 18, 22))
    dr = ImageDraw.Draw(im)
    for k, (aid, pcm) in enumerate(items):
        x = pcm.astype(float) / 32768.0
        c, r = k % cols, k // cols
        spec = _spec_img(x, cw - 8, ch - 40, win=512, hop=64)
        ox, oy = c * cw + 4, r * (ch + 18) + 16
        im.paste(Image.fromarray(spec), (ox, oy + 36))
        edges = np.linspace(0, len(x), cw - 7).astype(int)
        for i in range(cw - 8):
            seg = x[edges[i]:max(edges[i + 1], edges[i] + 1)]
            pk = float(np.max(np.abs(seg)))
            dr.line([(ox + i, oy + 34 - int(pk * 32)), (ox + i, oy + 34)], fill=(150, 220, 200))
        dr.text((ox, oy - 14), f"{aid} {len(x) / sy.SR:.2f}s", fill=(240, 240, 240))
    im.save(path)


# ---------------------------------------------------------------- manifest

def write_manifest():
    rooms = {}
    if MANIFEST.exists():
        try:
            rooms = json.loads(MANIFEST.read_text(encoding="utf-8")).get("rooms", {}) or {}
        except (ValueError, OSError):
            rooms = {}
    body = {
        "schema_version": 1,
        "music": {k: {"file": f"res://art/audio/music/{k}.wav", "loop": True, "volume_db": MUSIC_VOLUME_DB}
                  for k in MUSIC},
        "sfx": {k: {"file": f"res://art/audio/sfx/{k}.wav", "volume_db": SFX_VOLUME_DB} for k in SFX},
        "rooms": rooms,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(body, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*", help="asset ids to build (default: all)")
    ap.add_argument("--check", action="store_true", help="only analyse the WAV files on disk")
    ap.add_argument("--review", metavar="DIR", help="write spectrogram PNGs to DIR")
    ap.add_argument("--jobs", "-j", type=int, default=min(4, os.cpu_count() or 1))
    ap.add_argument("--verbose", "-v", action="store_true", help="print per-bus levels of music tracks")
    args = ap.parse_args(argv)

    unknown = [i for i in args.ids if i not in MUSIC and i not in SFX]
    if unknown:
        ap.error("unknown ids: " + ", ".join(unknown))
    todo = [("music", k) for k in MUSIC if not args.ids or k in args.ids]
    todo += [("sfx", k) for k in SFX if not args.ids or k in args.ids]

    results = {}
    if args.check:
        for kind, aid in todo:
            path = (MUSIC_DIR if kind == "music" else SFX_DIR) / f"{aid}.wav"
            if not path.exists():
                print(f"MISSING {path}")
                continue
            pcm, sr = sy.read_wav(path)
            assert sr == sy.SR, (path, sr)
            loop = kind == "music" or SFX[aid][1]
            results[(kind, aid)] = (pcm, loop, {})
    else:
        MUSIC_DIR.mkdir(parents=True, exist_ok=True)
        SFX_DIR.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        if args.jobs > 1 and len(todo) > 1:
            with ProcessPoolExecutor(max_workers=args.jobs) as ex:
                out = list(ex.map(_job, todo))
        else:
            out = [_job(j) for j in todo]
        for kind, aid, pcm, loop, info in out:
            path = (MUSIC_DIR if kind == "music" else SFX_DIR) / f"{aid}.wav"
            sy.write_wav(path, pcm)
            results[(kind, aid)] = (pcm, loop, info)
        write_manifest()
        print(f"rendered {len(out)} assets in {time.time() - t0:.1f}s -> {MANIFEST.relative_to(ROOT)}")

    failed = 0
    total_bytes = 0
    print(f"{'kind':5} {'id':16} {'len s':>6} {'peak':>6} {'rms':>6} {'seam':>8} {'p99.9':>7}  status")
    for (kind, aid), (pcm, loop, info) in results.items():
        a = analyse(pcm, loop)
        errs = problems(kind, aid, a, loop)
        failed += bool(errs)
        total_bytes += 44 + 2 * len(pcm)
        seam = a.get("seam", a.get("edge", 0.0))
        print(f"{kind:5} {aid:16} {a['len']:6.2f} {a['peak_db']:6.1f} {a['rms_db']:6.1f} {seam:8.4f} "
              f"{a['p999']:7.4f}  {'FAIL: ' + '; '.join(errs) if errs else 'ok'}"
              f"{'  loop' if loop else ''}")
    print(f"total {total_bytes / 1e6:.2f} MB in {len(results)} files; {failed} failing")

    if args.verbose and not args.check:
        for (kind, aid), (_, _, info) in results.items():
            if "stats" in info:
                lv = "  ".join(f"{k} {v:+.1f}" for k, v in info["stats"].items())
                print(f"  {aid:14} ({info['secs']:.1f}s) bus level vs mix (dBA): {lv}")
    if args.review:
        rdir = Path(args.review)
        rdir.mkdir(parents=True, exist_ok=True)
        items = []
        for (kind, aid), (pcm, loop, _) in results.items():
            if kind == "music":
                review_music(rdir / f"music_{aid}.png", aid, pcm)
            else:
                items.append((aid, pcm))
        if items:
            review_sfx(rdir / "sfx_sheet.png", items)
        print(f"review images -> {rdir}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
