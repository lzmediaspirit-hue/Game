"""Decision 43's sound pass: the top-down world's layered hits, whooshes, casts, footsteps, landings, foes' tells and
deaths, the world's small sounds, dialogue and scene cues, and the stingers (docs/redesign/sound.md).

Registered into sfx.SFX like every other effect (the builder fades, normalises and writes them; its VOLUME table
sets each one's level from its loudness). Variants of one sound (`_a`, `_b`, ...) are the same recipe with its own
seed (rng_for is keyed by the id) and a small change of pitch, so round robins never repeat a waveform.

A hit is three sounds the director plays as one (scripts/audio/audio_director.gd `hit`):
  hit_<family>_<v>   the weapon's transient, 60-200 ms: what the edge, shaft or palm does on contact
  hit_on_<mat>_<v>   the struck body: flesh, shell, wood (and puppets), slime (and water)
  hit_tail_<family>  the weapon's tail, played when the hit-stop lets go (the blade's ring, the bell's hum)
plus an accent for a crit or finisher, the chain's last blow, and a weave cancel.

Every low sound carries harmonics above 300 Hz, so a phone speaker (which plays nothing under ~200 Hz) still hears
its weight; the builder fails any new sound whose energy lives only in the sub-bass.
"""
from __future__ import annotations

import numpy as np

from synth import (SR, TAU, add_reverb, bandpass, bell, bubble, chime, click, cymbal, decay, doublets, env_pts,
                   fades, filt, flute, gong, highpass, lowpass, membrane, modal, mtof, noise, nsamp, peak, pluck,
                   pipa_params, smoothstep, tvec, woodblock)
from sfx import SFX, at, buf, grains, norm, plucks, sfx, tone, whoosh

FAMILIES = ("sword", "sabre", "spear", "fan", "brush", "flute", "bell", "bow", "fists")
MATERIALS = ("flesh", "shell", "wood", "slime")
SURFACES = ("grass", "dirt", "stone", "wood", "sand", "water", "reeds", "roof", "snow")
ELEMENTS = ("qi", "fire", "water", "wind", "thunder", "earth", "metal", "wood", "soul", "space", "time")
RACES = ("beast", "human", "construct", "spirit", "water")
VARIANTS = "abcd"


def reg(sid, fn, loop=False):
    SFX[sid] = (fn, loop)


# ---------------------------------------------------------------- helpers

def sat(x, drive=2.0):
    """Soft saturation: harmonics over a low thump so a small speaker hears it."""
    x = norm(x)
    return np.tanh(drive * x) / np.tanh(drive)


def burst(rng, dur, *resps, t60=None, attack=0.0004):
    """A band of noise with a fast exponential decay."""
    n = nsamp(dur)
    return noise(n, rng, *resps)[:n] * decay(n, t60 or dur * 0.5, attack)


def metal(rng, parts, dur, beat=(2.0, 7.0), attack=0.0004):
    """A struck piece of metal: inharmonic partials [(freq, amp, t60)] as beating doublets."""
    return norm(modal(doublets(parts, rng, beat), dur, rng, attack=attack))


def thump(rng, f0, t60=0.1, drop=0.5, drive=2.2, noise_amt=0.35, noise_fc=1200.0):
    """A body blow: a membrane with a pitch drop, saturated so its weight reaches past 300 Hz."""
    m = membrane(f0, rng, t60=t60, drop=drop, noise_amt=noise_amt, noise_fc=noise_fc, click_amt=0.05)
    return sat(m, drive)


def hp(x, fc=90.0):
    return filt(x, highpass(fc, 0.7))[:len(x)]


def sweep_tone(f0, f1, dur, harm=(1.0, 0.3, 0.1), env=None, curve="exp"):
    n = nsamp(dur)
    u = np.linspace(0.0, 1.0, n)
    f = f0 * (f1 / f0) ** u if curve == "exp" else f0 + (f1 - f0) * u
    y = tone(f, harm)
    return y * (env if env is not None else np.sin(np.pi * u) ** 0.8)


def formant_noise(rng, dur, f0, formants, voiced=0.5, f_end=None, jitter=0.02):
    """A breathy voiced source through resonances (a growl, a grunt, a croak): formants [(fc, bw, amp)]."""
    n = nsamp(dur)
    t = tvec(n)
    f = np.full(n, float(f0)) if f_end is None else np.geomspace(f0, f_end, n)
    f = f * (1.0 + jitter * filt(rng.standard_normal(n), lowpass(25.0))[:n] / 0.15)
    ph = TAU * np.cumsum(f) / SR
    src = voiced * sum(np.sin(k * ph) / k for k in range(1, 40) if k * f0 < 0.45 * SR) + (1.0 - voiced) * rng.standard_normal(n)

    def mag(tt, ff):
        out = np.zeros(np.broadcast(tt, ff).shape)
        for fc, bw, a in formants:
            out = out + a * np.exp(-0.5 * ((ff - fc) / bw) ** 2)
        return out

    from synth import stft_shape
    return norm(stft_shape(src, mag, win=512, hop=128))


