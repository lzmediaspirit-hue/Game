"""Stone guardian - a squat carved temple lion-dog (foo dog) statue come alive (Earth).

View: side, facing right.  ~55 art px tall to the top of the mane (cell 192).
Parts, back to front: far arm + fist (dark stone), far leg, carved flame-curl tail, torso
(barrel chest with a carved collar and stone bell, moss on the shoulders), near leg,
head group (spiral-curl mane framing the crown, nape and beard, big square face, bulging
glowing jade eye under a heavy brow, pug nose, wide open grin with fangs), near arm + fist.
The shoulders sit behind the head, so the raised arms pass behind the face.
Cracks run over the stone with moss in them; in the windup and slam they glow jade.
Windup: both fists hauled up overhead (held).  Attack: double fist slam, dust + impact on
frame 1.  Death: cracks flare, the pieces slip apart and settle into a heap of blocks.
"""
import math

import pixel as px

SPEC = {
    "id": "stone_guardian",
    "cell": 192,
    "anchor": [96, 168],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette: warm temple stone, violet-grey shadows, moss, jade glow ------------------------
STONE = px.material("sg_stone", "#dcd2b4", "#aaa085", "#777164", "#4c4a52", outline="#141319",
                    thresholds=(0.9, 0.52, 0.16))
DARK = px.material("sg_stone_dark", "#a49c88", "#7b7566", "#57544f", "#383840", outline="#121217",
                   thresholds=(0.9, 0.52, 0.16))
MOSS = px.material("sg_moss", "#b8d46a", "#80a445", "#56793a", "#3a562d", outline="#0d170c")
JADE = px.material("sg_jade", "#e6fff4", "#67d6bd", "#2c9e8f", "#15514f", outline="#0a2027")
MOUTH = px.material("sg_mouth", "#6a3a3a", "#4a2629", "#351c20", "#24141a", outline="#120a0c")
TOOTH = px.rgb("#efe8d2")
CRACK = STONE.deep
GLOW = px.rgb("#67d6bd")
GLOW_CORE = px.rgb("#e6fff4")
ARM = 12.0

# ---- poses --------------------------------------------------------------------------------
# bx, by  body offset       crouch  bend the knees (px)       lean  torso lean (deg, + = fwd)
# head    head tilt (deg)   jaw  0..1 (grin opening)
# fn, ff  near / far fist target: (dx from the hips, height above the ground)
# feet    (dx, lift) near, far      glow  cracks glow jade (0..1)    eye  open|angry|squeeze|dead
# dust    slam dust life    hit  impact    brk  crumble 0..1 (pieces slip apart)   rubble  heap
DEFAULTS = dict(bx=0, by=0, crouch=0, lean=4, head=0, jaw=0.4, fn=(10, 12), ff=(12, 13),
                feet=((0, 0), (0, 0)), glow=0.0, eye="open", dust=None, hit=False, brk=0.0, rubble=False,
                fade=1.0, breathe=0, back=False)

POSE = px.poses(DEFAULTS, {
    "idle": [  # heavy, slow: a 1 px settle, fists sway
        dict(),
        dict(fn=(10, 11), ff=(12, 12), breathe=1),
        dict(fn=(10, 11), ff=(12, 12), breathe=1, crouch=1, jaw=0.5),
        dict(fn=(10, 12), ff=(12, 13), jaw=0.45),
    ],
    "walk": [  # stomping waddle: one leg lifts at a time, body rocks, fists swing opposite
        dict(feet=((3, 0), (-3, 0)), fn=(8, 11), ff=(14, 12), crouch=1),
        dict(feet=((2, 0), (-1, 3)), fn=(9, 12), ff=(13, 13), by=-1, lean=6),
        dict(feet=((0, 0), (1, 2)), fn=(11, 12), ff=(11, 13), lean=6),
        dict(feet=((-3, 0), (3, 0)), fn=(13, 11), ff=(9, 12), crouch=1),
        dict(feet=((-1, 3), (2, 0)), fn=(12, 12), ff=(10, 13), by=-1, lean=2),
        dict(feet=((1, 2), (0, 0)), fn=(10, 12), ff=(12, 13), lean=2),
    ],
    "windup": [  # both fists hauled up overhead, cracks light up - held
        dict(fn=(6, 34), ff=(8, 33), lean=-2, head=4, jaw=0.6, glow=0.4, eye="angry", crouch=1),
        dict(fn=(-3, 56), ff=(-9, 54), lean=-6, head=-2, jaw=0.9, glow=0.8, eye="angry", bx=-1),
        dict(fn=(-3, 59), ff=(-10, 57), lean=-8, head=-4, jaw=1.0, glow=1.0, eye="angry", bx=-2),
    ],
    "attack": [  # slam: fists come over the top and down in front, hit + dust on frame 1
        dict(fn=(8, 57), ff=(3, 56), lean=4, head=-6, jaw=1.0, glow=1.0, eye="angry", back=True),
        dict(fn=(20, 4.6), ff=(18, 4.6), lean=24, head=-12, jaw=0.8, glow=1.0, eye="angry", crouch=5, bx=2,
             dust=0.15, hit=True),
        dict(fn=(20, 4.6), ff=(18, 4.6), lean=24, head=-10, jaw=0.6, glow=0.6, eye="angry", crouch=5, bx=2,
             dust=0.5),
        dict(fn=(15, 8), ff=(15, 9), lean=12, head=-3, jaw=0.4, glow=0.2, crouch=2, bx=1, dust=0.85),
    ],
    "hurt": [  # chips fly, it rocks back, the eye flickers
        dict(bx=-2, lean=-8, head=10, eye="squeeze", fn=(6, 18), ff=(8, 19), jaw=0.7),
        dict(bx=-1, lean=-3, head=4, eye="squeeze", fn=(8, 14), ff=(10, 15)),
    ],
    "death": [  # cracks flare, pieces slip apart, collapse into a heap of blocks, fade
        dict(bx=-2, lean=-6, head=8, eye="squeeze", glow=1.0, jaw=0.8, brk=0.15, fn=(7, 17), ff=(9, 18)),
        dict(bx=-2, lean=-2, head=-8, eye="dead", glow=0.5, brk=0.8, crouch=2, fn=(10, 7), ff=(12, 8)),
        dict(rubble=True, eye="dead"),
        dict(rubble=True, eye="dead", fade=0.6),
        dict(rubble=True, eye="dead", fade=0.3),
    ],
})


# ---- parts --------------------------------------------------------------------------------
def _crack(cv, pts, glow, clip, moss_at=None):
    """Zig-zag crack (1 px) through the stone; a moss tuft sits in it unless it glows."""
    col = GLOW if glow > 0.5 else CRACK
    for a, b in zip(pts, pts[1:]):
        cv.line((math.floor(a[0]), math.floor(a[1])), (math.floor(b[0]), math.floor(b[1])), col, band=None,
                decal=True, clip=clip, name=clip)
    if moss_at is not None and glow <= 0.5:
        q = pts[moss_at]
        cv.ellipse(q[0] + 0.5, q[1] + 0.5, 1.7, 1.1, MOSS, shade="soft", decal=True, clip=clip, name=clip)


def _fist(cv, c, far, sep=False):
    """Heavy carved paw-fist: rounded block, knuckle grooves, thumb pad."""
    mat = DARK if far else STONE
    cv.ellipse(c[0], c[1], 4.6, 4.2, mat, shade="dark" if far else "full", name="fist", sep=sep)
    if not far:
        for k in range(3):
            x, y = math.floor(c[0] + 2), math.floor(c[1] - 2 + k * 1.5)
            cv.line((x, y), (x + 1, y), mat.deep, band=None, decal=True, clip="fist", name="fist")
        cv.ellipse(c[0] - 1.4, c[1] + 2.0, 1.7, 1.2, mat, shade="two", name="fist")


def _arm(cv, sh, fist, far, sep=False, bend=None):
    d = math.hypot(fist[0] - sh[0], fist[1] - sh[1])
    if d > 2 * ARM - 0.5:  # clamp to reach so the fist stays attached
        k = (2 * ARM - 0.5) / d
        fist = (sh[0] + (fist[0] - sh[0]) * k, sh[1] + (fist[1] - sh[1]) * k)
    up = fist[1] < sh[1] - 6
    el = px.ik2(sh, fist, ARM, ARM, bend=bend if bend is not None else (1 if up else -1))
    mat = DARK if far else STONE
    cv.limb([sh, el, fist], [4.0, 3.4, 3.4], mat, shade="dark" if far else "soft", name="arm", sep=sep)
    _fist(cv, fist, far, sep="deep" if not far else False)
    return fist


def _leg(cv, hip, foot, far, sep=False):
    fx, fy = foot
    mat = DARK if far else STONE
    cv.limb([hip, (fx, fy - 3.5)], [5.4, 4.2], mat, shade="dark" if far else "soft", name="leg", sep=sep)
    cv.ellipse(fx + 1.8, fy - 2.4, 5.4, 2.9, mat, shade="dark" if far else "two", name="foot", sep=sep)
    if not far:  # carved toes
        for k in range(3):
            x = math.floor(fx + 2.5 + k * 1.8)
            cv.line((x, math.floor(fy - 2)), (x, math.floor(fy - 1)), mat.deep, band=None, decal=True,
                    clip="foot", name="foot")


CURLS = ((-4.5, -9.5, 3.2), (0.5, -10.6, 3.2), (5.5, -9.8, 2.9), (9.5, -7.6, 2.2), (-8.6, -5.5, 3.3),
         (-10.0, 0.0, 3.3), (-8.8, 5.5, 3.2), (-4.6, 9.2, 3.0), (0.5, 10.4, 2.9), (5.0, 10.0, 2.5))


def _head(cv, Hc, p):
    x, y = Hc
    # curly mane framing the crown, nape and beard
    g = [cv.geom_ellipse(x + cx, y + cy, r, r) for cx, cy, r in CURLS]
    cv.draw_geom(cv.union(*g), DARK, name="mane", sep="deep")
    for cx, cy, r in CURLS:  # spiral groove: a dark hook in each curl
        ix, iy = math.floor(x + cx), math.floor(y + cy)
        cv.pixels([(ix - 1, iy), (ix, iy), (ix, iy + 1)], DARK.deep, name="mane", decal=True, clip="mane")
    # big square face
    face = cv.geom_polygon([(x - 5.5, y - 7.5), (x + 6.5, y - 8.0), (x + 9.5, y - 4.5), (x + 10.0, y + 2.0),
                            (x + 7.0, y + 7.5), (x - 5.0, y + 7.5)])
    cv.draw_geom(face, STONE, name="head", sep="deep")
    # open grin: cavity, hinged lower jaw, fangs
    cv.polygon([(x - 1.0, y + 1.6), (x + 11.0, y + 1.4), (x + 10.0, y + 6.4), (x - 1.0, y + 5.4)], MOUTH,
               shade="two", name="mouth")
    with cv.xform(px.rotate(-20 * p.jaw, (x - 2.0, y + 4.0))):
        cv.polygon([(x - 3.0, y + 3.4), (x + 10.0, y + 3.6), (x + 9.2, y + 7.4), (x + 1.0, y + 9.0),
                    (x - 3.5, y + 7.6)], STONE, shade="two", name="jaw", sep="deep")
        jx, jy = math.floor(x), math.floor(y + 3)
        cv.pixels([(jx + 2, jy), (jx + 5, jy), (jx + 8, jy), (jx + 8, jy - 1)], TOOTH, name="tooth")
    # upper lip / muzzle over the grin, fangs hanging from it
    cv.polygon([(x - 1.5, y - 0.4), (x + 10.5, y - 1.2), (x + 11.2, y + 2.0), (x - 1.0, y + 2.4)], STONE,
               shade="two", name="lip", sep="deep")
    ux, uy = math.floor(x), math.floor(y + 2)
    cv.pixels([(ux + 1, uy + 1), (ux + 4, uy + 1), (ux + 6, uy + 1), (ux + 6, uy + 2), (ux + 9, uy + 1),
               (ux + 9, uy + 2)], TOOTH, name="tooth")
    # pug nose
    cv.ellipse(x + 10.2, y - 2.6, 2.3, 2.0, STONE, shade="soft", name="nose", sep="deep")
    cv.pixel(math.floor(x + 10), math.floor(y - 2), STONE.deep, name="nose")
    # drooping ear tucked into the mane
    cv.ellipse(x - 4.2, y - 3.0, 1.8, 3.0, DARK, angle=-20, shade="two", name="ear", sep="deep")
    # bulging eye socket with the glowing jade eye
    ex, ey = math.floor(x + 2), math.floor(y - 6)
    cv.ellipse(ex + 2.0, ey + 2.0, 3.0, 2.8, STONE, shade="soft", name="eyeball", sep="deep")
    if p.eye in ("open", "angry"):
        cv.stamp([".jj.", "jwJj", "jJJj", ".jj."], ex, ey, {"j": JADE.shadow, "J": GLOW, "w": GLOW_CORE},
                 name="eye")
    elif p.eye == "squeeze":
        cv.stamp(["jJJj"], ex, ey + 2, {"j": JADE.shadow, "J": GLOW}, name="eye")
    else:  # the light goes out
        cv.stamp([".dd.", "dddd", ".dd."], ex, ey + 1, {"d": STONE.deep}, name="eye")
    if p.eye == "angry":
        brow = [(x - 0.5, y - 9.2), (x + 3.5, y - 7.4), (x + 7.0, y - 5.0)]
    else:
        brow = [(x - 0.5, y - 8.6), (x + 3.5, y - 8.2), (x + 7.0, y - 6.4)]
    cv.limb(brow, [1.4, 1.3, 1.0], STONE, shade="two", name="brow", sep="deep")
    _crack(cv, [(x - 3, y - 7), (x - 2, y - 4), (x - 4, y - 1), (x - 3, y + 1)], p.glow, "head", moss_at=2)


def _torso(cv, T, p):
    torso = cv.union(cv.geom_ellipse(T[0], T[1], 11.0, 12.0 + p.breathe * 0.3),
                     cv.geom_ellipse(T[0] + 2.5, T[1] - 4.5, 10.0, 8.5))
    cv.draw_geom(torso, STONE, name="body", sep="deep")
    # carved belly plate with two grooves
    cv.ellipse(T[0] + 5.5, T[1] + 4.0, 4.8, 7.0, STONE.step(-1), shade="two", decal=True, clip="body", name="body")
    for dy in (1.0, 5.0):
        cv.line((math.floor(T[0] + 3), math.floor(T[1] + dy)), (math.floor(T[0] + 8), math.floor(T[1] + dy)),
                STONE.shadow, band=None, decal=True, clip="body", name="body")
    _crack(cv, [(T[0] - 6, T[1] - 7), (T[0] - 4, T[1] - 3), (T[0] - 7, T[1]), (T[0] - 5, T[1] + 4),
                (T[0] - 7, T[1] + 8)], p.glow, "body", moss_at=3)
    _crack(cv, [(T[0] + 1, T[1] + 9), (T[0] + 3, T[1] + 6), (T[0] + 2, T[1] + 3)], p.glow, "body")
    cv.ellipse(T[0] - 4.0, T[1] - 11.0, 4.5, 1.8, MOSS, decal=True, clip="body", name="body")
    # carved collar with a stone bell
    cv.limb([(T[0] + 1.0, T[1] - 12.5), (T[0] + 7.5, T[1] - 8.0), (T[0] + 10.5, T[1] - 3.0)], 1.5, DARK,
            shade="two", decal=True, clip="body", name="body")
    b = (T[0] + 10.0, T[1] - 2.0)
    cv.circle(b[0], b[1], 2.5, STONE, shade="soft", name="bell", sep="deep")
    cv.line((math.floor(b[0] - 1), math.floor(b[1] + 1)), (math.floor(b[0] + 1), math.floor(b[1] + 1)), STONE.deep,
            band=None, decal=True, clip="bell", name="bell")


def _tail(cv, R):
    """Carved flame-curl tail: three stacked curls rising behind the rump."""
    g = [cv.geom_ellipse(R[0] - 2.0, R[1] - 1.0, 3.2, 3.0), cv.geom_ellipse(R[0] - 4.5, R[1] - 5.0, 2.9, 2.8),
         cv.geom_ellipse(R[0] - 3.5, R[1] - 9.2, 2.5, 2.4), cv.geom_limb([R, (R[0] - 3.0, R[1] - 3.0)], 2.2)]
    cv.draw_geom(cv.union(*g), DARK, shade="nolight", name="tail")
    for (dx, dy) in ((-2.0, -1.0), (-4.5, -5.0), (-3.5, -9.2)):
        ix, iy = math.floor(R[0] + dx), math.floor(R[1] + dy)
        cv.pixels([(ix - 1, iy), (ix, iy), (ix, iy + 1)], DARK.deep, name="tail")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    ground = cv.ground
    cv.opacity = p.fade
    if p.rubble:
        _rubble(cv, ground, p)
        return
    X = cv.gx - 5 + p.bx
    hipY = ground - 12.0 + p.crouch + p.by
    T = (X, hipY - 12.0)
    pivot = (X, hipY)
    b = p.brk
    lean = px.rotate(-p.lean, pivot)

    def world(q):  # body-local point -> world, through the lean
        return px.rot_pt(q, -p.lean, pivot)

    def foot(dx, i):
        f = p.feet[i]
        return (X + dx + f[0], ground - f[1])

    def piece(dx, dy):  # crumble: pieces slip apart
        return px.translate(dx * b, dy * b)

    sh_f = world((T[0] + 1.0, T[1] - 10.0))
    sh_n = world((T[0] - 2.5, T[1] - 9.5))
    with cv.xform(piece(-4, 4)):
        _arm(cv, sh_f, (X + p.ff[0], ground - p.ff[1]), far=True)
    with cv.xform(piece(-2, 0)):
        _leg(cv, (X + 3.0, hipY), foot(4.0, 1), far=True)
    with cv.xform(lean):
        with cv.xform(piece(-3, 1)):
            _tail(cv, (X - 9.5, hipY - 4.0))
        with cv.xform(piece(0, 2)):
            _torso(cv, T, p)
    with cv.xform(piece(1, 0)):
        _leg(cv, (X - 1.5, hipY + 1.0), foot(-1.5, 0), far=False, sep="deep")
    if p.back:  # raised overhead: arms stand behind the head so the face stays readable
        fn = _arm(cv, sh_n, (X + p.fn[0], ground - p.fn[1]), far=False, sep="deep")
    with cv.xform(lean):
        Hc = (T[0] + 5.0, T[1] - 17.0)
        with cv.xform(piece(3, 5), px.rotate(p.head, (T[0] + 3.0, T[1] - 10.0))):
            _head(cv, Hc, p)
    if not p.back:
        with cv.xform(piece(4, 6)):  # raised: the elbow flares back so the arm clears the face
            fn = _arm(cv, sh_n, (X + p.fn[0], ground - p.fn[1]), far=False, sep="deep",
                      bend=-1 if p.fn[1] > 45 else None)
    slam = (fn[0] + 3.0, fn[1] + 2.0)
    if p.dust is not None:
        fx = cv.layer(above=True, outline=True)
        px.dust(fx, slam[0] + 3.0, cv.gy - 1, p.dust, size=1.3, direction=1)
        px.dust(fx, slam[0] - 7.0, cv.gy - 1, p.dust, size=1.0, direction=-1)
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, slam[0] + 1, slam[1] - 3, size=4)
    if action == "hurt" and frame == 0:  # stone chips knocked off the mane
        fx = cv.layer(above=True, outline=True)
        for (dx, dy) in ((15.0, -48.0), (19.0, -44.0), (14.0, -52.0)):
            fx.rect(X + dx, ground + dy, 1.5, 1.5, STONE, shade="soft", name="chip")
    if action == "death" and frame == 0:  # jade sparks spitting from the cracks
        fx = cv.layer(above=True, outline=False)
        for (dx, dy) in ((-12.0, -30.0), (-14.0, -22.0), (-3.0, -44.0)):
            fx.pixel(math.floor(X + dx), math.floor(ground + dy), GLOW, name="spark")
            fx.pixel(math.floor(X + dx) - 1, math.floor(ground + dy) + 1, JADE.shadow, name="spark")


