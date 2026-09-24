"""Hollowed boarlet - the wild boarlet drained by the Hollow (Hollow element).

Same silhouette, poses and timing as ``wild_boarlet`` (thin wrapper): ``cv.hollow``
re-colours every ramp to the grey-white Hollow family and turns the eye empty white.
On top: a dark socket around the empty eye (so it reads on the pale head) and a few
pale mist wisps curling up off its back; they thicken as it dies.
"""
import helpers_batch_a as hb
import pixel as px
import wild_boarlet as base

SPEC = dict(base.SPEC, id="hollowed_boarlet")

# wisps per action: (fraction along the back 0..1, length, sway phase offset)
_WISPS = {
    "idle": ((0.28, 5.0, 0.0), (0.62, 4.0, 2.0)),
    "walk": ((0.25, 5.0, 0.0), (0.60, 4.0, 2.0)),
    "windup": ((0.28, 6.0, 0.0), (0.60, 5.0, 2.0)),
    "attack": ((0.22, 5.0, 0.0), (0.55, 4.0, 2.0)),
    "hurt": ((0.35, 4.0, 1.0),),
    "death": ((0.22, 6.0, 0.0), (0.50, 7.0, 2.0), (0.76, 5.0, 4.0)),
}


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    cv.hollow = True  # grey-white ramps, parts named "eye" become empty white
    base.draw(cv, action, frame)
    if base.POSE(action, frame).eye in ("squeeze", "dead"):
        hb.recolour(cv, "eye", hb.HOLLOW_DARK.deep)  # a dark squint / X reads on the pale head
    else:
        hb.socket(cv)
    bb = hb.body_bbox(cv)
    if bb is None:
        return
    x0, y0, x1, y1 = bb
    fx = cv.layer(above=True, outline=False)
    drift = {"walk": -1, "attack": -1}.get(action, -1)
    for k, (u, ln, off) in enumerate(_WISPS[action]):
        x = round(x0 + 4 + u * (x1 - x0 - 12))
        col = cv.filled[:, x]
        top = int(col.argmax()) if col.any() else y0
        hb.mist_wisp(fx, x + 0.5, top - 0.5, phase=frame * 1.4 + off, length=ln, rise=1.0,
                     direction=drift, thick=0.85)
