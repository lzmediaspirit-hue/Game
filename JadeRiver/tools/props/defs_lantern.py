"""Act III (the Lantern Star Field) props: the old bronze cages that hold a fallen star over every
drifting island, Lanternfall Harbor's cranes, buoys and moored hulks, the Blackmast pirates' guns,
the Wyrmnest eggs and nests, the Star Warden Citadel and the Orbit Ruins, the Ashborn war camp,
the Tidebreak Bastion and the Hollow hives, the Nebula Deep and the Lantern Heart. Same conventions
as defs_expanse: short hue-shifted ramps, light from the upper left, dark outline, deterministic
noise; star light, flames, glows and motes go on after the outline so they never get inked."""
from __future__ import annotations

import math

import numpy as np

from defs_expanse import (EMBER, SAIL_OLD, STARLIGHT, WRECK_WOOD, FADED_LACQUER, FADED_ROOF, _chunk, _idx_fill,
                          _rot, _spline, tube)
from palette import *  # noqa: F401,F403
from parts import blob_mask, facet_field, grass_tuft, ground_shadow, lathe, motes, rock, smoke, sparks, wisp
from pixlib import (Canvas, bbox, border, bottom_edge, dilate, ellipse_ring, erode, glow, grid, hexc, left_edge,
                    m_curve, m_ellipse, m_line, m_poly, m_rect, outline, right_edge, rng, seed_of, shade, shift,
                    sparkle, top_edge, vnoise)
from registry import prop

# star light: the fallen stars burn white-gold from the core outward
STARFIRE = ramp("#6b3a12", "#a86421", "#dc9c3c", "#f3c966", "#ffe6a0", "#fff6d6")
STARFLAME = (STARFIRE[2], STARFIRE[3], STARFIRE[4], STARFIRE[5], WHITE_HOT)
STAR_HALO = hexc("#ffe2a0")
# a star gone out: a cracked grey cinder
CINDER = ramp("#16171b", "#24262b", "#373a40", "#4f5258", "#6b6e72", "#8b8d8f")
LANTERN_STATES = (("idle", 4, 5),)


def _bronze(cv, m, base=0.55, gain=1.2, mode="bevel", R=1, vg=0.0, seed="bronze", contour=True, **kw):
    """Old bronze: shaded with the BRONZE ramp, green verdigris gathered in the lower recesses."""
    shade(cv, m, BRONZE, contour=contour, mode=mode, R=R, base=base, gain=gain, **kw)
    if vg > 0 and m.any():
        W, H = cv.w, cv.h
        yy = grid(W, H)[1]
        x0, y0, x1, y1 = bbox(m)
        nz = vnoise(W, H, 3, seed_of("verdigris", seed), 2)
        low = (yy - y0) / max(1.0, y1 - y0)
        g = m & erode(m) & (nz + low * 0.35 > 1.12 - vg)
        cv.fill(g, VERDIGRIS[1])
        cv.fill(g & (nz > 0.62) & shift(g, 0, 1), VERDIGRIS[2])
    return m


def _star_body(cv, cx, cy, r, f=0, lit=True, seed="star"):
    """A fallen star: a rough, faceted lump of star-stuff. Lit, it burns white-gold from the core
    out (brighter each pulse); gone out, it is a cracked grey cinder lit only from the upper left."""
    W, H = cv.w, cv.h
    xx, yy = grid(W, H)
    m = blob_mask(W, H, cx, cy, r, r * 1.05, ("lstar", seed), 0.16, harmonics=5)
    fx, fy, _ = facet_field(m, ("lstar", seed), 3)
    if lit:
        pulse = (0.0, 0.45, 0.9, 0.45)[f % 4]
        d = np.hypot(xx - cx + 0.5, yy - cy + 0.5) / max(r, 1.0)
        v = 5.2 - d * 3.3 + (-fx * 0.55 - fy * 0.75) * 1.4 + pulse
        _idx_fill(cv, m, STARFIRE, np.clip(v, 1.0, 5.0))
        cr = max(1.0, r * (0.34 + 0.06 * pulse))
        cv.fill(m_ellipse(W, H, cx - 0.5, cy - 0.5, cr, cr) & m, WHITE_HOT)
    else:
        nz = vnoise(W, H, 2, seed_of("cinder", seed), 2)
        shade(cv, m, CINDER, contour=False, R=2, base=0.5, gain=1.3, noise=nz, namp=0.3, normal=(fx, fy))
        g = rng("cinder_cracks", seed)
        for _ in range(3):
            a = g.uniform(0, 2 * math.pi)
            p0 = (cx + math.cos(a) * r * 0.15, cy + math.sin(a) * r * 0.15)
            p1 = (cx + math.cos(a + 0.4) * r * 0.8, cy + math.sin(a + 0.4) * r * 0.8)
            cv.fill(m_line(W, H, [p0, p1]) & erode(m), CINDER[0])
    return m


def _star_rays(cv, cx, cy, r, f, reach=6, block=None, alpha=1.0):
    """Four long and four short rays thrown by a lit star; they stretch a pixel with each pulse.
    Pixels in `block` (bars in front of the star) are left alone."""
    pulse = (0, 1, 2, 1)[f % 4]
    for dirs, L in ((((1, 0), (-1, 0), (0, 1), (0, -1)), r + reach + pulse),
                    (((1, 1), (-1, 1), (1, -1), (-1, -1)), r * 0.72 + reach * 0.35 + pulse * 0.5)):
        for dx, dy in dirs:
            n = int(L)
            for k in range(int(r * 0.6), n + 1):
                t = k / max(1.0, L)
                x, y = int(cx) + dx * k, int(cy) + dy * k
                if not (0 <= x < cv.w and 0 <= y < cv.h) or (block is not None and block[y, x]):
                    continue
                c = WHITE_HOT if t < 0.45 else (STARFIRE[5] if t < 0.75 else STARFIRE[4])
                cv.put(x, y, c, alpha * (1.0 if t < 0.75 else 0.65))


def _flame(cv, cx, by, w, h, f, seed, pal=STARFLAME, tongues=3, lean=0.0, block=None, licks=True):
    """A licking flame of several tongues over a continuous base, layered from a darker rim to a
    white-hot heart low down; each of the 4 frames re-rolls the tongue heights and sway so the fire
    flickers, and now and then a lick breaks off above the tallest tongue."""
    W, H = cv.w, cv.h
    yy = grid(W, H)[1]
    g = rng("flame", seed, f % 4)
    layers = [np.zeros((H, W), bool) for _ in range(4)]
    hw0 = w / (tongues + 1.0)
    tallest = (cx, by - h)
    for k in range(tongues):
        off = (k - (tongues - 1) / 2.0) / max(1, tongues - 1) if tongues > 1 else 0.0
        tx = cx + off * w * 0.62 + g.uniform(-0.5, 0.5)
        th = h * (1.0 - abs(off) * 0.85) * g.uniform(0.72, 1.05)
        tw = hw0 * (1.0 - abs(off) * 0.3)
        sway = g.uniform(-1.4, 1.4) + lean + off * 1.5
        if k == tongues // 2:
            tallest = (tx + sway, by - th)
        for li, (sh, sw) in enumerate(((1.0, 1.0), (0.66, 0.72), (0.42, 0.5), (0.2, 0.34))):
            hh, hw = th * sh, tw * sw
            n = max(4, int(hh) + 1)
            left = [(tx - hw * (1 - t) ** 0.6 + sway * t * t * sh, by - hh * t) for t in np.linspace(0, 1, n)]
            right = [(tx + hw * (1 - t) ** 0.6 + sway * t * t * sh, by - hh * t) for t in np.linspace(1, 0, n)]
            layers[li] |= m_poly(W, H, left + right)
    for li, (sw, sh) in enumerate(((0.5, 0.2), (0.4, 0.14), (0.28, 0.09), (0.16, 0.05))):
        layers[li] |= m_ellipse(W, H, cx, by, w * sw, max(1.0, h * sh)) & (yy <= by)
    if licks and f % 2 == 0:
        lx, ly = tallest[0] + g.uniform(-1, 1), tallest[1] - 2 - int(g.integers(0, 3))
        layers[0] |= m_poly(W, H, [(lx - 1, ly + 2), (lx + 1, ly + 2), (lx + 0.5, ly - 1)])
    if block is not None:
        layers = [m & ~block for m in layers]
    cv.fill(layers[0], pal[1])
    cv.fill(border(layers[0]) & ~bottom_edge(layers[0]), pal[0])
    cv.fill(layers[1], pal[2])
    cv.fill(layers[2], pal[3])
    cv.fill(layers[3], pal[4])
    return layers[0]


# ------------------------------------------------------------------ the lantern cage (signature prop)
@prop("lantern_cage", 48, 96, states=(("idle", 4, 5), ("dark", 1, 0)), ground=3)
def lantern_cage(state, f):
    """One of the Star Wardens' lantern stars: a fallen star held in an old bronze cage on a post,
    burning so the dark between the islands stays thin. The back bars glow gold where the star
    lights them, the front bars cross it as dark silhouettes, and the star breathes brighter and
    dimmer. Dark, the star is a grey cinder and the cage is only old bronze in the night."""
    W, H = 48, 96
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 93
    cx, cy, r = 24, 31, 8
    ccx = cx - 0.5
    lit = state != "dark"
    ground_shadow(cv, cx, gy, 17, 1.6)
    nz = vnoise(W, H, 3, seed_of("lantern_cage"), 2)
    # plinth: two dressed stone steps with a carved band, streaked green below the bronze foot
    for (x0, x1, y0, y1) in ((cx - 15, cx + 14, 88, gy), (cx - 11, cx + 10, 83, 87)):
        blk = m_rect(W, H, x0, y0, x1, y1)
        shade(cv, blk, STONE, contour=True, R=1, base=0.52, gain=1.1, noise=nz, namp=0.15)
        cv.fill(m_rect(W, H, x0, y0, x1, y0), STONE[5])
        cv.fill(m_rect(W, H, x0, y0, x0, y1), STONE[4])
    cv.fill(m_rect(W, H, cx - 13, 90, cx + 12, 90) & ((xx % 3) != 0), STONE[2])
    for sx, ln in ((cx - 3, 5), (cx + 1, 3), (cx + 3, 6)):
        cv.fill(m_rect(W, H, sx, 84, sx, 83 + ln) & ~m_rect(W, H, sx, 88, sx, 88), VERDIGRIS[1])
    # bronze post with collars and a flared foot
    _bronze(cv, lathe(W, H, ccx, [(78, 3), (81, 5), (83, 7)]), base=0.55, gain=1.1, mode="cyl")
    cv.fill(m_rect(W, H, cx - 6, 82, cx + 5, 82), GOLD[4])
    _bronze(cv, m_rect(W, H, cx - 2, 56, cx + 1, 79), mode="cyl", base=0.55, gain=1.2, vg=0.25, seed="cage_post")
    for cy_ in (59, 72):
        band = m_rect(W, H, cx - 3, cy_, cx + 2, cy_ + 1)
        _bronze(cv, band, mode="cyl", base=0.6, gain=1.1)
        cv.fill(m_rect(W, H, cx - 3, cy_, cx + 1, cy_), GOLD[5])
    # the cage: six bars on a lathe profile (three behind the star, three in front) and three hoops
    prof = [(16, 7.5), (19, 12.0), (25, 15.4), (32, 16.2), (40, 15.0), (47, 11.0), (52, 7.0)]
    py = [p[0] for p in prof]
    ph = [p[1] for p in prof]
    ys = np.arange(16, 53)
    hw = np.interp(ys, py, ph)
    interior = erode(lathe(W, H, ccx, prof))
    bars_front = np.zeros((H, W), bool)
    bars_back = np.zeros((H, W), bool)
    for k in range(6):
        th = (k + 0.25) * 2 * math.pi / 6
        m = m_line(W, H, [(ccx + h_ * math.sin(th), y_) for y_, h_ in zip(ys, hw)])
        if math.cos(th) > 0:
            bars_front |= m
        else:
            bars_back |= m
    back_hoops = np.zeros((H, W), bool)
    front_hoops = np.zeros((H, W), bool)
    for hy_, thick in ((16, 1), (43, 2), (52, 1)):
        rx = float(np.interp(hy_, py, ph)) + 0.5
        ring = ellipse_ring(W, H, ccx, hy_, rx, max(1.0, rx * 0.2))
        if hy_ < 50:
            back_hoops |= ring & (yy < hy_)
        if thick > 1:
            ring |= shift(ring, 0, 1)
        front_hoops |= ring & (yy >= hy_)
    back = bars_back | back_hoops
    d = np.hypot(xx - ccx, yy - cy)
    if lit:
        cv.fill(back, BRONZE[4])
        cv.fill(back & (d < 14), GOLD[4])
        cv.fill(back & (d < 10.5), STARFIRE[4])
    else:
        cv.fill(back, BRONZE[2])
        cv.fill(back & (xx < cx) & (yy < 30), BRONZE[3])
    star = _star_body(cv, ccx, cy, r, f, lit, seed="cage")
    front = bars_front | front_hoops
    cv.fill(front, BRONZE[3])
    cv.fill(front & (xx < cx - 8), BRONZE[5] if not lit else BRONZE[4])
    cv.fill(front & (xx > cx + 8), BRONZE[2])
    if lit:
        cv.fill(front & dilate(star), BRONZE[1])
        cv.fill(front_hoops & (yy == 43) & (np.abs(xx - cx) < 9), GOLD[4])
    # the cup under the cage and the domed cap with upturned eaves and a star finial
    cup = lathe(W, H, ccx, [(52, 8.0), (54, 9.0), (56, 7.0), (58, 4.0)])
    _bronze(cv, cup, mode="cyl", base=0.5, gain=1.2)
    cv.fill(cup & (yy == 52), GOLD[5] if lit else GOLD[3])
    cap = lathe(W, H, ccx, [(7, 2.5), (9, 5.0), (11, 8.0), (13, 11.0), (14.5, 13.5), (16, 15.0)])
    for sgn in (-1, 1):
        cap |= m_poly(W, H, [(ccx + sgn * 12, 14), (ccx + sgn * 17.5, 11.5), (ccx + sgn * 16.5, 14.5),
                             (ccx + sgn * 13, 16.5)])
    _bronze(cv, cap, base=0.55, gain=1.3, R=2, top=0.15)
    pat = cap & (nz > 0.5) & (yy < 13) & erode(cap)
    cv.fill(pat, PATINA[2])
    cv.fill(pat & (xx < cx - 1), PATINA[3])
    rim = cap & ~shift(cap, 0, -1)
    cv.fill(rim, BRONZE[1])
    for k in range(-3, 4):
        cv.put(cx - 1 + k * 4, 15, GOLD[4] if k < 1 else GOLD[3])
    if lit:
        cv.fill(rim & (np.abs(xx - cx) < 12), STARFIRE[3])
    fin = (m_rect(W, H, cx - 1, 2, cx, 7) | m_rect(W, H, cx - 3, 4, cx + 2, 4)
           | m_poly(W, H, [(cx - 1, 2), (cx - 0.5, 1), (cx, 2)]))
    _bronze(cv, fin, base=0.6, gain=1.0)
    cv.fill(m_rect(W, H, cx - 1, 3, cx - 1, 5) | m_rect(W, H, cx - 3, 4, cx - 1, 4), GOLD[5])
    outline(cv, skip=interior & ~cv.solid)
    if lit:
        a = (0.07, 0.09, 0.12, 0.09)[f % 4]
        glow(cv, ccx, cy + 1, 21, 23, STAR_HALO, steps=((1.0, a * 0.55), (0.72, a * 0.8), (0.45, a * 1.1)))
        cv.light(interior & ~cv.solid & (d < 13), STARFIRE[4], 0.16 + a)
        _star_rays(cv, cx, cy, r, f, reach=3, block=front)
        motes(cv, 8, 6, 40, 52, f, 4, "cage_m", count=5, pal=(PALE_GOLD, WHITE_HOT))
    return cv


# ------------------------------------------------------------------ star lantern post
@prop("star_lantern_post", 20, 72, states=LANTERN_STATES, ground=3)
def star_lantern_post(state, f):
    """A bronze street lantern of Lanternfall Harbor: a six-sided lamp of glass panes under a small
    upswept roof, burning a sliver of star-light instead of oil."""
    W, H = 20, 72
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 69
    cx = 10
    ground_shadow(cv, cx, gy, 7, 1.3)
    foot = m_rect(W, H, 5, 64, 14, gy)
    shade(cv, foot, STONE, contour=True, R=1, base=0.5, gain=1.1)
    cv.fill(m_rect(W, H, 5, 64, 14, 64), STONE[5])
    _bronze(cv, lathe(W, H, cx, [(59, 2), (61, 3), (63, 4.5)]), mode="cyl", base=0.55)
    _bronze(cv, m_rect(W, H, 9, 22, 11, 60), mode="cyl", base=0.55, gain=1.2, vg=0.35, seed="slp")
    for by in (38, 50):
        cv.fill(m_rect(W, H, 8, by, 12, by + 1), BRONZE[3])
        cv.fill(m_rect(W, H, 8, by, 11, by), GOLD[4])
    # a scrolled bracket and the cup the lamp stands in
    for s in (-1, 1):
        cv.fill(m_curve(W, H, [(cx + s * 1, 26), (cx + s * 4, 24), (cx + s * 5, 21)]), BRONZE[3] if s < 0 else BRONZE[2])
    _bronze(cv, lathe(W, H, cx, [(19, 5.5), (21, 4.0), (23, 2.0)]), mode="cyl", base=0.55)
    # the lamp: two narrow side panes and a front pane between bronze corner posts
    fl = (0.0, 0.5, 0.2, 0.8)[f % 4]
    panes = m_rect(W, H, 5, 10, 14, 18)
    cv.fill(panes, STARFIRE[3])
    cv.fill(m_rect(W, H, 8, 10, 11, 18), STARFIRE[4])
    cv.fill(m_rect(W, H, 8, 12 + (f % 2), 11, 18) & (yy > 15 - fl), STARFIRE[5])
    cv.fill(m_rect(W, H, 5, 10, 6, 18), STARFIRE[2])
    for px in (4, 7, 12, 15):
        cv.fill(m_rect(W, H, px, 9, px, 19), BRONZE[2] if px > 10 else BRONZE[4])
    cv.fill(m_rect(W, H, 4, 19, 15, 19), BRONZE[2])
    cv.fill(m_rect(W, H, 4, 9, 15, 9), BRONZE[4])
    # the star-light flame in the front pane: a white teardrop that leans and stretches
    lean = (0, 1, 0, -1)[f % 4]
    flame_m = m_poly(W, H, [(8.5, 17), (11.5, 17), (10 + lean * 0.6, 12 - (f % 2))])
    cv.fill(flame_m, STARFIRE[5])
    cv.fill(m_rect(W, H, 9, 15, 10, 17), WHITE_HOT)
    # the roof: upswept eaves, a patina ridge and a gold finial
    roof = m_poly(W, H, [(1, 8), (3, 8.5), (5, 7), (8, 4), (12, 4), (15, 7), (17, 8.5), (18.4, 8), (17, 9.5), (2, 9.5)])
    _bronze(cv, roof, base=0.55, gain=1.3, R=1, top=0.2)
    cv.fill(roof & (yy <= 5), PATINA[3])
    cv.fill(m_rect(W, H, 8, 4, 10, 4), PATINA[4])
    cv.fill(roof & ~shift(roof, 0, -1), BRONZE[1])
    fin = m_rect(W, H, 9, 1, 10, 3)
    cv.fill(fin, GOLD[3])
    cv.put(9, 1, GOLD[5])
    cv.put(9, 2, GOLD[5])
    outline(cv)
    a = (0.12, 0.16, 0.13, 0.18)[f % 4]
    glow(cv, cx - 0.5, 14, 9, 9, STAR_HALO, steps=((1.0, a * 0.6), (0.6, a)))
    if f % 4 == 1:
        sparkle(cv, 10, 13, 1, WHITE_HOT, STARFIRE[5], 0.9)
    return cv


