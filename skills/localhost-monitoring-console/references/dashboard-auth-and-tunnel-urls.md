# Dashboard password auth, quick-tunnel URLs, and stable remote access

Measured on Android/Termux (HyperOS, no root, no adb) with `hermes dashboard`
served under runit. Every command below was run; results are quoted.

## 1. Set / change the dashboard password

The dashboard reads `dashboard.basic_auth.{username,password_hash}` from
`config.yaml`. There is **no** `hermes dashboard auth` subcommand — generate the
hash yourself and write it back with `hermes config set` (never hand-edit
`config.yaml`; the write guard refuses it).

```python
# hash_password() from plugins/dashboard_auth/basic — same params, same format
import hashlib, secrets, base64
salt = secrets.token_bytes(16)
dk = hashlib.scrypt(pw.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32, maxmem=0)
f"scrypt$16384$8$1${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"
```

```bash
cp ~/.hermes20/config.yaml ~/.hermes20/config.yaml.bak-$(date +%F)
hermes config set dashboard.basic_auth.password_hash "$(cat hash.txt)"   # value contains $ and +/= → quote it
sv restart hermes-dashboard      # config is read at boot; no restart = old hash still active
```

Notes:
- Keep the plaintext out of the config (`plaintext password wujud: False` is the
  check). Store it for the user in `~/.hermes20/secrets/dashboard_login.txt`
  (0600) together with the current URL — that file is what the "URL berubah"
  cron mailer references.
- Passwords the user dictates may contain a space (`ketua Hermes20`). Enter it
  exactly as dictated, then state the exact string back including the space and
  offer a no-space variant — do not silently "tidy" it.

## 2. Verify — the login is a POST, not a Basic header

`curl -u user:pass /` returns **302 → /login even with the correct password**,
and `-u` on `/api/meta` returns 401. That looks exactly like a wrong password.
The provider interface calls it a password-login flow:

```bash
# correct: JSON body, provider required (missing provider → 422)
curl -s -X POST http://127.0.0.1:9119/auth/password-login \
  -H 'Content-Type: application/json' \
  -d '{"provider":"basic","username":"firdaus","password":"…"}' \
  -o body.txt -D hdr.txt -w 'http=%{http_code}\n'
# 200 + {"ok":true,"next":"/"} + Set-Cookie hermes_session_at / _rt / _provider
# wrong password → 401 {"detail":"Invalid credentials"}
```

Verification matrix worth reporting to the user: new password 200, **old
password 401** (proves the change took), and the same POST through the public
URL 200 (proves the tunnel path end to end).

## 3. Why a saved public link stops working

`cloudflared tunnel --url http://127.0.0.1:9119` is a **quick tunnel**: the
`*.trycloudflare.com` hostname is minted per process. Any restart (runit
respawn, reboot, network death) mints a new one and the old link is dead —
nothing rewrites the user's bookmark.

- Stale-link signature: DNS fails instantly — `time_namelookup 0.000`,
  `total 0.0098s`, `http_code 000`. A live-but-broken tunnel instead connects
  and returns 502. Use that difference before blaming the user's mobile data.
- Publish the URL from the tunnel log into a stable file (`dashboard_url.txt`)
  and let a cron job mail it on change; that is the only reason the user finds
  the current link at all.
- `ssh`d/served from the phone itself, `curl` of the public URL still traverses
  the Cloudflare edge, so a 302 from that URL is real end-to-end proof.

## 4. LAN is the "never expires" answer — but only on the same Wi-Fi

`host 0.0.0.0` in the runit `run` script is what makes this possible. Then:

```bash
ifconfig | grep -oE 'inet 192\.168\.[0-9]+\.[0-9]+'
curl -s -o /dev/null -w '%{http_code}\n' http://192.168.0.11:9119/       # 302 expected
curl -s -X POST http://192.168.0.11:9119/auth/password-login …          # 200 expected
```

Read the interface name before promising anything: `ccmni1` (100.95.x.x) means
**mobile data / carrier CGNAT** — no LAN, and unreachable from outside; `wlan0`
plus `192.168.x.x` means Wi-Fi. A phone on mobile data can never be reached by
`localhost` (that is per-device by definition), so "why not just localhost?"
needs this three-layer answer: loopback (this device only) → LAN (same Wi-Fi,
stable) → internet (tunnel / tailnet / domain).

LAN caveat to state: DHCP can renumber the address; only a router-side DHCP
reservation makes `192.168.x.y` permanent.

## 5. Stable alternatives (with what was actually tested)

- **Tailscale** — free, permanent `100.x.y.z` plus MagicDNS `<host>.<tailnet>.ts.net`.
  The official Linux binary **cannot run inside Termux**: it is `Type: EXEC`
  (non-PIE) and Android refuses it —
  `error: "…/tailscaled" has unexpected e_type: 2`. There is no `tailscale`
  package in the Termux repos either. Use the **Android app** instead: because
  the dashboard already binds `0.0.0.0`, incoming tailnet traffic reaches
  `http://100.x.y.z:9119` with no Termux-side change. The tailnet IP is not
  readable from Termux (no root), so ask the user to read it off the app.
  Remind them: HyperOS → App → Tailscale → Battery → **Unrestricted**, or the
  VPN process itself gets frozen.
- **ngrok static domain** — one free permanent `*.ngrok-free.app`; no app needed
  on the viewing device (needs an account token).
- **Own domain + named Cloudflare tunnel** — the only option that yields
  `dashboard.example.com` with no app anywhere; requires buying a domain.
- **Google does not give a free domain.** Google Domains closed (migrated to
  Squarespace), Google One / Pro has no domain, Google Cloud still requires a
  purchase. Google's free hostnames (`sites.google.com`, `*.web.app`,
  `blogspot.com`) cannot point at a Termux origin. Say this plainly instead of
  hunting for a workaround.

## 6. Handing the whole thing over

When the user says "tulis semua jawapan untuk aku simpan dalam nota telefon",
deliver **one plain `.txt`** (not markdown, not 12 chat bubbles): numbered
`BAHAGIAN` sections, exact copy-paste commands, the two error strings they are
likely to hit (`/hermes-console/...: No such file or directory` = missing `~/`;
`auto-mode:: command not found` = they pasted script *output* as a command),
the current URL + login, and a final 3-line summary. Send it with `MEDIA:` and
also copy it into the vault (`~/vault/operasi/`). Re-verify each live fact
(status, LAN code, published URL) immediately before sending so the note is
not stale on arrival.
