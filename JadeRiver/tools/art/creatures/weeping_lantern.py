"""Weeping lantern - a haunted paper lantern with a sad painted face and a violet soul
flame inside, crying wax tears (Soul).

View: front-ish, turned a little to the right.  ~44 art px tall from the hanging loop to
the tassel tip on a 64 px art canvas (cell 128).  Flying: the anchor is the lantern's
centre.
Parts, back to front: tassel (swaying), bottom cap, paper globe (lit from inside: a
violet glow and the flame's silhouette show through the paper), bamboo ribs, the painted
face (sad brows, closed weeping eyes, frown, painted tear streaks), top cap and loop,
wax drips on the rim and falling tears.
Windup: the flame flares up out of the top; attack: a flare burst (hit on frame 1);
death: the paper crumples, the flame gutters out and it drops, fading.
"""
import math

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "weeping_lantern",
    "cell": 128,
    "anchor": [64, 64],
    "flying": True,
    "hit_frame": 1,
}

# ---- palette: violet-lit paper, lacquered caps, red tassel, violet soul flame --------------
PAPER = px.material("lantern_paper", "#f1e4ff", "#d3bdf0", "#a283d2", "#6c50a2", outline="#1b1128",
                    thresholds=(0.86, 0.5, 0.15))
PAPER_DARK = px.material("lantern_paper_dark", "#b9b0b8", "#8f8590", "#675f6c", "#453f4c", outline="#141018")
GLOW = px.material("lantern_glow", "#ffffff", "#fbf3ff", "#ecdcfb", "#dcc6f6", outline="#1b1128")
INNER_FLAME = (px.rgb("#a47fe0"), px.rgb("#d4bcf8"), px.rgb("#ffffff"))
CAP = px.material("lantern_cap", "#8a4a46", "#5c2e33", "#3f1f27", "#29141b", outline="#10070b")
TASSEL = px.material("lantern_tassel", "#ff8a78", "#d4474b", "#9c2f3d", "#661f30", outline="#1f0a10")
WAX = px.material("wax", "#ffffff", "#efe6f7", "#cbbde0", "#9c8cb8", outline="#2a1d3a")
FLAME = (px.rgb("#7d55c8"), px.rgb("#b28cf0"), px.rgb("#f3e8ff"))
INK = px.rgb("#2a1838")
TEAR = px.rgb("#8e6bd0")

# ---- poses ------------------------------------------------------------------------------------
# bx, by   offset       tilt  sway (deg)        swing  tassel swing (deg)     ph  flame flicker
# flare    flame height out of the top (px, 0 = hidden)      glow  inner glow strength 0..2
# drip     falling tear position 0..1 (None = none)          squash  crumple 0..1   lit  flame on
# burst    flare-burst life (None = off)                      face  sad|squeeze
DEFAULTS = dict(bx=0, by=0, tilt=0, swing=0, ph=0.0, flare=0.0, glow=1, drip=None, squash=0.0, lit=True,
                burst=None, face="sad", fade=1.0, crumple=0.0)

POSE = px.poses(DEFAULTS, {
    "idle": [
        dict(by=0, swing=4, ph=0.0, drip=0.1),
        dict(by=-1, swing=2, ph=1.6, drip=0.35),
        dict(by=-1, swing=-3, ph=3.2, drip=0.6),
        dict(by=0, swing=-4, ph=4.8, drip=0.85),
    ],
    "walk": [  # drifts along, swaying, tassel trailing
        dict(tilt=-3, swing=10, ph=0.0, drip=0.1),
        dict(tilt=-5, swing=12, ph=1.1, by=-1, drip=0.3),
        dict(tilt=-4, swing=9, ph=2.2, by=-1, drip=0.5),
        dict(tilt=-2, swing=6, ph=3.3, drip=0.7),
        dict(tilt=-3, swing=8, ph=4.4, by=1, drip=0.9),
        dict(tilt=-4, swing=11, ph=5.5, by=1),
    ],
    "windup": [  # the soul flame flares up out of the top, the paper blazes - held
        dict(flare=5.0, glow=2, ph=0.8, by=-1, swing=-4, tilt=4),
        dict(flare=9.0, glow=2, ph=2.0, by=-2, swing=-6, tilt=6),
        dict(flare=11.0, glow=2, ph=3.3, by=-2, swing=-7, tilt=6),
    ],
    "attack": [  # flare burst forward: hit on frame 1
        dict(flare=12.0, glow=2, ph=4.6, bx=1, tilt=-4, swing=8, burst=0.2),
        dict(flare=6.0, glow=2, ph=5.8, bx=3, tilt=-8, swing=14, burst=0.5),
        dict(flare=3.0, glow=1, ph=7.0, bx=2, tilt=-5, swing=10, burst=0.85),
        dict(flare=0.0, glow=1, ph=8.2, bx=1, tilt=-2, swing=4),
    ],
    "hurt": [
        dict(bx=-3, by=-1, tilt=14, swing=-14, face="squeeze", squash=0.3, glow=0, ph=1.0),
        dict(bx=-2, tilt=8, swing=-8, face="squeeze", squash=0.12, glow=1, ph=2.0),
    ],
    "death": [  # paper crumples, the flame gutters out, it drops and fades
        dict(bx=-3, by=-1, tilt=14, swing=-14, face="squeeze", squash=0.3, glow=0, ph=1.0),
        dict(bx=-3, by=3, tilt=22, swing=-18, face="squeeze", crumple=0.4, glow=0, ph=2.0, flare=2.0),
        dict(bx=-3, by=6, tilt=30, swing=-10, face="squeeze", crumple=0.75, lit=False, ph=3.0),
        dict(bx=-3, by=8, tilt=36, swing=-4, face="squeeze", crumple=1.0, lit=False, fade=0.6),
        dict(bx=-3, by=9, tilt=38, swing=0, face="squeeze", crumple=1.0, lit=False, fade=0.3),
    ],
})

