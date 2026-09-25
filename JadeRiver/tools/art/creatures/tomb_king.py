"""Tomb King of Sunscar - DUNGEON BOSS on the Throne of the Tomb King (Azure Expanse, level 77):
an ancient sage-king who sealed himself in his desert tomb and was preserved by sand Qi
(Earth: sun and sand).

View: side, facing right (cell 256, 128 art px).  ~96 art px tall to the tip of the sun crown,
about 1.85x the player (52 px).  The anchor is lowered to [128, 244] (ground on art row 122)
like the gate guardian so the raised glaive and the crown fit inside the cell with the 2 px
margin.  The body stands a little left of the anchor so the glaive sweep has room in front.
Rig: waist P, torso up to the shoulders S (``lean``), two-bone arms (``px.ik2``) in wide
vermilion sleeves.  There are no legs: below the belt the faded robe dissolves into a
slowly swirling bell of sand that pools on the ground, so he half-glides.  The crescent glaive
is placed by the near hand (grip ``g1`` from the butt, angle ``ga``); the far hand grips at
``g2`` when he wields it with both hands, and ``plant`` rests the butt on the ground.
Parts, back to front: aura halo and drifting motes (behind), far arm and pauldron, sand mantle
(cylinder-shaded bell, helical swirl bands, a stream trailing along the ground), robe skirt
with a ragged hem breaking into sand, a gold lamellar tasset, belt with a jade plaque and a
vermilion sash, the hood's back drape, gilded cuirass (lamellar belly, heart mirror), high
collar, head (sun crown of radiating gold spikes round a jade disc, dark hood, golden death
mask with molten-amber eye slits in dark slots), the glass-bladed glaive
(behind the head when raised), near arm with a layered pauldron, gold gauntlet over the shaft.
Idle: the mantle swirls, a glint runs over the crown, a slow regal sway.  Walk: glides
forward, the mantle trailing back.  Windup: raises the glaive high overhead, the crown blazes
and sand gathers into a whirl (held).  Attack: a wide sweeping arc that flings a crescent of
sand (hit on frame 1).  Hurt: recoils, a crack flickers across the mask.  Death: sinks to one
knee on his glaive, slumps and pours away as sand, leaving the crown and the glaive in a heap,
then fades.
"""
import math

import numpy as np

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "tomb_king",
    "cell": 256,
    "anchor": [128, 244],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette: old gold, faded vermilion, robe umber, sand, desert glass, jade, molten amber ------
GOLD = px.material("tk_gold", "#ffe7a3", "#d8a646", "#9a6334", "#5a3638", outline="#1c0e10",
                   thresholds=(0.88, 0.55, 0.2))
VERM = px.material("tk_vermilion", "#df846a", "#ae4a3d", "#782c3b", "#481d36", outline="#190a14")
UMBER = px.material("tk_umber", "#8b6b5a", "#5e4339", "#3f2b31", "#291a2a", outline="#0f080e")
SAND = px.material("tk_sand", "#fbeabb", "#e1bf84", "#b98f63", "#87645b", outline="#3a2427",
                   thresholds=(0.86, 0.5, 0.16))
GLASS = px.material("tk_glass", "#ffffff", "#d9f5f3", "#9dd3dc", "#6697b2", outline="#15293a",
                    thresholds=(0.8, 0.45, 0.1))
JADE = px.material("tk_jade", "#b6f0d4", "#4fb394", "#2d7a6c", "#1b4a4b", outline="#08201c")
AMBER = px.material("tk_amber", "#fff6c8", "#ffc14f", "#f08b2c", "#b9521f", outline="#3a1508")
GLINT = GLASS.light          # specular pixels on glass, jade and the crown
AURA = GOLD.base             # the faint sun halo
AURA_HOT = AMBER.base        # blazing crown glow and rays
SOCKET = px.rgb("#24100f")   # eye slots, mouth and the dark mask crack

# ---- poses ------------------------------------------------------------------------------------
# bx, by    waist offset          lean  torso angle (deg, 90 upright)   head  head tilt (deg)
# hn        near hand relative to the shoulders     hf  far hand (when it does not grip)
# ga        glaive angle, butt -> blade (deg)       g1 / g2  near / far grip distance from the butt
# plant     rest the glaive butt on the ground (g1 is solved from the hand height)
# behind    draw the glaive behind the body and head (raised / swinging)
# swirl     mantle phase in cycles (loops on whole numbers)   trail  mantle streams back (-1..1)
# glint     crown glint (spike index, -1 none)      eye   open|flare|squint|dead
# blaze     crown blaze 0..1      gather  sand gathering 0..1 (windup)
# sweep     (from, to) angles of the glass swing trail        crescent  thrown sand crescent life
# crack     mask crack 0 none | 1 dark | 2 glowing      sink  body lowered (death)
# knee      kneeling on the near knee    pour  body turning to sand 0..1    heap  None | 0..1
# nb        near elbow bend (-1 down/back, +1 out, for the raised arm)   hit  impact spark
# fade      stepped opacity        dust / puff  ground dust behind / in front (life 0..1)
DEFAULTS = dict(bx=0, by=0, lean=90.0, head=0.0, hn=(14.0, 16.0), hf=None, ga=90.0, g1=50.0, g2=None, plant=True,
                behind=False, swirl=0.0, trail=0.0, glint=-1, eye="open", blaze=0.0, gather=None, sweep=None,
                crescent=None, hit=False, crack=0, nb=-1, sink=0.0, knee=False, pour=0.0, heap=None, fade=1.0,
                dust=None, puff=None)