# ------------------------------------------------------------------ wick pillar (the Lantern Heart)
@prop("wick_pillar", 32, 120, states=LANTERN_STATES, ground=3)
def wick_pillar(state, f):
    """A tall bronze pillar of the Wick Gate: a fluted shaft ringed with gilt collars and a star
    medallion, carrying a wide dish in which a braided star-wick burns with a tall white-gold
    flame that sheds sparks upward."""
    W, H = 32, 120
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 117
    cx = 16
    ground_shadow(cv, cx, gy, 14, 1.6)
    nz = vnoise(W, H, 3, seed_of("wick_pillar"), 2)
    for (x0, x1, y0, y1) in ((2, 29, 111, gy), (5, 26, 106, 110)):
        blk = m_rect(W, H, x0, y0, x1, y1)
        shade(cv, blk, STONE_DARK, contour=True, R=1, base=0.55, gain=1.1, noise=nz, namp=0.15)
        cv.fill(m_rect(W, H, x0, y0, x1, y0), STONE_DARK[5])
        cv.fill(m_rect(W, H, x0, y0, x0, y1), STONE_DARK[4])
    base = lathe(W, H, cx, [(96, 6.5), (99, 7.5), (102, 9.0), (105, 10.5)])
    _bronze(cv, base, mode="cyl", base=0.55, gain=1.2, vg=0.12, seed="wp_base")
    cv.fill(base & (yy == 96), GOLD[4])
    shaft = m_rect(W, H, 11, 30, 20, 96)
    _bronze(cv, shaft, mode="cyl", base=0.55, gain=1.3)
    for fx_ in (12, 14, 17, 19):
        cv.fill(m_rect(W, H, fx_, 34, fx_, 93), BRONZE[2] if fx_ > 15 else BRONZE[3])
    g = rng("wick_vg")
    for _ in range(5):
        vx = int(g.integers(12, 20))
        vy = int(g.integers(36, 80))
        cv.fill(m_rect(W, H, vx, vy, vx, vy + int(g.integers(3, 9))) & shaft, VERDIGRIS[1])
    for by in (30, 60, 66, 93):
        band = m_rect(W, H, 10, by, 21, by + 2)
        _bronze(cv, band, mode="cyl", base=0.6, gain=1.2)
        cv.fill(m_rect(W, H, 10, by, 20, by), GOLD[5])
        cv.fill(m_rect(W, H, 10, by + 2, 21, by + 2), BRONZE[1])
    # star medallion between the middle collars
    med = m_ellipse(W, H, 15.5, 45, 4.2, 4.2)
    _bronze(cv, med, mode="sphere", base=0.6, gain=1.2)
    star = (m_rect(W, H, 13, 45, 18, 45) | m_rect(W, H, 15, 42, 16, 48)) & med
    cv.fill(star, GOLD[4])
    cv.fill(m_rect(W, H, 15, 44, 15, 45), GOLD[6])
    cv.fill(ellipse_ring(W, H, 15.5, 45, 4.2, 4.2) & (xx + yy > 60), BRONZE[1])
    # the dish: a flared capital under a wide shallow bowl of coals
    capital = lathe(W, H, cx, [(22, 13.5), (24, 12.0), (26, 9.0), (28, 7.0), (30, 5.5)])
    _bronze(cv, capital, mode="cyl", base=0.55, gain=1.3, vg=0.25, seed="wp_cap")
    lip = m_ellipse(W, H, cx, 21, 14.5, 2.4)
    _bronze(cv, lip, base=0.6, gain=1.0)
    bed = m_ellipse(W, H, cx, 20.5, 12, 1.6)
    cv.fill(bed, EMBER[1])
    cv.fill(bed & (nz > 0.5), EMBER[3])
    cv.fill(m_rect(W, H, 3, 22, 29, 22) & capital, GOLD[4])
    # the braided wick
    wick = m_rect(W, H, 15, 16, 16, 20)
    cv.fill(wick, CINDER[2])
    cv.fill(wick & ((yy % 2) == 0) & (xx == 15), CINDER[4])
    outline(cv)
    _flame(cv, cx - 0.5, 20, 13, 15, f, "wick_pillar", tongues=3)
    sparkle(cv, 15 + (f % 2), 12 - (f % 4 == 2), 1, WHITE_HOT, STARFIRE[5], 0.95)
    a = (0.1, 0.13, 0.11, 0.14)[f % 4]
    glow(cv, cx - 0.5, 12, 12, 15, STAR_HALO, steps=((1.0, a * 0.6), (0.65, a), (0.35, a * 1.2)))
    sparks(cv, cx - 0.5, 4, f, 4, "wick_sp", count=6, spread=7, pal=STARFIRE)
    return cv


# ------------------------------------------------------------------ flame basin (the Lantern Heart)
@prop("flame_basin", 60, 44, states=LANTERN_STATES, ground=3)
def flame_basin(state, f):
    """A great bronze basin of the Hall of Burning Stars: a round-bellied tripod cauldron with
    upright ears and a band of cast cloud-and-thunder pattern, holding a broad white-gold flame."""
    W, H = 60, 44
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 41
    cx = 30
    ground_shadow(cv, cx, gy, 26, 1.8)
    # three legs: the far one first, then the two near ones with paw feet
    for lx, base, far in ((30, 0.35, True), (15, 0.6, False), (45, 0.45, False)):
        leg = m_poly(W, H, [(lx - 3, 32), (lx + 3, 32), (lx + 2, gy - 2 if not far else gy - 4), (lx - 2, gy - 2 if not far else gy - 4)])
        _bronze(cv, leg, mode="cyl", base=base - (0.15 if far else 0), gain=1.1)
        paw = m_ellipse(W, H, lx, (gy - 1.5) if not far else gy - 3.5, 3.5, 1.8) & (yy <= gy - (0 if not far else 2))
        _bronze(cv, paw, base=base, gain=1.0)
        if not far:
            for k in (-1, 1):
                cv.put(lx + k * 2, gy - 1, BRONZE[1])
    # the bowl: a round belly on a lathe profile, verdigris low on the belly
    bowl = lathe(W, H, cx, [(21, 23.0), (24, 23.5), (27, 22.5), (30, 20.0), (33, 16.0), (35, 11.0)])
    _bronze(cv, bowl, mode="cyl", base=0.5, gain=1.3, vg=0.12, seed="basin", ao=0.2)
    # the cast band: a meander of hooked spirals between two raised lines
    band = bowl & (yy >= 23) & (yy <= 27)
    cv.fill(band, BRONZE[2])
    cv.fill(bowl & ((yy == 23) | (yy == 27)), BRONZE[4])
    cv.fill(bowl & (yy == 23) & (xx < cx - 6), BRONZE[5])
    for mx in range(9, 52, 6):
        hook = (m_rect(W, H, mx, 24, mx + 3, 24) | m_rect(W, H, mx + 3, 24, mx + 3, 26) | m_rect(W, H, mx + 1, 26, mx + 3, 26)
                | m_rect(W, H, mx + 1, 25, mx + 1, 25))
        cv.fill(hook & band, GOLD[3] if mx < cx else GOLD[2])
    # ears on the rim
    for ex in (12, 48):
        ear = m_rect(W, H, ex - 2, 12, ex + 2, 21) & ~m_rect(W, H, ex - 1, 14, ex + 1, 19)
        _bronze(cv, ear, base=0.6 if ex < cx else 0.45, gain=1.1)
        cv.fill(m_rect(W, H, ex - 2, 12, ex + 2, 12), GOLD[4])
    # rim and the bed of glowing coals seen over it
    rim = m_ellipse(W, H, cx, 21, 23.5, 3.2) & ~m_ellipse(W, H, cx, 20.6, 21.5, 2.2)
    coals = m_ellipse(W, H, cx, 20.6, 21.5, 2.2)
    cv.fill(coals, EMBER[1])
    nz = vnoise(W, H, 2, seed_of("basin_coal", f % 2), 1)
    cv.fill(coals & (nz > 0.45), EMBER[3])
    cv.fill(coals & (nz > 0.7), STARFIRE[4])
    _bronze(cv, rim, base=0.62, gain=0.9)
    cv.fill(rim & (yy <= 19) & (xx < cx), GOLD[5])
    cv.fill(rim & (yy >= 22), GOLD[4])
    front = bowl & (yy >= 22)
    outline(cv)
    _flame(cv, cx - 0.5, 21, 30, 17, f, "flame_basin", tongues=5, block=front | rim & (yy >= 21))
    a = (0.1, 0.14, 0.11, 0.15)[f % 4]
    glow(cv, cx - 0.5, 14, 27, 16, STAR_HALO, steps=((1.0, a * 0.5), (0.7, a * 0.8), (0.4, a * 1.1)))
    sparks(cv, cx - 0.5, 4, f, 4, "basin_sp", count=8, spread=10, pal=STARFIRE)
    return cv


# ------------------------------------------------------------------ star buoy
@prop("star_buoy", 28, 40, states=LANTERN_STATES, ground=4)
def star_buoy(state, f):
    """A bronze buoy that marks the lantern lanes: a banded drum riding the star-sea, three struts
    over it holding a small caged star light. It bobs a pixel and sends out rings of light."""
    W, H = 28, 40
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    wl = 36
    cx = 14
    bob = (0, -1, -1, 0)[f % 4]
    # the rings it sends across the water (not outlined)
    rings = np.zeros((H, W), bool)
    for k in range(2):
        ph = ((f % 4) + k * 2) / 4.0
        rx = 6 + ph * 7
        rg = ellipse_ring(W, H, cx - 0.5, wl + 0.5, rx, 1.2 + ph * 1.3) & (yy >= wl - 1)
        cv.fill(rg, STARLIGHT[5] if k else STARFIRE[4], 0.75 - ph * 0.5)
        rings |= rg
    body = lathe(W, H, cx - 0.5, [(20 + bob, 3.5), (22 + bob, 7.0), (25 + bob, 9.5), (29 + bob, 10.5), (wl + 1, 10.5)]) & (yy <= wl)
    _bronze(cv, body, mode="cyl", base=0.55, gain=1.3, vg=0.1, seed="buoy")
    for by, pal in ((27, CLOTH_RED), (32, CLOTH_RED)):
        b = body & (yy >= by + bob) & (yy <= by + bob + 1)
        shade(cv, b, pal, mode="cyl", base=0.55, gain=1.0)
    cv.fill(body & (yy == 26 + bob), GOLD[4])
    cv.fill(body & (yy == wl), BRONZE[1])
    deck = m_ellipse(W, H, cx - 0.5, 20.5 + bob, 4.5, 1.2)
    _bronze(cv, deck, base=0.62, gain=0.8)
    # three struts rising to the lamp cage
    ly = 11 + bob
    for sx, c in ((cx - 6, BRONZE[4]), (cx + 5, BRONZE[2]), (cx - 0.5, BRONZE[3])):
        cv.fill(m_line(W, H, [(sx, 21 + bob), (cx - 0.5 + (sx - cx) * 0.35, ly + 4)]), c)
    lamp = m_ellipse(W, H, cx - 0.5, ly, 3.2, 3.6)
    _star_body(cv, cx - 0.5, ly, 2.4, f, True, seed="buoy")
    for bx in (-2, 1):
        cv.fill(m_rect(W, H, cx + bx, ly - 3, cx + bx, ly + 3) & lamp, BRONZE[2])
    cv.fill(m_rect(W, H, cx - 3, ly + 3, cx + 2, ly + 4), BRONZE[3])
    cv.fill(m_rect(W, H, cx - 3, ly - 4, cx + 2, ly - 4), BRONZE[4])
    ring_top = ellipse_ring(W, H, cx - 0.5, ly - 6.5, 1.6, 1.6)
    cv.fill(ring_top, BRONZE[4])
    outline(cv, skip=rings & ~cv.solid)
    a = (0.12, 0.16, 0.2, 0.16)[f % 4]
    glow(cv, cx - 0.5, ly, 8, 8, STAR_HALO, steps=((1.0, a * 0.6), (0.55, a)))
    if f % 4 == 2:
        sparkle(cv, cx - 1, ly - 1, 2, WHITE_HOT, STARFIRE[5], 0.9)
    # the buoy's light shivering on the water under it
    for k in range(3):
        rx0 = cx - 3 + ((k * 3 + f) % 5) - 2
        cv.fill(m_rect(W, H, rx0, wl + 1 + k, rx0 + 2 - (k == 2), wl + 1 + k) & ~cv.solid, STARFIRE[4], 0.45 - k * 0.1)
    return cv


# ------------------------------------------------------------------ Lanternfall Harbor: the harbour crane
NET_CARGO = ramp("#3a2c1a", "#5e4a2c", "#86704a", "#ac9668", "#cdb98a", "#e8d9ae")


@prop("harbor_crane", 80, 110, ground=3)
def harbor_crane(state, f):
    """A wooden harbour crane on the Arrival Quay: a braced mast on a stone footing, a long jib
    pivoted halfway up with a box of stones for a counterweight, a stay to the masthead, a winch
    drum at the foot, and a rope cargo net bulging with crates and sacks hung from the jib tip."""
    W, H = 80, 110
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 107
    nz = vnoise(W, H, 3, seed_of("crane"), 2)
    ground_shadow(cv, 26, gy, 22, 1.8)
    ground_shadow(cv, 67, gy, 11, 1.4, a=0.25)
    # stone footing of the quay
    for (x0, x1, y0, y1) in ((4, 44, 101, gy), (9, 38, 97, 100)):
        blk = m_rect(W, H, x0, y0, x1, y1)
        shade(cv, blk, STONE, contour=True, R=1, base=0.5, gain=1.1, noise=nz, namp=0.15)
        cv.fill(m_rect(W, H, x0, y0, x1, y0), STONE[5])
    for jx in (14, 26, 36):
        cv.fill(m_rect(W, H, jx, 102, jx, gy), STONE[2])
    # the hoist rope runs from the winch up the jib (drawn first, the timbers cover it)
    piv = (23.5, 62.0)
    tip = (72.0, 21.0)
    back = (9.0, 71.0)
    cv.fill(m_line(W, H, [(31, 86), (27, 64), (tip[0] - 1, tip[1] + 3)]), ROPE[2])
    # mast and its two braces
    mast = m_rect(W, H, 21, 14, 26, 97)
    shade(cv, mast, WOOD, contour=True, mode="cyl", base=0.55, gain=1.1)
    for by in (30, 78):
        band = m_rect(W, H, 20, by, 27, by + 1)
        cv.fill(band, IRON[3])
        cv.fill(m_rect(W, H, 20, by, 25, by), IRON[5])
    for (x0, y0, x1, y1) in ((9, 97, 21, 76), (38, 97, 26, 80)):
        br = tube(W, H, [(x0, y0), (x1, y1)], 1.4)
        shade(cv, br, WOOD, contour=True, R=1, base=0.5 if x0 < 20 else 0.4, gain=1.1)
    cap = m_rect(W, H, 19, 11, 28, 14)
    shade(cv, cap, WOOD, contour=True, R=1, base=0.6, gain=1.0)
    cv.fill(m_rect(W, H, 19, 11, 28, 11), WOOD[5])
    # the jib: one long timber through the pivot, counterweight box on its short end
    jib = tube(W, H, [back, piv, tip], 2.6, 1.7)
    shade(cv, jib, WOOD, contour=True, R=1, base=0.58, gain=1.2)
    cv.fill(jib & ~shift(jib, 0, 1) & ~shift(jib, 1, 0), WOOD[5])
    ux, uy = tip[0] - back[0], tip[1] - back[1]
    n = math.hypot(ux, uy)
    for t in (0.35, 0.62, 0.85):
        bx, by_ = back[0] + ux * t, back[1] + uy * t
        cv.fill(m_line(W, H, [(bx - uy / n * 2, by_ + ux / n * 2), (bx + uy / n * 2, by_ - ux / n * 2)]) & jib,
                IRON[3])
    for sx in (5, 13):
        cv.fill(m_line(W, H, [(9, 71), (sx, 77)]), ROPE[2])
    for k, (sx, sy) in enumerate(((6, 78), (11, 77), (9, 76))):
        rock(cv, sx, sy, 2.4, 2.0, ("crane_ballast", k), pal=STONE, R=1, facets=1)
    box = m_rect(W, H, 3, 77, 15, 84)
    shade(cv, box, WOOD, contour=True, R=1, base=0.45, gain=1.1)
    cv.fill(m_rect(W, H, 3, 77, 15, 77), WOOD[5])
    cv.fill(m_rect(W, H, 3, 80, 15, 80) | m_rect(W, H, 9, 78, 9, 84), WOOD[2])
    for bx in (3, 15):
        cv.fill(m_rect(W, H, bx, 78, bx, 84), IRON[3])
    boss = m_ellipse(W, H, piv[0], piv[1], 2.2, 2.2)
    shade(cv, boss, IRON, contour=True, mode="sphere", base=0.6, gain=1.0)
    # the stay from the masthead to the jib tip, and the pulley block
    cv.fill(m_line(W, H, [(26, 12), (tip[0] - 1, tip[1] - 1)]), ROPE[3])
    blk = m_rect(W, H, tip[0] - 1, tip[1] + 1, tip[0] + 2, tip[1] + 5)
    shade(cv, blk, WOOD, contour=True, R=1, base=0.5, gain=1.0)
    cv.put(tip[0], tip[1] + 3, IRON[4])
    # winch: a drum wound with rope, a spoked handwheel beside it
    drum = m_rect(W, H, 28, 83, 35, 89)
    shade(cv, drum, WOOD, contour=True, mode="cylh", base=0.55, gain=1.1)
    cv.fill(drum & ((yy % 2) == 0) & (xx > 28) & (xx < 35), ROPE[3])
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        cv.fill(m_line(W, H, [(39, 86), (39 + math.cos(a) * 4.5, 86 + math.sin(a) * 4.5)]),
                WOOD[5] if k in (2, 3) else WOOD[3])
    cv.fill(m_ellipse(W, H, 39, 86, 1.3, 1.3), IRON[4])
    # the hoist line from the block down to the hook, and the net
    hx = int(tip[0]) - 1
    cv.fill(m_line(W, H, [(hx, tip[1] + 6), (hx - 1, 60)]), ROPE[3])
    cv.fill(m_rect(W, H, hx - 2, 60, hx, 62), IRON[4])
    bag = blob_mask(W, H, 67, 76, 11.5, 12, "crane_net", 0.08) & (yy >= 64)
    bag |= m_poly(W, H, [(hx - 2, 62), (59, 70), (76, 70)])
    # cargo inside, seen through the mesh: a crate, three sacks, a small keg
    cv.fill(bag, NET_CARGO[0])
    crate = m_rect(W, H, 58, 74, 68, 84) & bag
    shade(cv, crate, WOOD, R=1, base=0.55, gain=1.1)
    cv.fill(crate & ((xx == 58) | (yy == 74)), WOOD[5])
    cv.fill(crate & (np.abs((xx - 58) - (yy - 74)) < 0.6), WOOD[2])
    for (sx, sy, rx, ry, pal) in ((72, 80, 5.5, 6, STRAW), (70, 69, 5, 4, PAPER_R), (62, 68, 3.5, 3, STRAW)):
        sm = m_ellipse(W, H, sx, sy, rx, ry) & bag
        shade(cv, sm, pal, mode="sphere", base=0.5, gain=1.1)
    keg = m_rect(W, H, 64, 83, 71, 87) & bag
    shade(cv, keg, WOOD, mode="cylh", base=0.5, gain=1.0)
    cv.fill(keg & (xx % 3 == 0), IRON[3])
    mesh = bag & ((((xx + yy) % 4) == 0) | (((xx - yy) % 4) == 0))
    cv.fill(mesh & (xx < 68), ROPE[4])
    cv.fill(mesh & (xx >= 68), ROPE[3])
    cv.fill(border(bag), ROPE[2])
    for k, sx in enumerate((58, 62, 72, 77)):
        cv.fill(m_line(W, H, [(hx - 1, 62), (sx, 68 + (k in (0, 3)))]), ROPE[3])
    # a small star lantern hung from the masthead
    cv.fill(m_rect(W, H, 18, 15, 18, 17), INK)
    lamp = m_rect(W, H, 16, 18, 19, 22)
    cv.fill(lamp, STARFIRE[4])
    cv.fill(m_rect(W, H, 17, 19, 18, 21), STARFIRE[5])
    cv.fill(m_rect(W, H, 16, 17, 19, 17) | m_rect(W, H, 16, 23, 19, 23), BRONZE[3])
    outline(cv)
    glow(cv, 17.5, 20, 6, 6, STAR_HALO, steps=((1.0, 0.1), (0.55, 0.14)))
    return cv


