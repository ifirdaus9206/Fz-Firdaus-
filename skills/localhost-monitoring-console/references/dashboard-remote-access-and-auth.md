# Remote access to a Termux-hosted console / Hermes dashboard, and dashboard auth

Session: 2026-11-18. Host: Xiaomi HyperOS / Android 16, Termux (Google Play build), no root, adb unpaired.
Everything below was executed and verified on that device.

## 1. "The link you gave me doesn't open" — check the hostname first, not the network

Quick tunnels (`cloudflared tunnel --url http://127.0.0.1:<port>`) get a **new random
`*.trycloudflare.com` hostname every time the process starts**. A saved link silently rots. Users
read this as "my mobile data can't open it", so measure before theorising:

```bash
curl -s -m 12 -o /dev/null -w 'http=%{http_code} dns=%{time_namelookup}s connect=%{time_connect}s total=%{time_total}s\n' \
  https://<host-from-user>.trycloudflare.com/api/ping
```

- `dns=0.000000s … total=0.009804s` with `http=000` ⇒ **the name does not resolve**: the tunnel that
  owned it is gone. Nothing to do with the user's carrier data.
- `dns≈0.05s`, `http=302/401` ⇒ tunnel is alive; the remaining problem is auth (below).

Keep the live URL in one file written by the tunnel wrapper (`~/.hermes20/dashboard_url.txt`) and read
*that* file instead of remembering a link:

```bash
cat ~/.hermes20/dashboard_url.txt
tail -n 15 ~/.hermes20/logs/dashboard-tunnel.log   # "Registered tunnel connection … location=sin08"
```

Wrapper pattern that survives restarts (`~/.hermes20/scripts/dash_tunnel.sh`, started by a runit
service `hermes-dash-tunnel`): pipe cloudflared through a `while read` loop, grep
`https://[a-z0-9-]*\.trycloudflare\.com` (exclude `api.trycloudflare.com`), write it to the URL file,
and also `trap publish EXIT` so a dying tunnel still updates the file.

**Expect flapping transport, not failure.** The log shows, every ~2 min:
`ERR failed to accept incoming stream requests … timeout: no recent network activity` followed by
`INF Retrying connection in up to 1s` and `INF Registered tunnel connection`. That is Doze cutting
network; the process recovers itself. Do not "fix" it — fix the *URL churn* (file + notification)
or move to a stable address.

Stable-address options, cheapest first:
1. Cron job that mails/Telegrams the new URL when the file changes (what this device does).
2. A named Cloudflare tunnel — fixed hostname, needs a Cloudflare account **and** a domain.
3. Tailscale (`100.x.y.z` / MagicDNS) — fixed address, no domain (see §4 for the Termux constraint).

## 2. Hermes dashboard auth is a form POST, not HTTP Basic

A 401/302 on `/` with the correct password does **not** mean the password is wrong:

```bash
# WRONG — --user is ignored by the password provider; root always 302 -> /login
curl -s -o /dev/null -w '%{http_code}\n' --user "user:pass" http://127.0.0.1:9119/
# -> 302 (and /api/meta -> 401) even with the correct password
```

The real endpoint (verified: `200 {"ok":true,"next":"/"}` + `hermes_session_at` / `hermes_session_rt`
cookies; wrong password ⇒ `401 {"detail":"Invalid credentials"}`):

```bash
curl -s -X POST http://127.0.0.1:9119/auth/password-login \
  -H 'Content-Type: application/json' \
  -d '{"provider":"basic","username":"USER","password":"PASS"}' -w '%{http_code}\n'
```

- **`provider` is a required field.** Omitting it returns `422` with
  `{"type":"missing","loc":["body","provider"]}` — looks like a malformed request, not a bad password.
- The login page posts here from `/login?next=%2F`; provider list comes from `/api/meta` (also 401
  until a session exists). Only `provider: "basic"` exists when `dashboard.basic_auth` is configured.
- Do **not** write test bodies to `/tmp` on Termux (`curl -o /tmp/x` → `Permission denied`, then the
  verification "fails" for the wrong reason). Use `$HOME/lb.txt` and delete it.

## 3. Rotating the dashboard password without the UI

Provider: `plugins/dashboard_auth/basic/__init__.py` — stdlib scrypt, format
`scrypt$<n>$<r>$<p>$<salt_b64>$<dk_b64>` with `n=2**14, r=8, p=1, dklen=32, salt=16 bytes`.
Generate the hash yourself (same parameters ⇒ same verifier), then set it through the CLI — never
hand-edit `config.yaml`:

```bash
python3 - <<'EOF'
import hashlib, secrets, base64
salt = secrets.token_bytes(16)
dk = hashlib.scrypt(b"NEW PASSWORD", salt=salt, n=2**14, r=8, p=1, dklen=32, maxmem=0)
print("scrypt$16384$8$1$%s$%s" % (base64.b64encode(salt).decode(), base64.b64encode(dk).decode()))
EOF
# (write it to a file or capture in a var; don't paste the hash into chat)
hermes config set dashboard.basic_auth.password_hash "$h"
sv restart hermes-dashboard            # config is read at boot
```

Then prove it three ways and quote the codes: new password `200`, old password `401`, and the same
POST **through the public tunnel URL** `200` (that last one is what the user actually experiences).

Bookkeeping the user will look for later:
- `~/.hermes20/secrets/dashboard_login.txt` at `0600` — url / username / password / updated-at.
- `cp ~/.hermes20/config.yaml ~/.hermes20/config.yaml.bak-<date>` before any auth change.
- `dashboard.basic_auth` holds `username` + `password_hash` only; `password` (plaintext) must stay absent.

## 4. Tailscale inside Termux: the official binary cannot run

```bash
curl -sSL -o ts.tgz https://pkgs.tailscale.com/stable/tailscale_latest_arm64.tgz   # 37 MB
tar xzf ts.tgz -C ~/tailscale --strip-components=1
./tailscale/tailscaled --version
# error: ".../tailscaled" has unexpected e_type: 2
readelf -h tailscaled | grep Type      # Type: EXEC  (not ET_DYN)
```

Android only executes **PIE** binaries, and there is no `tailscale` package in the Termux repo
(`pkg search tailscale` → empty; root-repo builds need root). `tailscaled` also wants
`/dev/net/tun`, unusable without root — so do not burn time on userspace-networking workarounds.

What works instead: the console already binds `0.0.0.0` (`hermes dashboard --host 0.0.0.0 --port 9119`
in the runit `run` script), so the **Android Tailscale app on the same phone** is enough. From another
device on the same tailnet: `http://100.x.y.z:9119` (or `http://<magicdns-name>:9119`). The `100.x`
address never rotates. Tell the user to set **Tailscale → Battery → No restrictions** as well, or the
VPN service gets frozen by HyperOS exactly like Termux does.

## 5. Emailing the user a link/credential from Termux

`.env` already carries `GMAIL_USER` + `GMAIL_APP_PASSWORD` (16-char app password); Gmail SSL 465 via
stdlib is reliable and needs no extra package:

```python
import smtplib, ssl
from email.message import EmailMessage
msg = EmailMessage(); msg["From"] = msg["To"] = user
msg["Subject"] = "…"; msg.set_content(body)
with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context(), timeout=45) as s:
    s.login(user, app_password); refused = s.send_message(msg)
print("ditolak:", refused)      # {} == every recipient accepted
```

Always report `refused` (an empty dict is the proof of delivery acceptance) and never print the app
password. Spell out passwords with spaces character-by-character in the mail ("one space between
X and Y, capital H, digits 20") and offer the no-space variant — users mistype silent spaces.
