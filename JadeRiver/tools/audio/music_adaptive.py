"""Decision 43's adaptive music: a combat stem for each exploration track a fight can start in, and two boss themes.

A stem (`<track>_combat`) is built on its exploration track's own grid: the same tempo, metre, bar count and loop
length, the same key and chord roots. The director starts it with its track, silent, and brings it in on the next
beat when foes turn on the player, so the drums and the driving bass land in step with the tune already playing
(scripts/audio/audio_director.gd). A stem holds only what a fight adds (war drums, a pipa ostinato on the chord roots,
tremolo swells at the phrase ends, cymbals on the phrase starts), mixed about 2 dB under its track.

STEMS lists each stem's grid, which must match its track's Track(...) call in music.py; the builder checks that the
two loops have the same length.

The boss themes: Old Snapper (the ancient snapping turtle of the reed shallows) lumbers, its drums heavy and its jaw
clacking in the woodblocks; the Hollowed Eel of the Hollow Night coils, in a 6/8 that rolls like the river, the xiao
sinking under it.
"""
from __future__ import annotations

import numpy as np

from music import (PIPA_BODY, R_FAST, R_MID, TRI, ZHENG_BODY, Scale, Track, gliss, gliss_len, lane, music, period,
                   to_flute)
from synth import (TAU, bubble, cymbal, drone, gong, lowpass, membrane, mtof, pnoise, tvec, woodblock, bandpass)

# stem id -> (track, bpm, bar_beats, bars, (gong, mode), chord roots per bar, drum style)
STEMS = {
    "village_day_combat": ("village_day", 76, 3, 16, (67, 0), [0, 0, -2, -2, 0, 0, 1, -2, -1, -1, -2, 0, 1, -2, 0, 0], "waltz"),
    "village_night_combat": ("village_night", 52, 4, 8, (48, 4), [0, 0, -2, -1, 0, 1, -2, 0], "slow"),
    "field_combat": ("field", 100, 4, 16, (62, 3), [0, 0, -3, -2, 0, 0, 1, -2, -1, -1, -3, -2, 0, -3, -2, 0], "march"),
    "river_combat": ("river", 150, 6, 16, (60, 0), [0, -1, 2, -2, 0, -1, 1, -2, 0, 2, -1, 1, 0, -1, -2, 0], "six"),
    "sect_combat": ("sect", 72, 4, 12, (60, 3), [0, 0, -3, -3, -2, -2, 0, 0, 1, -1, -2, 0], "slow"),
}

# per drum style: one bar's lanes (big drum, tom, small drum), the bass's notes per bar as (beat, scale step, velocity)
STYLE = {
    "waltz": {"big": "X.....x.X...", "tom": "..x.x.....x.", "hi": "o.o.o.o.o.o.", "fill": "......xxXxXX",
              "bass": [(0, 0, 0.8), (0.5, 0, 0.5), (1, 3, 0.6), (1.5, 0, 0.5), (2, 4, 0.6), (2.5, 3, 0.5)]},
    "slow": {"big": "X.....x.X..x....", "tom": "..x.x...x.x.x.xx", "hi": "o.o.o.o.o.o.o.o.", "fill": "........xxXXxXXX",
             "bass": [(k * 0.25, s, v) for k, (s, v) in enumerate([(0, 0.8), (0, 0.4), (3, 0.5), (0, 0.4), (4, 0.6), (0, 0.4), (3, 0.5), (0, 0.4),
                                                                    (0, 0.7), (0, 0.4), (3, 0.5), (0, 0.4), (5, 0.6), (4, 0.5), (3, 0.5), (0, 0.4)])]},
    "march": {"big": "X..x..X...x.X...", "tom": "....x.......x.x.", "hi": "..o...o...o...o.", "fill": "........oxoxxxXX",
              "bass": [(k * 0.5, s, v) for k, (s, v) in enumerate([(0, 0.8), (0, 0.5), (3, 0.6), (0, 0.5), (4, 0.7), (0, 0.5), (3, 0.6), (5, 0.5)])]},
    "six": {"big": "X.....X..x..", "tom": "..x..x..x.xx", "hi": "o.o.o.o.o.o.", "fill": "......xxXxXX",
            "bass": [(0, 0, 0.8), (1, 3, 0.5), (2, 0, 0.6), (3, 4, 0.7), (4, 3, 0.5), (5, 0, 0.5)]},
}