# ------------------------------------------------------------------ Drifting Shoals: driftglass
DRIFTGLASS = ramp("#1c1236", "#38246a", "#583e9a", "#5a74b8", "#58b3c4", "#a2e8e4", "#effffb")


def _glass_shard(cv, x, by, h, w, lean, see=0.35, pal=DRIFTGLASS):
    """One translucent driftglass shard standing on row `by`: a long hexagonal prism, violet at the
    root and teal toward the tip, lit on its left facet, with a refraction line down the middle.
    Whatever it stands in front of shows faintly through it (`see`)."""
    W, H = cv.w, cv.h
    xx, yy = grid(W, H)
    tipx, tipy = x + lean, by - h
    m = m_poly(W, H, [(x - w / 2, by), (x - w / 2 + lean * 0.8, by - h * 0.78), (tipx, tipy),
                      (x + w / 2 + lean * 0.8, by - h * 0.78), (x + w / 2, by)])
    t = np.clip((by - yy) / max(1.0, h), 0, 1)
    mid = x + lean * t
    v = 1.3 + t * 2.6 + np.where(xx < mid - 0.3, 1.0, np.where(xx > mid + 0.6, -0.7, 0.2))
    under = cv.rgb.copy()
    had = cv.a > 0.5
    _idx_fill(cv, m, pal, np.clip(v, 1, len(pal) - 2))
    behind = m & had
    cv.rgb[behind] = cv.rgb[behind] * (1 - see) + under[behind] * see
    core = m_line(W, H, [(x + 0.3, by - 1), (x + lean * 0.7 + 0.3, by - h * 0.7)]) & erode(m)
    cv.fill(core, pal[len(pal) - 2])
    cv.fill(left_edge(m) & (yy < by - 1), pal[len(pal) - 2])
    cv.fill(right_edge(m) & ~left_edge(m), pal[1])
    cv.put(round(tipx), round(tipy) + 1, pal[-1])
    return m


@prop("driftglass_cluster", 40, 30, ground=3)
def driftglass_cluster(state, f):
    """A clump of driftglass on a shoal rock: long translucent shards, violet at the root and teal at
    the tip, grown out of dark stone at every angle, giving off a faint cold light."""
    W, H = 40, 30
    cv = Canvas(W, H)
    gy = 27
    ground_shadow(cv, 20, gy, 18, 1.5)
    # shards behind the rock, then the rock, then the front shards
    for (x, h, w, lean) in ((13, 15, 4, -3), (25, 18, 5, 2), (20, 20, 5, -1)):
        _glass_shard(cv, x, gy - 5, h, w, lean)
    rock(cv, 20, gy, 15, 6, "driftglass_rock", pal=STONE_DARK, R=2, base=0.5, facets=2)
    rock(cv, 32, gy, 4.5, 3.5, "driftglass_rock2", pal=STONE_DARK, R=1, facets=1)
    for (x, by, h, w, lean) in ((8, gy - 1, 10, 3, -3), (30, gy - 2, 13, 4, 3), (16, gy - 2, 9, 3, -1),
                                (35, gy - 1, 7, 3, 2), (24, gy - 1, 6, 3, 1)):
        _glass_shard(cv, x, by, h, w, lean, see=0.25)
    for (px, py) in ((12, 22), (27, 23), (21, 21)):
        cv.put(px, py, DRIFTGLASS[4])
        cv.put(px + 1, py, DRIFTGLASS[2])
    outline(cv)
    glow(cv, 21, 12, 14, 12, DRIFTGLASS[4], steps=((1.0, 0.05), (0.6, 0.08)))
    sparkle(cv, 19, 3, 1, WHITE_HOT, DRIFTGLASS[5], 0.8)
    return cv


# ------------------------------------------------------------------ Drifting Shoals: a moored hulk
QI_MIST_GREY = ramp("#3e5663", "#6f8a96", "#a9bec6")
FELT_PATCH = ramp("#4b3b2f", "#6e5846", "#95795e", "#b79c7c", "#d5bf9e")


@prop("moored_hulk", 160, 90, ground=4)
def moored_hulk(state, f):
    """The rotting hull of an old sky-junk moored at the Moored Hulks: listing a little on a thin,
    failing cushion of Qi mist, planks grey with age and patched with newer boards, the stern
    windows boarded over, a patched sail-cloth awning over the waist where the shoal-folk rest, a
    lantern on the stump of the mainmast, a rope ladder down the side and two mooring lines."""
    W, H = 160, 90
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 86
    nz = vnoise(W, H, 4, seed_of("hulk"), 2)
    nz2 = vnoise(W, H, 2, seed_of("hulk2"), 2)
    # mooring bollards and lines
    for px in (8, 152):
        ground_shadow(cv, px, gy, 5, 1.2)
        post = m_rect(W, H, px - 2, gy - 9, px + 1, gy)
        shade(cv, post, WRECK_WOOD, contour=True, mode="cyl", base=0.55, gain=1.1)
        cv.fill(m_rect(W, H, px - 3, gy - 10, px + 2, gy - 9), IRON[3])
    cv.fill(m_curve(W, H, [(8, gy - 8), (14, gy - 16), (22, 58)]), ROPE[2])
    cv.fill(m_curve(W, H, [(152, gy - 8), (146, gy - 18), (140, 55)]), ROPE[2])
    # the failing Qi cushion: thin grey-blue lobes
    for i, (cx, rx) in enumerate(((52, 20), (84, 24), (114, 18))):
        lobe = m_ellipse(W, H, cx, 72, rx, 4.5) & ~m_ellipse(W, H, cx + 4, 77, rx - 2, 3.5)
        lobe &= ~((vnoise(W, H, 3, seed_of("hulk_mist"), 1) > 0.62) & (yy > 70))
        cv.fill(lobe, QI_MIST_GREY[1], 0.45)
        cv.fill(lobe & (yy <= 70), QI_MIST_GREY[2], 0.55)
    a = math.radians(-3.0)
    P = _rot(16.0, 50.0, a)
    ca, sa = math.cos(a), math.sin(a)
    U = (xx - 16.0) * ca + (yy - 50.0) * sa
    V = -(xx - 16.0) * sa + (yy - 50.0) * ca
    L = 128.0

    def top_v(u):
        t = np.clip(np.asarray(u, float) / L, 0, 1)
        return (-9 * np.maximum(0.0, (0.2 - t) / 0.2) ** 1.2 - 7 * np.maximum(0.0, (t - 0.85) / 0.15) ** 1.4
                + 1.5 * np.sin(t * math.pi))

    def bot_v(u):
        t = np.clip(np.asarray(u, float) / L, 0, 1)
        return 20 - 7 * np.maximum(0.0, (0.15 - t) / 0.15) ** 1.3 - 11 * np.maximum(0.0, (t - 0.78) / 0.22) ** 1.5

    TV = top_v(U)
    # the mainmast stump and its lantern (behind the awning)
    stump = tube(W, H, [P(66, 0), P(66, -30)], 2.2, 1.9) & ~(V < -29 + ((xx * 5) % 3))
    shade(cv, stump, WRECK_WOOD, contour=True, mode="cyl", base=0.5, gain=1.1)
    cv.fill(tube(W, H, [P(66, -24), P(74, -24)], 0.8), WRECK_WOOD[3])
    lp = [int(round(v)) for v in P(74, -21)]
    cv.fill(m_rect(W, H, lp[0], lp[1] - 2, lp[0], lp[1]), INK)
    cv.fill(m_rect(W, H, lp[0] - 1, lp[1] + 1, lp[0] + 2, lp[1] + 4), STARFIRE[4])
    cv.fill(m_rect(W, H, lp[0], lp[1] + 2, lp[0] + 1, lp[1] + 3), WHITE_HOT)
    cv.fill(m_rect(W, H, lp[0] - 1, lp[1] + 5, lp[0] + 2, lp[1] + 5), BRONZE[3])
    pen = m_poly(W, H, [P(67, -30), P(78, -29), P(74, -27.5), P(79, -26), P(67, -26.5)])
    cv.fill(pen, FADED_LACQUER[3])
    cv.fill(bottom_edge(pen), FADED_LACQUER[1])
    # hull
    top = [P(u, float(top_v(u))) for u in np.arange(0, L + 0.5, 1.0)]
    bot = [P(u, float(bot_v(u))) for u in np.arange(0, L + 0.5, 1.0)]
    hull = m_poly(W, H, top + list(reversed(bot)))
    shade(cv, hull, WRECK_WOOD, contour=True, R=2, base=0.45, gain=1.1, noise=nz, namp=0.22)
    depth = V - TV
    cv.fill(hull & erode(hull) & (np.mod(depth, 4.0) < 0.9) & (depth > 3), WRECK_WOOD[1])
    k = np.floor(depth / 4.0)
    cv.fill(hull & erode(hull) & (np.mod(U + k * 19.0, 27.0) < 0.9) & (depth > 3), WRECK_WOOD[2])
    band = hull & (depth >= 1.5) & (depth < 3.5)
    shade(cv, band & ~(nz2 > 0.6), FADED_LACQUER, R=1, base=0.45, gain=0.8)
    rail = hull & (depth < 1.5)
    cv.fill(rail, WRECK_WOOD[4])
    cv.fill(rail & ~shift(hull, 0, 1), WRECK_WOOD[6])
    # holes rotted through, and newer boards nailed over others
    for (hu, hv, hw_, hh_) in ((40, 10, 5, 3), (97, 12, 4, 2.5), (60, 15, 3, 2)):
        c = P(hu, hv)
        hole = m_ellipse(W, H, c[0], c[1], hw_, hh_) & hull & erode(hull)
        cv.fill(hole, INK)
        cv.fill(hole & shift(~hole, 0, 1), WRECK_WOOD[0])
        cv.fill(dilate(hole) & ~hole & hull & (yy > c[1]), WRECK_WOOD[5])
    for (pu, pv, pw) in ((20, 7, 12), (78, 9, 14), (110, 6, 10)):
        patch = m_poly(W, H, [P(pu, pv), P(pu + pw, pv), P(pu + pw, pv + 3), P(pu, pv + 3)]) & hull
        shade(cv, patch, WOOD, R=1, base=0.55, gain=1.0)
        cv.fill(top_edge(patch), WOOD[5])
        for nu in (pu + 1, pu + pw - 1):
            q = P(nu, pv + 1.5)
            cv.put(q[0], q[1], IRON[2])
    # trailing cords and weed hanging from the keel
    g = rng("hulk_cords")
    for i in range(5):
        u = float(g.uniform(25, 110))
        q = P(u, float(bot_v(u)) - 1)
        ln = int(g.integers(2, 5))
        cv.fill(m_curve(W, H, [q, (q[0] + 1, q[1] + ln * 0.6), (q[0], q[1] + ln)]), ROPE[1])
    # stern castle with boarded windows under a sagging roof
    wall = m_poly(W, H, [P(0, -8), P(16, -7), P(16, -18), P(1, -19)])
    shade(cv, wall, FADED_LACQUER, contour=True, R=1, base=0.45, gain=0.8, noise=nz, namp=0.2)
    for wu in (3, 10):
        win = m_poly(W, H, [P(wu, -11), P(wu + 4, -11), P(wu + 4, -16), P(wu, -16)])
        cv.fill(win, INK)
        for bv in (-12.5, -14.5):
            cv.fill(m_line(W, H, [P(wu - 0.5, bv + 0.6), P(wu + 4.5, bv - 0.6)]), WRECK_WOOD[4])
    roof = m_poly(W, H, [P(-3, -17), P(8, -24), P(19, -17), P(17, -16.5), P(8, -21.5), P(-1, -16.5)])
    shade(cv, roof, FADED_ROOF, contour=True, R=1, base=0.5, gain=1.1)
    cv.fill(roof & ~shift(roof, 0, 1), FADED_ROOF[5])
    # the patched awning over the waist, on two poles
    for pu in (48, 92):
        cv.fill(tube(W, H, [P(pu, 0), P(pu, -14)], 0.7), WRECK_WOOD[3])
    awn = m_poly(W, H, [P(41, -8), P(46, -14), P(70, -19), P(94, -15), P(100, -9), P(94, -8.5), P(70, -12),
                        P(46, -8.5)])
    ridge_u = 70.0
    shade(cv, awn, SAIL_OLD, contour=True, R=1, mode="flat", base=0.62, gain=0.0,
          bias=np.where(U < ridge_u, 0.08, -0.12) - np.clip((V + 19) / 12.0, 0, 1) * 0.1)
    cv.fill(awn & (np.abs(U - ridge_u) < 0.7), SAIL_OLD[5])
    for (pu, pv, pal) in ((52, -12, CLOTH_BLUE), (78, -13, FELT_PATCH)):
        pm = m_poly(W, H, [P(pu, pv), P(pu + 7, pv), P(pu + 7, pv + 3), P(pu, pv + 3)]) & awn
        shade(cv, pm, pal, R=1, base=0.55, gain=0.8)
        cv.fill(border(pm) & ((xx + yy) % 2 == 0), SAIL_OLD[1])
    cv.fill(awn & ~shift(awn, 0, -1), SAIL_OLD[1])
    # rope ladder down the side
    lu = 104
    for s in (0, 3):
        cv.fill(m_line(W, H, [P(lu + s, 0), P(lu + s + 1, 30)]), ROPE[3])
    for rv in range(4, 30, 4):
        cv.fill(m_line(W, H, [P(lu, rv), P(lu + 3.5, rv)]), ROPE[4])
    outline(cv)
    glow(cv, lp[0] + 0.5, lp[1] + 2.5, 7, 7, STAR_HALO, steps=((1.0, 0.1), (0.55, 0.14)))
    return cv


# ------------------------------------------------------------------ Blackmast Haven: deck cannon and powder
@prop("pirate_cannon", 56, 34, states=(("idle", 1, 0), ("fire", 4, 10)), ground=3)
def pirate_cannon(state, f):
    """A bronze deck gun of Admiral Voss's gunners on a wooden truck carriage: a long barrel with
    reinforcing rings, lifting handles and a flared muzzle, a fuse at the touch hole. Firing, a
    white-hot flash bursts from the muzzle, the gun jumps back two pixels on its trucks and a cloud
    of powder smoke rolls out and thins."""
    W, H = 56, 34
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 31
    fire = state == "fire"
    ox = (0, -2, -1, 0)[f % 4] if fire else 0
    ground_shadow(cv, 24, gy, 20, 1.6)
    # carriage cheek: a stepped wooden side, higher at the front where the trunnion sits
    cheek = m_poly(W, H, [(8 + ox, 27), (8 + ox, 23), (16 + ox, 23), (16 + ox, 20), (26 + ox, 20), (26 + ox, 17),
                          (35 + ox, 17), (38 + ox, 22), (38 + ox, 27)])
    shade(cv, cheek, WOOD, contour=True, R=1, base=0.5, gain=1.1)
    cv.fill(top_edge(cheek), WOOD[5])
    cv.fill(m_line(W, H, [(10 + ox, 25), (36 + ox, 25)]) & cheek, WOOD[2])
    for bx in (12, 22, 32):
        cv.put(bx + ox, 24, IRON[4])
    # the two trucks (solid wheels) and their axle caps
    for wx in (13, 33):
        wm = m_ellipse(W, H, wx + ox, 27.5, 3.8, 3.5) & (yy <= gy)
        shade(cv, wm, WOOD, contour=True, mode="sphere", base=0.5, gain=1.1)
        cv.fill(ellipse_ring(W, H, wx + ox, 27.5, 3.8, 3.5) & (xx + yy > wx + ox + 29), WOOD[1])
        cv.fill(m_ellipse(W, H, wx + ox, 27.5, 1.1, 1.1), IRON[4])
        cv.put(wx + ox - 1, 26, IRON[6])
    # the barrel: cascabel knob, breech, rings, chase and a flared muzzle, tilted up a little
    R = _rot(28.0 + ox, 17.0, math.radians(-5))
    prof = [(-22, 1.2), (-20.5, 1.6), (-19.5, 3.4), (-17, 4.0), (-9, 3.7), (0, 3.3), (9, 2.9), (12.5, 2.8),
            (13.5, 3.4), (14.5, 3.4)]
    barrel = m_poly(W, H, [R(u, -h) for u, h in prof] + [R(u, h) for u, h in reversed(prof)])
    shade(cv, barrel, BRONZE, contour=True, mode="cylh", base=0.6, gain=1.3)
    for (u, wdt) in ((-17, 4.3), (-9, 4.0), (-3, 3.8), (8, 3.3), (13.5, 3.6)):
        ring = m_poly(W, H, [R(u - 0.6, -wdt), R(u + 0.6, -wdt), R(u + 0.6, wdt), R(u - 0.6, wdt)]) & dilate(barrel)
        cv.fill(ring, BRONZE[2])
        cv.fill(ring & (yy < R(u, 0)[1] - 1), GOLD[5])
    kn = R(-22.5, 0)
    cv.fill(m_ellipse(W, H, kn[0], kn[1], 1.6, 1.6), BRONZE[4])
    mz = R(14.8, 0)
    cv.fill(m_ellipse(W, H, mz[0], mz[1], 1.0, 2.4), INK)
    # lifting handles (a pair of small loops on top) and the trunnion
    for u in (-6, -1):
        p0, p1 = R(u, -3.5), R(u + 3, -3.5)
        cv.fill(m_curve(W, H, [p0, ((p0[0] + p1[0]) / 2, p0[1] - 2.5), p1]), BRONZE[4])
    tr = m_ellipse(W, H, 30.5 + ox, 19, 1.8, 1.8)
    shade(cv, tr, IRON, mode="sphere", base=0.6, gain=1.0)
    # the fuse at the touch hole
    th_ = R(-16, -4.2)
    cv.fill(m_curve(W, H, [th_, (th_[0] - 2, th_[1] - 3), (th_[0] - 4, th_[1] - 2)]), ROPE[2])
    outline(cv)
    if fire:
        k = f % 4
        g = rng("cannon_smoke")
        puffs = [(g.uniform(0, 1), g.uniform(-1, 1)) for _ in range(6)]
        for i, (o, dy) in enumerate(puffs):
            if k == 0 and i > 2:
                continue
            t = min(1.0, (k + o * 0.8) / 3.2)
            px = mz[0] + 3 + t * 3 + (i - 2.5) * 1.6 * t
            py = mz[1] - t * 9 + dy * 2.0 * t
            rr = 1.8 + t * 2.4
            aa = 0.75 * (1.0 - t) ** 0.7 if k else 0.6
            pm = m_ellipse(W, H, px, py, rr, rr * 0.85)
            cv.fill(pm, SMOKE[3 if i % 2 else 2], aa)
            cv.fill(pm & shift(pm, -1, -1) & ~shift(pm, 1, 1), SMOKE[4], aa)
        if k == 0:
            fl = m_poly(W, H, [(mz[0] + 1, mz[1] - 3), (mz[0] + 6, mz[1] - 6), (mz[0] + 5, mz[1] - 2),
                               (mz[0] + 10.5, mz[1]), (mz[0] + 5, mz[1] + 2), (mz[0] + 6, mz[1] + 5),
                               (mz[0] + 1, mz[1] + 3)])
            cv.fill(fl, EMBER[3])
            cv.fill(fl & m_ellipse(W, H, mz[0] + 3, mz[1], 3.5, 2.5), EMBER[5])
            cv.fill(m_ellipse(W, H, mz[0] + 2, mz[1], 1.8, 1.6), WHITE_HOT)
            glow(cv, mz[0] + 3, mz[1], 8, 8, EMBER[4], steps=((1.0, 0.18), (0.55, 0.3)))
            sparkle(cv, th_[0] - 4, th_[1] - 2, 1, WHITE_HOT, EMBER[4], 1.0)
        elif k == 1:
            cv.fill(m_ellipse(W, H, mz[0] + 3, mz[1], 3, 2), EMBER[4], 0.9)
            cv.fill(m_ellipse(W, H, mz[0] + 2, mz[1], 1.2, 1.0), EMBER[5])
            glow(cv, mz[0] + 3, mz[1], 8, 6, EMBER[3], steps=((1.0, 0.14),))
    else:
        cv.put(th_[0] - 4, th_[1] - 2, EMBER[4])
        wisp(cv, th_[0] - 4, th_[1] - 3, 0, 4, height=6, seed=2, c=SMOKE[3], alpha=0.45, amp=0.8)
    return cv


