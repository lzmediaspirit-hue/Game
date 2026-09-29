"""Decision 43's ambient beds: seamless loops the director lays under each room (data/sound.json `beds`).

A bed is a base loop for the place (the river, the marsh, wind in bamboo or pines, the town, the sect's courtyard, a
cave, a room indoors, an open field) and the layers the hour adds over it: birds by day, insects and frogs by night.
The layers have their own lengths (18, 14 and 20 s over the 16 s bases), so a base and its layer line up again only
after minutes, and the director starts each at a random point.

Everything is built circularly (periodic noise, wrapped events, circular filters and reverb), so each file joins
seamlessly; the builder checks the seam and writes the loops as Ogg Vorbis.
"""
from __future__ import annotations

import numpy as np

from synth import (SR, TAU, bandpass, bell, bird, bubble, chime, crickets, filt, highpass, lowpass,
                   nsamp, periodic_lfo, pnoise, rms, stream, tvec, wind, woodblock, wrap_add)
from sfx import _loop_reverb, _talker, sfx

BASE_T = 16.0
BAMBOO_MODES = ((1.0, 1.0, 1.0), (2.21, 0.3, 0.5), (3.9, 0.1, 0.3))   # a bamboo stem (music.py BAMBOO)


def _n(sec=BASE_T):
    return nsamp(sec)


def unit(x):
    return x / max(rms(x), 1e-9)


def gusts(n, T, rng, cycles=(1, 2, 3, 5), power=2.0):
    """A periodic 0..1 gust envelope (whole cycles per loop)."""
    return periodic_lfo(tvec(n), T, rng, cycles) ** power


def rustle(n, T, rng, lo=2800.0, hi=7000.0, env=None, grain_hz=25.0):
    """Leaves or reeds: high noise, broken into grains, riding a gust envelope."""
    g = np.abs(pnoise(n, rng, lowpass(grain_hz, 0.7)))
    x = pnoise(n, rng, highpass(lo), lowpass(hi)) * g
    return unit(x * (env if env is not None else 1.0))


def scatter(n, rng, count, make, gain=(0.3, 1.0), spots=None):
    """Wrap `count` events made by make(rng) into a loop of n samples."""
    y = np.zeros(n)
    for k in range(count):
        at = spots[k] if spots is not None else rng.uniform(0, n)
        wrap_add(y, make(rng), int(at), rng.uniform(*gain))
    return y


def hp(x, fc=90.0):
    return filt(x, highpass(fc, 0.7), circular=True)


# ---------------------------------------------------------------- bases (16 s)

@sfx("bed_river", loop=True)
def s_bed_river(rng):
    """A river: a broad soft rush, babbling over stones, now and then a deeper plop."""
    n = _n()
    T = n / SR
    t = tvec(n)
    rush = pnoise(n, rng, bandpass(520, 0.45), lowpass(2200)) * (0.8 + 0.2 * periodic_lfo(t, T, rng, (1, 2, 3)))
    bab = stream(n, T, rng, density=55, fmin=500, fmax=2800)
    plops = scatter(n, rng, 7, lambda r: bubble(r, r.uniform(260, 480), tau=r.uniform(0.02, 0.035), rise=r.uniform(0.5, 1.0)), (0.4, 1.0))
    y = 0.7 * unit(rush) + 0.8 * bab + 0.5 * unit(plops)
    return _loop_reverb(hp(y, 120.0), rng, 1.0, 0.18)


@sfx("bed_marsh", loop=True)
def s_bed_marsh(rng):
    """The marsh: still water lapping at the reeds, the reeds hissing in the wind, drips, a warbler far off."""
    n = _n()
    T = n / SR
    lap = pnoise(n, rng, bandpass(380, 0.6), lowpass(900)) * gusts(n, T, rng, (3, 4, 7), 1.5)
    env = 0.25 + 0.75 * gusts(n, T, rng, (1, 2, 3), 2.0)
    reeds = rustle(n, T, rng, 2600.0, 6500.0, env, 18.0)
    drips = scatter(n, rng, 9, lambda r: bubble(r, r.uniform(280, 750), tau=r.uniform(0.012, 0.025), rise=r.uniform(0.6, 1.3)), (0.3, 1.0))
    far = scatter(n, rng, 2, lambda r: bird(r, r.uniform(2400, 3000)), (0.15, 0.25))
    y = 0.7 * unit(lap) + 0.45 * reeds + 0.4 * unit(drips) + unit(far) * 0.25
    return _loop_reverb(hp(y, 110.0), rng, 1.4, 0.22)


