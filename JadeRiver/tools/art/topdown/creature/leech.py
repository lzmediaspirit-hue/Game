"""The marsh leech (decision 44: redrawn as a leech). A flattened, segmented body, broadest in its hind third and
tapering to a narrow head: dark olive down the back going to black on the flanks, a groove round it every ring, a
paler khaki belly banded ring by ring, and a wet sheen that catches the §14 sun on every ring, broken by the grooves.
At the front a sucker mouth: a fleshy lip ring round a dark maw set with tiny teeth, closed to a pucker as it creeps
and flared into a cup when it feeds. At the back a smaller sucker, a disc it plants on the ground. A pair of pale
eyespots on the head; an elite has three pairs of gold glow spots down its back.

It moves as a leech does. On land it loops like an inchworm: the rear sucker holds while the front stretches out long
and thin and plants its mouth, then the rear lets go and is drawn up behind it, the middle rising in a high loop; in
water (`swim`) it flattens into a ribbon and swims with a wave running down it. Idle, it holds by its rear sucker,
lifts its head and quests from side to side. Its tell: it rears its front half up in an S, winding sideways as well so
it reads from every side, and flares its mouth wide on its teeth, facing its prey. It lunges mouth first and latches
(the hit), swells as it drinks, then lets go and draws back; struck, it balls up short and thick; beaten, it writhes,
curls up and goes limp and flat.

`view` is the facing's turn on the ground (creatures.ANGLE): the reared head turns toward the camera in the side
facings so the cup of its mouth shows; facing the camera its reared front stands up in a column; head-on or tail-on its
S winds wider and its loop leans a little to one side, so both show.
"""
from __future__ import annotations

import math

import numpy as np

from . import mats as M
from .motion import pick, smooth
from .sculpt import E, Pose, v3

REST = 19.0          # its length at rest, rear sucker to lip (art px at size 1)
RING = 2.0           # a ring's length along it
SHEEN = (0.9, 0.97)  # N.H thresholds: the sheen and the glint on each ring (sculpt.Part.sheen)

# The body's half-width along it, tail (0) to head (1); its half-depth is DEPTH of that (a leech is flat).
WIDTH = ((0.0, 1.05), (0.1, 1.9), (0.3, 2.55), (0.55, 2.35), (0.78, 1.7), (0.92, 1.2), (1.0, 0.95))
DEPTH = 0.56

# Per-frame spacing (motion.py's catalogue).
# The tell: how high the front half rears (0..1), the lateral wind of its S, the mouth's flare.
REAR = {"windup": (0.25, 0.6, 0.9, 1.0), "attack": (0.35, 0.0, 0.0, 0.0, 0.1, 0.1), "hurt": (0.3, 0.1, 0.0),
        "death": (0.5, 0.15, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0)}
GAPE = {"idle": (0.05, 0.1, 0.2, 0.1, 0.05, 0.0), "windup": (0.35, 0.65, 0.95, 1.0), "attack": (1.0, 0.75, 0.7, 0.7, 0.5, 0.15),
        "hurt": (0.0, 0.2, 0.1), "death": (0.8, 0.3, 0.6, 0.2, 0.1, 0.0, 0.0, 0.0)}
# Where the rear sucker (R) and the lip (F) are along the ground, and how far the rear is drawn back.
LUNGE = {"windup": (-0.4, -0.9, -1.3, -1.5), "attack": (5.0, 6.2, 6.0, 5.4, 3.6, 1.2), "hurt": (-2.2, -1.4, -0.5),
         "death": (-0.6, -0.8, -0.8, -0.8, -0.8, -0.8, -0.8, -0.8)}
# The body's length against REST (the rest arched into a loop where the ends are nearer than it is long).
LENGTH = {"windup": (0.97, 0.94, 0.92, 0.92), "attack": (1.18, 0.9, 0.94, 0.9, 0.96, 1.0), "hurt": (0.62, 0.78, 0.92),
          "death": (1.05, 0.9, 1.0, 0.95, 0.92, 0.9, 0.9, 0.9)}
