"""The top-down foes (art bible §8, the plan's §1.4): the prototype room's early monsters, those of chapter 2's stretch
(the Trial Puppet, the Reed Marsh's frog, leech and otter, the hollowed boarlet) and the tutorial rooms' others (Old
Snapper, the mossback toad, and the night's hollow minnow and hollowed eel), redrawn from their side-view sheets
(art/creatures/) for the three-quarter view in eight facings.

Each creature is built as a small sculpture of ellipsoids in its own frame (a forward, b to its left, c up, in art px)
and posed per action and frame. The sculpture is turned to each drawn facing (S, SE, E, NE, N; SW, W and NW mirror in
the room view), seen from a camera to the south, 35 degrees above the ground, and lit by the room's sun
(upper left). Every pixel takes a step of its material's ramp by its light; a part tucked behind a nearer part takes
one step darker along the seam, so legs, claws and bodies separate by value; eyes, noses, tusks and stripes are placed
on the surface as marks; the sprite takes the prop outline (art bible §4). Loose drops and motes, and the water round a creature in it, are
laid on after the outline and take none, like the lotus pads (a creature in the water is cut off at its surface). No
randomness and no filtering: a rebuild is byte-identical.

The creatures keep what makes them recognisable in the side view: the mud crab's brown shell with pale patches, black
eye stalks and jade-tipped claws; the reed rat's grey-brown coat, pink ears and feet, red eyes and green segmented reed
tail; the boarlet's warm brown hide with pale stripes along its back, a bristle crest, a pink snout and small tusks;
Old Snapper's mossy shell and red crusher claw; the mossback toad's moss, ferns and golden eyes; and the Hollow's
grey on the minnow and the eel, with their empty white eyes and grey strands.

Actions (the side view's catalogue in data/creature_art.json): idle, walk, windup, attack (its strike on `hit_frame`),
hurt and death, at the frame rates in ACTIONS.
"""
from __future__ import annotations

import math

from canvas import Img, h01
from palette import c

# One cell for every foe, grown until the largest fits: 38 px over the feet for the puppet and Old Snapper's raised
# crusher, 31 under them for the eel's water (drawn 20 px under its hovering feet), and 31 either side for Old
# Snapper's slam and the eel's lunge.
CELL = (64, 72)
FOOT = (32, 40)
DIRS = ["s", "se", "e", "ne", "n"]
MIRROR = {"sw": "se", "w": "e", "nw": "ne"}
ANGLE = {"s": 90.0, "se": 45.0, "e": 0.0, "ne": -45.0, "n": -90.0}   # on the ground: east 0, south 90
# action: frames, fps, loop
ACTIONS = {"idle": (4, 6, True), "walk": (4, 10, True), "windup": (2, 8, False), "attack": (3, 12, False),
           "hurt": (2, 10, False), "death": (4, 8, False)}
HIT_FRAME = 1
SPECIES = ["mudshell_crab", "reedtail_rat", "wild_boarlet", "trial_puppet", "reed_frog", "marsh_leech", "reed_otter",
           "hollowed_boarlet", "old_snapper", "mossback_toad", "hollow_minnow", "hollowed_eel"]

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
        self.fx: list = []        # (point, colour): loose drops, dust and motes, drawn after the outline, never outlined
        self.water = None         # a creature in the water: the surface's height (world px from the feet); nothing
        self.water_fx = None      # under it is drawn, and water_fx(a, b) colours the surface round it (no outline)

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
    # hollowed boarlet: the boarlet with its colour drunk out of it, pale ash stripes, grey strands rising from its back
    "h_hide": _r("3A4242", "5C6563", "858D89", "A9AEA8", "C8CBC4"),
    "h_head": _r("2F3636", "4A5251", "6C7471", "8C938E", "A9AEA8"),
    "h_stripe": _r("5C6563", "8A928D", "D2D5CD", "E2E3DC", "F0F0EA"),
    "h_snout": _r("4A4E4E", "6A6E6C", "8E908C", "A8AAA4", "C0C2BC"),
    "h_bristle": _r("1A2020", "283030", "3A4444", "505A5A", "687272"),
    # trial puppet: carved timber, brass ball joints, the sect's jade sash and back plate
    "timber": _r("3A2412", "5E3C1E", "875A30", "AE7C46", "CFA064"),
    "timber_dark": _r("24160A", "3A2412", "5E3C1E", "7A5028", "96683A"),
    "brass": _r("3A2810", "5E4420", "8A6630", "B08A48", "D4B070"),
    "puppet_jade": _r("0F3A36", "17564F", "2C8A7C", "4CB6A2", "8AE0CC"),
    # reed frog: leaf green with a gold stripe down each flank and a pale belly
    "frog": _r("123A1E", "1E5A2A", "2F8A38", "5BB64A", "8ED866"),
    "frog_belly": _r("5A6A2A", "8A9A40", "BFC468", "DCD88A", "EEE8B0"),
    "frog_stripe": _r("6A5A14", "A89024", "D8C040", "F0DC60", "FFF090"),
    # marsh leech: an olive slug in soft rings, teal spots, a round pink mouth
    "leech": _r("1E2A12", "34461E", "53672C", "7A8A3C", "9CAA52"),
    "leech_belly": _r("3A3A1E", "5A5A2E", "7C7A44", "9C9860", "B8B27C"),
    # reed otter: a sleek brown coat, a pale muzzle and throat
    "otter": _r("2A1A10", "4A2E1A", "6E4426", "8E5C34", "A87444"),
    "otter_pale": _r("7A6040", "A88A64", "C8AA82", "DCC4A0", "EEDCBC"),
    # Old Snapper: a dark green shell grown over with moss, khaki skin, a pale hooked beak, the red crusher claw
    "snap_shell": _r("111A16", "1A2621", "2A392C", "3D5034", "61784A"),
    "snap_seam": _r("0C1310", "111A16", "1A2621", "2A392C", "3D5034"),
    "snap_moss": _r("2F4A26", "3C5A2B", "5B7C36", "80A445", "B3D066"),
    "snap_moss_lit": _r("3C5A2B", "5B7C36", "80A445", "A6C65C", "C6DE82"),
    "snap_moss_seam": _r("243A1E", "2F4A26", "3C5A2B", "5B7C36", "80A445"),
    "snap_belly_seam": _r("3A3530", "4F493C", "786C52", "A7966B", "C2B284"),
    "snap_skin": _r("33372F", "4F4F3E", "736E4F", "A29A6C", "BDB587"),
    "snap_belly": _r("4F493C", "786C52", "A7966B", "D0C08E", "E6D9AC"),
    "snap_beak": _r("5C5242", "958561", "CBB98A", "F0E2B6", "F8EDCB"),
    "crusher": _r("4A262B", "763C33", "A95C3D", "DE9463", "EDB287"),
    "crusher_tip": _r("1D1519", "2E2024", "44302F", "74514B", "8E6A62"),
    "weed": _r("2B3E2A", "425C33", "62803D", "93AE58", "B2C878"),
    # mossback toad: an olive-khaki hide, a mat of moss and fern sprouts on its back, a cream belly and throat sac
    "toad": _r("3B3A2A", "5D5637", "877A4A", "B9A66A", "CDBC84"),
    "toad_leg": _r("44412F", "6A6040", "998A55", "C9B67A", "DACB96"),
    "toad_belly": _r("766A55", "AA9870", "D9C690", "F3E6B8", "F8EFCE"),
    "toad_sac": _r("AD9A70", "D6C28E", "F2E3B2", "FBF3D6", "FCF7E6"),
    "toad_moss": _r("2F5230", "4D7C38", "78A845", "B6D86A", "CCE68A"),
    "toad_fern": _r("2F5A36", "4F8440", "7FB04C", "C2E27A", "D8F09A"),
    "tongue": _r("733946", "B0565F", "E0827F", "F6B7B0", "FAD0CA"),
    "toad_eye": _r("7A5A14", "B8861E", "E0A830", "F2C145", "FBE08A"),
    # hollowed eel: a huge river eel drained grey, darker than the minnow so its bulk is no white blob; a pale belly
    "eel": _r("36424A", "4E5B64", "6F7C84", "9AA6AA", "CBD3D1"),
    "eel_belly": _r("76838A", "9FABAD", "C9D0CD", "E0E5E0", "EEF0E9"),
    "eel_fin": _r("2F3840", "3F4A52", "58646C", "78848B", "A9B3B7"),
    # hollow minnow: a small grey fish, dark back, pale belly, grey fins
    "minnow": _r("3E4A53", "5A6770", "808D94", "AAB5B8", "D6DDD9"),
    "minnow_back": _r("343E47", "4B565F", "67737B", "8D989D", "A9B2B6"),
    "minnow_belly": _r("7D8990", "A4AFB1", "CDD4D0", "E9ECE4", "F2F4EE"),
    "minnow_fin": _r("535F69", "77848C", "A3AEB3", "D3DBDB", "E4EAE8"),
    "mist": _r("5F6B72", "7F8B92", "A3AEB2", "C9D2D3", "E6ECEA"),
}
GLINT = c("F4F0DE")
RAT_EYE = c("9A3A28")
INKY = c("1A1216")
TUSK = c("E9DCB8")
DUST = c("BFAE88")
HOLLOW_EYE = c("E2F4EE")
FROG_EYE = c("EAD24A")
LEECH_SPOT = c("5CC8B4")
QI_RING = c("67D6BD")
SNAP_EYE = c("F4B73A")
BARNACLE = c("F4F2E6")
BARNACLE_SHADE = c("959C92")
TALON = c("DDD3B2")
CLAW_TOOTH = c("FDF3D8")
HOOK = c("443C31")
SPLASH = c("CFEFE8")
SPLASH_DIM = c("8CCFC0")
WART = c("CDBB80")
TOAD_MOUTH = c("35191E")
EEL_TOOTH = c("EEF0E6")
EYE_HALO = c("CFE6EA")
FISH_MOUTH = c("2A333B")
# The water round the eel, laid on the river under it (translucent, like the prop shadows' teal): the Hollow's dark
# stain, the foam where the body breaks the surface, and the rings and the wake spreading from it.
POOL = c("1F2830", 150)
FOAM = c("DCE4E4", 235)
RIPPLE = c("B7C4C8", 210)
RIPPLE_DIM = c("7F8E96", 160)
MOTE = c("C9D2D3", 210)
MOTE_DIM = c("A3AEB2", 170)


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
                if pose.water is not None and O[2] + V[2] * t < pose.water:
                    continue   # under the water: the ray only goes deeper through this part

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
    # Loose points (a splash's drops, dust, a dissolving body's motes) and the water round a creature in it: like the
    # lotus pads and the cut's smear, they take no outline, and they never cover the figure.
    for at, col in pose.fx:
        P = world(at)
        i, j = int(math.floor(dot(P, R) + FOOT[0])), int(math.floor(dot(P, D) + FOOT[1]))
        if img.get(i, j)[3] == 0:
            img.put(i, j, col)
    if pose.water is not None and pose.water_fx is not None:
        for j in range(H):
            for i in range(W):
                if img.get(i, j)[3]:
                    continue
                O = add(mul(R, i + 0.5 - FOOT[0]), mul(D, j + 0.5 - FOOT[1]))
                hit = add(O, mul(V, (pose.water - O[2]) / V[2]))
                col = pose.water_fx((hit[0] * fwd[0] + hit[1] * fwd[1]) / pose.k, (hit[0] * left[0] + hit[1] * left[1]) / pose.k)
                if col is not None:
                    img.put(i, j, col)
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


