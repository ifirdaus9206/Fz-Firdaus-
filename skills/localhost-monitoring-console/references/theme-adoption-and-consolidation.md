# Theme adoption + consolidation (console becomes the only place)

Session-verified 2026-11-23 on `~/hermes-console` (FastAPI, tabbed SPA) when the user says
"tukar gaya macam Dashboard Hermes Agent", "gabung jadi satu tempat", "buang tempat kedua".

## 1. Steal the tokens from the built UI, don't guess

The Hermes dashboard ships as a built SPA; its design tokens are plain CSS variables:

```bash
D=~/.hermes20/tools/hermes-source/hermes-agent/hermes_cli/web_dist
ls "$D/assets" | head                 # index-*.css is the bundle
grep -o ":root{[^}]*}" "$D/assets/index-"*.css | head -c 1500
grep -o "#[0-9a-fA-F]\{6\}" "$D/assets/index-"*.css | sort | uniq -c | sort -rn | head -14
grep -o "font-family:[^;}]*" "$D/assets/index-"*.css | sort -u
```

Verified tokens (dark/amber theme):

```
--background:#170d02  --midground:#ffac02  --foreground:#fff
--radius:.5rem  --theme-base-size:15px  --theme-line-height:1.55
accent set: #4ade80 green · #fb2c36 red · #3080ff blue · #ffbd38 amber
fonts: "Collapse" (sans) · "Courier Prime" / "JetBrains Mono" (mono)
```

Put them in a **separate `static/theme.css`** loaded after `style.css`, so the old stylesheet stays
intact and the theme can be removed in one line if the user dislikes it.

## 2. Retro-fit a sidebar without rewriting the DOM

The console is a flat `<header class="top">` + `<nav class="tabs">` + `<main>` + `<section class="pane">`
layout. Do **not** restructure it — add a fixed nav and shift the content:

```html
<nav class="side" id="side">
  <div class="brand">…</div>
  <button data-go="pusat" class="on">PUSAT</button>   <!-- data-go == data-tab of an existing pane -->
  …
</nav>
```

```css
.side{position:fixed;top:0;left:0;bottom:0;width:236px}
header.top{padding-left:calc(236px + 14px)!important}
main{padding-left:calc(236px + 4px)!important}
nav.tabs{display:none!important}          /* legacy tabs stay functional, just invisible */
@media (max-width:900px){ .side{position:static;display:flex;overflow-x:auto} }
```

Wire it in JS with the **existing** `setTab()` global and mirror the active state:

```js
document.querySelectorAll('#side button[data-go]').forEach(b => b.addEventListener('click', () => {
  document.querySelectorAll('#side button[data-go]').forEach(x => x.classList.remove('on'));
  b.classList.add('on');
  if (typeof setTab === 'function') setTab(b.dataset.go);   // no new router needed
}));
```

Because every sidebar item maps to an existing `data-tab`, nothing can regress: all old panes and
their loaders keep working.

## 3. HUD bar + theme toggle

Put the cross-cutting numbers in one row above the panes (gateway alive flags, skill count, RAM),
fed by the existing `/api/fleet` every 30 s, and a toggle that persists:

```js
btn.addEventListener('click', () => {
  document.body.classList.toggle('light');
  localStorage.setItem('console_theme', document.body.classList.contains('light') ? 'light' : 'dark');
});
```

Light theme = a `body.light{ --bg:… --ink:… }` override block; every component already reads the
variables, so no per-component work is needed.

## 4. Cache-bust BOTH stylesheets

```html
<link rel="stylesheet" href="/static/style.css?v=YYYYMMDDb">
<link rel="stylesheet" href="/static/theme.css?v=1">
```

Without the version bump the phone browser re-serves the old CSS and the user reports
"sama saja" (seen twice this session). Bump on every visual change and still tell them Ctrl+Shift+R.

## 5. Consolidation checklist (user: "semuanya satu tempat")

