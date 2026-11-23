# Patching the in-repo Hermes console (127.0.0.1:8787)

Session-verified notes for **extending an existing** FastAPI console (`~/hermes-console`) rather than
writing a new one. Applies when the user says "tambah dalam konsol", "gabung jadi satu tempat",
"tukar gaya konsol".

## Shape of the app

```
~/hermes-console/
  app.py            FastAPI (~3k lines): /api/orgchart, /api/live/state, /api/web, /api/buka, /api/fleet
  static/index.html <button class="tab" data-tab="X"> + <section id="tab-X" class="pane">
  static/app.js     loadX() per tab, TABS title map, `if (S.tab === "x") await loadX();`
  static/style.css  :root tokens; append overrides at the END, never rewrite
  tools/patch_*.py  idempotent additive patch scripts (one per feature/tab)
```

## The patch-script pattern (copy this, don't hand-edit three files)

```python
def once(path, old, new, label, sentinel):
    t = path.read_text(encoding="utf-8")
    if sentinel in t:            # idempotent re-run
        print(f"skip (ada): {label}"); return
    if old not in t:             # fail loud, never silently skip
        print(f"GAGAL anchor: {label}"); sys.exit(2)
    path.write_text(t.replace(old, new, 1), encoding="utf-8")
    print(f"ok: {label}")
```

Anchors that exist in this repo (verified):

| Target | Anchor |
|---|---|
| tab button | `    <button class="tab" data-tab="web">WEB UI</button>` |
| pane | `  <section id="tab-gudang" class="pane">` (insert BEFORE) |
| loader JS | `/* ---------------- gudang (hantar ke telefon) ---------------- */` |
| routing | `if (S.tab === "gudang") await loadGudang();` |
| tab titles | `["gudang", "GUDANG"]` |
| init hooks | `  setTab(S.tab);` |
| API block | `# --- Termux:Boot ---…` comment line |

Back up all three files first (`cp app.py app.py.bak-<feature>`, same for index.html / app.js).

## Auth for POST endpoints

POST/PUT/DELETE require the CSRF header or they answer
`{"error":"token konsol tiada atau salah"}`:

```bash
TOK=$(curl -s http://127.0.0.1:8787/api/meta | python3 -c "import sys,json;print(json.load(sys.stdin)['csrf'])")
curl -s -X POST http://127.0.0.1:8787/api/buka \
  -H 'Content-Type: application/json' -H "X-Console-Token: $TOK" -d '{"target":"chrome"}'
```

`app.js`'s `api()` helper already injects `X-Console-Token` from `S.meta.csrf`, so the UI needs nothing.

## Verification (always run all four)

```bash
node --check ~/hermes-console/static/app.js      # JS syntax gate
cd ~/hermes-console && python3 -c "import ast;ast.parse(open('app.py').read())"
sv restart hermes-console && sleep 5
curl -s -o /dev/null -w '%{http_code}\n' 'http://127.0.0.1:8787/?tab=pusat'   # 200
curl -s http://127.0.0.1:8787/ | grep -c 'id="my-new-panel"'                  # 1
curl -s http://127.0.0.1:8787/api/myendpoint | head -c 300
```

Style changes are cached hard in the phone browser. Do **both**:

1. Version the stylesheet link so the browser is forced to refetch:
   `python3 tools/patch_cssver.py` (or hand-patch
   `<link rel="stylesheet" href="/static/style.css">` → `.../style.css?v=YYYYMMDD`).
   Without this the user opens the page, sees the old look, and reports "sama saja".
2. Still tell the user **Ctrl+Shift+R** after the patch.

## Restart can wedge the service (recovery recipe)

`sv restart hermes-console` sometimes returns `timeout: run: hermes-console: (pid N) … got TERM`
and the port goes dark (`curl → 000`) because the old `app.py` will not exit while a keep-alive
connection (the open browser tab / an SSE stream) holds it.

```bash
pgrep -af "python3 -u app.py"            # confirm exactly one stale pid, note it
kill -9 <pid>                            # plain pkill -f "app.py" can match your own shell
sv up hermes-console && sleep 6
sv status hermes-console | head -1       # want: run: hermes-console: (pid …)
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8787/   # 200
```

Report the brief outage honestly if it happened; do not claim the restart was clean.

## Data bugs this console is prone to (fix the data, not the card)

- **Org chart shows `0 SISTEM`.** `api_orgchart()` builds the tree from `md_table(get_section(SOUL.md, "ENJIN"))`.
  When SOUL.md is rewritten (v5 dropped the ENJIN table) the table is empty and the chart collapses while
  `totals.agents` still reports 282. Fix: keep a module-level `SYS_FALLBACK` dict of the eight engines
  (agent_factory … memory_manager) and use it when the parsed list is empty.
- **Phantom "2 AKTIF" runs at 0 %.** `_active_runs()` accepts status `planned`; abandoned runs stay
  `planned` for days. Filter `planned` rows older than ~6 h (`_aged_h(meta["created"])`) instead of
  deleting the run files — the history tab still shows them.
- **`address already in use` repeating in the console log** = a second instance started while the first
  still held 8787 (keeper cron + manual `sv restart`). Restart via `sv restart hermes-console` only;
  confirm one `app.py` process before restarting.

## Panels worth having on the "one place" page

`/api/web` (dashboard URL + LAN + login file + port probe), `/api/fleet` (per-gateway alive flag from
`pgrep -f`, log age from `st_mtime`, SKILL.md count, ATC flag, `/proc/meminfo`, `os.statvfs`), and the
org-chart counters rendered as chips: **BEKERJA / BERFIKIR / REHAT** (active, queued, remainder). Refresh
all of them on one 60 s timer started from the pane's init function, guarded by a `webInit` flag so
re-entering the tab does not stack timers.

## Presenting the result (user preference)

Lead with the evidence block (endpoint output, `node --check` line, HTTP code), then a short table of what
changed, then a numbered 3–4 option list in Malay. Skip prose descriptions of what the panel "will" show —
paste what the endpoint returns.
