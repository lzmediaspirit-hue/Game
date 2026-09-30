"""Decision 45: the first boss's sounds (docs/redesign/story_staging.md "The first boss"; docs/redesign/sound.md).

The staged scenes play them (data/scenes.json `sound` steps: SceneDirector through the Audio director) and the music
director plays the waking eel's theme:

  story_eel_roar        the Hollowed eel wakes: a throat far larger than a river eel's, a grinding bellow rising, water
                        tearing in it, the Hollow's hiss under the tail
  story_river_boil      the river boiling round it: the water heaving, bubbles by the hundred, spouts bursting
  story_talisman        Granny Liu's Nine Seals: nine paper slips whipping in, a brush's hiss, a bell's struck note and
                        the array's hum swelling to a crack
  story_palm            Old Ma's Thousand-Catty Palm: the air rushing down, a vast slap of force, the ground's boom
                        and stone chips raining
  story_dragon          Lu's river dragon: the river roaring up, a long rushing rise, the dragon's cry, the dive and a
                        crashing splash
  boss_eel_awakened     the music of the eel awakened: the night's 6/8 at a harder tempo, the drums doubled and in
                        the low register, a tremolo on the flat second and the xiao gone, a bowed gong every two bars

Registered into sfx.SFX and music.MUSIC like every other sound; the builder fades, normalises and levels them
(build_audio.py VOLUME: the scene's arts loud as a stinger's weight, the roar over the fight). Every one keeps energy
above 300 Hz (a phone speaker's band): the booms and roars are saturated so they carry in harmonics.
"""
from __future__ import annotations

import numpy as np

from music import PIPA_BODY, ZHENG_BODY, Scale, Track, lane, music
from synth import (SR, TAU, add_reverb, bandpass, bell, bubble, chime, cymbal, decay, drone, env_pts, filt, gong,
                   highpass, lowpass, membrane, mtof, noise, nsamp, rms, stft_shape, tvec, woodblock)
from sfx import at, buf, grains, norm, sfx, tone, whoosh


def _sat(x, drive=2.2):
    x = norm(x)
    return np.tanh(drive * x) / np.tanh(drive)


# ---------------------------------------------------------------- the eel wakes

@sfx("story_eel_roar")
def s_story_eel_roar(rng):
    """A bellow from a throat far too large: a sawtooth throat at 48-70 Hz under moving formants (a jaw opening), its
    pitch climbing and cracking, grinding amplitude flutter, water tearing through it and the Hollow's hiss after."""
    d = 2.2
    n = nsamp(d)
    t = tvec(n)
    jit = filt(rng.standard_normal(n), lowpass(14, 0.6))
    jit /= max(rms(jit), 1e-9)
    f0 = np.interp(t, [0, 0.3, 0.9, 1.5, d], [48, 70, 64, 58, 44]) * (1.0 + 0.04 * jit)
    src = tone(f0, [1.0 / k for k in range(1, 80)])
    am = 1.0 + 0.6 * np.sin(TAU * np.cumsum(22.0 + 8.0 * jit) / SR)
    breath = noise(n, rng, bandpass(1100, 0.5))
    x = norm(src) * am + 0.4 * breath

    def mag(tt, f):
        u = np.clip(tt / d, 0, 1)
        out = 0.3 * np.exp(-0.5 * (f / 240.0) ** 2)
        for (a0, a1), bw, amp in (((520, 760), 120, 1.0), ((980, 1300), 170, 0.7), ((2300, 2700), 260, 0.3)):
            fc = a0 + (a1 - a0) * np.sin(np.pi * u)
            out = out + amp * np.exp(-0.5 * ((f - fc) / bw) ** 2)
        return out

    y = stft_shape(x, mag)
    y *= env_pts(n, [(0, 0), (0.18, 1), (1.2, 0.95), (1.8, 0.5), (d, 0)])
    y = filt(np.tanh(2.4 * norm(y)), lowpass(3000, 0.7))[:n]
    # water tearing through the roar, and the Hollow's hiss after it
    tear = noise(n, rng, bandpass(1800, 0.6)) * env_pts(n, [(0, 0), (0.3, 0.6), (1.0, 0.3), (d, 0)])
    hiss = noise(n, rng, highpass(4200, 0.7)) * env_pts(n, [(0, 0), (1.2, 0), (1.6, 0.35), (d, 0)])
    y = y + 0.18 * tear + 0.12 * hiss
    return add_reverb(y, rng, t60=1.4, wet=0.28, keep=n)