@prop("powder_keg", 22, 26, ground=3)
def powder_keg(state, f):
    """A banded keg of Blackmast gunpowder: dark staves, three iron hoops, a red powder mark painted
    on the belly and a stoppered fuse hole in the lid, a little black powder spilled at its foot."""
    W, H = 22, 26
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 23
    cx = 11
    ground_shadow(cv, cx, gy, 9, 1.3)
    body = lathe(W, H, cx - 0.5, [(5, 7.0), (9, 8.3), (14, 8.8), (19, 8.3), (gy, 7.0)])
    shade(cv, body, WOOD, contour=True, mode="cyl", base=0.48, gain=1.3, ao=0.1)
    for sx in (5, 8, 12, 15):
        cv.fill(body & (xx == sx) & (yy > 6), WOOD[2] if sx > 10 else WOOD[3])
    for hy in (7, 12, 20):
        hoop = body & (yy >= hy) & (yy <= hy + 1)
        cv.fill(hoop, IRON[2])
        cv.fill(hoop & (yy == hy) & (xx < cx + 3), IRON[4])
    # the red powder mark: a flame in a diamond
    d = m_poly(W, H, [(cx - 0.5, 12.5), (cx + 3.5, 16.5), (cx - 0.5, 20.5), (cx - 4.5, 16.5)])
    cv.fill(border(d), CLOTH_RED[4])
    cv.fill(erode(d), CLOTH_RED[2])
    fm = m_poly(W, H, [(cx - 2, 18.5), (cx + 1, 18.5), (cx + 0.5, 16), (cx - 0.5, 14.5), (cx - 1.5, 16.5)])
    cv.fill(fm, WARNING_RED)
    cv.put(cx - 1, 17, hexc("#ff9c7a"))
    # the lid seen from a little above, the stopper and a twist of fuse
    lid = m_ellipse(W, H, cx - 0.5, 5, 7, 1.8)
    shade(cv, lid, WOOD, R=1, base=0.6, gain=0.9)
    cv.fill(ellipse_ring(W, H, cx - 0.5, 5, 7, 1.8) & (yy >= 5), WOOD[1])
    stop = m_rect(W, H, cx + 1, 2, cx + 3, 4)
    shade(cv, stop, WOOD, R=1, base=0.65, gain=0.8)
    cv.fill(m_curve(W, H, [(cx + 2, 2), (cx + 3, 1), (cx + 5, 1.5)]), ROPE[2])
    # spilled powder
    g = rng("keg_powder")
    for _ in range(9):
        px, py = int(g.integers(2, 20)), gy + int(g.integers(0, 2))
        if not body[min(H - 1, py), px]:
            cv.put(px, py, CINDER[1])
    outline(cv)
    return cv


# ------------------------------------------------------------------ Wyrmnest Isles: eggs, nests, star crystal
PEARL = ramp("#4a4560", "#6f6a86", "#9993ab", "#bfbacb", "#dfdbe6", "#f6f3fa")
IRIDESCENCE = (hexc("#f3c2dc"), hexc("#b4ece8"), hexc("#f6e2a6"))
STAR_CRYSTAL = ramp("#4a3312", "#7c5a22", "#b08a3a", "#d9b95e", "#f2dc94", "#fff5d2", "#fffdf2")
TWIG = ramp("#1f1710", "#35271a", "#4f3b26", "#6c5335", "#8c7049", "#ad9064")


def _egg_mask(W, H, cx, cy, rx, ry):
    """An egg: an ellipse that narrows toward the top."""
    xx, yy = grid(W, H)
    t = np.clip((cy - yy) / ry, -1, 1)
    hw = rx * np.sqrt(np.clip(1 - t * t, 0, 1)) * (1 - 0.18 * t)
    return (np.abs(xx - cx) <= hw) & (np.abs(yy - cy) <= ry)


@prop("wyrm_egg", 26, 32, states=(("idle", 4, 4),), ground=3)
def wyrm_egg(state, f):
    """A star-wyrm's egg: a big pearly egg whose shell shimmers pink, teal and gold as the light
    slides over it, with a faint star glowing inside. It rests on a scrape of pebbles and down."""
    W, H = 26, 32
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 29
    cx, cy, rx, ry = 12.5, 16.5, 9.2, 12.5
    ground_shadow(cv, cx, gy, 11, 1.5)
    egg = _egg_mask(W, H, cx, cy, rx, ry) & (yy <= gy - 1)
    shade(cv, egg, PEARL, contour=False, mode="sphere", base=0.62, gain=1.25)
    # the star inside, seen as a warm glow through the lower shell
    pulse = (0.0, 0.3, 0.6, 0.3)[f % 4]
    inner = m_ellipse(W, H, cx + 0.5, cy + 3, 4.5, 5) & egg
    cv.fill(inner, STARFIRE[4], 0.25 + pulse * 0.2)
    cv.fill(m_ellipse(W, H, cx + 0.5, cy + 3, 2.2, 2.4) & egg, STARFIRE[5], 0.4 + pulse * 0.3)
    sx_, sy_ = int(cx + 0.5), int(cy + 3)
    cross = (m_rect(W, H, sx_ - 2, sy_, sx_ + 2, sy_) | m_rect(W, H, sx_, sy_ - 2, sx_, sy_ + 2)) & egg
    cv.fill(cross, WHITE_HOT, 0.45 + pulse * 0.4)
    # iridescent bands that slide across the shell
    u = (xx - cx) / rx * 0.7 + (yy - cy) / ry * 0.5 + (f % 4) * 0.28
    for k, c in enumerate(IRIDESCENCE):
        band = egg & (np.abs(np.mod(u + k * 0.55, 1.65) - 0.4) < 0.11)
        cv.fill(band, c, 0.35)
    # speckles and the lit crown
    g = rng("egg_speck")
    for _ in range(8):
        px, py = int(g.integers(5, 21)), int(g.integers(7, 27))
        if erode(egg)[py, px]:
            cv.put(px, py, PEARL[2])
    hl = m_ellipse(W, H, cx - 3.5 + (f % 4) * 0.4, cy - 6, 1.6, 2.6) & egg
    cv.fill(hl, PEARL[5])
    cv.put(int(cx - 4), int(cy - 7), WHITE_HOT)
    # pebbles and a little down around the base
    for k, (px, rr) in enumerate(((4, 2.2), (21, 2.6), (17, 1.6))):
        rock(cv, px, gy, rr, rr * 0.8, ("egg_peb", k), pal=STONE, R=1, facets=0)
    for (dx, dy) in ((7, gy), (9, gy - 1), (16, gy), (18, gy - 1)):
        cv.put(dx, dy, CLOTH_WHITE[4])
    outline(cv)
    glow(cv, cx + 0.5, cy + 3, 9, 10, STAR_HALO, steps=((1.0, 0.04 + pulse * 0.05),))
    if f % 4 == 2:
        sparkle(cv, int(cx - 4), int(cy - 7), 1, WHITE_HOT, IRIDESCENCE[1], 0.9)
    return cv


@prop("wyrm_nest", 96, 34, ground=3)
def wyrm_nest(state, f):
    """A star-wyrm's nest on the Nest Cliffs: a wide round bowl woven of driftwood twigs and old
    bones, a rib and a thighbone worked into the rim, star crystals grown out of it, and pieces
    of pearly shell from an earlier hatching lying in the hollow."""
    W, H = 96, 34
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 31
    cx = 48
    ground_shadow(cv, cx, gy, 46, 2.0)
    nz = vnoise(W, H, 3, seed_of("nest"), 2)
    # the far rim and the hollow
    far = m_ellipse(W, H, cx, 13, 41, 5.5) & (yy <= 14)
    shade(cv, far, TWIG, contour=True, R=1, base=0.5, gain=1.0, noise=nz, namp=0.3)
    hollow = m_ellipse(W, H, cx, 15, 37, 4.2)
    _idx_fill(cv, hollow, TWIG, np.clip(0.3 + (yy - 11) * 0.35, 0, 2))
    # shell pieces and a crystal in the hollow
    for (sx, sy, sr) in ((34, 15, 3.0), (58, 16, 2.4), (44, 17, 1.8)):
        sh = m_ellipse(W, H, sx, sy, sr, sr * 0.7) & (yy <= sy + 0.5)
        shade(cv, sh, PEARL, mode="sphere", base=0.6, gain=1.1)
        cv.fill(top_edge(sh) & (xx % 2 == 0), PEARL[2])
    _glass_shard(cv, 66, 17, 5, 3, 1, see=0.0, pal=STAR_CRYSTAL)
    # the near body of the bowl
    body = m_ellipse(W, H, cx, 18, 46, 13) & (yy >= 16) & (yy <= gy)
    shade(cv, body, TWIG, contour=True, R=2, base=0.5, gain=1.2, noise=nz, namp=0.3, ao=0.25)
    # woven twigs: short curved strokes laid round the bowl, alternating light and dark
    g = rng("nest_twigs")
    for _ in range(95):
        x0 = float(g.uniform(4, 92))
        y0 = float(g.uniform(16, gy - 1))
        if not body[int(y0), int(x0)]:
            continue
        ln = float(g.uniform(4, 9))
        sl = float(g.uniform(-0.35, 0.35)) + (x0 - cx) / 90.0
        pts = [(x0, y0), (x0 + ln * 0.5, y0 + sl * ln * 0.5 - 0.6), (x0 + ln, y0 + sl * ln)]
        tw = m_curve(W, H, pts) & body
        lit = g.random() < 0.5
        cv.fill(tw, TWIG[4] if lit else TWIG[1])
        if lit:
            cv.fill(shift(tw, 0, 1) & body & ~tw, TWIG[2])
    # ragged twig ends poking out past the rim
    for _ in range(16):
        a = float(g.uniform(0, math.pi))
        px = cx + math.cos(a) * 43 * (1 if g.random() < 0.5 else -1)
        py = float(g.uniform(12, 24))
        dx = 3 if px > cx else -3
        cv.fill(m_line(W, H, [(px, py), (px + dx, py - g.uniform(1, 3))]), TWIG[3])
    # bones woven into the front: a rib arc and a long thighbone with knobbed ends
    rib = tube(W, H, [(18, 26), (26, 21), (36, 20), (44, 22)], 1.0)
    shade(cv, rib, BONE, contour=True, R=1, base=0.62, gain=1.0)
    femur = tube(W, H, [(56, 26), (74, 22)], 1.2)
    femur |= m_ellipse(W, H, 55, 26.5, 2.2, 2.0) | m_ellipse(W, H, 75, 21.5, 2.3, 2.0)
    shade(cv, femur, BONE, contour=True, R=1, base=0.6, gain=1.1)
    # star crystals grown from the rim
    for (x, by, h, w, lean) in ((13, 20, 9, 3, -2), (16, 21, 5, 2, 1), (80, 19, 11, 4, 2), (84, 21, 6, 2, 3),
                                (47, 12, 6, 3, 0)):
        _glass_shard(cv, x, by, h, w, lean, see=0.0, pal=STAR_CRYSTAL)
    outline(cv)
    for (gx, gy2) in ((80, 9), (13, 12)):
        glow(cv, gx, gy2 + 4, 6, 6, STAR_CRYSTAL[5], steps=((1.0, 0.08),))
    return cv


@prop("star_crystal", 30, 40, states=(("idle", 4, 4),), ground=3)
def star_crystal(state, f):
    """A cluster of pale gold star crystals grown out of a rock, the long prisms lit on their left
    facets; a glint runs from tip to tip."""
    W, H = 30, 40
    cv = Canvas(W, H)
    gy = 37
    ground_shadow(cv, 15, gy, 13, 1.5)
    tips = []
    for (x, by, h, w, lean) in ((10, gy - 4, 18, 4, -4), (19, gy - 4, 22, 5, 3), (15, gy - 5, 30, 6, 0)):
        _glass_shard(cv, x, by, h, w, lean, see=0.0, pal=STAR_CRYSTAL)
        tips.append((int(round(x + lean)), by - h + 1))
    rock(cv, 15, gy, 11, 5, "star_crystal_rock", pal=STONE, R=2, base=0.5, facets=2)
    for (x, by, h, w, lean) in ((6, gy - 1, 9, 3, -3), (23, gy - 1, 11, 4, 3), (13, gy - 2, 7, 3, -1),
                                (18, gy - 1, 5, 3, 1)):
        _glass_shard(cv, x, by, h, w, lean, see=0.0, pal=STAR_CRYSTAL)
        tips.append((int(round(x + lean)), by - h + 1))
    outline(cv)
    a = (0.07, 0.09, 0.11, 0.09)[f % 4]
    glow(cv, 15, 20, 13, 17, STAR_CRYSTAL[5], steps=((1.0, a * 0.6), (0.6, a)))
    order = (2, 1, 4, 0)
    tx, ty = tips[order[f % 4]]
    sparkle(cv, tx, ty, 2 if f % 2 == 0 else 1, WHITE_HOT, STAR_CRYSTAL[5], 0.95)
    return cv


# ------------------------------------------------------------------ Star Warden Citadel
WARDEN_STONE = ramp("#1c2226", "#2e373b", "#465155", "#606c6d", "#7f8a86", "#a4ada4", "#c9cfc2")


@prop("warden_statue", 44, 110, ground=3)
def warden_statue(state, f):
    """A stern stone Star Warden of the Citadel Gate: helmed and cloaked, a star on the breastplate,
    one hand resting on a tall staff crowned with a star, the other holding out a real bronze
    lantern in which a small star still burns."""
    W, H = 44, 110
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 107
    P = WARDEN_STONE
    nz = vnoise(W, H, 3, seed_of("warden"), 2)
    ground_shadow(cv, 22, gy, 20, 1.8)

    def part(m, base=0.58, gain=1.3, R=2, mode="bevel", contour=True):
        shade(cv, m, P, contour=contour, mode=mode, R=R, strength=2.2, base=base, gain=gain, noise=nz, namp=0.2)
        return m

    # plinth: footing, die with a carved star, cornice
    part(m_rect(W, H, 4, 101, 39, gy), base=0.5, gain=1.0, R=1)
    cv.fill(m_rect(W, H, 4, 101, 39, 101), P[5])
    die = part(m_rect(W, H, 7, 92, 36, 100), base=0.52, gain=1.0, R=1)
    star = (m_rect(W, H, 18, 96, 25, 96) | m_rect(W, H, 21, 93, 22, 99) | m_rect(W, H, 20, 95, 23, 97))
    cv.fill(dilate(star) & die & ~star, P[2])
    cv.fill(star, P[4])
    cv.fill(m_rect(W, H, 20, 95, 21, 96), P[5])
    part(m_rect(W, H, 5, 89, 38, 91), base=0.6, gain=1.0, R=1)
    cv.fill(m_rect(W, H, 5, 89, 38, 89), P[6])
    # the cloak behind, falling to the plinth
    cloak = m_poly(W, H, [(13, 27), (31, 27), (36, 60), (38, 88), (6, 88), (9, 60)])
    part(cloak, base=0.4, gain=1.1)
    for fx0 in (11, 34):
        cv.fill(m_line(W, H, [(fx0, 62), (fx0 + (1 if fx0 < 20 else -1), 87)]) & erode(cloak), P[1])
    # the staff on the viewer's right, planted on the plinth
    staff = m_rect(W, H, 35, 16, 36, 88)
    part(staff, base=0.55, R=1, mode="cyl")
    sf = (m_rect(W, H, 33, 12, 38, 12) | m_rect(W, H, 35, 9, 36, 15) | m_rect(W, H, 34, 11, 37, 13))
    part(sf, base=0.65, R=1)
    cv.put(35, 11, P[6])
    # the robe and armour
    robe = m_poly(W, H, [(14, 30), (30, 30), (32, 52), (34, 88), (10, 88), (12, 52)])
    part(robe, mode="cyl", base=0.6, gain=1.4)
    for (x0, x1) in ((16, 14), (20, 19), (27, 29), (31, 32)):
        fold = m_line(W, H, [(x0, 56), (x1, 87)]) & erode(robe)
        cv.fill(fold, P[2] if x0 < 22 else P[1])
        if x0 < 22:
            cv.fill(shift(fold, -1, 0) & erode(robe) & ~fold, P[5])
    plate = m_poly(W, H, [(14, 30), (30, 30), (29, 46), (22, 49), (15, 46)])
    part(plate, base=0.62, gain=1.3, R=2)
    pstar = (m_rect(W, H, 19, 37, 25, 37) | m_rect(W, H, 22, 34, 22, 40) | m_rect(W, H, 21, 36, 23, 38))
    cv.fill(pstar, P[5])
    cv.put(21, 36, P[6])
    cv.fill(shift(pstar, 1, 1) & plate & ~pstar, P[2])
    belt = m_rect(W, H, 12, 49, 32, 52)
    part(belt, mode="cyl", base=0.55, R=1)
    cv.fill(m_rect(W, H, 12, 49, 28, 49), P[5])
    tass = m_poly(W, H, [(15, 53), (29, 53), (28, 66), (22, 68), (16, 66)])
    part(tass, mode="cyl", base=0.6, R=1, gain=1.2)
    for ty in (57, 61):
        cv.fill(m_rect(W, H, 16, ty, 28, ty) & erode(tass), P[2])
    for (px, s) in ((13, -1), (31, 1)):
        pau = m_ellipse(W, H, px, 31, 5, 3.4) & (yy <= 33)
        part(pau, base=0.62 if s < 0 else 0.45, R=1)
        cv.fill(bottom_edge(pau), P[1])
    # the left hand on the staff
    arm_r = tube(W, H, [(31, 32), (34, 40), (35, 47)], 2.0, 1.7)
    part(arm_r, base=0.45, R=1)
    hand_r = m_ellipse(W, H, 35.5, 48, 2.0, 2.2)
    part(hand_r, base=0.55, R=1, mode="sphere")
    # the right arm held out, the hand gripping the lantern's ring
    arm_l = tube(W, H, [(13, 32), (10, 40), (7, 41)], 2.2, 1.8)
    part(arm_l, base=0.65, R=1)
    hand_l = m_ellipse(W, H, 6, 41, 2.1, 2.0)
    part(hand_l, base=0.7, R=1, mode="sphere")
    # the head: a crested helm over a stern face with a short beard
    face = m_ellipse(W, H, 22, 20, 4.5, 5.5)
    part(face, base=0.66, gain=1.2, R=2)
    cv.fill(m_rect(W, H, 19, 19, 20, 19) | m_rect(W, H, 24, 19, 25, 19), P[1])
    cv.fill(m_rect(W, H, 18, 18, 21, 18) | m_rect(W, H, 23, 18, 26, 18), P[2])
    cv.fill(m_rect(W, H, 22, 19, 22, 21), P[5])
    beard = m_poly(W, H, [(18.5, 22), (25.5, 22), (25, 25), (22, 27.5), (19, 25)])
    part(beard, base=0.5, R=1, mode="cyl")
    cv.fill(m_rect(W, H, 20, 23, 24, 23), P[1])
    helm = m_poly(W, H, [(16, 19), (16.5, 13), (19, 10), (25, 10), (27.5, 13), (28, 19), (26, 17), (26, 15), (18, 15),
                         (18, 17)])
    part(helm, base=0.6, R=1, gain=1.3)
    cv.fill(m_rect(W, H, 17, 15, 27, 15), P[2])
    crest = m_poly(W, H, [(20.5, 10), (22, 3), (23.5, 10)])
    part(crest, base=0.65, R=1)
    for side in (-1, 1):
        cv.fill(m_poly(W, H, [(22 + side * 5, 12), (22 + side * 8, 8), (22 + side * 6, 13)]), P[4 if side < 0 else 2])
    statue = cv.solid.copy() & (yy < 89)
    cv.fill(statue & (nz > 0.72) & erode(statue) & (yy > 60), P[2])
    lichen = statue & (vnoise(W, H, 4, seed_of("warden_lichen"), 2) > 0.7) & (yy > 70)
    cv.fill(lichen, MOSS[2])
    cv.fill(lichen & shift(~lichen, 0, 1), MOSS[3])
    # the bronze lantern hanging from the hand (real metal, a small star inside)
    lx, ly = 6, 49
    cv.fill(m_rect(W, H, lx, 43, lx, 44), BRONZE[2])
    lcap = m_poly(W, H, [(lx - 3.5, 46.5), (lx, 44.5), (lx + 3.5, 46.5)])
    _bronze(cv, lcap, base=0.6, gain=1.0)
    _star_body(cv, lx, ly + 1, 2.4, 1, True, seed="warden_lamp")
    for bx in (lx - 3, lx, lx + 3):
        cv.fill(m_rect(W, H, bx, 47, bx, 53), BRONZE[3] if bx != lx else BRONZE[2])
    _bronze(cv, m_rect(W, H, lx - 3, 54, lx + 3, 55), base=0.5, gain=1.0)
    outline(cv)
    glow(cv, lx, ly + 1, 9, 9, STAR_HALO, steps=((1.0, 0.08), (0.55, 0.14)))
    cv.light(dilate(dilate(arm_l | hand_l)) & cv.solid & (xx < 14), STARFIRE[4], 0.12)
    return cv


