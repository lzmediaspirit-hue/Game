"""Draw the v1.1 weapon families (S47) and the v1.2 Act III families for every registered avatar action,
pose-registered to the hand:

- heavy sabre (dao): the jian's own frames, blade broadened by one art pixel and reforged in dark steel, with a
  bronze guard, so every swing keeps its arc and smear;
- folding fan: redrawn along the short blade's grip and axis in every frame, open in the strikes (a ribbed paper
  wedge) and folded while carried;
- jade flute: a bamboo-jointed tube along the same grip, longer than the blade, with a red tassel;
- calligraphy brush (v1.2 Phase D): a jointed bamboo shaft along the short blade's grip, a lacquered collar and a
  tapered ink-black tip; in the strikes the tip drags a short curved ink stroke along the swing's arc, drying out
  at its far end;
- warden's hand-bell (v1.2 Phase D): a bronze bell on a short dark-wood handle in the fist, mouth pointing along
  the blade axis, a clapper in the mouth and a red cord at the handle end; in the strikes pale-gold sound lines
  ring off the mouth.

The grip of each source frame comes from its colours: the gold guard, the brown or dark hilt and the jade blade.
Art is drawn at native pixel scale 2 (one art pixel = 2x2 screen pixels) and registered in data/parts.json under
weapon "sabre", "fan", "flute", "brush" and "bell", mirroring the source weapon's layers, z and hidden poses.
Deterministic. Run from JadeRiver/: python3 tools/art/bake_weapons.py
"""
import json
import math
import os

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ART = os.path.join(ROOT, "art")

# The source art's palette (jade blade ramp, gold guard, hilt browns and outlines).
BLADE = [(39, 56, 65), (70, 112, 117), (91, 166, 155), (160, 211, 193), (232, 242, 220)]
GOLD = [(209, 166, 77)]
HILT = [(43, 28, 29), (65, 30, 5), (29, 19, 30)]

# Dark steel for the sabre (outline, shadow, body, light, edge gleam) and a bronze guard.
STEEL = {(39, 56, 65): (28, 30, 36), (70, 112, 117): (78, 84, 94), (91, 166, 155): (128, 136, 146),
         (160, 211, 193): (186, 192, 198), (232, 242, 220): (236, 238, 240)}
BRONZE = (176, 112, 58)
OUTLINE = (24, 18, 22, 255)

FAN_PAPER = [(242, 232, 204, 255), (222, 208, 172, 255), (196, 178, 140, 255)]
FAN_RIB = (92, 58, 34, 255)
FAN_INK = (44, 110, 104, 255)
FLUTE = [(62, 96, 58, 255), (104, 150, 88, 255), (150, 196, 120, 255)]
FLUTE_NODE = (48, 70, 40, 255)
TASSEL = (176, 40, 44, 255)

# The calligraphy brush: warm bamboo (light, base, shadow, joint), a lacquered collar, ink-soaked hair and its stroke.
BAMBOO = [(226, 194, 132, 255), (196, 158, 96, 255), (148, 110, 62, 255), (118, 84, 46, 255)]
LACQUER = [(122, 46, 52, 255), (66, 24, 30, 255)]
HAIR = [(88, 90, 104, 255), (34, 34, 44, 255)]
INK = [(16, 14, 20, 255), (58, 54, 62, 255)]

# The warden's hand-bell: bronze (highlight, body, shadow, rim), dark wood (light, base), the cord and its ring.
BELL = [(242, 210, 126, 255), (198, 142, 66, 255), (136, 86, 44, 255), (74, 46, 30, 255)]
WOOD = [(110, 74, 46, 255), (64, 40, 28, 255)]
CORD = (184, 42, 46, 255)
CHIME = (234, 196, 104, 255)


def to_art(img):
    """Sample one art pixel from each 2x2 block."""
    a = np.array(img)
    return a[::2, ::2].copy()


def to_screen(art):
    return Image.fromarray(np.repeat(np.repeat(art, 2, axis=0), 2, axis=1), "RGBA")


def mask_of(art, colours):
    m = np.zeros(art.shape[:2], bool)
    for c in colours:
        m |= (art[:, :, 0] == c[0]) & (art[:, :, 1] == c[1]) & (art[:, :, 2] == c[2]) & (art[:, :, 3] > 0)
    return m


