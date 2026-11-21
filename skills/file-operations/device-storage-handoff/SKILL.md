---
name: device-storage-handoff
description: Export artifacts to phone storage, verified one-way.
category: file-operations
---

# Device Storage Handoff — factory vs warehouse

## When to use
- The user wants finished artifacts (PDF, images, audio, zips) visible in the phone's Files/Gallery
  app, or ready to attach to Telegram/WhatsApp.
- The user is setting a *storage policy*: "Termux is the factory, phone storage is only a
  warehouse/delivery counter".
- You need to audit that no real work lives only on phone storage, and no secrets leaked there.
- The user wants a Markdown report readable in the phone (→ convert to PDF first), or a
  one-click "send to phone" button inside the local console (127.0.0.1:8787).

Related but opposite direction (phone → agent home) is covered by the user-owned
`file-retrieval-from-android-storage` and `locate-and-replicate-file` skills; do not duplicate them.

## The boundary rule (state it this way to the user)
1. **Factory = agent home** (`$HOME`: config, `.env`, SSH keys, scripts, cron, git, source files).
   Single source of truth. Never symlink it away.
2. **Warehouse = phone shared storage** — copies only: reports, images, zips for handoff.
3. **One-way flow: home → phone.** Copy, verify, never `mv`; never edit on the phone; never pull
   the working copy back.

## Steps
1. **Probe writability before building structure.** `/sdcard` root usually refuses `mkdir`
   (`Permission denied`); `Documents/` and `Download/` accept writes. Test with a throwaway file:
   `echo ok > "$ROOT/.wtest" && rm -f "$ROOT/.wtest"`. Pick the first writable root, e.g.
   `/sdcard/Documents/UIM/`.
2. **Create the warehouse tree** once, one folder per artifact class, plus a `BACA-DULU.md`
   (plain-language note with the 3-line rule, folder table, and usage commands).
3. **Copy only through the guard script** (`scripts/uim_hantar.sh`), which enforces:
   source inside `$HOME` · source not a symlink · source not already in the warehouse · category
   from a fixed allow-list · no silent overwrite (timestamp suffix unless `--ganti`) · `sha256sum`
   + size compared after copy, phone copy deleted on mismatch · one log line per success.
4. **Emit the phone path** as the last line (`MEDIA:<path>`) so it can be attached to chat directly.
5. **Audit silently with cron** (`scripts/uim_semak.sh`, `no_agent=True`, daily): it prints only on
   violations and exits 0 when clean — the watchdog pattern, so a clean day sends nothing.
6. **Sync new artifacts on a schedule instead of by hand.** Daily `no_agent` cron calling a script
   shaped like `~/.hermes20/scripts/uim_sync.sh`: fixed source set (`~/NOTA-*.pdf|txt`,
   `~/reports/*.md|pdf`, project `reports/`), then per file compare `sha256sum` with the warehouse
   copy and **skip when equal**, printing one line only when something was copied. Measured
   2026-11-20: 10 files in 1.8 s, second run printed nothing. Without the hash-skip every run
   re-copies and the chat gets a daily "disalin" message for files that never changed.
   Prefix warehouse names with the source folder (`reports-VERIFIKASI.md`) so two `reports/`
   directories cannot collide, and keep `cp -p` + post-copy hash compare so a truncated copy is
   counted as a failure, not a success.
7. **Report with evidence**: table of components + paths, table of guard tests with the *actual*
   exit codes and messages, then the log tail. Numbered next-step options at the end.

## Markdown → PDF leg (when the user wants readable reports, not raw .md)
Chain: `$HOME/**/*.md` → `~/.hermes20/tmp/<name>.pdf` → `/sdcard/Documents/UIM/01-LAPORAN/`.

- Engine: **`pip install fpdf2 markdown`** then `~/.hermes20/scripts/md_to_pdf.py`
  (`markdown` → HTML with extensions `tables,fenced_code,sane_lists,nl2br`, then `fpdf2.write_html`).
  Pure Python, no pandoc/LaTeX/wkhtmltopdf needed on Android.
- Wrapper: **`scripts/uim_pdf.sh <fail.md> [--nama NAMA.pdf]`** — validates (exists, inside `$HOME`,
  not a symlink), renders to `~/.hermes20/tmp/`, hands off via `uim_hantar.sh --ke 01-LAPORAN`,
  re-checks `sha256` **of the PDF** at the warehouse, deletes the temp file, prints `SIAP-PDF: <path>`.
