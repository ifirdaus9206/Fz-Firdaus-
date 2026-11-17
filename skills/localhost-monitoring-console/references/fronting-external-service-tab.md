# Fronting another service from the console ("buat app macam aku bagi")

Session 2026-11-17. Request: *"semak URL ni … aku nak buat app macam tu, mudah untuk susun atur ruang
kerja … jangan ikut 100 kalau tak boleh, cara susun app tu yang aku nak"*. The linked URL turned out
to be **the user's own Hermes dashboard on their PC**, not a third-party app.

## 0. Probe the link before framing it

```bash
curl -sSL -m 30 "<url>" -o ~/tmp_probe/page.html -w "HTTP:%{http_code} SIZE:%{size_download}\n"   # never /tmp
grep -o -i "<title>[^<]*</title>" ~/tmp_probe/page.html
grep -o -i "password-login\|nous-research\|Sign in" ~/tmp_probe/page.html | head
```

`<title>Sign in — Hermes Agent</title>` + Nous fonts = this product's own dashboard. Do **not** open
with "that's someone else's machine" — in this session it was theirs and the warning read as an
accusation. Instead check what already ships locally before proposing a build:

```bash
hermes --help | tr ',' '\n' | grep -E "dashboard|serve|gui|kanban|project"
hermes dashboard --help | head -20
```

Answer that lands: *"boleh, dan tak perlu bina dari kosong — kita ada app yang sama, cuma belum
dihidupkan"* + the missing pieces (built SPA, auth, service, tunnel) as the real work.

## 1. "Jangan ikut 100" = mirror the layout idiom, not the pixels

What the user actually wanted was the **arrangement**: hero band with live status chips at the top,
one URL/primary thing, a primary + one gold action button, a row-per-item control list, numbered
step cards for the physical/reboot steps, and a log pane at the bottom. Reuse the console's existing
classes (`hero-live`, `hl-kicker/hl-title/hl-sub/hl-chips`, `chip-live`, `panel/ph/pbody`,
`workbar`, `btn primary`, `btn gold`, `svc-row/svc-main/svc-act`, `steps/step`, `tag ok|bad`) —
inventing a theme for one tab is the tell that it was bolted on. Malay labels, no jargon, every tap
target big.

## 2. Register the service before writing any button

If the fronted thing is already supervised by runit, extend the **existing** allowlist first:

```python
SVC_ALLOW = {
    "hermes-dashboard":   ("Dashboard web 9119",  HOME/".hermes20/logs/hermes-dashboard.log"),
    "hermes-dash-tunnel": ("Tunnel Cloudflare",   HOME/".hermes20/logs/hermes-dash-tunnel.log"),
}
```

Now `/api/svc`, `/api/svc/{name}` and `/api/svc/{name}/log` drive HIDUP / MULA SEMULA / MATI / LOG
with no new code. Only then add the tab-specific read model:

```python
@app.get("/api/web")                      # one snapshot, no shelling out to sv
def api_web():                            # url file, port liveness, LAN IP, username,
    ...                                   # secret FILE PATH (never the value), service states

@app.post("/api/web/verify")              # shells the existing verify script
    subprocess.run([bash, str(DASH_VERIFY_SCRIPT)], capture_output=True, text=True, timeout=120)
    return {"ok": rc == 0 and "login POST : 200" in out, "exit": rc, "out": out[:4000]}
```

Helpers that avoid extra dependencies:

- **LAN IP without parsing `ifconfig`** — `s = socket.socket(AF_INET, SOCK_DGRAM); s.connect(("8.8.8.8", 80)); s.getsockname()[0]`.
- **Port liveness** — `socket.socket(AF_INET, SOCK_STREAM).connect_ex(("127.0.0.1", port)) == 0`.
  (No `ss`/`lsof` on this Android image: `ss` says *Cannot open netlink socket*. This also tells you
  the tab is showing the same process the supervisor thinks it is.)
- Remember `import socket` at module top; `NameError: socket` only surfaces when the tab is opened.

## 3. Verification for this shape of tab

- `GET /api/web` → url, `port_open: true`, both services `run`.
- `POST /api/web/verify` **without** `X-Console-Token` → `{"error":"token konsol tiada atau salah"}`
  (prove the guard still holds), then with the token from `/api/meta` → `{"ok":true,…}`.
- Served page must contain the nav button and the pane id (`curl / | grep -c 'data-tab="web"'`,
  `grep -o 'id="tab-web"'`); served JS must contain the loader (`curl /static/app.js | grep -c
  "async function loadWeb"`). A tab that exists in the file but not in the response is not shipped.
- `python -m py_compile app.py` and `node --check static/app.js` before restarting, and keep a
  `hermes-console/.bak-<feature>/` copy of the three touched files.
- Restart with `sv restart hermes-console`, then re-curl — `sv status` alone proves nothing.

## 4. Trap that cost a step here

An "idempotent" patch script that decides *already applied* with
`if new_text[:60] in file` silently skips edits whose first 60 characters are identical to the
original line (adding a dict entry, adding a sibling button). Assert on the **added marker**
(`'"hermes-dashboard": ('`, `'data-tab="web"'`) instead, then verify with a count grep.
