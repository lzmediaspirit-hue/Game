#!/usr/bin/env python3
"""Build Jade River music loops and sound effects (deterministic numpy synthesis).

    python3 tools/audio/build_audio.py                    # build everything
    python3 tools/audio/build_audio.py title hit coin     # rebuild only these ids
    python3 tools/audio/build_audio.py --review DIR       # + spectrogram PNGs
    python3 tools/audio/build_audio.py --check            # only verify the files on disk

One-shots are 16-bit PCM mono 22050 Hz WAVs (art/audio/sfx/<id>.wav; Godot imports them as QOA). Loops (the music,
its combat stems, the ambient beds) are Ogg Vorbis (art/audio/music/<id>.ogg, art/audio/sfx/<id>.ogg) when the
soundfile module is present, else WAVs. data/audio.json lists every id with its file, its level (VOLUME: each
new sound is levelled by its loudness, not its peak) and its length; a music track also its grid (bpm, beats per
bar, bars) and its combat stem (an existing "rooms" mapping is preserved). Prints peak / RMS / loop-seam / phone-band
checks and exits with status 1 if a check fails.
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
import music_adaptive  # noqa: E402,F401  (decision 43: the combat stems and the boss themes)
from sfx import SFX  # noqa: E402
import sfx_pass  # noqa: E402,F401  (decision 43: layered hits, steps, foes, the world, stingers)
import beds  # noqa: E402,F401  (decision 43: the ambient beds)
import life  # noqa: E402,F401  (decision 44: the living world's critters and work, the places)
import review  # noqa: E402

try:
    import soundfile  # Ogg Vorbis for the loops
except ImportError:  # pragma: no cover - the WAV fallback
    soundfile = None

ROOT = Path(__file__).resolve().parents[2]
MUSIC_DIR = ROOT / "art" / "audio" / "music"
SFX_DIR = ROOT / "art" / "audio" / "sfx"
MANIFEST = ROOT / "data" / "audio.json"

MUSIC_VOLUME_DB = -6
SFX_VOLUME_DB = -4
SFX_PEAK_DB = -3.0
MUSIC_LEN = (32.0, 48.0)
OGG_QUALITY = {"music": 0.15, "sfx": 0.1}   # Vorbis quality: ~32 kbps for music, ~28 kbps for the beds (mono 22 kHz)
TRIM_DB = -60.0                              # a one-shot's silent tail below this (re its peak) is cut off
PHONE_MIN_DB = -12.0                         # a new sound's share above 300 Hz (what a phone speaker plays)

# Decision 43's mix: each new sound's level is set from its loudness (review.loudness: the loudest 400 ms of a
# one-shot, the integrated loudness of a loop), so a sparse tick and a dense roar of the same category sound as loud.
# (prefix, target LUFS before the bus): the first matching prefix wins; ids that match none keep SFX_VOLUME_DB.
VOLUME = [
    ("hit_accent_", -27.0), ("hit_tail_", -31.0), ("hit_on_", -26.0), ("hit_el_", -26.0), ("hit_", -25.0),
    ("swing_", -25.0), ("cast_", -23.0), ("step_", -30.0), ("land_heavy", -27.0), ("land_", -27.0),
    ("tell_", -25.0), ("die_", -23.0), ("sting_", -18.0), ("bed_birds", -34.0), ("bed_insects", -35.0),
    ("bed_frogs", -34.0), ("bed_", -29.0), ("door_", -25.0), ("loot_drop", -26.0), ("splash", -24.0),
    ("ui_confirm", -24.0), ("ui_tab", -28.0), ("talk_", -26.0), ("bark", -28.0), ("scene_in", -24.0),
    # decision 44: the living world, ambience under the fight (and falling off with distance): the anvil's ring a little
    # over the rest of the work (the axe's short bite, peakier, a little under it), the swings, a look about, a brush and
    # a breath well under it; the smith's light tap between blows under his blows; the critters a touch over the work;
    # the player's own use of a place near a door's
    ("life_work_breathe", -41.0), ("life_work_look", -39.0), ("life_work_write", -37.0), ("life_work_hammer_hit_c", -35.0),
    ("life_work_pick", -35.0),
    ("life_work_chop_hit", -32.0), ("life_work_hammer_hit", -30.0), ("life_work_chop", -37.0), ("life_work_hammer", -37.0),
    ("life_work_", -33.0), ("life_frog_leap", -35.0), ("life_fish_flee", -34.0), ("life_cat_wake", -34.0),
    ("life_dog_bark", -31.0), ("life_", -32.0), ("place_open", -28.0), ("place_", -30.0),
]


def volume_for(aid, x, loop):
    for pre, target in VOLUME:
        if aid.startswith(pre):
            lufs, mom = review.loudness(x, loop)
            level = lufs if loop else mom
            return float(np.clip(round(2.0 * (target - level)) / 2.0, -30.0, 0.0))
    return float(SFX_VOLUME_DB)


def is_new(aid):
    """The pass's own sounds (decision 43), held to the phone-band rule."""
    return any(aid.startswith(p) for p, _ in VOLUME) or aid.endswith("_combat") or aid.startswith("boss_")


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
            x = trim(x)
            x = sy.fades(x, 0.001, 0.012)
        x = x * (sy.undb(SFX_PEAK_DB) / max(sy.peak(x), 1e-12))
    info["secs"] = time.time() - t0
    if kind == "music":
        info["meta"] = dict(MUSIC_META.get(aid, {}))
    return sy.to_pcm16(x), loop, info


