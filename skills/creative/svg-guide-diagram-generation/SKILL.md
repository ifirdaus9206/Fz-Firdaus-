---
name: svg-guide-diagram-generation
description: Build SVG how-to screens; verify no clipped text.
tags: [svg, diagrams, ui-mockup, screenshots, rsvg, font-metrics, qa]
---

# SVG guide diagrams (illustrated step-by-step screens)

Use when a task needs **illustrated how-to screens** instead of real screenshots:
app-install walkthroughs, settings paths, console onboarding, "tab X › row Y"
guides, multi-step flows (2 flows × 3 steps). Also use when extending an
existing `tools/gen_*_panduan.py`-style generator.

Core rule: **SVG/PNG diagrams are code — never hand-place numbers twice.**
One Python generator emits every screen from shared drawing helpers; a metric
checker then proves nothing is clipped or overlapping.

## 1. Reuse the house helper module, never copy it

If a sibling generator already exists (`gen_hyperos_panduan.py` etc.), import
it as a module so all screens keep one visual language:

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gen_hyperos_panduan import (W, H, BG, PANEL, LINE, INK, MUT, GREEN, YEL,
    ICO, MARGIN, OUT, kotak, teks, ikon, baris, label_anak_panah, shell)
```

Add only **new** small helpers locally (`pil`, `suis`, `tanda_semak`, `jubin`).
Duplicating an existing helper is a hard fail — it forks the style and later
diverges.

`shell(tajuk, isi_html, nota_baris)` typically draws: frame, status bar, title,
content band, and a bottom "LANGKAH" box. Read the module first and note the
**fixed regions** (e.g. rows start y=228 step 132 h=112; LANGKAH box y=H-206
h=164, note lines at H-136+i*38). Content must never cross into those bands.

## 2. Layout math before drawing

- Canvas 720×1280, safe margin ≥40px (house style uses `MARGIN=56`) → text
  bbox must stay inside **40 … 680**.
- Row list: `y, y+132, y+264 …` with `h=112`; anything below the last row is
  free for cards.
- A pill/badge inside a highlighted row is the cleanest "TEKAN INI" label when
  the gap between rows is only ~20px (no room for an arrow label).
- Reserve ~18px clearance between a pill and the next row's tile top.
- `label_anak_panah(x_teks, y_teks, x_hujung, y_hujung, s, anchor="end")`
  starts the arrow at `(x_teks-4, y_teks+8)`, i.e. just under the text — so put
  the text in genuinely empty space and aim the tip at the target's edge.

## 3. Text does not wrap — measure it

SVG `<text>` never wraps or ellipsizes: long labels silently run off-canvas or
into the neighbouring element. Before committing a string, measure it with the
*literal* font the SVG names:

```python
from PIL import ImageFont
f = ImageFont.truetype(FDIR + "DejaVuSans-Bold.ttf", size)
w = f.getlength(s)          # px at that font-size
```

Guard rails that came out of real runs:
- DejaVu Sans ≈ 0.55×size per char; **bold ≈ 0.62–0.65×size**, and caps/apostrophes
  push a 24px note line to ~13–14px per char.
- A `shell()` note line at 24px starting x=48 breaks past 680 at ~**47 chars**.
  Keep LANGKAH lines ≤ ~45 chars.
- Long file/folder names: split across title + sub (`autonomous_trading` +
  `controller_blueprint · folder`) rather than shrinking below 20px.
- Minimum font size 20 everywhere; headings 24–36.

## 4. Verify: metrics → render → eyes

`scripts/check_svg_text_fit.py` (in this skill) parses every `<text>` in the
SVGs, measures with DejaVu metrics, and reports (a) bboxes outside the safe
margin and (b) pairwise bbox overlaps:

```bash
python3 tools/gen_boot_adb_panduan.py
python3 <skill>/scripts/check_svg_text_fit.py static/img/panduan/boot-*.svg
```

Then render at half size and actually look at it:

```bash
for f in boot-01-fail boot-02-install; do
  rsvg-convert -w 480 static/img/panduan/$f.svg -o preview/$f.png
done
```

and inspect each PNG with `vision_analyze`. Metrics catch clipping; only vision
catches "pill floats 8px above the next row" or "arrow aims at the card edge,
not the switch". Iterate until both are clean, then report one line per image.

## Pitfalls

- `rsvg-convert` needs the font installed; check
  `PREFIX/share/fonts/TTF/DejaVuSans*.ttf` before blaming the SVG.
- `/tmp` may be unwritable on Termux — keep scratch scripts in `$HOME`,
  delete them after, and only the deliverables stay in the repo.
- `text-anchor` shifts the bbox: `middle` → `x-w/2`, `end` → `x-w`. The checker
  must apply it or it reports false overlaps.
- Colour on a white card: dark ink (`#12241d`) + muted (`#5f7369`); a yellow
  pill on white needs dark text (`#3a2c05`), not `INK`.
- Draw ✓ / ▶ / toggles as paths and rects; emoji glyphs are not reliable in
  `rsvg-convert`.
- Never touch `index.html`, `app.py`, `style.css`, `app.js`, or service files
  when the task says only assets + generator.
- Existing 4-file set = style reference; open one existing PNG first so new
  screens match spacing and density.

## Support files

- `scripts/check_svg_text_fit.py` — metric-based clipping/overlap checker.
- `references/hermes-console-panduan.md` — Hermes Console asset layout, the
  helper API, and the exact flow spec for boot/ADB guides.
