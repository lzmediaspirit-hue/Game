"""Decision 44: the living world's sounds (docs/redesign/sound.md §10). The critters TopdownLife raises (a flock of
sparrows or a fish fleeing, a frog's leap and plop, a hen's flap, a cat waking, a village dog's bark), the villagers'
work cues (data/topdown/life.json `cues`, raised as `life_work_<cue>`; the chop's and the hammer's blow landing as
`life_work_<cue>_hit`) and the player's use of a place (open, tend, sit).

Registered into sfx.SFX like every other effect; the builder fades, normalises and levels them (build_audio.py
`VOLUME`: the critters and the work well under the fight, a breath barely there). They are world sounds: the director
plays them where they happen (Audio.world_sound), falling off with distance, under the fight in the voice pool.

Where a sound repeats (a sweeper's strokes, a smith's blows, a woodcutter's swings, the washing, the dog) there are
takes: `<id>`, `<id>_b`, `<id>_c`, the same recipe with its own seed and a small change of pitch and shape, which the
director plays in turn (data/sound.json `life.takes`), each a little varied in pitch as well.

Every one keeps its energy above 300 Hz (a phone speaker's band): the few low weights (a basket set down, the axe's
bite, the body settling on a mat) are saturated so they carry in harmonics.
"""
from __future__ import annotations

import numpy as np

from synth import (TAU, SR, bandpass, bird, bubble, click, env_pts, filt, highpass, lowpass, noise, nsamp, peaking,
                   place, stft_shape, tvec, woodblock)
from sfx import SFX, at, buf, grains, norm, tone, whoosh
from sfx_pass import burst, hp, metal, sat, thump

# How many takes a sound has: `<id>`, `<id>_b`, `<id>_c` (tools/data/sound.py reads them from data/audio.json for the
# director; which ids the game asks for, and the check that each has a sound, are there too).
TAKES = {"life_work_sweep": 3, "life_work_chop": 2, "life_work_chop_hit": 3, "life_work_hammer": 2,
         "life_work_hammer_hit": 3, "life_work_scrub": 2, "life_dog_bark": 2}
TAKE_SUFFIX = ("", "_b", "_c", "_d")
PITCH = (1.0, 0.94, 1.06, 0.9)     # each take's small change of pitch


def reg(sid, fn):
    SFX[sid] = (fn, False)


def take_ids(sid):
    return [sid + TAKE_SUFFIX[k] for k in range(TAKES.get(sid, 1))]


# ---------------------------------------------------------------- helpers

def unit_lp(rng, n, fc):
    """A slow random control signal 0..1 (a hand's pressure, a flame's flicker)."""
    x = filt(rng.standard_normal(n), lowpass(fc, 0.7))[:n]
    return 0.5 + 0.5 * x / max(float(np.max(np.abs(x))), 1e-9)


def voice(rng, dur, f_pts, formants, voiced=0.6, jitter=0.02):
    """An animal's call: a buzzy source on a pitch contour f_pts [(sec, Hz)] through resonances [(fc, bw, amp)],
    each fc a frequency or a path [(sec, Hz)] (a mew's vowel moving from 'i' to 'ow')."""
    n = nsamp(dur)
    t = tvec(n)
    ts, fs = zip(*f_pts)
    f = np.interp(t, ts, fs)
    f = f * (1.0 + jitter * norm(filt(rng.standard_normal(n), lowpass(25.0))[:n]))
    ph = TAU * np.cumsum(f) / SR
    fmax = float(f.max())
    src = voiced * sum(np.sin(k * ph) / k for k in range(1, 40) if k * fmax < 0.45 * SR) + (1.0 - voiced) * rng.standard_normal(n)

    def centre(spec, tt):
        if isinstance(spec, (int, float)):
            return float(spec)
        a, b = zip(*spec)
        return np.interp(tt, a, b)

    def mag(tt, ff):
        out = np.zeros(np.broadcast(tt, ff).shape)
        for fc, bw, a in formants:
            out = out + a * np.exp(-0.5 * ((ff - centre(fc, tt)) / bw) ** 2)
        return out

    return norm(stft_shape(src, mag, win=512, hop=128))


def flutter(rng, dur, rate=20.0, fc=2000.0, q=0.6, fall=0.4, duty=0.5, lo_fc=700.0, lo_amt=0.5, slow=0.0):
    """Wings: a burst of air on each beat (rate a second, slowing by `slow` a second), dying away over `fall`."""
    n = nsamp(dur)
    e = np.zeros(n)
    t = 0.0
    while t < dur:
        per = 1.0 / max(rate - slow * t, 4.0) * (1.0 + rng.normal(0, 0.07))
        k = max(4, nsamp(per * duty))
        w = np.sin(np.pi * np.arange(k) / k) ** 2 * rng.uniform(0.6, 1.0) * np.exp(-t / fall)
        place(e, w, nsamp(t))
        t += per
    air = noise(n, rng, bandpass(fc, q))[:n] + lo_amt * noise(n, rng, bandpass(lo_fc, 0.8))[:n]
    return norm(air * e * np.minimum(1.0, tvec(n) / 0.01))


