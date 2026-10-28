# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) YORU contributors — see LICENSE for details.

"""Build the YORU-Explain logo and the site icons from the YORU logo.

Edit CONFIG if the YORU logo is elsewhere, then run (any Python with
numpy and Pillow, e.g. YORU-Explain's environment)::

    python scripts/make_logo.py

The logo is made the way YORU-Tracker's is (YORU-Tracker ``tools/make_logo.py``):
the YORU wordmark is kept -- same letters, moon, mouse and fly -- and
recoloured by writing every pixel as a mix of the logo's three inks (paper
white, navy, moon yellow), so the anti-aliased edges stay smooth.  Below it,
"EXPLAIN" and the application's motif: an occlusion map -- patches shaded by
how much hiding them lowers the score -- under a detection box tagged with a
delta.  The accent is YORU-Explain's hot pink (#FF69B4), the default
occlusion baseline and the accent of its GUI.

Writes ``logos/YORU-Explain_logo_dark.png`` (transparent, light ink, for the
navy sidebar), ``logos/YORU-Explain_logo_light.png`` (white background),
``logos/YORU-Explain_icon.png``, ``public/favicon.ico`` and
``public/apple-touch-icon-precomposed.png``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]

CONFIG = {
    # The first file that exists is used.
    "yoru_logo": [
        ROOT.parent / "YORU-dev" / "YORU" / "logos" / "YORU_logo.png",
        ROOT.parent / "YORU" / "logos" / "YORU_logo.png",
        ROOT.parent / "YORU_doc" / "logos" / "YORU_logo.png",
    ],
    "logos": ROOT / "logos",
    "public": ROOT / "public",
}

PAPER = np.array([255.0, 255.0, 255.0])
NAVY = np.array([1.0, 27.0, 67.0])
YELLOW = np.array([242.0, 216.0, 79.0])

#: YORU-Explain's accent: hot pink on dark backgrounds, the GUI's primary
#: button pink on white (readable there).
PINK_DARK_BG = (255, 105, 180)
PINK_LIGHT_BG = (196, 64, 138)
#: The GUI's window background (YORU's theme).
GUI_NAVY = (18, 24, 42)

#: Heat of the motif's patches, 0..1 (rows x columns); the box covers the
#: middle three columns.
HEAT = np.array([
    [0.06, 0.20, 0.42, 0.26, 0.08],
    [0.12, 0.48, 1.00, 0.68, 0.18],
    [0.05, 0.24, 0.56, 0.34, 0.07],
])


def _yoru_logo() -> Path:
    for p in CONFIG["yoru_logo"]:
        if Path(p).is_file():
            return Path(p)
    raise SystemExit(f"YORU logo not found; looked at {CONFIG['yoru_logo']}")


def _unmix(rgb: np.ndarray) -> np.ndarray:
    """Weights of (paper, navy, yellow) per pixel, least squares, clipped."""
    basis = np.stack([PAPER, NAVY, YELLOW], axis=1)
    weights = np.linalg.solve(basis, rgb.reshape(-1, 3).T).T
    weights = np.clip(weights, 0.0, None)
    weights /= np.maximum(weights.sum(axis=1, keepdims=True), 1e-6)
    return weights.reshape(*rgb.shape[:2], 3)


def _wordmark(src: Path, navy_to, yellow_to, transparent: bool) -> Image.Image:
    image = Image.open(src).convert("RGBA")
    flat = Image.new("RGBA", image.size, (255, 255, 255, 255))
    flat.alpha_composite(image)
    w, h = flat.size
    # The tagline sits in the bottom fifth; the wordmark is everything above.
    rgb = np.asarray(flat.convert("RGB").crop((0, 0, w, int(h * 0.80))), dtype=np.float64)
    weights = _unmix(rgb)
    ink = weights[..., 1:2] * np.array(navy_to, float) + weights[..., 2:3] * np.array(yellow_to, float)
    coverage = weights[..., 1] + weights[..., 2]
    if transparent:
        color = np.where(coverage[..., None] > 1e-3, ink / np.maximum(coverage[..., None], 1e-3), 0)
        alpha = np.clip(coverage, 0.0, 1.0) * 255.0
        out = np.dstack([color, alpha]).round().clip(0, 255).astype(np.uint8)
        return Image.fromarray(out, "RGBA")
    out = (weights[..., 0:1] * PAPER + ink).round().clip(0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGB").convert("RGBA")


def _font(size: int, names=("bahnschrift.ttf", "segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"),
          variation: str = "SemiBold"):
    for name in names:
        try:
            font = ImageFont.truetype(name, size)
        except OSError:
            continue
        try:
            font.set_variation_by_name(variation)
        except Exception:
            pass
        return font
    return ImageFont.load_default()


def _heat_cells(draw: ImageDraw.ImageDraw, x0: float, y0: float, cell: float, gap: float,
                accent, radius: float) -> None:
    for r, row in enumerate(HEAT):
        for c, v in enumerate(row):
            x = x0 + c * (cell + gap)
            y = y0 + r * (cell + gap)
            alpha = int(round(28 + 227 * float(v)))
            draw.rounded_rectangle((x, y, x + cell, y + cell), radius=radius, fill=(*accent[:3], alpha))


def _compose(mark: Image.Image, ink, accent, box_color, tag_ink, background) -> Image.Image:
    width = 1600
    scale = width / mark.width
    mark = mark.resize((width, int(mark.height * scale)), Image.LANCZOS)
    band = 250
    canvas = Image.new("RGBA", (width, mark.height + band), background)
    canvas.alpha_composite(mark, (0, 0))
    draw = ImageDraw.Draw(canvas)

    # "EXPLAIN", letter-spaced, under the wordmark and right of the motif.
    font = _font(140)
    letters = "EXPLAIN"
    spacing = 44
    boxes = [draw.textbbox((0, 0), ch, font=font) for ch in letters]
    widths = [b[2] - b[0] for b in boxes]
    glyph_top = min(b[1] for b in boxes)
    glyph_bottom = max(b[3] for b in boxes)
    text_w = sum(widths) + spacing * (len(letters) - 1)
    motif_w = 380
    x = (width - text_w - motif_w) // 2 + motif_w
    top = mark.height + 50 - glyph_top
    text_x0 = x
    for ch, cw, b in zip(letters, widths, boxes):
        draw.text((x - b[0], top), ch, font=font, fill=ink)
        x += cw + spacing
    mid = top + (glyph_top + glyph_bottom) / 2

    # The motif: an occlusion map (patches shaded by their effect on the
    # score) with the detection box over it and a delta tag -- what the
    # application measures for every detection it explains.
    rows, cols = HEAT.shape
    cell, gap = 34.0, 7.0
    grid_w = cols * cell + (cols - 1) * gap
    grid_h = rows * cell + (rows - 1) * gap
    gx = text_x0 - 64 - grid_w
    gy = mid + 4 - grid_h / 2
    cells = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    _heat_cells(ImageDraw.Draw(cells), gx, gy, cell, gap, accent, radius=7)
    canvas.alpha_composite(cells)
    pad = 9.0
    bx0 = gx + (cell + gap) - pad
    bx1 = gx + 4 * (cell + gap) - gap + pad
    by0, by1 = gy - pad, gy + grid_h + pad
    draw.rounded_rectangle((bx0, by0, bx1, by1), radius=12, outline=box_color, width=8)
    tag_font = _font(50)
    tb = draw.textbbox((0, 0), "Δ", font=tag_font)
    tag_w, tag_h = tb[2] - tb[0] + 30, tb[3] - tb[1] + 18
    tx, ty = bx0, by0 - tag_h + 4
    draw.rounded_rectangle((tx, ty, tx + tag_w, ty + tag_h), radius=8, fill=box_color)
    draw.text((tx + 15 - tb[0], ty + 9 - tb[1]), "Δ", font=tag_font, fill=tag_ink)
    return canvas


def _icon(size: int = 512) -> Image.Image:
    """The motif alone on the GUI's navy: the favicon and touch icon."""
    s = size / 512.0
    icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=int(112 * s), fill=(*GUI_NAVY, 255))
    heat = np.array([[0.16, 0.46, 0.20], [0.36, 1.00, 0.52], [0.10, 0.42, 0.16]])
    cell, gap = 104 * s, 18 * s
    grid = 3 * cell + 2 * gap
    x0 = y0 = (size - grid) / 2
    layer = Image.new("RGBA", icon.size, (0, 0, 0, 0))
    ldraw = ImageDraw.Draw(layer)
    for r in range(3):
        for c in range(3):
            v = heat[r, c]
            x, y = x0 + c * (cell + gap), y0 + r * (cell + gap)
            ldraw.rounded_rectangle((x, y, x + cell, y + cell), radius=20 * s,
                                    fill=(*PINK_DARK_BG, int(round(40 + 215 * v))))
    icon.alpha_composite(layer)
    pad = 16 * s
    bx0, by0 = x0 + (cell + gap) - pad, y0 + (cell + gap) - pad
    bx1, by1 = x0 + 2 * (cell + gap) - gap + pad, y0 + 2 * (cell + gap) - gap + pad
    draw.rounded_rectangle((bx0, by0, bx1, by1), radius=int(22 * s), outline=(*YELLOW.astype(int), 255),
                           width=max(2, int(round(22 * s))))
    return icon