# The ends' span against the length: below 1 the middle rises in a loop.
SPAN = {"attack": (1.0, 0.86, 0.9, 0.84, 0.94, 1.0), "hurt": (1.0, 1.0, 1.0)}
# Swelling as it drinks (the hind two thirds), and its writhing and curling up in death.
DRINK = {"attack": (0.0, 0.1, 0.22, 0.3, 0.2, 0.08)}
WRITHE = {"death": (1.0, -1.0, 0.8, -0.6, 0.3, 0.0, 0.0, 0.0), "hurt": (0.5, -0.3, 0.0)}
CURL = {"death": (0.0, 0.2, 0.45, 0.8, 1.0, 0.95, 0.85, 0.8)}
FLAT = {"death": (0.0, 0.0, 0.0, 0.1, 0.25, 0.4, 0.5, 0.55)}


def _width(u: float) -> float:
    for (u0, w0), (u1, w1) in zip(WIDTH, WIDTH[1:]):
        if u <= u1:
            t = (u - u0) / (u1 - u0)
            return w0 + (w1 - w0) * (t * t * (3 - 2 * t))
    return WIDTH[-1][1]


def _resample(pts: np.ndarray, n: int) -> tuple:
    """Points along the polyline `pts` at n even steps of its length, and the length."""
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    total = float(cum[-1])
    out = []
    for s in np.linspace(0.0, total, n):
        k = min(len(seg) - 1, int(np.searchsorted(cum, s, side="right") - 1))
        t = (s - cum[k]) / max(1e-9, seg[k])
        out.append(pts[k] + (pts[k + 1] - pts[k]) * t)
    return np.array(out), total


def _walk_ends(f: int) -> tuple:
    """The inchworm's ends over the walk (the sheet's origin travels on at the walk's rate, so a planted sucker slides
    back at it): the rear holds while the front reaches out and plants, then the front holds while the rear is drawn
    up. One cycle carries it 8 art px (creatures.REGISTRY's cycle)."""
    t = f / 8.0
    half, lc = 4.0, 9.6                 # a planted end slides back 4 a half cycle; the ends 9.6 apart drawn up
    if t < 0.5:
        u = t / 0.5
        rear = -lc / 2 - half * u
        front = lc / 2 + half * smooth(u)
        lift_f, lift_r = math.sin(u * math.pi) * 0.9, 0.0
    else:
        u = (t - 0.5) / 0.5
        front = lc / 2 + half - half * u
        rear = -lc / 2 - half + half * smooth(u)
        lift_f, lift_r = 0.0, math.sin(u * math.pi) * 0.7
    return rear, front, lift_r, lift_f


