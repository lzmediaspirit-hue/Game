"""Jade River sound effects.

Each @sfx(id) function takes a seeded generator and returns a float signal; the builder
fades, peak-normalises (-3 dBFS) and writes it. Loops (loop=True) return one exact
period and are only gain-normalised, so they stay seamless.
"""
from __future__ import annotations

import numpy as np

from synth import (SR, TAU, ZHENG_BODY, add_reverb, bandpass, bell, bowl, bubble, chime, click,
                   decay, doublets, env_pts, fades, filt, gong, highpass, lowpass, membrane,
                   modal, mtof, noise, nsamp, peak, place, pluck, pnoise, rms, smoothstep, stft_shape,
                   stream, tvec, wind, woodblock, wrap_add, zheng_params, reverb_ir, convolve)

SFX = {}


def sfx(sid, loop=False):
    def deco(fn):
        SFX[sid] = (fn, loop)
        return fn
    return deco


# ---------------------------------------------------------------- helpers

def buf(sec):
    return np.zeros(nsamp(sec))


def at(y, sig, t, gain=1.0):
    place(y, sig, nsamp(t) if t > 0 else 0, gain)


def norm(x):
    return x / max(peak(x), 1e-9)


def whoosh(rng, dur, f_path, a_path, width=0.6, tilt_db=-1.0):
    """Noise through a moving band. f_path / a_path: [(fraction_of_dur, value)]."""
    n = nsamp(dur)
    x = rng.standard_normal(n)
    fts, fvs = zip(*f_path)
    ats, avs = zip(*a_path)
    lfv = np.log(np.asarray(fvs, dtype=float))

    def mag(t, f):
        u = np.clip(t / dur, 0.0, 1.0)
        fc = np.exp(np.interp(u, fts, lfv))
        a = np.interp(u, ats, avs)
        band = np.exp(-0.5 * (np.log2(np.maximum(f, 20.0) / fc) / width) ** 2)
        return a * band * (np.maximum(f, 50.0) / 1000.0) ** (tilt_db / 6.02)

    y = stft_shape(x, mag, win=512, hop=128)
    y *= np.interp(tvec(n) / dur, ats, avs) ** 0.5   # sharpen the envelope below frame size
    return norm(fades(y, 0.002, 0.01))


def grains(rng, dur, count, t_range, f_range, g_dur=(0.001, 0.004), amp=(0.3, 1.0), q=1.2, fall=0.0):
    """Scatter of tiny band-passed noise ticks (crackle, crinkle, pebbles)."""
    y = buf(dur)
    for _ in range(count):
        t = rng.uniform(*t_range)
        f = float(np.exp(rng.uniform(np.log(f_range[0]), np.log(f_range[1]))))
        k = nsamp(rng.uniform(*g_dur))
        g = rng.standard_normal(k + 8) * np.exp(-np.arange(k + 8) / max(1.0, k / 3.0))
        g = filt(g, bandpass(f, q), tail=0.004)
        a = rng.uniform(*amp)
        if fall:
            a *= np.exp(-fall * (t - t_range[0]))
        at(y, norm(g), t, a)
    return y


def plucks(rng, notes, dur, body=True, **kw):
    """Guzheng notes [(t, midi, vel, ring)] rendered through the body resonance."""
    y = buf(dur)
    for t, m, v, ring in notes:
        f = float(mtof(m))
        p = zheng_params(f)
        p.update(kw)
        at(y, pluck(f, rng, ring=ring, vel=v, **p), t, v)
    if body:
        y = filt(y, *ZHENG_BODY)[:len(y)]
    return y


def tone(freq_curve, harm, phase0=0.0):
    ph = TAU * np.cumsum(freq_curve) / SR + phase0
    out = np.zeros(len(freq_curve))
    fmax = float(np.max(freq_curve))
    for k, a in enumerate(harm, start=1):
        if a and k * fmax < 0.46 * SR:
            out += a * np.sin(k * ph)
    return out


# ---------------------------------------------------------------- combat

@sfx("hit")
def s_hit(rng):
    y = buf(0.3)
    at(y, membrane(105, rng, t60=0.14, drop=0.9, drop_tau=0.018, noise_amt=0.2, noise_fc=900, click_amt=0.0), 0, 1.0)
    k = nsamp(0.05)
    at(y, noise(k, rng, bandpass(1400, 0.8)) * decay(k, 0.03, 0.0005), 0, 0.6)
    k = nsamp(0.12)
    at(y, noise(k, rng, bandpass(340, 1.0)) * decay(k, 0.06, 0.001), 0, 0.7)
    return np.tanh(2.4 * norm(y))