def chirp(f0, f1, dur, harm=(1.0, 0.15), shape=1.5):
    """A small bird's 'tsip': a quick sweep from f0 to f1."""
    n = nsamp(dur)
    u = np.linspace(0.0, 1.0, n)
    return tone(f0 * (f1 / f0) ** u, harm) * np.sin(np.pi * u) ** shape


def rub(rng, dur, fc, q=0.55, ridge=0.0, ridge_depth=0.55, shape=1.2, hi=0.0):
    """A stroke of something drawn over a surface: band noise swelling and fading, `ridge` bumps a second (a
    washboard's ribs, bristles catching) cutting it into a rasp."""
    n = nsamp(dur)
    u = np.linspace(0.0, 1.0, n)
    y = noise(n, rng, bandpass(fc, q), *((highpass(hi),) if hi else ()))[:n] * np.sin(np.pi * u) ** shape
    if ridge:
        r = ridge * (1.0 + 0.1 * rng.standard_normal()) * (0.85 + 0.3 * u)
        y = y * ((1.0 - ridge_depth) + ridge_depth * (0.5 + 0.5 * np.sin(TAU * np.cumsum(r) / SR)) ** 2)
    return y


def drips(rng, y, count, t_range, f_range=(1500.0, 2600.0), amp=0.25, tau=(0.005, 0.01)):
    for j in range(count):
        at(y, bubble(rng, rng.uniform(*f_range), tau=rng.uniform(*tau), rise=rng.uniform(0.8, 1.3)),
           rng.uniform(*t_range), amp * rng.uniform(0.5, 1.0))


# ---------------------------------------------------------------- critters

def s_sparrow_flee(rng):
    """A flock of sparrows bursting up: a flurry of small wings, staggered, and a few alarm chirps."""
    y = buf(1.0)
    for j in range(5):
        start = 0.0 if j == 0 else rng.uniform(0.02, 0.26)
        w = flutter(rng, rng.uniform(0.5, 0.7), rate=rng.uniform(19, 26), fc=rng.uniform(1600, 3000), q=0.7,
                    fall=rng.uniform(0.18, 0.32), duty=0.45, lo_fc=rng.uniform(600, 900), lo_amt=0.45, slow=6.0)
        at(y, w, start, (1.0 if j == 0 else rng.uniform(0.45, 0.8)))
    for k in range(3):
        f0 = rng.uniform(4300, 5600)
        at(y, chirp(f0, f0 * rng.uniform(0.7, 0.8), rng.uniform(0.035, 0.055)), rng.uniform(0.02, 0.45), rng.uniform(0.25, 0.45))
    at(y, bird(rng, 4800.0, 0.25), 0.3, 1.0)
    return hp(y, 250.0)


def s_fish_flee(rng):
    """A fish darting away: its tail flicks the surface (a small slap and a plip), a thin swirl, drops falling back."""
    y = buf(0.5)
    at(y, burst(rng, 0.03, bandpass(1900, 0.7), t60=0.018), 0, 0.7)
    at(y, bubble(rng, 1150, tau=0.012, rise=0.9), 0.004, 0.65)
    at(y, whoosh(rng, 0.2, [(0, 1300), (1, 2600)], [(0, 1), (0.4, 0.6), (1, 0)], width=0.6, tilt_db=-1.0), 0.01, 0.3)
    drips(rng, y, 3, (0.06, 0.22), amp=0.3)
    return hp(y, 250.0)


def s_frog_leap(rng):
    """A frog startled off the bank: a small squeaking croak and the flick of wet grass as it jumps."""
    y = buf(0.3)
    n = nsamp(0.075)
    cr = voice(rng, 0.075, [(0, 300), (0.075, 420)], [(900, 170, 1.0), (1900, 260, 0.6), (3000, 400, 0.2)], voiced=0.75, jitter=0.03)
    cr = cr * env_pts(n, [(0, 0), (0.008, 1), (0.05, 0.7), (0.075, 0)]) * (0.55 + 0.45 * np.sin(TAU * 95 * tvec(n)))
    at(y, cr, 0, 0.55)
    at(y, grains(rng, 0.14, 12, (0.0, 0.06), (1800, 5000), g_dur=(0.001, 0.003), amp=(0.2, 0.7), fall=20.0), 0.0, 0.6)
    at(y, burst(rng, 0.05, bandpass(1300, 0.8), t60=0.03, attack=0.002), 0.005, 0.35)
    return hp(y, 250.0)


