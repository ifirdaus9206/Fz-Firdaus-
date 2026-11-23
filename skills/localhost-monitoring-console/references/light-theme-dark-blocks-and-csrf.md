# Light theme: remaining dark blocks, and writing to a console API

Follow-up to `contrast-and-tunnel-exposure.md`. Both lessons came from the SATU PUSAT console
(port 8787) after the user said "aku napak macam tadi saje … yang hitam tu kau tukar warna lain
lebih terang" — i.e. the page was light but ONE block in the middle was still black.

## 1. A dark raster hero image is not a CSS background

The page had a light theme applied correctly, yet a black rectangle stayed in the middle.
Cause: a hero banner built from an `<img>` plus an absolutely-positioned overlay:

```html
<div class="hero-live">
  <img class="hero-img" src="/static/img/hero-control.png" alt="">
  <div class="hero-overlay"> … MISSION CONTROL / PUSAT PEMANTAU … </div>
</div>
```

```css
.hero-live{background:#050807}                       /* dark even in light mode */
.hero-img{display:block;object-fit:cover;opacity:.95}
.hero-overlay{position:absolute;inset:0;…}
```

No `body.light` rule touched these, so the image and its dark wrapper survived the theme switch.
Token overrides cannot fix a **raster image** — you must hide it.

```css
body.light .hero-live{background:#eef2f0!important;border:1px solid #e4e4e7!important}
body.light .hero-img{display:none!important}
body.light .hero-overlay{
  position:static!important;inset:auto!important;   /* stop absolute overlay */
  background:linear-gradient(135deg,#ecfdf5,#f4f4f5)!important
}
body.light .hl-kicker{color:#15803d!important;opacity:1!important}
body.light .hl-title{color:#18181b!important}
body.light .hl-chips span{background:#fff!important;border:1px solid #d4d8dc!important}
```

**Rule:** when auditing a light theme, grep for `<img`, `background:#0…`, and `position:absolute`
overlays — not just CSS variables. A dark *picture* is invisible to token-based audits.

**Verification that proves it:** `grep -c 'hero-img{display:none' <(curl -s "$U/static/theme.css?v=N")`
should return ≥1, and the served HTML must contain `body class="light"` so the theme does not
depend on JS running.

## 2. Write endpoints need the console CSRF token

Every mutating call on this console is rejected without a token:

```bash
curl -s -X POST http://127.0.0.1:8787/api/watak -H 'Content-Type: application/json' -d '{...}'
# {"error":"token konsol tiada atau salah"}
```

The token lives at `GET /api/meta` and is sent as the `X-Console-Token` header (the browser JS
does this automatically, so a working UI hides the requirement from you):

```bash
T=$(curl -s http://127.0.0.1:8787/api/meta | python3 -c 'import sys,json;print(json.load(sys.stdin)["csrf"])')
curl -s -X POST http://127.0.0.1:8787/api/watak \
  -H "X-Console-Token: $T" -H 'Content-Type: application/json' \
  -d '{"name":"Ujian Watak"}'
```

Full CRUD smoke test (create → edit → list → delete) is the only honest proof a management panel
works. Assert the count moves and returns to its original value:

```bash
# POST → count 282→283 · PUT → ketua:true · GET → ketua:['ujian-watak'] · DELETE → 282
```

## 3. Roster CRUD pattern (agents.json)

Adding/editing/deleting personas edits one JSON catalog. Do it through the API, not by hand:

- `POST /api/watak` → append; `PUT /api/watak/{slug}` → merge fields; `DELETE /api/watak/{slug}`
- Back up first: `shutil.copy2(path, path.with_suffix(".bak-watak"))`
- Strip and validate the name; slug from name; reject duplicate slugs
- Return the new count so the UI can refresh `282` without a second request
- A "Ketua" flag must be exclusive — setting it on one persona clears it on the others

## 4. When the user asks for a permanent tunnel URL

A `cloudflared tunnel --url http://127.0.0.1:PORT` **quick tunnel** gets a new hostname on every
restart; it cannot be pinned. A stable URL needs a **named tunnel** (Cloudflare account + a domain
you control) or a VPN mesh address. Say this plainly instead of promising "URL kekal" — and check
`which tailscale` before offering Tailscale as the fallback.
