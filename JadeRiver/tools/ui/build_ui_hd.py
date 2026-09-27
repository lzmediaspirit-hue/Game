#!/usr/bin/env python3
"""HD UI kit: art/ui/hd/<asset>__<state>.png + data/ui_assets_hd.json.

The pixel kit (build_ui.py) is authored at 2 screen px per art pixel and scaled with
nearest filtering. On a phone the canvas is scaled 1.5-3x, so its frames came out
blocky and uneven. This kit is rendered analytically instead: every shape is a signed
distance field sampled at 3 texels per screen pixel (anti-aliased over one texel), with
gradient enamel faces, bevelled gold trim and corner filigree. UiKit draws it through
HdStyleBox (scripts/ui/hd_style_box.gd), a nine-slice scaled down by 3 with mipmapped
linear filtering, so it stays sharp from 1280x720 up to 4K.

Same asset names, states and nine-slice margins (in screen px) as data/ui_assets.json.
Deterministic. Usage: python3 tools/ui/build_ui_hd.py [--review PNG]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

sys.dont_write_bytecode = True

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_DIR = os.path.join(ROOT, "art", "ui", "hd")
MANIFEST = os.path.join(ROOT, "data", "ui_assets_hd.json")
K = 3  # texels per screen pixel


def hexc(h: str, a: float = 1.0) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)] + [a])


INK = hexc("#071015")
GOLD_HI = hexc("#fff0bf")
GOLD = hexc("#e5b84c")
GOLD_MID = hexc("#c8923e")
BRONZE = hexc("#7a5426")
JADE_HI = hexc("#67d6bd")
JADE = hexc("#2c9e8f")
JADE_LO = hexc("#15514f")
TEAL_TOP = hexc("#11343b")
TEAL_BOT = hexc("#081c22")
PAPER_TOP = hexc("#f3ead4")
PAPER_BOT = hexc("#ddd0b0")
BROWN = hexc("#4a3620")
LACQUER = hexc("#a33a2a")
WHITE = hexc("#ffffff")
GREY_HI = hexc("#8d9694")
GREY_LO = hexc("#4a5250")


class Canvas:
    """Premultiplied RGBA float canvas in screen-px coordinates (K texels per px)."""

    def __init__(self, w: float, h: float):
        self.w, self.h = w, h
        self.tw, self.th = int(round(w * K)), int(round(h * K))
        self.px = np.zeros((self.th, self.tw, 4))
        xs = (np.arange(self.tw) + 0.5) / K
        ys = (np.arange(self.th) + 0.5) / K
        self.X, self.Y = np.meshgrid(xs, ys)

    def paint(self, cov: np.ndarray, color) -> None:
        """Composite `color` (RGBA, or an HxWx4 array) over the canvas with coverage `cov`."""
        col = np.broadcast_to(color, self.px.shape) if np.ndim(color) == 1 else color
        a = np.clip(cov, 0.0, 1.0) * col[..., 3]
        src = np.dstack([col[..., 0] * a, col[..., 1] * a, col[..., 2] * a, a])
        self.px = src + self.px * (1.0 - a[..., None])

    def vgrad(self, stops, y0: float = 0.0, y1: float | None = None) -> np.ndarray:
        """Vertical gradient through (t, color) stops between y0 and y1."""
        y1 = self.h if y1 is None else y1
        t = np.clip((self.Y - y0) / max(1e-6, y1 - y0), 0.0, 1.0)
        out = np.zeros(self.px.shape)
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            m = (t >= t0) & (t <= t1)
            f = ((t - t0) / max(1e-6, t1 - t0))[..., None]
            out = np.where(m[..., None], c0 * (1 - f) + c1 * f, out)
        return out

    def image(self) -> Image.Image:
        a = self.px[..., 3:4]
        rgb = np.where(a > 1e-6, self.px[..., :3] / np.maximum(a, 1e-6), 0.0)
        arr = np.dstack([rgb, a])
        return Image.fromarray(np.clip(arr * 255.0 + 0.5, 0, 255).astype(np.uint8), "RGBA")


# ------------------------------------------------------------------ distance fields
def sd_rrect(X, Y, x0, y0, x1, y1, r):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    hx, hy = (x1 - x0) / 2 - r, (y1 - y0) / 2 - r
    qx, qy = np.abs(X - cx) - hx, np.abs(Y - cy) - hy
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def sd_circle(X, Y, cx, cy, r):
    return np.hypot(X - cx, Y - cy) - r


def sd_diamond(X, Y, cx, cy, r):
    return (np.abs(X - cx) + np.abs(Y - cy) - r) / math.sqrt(2)


def sd_segment(X, Y, ax, ay, bx, by, w):
    px, py = X - ax, Y - ay
    dx, dy = bx - ax, by - ay
    h = np.clip((px * dx + py * dy) / (dx * dx + dy * dy), 0, 1)
    return np.hypot(px - dx * h, py - dy * h) - w / 2


def sd_arc(X, Y, cx, cy, r, a0, a1, w):
    """Ring segment of radius r and width w between angles a0..a1 (radians, y down)."""
    ang = np.arctan2(Y - cy, X - cx)
    mid, half = (a0 + a1) / 2, (a1 - a0) / 2
    d_ang = np.abs(np.angle(np.exp(1j * (ang - mid))))
    ring = np.abs(np.hypot(X - cx, Y - cy) - r) - w / 2
    ex = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in (a0, a1)]
    ends = np.minimum(*[np.hypot(X - ex_x, Y - ex_y) - w / 2 for ex_x, ex_y in ex])
    return np.where(d_ang <= half, ring, ends)


def cov(d):
    """Coverage of a distance field, anti-aliased across one texel."""
    return np.clip(0.5 - d * K, 0.0, 1.0)


def band(d, outer, inner):
    """Coverage of the ring between distances -outer..-inner inside a shape (outer < inner in depth)."""
    return np.clip(cov(d + outer) - cov(d + inner), 0.0, 1.0)


def soft(d, width):
    """A soft falloff outside a shape over `width` px (shadows, glows)."""
    return np.clip(1.0 - d / width, 0.0, 1.0) ** 2 * (d > 0) + (d <= 0)


# ------------------------------------------------------------------ shared pieces
def gold_bevel(c: Canvas, d, outer: float, inner: float, dim=False):
    """Gold trim from depth `outer` to `inner`, lit from above, darker below."""
    hi, mid, lo = (GREY_HI, GREY_HI * 0.85 + GREY_LO * 0.15, GREY_LO) if dim else (GOLD_HI, GOLD, BRONZE)
    c.paint(band(d, outer, inner), c.vgrad([(0, hi), (0.45, mid), (1, lo)]))


def gem(c: Canvas, x, y, r, jade=True):
    """A cut gem: gold rim, jade (or lacquer) body, a white glint."""
    body_hi, body_lo = (JADE_HI, JADE_LO) if jade else (hexc("#e06a52"), LACQUER * 0.8 + INK * 0.2)
    c.paint(cov(sd_diamond(c.X, c.Y, x, y + 0.5, r + 0.9)), INK * np.array([1, 1, 1, 0.5]))
    c.paint(cov(sd_diamond(c.X, c.Y, x, y, r + 0.9)), GOLD)
    c.paint(cov(sd_diamond(c.X, c.Y, x, y, r)), c.vgrad([(0, body_hi), (1, body_lo)], y - r, y + r))
    c.paint(cov(sd_circle(c.X, c.Y, x - r * 0.3, y - r * 0.35, max(0.35, r * 0.22))), WHITE * np.array([1, 1, 1, 0.8]))


def corner_brackets(c: Canvas, inset, leg, w, gem_r, curl=0.0, color=GOLD, jade=True):
    """Gold L-brackets in the four corners (inside the nine-slice corner squares), with
    optional scroll curls at the leg ends and a gem at each corner."""
    W, H = c.w, c.h
    for sx, sy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        x = inset if sx == 0 else W - inset
        y = inset if sy == 0 else H - inset
        dx = 1 if sx == 0 else -1
        dy = 1 if sy == 0 else -1
        d = np.minimum(sd_segment(c.X, c.Y, x, y, x + dx * leg, y, w), sd_segment(c.X, c.Y, x, y, x, y + dy * leg, w))
        if curl > 0:
            # Each leg ends in a small inward curl (a cloud-scroll hook).
            ex, ey = x + dx * leg, y
            d = np.minimum(d, sd_arc(c.X, c.Y, ex, ey + dy * curl, curl, *(_arc_span(dx, dy, "h")), w))
            ex, ey = x, y + dy * leg
            d = np.minimum(d, sd_arc(c.X, c.Y, ex + dx * curl, ey, curl, *(_arc_span(dx, dy, "v")), w))
        c.paint(cov(d - 0.35), INK * np.array([1, 1, 1, 0.55]))
        c.paint(cov(d), c.vgrad([(0, GOLD_HI), (1, color)], y - 3, y + 3) if sy == 0 else color)
        if gem_r > 0:
            gem(c, x, y, gem_r, jade)


def _arc_span(dx, dy, leg):
    # Angles (y down) so the curl hooks back toward the panel's inside.
    if leg == "h":
        base = -math.pi / 2 if dy > 0 else math.pi / 2
        return (base, base + math.pi * 1.1) if dx > 0 else (base - math.pi * 1.1, base)
    base = math.pi if dx > 0 else 0.0
    return (base - math.pi * 1.1, base) if dy > 0 else (base, base + math.pi * 1.1)


def drop_shadow(c: Canvas, x0, y0, x1, y1, r, dy=2.0, blur=3.0, alpha=0.5):
    d = sd_rrect(c.X, c.Y, x0, y0 + dy, x1, y1 + dy, r)
    c.paint(soft(d, blur) * alpha, INK)


# ------------------------------------------------------------------ assets
def panel(w, h, r=3.0, major=False):
    c = Canvas(w, h)
    d = sd_rrect(c.X, c.Y, 0, 0, w, h, r)
    c.paint(cov(d), c.vgrad([(0, TEAL_TOP), (1, TEAL_BOT)]))
    # A recessed top: a soft shade just inside the upper frame.
    c.paint(cov(d) * np.clip(1.0 - (c.Y - 3.0) / 6.0, 0, 1) * (c.Y > 2.0), INK * np.array([1, 1, 1, 0.28]))
    c.paint(band(d, 0.0, 1.0), INK)
    if major:
        gold_bevel(c, d, 1.0, 6.0)
        c.paint(band(d, 3.0, 3.6), BRONZE * np.array([1, 1, 1, 0.7]))
        c.paint(band(d, 6.0, 6.8), INK * np.array([1, 1, 1, 0.85]))
        c.paint(band(d, 9.0, 10.0), JADE * np.array([1, 1, 1, 0.6]))
        corner_brackets(c, 10.5, 13.5, 2.2, 4.0, curl=2.6)
    else:
        gold_bevel(c, d, 1.0, 2.0)
        c.paint(band(d, 3.4, 4.1), JADE * np.array([1, 1, 1, 0.45]))
        corner_brackets(c, 4.0, 6.5, 1.1, 1.4)
    return c


def button(w, h, state, primary=True):
    c = Canvas(w, h)
    r = 8.0 if primary else 6.0
    pressed, disabled = state == "pressed", state == "disabled"
    y_off = 1.0 if pressed else 0.0
    x0, y0, x1, y1 = 1.0, 1.0 + y_off, w - 1.0, h - 3.0 + y_off
    if not pressed:
        drop_shadow(c, x0, y0, x1, y1, r, dy=2.0, blur=2.5, alpha=0.55)
    d = sd_rrect(c.X, c.Y, x0, y0, x1, y1, r)
    c.paint(cov(d), INK)
    if primary:
        gold_bevel(c, d, 0.8, 3.0, dim=disabled)
        if disabled:
            face = [(0, hexc("#56615f")), (0.5, hexc("#3c4746")), (1, hexc("#29312f"))]
        elif pressed:
            face = [(0, hexc("#2f9a89")), (0.5, hexc("#1c6f66")), (1, hexc("#0f4640"))]
        else:
            face = [(0, hexc("#5fd4bf")), (0.45, hexc("#2c9e8f")), (1, hexc("#155e56"))]
        inner = 3.0
    else:
        c.paint(band(d, 0.8, 1.6), c.vgrad([(0, GOLD), (1, BRONZE)]) if not disabled else GREY_LO)
        c.paint(band(d, 1.6, 3.0), c.vgrad([(0, JADE_HI), (1, JADE)]) if not disabled else GREY_HI * 0.8)
        if disabled:
            face = [(0, hexc("#27302f")), (1, hexc("#171e1e"))]
        elif pressed:
            face = [(0, hexc("#0c2a30")), (1, hexc("#123b41"))]
        else:
            face = [(0, hexc("#1b4c52")), (1, hexc("#0a262c"))]
        inner = 3.0
    fd = d + inner
    c.paint(cov(fd), c.vgrad(face, y0, y1))
    if not disabled and not pressed:
        # Gloss on the upper half and a bright top edge.
        mid = (y0 + y1) / 2
        c.paint(cov(fd) * np.clip((mid - c.Y) / (mid - y0), 0, 1) ** 1.5, WHITE * np.array([1, 1, 1, 0.16 if primary else 0.07]))
        c.paint(band(fd, 0.0, 1.0) * (c.Y < y0 + inner + 3), WHITE * np.array([1, 1, 1, 0.35 if primary else 0.18]))
    # A dark lip along the bottom of the face.
    c.paint(band(fd, 0.0, 1.2) * (c.Y > y1 - inner - 3), INK * np.array([1, 1, 1, 0.35]))
    return c


def tab(w, h, state):
    c = Canvas(w, h)
    sel = state == "selected"
    r = 6.0
    # Rounded on top only: extend the shape below the texture.
    d = sd_rrect(c.X, c.Y, 0.5, 0.5, w - 0.5, h + r + 2, r)
    c.paint(cov(d), c.vgrad([(0, hexc("#1d5a5a")), (1, hexc("#0e3236"))]) if sel else c.vgrad([(0, hexc("#10313a")), (1, hexc("#0a2127"))]))
    c.paint(band(d, 0.0, 1.0), INK)
    c.paint(band(d, 1.0, 2.0), (JADE_HI if sel else JADE) * np.array([1, 1, 1, 0.9 if sel else 0.55]))
    if sel:
        top = cov(sd_rrect(c.X, c.Y, 2.0, 1.2, w - 2.0, 4.2, 1.5))
        c.paint(top, c.vgrad([(0, GOLD_HI), (1, GOLD)], 1.2, 4.2))
        c.paint(cov(d + 2.0) * np.clip((h * 0.5 - c.Y) / (h * 0.5), 0, 1), WHITE * np.array([1, 1, 1, 0.08]))
    return c


def slot(w, h, state):
    c = Canvas(w, h)
    r = 4.0
    d = sd_rrect(c.X, c.Y, 0.5, 0.5, w - 0.5, h - 0.5, r)
    dis, sel = state == "disabled", state == "selected"
    fill = [(0, hexc("#06161b")), (1, hexc("#0e2d33"))] if not dis else [(0, hexc("#070f12")), (1, hexc("#0c1618"))]
    c.paint(cov(d), c.vgrad(fill))
    c.paint(cov(d + 1.5) * np.clip(1.0 - (c.Y - 1.5) / 5.0, 0, 1), INK * np.array([1, 1, 1, 0.45]))
    c.paint(band(d, 0.0, 1.0), INK)
    if sel:
        gold_bevel(c, d, 1.0, 2.8)
        c.paint(band(d, 2.8, 6.0) * 0.5, GOLD * np.array([1, 1, 1, 0.35]))
    else:
        c.paint(band(d, 1.0, 2.0), (hexc("#3b4748") if dis else hexc("#2f8a7d")) * np.array([1, 1, 1, 0.9]))
        c.paint(band(d, 2.0, 2.6), WHITE * np.array([1, 1, 1, 0.04]))
    return c


def slot_glow(w, h):
    c = Canvas(w, h)
    d = sd_rrect(c.X, c.Y, 11, 11, w - 11, h - 11, 1.0)
    c.paint(soft(np.maximum(d, 0), 9.0) * (d > 0) * 0.6, GOLD)
    c.paint(band(d + 0.0, -1.5, 0.0), GOLD_HI)
    return c


def title_plaque(w, h):
    c = Canvas(w, h)
    # Swallow-tailed ribbons behind the plaque's ends.
    for side in (0, 1):
        xs = c.X if side == 0 else w - c.X
        body = sd_rrect(xs, c.Y, 4.0, h * 0.30, 46.0, h * 0.70, 1.5)
        notch = (np.abs(c.Y - h / 2) - (6.0 - (xs - 4.0) * 0.9)) / 1.4
        rib = np.maximum(body, -notch)
        c.paint(cov(rib - 0.6), INK * np.array([1, 1, 1, 0.6]))
        c.paint(cov(rib), c.vgrad([(0, GOLD_HI), (0.5, GOLD), (1, BRONZE)], h * 0.3, h * 0.7))
        c.paint(cov(sd_segment(xs, c.Y, 30, h * 0.3 + 1, 30, h * 0.7 - 1, 1.2)), BRONZE * np.array([1, 1, 1, 0.8]))
    x0, x1 = 38.0, w - 38.0
    drop_shadow(c, x0, 3.0, x1, h - 5.0, 6.0, dy=2.0, blur=2.5, alpha=0.5)
    d = sd_rrect(c.X, c.Y, x0, 3.0, x1, h - 5.0, 6.0)
    c.paint(cov(d), INK)
    gold_bevel(c, d, 0.8, 3.2)
    fd = d + 3.2
    c.paint(cov(fd), c.vgrad([(0, hexc("#2f9887")), (0.5, hexc("#17625a")), (1, hexc("#0d3f3b"))], 6, h - 8))
    c.paint(band(fd, 1.8, 2.5), GOLD * np.array([1, 1, 1, 0.55]))
    mid = h / 2
    c.paint(cov(fd) * np.clip((mid - c.Y) / (mid - 6), 0, 1) ** 1.5, WHITE * np.array([1, 1, 1, 0.15]))
    for gx in (x0 + 1.0, x1 - 1.0):
        gem(c, gx, h / 2 - 1.0, 3.0)
    return c


def close_button(w, h, state):
    c = Canvas(w, h)
    cx, cy, r = w / 2, h / 2 - 1, w / 2 - 4
    pressed = state == "pressed"
    if not pressed:
        c.paint(soft(sd_circle(c.X, c.Y, cx, cy + 2, r), 2.5) * 0.55, INK)
    cy += 1 if pressed else 0
    d = sd_circle(c.X, c.Y, cx, cy, r)
    c.paint(cov(d), INK)
    gold_bevel(c, d, 0.8, 3.2)
    c.paint(cov(d + 3.2), c.vgrad([(0, hexc("#1f5a5f")), (1, hexc("#08191e"))], cy - r, cy + r))
    c.paint(cov(d + 3.2) * np.clip((cy - c.Y) / r, 0, 1), WHITE * np.array([1, 1, 1, 0.1]))
    k = r * 0.42
    x = np.minimum(sd_segment(c.X, c.Y, cx - k, cy - k, cx + k, cy + k, 3.2), sd_segment(c.X, c.Y, cx + k, cy - k, cx - k, cy + k, 3.2))
    c.paint(cov(x - 1.0) * 0.6, INK)
    c.paint(cov(x), c.vgrad([(0, GOLD_HI), (1, GOLD)], cy - k, cy + k))
    return c


def capsule(w, h, r, fill_top, fill_bot, gold_w=1.5, jade_line=0.35, alpha=1.0, shadow=False, top_accent=False):
    c = Canvas(w, h)
    x0, y0, x1, y1 = 1.0, 1.0, w - 1.0, h - (3.0 if shadow else 1.0)
    if shadow:
        drop_shadow(c, x0, y0, x1, y1, r, dy=2.0, blur=3.0, alpha=0.45)
    d = sd_rrect(c.X, c.Y, x0, y0, x1, y1, r)
    c.paint(cov(d), c.vgrad([(0, fill_top * np.array([1, 1, 1, alpha])), (1, fill_bot * np.array([1, 1, 1, alpha]))], y0, y1))
    c.paint(band(d, 0.0, 0.8), INK)
    gold_bevel(c, d, 0.8, 0.8 + gold_w)
    if jade_line > 0:
        c.paint(band(d, gold_w + 1.8, gold_w + 2.5), JADE * np.array([1, 1, 1, jade_line]))
    if top_accent:
        c.paint(cov(sd_rrect(c.X, c.Y, r, y0 + 2.4, w - r, y0 + 4.0, 0.8)), c.vgrad([(0, GOLD_HI), (1, GOLD)], y0 + 2.4, y0 + 4.0))
    return c


def dialogue_box(w, h):
    c = Canvas(w, h)
    drop_shadow(c, 1, 1, w - 1, h - 3, 5, dy=2.0, blur=3.0, alpha=0.5)
    d = sd_rrect(c.X, c.Y, 1, 1, w - 1, h - 3, 5)
    c.paint(cov(d), c.vgrad([(0, PAPER_TOP), (1, PAPER_BOT)], 1, h - 3))
    c.paint(band(d, 0.0, 1.4), BROWN)
    c.paint(band(d, 1.4, 3.6), c.vgrad([(0, hexc("#d7a95b")), (1, hexc("#8a5e2b"))]))
    c.paint(band(d, 3.6, 4.2), BROWN * np.array([1, 1, 1, 0.7]))
    c.paint(band(d, 7.0, 7.6), BROWN * np.array([1, 1, 1, 0.35]))
    corner_brackets(c, 7.5, 10.0, 1.3, 2.2, color=hexc("#8a5e2b"), jade=False)
    return c


def minimap_frame(w, h):
    c = Canvas(w, h)
    d = sd_rrect(c.X, c.Y, 0, 0, w, h, 3)
    c.paint(cov(d), c.vgrad([(0, hexc("#0a2027", 0.94)), (1, hexc("#071a1f", 0.94))]))
    head = cov(np.maximum(d + 2.0, c.Y - 21.0))
    c.paint(head, c.vgrad([(0, hexc("#1a4a4f")), (1, hexc("#0f3238"))], 2, 21))
    c.paint(cov(sd_rrect(c.X, c.Y, 3, 21.0, w - 3, 22.4, 0.3)), c.vgrad([(0, GOLD_HI), (1, GOLD)], 21, 22.4))
    c.paint(cov(sd_rrect(c.X, c.Y, 4, 23.4, w - 4, 24.0, 0.2)), JADE * np.array([1, 1, 1, 0.45]))
    c.paint(band(d, 0.0, 1.0), INK)
    gold_bevel(c, d, 1.0, 2.6)
    for x, y in ((4.5, 4.5), (w - 4.5, 4.5), (4.5, h - 4.5), (w - 4.5, h - 4.5)):
        gem(c, x, y, 2.0)
    return c


def bar_shell(w, h):
    c = Canvas(w, h)
    d = sd_rrect(c.X, c.Y, 0.5, 0.5, w - 0.5, h - 0.5, 5)
    c.paint(cov(d), c.vgrad([(0, hexc("#030b0e")), (1, hexc("#0a1d22"))]))
    c.paint(band(d, 0.0, 1.0), INK)
    gold_bevel(c, d, 1.0, 2.2)
    c.paint(cov(d + 2.2) * np.clip(1.0 - (c.Y - 2.5) / 4.0, 0, 1), INK * np.array([1, 1, 1, 0.5]))
    return c


def ink_band(w, h):
    """P6 moments: one dry-brush stroke of ink (the band a breakthrough's name is written on, mockup 05). The stroke is
    48 bristle lines: pressed round at the head, solid through the stretchable middle (the same in every column, so it
    stretches sideways), and dry at the tail, where each bristle runs out at its own place and a few drops fall."""
    c = Canvas(w, h)
    rng = np.random.default_rng(605)
    n, mid, half = 48, h * 0.5, h * 0.42
    cov_all = np.zeros(c.X.shape)
    for i, v in enumerate(np.linspace(-1.0, 1.0, n)):
        v = float(np.clip(v + rng.uniform(-0.015, 0.015), -1.0, 1.0))
        y = mid + half * v + (1.0 - abs(v)) * 2.0          # the stroke sags a little at its heart
        edge = abs(v) > 0.72
        thick = half / n * (rng.uniform(0.5, 1.2) if edge else rng.uniform(1.5, 2.0))
        alpha = rng.uniform(0.3, 0.8) if edge else rng.uniform(0.93, 1.0)
        start = 8.0 + 72.0 * (1.0 - math.sqrt(max(0.0, 1.0 - v * v))) + rng.uniform(0.0, 8.0)
        end = w - 12.0 - (40.0 * abs(v) ** 1.5 + rng.uniform(0.0, 60.0))
        dry = rng.uniform(14.0, 38.0)
        across = np.clip(0.5 - (np.abs(c.Y - y) - thick) * K, 0.0, 1.0)
        along = np.clip((c.X - start) / 3.0, 0.0, 1.0) * np.clip((end - c.X) / dry, 0.0, 1.0) ** 0.6
        cov_all = np.maximum(cov_all, alpha * across * along)
    for dx, dy, r in ((w - 22.0, mid - half * 0.62, 3.0), (w - 10.0, mid + half * 0.3, 1.8), (w - 34.0, mid + half * 0.98, 2.2)):
        cov_all = np.maximum(cov_all, cov(sd_circle(c.X, c.Y, dx, dy, r)) * 0.8)
    c.paint(cov_all, INK)
    return c


HUD_RING_PAD = 14.0  # px round the ring's face for the drop shadow and the active halo


def hud_ring(size: int, state: str):
    """A HUD button (P4, docs/ui_style_guide.md §5): a jade-enamel face `size` px across with a vertical sheen, a thin
    gold bezel, an inner jade line and a gloss arc; `active` lights the bezel and adds a soft gold halo, `pressed`
    sinks the face a pixel and dims its gloss. The art is the face plus HUD_RING_PAD on each side; hud.gd ring() scales
    it to the radius it draws."""
    w = size + 2 * HUD_RING_PAD
    c = Canvas(w, w)
    cx = cy = w / 2
    r = size / 2
    lit, pressed = state == "active", state == "pressed"
    if pressed:
        cy += 1.0
    c.paint(cov(sd_circle(c.X, c.Y, cx, cy + (3.0 if pressed else 4.0), r + 4.0)), INK * np.array([1, 1, 1, 0.42]))
    if lit:
        for i in range(3):
            c.paint(cov(np.abs(sd_circle(c.X, c.Y, cx, cy, r + 5.0 + i * 3.0)) - 1.5), GOLD * np.array([1, 1, 1, 0.30 - i * 0.09]))
    rim_top, rim_bot = (hexc("#f0d08a"), hexc("#7a5426")) if lit else (hexc("#c6a262"), hexc("#5c4424"))
    rim = sd_circle(c.X, c.Y, cx, cy, r + 2.5)
    c.paint(cov(rim), c.vgrad([(0, rim_top), (1, rim_bot)], cy - r - 2.5, cy + r + 2.5))
    c.paint(band(rim, 0.0, 1.0), rim_bot * 0.7 + rim_top * 0.3)
    face = sd_circle(c.X, c.Y, cx, cy, r)
    face_top, face_bot = (hexc("#17454b"), hexc("#041013")) if pressed else (hexc("#1d5157"), hexc("#061519"))
    c.paint(cov(face), c.vgrad([(0, face_top), (1, face_bot)], cy - r, cy + r))
    c.paint(cov(np.abs(sd_circle(c.X, c.Y, cx, cy, r - 3.5)) - 0.75), JADE_HI * np.array([1, 1, 1, 0.30 if lit else 0.2]))
    gloss = sd_arc(c.X, c.Y, cx, cy, r - 2.0, math.pi * 1.15, math.pi * 1.85, max(2.0, r * 0.07))
    c.paint(cov(gloss), WHITE * np.array([1, 1, 1, 0.06 if pressed else 0.12]))
    return c


# The HUD's ring sizes (face diameters): the attack button, the technique and action rings, the small toggles and the
# item rings. hud.gd picks the nearest and scales it to the radius it draws.
HUD_RING_SIZES = (132, 64, 52, 48)


# ------------------------------------------------------------------ P5 page surfaces (docs/page_identity.md §5, §7)
# Each colour is a UiKit token or a SURFACE mix of two tokens (page_identity §7), so no new hue enters.
TOKEN = {k: hexc(v) for k, v in {"INK": "#071015", "JADE_SHADOW": "#15514f", "JADE": "#2c9e8f", "BRIGHT_JADE": "#67d6bd",
         "BRONZE": "#9a6a35", "GOLD": "#e5b84c", "PALE_GOLD": "#ffe6a1", "BLOOD": "#b3202e", "DEEP_TEAL": "#0d3035"}.items()}


def mix(a, b, t):
    """`a` mixed with `t` of `b` (RGBA arrays), as page_identity §7 writes the SURFACE tokens."""
    return a * (1.0 - t) + b * t


LACQUER_S = mix(TOKEN["BLOOD"], TOKEN["INK"], 0.55)        # SURFACE.lacquer #541720
SPACE_S = mix(TOKEN["DEEP_TEAL"], TOKEN["INK"], 0.55)      # SURFACE.space #0a1e23
SKY_S = mix(TOKEN["JADE_SHADOW"], TOKEN["INK"], 0.58)      # SURFACE.sky #0d2b2d


def jade_tag(w, h, faces, gold=False, shadow=True):
    """A jade slip-tag (the Character page's tabs and title): square-ish top, rounder foot, a lit top edge; the title's
    tag carries a gold inlay."""
    c = Canvas(w, h)
    y1 = h - (3.0 if shadow else 1.0)
    top = sd_rrect(c.X, c.Y, 1.0, 1.0, w - 1.0, y1, 3.0)
    foot = sd_rrect(c.X, c.Y, 1.0, 1.0, w - 1.0, y1, 10.0)
    d = np.where(c.Y < h * 0.5, top, foot)
    if shadow:
        c.paint(soft(np.maximum(d, 0), 3.0) * (d > 0) * 0.4 * (c.Y > y1 - 9.0), TOKEN["INK"])
    c.paint(cov(d), c.vgrad(faces, 1.0, y1))
    c.paint(band(d, 0.0, 1.4), TOKEN["INK"])
    if gold:
        c.paint(band(d, 1.4, 3.4), c.vgrad([(0, TOKEN["PALE_GOLD"]), (0.5, TOKEN["GOLD"]), (1, TOKEN["BRONZE"])], 1.0, y1))
    else:
        c.paint(band(d, 1.4, 2.4) * (c.Y < 5.0), TOKEN["BRIGHT_JADE"] * np.array([1, 1, 1, 0.35]))
    return c


def _chamfered(c, x0, y0, x1, y1, cut):
    """A rectangle with its four corners cut at 45 degrees (a lacquered tablet's outline)."""
    box = sd_rrect(c.X, c.Y, x0, y0, x1, y1, 1.0)
    corner = np.minimum(c.X - x0, x1 - c.X) + np.minimum(c.Y - y0, y1 - c.Y) - cut
    return np.maximum(box, -corner / math.sqrt(2))


def honour_tablet(w, h, worn=False):
    """A title as an honour (decision 16): a red lacquer tablet with cut corners, a gold inlay line and a gloss; the worn
    title's tablet in a gilded frame with a stud at each corner."""
    c = Canvas(w, h)
    y1 = h - 3.0
    d = _chamfered(c, 1.0, 1.0, w - 1.0, y1, 5.0)
    c.paint(soft(np.maximum(d, 0), 2.5) * (d > 0) * 0.5 * (c.Y > 4.0), TOKEN["INK"])
    face = [(0, mix(LACQUER_S, TOKEN["BLOOD"], 0.2 if worn else 0.12)), (0.55, LACQUER_S), (1, mix(LACQUER_S, TOKEN["INK"], 0.3))]
    c.paint(cov(d), c.vgrad(face, 1.0, y1))
    c.paint(cov(d + 3.0) * np.clip((h * 0.4 - c.Y) / (h * 0.4), 0, 1) ** 1.6, TOKEN["PALE_GOLD"] * np.array([1, 1, 1, 0.08]))
    c.paint(band(d, 0.0, 1.0), TOKEN["INK"])
    if worn:
        gold_bevel(c, d, 1.0, 4.2)
        c.paint(band(d, 4.2, 5.0), TOKEN["INK"] * np.array([1, 1, 1, 0.6]))
        for x, y in ((6.0, 6.0), (w - 6.0, 6.0), (6.0, y1 - 5.0), (w - 6.0, y1 - 5.0)):
            gem(c, x, y, 2.2, jade=False)
    else:
        c.paint(band(d, 3.0, 3.8), TOKEN["GOLD"] * np.array([1, 1, 1, 0.75]))
    return c


def sky_token(selected=False):
    """A token floating in the Bag's sky (decision 24: its tabs, kinds and Key Pouch): a pill of the gourd's night, see-
    through, ringed in jade and lit along its top; the chosen one glows jade inside a gold ring. 56 x 48, the ends round."""
    c = Canvas(56, 48)
    d = sd_rrect(c.X, c.Y, 1.0, 1.0, 55.0, 47.0, 23.0)
    if selected:
        c.paint(cov(d), c.vgrad([(0, TOKEN["JADE"] * np.array([1, 1, 1, 0.55])), (1, TOKEN["JADE_SHADOW"] * np.array([1, 1, 1, 0.8]))], 1.0, 47.0))
        c.paint(band(d, 0.0, 1.6), TOKEN["GOLD"])
    else:
        c.paint(cov(d), SPACE_S * np.array([1, 1, 1, 0.8]))
        c.paint(band(d, 0.0, 1.0), TOKEN["BRIGHT_JADE"] * np.array([1, 1, 1, 0.45]))
    c.paint(band(d, 1.6, 2.6) * (c.Y < 8.0), TOKEN["PALE_GOLD"] * np.array([1, 1, 1, 0.1]))
    return c


def sky_card():
    """The Bag's item card (decision 15, a small card for a chosen thing): a slip of the sky's own dark jade, ringed in
    bright jade with a faint gold line inside."""
    c = Canvas(48, 48)
    d = sd_rrect(c.X, c.Y, 1.0, 1.0, 47.0, 47.0, 10.0)
    c.paint(cov(d), c.vgrad([(0, SKY_S), (1, SPACE_S)], 1.0, 47.0))
    c.paint(band(d, 0.0, 1.5), TOKEN["BRIGHT_JADE"] * np.array([1, 1, 1, 0.65]))
    c.paint(band(d, 2.5, 3.3), TOKEN["PALE_GOLD"] * np.array([1, 1, 1, 0.12]))
    return c


CLOTH_S = mix(TOKEN["JADE_SHADOW"], TOKEN["INK"], 0.45)    # SURFACE.cloth #0f3435


def carved_panel(frame_only=False):
    """The Techniques page's panels (P13b, mockup 06): carved jade-teal with an ink edge, a jade band, a gold hairline and
    a gold fitting in each corner (a leg with a curl and a gem). `frame_only` leaves the inside clear, so the chart
    drawn under it shows through and only its rim is laid over the chart's edge."""
    c = Canvas(64, 64)
    d = sd_rrect(c.X, c.Y, 1.0, 1.0, 63.0, 63.0, 6.0)
    if not frame_only:
        c.paint(cov(d), c.vgrad([(0, CLOTH_S), (0.6, mix(CLOTH_S, SPACE_S, 0.6)), (1, SPACE_S)], 1.0, 63.0))
    c.paint(band(d, 0.0, 1.0), TOKEN["INK"])
    c.paint(band(d, 1.0, 3.0), TOKEN["JADE_SHADOW"])
    c.paint(band(d, 3.0, 4.0), TOKEN["GOLD"] * np.array([1, 1, 1, 0.85]))
    c.paint(band(d, 4.0, 5.0), TOKEN["INK"])
    corner_brackets(c, 3.0, 14.0, 2.2, 2.4, curl=3.0)
    return c


# The seals along the Techniques page's rail (P13b): an element's glyph in its own colour on a dark disc ringed in it;
# the colours are the element colours of data/elements.json (the emblems' too). Glyphs are drawn in a 24-unit square.
SEAL_COLOURS = {**json.load(open(os.path.join(ROOT, "data", "elements.json"), encoding="utf-8"))["colors"], "formless": "#e8e1cf",
                "lost": "#e8e1cf", "secret": "#afc9d1"}
SEAL_COLOURS["time"] = SEAL_COLOURS["ice"]


def _lens(X, Y, cx, cy, ang, length, width):
    u = (X - cx) * math.cos(ang) + (Y - cy) * math.sin(ang)
    v = -(X - cx) * math.sin(ang) + (Y - cy) * math.cos(ang)
    r = (length * length / 4.0 + width * width / 4.0) / width
    off = r - width / 2.0
    return np.maximum(np.hypot(u - off, v) - r, np.hypot(u + off, v) - r)


def _glyph(X, Y, g):
    """Glyph `g` as a distance field in units of a 24-unit square centred on 0 (y down)."""
    seg = lambda pts, w: np.minimum.reduce([sd_segment(X, Y, *a, *b, w) for a, b in zip(pts, pts[1:])])
    if g == "wood":
        return np.minimum.reduce([seg([(0, 10), (0, 1), (-7, -7)], 2.2), seg([(0, 1), (7, -8)], 2.2),
                                  _lens(X, Y, -5, -4, 0.8, 9, 4.5), _lens(X, Y, 5, -5, -0.8, 9, 4.5)])
    if g == "fire":
        return np.minimum(sd_circle(X, Y, 0, 4.5, 6.0), _lens(X, Y, 0, -2, 0.0, 20, 9))
    if g == "earth":
        return seg([(-11, 9), (-4, -4), (0, 2), (5, -8), (12, 9), (-11, 9)], 2.4)
    if g == "metal":
        return np.minimum(np.abs(sd_circle(X, Y, 0, 0, 9.5)) - 1.4, np.abs(sd_rrect(X, Y, -3.5, -3.5, 3.5, 3.5, 0.5)) - 1.2)
    if g == "water":
        waves = [np.abs(Y - y0 - 1.8 * np.sin(X * 0.62)) - 1.2 for y0 in (-5.0, 1.0, 7.0)]
        return np.maximum(np.minimum.reduce(waves), np.abs(X) - 11.0)
    if g == "wind":
        return np.minimum.reduce([seg([(-11, -3), (4, -3)], 2.2), sd_arc(X, Y, 4, -7, 4, -math.pi, math.pi / 2, 2.2),
                                  seg([(-11, 3), (6, 3)], 2.2), sd_arc(X, Y, 6, 7, 4, -math.pi / 2, math.pi, 2.2), seg([(-9, 9), (-2, 9)], 2.2)])
    if g == "thunder":
        return seg([(4, -12), (-6, 1), (1, 1), (-4, 12)], 2.8)
    if g == "soul":
        return np.minimum.reduce([seg([(-5, -9), (5, -9)], 2.0), seg([(0, -12), (0, -9)], 2.0), sd_arc(X, Y, 0, 0, 8, -0.35, math.pi + 0.35, 2.2),
                                  _lens(X, Y, 0, 1.5, 0.0, 9, 5)])
    if g == "formless":
        return sd_arc(X, Y, 0, 0, 10, -0.9, math.pi * 1.55, 3.0)
    if g == "space":
        a = math.radians(-25)
        u = X * math.cos(a) + Y * math.sin(a)
        v = -X * math.sin(a) + Y * math.cos(a)
        ring = (np.hypot(u / 11.0, v / 5.0) - 1.0) * 4.5
        return np.minimum.reduce([np.abs(ring) - 1.1, sd_circle(X, Y, 0, 0, 3.8), sd_circle(X, Y, 9, -6, 1.8)])
    if g == "time":
        return np.minimum(seg([(-7, -10), (7, -10), (-6, 10), (6, 10), (-7, 10)], 2.2), seg([(-7, -10), (6, 10)], 2.2))
    if g == "lost":
        return np.minimum.reduce([np.abs(sd_rrect(X, Y, -8, -11, 8, 11, 1.5)) - 1.2] + [seg([(-4.5, y), (4.5, y)], 1.5) for y in (-5, -1, 3, 7)])
    # secret: two footprints stepping up to the right, and their toes
    return np.minimum.reduce([_lens(X, Y, -5, 3, 0.35, 11, 5.5), _lens(X, Y, 5, -3, 0.2, 11, 5.5), sd_circle(X, Y, -7, -5.5, 1.6), sd_circle(X, Y, 3, -11, 1.6)])


def tech_seal(g):
    """A seal on the Techniques rail, 44 px: a dark disc lit at the top left, ringed in the element's colour and ink, its
    glyph in that colour with an ink edge."""
    c = Canvas(44, 44)
    col = hexc(SEAL_COLOURS[g])
    d = sd_circle(c.X, c.Y, 22, 22, 19.0)
    c.paint(cov(sd_circle(c.X, c.Y, 22, 22, 21.0)), TOKEN["INK"])
    c.paint(cov(d + 0.0), col)
    body = d + 2.0
    shade = np.clip(np.hypot(c.X - 18, c.Y - 17) / 22.0, 0, 1)[..., None]
    c.paint(cov(body), mix(TOKEN["DEEP_TEAL"], col, 0.12) * (1 - shade) + TOKEN["INK"] * shade)
    gl = _glyph((c.X - 22) / 0.86, (c.Y - 22) / 0.86, g) * 0.86
    c.paint(cov(gl - 1.1), TOKEN["INK"])
    c.paint(cov(gl), col)
    return c


# The Records family's paper (docs/page_identity.md §2, §5): the Quests' slips, the Mail's envelopes and letter, the
# Notice Board's posters. `scroll` and its edge, PAPER and PAPER_INK are UiKit tokens; each face is lit from above and
# its ornaments stay inside the corner squares (the edge check), so the torn tops and folds are drawn by the pages.
SCROLL_T = hexc("#e8dcbc")                                  # SURFACE.scroll
SCROLL_EDGE_T = hexc("#d9ccaa")                             # SURFACE.scroll_edge
PAPER_T = hexc("#e8e1cf")                                   # PAPER
PAPER_INK_T = hexc("#2b2118")                               # PAPER_INK
PAPER_LIT = mix(SCROLL_T, PAPER_T, 0.5)                     # the paper where the light falls


def paper_face(w, h, r, lit, shade, edge_alpha=0.55, shadow=2.0):
    """A sheet of paper: a soft ink shadow under it, lit from above, a fine bronze edge and a darker rim inside it."""
    c = Canvas(w, h)
    y1 = h - shadow - 1.0
    d = sd_rrect(c.X, c.Y, 1.0, 1.0, w - 1.0, y1, r)
    if shadow > 0:
        c.paint(soft(np.maximum(sd_rrect(c.X, c.Y, 1.0, 1.0 + shadow, w - 1.0, y1 + shadow, r), 0), 2.5) * (d > 0) * 0.45, TOKEN["INK"])
    c.paint(cov(d), c.vgrad([(0, lit), (0.7, SCROLL_T), (1, shade)], 1.0, y1))
    c.paint(band(d, 0.0, 1.0), TOKEN["BRONZE"] * np.array([1, 1, 1, edge_alpha]))
    c.paint(band(d, 1.0, 3.5), SCROLL_EDGE_T * np.array([1, 1, 1, 0.35]))
    return c, d


def paper_slip():
    """A mission slip (the Quests board): paper whose top is torn off the pad (the page draws the teeth above it), lit
    from above; the slips cast a shadow onto the board."""
    c, _ = paper_face(48, 48, 1.5, PAPER_LIT, SCROLL_EDGE_T)
    return c


def envelope(state):
    """A letter in its envelope (the Mail's stack): the flap's fold across the top, a darker pocket seam in each lower
    corner; the chosen one's edge lit in pale gold."""
    c, d = paper_face(48, 48, 2.0, PAPER_LIT, mix(SCROLL_T, SCROLL_EDGE_T, 0.8))
    c.paint(cov(sd_rrect(c.X, c.Y, 1.0, 1.0, 47.0, 7.0, 1.0)) * cov(d), mix(SCROLL_EDGE_T, TOKEN["BRONZE"], 0.25) * np.array([1, 1, 1, 0.35]))
    c.paint(cov(np.abs(c.Y - 7.5) - 0.4) * cov(d + 1.0), TOKEN["BRONZE"] * np.array([1, 1, 1, 0.45]))
    for x0, sx in ((1.0, 1.0), (47.0, -1.0)):
        seam = np.abs((c.X - x0) * sx - (45.0 - c.Y)) / math.sqrt(2) - 0.35
        c.paint(cov(seam) * (c.Y > 37.0) * cov(d + 1.0), TOKEN["BRONZE"] * np.array([1, 1, 1, 0.3]))
    if state == "selected":
        c.paint(band(d, 0.0, 2.2), TOKEN["PALE_GOLD"])
    return c


def letter_sheet():
    """The open letter (the Mail's desk): a larger sheet, the light pooled in its middle and the corners a little
    darker, as unfolded paper lies; the page draws the two fold creases over it."""
    c, d = paper_face(64, 64, 1.5, PAPER_LIT, SCROLL_EDGE_T, shadow=3.0)
    for x, y in ((1.0, 1.0), (63.0, 1.0), (1.0, 60.0), (63.0, 60.0)):
        c.paint(np.clip(1.0 - np.hypot(c.X - x, c.Y - y) / 14.0, 0, 1) ** 2 * cov(d), TOKEN["BRONZE"] * np.array([1, 1, 1, 0.16]))
    return c


def poster():
    """A wanted poster pasted on the town wall (the Notice Board): paper with paste stains in its corners, its top right
    corner torn away and its lower left corner curling off the brick."""
    c = Canvas(64, 64)
    y1 = 61.0
    # The torn top right corner: a ragged diagonal, all of it inside the corner square.
    tear = (c.X - 51.0) - c.Y + 1.1 * np.sin(c.Y * 2.3) + 0.7 * np.sin(c.Y * 5.1 + 1.0)
    d = np.maximum(sd_rrect(c.X, c.Y, 1.0, 1.0, 63.0, y1, 1.0), tear)
    lifted = np.maximum(sd_rrect(c.X, c.Y, 2.0, 3.0, 63.0, y1 + 2.0, 1.0), tear + 2.0)
    c.paint(soft(np.maximum(lifted, 0), 2.5) * (d > 0) * 0.4, TOKEN["INK"])
    c.paint(cov(d), c.vgrad([(0, PAPER_LIT), (0.6, SCROLL_T), (1, mix(SCROLL_T, SCROLL_EDGE_T, 0.9))], 1.0, y1))
    for x, y, r in ((8.0, 9.0, 7.0), (55.0, 53.0, 8.0), (10.0, 52.0, 5.0)):   # paste stains
        c.paint(np.clip(1.0 - np.hypot(c.X - x, c.Y - y) / r, 0, 1) ** 1.5 * cov(d), TOKEN["BRONZE"] * np.array([1, 1, 1, 0.18]))
    c.paint(band(d, 0.0, 1.0), TOKEN["BRONZE"] * np.array([1, 1, 1, 0.5]))
    # The curl at the lower left: a lifted triangle, its underside darker.
    curl = (c.X - 1.0) + (y1 - c.Y) - 12.0
    under = cov(curl) * cov(d)
    c.paint(under, mix(SCROLL_EDGE_T, TOKEN["BRONZE"], 0.35))
    c.paint(cov(np.abs(curl) - 0.5) * cov(d), TOKEN["BRONZE"] * np.array([1, 1, 1, 0.6]))
    return c


# The honours' motifs, one a stat family (character_page.gd MOTIF): each a gilt boss with its sign sunk in lacquer.
MOTIFS = ("blade", "shield", "pearl", "cloud", "peak", "lotus", "coin", "cauldron", "star")


def _motif(X, Y, m):
    """The sign of motif `m` as a distance field in a 32 px boss centred on (16, 16)."""
    seg = lambda ax, ay, bx, by, wd: sd_segment(X, Y, ax, ay, bx, by, wd)

    def lens(cx, cy, ang, length, width):
        # A petal or a flame: the lens where two circles overlap, `length` tall and `width` wide, turned by `ang`.
        u = (X - cx) * math.cos(ang) + (Y - cy) * math.sin(ang)
        v = -(X - cx) * math.sin(ang) + (Y - cy) * math.cos(ang)
        r = (length * length / 4.0 + width * width / 4.0) / width
        off = r - width / 2.0
        return np.maximum(np.hypot(u - off, v) - r, np.hypot(u + off, v) - r)

    if m == "blade":
        return np.minimum.reduce([seg(16, 6, 16, 19, 3.2), seg(11, 19.5, 21, 19.5, 2.4), seg(16, 20, 16, 25, 2.2), sd_circle(X, Y, 16, 26.5, 1.7)])
    if m == "shield":
        top = sd_rrect(X, Y, 10, 7, 22, 16, 2.0)
        point = np.maximum(sd_diamond(X, Y, 16, 16, 10.0), np.abs(X - 16) - 6.0)
        return np.maximum(np.minimum(top, point), -(np.abs(X - 16) - 0.7))
    if m == "pearl":
        # The flaming pearl: a pearl with its lit crescent, and a flame rising from it.
        return np.minimum(np.maximum(sd_circle(X, Y, 16, 19.5, 5.8), -sd_circle(X, Y, 14.2, 17.6, 2.2)), lens(16, 10.5, 0.0, 9.0, 4.2))
    if m == "cloud":
        blob = np.minimum.reduce([sd_circle(X, Y, 11.5, 18, 4.0), sd_circle(X, Y, 16.5, 14.5, 5.0), sd_circle(X, Y, 21, 18.5, 3.6), sd_rrect(X, Y, 9, 18, 23, 22, 2.0)])
        return np.maximum(blob, -(np.abs(sd_circle(X, Y, 16.5, 15, 2.4)) - 0.7))
    if m == "peak":
        return np.minimum.reduce([seg(7, 23, 12, 13, 2.4), seg(12, 13, 15.5, 18, 2.4), seg(15.5, 18, 20, 9, 2.4), seg(20, 9, 25, 23, 2.4), seg(7, 23.5, 25, 23.5, 2.0)])
    if m == "lotus":
        return np.minimum.reduce([lens(16, 15.5, 0.0, 13.0, 6.0), lens(11.0, 17.5, -0.75, 11.0, 5.0), lens(21.0, 17.5, 0.75, 11.0, 5.0),
                                  seg(8.5, 23.5, 23.5, 23.5, 2.0)])
    if m == "coin":
        return np.maximum(sd_circle(X, Y, 16, 16, 8.5), -sd_rrect(X, Y, 13, 13, 19, 19, 0.8))
    if m == "cauldron":
        return np.minimum.reduce([sd_rrect(X, Y, 9.5, 13, 22.5, 21.5, 3.0), seg(9, 12.5, 23, 12.5, 2.0), seg(11.5, 21, 10.5, 25, 2.0), seg(20.5, 21, 21.5, 25, 2.0),
                                  np.abs(sd_circle(X, Y, 11, 10, 2.2)) - 0.8, np.abs(sd_circle(X, Y, 21, 10, 2.2)) - 0.8])
    # star: a four-pointed sparkle and a small one beside it.
    arm = lambda cx, cy, a, b: (np.abs(X - cx) / a + np.abs(Y - cy) / b - 1.0) * min(a, b) * 0.7
    return np.minimum.reduce([arm(15, 16, 2.6, 9.0), arm(15, 16, 9.0, 2.6), arm(22.5, 9.5, 1.2, 3.4), arm(22.5, 9.5, 3.4, 1.2)])


def honour_seal(motif):
    """A title's motif on a gilt boss, 32 px: a gold disc lit from above, an ink ring, the sign sunk in dark lacquer."""
    c = Canvas(32, 32)
    d = sd_circle(c.X, c.Y, 16, 16.5, 14.5)
    c.paint(cov(sd_circle(c.X, c.Y, 16, 17.5, 14.5)), TOKEN["INK"] * np.array([1, 1, 1, 0.6]))
    c.paint(cov(d), c.vgrad([(0, TOKEN["PALE_GOLD"]), (0.45, TOKEN["GOLD"]), (1, TOKEN["BRONZE"])], 2, 31))
    c.paint(band(d, 0.0, 1.0), TOKEN["INK"])
    c.paint(cov(np.abs(d + 3.0) - 0.45), TOKEN["BRONZE"] * np.array([1, 1, 1, 0.8]))
    sign = _motif(c.X, c.Y, motif)
    c.paint(cov(sign - 0.8), TOKEN["PALE_GOLD"] * np.array([1, 1, 1, 0.55]))
    c.paint(cov(sign), c.vgrad([(0, mix(LACQUER_S, TOKEN["INK"], 0.2)), (1, LACQUER_S)], 6, 27))
    return c


# The Market family (P5, docs/page_identity.md §2: brass fittings and paper price tags on trade timber and black lacquer).
TOKEN.update({k: hexc(v) for k, v in {"WOOD": "#5a3620", "WOOD_DARK": "#3b2416"}.items()})
LACQUER_BLACK_S = mix(TOKEN["INK"], TOKEN["BRONZE"], 0.10)   # SURFACE.lacquer_black #161918


def market_plate():
    """A trader's sign board (the Shop's name over the awning, the County Hall's plaque): black lacquer with a gloss,
    framed in a bevelled brass fillet, a brass stud in each corner."""
    c = Canvas(64, 56)
    d = sd_rrect(c.X, c.Y, 1.0, 1.0, 63.0, 53.0, 5.0)
    c.paint(soft(np.maximum(sd_rrect(c.X, c.Y, 1.0, 3.0, 63.0, 55.0, 5.0), 0), 2.0) * 0.5, TOKEN["INK"])
    face = [(0, mix(LACQUER_BLACK_S, TOKEN["BRONZE"], 0.14)), (0.45, LACQUER_BLACK_S), (1, mix(LACQUER_BLACK_S, TOKEN["INK"], 0.4))]
    c.paint(cov(d), c.vgrad(face, 1.0, 53.0))
    c.paint(band(d, 0.0, 1.0), TOKEN["INK"])
    gold_bevel(c, d, 1.0, 4.0)
    c.paint(band(d, 4.0, 5.0), TOKEN["INK"] * np.array([1, 1, 1, 0.7]))
    for x, y in ((9.0, 9.0), (55.0, 9.0), (9.0, 45.0), (55.0, 45.0)):
        c.paint(cov(sd_circle(c.X, c.Y, x, y + 0.6, 2.6)), TOKEN["INK"] * np.array([1, 1, 1, 0.6]))
        c.paint(cov(sd_circle(c.X, c.Y, x, y, 2.4)), c.vgrad([(0, TOKEN["PALE_GOLD"]), (1, TOKEN["BRONZE"])], y - 2.4, y + 2.4))
    return c


def storehouse_lid(w=760, h=184):
    """The Storage page's chest lid thrown open (row 19): the raised lid in perspective, its far edge narrower, a camphor
    rim bound in bronze at the corners and hinges, the red lacquer lining inside framed by a gold line."""
    c = Canvas(w, h)
    inset, y0, y1 = 30.0, 4.0, h - 6.0

    def trap(pad):
        # The lid's outline shrunk by `pad` px: the far edge at the top, the hinge edge at the foot.
        t = np.clip((c.Y - y0) / (y1 - y0), 0.0, 1.0)
        half = (w / 2 - 2.0) - inset * (1.0 - t) - pad
        side = np.abs(c.X - w / 2) - half
        return np.maximum(side, np.maximum(y0 + pad - c.Y, c.Y - (y1 - pad)))

    outer = trap(0.0)
    c.paint(cov(outer), c.vgrad([(0, mix(TOKEN["WOOD"], TOKEN["BRONZE"], 0.25)), (0.5, TOKEN["WOOD"]), (1, TOKEN["WOOD_DARK"])], y0, y1))
    for i in range(1, 7):   # the camphor's grain along the rim
        c.paint(band(trap(i * 2.6), 0.0, 0.5) * 0.25, TOKEN["WOOD_DARK"])
    c.paint(band(outer, 0.0, 1.2), TOKEN["INK"])
    lining = trap(20.0)
    c.paint(cov(lining - 1.5), TOKEN["INK"])
    c.paint(cov(lining), c.vgrad([(0, mix(LACQUER_S, TOKEN["BLOOD"], 0.18)), (0.6, LACQUER_S), (1, mix(LACQUER_S, TOKEN["INK"], 0.35))], y0 + 20, y1 - 20))
    c.paint(band(lining, 7.0, 8.2), TOKEN["GOLD"] * np.array([1, 1, 1, 0.7]))
    c.paint(cov(lining) * np.clip((h * 0.45 - c.Y) / (h * 0.45), 0, 1) ** 2, TOKEN["PALE_GOLD"] * np.array([1, 1, 1, 0.07]))
    # Bronze corner straps on the rim, and the two hinges on the foot.
    for sx in (-1, 1):
        for yy, t in ((y0, 0.0), (y1, 1.0)):
            x = w / 2 + sx * ((w / 2 - 2.0) - inset * (1.0 - t))
            dy = 1 if yy == y0 else -1
            d = np.minimum(sd_segment(c.X, c.Y, x - sx * 3, yy + dy * 3, x - sx * 40, yy + dy * 3, 6.0),
                           sd_segment(c.X, c.Y, x - sx * 3, yy + dy * 3, x - sx * (3 + inset * 0.2), yy + dy * 40, 6.0))
            c.paint(cov(d - 0.6), TOKEN["INK"] * np.array([1, 1, 1, 0.6]))
            c.paint(cov(d), c.vgrad([(0, TOKEN["GOLD"]), (1, TOKEN["BRONZE"])], min(yy, yy + dy * 40), max(yy, yy + dy * 40)))
            for k in (14.0, 30.0):
                c.paint(cov(sd_circle(c.X, c.Y, x - sx * k, yy + dy * 3, 1.6)), TOKEN["PALE_GOLD"])
    for hx in (w * 0.25, w * 0.75):
        d = sd_rrect(c.X, c.Y, hx - 26, y1 - 12, hx + 26, y1 + 3, 3.0)
        c.paint(cov(d - 0.6), TOKEN["INK"] * np.array([1, 1, 1, 0.6]))
        c.paint(cov(d), c.vgrad([(0, TOKEN["GOLD"]), (1, TOKEN["BRONZE"])], y1 - 12, y1 + 3))
        c.paint(cov(sd_rrect(c.X, c.Y, hx - 4, y1 - 12, hx + 4, y1 + 3, 1.5)), mix(TOKEN["BRONZE"], TOKEN["INK"], 0.4))
    return c


# The Bonds family (P5, docs/page_identity.md §2: whitewash and red thread): the Gift page's tray (row 28).
def gift_tray():
    """The gift tray held out over the talk (row 28): red lacquer (SURFACE.lacquer) lit from above with a gloss, a raised
    gold rim bevelled from above, an ink line where the tray's floor drops inside the rim and a lighter lip below it; the
    page sets its compartments in the floor. It casts a shadow onto the scene."""
    c = Canvas(64, 64)
    d = sd_rrect(c.X, c.Y, 1.0, 1.0, 63.0, 60.0, 8.0)
    c.paint(soft(np.maximum(sd_rrect(c.X, c.Y, 1.0, 4.0, 63.0, 63.0, 8.0), 0), 2.5) * 0.55, TOKEN["INK"])
    face = [(0, mix(LACQUER_S, TOKEN["BLOOD"], 0.22)), (0.5, LACQUER_S), (1, mix(LACQUER_S, TOKEN["INK"], 0.3))]
    c.paint(cov(d), c.vgrad(face, 1.0, 60.0))
    c.paint(band(d, 0.0, 1.0), TOKEN["INK"])
    gold_bevel(c, d, 1.0, 4.5)
    c.paint(band(d, 4.5, 5.8), TOKEN["INK"] * np.array([1, 1, 1, 0.75]))
    c.paint(band(d, 5.8, 7.6), mix(LACQUER_S, TOKEN["BLOOD"], 0.4) * np.array([1, 1, 1, 0.7]))
    c.paint(cov(d + 8.0) * np.clip((24.0 - c.Y) / 24.0, 0, 1) ** 2, TOKEN["PALE_GOLD"] * np.array([1, 1, 1, 0.06]))
    return c


ASSETS = {
    # name: (margins, {state: builder})
    "minor_panel": ([12, 12, 12, 12], {"normal": lambda: panel(48, 48)}),
    "major_window": ([32, 32, 32, 32], {"normal": lambda: panel(112, 112, r=5.0, major=True)}),
    "portrait_frame": ([16, 16, 16, 16], {"normal": lambda: panel(48, 48, r=4.0, major=False)}),
    "tooltip": ([10, 10, 10, 10], {"normal": lambda: capsule(40, 40, 5, hexc("#0e2a31"), hexc("#081a1f"), gold_w=1.0, jade_line=0.3)}),
    "button_primary": ([16, 14, 16, 14], {s: (lambda s=s: button(96, 48, s, True)) for s in ("normal", "pressed", "disabled")}),
    "button_secondary": ([14, 12, 14, 12], {s: (lambda s=s: button(80, 42, s, False)) for s in ("normal", "pressed", "disabled")}),
    "tab": ([16, 10, 16, 10], {s: (lambda s=s: tab(64, 40, s)) for s in ("normal", "selected")}),
    "slot": ([8, 8, 8, 8], {s: (lambda s=s: slot(40, 40, s)) for s in ("normal", "selected", "disabled")}),
    "selected_slot_glow": ([12, 12, 12, 12], {"normal": lambda: slot_glow(48, 48)}),
    # No vertical centre: the plaque scales to its rect's height and stretches only sideways.
    "title_plaque": ([48, 26, 48, 26], {"normal": lambda: title_plaque(192, 52)}),
    "close_button": ([0, 0, 0, 0], {s: (lambda s=s: close_button(52, 52, s)) for s in ("normal", "pressed")}),
    "currency_pill": ([20, 10, 20, 10], {"normal": lambda: capsule(80, 36, 10, hexc("#0e2b31"), hexc("#07191e"), gold_w=1.4)}),
    "realm_badge": ([8, 8, 8, 8], {"normal": lambda: capsule(40, 24, 6, hexc("#123a40"), hexc("#0a2227"), gold_w=1.0, jade_line=0.0)}),
    "toast": ([20, 12, 20, 12], {"normal": lambda: capsule(96, 48, 10, hexc("#0e2a31"), hexc("#071a1f"), gold_w=1.0, jade_line=0.4, alpha=0.95, shadow=True, top_accent=True)}),
    "dialogue_box": ([24, 24, 24, 24], {"normal": lambda: dialogue_box(128, 96)}),
    "minimap_frame": ([24, 24, 24, 24], {"normal": lambda: minimap_frame(96, 72)}),
    "bar_shell": ([10, 8, 10, 8], {"normal": lambda: bar_shell(64, 24)}),
    # P6 moments: the ink band; its caps cover its full height, so it scales to its rect's height and stretches sideways.
    "ink_band": ([120, 60, 120, 60], {"normal": lambda: ink_band(360, 120)}),
}
for _size in HUD_RING_SIZES:
    ASSETS["hud_ring_%d" % _size] = ([0, 0, 0, 0], {s: (lambda s=s, z=_size: hud_ring(z, s)) for s in ("normal", "pressed", "active")})

# P5 page surfaces (docs/page_identity.md §5): the Character page's jade tags (its tabs and title), its titles as honour
# tablets (the worn one in a gilded frame) and each title's motif on a gilt boss.
ASSETS.update({
    "jade_tag": ([10, 8, 10, 12], {"normal": lambda: jade_tag(48, 48, [(0, mix(TOKEN["JADE_SHADOW"], TOKEN["JADE"], 0.12)), (0.5, TOKEN["JADE_SHADOW"]),
                                                                     (1, mix(TOKEN["JADE_SHADOW"], TOKEN["INK"], 0.25))]),
                                   "selected": lambda: jade_tag(48, 48, [(0, mix(TOKEN["JADE"], TOKEN["BRIGHT_JADE"], 0.15)), (0.45, TOKEN["JADE"]),
                                                                       (1, mix(TOKEN["JADE"], TOKEN["INK"], 0.3))])}),
    "jade_label": ([12, 12, 12, 12], {"normal": lambda: jade_tag(56, 52, [(0, TOKEN["JADE"]), (0.6, mix(TOKEN["JADE"], TOKEN["INK"], 0.3)),
                                                                        (1, TOKEN["JADE_SHADOW"])], gold=True)}),
    "honour_tablet": ([12, 12, 12, 12], {"normal": lambda: honour_tablet(48, 48), "selected": lambda: honour_tablet(48, 48, worn=True)}),
    "honour_seal": ([0, 0, 0, 0], {m: (lambda m=m: honour_seal(m)) for m in MOTIFS}),
    # The Bag's sky (decision 24): the floating tokens (no vertical centre: always 48 tall) and the item card.
    "sky_token": ([24, 24, 24, 24], {"normal": lambda: sky_token(), "selected": lambda: sky_token(True)}),
    "sky_card": ([14, 14, 14, 14], {"normal": lambda: sky_card()}),
    # The Techniques page (P13b): its carved panels (whole, and the rim alone laid over the chart) and the rail's seals.
    "carved_panel": ([22, 22, 22, 22], {"normal": lambda: carved_panel(), "frame": lambda: carved_panel(True)}),
    "tech_seal": ([0, 0, 0, 0], {g: (lambda g=g: tech_seal(g)) for g in ("wood", "fire", "earth", "metal", "water", "wind", "thunder", "soul",
                                                                        "formless", "space", "time", "lost", "secret")}),
    # The Records family (P5): the Quests' slips, the Mail's envelopes (the chosen one lit) and open letter, the Notice
    # Board's posters.
    "paper_slip": ([8, 8, 8, 10], {"normal": lambda: paper_slip()}),
    "envelope": ([10, 10, 10, 16], {"normal": lambda: envelope("normal"), "selected": lambda: envelope("selected")}),
    "letter_sheet": ([18, 18, 18, 18], {"normal": lambda: letter_sheet()}),
    "poster": ([16, 16, 16, 16], {"normal": lambda: poster()}),
    # The Market family (P5): the trader's sign board and the storehouse chest's raised lid.
    "market_plate": ([16, 16, 16, 16], {"normal": lambda: market_plate()}),
    "storehouse_lid": ([0, 0, 0, 0], {"normal": lambda: storehouse_lid()}),
    # The Bonds family (P5): the Gift page's red-lacquered tray.
    "gift_tray": ([16, 16, 16, 16], {"normal": lambda: gift_tray()}),
})


def _check_edges(name, state, img, margins):
    """Nine-slice edges stretch the texels between the corner squares: they must not vary
    along the stretch axis, or an ornament poking out of its corner smears into a streak."""
    if margins == [0, 0, 0, 0]:
        return
    a = np.asarray(img).astype(np.int16)
    ml, mt, mr, mb = [m * K for m in margins]
    h, w = a.shape[:2]
    top = a[:mt, ml:w - mr]
    left = a[mt:h - mb, :ml]
    for part, axis in ((top, 1), (a[h - mb:, ml:w - mr], 1), (left, 0), (a[mt:h - mb, w - mr:], 0)):
        if part.size and np.abs(np.diff(part, axis=axis)).max() > 20 and name not in ("tab",):
            raise SystemExit(f"{name}:{state}: an edge varies along its stretch axis (ornament outside its corner?)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--review", default="", help="write a contact sheet PNG here")
    args = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)
    manifest = {"scale": K}
    sheet_items = []
    for name, (margins, states) in ASSETS.items():
        entry = {"margins": margins}
        for state, build in states.items():
            img = build().image()
            _check_edges(name, state, img, margins)
            path = os.path.join(OUT_DIR, f"{name}__{state}.png")
            img.save(path, format="PNG", optimize=False, compress_level=9)
            entry[state] = f"res://art/ui/hd/{name}__{state}.png"
            sheet_items.append((f"{name}:{state}", img))
        manifest[name] = entry
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")
    if args.review:
        W = 1400
        x = y = row = 0
        sheet = Image.new("RGBA", (W, 1400), (48, 58, 60, 255))
        for _, img in sheet_items:
            im = img if img.width <= 600 else img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
            if x + im.width > W:
                x, y, row = 0, y + row + 12, 0
            sheet.alpha_composite(im, (x, y))
            x += im.width + 12
            row = max(row, im.height)
        sheet.crop((0, 0, W, min(1400, y + row + 12))).save(args.review)
    print("hd ui kit:", len(sheet_items), "images ->", os.path.relpath(OUT_DIR, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
