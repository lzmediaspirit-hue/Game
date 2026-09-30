"""Timing and spacing for the foes' actions (decision 43: more frames, and the principles of animation).

Every species draws the same catalogue, frame for frame:

  idle    6  loops    a breath, a look about, a twitch of the ears or claws
  walk    8  loops    its gait (a trot, a scuttle, a hop, a creep, a swim), the body bobbing on it
  windup  4  holds    the tell: an anticipation pose of its own, distinct per species, reached on the last frame and held
                      until the blow
  attack  6  holds    the blow: 0 the launch (stretched), 1 the hit (HIT_FRAME: squashed on the impact), 2 the impact
                      held, 3 and 4 the follow-through, 5 settling back
  hurt    3  holds    the flinch (squashed, knocked back), the recoil, the recovery
  death   8  holds    a fall that suits it, or a coming apart into motes

A species' pose function takes (action, frame) and reads its per-frame values from tables (`pick`), so the spacing of
each action is written out: slow in and out on the holds, a snap on the launch, overshoot and settle after.
"""
from __future__ import annotations

import math

FRAMES = {"idle": 6, "walk": 8, "windup": 4, "attack": 6, "hurt": 3, "death": 8}
HIT_FRAME = 1
TAU = math.tau


def pick(table: dict, action: str, f: int, default=0.0):
    """A per-frame value of an action from `table` (action: one value per frame), else `default`."""
    if action not in table:
        return default
    row = table[action]
    return row[min(f, len(row) - 1)]


def phase(action: str, f: int) -> float:
    """Where a looping action is in its cycle, 0..1."""
    return f / FRAMES[action]


def wave(action: str, f: int, off: float = 0.0) -> float:
    """sin over a looping action's cycle, `off` of a cycle later."""
    return math.sin((f / FRAMES[action] + off) * TAU)


def gait(action: str, f: int, off: float, lift: float, stride: float) -> tuple:
    """A leg on a walk cycle (`off` its share of a cycle behind the first): (lift, stride along the way it goes). The
    foot lifts and swings forward over the first half, and pushes back on the ground over the second."""
    if action != "walk":
        return 0.0, 0.0
    t = (f / FRAMES["walk"] + off) % 1.0
    if t < 0.5:
        u = t / 0.5
        return math.sin(u * math.pi) * lift, -stride + 2.0 * stride * (u * u * (3 - 2 * u))
    u = (t - 0.5) / 0.5
    return 0.0, stride - 2.0 * stride * u


def smooth(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def headon(view: float) -> tuple:
    """How far a facing (its turn on the ground, creatures.ANGLE: east 0, south 90) is head-on to the camera (`front`,
    1 in the S row) or tail-on (`back`, 1 in the N row), 0 in the SE, E and NE rows (decision 44). A beast seen so is
    posed to read as itself: facing the camera its face held up, forelegs apart, ears and shoulders framing its head;
    walking away its rump, tail and hind legs spread, its ears over its back."""
    s = math.sin(math.radians(view))
    return smooth((s - 0.8) / 0.15), smooth((-s - 0.8) / 0.15)


def h01v(x, y, s: int = 0):
    """h01 over arrays of integers (floats floored)."""
    import numpy as np
    n = (np.asarray(x).astype(np.int64) * 374761393 + np.asarray(y).astype(np.int64) * 668265263 + s * 2246822519) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65536.0


def h01(x: int, y: int, s: int = 0) -> float:
    """A hash of integers to [0, 1) (canvas.h01's)."""
    n = (x * 374761393 + y * 668265263 + s * 2246822519) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65536.0
