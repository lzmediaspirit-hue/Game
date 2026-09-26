#!/usr/bin/env python3
"""Build every prop and tile sheet, data/prop_art.json and review contact sheets.

Usage:  python3 tools/props/build_props.py [--only id1,id2] [--review-dir DIR]
Output is deterministic (byte-identical on re-run).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.dont_write_bytecode = True  # keep the repo free of __pycache__

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from pixlib import SCALE, save_png  # noqa: E402
from registry import PROPS  # noqa: E402
import defs_nature  # noqa: E402,F401
import defs_objects  # noqa: E402,F401
import defs_structures  # noqa: E402,F401
import defs_furniture  # noqa: E402,F401
import defs_tiles  # noqa: E402,F401
import defs_buildings  # noqa: E402,F401
import defs_scenery  # noqa: E402,F401
import defs_treasures  # noqa: E402,F401
import defs_expanse  # noqa: E402,F401
import defs_lantern  # noqa: E402,F401

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_REVIEW = "/tmp/claude-0/-home-user-Game/13461237-7857-505a-bd3b-55d18a20fe2c/scratchpad/art_review"


def render(p):
    """Return (sheet RGBA array, manifest entry, list of per-frame canvases)."""
    frames = []
    states = {}
    col = 0
    for name, n, fps in p["states"]:
        st = {"col": col, "frames": n}
        if n > 1 or fps:
            st["fps"] = fps or 6
        states[name] = st
        for f in range(n):
            cv = p["draw"](name, f)
            assert (cv.w, cv.h) == (p["w"], p["h"]), (p["id"], cv.w, cv.h)
            frames.append(cv)
            col += 1
    opaque = p["kind"] == "tile" and p["extra"].get("opaque", False)
    fw, fh = p["w"] * SCALE, p["h"] * SCALE
    sheet = np.zeros((fh, fw * len(frames), 4), np.uint8)
    for i, cv in enumerate(frames):
        sheet[:, i * fw:(i + 1) * fw] = cv.to_rgba(SCALE, opaque)
    folder = "tiles" if p["kind"] == "tile" else "props"
    if p["anchor"] is not None:
        ax, ay = p["anchor"]
    else:
        ax, ay = p["w"] / 2, p["h"] - p["ground"]
    entry = {"file": f"res://art/{folder}/{p['id']}.png", "frame": [fw, fh],
             "anchor": [int(round(ax * SCALE)), int(round(ay * SCALE))], "states": states}
    if p["kind"] == "tile":
        entry["tile"] = True
    if p["repeat"]:
        entry["repeat"] = p["repeat"]
    for k, v in sorted(p["extra"].items()):
        if k != "opaque":
            entry[k] = v
    return sheet, entry, frames


def label_font():
    try:
        return ImageFont.load_default()
    except Exception:  # pragma: no cover
        return None


def contact_sheet(items, path, bg=(38, 52, 56), zoom=1, cols_px=1800, ground=(92, 72, 48)):
    """items: list of (id, sheet array, entry). Draw each sheet on a panel with its anchor marked."""
    font = label_font()
    pad = 10
    rows = []
    x = pad
    row = []
    row_h = 0
    for pid, sheet, entry in items:
        h, w = sheet.shape[0] * zoom, sheet.shape[1] * zoom
        if x + w + pad > cols_px and row:
            rows.append((row, row_h))
            row, x, row_h = [], pad, 0
        row.append((pid, sheet, entry, x))
        x += w + pad * 2
        row_h = max(row_h, h + 14)
    if row:
        rows.append((row, row_h))
    H = sum(rh + pad for _, rh in rows) + pad
    img = Image.new("RGBA", (cols_px, H), bg + (255,))
    d = ImageDraw.Draw(img)
    y = pad
    for row, rh in rows:
        for pid, sheet, entry, x in row:
            h, w = sheet.shape[0] * zoom, sheet.shape[1] * zoom
            fw = entry["frame"][0] * zoom
            # ground strip under anchor line
            ay = entry["anchor"][1] * zoom
            if not entry.get("tile") and ay < h:
                d.rectangle([x, y + 12 + ay, x + w - 1, y + 12 + h - 1], fill=ground + (255,))
            sh = Image.fromarray(sheet, "RGBA")
            if zoom != 1:
                sh = sh.resize((w, h), Image.NEAREST)
            img.alpha_composite(sh, (x, y + 12))
            for c in range(sheet.shape[1] // entry["frame"][0]):
                d.rectangle([x + c * fw, y + 12, x + (c + 1) * fw - 1, y + 12 + h - 1], outline=(70, 90, 94, 255))
            d.text((x, y), pid, fill=(230, 225, 207, 255), font=font)
        y += rh + pad
    img.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--review-dir", default=DEFAULT_REVIEW)
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()
    only = set(filter(None, args.only.split(",")))
    os.makedirs(os.path.join(ROOT, "art", "props"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "art", "tiles"), exist_ok=True)
    os.makedirs(args.review_dir, exist_ok=True)
    manifest = {}
    groups = {}
    for pid in sorted(PROPS):
        if only and pid not in only:
            continue
        p = PROPS[pid]
        sheet, entry, _ = render(p)
        manifest[pid] = entry
        folder = "tiles" if p["kind"] == "tile" else "props"
        if not args.no_write:
            save_png(Image.fromarray(sheet, "RGBA"), os.path.join(ROOT, "art", folder, pid + ".png"))
        if p["extra"].get("building"):
            group = "buildings"
        elif folder == "tiles":
            group = "tiles"
        elif sheet.shape[1] > 900:
            group = "props_wide"
        else:
            group = "props"
        groups.setdefault(group, []).append((pid, sheet, entry))
    if not only and not args.no_write:
        with open(os.path.join(ROOT, "data", "prop_art.json"), "w") as fh:
            json.dump(manifest, fh, indent=2, sort_keys=True)
            fh.write("\n")
    # review sheets
    for group, items in sorted(groups.items()):
        width = 2400 if group in ("props_wide", "buildings", "tiles") else 1800
        contact_sheet(items, os.path.join(args.review_dir, f"{group}_contact.png"), cols_px=width)
    print(f"built {len(manifest)} sheets")


if __name__ == "__main__":
    main()