@sfx("story_river_boil")
def s_story_river_boil(rng):
    """The river boiling: a heaving low surge, hundreds of bubbles, three spouts bursting up and falling back."""
    d = 2.4
    y = buf(d)
    n = len(y)
    surge = noise(n, rng, bandpass(420, 0.7)) * (0.6 + 0.4 * np.sin(TAU * 1.3 * tvec(n)))
    at(y, _sat(surge, 1.6) * env_pts(n, [(0, 0), (0.4, 1), (1.9, 0.8), (d, 0)]), 0, 0.5)
    for _ in range(140):
        f0 = float(np.exp(rng.uniform(np.log(300), np.log(1900))))
        at(y, bubble(rng, f0, tau=rng.uniform(0.008, 0.03), rise=rng.uniform(0.4, 1.4)), rng.uniform(0.0, d - 0.2), rng.uniform(0.15, 0.5))
    for k, t0 in enumerate((0.25, 0.8, 1.35)):
        sp = whoosh(rng, 0.45, [(0, 700), (0.45, 1600), (1.0, 900)], [(0, 0), (0.12, 1), (1.0, 0)], width=0.8)
        at(y, sp, t0, 0.55)
        splash = noise(nsamp(0.5), rng, bandpass(2400, 0.6)) * decay(nsamp(0.5), 0.35, 0.01)
        at(y, splash, t0 + 0.4, 0.4)
    return add_reverb(filt(y, highpass(90, 0.7))[:n], rng, t60=1.0, wet=0.22, keep=n)


# ---------------------------------------------------------------- the elders' arts

@sfx("story_talisman")
def s_story_talisman(rng):
    """Nine paper slips whipping in one after another, a brush's hiss drawing the star, a small bell struck and the
    array's hum swelling on two fifths to a bright crack as it flares (at 0.64 s: the art's impact frame)."""
    d = 1.9
    y = buf(d)
    n = len(y)
    for k in range(9):
        w = whoosh(rng, 0.16, [(0, 2600), (0.5, 4200), (1.0, 3000)], [(0, 0), (0.2, 1), (1.0, 0)], width=0.5)
        at(y, w, 0.02 + k * 0.05, 0.35)
    brush = noise(nsamp(0.35), rng, bandpass(5200, 0.7)) * env_pts(nsamp(0.35), [(0, 0), (0.05, 1), (0.35, 0)])
    at(y, brush, 0.3, 0.25)
    hum_n = nsamp(1.4)
    th = tvec(hum_n)
    hum = sum(np.sin(TAU * f * th) * a for f, a in ((392.0, 1.0), (588.0, 0.6), (784.0, 0.35), (1176.0, 0.2)))
    hum = hum * env_pts(hum_n, [(0, 0), (0.35, 0.7), (0.45, 1.0), (1.4, 0)])
    at(y, hum, 0.28, 0.35)
    at(y, bell(1568.0, rng, dur=1.0, kind="small", strike=0.3), 0.64, 0.6)
    crack = noise(nsamp(0.08), rng, bandpass(3200, 0.9)) * decay(nsamp(0.08), 0.04, 0.0005)
    at(y, crack, 0.64, 0.7)
    at(y, chime(2093.0, rng, dur=0.9), 0.7, 0.3)
    return add_reverb(filt(y, highpass(150, 0.7))[:n], rng, t60=1.2, wet=0.3, keep=n)


@sfx("story_palm")
def s_story_palm(rng):
    """The air rushing down (0.3 s), a vast slap of force at 0.31 s (the art's impact frame), the ground's boom driven
    into harmonics, and stone chips raining after it."""
    d = 1.6
    y = buf(d)
    n = len(y)
    rush = whoosh(rng, 0.34, [(0, 500), (0.88, 1500), (1.0, 900)], [(0, 0), (0.75, 1), (1.0, 0.6)], width=0.9)
    at(y, rush, 0.0, 0.6)
    slap = noise(nsamp(0.09), rng, bandpass(1500, 0.6)) * decay(nsamp(0.09), 0.05, 0.0005)
    at(y, slap, 0.31, 1.0)
    boom = membrane(46, rng, t60=0.6, drop=0.6, noise_amt=0.5, noise_fc=900)
    at(y, _sat(boom, 3.2), 0.31, 0.95)
    at(y, gong(90.0, rng, dur=1.0, pitch=(0, -120), tau=0.3, bloom=0.2, bright=0.5), 0.31, 0.4)
    chips = grains(rng, 0.8, 26, (0.0, 0.8), (1800, 5200), amp=(0.2, 0.7))
    at(y, chips, 0.4, 0.35)
    return add_reverb(filt(y, highpass(55, 0.7))[:n], rng, t60=1.1, wet=0.25, keep=n)