def combat_stem(sid):
    base, bpm, bb, bars, (g, mode), prog, style = STEMS[sid]
    st = STYLE[style]
    tr = Track(sid, bpm, bb, bars)
    sc = Scale(g, mode)
    tr.bus("drum", -2, 0.12)
    tr.bus("hi", -9, 0.12)
    tr.bus("cym", -12, 0.2)
    tr.bus("bass", -5, 0.1, PIPA_BODY)
    tr.bus("trem", -9, 0.2, PIPA_BODY)
    rd = tr.r("drums")
    big = [membrane(66 * rd.uniform(0.98, 1.02), rd, t60=0.45, drop=0.7, noise_amt=0.35, noise_fc=1000) for _ in range(3)]
    big = [np.tanh(1.8 * b) / np.tanh(1.8) for b in big]          # harmonics, so a phone hears the war drum
    tom = [membrane(128 * rd.uniform(0.97, 1.03), rd, t60=0.28, drop=0.45, noise_amt=0.35) for _ in range(3)]
    small = [membrane(610 * rd.uniform(0.97, 1.03), rd, t60=0.06, drop=0.12, noise_amt=0.6, noise_fc=4000, click_amt=0.5)
             for _ in range(4)]
    cha = cymbal(rd, dur=1.4, t60=1.0, fmin=400, count=50, noise_amt=0.5)
    for bar in range(bars):
        last = bar % 4 == 3
        lane(tr, "drum", bar, st["big"], big, rd, vel=0.95)
        lane(tr, "drum", bar, st["fill"] if last else st["tom"], tom, rd, vel=0.62)
        lane(tr, "hi", bar, st["hi"], small, rd, vel=0.6 if not last else 0.8)
        if bar % 4 == 0:
            tr.add("cym", cha, tr.tb(bar), 0.7)
    rb = tr.r("bass")
    for bar, root in enumerate(prog):
        for beat, step, vel in st["bass"]:
            tr.pipa("bass", tr.tb(bar, beat), sc(root + step) - 24, vel, rb, ring=0.4, jitter=0.002)
    rt = tr.r("trem")
    for bar in range(3, bars, 4):
        root = prog[bar]
        for k, off in enumerate((0, 3)):
            tr.pipa_trem("trem", tr.tb(bar, bb * 0.5), bb * 0.5 * tr.spb, sc(root + off) - 12, 0.5 - 0.1 * k, rt)
    return tr.mix(t60=1.1, wet=0.18, target=-20.0)


for _sid in STEMS:
    music(_sid)(lambda _s=_sid: combat_stem(_s))


@music("boss_snapper")
def m_boss_snapper():
    """Old Snapper: an ancient snapping turtle rising out of the reeds. Heavy four-square drums that lumber, the jaw's
    clack in the woodblocks, a low pipa tremolo circling A, a reed-organ drone and a dark xiao over it."""
    tr = Track("boss_snapper", 96, 4, 16)                 # 40.0 s
    sc = Scale(48, 4)                                     # A yu (C gong), tonic A3
    tr.bus("drone", -19, 0.25, (lowpass(1200),))
    tr.bus("drum", -3, 0.12)
    tr.bus("clack", -8, 0.2)
    tr.bus("gong", -7, 0.35)
    tr.bus("pipa", -6, 0.18, PIPA_BODY)
    tr.bus("flute", -8, 0.35)
    tr.bus("water", -26, 0.3)
    tr.add("drone", drone(tr.L, tr.T, tr.r("drone"), [(mtof(45), 1.0), (mtof(52), 0.45), (mtof(57), 0.2)], harm=(1.0, 0.55, 0.4, 0.25, 0.15),
                          swell=(4, 0.5)), 0)
    tr.add("water", pnoise(tr.L, tr.r("water"), bandpass(600, 0.5)) * (1.0 + 0.4 * np.sin(TAU * 4 * tvec(tr.L) / tr.T)), 0)
    rd = tr.r("drums")
    dagu = [np.tanh(2.0 * membrane(56 * rd.uniform(0.98, 1.02), rd, t60=0.7, drop=0.8, noise_amt=0.45, noise_fc=1000)) for _ in range(3)]
    tom = [membrane(104 * rd.uniform(0.97, 1.03), rd, t60=0.35, drop=0.45, noise_amt=0.3) for _ in range(3)]
    clack = [woodblock(560 * rd.uniform(0.97, 1.03), rd, t60=0.06, click_amt=0.6, bright=1.1) for _ in range(3)]
    nao = cymbal(rd, dur=2.2, t60=1.6, fmin=320, count=60, noise_amt=0.5)
    luo = gong(110.0, rd, dur=3.0, pitch=(0, -80), tau=0.4, bloom=0.2, bright=0.75)
    for bar in range(16):
        g = bar % 4
        lane(tr, "drum", bar, "X...X...X..xX...", dagu, rd, vel=1.0)
        lane(tr, "drum", bar, "..x...x...x...x." if g != 3 else "..x.x.x.xxx.XXXX", tom, rd, vel=0.6)
        lane(tr, "clack", bar, "......X.......X." if g % 2 else "......X...X...X.", clack, rd, vel=0.8)
        if g == 0:
            tr.add("gong", luo, tr.tb(bar), 0.8)
            tr.add("drum", nao, tr.tb(bar), 0.25)
    rp = tr.r("pipa")
    osti = [(0, 2, 45), (2, 1, 48), (3, 1, 45), (4, 2, 43), (6, 2, 45)]
    for bar2 in range(0, 16, 2):
        for b, d, m in osti:
            tr.pipa_trem("pipa", tr.tb(bar2, b), d * tr.spb, m, 0.6, rp, rate=14.0)
    rm = tr.r("melody")
    fl = []
    pp = period(rm, R_MID, lo=-2, hi=5, first=0)
    for p, notes in enumerate(pp):
        fl += to_flute(tr, notes, sc, tr.tb(8 + 2 * p), rm, octave=1, grace_p=0.3, gap=0.05)
    tr.flute("flute", fl, tr.r("flute_sig"), kind="xiao", vib_depth=18, vib_rate=4.6)
    rw = tr.r("splash")
    for _ in range(10):
        tr.add("water", bubble(rw, rw.uniform(300, 700), tau=0.03, rise=0.7), rw.uniform(0, tr.T), 3.0)
    return tr.mix(t60=1.6, wet=0.24)