def leech(action: str, f: int, view: float = 90.0) -> Pose:
    P = Pose()
    rear_up = pick(REAR, action, f)
    gape = pick(GAPE, action, f)
    lunge = pick(LUNGE, action, f)
    length = pick(LENGTH, action, f, 1.0)
    span = pick(SPAN, action, f, 1.0)
    drink = pick(DRINK, action, f)
    writhe = pick(WRITHE, action, f)
    curl = pick(CURL, action, f)
    flat = pick(FLAT, action, f)
    swim = action == "swim"
    # Where the camera is in its own frame (a forward, b left): its reared head turns a little toward it.
    y = math.radians(view)
    cam_b = -math.cos(y)
    headon = abs(math.sin(y))          # 1 facing the camera or away from it, where a sideways wind is what reads
    fronton = max(0.0, math.sin(y))    # 1 facing the camera: its reared front stands up in a column, the cup toward it
    ph = f / 8.0 * math.tau

    # --- the spine: a polyline tail (index 0) to lip, laid out per action, then resampled evenly along its length.
    K = 48
    u = np.linspace(0.0, 1.0, K)
    arc = REST * length
    lift_r = lift_f = 0.0
    if action == "walk":
        rear, front, lift_r, lift_f = _walk_ends(f)
        d = front - rear
        arc = max(d + 0.4, 16.4 + (d - 9.6) / 8.0 * 4.0)     # it lengthens as it stretches (16.4 drawn up, 20.4 out)
    elif swim:
        rear, front = -arc * 0.5, arc * 0.5
        d = arc * 0.94
    else:
        d = arc * span
        rear, front = -d * 0.5 + lunge * 0.35, d * 0.5 + lunge
        d = front - rear
        arc = max(arc, d)
    a = rear + (front - rear) * u
    b = np.zeros(K)
    c = np.zeros(K)
    # The loop: where the ends are nearer than the body is long, its middle rises in a loop the body's length, its two
    # ends flat on the ground by the suckers.
    if arc > d + 0.05:
        bump = np.sin(np.pi * np.clip((u - 0.1) / 0.8, 0.0, 1.0)) ** 2
        lo, hi = 0.0, arc
        for _ in range(24):
            h = 0.5 * (lo + hi)
            pl = np.stack([a, b, c + h * bump], axis=1)
            if float(np.linalg.norm(np.diff(pl, axis=0), axis=1).sum()) > arc:
                hi = h
            else:
                lo = h
        c += lo * bump
        b += 0.5 * headon * lo * bump          # the loop leans a little to its side, so it shows from the front or behind
    c += lift_r * np.clip(1.0 - u / 0.2, 0.0, 1.0) + lift_f * np.clip((u - 0.8) / 0.2, 0.0, 1.0)
    if action == "idle":
        # Holding by its rear sucker, head lifted and questing side to side; a slow swell runs down it as it breathes.
        quest = (0.0, 0.6, 1.0, 0.4, -0.6, -1.0)[f]
        fr = np.clip((u - 0.62) / 0.38, 0.0, 1.0) ** 2
        c += fr * (0.9 + 0.4 * abs(quest))
        b += fr * 2.8 * quest
    if swim:
        # A ribbon in the water: a wave running tailward, mostly up and down (a leech swims so) and a little sideways.
        wave = np.sin(2 * math.pi * 1.1 * u + ph)
        c += 0.6 + 0.9 * wave * (0.35 + 0.65 * (1 - u))
        b += 1.2 * np.sin(2 * math.pi * 0.9 * u + ph + 1.2) * (0.3 + 0.7 * (1 - u))
    if rear_up > 0.0:
        # The S: the hind half stays on the ground, the front half rises (up, then its head bent forward over its prey),
        # and it winds sideways too, one way low and the other high, so the S reads from every side.
        v = np.clip((u - 0.38) / 0.62, 0.0, 1.0)
        # Its heading up from the ground: rising to upright by the middle of the front half, then bending forward over
        # its prey, level in the side views and still steep facing the camera, so the column shows.
        end = math.radians(58.0) * fronton
        th = rear_up * np.where(v < 0.45, math.radians(90.0) * np.sin(0.5 * np.pi * v / 0.45),
                                math.radians(90.0) + (end - math.radians(90.0)) * (v - 0.45) / 0.55)
        # Integrate the front part's heading in the (a, c) plane from where it leaves the ground.
        k0 = int(np.searchsorted(u, 0.38))
        for k in range(max(1, k0), K):
            ds = (u[k] - u[k - 1]) * arc
            a[k] = a[k - 1] + math.cos(th[k]) * ds
            c[k] = c[k - 1] + math.sin(th[k]) * ds
        side = 1.0 if cam_b >= 0 else -1.0
        wind = 1.0 + 0.7 * headon
        b += rear_up * wind * (-2.6 * np.sin(np.pi * np.clip(u / 0.5, 0, 1)) + 3.0 * side * np.sin(np.pi * v) * (0.4 + 0.6 * v))
    if writhe:
        b += writhe * 2.6 * np.sin(u * math.pi * 1.7 + f * 0.9)
    if curl:
        # Curling up on its side: the front bends round toward the tail (a C, then nearly a ring).
        ang = curl * math.radians(250.0) * u ** 1.2
        hd = np.zeros((K, 2))
        for k in range(1, K):
            ds = (u[k] - u[k - 1]) * arc
            hd[k] = hd[k - 1] + ds * np.array((math.cos(ang[k]), math.sin(ang[k])))
        hd -= hd.mean(axis=0)
        a = a * (1 - curl) + (hd[:, 0] + lunge) * curl
        b = b * (1 - curl) + hd[:, 1] * curl
    pts, total = _resample(np.stack([a, b, c], axis=1), 34)

    # --- the body: flattened ellipsoids along it, overlapping into one form; rings, flank and belly painted by the
    # length along it, so they stay on it as it loops and rears.
    thick = math.sqrt(REST / max(8.0, total)) * (1.0 + 0.12 * math.sin(ph) * (action == "idle"))
    depth = DEPTH * (1.0 - 0.45 * flat) * (0.72 if swim else 1.0)
    wide = 1.0 + 0.3 * flat + (0.12 if swim else 0.0)
    n = len(pts)
    T = np.gradient(pts, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    up = np.array((0.0, 0.0, 1.0))
    prevB = np.array((0.0, 1.0, 0.0))
    frames = []
    for k in range(n):
        B = np.cross(up, T[k])
        if np.linalg.norm(B) < 0.2:
            B = prevB
        B /= np.linalg.norm(B)
        prevB = B
        N = np.cross(T[k], B)
        frames.append((T[k], B, N))
    for k in range(n):
        s = k / (n - 1)
        w = _width(s) * thick * wide * (1.0 + drink * (1.0 - s) * 1.1 * (s > 0.15))
        hh = max(0.55, w * depth * (1.0 + drink * 0.6 * (1.0 - s)))
        Tk, Bk, Nk = frames[k]
        # The body lies on the ground: its underside at the spine's height, not under the ground.
        centre = pts[k] + np.array((0.0, 0.0, hh))
        m = np.stack([Tk, Bk, Nk], axis=1)
        sk = s * total
        P.add(E(centre, (max(0.62 * total / (n - 1) + 0.35, 0.7), w, hh), "leech", "body", m,
                _skin(centre, Tk, Bk, Nk, w, sk), sheen=SHEEN))
        # Paired spots down its back, three pairs (drawn on an elite only, in gold: its glow spots).
        if 0.2 < s < 0.8 and k % 6 == 3 and not swim:
            for sd in (1, -1):
                P.eye(centre + Bk * (sd * w * 0.42) + Nk * (hh + 0.25), None)
    # --- the rear sucker: a small disc under its tail, planted.
    T0, B0, N0 = frames[0]
    tail = pts[0] + np.array((0.0, 0.0, 0.45)) - T0 * 1.0
    disc_m = np.stack([T0, B0, N0], axis=1) if swim else np.eye(3)
    P.add(E(tail, (1.7 * thick, 1.7 * thick, 0.45), "leech_dark", "sucker", disc_m, _disc(tail, 1.7 * thick), sheen=SHEEN))
    # --- the head: eyespots on its crown, and the sucker mouth.
    Tn, Bn, Nn = frames[-1]
    wn = _width(1.0) * thick
    headc = pts[-1] + np.array((0.0, 0.0, max(0.55, wn * depth)))
    for sd in (1, -1):
        P.eye(pts[-3] + np.array((0.0, 0.0, max(0.55, _width(0.94) * thick * depth))) + Bn * sd * 0.55 + Nn * 0.45, M.LEECH_EYE)
    # The cup faces along the head, a little up at its prey in the tell and turned toward the camera in the side views.
    face = Tn + np.array((0.0, 0.0, 0.2 * rear_up))
    if rear_up > 0.3:
        face = face + np.array((0.0, cam_b, 0.0)) * 0.8 * rear_up
    face /= np.linalg.norm(face)
    fb = np.cross(np.array((0.0, 0.0, 1.0)), face)
    fb = fb / np.linalg.norm(fb) if np.linalg.norm(fb) > 0.2 else Bn
    fn = np.cross(face, fb)
    cm = np.stack([face, fb, fn], axis=1)
    R = 1.2 + 1.6 * gape
    lip = headc + face * (0.45 + 0.35 * gape)
    P.add(E(lip, (0.5 + 0.2 * gape, R, R * 0.92), "leech_lip", "mouth", cm))
    if gape > 0.25:
        maw = lip + face * (0.45 + 0.2 * gape)
        P.add(E(maw, (0.25, R * 0.64, R * 0.58), "leech_maw", "maw", cm, line=False))
        # Tiny teeth round the rim of the maw, muted so the cup reads as a mouth and not an eye.
        for i in range(6 if gape > 0.6 else 3):
            q = math.radians(90.0 + i * (60.0 if gape > 0.6 else 120.0))
            P.mark(maw + face * 0.2 + fb * math.cos(q) * R * 0.5 + fn * math.sin(q) * R * 0.46, M.LEECH_TOOTH)
    else:
        P.mark(lip + face * 0.55, M.RAMPS["leech_maw"][1])
    # The bite's glints as it latches, and the water a swimmer stirs.
    if action == "attack" and f in (1, 2):
        for dd in ((1.6, 0.6, 0.8), (1.9, -0.7, 1.4), (2.2, 0.2, 2.0)):
            P.glow.append((lip + v3(*dd), M.GLINT))
    if swim:
        for k in range(6):
            s = k / 5.0
            at = pts[int(s * (n - 1))]
            wv = math.sin(ph + k * 1.3)
            for sd in (1, -1):
                P.fx.append((at + v3(0.0, sd * (2.9 + 0.5 * wv + 0.6 * (1 - s)), 0.05), M.SPLASH if (k + f) % 3 else M.SPLASH_DIM))
        for k in range(3):
            P.fx.append((pts[0] + v3(-1.8 - k * 1.2, (k - 1) * 1.1 + 0.4 * math.sin(ph + k), 0.05), M.SPLASH_DIM))
    return P


def _disc(centre, r: float):
    """The rear sucker: its rim a step lit round a darker middle, so it reads as a disc."""
    def disc(q, nrm):
        rim = np.linalg.norm((q - centre)[:, :2], axis=1) > r * 0.62
        return np.full(len(q), "leech_dark", dtype=object), np.where(rim, 1, -1).astype(np.int16)
    return disc


def _skin(centre, T, B, N, w: float, s0: float):
    """A ring of the body's paint: the length along it `s0` at `centre`. A groove a step dark every RING (two on its
    back, where it cuts the sheen) with a lit ridge behind it; the back dark olive, the flanks going to black; the belly
    paler and banded by the same grooves."""
    def skin(q, nrm):
        d = q - centre
        s = s0 + d @ T
        lat = np.abs(d @ B) / max(0.3, w)
        nz = nrm @ N
        ph = (s / RING) % 1.0
        groove = ph < 0.3
        ridge = (ph >= 0.3) & (ph < 0.6) & (nz > 0.55)
        belly = nz < -0.28
        flank = (lat > 0.6) | (nz < 0.25)
        names = np.where(belly, "leech_belly", np.where(flank, "leech_dark", "leech")).astype(object)
        # The groove cuts through the sheen on its back, so the glint breaks ring by ring.
        bias = np.where(groove, np.where(nz > 0.6, -2, -1), np.where(ridge & ~belly, 1, 0)).astype(np.int16)
        return names, bias
    return skin