@sfx("hit_crit")
def s_hit_crit(rng):
    y = buf(0.9)
    at(y, membrane(68, rng, t60=0.3, drop=1.1, drop_tau=0.02, noise_amt=0.3, noise_fc=600, click_amt=0.0), 0, 1.0)
    k = nsamp(0.06)
    at(y, noise(k, rng, bandpass(1600, 0.8)) * decay(k, 0.04, 0.0005), 0, 0.35)
    k = nsamp(0.15)
    at(y, noise(k, rng, lowpass(300, 0.8)) * decay(k, 0.1, 0.001), 0, 0.4)
    ring = modal(doublets([(2250, 1.0, 0.7), (3170, 0.7, 0.55), (4420, 0.5, 0.45), (5630, 0.35, 0.35),
                           (6890, 0.2, 0.25)], rng, (2.0, 6.0)), 0.85, rng, attack=0.002)
    y = np.tanh(1.4 * norm(y))
    at(y, norm(ring), 0.008, 0.32)
    return y


@sfx("hurt")
def s_hurt(rng):
    y = buf(0.4)
    at(y, membrane(74, rng, t60=0.26, drop=0.6, drop_tau=0.03, noise_amt=0.35, noise_fc=500, click_amt=0.0), 0)
    k = nsamp(0.2)
    at(y, noise(k, rng, bandpass(300, 0.8)) * decay(k, 0.12, 0.002), 0, 0.7)
    at(y, noise(k, rng, lowpass(220, 0.7)) * decay(k, 0.15, 0.002), 0, 0.4)
    return np.tanh(2.0 * norm(filt(y, lowpass(1300, 0.7))[:len(y)]))


@sfx("swing")
def s_swing(rng):
    return whoosh(rng, 0.34, [(0, 450), (0.45, 2000), (1, 700)], [(0, 0), (0.35, 1), (0.6, 0.55), (1, 0)],
                  width=0.55)


@sfx("technique")
def s_technique(rng):
    y = buf(1.3)
    at(y, whoosh(rng, 0.45, [(0, 350), (0.5, 1500), (1, 900)], [(0, 0), (0.4, 1), (1, 0)], width=0.7), 0, 0.6)
    notes = (1174.7, 1318.5, 1480.0, 1760.0)
    for k, f in enumerate(notes):
        c = chime(f, rng, dur=0.5 + 0.25 * k)
        if k == len(notes) - 1:
            c *= 1.0 + 0.3 * np.sin(TAU * 11.0 * tvec(len(c)))
        at(y, c, 0.12 + 0.07 * k, 0.3 + 0.08 * k)
    return add_reverb(y, rng, t60=1.0, wet=0.2, keep=len(y))


@sfx("jump")
def s_jump(rng):
    y = buf(0.26)
    at(y, whoosh(rng, 0.24, [(0, 300), (1, 1400)], [(0, 0), (0.3, 1), (1, 0)], width=0.6, tilt_db=-3.0), 0, 0.8)
    at(y, membrane(115, rng, t60=0.07, drop=0.3, noise_amt=0.4, noise_fc=900), 0, 0.3)
    return y


@sfx("land")
def s_land(rng):
    y = buf(0.2)
    at(y, membrane(105, rng, t60=0.09, drop=0.35, noise_amt=0.5, noise_fc=1200, click_amt=0.05), 0)
    at(y, grains(rng, 0.2, 12, (0.0, 0.05), (1800, 4000), amp=(0.15, 0.45)), 0)
    k = nsamp(0.07)
    at(y, noise(k, rng, bandpass(700, 0.8)) * decay(k, 0.05, 0.001), 0, 0.5)
    return np.tanh(1.5 * norm(y))


@sfx("dodge")
def s_dodge(rng):
    return whoosh(rng, 0.17, [(0, 900), (0.5, 3000), (1, 1600)], [(0, 0), (0.3, 1), (1, 0)], width=0.45,
                  tilt_db=0.0)


@sfx("parry")
def s_parry(rng):
    y = buf(1.1)
    parts = [(980, 0.55, 1.1), (1570, 1.0, 1.0), (2710, 0.8, 0.8), (3890, 0.6, 0.6), (5240, 0.45, 0.45),
             (6620, 0.3, 0.32), (8100, 0.18, 0.22)]
    at(y, norm(modal(doublets(parts, rng, (3.0, 9.0)), 1.1, rng, attack=0.0008)), 0)
    at(y, click(rng, 0.004, 3500.0, 0.5), 0, 0.5)
    at(y, membrane(190, rng, t60=0.08, drop=0.2, noise_amt=0.3), 0, 0.35)
    return y