POSE = px.poses(DEFAULTS, {
    "idle": [  # the mantle swirls, a glint runs over the crown, a slow regal sway
        dict(swirl=0.0, glint=1),
        dict(swirl=0.25, glint=3, lean=91.0, head=1.0),
        dict(swirl=0.5, glint=5, lean=91.0, head=1.0, by=-1),
        dict(swirl=0.75, glint=-1, lean=89.5),
    ],
    "walk": [  # glides forward, the sand mantle streaming back (two swirl cycles per loop)
        dict(swirl=0.0, trail=1.0, lean=86.0, plant=False, ga=80.0, g1=40.0, hn=(15.0, 15.0), dust=0.1),
        dict(swirl=1 / 3, trail=0.9, lean=85.0, plant=False, ga=79.0, g1=40.0, hn=(15.0, 14.0), by=-1, dust=0.45),
        dict(swirl=2 / 3, trail=1.0, lean=86.0, plant=False, ga=78.0, g1=40.0, hn=(16.0, 14.0), by=-1, dust=0.8),
        dict(swirl=1.0, trail=1.0, lean=86.0, plant=False, ga=80.0, g1=40.0, hn=(15.0, 15.0), dust=0.1),
        dict(swirl=4 / 3, trail=0.9, lean=85.0, plant=False, ga=79.0, g1=40.0, hn=(15.0, 14.0), by=-1, dust=0.45),
        dict(swirl=5 / 3, trail=1.0, lean=86.0, plant=False, ga=78.0, g1=40.0, hn=(16.0, 14.0), by=-1, dust=0.8),
    ],
    "windup": [  # the near arm lifts the glaive high behind the crown, the far hand thrusts forward,
        #          the crown blazes and sand gathers - held
        dict(swirl=0.3, plant=False, behind=True, hn=(-6.0, -4.0), nb=1, ga=120.0, g1=48.0, hf=(15.0, 6.0),
             lean=92.0, head=3.0, eye="flare", blaze=0.35, gather=0.3),
        dict(swirl=0.6, plant=False, behind=True, hn=(-9.5, -12.0), nb=1, ga=118.0, g1=51.0, hf=(21.0, 2.0),
             lean=94.0, head=5.0, eye="flare", blaze=0.75, gather=0.65),
        dict(swirl=0.9, plant=False, behind=True, hn=(-10.5, -16.0), nb=1, ga=118.0, g1=52.0, hf=(24.0, -1.0),
             lean=95.0, head=6.0, eye="flare", blaze=1.0, gather=1.0, by=-1),
    ],
    "attack": [  # the wide sweep: over the top, out at chest height (hit), down, recover
        dict(swirl=1.1, plant=False, behind=True, hn=(15.0, -9.0), ga=62.0, g1=44.0, g2=28.0, lean=90.0,
             eye="flare", blaze=0.6, sweep=(118.0, 62.0), trail=0.3),
        dict(swirl=1.25, plant=False, behind=True, hn=(20.0, 7.0), ga=-18.0, g1=42.0, g2=26.0, lean=84.0,
             head=-4.0, bx=3, eye="flare", blaze=0.4, sweep=(118.0, -18.0), crescent=0.0, hit=True, trail=-0.4),
        dict(swirl=1.4, plant=False, behind=True, hn=(17.0, 15.0), ga=-52.0, g1=40.0, g2=24.0, lean=82.0,
             head=-6.0, bx=3, sweep=(40.0, -52.0), crescent=0.5, trail=-0.2),
        dict(swirl=1.55, plant=False, behind=True, hn=(15.0, 15.0), ga=40.0, g1=42.0, lean=87.0, head=-2.0, bx=1,
             crescent=1.0),
    ],
    "hurt": [  # recoils; a crack flickers across the death mask
        dict(swirl=0.2, bx=-5, lean=100.0, head=12.0, eye="squint", crack=2, ga=104.0, hn=(12.0, 17.0), trail=-0.6,
             puff=0.2),
        dict(swirl=0.35, bx=-3, lean=95.0, head=5.0, eye="squint", crack=1, ga=96.0, trail=-0.3, puff=0.6),
    ],
    "death": [  # reels, sinks to one knee on the glaive, pours away as sand, leaves crown and glaive
        dict(swirl=0.2, bx=-4, lean=98.0, head=10.0, eye="squint", crack=2, ga=100.0, trail=-0.6),
        dict(swirl=0.4, sink=9.0, lean=80.0, head=-14.0, eye="squint", crack=2, knee=True, ga=82.0,
             hn=(17.0, 6.0), hf=(10.0, 22.0)),
        dict(swirl=0.6, sink=15.0, lean=72.0, head=-24.0, eye="dead", crack=1, knee=True, ga=78.0,
             hn=(17.0, 10.0), hf=(9.0, 24.0), pour=0.55),
        dict(heap=0.0),
        dict(heap=1.0, fade=0.45),
    ],
})

L_UP, L_FO = 13.5, 13.0
TORSO = 25.0
POLE = 58.0     # butt -> collar
BLADE0 = 55.0   # where the blade's spine starts along the shaft
# crescent blade in shaft coordinates (t along the shaft from BLADE0, k toward the edge side)
EDGE = ((0.0, 1.0), (3.5, 5.0), (8.0, 7.8), (13.0, 8.8), (18.0, 8.0), (22.0, 5.8), (25.5, 2.4), (27.0, -1.4))
SPINE = ((24.0, 0.2), (20.0, 2.4), (15.0, 3.4), (10.0, 3.0), (5.5, 1.2), (2.0, -1.4))
SPIKES = (6.5, 9.0, 11.0, 12.0, 11.0, 9.0, 6.5)  # sun-crown spike lengths, back to front


def W(q, a, r):
    return px.polar(q, a, r)


def _pt(q):
    return (math.floor(q[0]), math.floor(q[1]))


def _ring(layer, m, color, dist=2):
    """1 px glow line ``dist`` px outside mask ``m`` (i.e. outside its dark outline) on ``layer``."""
    d = m
    for _ in range(dist - 1):
        d = px.dilate(d)
    r = px.dilate(d) & ~d
    layer._commit(r, np.where(r, 1, -1).astype(np.int8), px.flat(color), name="glow")


