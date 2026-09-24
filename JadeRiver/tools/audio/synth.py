"""Jade River audio synthesis toolkit (numpy only, deterministic).

Everything here renders mono float64 arrays at SR = 22050 Hz.

Design notes
* Filters are evaluated in the frequency domain (RBJ biquad responses applied to an
  FFT). With ``circular=True`` the filter treats the buffer as one period of a loop,
  so a filtered loop stays seamless.
* Karplus-Strong strings are solved in the frequency domain too: the delay line is
  exp(-jwD) with a fractional D, so every note is exactly in tune, and the loop filter
  is zero-phase, so partials stay harmonic. Pitch bends / vibrato are applied by
  resampling the rendered string.
* Randomness only comes from generators made by ``rng_for`` (seeded from names).
"""
from __future__ import annotations

import wave
import zlib

import numpy as np

SR = 22050
NYQ = SR / 2.0
TAU = 2.0 * np.pi
LN1000 = float(np.log(1000.0))
BASE_SEED = 7310  # change to re-roll every asset


# ---------------------------------------------------------------- basics

def rng_for(*keys):
    """Deterministic generator for a name path, e.g. rng_for("music", "title", "flute")."""
    text = "/".join(str(k) for k in keys)
    return np.random.default_rng([BASE_SEED, zlib.crc32(text.encode("utf-8"))])


def good_size(n):
    """Smallest 5-smooth integer >= n (a fast FFT length)."""
    n = max(1, int(n))
    best = 1 << (n - 1).bit_length()
    p5 = 1
    while p5 < best:
        p35 = p5
        while p35 < best:
            p = p35
            while p < n:
                p *= 2
            best = min(best, p)
            p35 *= 3
        p5 *= 5
    return best


def mtof(m):
    return 440.0 * 2.0 ** ((np.asarray(m, dtype=float) - 69.0) / 12.0)


def undb(d):
    return 10.0 ** (d / 20.0)


def db(x):
    return 20.0 * np.log10(max(float(x), 1e-12))


def rms(x):
    x = np.asarray(x, dtype=float)
    return float(np.sqrt(np.mean(x * x))) if len(x) else 0.0


def peak(x):
    return float(np.max(np.abs(x))) if len(x) else 0.0


def nsamp(sec):
    return max(1, int(round(sec * SR)))