@sfx("tell")
def s_tell(rng):
    y = buf(0.12)
    at(y, woodblock(1900, rng, t60=0.05, click_amt=0.6, bright=1.2), 0)
    at(y, norm(modal([(3300, 1.0, 0.1), (5100, 0.5, 0.06)], 0.12, rng, attack=0.0003)), 0.002, 0.3)
    return y


@sfx("enemy_die")
def s_enemy_die(rng):
    y = buf(0.55)
    at(y, whoosh(rng, 0.5, [(0, 1400), (1, 300)], [(0, 0), (0.08, 1), (1, 0)], width=1.0, tilt_db=-3.0), 0)
    n = nsamp(0.45)
    f = np.geomspace(620, 240, n)
    at(y, tone(f, (1.0, 0.2)) * decay(n, 0.35, 0.01), 0, 0.12)
    return y


@sfx("boss_roar")
def s_boss_roar(rng):
    d = 1.25
    n = nsamp(d)
    t = tvec(n)
    jit = filt(rng.standard_normal(n), lowpass(18, 0.6))
    jit /= max(rms(jit), 1e-9)
    f0 = np.interp(t, [0, 0.25, 0.8, d], [62, 82, 74, 55]) * (1.0 + 0.03 * jit)
    src = tone(f0, [1.0 / k for k in range(1, 65)])
    am = 1.0 + 0.55 * np.sin(TAU * np.cumsum(28.0 + 6.0 * jit) / SR)
    breath = noise(n, rng, bandpass(900, 0.5))
    x = norm(src) * am + 0.35 * breath

    def mag(tt, f):
        u = np.clip(tt / d, 0, 1)
        out = 0.25 * np.exp(-0.5 * (f / 260.0) ** 2)
        for (a0, a1), bw, amp in (((700, 450), 110, 1.0), ((1150, 800), 150, 0.6), ((2500, 2400), 220, 0.25)):
            fc = a0 + (a1 - a0) * u
            out = out + amp * np.exp(-0.5 * ((f - fc) / bw) ** 2)
        return out

    y = stft_shape(x, mag)
    y *= env_pts(n, [(0, 0), (0.12, 1), (0.8, 0.85), (d, 0)])
    y = filt(np.tanh(2.0 * norm(y)), lowpass(2600, 0.7))[:n]
    return add_reverb(y, rng, t60=0.8, wet=0.2, keep=n)


# ---------------------------------------------------------------- movement / world

@sfx("water_step")
def s_water_step(rng):
    y = buf(0.35)
    at(y, membrane(120, rng, t60=0.08, drop=0.3, noise_amt=0.3), 0, 0.5)
    k = nsamp(0.1)
    gr = np.abs(filt(rng.standard_normal(k), lowpass(60)))[:k]
    at(y, noise(k, rng, bandpass(2000, 0.5)) * decay(k, 0.06, 0.002) * (0.4 + gr / max(peak(gr), 1e-9)), 0, 0.7)
    at(y, bubble(rng, 900, tau=0.015, rise=0.9), 0.03, 0.4)
    at(y, bubble(rng, 1400, tau=0.01, rise=0.8), 0.07, 0.3)
    return y


@sfx("gather")
def s_gather(rng):
    y = buf(0.42)
    n = nsamp(0.28)
    env = np.zeros(n)
    for _ in range(40):
        c = rng.uniform(0.0, 0.26)
        w = rng.uniform(0.003, 0.01)
        env += rng.uniform(0.3, 1.0) * np.exp(-0.5 * ((tvec(n) - c) / w) ** 2)
    rust = noise(n, rng, bandpass(4000, 0.7)) * env * np.sin(np.pi * tvec(n) / 0.28) ** 0.5
    at(y, norm(rust), 0, 0.6)
    for dt, g in ((0.24, 1.0), (0.258, 0.7)):
        at(y, click(rng, 0.002, 5200.0, 2.0), dt, 0.5 * g)
        at(y, norm(modal([(4200, 1.0, 0.05), (6100, 0.5, 0.03)], 0.06, rng, attack=0.0003)), dt, 0.3 * g)
    return y


@sfx("mine")
def s_mine(rng):
    y = buf(0.45)
    at(y, click(rng, 0.004, 2500.0, 0.4), 0, 1.0)
    k = nsamp(0.15)
    at(y, noise(k, rng, bandpass(1800, 1.2)) * decay(k, 0.07, 0.0005), 0, 0.6)
    at(y, norm(modal([(2950, 1.0, 0.18), (4130, 0.6, 0.12), (5870, 0.3, 0.08)], 0.2, rng, attack=0.0005)), 0, 0.25)
    at(y, grains(rng, 0.45, 5, (0.08, 0.35), (3000, 5000), amp=(0.1, 0.25), fall=4.0), 0)
    at(y, membrane(140, rng, t60=0.08, drop=0.3, noise_amt=0.4), 0, 0.5)
    return y


