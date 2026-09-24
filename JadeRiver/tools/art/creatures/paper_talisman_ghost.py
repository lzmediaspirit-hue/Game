"""Paper talisman ghost - a floating spirit made of layered, yellowed paper talismans (Soul).

View: side, facing right (slight 3/4 on the mask).  ~40 art px tall, flying (cell 128,
anchor at the body centre).
Parts, back to front: soul wisps (FX), back strips (shadowed), the far arm bundle, the hooded
head dome of wrapped strips, the front skirt strips with ragged fluttering ends, the near arm
bundle, the face talisman (two dark eye holes glowing violet, a red ink seal), red ink
glyphs on every strip.
Walk: drifting flutter.  Windup: the arm bundles fan out behind like a peacock (held).
Attack: the near bundle flings a talisman on frame 1 (the engine draws the projectile).
Death: the strips come loose, scatter and fade.
"""
import math

import pixel as px

SPEC = {
    "id": "paper_talisman_ghost",
    "cell": 128,
    "anchor": [64, 64],
    "flying": True,
    "hit_frame": 1,
}

# ---- palette: aged talisman paper, cinnabar ink, soul violet --------------------------------
PAPER = px.material("talisman", "#fff4d2", "#ecd8a0", "#c4a86c", "#8c7246", outline="#24141f",
                    thresholds=(0.88, 0.45, 0.1))
OLD = px.material("talisman_old", "#e6d4a0", "#cdb67c", "#a28a58", "#6e5a3a", outline="#24141f",
                  thresholds=(0.88, 0.45, 0.1))
INKRED = px.material("cinnabar", "#f08070", "#cf3a3a", "#962430", "#5e1624", outline="#24141f")
VOID = px.rgb("#1a0f2a")
GLOW = px.rgb("#b89cf0")
GLOW_HI = px.rgb("#efe6ff")
WISP = px.material("soul_wisp", "#efe6ff", "#b89cf0", "#8a68c8", "#5a4290", outline="#1a0f2a")

# ---- poses --------------------------------------------------------------------------------
# bx, by   body offset (bob)    tilt  body lean (deg, - = leaning forward)
# ph       flutter phase        amp   flutter amplitude (px at the strip ends)
# fan      arm bundles fanned out 0..1        arm  near arm swing (deg, + = raised back)
# held     the near bundle still holds its top talisman     eye  open|angry|squeeze|dead
# scatter  strips flying apart 0..1        fade  opacity       glow  eye glow boost
DEFAULTS = dict(bx=0, by=0, tilt=0, ph=0.0, amp=1.0, fan=0.0, arm=0.0, held=True, eye="open", scatter=0.0,
                fade=1.0, glow=0, trail=0.0)

POSE = px.poses(DEFAULTS, {
    "idle": [  # hovering, strips breathing in an unseen draft
        dict(ph=0.0),
        dict(ph=1.6, by=-1),
        dict(ph=3.1, by=-1),
        dict(ph=4.7, by=0),
    ],
    "walk": [  # drifting forward, strips streaming back
        dict(ph=0.0, tilt=-8, trail=1.0, amp=1.4),
        dict(ph=1.05, tilt=-9, trail=1.0, amp=1.4, by=-1),
        dict(ph=2.1, tilt=-8, trail=1.0, amp=1.4, by=-1),
        dict(ph=3.15, tilt=-8, trail=1.0, amp=1.4),
        dict(ph=4.2, tilt=-9, trail=1.0, amp=1.4, by=1),
        dict(ph=5.25, tilt=-8, trail=1.0, amp=1.4, by=1),
    ],
    "windup": [  # talismans fan out behind, eyes flare - held
        dict(fan=0.4, ph=1.0, eye="angry", glow=1, tilt=4, bx=-1),
        dict(fan=0.85, ph=2.0, eye="angry", glow=2, tilt=8, bx=-2, by=-1),
        dict(fan=1.0, ph=2.6, eye="angry", glow=2, tilt=9, bx=-2, by=-1),
    ],
    "attack": [  # fling: the near bundle whips forward and releases a talisman on frame 1
        dict(fan=0.8, arm=30, ph=3.0, eye="angry", glow=2, tilt=6, bx=-2),
        dict(fan=0.3, arm=-10, held=False, ph=3.6, eye="angry", glow=2, tilt=-10, bx=2),
        dict(fan=0.1, arm=-10, held=False, ph=4.2, eye="angry", glow=1, tilt=-6, bx=1),
        dict(fan=0.0, arm=-5, held=False, ph=4.8, tilt=-2),
    ],
    "hurt": [
        dict(bx=-3, tilt=14, ph=2.0, amp=2.2, eye="squeeze", trail=-0.8),
        dict(bx=-2, tilt=8, ph=2.6, amp=1.6, eye="squeeze", trail=-0.4),
    ],
    "death": [  # the binding fails: strips come loose, scatter and fade
        dict(bx=-2, tilt=12, ph=2.0, amp=2.4, eye="squeeze", trail=-0.8),
        dict(scatter=0.3, ph=3.0, amp=2.0, eye="dead"),
        dict(scatter=0.6, ph=4.0, amp=2.0, eye="dead", fade=0.8),
        dict(scatter=0.85, ph=5.0, amp=2.0, eye="dead", fade=0.55),
        dict(scatter=1.0, ph=6.0, amp=2.0, eye="dead", fade=0.3),
    ],
})


