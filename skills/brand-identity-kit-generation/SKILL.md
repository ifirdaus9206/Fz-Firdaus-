---
name: brand-identity-kit-generation
description: Generate logo, palette, cards, guidelines PDFs as code.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, termux]
metadata:
  hermes:
    tags: [branding, logo, svg, fonttools, rsvg, pdf, design-system, deliverables, verification]
    related_skills: [localhost-monitoring-console, grounded-citations, docx, pdf]
---

# Brand Identity Kit Generation (code-first)

Produce a **complete, real brand kit as files** — primary/secondary logo in four colourways, palette
with HEX/RGB/CMYK, typography with licence, business cards, application mockups, and a multi-page
guidelines PDF — by generating SVG from licensed font outlines and rasterising/merging locally.

## Use when

- "buat logo / brand kit / identiti jenama", "kit jenama penuh untuk syarikat X".
- A multi-agent run delivered only *descriptions* of a logo/palette and the user expects files.
- Any request whose deliverable list contains words like logo, palette, typography, guidelines,
  business card, mockup, vehicle wrap, yard sign, "fail sumber".

## Non-negotiables

1. **Files, not prose.** A "brand concept document" is not a deliverable. Every brief item must map
   to a path on disk (SVG + PNG + PDF). If a brief item truly cannot be produced here (photographic
   mockup, AI/EPS native), produce the vector equivalent and say plainly what it is.
2. **No placeholders left standing.** If a run's agents hand back colours marked "WAJIB DIGANTI",
   replace them with a decided palette and compute the contrast numbers.
3. **Every number is measured, not asserted.** Contrast ratios computed, PDF page size read back
   with `pypdf`, XML parsed, images looked at. "Kontras lulus" without a number is a claim.
4. **Missing facts get `[TBC]` in the artwork**, never invented: licence number, phone, domain, owner
   name. List them in the report as the one thing only the user can supply.
5. **Text becomes outlines.** Convert every glyph to `<path>` so the SVG renders identically on a
   machine without the fonts installed, and the artwork stays editable in Illustrator/Affinity.
6. **Design once, repeat everywhere.** One primitive (tile/chamfer/rule) reused on cards, signs and
   the vehicle. A system that only exists on the cover is decoration.

## Pipeline

```
fonts (OFL)  → instance weights (fontTools)  → text→path lib
     → SVG builders (logo, palette, type, card, mockups, guideline pages)
     → rsvg-convert (PNG, PDF)  → pypdf merge  → render + look at every page
     → README.md + QA report + zip + INVENTORY.json
```

### 1. Fonts

Download the two families you intend to ship from the Google Fonts repo
(`github.com/google/fonts/raw/main/<ofl|apache>/<family>/<File>.ttf`), then cut static weights from
the variable files:

```python
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
inst = instantiateVariableFont(TTFont(src), {"wght": 900, "wdth": 100}, inplace=False)
inst.save(out)
```

Note the axes differ per family (`Inter` also has `opsz`). Ship `OFL.txt` beside the TTFs and name
the licence in the guidelines — commercial typeface rights is a question the client will ask.

### 2. Text → vector

Use `templates/svg_text_outlines.py` (fontTools `SVGPathPen` + `TransformPen`, y-flip, tracking,
`text_width`, `cap_height`). Do not rely on `<text>`: no font on the render box, no control over
metrics at export time.

### 3. Logos

- Geometry first: a reference tile (e.g. 200 units) carrying the brand's one signature cut
  (chamfer, notch, radius) as a fixed percentage, so every size scales exactly.
- Fit the monogram by **width**, not by cap height: `cap = 100 * (max_w / width_at_100)` — guessing
  a cap ratio is what clips letters against the tile.
- **Do not repeat the monogram.** If the icon already says "A1", the wordmark beside it must read
  "GENERAL BUILDERS", not "A1 GENERAL BUILDERS" (a 1:1 replay looks like a bug and drains the hero
  position). Ship a text-only `wordmark.svg` for narrow spaces.