# ---- sand mantle ---------------------------------------------------------------------------------
def _mantle_at(P, G, p, s):
    """(y, x_left, x_right) of the sand bell at height fraction ``s`` (0 waist .. 1 below ground);
    works on floats and numpy arrays."""
    top = P[1] + 1.0
    y = top + (G + 3.0 - top) * s
    ph = p.swirl * 2 * math.pi
    hw = 8.0 + 11.0 * s ** 1.6
    cx = P[0] - p.trail * 7.0 * s * s
    wr = np.sin(s * 7.0 - ph) * 1.2 * s
    wl = np.sin(s * 7.0 + 2.0 - ph) * 1.2 * s
    return y, cx - hw - wl - max(0.0, p.trail) * 4.0 * s * s, cx + hw + wr + min(0.0, p.trail) * 3.0 * s


def _mantle(cv, P, G, p, below):
    n = 18
    rows = [_mantle_at(P, G, p, k / n) for k in range(n + 1)]
    pts = [(float(xr), y) for (y, xl, xr) in rows] + [(float(xl), y) for (y, xl, xr) in rows[::-1]]
    mask = cv.mask_polygon(pts)
    mask |= cv.mask_ellipse(P[0] - 1.0 - p.trail * 8.0, G - 0.5, 20.0 + abs(p.trail) * 4.0, 3.6)
    if p.trail > 0.5:  # a stream of sand dragged along the ground behind him
        y, xl, xr = _mantle_at(P, G, p, 0.9)
        xl = float(xl)
        mask |= cv.mask_limb([(xl + 4.0, G - 1.5), (xl - 8.0, G - 0.5), (xl - 16.0 * p.trail, G)], [3.0, 2.2, 1.2])
    mask &= ~below
    # cylinder-like normals across the bell, tipped up because it flares toward the ground
    top = P[1] + 1.0
    s = np.clip((cv.Y - top) / (G + 3.0 - top), 0.0, 1.0)
    _, xl, xr = _mantle_at(P, G, p, s)
    nx = np.clip((cv.X - (xl + xr) / 2) / ((xr - xl) / 2 + 1.5), -1.0, 1.0) * 0.95
    ny = np.full(nx.shape, -0.35)
    nz = np.sqrt(np.clip(1.0 - nx * nx - ny * ny, 0.02, 1.0))
    cv.fill(mask, SAND, normals=(nx, ny, nz), name="mantle")
    # helical swirl bands wrapping round the bell (three bands: a third of a turn loops)
    ph = p.swirl * 2 * math.pi / 3
    for i in range(3):
        prev = None
        for k in range(29):
            s = 0.4 + 0.58 * k / 28
            y, xl, xr = _mantle_at(P, G, p, s)
            th = ph + i * 2 * math.pi / 3 + s * 1.7 * math.pi
            cx, hw = float(xl + xr) / 2, float(xr - xl) / 2 - 1.0
            q = _pt((cx + hw * math.cos(th), y))
            vis = math.sin(th) > 0.1
            if vis and prev is not None:
                cv.line(prev, q, SAND.step(-1), decal=True, clip="mantle", name="mantle")
                cv.line((prev[0], prev[1] + 1), (q[0], q[1] + 1), SAND.step(-1), decal=True, clip="mantle",
                        name="mantle")
                cv.line((prev[0], prev[1] + 2), (q[0], q[1] + 2), SAND.step(1), decal=True, clip="mantle",
                        name="mantle")
            prev = q if vis else None


def _ribbons(back, front, P, G, p, spread=3.0):
    """Thin streams of sand circling the lower mantle in opposed pairs: the front runs cross over
    the bell, the back runs peek out behind it.  Half a turn per swirl cycle (the pairs are
    two-fold symmetric), so idle and walk loop."""
    for i, (s, span, rise) in enumerate(((0.6, 100.0, 2.0), (0.84, 90.0, 1.0))):
        y, xl, xr = _mantle_at(P, G, p, s)
        cx, hw = float(xl + xr) / 2, float(xr - xl) / 2 + spread
        for half in (0.0, 180.0):
            a0 = p.swirl * 180.0 * (1.0 if i == 0 else -1.0) + i * 70.0 + half + 200.0
            n = 12
            runs = {True: [], False: []}
            cur, side = [], None
            for j in range(n + 1):
                a = math.radians(a0 + span * j / n)
                q = (cx + math.cos(a) * hw, y - math.sin(a) * 3.0 - rise * j / n)
                r = 0.45 + 0.7 * math.sin(math.pi * j / n)
                f = math.sin(a) < 0
                if side is not None and f != side:
                    runs[side].append(cur)
                    cur = [cur[-1]]
                cur.append((q, r))
                side = f
            runs[side].append(cur)
            for f, lst in runs.items():
                for run in lst:
                    if len(run) >= 2:
                        (front if f else back).limb([q for q, r in run], [r for q, r in run], SAND, shade="soft",
                                                    name="ribbon")


def _skirt(cv, P, G, p):
    """Faded vermilion robe flaring from the belt; its ragged hem breaks up into the sand."""
    top = P[1] - 1.0
    hem = min(P[1] + 17.0, G - 6.0)
    tr = p.trail
    fr = P[0] + 13.0 - tr * 1.0
    bk = P[0] - 13.5 - tr * 4.0
    pts = [(P[0] - 7.5, top), (P[0] + 8.0, top), (fr, hem - 3.0)]
    drops = (0.0, 3.0, 1.0, 4.5, 1.5, 3.5, 0.5, 4.0, 1.0, 2.5, 0.0)
    for k, dr in enumerate(drops):
        x = fr - (fr - bk) * k / (len(drops) - 1)
        pts.append((x, hem - 2.0 + dr))
    pts.append((bk, hem - 3.0))
    cv.polygon(pts, VERM, name="robe")
    # folds fanning out from the belt
    for dx0, dx1 in ((-3.0, -6.0), (2.0, 3.0), (6.5, 10.0)):
        cv.line(_pt((P[0] + dx0, top + 4.0)), _pt((P[0] + dx1 - tr * 2.0, hem - 4.0)), VERM.step(1), decal=True,
                clip="robe", name="robe")
    # gold hem band
    a, b = (fr - 1.0, hem - 3.5), (bk + 1.0, hem - 3.5)
    cv.line(_pt(a), _pt(b), GOLD, band=None, decal=True, clip="robe", name="robe")
    cv.line(_pt((a[0], a[1] + 1)), _pt((b[0], b[1] + 1)), GOLD.step(1), band=None, decal=True, clip="robe",
            name="robe")