def pent(i, gong=62):
    """The D gong pentatonic the stingers and qi notes share (i steps from D4)."""
    p = (0, 2, 4, 7, 9)
    return gong + 12 * (i // 5) + p[i % 5]


# ---------------------------------------------------------------- hits: the weapon's transient

def hit_transient(fam, k):
    """k: the variant's index (a small pitch step between round robins)."""
    def fn(rng):
        s = (1.0, 0.94, 1.05, 0.9)[k]
        y = buf(0.2)
        if fam == "sword":
            at(y, burst(rng, 0.012, highpass(2600), t60=0.008), 0, 0.9)
            at(y, metal(rng, [(2870 * s, 1.0, 0.07), (4130 * s, 0.7, 0.05), (5620 * s, 0.5, 0.04), (7310 * s, 0.3, 0.03)], 0.1), 0.001, 0.5)
            at(y, burst(rng, 0.04, bandpass(760 * s, 0.9), t60=0.025), 0, 0.55)
            at(y, thump(rng, 140 * s, t60=0.05, drop=0.4, drive=1.6), 0, 0.25)
        elif fam == "sabre":
            at(y, thump(rng, 150 * s, t60=0.08, drop=0.6, drive=2.6), 0, 0.9)
            at(y, metal(rng, [(1120 * s, 1.0, 0.1), (1930 * s, 0.7, 0.08), (2710 * s, 0.5, 0.06), (3590 * s, 0.3, 0.05)], 0.14), 0.002, 0.45)
            at(y, burst(rng, 0.03, bandpass(1800 * s, 0.8), t60=0.018), 0, 0.6)
        elif fam == "spear":
            at(y, click(rng, 0.003, 3500 * s, 0.7), 0, 0.8)
            at(y, burst(rng, 0.015, bandpass(2500 * s, 1.0), t60=0.006), 0, 0.6)
            at(y, metal(rng, [(4460 * s, 1.0, 0.04), (6120 * s, 0.4, 0.03)], 0.06), 0.001, 0.3)
            at(y, woodblock(420 * s, rng, t60=0.05, click_amt=0.3, bright=0.7), 0.004, 0.55)
            at(y, thump(rng, 170 * s, t60=0.04, drop=0.3, drive=1.8), 0, 0.3)
        elif fam == "fan":
            for dt, g in ((0.0, 1.0), (0.006, 0.7)):
                at(y, burst(rng, 0.03, bandpass(2200 * s, 0.8), t60=0.02), dt, 0.7 * g)
            at(y, woodblock(1800 * s, rng, t60=0.02, click_amt=0.4, bright=1.1), 0.001, 0.4)
            at(y, thump(rng, 210 * s, t60=0.035, drop=0.2, drive=1.5), 0, 0.25)
        elif fam == "brush":
            at(y, burst(rng, 0.035, lowpass(1300 * s), highpass(200), t60=0.02), 0, 0.8)
            for j in range(4):
                at(y, bubble(rng, (700 + 220 * j) * s, tau=0.008, rise=0.9), 0.004 + 0.009 * j, 0.35)
            at(y, grains(rng, 0.12, 14, (0.0, 0.05), (3000, 6500), amp=(0.1, 0.4), fall=25.0), 0, 0.6)
        elif fam == "flute":
            at(y, woodblock(1100 * s, rng, t60=0.04, click_amt=0.5, bright=0.9), 0, 0.7)
            n = nsamp(0.07)
            blip = tone(np.full(n, float(mtof(pent(8 + k))) * 1.0), (1.0, 0.25, 0.08)) * decay(n, 0.06, 0.002)
            at(y, blip, 0.002, 0.45)
            at(y, burst(rng, 0.04, bandpass(2400, 0.6), t60=0.03), 0, 0.25)
        elif fam == "bell":
            at(y, bell(880 * s, rng, dur=0.2, kind="small", strike=0.6), 0, 0.8)
            at(y, thump(rng, 220 * s, t60=0.05, drop=0.3, drive=1.8), 0, 0.5)
            at(y, click(rng, 0.002, 3000, 0.8), 0, 0.3)
        elif fam == "bow":
            at(y, woodblock(610 * s, rng, t60=0.035, click_amt=0.5, bright=0.8), 0, 0.7)
            at(y, burst(rng, 0.012, bandpass(1500 * s, 0.8), t60=0.006), 0, 0.6)
            n = nsamp(0.08)
            shaft = tone(np.full(n, 140.0 * s), (1.0, 0.5, 0.35, 0.25, 0.18)) * decay(n, 0.07) * (1.0 + 0.6 * np.sin(TAU * 38 * tvec(n)))
            at(y, shaft, 0.004, 0.35)
        elif fam == "fists":
            at(y, thump(rng, 118 * s, t60=0.06, drop=0.7, drive=3.0, noise_amt=0.5), 0, 1.0)
            at(y, burst(rng, 0.014, bandpass(1800 * s, 0.9), t60=0.008), 0, 0.55)
            at(y, burst(rng, 0.05, bandpass(420 * s, 1.0), t60=0.03), 0, 0.35)
        return hp(fades(y, 0.0003, 0.02), 70.0)
    return fn


# ---------------------------------------------------------------- hits: the weapon's tail (after the hit-stop)

def hit_tail(fam):
    def fn(rng):
        y = buf(0.7)
        if fam == "sword":
            ring = metal(rng, [(2650, 1.0, 0.45), (3890, 0.6, 0.35), (5240, 0.4, 0.28), (6820, 0.2, 0.2)], 0.6, beat=(3.0, 9.0))
            at(y, ring, 0, 0.5)
            at(y, whoosh(rng, 0.22, [(0, 2400), (1, 1000)], [(0, 1), (1, 0)], width=0.5), 0, 0.8)
        elif fam == "sabre":
            at(y, whoosh(rng, 0.3, [(0, 900), (1, 380)], [(0, 1), (0.3, 0.8), (1, 0)], width=0.8, tilt_db=-2.0), 0, 0.9)
            at(y, metal(rng, [(920, 1.0, 0.35), (1540, 0.6, 0.3), (2310, 0.35, 0.2)], 0.45), 0, 0.35)
        elif fam == "spear":
            n = nsamp(0.28)
            vib = tone(np.full(n, 182.0), (1.0, 0.45, 0.3, 0.2, 0.12, 0.08)) * decay(n, 0.25) * (1.0 + 0.7 * np.sin(TAU * 24 * tvec(n)))
            at(y, vib, 0, 0.7)
            at(y, metal(rng, [(4460, 1.0, 0.2), (6120, 0.4, 0.12)], 0.25), 0, 0.2)
        elif fam == "fan":
            n = nsamp(0.3)
            fl = whoosh(rng, 0.3, [(0, 1600), (1, 900)], [(0, 1), (1, 0)], width=0.7)[:n] * (0.6 + 0.4 * np.sin(TAU * 26 * tvec(n)))
            at(y, fl, 0, 0.9)
        elif fam == "brush":
            at(y, grains(rng, 0.35, 22, (0.0, 0.25), (1500, 4500), g_dur=(0.002, 0.006), amp=(0.2, 0.8), fall=8.0), 0, 1.0)
            for _ in range(5):
                at(y, bubble(rng, rng.uniform(900, 2000), tau=0.006, rise=1.2), rng.uniform(0.02, 0.25), 0.25)
        elif fam == "flute":
            m = float(mtof(pent(10)))
            sig, pre = flute([(0.0, 0.3, 74.0, 0.8, {"scoop": False})], rng, kind="xiao", vib_depth=25.0)
            at(y, sig[nsamp(pre):] * decay(len(sig) - nsamp(pre), 0.35, 0.01), 0, 0.8)
            at(y, chime(m, rng, dur=0.45, strike=0.05), 0.0, 0.25)
        elif fam == "bell":
            at(y, bell(660, rng, dur=0.7, kind="small", strike=0.1), 0, 0.8)
        elif fam == "bow":
            n = nsamp(0.18)
            at(y, noise(n, rng, bandpass(3000, 0.7)) * decay(n, 0.15, 0.002) * (0.5 + 0.5 * np.sin(TAU * 55 * tvec(n))), 0, 0.6)
        elif fam == "fists":
            at(y, whoosh(rng, 0.22, [(0, 700), (1, 320)], [(0, 1), (1, 0)], width=0.9, tilt_db=-2.0), 0, 0.9)
        return hp(fades(y, 0.002, 0.05), 80.0)
    return fn


# ---------------------------------------------------------------- hits: the struck body

def hit_body(mat, k):
    def fn(rng):
        s = (1.0, 0.92, 1.07, 0.88)[k]
        y = buf(0.35)
        if mat == "flesh":
            at(y, thump(rng, 96 * s, t60=0.12, drop=0.6, drive=3.0, noise_amt=0.4, noise_fc=900), 0, 1.0)
            at(y, burst(rng, 0.07, bandpass(620 * s, 0.9), t60=0.05), 0.002, 0.55)
            n = nsamp(0.05)
            sq = noise(n, rng, bandpass(1300 * s, 1.2))[:n] * decay(n, 0.04, 0.003) * (0.5 + 0.5 * np.sin(TAU * 70 * tvec(n)))
            at(y, sq, 0.006, 0.3)
        elif mat == "shell":
            at(y, metal(rng, [(1310 * s, 1.0, 0.06), (3020 * s, 0.6, 0.04), (4720 * s, 0.4, 0.03), (6680 * s, 0.2, 0.02)], 0.08, beat=(8.0, 20.0)), 0, 0.8)
            at(y, burst(rng, 0.012, highpass(2000), t60=0.008), 0, 0.7)
            at(y, grains(rng, 0.2, 9, (0.005, 0.07), (3000, 6500), amp=(0.2, 0.6), fall=20.0), 0, 0.5)
            at(y, thump(rng, 160 * s, t60=0.05, drop=0.3, drive=2.0), 0, 0.45)
        elif mat == "wood":
            at(y, woodblock(380 * s, rng, t60=0.12, click_amt=0.4, bright=0.8), 0, 0.9)
            at(y, woodblock(740 * s, rng, t60=0.08, click_amt=0.2, bright=0.7), 0.002, 0.5)
            at(y, woodblock(520 * s, rng, t60=0.05, click_amt=0.3, bright=0.7), 0.045, 0.3)
            at(y, woodblock(610 * s, rng, t60=0.04, click_amt=0.3, bright=0.7), 0.075, 0.18)
        elif mat == "slime":
            n = nsamp(0.08)
            sq = noise(n, rng, lowpass(900 * s))[:n] * decay(n, 0.06, 0.002)
            at(y, sq, 0, 0.8)
            at(y, formant_noise(rng, 0.09, 120 * s, [(450 * s, 120, 1.0), (1150 * s, 200, 0.5)], voiced=0.25, f_end=90 * s) * decay(nsamp(0.09), 0.08), 0, 0.5)
            for j in range(5):
                at(y, bubble(rng, rng.uniform(300, 900) * s, tau=rng.uniform(0.01, 0.02), rise=rng.uniform(0.6, 1.4)), 0.01 + 0.03 * j + rng.uniform(0, 0.02), 0.45)
            at(y, thump(rng, 110 * s, t60=0.06, drop=0.2, drive=1.6, noise_amt=0.2), 0, 0.35)
        return hp(fades(y, 0.0003, 0.03), 70.0)
    return fn


# ---------------------------------------------------------------- hits: accents

@sfx("hit_accent_crit")
def s_hit_accent_crit(rng):
    """A crit or a finisher: a bright double ring over a heavy saturated thump."""
    y = buf(0.75)
    at(y, thump(rng, 72, t60=0.25, drop=0.9, drive=3.0, noise_amt=0.3, noise_fc=700), 0, 0.9)
    at(y, metal(rng, [(3140, 1.0, 0.45), (4620, 0.6, 0.35), (6330, 0.35, 0.25)], 0.6, beat=(3.0, 6.0)), 0.004, 0.45)
    at(y, burst(rng, 0.05, bandpass(1600, 0.7), t60=0.03), 0, 0.4)
    return add_reverb(hp(y, 60.0), rng, t60=0.7, wet=0.18, keep=len(y))


@sfx("hit_accent_chain")
def s_hit_accent_chain(rng):
    """The chain's last blow: a rising qi zing that lands on a small cymbal flick."""
    y = buf(0.6)
    at(y, sweep_tone(1180, 2360, 0.09, harm=(1.0, 0.25), env=np.sin(np.pi * np.linspace(0, 1, nsamp(0.09)) * 0.5) ** 2), 0, 0.5)
    at(y, bell(2349.3, rng, dur=0.4, kind="small", strike=0.2), 0.08, 0.5)
    at(y, cymbal(rng, dur=0.35, t60=0.25, fmin=1500, count=30, noise_amt=0.6), 0.08, 0.35)
    return y


@sfx("hit_accent_weave")
def s_hit_accent_weave(rng):
    """A weave cancel: a quick flick of air and a tick, the blow folding into the next."""
    y = buf(0.12)
    at(y, whoosh(rng, 0.09, [(0, 3000), (1, 6000)], [(0, 0), (0.3, 1), (1, 0)], width=0.5, tilt_db=0.0), 0, 0.8)
    at(y, click(rng, 0.002, 4200, 1.0), 0.05, 0.5)
    return y


# ---------------------------------------------------------------- whooshes: a swing per family

def swing(fam):
    def fn(rng):
        if fam == "sword":
            return whoosh(rng, 0.22, [(0, 1200), (0.45, 3200), (1, 1500)], [(0, 0), (0.35, 1), (0.6, 0.5), (1, 0)], width=0.45, tilt_db=0.0)
        if fam == "sabre":
            y = whoosh(rng, 0.4, [(0, 300), (0.5, 900), (1, 380)], [(0, 0), (0.45, 1), (0.7, 0.6), (1, 0)], width=0.75, tilt_db=-2.5)
            return y + 0.3 * sat(whoosh(rng, 0.4, [(0, 160), (0.5, 320), (1, 180)], [(0, 0), (0.5, 1), (1, 0)], width=0.6), 1.5)
        if fam == "spear":
            y = whoosh(rng, 0.18, [(0, 800), (0.8, 2600), (1, 2200)], [(0, 0), (0.7, 1), (0.85, 0.4), (1, 0)], width=0.5, tilt_db=0.0)
            at(y, woodblock(330, rng, t60=0.03, click_amt=0.1, bright=0.6), 0.0, 0.25)
            return y
        if fam == "fan":
            y = whoosh(rng, 0.3, [(0, 900), (0.5, 1700), (1, 1000)], [(0, 0), (0.4, 1), (1, 0)], width=0.8, tilt_db=-1.0)
            return y * (0.65 + 0.35 * np.sin(TAU * 22 * tvec(len(y)))) + 0.3 * grains(rng, 0.3, 10, (0.05, 0.25), (3000, 6000), amp=(0.2, 0.6))
        if fam == "brush":
            y = whoosh(rng, 0.26, [(0, 1500), (0.5, 3000), (1, 2000)], [(0, 0), (0.3, 1), (1, 0)], width=0.9, tilt_db=-1.0)
            return y + 0.35 * grains(rng, 0.26, 20, (0.05, 0.22), (2500, 6500), amp=(0.2, 0.8), fall=6.0)
        if fam == "flute":
            y = buf(0.34)
            at(y, whoosh(rng, 0.3, [(0, 600), (0.5, 1400), (1, 800)], [(0, 0), (0.4, 1), (1, 0)], width=0.9), 0, 0.7)
            sig, pre = flute([(0.0, 0.18, 81.0, 0.7, {"scoop": True})], rng, kind="dizi", vib_depth=0.0)
            at(y, sig[nsamp(pre):], 0.05, 0.45)
            return y
        if fam == "bell":
            y = buf(0.4)
            at(y, whoosh(rng, 0.35, [(0, 500), (0.5, 1100), (1, 600)], [(0, 0), (0.45, 1), (1, 0)], width=0.8, tilt_db=-2.0), 0, 0.8)
            at(y, bell(1760, rng, dur=0.3, kind="small", strike=0.05), 0.12, 0.12)
            return y
        if fam == "bow":
            y = buf(0.35)
            s = pluck(110.0, rng, ring=0.28, t60=0.3, t60_hi=0.08, bright=0.9, pick=0.08, glide=30.0, nail=0.3)
            at(y, sat(s, 1.8), 0, 0.8)
            at(y, whoosh(rng, 0.14, [(0, 2000), (1, 4200)], [(0, 0), (0.2, 1), (1, 0)], width=0.45, tilt_db=0.0), 0.02, 0.6)
            return y
        return whoosh(rng, 0.16, [(0, 700), (0.5, 1800), (1, 900)], [(0, 0), (0.4, 1), (1, 0)], width=0.55, tilt_db=-0.5)
    return fn


# ---------------------------------------------------------------- techniques: a cast per element, a hit per element

def cast(el):
    def fn(rng):
        d = 0.9
        y = buf(d)
        at(y, whoosh(rng, 0.45, [(0, 350), (0.5, 1500), (1, 900)], [(0, 0), (0.4, 1), (1, 0)], width=0.7), 0, 0.45)
        if el == "qi":
            for k, m in enumerate((74, 76, 78, 81)):
                at(y, chime(float(mtof(m)), rng, dur=0.5), 0.1 + 0.06 * k, 0.28 + 0.05 * k)
        elif el == "fire":
            n = nsamp(0.7)
            roar = noise(n, rng, bandpass(700, 0.5), lowpass(3000))[:n] * env_pts(n, [(0, 0), (0.12, 1), (0.45, 0.6), (0.7, 0)])
            at(y, sat(roar, 1.5), 0.05, 0.8)
            at(y, grains(rng, 0.8, 50, (0.08, 0.7), (1500, 6000), g_dur=(0.0006, 0.003), amp=(0.1, 0.9)), 0, 0.5)
        elif el == "water":
            at(y, whoosh(rng, 0.6, [(0, 400), (0.5, 1200), (1, 500)], [(0, 0), (0.4, 1), (1, 0)], width=1.1), 0.05, 0.6)
            for _ in range(16):
                at(y, bubble(rng, rng.uniform(400, 1400), tau=rng.uniform(0.01, 0.03), rise=rng.uniform(0.5, 1.4)), rng.uniform(0.1, 0.6), 0.3)
        elif el == "wind":
            n = nsamp(0.8)
            g = whoosh(rng, 0.8, [(0, 600), (0.3, 1800), (0.6, 900), (1, 1500)], [(0, 0), (0.3, 1), (0.6, 0.6), (1, 0)], width=0.6)
            at(y, g * (0.7 + 0.3 * np.sin(TAU * 9 * tvec(n))), 0.02, 0.9)
        elif el == "thunder":
            at(y, grains(rng, 0.7, 90, (0.0, 0.45), (2000, 8000), amp=(0.1, 1.0), fall=-2.0), 0, 0.6)
            k = nsamp(0.05)
            at(y, noise(k, rng, highpass(1500))[:k] * decay(k, 0.02, 0.0002), 0.45, 0.9)
            at(y, sat(noise(nsamp(0.4), rng, lowpass(300))[:nsamp(0.4)] * decay(nsamp(0.4), 0.3), 2.0), 0.46, 0.5)
        elif el == "earth":
            n = nsamp(0.7)
            rum = sat(noise(n, rng, lowpass(260, 0.7))[:n] * env_pts(n, [(0, 0), (0.2, 1), (0.7, 0)]), 2.5)
            at(y, rum, 0.05, 0.8)
            at(y, grains(rng, 0.8, 30, (0.1, 0.7), (900, 3500), g_dur=(0.002, 0.008), amp=(0.2, 0.8)), 0, 0.6)
        elif el == "metal":
            at(y, whoosh(rng, 0.3, [(0, 2500), (1, 5000)], [(0, 0), (0.7, 1), (1, 0)], width=0.4, tilt_db=0.0), 0.1, 0.6)
            at(y, metal(rng, [(2310, 1.0, 0.6), (3470, 0.6, 0.45), (4980, 0.4, 0.3), (6240, 0.2, 0.2)], 0.7), 0.36, 0.55)
        elif el == "wood":
            at(y, grains(rng, 0.8, 40, (0.05, 0.6), (2500, 7000), g_dur=(0.002, 0.006), amp=(0.1, 0.6)), 0, 0.6)
            for j in range(3):
                at(y, woodblock(300 + 90 * j, rng, t60=0.18, click_amt=0.2, bright=0.7), 0.2 + 0.1 * j, 0.35)
        elif el == "soul":
            n = nsamp(0.8)
            wh = formant_noise(rng, 0.8, 220, [(800, 150, 1.0), (1300, 200, 0.6), (2600, 300, 0.3)], voiced=0.15, f_end=180)
            at(y, wh * env_pts(n, [(0, 0), (0.3, 1), (0.8, 0)]), 0, 0.6)
            for k, m in enumerate((81, 80, 76)):
                at(y, chime(float(mtof(m)), rng, dur=0.5), 0.2 + 0.1 * k, 0.2)
        elif el == "space":
            n = nsamp(0.8)
            ph = TAU * np.cumsum(np.geomspace(300, 1200, n)) / SR
            wob = (np.sin(ph) + 0.5 * np.sin(1.5 * ph + 0.3)) * env_pts(n, [(0, 0), (0.4, 1), (0.8, 0)]) * (0.6 + 0.4 * np.sin(TAU * 7 * tvec(n)))
            at(y, wob, 0, 0.45)
        elif el == "time":
            for j in range(6):
                at(y, woodblock(2200, rng, t60=0.02, click_amt=0.6, bright=1.0), 0.05 + 0.1 * j, 0.25 + 0.05 * j)
            at(y, bell(1318.5, rng, dur=0.4, kind="small", strike=0.2)[::-1], 0.2, 0.3)
        return add_reverb(hp(y, 80.0), rng, t60=0.8, wet=0.18, keep=len(y))
    return fn


def hit_element(el):
    def fn(rng):
        y = buf(0.3)
        if el == "qi":
            at(y, thump(rng, 150, t60=0.06, drop=0.5, drive=2.0), 0, 0.6)
            at(y, chime(1760, rng, dur=0.25, strike=0.5), 0, 0.5)
        elif el == "fire":
            at(y, burst(rng, 0.15, bandpass(900, 0.6), t60=0.1), 0, 0.8)
            at(y, grains(rng, 0.3, 30, (0.0, 0.2), (1500, 6000), g_dur=(0.0006, 0.003), amp=(0.1, 0.9), fall=8.0), 0, 0.6)
        elif el == "water":
            at(y, burst(rng, 0.1, bandpass(1200, 0.6), t60=0.07), 0, 0.7)
            for j in range(6):
                at(y, bubble(rng, rng.uniform(500, 1500), tau=0.012, rise=1.0), 0.01 + 0.02 * j, 0.4)
        elif el == "wind":
            at(y, whoosh(rng, 0.2, [(0, 2500), (1, 900)], [(0, 1), (1, 0)], width=0.6), 0, 0.9)
        elif el == "thunder":
            at(y, burst(rng, 0.02, highpass(1800), t60=0.01), 0, 0.9)
            at(y, grains(rng, 0.25, 30, (0.0, 0.15), (2500, 8000), amp=(0.2, 1.0), fall=15.0), 0, 0.6)
            at(y, thump(rng, 120, t60=0.08, drop=0.4, drive=2.5), 0, 0.5)
        elif el == "earth":
            at(y, thump(rng, 96, t60=0.12, drop=0.5, drive=4.0), 0, 0.9)
            at(y, burst(rng, 0.06, bandpass(700, 0.8), t60=0.04), 0, 0.45)
            at(y, grains(rng, 0.3, 14, (0.0, 0.12), (900, 3500), g_dur=(0.002, 0.008), amp=(0.3, 0.8), fall=10.0), 0, 0.6)
        elif el == "metal":
            at(y, metal(rng, [(2560, 1.0, 0.18), (3730, 0.6, 0.14), (5210, 0.4, 0.1)], 0.25), 0, 0.7)
            at(y, burst(rng, 0.01, highpass(2500), t60=0.006), 0, 0.6)
        elif el == "wood":
            at(y, woodblock(460, rng, t60=0.1, click_amt=0.4, bright=0.8), 0, 0.8)
            at(y, grains(rng, 0.25, 12, (0.0, 0.1), (2500, 6000), amp=(0.2, 0.6)), 0, 0.5)
        elif el == "soul":
            at(y, chime(1396.9, rng, dur=0.3, strike=0.1), 0, 0.5)
            at(y, whoosh(rng, 0.25, [(0, 1800), (1, 700)], [(0, 1), (1, 0)], width=0.8), 0, 0.6)
        elif el == "space":
            n = nsamp(0.2)
            at(y, sweep_tone(1400, 500, 0.2, harm=(1.0, 0.4, 0.2)), 0, 0.6)
            at(y, burst(rng, 0.02, bandpass(3000, 0.8), t60=0.01), 0, 0.5)
        elif el == "time":
            at(y, woodblock(2400, rng, t60=0.03, click_amt=0.8, bright=1.2), 0, 0.7)
            at(y, bell(1975.5, rng, dur=0.25, kind="small", strike=0.3), 0.01, 0.4)
        return hp(fades(y, 0.0003, 0.03), 80.0)
    return fn


# ---------------------------------------------------------------- footsteps and landings

def step_recipe(rng, surf, s=1.0, heavy=0.0):
    """One foot on a surface. heavy (0..1): a landing's extra weight."""
    y = buf(0.3 + 0.2 * heavy)
    w = 1.0 + heavy
    if surf == "grass":
        at(y, grains(rng, 0.2, 26, (0.0, 0.07), (1500 * s, 5000 * s), g_dur=(0.001, 0.004), amp=(0.2, 0.8), fall=12.0), 0, 0.8)
        at(y, burst(rng, 0.08, bandpass(2400 * s, 0.6), t60=0.05, attack=0.004), 0, 0.45)
        at(y, thump(rng, 110 * s, t60=0.04, drop=0.3, drive=1.4, noise_amt=0.2), 0, 0.3 * w)
    elif surf == "dirt":
        at(y, burst(rng, 0.07, bandpass(900 * s, 0.7), t60=0.04, attack=0.002), 0, 0.7)
        at(y, grains(rng, 0.15, 10, (0.0, 0.06), (2000 * s, 5000 * s), amp=(0.1, 0.5), fall=15.0), 0, 0.5)
        at(y, thump(rng, 120 * s, t60=0.05, drop=0.4, drive=1.8), 0, 0.5 * w)
    elif surf == "stone":
        at(y, click(rng, 0.003, 2600 * s, 0.8), 0, 0.7)
        at(y, metal(rng, [(1230 * s, 1.0, 0.03), (2870 * s, 0.5, 0.02), (4100 * s, 0.3, 0.015)], 0.05, beat=(10, 30)), 0, 0.45)
        at(y, burst(rng, 0.04, bandpass(3200 * s, 0.9), t60=0.02, attack=0.003), 0.05, 0.3)
        at(y, thump(rng, 150 * s, t60=0.03, drop=0.3, drive=1.6, noise_amt=0.2), 0, 0.3 * w)
    elif surf == "wood":
        at(y, woodblock(285 * s, rng, t60=0.09, click_amt=0.35, bright=0.75), 0, 0.8)
        at(y, woodblock(570 * s, rng, t60=0.05, click_amt=0.2, bright=0.7), 0.001, 0.4)
        if rng.random() < 0.5:
            n = nsamp(0.07)
            cr = tone(np.full(n, 420.0 * s) * (1 + 0.03 * np.sin(TAU * 31 * tvec(n))), (1.0, 0.5, 0.3)) * np.sin(np.pi * np.linspace(0, 1, n))
            at(y, cr, 0.03, 0.08)
        at(y, thump(rng, 130 * s, t60=0.05, drop=0.3, drive=1.6), 0, 0.3 * w)
    elif surf == "sand":
        at(y, grains(rng, 0.2, 60, (0.0, 0.09), (1800 * s, 6000 * s), g_dur=(0.0005, 0.002), amp=(0.1, 0.7), fall=8.0), 0, 0.9)
        at(y, burst(rng, 0.1, lowpass(2500 * s), highpass(400), t60=0.07, attack=0.01), 0, 0.4)
        at(y, thump(rng, 100 * s, t60=0.03, drop=0.2, drive=1.2, noise_amt=0.1), 0, 0.15 * w)
    elif surf == "water":
        n = nsamp(0.12)
        env = np.abs(filt(rng.standard_normal(n), lowpass(60))[:n])
        at(y, noise(n, rng, bandpass(1800 * s, 0.5))[:n] * decay(n, 0.08, 0.003) * (0.4 + env / max(peak(env), 1e-9)), 0, 0.7)
        for j in range(3 + int(2 * heavy)):
            at(y, bubble(rng, rng.uniform(700, 1500) * s, tau=0.012, rise=0.9), 0.02 + 0.03 * j, 0.35)
        at(y, burst(rng, 0.12, lowpass(700 * s), highpass(150), t60=0.08, attack=0.01), 0.01, 0.4 * w)
    elif surf == "reeds":
        n = nsamp(0.1)
        sq = formant_noise(rng, 0.1, 100 * s, [(380 * s, 110, 1.0), (900 * s, 160, 0.5)], voiced=0.2, f_end=80 * s)
        at(y, sq * decay(n, 0.09, 0.005), 0, 0.6)
        at(y, grains(rng, 0.25, 22, (0.02, 0.18), (3000 * s, 6500 * s), amp=(0.1, 0.5), fall=6.0), 0, 0.6)
        at(y, bubble(rng, 600 * s, tau=0.015, rise=0.7), 0.05, 0.25)
    elif surf == "roof":
        at(y, metal(rng, [(1810 * s, 1.0, 0.04), (3240 * s, 0.6, 0.03), (4710 * s, 0.35, 0.02)], 0.06, beat=(15, 40)), 0, 0.6)
        at(y, metal(rng, [(2050 * s, 1.0, 0.03), (3690 * s, 0.5, 0.02)], 0.05, beat=(15, 40)), 0.015, 0.35)
        at(y, grains(rng, 0.12, 6, (0.0, 0.05), (2500, 5000), amp=(0.1, 0.4)), 0, 0.4)
        at(y, thump(rng, 170 * s, t60=0.03, drop=0.3, drive=1.6), 0, 0.3 * w)
    elif surf == "snow":
        at(y, grains(rng, 0.2, 45, (0.0, 0.1), (900 * s, 3000 * s), g_dur=(0.001, 0.004), amp=(0.2, 0.8)), 0, 0.8)
        n = nsamp(0.06)
        sq = tone(np.full(n, 1100.0 * s) * (1 + 0.05 * np.sin(TAU * 60 * tvec(n))), (1.0, 0.3)) * np.sin(np.pi * np.linspace(0, 1, n)) ** 2
        at(y, sq, 0.03, 0.12)
        at(y, thump(rng, 100 * s, t60=0.04, drop=0.2, drive=1.2), 0, 0.25 * w)
    if heavy > 0:
        at(y, thump(rng, 88, t60=0.1 + 0.08 * heavy, drop=0.6, drive=2.8, noise_amt=0.5, noise_fc=900), 0, 0.6 * heavy)
    return hp(fades(y, 0.0003, 0.03), 70.0)


def step(surf, k):
    def fn(rng):
        return step_recipe(rng, surf, (1.0, 0.95, 1.05, 0.91)[k])
    return fn


def land(surf):
    def fn(rng):
        y = buf(0.5)
        at(y, step_recipe(rng, surf, 0.95, heavy=0.8), 0, 1.0)
        at(y, step_recipe(rng, surf, 1.02, heavy=0.4), 0.022, 0.7)   # the second foot
        return y
    return fn


@sfx("land_heavy")
def s_land_heavy(rng):
    """A fall from a height: the body's weight and the robe settling (layered over the surface's landing)."""
    y = buf(0.5)
    at(y, thump(rng, 84, t60=0.18, drop=0.8, drive=4.0, noise_amt=0.5, noise_fc=1200), 0, 1.0)
    at(y, burst(rng, 0.08, bandpass(520, 0.8), t60=0.06), 0, 0.45)
    at(y, burst(rng, 0.2, bandpass(1800, 0.5), t60=0.15, attack=0.01), 0.02, 0.45)
    at(y, grains(rng, 0.4, 16, (0.02, 0.3), (1500, 5000), amp=(0.1, 0.4), fall=6.0), 0, 0.5)
    return hp(y, 60.0)


# ---------------------------------------------------------------- foes: tells and deaths

def tell_voice(race):
    def fn(rng):
        if race == "beast":
            n = nsamp(0.34)
            g = formant_noise(rng, 0.34, 92, [(520, 120, 1.0), (1150, 180, 0.6), (2400, 300, 0.25)], voiced=0.55, f_end=118, jitter=0.06)
            g = g * env_pts(n, [(0, 0), (0.25, 1), (0.31, 0.8), (0.34, 0)]) * (0.75 + 0.25 * np.sin(TAU * 31 * tvec(n)))
            return sat(g, 1.6)
        if race == "human":
            y = buf(0.3)
            n = nsamp(0.13)
            at(y, formant_noise(rng, 0.13, 175, [(720, 110, 1.0), (1180, 140, 0.7), (2500, 250, 0.3)], voiced=0.6, f_end=205) * env_pts(n, [(0, 0), (0.02, 1), (0.13, 0)]), 0, 0.8)
            at(y, whoosh(rng, 0.2, [(0, 2500), (1, 5000)], [(0, 0), (0.8, 1), (1, 0)], width=0.4, tilt_db=0.0), 0.06, 0.4)
            return y
        if race == "construct":
            n = nsamp(0.4)
            gr = noise(n, rng, bandpass(420, 0.8))[:n] * (0.5 + 0.5 * np.abs(filt(rng.standard_normal(n), lowpass(40))[:n]) / 0.1)
            cr = tone(np.full(n, 310.0) * (1 + 0.04 * filt(rng.standard_normal(n), lowpass(30))[:n] / 0.1), (1.0, 0.6, 0.4, 0.3))
            return norm(gr) * 0.6 * env_pts(n, [(0, 0), (0.1, 1), (0.4, 0)]) + 0.35 * norm(cr) * env_pts(n, [(0, 0), (0.2, 1), (0.4, 0)])
        if race == "spirit":
            n = nsamp(0.45)
            wh = noise(n, rng, bandpass(2100, 0.8))[:n] * env_pts(n, [(0, 0), (0.3, 1), (0.45, 0)])
            ph = TAU * np.cumsum(np.geomspace(690, 1100, n) * (1 + 0.012 * np.sin(TAU * 6 * tvec(n)))) / SR
            return 0.6 * norm(wh) + 0.5 * np.sin(ph) * env_pts(n, [(0, 0), (0.3, 1), (0.45, 0)])
        y = buf(0.4)
        for j in range(8):
            at(y, bubble(rng, 350 * 1.18 ** j, tau=0.012, rise=1.2), 0.04 * j, 0.4 + 0.05 * j)
        at(y, whoosh(rng, 0.3, [(0, 900), (1, 2200)], [(0, 0), (0.85, 1), (1, 0)], width=0.8), 0.08, 0.5)
        return y
    return fn


def death(mat):
    def fn(rng):
        y = buf(0.9)
        if mat == "flesh":
            at(y, thump(rng, 84, t60=0.16, drop=0.6, drive=3.0, noise_amt=0.5, noise_fc=900), 0.05, 0.9)
            at(y, burst(rng, 0.25, bandpass(1500, 0.5), t60=0.18, attack=0.02), 0.06, 0.35)
            n = nsamp(0.45)
            ex = formant_noise(rng, 0.45, 130, [(600, 150, 1.0), (1100, 200, 0.4)], voiced=0.1, f_end=80) * env_pts(n, [(0, 0), (0.05, 1), (0.45, 0)])
            at(y, ex, 0, 0.45)
        elif mat == "shell":
            for j, dt in enumerate((0.0, 0.07, 0.16)):
                at(y, hit_body("shell", j)(rng), dt, 0.8 - 0.2 * j)
            at(y, grains(rng, 0.8, 24, (0.1, 0.5), (1500, 5000), g_dur=(0.002, 0.006), amp=(0.2, 0.7), fall=5.0), 0, 0.6)
            at(y, thump(rng, 120, t60=0.08, drop=0.3, drive=2.0), 0.28, 0.6)
        elif mat == "wood":
            tt = 0.0
            gap = 0.14
            for j in range(6):
                at(y, woodblock(rng.uniform(320, 820), rng, t60=0.08, click_amt=0.4, bright=0.8), tt, 0.9 * 0.8 ** j)
                tt += gap
                gap *= 0.72
        elif mat == "slime":
            at(y, hit_body("slime", 0)(rng), 0, 0.9)
            for _ in range(14):
                at(y, bubble(rng, rng.uniform(250, 1100), tau=rng.uniform(0.01, 0.03), rise=rng.uniform(0.4, 1.5)), rng.uniform(0.05, 0.7), 0.35)
            at(y, grains(rng, 0.9, 30, (0.2, 0.85), (2500, 7000), amp=(0.05, 0.3)), 0, 0.5)
        else:  # spirit: a dissolve
            n = nsamp(0.8)
            at(y, whoosh(rng, 0.8, [(0, 2400), (1, 500)], [(0, 0), (0.1, 1), (1, 0)], width=1.0, tilt_db=-2.0), 0, 0.6)
            for k, m in enumerate((88, 85, 81, 78)):
                at(y, chime(float(mtof(m)), rng, dur=0.5, strike=0.05), 0.08 + 0.1 * k, 0.25)
        return add_reverb(hp(fades(y, 0.0003, 0.05), 70.0), rng, t60=0.6, wet=0.12, keep=len(y))
    return fn


# ---------------------------------------------------------------- the world's small sounds

@sfx("door_open")
def s_door_open(rng):
    """A wooden door: the latch lifts, the hinge creaks, the room's air moves."""
    y = buf(0.7)
    at(y, click(rng, 0.003, 2200, 1.0), 0, 0.7)
    at(y, woodblock(900, rng, t60=0.03, click_amt=0.5, bright=1.0), 0.004, 0.4)
    n = nsamp(0.4)
    f = np.interp(tvec(n), [0, 0.2, 0.4], [340, 470, 400]) * (1 + 0.02 * filt(rng.standard_normal(n), lowpass(40))[:n] / 0.1)
    cr = tone(f, (1.0, 0.7, 0.5, 0.3, 0.2)) * (0.6 + 0.4 * np.abs(np.sin(TAU * 17 * tvec(n)))) * env_pts(n, [(0, 0), (0.05, 1), (0.35, 0.6), (0.4, 0)])
    at(y, cr, 0.08, 0.3)
    at(y, whoosh(rng, 0.45, [(0, 300), (1, 700)], [(0, 0), (0.5, 1), (1, 0)], width=1.0, tilt_db=-3.0), 0.1, 0.35)
    return hp(y, 80.0)


@sfx("door_close")
def s_door_close(rng):
    y = buf(0.45)
    at(y, thump(rng, 130, t60=0.08, drop=0.3, drive=2.0), 0, 0.8)
    at(y, woodblock(420, rng, t60=0.08, click_amt=0.4, bright=0.8), 0, 0.6)
    at(y, click(rng, 0.003, 2400, 1.0), 0.09, 0.5)
    return hp(y, 80.0)


@sfx("loot_drop")
def s_loot_drop(rng):
    """Loot spilling onto the ground: a few small clinks and a soft bump."""
    y = buf(0.5)
    for j, dt in enumerate((0.0, 0.07, 0.12, 0.2)):
        f = rng.uniform(2300, 3800)
        at(y, metal(rng, [(f, 1.0, 0.12), (f * 1.52, 0.5, 0.08), (f * 2.3, 0.3, 0.05)], 0.15), dt, 0.6 * 0.8 ** j)
    at(y, thump(rng, 160, t60=0.04, drop=0.3, drive=1.6), 0, 0.4)
    return y


@sfx("splash")
def s_splash(rng):
    """A body into water."""
    y = buf(0.8)
    n = nsamp(0.35)
    at(y, noise(n, rng, bandpass(1300, 0.45))[:n] * env_pts(n, [(0, 0), (0.01, 1), (0.35, 0)]), 0, 0.8)
    at(y, sat(noise(nsamp(0.2), rng, lowpass(400))[:nsamp(0.2)] * decay(nsamp(0.2), 0.15), 1.8), 0, 0.5)
    for _ in range(18):
        at(y, bubble(rng, rng.uniform(400, 1600), tau=rng.uniform(0.01, 0.025), rise=rng.uniform(0.5, 1.3)), rng.uniform(0.03, 0.55), 0.3)
    at(y, grains(rng, 0.8, 30, (0.1, 0.6), (1500, 5000), g_dur=(0.002, 0.005), amp=(0.1, 0.4), fall=3.0), 0, 0.5)
    return hp(y, 80.0)


@sfx("ui_confirm")
def s_ui_confirm(rng):
    y = buf(0.3)
    at(y, woodblock(1500, rng, t60=0.03, click_amt=0.25, bright=0.7), 0, 0.7)
    at(y, woodblock(2000, rng, t60=0.03, click_amt=0.25, bright=0.7), 0.06, 0.6)
    at(y, chime(2349.3, rng, dur=0.2, strike=0.1), 0.06, 0.25)
    return y


@sfx("ui_tab")
def s_ui_tab(rng):
    y = buf(0.09)
    at(y, burst(rng, 0.03, bandpass(3200, 0.8), t60=0.015, attack=0.002), 0, 0.6)
    at(y, woodblock(1700, rng, t60=0.02, click_amt=0.2, bright=0.7), 0.004, 0.5)
    return y


@sfx("talk_open")
def s_talk_open(rng):
    """A talk opens: a scroll unrolled, a soft tap of its rod."""
    y = buf(0.4)
    at(y, grains(rng, 0.3, 26, (0.0, 0.25), (2200, 6000), g_dur=(0.001, 0.004), amp=(0.1, 0.5)), 0, 0.7)
    at(y, burst(rng, 0.25, bandpass(3000, 0.6), t60=0.2, attack=0.03), 0, 0.3)
    at(y, woodblock(820, rng, t60=0.05, click_amt=0.2, bright=0.7), 0.26, 0.5)
    return y


@sfx("talk_next")
def s_talk_next(rng):
    """The next line: a soft high guzheng pluck."""
    y = plucks(rng, [(0.0, 86, 0.5, 0.35)], 0.35)
    return fades(y, 0.0005, 0.08)


@sfx("bark")
def s_bark(rng):
    """A speech bubble over someone: a small rising pip."""
    y = buf(0.12)
    at(y, sweep_tone(1180, 1760, 0.07, harm=(1.0, 0.2)), 0, 0.6)
    at(y, click(rng, 0.0015, 3000, 1.0), 0, 0.2)
    return y


@sfx("scene_in")
def s_scene_in(rng):
    """A staged scene begins (the letterbox slides in): a soft low gong swell and a breath of wind chimes."""
    d = 1.6
    y = buf(d)
    g = gong(146.8, rng, dur=d, pitch=(0, -20), tau=0.5, bloom=0.6, bright=0.62, thump=0.0)
    g = g * smoothstep(tvec(len(g)) / 0.5)
    at(y, g, 0, 0.6)
    for k, m in enumerate((86, 90, 93, 98)):
        at(y, chime(float(mtof(m)), rng, dur=0.8, strike=0.05), 0.3 + 0.11 * k, 0.12)
    return add_reverb(hp(y, 90.0), rng, t60=1.6, wet=0.3, keep=len(y))


# ---------------------------------------------------------------- stingers (the Music bus; the music ducks under them)

def _trem(y, rng, t, dur, midi, vel, rate=15.0):
    nh = max(2, int(dur * rate))
    hits = [(k / rate + rng.normal(0, 0.003), rng.uniform(0.7, 1.0)) for k in range(nh)]
    f = float(mtof(midi))
    p = pipa_params(f)
    p["nail"] = 0.03
    at(y, pluck(f, rng, ring=dur + 0.3, hits=hits, vel=vel, **p), t, vel)


@sfx("sting_quest")
def s_sting_quest(rng):
    """A quest done: a guzheng rising figure that lands on the tonic with a small bell."""
    notes = [(0.0, pent(3), 0.55, 0.9), (0.11, pent(5), 0.6, 0.9), (0.22, pent(6), 0.65, 0.9), (0.36, pent(8), 0.8, 1.4),
             (0.36, pent(0) - 12, 0.5, 1.4)]
    y = norm(plucks(rng, notes, 1.9))
    at(y, bell(float(mtof(pent(10))), rng, dur=1.2, kind="small", strike=0.2), 0.36, 0.3)
    at(y, membrane(180, rng, t60=0.2, drop=0.3, noise_amt=0.2), 0.36, 0.25)
    return add_reverb(y, rng, t60=1.2, wet=0.25, keep=len(y))


@sfx("sting_breakthrough")
def s_sting_breakthrough(rng):
    """A breakthrough or a new realm: a gong swells, a dizi climbs the scale, chimes cascade and the drum answers."""
    d = 3.6
    y = buf(d)
    g = gong(98.0, rng, dur=d, pitch=(0, -30), tau=0.8, bloom=0.5, bright=0.72)
    at(y, g, 0, 0.7)
    at(y, sat(membrane(70, rng, t60=0.6, drop=0.5, noise_amt=0.3), 1.8), 0, 0.5)
    fl = [(0.25 + 0.14 * k, 0.16 if k < 5 else 1.1, float(pent(5 + k)), 0.8, {"slur": k > 0}) for k in range(6)]
    sig, pre = flute(fl, rng, kind="dizi", vib_depth=22.0)
    at(y, sig, 0.25 - pre + 0.25, 0.55)
    for k in range(8):
        at(y, chime(float(mtof(pent(12 - k))), rng, dur=0.9), 1.25 + 0.07 * k, 0.22)
    for k, dt in enumerate((1.05, 1.2, 1.35)):
        at(y, sat(membrane(120, rng, t60=0.25, drop=0.4, noise_amt=0.3), 1.8), dt, 0.3 + 0.1 * k)
    return add_reverb(hp(y, 70.0), rng, t60=2.0, wet=0.3, keep=len(y))


@sfx("sting_rare")
def s_sting_rare(rng):
    """A rare find: a guzheng sweep up the strings into three bright bells and a shimmer."""
    d = 2.4
    y = buf(d)
    notes = [(0.035 * k, pent(3 + k), 0.35 + 0.03 * k, 0.9) for k in range(10)]
    at(y, norm(plucks(rng, notes, 1.2)), 0, 0.7)
    for k, m in enumerate((pent(13), pent(15), pent(17))):
        at(y, bell(float(mtof(m)), rng, dur=1.4, kind="small", strike=0.2), 0.36 + 0.09 * k, 0.45 - 0.07 * k)
    n = nsamp(1.6)
    sh = sum(np.sin(TAU * f * tvec(n) + rng.uniform(0, TAU)) for f in (3520, 3951, 4699)) * env_pts(n, [(0, 0), (0.3, 1), (1.6, 0)]) * (1 + 0.4 * np.sin(TAU * 9 * tvec(n)))
    at(y, sh / 3.0, 0.4, 0.12)
    return add_reverb(y, rng, t60=1.4, wet=0.3, keep=len(y))


@sfx("sting_unlock")
def s_sting_unlock(rng):
    """A system unlocked: two bianzhong bells a fifth apart over a plucked tonic."""
    d = 1.9
    y = buf(d)
    at(y, bell(float(mtof(pent(5))), rng, dur=1.6, kind="bianzhong", strike=0.25), 0, 0.8)
    at(y, bell(float(mtof(pent(8))), rng, dur=1.5, kind="bianzhong", strike=0.25), 0.16, 0.7)
    at(y, norm(plucks(rng, [(0.16, pent(0) - 12, 0.5, 1.3)], 1.5)), 0, 0.4)
    at(y, woodblock(900, rng, t60=0.06, click_amt=0.2, bright=0.7), 0, 0.3)
    return add_reverb(y, rng, t60=1.3, wet=0.25, keep=len(y))


@sfx("sting_elite")
def s_sting_elite(rng):
    """An elite appears: two war-drum strokes, a low pipa tremolo on a clashing second, a falling flute bend."""
    d = 2.2
    y = buf(d)
    for dt, v in ((0.0, 1.0), (0.22, 0.85)):
        at(y, sat(membrane(62, rng, t60=0.5, drop=0.8, noise_amt=0.45, noise_fc=1000), 2.6), dt, v)
        at(y, membrane(180, rng, t60=0.12, drop=0.3, noise_amt=0.3), dt, 0.3 * v)
    _trem(y, rng, 0.22, 1.2, 50, 0.6)
    _trem(y, rng, 0.22, 1.2, 51, 0.45)
    sig, pre = flute([(0.0, 0.9, 81.0, 0.8, {"scoop": False})], rng, kind="dizi", vib_depth=30.0)
    n = len(sig)
    ratio = 2.0 ** (np.interp(tvec(n), [0, pre + 0.3, pre + 0.9], [0, 0, -3]) / 12.0)
    pos = np.concatenate([[0.0], np.cumsum(ratio[:-1])])
    at(y, np.interp(pos, np.arange(n), sig), 0.45 - pre, 0.4)
    at(y, cymbal(rng, dur=0.9, t60=0.5, fmin=500, count=40, noise_amt=0.5), 0.22, 0.25)
    return add_reverb(hp(y, 60.0), rng, t60=1.1, wet=0.22, keep=len(y))


@sfx("sting_victory")
def s_sting_victory(rng):
    """Victory: the drums call (da-da-DUM), a bright guzheng cadence home, a cymbal and a bell."""
    d = 3.0
    y = buf(d)
    for dt, v in ((0.0, 0.7), (0.14, 0.75), (0.34, 1.0)):
        at(y, sat(membrane(96, rng, t60=0.35, drop=0.5, noise_amt=0.35), 2.2), dt, v)
    notes = [(0.34 + 0.075 * k, pent(i), 0.5 + 0.04 * k, 1.2) for k, i in enumerate((5, 6, 7, 8, 10))]
    notes += [(0.34, pent(0) - 12, 0.6, 2.0), (0.34, pent(3) - 12, 0.5, 2.0)]
    at(y, norm(plucks(rng, notes, 2.4)), 0, 0.75)
    at(y, cymbal(rng, dur=1.8, t60=1.4, fmin=350, count=60, noise_amt=0.5), 0.34, 0.35)
    at(y, bell(float(mtof(pent(10))), rng, dur=1.6, kind="small", strike=0.2), 0.72, 0.3)
    return add_reverb(hp(y, 60.0), rng, t60=1.5, wet=0.25, keep=len(y))


# ---------------------------------------------------------------- registration

for _fam in FAMILIES:
    for _k, _v in enumerate("ab"):
        reg(f"hit_{_fam}_{_v}", hit_transient(_fam, _k))
    reg(f"hit_tail_{_fam}", hit_tail(_fam))
    reg(f"swing_{_fam}", swing(_fam))
for _mat in MATERIALS:
    for _k, _v in enumerate("ab"):
        reg(f"hit_on_{_mat}_{_v}", hit_body(_mat, _k))
    reg(f"die_{_mat}", death(_mat))
reg("die_spirit", death("spirit"))
for _el in ELEMENTS:
    reg(f"cast_{_el}", cast(_el))
    reg(f"hit_el_{_el}", hit_element(_el))
for _s in SURFACES:
    for _k, _v in enumerate(VARIANTS):
        reg(f"step_{_s}_{_v}", step(_s, _k))
    reg(f"land_{_s}", land(_s))
for _r in RACES:
    reg(f"tell_{_r}", tell_voice(_r))
