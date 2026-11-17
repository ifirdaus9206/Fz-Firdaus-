# Adding a tab to an already-running console (no rewrite, no regressions)

Trigger: *"tambah tab X dalam konsol 127.0.0.1:8787"* on a live `~/hermes-console`
(`app.py` ~2.7k lines, `static/{index.html,app.js,style.css}`), supervised by runit as
`hermes-console`. The deliverable is a working tab + proven curl evidence, **with every
existing tab still alive**. Do not restructure the app; match the surrounding style.

## 1. Back up before touching (if not already done)

```bash
ls ~/backups/console-YYYYMMDD/   # app.py.bak, app.js.bak, index.html.bak, style.css.bak
```
If the caller already made one, do not make another and do not delete it. That folder is the
rollback path named in the report.

## 2. Six touch points — a tab that is wired in five places looks "half dead"

| # | File | What |
|---|---|---|
| 1 | `index.html` nav | `<button class="tab" data-tab="KEY">LABEL</button>` after the last tab |
| 2 | `index.html` main | `<section id="tab-KEY" class="pane">…</section>` |
| 3 | `app.js` `loadTab()` | `if (S.tab === "KEY") await loadKEY();` |
| 4 | `app.js` `TABS` | `["KEY","LABEL"]` — otherwise `?tab=KEY` deep link is rejected at boot |
| 5 | `app.js` boot/init | `$("#…").addEventListener(...)` for the new buttons |
| 6 | `app.js` | `loadKEY()` + render helpers |

The tab click handler is generic (`$$(".tab").forEach(t => …setTab(t.dataset.tab))`), so #1+#3 are
enough to switch panes — but #4 is what makes `/?tab=KEY` and the command palette work.

Grep proof after editing:

```bash
grep -c 'data-tab=' static/index.html          # old count + 1
curl -s 127.0.0.1:8787/ | grep -o 'data-tab="[a-z]*"' | tr '\n' ' '
```

## 3. Backend shape (subprocess, list args, no shell)

```python
UIM_HANTAR = Path.home() / ".hermes20" / "scripts" / "uim_hantar.sh"

def _uim_jalan(skrip: Path, args: list[str]) -> dict:
    if not skrip.exists():
        raise HTTPException(503, f"skrip belum sedia: {skrip.name}")   # sibling still building it
    try:
        p = subprocess.run([str(skrip), *args], capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        raise HTTPException(504, f"{skrip.name} tamat masa (120s)")
    out = ((p.stdout or "") + (p.stderr or "")).strip()
    return {"kod": p.returncode, "output": out[:8000], "stdout": p.stdout or ""}
```

- Never `shell=True`; the arguments are a list.
- `returncode` travels to the UI as `ok: kod == 0` — do not infer success from output text alone.
- Parse the script's contract lines (`SIAP: <path>`, `SIAP-PDF: <path>`,
  `HANTAR-TELEGRAM: MEDIA:<path>`) into `laluan` / `telegram` fields. Fall back to
  `MEDIA:{laluan}` when the script only printed `SIAP`.
- A missing collaborator script is **503**, not a 500 and not a fake success — the UI can then say
  "belum sedia" instead of looking broken.
- A "list the warehouse" GET should reuse the existing `tail()` helper for the log, cap the scan
  (20 candidates, newest first), skip `_LOG`-style dirs and symlinks, and return a `ringkasan`
  (`{fail, saiz}`) so the UI does not sum numbers client-side.

## 4. Path safety — the helper worth copying

Two independent conditions: **resolved inside `$HOME`** and **regular file**.

```python
HOME_REAL = Path(os.path.realpath(str(Path.home())))

def _uim_sumber(path_val) -> Path:
    if not isinstance(path_val, str) or not path_val.strip():
        raise HTTPException(400, "path diperlukan")
    p = Path(path_val.strip()).expanduser()
    if not p.is_absolute():
        p = HOME_REAL / p
    try:
        real = Path(os.path.realpath(str(p), strict=True))   # strict: symlinks resolved, must exist
    except (FileNotFoundError, NotADirectoryError):
        raise HTTPException(400, f"fail tidak wujud: {path_val}")
    if real != HOME_REAL and HOME_REAL not in real.parents:
        raise HTTPException(400, "path mesti di dalam $HOME")
    if not real.is_file():
        raise HTTPException(400, "path bukan fail biasa")
    return real
```

Why `Path.parents` and not `str.startswith(HOME)`: `startswith` accepts
`/data/data/com.termux/files/homeX/evil.md`. `parents` is component-wise, so it cannot.
`strict=True` also collapses `..` and rejects dangling symlinks before any `stat`.

