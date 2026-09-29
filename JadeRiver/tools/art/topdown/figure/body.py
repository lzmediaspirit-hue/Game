"""The unclothed body (AGENTS.md rule 4: every movement is drawn on it first) and the face.

Proportions follow the side-view body (a large round head, about two and a half heads tall, short legs), at the top-down
plan's scale: about 46 art px from the soles to the crown (decision 43: 1.2 times the 38 px it was first drawn at).
"""
from __future__ import annotations

import numpy as np

from .geom import TOWARD, depth, project, vec
from .raster import AX, AY, cone, ellipsoid, limb, sphere

# Head and body radii (figure units).
SKULL = (5.5, 6.0, 6.3)          # f, r, u
JAW_AT = (1.0, 0.0, -2.5)
JAW = (4.4, 4.9, 4.4)
HAND_R = 1.35


def arm_bands(sk) -> dict:
    """Each arm segment in front of the chest or behind it (the figure's three bands: back, mid, front). A segment
    level with the chest counts as in front, so arms at the sides draw over the torso's edge."""
    ref = depth(sk.chest) - 0.9
    out = {}
    for s in ("l", "r"):
        up = (sk.__dict__["shoulder_" + s] + sk.__dict__["elbow_" + s]) * 0.5
        fo = (sk.__dict__["elbow_" + s] + sk.__dict__["wrist_" + s]) * 0.5
        out["upper_" + s] = "front" if depth(up) >= ref else "back"
        out["fore_" + s] = "front" if depth(fo) >= ref or depth(sk.__dict__["hand_" + s]) >= ref + 1.5 else "back"
    return out


def solids(sk) -> list:
    Mh = sk.Mh
    bands = arm_bands(sk)
    S = [ellipsoid(sk.head, Mh, SKULL, "skin", part="head", band="head"),
         ellipsoid(sk.head + Mh @ vec(*JAW_AT), Mh, JAW, "skin", part="head", band="head")]
    for sg in (-1.0, 1.0):
        S.append(sphere(sk.head + Mh @ vec(-0.4, sg * 5.7, -1.4), 1.15, "skin", part="ear", band="head"))
    S += limb(sk.neck - sk.Mc[:, 2] * 1.0, sk.head + Mh @ vec(-0.4, 0, -3.6), 1.55, 1.45, "skin", part="neck", band="head")
    S += torso(sk, 0.0, "skin", "torso")
    for s in ("l", "r"):
        sh, el, wr, hd = (sk.__dict__[k + "_" + s] for k in ("shoulder", "elbow", "wrist", "hand"))
        bu, bf = bands["upper_" + s], bands["fore_" + s]
        S.append(sphere(sh, 1.75, "skin", band=bu, part="arm_" + s))
        S += limb(sh, el, 1.4, 1.25, "skin", band=bu, part="arm_" + s)
        S += limb(el, wr, 1.25, 1.05, "skin", band=bf, part="arm_" + s)
        S.append(sphere(hd, HAND_R + (0.12 if sk.__dict__["grip_" + s] == "fist" else 0.0), "skin", band=bf, part="hand_" + s))
        hp, kn, an, ft = (sk.__dict__[k + "_" + s] for k in ("hip", "knee", "ankle", "foot"))
        S += limb(hp, kn, 1.85, 1.5, "skin", part="leg_" + s)
        S += limb(kn, an, 1.5, 1.15, "skin", part="leg_" + s)
        S.append(foot_solid(sk, s, (2.0, 1.2, 0.95), "skin", "foot_" + s))
    return S


def torso(sk, grow: float, mat, part, band="mid", paint=None, clip=None, frame=None) -> list:
    """The trunk as two elliptic cones (hips to waist to chest) capped by the chest's and the hips' rounds, so it
    shades as one smooth form; `grow` thickens it for a garment."""
    kw = dict(band=band, part=part, paint=paint, clip=clip, frame=frame)
    g = grow
    side = sk.Mc[:, 1]
    top = sk.chest + sk.Mc[:, 2] * 1.4
    S = [cone(sk.pelvis - sk.Mp[:, 2] * 0.4, sk.waist, 3.8 + g, 3.4 + g, mat, k=(2.6 + g) / (3.8 + g), side=sk.Mp[:, 1], **kw),
         cone(sk.waist, top, 3.4 + g, 4.3 + g, mat, k=(2.5 + g) / (3.4 + g), side=side, **kw),
         ellipsoid(top, sk.Mc, (2.8 + g, 4.3 + g, 1.9 + g), mat, **kw),
         ellipsoid(sk.pelvis - sk.Mp[:, 2] * 0.4, sk.Mp, (2.6 + g, 3.8 + g, 2.3 + g), mat, **kw)]
    return S


def foot_solid(sk, s: str, radii, mat, part, **kw):
    fd = sk.__dict__["dir_foot_" + s]
    up = sk.up
    side = np.cross(up, fd)
    side = side / max(1e-9, np.linalg.norm(side))
    M = np.stack([fd, side, np.cross(fd, side)], axis=1)
    return ellipsoid(sk.__dict__["foot_" + s], M, radii, mat, part=part, **kw)


