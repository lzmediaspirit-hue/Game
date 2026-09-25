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
}


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