@prop("observatory_scope", 70, 80, ground=3)
def observatory_scope(state, f):
    """The Wardens' great star-telescope in the Observatory: a long bronze tube with a dew hood and a
    small finder, swung in a fork on a column over a round stone pedestal, a graduated arc at its
    side and the objective lens catching the starlight."""
    W, H = 70, 80
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 77
    nz = vnoise(W, H, 3, seed_of("scope"), 2)
    ground_shadow(cv, 32, gy, 26, 1.8)
    # round stone pedestal on two steps
    for (x0, x1, y0, y1) in ((8, 57, 71, gy), (14, 51, 66, 70)):
        blk = m_rect(W, H, x0, y0, x1, y1)
        shade(cv, blk, WARDEN_STONE, contour=True, R=1, base=0.5, gain=1.1, noise=nz, namp=0.12)
        cv.fill(m_rect(W, H, x0, y0, x1, y0), WARDEN_STONE[5])
        cv.fill(m_rect(W, H, x0, y0, x0, y1), WARDEN_STONE[4])
    drum = m_rect(W, H, 20, 52, 45, 65)
    shade(cv, drum, WARDEN_STONE, contour=True, mode="cyl", base=0.55, gain=1.2, noise=nz, namp=0.12)
    cv.fill(m_rect(W, H, 20, 52, 45, 53), WARDEN_STONE[5])
    for k in range(6):
        sx = 22 + k * 4
        cv.fill(m_rect(W, H, sx, 56, sx + 1, 61), WARDEN_STONE[2] if sx > 32 else WARDEN_STONE[3])
    # bronze column and the fork
    col = m_rect(W, H, 30, 36, 35, 51)
    _bronze(cv, col, mode="cyl", base=0.55, gain=1.2, vg=0.2, seed="scope_col")
    cv.fill(m_rect(W, H, 28, 49, 37, 51), BRONZE[3])
    cv.fill(m_rect(W, H, 28, 49, 36, 49), GOLD[4])
    fork = m_poly(W, H, [(26, 37), (39, 37), (41, 27), (38, 27), (36, 34), (29, 34), (27, 27), (24, 27)])
    _bronze(cv, fork, base=0.55, gain=1.2)
    # the graduated arc beside the fork
    arc = ellipse_ring(W, H, 32.5, 30, 14, 14) & ~ellipse_ring(W, H, 32.5, 30, 12, 12) & (yy >= 30) & (xx < 32)
    arc |= ellipse_ring(W, H, 32.5, 30, 13, 13) & (yy >= 30) & (xx < 32)
    _bronze(cv, arc, base=0.6, gain=1.0)
    for k in range(7):
        a = math.pi / 2 + k * math.pi / 12
        cv.put(int(round(32.5 + math.cos(a) * 13)), int(round(30 + math.sin(a) * 13)), GOLD[5] if k % 3 == 0 else BRONZE[1])
    # the tube, the dew hood and the eyepiece; a counterweight rod behind
    R = _rot(33.0, 30.0, math.radians(-33))
    rod = tube(W, H, [R(-10, 0), R(-24, 2)], 0.8)
    cv.fill(rod, BRONZE[2])
    cw = m_ellipse(W, H, *R(-24, 2.5), 2.6, 2.6)
    _bronze(cv, cw, mode="sphere", base=0.5, gain=1.1)
    prof = [(-20, 2.2), (-8, 3.0), (18, 3.4), (22, 3.4), (22.5, 4.3), (35, 4.3)]
    tube_m = m_poly(W, H, [R(u, -h) for u, h in prof] + [R(u, h) for u, h in reversed(prof)])
    shade(cv, tube_m, BRONZE, contour=True, mode="bevel", R=2, base=0.58, gain=1.3)
    for (u, hw_) in ((-12, 2.9), (-2, 3.2), (10, 3.3), (22.3, 4.4)):
        ring = m_poly(W, H, [R(u - 0.6, -hw_), R(u + 0.6, -hw_), R(u + 0.6, hw_), R(u - 0.6, hw_)]) & dilate(tube_m)
        cv.fill(ring, BRONZE[2])
        cv.fill(ring & ~shift(tube_m, 1, 1), GOLD[5])
    ep = tube(W, H, [R(-20, 0), R(-25, 1)], 1.3)
    _bronze(cv, ep, base=0.5, gain=1.0)
    finder = tube(W, H, [R(-4, -5.5), R(12, -5.5)], 1.2)
    _bronze(cv, finder, base=0.65, gain=1.0)
    for u in (-2, 9):
        cv.fill(m_line(W, H, [R(u, -3.2), R(u, -4.5)]), BRONZE[2])
    # the objective: a pale lens face at the mouth of the hood
    lens = m_ellipse(W, H, *R(35.3, 0), 1.4, 3.6)
    cv.fill(lens, STARGLASS_LENS[2])
    cv.fill(lens & (xx + yy < R(35.3, 0)[0] + R(35.3, 0)[1]), STARGLASS_LENS[4])
    tr = m_ellipse(W, H, 32.5, 30, 2.2, 2.2)
    shade(cv, tr, GOLD, mode="sphere", base=0.6, gain=1.0)
    outline(cv, skip=m_ellipse(W, H, 32.5, 30, 12, 12) & ~cv.solid)
    lc = R(35.5, -1.5)
    sparkle(cv, int(round(lc[0])), int(round(lc[1])), 2, WHITE_HOT, STARGLASS_LENS[4], 0.9)
    return cv


STARGLASS_LENS = ramp("#1c2c4a", "#3a5f8a", "#7fb0d8", "#bfe2f6", "#effbff")


# ------------------------------------------------------------------ Orbit Ruins: gravity switch
@prop("gravity_switch", 26, 44, states=(("up", 1, 0), ("down", 1, 0), ("active", 4, 6)), ground=3)
def gravity_switch(state, f):
    """A gravity switch of the Inverted Hall: a squat bronze pillar set with jade, a jade orb on top
    and a bronze lever in a slot on its face. Up, the jade sleeps; thrown down, the arrow runes
    and the orb shine; while the room's gravity is turning, the orb pulses and motes drift up."""
    W, H = 26, 44
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 41
    down = state in ("down", "active")
    on = state == "active"
    pulse = (0.0, 0.5, 1.0, 0.5)[f % 4] if on else 0.0
    ground_shadow(cv, 12, gy, 11, 1.4)
    foot = m_rect(W, H, 2, 36, 22, gy)
    shade(cv, foot, WARDEN_STONE, contour=True, R=1, base=0.5, gain=1.1)
    cv.fill(m_rect(W, H, 2, 36, 22, 36), WARDEN_STONE[5])
    body = m_poly(W, H, [(4, 35), (5, 14), (19, 14), (20, 35)])
    _bronze(cv, body, base=0.55, gain=1.3, R=2, vg=0.15, seed="gswitch")
    for by in (14, 33):
        band = m_rect(W, H, 3, by, 21, by + 2)
        _bronze(cv, band, mode="cyl", base=0.6, gain=1.1)
        cv.fill(m_rect(W, H, 3, by, 20, by), GOLD[4])
    # jade panels with arrow runes (up arrow above the slot pivot, down arrow below)
    lit_up = not down
    for (y0, up_arrow) in ((17, True), (27, False)):
        pan = m_rect(W, H, 6, y0, 9, y0 + 4)
        on_this = (down and not up_arrow) or on
        cv.fill(pan, JADE_R[1] if not on_this else JADE_R[2])
        cv.fill(left_edge(pan) | top_edge(pan), JADE_R[0])
        ax = 7.5
        if up_arrow:
            ar = m_poly(W, H, [(ax - 1.5, y0 + 2.5), (ax, y0 + 0.5), (ax + 1.5, y0 + 2.5)]) | m_rect(W, H, 7, y0 + 2, 8, y0 + 3)
        else:
            ar = m_poly(W, H, [(ax - 1.5, y0 + 1.5), (ax, y0 + 3.5), (ax + 1.5, y0 + 1.5)]) | m_rect(W, H, 7, y0 + 1, 8, y0 + 2)
        cv.fill(ar & pan, (JADE_R[6] if on else JADE_R[5]) if on_this else (JADE_R[3] if lit_up and up_arrow else JADE_R[2]))
    # the slot and the lever
    slot = m_rect(W, H, 12, 17, 13, 31)
    cv.fill(slot, BRONZE[0])
    cv.fill(right_edge(slot), BRONZE[1])
    piv = (12.5, 24.0)
    knob_c = (20.0, 33.0) if down else (20.0, 15.0)
    arm = tube(W, H, [piv, knob_c], 1.3)
    _bronze(cv, arm, base=0.7, gain=1.0)
    cv.fill(arm & ~shift(arm, 1, 1), GOLD[5])
    knob = m_ellipse(W, H, knob_c[0] + 0.5, knob_c[1], 2.7, 2.7)
    shade(cv, knob, JADE_R, contour=True, mode="sphere", base=0.55 + (0.15 if down else 0.0) + pulse * 0.1, gain=1.2)
    cv.fill(m_ellipse(W, H, piv[0], piv[1], 1.5, 1.5), GOLD[4])
    cv.put(12, 23, GOLD[6])
    # the capstone and jade orb
    capm = m_poly(W, H, [(3, 13), (6, 10), (18, 10), (21, 13)])
    _bronze(cv, capm, base=0.6, gain=1.1)
    orb = m_ellipse(W, H, 11.5, 6, 4.2, 4.2)
    shade(cv, orb, JADE_R, contour=True, mode="sphere", base=(0.42 if not down else 0.62) + pulse * 0.12, gain=1.3)
    cv.put(10, 4, JADE_R[6] if down else JADE_R[5])
    outline(cv)
    if down:
        a = 0.06 if not on else (0.08, 0.12, 0.16, 0.12)[f % 4]
        glow(cv, 11.5, 6, 7 + pulse * 2, 7 + pulse * 2, BRIGHT_JADE, steps=((1.0, a * 0.6), (0.6, a)))
        glow(cv, 7.5, 29, 4, 4, BRIGHT_JADE, steps=((1.0, a * 0.8),))
    if on:
        motes(cv, 2, 0, 23, 34, f, 4, "gswitch_m", count=6, pal=(BRIGHT_JADE, JADE_R[6]))
    return cv


# ------------------------------------------------------------------ Orbit Ruins: orbit stone
@prop("orbit_stone", 40, 36, states=(("idle", 4, 4),), ground=3)
def orbit_stone(state, f):
    """A chunk of ruin masonry that floats over a faint rune ring in the Orbit Garden: dressed faces
    with a carved band on top, a broken underside, and three pebbles circling it. It bobs slowly."""
    W, H = 40, 36
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 33
    bob = (0, -1, -2, -1)[f % 4]
    # the ring on the ground (translucent, never outlined) and the stone's small shadow
    ring = ellipse_ring(W, H, 19.5, gy - 1, 15, 2.6) | ellipse_ring(W, H, 19.5, gy - 1, 12, 1.8)
    cv.fill(ring, STARLIGHT[4], 0.45)
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.3
        cv.put(int(round(19.5 + math.cos(a) * 13.5)), int(round(gy - 1 + math.sin(a) * 2.2)), STARLIGHT[5], 0.8)
    ground_shadow(cv, 19.5, gy - 1, 7 + bob * 0.5, 1.0, a=0.25)
    # orbiting pebbles: those on the far side go behind the stone
    orbit = []
    for k in range(3):
        a = 2 * math.pi * (k / 3.0 + (f % 4) / 12.0)
        orbit.append((19.5 + math.cos(a) * 15.5, 14 + bob + math.sin(a) * 4, math.sin(a)))
    for (px, py, depth) in orbit:
        if depth < 0:
            rock(cv, px, int(round(py + 1)), 1.6, 1.3, ("orb_peb", int(px)), pal=STONE, R=1, facets=0, contour=False)
    oy = bob
    top = m_poly(W, H, [(8, 8 + oy), (14, 4 + oy), (31, 4 + oy), (33, 7 + oy), (33, 9 + oy), (9, 10 + oy)])
    front = m_poly(W, H, [(8, 9 + oy), (33, 9 + oy), (32, 17 + oy), (29, 20 + oy), (26, 18 + oy), (22, 23 + oy),
                          (18, 19 + oy), (14, 22 + oy), (11, 18 + oy), (8, 16 + oy)])
    side = m_poly(W, H, [(33, 7 + oy), (35, 9 + oy), (34, 16 + oy), (32, 17 + oy), (33, 9 + oy)])
    nz = vnoise(W, H, 3, seed_of("orbit_stone"), 2)
    shade(cv, front, STONE, contour=True, R=1, base=0.5, gain=1.0, noise=nz, namp=0.2)
    shade(cv, side, STONE, contour=True, R=1, base=0.3, gain=0.8)
    shade(cv, top, STONE, contour=True, R=1, base=0.72, gain=0.8, noise=nz, namp=0.15)
    cv.fill(top_edge(top), STONE[6])
    # a carved band across the dressed face and the broken underside
    band = m_rect(W, H, 9, 11 + oy, 32, 13 + oy) & front
    cv.fill(band, STONE[2])
    for bx in range(10, 32, 4):
        cv.fill(m_rect(W, H, bx, 12 + oy, bx + 1, 12 + oy) & band, STARLIGHT[3])
    brk = front & (yy >= 16 + oy)
    cv.fill(brk & (nz > 0.5), STONE[1])
    moss = top & (nz > 0.6)
    cv.fill(moss, MOSS[3])
    cv.fill(moss & shift(~moss, 0, 1), MOSS[4])
    for (px, py, depth) in orbit:
        if depth >= 0:
            rock(cv, px, int(round(py + 1)), 1.7, 1.4, ("orb_peb", int(px)), pal=STONE, R=1, facets=0)
    outline(cv, skip=ring & ~cv.solid)
    glow(cv, 19.5, gy - 1, 16, 4, STARLIGHT[4], steps=((1.0, 0.08), (0.6, 0.1)))
    for k in range(3):
        cv.put(int(19 + (k - 1) * 5), gy - 4 - ((f + k) % 4) * 3 + bob, STARLIGHT[5], 0.6)
    return cv


# ------------------------------------------------------------------ Orbit Ruins: the broken ring
@prop("broken_ring", 120, 90, ground=4)
def broken_ring(state, f):
    """A great stone ring of the Orbit Ruins standing on its edge in a footing of dressed blocks,
    carved round with a band of star-runes; a section broke out of its upper right long ago, one
    piece still hanging in the air beside the gap and the rest lying in the rubble at its foot."""
    W, H = 120, 90
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 86
    cx, cy, ro, ri = 57.5, 44.0, 40.0, 29.0
    nz = vnoise(W, H, 3, seed_of("broken_ring"), 2)
    ground_shadow(cv, 60, gy, 56, 2.0)
    d = np.hypot(xx - cx, yy - cy)
    ang = np.degrees(np.arctan2(yy - cy, xx - cx))
    jag = (nz - 0.5) * 16
    gap = (ang > -62 + jag) & (ang < -18 + jag)
    band = (d <= ro) & (d >= ri) & ~gap & (yy <= 80)
    shade(cv, band, STONE, contour=True, R=3, strength=2.4, base=0.55, gain=1.3, noise=nz, namp=0.18)
    # raised rims and the rune band between them
    for rr, c_hi, c_lo in ((ro - 2.5, STONE[5], STONE[2]), (ri + 2.5, STONE[2], STONE[5])):
        rim = ellipse_ring(W, H, cx, cy, rr, rr) & band & erode(band)
        cv.fill(rim & (xx + yy < cx + cy), c_hi)
        cv.fill(rim & (xx + yy >= cx + cy), c_lo)
    mid = (d > ri + 3.5) & (d < ro - 3.5) & band
    for k in range(28):
        a = 2 * math.pi * k / 28
        gx, gy2 = cx + math.cos(a) * 34.5, cy + math.sin(a) * 34.5
        ta = (-math.sin(a), math.cos(a))
        if k % 3 == 0:
            pts = [(gx - ta[0] * 1.5, gy2 - ta[1] * 1.5), (gx + ta[0] * 1.5, gy2 + ta[1] * 1.5)]
        elif k % 3 == 1:
            pts = [(gx - math.cos(a) * 1.5, gy2 - math.sin(a) * 1.5), (gx + math.cos(a) * 1.5, gy2 + math.sin(a) * 1.5)]
        else:
            pts = [(gx, gy2)]
        gm = m_line(W, H, pts) & mid
        cv.fill(gm, STONE[1])
        cv.fill(shift(gm, 1, 1) & mid & ~gm, STONE[5])
        if k % 5 == 2:
            cv.fill(gm, STARLIGHT[3])
    # broken faces at the gap
    edge = band & dilate(gap) & ~gap
    cv.fill(edge, STONE[4])
    cv.fill(edge & (nz > 0.55), STONE[2])
    cracks = m_line(W, H, [(cx - 30, cy + 20), (cx - 27, cy + 24), (cx - 29, cy + 28)]) & erode(band)
    cv.fill(cracks, STONE[1])
    # the hovering fragment beside the gap
    frag = m_poly(W, H, [(98, 6), (106, 10), (104, 19), (97, 17), (95, 11)])
    shade(cv, frag, STONE, contour=True, R=2, base=0.55, gain=1.2, noise=nz, namp=0.15)
    cv.fill(m_line(W, H, [(99, 10), (103, 13)]) & frag, STARLIGHT[3])
    # footing blocks, lichen and the rubble of the fallen section
    for (x0, x1, y0, y1) in ((20, 95, 80, gy), (28, 87, 74, 79)):
        blk = m_rect(W, H, x0, y0, x1, y1)
        shade(cv, blk, STONE, contour=True, R=1, base=0.5, gain=1.1, noise=nz, namp=0.15)
        cv.fill(m_rect(W, H, x0, y0, x1, y0), STONE[5])
        cv.fill(m_rect(W, H, x0, y0, x0, y1), STONE[4])
        for jx in range(x0 + 10, x1 - 3, 12):
            cv.fill(m_rect(W, H, jx, y0 + 1, jx, y1), STONE[2])
    lich = band & (vnoise(W, H, 4, seed_of("ring_lichen"), 2) > 0.66) & (ang < -90) & (ang > -170)
    cv.fill(lich, MOSS[2])
    cv.fill(lich & shift(~lich, 0, 1), MOSS[4])
    _chunk(cv, [(96, gy), (99, 77), (110, 75), (114, gy)], "ring_c1", pal=STONE, base=0.5)
    _chunk(cv, [(104, gy), (107, 80), (117, 81), (118, gy)], "ring_c2", pal=STONE, base=0.45)
    _chunk(cv, [(6, gy), (8, 81), (16, 80), (18, gy)], "ring_c3", pal=STONE, base=0.55)
    grass_tuft(cv, 22, gy, "ring_g1", h=4, n=3)
    grass_tuft(cv, 93, gy, "ring_g2", h=3, n=2)
    outline(cv, skip=(d < ri - 1) & ~cv.solid)
    glow(cv, 100, 12, 8, 8, STARLIGHT[4], steps=((1.0, 0.06),))
    return cv