def s_frog_plop(rng):
    """The frog into the water: a round plop and a few drops."""
    y = buf(0.5)
    at(y, burst(rng, 0.03, bandpass(1600, 0.6), t60=0.015), 0, 0.4)
    at(y, bubble(rng, 560, tau=0.035, rise=1.3), 0.008, 1.0)
    at(y, bubble(rng, 820, tau=0.02, rise=0.9), 0.05, 0.35)
    at(y, sat(burst(rng, 0.08, lowpass(700), highpass(200), t60=0.05), 1.5), 0.005, 0.22)
    drips(rng, y, 3, (0.12, 0.32), amp=0.22)
    return hp(y, 200.0)


def cluck(rng, f0, dur, bright=1.0, rise=1.0):
    """A hen's 'bok': a short buzzy call with a quick fall (or, rise > 1, the alarm's rising 'gawk')."""
    n = nsamp(dur)
    f = [(0, f0), (dur * 0.35, f0 * rise), (dur, f0 * 0.82)]
    v = voice(rng, dur, f, [(850 * bright, 160, 1.0), (1650 * bright, 260, 0.6), (2900 * bright, 400, 0.25)], voiced=0.7, jitter=0.04)
    return v * env_pts(n, [(0, 0), (0.006, 1), (dur * 0.6, 0.7), (dur, 0)])


def hen_flap(k):
    def fn(rng):
        """A hen scattering: its wings beating, a couple of clucks and an alarmed 'b-gawk'."""
        s = PITCH[k]
        y = buf(1.1)
        at(y, flutter(rng, 0.6, rate=11.5, fc=1300 * s, q=0.5, fall=0.35, duty=0.55, lo_fc=520, lo_amt=0.6, slow=3.0), 0.0, 0.8)
        at(y, grains(rng, 0.5, 18, (0.0, 0.45), (2000, 5500), g_dur=(0.001, 0.004), amp=(0.1, 0.4), fall=3.0), 0, 0.5)
        at(y, cluck(rng, 400 * s, 0.07), 0.02, 0.6)
        at(y, cluck(rng, 430 * s, 0.065), 0.15, 0.55)
        at(y, cluck(rng, 470 * s, 0.2, bright=1.25, rise=1.45), 0.3, 0.7)
        at(y, cluck(rng, 390 * s, 0.06), 0.66, 0.35)
        at(y, cluck(rng, 380 * s, 0.06), 0.8, 0.28)
        return hp(y, 250.0)
    return fn


def s_cat_wake(rng):
    """A cat woken from a nap: a small trilling 'mrrp', a soft mew, a stretch with its claws kneading."""
    y = buf(1.3)
    n = nsamp(0.13)
    tr = voice(rng, 0.13, [(0, 360), (0.13, 420)], [(700, 150, 1.0), (1500, 250, 0.5)], voiced=0.7, jitter=0.02)
    tr = tr * env_pts(n, [(0, 0), (0.02, 1), (0.1, 0.7), (0.13, 0)]) * (0.4 + 0.6 * (0.5 + 0.5 * np.sin(TAU * 28 * tvec(n))))
    at(y, tr, 0.0, 0.45)
    d = 0.42
    m = nsamp(d)
    mew = voice(rng, d, [(0, 620), (0.15, 820), (d, 560)],
                [([(0, 450), (0.2, 900), (d, 700)], 170, 1.0), ([(0, 2300), (0.2, 1600), (d, 1150)], 260, 0.7), (3200, 500, 0.2)],
                voiced=0.8, jitter=0.015)
    at(y, mew * env_pts(m, [(0, 0), (0.05, 0.8), (0.18, 1), (0.34, 0.6), (d, 0)]), 0.2, 0.6)
    k = nsamp(0.55)
    fur = noise(k, rng, bandpass(1800, 0.5), highpass(500))[:k] * env_pts(k, [(0, 0), (0.2, 1), (0.55, 0)]) * unit_lp(rng, k, 12.0)
    at(y, fur, 0.68, 0.16)
    for j in range(3):
        at(y, click(rng, 0.0015, rng.uniform(3200, 4200), 1.0), 0.78 + 0.13 * j + rng.uniform(0, 0.03), 0.1)
    return hp(y, 250.0)


def bark(rng, f0, dur, amt=1.0):
    """A friendly dog's 'arf': bright and short, a voiced burst with a quick rise and fall, a puff of breath on it."""
    n = nsamp(dur)
    v = voice(rng, dur, [(0, f0 * 0.85), (dur * 0.3, f0 * 1.12), (dur, f0 * 0.8)],
              [([(0, 700), (dur, 560)], 180, 1.0), (1350, 240, 0.7), (2600, 380, 0.3)], voiced=0.62, jitter=0.05)
    v = v * env_pts(n, [(0, 0), (0.006, 1), (dur * 0.45, 0.75), (dur, 0)])
    return amt * (sat(v, 1.4) + 0.25 * burst(rng, dur, bandpass(1700, 0.7), t60=dur * 0.6))