- Colourways: full colour, black, white, reversed (on ink), plus icon-only and stacked. One accent
  corner is enough; an accent on two corners reads muddy at small sizes.

### 4. Palette that survives print + accessibility

Give HEX, RGB and **computed CMYK** per colour, and add a darker variant of the accent when the pure
accent fails AA for small text (bronze `#B87333` on bone `#F2EFE9` = 3.3:1 → ship
`Bronze Deep #8A5726` = 5.3:1 and write the rule down). Contrast = WCAG 2.1 relative luminance:

```python
def rel_lum(h): ...                      # sRGB → linear, 0.2126R + 0.7152G + 0.0722B
def contrast(a, b): return (max(la, lb) + .05) / (min(la, lb) + .05)
```

State the print caveat: CMYK is a process conversion, ask the printer to proof the accent, and name
the nearest Pantone as an estimate only.

### 5. Collateral

| Item | Canvas | Notes |
|---|---|---|
| Logo PNGs | 1600 / 1024 / 512 / 256 | transparent by default (no background rect in the SVG) |
| Business card | 1050×600 px = 3.5×2 in @300 dpi | front = mark + wordmark + rule; back = contact + licence, mark small in a corner |
| Yard sign | 900×1200 | ink board, icon top, two-line wordmark, phone biggest |
| Vehicle wrap | 1600×900 | dark panel on the box front, wordmark on the flank, wheels *under* the body |
| Social | 1080×1080 | icon on ink, wordmark plus one credential line |
| Guidelines | A4 × 9 pages | cover, idea/voice, logo system, clear space/don'ts, colour, type, card, applications, files/open items |

Marketing vs legal naming must be enforced in the artwork: `INC` on cards/contracts, dropped on
signs and vehicles — and say so on the page, because a reviewer will otherwise flag it.

### 6. PDF that is actually A4

`rsvg-convert` sizes PDFs from the SVG's declared `width`/`height`, defaulting to 96 dpi, so a
1240×1754 px page comes out 930×1316 pt. Declare physical units and keep the design viewBox:

```python
f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1240 1754" width="210mm" height="297mm">'
```

Then per page `rsvg-convert -f pdf -o page-N.pdf page-N.svg`, merge with `pypdf.PdfWriter`, and
verify: `PdfReader(...).pages[0].mediabox` must read `[595, 842]`.

### 7. Verification loop (the part that finds the bugs)

For every page and mockup: `rsvg-convert -w 760 … -o preview.png` → `vision_analyze` → fix →
re-render. In one kit this caught: monogram clipped by the tile, body text overlapping a heading,
"INC." colliding with the wordmark, a duplicated `A1` on both truck and yard sign, a caption drawn
over its own icon, and a cover with the headline drawn twice. **No generated design ships without
being looked at.**

Also ship a **legibility test**: the icon at 16 / 32 / 48 / 96 px on light and dark. It proves where
the mark dies (16 px lost the chamfer) and turns that into a written minimum size (32 px / 15 mm
print / 22 mm embroidery).

## Handoff packaging (the kit leaves your hands)

A kit that stays in your working folder is not delivered. The user hands these files to printers,
sign makers, designers and web people who will not read a generator script. Package for **them**:

1. **One format per folder, numbered in reading order** — `01-LOGO-SVG/ 02-LOGO-PDF/ 03-PNG/
   04-PALET/ 05-TIPOGRAFI/ 06-KAD-PERNIAGAAN/ 07-GARIS-PANDUAN/ 08-MOCKUP/ 09-FON/ 10-SUMBER/`.
   Never one flat dump, and never "just send the zip" when the user asks for per-format files.
2. **`BACA-DULU.md` at the root**, in the user's language, plain words: what each folder holds,
   who receives which folder ("kedai cetak → 06 + 09"; "orang web → 03 + 09 + 04"), the palette
   table with HEX/RGB/CMYK, the naming and clear-space rules, and the copyable numbers. Mark
   `10-SUMBER` as internal — never send generators to a supplier.