# ------------------------------------------------------------------ Ashen Reach: the Ashborn war camp
ASH = ramp("#1b1918", "#2d2927", "#433d3a", "#5d5651", "#7b736c", "#9d958c", "#c1b9ae")
ASH_RED = ramp("#260809", "#4a1110", "#741c15", "#a02a1a", "#c94121", "#e8683a")
CHAR = ramp("#120e0c", "#211a16", "#33271f", "#4a392b", "#63503b", "#7f694f")
HIDE = ramp("#171210", "#2a211c", "#3f3229", "#564537", "#6f5a47", "#8b735b")
PYRE_FIRE = (FIRE[1], FIRE[2], FIRE[3], FIRE[4], FIRE[5])


def _flame_sigil(W, H, cx, cy, s):
    """The Ashborn flame sigil: three tongues rising from a bowl, `s` px per unit."""
    m = m_poly(W, H, [(cx - 2.2 * s, cy + 1.2 * s), (cx - 2.6 * s, cy - 0.6 * s), (cx - 1.4 * s, cy + 0.1 * s),
                      (cx - 1.1 * s, cy - 1.9 * s), (cx - 0.2 * s, cy - 0.7 * s), (cx, cy - 3.2 * s),
                      (cx + 0.2 * s, cy - 0.7 * s), (cx + 1.1 * s, cy - 1.9 * s), (cx + 1.4 * s, cy + 0.1 * s),
                      (cx + 2.6 * s, cy - 0.6 * s), (cx + 2.2 * s, cy + 1.2 * s)])
    bowl = m_ellipse(W, H, cx, cy + 1.3 * s, 2.4 * s, 0.9 * s)
    return m | bowl


@prop("ash_pyre", 60, 60, states=(("idle", 4, 4), ("lit", 4, 8)), ground=3)
def ash_pyre(state, f):
    """An Ashborn pyre in the war camp: split logs stacked crosswise in narrowing tiers inside a ring
    of stones, charred black at the edges. Smouldering, embers pulse in the gaps and smoke curls
    off the top; lit, it roars up in a column of flame that licks out between the logs."""
    W, H = 60, 60
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 57
    cx = 30
    lit = state == "lit"
    ground_shadow(cv, cx, gy, 27, 1.8)
    ember = (0.0, 0.5, 1.0, 0.5)[f % 4]
    # the log tiers: long logs seen side-on alternate with tiers of log ends
    tiers = []
    y = gy - 5
    half = 22.0
    k = 0
    while half > 9 and y > 26:
        tiers.append((y, half, k % 2))
        y -= 4
        half -= 2.3
        k += 1
    gaps = np.zeros((H, W), bool)
    for (ty, hw, kind) in tiers:
        if kind == 0:
            for dz, c0 in ((-0.8, 0.45), (0.8, 0.55)):
                log = m_rect(W, H, cx - hw + dz, ty - 1, cx + hw + dz, ty + 2)
                shade(cv, log, WOOD, contour=True, mode="cylh", base=c0, gain=1.2)
            charm = m_rect(W, H, cx - hw - 1, ty - 1, cx + hw + 1, ty + 2) & ((xx < cx - hw + 3) | (xx > cx + hw - 3))
            cv.fill(charm & cv.solid, CHAR[2])
            cv.fill(m_rect(W, H, cx - hw, ty - 1, cx + hw, ty - 1) & ~charm, WOOD[5])
        else:
            n = 3 if hw > 14 else 2
            for j in range(n):
                ex = cx - hw + 3 + j * (2 * hw - 6) / max(1, n - 1)
                end = m_ellipse(W, H, ex, ty + 0.5, 2.6, 2.3)
                shade(cv, end, STRAW, contour=True, mode="sphere", base=0.55, gain=0.9)
                cv.fill(ellipse_ring(W, H, ex, ty + 0.5, 1.4, 1.2), WOOD[3])
                cv.fill(ellipse_ring(W, H, ex, ty + 0.5, 2.6, 2.3), CHAR[3])
            gm = m_rect(W, H, cx - hw + 5, ty - 1, cx + hw - 5, ty + 2) & ~cv.solid
            cv.fill(gm, CHAR[0])
            gaps |= gm
    # a crown of kindling on the top tier
    g = rng("pyre_kindling")
    top_y = tiers[-1][0] - 2
    for _ in range(9):
        x0 = cx + g.uniform(-9, 9)
        cv.fill(m_line(W, H, [(x0, top_y + 1), (x0 + g.uniform(-3, 3), top_y - g.uniform(2, 5))]),
                CHAR[4] if g.random() < 0.5 else WOOD[3])
    # the stone ring round the foot
    for j, sx in enumerate(range(7, 54, 7)):
        rock(cv, sx + (j % 2), gy, 3.6, 2.8 + (j % 2) * 0.6, ("pyre_ring", j), pal=ASH, R=1, facets=1)
    # ash drifted at the foot
    ashm = m_ellipse(W, H, cx, gy, 20, 1.6) & (yy <= gy) & ~cv.solid
    cv.fill(ashm, ASH[4])
    outline(cv)
    # embers in the gaps (pulsing), or the fire
    if not lit:
        en = vnoise(W, H, 2, seed_of("pyre_emb", f % 2), 1)
        cv.fill(gaps & (en > 0.45), CHAR[1])
        cv.fill(gaps & (en > 0.62 - ember * 0.06), EMBER[1])
        cv.fill(gaps & (en > 0.74 - ember * 0.06), EMBER[3])
        for (ex, ey) in ((cx - 6, top_y + 1), (cx + 3, top_y), (cx - 1, top_y + 1)):
            cv.put(ex, ey, EMBER[4] if (ex + f) % 2 else EMBER[3])
        glow(cv, cx, gy - 12, 18, 14, EMBER[2], steps=((1.0, 0.04 + ember * 0.03),))
        smoke(cv, cx - 2, top_y - 2, f, 4, height=24, seed="pyre_sm", count=3, drift=2.5, size=1.8, alpha=0.6)
        smoke(cv, cx + 4, top_y - 1, (f + 2) % 4, 4, height=18, seed="pyre_sm2", count=2, drift=2, size=1.4, alpha=0.5)
    else:
        cv.fill(gaps, EMBER[4])
        cv.fill(gaps & (vnoise(W, H, 2, seed_of("pyre_lit", f), 1) > 0.5), FIRE[5])
        _flame(cv, cx, top_y + 2, 30, 24, f, "pyre", pal=PYRE_FIRE, tongues=5)
        for (lx, ly, lw, lh) in ((cx - 15, gy - 12, 8, 9), (cx + 14, gy - 16, 7, 8)):
            _flame(cv, lx, ly, lw, lh, (f + 1) % 4, ("pyre_lick", lx), pal=PYRE_FIRE, tongues=2, licks=False)
        glow(cv, cx, top_y - 8, 28, 26, FIRE[3], steps=((1.0, 0.06), (0.7, 0.09), (0.4, 0.12)))
        sparks(cv, cx, top_y - 16, f, 4, "pyre_sp", count=10, spread=14, pal=FIRE)
    return cv


@prop("ashborn_banner", 26, 92, ground=3)
def ashborn_banner(state, f):
    """A tall Ashborn war banner: ash-grey cloth bordered in ember-red with the red flame sigil,
    cut into two swallow-tails at the hem and scorched ragged, on an iron-bound pole with a
    flame-bladed spearhead and a crossbar hung with red tassels."""
    W, H = 26, 92
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 89
    ground_shadow(cv, 13, gy, 9, 1.4)
    # the base: a block of scorched stone with iron spikes
    base = m_rect(W, H, 7, 83, 18, gy)
    shade(cv, base, ASH, contour=True, R=1, base=0.5, gain=1.1)
    cv.fill(m_rect(W, H, 7, 83, 18, 83), ASH[5])
    for sx in (8, 17):
        cv.fill(m_poly(W, H, [(sx - 1, 83), (sx + 1, 83), (sx, 79)]), IRON[3])
    pole = m_rect(W, H, 12, 7, 13, 83)
    shade(cv, pole, CHAR, contour=True, mode="cyl", base=0.6, gain=1.0)
    for by in (20, 60, 76):
        cv.fill(m_rect(W, H, 11, by, 14, by + 1), IRON[3])
        cv.fill(m_rect(W, H, 11, by, 13, by), IRON[5])
    # flame-bladed spearhead
    head = m_poly(W, H, [(11, 7), (10.5, 4.5), (12, 3), (11.5, 1), (13.5, 2.5), (14.5, 4.5), (14, 7)])
    shade(cv, head, IRON, contour=True, R=1, base=0.62, gain=1.2)
    cv.put(12, 3, IRON[6])
    cv.fill(m_rect(W, H, 11, 7, 14, 8), ASH_RED[3])
    # crossbar and tassels
    bar = m_rect(W, H, 2, 9, 23, 10)
    shade(cv, bar, CHAR, contour=True, R=1, base=0.6, gain=1.0)
    for tx in (2, 23):
        cv.fill(m_rect(W, H, tx, 11, tx, 17), ASH_RED[3])
        cv.fill(m_rect(W, H, tx, 18, tx, 19), ASH_RED[4])
        cv.put(tx, 11, GOLD[3])
    # the cloth, swaying a little, with swallow-tails
    pts_l = [(4 + math.sin(y * 0.2) * 0.7, y) for y in range(11, 66)]
    pts_r = [(21 + math.sin(y * 0.2 + 0.7) * 0.7, y) for y in range(65, 10, -1)]
    hem = [(4, 70), (6, 76), (8.5, 69), (12.5, 64), (16.5, 69), (19, 76), (21, 70)]
    ban = m_poly(W, H, pts_l + hem + pts_r)
    shade(cv, ban, ASH, contour=True, mode="cyl", base=0.58, gain=0.9, bias=np.sin(yy * 0.2) * 0.1)
    edge = ban & ((xx <= 5) | (xx >= 20)) & ~bottom_edge(ban)
    cv.fill(edge, ASH_RED[3])
    cv.fill(edge & (xx <= 5) & left_edge(ban), ASH_RED[5])
    cv.fill(ban & ((yy == 12) | (yy == 13)), ASH_RED[3])
    cv.fill(ban & (yy == 12), ASH_RED[5])
    cv.fill(bottom_edge(ban) | (shift(bottom_edge(ban), 0, -1) & ban), ASH_RED[2])
    # the flame sigil in a ring
    ring = ellipse_ring(W, H, 12.5, 32, 6.5, 7) | ellipse_ring(W, H, 12.5, 32, 5.5, 6)
    cv.fill(ring & ban, ASH_RED[2])
    cv.fill(ellipse_ring(W, H, 12.5, 32, 6.5, 7) & ban & (xx + yy < 44), ASH_RED[4])
    sig = _flame_sigil(W, H, 12.5, 33, 1.5)
    cv.fill(sig, ASH_RED[4])
    cv.fill(sig & shift(~sig, 1, 0), ASH_RED[5])
    cv.fill(sig & shift(~sig, -1, 0) & ~shift(~sig, 1, 0), ASH_RED[2])
    cv.fill(m_ellipse(W, H, 12.5, 34.5, 1.2, 1.2), EMBER[4])
    # three marks of rank under it and scorch holes near the hem
    for k in range(3):
        cv.fill(m_rect(W, H, 9 + k * 3, 46, 10 + k * 3, 48) & ban, ASH_RED[3])
    for (hx, hy) in ((16, 58), (7, 62)):
        hole = m_ellipse(W, H, hx, hy, 1.3, 1.6)
        cv.fill(dilate(hole) & ban & ~hole, CHAR[1])
        cv.erase(hole)
    outline(cv)
    return cv