@sfx("bed_bamboo", loop=True)
def s_bed_bamboo(rng):
    """Wind in bamboo: the grove's hush, dry leaves in the gusts, stems knocking hollow, a creak."""
    n = _n()
    T = n / SR
    body = wind(n, T, rng, base=480, spread=900, width=0.9, cycles=(1, 2, 3, 5), floor=0.35)
    env = gusts(n, T, rng, (1, 2, 3), 2.0)
    leaves = rustle(n, T, rng, 3000.0, 7500.0, 0.2 + 0.8 * env, 30.0)
    knocks = np.zeros(n)
    tones = (430, 520, 610, 700, 820)
    peaks = np.argsort(env)[-2000:]
    for _ in range(9):
        t0 = int(peaks[int(rng.integers(len(peaks)))])
        for _ in range(int(rng.integers(2, 5))):
            s = woodblock(tones[int(rng.integers(len(tones)))] * rng.uniform(0.97, 1.03), rng, t60=rng.uniform(0.12, 0.25),
                          click_amt=0.15, bright=0.8, modes=BAMBOO_MODES)
            wrap_add(knocks, s, t0, rng.uniform(0.3, 1.0))
            t0 += nsamp(rng.uniform(0.06, 0.2))
    creak = np.zeros(n)
    for _ in range(2):
        m = nsamp(rng.uniform(0.3, 0.6))
        u = np.linspace(0, 1, m)
        f = rng.uniform(240, 330) * (1 + 0.08 * u) * (1 + 0.02 * np.sin(TAU * 23 * u))
        c = sum(a * np.sin(k * TAU * np.cumsum(f) / SR) for k, a in ((1, 1.0), (2, 0.6), (3, 0.4), (4, 0.25)))
        wrap_add(creak, c * np.sin(np.pi * u) ** 2, int(rng.uniform(0, n)), 0.5)
    y = 0.8 * body + 0.5 * leaves + 0.35 * unit(knocks) + 0.12 * unit(creak)
    return _loop_reverb(hp(y, 110.0), rng, 1.1, 0.2)


@sfx("bed_pines", loop=True)
def s_bed_pines(rng):
    """Wind through pines on a height: a long sighing roar, the needles hissing on top."""
    n = _n()
    T = n / SR
    sigh = wind(n, T, rng, base=650, spread=1300, width=1.0, cycles=(1, 2, 3), floor=0.3, tilt_db=-3.0)
    env = gusts(n, T, rng, (1, 2, 3), 1.6)
    needles = unit(pnoise(n, rng, bandpass(5200, 0.7)) * (0.3 + 0.7 * env))
    y = 0.9 * sigh + 0.3 * needles
    return _loop_reverb(hp(y, 130.0), rng, 1.3, 0.2)


@sfx("bed_field", loop=True)
def s_bed_field(rng):
    """An open field or path: a light breeze and the grass stirring."""
    n = _n()
    T = n / SR
    air = wind(n, T, rng, base=420, spread=700, width=0.95, cycles=(1, 2, 3, 5), floor=0.4)
    env = gusts(n, T, rng, (1, 2, 3, 4), 1.8)
    grass = rustle(n, T, rng, 2200.0, 6000.0, 0.15 + 0.85 * env, 20.0)
    y = 0.8 * air + 0.4 * grass
    return _loop_reverb(hp(y, 120.0), rng, 1.0, 0.15)


