# Kit handoff packaging — `SERAHAN-<brand>/`

Purpose: turn a generated kit directory (`<brand>-brand-kit/`) into a delivery a printer, sign maker
or web person can act on **without** you in the room. Built and verified on an A1 General Builders
kit (98 files, 10 folders, 8.1 MB zip, Termux).

## When the ask looks like this

- "ini ke semuanya akan aku bagi pada orang untuk jenama produk" — the user will forward the files
  to third parties.
- "aku minta dalam format masing-masing" — one format per folder, not a single archive.
- "tapi perlu sesuaikan apa yang aku minta nanti" — the package must be re-brandable, and the
  adaptation path must be written down.

Partial, mumbled asks like these are usually the *handoff* half of the job, not a request to
regenerate the design. Re-package first, then ask (numbered options) what to adapt next.

## Layout (numbered so non-technical readers follow order)

```
SERAHAN-<BRAND>/
  01-LOGO-SVG/        vector colourways, wordmarks, stacked, icon, legibility test
  02-LOGO-PDF/        print-ready vector PDFs
  03-PNG/             raster sizes 128 → 1600 px, transparent
  04-PALET/           palette card (.svg + .pdf)
  05-TIPOGRAFI/       type specimen (.svg + .pdf)
  06-KAD-PERNIAGAAN/  card front/back (.svg + 300 dpi .pdf)
  07-GARIS-PANDUAN/   merged guidelines PDF + individual page PDFs
  08-MOCKUP/          truck / yard / social application artwork
  09-FON/             .ttf weights + OFL licence files
  10-SUMBER/          generator scripts + build_all.sh — INTERNAL, never sent out
  BACA-DULU.md        client-facing instructions
  SENARAI-FAIL.txt    generated file listing
```

## Build steps

```bash
SRC=~/<brand>-brand-kit ; DST=~/SERAHAN-<BRAND>
rm -rf "$DST"; mkdir -p "$DST"/{01-LOGO-SVG,02-LOGO-PDF,03-PNG,04-PALET,05-TIPOGRAFI,\
06-KAD-PERNIAGAAN,07-GARIS-PANDUAN,08-MOCKUP,09-FON,10-SUMBER}
cd "$SRC"
mkdir -p source/_rosak            # quarantine target for invalid files
cp logo/*.svg  "$DST/01-LOGO-SVG/";  cp logo/*.pdf   "$DST/02-LOGO-PDF/"
cp png/*.png   "$DST/03-PNG/";       cp palette/*    "$DST/04-PALET/"
cp typography/* "$DST/05-TIPOGRAFI/"; cp business-card/* "$DST/06-KAD-PERNIAGAAN/"
cp guidelines/*.pdf "$DST/07-GARIS-PANDUAN/"; cp mockups/*.svg "$DST/08-MOCKUP/"
cp source/fonts/* "$DST/09-FON/"
cp source/*.py source/build_all.sh "$DST/10-SUMBER/"; rm -f "$DST/10-SUMBER/"_dbg*.py
```

Never copy `__pycache__`, `_dbg*` scratch scripts, or `*-b.svg` debug duplicates.

## Validate before packaging (mandatory)

```python
import glob, xml.etree.ElementTree as ET
bad = []
for f in glob.glob('**/*.svg', recursive=True):
    try: ET.parse(f)
    except Exception as e: bad.append((f, str(e)[:60]))
print('bad', bad)
```

Any failure → `mv file source/_rosak/` and name it in `BACA-DULU.md` under "Status fail ini". In the
A1 kit this caught `palette/palette-card-b.svg` — a leftover variant with a lone `<` at line 11,
the exact symptom of a refactor that left `para(...)[0]` behind. Also verify the merged PDF page
count and per-folder counts with `find … | wc -l`, then write **those** numbers into the doc.

## Delivery in chat

Send a small, high-value subset plus the archive — never 98 attachments:

```
MEDIA:.../SERAHAN-<BRAND>/BACA-DULU.md
MEDIA:.../SERAHAN-<BRAND>/07-GARIS-PANDUAN/<Brand>-Brand-Guidelines-v1.0.pdf
MEDIA:.../SERAHAN-<BRAND>/01-LOGO-SVG/primary-color.svg
MEDIA:.../SERAHAN-<BRAND>/06-KAD-PERNIAGAAN/card-front-300dpi.pdf
MEDIA:.../SERAHAN-<BRAND>-v1.1.zip
```

Then report counts per folder (from `find`, not memory), the one invalid file you removed, and the
honest gap (no native `.ai`/`.eps`; SVG re-saves as `.ai`). Close with a numbered 3–4 option list
for what to adapt next — this user answers by number and gets lost with open-ended questions.

## Re-brandability (the "sesuaikan nanti" promise)

Keep brand text and palette in exactly two places so the next brand is a config edit, not a rebuild:

- `source/gen_logo.py` — one `word`/monogram constant (e.g. line ~112 holds `"A1 GENERAL BUILDERS"`).
- `source/gen_logo.py` / `gen_guidelines.py` — the same name string appears in copy blocks
  (headers, legal-entity rows, tagline). `grep -n "<BRAND>" source/*.py` and fix every hit.
- `source/brand_lib.py` — the five palette constants (`INK`, `BONE`, `STEEL`, `BRONZE`,
  `BRONZE_DEEP`).
- `bash source/build_all.sh` regenerates every SVG/PDF/PNG.

Document this in `BACA-DULU.md` §"Bila mahu tukar jenama" with the file names and line numbers.
