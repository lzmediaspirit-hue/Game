"""The top-down foes (art bible §8, the plan's §1.4): the prototype room's early monsters, redrawn from their side-view
sheets (art/creatures/) for the three-quarter view in eight facings.

Each creature is built as a small sculpture of ellipsoids in its own frame (a forward, b to its left, c up, in art px)
and posed per action and frame. The sculpture is turned to each drawn facing (S, SE, E, NE, N; SW, W and NW mirror in
the room view), seen from a camera to the south, 35 degrees above the ground, and lit by the room's sun
(upper left). Every pixel takes a step of its material's ramp by its light; a part tucked behind a nearer part takes
one step darker along the seam, so legs, claws and bodies separate by value; eyes, noses, tusks and stripes are placed
on the surface as marks; the sprite takes the prop outline (art bible §4). No randomness and no filtering: a rebuild is
byte-identical.

The creatures keep what makes them recognisable in the side view: the mud crab's brown shell with pale patches, black
eye stalks and jade-tipped claws; the reed rat's grey-brown coat, pink ears and feet, red eyes and green segmented reed
tail; the boarlet's warm brown hide with pale stripes along its back, a bristle crest, a pink snout and small tusks.

Actions (the side view's catalogue in data/creature_art.json): idle, walk, windup, attack (its strike on `hit_frame`),
hurt and death, at the frame rates in ACTIONS.
"""
from __future__ import annotations

import math

from canvas import Img
from palette import c

CELL = (48, 40)
FOOT = (24, 27)
DIRS = ["s", "se", "e", "ne", "n"]
MIRROR = {"sw": "se", "w": "e", "nw": "ne"}
ANGLE = {"s": 90.0, "se": 45.0, "e": 0.0, "ne": -45.0, "n": -90.0}   # on the ground: east 0, south 90
# action: frames, fps, loop
ACTIONS = {"idle": (4, 6, True), "walk": (4, 10, True), "windup": (2, 8, False), "attack": (3, 12, False),
           "hurt": (2, 10, False), "death": (4, 8, False)}
HIT_FRAME = 1
SPECIES = ["mudshell_crab", "reedtail_rat", "wild_boarlet"]

ELEV = math.radians(35.0)
R = (1.0, 0.0, 0.0)                                  # screen right, in the world (east, south, up)
D = (0.0, math.sin(ELEV), -math.cos(ELEV))           # screen down
V = (0.0, -math.cos(ELEV), -math.sin(ELEV))          # the view, into the scene


