#!/usr/bin/env python3
"""Convert source-prepped.png into a monochrome ASCII SVG that prints itself once.

Each row is revealed by a clip that wipes left to right, with a block cursor
riding the edge. Rows run top to bottom, then everything freezes.

Env:
  STATIC=1   emit the finished frame with no animation (for previews)
  INVERT=1   dense glyphs for dark areas (the guide's mapping, reads as a negative
             on a dark panel). Default is dense glyphs for bright areas.
  OUT=path   output file, default portrait.svg
"""
import os
import pathlib
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(os.environ.get("OUT", ROOT / "portrait.svg"))
STATIC = os.environ.get("STATIC") == "1"
INVERT = os.environ.get("INVERT") == "1"

RAMP = " .`:-=+*cs#%@"  # sparse -> dense
COLS, ROWS = 120, 63
CHAR_W, CHAR_H = 7.0, 13.33
FONT_SIZE = 11.7
# Fractions of the source photo: a tight head-and-shoulders square.
CROP = (0.12, 0.03, 0.88, 0.79)
GAMMA = float(os.environ.get("GAMMA", 1.25))  # above 1 deepens shadows, so glasses and beard separate from skin
FLOOR = float(os.environ.get("FLOOR", 0.10))  # keeps dark hair visible against the panel
PAD = 20
BG, FG, CURSOR = "#0d1117", "#d7dde4", "#39d353"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono','Liberation Mono',monospace"
ROW_DUR, ROW_STAGGER = 0.24, 0.05


def load_channel(name, size):
    img = Image.open(ROOT / name).convert("L")
    w, h = img.size
    box = (int(CROP[0] * w), int(CROP[1] * h), int(CROP[2] * w), int(CROP[3] * h))
    return img.crop(box).resize(size, Image.LANCZOS)


def load_grid():
    size = (COLS, ROWS)
    gray = load_channel("source-prepped.png", size).filter(ImageFilter.UnsharpMask(radius=2, percent=130, threshold=0))
    mask = load_channel("source-mask.png", size)
    return np.array(gray, float) / 255.0, np.array(mask, float) / 255.0


def to_rows(gray, mask):
    low, high = np.percentile(gray[mask > 0.5], [3, 97])
    norm = np.clip((gray - low) / max(high - low, 1e-6), 0, 1) ** GAMMA
    density = 1 - norm if INVERT else FLOOR + norm * (1 - FLOOR)
    idx = np.round(density * (len(RAMP) - 1)).astype(int)
    idx[mask <= 0.5] = 0  # background always prints nothing
    return ["".join(RAMP[i] for i in row).rstrip() for row in idx]


def row_svg(i, text):
    y = PAD + CHAR_H * (i + 1) - 4
    width = len(text) * CHAR_W
    x_attrs = f'x="{PAD}" y="{y:.1f}" textLength="{width:.1f}" lengthAdjust="spacingAndGlyphs"'
    body = f'<text {x_attrs} xml:space="preserve">{escape(text)}</text>'
    if STATIC:
        return body

    begin = i * ROW_STAGGER
    top = y - CHAR_H + 4
    clip = (
        f'<clipPath id="r{i}"><rect x="{PAD}" y="{top:.1f}" width="0" height="{CHAR_H}">'
        f'<animate attributeName="width" from="0" to="{width:.1f}" begin="{begin:.2f}s" '
        f'dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>'
    )
    # The cursor stays hidden until its row starts, rides the wipe, then disappears.
    cursor = (
        f'<rect x="{PAD}" y="{top:.1f}" width="{CHAR_W}" height="{CHAR_H}" fill="{CURSOR}" opacity="0">'
        f'<animate attributeName="x" from="{PAD}" to="{PAD + width:.1f}" begin="{begin:.2f}s" '
        f'dur="{ROW_DUR}s" fill="freeze"/>'
        f'<set attributeName="opacity" to="1" begin="{begin:.2f}s" dur="{ROW_DUR}s"/></rect>'
    )
    return f'{clip}<g clip-path="url(#r{i})">{body}</g>{cursor}'


def main():
    rows = to_rows(*load_grid())
    w = COLS * CHAR_W + PAD * 2
    h = ROWS * CHAR_H + PAD * 2
    parts = "".join(row_svg(i, t) for i, t in enumerate(rows) if t)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}" '
        f'role="img" aria-label="ASCII portrait of Priyanshu Roy">'
        f'<rect width="100%" height="100%" rx="12" fill="{BG}"/>'
        f'<g font-family="{FONT}" font-size="{FONT_SIZE}" fill="{FG}">{parts}</g></svg>'
    )
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
