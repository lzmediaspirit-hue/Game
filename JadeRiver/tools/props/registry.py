"""Prop / tile registry. Definition modules register draw functions with @prop."""
from __future__ import annotations

from pixlib import Canvas

PROPS: dict = {}


def prop(pid, w, h, states=(("idle", 1, 0),), ground=2, kind="prop", repeat=None, anchor=None, **extra):
    """Register a drawing.

    states: sequence of (name, frames, fps); fps 0 = static.
    ground: art px between the ground-contact line and the bottom edge (contact shadow room).
    kind:   "prop" -> art/props, "tile" -> art/tiles (manifest gets "tile": true).
    repeat: for tiles, "x", "y", "xy" or None.
    anchor: override anchor in art px (default bottom centre at the ground line).
    """
    def deco(fn):
        PROPS[pid] = dict(id=pid, w=w, h=h, states=list(states), ground=ground, draw=fn, kind=kind,
                          repeat=repeat, anchor=anchor, extra=extra)
        return fn
    return deco


def new(p_or_w, h=None) -> Canvas:
    if h is None:
        return Canvas(p_or_w["w"], p_or_w["h"])
    return Canvas(p_or_w, h)