def trim(x):
    """Cut a one-shot's silent tail (below TRIM_DB of its peak), keeping 20 ms for the fade."""
    a = np.abs(x)
    over = np.nonzero(a > sy.peak(x) * sy.undb(TRIM_DB))[0]
    if not len(over):
        return x
    end = min(len(x), int(over[-1]) + sy.nsamp(0.02))
    return x[:max(end, sy.nsamp(0.03))]


def _job(args):
    kind, aid = args
    pcm, loop, info = render(kind, aid)
    return kind, aid, pcm, loop, info


# ---------------------------------------------------------------- files

MUSIC_META = {}   # each music track's grid, recorded as its Track is made (the wrapped music.Track.__init__)


def _capture_meta():
    import music
    orig = music.Track.__init__
    if getattr(orig, "_records_meta", False):
        return

    def init(self, tid, bpm, bar_beats, bars):
        orig(self, tid, bpm, bar_beats, bars)
        MUSIC_META[tid] = {"bpm": float(bpm), "bar_beats": int(bar_beats), "bars": int(bars), "loop_s": round(self.L / sy.SR, 6)}

    init._records_meta = True
    music.Track.__init__ = init


_capture_meta()


def is_loop(kind, aid):
    return kind == "music" or SFX[aid][1]


def ext_for(kind, aid):
    return ".ogg" if soundfile is not None and is_loop(kind, aid) else ".wav"


def path_for(kind, aid, ext=None):
    return (MUSIC_DIR if kind == "music" else SFX_DIR) / f"{aid}{ext or ext_for(kind, aid)}"


_CRC_TABLE = []


def ogg_crc(data):
    """The Ogg page checksum (CRC-32, polynomial 0x04c11db7, not reflected, starting at 0)."""
    if not _CRC_TABLE:
        for i in range(256):
            c = i << 24
            for _ in range(8):
                c = ((c << 1) ^ 0x04C11DB7) if c & 0x80000000 else (c << 1)
            _CRC_TABLE.append(c & 0xFFFFFFFF)
    crc = 0
    for b in data:
        crc = ((crc << 8) & 0xFFFFFFFF) ^ _CRC_TABLE[((crc >> 24) ^ b) & 0xFF]
    return crc


def fix_ogg_serial(data, aid):
    """libsndfile gives each Ogg stream a random serial number; set it from the id (and redo each page's checksum), so
    the same build writes the same bytes."""
    import zlib
    serial = zlib.crc32(aid.encode("utf-8")) & 0x7FFFFFFF
    buf = bytearray(data)
    i = 0
    while i + 27 <= len(buf) and buf[i:i + 4] == b"OggS":
        nseg = buf[i + 26]
        size = 27 + nseg + sum(buf[i + 27:i + 27 + nseg])
        buf[i + 14:i + 18] = serial.to_bytes(4, "little")
        buf[i + 22:i + 26] = bytes(4)
        buf[i + 22:i + 26] = ogg_crc(bytes(buf[i:i + size])).to_bytes(4, "little")
        i += size
    return bytes(buf)