3. **Quarantine, don't ship, the broken file.** XML-parse every SVG/PNG-bound file before packaging
   and move failures to `source/_rosak/` with the reason in the handoff doc. One stray debug
   duplicate (a lone `<` at line 11) is enough to make the whole delivery look careless.
4. **Write the re-brand path down**: which single file and which lines hold the brand name and the
   five palette constants, plus the one rebuild command. That is what turns "a logo job" into "an
   engine we can reuse for the next product brand" — and it is the answer to "perlu sesuaikan nanti".
5. **State what is missing**, in the same document: native `.ai`/`.eps`, photographic mockups, open
   facts (`[TBC]`) — with the workaround (SVG opens in Illustrator and re-saves as `.ai`).
6. Counts in the handoff doc must be generated from the folder (`find … | wc -l`), never typed from
   memory. Wrong counts are the fastest way to lose the user's trust.

## Pitfalls (each one cost real time)

- **A helper refactor from `(str, y)` to `str` left `para(...)[0]` behind**, returning the first
  character — a lone `<` inside the SVG. rsvg then reports `StartTag: invalid element name` at a line
  far from the cause. After any return-shape change, grep for `[0]`, and XML-parse every generated
  file before rendering.
- **Embedding one generated SVG inside another**: inline it as a nested
  `<svg x y width height viewBox>` with the source's inner markup; `xlink:href` to a sibling file is
  not reliable under rsvg.
- **Tracking underestimates the right edge** — `text_width` ignores the final bearing, so wordmarks
  look clipped at the frame. Add ~1% + ~18 px of padding on the measured width.
- **rsvg silently substitutes DejaVu** for any `<text>` left in an SVG, so the client can receive the
  wrong typeface with no error. Outlines are mandatory.
- **A square-ish canvas hides bad geometry.** Render at the aspect the file is actually used
  (2:1 wrap, 3:4 sign) before believing the layout.
- **`pkill -f "<pattern>"` kills the shell that runs it** when the pattern appears in your own
  command; kill by session id or `pkill -f "[h]ttp.server 9123"` (see
  `android-device-control-from-termux` → `references/lan-device-identity-verification.md`).
- **Zip after the last rebuild**, excluding `__pycache__` and preview PNGs you do not ship; record
  `INVENTORY.json` (path + bytes) so the report quotes real sizes.

## Deliverables checklist (quote this in the report)

1. primary logo, 4 colourways ✚ 2. icon/secondary + legibility test ✚ 3. palette HEX/RGB/CMYK with
contrast table ✚ 4. type pair + licence + specimen ✚ 5. guidelines PDF (page count + pt size) ✚
6. business card front/back ✚ 7. mockups ✚ 8. sources (SVG/PDF/TTF/generators) ✚ README (client,
English) + QA report (user's language) + zip.

One line per item, all with a path, then the `[TBC]` open items the user must supply.

## Files

- `templates/svg_text_outlines.py` — TTF → SVG path module (tracking, width, cap height, palette,
  CMYK and contrast helpers). Copy into the project's `source/`.
- `templates/build_all.sh` — fonts → logos → collateral → guidelines → exports in one command.
- `templates/handoff-BACA-DULU.md` — the client-facing "read this first" document: per-format folder
  table, recipient matrix, palette table, rules, re-brand instructions, honest gaps.
- `references/kit-handoff-packaging.md` — the exact `SERAHAN-<brand>/` layout, copy commands, the
  SVG validation + quarantine step, and how to send the delivery in chat (a few key files + zip).
- `references/vector-kit-on-termux.md` — exact toolchain that worked (fontTools, rsvg-convert,
  pypdf), export matrix, A4/PNG commands.
- `references/a1-builders-kit-2026-11.md` — worked example: geometry, palette, page list, the six
  defects the vision loop found, and the 0/8 multi-agent run that preceded the rebuild.