# ------------------------------------------------------------------ the heavy sabre (from the jian's pixels)
def sabre_frame(art):
    """Broaden the blade by one art pixel on every side and reforge the colours; the hilt and guard stay put."""
    out = art.copy()
    blade = mask_of(art, BLADE)
    if not blade.any():
        return out
    grown = blade.copy()
    grown[1:, :] |= blade[:-1, :]
    grown[:-1, :] |= blade[1:, :]
    grown[:, 1:] |= blade[:, :-1]
    grown[:, :-1] |= blade[:, 1:]
    solid = art[:, :, 3] > 0
    new = grown & ~solid
    # New body pixels take the steel's mid tone; the old ones map through the steel ramp.
    for src, dst in STEEL.items():
        m = mask_of(art, [src])
        out[m, :3] = dst
    out[new] = (*STEEL[(91, 166, 155)], 255)
    # A dark rim around the broadened blade.
    body = grown | solid
    rim = np.zeros_like(body)
    rim[1:, :] |= body[:-1, :]
    rim[:-1, :] |= body[1:, :]
    rim[:, 1:] |= body[:, :-1]
    rim[:, :-1] |= body[:, 1:]
    rim &= ~body
    near_blade = np.zeros_like(body)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            near_blade |= np.roll(np.roll(grown, dy, 0), dx, 1)
    out[rim & near_blade] = (*STEEL[(39, 56, 65)], 255)
    out[mask_of(art, GOLD), :3] = BRONZE
    return out


# ------------------------------------------------------------------ the fan and flute (redrawn along the grip)
def grip_of(art):
    """(hand, tip) of the held weapon in art pixels, or None when too little of it shows."""
    blade = np.argwhere(mask_of(art, BLADE))
    guard = np.argwhere(mask_of(art, GOLD))
    hilt = np.argwhere(mask_of(art, HILT[:2]))
    if len(blade) + len(guard) < 3:
        return None
    g = guard.mean(0) if len(guard) else (hilt.mean(0) if len(hilt) else blade.mean(0))
    d = ((blade - g) ** 2).sum(1) if len(blade) else np.array([0.0])
    tip = blade[int(d.argmax())].astype(float) if len(blade) else g + np.array([0.0, 4.0])
    if len(hilt):
        dh = ((hilt - tip) ** 2).sum(1)
        hand = hilt[int(dh.argmax())].astype(float)
    else:
        hand = g - (tip - g) * 0.25
    if np.hypot(*(tip - hand)) < 2.0:
        return None
    return hand, tip


def _paint(art, pts, colour):
    h, w = art.shape[:2]
    for (y, x) in pts:
        if 0 <= y < h and 0 <= x < w:
            art[y, x] = colour


def _outline(art, solid):
    h, w = art.shape[:2]
    rim = np.zeros_like(solid)
    rim[1:, :] |= solid[:-1, :]
    rim[:-1, :] |= solid[1:, :]
    rim[:, 1:] |= solid[:, :-1]
    rim[:, :-1] |= solid[:, 1:]
    rim &= ~solid
    art[rim] = OUTLINE


def stroke(out, solid, start, end, half, colour_of):
    """Fill every art pixel within `half` of the segment start-end; colour_of(s, side) picks the colour from the
    distance along the segment (0..1) and the signed side (-1 upper .. 1 lower)."""
    h, w = out.shape[:2]
    d = end - start
    L2 = float((d ** 2).sum()) or 1.0
    n = np.array([-d[1], d[0]]) / math.sqrt(L2)
    y0, y1 = int(max(0, min(start[0], end[0]) - half - 2)), int(min(h, max(start[0], end[0]) + half + 3))
    x0, x1 = int(max(0, min(start[1], end[1]) - half - 2)), int(min(w, max(start[1], end[1]) + half + 3))
    for y in range(y0, y1):
        for x in range(x0, x1):
            p = np.array([y, x], float)
            t = float(np.clip(((p - start) * d).sum() / L2, 0.0, 1.0))
            q = start + d * t
            off = float(((p - q) * n).sum())
            if np.hypot(*(p - q)) <= half + 0.01:
                out[y, x] = colour_of(t, off / max(half, 0.5))
                solid[y, x] = True


