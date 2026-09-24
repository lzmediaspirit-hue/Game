"""Reusable shape builders (return masks) and small decorative stamps."""
from __future__ import annotations

import math

import numpy as np

from pix import Canvas, dilate4, erode4, rgb  # noqa: F401


def _dir(angle_deg):
    a = math.radians(angle_deg)
    return math.cos(a), -math.sin(a)


def lens_pts(bx, by, angle, length, width, bend=0.0, k=14, tip_power=0.8, base_w=0.0):
    """Leaf / blade outline points. angle: 0 right, 90 up. bend: sideways bow."""
    dx, dy = _dir(angle)
    px, py = -dy, dx  # perpendicular (left of direction)
    left, right = [], []
    for i in range(k + 1):
        t = i / float(k)
        off = bend * math.sin(math.pi * t) * length
        cx = bx + dx * t * length + px * off
        cy = by + dy * t * length + py * off
        hw = base_w / 2.0 * (1 - t) + width / 2.0 * (math.sin(math.pi * min(1.0, t ** tip_power)))
        left.append((cx + px * hw, cy + py * hw))
        right.append((cx - px * hw, cy - py * hw))
    return left + right[::-1]


def leaf(c: Canvas, bx, by, angle, length, width, bend=0.0, **kw):
    return c.poly(lens_pts(bx, by, angle, length, width, bend, **kw))


def midrib(c: Canvas, bx, by, angle, length, bend=0.0, frac=0.8):
    dx, dy = _dir(angle)
    px, py = -dy, dx
    pts = []
    for i in range(9):
        t = i / 8.0 * frac
        off = bend * math.sin(math.pi * t) * length
        pts.append((bx + dx * t * length + px * off, by + dy * t * length + py * off))
    m = c.empty()
    for (a, b) in zip(pts, pts[1:]):
        m |= c.bres(int(a[0]), int(a[1]), int(b[0]), int(b[1]))
    return m


def curve_pts(p0, p1, p2, k=16):
    """Quadratic bezier points."""
    out = []
    for i in range(k + 1):
        t = i / float(k)
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        out.append((x, y))
    return out


def bez_line(c: Canvas, p0, p1, p2, w=1.0, k=16):
    pts = curve_pts(p0, p1, p2, k)
    if w <= 1.0:
        m = c.empty()
        ip = [(int(math.floor(x)), int(math.floor(y))) for x, y in pts]
        for a, b in zip(ip, ip[1:]):
            m |= c.bres(a[0], a[1], b[0], b[1])
        return m
    return c.polyline(pts, w)


def taper_curve(c: Canvas, p0, p1, p2, w0, w1, k=20):
    """Bezier stroke whose width goes from w0 to w1."""
    pts = curve_pts(p0, p1, p2, k)
    m = c.empty()
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        t = i / float(len(pts) - 1)
        m |= c.seg(a[0], a[1], b[0], b[1], w0 + (w1 - w0) * t)
    return m


def drop(c: Canvas, cx, cy, r, h=None):
    """Teardrop pointing up; (cx, cy) is the centre of the round bottom."""
    h = r * 1.9 if h is None else h
    body = c.circle(cx, cy, r)
    tri = c.poly([(cx - r * 0.93, cy - r * 0.35), (cx, cy - h), (cx + r * 0.93, cy - r * 0.35)])
    return body | tri


def flame(c: Canvas, cx, by, w, h, lean=0.0):
    """Flame silhouette sitting on (cx, by); three tongues."""
    pts = [
        (cx - w / 2.0, by - h * 0.28),
        (cx - w * 0.42 + lean * 0.3, by - h * 0.62),
        (cx - w * 0.18, by - h * 0.46),
        (cx + lean, by - h),
        (cx + w * 0.2, by - h * 0.52),
        (cx + w * 0.42 + lean * 0.3, by - h * 0.72),
        (cx + w / 2.0, by - h * 0.3),
    ]
    body = c.ellipse(cx, by - h * 0.28, w / 2.0, h * 0.3)
    return body | c.poly(pts + [(cx + w * 0.3, by - h * 0.1), (cx - w * 0.3, by - h * 0.1)])


def star4(c: Canvas, x, y, arm=2):
    """Plus-shaped sparkle mask centred on pixel (x, y)."""
    m = c.rect(x - arm, y, x + arm, y) | c.rect(x, y - arm, x, y + arm)
    return m


def sparkle(c: Canvas, x, y, col_hi='#FFFFFF', col_mid=None, arm=2):
    """Paint a small 4-point sparkle (unoutlined highlight) directly."""
    col_mid = col_mid or col_hi
    for k in range(1, arm + 1):
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            c.px(x + dx, y + dy, col_mid if k == arm else col_hi)
    c.px(x, y, col_hi)


def outline_only(mask):
    return mask & ~erode4(mask)


def diamond(c: Canvas, cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    return (abs(c.X - cx) / rx + abs(c.Y - cy) / ry) <= 1.0


def rounded_rect(c: Canvas, x0, y0, x1, y1, r=1):
    """Integer rect with r-pixel diagonal corner cuts."""
    m = c.rect(x0, y0, x1, y1)
    for k in range(r):
        n = r - k
        for (x, y, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            m &= ~c.rect(min(x, x + sx * (n - 1)), y + sy * k, max(x, x + sx * (n - 1)), y + sy * k)
    return m


def wave_line(c: Canvas, x0, x1, y, amp=1, period=6, phase=0):
    pts = []
    for x in range(x0, x1 + 1):
        yy = y + int(round(amp * math.sin((x - x0 + phase) / period * 2 * math.pi)))
        pts.append((x, yy))
    return c.pts(pts) | c.bres_path(pts)