@sfx("bed_town", loop=True)
def s_bed_town(rng):
    """A town: a murmur of voices, a vendor's clapper, someone chopping wood, a cart creaking past, a far hand-bell."""
    n = _n()
    T = n / SR
    talk = np.zeros(n)
    for _ in range(10):
        talk += _talker(n, T, rng, float(rng.lognormal(0.0, 0.35)))
    talk = filt(unit(talk), lowpass(2800, 0.6), highpass(140), circular=True)
    life = np.zeros(n)
    t0 = rng.uniform(0, n)
    for k in range(6):
        wrap_add(life, woodblock(980, rng, t60=0.05, click_amt=0.3, bright=0.8), int(t0 + k * nsamp(0.18 if k % 3 < 2 else 0.4)), 0.35)
    t1 = rng.uniform(0, n)
    for k in range(3):
        chop = woodblock(310 * rng.uniform(0.97, 1.03), rng, t60=0.1, click_amt=0.5, bright=0.7)
        wrap_add(life, chop, int(t1 + k * nsamp(rng.uniform(0.9, 1.2))), 0.6)
    m = nsamp(1.4)
    u = np.linspace(0, 1, m)
    f = 380 * (1 + 0.1 * np.sin(TAU * 3.1 * u)) * (1 + 0.02 * np.sin(TAU * 41 * u))
    cart = sum(a * np.sin(k * TAU * np.cumsum(f) / SR) for k, a in ((1, 1.0), (2, 0.5), (3, 0.3)))
    wrap_add(life, cart * np.sin(np.pi * u) ** 2 * (0.5 + 0.5 * np.abs(np.sin(TAU * 2.2 * u * 1.4))), int(rng.uniform(0, n)), 0.12)
    wrap_add(life, bell(1661.2, rng, dur=1.0, kind="small", strike=0.2), int(rng.uniform(0, n)), 0.2)
    life = filt(life, lowpass(3500), circular=True)
    y = unit(talk) + 0.45 * unit(life) + 0.2 * unit(pnoise(n, rng, bandpass(450, 0.5)))
    return _loop_reverb(hp(y, 130.0), rng, 1.2, 0.3)


@sfx("bed_sect", loop=True)
def s_bed_sect(rng):
    """A sect's courtyard: a hushed breeze, wind chimes under the eaves, one temple bell far up the mountain."""
    n = _n()
    T = n / SR
    air = wind(n, T, rng, base=520, spread=800, width=1.0, cycles=(1, 2, 3), floor=0.35)
    chimes = np.zeros(n)
    notes = (1174.7, 1318.5, 1480.0, 1760.0, 1975.5)
    for _ in range(2):
        t0 = rng.uniform(0, n)
        for _ in range(int(rng.integers(4, 7))):
            wrap_add(chimes, chime(notes[int(rng.integers(len(notes)))], rng, dur=1.4, strike=0.1), int(t0), rng.uniform(0.3, 0.9))
            t0 += nsamp(rng.uniform(0.08, 0.35))
    temple = bell(146.8, rng, dur=7.0, kind="temple", strike=0.15)
    far = np.zeros(n)
    wrap_add(far, temple, int(rng.uniform(0, n)), 1.0)
    far = filt(far, lowpass(1800), circular=True)
    y = 0.7 * air + 0.35 * unit(chimes) + 0.45 * unit(far)
    return _loop_reverb(hp(y, 110.0), rng, 2.2, 0.3)


@sfx("bed_cave", loop=True)
def s_bed_cave(rng):
    """A cave: drops falling into still pools, a low hollow air, a trickle somewhere deeper."""
    n = _n()
    T = n / SR
    drops = scatter(n, rng, 16, lambda r: bubble(r, float(np.exp(r.uniform(np.log(900), np.log(2600)))), tau=r.uniform(0.008, 0.02),
                                                 rise=r.uniform(0.8, 1.8)), (0.3, 1.0))
    air = pnoise(n, rng, bandpass(300, 0.5)) * (0.7 + 0.3 * periodic_lfo(tvec(n), T, rng, (1, 2)))
    trickle = filt(stream(n, T, rng, density=12, fmin=400, fmax=1400, bed=0.8, bub=0.5), lowpass(1500), circular=True)
    y = unit(drops) * 0.8 + 0.35 * unit(air) + 0.3 * unit(trickle)
    return _loop_reverb(hp(y, 100.0), rng, 2.8, 0.45)