# ---- parts --------------------------------------------------------------------------------
def _strip(cv, top, ang, length, width, sway, mat, name, shade="two", glyph=True, seal=False, cut=1.0):
    """A hanging talisman strip: a narrow, slightly bent quad with a slanted torn end,
    red ink glyphs down its centre and an optional seal."""
    d = (math.cos(math.radians(ang)), -math.sin(math.radians(ang)))
    n = (-d[1], d[0])
    mid = (top[0] + d[0] * length * 0.5 + n[0] * sway * 0.4, top[1] + d[1] * length * 0.5 + n[1] * sway * 0.4)
    end = (top[0] + d[0] * length + n[0] * sway, top[1] + d[1] * length + n[1] * sway)
    h = width / 2
    left = [(top[0] + n[0] * h, top[1] + n[1] * h), (mid[0] + n[0] * h, mid[1] + n[1] * h),
            (end[0] + n[0] * h + d[0] * cut, end[1] + n[1] * h + d[1] * cut)]
    right = [(end[0] - n[0] * h - d[0] * cut, end[1] - n[1] * h - d[1] * cut), (mid[0] - n[0] * h, mid[1] - n[1] * h),
             (top[0] - n[0] * h, top[1] - n[1] * h)]
    cv.polygon(left + right, mat, shade=shade, name=name, sep="deep")
    if glyph:  # calligraphy: one short vertical stroke and a dot in red ink
        a = px.lerp_pt(top, mid, 0.5)
        b = px.lerp_pt(top, mid, 0.72)
        cv.line((math.floor(a[0]), math.floor(a[1])), (math.floor(b[0]), math.floor(b[1])), INKRED.shadow, name=name,
                decal=True, clip=name)
        c = px.lerp_pt(mid, end, 0.3)
        cv.line((math.floor(c[0] - n[0] * 0.6), math.floor(c[1] - n[1] * 0.6)),
                (math.floor(c[0] + n[0] * 0.6), math.floor(c[1] + n[1] * 0.6)), INKRED.shadow, name=name,
                decal=True, clip=name)
    if seal:  # square cinnabar seal stamp near the top
        c = px.lerp_pt(top, mid, 0.35)
        cv.rect(math.floor(c[0]) - 1, math.floor(c[1]) - 1, 3, 3, INKRED, shade="two", name=name, decal=True,
                clip=name)
    return end


def _sway(p, k, depth):
    """Flutter offset for strip k (grows toward the strip end)."""
    return p.amp * depth * math.sin(p.ph + k * 1.3) - p.trail * depth * 1.2


def _bundle(cv, root, base_ang, spread, lengths, p, key, far):
    """A fan of 3 strips (an 'arm') hinged at root."""
    mat = OLD if far else PAPER
    ends = []
    for j, ln in enumerate(lengths):
        a = base_ang + (j - 1) * spread
        ends.append(_strip(cv, root, a, ln, 3.2, _sway(p, key + j, 1.0), mat, f"arm{key}{j}",
                           shade="nolight" if far else "two", seal=(j == 1 and not far)))
    return ends


