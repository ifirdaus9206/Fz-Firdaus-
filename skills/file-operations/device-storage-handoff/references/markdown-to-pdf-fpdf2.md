# Markdown → PDF on Termux with fpdf2 (no pandoc / no LaTeX)

Field notes from building `~/.hermes20/scripts/md_to_pdf.py` (Android 16, Termux, no root,
`fpdf2 2.9.0` + `markdown 3.11`). Verified by generating real PDFs and re-extracting text.

## Architecture that survives real documents

Do **not** feed the whole `markdown.markdown(...)` output to a single `write_html()` call.
Parse the HTML into blocks first, then render block by block:

```
markdown(text, extensions=[tables, fenced_code, sane_lists, nl2br])
  -> HTMLParser subclass collecting blocks:
     {"jenis":"teks", "tag":"h1..h6|p", "html": ...}
     {"jenis":"senarai", "tag":"ul|ol", "item":[{level, html}]}
     {"jenis":"kod", "teks": ...}
     {"jenis":"jadual", "baris":[[cell,...]], "kepala": bool}
     {"jenis":"petikan", "para":[html,...]}
     {"jenis":"hr"}
  -> render each in its own try/except -> plain-text fallback
```

Why: one bad tag can no longer kill the deliverable, tables/code get real control
instead of whatever `write_html` decides, and page breaks / orphan headings can be managed
with `pdf.ruang(h)` (`if get_y()+h > page_break_trigger: add_page()`).

## The bug that silently deletes content

Literal `<...>` inside backticks (`<nama>`, `<fail.md>`, `<in.md>`) reaches the block
sanitizer as raw text. A safety regex `re.sub(r"<[^>]+>", "", s)` eats it — the PDF renders
`01-LAPORAN/.pdf` and nobody notices until text extraction is diffed against the source.

Correct sanitizer order:

```python
s = re.sub(r"<br\s*/?>", "<br>", s, flags=re.I)
# escape every '<' that does NOT start a tag we actually support
s = re.sub(r"<(?!/?(?:b|i|u|br|a)\b)", "&lt;", s, flags=re.I)
```

fpdf2 unescapes `&lt;` on render, so the literal text survives. Allowed set is small on
purpose: `b, i, u, br, a`. Strip `<code>` (inline) — `write_html` switches to Courier for it,
which reintroduces the Unicode problem.

## Tables

```python
with pdf.table(
        col_widths=lebar,                    # proportional, min ~11 mm, then rescale to epw
        borders_layout="ALL",
        first_row_as_headings=True,
        headings_style=FontFace(emphasis="BOLD", fill_color=(233, 233, 233)),
        text_align="LEFT", line_height=4.4, padding=1.3,
        wrapmode=WrapMode.WORD) as t:
    for r in baris:
        row = t.row()
        for c in r:
            row.cell(c)
```

- `Table.__init__` defaults already give `borders_layout=ALL`, `first_row_as_headings=True`,
  `repeat_headings=1` (header repeats on page 2 — expected, not a bug).
- Column weights from `max(len(cell))` clamped to `[6, 34]`, then scaled so the table spans `epw`.
- Cell text is plain (`HTMLParser` → text), so bold inside cells is lost; acceptable trade for
  never raising on stray markup.

## WrapMode: WORD, not CHAR

`WrapMode.CHAR` breaks **every** line at the character boundary: a 30 mm table cell renders
`uim_hanta` / `r.log`. Use `WrapMode.WORD` everywhere first (fpdf2 hard-splits a genuinely
overlong token by itself — verified with an 80-char word in a 30 mm cell), and keep
`WrapMode.CHAR` only inside the `except` fallback. `WrapMode.CHAR` is still right for the
plain-text disaster fallback, where ugly-but-complete beats missing.

## Fonts / footer / code blocks

- Register one family with all styles so `<b>/<i>` resolve:
  `add_font("DejaVu","",sans)`, `("DejaVu","B",bold)`, `("DejaVu","I",oblique)`,
  `("DejaVu","BI",bold_oblique)`, plus `DejaVuMono` for code. Verify the embedded set with
  pypdf (`/BaseFont` per page) — `DejaVuSansBook/Bold/Oblique/Mono` proves bold/italic/mono
  were actually used, not just registered.
- `footer()` override: `set_y(-15)`, 7.5 pt gray, `cell(0,6,f"UIM · {nama} · halaman {page_no()}", align="C")`.
  Every block renderer must set its own font afterwards — `footer()` leaves the font changed.
- Code block: `multi_cell(..., fill=True)` with `set_fill_color(242,242,242)`, left margin +2.5 mm
  for padding, then a `rect()` border drawn only when `page_no()` did not change (a rect spanning
  a page break is worse than no rect).

## Verifying without a rasterizer

Termux here has no `pdftoppm`, `gs`, `mutool`, `pymupdf`. Don't install one just to look.
Two checks catch almost everything:

```python
r = PdfReader(path)
full = "".join(p.extract_text() for p in r.pages)
for k in ["<nama>", "<fail.md>", "→", "·"]:      # content that used to vanish
    print(k, full.count(k))

xs, ys = [], []
def vis(text, cm, tm, fd, fs):
    if text.strip(): xs.append(tm[4]); ys.append(tm[5])
for p in r.pages: p.extract_text(visitor_text=vis)
print(min(xs), max(xs))   # must sit inside 42.5 .. 552.8 pt on A4 (15 mm margins)
```

Also grep every page for `halaman N` to prove the footer is on each page, and compare
`len(extract_text)`/keyword counts against the source. Extraction glues wrapped words
(`sebelumlulus`) — that's a pypdf artifact of line breaks, not content loss; check for
*missing* tokens (`<nama>`) instead.

## Wrapper script gotchas

- Capture converter stderr into a variable, never into a file in the staging dir:
  `ERRMSG="$(python3 md_to_pdf.py in out 2>&1 >/dev/null)"` (note the order).
  Writing `2>"$TMPDIR/.err"` fails when the staging dir is read-only and the real error is lost
  behind `Permission denied` noise.
- Test the generation-failure path by `chmod 500` on the staging dir, expecting `GAGAL:` + code 6.
- Rejection tests need a file that actually exists: `/etc/hostname` and `/tmp` do **not** exist on
  Android. Use a real outside-`$HOME` file such as `$PREFIX/share/fonts/TTF/DejaVuSans.ttf`.
- When a doc is edited after its PDF was delivered, re-deliver; `uim_hantar.sh` suffixes the name
  with a timestamp instead of overwriting. Delete only your own just-created copy if the duplicate
  would confuse the evidence listing — never pre-existing files.