def write_audio(kind, aid, pcm):
    """Write one asset in its format; a stale file of the other format (and its .import) is removed."""
    path = path_for(kind, aid)
    other = path.with_suffix(".wav" if path.suffix == ".ogg" else ".ogg")
    for stale in (other, Path(str(other) + ".import")):
        if stale.exists():
            stale.unlink()
    if path.suffix == ".ogg":
        import io
        b = io.BytesIO()
        soundfile.write(b, pcm.astype(float) / 32768.0, sy.SR, format="OGG", subtype="VORBIS",
                        compression_level=1.0 - OGG_QUALITY[kind])
        path.write_bytes(fix_ogg_serial(b.getvalue(), aid))
    else:
        sy.write_wav(path, pcm)
    return path


def read_audio(path):
    """-> (int16 pcm, rate) of a WAV or an Ogg file (decoded)."""
    if Path(path).suffix == ".ogg":
        x, sr = soundfile.read(str(path), dtype="float64")
        return sy.to_pcm16(x), sr
    return sy.read_wav(path)


# ---------------------------------------------------------------- checks

def analyse(pcm, loop, kind="sfx"):
    x = pcm.astype(float) / 32768.0
    d = np.abs(np.diff(x))
    res = {
        "len": len(x) / sy.SR,
        "peak_db": sy.db(sy.peak(x)),
        "rms_db": sy.db(sy.rms(x)),
        "clipped": int(np.sum(np.abs(pcm.astype(int)) >= 32767)),
        "nan": bool(np.isnan(x).any()),
        "p999": float(np.percentile(d, 99.9)) if len(d) else 0.0,
        "phone": review.phone_share(x),
    }
    if loop:
        jump = abs(x[-1] - x[0])
        k = sy.nsamp(0.015 if kind == "music" else 0.05)   # music: before the downbeat 25 ms in; beds: a longer view
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
    # a bed's layer is sparse (a bird call may sit on one side of the seam): its level step is looser, its jump is not
    if loop and abs(a["seam_rms_db"]) > (6.0 if kind == "music" else 16.0):
        errs.append(f"seam level step {a['seam_rms_db']:+.1f} dB")
    if is_new(aid) and a.get("phone", 0.0) < PHONE_MIN_DB:
        errs.append(f"lives in the sub-bass: {a['phone']:.1f} dB above 300 Hz (a phone plays little under it)")
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