def fan_frame(art, open_fan):
    """A folding fan pivoting in the hand, spread toward where the blade pointed."""
    g = grip_of(art)
    out = np.zeros_like(art)
    if g is None:
        return out
    hand, tip = g
    v = tip - hand
    length = np.hypot(*v)
    if not open_fan:
        # Folded: a slim paper-and-rib stick in the hand, its guards darker at the pivot.
        u = v / length
        solid = np.zeros(art.shape[:2], bool)
        end = hand + u * max(7.0, length)
        stroke(out, solid, hand - u * 0.5, end, 1.0,
               lambda t, side: FAN_RIB if t < 0.22 or t > 0.93 else (FAN_PAPER[0] if side < 0 else FAN_PAPER[2]))
        _outline(out, solid)
        hy, hx = int(round(hand[0])), int(round(hand[1]))
        _paint(out, [(hy, hx)], (209, 166, 77, 255))
        return out
    base = math.atan2(v[0], v[1])
    radius = max(5.0, length * 1.15)
    spread = math.radians(42 if open_fan else 6)
    h, w = art.shape[:2]
    solid = np.zeros((h, w), bool)
    y0, y1 = int(max(0, hand[0] - radius - 2)), int(min(h, hand[0] + radius + 3))
    x0, x1 = int(max(0, hand[1] - radius - 2)), int(min(w, hand[1] + radius + 3))
    for y in range(y0, y1):
        for x in range(x0, x1):
            dy, dx = y - hand[0], x - hand[1]
            r = math.hypot(dy, dx)
            if r > radius or r < 0.5:
                continue
            ang = math.atan2(dy, dx) - base
            ang = (ang + math.pi) % (2 * math.pi) - math.pi
            if abs(ang) > spread:
                continue
            solid[y, x] = True
            if not open_fan:
                out[y, x] = FAN_RIB if r < radius * 0.35 else FAN_PAPER[1 if (y + x) % 2 else 2]
                continue
            if r < radius * 0.38:
                out[y, x] = FAN_RIB            # the ribs gather into the handle
            else:
                t = (ang + spread) / (2 * spread)
                rib = abs((t * 6.0) - round(t * 6.0)) < 0.09
                shade = 0 if t < 0.45 else (1 if t < 0.8 else 2)
                c = FAN_PAPER[shade]
                if rib:
                    c = FAN_PAPER[2]
                if r > radius * 0.8 and 0.3 < t < 0.7:
                    c = FAN_INK                # a band of ink near the edge
                out[y, x] = c
    if solid.any():
        _outline(out, solid)
        hy, hx = int(round(hand[0])), int(round(hand[1]))
        _paint(out, [(hy, hx)], (209, 166, 77, 255))  # the brass rivet
    return out


def flute_frame(art):
    """A jade-green bamboo flute in the hand, a little longer than the blade, with a red tassel at the hand end."""
    g = grip_of(art)
    out = np.zeros_like(art)
    if g is None:
        return out
    hand, tip = g
    v = tip - hand
    length = np.hypot(*v)
    u = v / length
    n = np.array([-u[1], u[0]])
    start = hand - u * 1.5
    end = hand + u * max(6.0, length * 1.35)
    h, w = art.shape[:2]
    solid = np.zeros((h, w), bool)
    span = float(np.hypot(*(end - start)))

    def colour(t, side):
        if int(t * span) % 5 == 4:
            return FLUTE_NODE                  # a bamboo joint
        return FLUTE[2] if side < -0.2 else (FLUTE[1] if side < 0.5 else FLUTE[0])
    stroke(out, solid, start, end, 1.0, colour)
    # Finger holes: dark dots along the upper side, toward the far end.
    for f in (0.55, 0.68, 0.81):
        q = start + (end - start) * f
        _paint(out, [(int(round(q[0])), int(round(q[1])))], (30, 40, 26, 255))
    if solid.any():
        _outline(out, solid)
    # The tassel hangs from the hand end.
    ty, tx = int(round(start[0])), int(round(start[1]))
    _paint(out, [(ty + 1, tx), (ty + 2, tx), (ty + 3, tx), (ty + 3, tx - 1), (ty + 3, tx + 1)], TASSEL)
    return out


OPEN_ACTIONS = {"attack", "punch", "punch_1", "punch_2", "punch_3", "swing", "swing_1", "swing_2", "swing_3",
                "thrust_1", "thrust_2", "thrust_3", "bow"}


# ------------------------------------------------------------------ the brush and the bell (v1.2 Phase D)
def up_normal(u):
    """The unit normal of the axis u that points up (or, for a vertical axis, left) on screen, so that highlights
    sit on the upper-left side in both facings."""
    n = np.array([-u[1], u[0]])
    if n[0] > 0 or (n[0] == 0 and n[1] > 0):
        n = -n
    return n


