"""Jade River music loops.

Every track is a function registered with @music(id) that builds a Track: a loop buffer
of whole bars into which notes are wrap-added (tails ring into the loop start), plus
circular bus effects and a circular reverb, so the finished loop joins seamlessly.

Melodies are generated from seeded random walks on the pentatonic scale
(gong-shang-jue-zhi-yu) with phrase structure A A' B A'' (question / answer), so
they are original to this project.
"""
from __future__ import annotations

import numpy as np

from synth import (SR, TAU, lowshelf, TRI, SOFT, ZHENG_BODY, PIPA_BODY, bell, bird, bowl, bubble, chime,
                   crickets, cymbal, db, drone, filt, flute, gong, harmonic_tone, highpass,
                   highshelf, limit, lowpass, membrane, mtof, nsamp, peak, pipa_params, pluck,
                   pnoise, reverb_ir, convolve, rms, rms_a, rng_for, smoothstep, stream, tvec, undb,
                   wind, woodblock, wrap_add, zheng_params, fades)

MUSIC = {}


def music(tid):
    def deco(fn):
        MUSIC[tid] = fn
        return fn
    return deco


# ---------------------------------------------------------------- scale / melody

PENTA = (0, 2, 4, 7, 9)


class Scale:
    """Pentatonic scale. gong: MIDI of the gong degree; mode: tonic degree (0 gong .. 4 yu).

    sc(i) is the MIDI note i pentatonic steps above the tonic (negative = below).
    """

    def __init__(self, gong, mode=0):
        self.gong, self.mode = int(gong), int(mode)

    def __call__(self, i):
        j = int(i) + self.mode
        return self.gong + 12 * (j // 5) + PENTA[j % 5]


# phrase rhythms (beats, negative = rest); every template fills two bars
R_SLOW = [[3, 1, 2, 2], [2, 1, 1, 4], [1.5, 0.5, 2, 4], [4, 1, 1, 2], [2, 2, 1, 1, 2],
          [3, 1, 3, -1], [1, 1, 2, 3, -1], [2, 1, 1, 3, -1]]
R_MID = [[1, 0.5, 0.5, 1, 1, 2, 2], [1.5, 0.5, 1, 1, 1, 1, 2], [0.5, 0.5, 1, 1, 1, 3, -1],
         [1, 1, 0.5, 0.5, 1, 2, 2], [2, 1, 1, 1.5, 0.5, 2], [1, 0.5, 0.5, 2, 1, 1, 2],
         [1.5, 0.5, 1.5, 0.5, 1, 1, 2]]
R_34 = [[1, 0.5, 0.5, 1, 3], [2, 1, 1.5, 0.5, 1], [1.5, 0.5, 1, 1, 2], [1, 1, 1, 2, 1],
        [0.5, 0.5, 1, 1, 3], [1, 0.5, 0.5, 1, 1, 2]]
R_68 = [[3, 1, 2, 3, 3], [2, 1, 3, 6], [1, 1, 1, 3, 4, 2], [3, 3, 2, 1, 3], [4, 2, 3, 3],
        [2, 1, 2, 1, 6]]
R_FAST = [[0.5, 0.5, 1, 0.5, 0.5, 1, 2, 2], [1.5, 0.5, 1, 1, 0.5, 0.5, 0.5, 0.5, 2],
          [1, 1, 1, 1, 3, 1], [0.5, 0.5, 0.5, 0.5, 1, 1, 2, 2], [1, 0.5, 0.5, 1, 1, 1.5, 0.5, 2]]
for _pool, _len in ((R_SLOW, 8), (R_MID, 8), (R_34, 6), (R_68, 12), (R_FAST, 8)):
    for _r in _pool:
        assert abs(sum(abs(x) for x in _r) - _len) < 1e-9, _r

STEP_W = {0: 0.2, 1: 1.0, 2: 0.55, 3: 0.16}


def walk(rng, n, start, end, lo, hi, peak_i, durs):
    """Pentatonic random walk from start to end shaped as an arch toward peak_i."""
    if n == 1:
        return [int(end)]
    seq = [int(start)]
    pk = max(1, int(round(0.6 * (n - 1))))
    for i in range(1, n):
        rem = n - 1 - i
        if rem == 0:
            seq.append(int(end))
            break
        cur = seq[-1]
        target = float(np.interp(i, [0, pk, n - 1], [start, peak_i, end]))
        cands, wts = [], []
        for s in range(-3, 4):
            p = cur + s
            if p < lo or p > hi or abs(p - end) > 2 * rem:
                continue
            if rem == 1 and abs(p - end) not in (1, 2):
                continue
            if s == 0 and len(seq) >= 2 and seq[-2] == cur:
                continue
            w = STEP_W[abs(s)] * (np.exp(-0.5 * ((p - target) / 1.4) ** 2) + 0.05)
            if durs[i] >= 1.5 and (p % 5) in (0, 3):
                w *= 1.8
            cands.append(p)
            wts.append(w)
        if not cands:
            step = int(np.sign(end - cur)) or 1
            seq.append(int(np.clip(cur + step, lo, hi)))
            continue
        wts = np.asarray(wts)
        seq.append(int(rng.choice(cands, p=wts / wts.sum())))
    return seq


def phrase(rng, rhythm, start, end, lo, hi, peak_i=None):
    """[(beat, dur, idx)] for one phrase rhythm."""
    durs = [d for d in rhythm if d > 0]
    peak_i = int(np.clip(start + 2 if peak_i is None else peak_i, lo, hi))
    ps = walk(rng, len(durs), start, end, lo, hi, peak_i, durs)
    out, b, k = [], 0.0, 0
    for d in rhythm:
        if d > 0:
            out.append((b, float(d), ps[k]))
            k += 1
        b += abs(d)
    return out


def vary(rng, notes, end, lo, hi, keep=0.5):
    """Same rhythm, keep the head, regenerate the tail toward a new ending."""
    n = len(notes)
    if n == 1:
        return [(notes[0][0], notes[0][1], int(end))]
    kk = int(np.clip(round(n * keep), 1, n - 1))
    rest = notes[kk:]
    durs = [notes[kk - 1][1]] + [x[1] for x in rest]
    pk = max(x[2] for x in notes) - int(rng.integers(0, 2))
    ps = walk(rng, len(rest) + 1, notes[kk - 1][2], end, lo, hi, pk, durs)
    return list(notes[:kk]) + [(x[0], x[1], ps[j + 1]) for j, x in enumerate(rest)]


def period(rng, pool, lo=-2, hi=7, first=None):
    """Four two-bar phrases: A (open) A' (closes on the tonic) B (higher, open) A'' (closes)."""
    ia, ib = rng.choice(len(pool), 2, replace=False)
    sA = int(first) if first is not None else int(rng.choice([0, 2, 3]))
    A = phrase(rng, pool[ia], sA, int(rng.choice([3, 1, 4])), lo, hi, sA + int(rng.integers(2, 4)))
    A2 = vary(rng, A, 0, lo, hi, 0.5)
    sB = int(rng.choice([3, 4, 5]))
    B = phrase(rng, pool[ib], sB, int(rng.choice([3, 4, 1])), lo, hi, sB + int(rng.integers(1, 3)))
    A3 = vary(rng, A, 0, lo, hi, 0.4)
    return [A, A2, B, A3]


def simplify(notes, min_d=0.75):
    """Heterophony helper: absorb short notes into the previous one (skeleton melody)."""
    out = []
    for b, d, i in notes:
        if out and d < min_d:
            pb, _, pi = out[-1]
            out[-1] = (pb, b + d - pb, pi)
        else:
            out.append((b, d, i))
    return out


def press_bend(cents, delay, time):
    """Guzheng press bend: start `cents` flat and press up to pitch."""
    def fn(t):
        return cents * (1.0 - smoothstep((t - delay) / time))
    return fn


def sink_bend(cents, delay, time):
    """Pitch sinks by `cents` after `delay` (release slide / eerie droop)."""
    def fn(t):
        return cents * smoothstep((t - delay) / time)
    return fn


# ---------------------------------------------------------------- track

class Track:
    OFFSET = 0.025  # events sit 25 ms after the loop point, so the seam falls between attacks

    def __init__(self, tid, bpm, bar_beats, bars):
        self.id = tid
        self.bpm, self.bb, self.bars = float(bpm), int(bar_beats), int(bars)
        self.spb = 60.0 / self.bpm
        self.L = int(round(self.bars * self.bb * self.spb * SR))
        self.T = self.L / SR
        self.buses = {}
        self.stats = {}

    def r(self, part):
        return rng_for("music", self.id, part)

    def bus(self, name, gain_db=0.0, send=0.25, fx=()):
        self.buses[name] = dict(buf=np.zeros(self.L), gain=undb(gain_db), send=send, fx=tuple(fx))

    def tb(self, bar, beat=0.0):
        """Seconds at bar/beat."""
        return (bar * self.bb + beat) * self.spb

    def add(self, name, sig, t, gain=1.0):
        wrap_add(self.buses[name]["buf"], sig, int(round((t + self.OFFSET) * SR)), gain)

    def zheng(self, name, t, midi, vel, rng, ring=None, jitter=0.006, **kw):
        f = float(mtof(midi))
        p = zheng_params(f)
        p.update(kw)
        if ring is None:
            ring = min(p["t60"] * 0.8, 5.0)
        sig = pluck(f, rng, ring=ring, vel=vel, **p)
        self.add(name, sig, t + (rng.normal(0, jitter) if jitter else 0.0), vel)

    def pipa(self, name, t, midi, vel, rng, ring=0.8, jitter=0.004, **kw):
        f = float(mtof(midi))
        p = pipa_params(f)
        p.update(kw)
        sig = pluck(f, rng, ring=ring, vel=vel, **p)
        self.add(name, sig, t + (rng.normal(0, jitter) if jitter else 0.0), vel)

    def pipa_trem(self, name, t, dur, midi, vel, rng, rate=15.0):
        """Pipa lunzhi tremolo: the same string re-plucked ~15 times a second."""
        nh = max(2, int(dur * rate))
        hits = []
        for k in range(nh):
            th = max(0.0, k / rate + rng.normal(0, 0.004))
            hits.append((th, rng.uniform(0.7, 1.0) * (0.75 + 0.25 * np.sin(np.pi * (k + 0.5) / nh))))
        f = float(mtof(midi))
        p = pipa_params(f)
        p["nail"] = 0.03
        sig = pluck(f, rng, ring=dur + 0.3, hits=hits, vel=vel, **p)
        self.add(name, sig, t + rng.normal(0, 0.003), vel)

    def flute(self, name, notes, rng, kind="dizi", gain=1.0, **kw):
        if not notes:
            return
        t0 = min(x[0] for x in notes)
        rel = [(x[0] - t0,) + tuple(x[1:]) for x in notes]
        sig, pre = flute(rel, rng, kind=kind, **kw)
        self.add(name, sig, t0 - pre, gain)

    def mix(self, t60=2.0, wet=0.35, predelay=0.02, hf=0.45, target=-18.0):
        L = self.L
        dry = np.zeros(L)
        send = np.zeros(L)
        parts = {}
        for name, b in self.buses.items():
            y = b["buf"]
            if b["fx"]:
                y = filt(y, *b["fx"], circular=True)
            y = y * b["gain"]
            dry += y
            send += y * b["send"]
            parts[name] = rms_a(y)
        ir = reverb_ir(rng_for("music", self.id, "reverb"), t60=t60, predelay=predelay, hf=hf)
        wet_sig = convolve(send, ir, circular=True) * wet
        out = dry + wet_sig
        out = filt(out, highpass(32, 0.6), highshelf(7500, -2.5), circular=True)
        out -= out.mean()
        total = rms(out)
        total_a = rms_a(out)
        self.stats = {k: db(v / max(total_a, 1e-12)) for k, v in parts.items()}
        self.stats["(reverb)"] = db(rms_a(wet_sig) / max(total_a, 1e-12))
        g = undb(target) / max(total, 1e-12)
        g = min(g, undb(3.0) / max(peak(out), 1e-12))  # at most ~4 dB of peak limiting
        return limit(out * g, undb(-1.0)), dict(self.stats)


# ---------------------------------------------------------------- arrangement helpers

def gliss(tr, name, t, sc, i0, i1, rng, dt=0.045, vel=0.42, octave=0, ring=1.6):
    """Guzheng glissando (guazou) across the pentatonic strings."""
    step = 1 if i1 >= i0 else -1
    idxs = list(range(i0, i1 + step, step))
    for k, i in enumerate(idxs):
        v = vel * (0.55 + 0.45 * k / max(1, len(idxs) - 1))
        tr.zheng(name, t + k * dt, sc(i) + 12 * octave, v, rng, ring=ring, jitter=0.002)


def gliss_len(i0, i1, dt=0.045):
    return (abs(i1 - i0)) * dt


def arp(tr, name, t0, step, sc, root, pattern, rng, vel=0.4, octave=-1, accent=1.3, ring=1.6, dyn=None):
    for k, off in enumerate(pattern):
        if off is None:
            continue
        v = vel * (accent if k == 0 else 1.0) * rng.uniform(0.85, 1.05)
        if dyn is not None:
            v *= dyn(k)
        tr.zheng(name, t0 + k * step, sc(root + off) + 12 * octave, v, rng, ring=ring)


def zheng_melody(tr, name, notes, sc, t0, rng, octave=0, vel=0.75, vib_p=0.7, bend_p=0.3,
                 ring_mul=1.8, max_ring=4.5):
    """Guzheng lead: 'yin' vibrato on long notes, press bends into whole-tone steps."""
    for k, (b, d, i) in enumerate(notes):
        t = t0 + b * tr.spb
        dur = d * tr.spb
        kw = {}
        if dur >= 0.7 and rng.random() < vib_p:
            kw["vib"] = (rng.uniform(4.6, 6.0), rng.uniform(12.0, 24.0), rng.uniform(0.18, 0.35))
        if k and notes[k - 1][2] == i - 1 and sc(i) - sc(i - 1) == 2 and rng.random() < bend_p:
            kw["bend"] = press_bend(-200.0, rng.uniform(0.04, 0.09), rng.uniform(0.1, 0.16))
        ring = float(np.clip(dur * ring_mul, 0.9, max_ring))
        tr.zheng(name, t, sc(i) + 12 * octave, vel * rng.uniform(0.85, 1.05), rng, ring=ring, **kw)


def to_flute(tr, notes, sc, t0, rng, octave=0, vel=0.85, grace_p=0.3, gap=0.06, subst=None):
    """Melody notes -> flute notes with slurs, grace notes and breaths."""
    out = []
    for k, (b, d, i) in enumerate(notes):
        t = t0 + b * tr.spb
        dur = d * tr.spb
        nb = notes[k + 1][0] if k + 1 < len(notes) else None
        legato = nb is not None and abs(nb - (b + d)) < 1e-6
        if not legato:
            dur = max(0.08, dur - gap)
        orn = {}
        prev = notes[k - 1] if k else None
        if prev is not None and abs(prev[0] + prev[1] - b) < 1e-6 and abs(i - prev[2]) == 1 \
                and rng.random() < 0.45:
            orn["slur"] = True
        if d * tr.spb >= 0.4 and rng.random() < grace_p:
            orn["grace"] = sc(i + 1) - sc(i)
        m = sc(i) + 12 * octave
        if subst:
            m = subst.get(m, m)
        out.append((t, dur, m, vel * rng.uniform(0.88, 1.0), orn))
    return out


def lane(tr, name, bar, pattern, samples, rng, vel=1.0, jitter=0.004):
    """Drum lane: pattern string over one bar ('X' accent, 'x' normal, 'o' ghost, '.' rest)."""
    step = tr.bb / len(pattern)
    for k, ch in enumerate(pattern):
        if ch in ". ":
            continue
        v = {"X": 1.0, "x": 0.68, "o": 0.38}[ch] * vel
        s = samples[int(rng.integers(len(samples)))]
        tr.add(name, s, tr.tb(bar, k * step) + rng.normal(0, jitter), v)


def pad_note(freqs, dur, rng, harm=SOFT, attack=0.8, release=1.2, detune=5.0):
    """Sustained chord (sheng-like when harm is reedy)."""
    n = nsamp(dur + release)
    t = tvec(n)
    out = np.zeros(n)
    for f in freqs:
        for det in (-detune, detune):
            fb = f * 2 ** (det / 1200.0)
            p0 = rng.uniform(0, TAU)
            for k, hk in enumerate(harm, start=1):
                if fb * k > 0.45 * SR:
                    break
                out += 0.5 * hk * np.sin(TAU * fb * k * t + p0 * k)
    env = smoothstep(t / attack) * (1.0 - smoothstep((t - dur) / release))
    return out * env / (len(freqs) * sum(harm))


REED = (1.0, 0.55, 0.4, 0.3, 0.22, 0.15, 0.11, 0.08, 0.05)
BAMBOO = ((1.0, 1.0, 1.0), (2.21, 0.3, 0.5), (3.9, 0.1, 0.3))


def reverse_swell(rng, dur=2.4, t60=2.0):
    """Reversed soft cymbal: a swell that lands on the next downbeat."""
    c = cymbal(rng, dur=dur, t60=t60, noise_amt=0.35, fmin=400)[::-1]
    return fades(c, 0.05, 0.008)


# ---------------------------------------------------------------- tracks

@music("title")
def m_title():
    tr = Track("title", 50, 4, 8)                      # 38.4 s
    sc = Scale(62, 0)                                  # D gong, tonic D4
    tr.bus("drone", -24, 0.3)
    tr.bus("mist", -36, 0.3)
    tr.bus("zheng", -2, 0.32, ZHENG_BODY)
    tr.bus("flute", -6, 0.42)
    tr.bus("perc", -4, 0.45)
    tr.add("drone", drone(tr.L, tr.T, tr.r("drone"), [(mtof(38), 1.0), (mtof(45), 0.5), (mtof(50), 0.3)],
                          harm=TRI, swell=(2, 0.45)), 0)
    tr.add("mist", wind(tr.L, tr.T, tr.r("mist"), base=700, spread=900, width=1.0, cycles=(1, 2, 3),
                        floor=0.3), 0)
    rz = tr.r("zheng")
    prog = [0, -1, -2, 0, 0, -1, 1, 0]                 # D Bm A D | D Bm E D (open fifths)
    for bar, root in enumerate(prog):
        tr.zheng("zheng", tr.tb(bar), sc(root) - 24, 0.8, rz, ring=5.5)
        for k, off in enumerate((3, 5, 7)):
            tr.zheng("zheng", tr.tb(bar, 1.0) + 0.05 * k, sc(root + off) - 24, 0.4 - 0.05 * k, rz, ring=3.5)
        tr.zheng("zheng", tr.tb(bar, 2.5), sc(root + 5) - 12, 0.26, rz, ring=2.5)
        tr.zheng("zheng", tr.tb(bar, 3.0), sc(root + 3) - 12, 0.22, rz, ring=2.5)
    gliss(tr, "zheng", -gliss_len(-5, 5, 0.056) - 0.056, sc, -5, 5, rz, dt=0.056, vel=0.4)
    rm = tr.r("melody")
    ph = period(rm, R_SLOW, lo=-2, hi=6, first=0)
    fl = []
    for p, notes in enumerate(ph):
        if p == 2:                                     # the guzheng answers in bars 5-6
            zheng_melody(tr, "zheng", notes, sc, tr.tb(2 * p), rm, octave=1, vel=0.72)
            continue
        fl += to_flute(tr, notes, sc, tr.tb(2 * p), rm, octave=1)
    tr.flute("flute", fl, tr.r("flute_sig"), kind="dizi", vib_depth=22)
    rp = tr.r("perc")
    tr.add("perc", gong(62.0, rp, dur=6.0, pitch=(0, -40), bloom=0.6, bright=0.65), tr.tb(0), 0.5)
    drum = membrane(70, rp, t60=0.9, drop=0.35, noise_amt=0.15)
    tr.add("perc", drum, tr.tb(0), 0.8)
    tr.add("perc", drum, tr.tb(4), 0.55)
    sw = reverse_swell(rp, 2.4)
    tr.add("perc", sw, -len(sw) / SR, 0.28)
    return tr.mix(t60=3.2, wet=0.42, predelay=0.03)


@music("village_day")
def m_village_day():
    tr = Track("village_day", 76, 3, 16)               # 37.9 s, lilting 3/4
    sc = Scale(67, 0)                                  # G gong, tonic G4
    tr.bus("zheng", -6, 0.2, ZHENG_BODY)
    tr.bus("lead", -2, 0.24, ZHENG_BODY)
    tr.bus("flute", -11, 0.3)
    tr.bus("perc", -9, 0.2)
    tr.bus("amb", -24, 0.35)
    prog = [0, 0, -2, -2, 0, 0, 1, -2, -1, -1, -2, 0, 1, -2, 0, 0]
    rz = tr.r("acc")
    pats = [[None, None, 3, 5, 7, 5], [None, None, 3, 5, 3, 7]]
    for bar, root in enumerate(prog):
        tr.zheng("zheng", tr.tb(bar), sc(root) - 24, 0.62, rz, ring=3.0)
        arp(tr, "zheng", tr.tb(bar), tr.spb / 2, sc, root, pats[bar % 2], rz, vel=0.34, octave=-1,
            accent=1.0, ring=1.4)
    rm = tr.r("melody")
    p1 = period(rm, R_34, lo=-2, hi=7, first=2)
    b2 = phrase(rm, R_34[int(rm.integers(len(R_34)))], 4, 3, -2, 7, 6)
    p2 = [p1[0], p1[1], b2, vary(rm, p1[0], 0, -2, 7, 0.55)]
    for p, notes in enumerate(p1 + p2):
        zheng_melody(tr, "lead", notes, sc, tr.tb(2 * p), rm, octave=0, vel=0.72)
    fl = []
    for p, notes in enumerate(p2):                     # dizi joins in heterophony
        fl += to_flute(tr, simplify(notes), sc, tr.tb(8 + 2 * p), rm, octave=0, grace_p=0.4)
    tr.flute("flute", fl, tr.r("flute_sig"), kind="dizi", vib_depth=16)
    rp = tr.r("perc")
    muyu = [woodblock(720 * rp.uniform(0.98, 1.02), rp, t60=0.1) for _ in range(3)]
    ding = bell(2093.0, rp, dur=1.2, kind="small", strike=0.1)
    for bar in range(16):
        lane(tr, "perc", bar, "x.o", muyu, rp, vel=0.8)
        if bar % 4 == 0:
            tr.add("perc", ding, tr.tb(bar), 0.22)
    ra = tr.r("birds")
    for _ in range(5):
        tr.add("amb", bird(ra, ra.uniform(2800, 4200)), ra.uniform(0, tr.T), ra.uniform(0.4, 1.0))
    return tr.mix(t60=1.5, wet=0.3)


@music("village_night")
def m_village_night():
    tr = Track("village_night", 52, 4, 8)              # 36.9 s
    sc = Scale(48, 4)                                  # A yu (C gong), tonic A3
    tr.bus("drone", -21, 0.25, (lowpass(900),))
    tr.bus("night", -35, 0.2)
    tr.bus("water", -32, 0.2, (lowpass(2200),))
    tr.bus("zheng", -2, 0.36, ZHENG_BODY)
    tr.bus("flute", -8, 0.45)
    tr.bus("perc", -11, 0.7)
    tr.add("drone", drone(tr.L, tr.T, tr.r("drone"), [(mtof(45), 1.0), (mtof(52), 0.35)], harm=SOFT,
                          swell=(1, 0.5)), 0)
    tr.add("night", crickets(tr.L, tr.T, tr.r("crickets"), count=3), 0)
    tr.add("water", stream(tr.L, tr.T, tr.r("water"), density=8, fmin=300, fmax=1200, bed=0.8, bub=0.6), 0)
    rz = tr.r("zheng")
    prog = [0, 0, -2, -1, 0, 1, -2, 0]
    for bar, root in enumerate(prog):
        tr.zheng("zheng", tr.tb(bar), sc(root) - 12, 0.66, rz, ring=5.0)
        if bar % 2 == 1:
            tr.zheng("zheng", tr.tb(bar, 2.0), sc(root + 3) - 12, 0.3, rz, ring=3.0)
    rm = tr.r("melody")
    ph = period(rm, R_SLOW, lo=-1, hi=5, first=0)
    zheng_melody(tr, "zheng", ph[0], sc, tr.tb(0), rm, octave=0, vel=0.6)
    zheng_melody(tr, "zheng", ph[2], sc, tr.tb(4), rm, octave=0, vel=0.6)
    fl = to_flute(tr, ph[1], sc, tr.tb(2), rm, octave=1) + to_flute(tr, ph[3], sc, tr.tb(6), rm, octave=1)
    tr.flute("flute", fl, tr.r("flute_sig"), kind="xiao", vib_depth=16, vib_rate=4.8)
    rp = tr.r("perc")                                  # distant night-watch clapper
    for k, dt in enumerate((0.0, 0.34)):
        tr.add("perc", woodblock(1650, rp, t60=0.07, click_amt=0.5), tr.tb(5, 2.0) + dt, 0.9 - 0.2 * k)
    return tr.mix(t60=2.6, wet=0.45, predelay=0.03)


@music("field")
def m_field():
    tr = Track("field", 100, 4, 16)                    # 38.4 s
    sc = Scale(62, 3)                                  # A zhi (D gong), tonic A4
    tr.bus("pad", -25, 0.3)
    tr.bus("zheng", -4, 0.2, ZHENG_BODY)
    tr.bus("flute", -4, 0.28)
    tr.bus("drum", -2, 0.15)
    tr.bus("wood", -4, 0.15)
    tr.add("pad", drone(tr.L, tr.T, tr.r("pad"), [(mtof(45), 1.0), (mtof(52), 0.5)], harm=SOFT,
                        swell=(4, 0.5)), 0)
    prog = [0, 0, -3, -2, 0, 0, 1, -2, -1, -1, -3, -2, 0, -3, -2, 0]
    rz = tr.r("zheng")
    pats = [[0, 3, 5, 7, 8, 7, 5, 3], [0, 3, 5, 3, 7, 5, 8, 5]]
    for bar, root in enumerate(prog):
        arp(tr, "zheng", tr.tb(bar), tr.spb / 2, sc, root, pats[(bar // 2) % 2], rz, vel=0.4,
            octave=-2, accent=1.5, ring=1.5)
    rm = tr.r("melody")
    p1 = period(rm, R_MID, lo=-2, hi=7, first=0)
    p2 = period(rm, R_MID, lo=-1, hi=8, first=3)
    fl = []
    for p, notes in enumerate(p1 + p2):
        fl += to_flute(tr, notes, sc, tr.tb(2 * p), rm, octave=0, grace_p=0.35)
    tr.flute("flute", fl, tr.r("flute_sig"), kind="dizi", vib_depth=18)
    rp = tr.r("perc")
    drum = [membrane(128 * rp.uniform(0.98, 1.02), rp, t60=0.35, drop=0.4, noise_amt=0.3) for _ in range(3)]
    small = [membrane(430 * rp.uniform(0.97, 1.03), rp, t60=0.09, drop=0.15, noise_amt=0.45,
                      noise_fc=3500, click_amt=0.3) for _ in range(3)]
    muyu = [woodblock(850 * rp.uniform(0.98, 1.02), rp, t60=0.09) for _ in range(3)]
    cym = cymbal(rp, dur=1.6, t60=1.2, noise_amt=0.4)
    for bar in range(16):
        g = bar % 4
        lane(tr, "drum", bar, "X...x..x" if g != 3 else "X...x.x.", drum, rp, vel=0.8)
        lane(tr, "wood", bar, "..x...x.", muyu, rp, vel=0.7)
        if g == 3:
            lane(tr, "drum", bar, "............oxxx", small, rp, vel=0.6)
        if bar % 8 == 0:
            tr.add("drum", cym, tr.tb(bar), 0.22)
    return tr.mix(t60=1.4, wet=0.28)


@music("forest")
def m_forest():
    tr = Track("forest", 72, 4, 12)                    # 40.0 s
    sc = Scale(55, 4)                                  # E yu (G gong), tonic E4
    tr.bus("wind", -23, 0.2)
    tr.bus("bamboo", -5, 0.35)
    tr.bus("wood", -2, 0.3)
    tr.bus("zheng", -2, 0.3, ZHENG_BODY)
    tr.bus("flute", -3, 0.38)
    tr.bus("birds", -17, 0.4)
    tr.add("wind", wind(tr.L, tr.T, tr.r("wind"), base=450, spread=1100, width=1.0, cycles=(1, 2, 3, 4, 7),
                        floor=0.18, whistle=0.2), 0)
    rb = tr.r("bamboo")
    tones = [430, 520, 610, 700, 820, 960]
    for _ in range(6):
        t = rb.uniform(0, tr.T)
        for _ in range(int(rb.integers(3, 7))):
            f = tones[int(rb.integers(len(tones)))] * rb.uniform(0.98, 1.02)
            s = woodblock(f, rb, t60=rb.uniform(0.15, 0.3), click_amt=0.2, bright=0.8, modes=BAMBOO)
            tr.add("bamboo", s, t, rb.uniform(0.3, 1.0))
            t += rb.uniform(0.05, 0.22)
    rp = tr.r("wood")
    lo_b = [woodblock(560 * rp.uniform(0.98, 1.02), rp, t60=0.12) for _ in range(2)]
    hi_b = [woodblock(830 * rp.uniform(0.98, 1.02), rp, t60=0.1) for _ in range(2)]
    pats = [("x.......", "....x.x."), ("x..x....", "......x."), ("x.....x.", "..x....."),
            ("x...x...", ".......x")]
    for bar in range(12):
        pl, ph_ = pats[int(rp.integers(len(pats)))]
        lane(tr, "wood", bar, pl, lo_b, rp, vel=0.8)
        lane(tr, "wood", bar, ph_, hi_b, rp, vel=0.55)
    rz = tr.r("zheng")
    prog = [0, 0, 1, -1, 0, 2, -1, 0, 1, -1, -2, 0]
    for bar, root in enumerate(prog):
        tr.zheng("zheng", tr.tb(bar), sc(root) - 24, 0.7, rz, ring=4.0)
        if bar % 3 == 2:
            tr.add("zheng", harmonic_tone(float(mtof(sc(root + 3) - 12)), rz, ring=3.0), tr.tb(bar, 2.0), 0.4)
    rm = tr.r("melody")
    p = period(rm, R_MID, lo=-1, hi=7, first=0)
    phrases = p + [vary(rm, p[2], 3, -1, 7, 0.5), vary(rm, p[0], 0, -1, 7, 0.3)]
    fl = []
    for k, notes in enumerate(phrases):
        fl += to_flute(tr, notes, sc, tr.tb(2 * k), rm, octave=0, grace_p=0.3)
    tr.flute("flute", fl, tr.r("flute_sig"), kind="xiao", vib_depth=16)
    ra = tr.r("birds")
    for _ in range(3):
        tr.add("birds", bird(ra, ra.uniform(3000, 4500)), ra.uniform(0, tr.T), ra.uniform(0.5, 1.0))
    return tr.mix(t60=2.0, wet=0.36)


@music("river")
def m_river():
    tr = Track("river", 150, 6, 16)                    # 6/8 counted in eighths: 38.4 s
    sc = Scale(60, 0)                                  # C gong, tonic C4
    tr.bus("water", -28, 0.2)
    tr.bus("arp", -6, 0.25, ZHENG_BODY)
    tr.bus("lead", 1, 0.3, ZHENG_BODY)
    tr.bus("flute", -7, 0.35)
    tr.add("water", stream(tr.L, tr.T, tr.r("water"), density=35), 0)
    rz = tr.r("arp")
    prog = [0, -1, 2, -2, 0, -1, 1, -2, 0, 2, -1, 1, 0, -1, -2, 0]
    pat = [0, 3, 5, 7, 5, 3, 0, 3, 5, 8, 7, 5]
    for bar, root in enumerate(prog):
        arp(tr, "arp", tr.tb(bar), tr.spb / 2, sc, root, pat, rz, vel=0.36, octave=-1, accent=1.35,
            ring=1.3, dyn=lambda k: 0.75 + 0.25 * np.sin(np.pi * k / 12.0))
    rm = tr.r("melody")
    p1 = period(rm, R_68, lo=-1, hi=7, first=2)
    b2 = phrase(rm, R_68[int(rm.integers(len(R_68)))], 5, 3, -1, 7, 7)
    p2 = [vary(rm, p1[0], 3, -1, 7, 0.6), p1[1], b2, p1[3]]
    for p, notes in enumerate(p1):
        zheng_melody(tr, "lead", notes, sc, tr.tb(2 * p), rm, octave=1, vel=0.7)
    fl = []
    for p, notes in enumerate(p2):
        fl += to_flute(tr, notes, sc, tr.tb(8 + 2 * p), rm, octave=1)
        for b, d, i in notes:                          # light guzheng doubling of long notes
            if d >= 3:
                tr.zheng("lead", tr.tb(8 + 2 * p, b), sc(i) + 12, 0.35, rm, ring=2.0)
    tr.flute("flute", fl, tr.r("flute_sig"), kind="dizi", vib_depth=18)
    rg = tr.r("gliss")
    gliss(tr, "lead", tr.tb(8) - gliss_len(-5, 5) - 0.045, sc, -5, 5, rg, octave=1, vel=0.36)
    gliss(tr, "lead", -gliss_len(10, 0) - 0.045, sc, 10, 0, rg, octave=0, vel=0.36)
    return tr.mix(t60=1.8, wet=0.32)


@music("sect")
def m_sect():
    tr = Track("sect", 72, 4, 12)                      # 40.0 s
    sc = Scale(60, 3)                                  # G zhi (C gong), tonic G4
    tr.bus("sheng", -17, 0.35, (lowpass(2200, 0.6),))
    tr.bus("bells", -4, 0.35)
    tr.bus("big", -8, 0.5)
    tr.bus("zheng", -11, 0.25, ZHENG_BODY)
    tr.bus("muyu", -14, 0.2)
    tr.bus("drum", -6, 0.3)
    prog = [0, 0, -3, -3, -2, -2, 0, 0, 1, -1, -2, 0]
    rs = tr.r("sheng")
    for bar in range(0, 12, 2):
        root = prog[bar]
        chord = [float(mtof(sc(root + o) - 12)) for o in (0, 3, 5)]
        tr.add("sheng", pad_note(chord, 2 * tr.bb * tr.spb, rs, harm=REED, attack=0.6, release=0.9), tr.tb(bar))
    rm = tr.r("melody")
    p = period(rm, R_SLOW, lo=-2, hi=6, first=0)
    phrases = p + [vary(rm, p[2], 3, -2, 6, 0.5), vary(rm, p[0], 0, -2, 6, 0.4)]
    rb = tr.r("bells")
    for k, notes in enumerate(phrases):
        for b, d, i in notes:
            s = bell(float(mtof(sc(i))), rb, dur=float(np.clip(d * tr.spb * 1.5, 2.0, 4.0)), kind="bianzhong",
                     strike=0.2)
            tr.add("bells", s, tr.tb(2 * k, b) + rb.normal(0, 0.004), 0.8 * rb.uniform(0.9, 1.0))
    rt = tr.r("temple")
    tr.add("big", bell(98.0, rt, dur=8.0, kind="temple", strike=0.1), tr.tb(0), 0.9)
    tr.add("big", bell(98.0, rt, dur=8.0, kind="temple", strike=0.1), tr.tb(6), 0.65)
    tr.add("big", bowl(392.0, rt, dur=6.0), tr.tb(3, 2.0), 0.35)
    tr.add("big", bowl(392.0, rt, dur=6.0), tr.tb(9, 2.0), 0.3)
    rp = tr.r("muyu")
    mu = [woodblock(600 * rp.uniform(0.99, 1.01), rp, t60=0.14) for _ in range(3)]
    drum = [membrane(88 * rp.uniform(0.98, 1.02), rp, t60=0.6, drop=0.3, noise_amt=0.2) for _ in range(2)]
    for bar in range(12):
        lane(tr, "muyu", bar, "Xxxx", mu, rp, vel=0.8)
        lane(tr, "drum", bar, "X.x." if bar % 4 == 3 else "X...", drum, rp, vel=0.8)
    rz = tr.r("zheng")
    for bar, root in enumerate(prog):
        for beat in (0.0, 2.0):
            v = 0.5 if beat == 0 else 0.36
            tr.zheng("zheng", tr.tb(bar, beat), sc(root) - 24, v, rz, ring=2.5)
            tr.zheng("zheng", tr.tb(bar, beat) + 0.03, sc(root + 3) - 24, v * 0.8, rz, ring=2.5)
    return tr.mix(t60=2.6, wet=0.4, predelay=0.03)


@music("dungeon")
def m_dungeon():
    tr = Track("dungeon", 60, 4, 10)                   # 40.0 s
    tr.bus("drone", -16, 0.3, (lowpass(850, 0.7), lowshelf(110, -4.0)))
    tr.bus("rumble", -26, 0.2)
    tr.bus("moan", -34, 0.45)
    tr.bus("pluck", -4, 0.5, PIPA_BODY)
    tr.bus("drip", -10, 0.85)
    tr.bus("gong", -2, 0.6)
    tr.bus("drum", -10, 0.5)
    rd = tr.r("drone")
    tr.add("drone", drone(tr.L, tr.T, rd, [(mtof(38), 1.0), (mtof(45), 0.3), (mtof(44), 0.22), (mtof(50), 0.3)],
                          harm=(1.0, 0.5, 0.35, 0.25, 0.15, 0.1, 0.06), swell=(2, 0.6), detune=6.0), 0)
    t = tvec(tr.L)
    rum = pnoise(tr.L, tr.r("rumble"), lowpass(110, 0.8)) * (1.0 + 0.4 * np.sin(TAU * 3 * t / tr.T + 1.0))
    tr.add("rumble", rum, 0)
    tr.add("moan", wind(tr.L, tr.T, tr.r("moan"), base=260, spread=300, width=0.45, cycles=(1, 2, 3),
                        floor=0.1, whistle=0.5), 0)
    rp = tr.r("pluck")
    pool = [50, 51, 53, 56, 57, 60, 61, 62, 63]
    tp = 0.3
    while tp < tr.T - 0.5:
        m = pool[int(rp.integers(len(pool)))]
        roll = rp.random()
        if roll < 0.3:                                 # minor-second cluster
            tr.pipa("pluck", tp, m, 0.6, rp, ring=2.5)
            tr.pipa("pluck", tp + 0.07, m + 1, 0.5, rp, ring=2.5)
        elif roll < 0.55:                              # sinking note
            tr.pipa("pluck", tp, m, 0.65, rp, ring=2.8, bend=sink_bend(-90.0, 0.35, 1.4))
        else:
            tr.pipa("pluck", tp, m, 0.55, rp, ring=2.2)
        tp += float(rp.choice([1.0, 1.5, 2.0, 2.5, 3.0])) * tr.spb
    rdr = tr.r("drip")
    for _ in range(18):
        f0 = float(np.exp(rdr.uniform(np.log(900), np.log(2600))))
        tr.add("drip", bubble(rdr, f0, tau=rdr.uniform(0.01, 0.022), rise=rdr.uniform(0.8, 1.8)),
               rdr.uniform(0, tr.T), rdr.uniform(0.3, 1.0))
    rg = tr.r("gong")
    g = gong(82.0, rg, dur=7.0, pitch=(0, -30), bloom=1.2, bright=0.8, thump=0.0)
    g *= smoothstep(tvec(len(g)) / 2.5)                # bowed swell
    tr.add("gong", g, tr.tb(4), 0.8)
    beat = membrane(52, rg, t60=0.8, drop=0.3, noise_amt=0.1)
    tr.add("drum", beat, tr.tb(0), 0.7)
    tr.add("drum", beat, tr.tb(5), 0.55)
    return tr.mix(t60=4.2, wet=0.55, predelay=0.05, hf=0.35)


@music("battle")
def m_battle():
    tr = Track("battle", 132, 4, 20)                   # 36.4 s
    sc = Scale(55, 4)                                  # E yu (G gong), tonic E4
    tr.bus("drum", -3, 0.12)
    tr.bus("hi", -10, 0.12)
    tr.bus("cym", -12, 0.2)
    tr.bus("bass", -11, 0.08, ZHENG_BODY)
    tr.bus("pipa", -5, 0.2, PIPA_BODY)
    tr.bus("flute", -6, 0.25)
    tr.bus("drone", -24, 0.2)
    tr.add("drone", drone(tr.L, tr.T, tr.r("drone"), [(mtof(40), 1.0), (mtof(47), 0.5)], harm=SOFT,
                          swell=(5, 0.5)), 0)
    rd = tr.r("drums")
    big = [membrane(64 * rd.uniform(0.98, 1.02), rd, t60=0.5, drop=0.7, noise_amt=0.3, noise_fc=900)
           for _ in range(3)]
    tom = [membrane(125 * rd.uniform(0.97, 1.03), rd, t60=0.3, drop=0.45, noise_amt=0.35) for _ in range(3)]
    bangu = [membrane(640 * rd.uniform(0.97, 1.03), rd, t60=0.06, drop=0.12, noise_amt=0.6, noise_fc=4000,
                      click_amt=0.5) for _ in range(4)]
    cha = [cymbal(rd, dur=0.35, t60=0.22, fmin=900, count=40, noise_amt=0.7) for _ in range(2)]
    nao = cymbal(rd, dur=2.2, t60=1.7, fmin=350, count=64, noise_amt=0.5)
    for bar in range(20):
        g = bar % 4
        lane(tr, "drum", bar, "X.....x.X..x....", big, rd, vel=0.95)
        lane(tr, "drum", bar, "..x.x...x.x.x.xx" if g != 3 else "..x.x.x.xxxxXXXX", tom, rd, vel=0.62)
        lane(tr, "hi", bar, "....x.......x...", cha, rd, vel=0.7)
        if g == 3:
            lane(tr, "hi", bar, "........oxoxxxXX", bangu, rd, vel=0.8)
        else:
            lane(tr, "hi", bar, "..o...o...o...o.", bangu, rd, vel=0.5)
        if g == 0:
            tr.add("cym", nao, tr.tb(bar), 0.8)
    prog = [0, 0, -1, -1, 0, 0, 1, 2, 0, 0, -1, -1, 1, 1, 2, 3, 0, -1, 1, 0]
    rb = tr.r("bass")
    for bar, root in enumerate(prog):
        for k, off in enumerate((0, 0, 5, 0, 3, 0, 4, 0)):
            tr.zheng("bass", tr.tb(bar, 0.5 * k), sc(root + off) - 24, 0.75 if k in (0, 4) else 0.55, rb,
                     ring=0.32, release=0.05, jitter=0.003)
    rm = tr.r("melody")
    rp = tr.r("pipa")
    p1 = period(rm, R_MID, lo=-2, hi=7, first=0)

    def pipa_line(notes, t0, vel):
        for b, d, i in notes:
            dur = d * tr.spb
            if dur >= 0.4:
                tr.pipa_trem("pipa", t0 + b * tr.spb, dur, sc(i), vel, rp)
            else:
                tr.pipa("pipa", t0 + b * tr.spb, sc(i), vel, rp, ring=0.5)

    for p, notes in enumerate(p1):
        pipa_line(notes, tr.tb(2 * p), 0.75)
    p2 = period(rm, R_FAST, lo=0, hi=8, first=3)
    fl = []
    for p, notes in enumerate(p2):
        fl += to_flute(tr, notes, sc, tr.tb(8 + 2 * p), rm, octave=0, grace_p=0.4, gap=0.03)
        for bb in (0.0, 1.5, 4.0, 5.5):                # pipa 'sao' strums under the dizi
            root = prog[8 + 2 * p + int(bb // 4)]
            for k, o in enumerate((0, 3, 5, 7)):
                tr.pipa("pipa", tr.tb(8 + 2 * p, bb) + 0.012 * k, sc(root + o) - 12, 0.5 - 0.05 * k, rp, ring=0.5)
    fin = vary(rm, p1[0], 0, -2, 7, 0.5)
    pipa_line(fin, tr.tb(16), 0.8)
    pipa_line(p1[3], tr.tb(18), 0.8)
    fl += to_flute(tr, simplify(fin), sc, tr.tb(16), rm, octave=1, grace_p=0.4, vel=0.7)
    fl += to_flute(tr, simplify(p1[3]), sc, tr.tb(18), rm, octave=1, grace_p=0.4, vel=0.7)
    tr.flute("flute", fl, tr.r("flute_sig"), kind="dizi", vib_depth=12, vib_rate=6.0)
    return tr.mix(t60=1.2, wet=0.22)


@music("boss")
def m_boss():
    tr = Track("boss", 144, 4, 24)                     # 40.0 s
    sc = Scale(53, 4)                                  # D yu (F gong) + flat second, tonic D4
    tr.bus("drum", -4, 0.12)
    tr.bus("gong", -4, 0.35)
    tr.bus("cym", -11, 0.2)
    tr.bus("pipa", -6, 0.2, PIPA_BODY)
    tr.bus("zheng", -5, 0.25, ZHENG_BODY)
    tr.bus("flute", -9, 0.25)
    tr.bus("drone", -20, 0.2, (lowpass(900),))
    tr.add("drone", drone(tr.L, tr.T, tr.r("drone"), [(mtof(38), 1.0), (mtof(45), 0.45), (mtof(39), 0.15)],
                          harm=TRI, swell=(3, 0.5)), 0)
    rd = tr.r("drums")
    dagu = [membrane(58 * rd.uniform(0.98, 1.02), rd, t60=0.7, drop=0.8, noise_amt=0.45, noise_fc=1100)
            for _ in range(3)]
    tom = [membrane(98 * rd.uniform(0.97, 1.03), rd, t60=0.35, drop=0.45, noise_amt=0.3) for _ in range(3)]
    hi = [membrane(165 * rd.uniform(0.97, 1.03), rd, t60=0.25, drop=0.4, noise_amt=0.4) for _ in range(3)]
    luo = [gong(420 * rd.uniform(0.99, 1.01), rd, dur=1.1, pitch=(0, 110), tau=0.15, bloom=0.03, bright=0.6,
                thump=0.2) for _ in range(2)]
    daluo = gong(92.0, rd, dur=3.5, pitch=(0, -120), tau=0.4, bloom=0.2, bright=0.8)
    nao = cymbal(rd, dur=2.4, t60=1.8, fmin=300, count=64, noise_amt=0.55)
    for bar in range(24):
        g = bar % 4
        lane(tr, "drum", bar, "X..x..X...x.X..x", dagu, rd, vel=1.0)
        if g == 3:
            lane(tr, "drum", bar, "x.x.x.xxX.X.XxXx", tom, rd, vel=0.7)
            lane(tr, "drum", bar, "..o...o.x.x.x.xx", hi, rd, vel=0.6)
        else:
            lane(tr, "drum", bar, "o.o.o.o.o.o.o.o.", tom, rd, vel=0.55)
            lane(tr, "drum", bar, "....x.......x...", hi, rd, vel=0.7)
        if g == 0:
            tr.add("gong", daluo, tr.tb(bar), 0.9)
            tr.add("cym", nao, tr.tb(bar), 0.7)
        elif g in (1, 2):
            lane(tr, "gong", bar, "..x...x.", luo, rd, vel=0.35)
    rp = tr.r("pipa")
    osti = [(0, 3, 50), (3, 1, 51), (4, 2, 50), (6, 1, 48), (7, 1, 51)]   # D  Eb  D  C  Eb (beats)
    for bar2 in range(0, 24, 2):
        for b, d, m in osti:
            tr.pipa_trem("pipa", tr.tb(bar2, b), d * tr.spb, m, 0.6, rp, rate=16.0)
    for bar in range(8, 24):
        for bb in (1.5, 3.5):
            for k, m in enumerate((50, 57, 63)):
                tr.pipa("pipa", tr.tb(bar, bb) + 0.012 * k, m, 0.5 - 0.06 * k, rp, ring=0.45)
    rm = tr.r("melody")
    fl = []
    for half in (0, 1):
        pp = period(rm, R_FAST, lo=0, hi=6, first=3)
        for p, notes in enumerate(pp):
            fl += to_flute(tr, notes, sc, tr.tb(8 + 8 * half + 2 * p), rm, octave=1, grace_p=0.45, gap=0.03,
                           subst={77: 75, 89: 87} if half else {77: 75})
    tr.flute("flute", fl, tr.r("flute_sig"), kind="dizi", vib_depth=12, vib_rate=6.3)
    rz = tr.r("zheng")
    for bar in (8, 16):
        gliss(tr, "zheng", tr.tb(bar) - gliss_len(-5, 5, 0.04) - 0.04, sc, -5, 5, rz, dt=0.04, vel=0.45)
    gliss(tr, "zheng", -gliss_len(10, 0, 0.04) - 0.04, sc, 10, 0, rz, dt=0.04, vel=0.45)
    return tr.mix(t60=1.6, wet=0.2)


@music("peak")
def m_peak():
    tr = Track("peak", 52, 4, 8)                       # 36.9 s
    sc = Scale(69, 0)                                  # A gong, tonic A4
    tr.bus("wind", -23, 0.2)
    tr.bus("pad", -22, 0.4)
    tr.bus("flute", -3, 0.55)
    tr.bus("zheng", -2, 0.45, ZHENG_BODY)
    tr.bus("harm", -5, 0.6)
    tr.bus("bell", -9, 0.6)
    tr.add("wind", wind(tr.L, tr.T, tr.r("wind"), base=900, spread=2200, width=1.1, cycles=(1, 2, 3, 5, 8),
                        floor=0.15, tilt_db=0.0, whistle=0.25), 0)
    tr.add("pad", drone(tr.L, tr.T, tr.r("pad"), [(mtof(57), 1.0), (mtof(64), 0.6), (mtof(69), 0.35)],
                        harm=(1.0, 0.1), swell=(2, 0.6)), 0)
    rm = tr.r("melody")
    ph = period(rm, R_SLOW, lo=0, hi=7, first=3)
    fl = []
    for p in (0, 1, 3):
        fl += to_flute(tr, ph[p], sc, tr.tb(2 * p), rm, octave=0, grace_p=0.25)
    tr.flute("flute", fl, tr.r("flute_sig"), kind="dizi", vib_depth=20, breath=1.3)
    rh = tr.r("harm")
    for b, d, i in ph[2]:
        tr.add("harm", harmonic_tone(float(mtof(sc(i) - 12)), rh, ring=float(np.clip(d * tr.spb * 1.6, 1.5, 4.0))),
               tr.tb(4, b), 0.6)
    rz = tr.r("zheng")
    gliss(tr, "zheng", tr.tb(0) + 0.02, sc, 10, 0, rz, dt=0.06, vel=0.35, ring=2.5)
    gliss(tr, "zheng", tr.tb(4) + 0.02, sc, 8, -2, rz, dt=0.06, vel=0.32, ring=2.5)
    for bar in (0, 2, 4, 6):
        tr.zheng("zheng", tr.tb(bar), sc(0 if bar % 4 == 0 else -2) - 24, 0.55, rz, ring=5.0)
    rb = tr.r("bell")
    tr.add("bell", chime(1760.0, rb, dur=2.5), tr.tb(2, 2.0), 0.6)
    tr.add("bell", chime(1318.5, rb, dur=2.5), tr.tb(6, 2.0), 0.5)
    return tr.mix(t60=3.8, wet=0.55, predelay=0.035)


@music("meditation")
def m_meditation():
    tr = Track("meditation", 48, 4, 8)                 # 40.0 s
    tr.bus("drone", -17, 0.3, (lowshelf(120, -4.0),))
    tr.bus("bowl", -3, 0.4)
    tr.bus("water", -39, 0.2, (lowpass(1800),))
    tr.add("drone", drone(tr.L, tr.T, tr.r("drone"),
                          [(mtof(38), 0.45), (mtof(50), 1.0), (mtof(57), 0.6), (mtof(62), 0.22)],
                          harm=(1.0, 0.22, 0.08, 0.03), swell=(1, 0.5), detune=2.0), 0)
    rb = tr.r("bowl")
    tr.add("bowl", bowl(293.66, rb, dur=12.0), tr.tb(0), 0.9)
    tr.add("bowl", bowl(220.0, rb, dur=12.0), tr.tb(4), 0.8)
    tr.add("bowl", bowl(587.3, rb, dur=7.0), tr.tb(2, 2.0), 0.3)
    tr.add("bowl", bowl(440.0, rb, dur=7.0), tr.tb(6, 2.0), 0.28)
    tr.add("water", stream(tr.L, tr.T, tr.r("water"), density=6, fmin=300, fmax=1100, bed=0.9, bub=0.5), 0)
    return tr.mix(t60=3.0, wet=0.4, predelay=0.03)


@music("sky_port")
def m_sky_port():
    """Cloudgate Port: a bright, busy harbour in the sky. Guzheng arpeggios, pipa tremolo lead,
    a dizi answer, ship bells and a thin wind high above everything."""
    tr = Track("sky_port", 88, 4, 14)                  # 38.2 s
    sc = Scale(62, 0)                                  # D gong, tonic D4
    tr.bus("pad", -24, 0.35)
    tr.bus("wind", -38, 0.2)
    tr.bus("zheng", -6, 0.25, ZHENG_BODY)
    tr.bus("pipa", -5, 0.22, PIPA_BODY)
    tr.bus("flute", -5, 0.35)
    tr.bus("bell", -8, 0.55)
    tr.bus("perc", -8, 0.2)
    tr.add("pad", drone(tr.L, tr.T, tr.r("pad"), [(mtof(50), 1.0), (mtof(57), 0.5)], harm=SOFT, swell=(2, 0.5)), 0)
    tr.add("wind", wind(tr.L, tr.T, tr.r("wind"), base=800, spread=1800, width=1.0, cycles=(1, 2, 3), floor=0.2,
                        tilt_db=0.0, whistle=0.2), 0)
    prog = [0, 0, -2, -1, 0, 0, 1, -2, 0, 0, -2, -1, 1, 0]
    rz = tr.r("zheng")
    pats = [[0, 3, 5, 7, 5, 3, 5, 7], [0, 5, 3, 7, 5, 8, 7, 5]]
    for bar, root in enumerate(prog):
        arp(tr, "zheng", tr.tb(bar), tr.spb / 2, sc, root, pats[bar % 2], rz, vel=0.34, octave=-1, accent=1.3, ring=1.8)
    rm = tr.r("melody")
    rp = tr.r("pipa")
    p1 = period(rm, R_MID, lo=-1, hi=8, first=2)
    for p, notes in enumerate(p1):
        for b, d, i in notes:
            dur = d * tr.spb
            if dur >= 0.5:
                tr.pipa_trem("pipa", tr.tb(2 * p, b), dur, sc(i), 0.6, rp)
            else:
                tr.pipa("pipa", tr.tb(2 * p, b), sc(i), 0.62, rp, ring=0.6)
    answer = [vary(rm, p1[0], 2, -1, 8, 0.5), p1[2], vary(rm, p1[3], 0, -1, 8, 0.6)]
    fl = []
    for p, notes in enumerate(answer):
        fl += to_flute(tr, notes, sc, tr.tb(8 + 2 * p), rm, octave=0, grace_p=0.4)
    tr.flute("flute", fl, tr.r("flute_sig"), kind="dizi", vib_depth=16)
    rb = tr.r("bell")
    for bar, f0 in ((0, 1174.7), (4, 1318.5), (8, 1174.7), (12, 880.0)):
        tr.add("bell", bell(f0, rb, dur=2.0, kind="small", strike=0.15), tr.tb(bar, 2.0), 0.5)
    rq = tr.r("perc")
    muyu = [woodblock(780 * rq.uniform(0.98, 1.02), rq, t60=0.09) for _ in range(3)]
    for bar in range(14):
        lane(tr, "perc", bar, "x.o.x.o." if bar % 4 != 3 else "x.o.x.xx", muyu, rq, vel=0.7)
    return tr.mix(t60=2.0, wet=0.34)


@music("storm_plains")
def m_storm_plains():
    """Thunderhorn Plains: a galloping 6/8 over open grass. Deep drums, a low gong for far thunder,
    pipa tremolo in the minor (yu) mode and a xiao that answers across the wind."""
    tr = Track("storm_plains", 150, 6, 16)             # 38.4 s, eighth-note pulse
    sc = Scale(53, 4)                                  # F gong, D yu, tonic D4
    tr.bus("wind", -33, 0.2)
    tr.bus("drone", -21, 0.25)
    tr.bus("drum", 0, 0.14)
    tr.bus("thunder", 4, 0.35, (lowpass(900),))
    tr.bus("bass", -10, 0.1, ZHENG_BODY)
    tr.bus("pipa", -5, 0.24, PIPA_BODY)
    tr.bus("flute", -6, 0.4)
    tr.add("wind", wind(tr.L, tr.T, tr.r("wind"), base=500, spread=1400, width=1.0, cycles=(1, 2, 3, 5), floor=0.25,
                        tilt_db=-1.0, whistle=0.1), 0)
    tr.add("drone", drone(tr.L, tr.T, tr.r("drone"), [(mtof(38), 1.0), (mtof(45), 0.45)], harm=SOFT, swell=(4, 0.5)), 0)
    rd = tr.r("drums")
    big = [membrane(70 * rd.uniform(0.98, 1.02), rd, t60=0.45, drop=0.6, noise_amt=0.3, noise_fc=900) for _ in range(3)]
    tom = [membrane(150 * rd.uniform(0.97, 1.03), rd, t60=0.22, drop=0.35, noise_amt=0.35) for _ in range(3)]
    for bar in range(16):
        lane(tr, "drum", bar, "X..x.x", big, rd, vel=0.9)          # the herd's gallop
        lane(tr, "drum", bar, ".x..x." if bar % 4 != 3 else ".xx.xx", tom, rd, vel=0.55)
    rt = tr.r("thunder")
    for bar in (3, 11):
        tr.add("thunder", gong(55.0, rt, dur=5.0, pitch=(0.0, -120.0), tau=0.9, bloom=0.5, bright=0.6), tr.tb(bar, 3.0), 0.8)
    prog = [0, 0, -2, -2, 0, 0, 1, -1, 0, 0, -2, -2, 1, 1, -1, 0]
    rb = tr.r("bass")
    for bar, root in enumerate(prog):
        for k, off in enumerate((0, None, None, 3, None, 0)):
            if off is not None:
                tr.zheng("bass", tr.tb(bar, k), sc(root + off) - 24, 0.7 if k == 0 else 0.5, rb, ring=0.5, jitter=0.003)
    rm = tr.r("melody")
    rp = tr.r("pipa")
    p1 = period(rm, R_68, lo=-2, hi=7, first=0)
    for p, notes in enumerate(p1):
        for b, d, i in notes:
            dur = d * tr.spb
            if dur >= 0.55:
                tr.pipa_trem("pipa", tr.tb(2 * p, b), dur, sc(i), 0.62, rp)
            else:
                tr.pipa("pipa", tr.tb(2 * p, b), sc(i), 0.64, rp, ring=0.5)
    p2 = period(rm, R_68, lo=-1, hi=8, first=3)
    fl = []
    for p, notes in enumerate(p2):
        fl += to_flute(tr, simplify(notes, 1.5), sc, tr.tb(8 + 2 * p), rm, octave=0, grace_p=0.3)
    tr.flute("flute", fl, tr.r("flute_sig"), kind="xiao", vib_depth=18, vib_rate=5.0)
    return tr.mix(t60=1.8, wet=0.3)


@music("desert")
def m_desert():
    """The Sunscar Desert: heat that makes time slow down. A low drone in the yu mode, a frame drum
    and a sand shaker in a lazy 4/4, caravan bells far off, and a xiao that bends its long notes
    like air over hot sand."""
    tr = Track("desert", 72, 4, 12)                    # 40.0 s
    sc = Scale(57, 4)                                  # A gong, F# yu, tonic F#4
    tr.bus("drone", -18, 0.3, (lowpass(1200, 0.7),))
    tr.bus("wind", -36, 0.2)
    tr.bus("drum", 2, 0.18)
    tr.bus("shaker", -12, 0.12, (highpass(2500),))
    tr.bus("bell", -8, 0.5)
    tr.bus("bass", -10, 0.12, ZHENG_BODY)
    tr.bus("flute", -5, 0.42)
    tr.add("drone", drone(tr.L, tr.T, tr.r("drone"), [(mtof(42), 1.0), (mtof(49), 0.45), (mtof(54), 0.2)],
                          harm=SOFT, swell=(3, 0.55), detune=4.0), 0)
    tr.add("wind", wind(tr.L, tr.T, tr.r("wind"), base=700, spread=1600, width=1.1, cycles=(1, 2, 3), floor=0.3,
                        tilt_db=-0.5, whistle=0.05), 0)
    rd = tr.r("drums")
    frame = [membrane(96 * rd.uniform(0.98, 1.02), rd, t60=0.35, drop=0.25, noise_amt=0.4, noise_fc=1400) for _ in range(3)]
    tik = [woodblock(1400 * rd.uniform(0.97, 1.03), rd, t60=0.05, click_amt=0.4) for _ in range(3)]
    for bar in range(12):
        lane(tr, "drum", bar, "X...x.x." if bar % 4 != 3 else "X...x.xx", frame, rd, vel=0.8)
        lane(tr, "drum", bar, "..o...o.", tik, rd, vel=0.35)
    rs = tr.r("shaker")
    for k in range(12 * 8):
        n = nsamp(0.09)
        g = pnoise(n, rs, highpass(4000)) * np.exp(-np.arange(n) / (n / 3.0))
        tr.add("shaker", g, k * tr.spb / 2, 0.55 if k % 2 == 0 else 0.3)
    rb = tr.r("bell")
    for bar, f0 in ((1, 1480.0), (5, 1318.5), (9, 1480.0)):
        for j in range(3):
            tr.add("bell", bell(f0 * (1.0 + 0.004 * j), rb, dur=1.6, kind="small", strike=0.2), tr.tb(bar, 1.0 + j * 0.5), 0.35 - j * 0.08)
    prog = [0, 0, -2, -2, 0, 0, 1, -1, 0, -2, 1, 0]
    rbass = tr.r("bass")
    for bar, root in enumerate(prog):
        tr.zheng("bass", tr.tb(bar, 0), sc(root) - 24, 0.7, rbass, ring=1.4, jitter=0.003)
        tr.zheng("bass", tr.tb(bar, 2.5), sc(root + 3) - 24, 0.45, rbass, ring=0.9, jitter=0.003)
    rm = tr.r("melody")
    p1 = period(rm, R_SLOW, lo=-2, hi=6, first=0)
    fl = []
    for p, notes in enumerate(p1):
        fl += to_flute(tr, simplify(notes, 1.0), sc, tr.tb(2 * p), rm, octave=0, grace_p=0.45)
    p2 = [vary(rm, p1[0], 1, -2, 6, 0.5), p1[3]]
    for p, notes in enumerate(p2):
        fl += to_flute(tr, simplify(notes, 1.0), sc, tr.tb(8 + 2 * p), rm, octave=0, grace_p=0.45)
    tr.flute("flute", fl, tr.r("flute_sig"), kind="xiao", vib_depth=22, vib_rate=4.5)
    return tr.mix(t60=2.4, wet=0.36)


@music("starsea")
def m_starsea():
    """The Starsea and the Skyport Wreck: weightless and glittering. A slow 3/4 sway like a skiff
    riding on air, a deep drone, wind that never touches ground, jade chimes that twinkle on the
    off-beats like stars, zheng glissandi that rise and fall like swells, and a dizi melody in the
    shang mode that keeps looking past the horizon."""
    tr = Track("starsea", 66, 3, 16)                   # 43.6 s
    sc = Scale(55, 1)                                  # G gong, A shang, tonic A4
    tr.bus("drone", -17, 0.4, (lowpass(900, 0.7),))
    tr.bus("wind", -34, 0.35)
    tr.bus("chime", -9, 0.7, (highpass(900),))
    tr.bus("zheng", -6, 0.5, ZHENG_BODY)
    tr.bus("bass", -11, 0.25, ZHENG_BODY)
    tr.bus("flute", -5, 0.5)
    tr.add("drone", drone(tr.L, tr.T, tr.r("drone"), [(mtof(45), 1.0), (mtof(52), 0.5), (mtof(57), 0.25), (mtof(64), 0.08)],
                          harm=SOFT, swell=(2, 0.6), detune=5.0), 0)
    tr.add("wind", wind(tr.L, tr.T, tr.r("wind"), base=900, spread=2200, width=1.2, cycles=(1, 2, 4), floor=0.25,
                        tilt_db=-1.0, whistle=0.12), 0)
    # Stars: jade chimes on scattered off-beats, high in the scale.
    rc = tr.r("chime")
    for bar in range(16):
        for beat in (1.5, 2.5):
            if rc.random() < 0.55:
                i = int(rc.integers(5, 12))
                tr.add("chime", chime(mtof(sc(i) + 12), rc, dur=1.4), tr.tb(bar, beat), rc.uniform(0.18, 0.34))
    # Swells: a rising glissando every four bars, a falling one two bars later.
    rz = tr.r("zheng")
    for bar in (0, 4, 8, 12):
        gliss(tr, "zheng", tr.tb(bar, 0.0), sc, -3, 5, rz, dt=0.06, vel=0.36, ring=2.2)
        gliss(tr, "zheng", tr.tb(bar + 2, 1.0), sc, 6, 0, rz, dt=0.07, vel=0.3, ring=2.0)
    prog = [0, 0, -2, -2, 1, 1, 0, 0, -1, -1, -2, -2, 0, 1, 0, 0]
    rb = tr.r("bass")
    for bar, root in enumerate(prog):
        tr.zheng("bass", tr.tb(bar, 0), sc(root) - 24, 0.65, rb, ring=2.4, jitter=0.003)
        tr.zheng("bass", tr.tb(bar, 2), sc(root + 2) - 24, 0.35, rb, ring=1.2, jitter=0.003)
    rm = tr.r("melody")
    p1 = period(rm, R_34, lo=-1, hi=8, first=2)
    fl = []
    for p, notes in enumerate(p1):
        fl += to_flute(tr, simplify(notes, 1.0), sc, tr.tb(2 * p + 4), rm, octave=0, grace_p=0.35)
    tr.flute("flute", fl, tr.r("flute_sig"), kind="dizi", vib_depth=16, vib_rate=5.2)
    return tr.mix(t60=3.2, wet=0.48, predelay=0.04)


@music("tomb")
def m_tomb():
    """The Tomb of Sunscar: a buried palace that is still awake. A deep bowed drone, singing
    bowls, sand trickling, low pipa notes that sink, and a great bronze gong that answers the
    listener's footsteps from very far away."""
    tr = Track("tomb", 56, 4, 10)                      # 42.9 s
    sc = Scale(50, 4)                                  # D gong, B yu, tonic B3
    tr.bus("drone", -15, 0.3, (lowpass(700, 0.7), lowshelf(110, -3.0)))
    tr.bus("bowl", -12, 0.6)
    tr.bus("sand", -32, 0.5, (highpass(3000),))
    tr.bus("pluck", -2, 0.5, PIPA_BODY)
    tr.bus("gong", 2, 0.65)
    rd = tr.r("drone")
    tr.add("drone", drone(tr.L, tr.T, rd, [(mtof(35), 1.0), (mtof(42), 0.35), (mtof(47), 0.25), (mtof(41), 0.12)],
                          harm=(1.0, 0.55, 0.4, 0.25, 0.15, 0.08), swell=(2, 0.65), detune=5.0), 0)
    rb = tr.r("bowl")
    for bar, f0 in ((0, 246.9), (3, 220.0), (6, 293.7), (8, 246.9)):
        tr.add("bowl", bowl(f0, rb, dur=6.0), tr.tb(bar, 1.0), 0.6)
    rs = tr.r("sand")
    t = tvec(tr.L)
    trickle = pnoise(tr.L, rs, highpass(5000)) * (0.3 + 0.7 * np.clip(np.sin(TAU * 2 * t / tr.T + 0.7), 0, 1) ** 2)
    tr.add("sand", trickle, 0, 0.6)
    rp = tr.r("pluck")
    tp = 0.8
    while tp < tr.T - 1.0:
        i = int(rp.integers(-3, 4))
        if rp.random() < 0.45:
            tr.pipa("pluck", tp, sc(i) - 12, 0.6, rp, ring=3.0, bend=sink_bend(-70.0, 0.4, 1.6))
        else:
            tr.pipa("pluck", tp, sc(i) - 12, 0.5, rp, ring=2.4)
        tp += float(rp.choice([2.0, 2.5, 3.0, 4.0])) * tr.spb
    rg = tr.r("gong")
    g = gong(62.0, rg, dur=8.0, pitch=(0, -25), bloom=1.4, bright=0.7, thump=0.1)
    tr.add("gong", g, tr.tb(2), 0.75)
    tr.add("gong", gong(92.0, rg, dur=6.0, pitch=(0, -20), bloom=1.0, bright=0.6, thump=0.0), tr.tb(7, 2.0), 0.45)
    return tr.mix(t60=4.8, wet=0.58, predelay=0.06, hf=0.3)