def _norm(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return tuple(x / n for x in v)


# Lit from the screen's upper left like the props (art bible §8): from the west, high, a little toward the camera, so
# a creature's front takes its base colour and its east side the shade.
LIGHT = _norm((-0.6, 0.25, 0.75))


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def rot(axis: str, deg: float):
    """A rotation matrix (rows) about the creature's a, b or c axis."""
    t = math.radians(deg)
    co, si = math.cos(t), math.sin(t)
    if axis == "c":      # yaw: turns a toward b
        return ((co, -si, 0.0), (si, co, 0.0), (0.0, 0.0, 1.0))
    if axis == "b":      # pitch: positive lifts a (the nose) up
        return ((co, 0.0, -si), (0.0, 1.0, 0.0), (si, 0.0, co))
    return ((1.0, 0.0, 0.0), (0.0, co, -si), (0.0, si, co))   # roll about a: positive lifts the left side


def apply(m, v):
    return (dot(m[0], v), dot(m[1], v), dot(m[2], v))


def mat_mul(m, n):
    cols = [(n[0][k], n[1][k], n[2][k]) for k in range(3)]
    return tuple(tuple(dot(m[i], cols[k]) for k in range(3)) for i in range(3))


IDENT = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


class Part:
    """An ellipsoid in the creature's frame: centre, radii along its own axes (turned by `m`), a material and a group
    (parts of one group do not darken each other's seams)."""

    def __init__(self, at, radii, mat: str, group: str, m=IDENT, pattern=None):
        self.at, self.radii, self.mat, self.group, self.m, self.pattern = at, radii, mat, group, m, pattern


def chain(p0, p1, r0: float, r1: float, n: int, mat: str, group: str, mats=None) -> list:
    """Spheres from p0 to p1 (a leg, a stalk, a tail), `mats` alternating by index when given (a segmented tail)."""
    out = []
    for k in range(n):
        u = k / max(1, n - 1)
        p = tuple(p0[i] + (p1[i] - p0[i]) * u for i in range(3))
        r = r0 + (r1 - r0) * u
        out.append(Part(p, (r, r, r), mats[k % len(mats)] if mats else mat, group))
    return out


class Pose:
    """A posed creature: its parts, marks (points on the surface drawn as single pixels) and a body transform (a roll
    or a lift for a fall), all in the creature's frame."""

    def __init__(self):
        self.k = 1.0              # the creature's size against the sculpture's art px
        self.parts: list = []
        self.marks: list = []     # (point, colour)
        self.m = IDENT
        self.shift = (0.0, 0.0, 0.0)

    def add(self, *parts) -> None:
        for p in parts:
            if isinstance(p, list):
                self.parts += p
            else:
                self.parts.append(p)

    def mark(self, at, col) -> None:
        self.marks.append((at, col))


# ================================================================================================= materials (ramps)
# Five steps dark -> light: seam, shade, base, lit, highlight. Taken from each creature's side-view sheet.
def _r(*h):
    return [c(x) for x in h]


MATS = {
    # mud crab
    "shell": _r("40303A", "634739", "8E6444", "B58A5C", "D4BD92"),
    "shell_rim": _r("2E2226", "453235", "634739", "7C5A40", "8E6444"),
    "crab_leg": _r("2E2226", "453235", "684B3B", "8E6444", "A9805A"),
    "claw": _r("40303A", "684B3B", "8E6444", "B08158", "C9A07A"),
    "claw_tip": _r("124F4A", "257F78", "46BAA6", "7FDCC6", "A4F2DC"),
    "eye": _r("0A1A1D", "1A1216", "1A1216", "2B2A2E", "3B4141"),
    # reed rat
    "fur": _r("2E2630", "3D3340", "5F5052", "7E6E66", "977F68"),
    "fur_light": _r("5F5052", "7C6C66", "977F68", "B8A488", "C7B397"),
    "pink": _r("6E3E48", "B56D72", "CF918A", "E39A92", "F2C0B6"),
    "tail_a": _r("1F3A20", "33552F", "4B7036", "6E9A44", "82AD4F"),
    "tail_b": _r("1A301B", "2A4828", "3F6232", "5C8A3E", "76A248"),
    # boarlet
    "hide": _r("241611", "3A2520", "5A3A27", "7E5230", "925F35"),
    "hide_head": _r("1C110E", "2E1D18", "47302A", "65402E", "7A4F32"),
    "stripe": _r("6B4A28", "A88253", "C38C50", "D6B072", "F3D89C"),
    "hoof": _r("120B0B", "1C110E", "2B1C17", "3F2A22", "553A2E"),
    "snout": _r("4A2A26", "7F4A3C", "8F5A52", "B07A6E", "C99A8E"),
    "bristle": _r("120B0B", "1C110E", "2B1C17", "422B28", "5C3A28"),
}
GLINT = c("F4F0DE")
RAT_EYE = c("9A3A28")
INKY = c("1A1216")
TUSK = c("E9DCB8")
DUST = c("BFAE88")


def _lambert(n) -> int:
    """The ramp step a surface normal takes: light (lambert with a little ambient) cut into bands, the top band for
    the facets turned right into the sun."""
    v = 0.25 + 0.75 * max(0.0, dot(n, LIGHT))
    return 0 if v < 0.3 else 1 if v < 0.48 else 2 if v < 0.7 else 3 if v < 0.9 else 4


# ================================================================================================= the rasteriser
def render(pose: Pose, yaw_deg: float) -> Img:
    """The posed creature seen from the camera, its front turned `yaw_deg` on the ground (east 0, south 90), feet on
    FOOT of a CELL sprite."""
    yaw = math.radians(yaw_deg)
    fwd, left = (math.cos(yaw), math.sin(yaw)), (math.sin(yaw), -math.cos(yaw))

    def world(p):
        """The creature's frame (after its body transform) to the world (east, south, up)."""
        q = mul(add(apply(pose.m, p), pose.shift), pose.k)
        return (q[0] * fwd[0] + q[1] * left[0], q[0] * fwd[1] + q[1] * left[1], q[2])

    def wdir(v):
        q = apply(pose.m, v)
        return (q[0] * fwd[0] + q[1] * left[0], q[0] * fwd[1] + q[1] * left[1], q[2])

    W, H = CELL
    depth = [[math.inf] * W for _ in range(H)]
    colour = [[None] * W for _ in range(H)]
    group = [[""] * W for _ in range(H)]
    step = [[0] * W for _ in range(H)]
    mat = [[""] * W for _ in range(H)]
    for part in pose.parts:
        C = world(part.at)
        axes = [wdir(apply(part.m, e)) for e in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))]
        cx, cy = dot(C, R) + FOOT[0], dot(C, D) + FOOT[1]
        radii = [r * pose.k for r in part.radii]
        rmax = max(radii) + 1.0
        dv = [dot(V, axes[i]) / radii[i] for i in range(3)]
        a = sum(x * x for x in dv)
        for j in range(max(0, int(cy - rmax)), min(H, int(cy + rmax) + 2)):
            for i in range(max(0, int(cx - rmax)), min(W, int(cx + rmax) + 2)):
                # The ray through this pixel's centre: O + t V, O on the screen plane through the world origin.
                sx, sy = i + 0.5 - FOOT[0], j + 0.5 - FOOT[1]
                O = add(mul(R, sx), mul(D, sy))
                rel = (O[0] - C[0], O[1] - C[1], O[2] - C[2])
                q = [dot(rel, axes[k]) / radii[k] for k in range(3)]
                b = 2.0 * sum(q[k] * dv[k] for k in range(3))
                cc = sum(x * x for x in q) - 1.0
                disc = b * b - 4.0 * a * cc
                if disc < 0.0:
                    continue
                t = (-b - math.sqrt(disc)) / (2.0 * a)
                if t >= depth[j][i]:
                    continue
                p = [q[k] + t * dv[k] for k in range(3)]
                n = _norm(tuple(sum(p[k] / radii[k] * axes[k][x] for k in range(3)) for x in range(3)))
                m = part.mat
                if part.pattern is not None:
                    hit = add(O, mul(V, t))
                    m = part.pattern(hit, n) or m
                depth[j][i] = t
                group[j][i] = part.group
                mat[j][i] = m
                step[j][i] = _lambert(n)
    # Seams: a pixel just behind a nearer part of another group (above it or to its left on screen) goes a step darker.
    for j in range(H):
        for i in range(W):
            if not mat[j][i]:
                continue
            s = step[j][i]
            for di, dj in ((0, -1), (-1, 0), (1, 0)):
                ii, jj = i + di, j + dj
                if 0 <= ii < W and 0 <= jj < H and mat[jj][ii] and group[jj][ii] != group[j][i] and depth[jj][ii] < depth[j][i] - 1.5:
                    s = max(0, s - 1)
                    break
            colour[j][i] = MATS[mat[j][i]][s]
    img = Img(W, H)
    for j in range(H):
        for i in range(W):
            if colour[j][i] is not None:
                img.put(i, j, colour[j][i])
    # Marks on the surface: drawn where the point is not hidden behind a nearer part.
    for at, col in pose.marks:
        P = world(at)
        i, j = int(math.floor(dot(P, R) + FOOT[0])), int(math.floor(dot(P, D) + FOOT[1]))
        if 0 <= i < W and 0 <= j < H and mat[j][i] and dot(P, V) <= depth[j][i] + 1.2:   # a point's ray depth is P.V
            img.put(i, j, col)
    img.outline()
    return img