def taper(out, solid, start, end, half_of, colour_of, step=0.35, flat_end=False):
    """Paint a stroke of varying width from start to end: at each sample along the axis every pixel within
    half_of(t) of it (and always the pixel under the sample) takes colour_of(a, side), a being the pixel's distance
    along the axis in art px and side its signed offset across it, upper-left positive, in halves. With flat_end
    the far end is cut square across the axis instead of rounded."""
    h, w = out.shape[:2]
    d = end - start
    span = float(np.hypot(*d)) or 1.0
    u = d / span
    n = up_normal(u)
    steps = max(1, int(math.ceil(span / step)))
    for i in range(steps + 1):
        t = min(1.0, i * step / span)
        q = start + d * t
        r = half_of(t)
        qy, qx = int(round(q[0])), int(round(q[1]))
        for y in range(int(math.floor(q[0] - r - 1)), int(math.ceil(q[0] + r + 1)) + 1):
            for x in range(int(math.floor(q[1] - r - 1)), int(math.ceil(q[1] + r + 1)) + 1):
                if not (0 <= y < h and 0 <= x < w):
                    continue
                dy, dx = y - q[0], x - q[1]
                if (y == qy and x == qx) or math.hypot(dy, dx) <= r + 0.01:
                    a = (y - start[0]) * u[0] + (x - start[1]) * u[1]
                    if flat_end and a > span + 0.3:
                        continue
                    side = (dy * n[0] + dx * n[1]) / max(r, 0.5)
                    out[y, x] = colour_of(a, side)
                    solid[y, x] = True


def _angle(hand, tip):
    return math.atan2(tip[0] - hand[0], tip[1] - hand[1])


def _wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def swing_of(hand, tip, g_prev):
    """How the held axis has moved since the previous frame: (turn, move) with turn the signed rotation about the
    hand in radians (clockwise positive on screen) and move the tip's translation in art px, both None on a
    first frame or when the previous frame shows no grip (nothing has been swept yet)."""
    if g_prev is None:
        return None, None
    return _wrap(_angle(hand, tip) - _angle(*g_prev)), tip - g_prev[1]


def ink_stroke(out, hand, tip, g_prev):
    """A short curved smear the brush tip leaves along the arc it swings on (centred on the hand), trailing behind
    the motion since the previous frame: black beside the tip, drying to a speckled edge at its end."""
    r = float(np.hypot(*(tip - hand)))
    a0 = _angle(hand, tip)
    turn, move = swing_of(hand, tip, g_prev)
    trail = 0
    if turn is not None and abs(turn) >= 0.3:                # a real swing, not grip-detection jitter
        trail = -1 if turn > 0 else 1
        theta = min(0.95, max(0.45, abs(turn) * 1.5))
    else:
        n = up_normal((tip - hand) / max(r, 1.0))
        across = float((move * n).sum()) if move is not None else 0.0
        theta = 0.45 if abs(across) >= 1.0 else 0.32         # a thrust or a still tip leaves only a dab
        best = None
        for s in (1, -1):
            a = a0 + s * 0.35
            p = hand + np.array([math.sin(a), math.cos(a)]) * r
            if abs(across) >= 1.0:
                score = -float(((p - tip) * n).sum()) * across   # behind the motion across the axis
            else:
                score = float(p[0])                          # a thrust or a still tip drips downward
            if best is None or score > best:
                best, trail = score, s
    gap = 2.2 / max(r, 1.0)                                  # two art pixels clear of the hair's point
    h, w = out.shape[:2]
    y0, y1 = int(max(0, hand[0] - r - 3)), int(min(h, hand[0] + r + 4))
    x0, x1 = int(max(0, hand[1] - r - 3)), int(min(w, hand[1] + r + 4))
    for y in range(y0, y1):
        for x in range(x0, x1):
            dy, dx = y - hand[0], x - hand[1]
            rp = math.hypot(dy, dx)
            da = _wrap(math.atan2(dy, dx) - a0) * trail
            if da < gap or da > gap + theta:
                continue
            s = (da - gap) / theta
            if abs(rp - (r + 0.5)) > (2.4 - 1.4 * s) * 0.5:
                continue
            if s > 0.6 and (y + x) % 2:
                continue                                     # the dry-brush edge breaks up
            out[y, x] = INK[1] if s > 0.8 else INK[0]