def _tassets(cv, P, p):
    """A flaring gold lamellar flap hanging from the belt over the front of the robe."""
    tr = p.trail
    x0, x1, ln = 1.5, 8.5, 11.0
    q = [(P[0] + x0, P[1]), (P[0] + x1, P[1]), (P[0] + x1 + 3.0 - tr, P[1] + ln),
         (P[0] + x0 + 0.5 - tr * 1.5, P[1] + ln)]
    cv.polygon(q, GOLD, name="tasset", sep="deep")
    for j in range(3):
        y = P[1] + 3.0 + j * 3.0
        cv.line(_pt((P[0] + x0 - 3.0, y)), _pt((P[0] + x1 + 5.0, y)), GOLD.step(1), band=None, decal=True,
                clip="tasset", name="tasset")


def _belt(cv, P, p):
    cv.limb([(P[0] - 8.0, P[1] - 1.0), (P[0] + 9.0, P[1] - 1.0)], 2.2, UMBER, shade="two", name="belt", sep="deep")
    for dx in (-5.0, -1.0):
        cv.pixels([_pt((P[0] + dx, P[1] - 1.5)), _pt((P[0] + dx + 1.0, P[1] - 1.5))], GOLD.base, name="belt")
    cv.rect(P[0] + 3.0, P[1] - 3.5, 4.0, 5.0, JADE, shade="soft", name="belt", sep="deep")
    sw = math.sin(p.swirl * 2 * math.pi) * 0.8 - p.trail * 2.0
    cv.limb([(P[0] + 8.0, P[1] + 1.0), (P[0] + 9.0 + sw * 0.5, P[1] + 8.0), (P[0] + 8.5 + sw, P[1] + 15.0)],
            [1.6, 1.4, 1.0], VERM, shade="two", name="sash", sep="deep")


# ---- torso ----------------------------------------------------------------------------------------
def _torso(cv, P, S, p):
    up = p.lean
    waist = W(P, up, 1.0)
    robe = [W(waist, up - 90, 6.5), W(W(S, up, -10.0), up - 90, 9.5), W(W(S, up, -0.5), up - 90, 10.0),
            W(W(S, up, 2.5), up - 45, 6.0), W(W(S, up, 2.5), up + 45, 6.0), W(W(S, up, -0.5), up + 90, 10.5),
            W(W(S, up, -10.0), up + 90, 8.5), W(waist, up + 90, 6.0)]
    cv.polygon(robe, VERM, name="body")
    # gilded cuirass over the robe: V neck, a strip of robe left showing down the back
    cuir = [W(waist, up - 90, 6.5), W(W(S, up, -10.0), up - 90, 9.5), W(W(S, up, -1.5), up - 90, 9.5),
            W(W(S, up, -1.0), up - 90, 5.5), W(W(S, up, -7.0), up - 90, 1.5), W(W(S, up, -1.0), up + 90, 3.5),
            W(W(S, up, -2.0), up + 90, 8.0), W(W(S, up, -10.0), up + 90, 6.5), W(waist, up + 90, 3.5)]
    cv.polygon(cuir, GOLD, name="cuirass", sep="deep")
    # lamellar belly: rows of lames with staggered lacing
    for k in range(4):
        d = 2.5 + k * 3.0
        a, b = W(W(waist, up, d), up + 90, 9.0), W(W(waist, up, d), up - 90, 11.0)
        cv.line(_pt(a), _pt(b), GOLD.step(1), band=None, decal=True, clip="cuirass", name="cuirass")
        for j in range(-3, 4):
            q = W(W(waist, up, d + 1.5), up - 90, j * 3.0 + (1.5 if k % 2 else 0.0))
            cv.pixel(*_pt(q), GOLD.step(1), band=None, decal=True, clip="cuirass", name="cuirass")
    # breast plate edge and the heart-protecting mirror
    e0, e1 = W(W(waist, up, 13.5), up + 90, 9.0), W(W(waist, up, 13.5), up - 90, 11.0)
    cv.line(_pt(e0), _pt(e1), GOLD.deep, band=None, decal=True, clip="cuirass", name="cuirass")
    m = W(W(S, up, -8.0), up - 90, 5.5)
    cv.circle(m[0], m[1], 2.6, GOLD, name="mirror", sep="deep")
    cv.pixel(*_pt((m[0] - 0.5, m[1] - 0.5)), AMBER.light, name="mirror")
    # high collar
    cv.limb([W(W(S, up, 1.5), up + 90, 4.5), W(W(S, up, 2.0), up - 90, 5.0)], 2.2, GOLD, shade="two", name="collar",
            sep="deep")


def _drape(cv, H, S, p):
    """Back drape of the hood, falling over the shoulders."""
    sw = math.sin(p.swirl * 2 * math.pi) * 0.8 - p.trail * 1.5
    pts = [(H[0] - 6.5, H[1] - 3.0), (H[0] - 1.5, H[1] + 1.0), (S[0] - 4.0, S[1] + 6.0),
           (S[0] - 8.0 + sw, S[1] + 13.0), (S[0] - 12.0 + sw, S[1] + 11.0), (S[0] - 11.0, S[1] + 2.0),
           (H[0] - 8.5, H[1] + 3.0)]
    cv.polygon(pts, UMBER, shade="soft", name="drape")