@music("boss_eel")
def m_boss_eel():
    """The Hollowed Eel of the Hollow Night: a 6/8 that rolls like the river at night. Toms in waves, a guzheng
    tremolo rippling over a beating drone with a flat second, a xiao that sinks at its phrase ends, drops of water,
    and a bowed gong swelling every four bars."""
    tr = Track("boss_eel", 132, 6, 16)                    # counted in eighths: 43.6 s
    sc = Scale(46, 4)                                     # G yu (Bb gong), tonic G3
    tr.bus("drone", -18, 0.3, (lowpass(1000),))
    tr.bus("drum", -4, 0.15)
    tr.bus("gong", -8, 0.45)
    tr.bus("zheng", -8, 0.3, ZHENG_BODY)
    tr.bus("flute", -7, 0.4)
    tr.bus("drip", -14, 0.7)
    tr.add("drone", drone(tr.L, tr.T, tr.r("drone"), [(mtof(43), 1.0), (mtof(44), 0.3), (mtof(50), 0.35)], harm=TRI,
                          swell=(2, 0.6), detune=7.0), 0)
    rd = tr.r("drums")
    tom = [membrane(96 * rd.uniform(0.97, 1.03), rd, t60=0.4, drop=0.5, noise_amt=0.3) for _ in range(3)]
    low = [np.tanh(1.8 * membrane(60 * rd.uniform(0.98, 1.02), rd, t60=0.6, drop=0.7, noise_amt=0.4)) for _ in range(3)]
    tick = [woodblock(1300 * rd.uniform(0.97, 1.03), rd, t60=0.04, click_amt=0.4) for _ in range(3)]
    for bar in range(16):
        g = bar % 4
        lane(tr, "drum", bar, "X.....x.....", low, rd, vel=0.95)
        lane(tr, "drum", bar, "..x.xx..x.xx" if g != 3 else "..xxxxXXxXXX", tom, rd, vel=0.55 + 0.1 * g)
        lane(tr, "drum", bar, "o.o.o.o.o.o.", tick, rd, vel=0.4)
    rg = tr.r("gong")
    for bar in (0, 4, 8, 12):
        gg = gong(78.0, rg, dur=4.0, pitch=(0, -30), bloom=1.0, bright=0.72, thump=0.0)
        gg = gg * np.clip(tvec(len(gg)) / 1.2, 0, 1) ** 2
        tr.add("gong", gg, tr.tb(bar), 0.7)
    rz = tr.r("zheng")
    prog = [0, 0, -1, 0, 0, 1, -1, -2, 0, 0, -1, 0, 1, 1, -1, 0]
    for bar, root in enumerate(prog):
        for k, off in enumerate((0, 3, 5, 3, 0, 3)):
            tr.zheng("zheng", tr.tb(bar, k), sc(root + off) - 12, 0.45 if k == 0 else 0.3, rz, ring=1.2, jitter=0.003)
    for bar in (7, 15):
        gliss(tr, "zheng", tr.tb(bar + 1) - gliss_len(8, -2, 0.04) - 0.04, sc, 8, -2, rz, dt=0.04, vel=0.4)
    rm = tr.r("melody")
    fl = []
    pp = period(rm, R_FAST, lo=-1, hi=6, first=3)
    for p, notes in enumerate(pp):
        fl += to_flute(tr, notes, sc, tr.tb(8 + 2 * p), rm, octave=1, grace_p=0.35, gap=0.04, subst={sc(1) + 12: sc(1) + 11})
    tr.flute("flute", fl, tr.r("flute_sig"), kind="xiao", vib_depth=22, vib_rate=4.4)
    rdr = tr.r("drip")
    for _ in range(14):
        f0 = float(np.exp(rdr.uniform(np.log(800), np.log(2200))))
        tr.add("drip", bubble(rdr, f0, tau=rdr.uniform(0.01, 0.02), rise=rdr.uniform(0.8, 1.6)), rdr.uniform(0, tr.T), rdr.uniform(0.4, 1.0))
    return tr.mix(t60=2.2, wet=0.32)
