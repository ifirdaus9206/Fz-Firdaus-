#!/usr/bin/env python3
"""Semak SVG panduan: teks terpotong (luar margin selamat) & teks bertindih.

Mengukur setiap <text> dengan metrik fon sebenar (DejaVu Sans / Bold) —
SVG tidak membalut teks, jadi ini satu-satunya cara menangkap teks yang
melimpah keluar kanvas atau menindih elemen lain tanpa buka gambar.

Guna:
    python3 check_svg_text_fit.py static/img/panduan/boot-*.svg
    python3 check_svg_text_fit.py --margin 40 --max-x 680 file.svg

Kod keluar 1 jika ada isu (boleh dipakai dalam gate CI / loop pembaikan).
Perhatian: laluan fon berbeza ikut sistem; jika tiada DejaVu, tetapkan
--fontdir atau ubah FDIR di bawah.
"""
import argparse
import re
import sys
from pathlib import Path

from PIL import ImageFont

FDIR = "/data/data/com.termux/files/usr/share/fonts/TTF/"
_FALLBACKS = [
    "/usr/share/fonts/truetype/dejavu/",
    "/usr/share/fonts/TTF/",
    "/usr/local/share/fonts/",
]
_cache = {}

TXT = re.compile(
    r'<text x="([-\d.]+)" y="([-\d.]+)" font-size="(\d+)"[^>]*?'
    r'fill="([^"]+)" font-weight="(\w+)" text-anchor="(\w+)">(.*?)</text>',
    re.S,
)


def font(size, bold, fontdir):
    key = (size, bold)
    if key not in _cache:
        nama = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        for d in [fontdir] + _FALLBACKS:
            p = Path(d) / nama
            if p.exists():
                _cache[key] = ImageFont.truetype(str(p), size)
                break
        else:
            sys.exit(f"Fon tidak dijumpai: {nama} (cuba --fontdir)")
    return _cache[key]


def boxes(svg, fontdir):
    out = []
    for m in TXT.finditer(svg):
        x, y, sz = float(m.group(1)), float(m.group(2)), int(m.group(3))
        weight, anchor, s = m.group(5), m.group(6), m.group(7)
        s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        w = font(sz, weight == "bold", fontdir).getlength(s)
        x0 = x - (w / 2 if anchor == "middle" else w if anchor == "end" else 0)
        # ascent ~0.80em, descent ~0.24em — generous but stable across strings
        out.append(dict(s=s, x0=x0, x1=x0 + w, y0=y - 0.80 * sz, y1=y + 0.24 * sz))
    return out


def check(path, margin, max_x, fontdir):
    b = boxes(Path(path).read_text(encoding="utf-8"), fontdir)
    isu = []
    for t in b:
        if t["x0"] < margin:
            isu.append(f"KIRI x0={t['x0']:.0f} < {margin} '{t['s']}'")
        if t["x1"] > max_x:
            isu.append(f"KANAN x1={t['x1']:.0f} > {max_x} '{t['s']}'")
        if t["y1"] > 1280 or t["y0"] < 0:
            isu.append(f"ATAS/BAWAH y=({t['y0']:.0f},{t['y1']:.0f}) '{t['s']}'")
    for i in range(len(b)):
        for j in range(i + 1, len(b)):
            a, c = b[i], b[j]
            ox = min(a["x1"], c["x1"]) - max(a["x0"], c["x0"])
            oy = min(a["y1"], c["y1"]) - max(a["y0"], c["y0"])
            if ox > 1.5 and oy > 2:
                isu.append(f"TINDIH '{a['s'][:26]}' <> '{c['s'][:26]}' "
                           f"(ox={ox:.0f}, oy={oy:.0f})")
    print(f"\n=== {Path(path).name}  ({len(b)} teks) ===")
    for m in isu:
        print("  !!", m)
    if not isu:
        print("  OK")
    return len(isu)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--margin", type=float, default=40)
    ap.add_argument("--max-x", type=float, default=680)
    ap.add_argument("--fontdir", default=FDIR)
    a = ap.parse_args()
    files = a.files or sorted(str(p) for p in
                              Path("static/img/panduan").glob("*.svg"))
    total = sum(check(f, a.margin, a.max_x, a.fontdir) for f in files)
    print(f"\nJumlah isu: {total}")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