def _face(cv, H, p):
    """The face talisman: a broad strip over the hood with two eye holes and a seal."""
    top = (H[0] + 3.5, H[1] - 6.0)
    _strip(cv, top, -86, 15.0, 7.0, 0.3 * math.sin(p.ph), PAPER, "mask", shade="two", glyph=False, cut=1.5)
    # eye holes: dark voids with a violet soul-light deep inside
    for ex in (0.0, 4.5):
        x, y = math.floor(H[0] + ex), math.floor(H[1] - 4.0)
        if p.eye == "dead":
            cv.stamp(["v.v", ".v.", "v.v"], x - 1 + (ex > 2), y, {"v": VOID}, name="eye")
        elif p.eye == "squeeze":
            cv.stamp(["vvv", ".v."], x - 1 + (ex > 2), y + 1, {"v": VOID}, name="eye")
        else:
            rows = (["vv", "vv", "vg", "vv"] if p.glow == 0 else
                    ["vv", "vg", "gh", "vv"] if p.glow == 1 else ["vg", "gh", "hh", "vg"])
            cv.stamp(rows, x, y, {"v": VOID, "g": GLOW, "h": GLOW_HI}, name="eye")
            if p.eye == "angry":  # torn, slanted brows in red ink
                pts = [(x - 1, y - 2), (x, y - 1), (x + 1, y - 1)] if ex < 2 else [(x, y - 1), (x + 1, y - 1), (x + 2, y - 2)]
                cv.pixels(pts, INKRED.base, name="brow")
    # big cinnabar seal below the eyes, like a stamped mouth
    sx, sy = math.floor(H[0] + 2), math.floor(H[1] + 2)
    cv.stamp(["rrrr", "rllr", "rrlr", "rrrr"], sx, sy, {"r": INKRED.base, "l": INKRED.light}, name="seal")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    O = (cv.gx + p.bx, cv.gy + p.by)  # body centre (anchor)
    s = p.scatter
    rot = px.rotate(p.tilt, (O[0], O[1] - 6))

    def spread(k, dx, dy, spin=0):  # death: pieces fly apart from the centre
        if s <= 0:
            return px.translate(0, 0)
        return px.translate(dx * s * 0.8, dy * s * 0.6 + 2 * s * s) @ px.rotate(spin * s, (O[0] + dx * 0.3, O[1] + dy * 0.3))

    if s <= 0 and p.eye != "dead":  # soul wisps drifting up behind
        fx = cv.layer(above=False, outline=True)
        for k, (dx, dy) in enumerate(((-10.0, -16.0), (9.0, -19.0))):
            t = (p.ph * 0.6 + k * 0.5) % 1.0
            fx.circle(O[0] + dx + math.sin(p.ph + k) * 1.0, O[1] + dy - t * 3.0, 1.1 - 0.3 * t, WISP, shade="soft",
                      name="wisp")
    with cv.xform(rot):
        H = (O[0] + 1.0, O[1] - 9.0)  # head centre
        # back strips (shadowed, behind everything)
        for k, (dx, ln, a) in enumerate(((-7.0, 22.0, -98), (-3.5, 25.0, -95), (1.5, 24.0, -92), (5.5, 20.0, -88))):
            with cv.xform(spread(k, -14 + k * 6, 4 + k * 2, 40 - k * 25)):
                _strip(cv, (O[0] + dx, O[1] - 6.0), a - p.trail * 8, ln, 3.4, _sway(p, k, 1.4), OLD, f"back{k}",
                       shade="nolight", glyph=(k % 2 == 0))
        # far arm bundle (fans up and back in the windup)
        with cv.xform(spread(10, -16, -6, 60)):
            fa = -120 - 110 * p.fan
            _bundle(cv, (O[0] - 5.0, O[1] - 5.0), fa - p.trail * 10, 16 + 16 * p.fan, (13.0, 15.0, 12.0), p, 10, True)
        def near_bundle():
            with cv.xform(spread(50, 14, 0, -70)):
                na = -70 + 135 * p.fan + p.arm
                lengths = (12.0, 15.0, 11.0) if p.held else (12.0, 7.0, 11.0)
                return _bundle(cv, (O[0] + 4.0, O[1] - 3.0), na - p.trail * 10, 14 + 14 * p.fan, lengths, p, 50, False)
        behind = p.fan > 0.3 and p.arm >= 0
        if behind:  # fanned up and back: the bundle stands behind the head
            ends = near_bundle()
        # hooded head: a dome of wrapped strips
        with cv.xform(spread(20, 2, -14, -30)):
            hood = cv.union(cv.geom_ellipse(H[0], H[1], 8.0, 7.5), cv.geom_ellipse(H[0] - 1.5, H[1] + 4.0, 7.0, 5.0))
            cv.draw_geom(hood, PAPER, name="hood", sep="deep")
            for dx in (-5.0, -2.0, 1.0):  # seams between the wrapped strips
                cv.line((math.floor(H[0] + dx), math.floor(H[1] - 7)), (math.floor(H[0] + dx - 1), math.floor(H[1] + 7)),
                        PAPER.step(1), band=None, decal=True, clip="hood", name="hood")
            cv.line((math.floor(H[0] - 6), math.floor(H[1] - 1)), (math.floor(H[0] - 4), math.floor(H[1] - 1)),
                    INKRED.base, decal=True, clip="hood", name="hood")
        # front skirt strips with ragged, fluttering ends
        for k, (dx, ln, a) in enumerate(((-5.0, 20.0, -96), (-1.0, 23.0, -92), (3.0, 19.0, -86))):
            with cv.xform(spread(30 + k, -8 + k * 8, 8, -50 + k * 40)):
                _strip(cv, (O[0] + dx, O[1] - 1.0), a - p.trail * 6, ln - 3 * s, 3.6, _sway(p, 30 + k, 1.2), PAPER,
                       f"skirt{k}", seal=(k == 1))
        # the face talisman
        with cv.xform(spread(40, 6, -12, 20)):
            _face(cv, H, p)
        if not behind:  # near arm bundle: rests down the front, flings forward
            ends = near_bundle()
        release = cv.tp(ends[1])
    if action == "attack" and frame == SPEC["hit_frame"]:
        top = cv.layer(above=True, outline=False)
        px.impact(top, release[0] + 2, release[1], size=3, color=GLOW, core=GLOW_HI)
    if action == "windup" or (action == "attack" and frame == 0):  # soul-fire licking along the fanned strips
        fx2 = cv.layer(above=True, outline=True)
        for k, (dx, dy) in enumerate(((-15.0, -12.0), (-12.0, -20.0), (6.0, -22.0), (12.0, -16.0))):
            if k >= frame + 2 and action == "windup":
                continue
            r = 1.0 + 0.4 * ((k + frame) % 2)
            fx2.circle(O[0] + dx, O[1] + dy, r, WISP, shade="soft", name="wisp")