def _block(cv, x, y, w, h, ang, mat=STONE, moss=False):
    """One fallen masonry block (rotated rectangle with chamfered top corners)."""
    c = (x + w / 2, y + h / 2)
    with cv.xform(px.rotate(ang, c)):
        cv.polygon([(x + 0.8, y), (x + w - 0.8, y), (x + w, y + 0.8), (x + w, y + h), (x, y + h), (x, y + 0.8)], mat,
                   name="block", sep="deep")
        if moss:
            cv.ellipse(x + w * 0.4, y + 0.6, w * 0.35, 1.0, MOSS, decal=True, clip="block", name="block")


def _rubble(cv, ground, p):
    """A heap of broken blocks; the lion-dog head rests on top, its light gone."""
    cv.snap_ground = True
    X = cv.gx - 4
    g = ground + 0.5
    _block(cv, X - 17, g - 7, 9, 7, 4, DARK)
    _block(cv, X + 9, g - 6, 8, 6, -6, DARK, moss=True)
    _block(cv, X - 9, g - 9, 11, 9, -3, STONE, moss=True)
    _block(cv, X + 2, g - 8, 8, 8, 8, STONE)
    _block(cv, X - 14, g - 13, 7, 6, 14, STONE)
    _block(cv, X + 15, g - 4, 5, 4, 20, STONE)
    _block(cv, X - 22, g - 4, 5, 4, -12, DARK)
    Hc = (X + 2.0, g - 19.0)
    with cv.xform(px.rotate(-16, Hc)):
        _head(cv, Hc, p)
