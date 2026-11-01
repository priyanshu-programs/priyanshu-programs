#!/usr/bin/env python3
"""Prepare a portrait photo for ASCII conversion. Run once per photo.

Removes the background and writes:
  source-prepped.png  grayscale subject composited on pure white
  source-mask.png     subject alpha, so the background can always become spaces

Usage: python scripts/prep_photo.py path/to/photo.png

CLAHE=1.5 adds local contrast for flatly lit photos. It stays off by default
because it flattens the tones of a well-lit photo and loses the face.
"""
import os
import pathlib
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: prep_photo.py <photo>")

    rgba = np.array(remove(Image.open(sys.argv[1]).convert("RGB")).convert("RGBA"))
    alpha = rgba[:, :, 3].astype(np.float32) / 255.0

    gray = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2GRAY)
    clip = float(os.environ.get("CLAHE", 0))
    if clip:
        gray = cv2.createCLAHE(clipLimit=clip, tileGridSize=(4, 4)).apply(gray)

    composited = gray.astype(np.float32) * alpha + 255.0 * (1.0 - alpha)
    Image.fromarray(composited.astype(np.uint8), "L").save(ROOT / "source-prepped.png")
    Image.fromarray((alpha * 255).astype(np.uint8), "L").save(ROOT / "source-mask.png")
    print("wrote source-prepped.png and source-mask.png")


if __name__ == "__main__":
    main()
