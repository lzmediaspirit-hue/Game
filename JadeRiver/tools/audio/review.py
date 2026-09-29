#!/usr/bin/env python3
"""Look at sounds nobody can listen to: waveform and spectrogram PNGs, loop seams and a loudness table.

    python3 tools/audio/review.py --out DIR hit swing water_ambience        # one PNG per id + sheet.png
    python3 tools/audio/review.py --out DIR --root OLD/art/audio hit        # the same from another copy (before)
    python3 tools/audio/review.py --out DIR --pair OLD/art/audio hit=hit:sword:flesh
                                                                            # before | after side by side
    python3 tools/audio/review.py --table ids...                            # markdown loudness table on stdout

An id is a file id (art/audio/sfx/<id>.* or art/audio/music/<id>.*), or a runtime composite the director plays as
one event, rendered here the way scripts/audio/audio_director.gd layers it:
  hit:<family>:<material>[:crit|:chain]   the weapon's transient, the struck body, the weapon's tail after the
                                          hit-stop (data/sound.json `hits`)
  step:<surface>                          four footsteps of the surface at the sprint's cadence
  bed:<bed>[:day|:night]                  an ambient bed with its layer of the hour
  combat:<track>                          the exploration track with its combat stem over it (stem from 50 %)

Loudness is an approximation of ITU-R BS.1770 (K-weighting as a +4 dB shelf over 1.5 kHz and a 38 Hz high-pass,
400 ms blocks, gated): integrated LUFS for loops, the loudest 400 ms block (momentary max) for one-shots. "Phone"
is the share of the energy a small phone speaker plays (above 300 Hz), in dB: near 0 is all audible, below -12 dB
the sound lives in the bass a phone cannot play.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402

import synth as sy  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
AUDIO = ROOT / "art" / "audio"
SOUND = ROOT / "data" / "sound.json"


# ---------------------------------------------------------------- loading

def find(aid, root=AUDIO):
    for kind in ("sfx", "music"):
        for ext in (".wav", ".ogg"):
            p = Path(root) / kind / f"{aid}{ext}"
            if p.exists():
                return p
    return None


def load(path):
    path = Path(path)
    if path.suffix == ".ogg":
        import soundfile as sf
        x, sr = sf.read(str(path), dtype="float64")
    else:
        pcm, sr = sy.read_wav(path)
        x = pcm.astype(float) / 32768.0
    if x.ndim > 1:
        x = x.mean(axis=1)
    assert sr == sy.SR, (path, sr)
    return x


def is_loop(aid, root=AUDIO):
    p = find(aid, root)
    if p is None:
        return False
    if p.parent.name == "music":
        return True
    man = Path(root).parents[1] / "data" / "audio.json"
    try:
        e = json.loads(man.read_text(encoding="utf-8")).get("sfx", {}).get(aid, {})
        if "loop" in e:
            return bool(e["loop"])
    except (OSError, ValueError):
        pass
    return aid.endswith("_ambience") or aid.startswith("bed_")


def _table():
    try:
        return json.loads(SOUND.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _add(y, x, at, gain=1.0):
    i = int(round(at * sy.SR))
    if i + len(x) > len(y):
        y = np.concatenate([y, np.zeros(i + len(x) - len(y))])
    y[i:i + len(x)] += gain * x
    return y


def compose(spec, root=AUDIO):
    """A runtime composite (see the module doc) -> (signal, is_loop, label)."""
    parts = spec.split(":")
    snd = _table()
    if len(parts) > 1 and parts[0] == "hit":
        fam, mat = parts[1], parts[2]
        extra = parts[3] if len(parts) > 3 else ""
        hits = snd.get("hits", {})
        f = hits.get("families", {}).get(fam, {})
        weight = "finisher" if extra in ("crit", "chain") else str(f.get("weight", "medium"))
        stop = float(hits.get("hitstop_f", {}).get(weight, 4)) / 60.0
        y = np.zeros(1)
        y = _add(y, load(find(f"hit_{fam}_a", root)), 0.0, sy.undb(float(hits.get("mix", {}).get("transient_db", 0))))
        y = _add(y, load(find(f"hit_on_{mat}_a", root)), 0.0, sy.undb(float(hits.get("mix", {}).get("body_db", -2))))
        y = _add(y, load(find(f"hit_tail_{fam}", root)), stop, sy.undb(float(hits.get("mix", {}).get("tail_db", -6))))
        if extra:
            y = _add(y, load(find("hit_accent_" + extra, root)), 0.0, sy.undb(float(hits.get("mix", {}).get("accent_db", -3))))
        return y, False, f"hit {fam} on {mat}{' ' + extra if extra else ''} (hit-stop {stop * 1000:.0f} ms)"
    if len(parts) > 1 and parts[0] == "step":
        sid = parts[1]
        y = np.zeros(1)
        cadence = 60.0 / 14.0 * 4.0 / 8.0   # the run's contacts: frames 0 and 4 of 8 at 14 fps
        for k, v in enumerate("abcd"):
            p = find(f"step_{sid}_{v}", root)
            if p is not None:
                y = _add(y, load(p), k * cadence, 1.0)
        return y, False, f"4 steps on {sid} at the sprint's cadence ({cadence * 1000:.0f} ms)"
    if len(parts) > 1 and parts[0] == "bed":
        base = load(find(f"bed_{parts[1]}", root))
        label = f"bed {parts[1]}"
        if len(parts) > 2:
            lay = find(f"bed_{parts[2]}_{parts[1]}", root) or find(f"bed_{parts[2]}", root)
            if lay is not None:
                x = load(lay)
                n = min(len(base), len(x))
                base = base[:n] + sy.undb(-4.0) * x[:n]
                label += f" + {lay.stem}"
        return base, True, label
    if len(parts) > 1 and parts[0] == "combat":
        a = load(find(parts[1], root))
        b = load(find(parts[1] + "_combat", root))
        n = min(len(a), len(b))
        k = np.clip((np.arange(n) / n - 0.45) / 0.1, 0, 1)
        return a[:n] * sy.undb(-3.0 * k) + b[:n] * k, True, f"{parts[1]} with its combat stem entering at 45-55 %"
    p = find(spec, root)
    if p is None:
        raise SystemExit(f"no audio for {spec} under {root}")
    return load(p), is_loop(spec, root), f"{spec}{p.suffix}"


# ---------------------------------------------------------------- analysis

K_WEIGHT = (sy.highshelf(1500.0, 4.0), sy.highpass(38.0, 0.5))


def loudness(x, loop=False):
    """(integrated LUFS, momentary max LUFS) of x, approximating BS.1770."""
    y = sy.filt(np.asarray(x, dtype=float), *K_WEIGHT, circular=loop)[:len(x)]
    n = sy.nsamp(0.4)
    hop = max(1, n // 4)
    if len(y) < n:
        y = np.concatenate([y, np.zeros(n - len(y))])
    ms = np.array([np.mean(y[i:i + n] ** 2) for i in range(0, len(y) - n + 1, hop)])
    lk = -0.691 + 10 * np.log10(np.maximum(ms, 1e-12))
    mom = float(lk.max())
    g = ms[lk > -70.0]
    if not len(g):
        return -70.0, mom
    rel = -0.691 + 10 * np.log10(np.mean(g)) - 10.0
    g = ms[(lk > -70.0) & (lk > rel)]
    return float(-0.691 + 10 * np.log10(np.mean(g))), mom


def phone_share(x):
    """dB of the energy above 300 Hz (a small speaker's band) relative to all of it."""
    x = np.asarray(x, dtype=float)
    hi = sy.filt(x, sy.highpass(300.0, 0.7), sy.highpass(300.0, 0.7))[:len(x)]
    return sy.db(sy.rms(hi) / max(sy.rms(x), 1e-12))


def analyse(x, loop):
    lufs, mom = loudness(x, loop)
    d = np.abs(np.diff(x)) if len(x) > 1 else np.zeros(1)
    res = {"len": len(x) / sy.SR, "peak": sy.db(sy.peak(x)), "rms": sy.db(sy.rms(x)), "lufs": lufs, "mom": mom,
           "phone": phone_share(x), "clipped": int(np.sum(np.abs(x) >= 32767 / 32768)), "loop": loop}
    if loop:
        res["seam"] = float(abs(x[-1] - x[0]))
        res["p999"] = float(np.percentile(d, 99.9))
        k = sy.nsamp(0.05)
        res["seam_db"] = sy.db(sy.rms(x[:k]) / max(sy.rms(x[-k:]), 1e-12))
    return res


def table(rows):
    out = ["| sound | length s | peak dBFS | RMS dBFS | LUFS (int.) | LUFS (mom. max) | phone band dB | clipped | loop seam |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    for name, a in rows:
        seam = f"jump {a['seam']:.4f} (p99.9 step {a['p999']:.4f}), level step {a['seam_db']:+.1f} dB" if a["loop"] else "one-shot"
        out.append(f"| {name} | {a['len']:.2f} | {a['peak']:.1f} | {a['rms']:.1f} | {a['lufs']:.1f} | {a['mom']:.1f} | "
                   f"{a['phone']:.1f} | {a['clipped']} | {seam} |")
    return "\n".join(out)


# ---------------------------------------------------------------- images

def _cmap(v):
    anchors = np.array([[0, 0, 4], [40, 11, 84], [101, 21, 110], [159, 42, 99], [212, 72, 66],
                        [245, 125, 21], [250, 193, 39], [252, 255, 164]], dtype=float)
    v = np.clip(v, 0, 1) * (len(anchors) - 1)
    i = np.minimum(v.astype(int), len(anchors) - 2)
    f = (v - i)[..., None]
    return (anchors[i] * (1 - f) + anchors[i + 1] * f).astype(np.uint8)


def spec_img(x, width, height, fmin=40.0, floor=-80.0):
    x = np.asarray(x, dtype=float)
    win = 512 if len(x) < sy.SR * 2 else 1024
    hop = max(32, min(256, len(x) // (width * 2) or 32))
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
    L = 20 * np.log10(img)
    L = (L - L.max() - floor) / (-floor)
    return _cmap(L[::-1])


def panel(x, loop, title, W=640, H=200, WAVE=90):
    """One sound: a title, its waveform (peak dim, RMS bright, -3 dBFS and 0 dBFS lines), its spectrogram, and for a
    loop the seam (the last 0.25 s | the first 0.25 s, the red line where the loop joins)."""
    from PIL import Image, ImageDraw
    seam_w = 170 if loop else 0
    im = Image.new("RGB", (W + seam_w + (10 if loop else 0), WAVE + H + 44), (18, 18, 22))
    dr = ImageDraw.Draw(im)
    a = analyse(x, loop)
    dr.text((4, 3), title, fill=(240, 240, 240))
    dr.text((4, 15), f"{a['len']:.2f}s  peak {a['peak']:.1f} dBFS  RMS {a['rms']:.1f}  "
                     f"{'LUFS ' + format(a['lufs'], '.1f') if loop else 'mom. max ' + format(a['mom'], '.1f') + ' LUFS'}  "
                     f"phone {a['phone']:.1f} dB" + (f"  seam {a['seam']:.4f}" if loop else ""), fill=(170, 200, 190))
    top = 30
    mid = top + WAVE // 2
    for lvl, col in ((1.0, (90, 40, 40)), (sy.undb(-3.0), (70, 70, 40))):
        for s in (-1, 1):
            yy = mid - s * int(lvl * (WAVE // 2 - 2))
            dr.line([(0, yy), (W, yy)], fill=col)
    edges = np.linspace(0, len(x), W + 1).astype(int)
    for c in range(W):
        seg = x[edges[c]:max(edges[c + 1], edges[c] + 1)]
        hi, lo = float(seg.max()), float(seg.min())
        r = float(np.sqrt(np.mean(seg * seg)))
        s = WAVE // 2 - 2
        dr.line([(c, mid - int(hi * s)), (c, mid - int(lo * s))], fill=(70, 100, 120))
        dr.line([(c, mid - int(r * s)), (c, mid + int(r * s))], fill=(150, 220, 200))
    im.paste(Image.fromarray(spec_img(x, W, H)), (0, top + WAVE + 4))
    for f in (100, 300, 1000, 5000):
        yy = top + WAVE + 4 + int((1 - np.log(f / 40.0) / np.log(sy.NYQ * 0.98 / 40.0)) * (H - 1))
        dr.line([(0, yy), (6, yy)], fill=(220, 220, 220))
        dr.text((8, yy - 6), f"{f}", fill=(220, 220, 220))
    if loop:
        k = sy.nsamp(0.25)
        seam = np.concatenate([x[-k:], x[:k]])
        ox = W + 10
        sedges = np.linspace(0, len(seam), seam_w + 1).astype(int)
        for c in range(seam_w):
            seg = seam[sedges[c]:max(sedges[c + 1], sedges[c] + 1)]
            s = WAVE // 2 - 2
            dr.line([(ox + c, mid - int(float(seg.max()) * s)), (ox + c, mid - int(float(seg.min()) * s))], fill=(150, 220, 200))
        im.paste(Image.fromarray(spec_img(seam, seam_w, H)), (ox, top + WAVE + 4))
        dr.line([(ox + seam_w // 2, top), (ox + seam_w // 2, top + WAVE + H + 4)], fill=(255, 60, 60))
        dr.text((ox, 3), "seam: end | start", fill=(240, 240, 240))
    return im, a


def stack(images, cols=1, gap=8, bg=(10, 10, 12)):
    from PIL import Image
    if not images:
        return None
    w = max(i.width for i in images)
    h = max(i.height for i in images)
    rows = -(-len(images) // cols)
    out = Image.new("RGB", (cols * w + (cols - 1) * gap, rows * h + (rows - 1) * gap), bg)
    for k, im in enumerate(images):
        out.paste(im, ((k % cols) * (w + gap), (k // cols) * (h + gap)))
    return out


def safe(name):
    return name.replace(":", "_").replace("/", "_")


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--out", help="write PNGs here")
    ap.add_argument("--root", default=str(AUDIO), help="the art/audio folder to read (default: this checkout's)")
    ap.add_argument("--pair", metavar="OLD_ROOT", help="ids are before=after; before is read from OLD_ROOT")
    ap.add_argument("--table", action="store_true", help="print a markdown loudness table")
    ap.add_argument("--sheet", default="sheet.png", help="the contact sheet's name")
    args = ap.parse_args(argv)
    rows = []
    shots = []
    for spec in args.ids:
        if args.pair:
            before, after = spec.split("=") if "=" in spec else (spec, spec)
            xb, lb, tb = compose(before, Path(args.pair))
            xa, la, ta = compose(after, Path(args.root))
            ib, ab = panel(xb, lb, "BEFORE  " + tb)
            ia, aa = panel(xa, la, "AFTER  " + ta)
            rows += [("before: " + tb, ab), ("after: " + ta, aa)]
            im = stack([ib, ia], cols=2)
            name = safe(after)
        else:
            x, loop, title = compose(spec, Path(args.root))
            im, a = panel(x, loop, title)
            rows.append((title, a))
            name = safe(spec)
        if args.out:
            Path(args.out).mkdir(parents=True, exist_ok=True)
            im.save(Path(args.out) / f"{name}.png")
            shots.append(im)
    if args.out and shots and args.sheet:
        stack(shots, cols=1 if args.pair else 2).save(Path(args.out) / args.sheet)
    if args.table or not args.out:
        print(table(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
