"""V10a Insect Netting gathering nodes: eight insect swarms. Each is a small scene rooted on the ground (a
reed clump, a willow stump, a rotten log, a mulberry shrub, a grass tuft, a frosted rock, a desert shrub,
a star-coral stem) with its insects clustered on and around it, frozen mid-flight with a few motion
strokes; the engine may add moving particles on top. Same layout as the herb patches (bottom-centre
anchor on the ground line, ground=2, about the willow_moss_patch footprint), one static `idle` frame.

Insects are tiny hand-drawn pixel maps (`_bug`) a few art px long. Bugs sitting on the plant get a local
dark edge (`_ink`) so they stay readable against bark and leaves; flying bodies are drawn before the
outline so they get inked with the silhouette, while wings, motion strokes, glows and sparks go on after
it so they never get inked."""
from __future__ import annotations

import numpy as np

from defs_expanse import DUNE, _spline, tube
from defs_lantern import STAR_HALO, _glass_shard
from palette import *  # noqa: F401,F403
from parts import blob_mask, grass_tuft, ground_shadow, moss_top, rock, soil_mound
from pixlib import (Canvas, bottom_edge, dilate, erode, glow, grid, hexc, left_edge, m_curve, m_ellipse, m_line,
                    m_poly, m_rect, outline, rng, seed_of, shade, shift, top_edge, vnoise)
from registry import prop

SWARM_W = 32
WING = hexc("#e4f0e8")  # pale wing ghost shared by most flyers


# ------------------------------------------------------------------ shared helpers
def _stamp(cv, x, y, rows, pal, flip=False):
    """Stamp a tiny hand-drawn pixel map with its top-left at (x, y). rows: strings, '.' = empty; pal maps
    a character to an RGB colour or (RGB, alpha). flip mirrors it left-right. Returns the opaque mask."""
    m = cv.empty()
    n = max(len(r) for r in rows)
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            c = pal[ch]
            a = 1.0
            if len(c) == 2:
                c, a = c
            px, py = x + (n - 1 - i if flip else i), y + j
            if 0 <= px < cv.w and 0 <= py < cv.h:
                cv.put(px, py, c, a)
                if a >= 1.0:
                    m[py, px] = True
    return m


def _rot_left(rows):
    """A pixel map turned 90 degrees counter-clockwise (a head-up bug becomes head-left)."""
    w = max(len(r) for r in rows)
    rows = [r.ljust(w, ".") for r in rows]
    return tuple("".join(rows[j][w - 1 - i] for j in range(len(rows))) for i in range(w))


def _ink(cv, src, keep, t=0.6):
    """Local outline: darken the already painted pixels just outside mask src (but not those in keep)
    toward ink, so a bug sitting on bark or leaves keeps a readable edge inside the prop's silhouette."""
    ring = dilate(src) & ~keep & cv.solid
    cv.rgb[ring] = cv.rgb[ring] * (1 - t) + np.array(INK, float) * t
    return ring


def _bug(cv, x, y, rows, pal, flip=False, ink=True, bare="l"):
    """Stamp an insect map and ink its edge where it overlaps the plant. Pixels drawn with a character in
    `bare` (the legs) are not inked around, so they still stick out as dark spikes."""
    m = _stamp(cv, x, y, rows, pal, flip)
    if ink:
        body = _stamp(Canvas(cv.w, cv.h), x, y, [r.translate({ord(c): "." for c in bare}) for r in rows],
                      {k: v for k, v in pal.items() if k not in bare}, flip)
        _ink(cv, body, m)
    return m


def _path_px(pts):
    """Pixel-perfect 1 px path through pts (no doubled L-corners), in order."""
    out = []
    for x, y in _spline(pts, 0.3):
        p = (int(round(x)), int(round(y)))
        if not out or out[-1] != p:
            out.append(p)
    clean = []
    for i, p in enumerate(out):
        if 0 < i < len(out) - 1 and clean:
            a, b = clean[-1], out[i + 1]
            if abs(a[0] - b[0]) == 1 and abs(a[1] - b[1]) == 1:
                continue
        clean.append(p)
    return clean


def _streak(cv, pts, c, a0=0.6, a1=0.12, dotted=False, over=False):
    """A motion stroke along pts, starting at the insect and running back along its path: 1 px wide,
    fading from alpha a0 to a1. dotted leaves every other pixel out; over=False skips opaque pixels."""
    px = _path_px(pts)
    n = len(px)
    for k, (x, y) in enumerate(px):
        if dotted and k % 2:
            continue
        if not (0 <= x < cv.w and 0 <= y < cv.h):
            continue
        if not over and cv.a[y, x] > 0.999:
            continue
        cv.put(x, y, c, a0 + (a1 - a0) * k / max(1, n - 1))