def main(config=CONFIG) -> None:
    src = _yoru_logo()
    logos, public = Path(config["logos"]), Path(config["public"])
    logos.mkdir(parents=True, exist_ok=True)
    public.mkdir(parents=True, exist_ok=True)

    dark_mark = _wordmark(src, navy_to=(236, 240, 248), yellow_to=tuple(YELLOW), transparent=True)
    dark = _compose(dark_mark, ink=(236, 240, 248, 255), accent=(*PINK_DARK_BG, 255),
                    box_color=(242, 216, 79, 255), tag_ink=(16, 22, 40, 255),
                    background=(0, 0, 0, 0))
    dark.save(logos / "YORU-Explain_logo_dark.png", optimize=True)

    light_mark = _wordmark(src, navy_to=tuple(NAVY), yellow_to=tuple(YELLOW), transparent=False)
    light = _compose(light_mark, ink=(1, 27, 67, 255), accent=(*PINK_LIGHT_BG, 255),
                     box_color=(1, 27, 67, 255), tag_ink=(255, 255, 255, 255),
                     background=(255, 255, 255, 255))
    light.convert("RGB").save(logos / "YORU-Explain_logo_light.png", optimize=True)

    icon = _icon(512)
    icon.save(logos / "YORU-Explain_icon.png", optimize=True)
    icon.save(public / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    touch = Image.new("RGBA", (180, 180), (*GUI_NAVY, 255))
    touch.alpha_composite(icon.resize((180, 180), Image.LANCZOS))
    touch.convert("RGB").save(public / "apple-touch-icon-precomposed.png", optimize=True)
    print(f"logo from {src}")
    for p in ("YORU-Explain_logo_dark.png", "YORU-Explain_logo_light.png", "YORU-Explain_icon.png"):
        print("wrote", logos / p)
    print("wrote", public / "favicon.ico", "and", public / "apple-touch-icon-precomposed.png")


if __name__ == "__main__":
    main()