def brush_frame(art, action, prev=None, nxt=None):
    """A scholar's writing brush held like the short blade: a jointed bamboo shaft, a lacquered collar and an
    ink-black tapered tip. In the strike frames the tip drags an ink stroke along the swing's arc."""
    g = grip_of(art)
    out = np.zeros_like(art)
    if g is None:
        return out
    hand, tip = g
    v = tip - hand
    length = float(np.hypot(*v))
    u = v / length
    n = up_normal(u)
    shaft = max(5.0, length * 0.72)
    hair = max(3.5, length * 0.42)
    start = hand - u * 1.0
    s_end = hand + u * shaft
    c_end = s_end + u * 2.0
    h_end = c_end + u * hair
    h, w = art.shape[:2]
    solid = np.zeros((h, w), bool)
    if action in OPEN_ACTIONS:
        ink_stroke(out, hand, h_end, grip_of(prev) if prev is not None else None)

    def bamboo(a, side):
        if int(a) % 4 == 3:
            return BAMBOO[3]                                 # a joint
        return BAMBOO[0] if side > 0.2 else (BAMBOO[1] if side > -0.7 else BAMBOO[2])
    # The shaft is two art pixels wide: its axis sits half a pixel up the normal so its rows straddle the collar's.
    taper(out, solid, start + n * 0.5, s_end + n * 0.5, lambda t: 0.75, bamboo)
    taper(out, solid, s_end, c_end, lambda t: 1.0, lambda a, side: LACQUER[0] if side > 0.4 else LACQUER[1])
    hair_solid = np.zeros((h, w), bool)
    taper(out, hair_solid, c_end, h_end, lambda t: 1.1 - 0.9 * t,
          lambda a, side: HAIR[0] if (side > 0.45 and a < hair * 0.5) else HAIR[1])
    painted = out.copy()
    ys, xs = np.nonzero(hair_solid)
    along = (ys - c_end[0]) * u[0] + (xs - c_end[1]) * u[1]
    root = np.zeros_like(hair_solid)
    root[ys[along < hair * 0.55], xs[along < hair * 0.55]] = True
    _outline(out, solid | root)
    point = hair_solid & ~root                               # the point is not outlined, so it stays sharp
    out[point] = painted[point]
    _paint(out, [(int(round(h_end[0])), int(round(h_end[1])))], HAIR[1])
    return out


def chime(out, mouth, u):
    """Two or three short pale-gold sound lines ringing off the bell mouth along the axis u."""
    h, w = out.shape[:2]
    base = math.atan2(u[0], u[1])
    for r, span in ((2.5, 0.62), (4.5, 0.54), (6.5, 0.46)):
        y0, y1 = int(max(0, mouth[0] - r - 2)), int(min(h, mouth[0] + r + 3))
        x0, x1 = int(max(0, mouth[1] - r - 2)), int(min(w, mouth[1] + r + 3))
        for y in range(y0, y1):
            for x in range(x0, x1):
                if out[y, x, 3]:
                    continue
                dy, dx = y - mouth[0], x - mouth[1]
                if abs(math.hypot(dy, dx) - r) > 0.5 or abs(_wrap(math.atan2(dy, dx) - base)) > span:
                    continue
                out[y, x] = CHIME


