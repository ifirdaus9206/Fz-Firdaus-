# Worked example — Hermes web dashboard on Termux + Cloudflare quick tunnel

Session: 2026-11-17, Hermes 0.20.0, `HERMES_HOME=~/.hermes20`, Android 16 / Termux, no root.
Goal: run the same dashboard UI the user runs on their PC, but on the phone, reachable by URL.

## 0. Identify what the URL actually is

A `*.trycloudflare.com/chat?pro` link that shows `<title>Sign in — Hermes Agent</title>`,
Nous brand fonts (`@nous-research/ui`) and a `Public bind · Auth required` footer is **a Hermes
dashboard**, not a third-party app. Do not warn "this is someone else's machine" before asking —
in this session it was the user's own PC instance. Probe first:

```bash
curl -sSL -m 30 "<url>" -o ~/tmp_probe/page.html -w "HTTP:%{http_code}\n"   # NOT /tmp
grep -o -i "<title>[^<]*</title>" ~/tmp_probe/page.html
```

## 1. Build the SPA (web_dist is often absent from a source install)

`hermes dashboard` serves `hermes_cli/web_dist/`. When missing, `--skip-build` serves nothing.

```bash
cd ~/.hermes20/tools/hermes-source/hermes-agent/web
npm install --no-audit --no-fund --loglevel=error     # ~408 packages, ~1 min
npm run build                                          # tsc -b && vite build → ../hermes_cli/web_dist
```

`vite.config.ts` has `outDir: "../hermes_cli/web_dist"`. Build takes ~2 s once deps exist.

## 2. Bind rule — the part that decides the architecture

`hermes_cli/web_server.py`:

- `should_require_auth(host)` → auth gate ON for any **non-loopback** bind; loopback = trusted.
- `host_header_middleware` rejects a Host header that doesn't match the bind: loopback bind
  accepts only loopback names → a tunnel's `Host: xxx.trycloudflare.com` gets
  `400 {"detail":"Invalid Host header..."}`.
- Non-loopback bind with **no** auth provider refuses to start (fail-closed, June 2026 hardening).
- `--insecure` is a no-op for auth now.

Consequence: **tunnel ⇒ bind `0.0.0.0` ⇒ auth provider is mandatory.** Binding loopback and
rewriting the Host header with `--http-host-header` would leave a public *unauthenticated*
dashboard — never do that.

## 3. Password auth provider

Config keys (write with `hermes config set`, never by editing config.yaml):

```
dashboard.basic_auth.username
dashboard.basic_auth.password_hash     # scrypt$N$r$p$salt$dk
```

Hash with the bundled plugin (needs the source tree on PYTHONPATH or `hermes_cli` is not found):

```bash
cd ~/.hermes20/tools/hermes-source/hermes-agent && PYTHONPATH=$PWD python mk_hash.py
# inside: importlib-load plugins/dashboard_auth/basic/__init__.py → m.hash_password(pw)
```

Then `hermes plugins enable basic` (bundled; shows "not enabled" until credentials exist).

Generate the password inside the script, write it to `~/.hermes20/secrets/dashboard_login.txt`
(chmod 600), print only the hash — never echo the password into chat or logs.

## 4. Services

| Service | `run` |
|---|---|
| `hermes-dashboard` | `exec hermes dashboard --host 0.0.0.0 --port 9119 --no-open --skip-build` |
| `hermes-dash-tunnel` | `exec bash ~/.hermes20/scripts/dash_tunnel.sh` (cloudflared quick tunnel) |

`HERMES_HOME` must be exported in `run`. `sv-enable` both so they start at boot. The tunnel script
republishes the URL to `~/.hermes20/dashboard_url.txt` on every start (quick-tunnel hostnames
change each restart) — see `templates/tunnel_url_publish.sh`.

## 5. Evidence block (repeat verbatim in the report)

```
GET /       : 302 -> /login?next=%2F
login page  : 200   (Sign in — Hermes Agent)
login POST  : 200   {"ok":true,"next":"/"}
dashboard   : 200   (Hermes Agent - Dashboard)   # with session cookie
api/status  : 200   version 0.20.0, gateway_running true
```

Verify script kept at `~/.hermes20/scripts/dash_verify.sh`; run it after any restart.
It reads the password from the secret file into a shell variable — never prints it.

## 6. Operational caveats worth telling the user

- Quick tunnels have no uptime guarantee and a new hostname per start → named tunnel + domain for
  a stable URL.
- Phone must stay awake/online; Android battery optimisation kills Termux → whitelist it.
- LAN alternative (same Wi-Fi): `http://<phone-lan-ip>:9119/`, same password.
- Never post the public URL together with the password.
