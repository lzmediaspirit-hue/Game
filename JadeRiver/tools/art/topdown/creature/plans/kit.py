"""What every body plan shares (audit 45 §6.2, the monster engine): a species' resolved body (`Body`: its plan's variant
with the spec's parts, materials and motion merged over it), the per-frame lookups the pose functions make, colours by
name, and the falls most plans end with.

A plan's motion is a set of named styles, one an action. A style is a dict: its per-frame tables (a tuple a channel,
one value a frame: `lunge`, `pitch`, `head`, `yaw`, `gape`, `squash`, `roll`, `tail`, ... read with `Body.pick`, as the
hand modules read their LUNGE, PITCH, ... tables with motion.pick) and its scalars (a loop's amplitudes and phases, read
with `Body.style`). `kind` names the formula a loop style runs (a walk's `bound`, `lope` or `trot`). A spec names a style
an action (`motion={"windup": "rear"}`), or a style and its overrides (`("rear", {"pitch": (8, 18, 30, 40)})`).

Nothing here is random: a pose is a function of (species, action, frame, facing).
"""
from __future__ import annotations

import copy
import math

from .. import mats as M
from ..motion import pick as _pick
from ..sculpt import rot, v3

ACTIONS = ("idle", "walk", "windup", "attack", "hurt", "death", "swim")


class D(dict):
    """A dict read by attribute (a part's parameters)."""

    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError:
            raise AttributeError(k) from None


def deep(x):
    """`x` with its dicts as D, all the way down."""
    if isinstance(x, dict):
        return D({k: deep(v) for k, v in x.items()})
    if isinstance(x, list):
        return [deep(v) for v in x]
    return x


def merge(base: dict, over: dict | None) -> dict:
    """`base` with `over` laid on it: dicts merge key by key, anything else (a number, a tuple, a list) is replaced."""
    out = copy.deepcopy(dict(base))
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


class Body:
    """A species' resolved body plan: `parts` (each part's kind and sizes), `mats` (the plan's material roles -> the
    palette's names), `motion` (action -> its style, resolved to a dict) and `opts` (what the species is told besides:
    hollowed, ...)."""

    def __init__(self, plan: str, variant: str, parts: dict, mats: dict, motion: dict, styles: dict, opts=None):
        self.plan, self.variant = plan, variant
        self.parts = deep(parts)
        self.mats = D(mats)
        self.opts = D(opts or {})
        self.styles = {}
        self.names = {}
        for action, st in motion.items():
            name, over = (st, None) if isinstance(st, str) else (st[0], st[1])
            if name not in styles:
                raise KeyError("%s: no motion style %r (styles: %s)" % (plan, name, ", ".join(sorted(styles))))
            self.styles[action] = D(merge(styles[name], over))
            self.names[action] = name

    def style(self, action: str) -> D:
        """The action's style (its scalars and tables); an empty style where the species names none."""
        return self.styles.get(action, D())

    def pick(self, channel: str, action: str, f: int, default=0.0):
        """A channel's value on frame `f` of `action` (motion.pick over the action's style), else `default`."""
        st = self.styles.get(action)
        if st is None or not isinstance(st.get(channel), (tuple, list)):
            return default
        return _pick({action: st[channel]}, action, f, default)

    def has(self, channel: str, action: str) -> bool:
        st = self.styles.get(action)
        return st is not None and channel in st


def colour(x):
    """A colour by name: a mats constant ("GLINT"), a ramp's step (("pink", 0)), or an RGBA tuple as it is."""
    if isinstance(x, str):
        return getattr(M, x)
    if isinstance(x, (tuple, list)) and len(x) == 2 and isinstance(x[0], str):
        return M.RAMPS[x[0]][int(x[1])]
    return tuple(x)


def lin(t, fr: float, bk: float) -> float:
    """A size that turns with the facing: (x, on the head-on row, on the tail-on row) -> x + kf * fr + kb * bk
    (motion.headon's fr and bk), or a plain number."""
    if isinstance(t, (int, float)):
        return t
    return t[0] + t[1] * fr + t[2] * bk


def shut(eyes: dict, action: str, f: int) -> bool:
    """Whether the eyes are shut on this frame: `eyes.shut` maps an action to the first frame they close on (hurt 0:
    the flinch only, death 5: from the fifth frame on)."""
    s = eyes.get("shut", {})
    if action == "hurt":
        return "hurt" in s and f == s["hurt"]
    return action in s and f >= s[action]


def collapse(P, t: float, seed: int) -> None:
    """A body of stone coming apart (0..1): every part drops to the ground and spreads into a heap, each its own way
    (by the species' seed), a limb becoming a lump at its middle; the marks and lights go dark early, the dust stays."""
    from ..motion import h01, smooth
    import numpy as np
    e = smooth(t)
    for i, part in enumerate(P.parts):
        g = part.geo
        if part.kind == "limb":
            c = (np.asarray(g["p0"]) + np.asarray(g["p1"])) * 0.5
            r = 0.5 * (g["r0"] + g["r1"]) * (1.0 + 0.6 * e)
        else:
            c = np.asarray(g["at"], float)
            r = float(g["r"]) if part.kind == "sph" else float(min(g["radii"]))
        ja, jb = h01(i, 3, seed % 997) - 0.5, h01(i, 7, seed % 991) - 0.5
        land = np.array((c[0] * 1.15 + ja * 4.0, c[1] * 1.3 + jb * 4.0, r * 0.8))
        hop = 1.6 * math.sin(math.pi * min(1.0, t * 1.3)) * h01(i, 11, seed % 983)
        to = c + (land - c) * e + np.array((0.0, 0.0, hop * (1.0 - e)))
        if part.kind == "limb":
            half = (np.asarray(g["p1"]) - np.asarray(g["p0"])) * 0.5 * (1.0 - e)
            g["p0"], g["p1"] = to - half, to + half
            g["r0"], g["r1"] = g["r0"] + (r - g["r0"]) * e, g["r1"] + (r - g["r1"]) * e
        else:
            g["at"] = to
    if t > 0.25:
        P.marks, P.eyes, P.glow = [], [], []
    for k in range(int(10 * e)):
        a = math.radians(k * 67.0 + seed % 360)
        rr = 3.0 + (k % 4) * 1.4 + 2.0 * e
        P.fx.append((v3(math.cos(a) * rr, math.sin(a) * rr * 0.8, 0.3 + (k % 3) * 0.4 * (1.0 - e)), M.DUST if k % 2 else M.DUST_DIM))


def topple(P, roll: float, mid: float, half: float) -> None:
    """A fall onto its side: rolled `roll` degrees about its length, its middle (`mid` over the ground) coming down to
    `half` (the body's half width) as it lies."""
    P.m = rot("a", roll)
    turned = P.m @ v3(0.0, 0.0, mid)
    P.shift = v3(-turned[0], -turned[1], mid - turned[2] - (mid - half) * math.sin(math.radians(min(roll, 90.0))))