def bell_frame(art, action, prev=None, nxt=None):
    """A bronze hand-bell on a short dark-wood handle in the fist, its mouth pointing along the blade axis, a
    clapper in the mouth and a red cord at the handle end. In the strike frames sound lines ring off the mouth."""
    g = grip_of(art)
    out = np.zeros_like(art)
    if g is None:
        return out
    hand, tip = g
    v = tip - hand
    length = float(np.hypot(*v))
    u = v / length
    n = up_normal(u)
    body = max(6.0, length * 0.7)
    start = hand - u * 1.0
    crown = hand + u * 3.0
    mouth = crown + u * body
    h, w = art.shape[:2]
    solid = np.zeros((h, w), bool)
    taper(out, solid, start + n * 0.5, crown + n * 0.5, lambda t: 0.75,
          lambda a, side: WOOD[0] if side > 0.2 else WOOD[1])

    def half(t):
        if t < 0.3:
            return 0.9 + 1.2 * math.sqrt(t / 0.3)            # the domed crown
        if t < 0.7:
            return 2.1 + 0.2 * (t - 0.3) / 0.4               # the waist
        return 2.3 + 1.3 * ((t - 0.7) / 0.3) ** 1.4          # the flared lip

    def bronze(a, side):
        if a > body - 1.0:
            return BELL[3]                                   # the dark rim of the open mouth
        if a > body - 2.0:
            return BELL[0] if side > 0.5 else (BELL[1] if side > -0.5 else BELL[2])   # the lip
        if 2.0 < a < 2.8 and side < 0.6:
            return BELL[3] if side < -0.3 else BELL[2]       # the ring under the crown
        return BELL[0] if side > 0.45 else (BELL[1] if side > -0.55 else BELL[2])
    taper(out, solid, crown, mouth, half, bronze, flat_end=True)
    for k in (0.6, 1.5):                                     # the clapper's tongue in the mouth
        cy, cx = int(round(mouth[0] + u[0] * k)), int(round(mouth[1] + u[1] * k))
        _paint(out, [(cy, cx)], WOOD[1])
        if 0 <= cy < h and 0 <= cx < w:
            solid[cy, cx] = True
    _outline(out, solid)
    ty, tx = int(round(start[0])), int(round(start[1]))
    _paint(out, [(ty + 1, tx), (ty + 2, tx - 1), (ty + 2, tx + 1), (ty + 3, tx)], CORD)   # the cord loop
    if action in OPEN_ACTIONS:
        chime(out, mouth, u)
    return out


def bake(parts, weapon_id, source_id, label, frame_fn, neighbours=False):
    """With neighbours, frame_fn(art, action, prev, nxt) also receives the frames before and after it in the
    row (None at the ends or when empty), so a stroke can trail the swing."""
    src_item = parts["weapon"][source_id]
    layers = []
    made = 0
    for li, layer in enumerate(src_item["layers"]):
        new_layer = {k: v for k, v in layer.items() if k != "animations"}
        new_layer["animations"] = {}
        for action, anim in layer["animations"].items():
            if anim.get("hidden") or not anim.get("sheets"):
                new_layer["animations"][action] = dict(anim)
                continue
            cell = int(anim.get("cell", 256))
            sheets = []
            for si, sheet_path in enumerate(anim["sheets"]):
                sheet = Image.open(os.path.join(ART, os.path.basename(sheet_path))).convert("RGBA")
                out = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
                for row in range(sheet.height // cell):
                    arts = []
                    for col in range(sheet.width // cell):
                        box = (col * cell, row * cell, (col + 1) * cell, (row + 1) * cell)
                        art = to_art(sheet.crop(box))
                        arts.append(art if (art[:, :, 3] > 0).any() else None)
                    for col, art in enumerate(arts):
                        if art is None:
                            continue
                        if neighbours:
                            new = frame_fn(art, action, arts[col - 1] if col > 0 else None,
                                           arts[col + 1] if col + 1 < len(arts) else None)
                        else:
                            new = frame_fn(art, action)
                        out.paste(to_screen(new), (col * cell, row * cell))
                base = os.path.basename(sheet_path).replace("weapon_%s_" % source_id, "weapon_%s_" % weapon_id)
                out.save(os.path.join(ART, base), optimize=True)
                sheets.append("art_v12/" + base)
                made += 1
            entry = dict(anim)
            entry["sheets"] = sheets
            entry["source"] = "generated:bake_weapons.py from " + source_id
            entry.pop("rig", None)
            new_layer["animations"][action] = entry
        layers.append(new_layer)
    parts["weapon"][weapon_id] = {"label": label, "layers": layers}
    parts["_attack_by_weapon"][weapon_id] = parts["_attack_by_weapon"].get(source_id, "attack")
    return made


def main():
    parts_path = os.path.join(ROOT, "data", "parts.json")
    parts = json.load(open(parts_path))
    n = bake(parts, "sabre", "sword", "Heavy sabre", lambda art, action: sabre_frame(art))
    n += bake(parts, "fan", "dagger", "Iron fan", lambda art, action: fan_frame(art, action in OPEN_ACTIONS))
    n += bake(parts, "flute", "dagger", "Jade flute", lambda art, action: flute_frame(art))
    n += bake(parts, "brush", "dagger", "Calligraphy brush", brush_frame, neighbours=True)
    n += bake(parts, "bell", "dagger", "Warden's hand-bell", bell_frame, neighbours=True)
    with open(parts_path, "w") as f:
        json.dump(parts, f, indent=2)
    print("WEAPONS:", n, "sheets")


if __name__ == "__main__":
    main()