- Fonts are mandatory: register `DejaVuSans.ttf` / `DejaVuSans-Bold.ttf` / `DejaVuSansMono.ttf` from
  `$PREFIX/share/fonts/TTF/`. Add a footer `UIM · <file> · halaman N` per page.
- `write_html` is fragile: wrap it, and on an unsupported tag fall back to plain text so a PDF is
  always produced (never let one weird table kill the deliverable).
- **Literal `<placeholder>` text inside backticks disappears** — `write_html` treats `<nama>` as an
  HTML tag. Sanitize: escape every `<` that does not open a real allowed tag, then re-extract text
  with `pypdf` and grep for the placeholder to prove it survived.
- Render **block by block** — parse headings/paragraphs/lists/tables/code/quotes out of the
  `markdown` HTML first, then render each with its own `try/except`. One whole-document
  `write_html` call cannot fall back per tag and gives no control over tables or code boxes.
- Tables: `pdf.table(borders_layout="ALL", headings_style=FontFace(emphasis="BOLD",
  fill_color=(233,233,233)), wrapmode=WrapMode.WORD)`; code: `multi_cell(fill=True)` on
  `(242,242,242)` plus a border drawn only when the page did not change.
- Recipe, the sanitizer bug that silently deletes `<nama>`-style text, and rasterizer-free
  verification: see `references/markdown-to-pdf-fpdf2.md`.
- **Deliver a PDF, never a `.txt`, when the user says "simpan dalam nota telefon".** A plain-text
  attachment can arrive with nothing the phone's Notes app will import — this user's verdict was
  *"fail yang kau bagi tak boleh buka pun dan dalam buku nota apa pun tak ada lagi"*. Render the
  PDF, hand it over with `MEDIA:<absolute path>` (Telegram shows it as a document), optionally
  attach the same PDF to email via SMTP, and name the exact save path in the reply.
- **`multi_cell(0, …)` right after a filled cell raises
  `FPDFException: Not enough horizontal space to render a single character`** — `x` is already at the
  right margin. Route every call through one helper: `def row(h, text, **kw): pdf.set_x(MARGIN);
  pdf.multi_cell(pdf.epw, h, text, **kw)`. Then no width-0 call can land off-page.
- **Verify by extraction, not by page count.** `pypdf` → join all pages → assert the strings the user
  actually cares about (address, password, section headings) appear; only then say "siap". A 4-page
  PDF that lost the URL is worse than no PDF.
- **Line-oriented renderer for plain-text notes:** when the source is a `.txt` instruction sheet
  rather than Markdown, skip `markdown`+`write_html` and walk the lines — `═══` → rule,
  `BAHAGIAN …` → filled bold heading, indented/command lines → `DejaVuSansMono` in a tinted box,
  everything else → body. Reusable script: `scripts/txt_note_pdf.py`.

## One-click button in the local console
Console = FastAPI app at `~/hermes-console/app.py` + `static/{index.html,app.js,style.css}`,
runit service `hermes-console`, `127.0.0.1:8787`.

- Endpoints to add: `GET /api/uim/state` (warehouse listing + candidate files + log tail),
  `POST /api/uim/hantar {path,kategori?}`, `POST /api/uim/pdf {path,nama?}`.
  Call the shell scripts with `subprocess.run([...], timeout=120)` — never `shell=True`.
- Security guard in the endpoint: `Path(p).resolve()` must start with `$HOME`, `p` must be a regular
  file; otherwise 400. This duplicates the script guard on purpose (defence in depth).
- UI: new tab (`data-tab="gudang"` + `<section id="tab-gudang" class="pane">`) with numbered
  plain-Malay steps, a candidate-file dropdown, and two big buttons (HANTAR / HANTAR SEBAGAI PDF,
  the PDF one only for `.md`).

## Pitfalls
- **`/sdcard` top level is not writable on modern Android.** Creating `/sdcard/<NEWDIR>` fails with
  `Permission denied` even though listing works. Use `/sdcard/Documents/<app>/`.
- **Symlink audits produce false positives**: `termux-setup-storage` legitimately creates
  `~/storage/*` and `~/phone` pointing into `/sdcard`. Exclude `$HOME/storage` and `$HOME/phone`
  or a "no symlinks" check reports ~12 bogus violations.