@sfx("fish_bite")
def s_fish_bite(rng):
    y = buf(0.42)
    at(y, bubble(rng, 650, tau=0.03, rise=1.2), 0, 1.0)
    at(y, bubble(rng, 900, tau=0.02, rise=1.0), 0.05, 0.7)
    at(y, bubble(rng, 1200, tau=0.015, rise=0.8), 0.09, 0.5)
    k = nsamp(0.14)
    gr = np.abs(filt(rng.standard_normal(k), lowpass(80)))[:k]
    at(y, noise(k, rng, bandpass(2200, 0.6)) * decay(k, 0.08, 0.002) * norm(gr), 0.01, 0.35)
    return y


@sfx("cook")
def s_cook(rng):
    d = 1.05
    n = nsamp(d)
    y = 0.25 * noise(n, rng, highpass(2500), lowpass(8000))
    y *= 0.7 + 0.3 * np.abs(filt(rng.standard_normal(n), lowpass(12)))[:n] / 0.8
    y += grains(rng, d, 90, (0.0, d), (2000, 7000), g_dur=(0.0005, 0.003), amp=(0.1, 0.9))
    for _ in range(4):
        at(y, bubble(rng, rng.uniform(200, 400), tau=0.03, rise=0.6), rng.uniform(0.1, 0.8), 0.25)
    return y * env_pts(n, [(0, 0), (0.04, 1), (d - 0.35, 1), (d, 0)])


@sfx("forge")
def s_forge(rng):
    y = buf(1.15)
    parts = [(1045, 0.7, 1.1), (2380, 1.0, 0.9), (3740, 0.6, 0.7), (4460, 0.45, 0.55), (5920, 0.3, 0.4),
             (7310, 0.2, 0.3)]
    anvil = norm(modal(doublets(parts, rng, (2.0, 7.0)), 1.15, rng, attack=0.0005))
    at(y, anvil, 0, 1.0)
    at(y, click(rng, 0.003, 3000.0, 0.6), 0, 0.7)
    at(y, membrane(210, rng, t60=0.09, drop=0.3, noise_amt=0.4), 0, 0.45)
    at(y, anvil[:nsamp(0.6)] * decay(nsamp(0.6), 0.5), 0.1, 0.25)
    at(y, click(rng, 0.002, 3000.0, 0.6), 0.1, 0.2)
    return y


@sfx("alchemy")
def s_alchemy(rng):
    y = buf(1.1)
    at(y, whoosh(rng, 0.75, [(0, 250), (0.5, 800), (1, 400)], [(0, 0), (0.3, 1), (1, 0)], width=1.0,
                 tilt_db=-3.0), 0, 0.8)
    at(y, grains(rng, 0.75, 25, (0.1, 0.6), (1500, 5000), amp=(0.05, 0.2)), 0)
    for k in range(7):
        at(y, bubble(rng, rng.uniform(300, 900), tau=rng.uniform(0.02, 0.04), rise=rng.uniform(0.5, 1.2)),
           0.35 + 0.09 * k + rng.uniform(0, 0.04), rng.uniform(0.3, 0.6))
    return y


@sfx("break")
def s_break(rng):
    y = buf(0.65)
    k = nsamp(0.03)
    at(y, noise(k, rng, bandpass(2500, 0.6)) * decay(k, 0.012, 0.0003), 0, 1.0)
    at(y, grains(rng, 0.65, 18, (0.0, 0.07), (1500, 5000), amp=(0.3, 0.8), fall=20.0), 0)
    body = modal([(420, 0.8, 0.18), (1130, 0.6, 0.12), (2250, 0.4, 0.08), (3380, 0.25, 0.06)], 0.3, rng,
                 attack=0.0005)
    at(y, norm(body), 0, 0.6)
    for _ in range(12):
        t = rng.uniform(0.06, 0.5)
        f = rng.uniform(2500, 6000)
        s = modal([(f, 1.0, rng.uniform(0.04, 0.1)), (f * 1.7, 0.4, 0.04)], 0.12, rng, attack=0.0003)
        at(y, norm(s), t, 0.3 * np.exp(-4.0 * t))
    at(y, membrane(150, rng, t60=0.1, drop=0.3, noise_amt=0.5), 0, 0.5)
    return y