def _halo(cv, x, y, c, r=2.4, inner=0.42, outer=0.15):
    """Soft glow around a point of light: a bright plus, then a faint disc (flat alpha steps)."""
    W, H = cv.w, cv.h
    cv.light(m_rect(W, H, x - 1, y, x + 1, y) | m_rect(W, H, x, y - 1, x, y + 1), c, inner)
    cv.light(m_ellipse(W, H, x, y, r, r), c, outer)


def _blade(cv, x, by, tx, ty, c, wide_to=None, bend=0.25):
    """A grass or reed blade from (x, by) to its tip (tx, ty), 2 px wide below row `wide_to`."""
    W, H = cv.w, cv.h
    pts = [(x, by), (x + (tx - x) * bend, (by + ty) / 2 + 1), (tx, ty)]
    m = m_curve(W, H, pts)
    if wide_to is not None:
        m |= shift(m, 1, 0) & (grid(W, H)[1] >= wide_to)
    cv.fill(m, c)
    return m


# ------------------------------------------------------------------ glowfly swarm (valley, dusk)
DUSK_REED = ramp("#10231c", "#1b3a26", "#2a5530", "#3f7336", "#5e8c3c", "#8fae4c")
DUSK_RIM = hexc("#c8904a")
LAMP = ramp("#6f8a1c", "#a8c42a", "#d6ec4a", "#f2ff8c", "#fbffd6")
FF_BODY = hexc("#2b2616")


def _firefly(cv, x, y, d=1, big=False):
    """A glowfly heading d (+1 right, -1 left): dark head, lit tail (2 px when near), pale wing ghost."""
    _halo(cv, x, y, LAMP[2], r=2.8 if big else 2.2, inner=0.45 if big else 0.36, outer=0.16 if big else 0.12)
    cv.put(x + d, y, FF_BODY)
    cv.put(x, y, LAMP[4] if big else LAMP[3])
    if big:
        cv.put(x - d, y, LAMP[3])
        cv.put(x + d, y - 1, WING, 0.6)
        cv.put(x, y - 1, WING, 0.4)
    else:
        cv.put(x + d, y - 1, WING, 0.45)


@prop("glowfly_swarm", SWARM_W, 32)
def glowfly_swarm(state, f):
    """A clump of dusk reeds rimmed gold by the low sun, with a dozen glowflies hanging in a loose cloud
    over the tips, a few trailing short streaks of light."""
    W, H = SWARM_W, 32
    cv = Canvas(W, H)
    yy = grid(W, H)[1]
    gy = 29
    ground_shadow(cv, 16, 30, 12, 1.4)
    blades = [(10, 18, 5), (12, 13, 8), (13, 19, 11), (15, 11, 13), (17, 16, 18), (18, 12, 21), (20, 18, 24),
              (21, 14, 27), (14, 21, 9), (19, 21, 25)]
    for i, (bx, ty, tx) in enumerate(blades):
        m = _blade(cv, bx, gy, tx, ty, DUSK_REED[2 + i % 3], wide_to=gy - 6)
        if tx < bx:
            cv.fill(m & (yy < ty + 4), DUSK_RIM)
        else:
            cv.fill(m & (yy < ty + 2), DUSK_REED[5])
    for (bx, ty, lean) in ((14, 9, -1), (19, 10, 1)):
        cv.fill(m_line(W, H, [(bx, gy), (bx + lean, ty + 5)]), FOLIAGE_DRY[2])
        cx = bx + lean
        head = m_rect(W, H, cx, ty, cx + 1, ty + 4)
        cv.fill(head, WOOD[3])
        cv.fill(head & (grid(W, H)[0] == cx), WOOD[4])
        cv.put(cx, ty, DUSK_RIM)
        cv.put(cx + 1, ty + 4, WOOD[2])
        cv.put(cx, ty - 1, FOLIAGE_DRY[3])
    soil_mound(cv, 16, gy, 9, 2.4, "gf_mud", pal=MUD, moss=0.35)
    grass_tuft(cv, 7, gy, "gf_t1", h=4, n=3, pal=DUSK_REED)
    grass_tuft(cv, 25, gy, "gf_t2", h=3, n=2, pal=DUSK_REED)
    outline(cv)
    glow(cv, 16, 10, 15, 10, LAMP[2], steps=((1.0, 0.05),))
    trails = ([(5, 8), (3, 10), (4, 13), (7, 12)], [(24, 4), (27, 2), (29, 5), (27, 7)], [(3, 18), (1, 21), (3, 23)],
              [(18, 3), (15, 1), (12, 2)])
    for pts in trails:
        _streak(cv, pts, LAMP[2], 0.5, 0.1, dotted=True, over=True)
    near = [(5, 8, 1), (24, 4, -1), (18, 3, 1), (11, 10, -1)]
    far = [(9, 3, 1), (14, 7, 1), (21, 9, -1), (28, 11, -1), (3, 18, 1), (27, 17, -1), (8, 14, 1), (23, 13, 1)]
    for (x, y, d) in far:
        _firefly(cv, x, y, d)
    for (x, y, d) in near:
        _firefly(cv, x, y, d, big=True)
    return cv