def write_manifest(levels, meta):
    """levels: (kind, id) -> (volume_db, len_s) of the assets just rendered; meta: music id -> its grid. Ids not rebuilt
    keep their entries from the manifest on disk."""
    old = {}
    rooms = {}
    if MANIFEST.exists():
        try:
            old = json.loads(MANIFEST.read_text(encoding="utf-8"))
            rooms = old.get("rooms", {}) or {}
        except (ValueError, OSError):
            old = {}
    stems = {sid: spec[0] for sid, spec in music_adaptive.STEMS.items()}

    def entry(kind, k, default_db):
        prev = old.get(kind, {}).get(k, {})
        e = {"file": f"res://art/audio/{kind}/{k}{ext_for(kind, k)}"}
        vol, secs = levels.get((kind, k), (prev.get("volume_db", default_db), prev.get("len_s")))
        e["volume_db"] = vol
        if secs is not None:
            e["len_s"] = secs
        if is_loop(kind, k):
            e["loop"] = True
        if kind == "music":
            e.update(meta.get(k) or {x: prev[x] for x in ("bpm", "bar_beats", "bars", "loop_s") if x in prev})
            if k in stems:
                e["stem_of"] = stems[k]
            stem = next((sid for sid, base in stems.items() if base == k), "")
            if stem:
                e["stem"] = stem
        return e

    body = {
        "schema_version": 2,
        "music": {k: entry("music", k, MUSIC_VOLUME_DB) for k in MUSIC},
        "sfx": {k: entry("sfx", k, SFX_VOLUME_DB) for k in SFX},
        "rooms": rooms,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(body, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")


def prune():
    """A full build removes the audio files (and their .import) of ids no longer registered."""
    for d, reg in ((MUSIC_DIR, MUSIC), (SFX_DIR, SFX)):
        for f in sorted(d.iterdir()):
            if f.suffix in (".wav", ".ogg") and f.stem not in reg:
                print(f"removed {f.relative_to(ROOT)} (no longer built)")
                f.unlink()
                imp = Path(str(f) + ".import")
                if imp.exists():
                    imp.unlink()


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*", help="asset ids to build (default: all)")
    ap.add_argument("--check", action="store_true", help="only analyse the WAV files on disk")
    ap.add_argument("--review", metavar="DIR", help="write spectrogram PNGs to DIR")
    ap.add_argument("--jobs", "-j", type=int, default=min(4, os.cpu_count() or 1))
    ap.add_argument("--verbose", "-v", action="store_true", help="print per-bus levels of music tracks")
    args = ap.parse_args(argv)

    import fnmatch   # an id may be a pattern: 'hit_*', 'step_grass_?'
    args.ids = [k for i in args.ids for k in ([i] if not any(c in i for c in "*?[") else
                                              fnmatch.filter(list(MUSIC) + list(SFX), i) or [i])]
    unknown = [i for i in args.ids if i not in MUSIC and i not in SFX]
    if unknown:
        ap.error("unknown ids: " + ", ".join(unknown))
    todo = [("music", k) for k in MUSIC if not args.ids or k in args.ids]
    todo += [("sfx", k) for k in SFX if not args.ids or k in args.ids]

    results = {}
    missing = 0
    if args.check:
        for kind, aid in todo:
            path = path_for(kind, aid)
            if not path.exists() and path_for(kind, aid, ".ogg").exists():
                path = path_for(kind, aid, ".ogg")
            if path.suffix == ".ogg" and soundfile is None:
                print(f"skip {path.relative_to(ROOT)}: decoding Ogg needs the soundfile module")
                continue
            if not path.exists():
                print(f"MISSING {path}")
                missing += 1
                continue
            pcm, sr = read_audio(path)
            assert sr == sy.SR, (path, sr)
            results[(kind, aid)] = (pcm, is_loop(kind, aid), {})
    else:
        MUSIC_DIR.mkdir(parents=True, exist_ok=True)
        SFX_DIR.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        if args.jobs > 1 and len(todo) > 1:
            with ProcessPoolExecutor(max_workers=args.jobs) as ex:
                out = list(ex.map(_job, todo))
        else:
            out = [_job(j) for j in todo]
        levels = {}
        meta = {}
        for kind, aid, pcm, loop, info in out:
            path = write_audio(kind, aid, pcm)
            if path.suffix == ".ogg":
                pcm, _ = read_audio(path)       # check what the game will play: the decoded Vorbis
            results[(kind, aid)] = (pcm, loop, info)
            x = pcm.astype(float) / 32768.0
            levels[(kind, aid)] = (MUSIC_VOLUME_DB if kind == "music" else volume_for(aid, x, loop), round(len(pcm) / sy.SR, 3))
            if "meta" in info:
                meta[aid] = info["meta"]
        write_manifest(levels, meta)
        if not args.ids:
            prune()
        print(f"rendered {len(out)} assets in {time.time() - t0:.1f}s -> {MANIFEST.relative_to(ROOT)}")

    failed = missing
    total_bytes = 0
    print(f"{'kind':5} {'id':22} {'len s':>6} {'peak':>6} {'rms':>6} {'phone':>6} {'seam':>8} {'p99.9':>7}  status")
    for (kind, aid), (pcm, loop, info) in results.items():
        a = analyse(pcm, loop, kind)
        errs = problems(kind, aid, a, loop)
        failed += bool(errs)
        total_bytes += path_for(kind, aid).stat().st_size if path_for(kind, aid).exists() else 0
        seam = a.get("seam", a.get("edge", 0.0))
        print(f"{kind:5} {aid:22} {a['len']:6.2f} {a['peak_db']:6.1f} {a['rms_db']:6.1f} {a['phone']:6.1f} {seam:8.4f} "
              f"{a['p999']:7.4f}  {'FAIL: ' + '; '.join(errs) if errs else 'ok'}"
              f"{'  loop' if loop else ''}")
    for sid, spec in music_adaptive.STEMS.items():
        a, b = results.get(("music", sid)), results.get(("music", spec[0]))
        if a and b and len(a[0]) != len(b[0]):
            print(f"FAIL: {sid} is {len(a[0])} samples, its track {spec[0]} {len(b[0])}: the stem would drift")
            failed += 1
    print(f"total {total_bytes / 1e6:.2f} MB on disk in {len(results)} files; {failed} failing")

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
            if kind == "music" or loop:
                review_music(rdir / f"{kind}_{aid}.png", aid, pcm)
            else:
                items.append((aid, pcm))
        if items:
            review_sfx(rdir / "sfx_sheet.png", items)
        print(f"review images -> {rdir}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
