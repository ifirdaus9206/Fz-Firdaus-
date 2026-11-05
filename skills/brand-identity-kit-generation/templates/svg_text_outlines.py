"""TTF -> SVG outlines + palette helpers (copy into <project>/source/brand_lib.py).

Why: generated artwork must not depend on fonts being installed on the render box.
Every glyph becomes a <path>, so rsvg-convert / Illustrator / Inkscape render it identically.

Requires: pip install fonttools
"""
from __future__ import annotations

from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONTS = Path(__file__).resolve().parent / "fonts"


class Typeface:
    def __init__(self, filename: str):
        self.tt = TTFont(FONTS / filename)
        self.upem = self.tt["head"].unitsPerEm
        self.cmap = self.tt.getBestCmap()
        self.glyphset = self.tt.getGlyphSet()
        self.hmtx = self.tt["hmtx"]

    def text_width(self, text: str, size: float, tracking: float = 0.0) -> float:
        """Width in user units. NOTE: ignores the final right side bearing — pad the frame."""
        s = size / self.upem
        w = 0.0
        for ch in text:
            g = self.cmap.get(ord(ch))
            if g:
                w += self.hmtx[g][0] * s
            w += tracking
        return w - tracking if text else 0.0

    def text_path(self, text: str, size: float, x: float = 0.0, y: float = 0.0,
                  tracking: float = 0.0) -> str:
        """SVG path data for `text`; (x, y) is the LEFT BASELINE."""
        s = size / self.upem
        parts, cursor = [], x
        for ch in text:
            g = self.cmap.get(ord(ch))
            if g is None:
                cursor += tracking
                continue
            pen = SVGPathPen(self.glyphset)
            self.glyphset[g].draw(TransformPen(pen, (s, 0, 0, -s, cursor, y)))  # y flip
            d = pen.getCommands()
            if d:
                parts.append(d)
            cursor += self.hmtx[g][0] * s + tracking
        return " ".join(parts)

    def cap_height(self, size: float) -> float:
        os2 = self.tt["OS/2"]
        return getattr(os2, "sCapHeight", int(self.upem * 0.72)) * size / self.upem


def fit_cap(font: Typeface, text: str, max_w: float, tracking_em: float = 0.0) -> float:
    """Cap height that makes `text` exactly max_w wide — fit by width, never by eye."""
    cap = 100.0
    size = cap / font.cap_height(1.0)
    w = font.text_width(text, size, tracking_em * size)
    return cap * (max_w / w)


def centred(font: Typeface, text: str, cap: float, max_w: float, cx: float,
            baseline: float, tracking_em: float = 0.0) -> tuple[float, float, str]:
    """(size, width, path) for text centred at cx, shrunk to max_w. Baseline stays as given."""
    size = cap / font.cap_height(1.0)
    tracking = tracking_em * size
    w = font.text_width(text, size, tracking)
    if w > max_w:
        k = max_w / w
        size *= k
        tracking *= k
        w = font.text_width(text, size, tracking)
    return size, w, font.text_path(text, size, cx - w / 2, baseline, tracking)


def wrap(font: Typeface, text: str, size: float, max_w: float) -> list[str]:
    """Greedy word wrap measured with real advance widths."""
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if font.text_width(trial, size) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- colour maths
def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_cmyk(r: int, g: int, b: int) -> tuple[int, int, int, int]:
    if (r, g, b) == (0, 0, 0):
        return (0, 0, 0, 100)
    r_, g_, b_ = r / 255, g / 255, b / 255
    k = 1 - max(r_, g_, b_)
    return tuple(round((1 - v - k) / (1 - k) * 100) for v in (r_, g_, b_)) + (round(k * 100),)


def rel_luminance(h: str) -> float:
    def ch(v: float) -> float:
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = hex_to_rgb(h)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a: str, b: str) -> float:
    """WCAG 2.1 ratio. >=7 AAA, >=4.5 AA body, >=3 large text/graphics only."""
    la, lb = rel_luminance(a), rel_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def verdict(ratio: float) -> str:
    return "AAA" if ratio >= 7 else ("AA" if ratio >= 4.5 else "large-only")