A symlink that *resolves outside* `$HOME` is rejected here even though the path string is inside —
test precisely that case.

## 5. Frontend — reuse the theme, do not invent one

Existing classes cover everything: `panel`, `ph`/`h2`/`hint`, `pbody`, `workbar`, `btn`,
`btn primary`, `btn gold`, `bodytext`, `pre.log`, `grid2`, `card`. A numbered 4-step "LANGKAH"
block only needs an inline `<ol style="…">`; no new CSS file section.

Renderer shape (keeps the surrounding conventions):

```js
async function loadGudang() {
  const d = await api("/api/uim/state");
  S.gd = d;                                  // cache for dependent decisions
  const lama = $("#gd-calon").value;         // preserve selection across reloads
  $("#gd-calon").innerHTML = d.calon.map(c =>
    `<option value="${esc(c.laluan)}">${esc(c.nama)}</option>`).join("");
  if (lama && d.calon.some(c => c.laluan === lama)) $("#gd-calon").value = lama;
  gdPilih();                                 // enable/disable the secondary button
}
```

- `esc()` every server string; `dt()`/`num()` reuse instead of local formatters.
- POST through the existing `api()` helper so the CSRF header and `AbortController` are inherited;
  pass `timeout: 130000` for a 120 s server-side timeout.
- Gate the narrower action on the file type (`$("#gd-pdf").disabled = !/\.md$/i.test(path)`) and
  re-evaluate it after every reload, otherwise a stale enabled button sends a doomed request.
- On success print the **full path** plus the human instruction ("Buka app Files → Documents →
  UIM"), then refresh the warehouse list — the user's next question is always "where did it go".
- Disable both buttons while a request is in flight and restore them in `finally`.

## 6. Verification sequence (this order, every time)

```bash
python3 -c "import ast;ast.parse(open('$HOME/hermes-console/app.py').read());print('AST OK')"
node --check ~/hermes-console/static/app.js && echo 'JS OK'      # node exists in Termux here
sv restart hermes-console; echo EXIT=$?; sleep 3
curl -s http://127.0.0.1:8787/api/ping
TOK=$(curl -s http://127.0.0.1:8787/api/meta | python3 -c "import sys,json;print(json.load(sys.stdin)['csrf'])")
curl -s -X POST http://127.0.0.1:8787/api/uim/hantar -H 'Content-Type: application/json' \
     -H "X-Console-Token: $TOK" -d '{"path":"<real .md in $HOME>"}'
ls -la /sdcard/Documents/UIM/01-LAPORAN | tail -5
```

- **POST needs `X-Console-Token`.** The guard middleware returns 403 for every POST without it.
  A test written as "curl -d … must return ok" fails against a perfectly healthy endpoint. Fetch
  the token from `/api/meta` (`csrf`) in the same script; never exempt the new route from the
  guard to make testing easier (prove it still 403s without the header).
- Destination filename ≠ source filename: `uim_hantar.sh` appends `-YYYYMMDD-HHMMSS` when the name
  already exists. Assert the `laluan` returned by the API, not a hardcoded path.
- `curl -o /tmp/x.json` silently produces nothing on Termux (`/tmp` unwritable). Use `-i` and read
  the body from stdout, or write under `$HOME`.
- Prove the old surface: `/api/overview`, `/api/agency/health`, tab count in `/`, `/static/app.js`
  200. "I only added a tab" is a claim until these answer.

Negative matrix that must be 400:

| body | expected |
|---|---|
| `{"path":"/etc/hostname"}` | 400 `fail tidak wujud` / outside `$HOME` |
| `{"path":"<a directory inside $HOME>"}` | 400 `path bukan fail biasa` |
| symlink inside `$HOME` → `/sdcard/...` | 400 `path mesti di dalam $HOME` |
| `{"kategori":"99-X"}` | 400 `kategori tidak sah` |
| PDF endpoint on a `.css`/`.png` | 400 `PDF hanya untuk fail .md` |

Run the outside-`$HOME` test even on Android, where `/etc/hostname` may not exist: the 400 is still
correct, but say in the report *which* rule fired (`fail tidak wujud` vs `mesti di dalam $HOME`) —
they are different proofs.

## 7. Reporting

Line counts added per file come from the backup, not from memory:

```bash
for f in app.py static/app.js static/index.html; do
  echo -n "$f: "; diff -u ~/backups/console-YYYYMMDD/$(basename $f).bak ~/hermes-console/$f | grep -c '^+[^+]'
done
```

State plainly when a collaborator script (`uim_pdf.sh`) does not exist yet: the endpoint answers
503, the button is wired, and real PDF generation is **unverified**. Do not dress that up as a
passing test.
