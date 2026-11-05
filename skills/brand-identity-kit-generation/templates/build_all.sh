#!/data/data/com.termux/files/usr/bin/bash
# Rebuild every brand asset from source. Run from <project>/source/.
# Needs: python3, fonttools, pypdf, rsvg-convert (librsvg).
set -e
cd "$(dirname "$0")"

python3 make_fonts.py        # variable TTF -> static weights (wght/wdth/opsz)
python3 gen_logo.py          # icon / primary / wordmark / stacked, all colourways
python3 gen_collateral.py    # palette card, type specimen, cards, mockups
python3 gen_guidelines.py    # A4 page SVGs (viewBox px + width/height in mm)

# per-page vector PDFs, then one merged document
cd ../guidelines
for f in pages/page-*.svg; do
  n=$(basename "$f" .svg)
  rsvg-convert -f pdf -o "$n.pdf" "$f"
done
python3 - <<'PY'
from pathlib import Path
from pypdf import PdfWriter, PdfReader
g = Path(".")
w = PdfWriter()
for p in sorted(g.glob("page-*.pdf"), key=lambda p: int(p.stem.split("-")[1])):
    w.append(str(p))
out = g / "Brand-Guidelines-v1.0.pdf"
w.write(str(out))
r = PdfReader(str(out))
print("pages:", len(r.pages), "size pt:", [round(float(x)) for x in r.pages[0].mediabox[2:]])
PY

cd ../source
python3 finalize.py          # PNG exports, logo PDFs, legibility strip, inventory
echo "DONE — check ../guidelines/Brand-Guidelines-v1.0.pdf and ../README.md"