def dog_bark(k):
    def fn(rng):
        """A village dog glad to see someone (not a warning): two bright 'arf's; the other take a 'ruff' and a whine."""
        y = buf(1.0)
        if k == 0:
            at(y, bark(rng, 470, 0.12), 0.0, 0.9)
            at(y, bark(rng, 500, 0.11), 0.26, 0.85)
        else:
            at(y, bark(rng, 420, 0.14), 0.0, 0.85)
            n = nsamp(0.32)
            wh = voice(rng, 0.32, [(0, 900), (0.12, 1180), (0.32, 980)], [(1200, 250, 1.0), (2400, 400, 0.4)], voiced=0.9, jitter=0.01)
            at(y, wh * env_pts(n, [(0, 0), (0.06, 1), (0.25, 0.6), (0.32, 0)]), 0.3, 0.3)
        return hp(y, 250.0)
    return fn


# ---------------------------------------------------------------- work

def work_sweep(k):
    def fn(rng):
        """A broom on paving: two or three strokes of the bristles, each a gritty 'shhk' with a tap of the head."""
        s = PITCH[k]
        y = buf(1.75)
        count = (3, 2, 3)[k]
        tt = 0.0
        for j in range(count):
            d = rng.uniform(0.34, 0.46)
            fc = (3300 if j % 2 == 0 else 4300) * s
            at(y, click(rng, 0.0015, 1800 * s, 0.9), tt, 0.18)
            st = rub(rng, d, fc, q=0.5, ridge=rng.uniform(110, 160), ridge_depth=0.45, shape=1.0, hi=1200)
            at(y, st, tt + 0.01, 0.8)
            at(y, grains(rng, d, int(55 * d), (0.0, d * 0.85), (2500 * s, 7000 * s), g_dur=(0.0005, 0.002), amp=(0.1, 0.6)), tt + 0.01, 0.5)
            at(y, rub(rng, d, 1100 * s, q=0.8, shape=1.5), tt + 0.01, 0.2)
            tt += d + rng.uniform(0.14, 0.22)
        return hp(y, 300.0)
    return fn


def s_set_down(rng):
    """A basket (or the pole's end) set down: a dull wicker thud, its weave creaking, the pole knocking after."""
    y = buf(0.5)
    at(y, thump(rng, 170, t60=0.06, drop=0.3, drive=2.2, noise_amt=0.4, noise_fc=1500), 0, 0.65)
    at(y, woodblock(260, rng, t60=0.06, click_amt=0.2, bright=0.6), 0.002, 0.45)
    at(y, grains(rng, 0.25, 22, (0.0, 0.14), (1500, 4500), g_dur=(0.001, 0.004), amp=(0.2, 0.8), fall=14.0), 0, 0.6)
    at(y, woodblock(430, rng, t60=0.05, click_amt=0.35, bright=0.8), 0.09, 0.45)
    at(y, woodblock(610, rng, t60=0.03, click_amt=0.3, bright=0.8), 0.16, 0.18)
    return hp(y, 120.0)


def work_scrub(k):
    def fn(rng):
        """Washing on a ribbed board: four wet strokes rasping over the ribs, the water sloshing, drops."""
        s = PITCH[k]
        y = buf(1.8)
        tt = 0.0
        for j in range(4):
            d = rng.uniform(0.26, 0.34)
            fc = (1500 if j % 2 == 0 else 1900) * s
            at(y, rub(rng, d, fc, q=0.6, ridge=rng.uniform(55, 75), ridge_depth=0.7, shape=1.1), tt, 0.8)
            at(y, rub(rng, d, 3200 * s, q=0.7, shape=1.6), tt, 0.25)
            for _ in range(2):
                at(y, bubble(rng, rng.uniform(700, 1400) * s, tau=0.012, rise=0.9), tt + rng.uniform(0.05, d), 0.2)
            tt += d + rng.uniform(0.02, 0.06)
        n = nsamp(0.35)
        at(y, noise(n, rng, bandpass(900 * s, 0.6))[:n] * env_pts(n, [(0, 0), (0.05, 1), (0.35, 0)]), tt, 0.35)
        drips(rng, y, 4, (tt, tt + 0.35), amp=0.2)
        return hp(y, 250.0)
    return fn


def s_hang(rng):
    """Washing hung up: the damp cloth shaken out with two flaps, then a wooden peg clicked on."""
    y = buf(0.75)
    for dt, g in ((0.0, 1.0), (0.17, 0.75)):
        n = nsamp(0.12)
        fl = noise(n, rng, bandpass(950, 0.5), highpass(300))[:n] * env_pts(n, [(0, 0), (0.01, 1), (0.04, 0.5), (0.12, 0)])
        at(y, fl * (0.6 + 0.4 * np.sin(TAU * 38 * tvec(n))), dt, 0.8 * g)
        at(y, burst(rng, 0.015, bandpass(2400, 0.8), t60=0.008), dt + 0.01, 0.45 * g)
    drips(rng, y, 3, (0.2, 0.4), amp=0.12)
    at(y, woodblock(2100, rng, t60=0.02, click_amt=0.6, bright=1.0), 0.48, 0.5)
    at(y, woodblock(1600, rng, t60=0.015, click_amt=0.4, bright=1.0), 0.505, 0.3)
    return hp(y, 250.0)