# ================================================================================================= the creatures
def _walk(f: int, k: int) -> tuple:
    """A leg's lift and stride in a 4-frame walk, legs in two alternating sets (k even / odd)."""
    ph = f / 4.0 * math.tau + (math.pi if k % 2 else 0.0)
    return max(0.0, math.sin(ph)) * 1.6, math.cos(ph) * 1.4


def _topple(P: Pose, deg: float, mid: float, half: float) -> None:
    """Roll the body `deg` onto its side about its middle (`mid` up), settling it down onto the ground (its flank
    `half` from the middle), for a fall in death that stays over its feet."""
    P.m = rot("a", deg)
    turned = apply(P.m, (0.0, 0.0, mid))
    P.shift = (-turned[0], -turned[1], mid - turned[2] - (mid - half) * math.sin(math.radians(deg)))


def crab(action: str, f: int, aim=(1.0, 0.0)) -> Pose:
    """The mud crab: a wide shell on six jointed legs, eye stalks, two claws with jade tips held up at its sides. Like
    its side-view sheet it keeps its broad side to the camera and scuttles sideways (`aim` is where it faces, in its own
    frame). It snaps its claws while idle, raises them in its wind-up and brings the claw on the struck side down on
    the strike."""
    P = Pose()
    da, db = aim
    lunge = {"windup": (-1.5, -1.5), "attack": (1.0, 3.5, 2.5), "hurt": (-2.0, -1.0)}.get(action, (0,) * 4)[f] if action in ("windup", "attack", "hurt") else 0.0
    P.shift = (da * lunge, db * lunge, 0.0)
    bob = {"idle": (0, 0, 0.6, 0.6), "walk": (0, 0.7, 0, 0.7)}.get(action, (0,) * 4)[f] if action in ("idle", "walk") else 0.0
    sink = {"death": (0.0, 1.2, 2.2, 2.6)}.get(action, (0,) * 4)[f] if action == "death" else 0.0
    z = 5.2 + bob - sink
    P.add(Part((0.0, 0.0, z), (5.0, 7.2, 3.3), "shell", "body"),
          Part((-0.3, 0.0, z - 1.3), (5.4, 7.7, 2.3), "shell_rim", "body"))
    # Pale patches on the shell's top (the side view's lit blotches).
    for pa, pb in ((0.8, 2.6), (-1.6, -2.4), (1.8, -3.8), (-2.2, 3.4)):
        P.mark((pa, pb, z + 3.4), MATS["shell"][4])
    # Eye stalks and eyes; they droop in death.
    droop = sink * 1.2
    for side in (1, -1):
        base = (1.6, side * 1.9, z + 2.9)
        tip = (1.8 + droop * 1.2, side * 2.4, z + 8.0 - droop * 2.0)
        P.add(chain(base, tip, 0.65, 0.6, 4, "crab_leg", "stalk"))
        P.add(Part(add(tip, (0.2, 0.0, 0.8)), (1.15, 1.15, 1.25), "eye", "stalk"))
        P.mark(add(tip, (0.9, side * -0.3, 1.5)), GLINT)
    # Legs: three a side, knees up and out, feet on the ground; a walk lifts them in two sets and strides them along
    # the way it goes.
    for side in (1, -1):
        for k, a in enumerate((-3.0, -0.6, 1.8)):
            lift, stride = _walk(f, k + (side > 0)) if action == "walk" else (0.0, 0.0)
            curl = sink * 1.3
            hip = (a, side * 6.4, z - 1.0)
            knee = (a + da * stride * 0.5 - 0.4, side * (9.6 - curl) + db * stride * 0.5, z + 1.2 + lift * 0.5 - curl * 0.3)
            foot = (a + da * stride - 0.8, side * (11.2 - curl * 1.8) + db * stride, 0.6 + lift + curl * 0.8)
            P.add(chain(hip, knee, 1.05, 0.95, 3, "crab_leg", "leg%d" % side), chain(knee, foot, 0.95, 0.7, 4, "crab_leg", "leg%d" % side))
    # Claws: arms from the shell's front corners to the pincers, held up at the sides. Idle snaps them; the wind-up
    # raises them high; the strike brings the claw on the struck side (both, straight ahead) out and down; death lets
    # them fall.
    for side in (1, -1):
        snap = (0.0, 0.5, 0.0, 0.5)[f] if action == "idle" else 0.0
        m = None
        if action == "windup":
            elbow, claw, pitch = (2.2, side * 9.4, z + 3.4), (2.2 + f * 0.5, side * 10.4, z + 8.6 + f * 1.4), 80.0
        elif action == "attack" and 0.3 * da + side * db > -0.2:
            reach = 2.0 + (1.0, 3.0, 2.2)[f]
            elbow = (3.2 + da * 2.0, side * 8.0 + db * 2.0, z + 1.5)
            claw = (3.6 + da * reach, side * 8.4 + db * reach, z - 0.4 - f * 0.4)
            m = mat_mul(rot("c", math.degrees(math.atan2(db, da))), rot("b", -25.0))
        elif action == "death":
            elbow, claw, pitch = (4.4, side * 8.0, z), (6.8, side * 9.0, 2.0), -10.0
        else:
            elbow, claw, pitch = (2.8, side * 8.8, z + 2.0), (3.6, side * 10.0, z + 5.6 + snap), 60.0
        P.add(chain((2.4, side * 6.2, z - 0.2), elbow, 1.25, 1.2, 3, "claw", "arm%d" % side),
              chain(elbow, claw, 1.2, 1.3, 3, "claw", "arm%d" % side))
        m = m or rot("b", pitch)
        P.add(Part(claw, (2.5, 1.9, 2.1), "claw", "arm%d" % side, m))
        tip = add(claw, apply(m, (2.2, 0.0, 0.5)))
        P.add(Part(tip, (1.3, 1.25, 1.35), "claw_tip", "arm%d" % side, m),
              Part(add(claw, apply(m, (2.0, 0.0, -1.2 - snap))), (1.1, 1.0, 0.9), "claw_tip", "arm%d" % side, m))
    if action == "death" and f >= 2:
        P.m = rot("a", 12.0 * (f - 1))
    return P