def boarlet(action: str, f: int, hollow: bool = False) -> Pose:
    """The boarlet: a young boar's warm brown hide with pale stripes along its back, a bristle crest, small ears, a
    pink snout and short tusks. It lowers its head and paws the ground in its wind-up, then charges, tusks up. Hollowed
    (`hollow`, the Reed Marsh's grey boarlets): the same beast with its colour drunk out of it, ash-grey with pale
    stripes, eyes a cold white, and thin grey strands rising and curling from its back as in its side-view sheet."""
    m = {"hide": "hide", "hide_head": "hide_head", "stripe": "stripe", "hoof": "hoof", "snout": "snout", "bristle": "bristle"}
    if hollow:
        m = {"hide": "h_hide", "hide_head": "h_head", "stripe": "h_stripe", "hoof": "h_bristle", "snout": "h_snout",
             "bristle": "h_bristle"}
    P = Pose()
    lunge = {"windup": (-1.5, -2.5), "attack": (2.5, 5.5, 4.0), "hurt": (-2.4, -1.2)}.get(action, (0,) * 4)[f] if action in ("windup", "attack", "hurt") else 0.0
    bob = {"idle": (0, 0, 0.5, 0.5), "walk": (0, 0.8, 0, 0.8)}.get(action, (0,) * 4)[f] if action in ("idle", "walk") else 0.0
    z = 7.4 + bob

    def stripes(hit, n):
        """Pale stripes run along the back: bands across the body's width on its upper half."""
        if n[2] < 0.2:
            return None
        b = abs(_local_b(hit))
        return m["stripe"] if 0.7 < b < 1.7 or 2.7 < b < 3.5 else None

    P.add(Part((lunge - 1.4, 0.0, z), (6.8, 4.8, 4.8), m["hide"], "body", IDENT, stripes),
          Part((lunge - 5.6, 0.0, z - 0.2), (3.6, 4.6, 4.6), m["hide"], "body", IDENT, stripes))
    for k in range(9):   # the bristle crest along the spine
        a = lunge - 6.0 + k * 1.3
        P.add(Part((a, 0.0, z + 4.6 - abs(k - 4) * 0.12), (0.7, 0.7, 0.9), m["bristle"], "crest"))
    dip = {"windup": (-18.0, -26.0), "attack": (6.0, 14.0, 8.0)}.get(action, (0,) * 4)[f] if action in ("windup", "attack") else 0.0
    sniff = (0.0, 0.3, 0.0, 0.3)[f] if action == "idle" else 0.0
    hc = (lunge + 6.6 + sniff, 0.0, z - 1.2)
    head_m = rot("b", -15.0 + dip)
    P.add(Part(hc, (4.0, 3.5, 3.6), m["hide_head"], "head", head_m))
    snout = add(hc, apply(head_m, (3.9, 0.0, -0.9)))
    P.add(Part(snout, (1.5, 1.7, 1.5), m["snout"], "head", head_m))
    P.mark(add(snout, apply(head_m, (1.4, 0.6, 0.2))), MATS[m["snout"]][0])
    P.mark(add(snout, apply(head_m, (1.4, -0.6, 0.2))), MATS[m["snout"]][0])
    for side in (1, -1):
        P.mark(add(snout, apply(head_m, (-0.4, side * 1.9, -1.2))), TUSK)
        P.mark(add(hc, apply(head_m, (1.7, side * 2.4, 1.1))), HOLLOW_EYE if hollow else INKY)
        P.add(Part(add(hc, apply(head_m, (-1.4, side * 2.3, 3.2))), (1.0, 1.2, 1.9), m["bristle"], "ear", rot("a", side * -25.0)))
    for k, (a, b) in enumerate(((3.6, 2.6), (3.6, -2.6), (-5.2, 2.8), (-5.2, -2.8))):
        up, stride = _walk(f, k + (k // 2)) if action == "walk" else (0.0, 0.0)
        if action == "windup" and k == 0:
            stride = (-1.5, -3.0)[f]
            up = 0.6
        P.add(chain((lunge + a, b, z - 3.0), (lunge + a + stride, b, 1.2 + up), 1.35, 1.2, 4, m["hoof"], "leg"))
    P.add(chain((lunge - 8.6, 0.0, z + 1.0), (lunge - 9.6, 0.6, z + 2.4), 0.7, 0.6, 3, m["hide"], "tail"))
    if hollow and action != "death":
        # The grey strands: three thin wisps rising from the spine and curling back, stirring as it breathes.
        stir = (0.0, 0.5, 0.0, -0.5)[f] if action in ("idle", "walk") else 0.8
        for k, (a, bb) in enumerate(((-4.4, 0.4), (-1.6, -0.3), (1.2, 0.2))):
            base = (lunge + a, bb, z + 4.4)
            tip = (lunge + a - 2.2 - k * 0.3, bb + stir * (1 if k % 2 else -1), z + 10.5 - k * 0.8)
            P.add(chain(base, tip, 0.55, 0.4, 6, "h_stripe", "strand%d" % k))
    if action == "windup":
        for k in range(3):
            P.marks.append(((lunge + 1.0 - k * 2.0, 3.4 + k * 0.6, 0.4 + k * 0.5 * f), DUST))
    if action == "death":
        _topple(P, (12.0, 36.0, 64.0, 80.0)[f], z, 4.8)
    return P


def puppet(action: str, f: int) -> Pose:
    """The Trial Puppet: a sparring figure of carved timber on brass ball joints, the sect's jade sash across its chest
    and a jade plate on its back, a jade tuft on its crown (as on its side-view sheet). It sways on guard, walks with
    its fists up, draws its right fist back in the wind-up and drives it out on the strike with a ring of Qi at the
    knuckles; struck, it rocks back; beaten, it topples onto its side."""
    P = Pose()
    sway = (0.0, 0.3, 0.0, -0.3)[f] if action == "idle" else 0.0
    lean = {"hurt": (-9.0, -5.0), "windup": (-6.0, -8.0), "attack": (8.0, 12.0, 6.0)}.get(action, (0,) * 4)[f] \
        if action in ("hurt", "windup", "attack") else 0.0
    body_m = rot("b", -lean)   # a lean forward tips the torso's top ahead (a positive pitch lifts the front)

    def up(p, hip=16.0):
        """A point of the upper body, leaned about the hips."""
        q = apply(body_m, (p[0], p[1], p[2] - hip))
        return (q[0] + sway * 0.4, q[1] + sway, q[2] + hip)

    def sash(hit, n):
        """The jade sash across the chest (from the left shoulder down to the right hip) and the plate on its back."""
        a = (hit[0] * _frame["fwd"][0] + hit[1] * _frame["fwd"][1]) / P.k
        b = _local_b(hit) / P.k
        zz = hit[2] / P.k
        if n[0] * _frame["fwd"][0] + n[1] * _frame["fwd"][1] < -0.55 and zz > 18.0:
            return "puppet_jade"
        return "puppet_jade" if abs((zz - 21.5) - b * 0.9) < 1.1 and a > -1.0 else None

    # Legs: a stride in the walk, planted apart otherwise.
    for side in (1, -1):
        ph = f / 4.0 * math.tau + (0.0 if side > 0 else math.pi)
        stride = math.sin(ph) * 2.6 if action == "walk" else 0.0
        lift = max(0.0, math.cos(ph)) * 1.2 if action == "walk" else 0.0
        plant = (-1.2 if side < 0 else 1.0) if action in ("windup", "attack") else 0.0
        foot = (stride + plant + 0.8, side * 2.5, 1.0 + lift)
        knee = (stride * 0.5 + plant * 0.5 + 0.4, side * 2.4, 9.0 + lift * 0.5)
        P.add(Part(foot, (2.5, 1.3, 1.0), "timber_dark", "foot%d" % side),
              chain((foot[0] - 0.6, foot[1], 1.8 + lift), knee, 1.3, 1.35, 4, "timber", "leg%d" % side),
              Part(knee, (1.5, 1.5, 1.5), "brass", "leg%d" % side),
              chain(knee, (0.0, side * 2.1, 15.2), 1.45, 1.7, 4, "timber", "leg%d" % side))
    P.add(Part(up((0.0, 0.0, 16.6)), (2.4, 3.6, 2.0), "timber", "body"),
          Part(up((0.0, 0.0, 21.6)), (2.8, 4.4, 4.6), "timber", "body", body_m, sash),
          Part(up((0.0, 0.0, 26.4)), (1.1, 1.1, 1.2), "timber_dark", "body"),
          Part(up((0.3, 0.0, 29.4)), (2.6, 2.4, 3.0), "timber", "head", body_m))
    for side in (1, -1):
        P.mark(up((2.7, side * 1.0, 29.9)), INKY)
    P.mark(up((2.5, 0.0, 31.3)), QI_RING)
    P.add(Part(up((-0.2, 0.0, 32.9)), (1.0, 1.0, 1.2), "puppet_jade", "tuft"),
          Part(up((-0.9, 0.3, 33.8)), (0.8, 0.8, 1.0), "puppet_jade", "tuft"))
    # Arms: fists up on guard; the right (b < 0) draws back in the wind-up and drives out on the strike.
    for side in (1, -1):
        sh = up((0.0, side * 4.9, 24.4))
        guard = (0.3, 0.6, 0.3, 0.0)[f] if action == "idle" else 0.0
        swing = -math.sin(f / 4.0 * math.tau + (0.0 if side > 0 else math.pi)) * 1.8 if action == "walk" else 0.0
        if side < 0 and action == "windup":
            elbow, fist = up((-3.0, -5.6, 21.0)), up((-2.0 - f, -4.4, 22.5))
        elif side < 0 and action == "attack":
            reach = (4.0, 7.5, 5.5)[f]
            elbow, fist = up((2.0 + reach * 0.3, -4.8, 23.0)), up((3.0 + reach, -3.2, 23.2))
            if f >= 1:
                for dy, dz in ((0.0, 1.6), (1.1, 1.1), (1.6, 0.0), (1.1, -1.1), (0.0, -1.6), (-1.1, -1.1), (-1.6, 0.0), (-1.1, 1.1)):
                    P.mark(add(fist, (1.4, dy, dz)), QI_RING)
        elif action == "death":
            elbow, fist = up((0.4, side * 5.8, 19.0)), up((1.0, side * 5.6, 14.5))
        else:
            elbow, fist = up((1.4 + swing * 0.5, side * 5.7, 19.8 + guard)), up((3.4 + swing, side * 3.6, 22.4 + guard))
        P.add(Part(sh, (1.5, 1.5, 1.5), "brass", "arm%d" % side),
              chain(sh, elbow, 1.25, 1.2, 4, "timber", "arm%d" % side),
              Part(elbow, (1.2, 1.2, 1.2), "brass", "arm%d" % side),
              chain(elbow, fist, 1.15, 1.1, 4, "timber", "arm%d" % side),
              Part(fist, (1.6, 1.5, 1.5), "timber_dark", "arm%d" % side))
    if action == "death":
        _topple(P, (14.0, 38.0, 66.0, 84.0)[f], 16.0, 4.4)
    return P


def frog(action: str, f: int) -> Pose:
    """The reed frog: leaf green with a gold stripe down each flank, a pale belly, gold eyes set high. It sits with its
    long hind legs folded at its sides, gulps while idle, hops as it goes, crouches in its wind-up and leaps at its
    prey; beaten, it rolls onto its back."""
    P = Pose()
    hop = {"walk": (0.0, 1.4, 3.0, 1.0), "attack": (2.0, 5.0, 2.2)}.get(action, (0,) * 4)[f] if action in ("walk", "attack") else 0.0
    ahead = {"walk": (0.0, 1.0, 2.2, 3.0), "attack": (2.0, 5.5, 4.5), "hurt": (-2.2, -1.0)}.get(action, (0,) * 4)[f] \
        if action in ("walk", "attack", "hurt") else 0.0
    crouch = (-1.0, -1.6)[f] if action == "windup" else 0.0
    stretch = hop > 1.2   # in the air: hind legs trailing
    z = 4.4 + hop + crouch
    tilt = rot("b", 14.0 if stretch else (6.0 if action == "windup" else 0.0))
    centre = (ahead - 0.6, 0.0, z)

    def flank(hit, n):
        """The belly underneath; a gold stripe along each flank."""
        if n[2] < -0.35:
            return "frog_belly"
        b = abs(_local_b(hit)) / P.k
        return "frog_stripe" if 2.6 < b < 3.4 and n[2] > -0.1 else None

    P.add(Part(centre, (5.4, 4.2, 3.2), "frog", "body", tilt, flank),
          Part(add(centre, apply(tilt, (4.6, 0.0, 0.5))), (3.2, 3.7, 2.4), "frog", "body", tilt, flank))
    gulp = (0.0, 0.5, 0.9, 0.3)[f] if action == "idle" else 0.0
    P.add(Part(add(centre, apply(tilt, (5.4, 0.0, -1.8))), (1.8 + gulp * 0.4, 2.6 + gulp, 1.2 + gulp), "frog_belly", "throat", tilt))
    for side in (1, -1):
        eye = add(centre, apply(tilt, (5.0, side * 2.2, 2.7)))
        P.add(Part(eye, (1.6, 1.6, 1.5), "frog", "eye%d" % side))
        for d in ((0.3, side * 0.3, 1.4), (1.0, side * 0.6, 1.0), (0.6, side * 1.1, 1.0), (1.4, side * 0.1, 0.4)):
            P.mark(add(eye, d), FROG_EYE)
        P.mark(add(eye, (1.2, side * 0.5, 0.8)), INKY)
        # Hind legs: folded at the sides, trailing straight back in a leap.
        if stretch:
            hip, knee, foot = (ahead - 4.0, side * 3.0, z - 0.4), (ahead - 7.0, side * 3.6, z - 1.2), (ahead - 10.0, side * 3.4, z - 1.8)
        else:
            hip, knee, foot = (ahead - 3.8, side * 3.6, z - 1.0), (ahead - 0.2, side * 5.0, 1.8 - crouch * 0.3), (ahead - 3.4, side * 5.4, 0.6)
        P.add(Part(add(hip, (0.8, 0.0, 0.0)), (3.0, 1.7, 1.8), "frog", "hind%d" % side, rot("c", side * 20.0)),
              chain(hip, knee, 1.5, 1.2, 4, "frog", "hind%d" % side),
              chain(knee, foot, 1.1, 0.9, 4, "frog", "hind%d" % side),
              Part(add(foot, (-0.8 if stretch else 1.0, 0.0, 0.0)), (1.9, 1.3, 0.5), "frog_belly", "hind%d" % side))
        # Front legs: short props under the chest, reaching ahead in a leap.
        reach = 2.0 if stretch else 0.0
        shoulder = add(centre, apply(tilt, (3.6, side * 2.4, -1.2)))
        hand = (ahead + 4.4 + reach, side * 3.0, 0.6 + (hop * 0.6 if stretch else 0.0))
        P.add(chain(shoulder, hand, 0.9, 0.75, 4, "frog", "arm%d" % side),
              Part(hand, (1.1, 1.0, 0.45), "frog_belly", "arm%d" % side))
    if action == "attack" and f == 0:
        for k in range(3):
            P.marks.append(((ahead - 7.0 - k * 1.6, 2.0 - k * 1.8, 0.4), DUST))
    if action == "death":
        _topple(P, (25.0, 70.0, 120.0, 160.0)[f], z, 3.2)
    return P


def leech(action: str, f: int) -> Pose:
    """The marsh leech: a long olive slug in soft rings with teal spots down its back and a round pink mouth at its
    front. It creeps in a travelling ripple, rears its front up in the wind-up and lunges, mouth first; beaten, it
    sags flat."""
    P = Pose()
    n = 7
    lunge = {"attack": (2.0, 4.5, 3.0), "hurt": (-2.0, -1.0)}.get(action, (0,) * 4)[f] if action in ("attack", "hurt") else 0.0
    flat = (0.0, 0.3, 0.55, 0.7)[f] if action == "death" else 0.0

    def belly(hit, nn):
        return "leech_belly" if nn[2] < -0.3 else None

    segs = []
    for k in range(n):
        u = k / (n - 1)                       # 0 at the tail, 1 at the mouth
        a = -8.0 + 15.0 * u + lunge * u
        ripple = max(0.0, math.sin(f / 4.0 * math.tau - k * 1.1)) * 1.2 if action in ("walk", "idle") else 0.0
        if action == "idle":
            ripple *= 0.4
        rear = 0.0
        if action == "windup":
            rear = max(0.0, u - 0.45) * (7.0 + f * 3.0)
        elif action == "attack":
            rear = max(0.0, u - 0.55) * (3.0, 1.0, 0.5)[f] * 3.0
        r = 2.1 + 1.0 * math.sin(math.pi * (0.25 + 0.6 * u))
        zc = (r * 0.85 + ripple + rear) * (1.0 - flat)
        segs.append(((a - rear * 0.35, 0.0, max(zc, 0.8)), r))
    for k, (at, r) in enumerate(segs):
        P.add(Part(at, (r * 1.05, r, r * 0.85 * (1.0 - flat * 0.5)), "leech", "body", IDENT, belly))
        if k % 2 == 0 and k < n - 1:
            for d in ((0.0, 0.9, r * 0.8), (0.5, 1.0, r * 0.78), (0.6, -1.0, r * 0.75), (1.1, -0.9, r * 0.7)):
                P.mark(add(at, d), LEECH_SPOT)
    head, r = segs[-1]
    mouth = add(head, (r * 1.0, 0.0, 0.2 + (0.6 if action == "windup" else 0.0)))
    P.add(Part(mouth, (0.7, 1.3, 1.3), "pink", "mouth"))
    P.mark(add(mouth, (0.7, 0.0, 0.0)), MATS["pink"][0])
    if action == "attack" and f >= 1:
        P.mark(add(mouth, (1.0, 0.5, 0.6)), GLINT)
    return P


def otter(action: str, f: int) -> Pose:
    """The reed otter: a long, sleek brown body on short legs, a pale muzzle and throat, small round ears, whiskers and
    a thick tapering tail. It bounds as it runs, sits up on its haunches in the wind-up (as in its side-view sheet) and
    lunges to bite; beaten, it curls onto its side."""
    P = Pose()
    lunge = {"attack": (2.5, 5.0, 3.5), "hurt": (-2.4, -1.2)}.get(action, (0,) * 4)[f] if action in ("attack", "hurt") else 0.0
    bound = (0.0, 1.2, 0.4, 0.0)[f] if action == "walk" else ((0, 0.3, 0.3, 0)[f] if action == "idle" else 0.0)
    rear = (28.0, 40.0)[f] if action == "windup" else 0.0
    z = 5.0 + bound
    hips = (lunge - 4.6, 0.0, z)
    body_m = rot("b", rear)

    def at(p):
        """A point of the forebody, reared about the hips."""
        return add(hips, apply(body_m, (p[0] - hips[0] + lunge, p[1], p[2] - z)))

    def pale(hit, n):
        """The pale throat and chest under the forebody."""
        fwd = n[0] * _frame["fwd"][0] + n[1] * _frame["fwd"][1]
        return "otter_pale" if n[2] < -0.1 and fwd > -0.2 else None

    P.add(Part(at((0.4, 0.0, z + 0.2)), (6.2, 3.4, 3.2), "otter", "body", body_m, pale),
          Part(hips, (3.8, 3.7, 3.4), "otter", "body"))
    hc = at((6.8, 0.0, z + 1.4))
    head_m = mat_mul(body_m, rot("b", -10.0 - rear * 0.8))
    P.add(Part(hc, (2.9, 2.7, 2.5), "otter", "head", head_m, pale))
    muzzle = add(hc, apply(head_m, (2.5, 0.0, -0.6)))
    P.add(Part(muzzle, (1.5, 1.8, 1.3), "otter_pale", "head", head_m))
    P.mark(add(muzzle, apply(head_m, (1.4, 0.0, 0.5))), INKY)
    for side in (1, -1):
        P.mark(add(hc, apply(head_m, (1.6, side * 1.6, 1.2))), INKY)
        P.add(Part(add(hc, apply(head_m, (-0.6, side * 2.3, 1.9))), (0.8, 0.8, 0.9), "otter", "ear"))
        for w in range(3):   # whiskers
            P.mark(add(muzzle, apply(head_m, (0.6 + w * 0.5, side * (2.0 + w * 0.5), -0.1 - w * 0.3))), MATS["otter_pale"][4])
    for k, (a, b) in enumerate(((3.4, 2.4), (3.4, -2.4), (-5.6, 2.6), (-5.6, -2.6))):
        step_up, stride = _walk(f, k + (k // 2)) if action == "walk" else (0.0, 0.0)
        top = at((a, b, z - 2.0)) if k < 2 else (hips[0] - 1.0, b, z - 2.0)
        foot = add(top, (1.4, 0.0, -2.0)) if (k < 2 and rear) else (top[0] + stride, b, 0.8 + step_up)
        P.add(chain(top, foot, 1.25, 1.0, 4, "otter", "leg"),
              Part(add(foot, (0.5, 0.0, -0.2)), (1.1, 0.9, 0.5), "hide_head", "leg"))
    wag = (0.0, 0.8, 0.0, -0.8)[f] if action in ("idle", "walk") else 0.0
    for k in range(8):
        u = k / 7.0
        p = (hips[0] - 3.2 - 8.0 * u, wag * math.sin(u * 2.4), z - 0.8 - 2.6 * u + (1.2 * u if rear else 0.0))
        r = 1.6 - 0.9 * u
        P.add(Part(p, (r, r, r), "otter", "tail"))
    if action == "death":
        _topple(P, (15.0, 40.0, 70.0, 85.0)[f], z, 3.4)
    return P


# ================================================================================ the tutorial's other foes: helpers
def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _into(m, v):
    """A vector back through a rotation (by its transpose)."""
    return tuple(m[0][i] * v[0] + m[1][i] * v[1] + m[2][i] * v[2] for i in range(3))


def _unframe(P: Pose, v, point: bool = False):
    """A world normal (or, with `point`, a hit point) back in the creature's own frame before its body transform, so a
    pattern stays on the body as it rolls over: a belly shows when a beaten creature lies on its back."""
    fx, fy = _frame["fwd"]
    lx, ly = _frame["left"]
    q = (v[0] * fx + v[1] * fy, v[0] * lx + v[1] * ly, v[2])
    if point:
        q = tuple(q[i] / P.k - P.shift[i] for i in range(3))
    return _into(P.m, q)


def _on(centre, radii, m, u: float, v: float, out: float = 0.2):
    """A point just proud of an ellipsoid's surface, `u` degrees round its equator from its front toward its left and
    `v` up from it, so a mark lands on the part."""
    cu, su = math.cos(math.radians(u)), math.sin(math.radians(u))
    cv, sv = math.cos(math.radians(v)), math.sin(math.radians(v))
    return add(centre, apply(m, ((radii[0] + out) * cv * cu, (radii[1] + out) * cv * su, (radii[2] + out) * sv)))


def _spline(pts, n: int) -> list:
    """`n` points along a Catmull-Rom curve through `pts`, its ends held."""
    Q = [pts[0]] + list(pts) + [pts[-1]]
    segs = len(pts) - 1
    out = []
    for k in range(n):
        u = k / (n - 1) * segs
        s = min(int(u), segs - 1)
        t = u - s
        p0, p1, p2, p3 = Q[s], Q[s + 1], Q[s + 2], Q[s + 3]
        out.append(tuple(0.5 * (2.0 * p1[i] + (p2[i] - p0[i]) * t + (2.0 * p0[i] - 5.0 * p1[i] + 4.0 * p2[i] - p3[i]) * t * t
                                + (3.0 * p1[i] - p0[i] - 3.0 * p2[i] + p3[i]) * t * t * t) for i in range(3)))
    return out


def _pick(table: dict, action: str, f: int, default=0.0):
    """A per-frame value of an action from `table` (action: one value per frame), else `default`."""
    return table[action][f] if action in table else default


# ================================================================================ Old Snapper
def snapper(action: str, f: int) -> Pose:
    """Old Snapper, the Reed Shallows' old elite: an ancient river snapping turtle. A high domed shell grown over with
    moss along three knobbed keels, its dark green flanks seamed into plates, a serrated back edge with barnacles on the
    rim and river weed trailing behind; a big khaki head with a pale hooked beak and amber eyes; thick scaled legs and a
    saw-backed tail; and on its right the great red crusher claw with dark tips, as on its side-view sheet. It breathes
    and works the pincer while idle, lumbers on diagonal pairs of legs with its shell rocking, raises the crusher high
    over its head in the wind-up and slams it down before it in a splash; struck, it pulls its head into its shell;
    beaten, it rolls onto its back."""
    P = Pose()
    lunge = _pick({"attack": (0.6, 1.4, 1.0), "hurt": (-1.8, -0.9)}, action, f)
    rock = _pick({"walk": (0.0, 3.0, 0.0, -3.0)}, action, f)
    breathe = _pick({"idle": (0.0, 0.25, 0.4, 0.15)}, action, f)
    rear = _pick({"windup": (4.0, 7.0), "attack": (2.0, -1.5, -0.5)}, action, f)
    z = 6.6 + breathe * 0.4
    C = (lunge, 0.0, z)
    body_m = mat_mul(rot("a", rock), rot("b", rear))

    def at(p):
        """A point of the shell's frame (from its middle), rocked and reared with it."""
        return add(C, apply(body_m, p))

    def local(hit, n):
        return _into(body_m, _sub(_unframe(P, hit, True), C)), _into(body_m, _unframe(P, n))

    def plates(a: float, b: float) -> bool:
        """The seams between the shell's plates: a row of five down the spine, four a side beside it."""
        if abs(abs(b) - 3.9) < 0.4:
            return True
        return min(abs(a - s) for s in ((-5.0, -1.4, 2.2, 5.6) if abs(b) < 3.9 else (-3.2, 0.6, 4.2))) < 0.4

    def carapace(hit, n):
        """Moss over the dome's top in patches, lighter blotches in it and the plates' seams faint under it; the dark
        green plates on the flanks, their seams a step darker; the pale plastron underneath."""
        q, ln = local(hit, n)
        if ln[2] < -0.25:
            return "snap_belly"
        a, b = q[0], q[1]
        seam = plates(a, b)
        if ln[2] > 0.58 - 0.14 * h01(int(a * 1.2 + 40), int(b * 1.2 + 40), 3):
            if seam:
                return "snap_moss_seam"
            return "snap_moss_lit" if h01(int(a * 0.9 + 40), int(b * 0.9 + 40), 5) > 0.74 else "snap_moss"
        return "snap_seam" if seam else None

    def rim(hit, n):
        """The marginal plates round the rim, seamed every 30 degrees."""
        q, ln = local(hit, n)
        if ln[2] < -0.35:
            return "snap_belly"
        return "snap_seam" if math.degrees(math.atan2(q[1] / 10.4, q[0] / 12.0)) % 30.0 < 5.0 else None

    def plastron(hit, n):
        """The plastron's plates (seen when it lies on its back): a seam down its middle and three across."""
        q, _ = local(hit, n)
        return "snap_belly_seam" if abs(q[1]) < 0.4 or min(abs(q[0] - s) for s in (-4.2, 0.2, 4.4)) < 0.4 else None

    rim_c, rim_r = at((0.0, 0.0, -2.6)), (12.0, 10.4, 2.2)
    P.add(Part(rim_c, rim_r, "snap_shell", "shell", body_m, rim),
          Part(at((0.4, 0.0, -3.6)), (10.2, 8.6, 1.9), "snap_belly", "shell", body_m, plastron),
          Part(at((0.0, 0.0, -0.8)), (11.0, 9.4, 5.6), "snap_shell", "shell", body_m, carapace))
    # Three keels of knobs along the dome, and the serrated back edge.
    for b0, row in ((0.0, (-6.8, -3.6, -0.4, 2.8, 5.8)), (4.3, (-5.0, -1.6, 1.8)), (-4.3, (-5.0, -1.6, 1.8))):
        for a0 in row:
            top = -0.8 + 5.6 * math.sqrt(max(0.0, 1.0 - (a0 / 11.0) ** 2 - (b0 / 9.4) ** 2))
            P.add(Part(at((a0, b0, top - 0.1)), (1.3, 0.9, 0.9), "snap_shell", "keel", body_m))
    for ang in (144.0, 162.0, 180.0, 198.0, 216.0):
        P.add(Part(at((12.0 * math.cos(math.radians(ang)), 10.4 * math.sin(math.radians(ang)), -2.6)), (1.3, 1.3, 0.9),
                   "snap_shell", "shell", body_m))
    for u, v in ((32.0, 30.0), (52.0, 10.0), (-38.0, 25.0), (76.0, 35.0), (-72.0, 15.0), (112.0, 25.0)):
        P.mark(_on(rim_c, rim_r, body_m, u, v), BARNACLE)
        P.mark(_on(rim_c, rim_r, body_m, u + 4.0, v - 12.0), BARNACLE_SHADE)
    # River weed trailing from the back edge, stirring as it moves.
    sway = _pick({"idle": (0.0, 0.6, 1.0, 0.4), "walk": (0.0, 1.0, 0.0, -1.0)}, action, f, 0.3)
    for k, b0 in enumerate((-4.2, 0.8, 5.0)):
        root = at((-11.2 + abs(b0) * 0.2, b0, -2.4))
        tip = (lunge - 14.8 - k * 0.6, b0 * 1.1 + sway * (1.0 if k % 2 else -1.0), 0.8)
        P.add(chain(root, tip, 0.6, 0.45, 6, "weed", "weed%d" % k))
    # The head on its thick neck: pulled into the shell when struck, dropped when beaten.
    neck = _pick({"hurt": (0.2, 0.45), "death": (0.5, 0.4, 0.4, 0.4)}, action, f, 1.0)
    bob = _pick({"idle": (0.0, 0.2, 0.3, 0.1), "walk": (0.0, 0.4, 0.0, 0.4)}, action, f)
    pitch = _pick({"windup": (8.0, 14.0), "attack": (-6.0, -12.0, -8.0), "death": (-6.0, -12.0, -14.0, -14.0)}, action, f)
    gape = _pick({"idle": (0.0, 0.0, 0.15, 0.0), "windup": (0.3, 0.6), "attack": (0.5, 0.2, 0.3), "hurt": (0.4, 0.2)}, action, f)
    hc = at((10.6 + 3.4 * neck, 0.0, -0.9 + bob))
    head_m = mat_mul(body_m, rot("b", pitch))
    P.add(chain(at((7.2, 0.0, -1.4)), hc, 2.5, 2.7, 4, "snap_skin", "neck"),
          Part(hc, (3.9, 3.4, 3.0), "snap_skin", "head", head_m))
    beak = add(hc, apply(head_m, (3.5, 0.0, -0.4)))
    P.add(Part(beak, (1.9, 2.2, 1.9), "snap_beak", "head", head_m))
    P.mark(add(beak, apply(head_m, (2.0, 0.0, -0.8))), HOOK)
    if gape > 0.0:
        jm = mat_mul(head_m, rot("b", -gape * 35.0))
        hinge = add(hc, apply(head_m, (0.6, 0.0, -1.6)))
        P.add(Part(add(hinge, apply(jm, (2.8, 0.0, -0.3))), (2.6, 2.2, 0.9), "snap_beak", "jaw", jm))
    for side in (1, -1):
        P.mark(add(hc, apply(head_m, (1.7, side * 2.9, 1.1))), SNAP_EYE)
        P.mark(add(hc, apply(head_m, (2.4, side * 2.6, 1.2))), INKY)
        P.mark(add(hc, apply(head_m, (1.2, side * 2.5, 2.3))), MATS["snap_skin"][0])
    for u, v in ((150.0, 50.0), (-140.0, 40.0), (180.0, 70.0), (110.0, 60.0)):
        P.mark(_on(hc, (3.9, 3.4, 3.0), head_m, u, v), MATS["snap_skin"][1])
    # Legs: thick, splayed, stepping in diagonal pairs; they tuck in when struck and curl up when it lies on its back.
    curl = _pick({"death": (0.3, 0.7, 1.0, 1.0)}, action, f)
    tuck = _pick({"hurt": (0.5, 0.25)}, action, f)
    for k, (a, b) in enumerate(((5.6, 8.4), (5.6, -8.4), (-6.0, 8.0), (-6.0, -8.0))):
        up, stride = _walk(f, k + (k // 2)) if action == "walk" else (0.0, 0.0)
        hip = at((a * 0.85, b * 0.78, -2.8))
        out = 1.0 - 0.4 * curl - 0.3 * tuck
        foot = (lunge + a * (0.9 + 0.1 * out) + stride * 1.2, b * (0.78 + 0.34 * out), 1.1 + up * 0.9 + curl * 3.0)
        pad = add(foot, (0.8 if a > 0 else -0.5, 0.0, -0.2))
        P.add(chain(hip, foot, 2.3, 2.0, 4, "snap_skin", "leg%d" % k), Part(pad, (2.3, 2.0, 1.1), "snap_skin", "leg%d" % k))
        if a > 0:
            for u in (-28.0, 0.0, 28.0):
                P.mark(_on(pad, (2.3, 2.0, 1.1), IDENT, u, 10.0), TALON)
    # The saw-backed tail.
    wag = _pick({"idle": (0.0, 0.5, 0.0, -0.5), "walk": (0.0, 1.0, 0.0, -1.0)}, action, f)
    root, tip = at((-9.8, 0.0, -2.6)), (lunge - 18.0, wag * 2.0, 1.2)
    P.add(chain(root, tip, 2.0, 0.7, 7, "snap_skin", "tail"))
    for u in (0.25, 0.45, 0.65, 0.82):
        p = tuple(root[i] + (tip[i] - root[i]) * u for i in range(3))
        P.add(Part(add(p, (0.0, 0.0, 2.0 - 1.3 * u + 0.1)), (0.8, 0.5, 0.7), "snap_skin", "saw"))
    # The crusher on its right: held low before it and working while idle, raised high over its head in the wind-up
    # (gaping), slammed down before it on the strike (a splash on frame 1 and after), drawn in when struck.
    snap = _pick({"idle": (0.35, 0.5, 0.6, 0.3)}, action, f, 0.35)
    swing = _pick({"walk": (0.0, 0.8, 0.0, -0.8)}, action, f)
    if action == "windup":
        elbow, palm, pitch, yaw, open_ = (8.4, -11.6, 3.5 + f * 2.0), (9.0 + f * 0.4, -10.6, 10.5 + f * 4.0), 55.0 + f * 20.0, -10.0, 0.7 + 0.3 * f
    elif action == "attack":
        elbow, palm, pitch, yaw, open_ = (((10.4, -11.0, 2.6), (14.0, -10.2, 6.2), 22.0, -8.0, 0.6),
                                          ((10.8, -10.4, -1.8), (14.4, -8.8, -3.3), -12.0, -6.0, 0.0),
                                          ((10.8, -10.4, -1.8), (14.4, -8.8, -3.3), -12.0, -6.0, 0.05))[f]
    elif action == "hurt":
        elbow, palm, pitch, yaw, open_ = (8.8, -10.8, -1.4), (11.6, -10.8, -1.6), 4.0, -14.0, 0.3
    elif action == "death":
        elbow, palm, pitch, yaw, open_ = (9.6, -11.0, -2.4), (11.6, -11.0, -2.6), -8.0, -20.0, 0.5
    else:
        elbow, palm, pitch, yaw, open_ = (10.0, -11.0, -1.2), (13.2 + swing, -10.0, 0.6), 22.0, -10.0, snap
    cm = mat_mul(body_m, mat_mul(rot("c", yaw), rot("b", pitch)))
    el, pc = at(elbow), at(palm)
    P.add(chain(at((6.8, -7.6, -1.6)), el, 1.9, 2.0, 3, "crusher", "claw"), chain(el, pc, 2.0, 2.3, 3, "crusher", "claw"),
          Part(pc, (4.3, 3.1, 3.5), "crusher", "claw", cm),
          Part(add(pc, apply(cm, (4.4, 0.3, -1.4))), (2.5, 1.6, 1.3), "crusher", "claw", cm),
          Part(add(pc, apply(cm, (7.0, 0.3, -1.0))), (1.6, 1.2, 1.0), "crusher_tip", "claw", cm))
    dm = mat_mul(cm, rot("b", open_ * 50.0))
    hinge = add(pc, apply(cm, (2.0, 0.0, 1.4)))
    P.add(Part(add(hinge, apply(dm, (3.0, -0.2, 0.6))), (2.6, 1.5, 1.3), "crusher", "dactyl", dm),
          Part(add(hinge, apply(dm, (5.6, -0.2, 0.7))), (1.6, 1.2, 1.0), "crusher_tip", "dactyl", dm))
    for t in (3.4, 4.6, 5.8):
        P.mark(add(pc, apply(cm, (t, 0.3, -0.05))), CLAW_TOOTH)
    if action == "attack" and f >= 1:
        imp = add(pc, apply(cm, (4.2, 0.0, 0.0)))
        rr, hh = (3.4, 4.4)[f - 1], (1.6, 3.4)[f - 1]
        for k in range(12):
            ang = math.radians(k * 30.0 + (15.0 if f == 2 else 0.0))
            lift = hh * (0.55 + 0.45 * math.sin(ang * 2.0 + f))
            P.fx.append(((imp[0] + math.cos(ang) * rr, imp[1] + math.sin(ang) * rr * 0.9, 0.3 + lift), SPLASH if k % 2 else SPLASH_DIM))
            P.fx.append(((imp[0] + math.cos(ang) * (rr + 1.0), imp[1] + math.sin(ang) * (rr + 1.0) * 0.9, 0.0), SPLASH_DIM))
        for d in ((0.0, 0.0, 4.0 + hh), (1.2, 1.0, 3.0 + hh), (-1.0, -1.2, 3.4 + hh), (0.4, -0.6, 5.2 + hh)):
            P.fx.append((add((imp[0], imp[1], 0.0), d), SPLASH))
    if action == "death":
        _topple(P, (30.0, 80.0, 135.0, 172.0)[f], z, 5.0)
    return P


# ================================================================================ the mossback toad
def toad(action: str, f: int) -> Pose:
    """The mossback toad: a fat, warty toad in olive khaki, a mat of bright moss and three curled fern sprouts growing
    on its back, parotoid ridges behind golden slit-pupilled eyes under heavy lids, a wide down-turned mouth and a
    cream belly and throat sac. It breathes with a fluttering throat while its ferns sway, goes in short heavy hops,
    puffs its cheeks and throat up in the wind-up, and lashes a long pink tongue out at its prey (as far as its cell
    lets it); beaten, it flops onto its back."""
    P = Pose()
    hop = _pick({"walk": (0.0, 1.8, 2.8, 0.6)}, action, f)
    ahead = _pick({"walk": (0.0, 0.8, 1.8, 2.6), "hurt": (-1.8, -0.8)}, action, f)
    sq = _pick({"walk": (0.9, 1.0, 1.02, 0.94), "idle": (1.0, 1.03, 1.05, 1.02), "hurt": (0.88, 0.95)}, action, f, 1.0)
    lean = _pick({"walk": (0.0, 12.0, 6.0, -6.0), "windup": (6.0, 10.0), "attack": (3.0, 2.0, 1.0), "hurt": (-6.0, -3.0)}, action, f)
    puff = _pick({"idle": (0.0, 0.15, 0.25, 0.1), "windup": (0.6, 1.0), "attack": (0.3, 0.15, 0.2)}, action, f)
    z = 4.4 * sq + hop
    tilt = rot("b", lean)
    centre = (ahead - 1.0, 0.0, z)

    def at(p):
        return add(centre, apply(tilt, p))

    def hide(hit, n):
        """The cream belly underneath; the moss over the back behind the head, its edge ragged."""
        ln = _into(tilt, _unframe(P, n))
        if ln[2] < -0.4:
            return "toad_belly"
        q = _into(tilt, _sub(_unframe(P, hit, True), centre))
        if q[0] < 3.0 and ln[2] > 0.4 + 0.28 * h01(int(q[0] * 1.5 + 30), int(q[1] * 1.5 + 30), 11):
            return "toad_moss"
        return None

    body_r = (6.8, 6.4, 3.9 * sq)
    P.add(Part(centre, body_r, "toad", "body", tilt, hide),
          Part(at((5.0, 0.0, 0.4)), (4.0, 5.5, 2.7 * sq), "toad", "body", tilt, hide),
          Part(at((7.9, 0.0, -0.3)), (2.0, 4.0, 1.7), "toad", "body", tilt, hide))
    for side in (1, -1):
        P.add(Part(at((2.4, side * 3.7, 2.9 * sq)), (2.4, 1.4, 1.0), "toad", "gland%d" % side, tilt))
    for u, v in ((50.0, 18.0), (85.0, 10.0), (118.0, 22.0), (150.0, 14.0), (100.0, 32.0), (68.0, 28.0)):
        for side in (1, -1):
            P.mark(_on(centre, body_r, tilt, side * u, v), WART)
    # Moss tufts breaking the back's line, and three fiddlehead ferns curling up out of it, swaying.
    sway = _pick({"idle": (0.0, 0.5, 0.8, 0.3), "walk": (0.0, 0.8, 0.3, -0.6)}, action, f, 0.6 if action == "windup" else 0.0)
    for p in ((-4.4, 0.8, 3.2), (0.6, 2.8, 3.2), (-1.6, -3.0, 3.2), (-5.4, -1.8, 2.3)):
        P.add(Part(at((p[0], p[1], p[2] * sq)), (1.2, 1.1, 0.9), "toad_moss", "moss", tilt))
    for k, (a0, b0) in enumerate(((-2.4, 1.8), (-0.2, -1.2), (-4.6, -0.4))):
        s = sway * (1.0 if k % 2 else -1.0)
        h0 = 3.6 * sq
        frond = _spline([(a0, b0, h0), (a0 - 0.4, b0 + s * 0.3, h0 + 2.0), (a0 - 0.1, b0 + s * 0.6, h0 + 3.8),
                         (a0 + 1.0, b0 + s * 0.8, h0 + 4.5), (a0 + 1.7, b0 + s * 0.8, h0 + 3.7), (a0 + 1.0, b0 + s * 0.7, h0 + 3.0)], 11)
        for q in frond:
            P.add(Part(at(q), (0.62, 0.62, 0.62), "toad_fern", "fern%d" % k))
    # Golden eyes on top of the head, a black slit in each, heavy lids (lower in the wind-up's glare).
    for side in (1, -1):
        eye = at((5.4, side * 2.9, 2.5 * sq))
        P.add(Part(eye, (1.8, 1.7, 1.5), "toad_eye", "eye%d" % side, tilt))
        P.mark(add(eye, apply(tilt, (1.6, side * 0.4, 0.5))), INKY)
        P.mark(add(eye, apply(tilt, (1.2, side * 0.5, 1.0))), INKY)
        P.mark(add(eye, apply(tilt, (-0.2, side * 0.5, 1.2 if action == "windup" else 1.4))), MATS["toad"][1])
        if action == "windup":
            P.mark(add(eye, apply(tilt, (0.6, side * 0.6, 1.4))), MATS["toad"][1])
        for u in (38.0, 58.0, 78.0):
            P.mark(_on(at((7.9, 0.0, -0.3)), (2.0, 4.0, 1.7), tilt, side * u, -16.0), TOAD_MOUTH)
    # The throat sac (and in the wind-up the cheeks) puff up.
    P.add(Part(at((6.3, 0.0, -2.4)), (1.8 + puff * 1.3, 3.0 + puff * 1.6, 1.2 + puff * 1.5), "toad_sac", "throat", tilt))
    if puff > 0.3:
        for side in (1, -1):
            P.add(Part(at((5.4, side * 4.2, -0.4)), (1.4 + puff, 1.0 + puff * 0.9, 1.1 + puff * 0.8), "toad_sac", "cheek%d" % side, tilt))
    # Legs: the thick hind legs folded at its sides, trailing in a hop; short front legs propping the chest.
    air = action == "walk" and hop > 1.0
    for side in (1, -1):
        if air:
            hip, knee, foot = (ahead - 4.2, side * 3.8, z - 1.0), (ahead - 7.4, side * 4.8, z - 1.8), (ahead - 10.2, side * 4.4, z - 2.4)
        else:
            hip, knee, foot = (ahead - 4.0, side * 4.6, z - 1.6), (ahead + 0.4, side * 6.6, 2.2), (ahead - 3.0, side * 6.8, 0.6)
        P.add(Part(add(hip, (0.6, 0.0, 0.0)), (3.2, 2.2, 2.3), "toad", "hind%d" % side, rot("c", side * 20.0)),
              chain(hip, knee, 1.8, 1.4, 4, "toad_leg", "hind%d" % side),
              chain(knee, foot, 1.3, 1.0, 4, "toad_leg", "hind%d" % side),
              Part(add(foot, (-0.8 if air else 1.0, 0.0, 0.0)), (2.1, 1.5, 0.55), "toad_leg", "hind%d" % side))
        hand = (ahead + 5.4 + (1.8 if air else 0.0), side * 4.8, 0.6 + (hop * 0.5 if air else 0.0))
        P.add(chain(at((3.8, side * 3.6, -2.2)), hand, 1.2, 1.0, 4, "toad_leg", "arm%d" % side),
              Part(hand, (1.3, 1.1, 0.5), "toad_leg", "arm%d" % side))
    # The tongue lash: out to its full reach on the strike (frame 1, a glint at its sticky tip), then reeled in.
    if action == "attack":
        reach = (6.0, 13.0, 8.0)[f]
        mouth = at((9.2, 0.0, -0.8))
        tip = (mouth[0] + reach, 0.0, max(2.2, mouth[2] - reach * 0.08))
        P.add(chain(mouth, tip, 0.9, 0.8, max(4, int(reach * 1.4)), "tongue", "tongue"), Part(tip, (1.5, 1.4, 1.2), "tongue", "tongue"))
        if f == 1:
            for d in ((1.9, 0.0, 1.6), (2.5, 0.0, 2.2), (1.3, 0.0, 2.2), (1.9, 0.0, 2.8)):
                P.fx.append((add(tip, d), GLINT))
    if action == "death":
        _topple(P, (35.0, 90.0, 145.0, 172.0)[f], z, 4.0)
    return P


# ================================================================================ the hollow minnow
def minnow(action: str, f: int) -> Pose:
    """The hollow minnow: a small river fish drained grey by the Hollow, swimming through the night air. It flies (the
    enemy's `flying`): the view draws it at its hover, about 24 art px up, its shadow on the ground under it, so the fish
    is drawn round its feet. A dark back and a pale belly, a ragged dorsal fin, a forked tail, an empty white eye in a
    dark socket; two grey strands trail and rise from its tail as its wake, the hollowing look. It hangs and sways
    while idle, swims with a swish of its tail, draws back gaping in the wind-up and darts in to nibble; struck, it
    jerks back; beaten, it turns belly-up and comes apart into grey mist."""
    P = Pose()
    if action == "death" and f >= 2:
        # Coming apart: three grey puffs (frame 2), then only motes drifting up (frame 3).
        if f == 2:
            for k, (a, b, c_, r) in enumerate(((1.8, 0.2, 0.4, 1.4), (-1.2, -0.3, 0.9, 1.2), (-3.8, 0.4, 0.3, 0.9))):
                P.add(Part((a, b, c_), (r, r, r * 0.8), "mist", "puff%d" % k))
        for k in range(9):
            ang = math.radians(k * 40.0 + f * 20.0)
            rr = 2.5 + f * 1.6 + (k % 3) * 0.6
            P.fx.append(((math.cos(ang) * rr, math.sin(ang) * rr * 0.6, 0.6 + f * 1.2 + (k % 4) * 0.7), MOTE if k % 2 else MOTE_DIM))
        return P
    dart = _pick({"windup": (-1.5, -3.0), "attack": (2.5, 5.5, 3.5), "hurt": (-2.0, -1.0)}, action, f)
    bob = _pick({"idle": (0.0, -0.4, -0.6, -0.2), "walk": (0.0, 0.3, 0.0, -0.3)}, action, f)
    swish = _pick({"idle": (6.0, 14.0, 8.0, -4.0), "walk": (26.0, 8.0, -24.0, -8.0), "windup": (28.0, 40.0),
                   "attack": (-18.0, -8.0, 12.0), "hurt": (22.0, 10.0)}, action, f)
    nose = _pick({"windup": (6.0, 10.0), "attack": (-4.0, -8.0, -2.0), "hurt": (12.0, 6.0)}, action, f)
    flap = _pick({"idle": (0.0, -15.0, -25.0, -10.0), "walk": (-10.0, -25.0, -30.0, -15.0), "windup": (-20.0, -35.0)}, action, f)
    gape = _pick({"windup": (0.5, 1.0), "attack": (1.0, 0.0, 0.3)}, action, f)
    trail = _pick({"idle": (4.0, 4.5, 5.0, 4.5), "walk": (5.0, 5.5, 6.0, 5.5), "attack": (6.0, 7.0, 6.0), "hurt": (3.0, 3.5),
                   "death": (3.0, 2.0)}, action, f)
    body_m = rot("b", nose)
    C = (dart, 0.0, bob)

    def at(p):
        return add(C, apply(body_m, p))

    def fish(hit, n):
        ln = _unframe(P, n)
        return "minnow_back" if ln[2] > 0.5 else ("minnow_belly" if ln[2] < -0.35 else None)

    P.add(Part(at((0.0, 0.0, 0.0)), (4.2, 1.9, 2.3), "minnow", "body", body_m, fish),
          Part(at((3.1, 0.0, 0.1)), (2.3, 1.7, 1.95), "minnow", "body", body_m, fish))
    tm = mat_mul(body_m, rot("c", swish))
    piv = at((-3.0, 0.0, 0.0))
    P.add(Part(add(piv, apply(tm, (-1.5, 0.0, 0.0))), (2.1, 0.95, 1.35), "minnow", "body", tm, fish))
    for s in (1, -1):   # the forked tail: an upper and a lower lobe
        P.add(Part(add(piv, apply(tm, (-4.0, 0.0, s * 0.9))), (1.9, 0.35, 0.8), "minnow_fin", "tail", mat_mul(tm, rot("b", -s * 38.0))))
    for a, h in ((-1.4, 1.0), (-0.3, 1.5), (0.8, 1.1), (1.7, 0.6)):   # the ragged dorsal fin
        P.add(Part(at((a, 0.0, 2.0 + h * 0.5)), (0.6, 0.3, h), "minnow_fin", "dorsal", body_m))
    for s in (1, -1):
        P.add(Part(at((1.6, s * 1.5, -0.8)), (1.2, 0.9, 0.3), "minnow_fin", "pec%d" % s, mat_mul(body_m, rot("a", s * flap))))
        P.mark(_on(at((3.1, 0.0, 0.1)), (2.3, 1.7, 1.95), body_m, s * 62.0, 30.0), MATS["minnow_back"][0])
        P.mark(_on(at((3.1, 0.0, 0.1)), (2.3, 1.7, 1.95), body_m, s * 50.0, 14.0), HOLLOW_EYE if action != "hurt" else MATS["minnow_back"][0])
    P.mark(at((5.35, 0.0, -0.3)), FISH_MOUTH)
    if gape > 0.0:
        P.add(Part(at((3.8, 0.0, -1.2 - gape * 0.4)), (1.4, 1.0, 0.45), "minnow_belly", "jaw", mat_mul(body_m, rot("b", -30.0 * gape))))
        P.mark(at((5.0, 0.0, -0.8)), FISH_MOUTH)
    if action == "attack" and f == 1:
        for d in ((6.6, 0.0, 0.4), (7.2, 0.0, 0.9), (6.1, 0.0, 0.9)):
            P.fx.append((at(d), GLINT))
    # The wake: two grey strands trailing from the tail and rising, waving as it swims.
    wave = _pick({"idle": (0.0, 0.4, 0.0, -0.4), "walk": (0.0, 0.7, 0.0, -0.7)}, action, f)
    for s in (1, -1):
        root = add(piv, apply(tm, (-5.4, s * 0.4, 0.3)))
        pts = [root, (root[0] - trail * 0.35, root[1] + s * 0.7 + wave, root[2] + 0.3),
               (root[0] - trail * 0.7, root[1] + s * 0.5 - wave, root[2] + 0.8), (root[0] - trail, root[1] + s * 1.2 + wave * 0.5, root[2] + 1.4)]
        for p in _spline(pts, 8):
            P.add(Part(p, (0.42, 0.42, 0.42), "h_stripe", "strand%d" % s))
    if action == "hurt":
        P.m = rot("a", (24.0, 12.0)[f])
    elif action == "death":
        P.m = rot("a", (80.0, 165.0)[f])
        if f == 1:
            for k in range(5):
                ang = math.radians(k * 72.0 + 10.0)
                P.fx.append(((math.cos(ang) * 5.0, math.sin(ang) * 2.4, 1.0 + k * 0.5), MOTE_DIM))
    return P


# ================================================================================ the hollowed eel
# The eel hovers 40 world units over the river's surface (enemy_authority.gd `_eel`), 20 art px (TopdownRoom.ART),
# and the view draws a foe's feet where it hovers and its shadow on the surface under it. So the figure rises out of
# water drawn EEL_LIFT px under its feet, where the view lays the shadow, as the side view's sheet does with its pool.
EEL_LIFT = 20.0
# Per frame, from its side-view sheet (tools/art/creatures/hollowed_eel.py): the spine's control points (x ahead, y
# down from the water, its art px; the first under the water), the head's tilt, the gape, the eyes and how far it
# has sunk; the view's frames are picked from the side view's (idle 4 of 4, windup 1 and 3 of 3, attack 1-3 of 4,
# hurt 2 of 2, death 2-5 of 5).
_EEL_IDLE = ((0, 8), (-6, -12), (8, -32), (20, -50), (12, -70), (24, -84))
EEL = {
    "idle": [(_EEL_IDLE, 0, 0.0, "open", 0), (((0, 8), (-5, -12), (9, -32), (21, -50), (13, -70), (25, -83)), -2, 0.0, "open", 0),
             (((0, 8), (-4, -12), (10, -32), (21, -50), (14, -70), (26, -83)), -3, 0.1, "open", 0),
             (((0, 8), (-5, -12), (9, -32), (20, -50), (13, -70), (25, -84)), -1, 0.0, "open", 0)],
    "walk": [(_EEL_IDLE, 0, 0.0, "open", 0), (_EEL_IDLE, -2, 0.0, "open", 0), (_EEL_IDLE, -2, 0.0, "open", 0),
             (_EEL_IDLE, 0, 0.0, "open", 0)],
    "windup": [(((0, 8), (-4, -14), (10, -32), (16, -50), (6, -68), (14, -84)), 12, 0.5, "wide", 0),
               (((0, 8), (-1, -16), (13, -32), (11, -50), (-2, -66), (2, -85)), 28, 1.0, "wide", 0)],
    "attack": [(((0, 8), (-4, -14), (10, -30), (23, -44), (35, -54), (46, -60)), -6, 1.0, "wide", 0),
               (((0, 8), (-2, -14), (13, -28), (28, -40), (42, -48), (54, -51)), -12, 0.1, "wide", 0),
               (((0, 8), (-4, -13), (10, -30), (24, -46), (30, -64), (42, -74)), -4, 0.4, "open", 0)],
    "hurt": [(((0, 8), (-5, -12), (10, -32), (16, -50), (4, -68), (8, -86)), 26, 0.6, "squeeze", 0),
             (((0, 8), (-6, -12), (9, -32), (18, -50), (9, -70), (18, -85)), 12, 0.3, "squeeze", 0)],
    "death": [(((0, 8), (-6, -12), (6, -30), (18, -44), (20, -60), (32, -66)), -24, 0.5, "dead", 18),
              (((0, 8), (-6, -12), (6, -28), (18, -40), (24, -52), (36, -54)), -32, 0.4, "dead", 42),
              (((0, 8), (-6, -12), (6, -28), (18, -40), (24, -52), (36, -54)), -36, 0.4, "dead", 62),
              (((0, 8), (-6, -12), (6, -28), (18, -40), (24, -52), (36, -54)), -36, 0.4, "dead", 90)],
}
EEL_AHEAD, EEL_UP = 0.5, 0.55     # the side view's art px to the figure's, ahead and up (a lunge's reach a little less)
EEL_S = (0.0, 2.6, -1.8, 2.2, -0.9, 0.3)   # its S-curve sideways too, so it winds from every side, not a pillar
EEL_FIN = (1.4, 2.2, 1.0, 2.4, 1.6, 0.8, 2.0, 1.4, 2.2, 1.0, 1.8, 1.2)   # the torn dorsal fin's plates


def eel(action: str, f: int) -> Pose:
    """The hollowed eel: a huge river eel drained grey by the Hollow, rising out of the river in an S-curve over a dark
    stain in the water. A grey body with a pale belly down its front, a torn dorsal fin along its back, gill slits, a
    long snout with a hinged jaw of jagged teeth, empty white eyes in a cold halo; grey strands rise off its back, and
    behind it a loop of its back breaks the surface. Foam rings its body where it leaves the water, rings spread from
    it and a wake trails when it glides. It sways while idle, undulates as it glides, rears back gaping in the wind-up,
    lunges head-down on the strike, snaps back when struck and sinks back under the water in death."""
    P = Pose()
    P.water = wz = -EEL_LIFT / math.cos(ELEV)
    ctrl, head_deg, gape, eye, sink = EEL[action][f]
    sway = _pick({"idle": (0.0, 0.8, 1.2, 0.5), "walk": (0.0, -0.6, 0.0, 0.6)}, action, f)
    ahead = {"attack": 0.42, "death": 0.38}.get(action, EEL_AHEAD)
    pts = [(x * ahead, EEL_S[k] + sway * (k / 5.0) ** 2, wz - (y + sink) * EEL_UP) for k, (x, y) in enumerate(ctrl)]
    spine = _spline(pts, 60)
    if action == "walk":   # a wave rolls up the body
        ph = f / 4.0 * math.tau
        out = []
        for k, q in enumerate(spine):
            t = k / (len(spine) - 1)
            nxt, prv = spine[min(k + 1, len(spine) - 1)], spine[max(k - 1, 0)]
            ta, tc = nxt[0] - prv[0], nxt[2] - prv[2]
            ln = math.hypot(ta, tc) or 1.0
            s = 1.7 * math.sin(ph - t * 6.0) * min(1.0, t * 3.0) * (1.0 - t * 0.4)
            out.append((q[0] - tc / ln * s, q[1], q[2] + ta / ln * s))
        spine = out
    n = len(spine)

    def radius(t):
        prof = ((0.0, 4.8), (0.3, 4.4), (0.6, 3.9), (0.85, 3.4), (1.0, 3.2))
        for (t0, r0), (t1, r1) in zip(prof, prof[1:]):
            if t <= t1:
                return r0 + (r1 - r0) * (t - t0) / (t1 - t0)
        return prof[-1][1]

    def belly(hit, nn):
        ln = _unframe(P, nn)
        return "eel_belly" if ln[0] > 0.5 or ln[2] < -0.6 else None

    def tangent(k):
        a, b = spine[max(k - 3, 0)], spine[min(k + 3, n - 1)]
        ta, tc = b[0] - a[0], b[2] - a[2]
        ln = math.hypot(ta, tc) or 1.0
        return ta / ln, tc / ln

    for k, q in enumerate(spine):
        r = radius(k / (n - 1))
        P.add(Part(q, (r, r, r), "eel", "body", IDENT, belly))
    # The torn dorsal fin along its back (the side away from the belly), fluttering.
    for i, k in enumerate(range(10, n - 8, 3)):
        ta, tc = tangent(k)
        da, dc = -tc, ta
        h = EEL_FIN[i % len(EEL_FIN)] + 0.35 * math.sin(f * 1.7 + i)
        r = radius(k / (n - 1))
        q = spine[k]
        if q[2] < wz:
            continue
        m = ((ta, 0.0, da), (0.0, 1.0, 0.0), (tc, 0.0, dc))
        P.add(Part((q[0] + da * (r + h * 0.5 - 0.5), q[1], q[2] + dc * (r + h * 0.5 - 0.5)), (1.5, 0.45, h * 0.95), "eel_fin", "fin", m))
    # A loop of its back breaking the surface behind it, a fin tip beyond; it rolls back along the body as it glides.
    roll = _pick({"walk": (0.0, -0.8, -1.6, -0.8)}, action, f)
    lift = _pick({"idle": (0.0, 0.3, 0.5, 0.2), "walk": (0.0, 0.8, 0.2, -0.6)}, action, f) - sink * EEL_UP
    under = -2.6 - sink * EEL_UP
    loop = ((-5.6, 2.0, under), (-7.4, 3.8, 2.4 + lift), (-9.4, 5.6, 3.4 + lift), (-11.2, 7.2, 1.4 + lift * 0.5), (-12.6, 8.6, under))
    hump = _spline([(a + roll, b, wz + c_) for a, b, c_ in loop], 16)
    for k, q in enumerate(hump):
        P.add(Part(q, (3.0 - 0.5 * k / 15.0,) * 3, "eel", "hump", IDENT, belly))
    for k in (5, 8, 11):
        q = hump[k]
        P.add(Part((q[0], q[1], q[2] + 3.0), (1.0, 0.35, 0.9 + 0.3 * (k % 3)), "eel_fin", "hump_fin", rot("c", -42.0)))
    P.add(Part((-14.2 + roll, 10.2, wz + 0.2 + lift * 0.4), (1.8, 0.35, 1.4), "eel_fin", "tail", mat_mul(rot("c", -42.0), rot("b", -20.0))))
    # The head: its skull and long snout along the neck's end, tilted like the side view's; the jaw hangs by the gape.
    H = spine[-1]
    ta, tc = tangent(n - 1)
    pitch = math.degrees(math.atan2(tc, ta)) * 0.35 + head_deg * 0.8
    head_m = rot("b", pitch)
    P.add(Part(add(H, apply(head_m, (1.0, 0.0, 0.3))), (3.8, 3.0, 2.7), "eel", "head", head_m, belly),
          Part(add(H, apply(head_m, (4.6, 0.0, -0.2))), (2.8, 2.1, 1.7), "eel", "head", head_m))
    jm = mat_mul(head_m, rot("b", -gape * 38.0))
    hinge = add(H, apply(head_m, (0.8, 0.0, -1.3)))
    if gape > 0.2:
        P.add(Part(add(hinge, apply(mat_mul(head_m, rot("b", -gape * 19.0)), (3.0, 0.0, -0.2))), (2.6, 1.5, 0.8), "eel_fin", "mouth", jm))
        for t in (2.6, 3.8, 5.0):
            for s in (1, -1):
                P.mark(add(H, apply(head_m, (t, s * 1.3, -1.7))), EEL_TOOTH)
                P.mark(add(hinge, apply(jm, (t - 0.6, s * 1.1, 0.35))), EEL_TOOTH)
    P.add(Part(add(hinge, apply(jm, (3.4, 0.0, -0.5))), (3.2, 1.9, 0.9), "eel_belly", "jaw", jm))
    skull_c, skull_r = add(H, apply(head_m, (1.0, 0.0, 0.3))), (3.8, 3.0, 2.7)
    for s in (1, -1):
        # An empty white eye in a dark socket (so it glows on the pale head), a cold halo over it; screwed shut when
        # struck, dull when dead.
        for du, dv in ((-15.0, 0.0), (15.0, 0.0), (0.0, 16.0), (0.0, -16.0), (-12.0, 13.0), (12.0, -13.0)):
            P.mark(_on(skull_c, skull_r, head_m, s * (62.0 + du), 18.0 + dv), MATS["eel"][0])
        if eye in ("open", "wide"):
            P.mark(_on(skull_c, skull_r, head_m, s * 62.0, 18.0), HOLLOW_EYE)
            P.mark(_on(skull_c, skull_r, head_m, s * 60.0, 40.0), EYE_HALO)
            if eye == "wide":
                P.mark(_on(skull_c, skull_r, head_m, s * 52.0, 20.0), HOLLOW_EYE)
        elif eye == "dead":
            P.mark(_on(skull_c, skull_r, head_m, s * 62.0, 18.0), MATS["eel"][2])
        for d in (6, 9, 12):   # gill slits behind the head
            k = max(0, n - 1 - d)
            P.mark(_on(spine[k], (radius(k / (n - 1)),) * 3, IDENT, s * 80.0, 5.0), MATS["eel"][1])
    # Grey strands rising off its back and the loop behind, curling back as they rise.
    stir = _pick({"idle": (0.0, 0.5, 0.0, -0.5), "walk": (0.0, 0.7, 0.0, -0.7)}, action, f, 0.6)
    roots = []
    for k in ((int(n * 0.3),) if action in ("attack", "death") else (int(n * 0.4), int(n * 0.62))):
        ta, tc = tangent(k)
        r = radius(k / (n - 1))
        roots.append((spine[k][0] - tc * r, spine[k][1], spine[k][2] + ta * r))
    roots.append((hump[8][0], hump[8][1], hump[8][2] + 2.6))
    for i, b0 in enumerate(roots):
        if b0[2] < wz:
            continue
        s = 1.0 if i % 2 else -1.0
        rise = (1.0, 0.8, 0.7)[i] * (0.45 if action in ("attack", "death") else 1.0)   # the lunge sweeps them back
        back = 1.0 if action in ("attack", "death") else 0.0
        wisp = _spline([b0, (b0[0] - 0.6 - back * 1.6, b0[1] + s * 0.4 + stir * 0.3, b0[2] + 2.8 * rise),
                        (b0[0] - 1.8 - back * 3.4, b0[1] - s * 0.5 - stir * 0.3, b0[2] + 5.6 * rise),
                        (b0[0] - 1.6 - back * 5.2, b0[1] + s * 0.3 + stir * 0.5, b0[2] + 8.4 * rise),
                        (b0[0] + 0.2 - back * 6.4, b0[1] + s * 0.9 + stir * 0.6, b0[2] + 9.6 * rise),
                        (b0[0] + 1.4 - back * 6.8, b0[1] + s * 1.2 + stir * 0.6, b0[2] + 8.6 * rise)], 16)
        for k, q in enumerate(wisp):
            P.add(Part(q, (0.5 - 0.18 * k / 15.0,) * 3, "h_stripe", "strand%d" % i))
    # The water round it: the Hollow's dark stain, foam where the body and the loop break the surface, the rings
    # spreading from it (a step each frame) and, gliding, a wake behind the loop.
    k0 = next((k for k, q in enumerate(spine) if q[2] >= wz), 0)
    base_a, base_r = spine[k0][0], radius(k0 / (n - 1))
    ring = _pick({"idle": (7.4, 8.4, 9.4, 10.4), "walk": (7.8, 8.8, 9.8, 10.8), "death": (7.4, 8.6, 9.8, 11.0)}, action, f, 8.4)
    breaks = [q for q in (hump[0], hump[-1]) if sink < 30]
    wake = action == "walk"

    def along(a, b):
        """How far (a, b) lies from the loop's line on the water."""
        (a0, b0), (a1, b1) = (loop[0][0] + roll, loop[0][1]), (loop[-1][0] + roll, loop[-1][1])
        da, db = a1 - a0, b1 - b0
        u = max(0.0, min(1.0, ((a - a0) * da + (b - b0) * db) / (da * da + db * db)))
        return math.hypot(a - a0 - da * u, b - b0 - db * u)

    def water(a, b):
        d0 = math.hypot(a - base_a, b)
        dh = min((math.hypot(a - q[0], b - q[1]) for q in breaks), default=99.0)
        if d0 < base_r + 1.1 and sink < 60:
            ang = int((math.degrees(math.atan2(b, a - base_a)) + 360.0) // 30.0)
            return FOAM if h01(ang, f, 17) > 0.25 else POOL
        if dh < 2.6:
            return FOAM
        if abs(d0 - ring) < 0.5 and d0 > base_r + 3.0:
            return RIPPLE
        if abs(d0 - ring + 3.8) < 0.45 and d0 > base_r + 3.0:
            return RIPPLE_DIM
        if wake and -14.0 + roll > a > -19.5:
            w = (-14.0 + roll - a) * 0.5 + 0.8
            if abs(abs(b - 10.0) - w) < 0.45:
                return RIPPLE_DIM
        if d0 < base_r + 3.2 or dh < 4.2 or (along(a, b) < 3.3 and sink < 30):
            return POOL
        return None

    P.water_fx = water
    return P


# The stripes' band (and the puppet's sash, the frog's flank stripe, the otter's pale throat) is measured in the
# creature's own frame; `render` passes world hit points, so the pattern needs the current facing to turn them back.
# `_frame` holds it while a sprite renders.
_frame = {"left": (0.0, -1.0), "fwd": (1.0, 0.0)}


def _local_b(hit) -> float:
    lx, ly = _frame["left"]
    return hit[0] * lx + hit[1] * ly


BUILD = {"mudshell_crab": crab, "reedtail_rat": rat, "wild_boarlet": boarlet, "trial_puppet": puppet, "reed_frog": frog,
         "marsh_leech": leech, "reed_otter": otter, "hollowed_boarlet": lambda action, f: boarlet(action, f, True),
         "old_snapper": snapper, "mossback_toad": toad, "hollow_minnow": minnow, "hollowed_eel": eel}
SHADOW = {"mudshell_crab": [10, 3], "reedtail_rat": [8, 2], "wild_boarlet": [11, 3], "trial_puppet": [8, 3],
          "reed_frog": [9, 3], "marsh_leech": [11, 3], "reed_otter": [11, 3], "hollowed_boarlet": [11, 3],
          "old_snapper": [17, 4], "mossback_toad": [10, 3], "hollow_minnow": [4, 2], "hollowed_eel": [9, 3]}
# Sizes against the 38 px body (the plan's §1.4): the crab and the rat small, about 24 and 30 px with its tail; the
# boarlet medium, about 28 px long; the frog small, the leech and the otter medium (the otter about 30 px with its
# tail); the Trial Puppet a sparring figure a little shorter than a disciple, about 34 px. Old Snapper is the big one,
# about 44 px from its tail to its beak and 32 across; the mossback toad about 22 px, the minnow about 18 with its
# wake, and the eel rises about 40 px out of the river (drawn at 1: its spine is laid out in art px).
SIZE = {"reedtail_rat": 1.1, "wild_boarlet": 1.25, "hollowed_boarlet": 1.25, "trial_puppet": 1.2, "reed_frog": 1.1,
        "marsh_leech": 1.2, "reed_otter": 1.2, "old_snapper": 1.2, "mossback_toad": 1.3, "hollow_minnow": 1.35}


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
    _frame["fwd"] = (math.cos(math.radians(yaw)), math.sin(math.radians(yaw)))
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
                   "note": "the top-down foes in eight facings (five drawn, three mirrored), built by tools/art/topdown/creatures.py"}