# The face (decision 42; decision 43 draws it for the 46 px figure), stamped on the head's resolved pixels before
# shading. Glyphs, rows top to bottom, left to right as seen on screen for the eye on the screen's left (the other eye
# mirrors): K lash, W white, D pupil, I iris, L the iris's lower light, B brow, M mouth, N the nose's shade, P blush.
# `.` leaves skin. An eye is 3 px wide and 3 tall: the lash row, the white, the pupil and the iris, the iris and its
# lower light; the far eye in three quarters and the eye in profile are narrower.
FACE = {
    "eye_front": ["KKK", "WDI", ".IL"], "eye_near": ["KKK", "WDI", ".IL"], "eye_far": ["K", "D", "I"],
    "eye_side": ["KK", ".D", ".I"], "eye_shut": ["KKK"], "brow": ["BB."], "brow_far": ["B"], "brow_dy": -2,
    "mouth_front": ["MM"], "mouth_near": ["M"], "nose_side": ["N"], "blush": ["P"], "blush_dy": 3, "blush_dx": -1,
}
GLYPH_MAT = {"K": "eye_dark", "I": "iris", "L": "iris_light", "W": "eye_white", "D": "pupil", "B": "brow", "N": "nose",
             "M": "mouth", "P": "blush"}
FACE_MATS = ["eye_dark", "iris", "iris_light", "eye_white", "pupil", "brow", "nose", "mouth", "blush"]
# One ellipsoid round the skull and the jaw, in the head's frame: the face shades as one form (raster.smooth_normals).
HEAD_AT = (0.4, 0.0, -0.9)
HEAD_R = (5.9, 6.1, 7.4)


def smooth_head(sk, fines, caster) -> None:
    """The skull and the jaw shaded as one form, so the seam where they meet does not crease the face."""
    if "head" in caster.parts:
        from .raster import smooth_normals
        smooth_normals(fines["head"], caster.parts["head"], sk.head + sk.Mh @ np.array(HEAD_AT), sk.Mh, HEAD_R)


def face(sk, layer, caster) -> None:
    """Stamp the eyes, brows, mouth, nose and blush on the head where it shows and faces the camera: both eyes from the
    front, the near one full and the far one narrow in three quarters, the near one alone in profile; shut in a hurt,
    a fall and meditation."""
    F = FACE
    Mh = sk.Mh
    yaw = sk.fr.yaw_to_camera(Mh[:, 0])
    a = abs(yaw)
    if a > 118:
        return
    head_id = caster.parts.get("head", -9)
    near = "r" if yaw < 0 else "l"
    hx, _ = project(sk.head)
    shut = sk.eyes == "shut"
    for s, sg in (("l", -1.0), ("r", 1.0)):
        p = sk.head + Mh @ vec(4.95, sg * 2.2, 1.0)
        n = (p - sk.head) / np.linalg.norm(p - sk.head)
        if float(n @ TOWARD) < 0.05:
            continue
        sx, sy = project(p)
        on_left = sx < hx
        if shut:
            _stamp(layer, caster, sx, sy, F["eye_shut"], head_id, mirror=not on_left)
            continue
        if a <= 24:
            glyph, brow, mir = F["eye_front"], F["brow"], not on_left
        elif a <= 66:
            if s == near:
                glyph, brow, mir = F["eye_near"], F["brow"], yaw > 0
            else:
                glyph, brow, mir = F["eye_far"], F["brow_far"], yaw > 0
        else:
            if s != near:
                continue
            glyph, brow, mir = F["eye_side"], F["brow_far"], yaw > 0
            sx += -1 if yaw < 0 else 1          # a profile's eye sits a pixel in from the face's edge
        _stamp(layer, caster, sx, sy + F["brow_dy"], brow, head_id, mirror=mir)
        _stamp(layer, caster, sx, sy, glyph, head_id, mirror=mir)
        if a <= 66 and (a <= 24 or s == near):
            bx = sx + F["blush_dx"] * (1 if on_left else -1)
            _stamp(layer, caster, bx, sy + F["blush_dy"], F["blush"], head_id, mirror=mir)
    if shut or a > 80:
        return
    mx, my = project(sk.head + Mh @ vec(5.0, 0.0, -2.4))
    _stamp(layer, caster, mx, my, F["mouth_front"] if a <= 24 else F["mouth_near"], head_id, mirror=yaw > 0)
    if a > 24:
        nx, ny = project(sk.head + Mh @ vec(5.6, 0.25, -0.9))
        _stamp(layer, caster, nx + (1 if yaw < 0 else -1), ny, F["nose_side"], head_id)


def _stamp(layer, caster, sx, sy, glyph, head_id, mirror=False) -> None:
    w = len(glyph[0])
    x0 = int(np.floor(sx + AX - (w - 1) * 0.5))
    y0 = int(np.floor(sy + AY))
    for j, row in enumerate(glyph):
        if mirror:
            row = row[::-1]
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            x, y = x0 + i, y0 + j
            if 0 <= y < layer.mat.shape[0] and 0 <= x < layer.mat.shape[1] and layer.part[y, x] == head_id \
                    and layer.mat[y, x] >= 0:
                layer.mat[y, x] = caster.mid(GLYPH_MAT[ch])


def light_face(layers, caster) -> None:
    """A face reads best nearly flat: the head's skin keeps to the shadow and the base step, with no rim or bounce
    across it; the neck sits in the jaw's shade, one flat step, with a line of the core shadow along the jaw."""
    R = layers["head"]
    if "head" not in caster.parts:
        return
    skin = caster.mid("skin")
    face_px = (R.part == caster.parts["head"]) & (R.mat == skin)
    R.tone = np.where(face_px, np.clip(R.tone, 2, 3), R.tone).astype(np.int8)
    R.rim &= ~face_px
    R.bounce &= ~face_px
    if "neck" in caster.parts:
        neck = (R.part == caster.parts["neck"]) & (R.mat == skin)
        hd = R.part == caster.parts["head"]
        by = np.zeros_like(hd)
        by[1:] |= hd[:-1]
        by[:, 1:] |= hd[:, :-1]
        by[:, :-1] |= hd[:, 1:]
        R.tone = np.where(neck, np.where(by, 1, 2), R.tone).astype(np.int8)
        R.rim &= ~neck
        R.bounce &= ~neck
