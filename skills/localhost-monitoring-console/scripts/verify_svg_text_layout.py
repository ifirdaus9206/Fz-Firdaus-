#!/usr/bin/env python3
"""Geometric text checker for generated SVG guides (no browser, no vision model).

Why: `vision_analyze` on portrait schematic PNGs is not a reliable proofreader — in one
session every PNG came back drawn as tofu blocks even though the bytes were correct, and
in another it passed a line that was actually clipped past the frame edge. This script
parses the `<text>` nodes, estimates each bounding box, and reports clipping/overlaps.

Usage
    python3 verify_svg_text_layout.py                 # ./static/img/panduan/*.svg
    python3 verify_svg_text_layout.py path/to/dir
    python3 verify_svg_text_layout.py --width 720 --margin 26 static/img/panduan

Exit code = number of files with warnings (0 = clean), so it drops straight into a smoke test.
Tune WIDTH/MARGIN for your frame: the phone mock used here is 720 px wide with a 22 px
outer frame, so text may not extend past 720 - 26.

Estimates, not truth: 0.55 x font-size per character (0.60 when bold), `text-anchor`
honoured. It is deliberately conservative — a false positive costs one caption rewrite.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RE_TEXT = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.S)
RE_ATTR = re.compile(r'([\w-]+)="([^"]*)"')
BOLD = {"bold", "600", "700", "800", "900"}


def bbox(attrs: dict, text: str, margin: int, width: int):
    x = float(attrs.get("x") or 0)
    y = float(attrs.get("y") or 0)
    size = float(attrs.get("font-size") or 16)
    factor = 0.60 if (attrs.get("font-weight") or "") in BOLD else 0.55
    anchor = attrs.get("text-anchor") or "start"
    clean = re.sub(r"&[a-z]+;", "x", text)
    w = max(1.0, len(clean) * size * factor)
    x0 = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
    return (x0, y - size * 0.80, x0 + w, y + size * 0.20)


def overlaps(a, b, tol: float = 8.0) -> bool:
    if a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1]:
        return False
    return (min(a[2], b[2]) - max(a[0], b[0])) > tol and (min(a[3], b[3]) - max(a[1], b[1])) > tol


def check(path: Path, margin: int, width: int) -> list[str]:
    svg = path.read_text(encoding="utf-8")
    boxes: list[tuple[str, tuple]] = []
    warn: list[str] = []
    for m in RE_TEXT.finditer(svg):
        attrs = dict(RE_ATTR.findall(m.group(1)))
        label = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if not label:
            continue
        bb = bbox(attrs, label, margin, width)
        boxes.append((label, bb))
        if bb[0] < margin - 2:
            warn.append(f"keluar kiri: '{label}' x0={bb[0]:.0f} < {margin}")
        if bb[2] > width - margin + 2:
            warn.append(f"keluar kanan: '{label}' x1={bb[2]:.0f} > {width - margin}")
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            (t1, b1), (t2, b2) = boxes[i], boxes[j]
            if overlaps(b1, b2):
                w = min(b1[2], b2[2]) - max(b1[0], b2[0])
                h = min(b1[3], b2[3]) - max(b1[1], b2[1])
                warn.append(f"bertindih: '{t1[:24]}' <> '{t2[:24]}' ({w:.0f}x{h:.0f}px)")
    return warn


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dir", nargs="?", default="static/img/panduan")
    ap.add_argument("--width", type=int, default=720)
    ap.add_argument("--margin", type=int, default=26)
    a = ap.parse_args()
    d = Path(a.dir)
    files = sorted(d.glob("*.svg"))
    if not files:
        print(f"tiada SVG dalam {d}")
        return 1
    bad = 0
    for f in files:
        w = check(f, a.margin, a.width)
        print(f"{f.name:32} {'OK' if not w else str(len(w)) + ' amaran'}")
        for line in w[:6]:
            print("    -", line)
        bad += bool(w)
    print(f"\nFail dengan amaran: {bad}")
    return bad


if __name__ == "__main__":
    sys.exit(main())