@sfx("portal")
def s_portal(rng):
    d = 1.4
    y = buf(d)
    at(y, whoosh(rng, d, [(0, 250), (0.45, 1400), (1, 500)], [(0, 0), (0.4, 1), (1, 0)], width=0.8), 0, 0.8)
    n = nsamp(d)
    t = tvec(n)
    sh = np.zeros(n)
    for _ in range(28):
        f = rng.uniform(2000, 7000)
        c = rng.uniform(0.2, 1.1)
        env = np.exp(-0.5 * ((t - c) / 0.15) ** 2) * (1.0 + 0.6 * np.sin(TAU * rng.uniform(10, 18) * t))
        sh += rng.uniform(0.3, 1.0) * env * np.sin(TAU * f * t + rng.uniform(0, TAU))
    at(y, norm(sh), 0, 0.3)
    sub = tone(np.geomspace(70, 55, n), (1.0,)) * np.sin(np.pi * t / d) ** 2
    at(y, sub, 0, 0.35)
    return add_reverb(y, rng, t60=1.5, wet=0.3, keep=n)


@sfx("mail")
def s_mail(rng):
    y = buf(0.85)
    at(y, whoosh(rng, 0.22, [(0, 2000), (1, 4500)], [(0, 0), (0.5, 1), (1, 0)], width=0.9), 0, 0.45)
    at(y, grains(rng, 0.3, 8, (0.0, 0.2), (3000, 6000), amp=(0.05, 0.15)), 0)
    at(y, bell(1568.0, rng, dur=0.7, kind="small", strike=0.25), 0.13, 0.7)
    return add_reverb(y, rng, t60=0.8, wet=0.15, keep=len(y))


# ---------------------------------------------------------------- progression / cultivation

@sfx("pickup")
def s_pickup(rng):
    y = buf(0.85)
    at(y, chime(1174.7, rng, 0.45), 0, 0.7)
    at(y, chime(1760.0, rng, 0.7), 0.075, 0.85)
    return add_reverb(y, rng, t60=0.8, wet=0.15, keep=len(y))


@sfx("coin")
def s_coin(rng):
    def ding(f):
        parts = [(f, 1.0, 0.45), (f * 1.46, 0.5, 0.3), (f * 2.26, 0.35, 0.2), (f * 2.87, 0.2, 0.15)]
        s = norm(modal(doublets(parts, rng, (4.0, 12.0)), 0.5, rng, attack=0.0004))
        s[:nsamp(0.002)] += 0.3 * click(rng, 0.0015, 5000.0, 1.0)[:nsamp(0.002)]
        return s

    y = buf(0.55)
    at(y, ding(2350.0), 0, 1.0)
    at(y, ding(2490.0), 0.055, 0.45)
    return y


@sfx("breakthrough")
def s_breakthrough(rng):
    d = 2.6
    y = buf(d)
    at(y, gong(105.0, rng, dur=d, pitch=(0, -35), tau=0.8, bloom=0.4, bright=0.75), 0, 0.9)
    at(y, membrane(58, rng, t60=0.8, drop=0.5, noise_amt=0.25), 0, 0.7)
    midis = [74, 76, 78, 81, 83, 86, 88, 90, 93, 95]
    for k, m in enumerate(midis):
        c = chime(float(mtof(m)), rng, dur=max(0.6, 1.3 - 0.05 * k))
        c *= 1.0 + 0.25 * np.sin(TAU * 9.0 * tvec(len(c)) + k)
        at(y, c, 0.25 + 0.085 * k, 0.3 + 0.02 * k)
    n = nsamp(d)
    t = tvec(n)
    pad = sum(np.sin(TAU * f * t + p) for f, p in ((1760, 0.0), (1975.5, 1.0), (2349.3, 2.0), (2637.0, 3.0)))
    pad *= smoothstep((t - 0.4) / 1.0) * (1.0 - smoothstep((t - 1.6) / 1.0)) * (1.0 + 0.3 * np.sin(TAU * 7.0 * t))
    at(y, norm(pad), 0, 0.15)
    return add_reverb(y, rng, t60=2.0, wet=0.35, keep=n)


@sfx("fail")
def s_fail(rng):
    d = 0.95
    n = nsamp(d)
    t = tvec(n)
    ratio = 2.0 ** (-5.0 * (t / d) ** 0.8 / 12.0)
    y = tone(220.0 * ratio, (1.0, 0.35, 0.15)) + tone(233.08 * ratio, (1.0, 0.35, 0.15))
    y = filt(y, lowpass(1200, 0.7))[:n] * decay(n, 1.2, 0.01) * (1.0 - smoothstep((t - d + 0.25) / 0.25))
    at(y, membrane(80, rng, t60=0.2, drop=0.4, noise_amt=0.3) * peak(y), 0, 0.4)
    return y