1. Pick the survivor (here: `http://127.0.0.1:8787/?tab=pusat`) and say so explicitly.
2. Stop the losers **and stop them coming back**:
   ```bash
   sv down hermes-dash-tunnel; sv down hermes-dashboard
   touch $PREFIX/var/service/hermes-dash-tunnel/down $PREFIX/var/service/hermes-dashboard/down
   ```
   `sv down` alone is not enough — the Termux:Boot script runs `sv up` for those services on every
   boot. Either create the `down` files (runit honours them) or delete those `sv up` lines.
3. Kill the noise cron that reported the secondary URL: `cronjob action=list` → `action=remove`
   (here `b3aa5823840f "URL dashboard berubah"`, `*/15`).
4. Move what the loser uniquely showed into the survivor first (URL, login user, port probe →
   `/api/web` panel) so nothing is lost by switching.

## 6. Why the second URL kept changing (root cause worth stating)

Cloudflare **quick tunnels** get a new hostname every time the process restarts, and they die on
network switch / VPN toggle. The phone had a VPN icon and the tunnel restarted repeatedly, so the
dashboard URL churned and the "URL berubah" cron fired. The gateway itself never dropped (log
continuous, wake lock HELD) — it was the tunnel, not Termux. Prefer a stable address (Tailscale
`100.x` or a named tunnel) and stop notifying on churn.

## 6b. `sv down` does not stop an already-spawned `cloudflared`

Measured 2026-11-23: after `sv down hermes-dash-tunnel` the service read `down:` yet
`https://<old>.trycloudflare.com/` still answered **302** — the tunnel process was an orphan from the
supervised start. Nothing on the user's side reveals this; they just see "masih ada lagi".

```bash
pgrep -af "cloudflared tunnel"        # filter out your own bash wrapper
kill -9 <pid>                         # explicit pid, never pkill -f with a pattern you typed
curl -s -m 12 -o /dev/null -w "awam=%{http_code}\n" https://<old>.trycloudflare.com/   # 502/000 = dead
```

So the consolidation proof is **two** probes: `sv status` = `down`, *and* the old public URL no
longer answers `302`. Report both, otherwise the user will paste the old URL back and ask why it
still works.

## 6c. Adding data panels: three endpoints that pay off immediately

All are read-only, cheap, and give the "everything in one place" page real content
(patterns verified on the same console):

```python
@app.get("/api/skills")      # rglob("SKILL.md"), skip node_modules,
                            # desc = first "description:" line from the frontmatter, category = parent dir
@app.get("/api/cron")        # <hermes home>/cron/jobs.json
@app.get("/api/email")       # ~/vault/email-inbox: per-folder *.md counts + last 12 log lines
```

Two traps:

1. **`schedule` in `jobs.json` is a dict**, not a string:
   `{"kind":"cron","expr":"0 8 * * *","display":"0 8 * * *"}`. Returning it as-is renders
   `[object Object]` in the panel. Normalise server-side:
   `sc = sc.get("expr") or sc.get("cron") or sc.get("value") or sc.get("kind")` and `str()` it.
   `last_run_at` likewise wants `str()`.
2. **A 200 from the console only proves the OLD process is alive.** After adding an endpoint,
   probe the endpoint itself (`curl …/api/cron | head -c 120`) — that is what proves the restart
   took effect. If the field still looks wrong, the restart never happened (see
   `termux-runit-services` → `references/uvicorn-service-restart-hangs.md`).

Front-end shape that worked: one `<div class="svc-row">` per item with
`<b>name</b> <span class="tag …">STATE</span>` plus a `hint mono` detail line, `chip-live` pills for
counts, and a search `<input>` that filters a cached array client-side (no extra requests).

## 7. Verification

```bash
curl -s -o /dev/null -w 'theme.css=%{http_code}\n' http://127.0.0.1:8787/static/theme.css   # 200
curl -s http://127.0.0.1:8787/ | grep -c 'id="side"'                                        # 1
curl -s http://127.0.0.1:8787/ | grep -c 'hud-gw1'                                          # 1
curl -s -m 5 -o /dev/null -w '9119=%{http_code}\n' http://127.0.0.1:9119/                   # 000 (dead)
sv status hermes-dashboard hermes-dash-tunnel                                               # down
node --check ~/hermes-console/static/app.js
```