def tvec(n):
    return np.arange(n) / SR


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def smooth(x, sec):
    """Centred moving average (cheap control-signal smoother)."""
    k = nsamp(sec)
    if k <= 1:
        return np.asarray(x, dtype=float)
    xp = np.pad(np.asarray(x, dtype=float), (k // 2, k - 1 - k // 2), mode="edge")
    c = np.cumsum(np.concatenate([[0.0], xp]))
    return (c[k:] - c[:-k]) / k


def fades(x, fin=0.002, fout=0.01):
    """Raised-cosine fade in/out so one-shots start and end at zero."""
    x = np.array(x, dtype=float)
    a = min(len(x) // 2, nsamp(fin)) if fin > 0 else 0
    b = min(len(x) // 2, nsamp(fout)) if fout > 0 else 0
    if a > 1:
        x[:a] *= np.sin(0.5 * np.pi * np.arange(a) / a) ** 2
    if b > 1:
        x[-b:] *= np.cos(0.5 * np.pi * np.arange(1, b + 1) / b) ** 2
    return x


def env_pts(n, pts):
    """Piecewise-linear envelope from [(seconds, value), ...]."""
    ts, vs = zip(*pts)
    return np.interp(tvec(n), ts, vs)


def decay(n, t60, attack=0.0):
    t = tvec(n)
    e = np.exp(-LN1000 * t / t60)
    if attack > 0:
        e = e * (1.0 - np.exp(-t / attack))
    return e


def fit(x, n):
    """Pad with zeros / truncate to n samples."""
    x = np.asarray(x, dtype=float)
    if len(x) >= n:
        return x[:n].copy()
    return np.concatenate([x, np.zeros(n - len(x))])


def place(dst, sig, start, gain=1.0):
    """Add sig into dst at sample index start (clipped at the ends, no wrap)."""
    s = int(start)
    a = max(0, -s)
    b = min(len(sig), len(dst) - s)
    if b > a:
        dst[s + a:s + b] += gain * np.asarray(sig[a:b])


def wrap_add(dst, sig, start, gain=1.0):
    """Add sig into a loop buffer at start, wrapping around the end."""
    L = len(dst)
    pos = int(start) % L
    sig = np.asarray(sig, dtype=float)
    i, n = 0, len(sig)
    while i < n:
        seg = min(n - i, L - pos)
        dst[pos:pos + seg] += gain * sig[i:i + seg]
        i += seg
        pos = 0


# ---------------------------------------------------------------- filters (frequency domain)

def _biquad(b0, b1, b2, a0, a1, a2):
    def resp(f):
        z = np.exp(-1j * TAU * np.asarray(f, dtype=float) / SR)
        return (b0 + b1 * z + b2 * z * z) / (a0 + a1 * z + a2 * z * z)
    return resp


def _w0(fc):
    return TAU * min(max(float(fc), 1.0), 0.48 * SR) / SR


def lowpass(fc, q=0.7071):
    w = _w0(fc)
    c, al = np.cos(w), np.sin(w) / (2 * q)
    return _biquad((1 - c) / 2, 1 - c, (1 - c) / 2, 1 + al, -2 * c, 1 - al)


def highpass(fc, q=0.7071):
    w = _w0(fc)
    c, al = np.cos(w), np.sin(w) / (2 * q)
    return _biquad((1 + c) / 2, -(1 + c), (1 + c) / 2, 1 + al, -2 * c, 1 - al)


def bandpass(fc, q=1.0):
    """Band-pass with 0 dB gain at fc."""
    w = _w0(fc)
    c, al = np.cos(w), np.sin(w) / (2 * q)
    return _biquad(al, 0.0, -al, 1 + al, -2 * c, 1 - al)


def peaking(fc, q, gain_db):
    A = 10 ** (gain_db / 40.0)
    w = _w0(fc)
    c, al = np.cos(w), np.sin(w) / (2 * q)
    return _biquad(1 + al * A, -2 * c, 1 - al * A, 1 + al / A, -2 * c, 1 - al / A)


def lowshelf(fc, gain_db, s=1.0):
    A = 10 ** (gain_db / 40.0)
    w = _w0(fc)
    c, sn = np.cos(w), np.sin(w)
    al = sn / 2 * np.sqrt((A + 1 / A) * (1 / s - 1) + 2)
    sa = 2 * np.sqrt(A) * al
    return _biquad(A * ((A + 1) - (A - 1) * c + sa), 2 * A * ((A - 1) - (A + 1) * c),
                   A * ((A + 1) - (A - 1) * c - sa), (A + 1) + (A - 1) * c + sa,
                   -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - sa)


def highshelf(fc, gain_db, s=1.0):
    A = 10 ** (gain_db / 40.0)
    w = _w0(fc)
    c, sn = np.cos(w), np.sin(w)
    al = sn / 2 * np.sqrt((A + 1 / A) * (1 / s - 1) + 2)
    sa = 2 * np.sqrt(A) * al
    return _biquad(A * ((A + 1) + (A - 1) * c + sa), -2 * A * ((A - 1) + (A + 1) * c),
                   A * ((A + 1) + (A - 1) * c - sa), (A + 1) - (A - 1) * c + sa,
                   2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - sa)


def tilt(db_per_oct, ref=1000.0):
    """Magnitude-only spectral tilt (e.g. -3 = pink)."""
    def resp(f):
        return (np.maximum(np.asarray(f, dtype=float), 20.0) / ref) ** (db_per_oct / 6.0206)
    return resp


def gauss_band(fc, width_oct):
    """Magnitude-only band, Gaussian in log-frequency."""
    def resp(f):
        lf = np.log2(np.maximum(np.asarray(f, dtype=float), 10.0) / fc)
        return np.exp(-0.5 * (lf / width_oct) ** 2)
    return resp


def a_weight(f):
    """IEC A-weighting magnitude (for level meters)."""
    f2 = np.asarray(f, dtype=float) ** 2
    ra = (12194.0 ** 2 * f2 ** 2) / ((f2 + 20.6 ** 2) * np.sqrt((f2 + 107.7 ** 2) * (f2 + 737.9 ** 2))
                                      * (f2 + 12194.0 ** 2))
    return ra * 10 ** (2.0 / 20.0)


def rms_a(x):
    """A-weighted RMS (treats x as a loop)."""
    return rms(filt(x, a_weight, circular=True))


def filt(x, *resps, circular=False, tail=0.0):
    """Filter x by the product of frequency responses.

    circular=True treats x as one loop period (output length == input length).
    Otherwise x is zero padded; ``tail`` seconds of ring-out are kept.
    """
    x = np.asarray(x, dtype=float)
    n = len(x)
    extra = nsamp(tail) if tail > 0 else 0
    N = n if circular else good_size(n + extra + nsamp(0.3))
    X = np.fft.rfft(x, N)
    f = np.fft.rfftfreq(N, 1.0 / SR)
    for r in resps:
        X = X * r(f)
    y = np.fft.irfft(X, N)
    return y if circular else y[:n + extra]


def stft_shape(x, mag_fn, win=1024, hop=256, circular=False):
    """Time-varying filter: multiply every STFT frame by mag_fn(times[:,None], freqs[None,:])."""
    x = np.asarray(x, dtype=float)
    n0 = len(x)
    pad = 0 if circular else win
    if pad:
        x = np.concatenate([np.zeros(pad), x, np.zeros(pad)])
    n = len(x)
    w = np.sin(np.pi * (np.arange(win) + 0.5) / win) ** 2
    nfr = -(-n // hop)
    starts = np.arange(nfr) * hop - win // 2
    idx = (starts[:, None] + np.arange(win)[None, :]) % n
    spec = np.fft.rfft(x[idx] * w, axis=1)
    times = (starts + win // 2 - pad) / SR
    freqs = np.fft.rfftfreq(win, 1.0 / SR)
    spec *= mag_fn(times[:, None], freqs[None, :])
    frames = np.fft.irfft(spec, win, axis=1) * w
    flat = idx.ravel()
    y = np.bincount(flat, weights=frames.ravel(), minlength=n)
    norm = np.bincount(flat, weights=np.tile(w * w, nfr), minlength=n)
    y /= np.maximum(norm, 1e-9)
    return y[pad:pad + n0] if pad else y


# ---------------------------------------------------------------- noise

def pnoise(n, rng, *resps):
    """Periodic (loopable) noise of exactly n samples, spectrally shaped, unit RMS."""
    k = n // 2 + 1
    X = rng.standard_normal(k) + 1j * rng.standard_normal(k)
    X[0] = 0.0
    f = np.fft.rfftfreq(n, 1.0 / SR)
    for r in resps:
        X = X * np.abs(r(f))
    y = np.fft.irfft(X, n)
    return y / max(rms(y), 1e-12)


def noise(n, rng, *resps):
    """One-shot shaped noise (not periodic), unit RMS."""
    y = rng.standard_normal(n)
    if resps:
        y = filt(y, *resps)
    return y / max(rms(y), 1e-12)


def slow_noise(n, rng, rate=2.0):
    """Smooth random control signal, unit RMS, periodic over n samples."""
    return pnoise(n, rng, lowpass(rate, 0.5))


def qf(f, T):
    """Quantise a frequency to a whole number of cycles per loop of T seconds."""
    return max(1.0, round(float(f) * T)) / T


# ---------------------------------------------------------------- modal / percussion

def modal(partials, dur, rng=None, attack=0.0015, pitch=(0.0, 0.0), tau=0.3):
    """Sum of exponentially decaying sines.

    partials: iterable of (freq, amp, t60[, attack]). pitch=(start_cents, end_cents): a
    global pitch glide that moves from start to end with time constant tau.
    """
    n = nsamp(dur)
    t = tvec(n)
    if pitch[0] or pitch[1]:
        cents = pitch[1] + (pitch[0] - pitch[1]) * np.exp(-t / tau)
        ratio = 2.0 ** (cents / 1200.0)
        tw = np.concatenate([[0.0], np.cumsum(ratio[:-1])]) / SR
        rmax = float(ratio.max())
    else:
        tw, rmax = t, 1.0
    out = np.zeros(n)
    for p in partials:
        f, a, t60 = float(p[0]), float(p[1]), float(p[2])
        att = float(p[3]) if len(p) > 3 else attack
        if a == 0 or f <= 0 or f * rmax >= 0.47 * SR:
            continue
        ph = rng.uniform(0, TAU) if rng is not None else 0.0
        e = np.exp(-LN1000 * t / t60)
        if att > 0:
            e = e * (1.0 - np.exp(-t / att))
        out += a * e * np.sin(TAU * f * tw + ph)
    return out


def doublets(partials, rng, beat=(0.4, 2.0), balance=0.64):
    """Split each partial into a slightly detuned, unequal pair (gentle beating, warmth)."""
    out = []
    for p in partials:
        b = rng.uniform(*beat)
        out.append((p[0] - b / 2, p[1] * balance) + tuple(p[2:]))
        out.append((p[0] + b / 2, p[1] * (1.0 - balance)) + tuple(p[2:]))
    return out


def click(rng, dur=0.002, fc=3000.0, q=0.8):
    n = nsamp(dur) + 2
    x = rng.standard_normal(n) * np.exp(-np.arange(n) / max(1.0, n / 4.0))
    y = filt(x, bandpass(fc, q), tail=0.004)
    return y / max(peak(y), 1e-9)


def membrane(f0, rng, t60=0.5, drop=0.5, drop_tau=0.03, noise_amt=0.3, noise_fc=1500.0,
             click_amt=0.1, modes=((1.0, 1.0, 1.0), (1.59, 0.42, 0.6), (2.14, 0.22, 0.45),
                                   (2.65, 0.12, 0.35), (3.16, 0.06, 0.25)), dur=None):
    """Drum head: pitched modes with a downward pitch glide + beater noise."""
    dur = dur or t60 * 1.05 + 0.02
    partials = [(f0 * r * (1 + rng.normal(0, 0.004)), a, t60 * d, 0.0008) for r, a, d in modes]
    cents = 1200.0 * np.log2(1.0 + drop)
    y = modal(partials, dur, rng, pitch=(cents, 0.0), tau=drop_tau)
    y /= max(peak(y), 1e-9)
    n = len(y)
    if noise_amt > 0:
        k = min(n, nsamp(0.06))
        nz = rng.standard_normal(k) * np.exp(-np.arange(k) / (0.009 * SR))
        nz = filt(nz, lowpass(noise_fc, 0.7))[:k]
        y[:k] += noise_amt * nz / max(peak(nz), 1e-9)
    if click_amt > 0:
        c = click(rng, 0.0015, 4000.0, 0.7)
        y[:len(c)] += click_amt * c[:n]
    return fades(y, 0.0005, 0.02)


def woodblock(f0, rng, t60=0.12, click_amt=0.35, bright=1.0,
              modes=((1.0, 1.0, 1.0), (1.63, 0.33, 0.55), (2.71, 0.16, 0.35), (4.07, 0.06, 0.2))):
    """Hollow wooden block (muyu / bangzi / bamboo)."""
    partials = [(f0 * r * (1 + rng.normal(0, 0.004)), a * (bright ** k), t60 * d, 0.0004)
                for k, (r, a, d) in enumerate(modes)]
    y = modal(partials, t60 * 1.3 + 0.02, rng, pitch=(35.0, 0.0), tau=0.012)
    y /= max(peak(y), 1e-9)
    if click_amt > 0:
        c = click(rng, 0.0012, min(4.5 * f0, 7000.0), 0.9)
        y[:len(c)] += click_amt * c[:len(y)]
    return fades(y, 0.0003, 0.01)


def cymbal(rng, dur=2.0, t60=1.6, fmin=320.0, fmax=9500.0, count=60, noise_amt=0.5,
           attack=0.0015, hp=900.0, tilt_db=-1.5):
    """Chinese cymbal (bo / nao): dense inharmonic partials + noise wash."""
    fs = np.exp(rng.uniform(np.log(fmin), np.log(fmax), count))
    partials = []
    for f in fs:
        a = rng.uniform(0.35, 1.0) * (f / 1000.0) ** (tilt_db / 6.0)
        d = t60 * rng.uniform(0.35, 1.0) * (1000.0 / f) ** 0.3
        partials.append((f, a, d, attack))
    y = modal(partials, dur, rng)
    y /= max(peak(y), 1e-9)
    n = len(y)
    nz = rng.standard_normal(n) * decay(n, t60 * 0.55, attack)
    nz = filt(nz, highpass(hp), lowpass(8500))[:n]
    y += noise_amt * nz / max(peak(nz), 1e-9)
    y = filt(y, highpass(hp * 0.6))[:n]
    return fades(y / max(peak(y), 1e-9), 0.0005, 0.05)


GONG_RATIOS = (1.0, 1.47, 1.98, 2.33, 2.87, 3.39, 3.94, 4.41, 5.02, 5.66, 6.37, 7.1, 7.83, 8.6)


def gong(f0, rng, dur=4.0, pitch=(0.0, -60.0), tau=0.6, bloom=0.35, bright=0.72, count=14,
         thump=0.5):
    """Tam-tam / opera gong: inharmonic doublets whose upper partials bloom late."""
    partials = []
    for k, r in enumerate(GONG_RATIOS[:count]):
        f = f0 * r * (1 + rng.normal(0, 0.006))
        a = (bright ** k) * rng.uniform(0.7, 1.0)
        t60 = dur * 1.1 / (1.0 + 0.25 * k)
        att = 0.004 + bloom * k / count
        partials.append((f, a, t60, att))
    y = modal(doublets(partials, rng, (0.3, 1.6)), dur, rng, pitch=pitch, tau=tau)
    y /= max(peak(y), 1e-9)
    n = len(y)
    if thump > 0:
        k = min(n, nsamp(0.08))
        th = rng.standard_normal(k) * np.exp(-np.arange(k) / (0.015 * SR))
        th = filt(th, lowpass(min(4 * f0, 900.0)))[:k]
        y[:k] += thump * th / max(peak(th), 1e-9)
    return fades(y / max(peak(y), 1e-9), 0.0008, 0.3)


BELL_SPECS = {
    # (ratio, amp, t60 fraction)
    "temple": ((0.5, 0.5, 1.0), (1.0, 1.0, 0.75), (1.19, 0.45, 0.55), (1.5, 0.3, 0.45),
               (2.0, 0.45, 0.4), (2.52, 0.22, 0.3), (2.66, 0.18, 0.27), (3.01, 0.15, 0.22),
               (4.17, 0.09, 0.15), (5.43, 0.05, 0.1)),
    "small": ((1.0, 1.0, 1.0), (2.32, 0.42, 0.55), (2.93, 0.3, 0.45), (4.07, 0.18, 0.3),
              (5.28, 0.1, 0.2), (6.41, 0.05, 0.14)),
    "bianzhong": ((1.0, 1.0, 1.0), (1.21, 0.5, 0.8), (2.03, 0.45, 0.5), (2.71, 0.3, 0.35),
                  (3.52, 0.18, 0.25), (4.63, 0.1, 0.18), (5.9, 0.05, 0.12)),
}


def bell(f0, rng, dur=3.0, kind="small", strike=0.25):
    spec = BELL_SPECS[kind]
    partials = [(f0 * r * (1 + rng.normal(0, 0.002)), a, dur * d, 0.001) for r, a, d in spec]
    y = modal(doublets(partials, rng, (0.5, 2.2)), dur, rng)
    y /= max(peak(y), 1e-9)
    if strike > 0:
        c = click(rng, 0.002, min(3.2 * f0, 6500.0), 1.2)
        y[:len(c)] += strike * c[:len(y)]
    return fades(y / max(peak(y), 1e-9), 0.0005, 0.15)


def bowl(f0, rng, dur=6.0, strike=0.12):
    """Singing bowl: long beating doublets."""
    spec = ((1.0, 1.0, 1.0), (2.71, 0.5, 0.62), (5.15, 0.2, 0.36), (8.3, 0.07, 0.2))
    partials = [(f0 * r * (1 + rng.normal(0, 0.002)), a, dur * d, 0.004) for r, a, d in spec]
    y = modal(doublets(partials, rng, (0.9, 2.6), balance=0.72), dur, rng)
    y /= max(peak(y), 1e-9)
    if strike > 0:
        k = nsamp(0.03)
        th = rng.standard_normal(k) * np.exp(-np.arange(k) / (0.004 * SR))
        th = filt(th, bandpass(f0 * 2.0, 0.7))[:k]
        y[:k] += strike * th / max(peak(th), 1e-9)
    return fades(y / max(peak(y), 1e-9), 0.001, 0.3)


def chime(f0, rng, dur=1.0, strike=0.2):
    """Jade / glass bar: free-bar mode ratios."""
    spec = ((1.0, 1.0, 1.0), (2.756, 0.38, 0.45), (5.404, 0.14, 0.25), (8.933, 0.05, 0.12))
    partials = [(f0 * r, a, dur * d, 0.0008) for r, a, d in spec]
    y = modal(doublets(partials, rng, (0.8, 3.0)), dur, rng)
    y /= max(peak(y), 1e-9)
    if strike > 0:
        c = click(rng, 0.0015, min(4.0 * f0, 7000.0), 1.5)
        y[:len(c)] += strike * c[:len(y)]
    return fades(y / max(peak(y), 1e-9), 0.0004, 0.08)


def bubble(rng, f0, tau=0.02, rise=0.6):
    """Minnaert bubble / water drop: short rising sine chirp."""
    dur = tau * 6.0
    n = nsamp(dur)
    t = tvec(n)
    f = f0 * (1.0 + rise * t / dur)
    ph = TAU * np.cumsum(f) / SR
    env = (1.0 - np.exp(-t / 0.0012)) * np.exp(-t / tau)
    return fades(env * np.sin(ph), 0.0, 0.004)


def bird(rng, f0=3400.0, level=1.0):
    """A small bird call: 2-4 quick FM chirps."""
    out = []
    for _ in range(int(rng.integers(2, 5))):
        d = rng.uniform(0.045, 0.11)
        n = nsamp(d)
        u = np.linspace(0, 1, n)
        shape = rng.integers(3)
        if shape == 0:
            f = f0 * (1.25 - 0.45 * u)
        elif shape == 1:
            f = f0 * (0.85 + 0.35 * np.sin(np.pi * u))
        else:
            f = f0 * (0.9 + 0.3 * u + 0.05 * np.sin(TAU * 18 * u * d))
        ph = TAU * np.cumsum(f) / SR
        env = np.sin(np.pi * u) ** 2
        out.append(env * (np.sin(ph) + 0.12 * np.sin(2 * ph)))
        out.append(np.zeros(nsamp(rng.uniform(0.03, 0.08))))
    return level * np.concatenate(out)


# ---------------------------------------------------------------- strings (Karplus-Strong)

def pluck(freq, rng, ring=2.5, t60=3.0, t60_hi=0.3, bright=0.6, pick=0.13, glide=7.0,
          glide_tau=0.05, bend=None, vib=None, hits=None, nail=0.05, release=0.08, vel=0.8):
    """Plucked string: Karplus-Strong solved in the frequency domain.

    t60: decay of the fundamental; t60_hi: decay near 3 kHz (upper partials die faster).
    bright: excitation brightness 0..1; pick: pluck position (comb); glide: cents sharp
    at the attack (tension settle); bend(t)->cents; vib=(rate, depth_cents, delay);
    hits=[(seconds, amp), ...] re-excites the same string (pipa tremolo).
    Returns a peak-normalised signal of ``ring`` seconds.
    """
    D = SR / float(freq)
    n_out = nsamp(ring)
    hits = hits or [(0.0, 1.0)]
    span = int(n_out * 1.16) + 64
    M = good_size(max(span, nsamp(min(t60, 9.0) + 0.3)) + int(D) + 32)
    f = np.fft.rfftfreq(M, 1.0 / SR)
    wv = TAU * f / SR
    L0 = max(2, int(round(D)))
    exc = np.zeros(M)
    for th, ah in hits:
        s0 = int(round(th * SR))
        if s0 + L0 >= M:
            continue
        burst = rng.uniform(-1.0, 1.0, L0)
        exc[s0:s0 + L0] += ah * (burst - burst.mean())
    E = np.fft.rfft(exc)
    b = float(np.clip(bright + 0.25 * (vel - 0.7), 0.05, 1.0))
    fc = 700.0 * (14.0 ** b)
    E *= 1.0 / np.sqrt(1.0 + (f / fc) ** 4)
    if pick > 0:
        E *= 1.0 - np.exp(-1j * wv * pick * D)
    a0 = LN1000 / t60
    alpha = a0 + (LN1000 / t60_hi - a0) * (f / 3000.0) ** 2
    g = np.exp(-alpha * D / SR)
    y = np.fft.irfft(E / (1.0 - g * np.exp(-1j * wv * D)), M)
    t = tvec(n_out)
    cents = glide * np.exp(-t / glide_tau)
    if bend is not None:
        cents = cents + bend(t)
    if vib is not None:
        rate, depth, delay = vib
        cents = cents + depth * smoothstep((t - delay) / 0.35) * np.sin(TAU * rate * t)
    ratio = 2.0 ** (cents / 1200.0)
    pos = np.concatenate([[0.0], np.cumsum(ratio[:-1])])
    out = np.interp(pos, np.arange(M), y)
    out /= max(peak(out), 1e-9)
    if nail > 0:
        c = click(rng, 0.0025, 3500.0, 0.6)
        out[:len(c)] += nail * c[:n_out]
    return fades(out, 0.0005, release)


def zheng_params(freq):
    """Guzheng: long ringing strings, warm nail attack."""
    return dict(t60=float(np.clip(6.5 * (110.0 / freq) ** 0.5, 1.4, 7.0)),
                t60_hi=float(np.clip(0.45 * (110.0 / freq) ** 0.25, 0.12, 0.6)),
                bright=0.58, pick=0.13, glide=7.0, nail=0.05)


def pipa_params(freq):
    """Pipa: brighter, shorter, twangier."""
    return dict(t60=float(np.clip(2.4 * (110.0 / freq) ** 0.5, 0.6, 2.6)),
                t60_hi=float(np.clip(0.2 * (110.0 / freq) ** 0.2, 0.07, 0.28)),
                bright=0.74, pick=0.085, glide=12.0, nail=0.08)


# body resonances applied on the instrument bus
ZHENG_BODY = (peaking(118, 1.6, 4.0), peaking(236, 2.4, 2.5), peaking(415, 3.0, 2.0),
              peaking(760, 3.0, 1.5), peaking(1350, 2.5, 1.2), highshelf(5200, -4.0),
              highpass(50, 0.7))
PIPA_BODY = (peaking(265, 2.0, 3.0), peaking(530, 3.0, 2.5), peaking(1120, 3.0, 2.5),
             peaking(2350, 2.5, 1.5), highshelf(6500, -3.5), highpass(80, 0.7))


def harmonic_tone(freq, rng, ring=3.0):
    """Guzheng natural harmonic: glassy octave tone."""
    partials = [(2 * freq, 1.0, ring * 0.9, 0.002), (4 * freq, 0.1, ring * 0.35, 0.002),
                (6 * freq, 0.03, ring * 0.2, 0.002)]
    y = modal(partials, ring, rng, pitch=(6.0, 0.0), tau=0.05)
    y /= max(peak(y), 1e-9)
    c = click(rng, 0.002, 3000.0, 0.7)
    y[:len(c)] += 0.04 * c
    return fades(y, 0.0, 0.1)


# ---------------------------------------------------------------- flute (dizi / xiao)

FLUTES = {
    "dizi": dict(harm=(1.0, 0.5, 0.3, 0.17, 0.11, 0.07, 0.045, 0.03), tilt=0.35, buzz=0.09,
                 breath=0.022, breath_fc=2800.0, airtone=0.06, attack=0.055, release=0.075,
                 scoop=45.0),
    "xiao": dict(harm=(1.0, 0.24, 0.1, 0.05, 0.025), tilt=0.5, buzz=0.0, breath=0.05,
                 breath_fc=1500.0, airtone=0.13, attack=0.09, release=0.11, scoop=60.0),
}


def flute(notes, rng, kind="dizi", vib_rate=5.2, vib_depth=20.0, porta=0.028, breath=1.0):
    """Breathy bamboo flute phrase.

    notes: [(t, dur, midi, vel, orn)], t in seconds from the phrase origin. orn keys:
    grace (semitones of an upper/lower grace note), scoop (bool), slur (bool, no tongue
    dip), vib (cents). Returns (signal, pre): place the signal at origin - pre.
    """
    P = FLUTES[kind]
    notes = sorted(notes, key=lambda x: x[0])
    pre, post = 0.12, 0.6
    t_end = max(x[0] + x[1] for x in notes) + post
    n = nsamp(t_end + pre)
    tt = tvec(n) - pre

    def ix(sec):
        return int(np.clip(round((sec + pre) * SR), 0, n))

    ev_t, ev_m = [], []
    for t0, d, m, v, o in notes:
        g = o.get("grace")
        if g:
            gd = min(0.075, d * 0.3)
            ev_t += [t0, t0 + gd]
            ev_m += [m + g, m]
        else:
            ev_t.append(t0)
            ev_m.append(m)
    ev_t = np.asarray(ev_t)
    ev_m = np.asarray(ev_m, dtype=float)
    k = np.clip(np.searchsorted(ev_t, tt, side="right") - 1, 0, len(ev_t) - 1)
    midi = smooth(ev_m[k], porta)
    cents = np.zeros(n)
    depth = np.zeros(n)
    amp = np.zeros(n)
    chiff = np.zeros(n)
    for i, (t0, d, m, v, o) in enumerate(notes):
        s, e = ix(t0), ix(t0 + d)
        nxt = notes[i + 1][0] if i + 1 < len(notes) else 1e9
        prv = notes[i - 1][0] + notes[i - 1][1] if i > 0 else -1e9
        after_rest = (t0 - prv) > 0.05
        legato = (nxt - (t0 + d)) < 0.05
        tl = tt[s:e] - t0
        if o.get("scoop", after_rest):
            cents[s:e] -= P["scoop"] * np.exp(-tl / 0.07)
        if d > 0.42:
            vd = o.get("vib", vib_depth)
            r_end = e if legato else ix(t0 + d + P["release"] * 2)
            tl2 = tt[s:r_end] - t0
            depth[s:r_end] = np.maximum(depth[s:r_end], vd * smoothstep((tl2 - 0.2) / max(0.3, 0.45 * d)))
        body = v * (0.84 + 0.16 * np.sin(np.pi * np.clip(tl / d, 0, 1)))
        if after_rest:
            body = body * smoothstep(tl / P["attack"])
        elif not o.get("slur"):
            body = body * (1.0 - 0.42 * np.exp(-tl / 0.022))
        if after_rest or not o.get("slur"):
            ce = ix(t0 + 0.05)
            chiff[s:ce] += np.exp(-(tt[s:ce] - t0) / 0.012) * v
        amp[s:e] = np.maximum(amp[s:e], body)
        if not legato and len(body):
            r1 = ix(t0 + d + P["release"] * 4)
            tl3 = tt[e:r1] - (t0 + d)
            amp[e:r1] = np.maximum(amp[e:r1], body[-1] * np.exp(-tl3 / P["release"]))
    amp = smooth(amp, 0.012)
    s1 = slow_noise(n, rng, 1.5)
    s2 = slow_noise(n, rng, 0.7)
    vph = TAU * np.cumsum(vib_rate * (1.0 + 0.05 * s1)) / SR
    cents = cents + depth * np.sin(vph) + 3.0 * s2
    fr = mtof(midi + cents / 100.0)
    ph = TAU * np.cumsum(fr) / SR
    a_eff = amp * (1.0 + 0.035 * (depth / max(vib_depth, 1.0)) * np.sin(vph + 0.6))
    fmax = float(fr.max())
    tone = np.zeros(n)
    phs = rng.uniform(0, TAU, 16)
    for kk, bk in enumerate(P["harm"], start=1):
        if kk * fmax > 0.46 * SR:
            break
        tone += bk * a_eff ** (1.0 + P["tilt"] * (kk - 1)) * np.sin(kk * ph + phs[kk])
    tone /= sum(P["harm"])
    if P["buzz"] > 0:
        nz = filt(rng.standard_normal(n), bandpass(140, 0.7))
        nz /= max(rms(nz), 1e-9)
        bz = np.zeros(n)
        for kk in range(4, 13):
            if kk * fmax > 0.46 * SR:
                break
            bz += np.sin(kk * ph + phs[kk]) / kk
        tone += P["buzz"] * amp ** 2 * bz * (0.6 + 0.4 * np.tanh(nz))
    air = filt(rng.standard_normal(n), lowpass(160, 0.7))
    air /= max(rms(air), 1e-9)
    tone += P["airtone"] * amp * air * np.sin(ph)
    br = filt(rng.standard_normal(n), bandpass(P["breath_fc"], 0.55), highpass(450))
    br /= max(rms(br), 1e-9)
    tone += breath * P["breath"] * br * (amp ** 0.7 + 1.2 * chiff)
    return tone, pre


# ---------------------------------------------------------------- pads / textures

TRI = (1.0, 0.0, 1 / 9.0, 0.0, 1 / 25.0)
SOFT = (1.0, 0.18, 0.08, 0.03)
SINE = (1.0,)


def drone(n, T, rng, voices, harm=SOFT, swell=(1, 0.4), detune=3.0, beat=True):
    """Periodic drone of n samples (T seconds): every partial has whole cycles per loop.

    voices: [(freq, amp)]. swell=(cycles_per_loop, depth).
    """
    t = tvec(n)
    out = np.zeros(n)
    for f, a in voices:
        v = np.zeros(n)
        copies = ((0.0, 1.0), (detune, 0.6)) if beat else ((0.0, 1.0),)
        for det, ca in copies:
            fb = qf(f * 2 ** (det / 1200.0), T)
            p0 = rng.uniform(0, TAU)
            for k, hk in enumerate(harm, start=1):
                if hk == 0:
                    continue
                if fb * k > 0.45 * SR:
                    break
                v += ca * hk * np.sin(TAU * fb * k * t + p0 * k)
        c, dpt = swell
        sw = 1.0 - dpt * (0.5 - 0.5 * np.cos(TAU * c * t / T + rng.uniform(0, TAU)))
        out += a * v * sw
    return out / max(rms(out), 1e-9)


def periodic_lfo(t, T, rng, cycles=(1, 2, 3, 5)):
    """Smooth 0..1 modulator, periodic over T, mixing whole-cycle sines."""
    amps = rng.uniform(0.4, 1.0, len(cycles))
    phs = rng.uniform(0, TAU, len(cycles))
    g = sum(a * (0.5 + 0.5 * np.sin(TAU * c * t / T + p)) for a, c, p in zip(amps, cycles, phs))
    return g / amps.sum()


def wind(n, T, rng, base=380.0, spread=900.0, width=0.85, cycles=(1, 2, 3, 5), floor=0.2,
         tilt_db=-2.0, whistle=0.0):
    """Loopable wind: noise through a moving band whose level and pitch follow the gusts."""
    x = pnoise(n, rng)
    amps = rng.uniform(0.4, 1.0, len(cycles))
    phs = rng.uniform(0, TAU, len(cycles))
    wph = rng.uniform(0, TAU, 2)

    def mag(t, f):
        g = sum(a * (0.5 + 0.5 * np.sin(TAU * c * t / T + p)) for a, c, p in zip(amps, cycles, phs))
        g = (g / amps.sum()) ** 1.6
        fc = base + spread * g
        band = np.exp(-0.5 * (np.log2(np.maximum(f, 20.0) / fc) / width) ** 2)
        m = (floor + (1.0 - floor) * g) * band * (np.maximum(f, 60.0) / 1000.0) ** (tilt_db / 6.02)
        if whistle > 0:
            fw = 650.0 + 450.0 * (0.5 + 0.5 * np.sin(TAU * 2 * t / T + wph[0]))
            m = m + whistle * g ** 2 * np.exp(-0.5 * ((f - fw) / 35.0) ** 2)
        return m

    y = stft_shape(x, mag, circular=True)
    return y / max(rms(y), 1e-9)


def stream(n, T, rng, density=40.0, fmin=450.0, fmax=2600.0, bed=0.6, bub=1.0, tau=(0.006, 0.028)):
    """Loopable brook: filtered noise bed + many small wrapped bubbles."""
    t = tvec(n)
    bedn = pnoise(n, rng, bandpass(850, 0.45), tilt(-1.5))
    bedn *= 1.0 + 0.3 * np.sin(TAU * 2 * t / T + rng.uniform(0, TAU)) \
        + 0.15 * np.sin(TAU * 5 * t / T + rng.uniform(0, TAU))
    bubs = np.zeros(n)
    for _ in range(int(density * T)):
        f0 = float(np.exp(rng.uniform(np.log(fmin), np.log(fmax))))
        b = bubble(rng, f0, tau=rng.uniform(*tau), rise=rng.uniform(0.3, 1.2))
        wrap_add(bubs, b, int(rng.uniform(0, n)), float(rng.lognormal(0, 0.5)) * (700.0 / f0) ** 0.3)
    bubs /= max(rms(bubs), 1e-9)
    y = bed * bedn + bub * bubs
    return y / max(rms(y), 1e-9)


def crickets(n, T, rng, count=3, fbase=4300.0):
    """Loopable crickets: pulse-train chirps on a 4-5 kHz carrier."""
    out = np.zeros(n)
    for _ in range(count):
        fc = fbase * rng.uniform(0.9, 1.15)
        pr = rng.uniform(26.0, 38.0)
        pulses = int(rng.integers(3, 6))
        pl = 1.0 / pr
        m = nsamp(pulses * pl)
        tt = tvec(m)
        ph = (tt % pl) / pl
        penv = np.where(ph < 0.6, np.sin(np.pi * ph / 0.6) ** 2, 0.0)
        ch = penv * (np.sin(TAU * fc * tt) + 0.15 * np.sin(TAU * 2 * fc * tt))
        per = T / max(1, int(round(T / rng.uniform(0.5, 0.95))))
        lvl = rng.uniform(0.35, 1.0)
        off = rng.uniform(0, per)
        k = 0
        while k * per < T:
            if rng.random() > 0.12:
                wrap_add(out, ch, nsamp(off + k * per + rng.normal(0, 0.008)), lvl * rng.uniform(0.8, 1.1))
            k += 1
    return out / max(rms(out), 1e-9)


# ---------------------------------------------------------------- reverb / mastering

def reverb_ir(rng, t60=2.0, predelay=0.02, hf=0.45, lf=1.1, er=0.3):
    """Synthetic room: band-split decaying noise + a few early reflections, unit energy."""
    n = nsamp(predelay + t60 * 1.05)
    t = tvec(n)
    nz = rng.standard_normal(n)
    lo = filt(nz, lowpass(350), circular=True)
    hi = filt(nz, highpass(3200), circular=True)
    mid = nz - lo - hi
    tp = np.maximum(t - predelay, 0.0)

    def env(T):
        return np.exp(-LN1000 * tp / T)

    ir = lo * env(t60 * lf) + mid * env(t60) + hi * env(t60 * hf)
    ir *= smoothstep((t - predelay) / 0.035)
    for _ in range(7):
        d = predelay * 0.4 + rng.uniform(0.004, 0.06)
        i = nsamp(d)
        if i < n:
            ir[i] += er * rng.choice([-1.0, 1.0]) * rng.uniform(0.4, 1.0) * np.sqrt(n) / 60.0
    return ir / np.sqrt(np.sum(ir * ir))


def convolve(x, ir, circular=False):
    x = np.asarray(x, dtype=float)
    if circular:
        n = len(x)
        h = np.zeros(n)
        m = min(n, len(ir))
        h[:m] = ir[:m]
        return np.fft.irfft(np.fft.rfft(x) * np.fft.rfft(h), n)
    N = good_size(len(x) + len(ir))
    y = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)
    return y[:len(x) + len(ir) - 1]


def add_reverb(x, rng, t60=1.2, wet=0.25, predelay=0.015, hf=0.45, keep=None):
    """One-shot reverb (linear). keep: output length in samples (default input + tail)."""
    ir = reverb_ir(rng, t60=t60, predelay=predelay, hf=hf)
    y = convolve(x, ir)
    out = np.zeros(len(y))
    out[:len(x)] += x
    out += wet * y
    if keep is not None:
        out = fit(out, keep)
    return out


def limit(x, ceiling=undb(-1.0), block=256, circular=True):
    """Block-wise brickwall gain (never exceeds ceiling); circular keeps loops seamless."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    a = np.abs(x)
    nb = -(-n // block)
    padn = nb * block - n
    ap = np.concatenate([a, a[:padn] if circular else np.zeros(padn)])
    pk = ap.reshape(nb, block).max(axis=1)
    g = np.minimum(1.0, ceiling / np.maximum(pk, 1e-12))
    if circular:
        gm = np.minimum(g, np.minimum(np.roll(g, 1), np.roll(g, -1)))
    else:
        gp = np.concatenate([[1.0], g, [1.0]])
        gm = np.minimum(np.minimum(gp[:-2], gp[1:-1]), gp[2:])
    centers = (np.arange(nb) + 0.5) * block
    if circular:
        xs = np.concatenate([[centers[-1] - nb * block], centers, [centers[0] + nb * block]])
        gs = np.concatenate([[gm[-1]], gm, [gm[0]]])
    else:
        xs = np.concatenate([[0.0], centers, [nb * block]])
        gs = np.concatenate([[gm[0]], gm, [gm[-1]]])
    gain = np.interp(np.arange(n), xs, gs)
    return x * gain


def to_pcm16(x):
    x = np.nan_to_num(np.asarray(x, dtype=float))
    return np.clip(np.round(x * 32767.0), -32768, 32767).astype("<i2")


def write_wav(path, pcm):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(np.asarray(pcm, dtype="<i2").tobytes())


def read_wav(path):
    with wave.open(str(path), "rb") as w:
        assert w.getnchannels() == 1 and w.getsampwidth() == 2, path
        sr = w.getframerate()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    return data, sr
