# Tab berasingan + pengeksport data sendiri (isolated-tab pattern)

Use when the request is *"bina RUANG BAHARU yang berasingan … tidak bercampur dengan tab/kerja
sebelum ini"*. The visible tab is only half of it: the data must also come from its own directory,
its own exporter and its own read-only endpoint, so no existing renderer, payload or file is shared.

Measured on `~/hermes-console` (2026-11-18): `app.py` 2,945 lines, `static/app.js` 2,404 lines.
A normal 6-touch-point insertion (see `adding-a-console-tab.md`) would have added ~140 lines to
`app.js`. The isolated variant added **2 lines to `app.js`** and a 6.9 KB standalone file.

## Shape

```
~/.hermesNN/scripts/export_<key>.py        # writes the data, tolerant per-section
~/.hermesNN/reports/<key>/                 # status.json sejarah.json larian.json cron.json <insiden>.md
~/hermes-console/static/tab-<key>.js       # all UI logic, IIFE, own helpers
```

- `app.py`: 3 blocks only — a constants/helpers block, `GET /api/<key>`, `GET /api/<key>/fail/{nama}`.
- `index.html`: 1 nav button, 1 `<section id="tab-KEY" class="pane">`, 1
  `<script src="/static/tab-KEY.js">` **before** `app.js`.
- `app.js`: `if (S.tab === "KEY") await window.loadSandaran();` plus one `TABS` entry.
  `TABS` also feeds `?tab=` handling, the Ctrl-K palette and typing work, so ship the entry —
  keep `loadTab()`'s line first as `await window.KEY()` so a missing script throws inside the
  existing try/catch instead of killing boot.

Classic scripts share the global scope, so `tab-<key>.js` may call `api()` / `esc()` from `app.js`
**at call time**, not at load time. Rule: no top-level DOM access and no top-level call into
`app.js` symbols — wrap everything in `(function(){ … })()` and expose exactly one function
(`window.loadX = async function(){…}`). The smoke test can then `require()` the file with a fake
`document`.

## Exporter contract

- Every section in its own `try/except`; a Failed `git ls-remote` (SSH/network down) writes
  `"commit_remote": "remote_tidak_dapat_disemak"` and `"segerak": null`, **never** aborts the run.
- `subprocess.run([...], capture_output=True, text=True, timeout=25)` with a list; a helper
  `git(*args) -> (ok, text)` keeps six call sites readable.
- Compute `segerak` by comparing full hashes (`git rev-parse HEAD` vs `git ls-remote origin HEAD`),
  and read plain `git ls-files | wc -l` / `du` of `.git` for the honest headline numbers.
- One combined print at the end:
  `{"ok": true, "folder": …, "fail": {"status.json": "ok", …}}` so a cron/curl caller sees per-file status.
- Log parsing: classify each line into a closed vocabulary (`commit`, `push-berjaya`, `dibatalkan`,
  `tiada-remote`, `push-gagal`, `diabaikan`, `gagal`) and keep the raw message beside the class.
  The UI maps class → `[badge, "maksud dalam bahasa manusia"]`; never show the class name alone.
- Malay prose report (`insiden-*.md`) has a line budget in the brief (here 20–30). Write it as a
  literal block in the script and check `wc -l` after the first run — a generous draft came out
  33 lines and needed two merges, not a rewrite.

## Endpoint contract (read-only + whitelist)

```python
SANDARAN_FILES = ("status.json", "sejarah.json", "larian.json", "cron.json", "insiden-….md")

# refresh when missing OR stale, so the tab reports the CURRENT commit, not a frozen one
basi = True
try:
    basi = time.time() - (DIR / "status.json").stat().st_mtime > 300
except Exception:
    basi = True
if data["status.json"] is None or basi:
    eksport = _eksport()          # subprocess.run(["python3", script], timeout=60)
    data = {n: _baca(n) for n in SANDARAN_FILES}
if data["status.json"] is None:
    return {"ok": False, "sebab": "…", "folder": str(DIR), "eksport": eksport}
```

- `_baca()` returns `None` on any exception (missing file, bad JSON) — callers use `… or {}`.
- The combined payload carries `status`, `sejarah` (list, not the wrapper), `larian` (list),
  `cron`, `insiden_md` (text), and `fail: [{nama, ada, saiz, url}]` so the UI renders download
  links without hardcoding paths.