def s_pick(rng):
    """A herb picked: the leaves parted, a crisp green stem snapped, its fibres tearing."""
    y = buf(0.5)
    at(y, grains(rng, 0.3, 26, (0.0, 0.18), (2200, 6500), g_dur=(0.001, 0.004), amp=(0.1, 0.5), fall=5.0), 0, 0.5)
    at(y, burst(rng, 0.15, bandpass(3000, 0.6), t60=0.1, attack=0.02), 0, 0.18)
    at(y, click(rng, 0.002, 3600, 1.2), 0.17, 0.9)
    at(y, burst(rng, 0.012, highpass(1800), t60=0.006), 0.17, 0.6)
    at(y, woodblock(1900, rng, t60=0.015, click_amt=0.3, bright=1.1), 0.171, 0.3)
    at(y, click(rng, 0.0015, 4400, 1.0), 0.186, 0.35)
    at(y, grains(rng, 0.3, 8, (0.18, 0.27), (3000, 6000), amp=(0.1, 0.4)), 0, 0.4)
    return hp(y, 300.0)


def s_stir(rng):
    """A ladle round an iron pot: a soft scrape with the pot's ring in it, the broth swirling, thick bubbles, a tap on
    the rim."""
    y = buf(1.3)
    n = nsamp(0.85)
    u = np.linspace(0.0, 1.0, n)
    scr = noise(n, rng, bandpass(1700, 0.8))[:n] * np.sin(np.pi * u) ** 1.5 * unit_lp(rng, n, 10.0)
    scr = filt(scr, peaking(760, 12, 12), peaking(1830, 12, 10), peaking(2940, 12, 8))[:n]
    at(y, norm(scr), 0, 0.45)
    sl = noise(n, rng, lowpass(1100), highpass(300))[:n] * np.sin(np.pi * u) * (0.4 + 0.6 * (0.5 + 0.5 * np.sin(TAU * 1.6 * tvec(n))) ** 2)
    at(y, sl, 0.02, 0.4)
    for j in range(4):
        at(y, bubble(rng, rng.uniform(360, 620), tau=rng.uniform(0.02, 0.035), rise=0.8), 0.3 + 0.2 * j + rng.uniform(0, 0.06), 0.45)
    at(y, metal(rng, [(1250, 1.0, 0.25), (2780, 0.5, 0.18), (4100, 0.3, 0.12)], 0.3), 0.9, 0.3)
    return hp(y, 250.0)


def s_grind(rng):
    """A pestle ground round a stone mortar: two rounds of grit with the bowl's hollow in them, seeds cracking, a tap."""
    y = buf(2.0)
    for r in range(2):
        d = 0.8
        n = nsamp(d)
        u = np.linspace(0.0, 1.0, n)
        g = noise(n, rng, bandpass(2300, 0.6))[:n] * (0.3 + 0.7 * unit_lp(rng, n, 30.0))
        g = g + 0.6 * norm(grains(rng, d, 90, (0.0, d - 0.02), (1500, 6000), g_dur=(0.0005, 0.002), amp=(0.1, 0.8)))
        g = filt(g, peaking(540, 6, 12), peaking(1260, 6, 8))[:n]
        at(y, norm(g) * np.sin(np.pi * u) ** 0.8 * (0.7 + 0.3 * np.sin(TAU * 1.25 * tvec(n))), 0.05 + 0.88 * r, 0.8 if r == 0 else 0.7)
    at(y, metal(rng, [(1480, 1.0, 0.05), (3300, 0.5, 0.04)], 0.08, beat=(10, 30)), 1.82, 0.4)
    at(y, thump(rng, 210, t60=0.04, drop=0.2, drive=1.8), 1.82, 0.25)
    return hp(y, 250.0)


def work_chop(k):
    def fn(rng):
        """The woodcutter's axe coming down: a heavy, dark swing."""
        s = PITCH[k]
        y = whoosh(rng, 0.32, [(0, 420 * s), (0.55, 1150 * s), (1, 560 * s)], [(0, 0), (0.55, 1), (0.8, 0.45), (1, 0)], width=0.8, tilt_db=-1.5)
        return hp(y, 250.0)
    return fn


