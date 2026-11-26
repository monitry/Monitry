"""Draws the Onitry app icon (a ring with an eye-like dot) and writes packaging/Onitry.icns.

    python packaging/make_icon.py

Needs Pillow. The icon is generated, not a checked-in binary, so it can be changed in one place.
"""
import os
import sys

from PIL import Image, ImageDraw

SIZE = 1024
BG = (12, 12, 12, 255)
GREEN = (46, 160, 67, 255)
GREEN_LIGHT = (63, 185, 80, 255)


def draw(size: int = SIZE) -> Image.Image:
    k = size / 1024
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # macOS app icons are a rounded square with a little margin
    margin = int(100 * k)
    d.rounded_rectangle((margin, margin, size - margin, size - margin), radius=int(185 * k), fill=BG)
    cx = cy = size // 2
    # a ring (the "watching" eye) and a bright pupil
    r_out, r_in = int(290 * k), int(215 * k)
    d.ellipse((cx - r_out, cy - r_out, cx + r_out, cy + r_out), fill=GREEN)
    d.ellipse((cx - r_in, cy - r_in, cx + r_in, cy + r_in), fill=BG)
    p = int(88 * k)
    d.ellipse((cx - p, cy - p, cx + p, cy + p), fill=GREEN_LIGHT)
    return img


def main() -> int:
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Onitry.icns")
    img = draw()
    img.save(out, format="ICNS", sizes=[(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024)])
    img.resize((512, 512), Image.LANCZOS).save(os.path.join(os.path.dirname(out), "Onitry-preview.png"))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