# ------------------------------------------------------------------ reed cicada swarm (valley)
BARK = ramp("#1a1612", "#2e2720", "#473d31", "#625443", "#7f6e57", "#a08c6e")
CUT_WOOD = ramp("#5e4630", "#86653f", "#ab8a5a", "#cdb07c", "#e6cf9c")
CICADA = ramp("#1c2010", "#343a18", "#525624", "#737430", "#96963e", "#bdb865")
CIC_WING = hexc("#d4e2c4")
CIC_VEIN = hexc("#8f9e7c")
CIC_GLASS = hexc("#b8c6a2")  # folded wings over bark: glassy, the bark darkening them
CIC_GLASS_VEIN = hexc("#5e6a4c")
CIC_EYE = hexc("#d9b45a")
CICADA_PAL = {"e": CIC_EYE, "H": CICADA[2], "h": CICADA[4], "B": CICADA[3], "b": CICADA[1], "w": CIC_WING,
              "v": CIC_VEIN, "l": CICADA[0]}
CICADA_CLING = ("eHhHe", "hBBBh", "wBbBw", "wvbvw", "wvbvw", ".wbw.", "..v..")
CICADA_CLING_PAL = CICADA_PAL | {"w": CIC_GLASS, "v": CIC_GLASS_VEIN, "b": CICADA[2]}
CICADA_FLY = (".bBBHe", "bbBBh.", "..l.l.")
CICADA_FLY_WING = (".ww..", "wwvw.", "wvw..")