def rat(action: str, f: int) -> Pose:
    """The reed rat: a grey-brown coat with a paler belly, pink ears and feet, red eyes and a long green reed tail in
    segments. It sniffs while idle, rears back in its wind-up and lunges to bite, teeth bared."""
    P = Pose()
    lunge = {"windup": (-1.0, -2.2), "attack": (2.0, 5.0, 3.5), "hurt": (-2.4, -1.2)}.get(action, (0,) * 4)[f] if action in ("windup", "attack", "hurt") else 0.0
    bob = {"idle": (0, 0.4, 0.4, 0), "walk": (0, 0.8, 0, 0.8)}.get(action, (0,) * 4)[f] if action in ("idle", "walk") else 0.0
    rear = {"windup": (12.0, 20.0), "attack": (-6.0, -10.0, -4.0)}.get(action, (0,) * 4)[f] if action in ("windup", "attack") else 0.0
    z = 4.3 + bob
    belly = lambda hit, n: "fur_light" if n[2] < -0.15 else None
    body_m = rot("b", rear * 0.5)
    P.add(Part((lunge - 1.2, 0.0, z), (6.2, 3.5, 3.4), "fur", "body", body_m, belly),
          Part((lunge - 4.0, 0.0, z - 0.2), (3.4, 3.8, 3.5), "fur", "body", body_m, belly))
    lift = math.sin(math.radians(rear)) * 6.0
    sniff = (0.0, 0.4, 0.0, 0.4)[f] if action == "idle" else 0.0
    hx = lunge + 4.6 + sniff
    head_m = rot("b", -12.0 + rear * 0.6)
    P.add(Part((hx, 0.0, z + 0.8 + lift), (3.2, 2.5, 2.5), "fur", "head", head_m),
          Part(add((hx, 0.0, z + 0.8 + lift), apply(head_m, (2.9, 0.0, -0.4))), (1.7, 1.3, 1.3), "fur", "head", head_m))
    nose = add((hx, 0.0, z + 0.8 + lift), apply(head_m, (4.5, 0.0, -0.5)))
    P.mark(nose, MATS["pink"][3])
    if action == "attack" and f >= 1:
        P.mark(add(nose, (-0.6, 0.0, -1.0)), GLINT)
    for side in (1, -1):
        P.add(Part((hx - 0.8, side * 1.9, z + 3.3 + lift), (0.8, 1.4, 1.9), "pink", "ear", rot("c", side * 25.0)))
        P.mark((hx + 1.4, side * 1.7, z + 1.8 + lift), RAT_EYE)
    # Legs: pink feet under short furred legs, stepping in the walk.
    for k, (a, b) in enumerate(((2.4, 2.0), (2.4, -2.0), (-3.6, 2.4), (-3.6, -2.4))):
        up, stride = _walk(f, k + (k // 2)) if action == "walk" else (0.0, 0.0)
        P.add(chain((lunge + a, b, z - 1.6), (lunge + a + stride, b, 0.9 + up), 1.0, 0.8, 3, "fur", "leg"),
              Part((lunge + a + stride + 0.5, b, 0.6 + up), (1.2, 0.9, 0.6), "pink", "leg"))
    # The reed tail: green segments curving back along the ground, the tip lifting and swaying.
    sway = (0.0, 1.0, 0.0, -1.0)[f] if action in ("idle", "walk") else (0.8 if action == "windup" else 0.0)
    pts = []
    for k in range(12):
        u = k / 11.0
        pts.append((lunge - 7.0 - 9.5 * u, (2.8 + sway) * math.sin(u * 2.6), 2.6 - 1.8 * u + 3.2 * u * u * (1.0 if action != "death" else 0.2)))
    for k, p in enumerate(pts):
        r = 1.05 - 0.35 * k / 11.0
        P.add(Part(p, (r, r, r), "tail_a" if k % 2 == 0 else "tail_b", "tail"))
    if action == "death":
        _topple(P, (15.0, 40.0, 70.0, 82.0)[f], z, 3.4)
    return P


def boarlet(action: str, f: int) -> Pose:
    """The boarlet: a young boar's warm brown hide with pale stripes along its back, a bristle crest, small ears, a
    pink snout and short tusks. It lowers its head and paws the ground in its wind-up, then charges, tusks up."""
    P = Pose()
    lunge = {"windup": (-1.5, -2.5), "attack": (2.5, 5.5, 4.0), "hurt": (-2.4, -1.2)}.get(action, (0,) * 4)[f] if action in ("windup", "attack", "hurt") else 0.0
    bob = {"idle": (0, 0, 0.5, 0.5), "walk": (0, 0.8, 0, 0.8)}.get(action, (0,) * 4)[f] if action in ("idle", "walk") else 0.0
    z = 7.4 + bob

    def stripes(hit, n):
        """Pale stripes run along the back: bands across the body's width on its upper half."""
        if n[2] < 0.2:
            return None
        b = abs(_local_b(hit))
        return "stripe" if 0.7 < b < 1.7 or 2.7 < b < 3.5 else None

    P.add(Part((lunge - 1.4, 0.0, z), (6.8, 4.8, 4.8), "hide", "body", IDENT, stripes),
          Part((lunge - 5.6, 0.0, z - 0.2), (3.6, 4.6, 4.6), "hide", "body", IDENT, stripes))
    for k in range(9):   # the bristle crest along the spine
        a = lunge - 6.0 + k * 1.3
        P.add(Part((a, 0.0, z + 4.6 - abs(k - 4) * 0.12), (0.7, 0.7, 0.9), "bristle", "crest"))
    dip = {"windup": (-18.0, -26.0), "attack": (6.0, 14.0, 8.0)}.get(action, (0,) * 4)[f] if action in ("windup", "attack") else 0.0
    sniff = (0.0, 0.3, 0.0, 0.3)[f] if action == "idle" else 0.0
    hc = (lunge + 6.6 + sniff, 0.0, z - 1.2)
    head_m = rot("b", -15.0 + dip)
    P.add(Part(hc, (4.0, 3.5, 3.6), "hide_head", "head", head_m))
    snout = add(hc, apply(head_m, (3.9, 0.0, -0.9)))
    P.add(Part(snout, (1.5, 1.7, 1.5), "snout", "head", head_m))
    P.mark(add(snout, apply(head_m, (1.4, 0.6, 0.2))), MATS["snout"][0])
    P.mark(add(snout, apply(head_m, (1.4, -0.6, 0.2))), MATS["snout"][0])
    for side in (1, -1):
        P.mark(add(snout, apply(head_m, (-0.4, side * 1.9, -1.2))), TUSK)
        P.mark(add(hc, apply(head_m, (1.7, side * 2.4, 1.1))), INKY)
        P.add(Part(add(hc, apply(head_m, (-1.4, side * 2.3, 3.2))), (1.0, 1.2, 1.9), "bristle", "ear", rot("a", side * -25.0)))
    for k, (a, b) in enumerate(((3.6, 2.6), (3.6, -2.6), (-5.2, 2.8), (-5.2, -2.8))):
        up, stride = _walk(f, k + (k // 2)) if action == "walk" else (0.0, 0.0)
        if action == "windup" and k == 0:
            stride = (-1.5, -3.0)[f]
            up = 0.6
        P.add(chain((lunge + a, b, z - 3.0), (lunge + a + stride, b, 1.2 + up), 1.35, 1.2, 4, "hoof", "leg"))
    P.add(chain((lunge - 8.6, 0.0, z + 1.0), (lunge - 9.6, 0.6, z + 2.4), 0.7, 0.6, 3, "hide", "tail"))
    if action == "windup":
        for k in range(3):
            P.marks.append(((lunge + 1.0 - k * 2.0, 3.4 + k * 0.6, 0.4 + k * 0.5 * f), DUST))
    if action == "death":
        _topple(P, (12.0, 36.0, 64.0, 80.0)[f], z, 4.8)
    return P


# The stripes' band is measured across the body in the creature's own frame; `render` passes world hit points, so the
# pattern needs the current facing to turn them back. `_frame` holds it while a sprite renders.
_frame = {"left": (0.0, -1.0)}


def _local_b(hit) -> float:
    lx, ly = _frame["left"]
    return hit[0] * lx + hit[1] * ly


BUILD = {"mudshell_crab": crab, "reedtail_rat": rat, "wild_boarlet": boarlet}
SHADOW = {"mudshell_crab": [10, 3], "reedtail_rat": [8, 2], "wild_boarlet": [11, 3]}
# Sizes against the 38 px body (the plan's §1.4): the crab and the rat small, about 24 and 30 px with its tail; the
# boarlet medium, about 28 px long.
SIZE = {"reedtail_rat": 1.1, "wild_boarlet": 1.25}


def body_yaw(species: str, facing: str) -> tuple:
    """How a creature turns its body to a facing: its yaw on the ground and the facing in its own frame (a, b). Most
    face where they go; the crab keeps its broad side to the camera, front or back, and scuttles sideways."""
    if species != "mudshell_crab":
        return ANGLE[facing], (1.0, 0.0)
    yaw = 90.0 if facing in ("s", "se", "e") else -90.0
    g, y = math.radians(ANGLE[facing]), math.radians(yaw)
    return yaw, (math.cos(g - y), -math.sin(g - y))


def sprite(species: str, action: str, f: int, facing: str) -> Img:
    yaw, aim = body_yaw(species, facing)
    _frame["left"] = (math.sin(math.radians(yaw)), -math.cos(math.radians(yaw)))
    pose = crab(action, f, aim) if species == "mudshell_crab" else BUILD[species](action, f)
    pose.k = SIZE.get(species, 1.0)
    return render(pose, yaw)


def build() -> tuple[Img, dict]:
    """The foe sheet: a row per species and drawn facing, the actions' frames along it; and its manifest block."""
    cols = sum(n for n, _, _ in ACTIONS.values())
    sheet = Img(cols * CELL[0], len(SPECIES) * len(DIRS) * CELL[1])
    species: dict = {}
    for s, sp in enumerate(SPECIES):
        acts: dict = {}
        for d, facing in enumerate(DIRS):
            row = (s * len(DIRS) + d) * CELL[1]
            col = 0
            for action, (n, fps, loop) in ACTIONS.items():
                entry = acts.setdefault(action, {"fps": fps, "loop": loop, "frames": {}})
                entry["frames"][facing] = [[(col + f) * CELL[0], row] for f in range(n)]
                for f in range(n):
                    sheet.paste(sprite(sp, action, f, facing), (col + f) * CELL[0], row)
                col += n
        acts["attack"]["hit_frame"] = HIT_FRAME
        species[sp] = {"actions": acts, "shadow": SHADOW[sp]}
    return sheet, {"cell": list(CELL), "foot": list(FOOT), "dirs": DIRS, "mirror": MIRROR, "species": species,
                   "note": "the prototype's foes in eight facings (five drawn, three mirrored), built by tools/art/topdown/creatures.py"}