@prop("cinder_tent", 110, 70, ground=3)
def cinder_tent(state, f):
    """An Ashborn war tent on the Cinder Fields: a long ridge tent of dark stitched hide over a low
    wall, the eaves trimmed with a flame-cut ember-red valance and the flame sigil painted on the
    roof; the door flaps are tied back on a brazier-lit interior, and guy ropes run to stakes."""
    W, H = 110, 70
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 67
    nz = vnoise(W, H, 3, seed_of("tent"), 2)
    ground_shadow(cv, 55, gy, 52, 2.0)
    # guy ropes and stakes (behind)
    for (sx, ex, ey) in ((3, 14, 42), (107, 96, 42)):
        cv.fill(m_line(W, H, [(sx, gy - 2), (ex, ey)]), ROPE[2])
        cv.fill(m_rect(W, H, sx - 1, gy - 4, sx, gy), WOOD[2])
    # ridge poles standing proud at both ends, with streamers
    for px in (27, 83):
        pole = m_rect(W, H, px - 1, 3, px, 16)
        shade(cv, pole, CHAR, contour=True, mode="cyl", base=0.6, gain=1.0)
        cv.fill(m_poly(W, H, [(px - 1.5, 3), (px - 0.5, 1), (px + 0.5, 3)]), IRON[4])
        st = m_poly(W, H, [(px + 1, 4), (px + 9, 5 + (px % 3)), (px + 6, 6.5), (px + 10, 8), (px + 1, 7)])
        cv.fill(st, ASH_RED[4])
        cv.fill(bottom_edge(st), ASH_RED[2])
    # the wall
    wall = m_rect(W, H, 10, 44, 99, gy - 1)
    shade(cv, wall, HIDE, contour=True, R=1, mode="flat", base=0.42, gain=0.0, noise=nz, namp=0.2,
          bias=-np.clip((xx - 10) / 90.0, 0, 1) * 0.15)
    for sx in range(18, 99, 11):
        cv.fill(m_rect(W, H, sx, 45, sx, gy - 2) & ((yy % 2) == 0), HIDE[4])
    # the roof: two slopes meeting at the ridge, panels stitched down the fall
    roof = m_poly(W, H, [(4, 46), (25, 14), (85, 14), (106, 46), (104, 48), (6, 48)])
    shade(cv, roof, HIDE, contour=True, R=2, base=0.55, gain=1.1, noise=nz, namp=0.25, top=0.15)
    cv.fill(roof & (yy <= 16), HIDE[5])
    for k in range(9):
        x0 = 25 + k * 7.5
        x1 = 4 + k * 12.75
        seam = m_line(W, H, [(x0, 16), (x1, 46)]) & erode(roof)
        cv.fill(seam & ((yy % 2) == 1), HIDE[1])
        cv.fill(shift(seam, 1, 0) & erode(roof) & ((yy % 2) == 1), HIDE[4])
    for (px, py) in ((36, 30), (72, 24)):
        pm = m_poly(W, H, [(px - 4, py - 3), (px + 4, py - 3), (px + 5, py + 3), (px - 4, py + 3)]) & roof
        shade(cv, pm, ASH, R=1, base=0.55, gain=0.8)
        cv.fill(border(pm) & ((xx + yy) % 2 == 0), HIDE[1])
    sig = _flame_sigil(W, H, 55, 29, 2.6) & roof
    cv.fill(dilate(sig) & roof & ~sig, HIDE[1])
    cv.fill(sig, ASH_RED[3])
    cv.fill(sig & shift(~sig, 1, 0), ASH_RED[5])
    # the ember-red valance along the eave: a band cut into flame points
    val = m_rect(W, H, 5, 45, 105, 48)
    for vx in range(6, 105, 6):
        val |= m_poly(W, H, [(vx - 2.5, 48), (vx, 52 + (vx // 6) % 2), (vx + 2.5, 48)])
    val &= ~m_rect(W, H, 44, 49, 66, 60)
    shade(cv, val, ASH_RED, contour=True, R=1, mode="flat", base=0.6, gain=0.0,
          bias=-np.clip((xx - 5) / 100.0, 0, 1) * 0.2)
    cv.fill(val & (yy == 45), ASH_RED[5])
    cv.fill(val & (yy == 47) & ((xx % 3) == 0), GOLD[3])
    # the door: flaps tied back on a dark, brazier-lit interior
    door = m_poly(W, H, [(46, gy - 1), (48, 49), (62, 49), (64, gy - 1)])
    cv.fill(door, CHAR[0])
    inside = door & (yy > 56)
    cv.fill(inside & (vnoise(W, H, 2, seed_of("tent_in"), 1) > 0.5), CHAR[1])
    br = m_rect(W, H, 53, 60, 57, 63)
    cv.fill(br, IRON[2])
    cv.fill(m_rect(W, H, 53, 60, 57, 60), IRON[4])
    cv.fill(m_poly(W, H, [(53.5, 60), (55, 56), (56.5, 60)]), EMBER[3])
    cv.put(55, 58, EMBER[5])
    for (x0, x1, sgn) in ((42, 48, -1), (62, 68, 1)):
        flap = m_poly(W, H, [(x0 if sgn < 0 else x1, 49), ((x0 + x1) / 2, 49), (x0 + 3 if sgn < 0 else x1 - 3, 57),
                             (x0 if sgn < 0 else x1, 60)])
        shade(cv, flap, HIDE, contour=True, R=1, base=0.6 if sgn < 0 else 0.45, gain=1.0)
        cv.fill(flap & (yy == 55), ROPE[3])
    cv.fill(m_rect(W, H, 45, 48, 65, 49), ASH_RED[2])
    # beast-tooth trophies hung from the door posts
    for tx in (44, 66):
        cv.fill(m_rect(W, H, tx, 50, tx, 55), ROPE[2])
        tooth = m_poly(W, H, [(tx - 1, 55), (tx + 1, 55), (tx, 58)])
        cv.fill(tooth, BONE[3])
    outline(cv)
    glow(cv, 55, 58, 9, 7, EMBER[3], steps=((1.0, 0.1), (0.6, 0.14)))
    return cv


@prop("war_drum", 44, 46, ground=3)
def war_drum(state, f):
    """An Ashborn war drum: a big barrel drum hung in a crossed timber frame, both heads of dark
    hide laced on with red cord and studded round the rim, the flame sigil daubed on the head,
    and a pair of heavy mallets propped against the frame."""
    W, H = 44, 46
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 43
    ground_shadow(cv, 22, gy, 20, 1.6)
    # the stands: an X of timbers at each side of the drum, behind it, joined by a sill
    for (xa, xb, base) in ((3, 13, 0.55), (29, 39, 0.4)):
        for (x0, x1) in ((xa, xb), (xb, xa)):
            leg = tube(W, H, [(x0, gy), (x1, 12)], 1.3)
            shade(cv, leg, WOOD, contour=True, R=1, base=base, gain=1.1)
        cv.fill(m_rect(W, H, (xa + xb) // 2 - 2, 25, (xa + xb) // 2 + 1, 28), ROPE[2])
    sill = m_rect(W, H, 3, gy - 3, 40, gy - 1)
    shade(cv, sill, CHAR, contour=True, R=1, base=0.5, gain=1.0)
    cv.fill(m_rect(W, H, 3, gy - 3, 40, gy - 3), CHAR[4])
    # the drum body seen three-quarters: the shell curving back to the right of the near head
    body = m_ellipse(W, H, 25, 24, 13, 15) | m_rect(W, H, 18, 9, 25, 39)
    shade(cv, body, ASH_RED, contour=True, mode="cyl", base=0.45, gain=1.2)
    for k, by in enumerate((12, 36)):
        cv.fill(body & (np.abs(yy - by) < 1) & (xx > 18), IRON[3])
    # cords laced from head to head
    for k in range(6):
        y0 = 11 + k * 5
        cv.fill(m_line(W, H, [(21, y0), (33, y0 + 2.5), (21, y0 + 5)]) & body, ROPE[4] if k % 2 else ROPE[3])
    # the near head: a hide disc, darker toward the rim, studs round it, the sigil in the middle
    head = m_ellipse(W, H, 17, 24, 10.5, 15)
    shade(cv, head, HIDE, contour=True, mode="sphere", base=0.62, gain=0.9)
    rim = ellipse_ring(W, H, 17, 24, 10.5, 15) | ellipse_ring(W, H, 17, 24, 9.5, 14)
    cv.fill(rim, ASH_RED[2])
    cv.fill(ellipse_ring(W, H, 17, 24, 10.5, 15) & (xx + yy < 38), ASH_RED[4])
    for k in range(14):
        a = 2 * math.pi * k / 14
        sx, sy = 17 + math.cos(a) * 9.8, 24 + math.sin(a) * 14.3
        cv.put(int(round(sx)), int(round(sy)), GOLD[5] if math.cos(a) + math.sin(a) < 0 else GOLD[3])
    sig = _flame_sigil(W, H, 17, 25, 1.7)
    cv.fill(sig, ASH_RED[3])
    cv.fill(sig & shift(~sig, 1, 0), ASH_RED[5])
    cv.fill(m_ellipse(W, H, 15, 18, 2.2, 3.5) & head & ~sig, HIDE[5])
    # the yoke timbers that the drum hangs from, across the top of both stands
    yoke = m_rect(W, H, 5, 8, 37, 10)
    shade(cv, yoke, WOOD, contour=True, R=1, base=0.55, gain=1.1)
    cv.fill(m_rect(W, H, 5, 8, 37, 8), WOOD[5])
    for hx in (12, 30):
        cv.fill(m_rect(W, H, hx, 11, hx, 13), ROPE[2])
    # the mallets propped against the frame
    for (x0, y0, x1, y1) in ((34, gy - 3, 38, 29), (37, gy - 3, 40, 31)):
        cv.fill(m_line(W, H, [(x0, y0), (x1, y1)]), WOOD[4])
        hd = m_ellipse(W, H, x1, y1 - 1, 1.9, 2.3)
        shade(cv, hd, ASH_RED, contour=True, mode="sphere", base=0.55, gain=1.0)
    outline(cv)
    return cv


# ------------------------------------------------------------------ Tidebreak Front: the bastion and the Hollow
BASTION = ramp("#141a1f", "#222b31", "#323e44", "#46545a", "#5e6d70", "#7c8a89", "#a1ada7")
CORRUPT = ramp("#1a191f", "#2b2932", "#3e3b47", "#54505e", "#6c6777", "#8a8494", "#afa9b8")
HOLLOW_GLOW = ramp("#2a1244", "#4b2380", "#7447b8", "#a57ae4", "#d6bcff", "#f6eeff")


@prop("bastion_wall", 128, 96, repeat="x", ground=2)
def bastion_wall(state, f):
    """A section of the Tidebreak Bastion's rampart: heavy courses of dark ashlar on a battered
    footing, a moulded string course, a parapet of merlons pierced with arrow slits, and a bronze
    lantern cage on a bracket burning to keep the Hollow Tide back. Repeats seamlessly along x."""
    W, H = 128, 96
    gy = H - 2
    big = Canvas(3 * W, H)
    BW = big.w
    xx, yy = grid(BW, H)
    xm = xx % W
    nz = np.tile(vnoise(W, H, 4, seed_of("bastion"), 2, wrap=True), (1, 3))
    # merlons (never crossing the tile edge) and the wall body
    merl = ((xm % 32) >= 6) & ((xm % 32) <= 25) & (yy >= 12) & (yy <= 30)
    body = (yy >= 30) & (yy <= gy)
    foot = (yy >= 84) & (yy <= gy)
    wall = merl | body
    shade(big, body, BASTION, contour=False, mode="flat", base=0.5, gain=0.0, noise=nz, namp=0.25)
    # ashlar courses: 9 px tall, staggered joints every course, each block's own tone
    course = (yy - 33) // 9
    g = rng("bastion_blocks")
    tones = g.uniform(-0.12, 0.12, (20, 16))
    blk_w = 32
    bx = (xm + (course % 2) * 16) % W
    bid = (bx // blk_w).astype(int) % 4
    tone = tones[np.clip(course, 0, 19), bid]
    in_c = body & (yy >= 33) & (yy < 84)
    _idx_fill(big, in_c, BASTION, np.clip(3.0 + tone * 6 + (nz - 0.5) * 1.2, 1, 5))
    joint_h = in_c & (((yy - 33) % 9) == 8)
    joint_v = in_c & ((bx % blk_w) == 0)
    big.fill(joint_h | joint_v, BASTION[1])
    big.fill(in_c & (((yy - 33) % 9) == 0) & ~joint_v, BASTION[5])
    big.fill(in_c & ((bx % blk_w) == 1) & ~joint_h, BASTION[4])
    # battered footing, a darker plinth course
    _idx_fill(big, foot, BASTION, np.clip(2.2 + (nz - 0.5) * 1.5 - (yy - 84) * 0.08, 1, 4))
    big.fill(foot & (yy == 84), BASTION[5])
    big.fill(foot & ((xm % 21) == 0), BASTION[1])
    # string course under the parapet
    sc = (yy >= 30) & (yy <= 32)
    big.fill(sc, BASTION[4])
    big.fill(sc & (yy == 30), BASTION[6])
    big.fill(sc & (yy == 32), BASTION[2])
    # merlons: capped, lit on their left faces, each with an arrow slit
    _idx_fill(big, merl, BASTION, np.clip(3.2 + (nz - 0.5) * 1.2, 1, 5))
    big.fill(merl & (yy <= 13), BASTION[6])
    big.fill(merl & ((xm % 32) == 6), BASTION[5])
    big.fill(merl & ((xm % 32) == 25), BASTION[2])
    slit = merl & ((xm % 32) >= 15) & ((xm % 32) <= 16) & (yy >= 17) & (yy <= 26)
    big.fill(slit, INK)
    big.fill(merl & ((xm % 32) == 17) & (yy >= 17) & (yy <= 26), BASTION[5])
    # weathering: a few chipped block corners and grey Hollow stains creeping up from the foot
    stain = body & (vnoise(W, H, 4, seed_of("bastion_stain"), 1, wrap=True)[:, np.arange(BW) % W] > 0.62) & (yy > 70)
    big.fill(stain, CORRUPT[3], 0.3)
    # the lantern: a bronze bracket and cage on the wall face in the middle of the tile
    lcx = [W // 2 + k * W for k in range(3)]
    lamps = []
    for lx in lcx:
        brk = m_rect(BW, H, lx - 1, 36, lx, 42) | m_line(BW, H, [(lx, 42), (lx + 6, 38)]) | m_rect(BW, H, lx - 2, 35, lx + 1, 36)
        _bronze(big, brk, base=0.55, gain=1.1)
        cap = m_poly(BW, H, [(lx + 2, 43), (lx + 6, 40), (lx + 10, 43)])
        _bronze(big, cap, base=0.6, gain=1.2)
        big.fill(m_rect(BW, H, lx + 6, 38, lx + 6, 40), BRONZE[3])
        _star_body(big, lx + 6, 47, 2.6, 1, True, seed="bastion_lamp")
        cage = np.zeros((H, BW), bool)
        for cxb in (lx + 3, lx + 6, lx + 9):
            cage |= m_rect(BW, H, cxb, 44, cxb, 50)
        big.fill(cage, BRONZE[3])
        big.fill(m_rect(BW, H, lx + 3, 51, lx + 9, 52), BRONZE[2])
        lamps.append(lx)
        # its light on the stones
        big.light(m_ellipse(BW, H, lx + 6, 47, 14, 12) & body, STARFIRE[3], 0.08)
    outline(big, close_edges=False)
    for lx in lamps:
        glow(big, lx + 6, 47, 10, 10, STAR_HALO, steps=((1.0, 0.1), (0.55, 0.16)))
    cv = Canvas(W, H)
    cv.rgb = big.rgb[:, W:2 * W].copy()
    cv.a = big.a[:, W:2 * W].copy()
    return cv


@prop("hollow_crystal", 30, 44, states=(("idle", 4, 5),), ground=3)
def hollow_crystal(state, f):
    """A crystal the Hollow Tide has corrupted: grey-violet prisms split by cracks that leak a faint
    violet light, standing in a grey puddle of Hollow seep; wisps rise off it and fall back."""
    W, H = 30, 44
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 41
    pulse = (0.0, 0.5, 1.0, 0.5)[f % 4]
    ground_shadow(cv, 15, gy, 13, 1.5)
    puddle = m_ellipse(W, H, 15, gy - 0.5, 13, 2.2) & (yy <= gy)
    cv.fill(puddle, HOLLOW[1])
    cv.fill(puddle & (yy <= gy - 1), HOLLOW[2])
    cv.fill(ellipse_ring(W, H, 15, gy - 0.5, 13, 2.2) & (yy < gy - 1), HOLLOW[4])
    cracks = np.zeros((H, W), bool)
    for (x, by, h, w, lean) in ((10, gy - 3, 22, 5, -3), (20, gy - 3, 26, 5, 2), (15, gy - 4, 35, 6, 0),
                                (6, gy - 1, 10, 3, -3), (24, gy - 1, 12, 4, 2)):
        m = _glass_shard(cv, x, by, h, w, lean, see=0.0, pal=CORRUPT)
        g = rng("hollow_crack", x)
        cx0 = x + lean * 0.3
        pts = [(cx0 + g.uniform(-0.8, 0.8), by - h * t) for t in (0.1, 0.3, 0.5, 0.7)]
        cracks |= m_line(W, H, pts) & erode(m)
    cv.fill(cracks, HOLLOW_GLOW[2 + int(pulse >= 0.5)])
    cv.fill(cracks & (vnoise(W, H, 2, seed_of("hc", f % 2), 1) > 0.6), HOLLOW_GLOW[4])
    rock(cv, 15, gy - 1, 7, 2.5, "hollow_crystal_rock", pal=HOLLOW, R=1, facets=1)
    outline(cv, skip=puddle & ~cv.solid)
    # violet seep running down from the cracks and a pulsing glow
    for (dx, dy) in ((12, 30), (21, 27), (16, 22)):
        ln = 2 + (f + dx) % 3
        cv.fill(m_rect(W, H, dx, dy, dx, dy + ln), HOLLOW_GLOW[3], 0.7)
    a = 0.06 + pulse * 0.05
    glow(cv, 15, 24, 13, 18, HOLLOW_GLOW[3], steps=((1.0, a * 0.7), (0.6, a)))
    wisp(cv, 11, 12, f, 4, height=10, seed=1.0, c=HOLLOW_GLOW[3], alpha=0.5, amp=1.2)
    wisp(cv, 19, 8, (f + 2) % 4, 4, height=8, seed=2.5, c=HOLLOW_GLOW[4], alpha=0.4, amp=1.0)
    motes(cv, 4, 4, 26, 38, f, 4, "hollow_cm", count=4, pal=(HOLLOW_GLOW[3], HOLLOW_GLOW[5]), alpha=0.8)
    return cv


@prop("drone_hive", 70, 90, ground=3)
def drone_hive(state, f):
    """A Hollow drone hive grown at the Greyfall Breach: a leaning spire of grey shell plates laid
    over each other like the scales of a cone, split open here and there on violet-lit cells, the
    largest a glowing mouth at its foot, and roots spreading into a stain of grey seep."""
    W, H = 70, 90
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 87
    ground_shadow(cv, 35, gy, 32, 2.0)
    seep = m_ellipse(W, H, 35, gy - 0.5, 33, 2.5) & (yy <= gy)
    cv.fill(seep, HOLLOW[1])
    cv.fill(seep & (yy <= gy - 1), HOLLOW[2])
    g = rng("hive_roots")
    for k in range(7):
        sx = 35 + (k - 3) * 7 + g.uniform(-2, 2)
        ex = sx + (k - 3) * 3.5 + g.uniform(-2, 2)
        root = tube(W, H, [(sx, gy - 8), ((sx + ex) / 2, gy - 3), (ex, gy - 1)], 1.8, 0.8)
        shade(cv, root, HOLLOW, contour=True, R=1, base=0.35, gain=1.0)

    def axis(t):
        """Centre line of the spire from base (t=0) to tip (t=1): it leans and curls to the right."""
        return 33 + 7 * t ** 2 + math.sin(t * 3.0) * 1.5, gy - 3 - t * 80

    def half(t):
        return 30 * (1 - t) ** 0.85 + 2

    # the core mass, then rows of pointed plates from the bottom up so each row laps the one below
    core = np.zeros((H, W), bool)
    for yv in range(H):
        t = (gy - 3 - yv) / 80.0
        if 0 <= t <= 1:
            ax, _ = axis(t)
            hw = half(t) - 1
            core[yv, int(ax - hw):int(ax + hw) + 1] = True
    shade(cv, core, HOLLOW, contour=True, R=3, base=0.3, gain=1.0)
    cells = []
    rows = 13
    for r in range(rows):
        t = r / (rows - 1.0)
        ax, ay = axis(t)
        hw = half(t)
        n = max(1, int(round(hw / 6.0)))
        for j in range(n + 1):
            u = (j + (0.5 if r % 2 else 0.0)) / n - 0.5
            if abs(u) > 0.5:
                continue
            pw = hw / n + 1.5
            px = ax + u * 2 * max(0.0, hw - pw * 0.7)
            ph = 7.5 - t * 3
            plate = (m_ellipse(W, H, px, ay - ph * 0.25, pw, ph * 0.75) & (yy <= ay - ph * 0.25)) | m_poly(
                W, H, [(px - pw, ay - ph * 0.25), (px + pw, ay - ph * 0.25), (px + pw * 0.3, ay + ph * 0.3),
                       (px, ay + ph * 0.4), (px - pw * 0.3, ay + ph * 0.3)])
            plate &= dilate(core)
            side = u * 2
            shade(cv, plate, HOLLOW, contour=True, R=2, base=0.4 - side * 0.14, gain=1.2)
            ridge = m_line(W, H, [(px, ay - ph + 1), (px, ay + ph * 0.3)]) & erode(plate)
            cv.fill(ridge, HOLLOW[4] if side < 0.2 else HOLLOW[2])
            cv.fill(bottom_edge(plate), HOLLOW[0])
            if (r, j) in ((4, 1), (5, 3), (7, 0), (8, 2), (10, 1), (2, 4), (3, 0)):
                cells.append((px, ay - ph * 0.5, max(2.0, pw * 0.5), max(1.8, ph * 0.35)))
    mouth = (33.0, gy - 7.0, 6.0, 4.5)
    cells.append(mouth)
    for (px, py, rx, ry) in cells:
        hole = m_ellipse(W, H, px, py, rx + 1, ry + 1)
        cv.fill(hole, HOLLOW[0])
        inner = m_ellipse(W, H, px + 0.5, py + 0.5, rx, ry)
        cv.fill(inner, HOLLOW_GLOW[1])
        cv.fill(m_ellipse(W, H, px + 0.5, py + 1, rx * 0.7, ry * 0.6), HOLLOW_GLOW[2])
        cv.fill(m_ellipse(W, H, px + 0.5, py + 1, rx * 0.35, ry * 0.3), HOLLOW_GLOW[4])
        cv.fill(top_edge(inner), CORRUPT[0])
    tx, ty = axis(1.0)
    tipm = tube(W, H, [(tx - 1, ty + 6), (tx + 1, ty + 1), (tx + 4, ty - 1)], 2.2, 0.8)
    shade(cv, tipm, HOLLOW, contour=True, R=1, base=0.55, gain=1.1)
    outline(cv, skip=seep & ~cv.solid)
    for (px, py, rx, ry) in cells:
        glow(cv, px + 0.5, py + 0.5, rx + 5, ry + 5, HOLLOW_GLOW[3], steps=((1.0, 0.08), (0.55, 0.14)))
    motes(cv, 12, 8, 60, 70, 0, 4, "hive_m", count=6, pal=(HOLLOW_GLOW[3], HOLLOW_GLOW[5]), alpha=0.7)
    return cv


# ------------------------------------------------------------------ Nebula Deep
NEB_TEAL = ramp("#062a30", "#0b4a50", "#137270", "#20a094", "#4fcdb8", "#a8f0dc")
NEB_MAGENTA = ramp("#2a0a2c", "#4f1250", "#7c1f74", "#aa3496", "#d65cb6", "#f5a0d8")
NEB_BONE = ramp("#262b3a", "#454c5f", "#6d7385", "#9c9ea8", "#c7c7c2", "#e9e7dc")
VOID = ramp("#05040c", "#0c0a1c", "#161236", "#241c52", "#35286e")


def _coral_branch(cv, x, y, ang, ln, r, depth, g, out, pal):
    """Grow one coral branch and its forks; collect (mask, tip) pairs in `out`."""
    ex, ey = x + math.cos(ang) * ln, y + math.sin(ang) * ln
    mx, my = (x + ex) / 2 + math.cos(ang + 1.57) * ln * 0.12, (y + ey) / 2 + math.sin(ang + 1.57) * ln * 0.12
    m = tube(cv.w, cv.h, [(x, y), (mx, my), (ex, ey)], r, max(0.7, r * 0.72))
    out.append((m, (ex, ey), depth, r))
    if depth <= 0:
        return
    for s in (-1, 1):
        a2 = ang + s * g.uniform(0.3, 0.6)
        _coral_branch(cv, ex, ey, a2, ln * g.uniform(0.66, 0.8), max(0.7, r * 0.72), depth - 1, g, out, pal)


@prop("nebula_coral", 40, 50, ground=3)
def nebula_coral(state, f):
    """A branching star-coral of the Nebula Deep: teal stems forking into magenta tips that each
    hold a pale star-polyp, grown up from a dark rock with a smaller, dimmer coral behind it."""
    W, H = 40, 50
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 47
    ground_shadow(cv, 20, gy, 17, 1.5)
    for (bx, ang, ln, r, depth, seed, base) in ((27, -1.3, 8, 1.6, 2, "coral_b", 0.3), (19, -1.62, 12, 2.3, 3, "coral_a", 0.55)):
        g = rng("coral", seed)
        parts_ = []
        _coral_branch(cv, bx, gy - 4, ang, ln, r, depth, g, parts_, NEB_TEAL)
        stems = np.zeros((H, W), bool)
        for m, tip, d, rr in parts_:
            stems |= m
        shade(cv, stems, NEB_TEAL, contour=True, R=1, mode="bevel", base=base, gain=1.3)
        for m, (tx, ty), d, rr in parts_:
            if d == 0:
                tipm = m_ellipse(W, H, tx, ty, rr + 0.9, rr + 0.9)
                shade(cv, tipm, NEB_MAGENTA, contour=True, mode="sphere", base=base + 0.1, gain=1.2)
                if base > 0.4:
                    cv.put(int(round(tx - 0.4)), int(round(ty - 0.4)), WHITE_HOT)
        g2 = rng("coral_polyps", seed)
        for _ in range(10):
            m, (tx, ty), d, rr = parts_[int(g2.integers(len(parts_)))]
            ys, xs = np.nonzero(m & erode(m))
            if len(xs):
                i = int(g2.integers(len(xs)))
                cv.put(xs[i], ys[i], NEB_TEAL[5] if base > 0.4 else NEB_TEAL[3])
    rock(cv, 20, gy, 13, 5, "coral_rock", pal=STONE_DARK, R=2, base=0.5, facets=2)
    rock(cv, 32, gy, 5, 3, "coral_rock2", pal=STONE_DARK, R=1, facets=1)
    outline(cv)
    glow(cv, 19, 18, 16, 16, NEB_MAGENTA[4], steps=((1.0, 0.04), (0.6, 0.06)))
    return cv


@prop("void_geode", 36, 30, ground=3)
def void_geode(state, f):
    """A geode split open on the floor of the Nebula Deep: a rough grey shell, a rim of violet
    crystal teeth, and inside, instead of crystal, a small night sky of stars and a smudge of
    nebula. The other half lies tipped over beside it."""
    W, H = 36, 30
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 27
    ground_shadow(cv, 18, gy, 16, 1.5)
    # the other half, tipped on its back to the right, its rough outside up
    rock(cv, 28, gy, 6, 5, "geode_half", pal=STONE, R=2, base=0.45, facets=2)
    # the standing half: a shell with the cut face turned to us
    shell = m_ellipse(W, H, 15, 16, 12, 11) & (yy <= gy)
    nz = vnoise(W, H, 2, seed_of("geode"), 2)
    shade(cv, shell, STONE, contour=True, R=2, base=0.5, gain=1.3, noise=nz, namp=0.3)
    teeth = m_ellipse(W, H, 15.5, 16, 9, 8.3)
    cv.fill(teeth, VIOLET[3])
    g = rng("geode_teeth")
    for k in range(22):
        a = 2 * math.pi * k / 22
        tx, ty = 15.5 + math.cos(a) * 8.3, 16 + math.sin(a) * 7.6
        ix, iy = 15.5 + math.cos(a) * 6.4, 16 + math.sin(a) * 5.8
        tooth = m_line(W, H, [(tx, ty), (ix, iy)])
        lit = math.cos(a) + math.sin(a) > 0.3
        cv.fill(tooth, VIOLET[5] if lit else VIOLET[2])
    space = m_ellipse(W, H, 15.5, 16, 6.8, 6.2)
    d = np.hypot((xx - 15.5) / 6.8, (yy - 16) / 6.2)
    _idx_fill(cv, space, VOID, np.clip(4.2 - d * 4, 0, 4))
    neb = space & (vnoise(W, H, 3, seed_of("geode_neb"), 2) > 0.58)
    cv.fill(neb & (xx < 16), NEB_MAGENTA[2])
    cv.fill(neb & (xx >= 16), NEB_TEAL[2])
    for (sx, sy, c) in ((12, 13, WHITE_HOT), (18, 18, STARLIGHT[6]), (14, 19, STARLIGHT[5]), (19, 13, STARLIGHT[5]),
                        (11, 17, STARLIGHT[4]), (16, 15, WHITE_HOT), (20, 16, STARLIGHT[4])):
        cv.put(sx, sy, c)
    cv.fill(m_rect(W, H, 15, 15, 17, 15) | m_rect(W, H, 16, 14, 16, 16), STARLIGHT[5])
    cv.put(16, 15, WHITE_HOT)
    outline(cv)
    glow(cv, 15.5, 16, 9, 8, VIOLET[4], steps=((1.0, 0.05), (0.6, 0.08)))
    return cv


@prop("leviathan_bones", 180, 70, ground=4)
def leviathan_bones(state, f):
    """The bones of a sky leviathan on the floor of the Nebula Deep: a long spine arching low over
    the ground with its tail sinking into it, great ribs curving down on both sides, and the long
    skull resting on its jaw at the right; teal and magenta star-crystal has grown at the joints
    and a thin nebula mist lies round the bones."""
    W, H = 180, 70
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 66
    ground_shadow(cv, 90, gy, 88, 2.2)
    nz = vnoise(W, H, 3, seed_of("leviathan"), 2)
    spine_pts = [(4, gy - 1), (18, 47), (40, 26), (70, 15), (100, 14), (126, 21), (144, 33)]
    sp = _spline(spine_pts)

    def spine_y(x):
        return min(sp, key=lambda p: abs(p[0] - x))[1]

    def bone(m, base=0.6, gain=1.3):
        shade(cv, m, NEB_BONE, contour=True, R=2, base=base, gain=gain, noise=nz, namp=0.2)
        return m

    ribs = [(34, 0.8), (48, 1.0), (62, 1.15), (76, 1.2), (90, 1.2), (104, 1.1), (118, 0.95), (130, 0.8)]

    def rib(sx, sc, far):
        sy = spine_y(sx) + 1
        dx = 5 if far else 0
        bot = gy - 1 if not far else gy - 4
        reach = (bot - sy)
        pts = [(sx + dx, sy - (1 if far else 0)), (sx - 6 * sc + dx, sy + reach * 0.25),
               (sx - 10 * sc + dx, sy + reach * 0.6), (sx - 9 * sc + dx, bot)]
        m = tube(W, H, pts, 2.0 if far else 2.6, 1.1 if far else 1.6)
        bone(m, base=0.25 if far else 0.58, gain=1.0 if far else 1.3)
        return m

    for sx, sc in ribs:
        rib(sx, sc, True)
    spine = tube(W, H, spine_pts, 2.0, 3.4)
    bone(spine, base=0.6)
    for i, (px, py) in enumerate(sp[8::12]):
        if not 10 < px < 140:
            continue
        cv.fill(m_rect(W, H, px, py - 2, px, py + 2) & erode(spine), NEB_BONE[2])
        ln = 3 + 4 * math.exp(-((px - 80) / 40.0) ** 2)
        spur = m_poly(W, H, [(px - 1.5, py - 2), (px - 0.5 - ln * 0.4, py - 2 - ln), (px + 1, py - 2)])
        bone(spur, base=0.65, gain=1.0)
    for sx, sc in ribs:
        rib(sx, sc, False)
    # the skull: a long wedge resting on its lower jaw, a heavy brow over an empty socket, a horn
    horn = tube(W, H, [(147, 29), (137, 23), (126, 21), (120, 23)], 2.6, 0.7)
    bone(horn, base=0.62)
    skull = m_poly(W, H, [(137, 34), (143, 27), (153, 26), (160, 30), (175, 45), (176, 49), (168, 50), (150, 50),
                          (141, 46)])
    bone(skull, base=0.58)
    brow = m_poly(W, H, [(147, 30), (158, 30), (162, 34), (150, 33)])
    bone(brow, base=0.72, gain=1.0)
    eye = m_poly(W, H, [(150, 34), (158, 34), (159, 38), (153, 40), (149, 37)])
    cv.fill(eye, VOID[1])
    cv.fill(eye & shift(~eye, 0, 1), NEB_BONE[0])
    cv.put(157, 36, NEB_TEAL[4])
    for (x0, x1) in ((162, 171), (165, 174)):
        cv.fill(m_line(W, H, [(x0, 38 + (x0 - 162) * 0.5), (x1, 44)]) & erode(skull), NEB_BONE[2])
    cv.fill(m_line(W, H, [(173, 46), (175, 46)]), VOID[1])
    jaw = m_poly(W, H, [(143, 52), (175, 53), (176, 56), (162, gy - 1), (148, gy - 2), (141, 57)])
    bone(jaw, base=0.48, gain=1.2)
    for tx in range(150, 174, 3):
        cv.fill(m_poly(W, H, [(tx, 50), (tx + 1.6, 50), (tx + 0.8, 52.5)]), NEB_BONE[5])
        cv.fill(m_poly(W, H, [(tx + 1, 53), (tx + 2.4, 53), (tx + 1.7, 51)]), NEB_BONE[4])
    cv.fill(m_rect(W, H, 146, 50, 176, 50) & ~skull, VOID[1])
    # star-crystal grown at the joints, and a few loose vertebrae
    g = rng("leviathan_crystal")
    for (cx, cy) in ((40, 26), (71, 14), (100, 13), (126, 20), (61, 52), (150, 27)):
        for k in range(3):
            pal = NEB_TEAL if k % 2 == 0 else NEB_MAGENTA
            _glass_shard(cv, cx + (k - 1) * 3, cy + 1, int(g.integers(3, 7)), 2, (k - 1) * 1.5, see=0.0, pal=pal)
    for (vx, vy) in ((12, gy - 2), (24, gy - 1)):
        v = m_ellipse(W, H, vx, vy - 1.5, 2.6, 2) & (yy <= gy)
        bone(v, base=0.55, gain=1.0)
    rock(cv, 100, gy, 7, 3, "lev_r1", pal=STONE_DARK, R=1, facets=1)
    rock(cv, 60, gy, 5, 2.5, "lev_r2", pal=STONE_DARK, R=1, facets=1)
    outline(cv)
    # thin nebula mist lying round the bones
    mist = (yy > gy - 8) & (yy <= gy) & (vnoise(W, H, 6, seed_of("lev_mist"), 2) > 0.55)
    cv.fill(mist & ~cv.solid & (xx < 90), NEB_MAGENTA[3], 0.18)
    cv.fill(mist & ~cv.solid & (xx >= 90), NEB_TEAL[3], 0.2)
    glow(cv, 153, 36, 5, 5, NEB_TEAL[4], steps=((1.0, 0.1),))
    return cv


# ------------------------------------------------------------------ gathering nodes (same layout as Act II's)
from defs_nature import HERB_STATES, _crack_path, cut_stems  # noqa: E402
from parts import herb_sparkle  # noqa: E402

STAR_PETAL = ramp("#6b5220", "#a88a3c", "#d6bb68", "#f0dc9a", "#fbf0c8", "#fffcee")
VOID_PETAL = ramp("#07050e", "#130d24", "#22183e", "#352660", "#4f3a86", "#7a5cb8")
VOID_LEAF = ramp("#0a1418", "#10262a", "#17393a", "#22504b", "#35705f", "#58927a")


@prop("star_lotus_patch", 28, 22, states=HERB_STATES)
def star_lotus_patch(state, f):
    """A star lotus on a dark islet pool: pale gold petals, each tipped with a tiny star point,
    over round pads floating on still black water that mirrors a few stars."""
    W, H = 28, 22
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 14, 20, 13, 1.4)
    rim = m_ellipse(W, H, 14, 18, 12, 3.4) & (yy <= 20)
    shade(cv, rim, STONE_DARK, contour=True, R=1, base=0.5, gain=1.0)
    pool = m_ellipse(W, H, 14, 17.5, 11, 2.3)
    cv.fill(pool, VOID[1])
    cv.fill(pool & (yy <= 16), VOID[2])
    for (sx, sy) in ((6, 18), (21, 17), (17, 19)):
        cv.put(sx, sy, STARLIGHT[5])
    for (cx, cy, rx) in ((7, 17, 4.5), (21, 17.5, 4), (14, 18.5, 5)):
        pad = m_ellipse(W, H, cx, cy, rx, 1.6)
        pad &= ~m_poly(W, H, [(cx, cy), (cx + rx, cy - 1), (cx + rx, cy + 0.5)])
        shade(cv, pad, VOID_LEAF, contour=True, R=1, base=0.6, gain=1.0)
        cv.fill(top_edge(pad) & (xx < cx), VOID_LEAF[5])
    if state == "ready":
        petals = ((5, 12, 6, 9), (16, 23, 22, 9), (8, 14, 10, 6), (14, 20, 18, 6), (11, 17, 14, 4))
        tips = []
        for k, (x0, x1, tip, ty) in enumerate(petals):
            pm = m_poly(W, H, [(x0, 16), ((x0 + tip) / 2 - 1, (16 + ty) / 2), (tip, ty), ((x1 + tip) / 2 + 1, (16 + ty) / 2),
                               (x1, 16)])
            cv.fill(pm, STAR_PETAL[2 + (k % 2)] if k < 4 else STAR_PETAL[4])
            cv.fill(left_edge(pm), STAR_PETAL[4 if k < 4 else 5])
            cv.fill(right_edge(pm) & ~left_edge(pm), STAR_PETAL[1])
            tips.append((tip, ty))
        cv.fill(m_rect(W, H, 13, 13, 15, 15), STARFIRE[4])
        cv.put(13, 13, WHITE_HOT)
    else:
        cut_stems(cv, [(14, 16)], pal=VOID_LEAF, h=2)
    outline(cv)
    if state == "ready":
        for k, (tx, ty) in enumerate(tips):
            cv.put(tx, ty - 1, WHITE_HOT if (k + f) % 3 == 0 else STARFIRE[5])
        glow(cv, 14, 11, 10, 7, STAR_HALO, steps=((1.0, 0.08 + 0.03 * (f % 2)),))
        herb_sparkle(cv, f, [(6, 8), (22, 8), (14, 3)], c1=STARFIRE[5])
    return cv


@prop("void_orchid_patch", 28, 22, states=HERB_STATES)
def void_orchid_patch(state, f):
    """A void orchid: violet-black blooms on arching stems whose petals hold a starfield instead of a
    pattern, over dark strap leaves on a clump of Nebula Deep rock."""
    W, H = 28, 22
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    ground_shadow(cv, 14, 20, 12, 1.4)
    rock(cv, 14, 19, 10, 4, "vo_rock", pal=STONE_DARK, R=2)
    rock(cv, 22, 19, 4, 2.5, "vo_rock2", pal=STONE_DARK, R=1)
    for (x0, y0, x1, y1, x2, y2) in ((13, 17, 8, 12, 3, 14), (15, 17, 20, 11, 25, 13), (14, 17, 11, 11, 9, 9),
                                     (14, 17, 18, 13, 22, 17), (13, 17, 9, 15, 5, 18)):
        a = m_curve(W, H, [(x0, y0), (x1, y1), (x2, y2)])
        b = m_curve(W, H, [(x0, y0 + 1), (x1, y1 + 1.4), ((x2 + x1) / 2, (y2 + y1) / 2 + 1)])
        cv.fill(a | b, VOID_LEAF[2])
        cv.fill(a & ~b, VOID_LEAF[4])
        cv.fill(b & ~a, VOID_LEAF[1])
    blooms = []
    if state == "ready":
        for spray in (((14, 15), (15, 9), (18, 5)), ((13, 15), (11, 10), (7, 6))):
            cv.fill(m_curve(W, H, list(spray)), VOID_LEAF[3])
        for (bx, by, big) in ((18, 5, True), (7, 6, True), (11, 9, False)):
            r = 2.6 if big else 1.8
            fl = (m_ellipse(W, H, bx - r * 0.8, by, r * 0.8, r * 0.55) | m_ellipse(W, H, bx + r * 0.8, by, r * 0.8, r * 0.55)
                  | m_ellipse(W, H, bx, by - r * 0.7, r * 0.55, r * 0.8) | m_ellipse(W, H, bx, by + r * 0.8, r * 0.6, r * 0.9))
            cv.fill(fl, VOID_PETAL[2])
            cv.fill(border(fl), VOID_PETAL[4])
            cv.fill(border(fl) & (xx + yy < bx + by), VOID_PETAL[5])
            cv.fill(m_rect(W, H, bx, by, bx, by + 1), VOID_PETAL[0])
            blooms.append((bx, by, r))
    else:
        cut_stems(cv, [(14, 15), (13, 15)], pal=VOID_LEAF, h=3)
    outline(cv)
    if state == "ready":
        g = rng("void_orchid_stars", f % 3)
        for (bx, by, r) in blooms:
            for _ in range(3 if r > 2 else 2):
                sx = int(round(bx + g.uniform(-r, r) * 0.8))
                sy = int(round(by + g.uniform(-r, r) * 0.6))
                if cv.solid[sy, sx] and np.allclose(cv.rgb[sy, sx], VOID_PETAL[2]):
                    cv.put(sx, sy, WHITE_HOT if g.random() < 0.4 else STARLIGHT[5])
        glow(cv, 13, 6, 10, 6, VIOLET[4], steps=((1.0, 0.06 + 0.02 * (f % 2)),))
        herb_sparkle(cv, f, [(20, 2), (5, 4), (12, 7)], c1=VIOLET[5])
    return cv


def _lantern_vein(pid, state, stone, ore_fn, debris_c):
    """An Act III ore vein on the Act II vein layout (36x28, full / cracked / depleted): a big rock
    split by cracks, the ore drawn by `ore_fn(cv, m, inner, cracked, spots)` along them."""
    W, H = 36, 28
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    by = 25
    ground_shadow(cv, 18, 26, 17, 1.6)
    if state == "depleted":
        m = rock(cv, 17, by, 11, 5, (pid, "stump"), pal=stone, R=2, base=0.5, facets=2)
        x0, y0, x1, y1 = bbox(m)
        top = m & (yy <= y0 + 1)
        cv.fill(top, stone[5])
        cv.fill(top_edge(m) & ~top, stone[4])
        for i, (rx, rr, rh) in enumerate(((5, 3, 2.2), (29, 4, 3), (24, 2.2, 1.6), (10, 2, 1.4), (33, 2, 1.4))):
            rock(cv, rx, by, rr, rh, (pid, "deb", i), pal=stone, R=1, base=0.52, facets=1)
        for (px, py) in ((14, by - 3), (21, by - 2), (28, by - 2)):
            cv.put(px, py, debris_c)
        outline(cv)
        return cv
    cracked = state == "cracked"
    m = rock(cv, 18, by, 14, 10.5, (pid, "main"), pal=stone, R=3, base=0.55, rough=0.12, facets=3)
    rock(cv, 5, by, 4, 3, (pid, "s1"), pal=stone, R=1, facets=1)
    rock(cv, 31, by, 4.5, 3.5, (pid, "s2"), pal=stone, R=1, facets=1)
    inner = erode(erode(m))
    g = rng("lvein", pid)
    starts = [(11, 8, 1), (20, 7, 0), (25, 12, -1)] + ([(15, 14, 1)] if cracked else [])
    spots = []
    for i, (sx, sy, bias) in enumerate(starts):
        pts = _crack_path(g, sx, sy, 9 if cracked else 7, bias * 0.4)
        pm = m_line(W, H, pts) & inner
        if cracked:
            pm |= shift(pm, 1, 0) & inner & (vnoise(W, H, 2, seed_of(pid, i)) > 0.5)
        cv.fill(pm, stone[0])
        lip = shift(pm, -1, 0) & inner & ~pm
        cv.fill(lip, stone[5])
        spots.append((pts[len(pts) // 2], pm))
        spots.append((pts[-2], pm))
    ore_fn(cv, m, inner, cracked, spots)
    if cracked:
        x0, y0, x1, y1 = bbox(m)
        cut = m_poly(W, H, [(21, y0 - 1), (x1 + 2, y0 - 1), (x1 + 2, y0 + 7), (27, y0 + 5)])
        face = m & shift(cut, -1, 1) & ~cut
        cv.erase(cut & m)
        cv.fill(face, stone[5])
        cv.fill(face & shift(face, 1, 0) & shift(face, 0, 1), stone[4])
        for i, (rx, rr) in enumerate(((27, 2.2), (9, 1.8), (24, 1.4))):
            rock(cv, rx, by, rr, rr * 0.8, (pid, "dbr", i), pal=stone, R=1, facets=0)
    outline(cv)
    return cv


def _driftglass_ore(cv, m, inner, cracked, spots):
    W, H = cv.w, cv.h
    for i, ((sx, sy), pm) in enumerate(spots[: (6 if cracked else 4)]):
        x, y = int(round(sx)) + 1, int(round(sy)) + 1
        if not inner[min(H - 1, y), min(W - 1, x)]:
            continue
        _glass_shard(cv, x, y, 5 + (i % 2) * 2 + (2 if cracked else 0), 3, (-1) ** i * 1.5, see=0.3)
    _glass_shard(cv, 9, 16, 7 if cracked else 5, 3, -2, see=0.3)
    if cracked:
        x0, y0, x1, y1 = bbox(m)
        _glass_shard(cv, 17, y0 + 8, 9, 4, 1, see=0.3)


def _star_iron_ore(cv, m, inner, cracked, spots):
    W, H = cv.w, cv.h
    nzo = vnoise(W, H, 3, seed_of("star_iron", cracked), 2)
    ore = np.zeros((H, W), bool)
    for (sx, sy), pm in spots:
        band = dilate(pm) & inner & ~pm
        if cracked:
            band = dilate(band) & inner & ~pm
        ore |= band & (nzo > 0.3)
    cv.fill(ore, IRON[2])
    cv.fill(ore & shift(~ore, 0, 1), IRON[4])
    cv.fill(ore & shift(~ore, 1, 0) & ~shift(~ore, 0, 1), IRON[5])
    cv.fill(ore & shift(~ore, 0, -1), IRON[1])
    sp = vnoise(W, H, 1, seed_of("star_iron_specks", cracked), 1)
    cv.fill(ore & (sp > (0.72 if cracked else 0.8)), STAR_CRYSTAL[4])
    cv.fill(ore & (sp > 0.93), WHITE_HOT)
    for i, ((sx, sy), pm) in enumerate(spots[: (6 if cracked else 3)]):
        x, y = int(round(sx)) + 1, int(round(sy))
        if inner[min(H - 1, y), min(W - 1, x)]:
            cv.fill(m_rect(W, H, x - 1, y - 1, x + (1 if cracked else 0), y), IRON[3])
            cv.put(x - 1, y - 1, IRON[6])
            cv.put(x, y, STAR_CRYSTAL[5])


def _reg_lantern_vein(pid, stone, ore_fn, debris_c):
    @prop(pid, 36, 28, states=(("full", 1, 0), ("cracked", 1, 0), ("depleted", 1, 0)))
    def _d(state, f, _pid=pid):
        """Driftglass shards bedded in dark rock, or dark star-iron flecked with pale-gold specks."""
        return _lantern_vein(_pid, state, stone, ore_fn, debris_c)
    return _d


_reg_lantern_vein("driftglass_vein", STONE_DARK, _driftglass_ore, DRIFTGLASS[4])
_reg_lantern_vein("star_iron_vein", STONE_DARK, _star_iron_ore, STAR_CRYSTAL[4])