@prop("reed_cicada_swarm", SWARM_W, 30)
def reed_cicada_swarm(state, f):
    """A short willow stump, its cut face ringed and a willow whip sprouting from it, with brown-green
    cicadas clinging to the bark and two more buzzing off it."""
    W, H = SWARM_W, 30
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 27
    ground_shadow(cv, 16, 28, 13, 1.4)
    whip = [(20, 14), (23, 7), (27, 6), (29, 10)]
    cv.fill(m_curve(W, H, whip), WOOD[3])
    for k, (x, y) in enumerate(_path_px(whip)[4::2]):
        cv.put(x + 1, y + 1, LEAF[4] if k % 2 else LEAF[3])
        cv.put(x + 1, y + 2, LEAF[2])
    sprout = [(11, 14), (9, 9), (6, 9)]
    cv.fill(m_curve(W, H, sprout), WOOD[3])
    for (x, y, c) in ((8, 10, LEAF[4]), (7, 11, LEAF[3]), (10, 11, LEAF[3]), (6, 10, LEAF[2])):
        cv.put(x, y, c)
    trunk = m_rect(W, H, 10, 14, 21, gy)
    trunk |= m_poly(W, H, [(6, gy), (10, gy - 6), (11, gy)]) | m_poly(W, H, [(25, gy), (21, gy - 6), (20, gy)])
    trunk |= m_poly(W, H, [(3, gy), (7, gy - 2), (8, gy)])
    nz = vnoise(W, H, 2, seed_of("cic_bark"), 2)
    shade(cv, trunk, BARK, contour=True, mode="cyl", base=0.5, gain=1.1, noise=nz, namp=0.25)
    for x in (12, 15, 19):
        fur = trunk & erode(trunk) & (xx == x + ((yy // 5) % 2)) & (yy > 16) & (nz > 0.35)
        cv.fill(fur, BARK[1])
    top = m_ellipse(W, H, 15.5, 14, 5.8, 1.8)
    cv.fill(top, CUT_WOOD[3])
    cv.fill(top & ~erode(top), CUT_WOOD[1])
    cv.fill(m_ellipse(W, H, 15.5, 14, 3.2, 0.9) & ~m_ellipse(W, H, 15.5, 14, 2, 0.5), CUT_WOOD[2])
    cv.put(15, 14, CUT_WOOD[1])
    cv.fill(top_edge(top) & (xx < 15), CUT_WOOD[4])
    moss_top(cv, trunk & (yy > gy - 5), "cic_moss", 0.4, thick=1, drips=False)
    grass_tuft(cv, 4, gy, "cic_g", h=3, n=2)
    grass_tuft(cv, 27, gy, "cic_g2", h=4, n=3)
    for (x, y) in ((11, 16), (16, 19), (25, 11)):
        _bug(cv, x, y, CICADA_CLING, CICADA_CLING_PAL)
    fly = [(17, 3, False), (1, 6, False)]
    for (x, y, fl) in fly:
        _stamp(cv, x, y, CICADA_FLY, CICADA_PAL, fl)
    outline(cv)
    for (x, y, fl) in fly:
        _stamp(cv, x + (0 if fl else 1), y - 3, CICADA_FLY_WING, {"w": (CIC_WING, 0.85), "v": (CIC_VEIN, 0.85)}, fl)
        d = -1 if fl else 1
        tail = x + (5 if fl else 0)
        _streak(cv, [(tail - d, y + 1), (tail - d * 4, y + 3), (tail - d * 7, y + 2)], PAPER, 0.5, 0.1)
        _streak(cv, [(tail - d, y - 1), (tail - d * 3, y - 2)], PAPER, 0.4, 0.15)
    return cv


# ------------------------------------------------------------------ jade scarab swarm (valley, bamboo grove)
ROTWOOD = ramp("#1f1c17", "#353027", "#514a3c", "#6d6450", "#8a7f66", "#a89c80", "#c4b99c")
PUNK = ramp("#4a2c18", "#6e4424", "#935f34", "#b57d48", "#d09c62")
SCARAB_PAL = {"k": hexc("#0b2a28"), "h": hexc("#0f3a38"), "l": hexc("#101818"), "P": JADE_R[3], "p": JADE_R[5],
              "H": JADE_R[5], "M": JADE_R[4], "m": JADE_R[3], "s": JADE_R[2], "S": JADE_R[2], "E": JADE_R[4],
              "e": JADE_R[2], "G": JADE_R[6]}
# top view, head up: antennae, head, pronotum, the split wing cases, six legs
SCARAB_TOP = ("..k.k..", "...h...", "l.PpP.l", ".GMMms.", "lHMkmsl", ".MMkms.", "l.mks.l", "..sss..")
# side view, walking
SCARAB_SIDE = ("..GMm...", ".HMmmSh.", "hMmmmSs.", ".l.l.l..", "l..l..l.")
SCARAB_FLY = ("..khk..", "E.PpP.E", "EE.m.EE", ".E.s.E.")
SCARAB_FLY_WING = ("ww.......ww", ".ww.....ww.")


@prop("jade_scarab_swarm", SWARM_W, 26)
def jade_scarab_swarm(state, f):
    """A mossy fallen log gone soft and pale, its bark split open on punk wood, with jade-green scarabs
    crawling over it (two walking the top, two on its flank) and one lifting off on open wing cases.
    The log is kept light so the beetles' dark legs and heads show without an ink edge."""
    W, H = SWARM_W, 26
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 23
    ground_shadow(cv, 16, 24, 14, 1.4)
    log = m_poly(W, H, [(3, gy), (2, 18), (4, 14), (18, 13), (25, 14), (27, 13), (28, 16), (27, 17), (29, 19),
                        (28, gy)])
    nz = vnoise(W, H, 3, seed_of("js_log"), 2)
    shade(cv, log, ROTWOOD, contour=True, mode="cylh", base=0.62, gain=0.8, noise=nz, namp=0.3)
    grain = log & erode(log) & ((yy * 5 + xx // 5) % 3 == 0) & (nz > 0.55)
    cv.fill(grain, ROTWOOD[2])
    punk = m_poly(W, H, [(15, 16), (20, 15), (25, 16), (24, 21), (16, 21)]) & erode(log)
    cv.fill(punk, PUNK[3])
    cv.fill(punk & (nz > 0.6), PUNK[2])
    cv.fill(top_edge(punk), PUNK[4])
    cv.fill(bottom_edge(punk), PUNK[1])
    end = m_ellipse(W, H, 4, 18.5, 2.2, 4) & log
    cv.fill(end, PUNK[2])
    cv.fill(m_ellipse(W, H, 4.3, 19, 1.2, 2.4), ROTWOOD[0])
    cv.fill(left_edge(end), ROTWOOD[3])
    moss_top(cv, log, "js_moss", 0.4, thick=2)
    grass_tuft(cv, 1, gy, "js_g1", h=3, n=2)
    grass_tuft(cv, 30, gy, "js_g2", h=4, n=2)
    _bug(cv, 7, 14, SCARAB_TOP, SCARAB_PAL, ink=False)
    _bug(cv, 16, 15, _rot_left(SCARAB_TOP), SCARAB_PAL, ink=False)
    _bug(cv, 9, 11, SCARAB_SIDE, SCARAB_PAL, ink=False)
    _bug(cv, 20, 11, SCARAB_SIDE, SCARAB_PAL, flip=True, ink=False)
    _stamp(cv, 23, 1, SCARAB_FLY, SCARAB_PAL)
    outline(cv)
    _stamp(cv, 21, 1, SCARAB_FLY_WING, {"w": (WING, 0.6)})
    _streak(cv, [(26, 6), (25, 8), (27, 10)], PAPER, 0.5, 0.12)
    _streak(cv, [(22, 4), (20, 6)], PAPER, 0.4, 0.12)
    _streak(cv, [(30, 4), (31, 6)], PAPER, 0.4, 0.12)
    return cv


# ------------------------------------------------------------------ silk moth swarm (Mist Peak)
MULBERRY = ramp("#0c2220", "#143a30", "#1f543c", "#2f6f48", "#4a8e58", "#7cb274")
CREAM = ramp("#6e6250", "#a39478", "#cdbf9c", "#e9dfc2", "#faf4e2")
MOTH_PAL = {"W": CREAM[4], "w": CREAM[3], "s": CREAM[2], "h": hexc("#9a8062"), "b": hexc("#7a6248"),
            "a": hexc("#8a7458")}
MOTH_REST = (".a.a.", "WWhWW", "wsbsw", ".w.w.")
MOTH_FLY = ("W...W", "wW.Ww")
SILK = ramp("#8a8a86", "#c2c4bc", "#e6e8e0", "#fbfbf6")


@prop("silk_moth_swarm", SWARM_W, 30)
def silk_moth_swarm(state, f):
    """A mulberry shrub in the mist with pale cream silk moths resting on its leaves and fluttering
    round it, and silk cocoons hanging on threads under the branches."""
    W, H = SWARM_W, 30
    cv = Canvas(W, H)
    yy = grid(W, H)[1]
    gy = 27
    ground_shadow(cv, 16, 28, 12, 1.4)
    for pts in (((16, gy), (15, 20), (10, 15)), ((16, gy), (17, 19), (22, 14)), ((15, 22), (14, 14))):
        cv.fill(tube(W, H, list(pts), 0.9, 0.6), WOOD[2])
    bush = (blob_mask(W, H, 10, 16, 6.5, 4.8, "sm_b1", 0.2) | blob_mask(W, H, 21, 15, 6.5, 5, "sm_b2", 0.2)
            | blob_mask(W, H, 15, 10, 7, 5, "sm_b3", 0.2) | blob_mask(W, H, 25, 20, 3.5, 3, "sm_b4", 0.2))
    bush &= yy <= gy - 4
    nz = vnoise(W, H, 2, seed_of("sm_leaf"), 2)
    shade(cv, bush, MULBERRY, contour=True, R=3, base=0.45, gain=1.5, noise=nz, namp=0.5)
    for (lx, ly) in ((5, 14), (9, 10), (14, 5), (20, 8), (26, 12), (28, 18), (4, 19)):
        cv.put(lx, ly, MULBERRY[4])
    for (bx, by) in ((8, 18), (19, 19), (24, 12)):
        cv.fill(m_rect(W, H, bx, by, bx + 1, by + 1), hexc("#3a1830"))
        cv.put(bx, by, hexc("#7a3a60"))
    soil_mound(cv, 16, gy, 7, 2, "sm_soil", pal=EARTH, moss=0.3)
    for (x, y, fl) in ((5, 11, False), (17, 6, False), (20, 15, True)):
        _bug(cv, x, y, MOTH_REST, MOTH_PAL, fl)
    for (x, y) in ((10, 21), (22, 20), (14, 16)):
        _bug(cv, x, y, ("c.", "Cc", "Cs", ".s"), {"C": SILK[3], "c": SILK[2], "s": SILK[1]})
    flies = [(1, 4, False), (26, 2, True), (27, 23, False), (0, 22, True)]
    for (x, y, fl) in flies:
        _stamp(cv, x + 2, y + 2, ("b",), MOTH_PAL)
    outline(cv)
    for (x, y, fl) in flies:
        _stamp(cv, x, y, MOTH_FLY, {"W": (CREAM[4], 0.95), "w": (CREAM[3], 0.9)}, fl)
        d = -1 if fl else 1
        _streak(cv, [(x + 2 - d * 3, y + 3), (x + 2 - d * 5, y + 1), (x + 2 - d * 7, y + 3), (x + 2 - d * 9, y + 1)],
                PAPER, 0.45, 0.1)
    for (x0, y0, x1, y1) in ((9, 20, 5, 22), (23, 19, 27, 21)):
        _streak(cv, [(x0, y0), ((x0 + x1) / 2, y1 + 1), (x1, y1)], SILK[3], 0.5, 0.3)
    for i in range(3):
        y = gy - 1 - i * 2
        x0 = 3 + (i * 7) % 11
        cv.fill(m_rect(W, H, x0, y, x0 + 5, y) & ~cv.solid, MIST_BLUE, 0.35)
        cv.fill(m_rect(W, H, x0 + 16, y + 1, x0 + 20, y + 1) & ~cv.solid, MIST_BLUE, 0.3)
    return cv


# ------------------------------------------------------------------ thunder mantis swarm (Azure Expanse)
STORM_GRASS = ramp("#0e1a22", "#152a33", "#1e3c42", "#2a5052", "#3b6863", "#5a8a7e", "#9dbfb2")
MANTIS = ramp("#171638", "#262a62", "#3a44a0", "#5a6ad0", "#8898ee", "#bccaf8", "#eef2ff")
MANTIS_VIOLET = hexc("#6c5ad0")
MANTIS_PAL = {"E": MANTIS[6], "h": MANTIS[5], "t": MANTIS[4], "f": MANTIS[6], "W": MANTIS_VIOLET, "a": MANTIS[3],
              "l": MANTIS[2]}
MANTIS_PERCH = ("hE...", ".t...", "ft...", "f.t..", "ff.W.", "..lWa", "...Wa", "..l.a")
MANTIS_PRAY = (".hE..", "..t..", "f.t..", "fft..", "..tW.", "..lWa", "..Wa.", ".l.a.", "...a.")
MANTIS_FLY = ("aaaWtttEh", "....f.f..")
MANTIS_WING = ("...W..W.", "..WW.WW.", ".WWwWW..")
SPARK = hexc("#9ff4ff")


def _spark(cv, x, y, big=False):
    """A tiny electric crackle: a white-hot kink with cyan ends."""
    cv.put(x, y, WHITE_HOT)
    cv.put(x - 1, y - 1, SPARK, 0.85)
    cv.put(x + 1, y + 1, SPARK, 0.7)
    if big:
        cv.put(x + 1, y + 2, WHITE_HOT)
        cv.put(x, y + 3, SPARK, 0.6)


@prop("thunder_mantis_swarm", SWARM_W, 34)
def thunder_mantis_swarm(state, f):
    """A tuft of tall storm grass on the plains, silver at the tips, with blue-violet thunder mantises
    praying on the blades, two more in flight, and tiny sparks crackling off their forelegs."""
    W, H = SWARM_W, 34
    cv = Canvas(W, H)
    yy = grid(W, H)[1]
    gy = 31
    ground_shadow(cv, 16, 32, 11, 1.4)
    blades = [(10, 12, 5), (12, 8, 9), (14, 15, 12), (15, 5, 15), (17, 10, 20), (19, 14, 25), (21, 19, 28),
              (11, 20, 6)]
    for i, (bx, ty, tx) in enumerate(blades):
        m = _blade(cv, bx, gy, tx, ty, STORM_GRASS[1 + i % 3], wide_to=gy - 9)
        cv.fill(m & (yy <= ty + 3), STORM_GRASS[5] if i % 2 else STORM_GRASS[4])
    soil_mound(cv, 16, gy, 7, 2, "tm_soil", pal=EARTH, moss=0.0)
    grass_tuft(cv, 8, gy, "tm_g1", h=4, n=3, pal=STORM_GRASS)
    grass_tuft(cv, 24, gy, "tm_g2", h=5, n=3, pal=STORM_GRASS)
    # perched on the outer blade tips, heads and raised forelegs out against the sky
    _bug(cv, 3, 11, MANTIS_PERCH, MANTIS_PAL)
    _bug(cv, 13, 3, MANTIS_PRAY, MANTIS_PAL)
    _bug(cv, 23, 13, MANTIS_PERCH, MANTIS_PAL, flip=True)
    fly = [(22, 3, True), (1, 4, False)]
    for (x, y, fl) in fly:
        _stamp(cv, x, y, MANTIS_FLY, MANTIS_PAL, fl)
    outline(cv)
    for (x, y, fl) in fly:
        _stamp(cv, x + (0 if fl else 1), y - 3, MANTIS_WING, {"W": (hexc("#b09ae8"), 0.75), "w": (hexc("#7d6cc8"), 0.75)},
               fl)
        d = -1 if fl else 1
        tail = x + (8 if fl else 0)
        _streak(cv, [(tail - d, y), (tail - d * 4, y + 2), (tail - d * 7, y + 1)], MIST_BLUE, 0.5, 0.1)
    for (x, y, big) in ((1, 13, True), (29, 15, True), (11, 5, True), (20, 9, False), (7, 20, False)):
        _spark(cv, x, y, big)
    _streak(cv, [(12, 3), (10, 2), (9, 4), (7, 3)], SPARK, 0.9, 0.4, over=True)
    glow(cv, 16, 12, 13, 11, QI_CYAN, steps=((1.0, 0.05),))
    return cv


# ------------------------------------------------------------------ frost cricket swarm (Azure Expanse)
ICE_BUG = ramp("#1c3656", "#2c5a86", "#4a86b8", "#7fb6e0", "#c6e6fa")
SNOW = ramp("#9fb3c8", "#c6d4e2", "#e3ebf2", "#f7fafc")
FROST_GRASS = ramp("#2c3e48", "#4a6270", "#7e98a4", "#a8c0ca", "#d6e6ec")
CRICKET_PAL = {"K": ICE_BUG[4], "F": ICE_BUG[3], "T": ICE_BUG[1], "B": ICE_BUG[2], "b": ICE_BUG[1], "h": ICE_BUG[3],
               "e": ICE_BUG[4], "l": ICE_BUG[0], "a": ICE_BUG[3]}
CRICKET = ("...K....a", "..T.F..a.", ".T..FBBh.", "T..bbBBhe", ".....l.l.")
CRICKET_HOP = ("........aa", "..........", "TTFFbBBBh.", "....bbBhe.", "......l.l.")


@prop("frost_cricket_swarm", SWARM_W, 28)
def frost_cricket_swarm(state, f):
    """A boulder under a snow cap with tufts of snow round its foot, ice-blue frost crickets perched on
    it and one caught mid-hop."""
    W, H = SWARM_W, 28
    cv = Canvas(W, H)
    xx, yy = grid(W, H)
    gy = 25
    ground_shadow(cv, 16, 26, 13, 1.4)
    m = rock(cv, 15, gy, 10, 8, "fc_rock", pal=STONE, R=2, base=0.45, facets=2)
    rock(cv, 25, gy, 4, 3, "fc_rock2", pal=STONE, R=1, facets=1)
    cols = np.where(m.any(axis=0))[0]
    for x in cols:
        ys = np.where(m[:, x])[0]
        d = 2 + (1 if (x * 7) % 5 < 2 else 0) + (1 if 11 <= x <= 17 else 0)
        cap = m & (xx == x) & (yy < ys[0] + d)
        cv.fill(cap, SNOW[3] if x < 16 else SNOW[2])
        cv.fill(cap & (yy == ys[0] + d - 1), SNOW[0])
    # rime: frost feathers along the lit left flank and just under the cap
    face = m & erode(m) & ~dilate(cv.a < 0.5)
    rime = face & (vnoise(W, H, 2, seed_of("fc_rime"), 1) > 0.7) & (xx < 12) & (yy > 13)
    cv.fill(rime, SNOW[1])
    cv.fill(rime & shift(rime, 0, 1), SNOW[3])
    for (cx, rx, ry) in ((5, 4, 2), (22, 5, 2.2), (13, 3, 1.4)):
        mound = m_ellipse(W, H, cx, gy, rx, ry) & (yy <= gy)
        shade(cv, mound, SNOW, R=1, base=0.6, gain=0.6)
    grass_tuft(cv, 2, gy - 1, "fc_g", h=3, n=2, pal=FROST_GRASS)
    grass_tuft(cv, 29, gy, "fc_g2", h=3, n=2, pal=FROST_GRASS)
    _bug(cv, 5, 7, CRICKET, CRICKET_PAL)
    _bug(cv, 14, 12, CRICKET, CRICKET_PAL, flip=True)
    _bug(cv, 20, 19, CRICKET, CRICKET_PAL, flip=True)
    _stamp(cv, 20, 2, CRICKET_HOP, CRICKET_PAL, True)
    outline(cv)
    _streak(cv, [(30, 5), (31, 9), (29, 13), (26, 15)], SNOW[3], 0.6, 0.1, dotted=True)
    cv.put(12, 10, WHITE_HOT)
    return cv


# ------------------------------------------------------------------ ember locust swarm (Sunscar)
DRY_WOOD = ramp("#24170f", "#3d2818", "#5a3e22", "#7a5630", "#9b7342", "#bb9560")
LOCUST = ramp("#3a0e08", "#6a1a0e", "#9c2c14", "#cc4a1e", "#ee7a2c", "#ffb150", "#ffe08a")
LOCUST_PAL = {"K": LOCUST[5], "F": LOCUST[4], "T": LOCUST[1], "W": LOCUST[2], "B": LOCUST[3], "b": LOCUST[2],
              "h": LOCUST[4], "e": LOCUST[6], "l": LOCUST[1]}
LOCUST_PERCH = ("...KF.....", "..T.FWWWh.", ".T.bbbBBhe", "T....l.l..")
LOCUST_LEAP = (".......he", ".....bBh.", "...bbB...", "TFF......", "T........")
LOCUST_WING = ("..WWw", ".WFFw", "WFFf.", ".f...")


@prop("ember_locust_swarm", SWARM_W, 28)
def ember_locust_swarm(state, f):
    """A dry thorn shrub on a drift of Sunscar sand with red-orange ember locusts on its twigs and one
    caught mid-leap, hind wings flared like a flame."""
    W, H = SWARM_W, 28
    cv = Canvas(W, H)
    gy = 25
    ground_shadow(cv, 16, 26, 12, 1.4)
    twigs = [((15, gy), (13, 18), (7, 12), (4, 10)), ((16, gy), (17, 17), (22, 12), (25, 9)),
             ((15, gy - 2), (14, 14), (13, 7)), ((16, 20), (20, 17), (27, 16)), ((15, 20), (10, 18), (4, 18))]
    for i, pts in enumerate(twigs):
        mm = tube(W, H, list(pts), 1.0, 0.5) if i < 2 else m_curve(W, H, list(pts))
        cv.fill(mm, DRY_WOOD[3 if i % 2 else 2])
    g = rng("el_leaves")
    for i in range(16):
        pts = twigs[int(g.integers(len(twigs)))]
        px = _path_px(list(pts))
        x, y = px[int(g.integers(2, len(px)))]
        cv.put(x + int(g.integers(-1, 2)), y - 1, FOLIAGE_DRY[3 + int(g.integers(0, 3))])
    snz = vnoise(W, H, 2, seed_of("el_sand"), 2)
    for (cx, rx, ry, seed) in ((15, 7, 4, "el_sand"), (24, 4, 2.2, "el_sand2"), (7, 3, 1.6, "el_sand3")):
        mound = blob_mask(W, H, cx, gy, rx, ry, seed, 0.12, flat_base=gy)
        shade(cv, mound, DUNE, contour=True, contour_c=DUNE[2], R=3, strength=1.6, base=0.6, gain=0.9, noise=snz,
              namp=0.25)
    _bug(cv, 1, 7, LOCUST_PERCH, LOCUST_PAL)
    _bug(cv, 17, 14, LOCUST_PERCH, LOCUST_PAL, flip=True)
    _bug(cv, 5, 15, LOCUST_PERCH, LOCUST_PAL)
    _stamp(cv, 21, 3, LOCUST_LEAP, LOCUST_PAL)
    outline(cv)
    _stamp(cv, 23, 0, LOCUST_WING, {"W": (LOCUST[4], 0.9), "w": (LOCUST[2], 0.9), "F": (LOCUST[5], 0.9),
                                    "f": (LOCUST[1], 0.9)})
    _streak(cv, [(21, 7), (19, 9), (17, 13)], PAPER, 0.55, 0.1, dotted=True)
    for (x, y) in ((20, 9), (22, 10), (19, 11)):
        cv.put(x, y, FIRE[3], 0.85)
    return cv


# ------------------------------------------------------------------ starwing mote swarm (Lantern Star Field)
STARLIGHT_R = ramp("#140d2e", "#261a56", "#3d2f88", "#5d4fb8", "#8f84dd", "#c9c3f6")
MOTE_GOLD = ramp("#b8862e", "#f0c24e", "#ffe08a", "#fff6d6")


@prop("starwing_mote_swarm", SWARM_W, 32)
def starwing_mote_swarm(state, f):
    """A small star-coral stem grown out of a clump of driftglass, pale-tipped, with starwing motes (tiny
    gold-bodied, cyan-winged insects) glowing round it on trails of star-dust."""
    W, H = SWARM_W, 32
    cv = Canvas(W, H)
    gy = 29
    ground_shadow(cv, 16, 30, 12, 1.4)
    for (x, h, w, lean) in ((10, 9, 3, -2), (22, 11, 4, 2)):
        _glass_shard(cv, x, gy - 2, h, w, lean)
    stems = tube(W, H, [(16, gy - 3), (15, 21), (16, 16)], 1.3, 0.9)
    stems |= tube(W, H, [(15, 21), (11, 17), (10, 12)], 0.9, 0.7)
    stems |= tube(W, H, [(16, 18), (20, 14), (21, 10)], 0.9, 0.7)
    stems |= tube(W, H, [(16, 16), (16, 11), (15, 8)], 0.8, 0.7)
    shade(cv, stems, STARLIGHT_R, contour=True, R=1, base=0.55, gain=1.3)
    for (tx, ty) in ((10, 12), (21, 10), (15, 8)):
        shade(cv, m_ellipse(W, H, tx, ty, 1.4, 1.4), SHARD, mode="sphere", base=0.6, gain=1.2)
    rock(cv, 16, gy, 9, 3, "sw_rock", pal=STONE_DARK, R=1, base=0.5, facets=1)
    for (x, by, h, w, lean) in ((7, gy - 1, 6, 3, -2), (25, gy - 1, 7, 3, 2), (18, gy - 1, 4, 2, 1)):
        _glass_shard(cv, x, by, h, w, lean, see=0.25)
    outline(cv)
    glow(cv, 16, 11, 15, 11, STAR_HALO, steps=((1.0, 0.05),))
    for (tx, ty) in ((10, 12), (21, 10), (15, 8)):
        cv.put(tx - 1, ty - 1, SHARD[5])
    for pts in ([(5, 6), (2, 9), (3, 13), (5, 15)], [(27, 11), (30, 15), (28, 19), (26, 21)],
                [(25, 3), (21, 1), (17, 2)], [(9, 19), (6, 21), (8, 24)]):
        _streak(cv, pts, MOTE_GOLD[2], 0.45, 0.1, dotted=True, over=True)
    motes = [(5, 6, 1, True), (10, 3, 1, False), (25, 3, -1, True), (27, 11, -1, False), (4, 17, 1, False),
             (23, 17, -1, True), (12, 14, 1, False), (19, 7, -1, False), (28, 24, -1, False), (9, 19, 1, True),
             (15, 2, 1, False), (19, 13, 1, False)]
    for (x, y, d, big) in motes:
        _halo(cv, x, y, MOTE_GOLD[2], r=2.6 if big else 2.0, inner=0.4 if big else 0.3, outer=0.13 if big else 0.1)
        cv.put(x, y, MOTE_GOLD[3])
        cv.put(x - d, y, MOTE_GOLD[1])
        if big:
            cv.put(x - d - 1, y - 1, SHARD[4], 0.75)
            cv.put(x - d + 1, y - 1, SHARD[4], 0.75)
            cv.put(x - 2 * d, y, MOTE_GOLD[0])
        else:
            cv.put(x - d, y - 1, SHARD[4], 0.75)
    return cv