def work_chop_hit(k):
    def fn(rng):
        """The axe into the log: a thick bite of wood, and (two takes of three) the split cracking and the halves
        knocking down on the block."""
        s = PITCH[k]
        y = buf(0.6)
        at(y, thump(rng, 150 * s, t60=0.07, drop=0.4, drive=2.4, noise_amt=0.5, noise_fc=1400), 0, 0.8)
        at(y, woodblock(300 * s, rng, t60=0.1, click_amt=0.5, bright=0.8), 0, 0.8)
        at(y, woodblock(520 * s, rng, t60=0.06, click_amt=0.3, bright=0.8), 0.002, 0.45)
        at(y, burst(rng, 0.02, bandpass(2400, 0.7), t60=0.01), 0, 0.5)
        if k != 1:
            at(y, burst(rng, 0.03, highpass(1500), t60=0.012), 0.045, 0.5)
            at(y, grains(rng, 0.2, 12, (0.045, 0.12), (1500, 5000), g_dur=(0.001, 0.004), amp=(0.2, 0.8), fall=25.0), 0, 0.55)
            at(y, woodblock(440 * s, rng, t60=0.05, click_amt=0.3, bright=0.7), 0.24, 0.35)
            at(y, woodblock(360 * s, rng, t60=0.05, click_amt=0.3, bright=0.7), 0.31, 0.25)
        else:
            at(y, grains(rng, 0.15, 6, (0.01, 0.08), (2000, 5000), amp=(0.1, 0.4), fall=20.0), 0, 0.4)
        return hp(y, 120.0)
    return fn


def work_hammer(k):
    def fn(rng):
        """The smith's hammer raised and brought down: a short swing."""
        s = PITCH[k]
        y = whoosh(rng, 0.2, [(0, 520 * s), (0.6, 1500 * s), (1, 800 * s)], [(0, 0), (0.6, 1), (1, 0)], width=0.7, tilt_db=-1.0)
        return hp(y, 250.0)
    return fn


def work_hammer_hit(k):
    def fn(rng):
        """The hammer on the anvil: the crack of the blow, the iron's dull clank, the anvil ringing on bright. The third
        take is the lighter tap a smith gives the anvil between blows (levelled under the others, build_audio.py)."""
        s = PITCH[k]
        y = buf(1.2)
        light = k == 2
        parts = [(1180 * s, 1.0, 0.9), (2610 * s, 0.7, 0.7), (3470 * s, 0.45, 0.55), (4880 * s, 0.3, 0.4),
                 (6210 * s, 0.2, 0.3), (8120 * s, 0.1, 0.2)]
        at(y, metal(rng, parts, 1.1, beat=(1.5, 5.0)), 0.001, 0.7 if light else 0.55)
        at(y, burst(rng, 0.008, highpass(3000), t60=0.004), 0, 0.5 if light else 0.8)
        if not light:
            at(y, thump(rng, 210 * s, t60=0.04, drop=0.3, drive=2.2, noise_amt=0.3), 0, 0.5)
            at(y, metal(rng, [(640 * s, 1.0, 0.12), (1530 * s, 0.6, 0.08)], 0.15), 0, 0.4)
        return hp(y, 150.0)
    return fn


def s_stoke(rng):
    """A fire poked: the iron in the coals, a log shifting, the flames flaring with a roar and a crackle."""
    y = buf(1.4)
    at(y, metal(rng, [(880, 1.0, 0.08), (2150, 0.6, 0.06), (3400, 0.3, 0.04)], 0.12, beat=(8, 20)), 0, 0.45)
    at(y, woodblock(240, rng, t60=0.06, click_amt=0.2, bright=0.6), 0.03, 0.4)
    at(y, grains(rng, 0.3, 18, (0.02, 0.2), (800, 3000), g_dur=(0.002, 0.006), amp=(0.2, 0.7), fall=8.0), 0, 0.5)
    n = nsamp(1.0)
    at(y, noise(n, rng, bandpass(700, 0.5), lowpass(2500))[:n] * env_pts(n, [(0, 0), (0.15, 1), (1.0, 0)]) * unit_lp(rng, n, 8.0), 0.08, 0.4)
    at(y, grains(rng, 1.3, 70, (0.1, 1.25), (1200, 7000), g_dur=(0.0005, 0.003), amp=(0.1, 1.0), fall=2.5), 0, 0.75)
    for _ in range(3):
        at(y, click(rng, 0.002, rng.uniform(1500, 2500), 1.0), rng.uniform(0.2, 0.9), 0.35)
    return hp(y, 200.0)


def s_fish(rng):
    """A line cast: the rod's tip whips forward, the line runs out, the float lands with a plip and a ripple."""
    y = buf(0.85)
    at(y, whoosh(rng, 0.22, [(0, 1500), (0.7, 4200), (1, 3000)], [(0, 0), (0.6, 1), (1, 0)], width=0.35, tilt_db=0.0), 0, 0.5)
    at(y, grains(rng, 0.45, 14, (0.15, 0.42), (4000, 7000), g_dur=(0.0005, 0.0012), amp=(0.05, 0.25)), 0, 0.5)
    at(y, bubble(rng, 1250, tau=0.014, rise=0.8), 0.52, 0.9)
    at(y, burst(rng, 0.02, bandpass(2400, 0.9), t60=0.01), 0.518, 0.3)
    at(y, bubble(rng, 1700, tau=0.007, rise=1.0), 0.6, 0.25)
    return hp(y, 300.0)