# ---- head and crown -------------------------------------------------------------------------------
def _crown(cv, C, hot=False):
    """Sun crown: a fan of radiating gold spikes round a jade disc at ``C``; returns the tips."""
    mat = AMBER if hot else GOLD
    n = len(SPIKES)
    step = 164.0 / (2 * n - 2)
    pts = [W(C, 186.0, 5.0)]
    for i in range(2 * n - 1):
        a = 172.0 - i * step
        pts.append(W(C, a, SPIKES[i // 2] if i % 2 == 0 else 6.5))
    pts += [W(C, -6.0, 5.0), (C[0] + 4.0, C[1] + 3.5), (C[0] - 4.0, C[1] + 3.5)]
    cv.polygon(pts, mat, name="crown", sep="deep")
    for i in range(1, n - 1):  # a lit ridge down each long spike
        a = 172.0 - 2 * i * step
        cv.line(_pt(W(C, a, 5.0)), _pt(W(C, a, SPIKES[i] - 3.5)), mat.step(-1), decal=True, clip="crown",
                name="crown")
    cv.circle(C[0], C[1], 3.2, JADE, name="disc", sep="deep")
    cv.pixels([_pt((C[0] - 1.3, C[1] - 1.3)), _pt((C[0] - 0.3, C[1] - 1.3))], GLINT, name="disc")
    return [W(C, 172.0 - 2 * i * step, SPIKES[i] - 1.5) for i in range(n)]


def _head(cv, H, p):
    hot = p.blaze >= 0.5
    C = (H[0] + 0.5, H[1] - 9.5)
    tips = _crown(cv, C, hot)
    # dark hood at the back of the head
    cv.ellipse(H[0] - 3.0, H[1] + 0.5, 5.5, 7.6, UMBER, name="hood", sep="deep")
    # golden death mask (3/4 right): high brow, long straight nose, closed serene mouth
    mask = [(H[0] - 3.0, H[1] - 7.0), (H[0] + 5.5, H[1] - 7.2), (H[0] + 7.8, H[1] - 3.5), (H[0] + 8.4, H[1] - 0.5),
            (H[0] + 9.8, H[1] + 1.8), (H[0] + 8.2, H[1] + 3.0), (H[0] + 8.4, H[1] + 4.8), (H[0] + 6.4, H[1] + 8.5),
            (H[0] + 1.5, H[1] + 8.8), (H[0] - 2.5, H[1] + 5.0), (H[0] - 3.6, H[1] - 1.0)]
    cv.polygon(mask, GOLD, name="mask", sep="deep")
    ex, ey = _pt((H[0] - 1.0, H[1] - 1.5))  # near eye slot (left end)
    fx_ = ex + 7                            # far eye slot (left end)
    # lit brow ridge, dark eye slots, nose ridge, closed mouth
    cv.line((ex, ey - 2), (ex + 4, ey - 2), GOLD.light, name="mask")
    cv.line((ex, ey - 1), (ex + 5, ey - 1), SOCKET, name="mask")
    cv.line((ex, ey), (ex + 5, ey), SOCKET, name="mask")
    cv.pixels([(fx_, ey - 1), (fx_ + 1, ey - 1), (fx_, ey), (fx_ + 1, ey)], SOCKET, name="mask")
    cv.line((ex + 6, ey - 2), (ex + 6, ey + 3), GOLD.light, name="mask")
    cv.pixels([(ex + 7, ey + 1), (ex + 7, ey + 2), (ex + 7, ey + 3)], GOLD.shadow, name="mask")
    cv.line((ex + 4, ey + 6), (ex + 7, ey + 6), SOCKET, name="mask")
    cv.pixels([(ex + 5, ey + 7), (ex + 6, ey + 7)], GOLD.light, name="mask")
    # crown band across the brow
    cv.limb([(H[0] - 4.5, H[1] - 6.2), (H[0] + 5.5, H[1] - 7.4)], 1.1, AMBER if hot else GOLD, shade="two",
            name="band", sep="deep")
    # molten-amber eyes glowing in the slots
    if p.eye == "dead":
        pass
    elif p.eye == "squint":
        cv.pixels([(ex + 2, ey), (ex + 3, ey), (fx_ + 1, ey)], AMBER.shadow, name="eye")
    else:
        hot_eye = p.eye == "flare"
        cv.pixels([(ex + 1, ey), (ex + 4, ey), (fx_ + 1, ey)], AMBER.base, name="eye")
        cv.pixels([(ex + 2, ey), (ex + 3, ey), (fx_, ey)], GLINT if hot_eye else AMBER.light, name="eye")
        cv.pixel(ex + 2, ey + 1, AMBER.shadow, name="eye")  # a molten drip
        if hot_eye:
            cv.pixels([(ex + 2, ey - 1), (ex + 3, ey - 1), (fx_, ey - 1)], AMBER.base, name="eye")
            cv.pixel(ex + 2, ey + 2, AMBER.deep, name="eye")
    if p.crack:
        col = AMBER.light if p.crack == 2 else SOCKET
        pts = [(H[0] + 1.0, H[1] - 7.0), (H[0] + 3.0, H[1] - 3.5), (H[0] + 2.0, H[1] + 0.5), (H[0] + 4.5, H[1] + 3.5),
               (H[0] + 3.0, H[1] + 8.0)]
        for a, b in zip(pts, pts[1:]):
            cv.line(_pt(a), _pt(b), col, decal=True, clip="mask", name="mask")
    return C, tips


# ---- arms and glaive ------------------------------------------------------------------------------
def _arm(cv, sh, hand, far, bend=-1):
    d = math.hypot(hand[0] - sh[0], hand[1] - sh[1])
    if d < L_UP + L_FO - 0.3:
        elbow = px.ik2(sh, hand, L_UP, L_FO, bend=bend)
    else:
        elbow = px.lerp_pt(sh, hand, 0.5)
    name = "arm_far" if far else "arm"
    shade = "dark" if far else "soft"
    cv.limb([sh, elbow, hand], [3.6, 3.0, 2.4], VERM, shade=shade, name=name, sep=False if far else "deep")
    # the wide imperial sleeve hangs from the forearm
    cuff = px.lerp_pt(elbow, hand, 0.7)
    mid = px.lerp_pt(elbow, cuff, 0.5)
    sl = [(elbow[0], elbow[1] - 1.0), cuff, (cuff[0] + 0.5, cuff[1] + 5.0), (cuff[0] - 1.0, cuff[1] + 9.0),
          (mid[0] - 2.0, mid[1] + 11.0), (elbow[0] - 3.0, elbow[1] + 6.0)]
    cv.polygon(sl, VERM, shade="dark" if far else "two", name=name, sep=False if far else "deep")
    cv.line(_pt((cuff[0] - 1.0, cuff[1] + 8.5)), _pt((mid[0] - 2.0, mid[1] + 10.0)), GOLD.step(1), band=None,
            decal=True, clip=name, name=name)
    cv.limb([px.lerp_pt(elbow, hand, 0.68), px.lerp_pt(elbow, hand, 0.84)], 2.8, GOLD,
            shade="dark" if far else "two", name=name, sep=False if far else "deep")
    cv.circle(hand[0], hand[1], 2.4, GOLD, shade="dark" if far else "full", name="fist", sep=False if far else "deep")
    return elbow


def _pauldron(cv, sh, up, far=False):
    """Three overlapping gold lames capping the shoulder, drooping outward (upper lame on top)."""
    out = up - 90 if far else up + 90
    tilt = -16.0 if far else 16.0
    for k in (2, 1, 0):
        c = W(W(sh, up + 180, k * 2.4 - 1.0), out, k * 0.9)
        cv.ellipse(c[0], c[1], 5.0 + k * 0.7, 3.0, GOLD, angle=up - 90 + tilt, shade="dark" if far else "full",
                   name="pauldron_far" if far else "pauldron", sep=False if far else "deep")
    if not far:
        q = W(W(sh, up, 1.5), out, 1.5)
        cv.pixels([_pt(q), _pt((q[0] + 1.0, q[1]))], GLINT, name="pauldron")


def _gframe(butt, ga):
    u = px.polar((0.0, 0.0), ga, 1.0)
    n = px.polar((0.0, 0.0), ga - 90.0, 1.0)

    def L(t, k=0.0):
        return (butt[0] + u[0] * t + n[0] * k, butt[1] + u[1] * t + n[1] * k)
    return L


def _glaive(cv, butt, ga):
    L = _gframe(butt, ga)
    cv.limb([L(0.0), L(POLE)], [1.5, 1.4], UMBER, shade="two", name="pole")
    cv.limb([L(0.0), L(3.0)], [1.8, 1.6], GOLD, shade="two", name="pole")
    pts = [L(BLADE0 + t, k) for (t, k) in EDGE] + [L(BLADE0 + t, k) for (t, k) in SPINE]
    cv.polygon(pts, GLASS, name="blade", sep="deep")
    cv.polygon([L(BLADE0 + 1.0, -1.0), L(BLADE0 - 2.5, -4.5), L(BLADE0 + 4.0, -1.2)], GLASS, shade="two",
               name="blade", sep="deep")
    for t, k in ((10.0, 6.5), (11.0, 6.8), (16.0, 6.6)):
        cv.pixel(*_pt(L(BLADE0 + t, k)), GLINT, decal=True, clip="blade", name="blade")
    cv.limb([L(BLADE0 - 3.0), L(BLADE0 + 1.0)], 2.2, GOLD, shade="two", name="collar", sep="deep")
    # vermilion tassel hanging from the collar
    q = L(BLADE0 - 2.5, -1.8)
    cv.limb([q, (q[0] - 1.0, q[1] + 3.0), (q[0] - 0.5, q[1] + 6.0)], [1.3, 1.1, 0.7], VERM, shade="two",
            name="tassel", sep="deep")
    return L


# ---- FX -------------------------------------------------------------------------------------------
def _sparkle(fx, q, big=False):
    x, y = _pt(q)
    fx.pixels([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], AMBER.light, name="glint")
    if big:
        fx.pixels([(x - 2, y), (x + 2, y), (x, y - 2), (x, y + 2)], AMBER.base, name="glint")
    fx.pixel(x, y, GLINT, name="glint")


def _motes(fx, P, G, p, n=6):
    """Sand motes drifting up and back round the king (2 px specks, never lone pixels)."""
    for k in range(n):
        h = px.hash01("tk_mote", k)
        age = (p.swirl + k / n + h * 0.3) % 1.0  # whole swirl cycles loop
        x = P[0] + (-28.0 + 56.0 * px.hash01("tk_mx", k)) - age * 6.0
        y = G - 8.0 - 62.0 * px.hash01("tk_my", k) - age * 8.0
        x, y = math.floor(x), math.floor(y)
        fx.pixel(x, y, SAND.light, name="mote")
        fx.pixel(x + 1, y + (k % 2), SAND.shadow, name="mote")


def _crescent(fx, c, r, a0, a1, thick, mat=SAND, name="crescent"):
    """A crescent band along a circular arc: thickest in the middle, pointed at both ends."""
    n = 14
    pts, radii = [], []
    for i in range(n + 1):
        t = i / n
        pts.append(W(c, a0 + (a1 - a0) * t, r))
        radii.append(max(0.45, thick * math.sin(math.pi * t) ** 0.8))
    fx.limb(pts, radii, mat, shade="soft", name=name)


def _gather(back, front, P, G, t, frame):
    """Sand streams whirling in toward the mantle on a shrinking, rising orbit."""
    for k in range(6):
        a0 = k * 60.0 + frame * 28.0
        r = 33.0 - 9.0 * t
        yb = G - 4.0 - (k % 3) * 7.0 * t
        pts, radii = [], []
        for j in range(6):
            a = math.radians(a0 + j * 9.0)
            pts.append((P[0] - 2.0 + math.cos(a) * r, min(G - 1.5, yb - math.sin(a) * 4.5)))
            radii.append((0.4, 0.8, 1.1, 1.2, 1.0, 0.6)[j])
        lay = front if math.sin(math.radians(a0 + 25.0)) < 0 else back
        lay.limb(pts, radii, SAND, shade="soft", name="gather")


# ---- death heap -----------------------------------------------------------------------------------
def _heap(cv, P, G, t, below):
    cx = P[0] + 2.0
    _glaive(cv, (cx + 5.0, G - 7.0), 66.0)
    top = 14.0 - 4.0 * t
    g = cv.union(cv.geom_ellipse(cx, G + 1.0, 22.0 - 2.0 * t, top),
                 cv.geom_ellipse(cx - 13.0, G + 1.0, 13.0, 7.0 - t),
                 cv.geom_ellipse(cx + 13.0, G + 1.0, 13.0, 6.0 - t), weights=[1.0, 0.8, 0.8])
    cv.draw_geom(g, SAND, name="heap", minus=below)
    for k in range(3):  # wind ripples on the heap
        a = (cx - 19.0 + k * 11.0, G - 2.0 - (1 - abs(k - 1)) * 5.0 + t)
        b = (a[0] + 9.0, a[1] - 2.0)
        cv.line(_pt(a), _pt(b), SAND.step(-1), decal=True, clip="heap", name="heap")
    C = (cx - 6.0, G - top - 3.0)
    with cv.xform(px.rotate(12.0, (C[0], C[1] + 4.0))):
        _crown(cv, C)


# ---- draw -----------------------------------------------------------------------------------------
def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    G = cv.ground
    below = cv.mask_polygon([(0, cv.gy - 1.0), (cv.w, cv.gy - 1.0), (cv.w, cv.h), (0, cv.h)])
    P = (cv.gx - 10.0 + p.bx, G - 37.0 + p.by + p.sink)
    back = cv.layer(above=False, outline=False)
    if p.heap is not None:
        _heap(cv, P, G, p.heap, below)
        _motes(back, P, G, p, n=5)
        return

    up = p.lean
    S = W(P, up, TORSO)
    H = W(W(S, up, 10.0), up - 90, 2.0)
    neck = W(S, up, 3.0)
    sh_near = W(W(S, up + 180, 2.0), up + 90, 6.5)
    sh_far = W(W(S, up + 180, 2.0), up - 90, 7.5)

    hand_n = (S[0] + p.hn[0], S[1] + p.hn[1])
    if p.plant:
        g1 = (G - 1.5 - hand_n[1]) / max(0.2, math.sin(math.radians(p.ga)))
    else:
        g1 = p.g1
    butt = W(hand_n, p.ga + 180.0, g1)
    L = _gframe(butt, p.ga)
    if p.g2 is not None:
        hand_f = L(p.g2)
    elif p.hf is not None:
        hand_f = (S[0] + p.hf[0], S[1] + p.hf[1])
    else:
        hand_f = (S[0] + 8.0, S[1] + 23.0)

    # ---- behind: aura halo round the crown, drifting motes, the swing trail
    C_est = W(H, up + p.head, 9.5)
    if p.blaze < 0.5:
        for a0, a1 in ((18, 62), (76, 104), (118, 162)):
            hc.arc_line(back, C_est, 17.0, a0, a1, AURA, name="aura")
    _motes(back, P, G, p)
    trail = cv.layer(above=False, outline=False)
    if p.sweep is not None:
        a0, a1 = p.sweep
        hc.arc_line(trail, sh_near, 50.0, a0, a1, GLASS.shadow, name="sweep")
        hc.arc_line(trail, sh_near, 47.0, a0 - 6.0, a1, GLASS.light, name="sweep")
        hc.arc_line(trail, sh_near, 44.0, a0 - 12.0, a1, GLASS.shadow, name="sweep")
    sand_back = cv.layer(above=False, outline=True)
    sand_front = cv.layer(above=True, outline=True)
    if p.sink == 0 and p.gather is None:
        _ribbons(sand_back, sand_front, P, G, p)

    # ---- far arm and pauldron, glaive when it is raised behind
    _arm(cv, sh_far, hand_f, far=True)
    _pauldron(cv, sh_far, up, far=True)
    if p.behind:
        _glaive(cv, butt, p.ga)
    # ---- lower body: sand mantle, robe, tassets, belt
    _mantle(cv, P, G, p, below)
    _skirt(cv, P, G, p)
    if p.knee:  # the robe drapes over the raised near knee; its shin sinks into the sand
        K = (P[0] + 12.0, G - 11.0)
        cv.limb([K, (K[0] + 0.5, G + 2.0)], [4.2, 3.6], VERM, shade="two", name="knee", sep="deep", minus=below)
        cv.limb([(P[0] + 1.0, P[1] + 5.0), K], [5.6, 4.8], VERM, shade="soft", name="knee", sep="deep")
        cv.line(_pt((K[0] - 6.0, K[1] - 3.0)), _pt((K[0] + 3.0, K[1] - 4.0)), GOLD, band=None, decal=True,
                clip="knee", name="knee")
        cv.ellipse(K[0] + 1.0, G + 0.5, 8.0, 3.4, SAND, name="mantle", sep="deep", minus=below)
    _tassets(cv, P, p)
    _belt(cv, P, p)
    # ---- torso and head
    _drape(cv, H, S, p)
    _torso(cv, P, S, p)
    with cv.xform(px.rotate(p.head, neck)):
        C, tips = _head(cv, H, p)
        C = cv.tp(C)
        tips = [cv.tp(t) for t in tips]
    # ---- glaive in hand, near arm over the shaft
    if not p.behind:
        _glaive(cv, butt, p.ga)
    _arm(cv, sh_near, hand_n, far=False, bend=p.nb)
    _pauldron(cv, sh_near, up)

    # ---- the body pours away as sand: a mound swallows everything below the cut, holes open
    # in the armour above it and sand runs off the sleeves
    if p.pour > 0:
        cut = P[1] + 16.0 - p.pour * 34.0
        keep = cv.mask_of(["pole", "blade", "collar", "tassel"])
        low = (cv.Y > cut + 1.5 * np.sin(cv.X * 0.9)) & cv.filled & ~keep
        cv._commit(low, np.where(low, 1, -1).astype(np.int8), px.flat(px.INK), erase=True)
        holes = [(P[0] - 9.0 + 5.5 * k, cut - 3.0 - 4.0 * px.hash01("tk_hole", k), 1.1 + px.hash01("tk_hr", k))
                 for k in range(4)]
        hc.erase_blobs(cv, holes)
        mh = G - cut + 3.0
        bumps = [cv.geom_ellipse(P[0] - 6.0 + 7.0 * k, cut + 1.0 + 1.5 * (k % 2), 4.5, 3.0) for k in range(3)]
        g = cv.union(cv.geom_ellipse(P[0] + 1.0, G + 2.0, 17.0, mh), cv.geom_ellipse(P[0] + 1.0, G + 1.0, 27.0, 6.5),
                     *bumps, weights=[1.0, 0.8, 0.6, 0.6, 0.6])
        cv.draw_geom(g, SAND, name="heap", minus=[below, keep], sep="deep")
        for k in range(3):  # ripples down the slope
            a = (P[0] - 14.0 + k * 9.0, G - 3.0 - (1 - abs(k - 1)) * 4.0)
            cv.line(_pt(a), _pt((a[0] + 7.0, a[1] - 2.0)), SAND.step(-1), decal=True, clip="heap", name="heap")
        for k, (dx, dy) in enumerate(((-12.0, 0.0), (-4.0, 2.0))):  # sand spilling from the far side
            q = (P[0] + dx, cut + dy - 2.0)
            cv.limb([q, (q[0] - 1.5, q[1] + 3.0), (q[0] - 3.5, q[1] + 6.0)], [1.4, 1.1, 0.6], SAND, shade="soft",
                    name="stream")
        hc.drop_specks(cv)

    # ---- FX above
    fx = cv.layer(above=True, outline=False)
    if p.glint >= 0 and p.blaze < 0.5:
        _sparkle(fx, tips[p.glint % len(tips)])
    if p.blaze > 0:
        glow = cv.layer(above=False, outline=False)
        _ring(glow, cv.mask_of(["crown", "disc"]), AURA_HOT, dist=2)
        if p.blaze >= 0.7:
            _ring(glow, cv.mask_of(["crown", "disc"]), AURA, dist=3)
        for i, t in enumerate(tips):
            a = math.degrees(math.atan2(-(t[1] - C[1]), t[0] - C[0]))
            r0 = math.hypot(t[0] - C[0], t[1] - C[1]) + 4.5
            q0, q1 = W(C, a, r0), W(C, a, r0 + 1.0 + 4.0 * p.blaze * (1.0 if i % 2 else 0.6))
            fx.line(_pt(q0), _pt(q1), AURA_HOT, name="ray")
        if p.blaze >= 1.0:
            _sparkle(fx, tips[3], big=True)
    if p.gather is not None:
        _ribbons(sand_back, sand_front, P, G, p, spread=3.0 + 3.0 * p.gather)
        _gather(sand_back, sand_front, P, G, p.gather, frame)
    if p.crescent is not None:
        top = cv.layer(above=True, outline=True)
        t = p.crescent
        c = (sh_near[0] + 4.0 * t, sh_near[1] + 2.0)
        if t < 0.9:
            _crescent(top, c, 54.0 + 6.0 * t, 36.0 - 8.0 * t, -26.0 + 4.0 * t, 2.6 - 1.0 * t)
        else:  # the spent crescent crumbles into falling pieces and grains
            for k, (a0, a1) in enumerate(((30.0, 17.0), (9.0, -3.0), (-12.0, -22.0))):
                c2 = (c[0] + 2.0, c[1] + 3.0 + 2.5 * k)
                _crescent(top, c2, 56.0, a0, a1, 1.1, name="grain")
            grains = cv.layer(above=True, outline=False)
            for k in range(6):
                q = W(c, 28.0 - k * 10.0, 50.0 + px.hash01("tk_gr", k) * 8.0)
                x, y = _pt((q[0], q[1] + 6.0 + 7.0 * px.hash01("tk_gy", k)))
                grains.pixel(x, y, SAND.light, name="grain")
                grains.pixel(x, y + 1, SAND.shadow, name="grain")
    if p.crack == 2 and p.sink == 0:
        m = W(H, up - 90, 4.0)
        hc.sparks(fx, m[0] + 3.0, m[1] - 1.0, 0.6, n=4, radius=8.0, colors=(AMBER.light, AMBER.base), seed=3,
                  spread=110.0, aim=40.0)
    if p.hit:
        spark = cv.layer(above=True, outline=False)
        tip = L(BLADE0 + 13.0, 9.5)
        px.impact(spark, tip[0], tip[1], size=5, color=AMBER.light)
    if p.dust is not None:
        d = cv.layer(above=True, outline=True)
        px.dust(d, P[0] - 22.0, cv.gy - 1, p.dust, size=1.2, direction=-1, mat=SAND)
    if p.puff is not None:
        d = cv.layer(above=True, outline=True)
        px.dust(d, P[0] + 18.0, cv.gy - 1, p.puff, size=1.0, direction=1, mat=SAND)