@sfx("story_dragon")
def s_story_dragon(rng):
    """The river roaring up into a dragon: a long rushing rise of water, the dragon's cry (a bright rising call over a
    throat), its dive whistling down and a crashing splash at 0.79 s (the art's impact frame), spray falling after."""
    d = 2.2
    y = buf(d)
    n = len(y)
    rise = noise(nsamp(0.8), rng, bandpass(900, 0.5)) * env_pts(nsamp(0.8), [(0, 0), (0.5, 1), (0.8, 0.3)])
    at(y, _sat(rise, 1.6), 0.0, 0.55)
    for _ in range(40):
        at(y, bubble(rng, float(rng.uniform(500, 1600)), tau=0.015, rise=1.2), rng.uniform(0.0, 0.7), rng.uniform(0.1, 0.35))
    cn = nsamp(0.6)
    ct = tvec(cn)
    f0 = np.interp(ct, [0, 0.25, 0.6], [330, 660, 520])
    cry = tone(f0, [1.0, 0.5, 0.35, 0.2, 0.12]) * env_pts(cn, [(0, 0), (0.08, 1), (0.45, 0.8), (0.6, 0)])
    cry = cry * (1.0 + 0.2 * np.sin(TAU * 7.0 * ct))
    at(y, norm(cry), 0.2, 0.45)
    dive = whoosh(rng, 0.3, [(0, 2400), (1.0, 700)], [(0, 0.2), (0.66, 1), (1.0, 0.6)], width=0.7)
    at(y, dive, 0.5, 0.6)
    crash = noise(nsamp(0.9), rng, bandpass(1300, 0.4)) * decay(nsamp(0.9), 0.5, 0.002)
    at(y, _sat(crash, 1.8), 0.79, 0.9)
    at(y, _sat(membrane(52, rng, t60=0.5, drop=0.5, noise_amt=0.4), 2.8), 0.79, 0.7)
    spray = grains(rng, 1.2, 60, (0.0, 1.2), (2500, 7000), amp=(0.1, 0.5))
    at(y, spray, 0.85, 0.35)
    return add_reverb(filt(y, highpass(60, 0.7))[:n], rng, t60=1.6, wet=0.3, keep=n)


# ---------------------------------------------------------------- the eel awakened: its own music

@music("boss_eel_awakened")
def m_boss_eel_awakened():
    """The eel awakened: the night's 6/8 on the same G at a harder 150, the drums doubled and low (every eighth on the
    big drum in the last bar of four), a pipa tremolo sawing on the flat second, the drone's beating wider, a bowed gong
    every two bars and cymbal swells on the phrase ends; no xiao: nothing sings over it."""
    tr = Track("boss_eel_awakened", 150, 6, 16)          # counted in eighths: 38.4 s
    sc = Scale(46, 4)                                     # G yu (Bb gong), tonic G3, the eel's own key
    tr.bus("drone", -16, 0.3, (lowpass(900),))
    tr.bus("drum", -3, 0.14)
    tr.bus("gong", -7, 0.45)
    tr.bus("trem", -7, 0.25, PIPA_BODY)
    tr.bus("cym", -12, 0.3)
    tr.add("drone", drone(tr.L, tr.T, tr.r("drone"), [(mtof(43), 1.0), (mtof(44), 0.55), (mtof(49), 0.35)], harm=(1.0, 0.6, 0.45, 0.3, 0.2),
                          swell=(4, 0.7), detune=11.0), 0)
    rd = tr.r("drums")
    low = [np.tanh(2.2 * membrane(52 * rd.uniform(0.98, 1.02), rd, t60=0.55, drop=0.75, noise_amt=0.45, noise_fc=1000)) for _ in range(3)]
    tom = [membrane(90 * rd.uniform(0.97, 1.03), rd, t60=0.35, drop=0.5, noise_amt=0.35) for _ in range(3)]
    tick = [woodblock(1100 * rd.uniform(0.97, 1.03), rd, t60=0.04, click_amt=0.5) for _ in range(3)]
    cha = cymbal(rd, dur=1.6, t60=1.2, fmin=380, count=50, noise_amt=0.5)
    for bar in range(16):
        g = bar % 4
        lane(tr, "drum", bar, "X..X..X..X.." if g != 3 else "XxXxXxXXXXXX", low, rd, vel=1.0)
        lane(tr, "drum", bar, ".x.xx..x.xxx", tom, rd, vel=0.6 + 0.08 * g)
        lane(tr, "drum", bar, "oooooooooooo", tick, rd, vel=0.35)
        if g == 3:
            tr.add("cym", cha, tr.tb(bar, 3), 0.6)
    rg = tr.r("gong")
    for bar in range(0, 16, 2):
        gg = gong(70.0, rg, dur=3.0, pitch=(0, -40), bloom=1.0, bright=0.7, thump=0.0)
        gg = gg * np.clip(tvec(len(gg)) / 0.8, 0, 1) ** 2
        tr.add("gong", gg, tr.tb(bar), 0.7)
    rt = tr.r("trem")
    prog = [0, 1, 0, -1, 0, 1, 0, -2, 0, 1, 0, -1, 1, 1, 0, -2]
    for bar, root in enumerate(prog):
        tr.pipa_trem("trem", tr.tb(bar), 3 * tr.spb, sc(root) - 12, 0.55, rt, rate=16.0)
        tr.pipa_trem("trem", tr.tb(bar, 3), 3 * tr.spb, sc(root) - 12 + 1, 0.45, rt, rate=16.0)
    return tr.mix(t60=1.8, wet=0.3)