def s_recast(rng):
    """The line lifted from the water (a small tear of the surface, drops) and the rod swung back to cast again."""
    y = buf(0.7)
    n = nsamp(0.09)
    at(y, noise(n, rng, bandpass(1800, 0.7))[:n] * env_pts(n, [(0, 0), (0.01, 1), (0.09, 0)]), 0, 0.5)
    at(y, bubble(rng, 900, tau=0.01, rise=1.2), 0.0, 0.4)
    drips(rng, y, 3, (0.1, 0.45), amp=0.2)
    at(y, whoosh(rng, 0.25, [(0, 900), (0.6, 2600), (1, 1600)], [(0, 0), (0.5, 1), (1, 0)], width=0.45, tilt_db=-0.5), 0.12, 0.45)
    return hp(y, 300.0)


def s_mend(rng):
    """A net mended: the cord drawn through the mesh twice, rasping as it sticks and slips, the knot pulled tight."""
    y = buf(1.0)
    for dt, d, g in ((0.0, 0.28, 1.0), (0.45, 0.22, 0.85)):
        n = nsamp(d)
        u = np.linspace(0.0, 1.0, n)
        slip = np.zeros(n)
        t = 0.0
        while t < d:
            per = 1.0 / rng.uniform(70, 140)
            place(slip, np.exp(-np.arange(nsamp(per)) / (0.25 * per * SR)), nsamp(t))
            t += per
        at(y, noise(n, rng, bandpass(2600, 0.7))[:n] * (0.3 + 0.7 * slip) * np.sin(np.pi * u) ** 0.7, dt, 0.6 * g)
        m = nsamp(0.07)
        cr = tone(np.full(m, 520.0) * (1 + 0.03 * np.sin(TAU * 17 * tvec(m))), (1.0, 0.6, 0.4, 0.25)) * np.sin(np.pi * np.linspace(0, 1, m))
        at(y, cr * (0.5 + 0.5 * np.sin(TAU * 60 * tvec(m))), dt + d - 0.04, 0.12 * g)
    return hp(y, 300.0)


def s_look(rng):
    """Someone looking about: a soft rustle of their sleeves and robe."""
    y = buf(0.65)
    n = nsamp(0.55)
    at(y, noise(n, rng, bandpass(1600, 0.45), highpass(400))[:n] * env_pts(n, [(0, 0), (0.12, 1), (0.3, 0.6), (0.55, 0)]) * unit_lp(rng, n, 14.0), 0.02, 0.6)
    at(y, grains(rng, 0.6, 16, (0.02, 0.5), (1800, 5000), g_dur=(0.001, 0.004), amp=(0.1, 0.4)), 0, 0.5)
    return hp(y, 300.0)


def s_write(rng):
    """A brush on paper: a tick on the inkstone and a short wipe, then a touch and a pressed sweep that lifts away."""
    y = buf(0.95)
    at(y, click(rng, 0.0015, 2200, 1.0), 0, 0.3)
    n = nsamp(0.12)
    at(y, noise(n, rng, bandpass(2600, 0.6))[:n] * env_pts(n, [(0, 0), (0.03, 1), (0.12, 0)]), 0.01, 0.3)
    for t0, d, fc, g in ((0.25, 0.12, 4200, 0.7), (0.45, 0.38, 3600, 1.0)):
        m = nsamp(d)
        u = np.linspace(0.0, 1.0, m)
        env = np.sin(np.pi * u ** 0.6) ** 1.2
        sh = noise(m, rng, bandpass(fc, 0.5), highpass(1500))[:m] * env * (0.75 + 0.25 * unit_lp(rng, m, 60.0))
        at(y, sh, t0, 0.8 * g)
        at(y, grains(rng, d, int(40 * d), (0.0, d * 0.9), (3000, 7000), g_dur=(0.0005, 0.0015), amp=(0.05, 0.3)), t0, 0.5 * g)
    return hp(y, 300.0)


def s_breathe(rng):
    """Someone meditating: a quiet breath in through the nose and a long, slow breath out."""
    y = buf(3.6)
    n = nsamp(1.1)
    inb = noise(n, rng, bandpass(2400, 0.6), highpass(700))[:n] * env_pts(n, [(0, 0), (0.5, 1), (1.0, 0.6), (1.1, 0)]) ** 1.5
    at(y, inb, 0, 0.3)
    m = nsamp(2.3)
    src = rng.standard_normal(m)

    def mag(tt, ff):
        return (1.0 * np.exp(-0.5 * ((ff - 620) / 260) ** 2) + 0.7 * np.exp(-0.5 * ((ff - 1250) / 320) ** 2)
                + 0.35 * np.exp(-0.5 * ((ff - 2500) / 500) ** 2))

    out = norm(stft_shape(src, mag, win=512, hop=128)) * env_pts(m, [(0, 0), (0.25, 1), (1.2, 0.7), (2.3, 0)]) ** 1.3
    at(y, out, 1.2, 1.0)
    return hp(y, 300.0)


