"""Ironclaw mole - plump velvet-furred mole with a pink star nose and huge iron-grey
digging claws (Earth element).

View: side, facing right.  ~22 art px tall, ~30 long (claws included).
Parts, back to front: far digging paw (dark), stub tail, hind feet, velvet body (rump +
tapering snout shaded as one form, a violet sheen along the back), pink star nose with
twitching feelers, tiny bead eye, near digging paw (broad palm, four long curved iron
claws with a bright glint).  Everything below the ground line is hidden when it digs;
a dirt mound marks the hole.  FX: dust, flying clods, impact.
"""
import math


import pixel as px

SPEC = {
    "id": "ironclaw_mole",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette: violet-black velvet, pink star nose, iron claws, brown dirt ----------------
FUR = px.material("mole_fur", "#7c7189", "#4b4356", "#332d3d", "#221e2a", outline="#0b090e",
                  thresholds=(0.88, 0.52, 0.2))
SHEEN = px.material("mole_sheen", "#9a90a8", "#6c637a", "#4a4357", "#332d3d", outline="#0b090e")
PINK = px.material("mole_pink", "#ffc4c4", "#ec8f98", "#b95f70", "#7c3e4e", outline="#1f0c12")
IRON = px.material("mole_iron", "#e2e7ea", "#9aa3aa", "#646d76", "#3d454d", outline="#0c1014",
                   thresholds=(0.84, 0.5, 0.2))
PALM = px.material("mole_palm", "#d99aa0", "#b0707c", "#80505c", "#553644", outline="#1a0c12")
DIRT = px.material("mole_dirt", "#b89163", "#8a6841", "#5f4830", "#3f3023", outline="#1a120b",
                   thresholds=(0.86, 0.5, 0.2))
CLOD = px.material("mole_clod", "#d2ad7a", "#a8835a", "#7a5d3f", "#523f2d", outline="#2a1d12")

# ---- poses --------------------------------------------------------------------------------
# bx, by  body offset       rot  pitch (deg, - = nose down)     sink  rows hidden below ground
# pn, pf  near / far paw (dx, dy from rest, claw angle deg: 0 = forward, - = down)
# feet    hind-foot lift (near, far)   nose  star-nose twitch 0..1   eye  open|angry|squeeze|dead
# mound   dirt mound height (0 = none) at mound_x    dust  dust life    clods  clod burst life
# flip    on its back   fade  opacity   hit  impact at the claws
DEFAULTS = dict(bx=0, by=0, rot=0, pn=(0, 0, -30), pf=(0, 0, -30), feet=(0, 0), nose=0.0, eye="open",
                mound=0.0, mound_x=10.0, dust=None, clods=None, flip=False, fade=1.0, hit=False, breathe=0.0,
                sink=False)

POSE = px.poses(DEFAULTS, {
    "idle": [  # sniffing: the star nose twitches, claws flex
        dict(),
        dict(nose=1.0, breathe=0.4, pn=(0, 0, -24)),
        dict(nose=0.0, breathe=0.6, pn=(0, -1, -18)),
        dict(nose=1.0, breathe=0.2, pn=(0, 0, -26)),
    ],
    "walk": [  # waddling shuffle: paws paddle in turn, hind feet scuff, dust kicks back
        dict(pn=(2, -1, -20), pf=(-2, 0, -40), feet=(0, 1), dust=0.2),
        dict(pn=(1, 0, -30), pf=(-1, 0, -35), by=-1, nose=1.0, dust=0.45),
        dict(pn=(-1, 0, -40), pf=(1, -1, -25), feet=(1, 0), dust=0.7),
        dict(pn=(-2, 0, -40), pf=(2, -1, -20), feet=(1, 0), dust=0.2),
        dict(pn=(-1, 0, -35), pf=(1, 0, -30), by=-1, nose=1.0, dust=0.45),
        dict(pn=(1, -1, -25), pf=(-1, 0, -40), feet=(0, 1), dust=0.7),
    ],
    "windup": [  # digs in nose-first and dives half under, throwing up a mound - held
        dict(rot=-18, bx=1, pn=(2, 2, -70), pf=(1, 2, -70), eye="angry", mound=2.5, mound_x=14.0, dust=0.3,
             clods=0.2, sink=True),
        dict(rot=-38, bx=3, by=3, pn=(2, 3, -80), pf=(1, 3, -80), eye="angry", mound=4.0, mound_x=15.0,
             dust=0.55, clods=0.5, sink=True),
        dict(rot=-44, bx=4, by=6, pn=(2, 3, -80), pf=(1, 3, -80), eye="angry", mound=5.0, mound_x=15.0,
             dust=0.8, clods=0.8, sink=True, feet=(2, 1)),
    ],
    "attack": [  # bursts up out of the earth ahead, claws raised, rakes on frame 1, lands
        dict(rot=38, bx=8, by=4, pn=(1, -6, 60), pf=(0, -5, 70), eye="angry", mound=4.5, mound_x=16.0,
             clods=0.15, sink=True),
        dict(rot=20, bx=10, by=-4, pn=(3, -5, 30), pf=(2, -6, 45), eye="angry", mound=3.0, mound_x=14.0,
             clods=0.5, hit=True),
        dict(rot=-6, bx=11, pn=(3, 1, -50), pf=(2, 1, -45), eye="angry", mound=2.0, mound_x=13.0, dust=0.3,
             sink=True),
        dict(bx=10, pn=(1, 0, -35), pf=(0, 0, -35), dust=0.6),
    ],
    "hurt": [
        dict(bx=-3, rot=12, pn=(-1, -4, 40), pf=(-2, -4, 50), eye="squeeze", feet=(1, 1)),
        dict(bx=-2, rot=5, pn=(0, -2, 10), pf=(-1, -2, 20), eye="squeeze"),
    ],
    "death": [  # reels, flops over onto its back, iron claws fall limp, fades
        dict(bx=-3, by=-2, rot=14, pn=(-1, -4, 40), pf=(-2, -4, 50), eye="squeeze", feet=(1, 1)),
        dict(bx=-3, rot=-70, pn=(1, 2, -90), pf=(0, 2, -90), eye="dead"),
        dict(bx=-3, flip=True, pn=(1, 1, -60), pf=(0, 1, -50), eye="dead"),
        dict(bx=-3, flip=True, pn=(1, 2, -80), pf=(0, 2, -75), eye="dead", fade=0.6),
        dict(bx=-3, flip=True, pn=(1, 2, -85), pf=(0, 2, -80), eye="dead", fade=0.3),
    ],
})

PAW_N = (10.0, 5.5)  # paw rest positions relative to the body centre
PAW_F = (8.2, 4.6)


def _paw(cv, C, rest, off, far, ground=None):
    """Big spade paw: short arm, pink palm turned outward, four long curved iron claws.
    With ``ground`` set, the whole paw is lifted so no claw tip sinks below it."""
    dx, dy, ang = off
    P = (C[0] + rest[0] + dx, C[1] + rest[1] + dy)

    def claw_pts(P):
        out = []  # three long hooked claws fanned along the palm's front edge
        for k in (1, 0, -1):
            base = px.polar(px.polar(P, ang, 1.8), ang + 90, 1.9 * k)
            mid = px.polar(base, ang + 12 * k, 3.4)
            tip = px.polar(mid, ang + 12 * k - 42, 2.8)
            out.append((base, mid, tip))
        return out
    if ground is not None:
        low = max(t[1] for _, _, t in claw_pts(P))
        if low > ground:
            P = (P[0], P[1] - (low - ground))
    sh = (C[0] + rest[0] - 4.0, C[1] + rest[1] - 3.5)
    shade = "dark" if far else "soft"
    cv.limb([sh, P], [2.8, 2.4], FUR, shade="dark" if far else "two", name="arm", sep=False if far else "deep")
    cv.ellipse(P[0], P[1], 3.4, 2.8, PALM, angle=ang, shade="dark" if far else "two", name="palm",
               sep=False if far else "deep")
    tips = []
    for base, mid, tip in claw_pts(P):
        cv.limb([base, mid, tip], [1.15, 0.9, 0.4], IRON, shade=shade, name="claw",
                sep=False if far else "deep")
        tips.append(tip)
    if not far:  # bright glint on the top claw
        b, m, t = claw_pts(P)[0]
        cv.pixel(math.floor(m[0]), math.floor(m[1]) - 1, IRON.light, name="claw")
    return tips


def _star(cv, tip, ang, twitch):
    """Pink star nose: a fleshy knob ringed with short feelers that splay when it sniffs."""
    cv.circle(tip[0], tip[1], 1.7, PINK, shade="soft", name="nose", sep="deep")
    for k in range(5):
        a = ang - 80 + k * 40
        ln = 1.6 + (0.8 if (k + int(twitch * 2)) % 2 == 0 else 0.2) * (0.6 + twitch * 0.4)
        e = px.polar(tip, a, 1.2 + ln)
        cv.limb([px.polar(tip, a, 1.0), e], [0.55, 0.45], PINK, shade="two", name="nose")


def _mound(cv, x, ground, h, rx):
    """Dirt heap at the hole: a flat-bottomed dome of earth with a few stones."""
    if h <= 0:
        return
    cut = cv.mask_polygon([(x - 20, ground + 0.5), (x + 20, ground + 0.5), (x + 20, ground + 10),
                           (x - 20, ground + 10)])
    cv.ellipse(x, ground + 0.5, rx, h, DIRT, name="mound", minus=cut, sep="deep")
    for (dx, dy) in ((-rx * 0.4, -h * 0.45), (rx * 0.3, -h * 0.6), (rx * 0.1, -h * 0.25)):
        cv.pixel(math.floor(x + dx), math.floor(ground + dy), DIRT.light, name="mound", clip="mound")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    ground = cv.ground
    C = (cv.gx - 3 + p.bx, ground - 10.3 + p.by)
    cv.opacity = p.fade
    xf = [px.rotate(p.rot, (C[0] + 6, ground))] if p.rot and not p.flip else []
    if p.flip:
        xf = [px.flip_y(C[1])]
    if p.flip or (action in ("death", "hurt") and p.rot):
        cv.snap_ground = True
    br = p.breathe
    with cv.xform(*xf):
        gclamp = ground if not xf else None
        _paw(cv, C, PAW_F, p.pf, far=True, ground=gclamp)
        # stub tail and small pink hind feet under the rump
        cv.limb([(C[0] - 11.0, C[1] + 1.0), (C[0] - 14.0, C[1] - 0.5)], [1.2, 0.7], PINK, shade="two", name="tail")
        for dx, lift, far in ((-4.0, p.feet[1], True), (-6.5, p.feet[0], False)):
            fy = C[1] + 9.1 - lift
            cv.limb([(C[0] + dx, C[1] + 5.5), (C[0] + dx + 0.5, fy - 0.6)], [1.6, 1.2], FUR, shade="dark" if far else "two",
                    name="leg")
            cv.limb([(C[0] + dx - 0.5, fy), (C[0] + dx + 2.2, fy)], [0.85, 0.7], PALM, shade="dark" if far else "two",
                    name="foot")
        # velvet body: round rump + tapering snout as one form
        body = cv.union(cv.geom_ellipse(C[0] - 1.5, C[1] - br * 0.4, 10.8, 9.0 + br * 0.4),
                        cv.geom_limb([(C[0] + 5.5, C[1] + 0.5), (C[0] + 10.5, C[1] + 1.5), (C[0] + 14.0, C[1] + 2.0)],
                                     [5.2, 3.2, 1.6]),
                        weights=[1.0, 0.7])
        cv.draw_geom(body, FUR, name="body", sep="deep")
        # soft violet sheen along the back (velvet catching the light)
        cv.limb([(C[0] - 8.5, C[1] - 5.0), (C[0] - 2.0, C[1] - 8.0), (C[0] + 4.5, C[1] - 5.8), (C[0] + 9.0, C[1] - 1.8)],
                0.7, SHEEN, shade="flat", decal=True, clip="body")
        cv.pixels([(math.floor(C[0] - 3), math.floor(C[1] - 8.2)), (math.floor(C[0] - 2), math.floor(C[1] - 8.2))],
                  SHEEN.light, name="sheen", clip="body")
        _star(cv, (C[0] + 15.0, C[1] + 2.0), 0, p.nose)
        # tiny bead eye, half-hidden in fur
        ex, ey = math.floor(C[0] + 8.5), math.floor(C[1] - 1.5)
        if p.eye == "squeeze":
            cv.pixels([(ex - 1, ey), (ex, ey + 1), (ex + 1, ey)], px.INK, name="eye")
        elif p.eye == "dead":
            cv.stamp(["k.k", ".k.", "k.k"], ex - 1, ey - 1, {"k": PINK.light}, name="eye")
        else:
            cv.stamp(["gk"], ex, ey, {"g": px.GLINT, "k": px.INK}, name="eye")
            if p.eye == "angry":
                cv.pixels([(ex - 1, ey - 1), (ex, ey - 1), (ex + 1, ey)], px.INK, name="brow")
        tips = _paw(cv, C, PAW_N, p.pn, far=False, ground=gclamp)
        tip = cv.tp(max(tips, key=lambda q: q[0]))
    if p.sink:  # dug in: everything below the surface is hidden
        m = cv.filled & (cv.Y > ground + 0.5)
        cv.fill(m, px.flat("#000000"), erase=True)
    _mound(cv, cv.gx - 3 + p.mound_x, ground, p.mound, 3.5 + p.mound * 0.9)
    if p.dust is not None:
        fx = cv.layer(above=True, outline=True)
        px.dust(fx, C[0] - 6, cv.gy - 1, p.dust, size=0.75, direction=-1)
    if p.clods is not None:
        cl = cv.layer(above=True, outline=True)
        t = p.clods
        ox = cv.gx - 3 + p.mound_x
        for k, (vx, vy, r) in enumerate(((0.6, 3.2, 1.1), (1.8, 2.2, 0.9), (2.6, 3.0, 0.8))):
            x = ox + vx * 4.5 * t
            y = ground - 1.0 - (vy * 5.0 * t - 4.0 * t * t)
            cl.circle(x, y, r, CLOD, shade="soft", name="clod")
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, tip[0] + 1.5, tip[1] - 1.0, size=3)
