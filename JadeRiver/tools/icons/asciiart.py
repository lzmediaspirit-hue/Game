"""Colour-keyed ASCII sprites for the tiny icon families (status 12x12, markers 12x12).

Each char maps to a colour; '.' and ' ' are empty. The sprite is centred on the
canvas by its bounding box and receives the automatic hue-tinted dark outline.
"""
from pix import Canvas, dark_of

KEY = {
    # reds / warm
    'R': '#E45858', 'r': '#8C2A38', 'P': '#FF9C86',
    'O': '#F58A3A', 'o': '#A6341C', 'Y': '#FFE070', 'y': '#E5B84C', 'Z': '#FFF6D6',
    # greens
    'G': '#7CC456', 'g': '#2F7A3A', 'L': '#C2E68A',
    'J': '#2C9E8F', 'j': '#15514F', 'K': '#67D6BD',
    # blues / cyan
    'C': '#32BED1', 'c': '#166E8C', 'I': '#B7EEF7',
    'B': '#5A82B8', 'b': '#34497A',
    # violets
    'V': '#9B78D1', 'v': '#51398A', 'U': '#C9AEF2',
    # neutrals
    'W': '#F4FBFB', 'w': '#AFC9D1', 'h': '#87949A', 'H': '#5A676D', 'D': '#3E484E',
    'N': '#EBE4D0', 'n': '#B8AE92',
    'E': '#A87A42', 'e': '#6A4422',
    'k': '#071015',
}


def sprite(rows, size=12, key=None, outline_col=None, dx=0, dy=0):
    key = key or KEY
    rows = [r for r in rows]
    h = len(rows)
    w = max(len(r) for r in rows)
    c = Canvas(size)
    ox = (size - w) // 2 + dx
    oy = (size - h) // 2 + dy
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in '. ':
                continue
            col = key[ch]
            c.px(ox + i, oy + j, col, out=outline_col or dark_of(col))
    c.outline()
    return c


def parse(block):
    return [r for r in block.strip('\n').split('\n')]