- Download route: `if nama not in SANDARAN_FILES: raise HTTPException(400, …)`, then
  `f.is_file()` else 404, then `FileResponse(f, filename=nama)`. A tuple membership test cannot be
  traversed; do **not** build the path first and validate afterwards.

## Verification matrix that actually proves it

```
curl -s -o /dev/null -w '%{http_code}' 127.0.0.1:8787/                                   # 200
curl -s 127.0.0.1:8787/api/K | head -c 600                                               # real commit hash
curl -s 127.0.0.1:8787/ | grep -c 'tab-K'                                                # ≥1
curl -s -o /dev/null -w '%{http_code}' 127.0.0.1:8787/api/K/fail/status.json             # 200
curl -s -o /dev/null -w '%{http_code}' 127.0.0.1:8787/api/K/fail/../../.env              # 404
curl -s -o /dev/null -w '%{http_code}' --path-as-is 127.0.0.1:8787/api/K/fail/../../.env # 404
curl -s -o /dev/null -w '%{http_code}' 127.0.0.1:8787/api/K/fail/.env                    # 400
curl -s -o /dev/null -w '%{http_code}' 127.0.0.1:8787/api/K/fail/secrets.txt             # 400
```

Delete the data file and re-curl once (`mv status.json x && curl … && rm x`) to prove the
auto-export path — otherwise "it regenerates itself" is untested.

Prove nothing else moved without a git repo (the console isn't one):
`ls -l --time-style=+%H:%M app.py static/app.js static/style.css static/index.html static/tab-K.js`
— `style.css` and any untouched file must keep their old mtime **and** byte size, which is stronger
evidence than a line count. Then `grep -n` the touched files for the exact added lines.

## Browserless render proof for a standalone tab file

```js
global.document = { getElementById: (id) => (els[id] ||= {id, innerHTML:"", textContent:""}),
                    addEventListener: () => {} };
global.window = global;
global.api = async () => (/* real JSON read from reports/<key>/ */);
require(process.env.HOME + "/hermes-console/static/tab-<key>.js");
loadX().then(() => { for (const k of ["x-cards","x-table"]) console.log(k, els[k].innerHTML.length); });
```

Assert per-panel `innerHTML.length` and print a 110-char slice — that catches "table renders but
every cell is `undefined`", which a length check alone misses. Write the harness inside the project
(`.smoke-<key>.js`), run it, delete it: `/tmp` is unwritable/noexec on Termux.

## Pitfalls specific to this pattern

- **`curl …/fail/../../.env` can answer 404 for the wrong reason.** curl squashes `../` client-side,
  so the request becomes `/.env` and the 404 proves nothing about the route. Always repeat with
  `--path-as-is`; expect the path-param route to miss entirely (`/` isn't matched by `{nama}`),
  plus a 400 for `fail/.env` (name not in the tuple) to show the whitelist itself fired.
- **Generated reports that live inside the repo the backup job commits cause nightly churn.**
  `~/.hermesNN` is often itself the git repo the 02:00 backup pushes, so `reports/<key>/*.json`
  becomes tracked the first night and then every export dirties the tree → one tiny commit per
  night, forever. It also makes `segerak` flap if the UI compares HEAD to remote without noticing
  the working tree. Say this out loud in the report and offer `reports/<key>/` in `.gitignore`;
  don't quietly add it yourself when the brief fixed the write scope.
- **A brief containing a commit hash must not become a constant.** The payload has to come from
  `git rev-parse HEAD` at export time: the first verified run already showed `cf40661`, and ten
  minutes later the real HEAD was `ee11426` because another job pushed. Quote whichever hash the
  endpoint returns, and note in the reply that it moves.
- **Refreshing only "if the file is missing" serves week-old data.** Add the mtime TTL (300 s here).
  Cost: one `git ls-remote` (~1–3 s) per refresh, paid at most once per TTL window, not per poll.
- **`python3 -c` inside `execute_code` cannot always spawn `python3`** (`PermissionError: [Errno 13]`
  on `subprocess.run(["python3", …])`). Run exporters/harnesses through the `terminal` tool instead
  of nesting them in the sandboxed script.