RX, RY = 10.5, 12.5


def _globe_pts(C, cr, n=28):
    """Paper outline; ``cr`` crumples it into a dented, jagged, squashed shape."""
    pts = []
    for i in range(n):
        a = 360.0 * i / n
        r = 1.0 - cr * (0.18 * (i % 3 == 0) + 0.1 * math.sin(i * 1.7))
        x = RX * (1 + 0.15 * cr) * math.cos(math.radians(a)) * r
        y = -RY * (1 - 0.35 * cr) * math.sin(math.radians(a)) * r
        pts.append((C[0] + x, C[1] + y + cr * 4.0))
    return pts


def _face(cv, C, p):
    fx0, fy0 = round(C[0]) + 2, round(C[1]) - 1  # the face looks a little to the right
    pix = lambda pts, col: cv.pixels([(fx0 + x, fy0 + y) for x, y in pts], col, decal=True, name="face")
    if p.face == "squeeze":
        pix([(-6, -1), (-5, 0), (-6, 1), (-4, 0)], INK)
        pix([(2, -1), (1, 0), (2, 1), (0, 0)], INK)
        pix([(-3, 4), (-2, 3), (-1, 3), (0, 4)], INK)
        return
    # sad brows: high at the inner ends
    pix([(-7, -4), (-6, -5), (-5, -5), (-4, -6)], INK)
    pix([(0, -6), (1, -5), (2, -5), (3, -4)], INK)
    # closed weeping eyes (upward arcs)
    pix([(-7, -1), (-6, -2), (-5, -2), (-4, -1)], INK)
    pix([(0, -1), (1, -2), (2, -2), (3, -1)], INK)
    # painted tear streaks
    pix([(-6, 0), (-6, 1), (-6, 2), (-5, 3)], TEAR)
    pix([(2, 0), (2, 1), (2, 2), (3, 3), (3, 4)], TEAR)
    # frown
    pix([(-3, 5), (-2, 4), (-1, 4), (0, 5)], INK)


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    C = (cv.gx + p.bx, cv.gy - 2 + p.by)
    cr = max(p.crumple, p.squash * 0.5)
    fx_back = cv.layer(above=False, outline=True)
    with cv.xform(px.rotate(p.tilt, C)):
        # tassel: cord, knot and strands swinging from the bottom cap
        bottom = (C[0], C[1] + RY * (1 - 0.35 * cr) + cr * 4.0 + 1.0)
        with cv.xform(px.rotate(p.swing, bottom)):
            cv.line((round(bottom[0]), round(bottom[1])), (round(bottom[0]), round(bottom[1]) + 3), TASSEL.shadow,
                    name="tassel")
            k = (bottom[0], bottom[1] + 4.5)
            cv.circle(k[0], k[1], 1.6, TASSEL, name="tassel")
            cv.polygon([(k[0] - 1.6, k[1] + 1.0), (k[0] + 1.6, k[1] + 1.0), (k[0] + 2.4, k[1] + 9.0),
                        (k[0] - 2.4, k[1] + 9.0)], TASSEL, shade="two", name="tassel")
            for dx in (-1.0, 1.0):
                cv.line((round(k[0] + dx), round(k[1] + 3)), (round(k[0] + dx * 1.6), round(k[1] + 8)),
                        TASSEL.deep, band=None, decal=True, clip="tassel", name="tassel")
        # bottom cap
        cv.ellipse(C[0], bottom[1] - 1.0, 5.0, 1.8, CAP, shade="two", name="cap")
        # paper globe
        mat = PAPER if p.lit else PAPER_DARK
        cv.polygon(_globe_pts(C, cr), mat, name="paper", bulge=1.0)
        paper_m = cv.mask_of("paper")
        if p.lit and p.glow > 0:  # the flame lights the paper from inside
            g = 3.5 + 2.5 * p.glow
            cv.ellipse(C[0] - 0.5, C[1] + 3.0 + cr * 3, g * 0.9, g * 1.1, GLOW, shade="soft", decal=True, clip="paper")
            # the flame's silhouette through the paper
            hc.flame(cv, (C[0] - 0.5, C[1] + 8.0 + cr * 3), 6.0 + 2.0 * p.glow, 2.4 + 0.6 * p.glow, p.ph,
                     INNER_FLAME, name="inner_flame")
            hc.erase_mask(cv, cv.mask_of("inner_flame") & ~paper_m)  # keep it inside the globe
        # bamboo ribs
        for k2 in (-8.0, -3.5, 1.5, 6.5):
            y = C[1] + k2 * (1 - 0.35 * cr) + cr * 4.0
            half = RX * math.sqrt(max(0.0, 1 - (k2 / RY) ** 2)) * (1 + 0.15 * cr)
            pts = [(C[0] - half + 0.8, y), (C[0], y + 1.2), (C[0] + half - 0.8, y)]
            for a, b in zip(pts, pts[1:]):
                cv.line((round(a[0]), round(a[1])), (round(b[0]), round(b[1])), mat.step(1), band=None, decal=True,
                        clip=["paper", "inner_flame"], name="paper")
        if cr < 0.9:
            _face(cv, (C[0], C[1] + cr * 3), p)
        # top cap + hanging loop
        top = (C[0], C[1] - RY * (1 - 0.35 * cr) + cr * 4.0)
        cv.ellipse(top[0], top[1] + 0.5, 4.6, 1.9, CAP, shade="two", name="cap")
        cv.limb([(top[0] - 1.6, top[1] - 1.0), (top[0] - 1.4, top[1] - 4.0), (top[0] + 1.4, top[1] - 4.0),
                 (top[0] + 1.6, top[1] - 1.0)], 0.6, CAP, shade="two", name="loop")
        # wax drips hanging from the rim, one on the left cheek
        for (dx, ln) in ((-5.0, 2.0), (3.5, 3.0)):
            b = (C[0] + dx, bottom[1] - 2.0)
            cv.limb([b, (b[0], b[1] + ln)], [1.0, 0.8], WAX, shade="two", name="wax")
        if p.flare > 0 and p.lit:  # the soul flame rising out of the top opening
            hc.flame(cv, (top[0], top[1] - 0.5), p.flare, 2.4 + p.flare * 0.12, p.ph, FLAME, name="flame")
    if p.drip is not None and p.lit:  # a falling wax tear
        d = p.drip
        y = C[1] + RY + 2 + d * 14
        fx_back.ellipse(C[0] + 3.5 + p.bx * 0, y, 0.9, 1.3, WAX, shade="soft", name="drop")
    if p.burst is not None:  # jets of soul fire burst out of the lantern's face
        t = p.burst
        E = (C[0] + RX - 1, C[1] + 1)
        ring = cv.layer(above=False, outline=False)
        px.glow_ring(ring, C[0], C[1] + 1, RX + 2 + 6 * t, hc.SOUL_GLOW, thickness=1.0,
                     inner=px.SOUL_VIOLET if t < 0.7 else None)
        jets = cv.layer(above=True, outline=True)
        for k, (dy, ln, ang) in enumerate(((-5, 10, 14), (0, 13, 0), (5, 10, -14))):
            if t > 0.9:
                break
            base = (E[0] + 1 + 4 * t, E[1] + dy)
            L = ln * (1.0 - 0.35 * t)
            pts = [base]
            for j in range(1, 4):
                q = px.polar(base, ang, L * j / 3)
                pts.append((q[0], q[1] + math.sin(t * 9 + k * 2 + j * 1.8) * 1.2 * j / 3))
            for (mat, sc) in ((FLAME[0], 1.0), (FLAME[1], 0.62), (FLAME[2], 0.3)):
                jets.limb(pts, [2.6 * sc + 0.4, 2.0 * sc + 0.3, 1.2 * sc + 0.2, 0.5], px.flat(mat), shade="flat",
                          name="burst")
        if 0.3 < t < 0.7:
            fx = cv.layer(above=True, outline=False)
            px.impact(fx, E[0] + 12, E[1], size=3, color=hc.SOUL_GLOW, core=px.GLINT)