- **`/tmp` is not writable in Termux** — use `$PREFIX/tmp` (and `~/.hermes20/tmp` for PDF staging).
- Verify the copy, don't trust `cp`: compare `sha256sum` *and* `stat -c %s`, and delete the
  destination on mismatch so a truncated file never looks delivered.
- Never let secrets cross the boundary: `.env*`, `id_rsa*`, `id_ed25519*`, `*token*`, `auth.json`,
  `config.yaml` must stay in the factory; include them in the audit.
- Category names come from a hard allow-list — reject `--ke ../../etc` style input (path traversal).
- Do not create the warehouse with brace expansion split across lines; a stray newline produced a
  literal directory named `{01-LAPORAN,...}`. One `mkdir -p a b c` line instead.
- **fpdf2 core fonts (Helvetica/Courier) are latin-1**: `→ … — ·` raise
  `UnicodeEncodeError`/render as blanks. Always embed DejaVu TTF. Verify with
  `pypdf` text extraction and grep for `\ufffd` / `\u25a1`.
- **A catch-all `<[^>]+>` strip silently deletes real text.** Backticked literals like `<nama>` or
  `<fail.md>` arrive as plain text in the block buffer; stripping every tag-shaped run removes them
  from the PDF. Escape instead: `re.sub(r"<(?!/?(?:b|i|u|br|a)\b)", "&lt;", s)`. Catch it by
  diffing extracted text against the source, not by eyeballing page count.
- **`WrapMode.CHAR` splits words mid-character** (`uim_hanta` / `r.log`) even where there is room.
  Use `WrapMode.WORD` for tables and code (fpdf2 hard-splits genuinely overlong tokens itself);
  keep CHAR only for the last-resort plain-text fallback.
- **Don't stage converter stderr in the staging dir.** `2>"$TMPDIR/.err"` fails when that dir is
  read-only and hides the real error behind `Permission denied`; capture it with
  `ERRMSG="$(python3 … 2>&1 >/dev/null)"` instead.
- **Console POSTs need `X-Console-Token`** = `CSRF_TOKEN` fetched from `/api/meta`. Without it every
  POST answers `403 {"error":"token konsol tiada atau salah"}` — a curl test that forgets this looks
  like a broken endpoint.
- **`~/hermes-console` is not a git repo.** Copy `app.py`, `static/app.js`, `static/index.html`,
  `static/style.css` to `~/backups/console-<date>/` before editing; restore from there if
  `sv restart hermes-console` leaves it dead. Restart = `sv restart hermes-console`, then
  `curl http://127.0.0.1:8787/api/ping`.

## Verification
- `uim_hantar.sh <file>` → `SIAP: <phone path>` + matching `sha256` prefix + log entry.
- `uim_pdf.sh <file.md>` → `SIAP-PDF: <phone path>` + non-zero byte size + extractable text, and
  source tokens that usually vanish (`<nama>`, `→`, `·`) still present in the extraction.
- `uim_semak.sh` → no output, exit 0.
- Deliberate violations (a symlink to `/sdcard`, a stray `.env.uji`, `/etc/hostname` through the
  API) → exit 1 / HTTP 400 with the exact path.
- Console stays healthy after edits: `/api/ping`, `/api/overview`, `/api/uim/state` all 200 and all
  original tabs still present (`grep -c 'data-tab' static/index.html` must not decrease).

## Support files
- `scripts/uim_hantar.sh` — guarded one-way copy with category routing, hash rollback, logging.
- `scripts/uim_semak.sh` — silent auditor for forbidden symlinks and secrets on phone storage.
- `scripts/uim_pdf.sh` — Markdown → PDF → warehouse wrapper (expects `md_to_pdf.py` beside it; the
  live converter is `~/.hermes20/scripts/md_to_pdf.py`, ~25 KB, backed up nightly — do not duplicate
  it here, restore from the `~/.hermes20` backup if lost).
- `scripts/txt_note_pdf.py` — line-oriented `.txt` → A4 PDF renderer (rule lines, `BAHAGIAN …`
  headings, mono command boxes) plus the `row()` x-reset helper that prevents fpdf2's
  "Not enough horizontal space to render a single character". For plain-text instruction sheets,
  not Markdown.
- `references/termux-phone-storage-boundary.md` — permission findings, test matrix, log format.
- `references/markdown-to-pdf-fpdf2.md` — fpdf2 block-render architecture, table/WrapMode settings,
  the `<nama>` sanitizer bug, rasterizer-free verification, wrapper failure-path tests.
