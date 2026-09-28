"""The unclothed body (AGENTS.md rule 4: every movement is drawn on it first) and the face.

Proportions follow the side-view body (a large round head, about two and a half heads tall, short legs), at the top-down
plan's scale: about 38 art px from the soles to the crown.
"""
from __future__ import annotations

import numpy as np

from .geom import SCALE, TOWARD, depth, project, vec
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


# Face glyphs, rows top to bottom, left to right on screen: K lash, I iris, L light iris, W white. `.` leaves skin.
EYE_FRONT_L = ["KK", "WI"]
EYE_FRONT_R = ["KK", "IW"]
EYE_NARROW = ["K", "I"]
EYE_SIDE = ["KK", "I."]
EYE_SHUT = ["KK"]
GLYPH_MAT = {"K": "eye_dark", "I": "iris", "L": "iris_light", "W": "eye_white", "M": "mouth"}


def face(sk, layer, caster) -> None:
    """Stamp the eyes and mouth on the head in the body's mid layer, where the head shows and faces the camera."""
    Mh = sk.Mh
    yaw = sk.fr.yaw_to_camera(Mh[:, 0])
    a = abs(yaw)
    if a > 118:
        return
    head_id = caster.parts.get("head", -9)
    near = "r" if yaw < 0 else "l"
    for s, sg in (("l", -1.0), ("r", 1.0)):
        p = sk.head + Mh @ vec(4.95, sg * 2.2, 1.0)
        n = (p - sk.head)
        n = n / np.linalg.norm(n)
        if float(n @ TOWARD) < 0.05:
            continue
        if sk.eyes == "shut":
            g = EYE_SHUT
        elif a <= 24:
            g = EYE_FRONT_L if project(p)[0] < project(sk.head)[0] else EYE_FRONT_R
        elif a <= 66:
            g = (EYE_FRONT_L if yaw > 0 else EYE_FRONT_R) if s == near else EYE_NARROW
        else:
            if s != near:
                continue
            g = EYE_SIDE if yaw < 0 else [row[::-1] for row in EYE_SIDE]
            # a profile's eye sits a pixel in from the face's edge
            _stamp(layer, caster, p, g, head_id, dx=-1 if yaw < 0 else 1)
            continue
        _stamp(layer, caster, p, g, head_id)
    if a <= 70 and sk.eyes != "shut":
        p = sk.head + Mh @ vec(5.0, 0.0, -2.4)
        _stamp(layer, caster, p, ["M"], head_id, dy=0)


def _stamp(layer, caster, p, glyph, head_id, dx=0, dy=0) -> None:
    sx, sy = project(p)
    w = len(glyph[0])
    x0 = int(np.floor(sx + AX - (w - 1) * 0.5 + 0.0)) + dx
    y0 = int(np.floor(sy + AY)) + dy
    for j, row in enumerate(glyph):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            x, y = x0 + i, y0 + j
            if 0 <= y < layer.mat.shape[0] and 0 <= x < layer.mat.shape[1] and layer.part[y, x] == head_id:
                layer.mat[y, x] = caster.mid(GLYPH_MAT[ch])
