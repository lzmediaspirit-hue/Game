"""Cloth folds (decision 42): paint added to a garment's own, so its cloth reads as cloth at 38 px. Each adds a paint
bias to the `cloth` samples only (trim, belts and panels stay clean): a groove a step down and, beside it on the sunlit
west, a lit ridge half a step up.

  skirt    folds that hang from the belt, a few broad ones, uneven, widening to the hem (a long robe darkens its hem)
  chest    gathers over the belt, and two pulls from the belt toward the chest's sides
  sleeve   a crease in the crook of the elbow (the upper sleeve's end), a fold near the cuff
  trouser  a crease behind the knee; over the shin's ankle wrap the cloth gathers in a zigzag
Used by torso.py and legs.py; not a layer of its own.
"""
from __future__ import annotations

import numpy as np


def wrap(orig, mat: str, extra):
    """A paint (`orig`, or plain `mat` when None) with `extra(loc, P, nrm, names)`'s bias added."""

    def paint(loc, P, nrm):
        if orig is None:
            names = np.array([mat] * len(loc), dtype=object)
            bias = np.zeros(len(loc), dtype=np.float32)
        else:
            names, bias = orig(loc, P, nrm)
            names = np.asarray(names, dtype=object)
            bias = np.asarray(bias, dtype=np.float32).copy()
        return names, bias + extra(loc, P, nrm, names)
    return paint


def skirt(L: float, long: bool):
    """Folds from the belt to the hem (the skirt cone's frame: its axis down, `L` long)."""
    centres = np.array([-128.0, -74.0, -22.0, 34.0, 86.0, 142.0])   # angles round the skirt (0 its right side)

    def extra(loc, P, nrm, names):
        th = np.degrees(np.arctan2(loc[:, 1], loc[:, 0]))
        w = loc[:, 2] / max(L, 1e-6)
        out = np.zeros(len(loc), dtype=np.float32)
        cloth = names == "cloth"
        grow = np.clip((w - 0.18) / 0.5, 0.0, 1.0)
        for i, c in enumerate(centres):
            d = (th - c + 180.0) % 360.0 - 180.0
            wid = 7.0 + 5.0 * grow + (i % 2) * 2.0
            out[cloth & (np.abs(d) < wid * 0.45) & (w > 0.2 + 0.1 * (i % 3))] -= 1.0
            out[cloth & (d > wid * 0.45) & (d < wid * 1.1) & (w > 0.3)] += 1.0
        if long:
            out[cloth & (w > 0.92)] -= 0.5
        return out
    return extra


def chest(sk):
    """Gathers over the belt and two pulls from the belt toward the chest's sides (the chest's frame)."""
    wu = float((sk.waist - sk.chest) @ sk.Mc[:, 2])

    def extra(loc, P, nrm, names):
        f, r, u = loc[:, 0], loc[:, 1], loc[:, 2]
        out = np.zeros(len(loc), dtype=np.float32)
        cloth = names == "cloth"
        band = (u > wu + 0.95) & (u < wu + 2.0) & (f > 0.2)
        g = np.abs(((r + 3.0) % 1.9) - 0.95) < 0.24
        out[cloth & band & g] -= 1.0
        pull = (f > 0.4) & (u > wu + 1.6) & (u < 3.0)
        for sg in (-1.0, 1.0):
            line = r * sg - (2.1 + (u - wu - 1.6) * 0.55)
            out[cloth & pull & (np.abs(line) < 0.28)] -= 1.0
            out[cloth & pull & (line < -0.28) & (line > -0.8)] += 0.5
        return out
    return extra


def sleeve(upper: bool, L: float):
    """A crease in the crook of the elbow (the upper sleeve's end), a fold near the cuff (the sleeve cone's frame)."""

    def extra(loc, P, nrm, names):
        z = loc[:, 2]
        out = np.zeros(len(loc), dtype=np.float32)
        cloth = names == "cloth"
        ang = np.degrees(np.arctan2(loc[:, 1], loc[:, 0]))
        if upper:
            out[cloth & (z > L * 0.72) & (z < L * 0.86) & (np.abs(ang) < 70)] -= 1.0
        else:
            out[cloth & (z > L * 0.35) & (z < L * 0.5) & (np.abs(ang - 40) < 60)] -= 1.0
        return out
    return extra


def trouser(shin: bool, L: float):
    """Behind the knee a crease; over the ankle wrap the cloth gathers in a zigzag (the leg cone's frame)."""

    def extra(loc, P, nrm, names):
        z = loc[:, 2]
        out = np.zeros(len(loc), dtype=np.float32)
        cloth = names == "cloth"
        ang = np.degrees(np.arctan2(loc[:, 1], loc[:, 0]))
        if shin:
            zig = z / L - 0.62 - 0.05 * np.abs(((ang + 180.0) % 60.0) - 30.0) / 30.0
            out[cloth & (np.abs(zig) < 0.045)] -= 1.0
            out[cloth & (zig > 0.045) & (zig < 0.1)] += 0.5
            out[cloth & (z < L * 0.16) & (np.abs(ang) < 50)] -= 1.0
        else:
            out[cloth & (np.abs(((ang + 200.0) % 120.0) - 60.0) < 7.0) & (z > 1.2)] -= 1.0
        return out
    return extra