@sfx("level")
def s_level(rng):
    d = 1.5
    notes = [(0.065 * k, m, 0.55 + 0.05 * k, 1.2) for k, m in enumerate((62, 64, 66, 69, 71, 74))]
    y = plucks(rng, notes, d)
    ch = buf(d)
    for f, g in ((587.3, 0.5), (880.0, 0.4), (1174.7, 0.35)):
        at(ch, chime(f, rng, dur=1.0), 0.42, g)
    y = norm(y) + 0.8 * norm(ch)
    return add_reverb(y, rng, t60=1.2, wet=0.25, keep=len(y))


@sfx("unlock")
def s_unlock(rng):
    y = buf(1.3)
    at(y, bell(1318.5, rng, dur=1.2, kind="small", strike=0.3), 0, 1.0)
    at(y, bell(1975.5, rng, dur=1.0, kind="small", strike=0.2), 0.11, 0.6)
    return add_reverb(y, rng, t60=1.0, wet=0.2, keep=len(y))


@sfx("quest_accept")
def s_quest_accept(rng):
    y = plucks(rng, [(0.0, 69, 0.6, 0.8), (0.14, 74, 0.7, 0.8)], 0.9)
    return add_reverb(y, rng, t60=0.9, wet=0.2, keep=len(y))


@sfx("quest_complete")
def s_quest_complete(rng):
    notes = [(0.0, 69, 0.6, 0.7), (0.13, 71, 0.65, 0.7), (0.26, 74, 0.8, 1.1), (0.26, 50, 0.45, 1.1)]
    y = norm(plucks(rng, notes, 1.4))
    at(y, chime(1174.7, rng, dur=1.0), 0.26, 0.25)
    return add_reverb(y, rng, t60=1.0, wet=0.22, keep=len(y))


@sfx("meditate")
def s_meditate(rng):
    b = bowl(293.66, rng, dur=6.0, strike=0.15)[:nsamp(2.0)]
    return fades(b, 0.0, 0.6)


@sfx("backlash")
def s_backlash(rng):
    d = 1.25
    n = nsamp(d)
    t = tvec(n)
    y = buf(d)
    k = nsamp(0.03)
    at(y, noise(k, rng, highpass(1200)) * decay(k, 0.02, 0.0003), 0, 1.0)
    at(y, grains(rng, d, 14, (0.0, 0.08), (1500, 6000), amp=(0.3, 0.8), fall=15.0), 0)
    ratio = 2.0 ** (-3.0 * (t / d) / 12.0)
    hum = tone(58.0 * ratio, (1.0, 0.6, 0.4, 0.25, 0.15)) + tone(61.5 * ratio, (1.0, 0.6, 0.4, 0.25, 0.15))
    hum = np.tanh(1.5 * norm(hum)) * env_pts(n, [(0, 0), (0.03, 1), (0.5, 0.7), (d, 0)])
    at(y, hum, 0, 0.8)
    return y


# ---------------------------------------------------------------- ui

@sfx("ui_tap")
def s_ui_tap(rng):
    return woodblock(1500, rng, t60=0.028, click_amt=0.25, bright=0.7)[:nsamp(0.06)]


@sfx("ui_open")
def s_ui_open(rng):
    y = buf(0.26)
    at(y, whoosh(rng, 0.26, [(0, 1400), (1, 4800)], [(0, 0), (0.6, 1), (1, 0)], width=0.8, tilt_db=-2.0), 0)
    at(y, grains(rng, 0.26, 6, (0.02, 0.2), (3000, 6000), amp=(0.05, 0.12)), 0)
    return y


@sfx("ui_close")
def s_ui_close(rng):
    y = whoosh(rng, 0.22, [(0, 1300), (1, 4200)], [(0, 0), (0.6, 1), (1, 0)], width=0.8, tilt_db=-2.0)
    return fades(y[::-1], 0.002, 0.012)


@sfx("error")
def s_error(rng):
    d = 0.28
    n = nsamp(d)
    t = tvec(n)
    f = np.interp(t, [0, d], [110, 104])
    y = tone(f, [1.0 / k if k % 2 else 0.0 for k in range(1, 16)])
    y *= 1.0 + 0.15 * np.sin(TAU * 30.0 * t)
    y = filt(y, lowpass(650, 0.7))[:n]
    return y * env_pts(n, [(0, 0), (0.008, 1), (d - 0.05, 0.9), (d, 0)])


# ---------------------------------------------------------------- hazards (S17)