@sfx("bed_interior", loop=True)
def s_bed_interior(rng):
    """Indoors: the quiet of a room, a hearth's small crackle, a beam settling once."""
    n = _n()
    T = n / SR
    room = pnoise(n, rng, bandpass(420, 0.4))
    crackle = np.zeros(n)
    for _ in range(int(8 * T)):
        k = nsamp(rng.uniform(0.0006, 0.003))
        g = rng.standard_normal(k + 8) * np.exp(-np.arange(k + 8) / max(1.0, k / 3.0))
        wrap_add(crackle, filt(g, bandpass(rng.uniform(1200, 5000), 1.2), tail=0.004), int(rng.uniform(0, n)), rng.uniform(0.1, 1.0))
    m = nsamp(0.45)
    u = np.linspace(0, 1, m)
    f = 260 * (1 + 0.06 * u) * (1 + 0.02 * np.sin(TAU * 19 * u))
    creak = sum(a * np.sin(k * TAU * np.cumsum(f) / SR) for k, a in ((1, 1.0), (2, 0.6), (3, 0.35)))
    beam = np.zeros(n)
    wrap_add(beam, creak * np.sin(np.pi * u) ** 2, int(rng.uniform(0, n)), 1.0)
    y = 0.4 * unit(room) + 0.6 * unit(crackle) + 0.15 * unit(beam)
    return _loop_reverb(hp(y, 110.0), rng, 0.6, 0.2)


# ---------------------------------------------------------------- layers of the hour

@sfx("bed_birds", loop=True)
def s_bed_birds(rng):
    """Birds by day (18 s): a few small birds near and far, now and then answering each other."""
    n = _n(18.0)
    y = np.zeros(n)
    for k in range(16):
        f0 = rng.uniform(3000, 4600) if k % 3 else rng.uniform(2100, 2800)
        near = rng.uniform(0.2, 1.0)
        call = bird(rng, f0)
        if near < 0.5:
            call = filt(call, lowpass(4000), tail=0.01)
        wrap_add(y, call, int(rng.uniform(0, n)), near)
    y = unit(y) + 0.06 * pnoise(n, rng, bandpass(3500, 0.6))   # the leaves they sit in, so the loop never falls silent
    return _loop_reverb(hp(y, 900.0), rng, 1.2, 0.3)


@sfx("bed_insects", loop=True)
def s_bed_insects(rng):
    """Insects by night (14 s): crickets in the grass and a katydid's rasp."""
    n = _n(14.0)
    T = n / SR
    cr = crickets(n, T, rng, count=5, fbase=4300.0)
    kat = np.zeros(n)
    per = T / 11.0
    for k in range(11):
        m = nsamp(0.09)
        rasp = rng.standard_normal(m) * np.sin(np.pi * np.linspace(0, 1, m)) * (0.5 + 0.5 * np.sign(np.sin(TAU * 90 * tvec(m))))
        wrap_add(kat, filt(rasp, bandpass(6200, 1.5), tail=0.01), int(nsamp(k * per + rng.normal(0, 0.03))), rng.uniform(0.6, 1.0))
    air = pnoise(n, rng, bandpass(2400, 0.5))   # the night air, so the loop never drops to silence
    y = unit(cr) + 0.35 * unit(kat) + 0.1 * air
    return _loop_reverb(hp(y, 1500.0), rng, 0.9, 0.25)


def _croak(rng, f0, pulses, rate):
    m = nsamp(pulses / rate)
    t = tvec(m)
    ph = TAU * f0 * t
    src = sum(np.sin(k * ph) / k ** 0.7 for k in range(1, 18) if k * f0 < 0.45 * SR)
    pulse = np.clip(np.sin(TAU * rate * t), 0, None) ** 3
    y = filt(src * pulse, bandpass(700, 1.2), bandpass(1500, 0.9), tail=0.01)
    return y / max(np.max(np.abs(y)), 1e-9) * np.sin(np.pi * np.linspace(0, 1, len(y))) ** 0.3


@sfx("bed_frogs", loop=True)
def s_bed_frogs(rng):
    """Frogs by night near water (20 s): four frogs, each with its own call and its own slow rhythm."""
    n = _n(20.0)
    T = n / SR
    y = np.zeros(n)
    for _ in range(4):
        f0 = rng.uniform(170, 330)
        rate = rng.uniform(9, 16)
        pulses = int(rng.integers(3, 7))
        lvl = rng.uniform(0.3, 1.0)
        per = T / int(rng.integers(5, 10))
        off = rng.uniform(0, per)
        k = 0
        while k * per < T:
            if rng.random() > 0.2:
                wrap_add(y, _croak(rng, f0 * rng.uniform(0.98, 1.02), pulses, rate), nsamp(off + k * per + rng.normal(0, 0.05)), lvl)
            k += 1
    y = unit(y) + 0.12 * pnoise(n, rng, bandpass(900, 0.5))   # still night air over the water
    return _loop_reverb(hp(y, 200.0), rng, 1.2, 0.3)
