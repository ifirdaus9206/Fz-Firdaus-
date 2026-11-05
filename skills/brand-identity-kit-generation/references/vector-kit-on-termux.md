# Toolchain that produced a full kit on Termux (no browser, no Inkscape)

Verified 2026-11 on Android 16 / Termux: python 3.13, fonts and PDFs generated end-to-end with
`Pillow` present but unused, `reportlab`/`cairosvg`/`matplotlib` **absent and not needed**.

## Install

```bash
pip install fonttools pypdf          # both pure-python, ~seconds
# rsvg-convert already ships with librsvg in $PREFIX/bin; check: rsvg-convert --version
```

`rsvg-convert 2.62.3 (cairo 1.18.4, pango 1.57.1, harfbuzz 14.2.1, fontconfig 2.18.1)` renders SVG →
PNG **and** SVG → PDF (`-f pdf`). That is the whole rendering stack; there is no need for Inkscape,
ImageMagick or a headless browser.

## Export matrix

| From | Command | Output |
|---|---|---|
| logo SVG | `rsvg-convert -w 1600 logo/primary-color.svg -o png/primary-color-1600.png` | transparent PNG |
| logo SVG | `rsvg-convert -f pdf logo/primary-color.svg -o logo/primary-color.pdf` | vector PDF |
| card SVG (1050×600 px) | `rsvg-convert -f pdf -w 1050 card-front.svg -o card-front-300dpi.pdf` | 3.5×2 in PDF |
| guideline page | `rsvg-convert -f pdf -o page-3.pdf pages/page-3.svg` | single-page A4 PDF |
| multi-page | `pypdf.PdfWriter().append(...)` in page order | merged PDF |
| preview for review | `rsvg-convert -w 760 pages/page-3.svg -o preview.png` | image for `vision_analyze` |

## A4 exactness (the trap)

`rsvg-convert` derives PDF page size from the SVG root `width`/`height`; if those are px it assumes
96 dpi, so 1240×1754 px → **930×1316 pt** (bigger than A4). Declare millimetres and keep the design
viewBox:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1240 1754" width="210mm" height="297mm">
```

Proof after merge:

```python
from pypdf import PdfReader
r = PdfReader("Brand-Guidelines-v1.0.pdf")
len(r.pages), [round(float(x)) for x in r.pages[0].mediabox[2:]]   # (9, [595, 842])
```

## Embedding one generated SVG inside another page

Do not reach for `<image xlink:href="logo.svg">`. Inline the child's inner markup in a nested `<svg>`
that carries its own viewBox — rsvg then scales it exactly like a group:

```python
m = re.search(r'<svg[^>]*viewBox="([^"]+)"[^>]*>(.*)</svg>', Path(rel).read_text(), re.S)
vb, inner = m.group(1), m.group(2)
f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{vb}">{inner}</svg>'
```

## Fonts

```bash
curl -sL -o ArchivoVar.ttf "https://github.com/google/fonts/raw/main/ofl/archivo/Archivo%5Bwdth,wght%5D.ttf"
curl -sL -o InterVar.ttf   "https://github.com/google/fonts/raw/main/ofl/inter/Inter%5Bopsz,wght%5D.ttf"
curl -sL -o OFL-Archivo.txt "https://github.com/google/fonts/raw/main/ofl/archivo/OFL.txt"
```

Instance the axes you need (`{"wght":900,"wdth":100}` for Archivo, `{"wght":400,"opsz":14}` for Inter)
and ship the OFL text. Because artwork uses outlines, the instanced TTFs are only needed to *rebuild*.

## Deterministic self-check before delivery

```bash
python3 -c "import xml.dom.minidom as m; [m.parse(f) for f in [...]]"   # every generated SVG
python3 -c "from pypdf import PdfReader; ..."                            # page count + pt size
du -sh <project>; find <project> -type f | wc -l                         # sizes for the report
```

`INVENTORY.json` (path + bytes for every file) makes the final report quotable without re-running
`find` under a tool timeout.