@sfx("rumble")
def s_rumble(rng):
    """Stone shifting in a quarry wall: a low roll and a trickle of grit (the rockfall warning)."""
    d = 0.9
    n = nsamp(d)
    y = norm(noise(n, rng, lowpass(150, 0.7)) * env_pts(n, [(0, 0), (0.25, 1), (0.6, 0.8), (d, 0)]))
    return y + 0.35 * grains(rng, d, 26, (0.05, 0.8), (1800, 4500), amp=(0.2, 0.7))


@sfx("rockfall")
def s_rockfall(rng):
    """A boulder landing: a heavy thud, a crack, then scattering stones."""
    y = buf(0.8)
    at(y, membrane(70, rng, t60=0.25, drop=0.4, noise_amt=0.6), 0, 1.0)
    k = nsamp(0.05)
    at(y, noise(k, rng, bandpass(900, 0.7)) * decay(k, 0.02, 0.0005), 0, 0.6)
    at(y, grains(rng, 0.8, 30, (0.02, 0.5), (900, 4000), g_dur=(0.002, 0.008), amp=(0.2, 0.8), fall=6.0), 0, 0.7)
    return add_reverb(y, rng, t60=0.6, wet=0.2, keep=len(y))


@sfx("thunder")
def s_thunder(rng):
    """A close strike: a sharp crack, then the roll across the plain."""
    d = 1.6
    n = nsamp(d)
    y = buf(d)
    k = nsamp(0.06)
    at(y, noise(k, rng, highpass(1200, 0.7)) * decay(k, 0.02, 0.0002), 0, 1.0)
    roll = noise(n, rng, lowpass(220, 0.6)) * env_pts(n, [(0, 0), (0.05, 1), (0.4, 0.7), (0.9, 0.45), (d, 0)])
    at(y, norm(roll), 0.02, 0.9)
    at(y, grains(rng, d, 20, (0.0, 0.25), (2000, 7000), amp=(0.2, 0.6), fall=10.0), 0, 0.5)
    return add_reverb(y, rng, t60=1.2, wet=0.3, keep=n)


@sfx("charge")
def s_charge(rng):
    """Static gathering before a strike: a rising crackle (the lightning warning)."""
    d = 0.8
    return grains(rng, d, 70, (0.0, 0.78), (2500, 8000), amp=(0.1, 1.0), fall=-2.5) + 0.3 * whoosh(
        rng, d, [(0, 2000), (1, 5000)], [(0, 0), (0.9, 1), (1, 0)], width=0.5, tilt_db=0.0)


@sfx("gust")
def s_gust(rng):
    """A wind gust sweeping through."""
    return whoosh(rng, 1.4, [(0, 450), (0.4, 950), (1, 380)], [(0, 0), (0.35, 1), (0.7, 0.8), (1, 0)], width=1.1, tilt_db=-2.0)


@sfx("surge")
def s_surge(rng):
    """Whitewater rising: a rushing band and bubbles."""
    d = 1.2
    y = whoosh(rng, d, [(0, 600), (0.5, 1500), (1, 700)], [(0, 0), (0.4, 1), (1, 0)], width=1.2, tilt_db=-1.5)
    for _ in range(14):
        at(y, bubble(rng, rng.uniform(500, 1400), tau=0.015), rng.uniform(0.1, 1.0), 0.25)
    return y


@sfx("hiss")
def s_hiss(rng):
    """A gas vent breathing out."""
    d = 1.0
    n = nsamp(d)
    y = norm(noise(n, rng, bandpass(4200, 0.8)) * env_pts(n, [(0, 0), (0.15, 1), (0.8, 0.6), (d, 0)]))
    return y + 0.25 * grains(rng, d, 10, (0.1, 0.9), (300, 900), g_dur=(0.01, 0.03), amp=(0.3, 0.7))


@sfx("frost")
def s_frost(rng):
    """A freezing blast: high wind with ice crystals ticking in it."""
    d = 1.3
    y = whoosh(rng, d, [(0, 1600), (0.5, 2600), (1, 1400)], [(0, 0), (0.3, 1), (0.8, 0.7), (1, 0)], width=0.8, tilt_db=0.0)
    return y + 0.3 * grains(rng, d, 40, (0.1, 1.2), (5000, 9000), amp=(0.2, 0.8))


# ---------------------------------------------------------------- ambience loops (6 s)

AMB_T = 6.0


def _amb_len():
    return nsamp(AMB_T)


def _loop_reverb(x, rng, t60=1.2, wet=0.3):
    ir = reverb_ir(rng, t60=t60, predelay=0.02)
    return x + wet * convolve(x, ir, circular=True)