# ---------------------------------------------------------------- places (the player's use of one)

def s_place_open(rng):
    """Opening a place (a chest's lid, a door, the letter box's flap): a latch clicks, a short hinge creak, the lid or
    flap resting open with a light wooden knock."""
    y = buf(0.7)
    at(y, click(rng, 0.002, 2600, 1.2), 0, 0.5)
    at(y, woodblock(1300, rng, t60=0.025, click_amt=0.5, bright=1.0), 0.003, 0.35)
    n = nsamp(0.28)
    f = np.interp(tvec(n), [0, 0.14, 0.28], [520, 640, 590]) * (1 + 0.015 * norm(filt(rng.standard_normal(n), lowpass(40))[:n]))
    cr = tone(f, (1.0, 0.6, 0.45, 0.3, 0.2)) * (0.55 + 0.45 * np.abs(np.sin(TAU * 23 * tvec(n)))) * env_pts(n, [(0, 0), (0.04, 1), (0.22, 0.5), (0.28, 0)])
    at(y, cr, 0.06, 0.22)
    at(y, whoosh(rng, 0.3, [(0, 500), (1, 1100)], [(0, 0), (0.5, 1), (1, 0)], width=1.0, tilt_db=-2.0), 0.08, 0.2)
    at(y, woodblock(560, rng, t60=0.07, click_amt=0.3, bright=0.8), 0.38, 0.55)
    at(y, woodblock(820, rng, t60=0.04, click_amt=0.2, bright=0.8), 0.385, 0.25)
    return hp(y, 200.0)


def s_place_tend(rng):
    """Tending a bed of herbs: two handfuls of crumbling soil, then the leaves turned over."""
    y = buf(1.0)
    for dt in (0.0, 0.36):
        at(y, burst(rng, 0.14, bandpass(900, 0.7), t60=0.1, attack=0.01), dt, 0.5)
        at(y, grains(rng, 0.25, 30, (0.0, 0.2), (700, 3500), g_dur=(0.002, 0.006), amp=(0.1, 0.6), fall=6.0), dt, 0.7)
    at(y, grains(rng, 0.45, 28, (0.0, 0.38), (2500, 6500), g_dur=(0.001, 0.004), amp=(0.1, 0.5)), 0.52, 0.55)
    n = nsamp(0.4)
    at(y, noise(n, rng, bandpass(3200, 0.5))[:n] * env_pts(n, [(0, 0), (0.1, 1), (0.4, 0)]), 0.52, 0.18)
    return hp(y, 250.0)


def s_place_sit(rng):
    """Settling on a mat: the robe rustling as one kneels, the weight onto the straw with its crackle, a last shift."""
    y = buf(1.0)
    n = nsamp(0.45)
    at(y, noise(n, rng, bandpass(1500, 0.5), highpass(350))[:n] * env_pts(n, [(0, 0), (0.2, 1), (0.45, 0)]), 0, 0.4)
    at(y, thump(rng, 150, t60=0.07, drop=0.3, drive=1.8, noise_amt=0.3, noise_fc=900), 0.33, 0.55)
    at(y, grains(rng, 0.65, 34, (0.33, 0.6), (1500, 5000), g_dur=(0.0008, 0.003), amp=(0.1, 0.6), fall=8.0), 0, 0.6)
    m = nsamp(0.3)
    at(y, noise(m, rng, bandpass(1200, 0.5))[:m] * env_pts(m, [(0, 0), (0.1, 1), (0.3, 0)]), 0.62, 0.2)
    return hp(y, 150.0)


# ---------------------------------------------------------------- registration

_ONE = {"sparrow_flee": s_sparrow_flee, "fish_flee": s_fish_flee, "frog_leap": s_frog_leap, "frog_plop": s_frog_plop,
        "cat_wake": s_cat_wake, "work_set_down": s_set_down, "work_hang": s_hang, "work_pick": s_pick,
        "work_stir": s_stir, "work_grind": s_grind, "work_stoke": s_stoke, "work_fish": s_fish, "work_recast": s_recast,
        "work_mend": s_mend, "work_look": s_look, "work_write": s_write, "work_breathe": s_breathe}
_TAKES = {"hen_flap": hen_flap, "dog_bark": dog_bark, "work_sweep": work_sweep, "work_scrub": work_scrub,
          "work_chop": work_chop, "work_chop_hit": work_chop_hit, "work_hammer": work_hammer,
          "work_hammer_hit": work_hammer_hit}

for _name, _fn in _ONE.items():
    reg("life_" + _name, _fn)
for _name, _make in _TAKES.items():
    for _k, _sid in enumerate(take_ids("life_" + _name)):
        reg(_sid, _make(_k))
reg("place_open", s_place_open)
reg("place_tend", s_place_tend)
reg("place_sit", s_place_sit)