@sfx("wind_ambience", loop=True)
def s_wind_ambience(rng):
    n = _amb_len()
    T = n / SR
    t = tvec(n)
    body = wind(n, T, rng, base=380, spread=700, width=0.95, cycles=(1, 2, 3, 5, 7), floor=0.5, whistle=0.08)
    high = wind(n, T, rng, base=1400, spread=1600, width=0.7, cycles=(2, 3, 4, 6, 9), floor=0.15)
    gust = 0.5 + 0.3 * np.sin(TAU * 3 * t / T + rng.uniform(0, TAU)) + 0.2 * np.sin(TAU * 5 * t / T + rng.uniform(0, TAU))
    grain = np.abs(pnoise(n, rng, lowpass(25, 0.7)))
    rustle = pnoise(n, rng, highpass(2800), lowpass(7000)) * grain * gust ** 2
    y = body + 0.35 * high + 0.1 * rustle
    return _loop_reverb(filt(y, highpass(60), circular=True), rng, 1.0, 0.2)


@sfx("water_ambience", loop=True)
def s_water_ambience(rng):
    n = _amb_len()
    T = n / SR
    t = tvec(n)
    brook = stream(n, T, rng, density=45)
    lap = pnoise(n, rng, lowpass(400, 0.7)) * (1.0 + 0.5 * np.sin(TAU * 3 * t / T + rng.uniform(0, TAU)))
    y = brook + 0.35 * lap
    return _loop_reverb(y, rng, 0.9, 0.2)


VOWELS = ((730, 1090, 2440), (530, 1840, 2480), (270, 2290, 3010), (570, 840, 2410), (300, 870, 2240),
          (660, 1720, 2410), (490, 1350, 1690))


def _talker(n, T, rng, level):
    """One unintelligible talker: noisy + faintly voiced source through moving formants."""
    syl = []
    tpos = 0.0
    while tpos < T:
        if rng.random() < 0.18:
            tpos += rng.uniform(0.3, 1.1)
            continue
        d = rng.uniform(0.11, 0.26)
        syl.append((tpos, d, VOWELS[int(rng.integers(len(VOWELS)))], rng.uniform(0.5, 1.0)))
        tpos += d + rng.uniform(0.0, 0.05)
    t = tvec(n)
    amp = np.zeros(n)
    for s, d, _, a in syl:
        m = nsamp(d)
        u = np.arange(m) / m
        wrap_add(amp, a * np.sin(np.pi * u) ** 1.5, nsamp(s))
    centers = np.array([s + d / 2 for s, d, _, _ in syl])
    fmts = np.array([v for _, _, v, _ in syl], dtype=float)
    cx = np.concatenate([centers - T, centers, centers + T])
    fx = np.concatenate([fmts, fmts, fmts])
    base = rng.choice([rng.uniform(95, 140), rng.uniform(170, 240)])
    pv = base * rng.uniform(0.85, 1.2, len(syl))
    f0 = np.interp(t, cx, np.concatenate([pv, pv, pv]))
    cycles = np.sum(f0) / SR
    f0 *= max(1.0, round(cycles)) / cycles                     # whole cycles per loop
    ph = TAU * np.cumsum(f0) / SR
    voiced = sum(np.sin(k * ph) / k ** 1.2 for k in range(1, 30))
    src = 0.35 * voiced / max(rms(voiced), 1e-9) + 0.65 * pnoise(n, rng)

    def mag(tt, f):
        tt = np.mod(tt, T)
        out = np.zeros(np.broadcast(tt, f).shape)
        for j, bw, a in ((0, 90.0, 1.0), (1, 130.0, 0.55), (2, 200.0, 0.25)):
            fc = np.interp(tt, cx, fx[:, j])
            out = out + a * np.exp(-0.5 * ((f - fc) / bw) ** 2)
        return out

    y = stft_shape(src, mag, circular=True) * amp
    return level * y / max(rms(y), 1e-9)


@sfx("crowd_ambience", loop=True)
def s_crowd_ambience(rng):
    n = _amb_len()
    T = n / SR
    t = tvec(n)
    y = np.zeros(n)
    for _ in range(12):
        y += _talker(n, T, rng, float(rng.lognormal(0.0, 0.35)))
    bed = pnoise(n, rng, bandpass(500, 0.5)) * (1.0 + 0.25 * np.sin(TAU * 2 * t / T + rng.uniform(0, TAU)))
    y = y / max(rms(y), 1e-9) + 0.35 * bed
    y = filt(y, lowpass(3000, 0.6), highpass(120), circular=True)
    return _loop_reverb(y, rng, 1.1, 0.35)
