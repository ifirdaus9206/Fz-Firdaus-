# Hermes dashboard (9119): password auth and public links

Separate from the console this skill builds (8787). The dashboard is Hermes's own web UI:
`hermes dashboard --host 0.0.0.0 --port 9119 --no-open --skip-build`, usually under runit as
`hermes-dashboard`. Measured 2026-11-18/20 on Termux + HyperOS 3.

## Auth model

`~/.hermes20/config.yaml`:

```yaml
dashboard:
  basic_auth:
    username: firdaus
    password_hash: scrypt$16384$8$1$<salt_b64>$<dk_b64>
```

Hashing lives in `plugins/dashboard_auth/basic/__init__.py` (`hash_password`): `hashlib.scrypt`,
`n=2**14`, `r=8`, `p=1`, `dklen=32`, 16-byte random salt, base64 for salt and derived key. A plaintext
`password:` key is accepted as a fallback but `password_hash` is preferred — no plaintext at rest.

## Change the password (no CLI subcommand exists)

```bash
cp ~/.hermes20/config.yaml ~/.hermes20/config.yaml.bak-$(date +%F)
python3 - <<'EOF'
import hashlib, secrets, base64
pw = "NEW PASSWORD"                      # keep spaces only if the user typed them
salt = secrets.token_bytes(16)
dk = hashlib.scrypt(pw.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32, maxmem=0)
print("scrypt$16384$8$1$%s$%s" % (base64.b64encode(salt).decode(), base64.b64encode(dk).decode()))
EOF
hermes config set dashboard.basic_auth.password_hash "<hash from above>"
sv restart hermes-dashboard               # config is read at process start
```

`hermes dashboard` has no `auth`/`password` subcommand (only `register`) — do not invent one.
`hermes config set` handles the dotted key; writing `config.yaml` directly is blocked by the config
guard.

## Verify — the endpoint is NOT HTTP Basic

`curl --user user:pass http://127.0.0.1:9119/` returns **302** and `/api/meta` returns **401** for
*correct* credentials too: the dashboard authenticates through a JSON login, then a session cookie.

```bash
# correct password
curl -s -X POST http://127.0.0.1:9119/auth/password-login \
  -H 'Content-Type: application/json' \
  -d '{"provider":"basic","username":"firdaus","password":"NEW PASSWORD"}' \
  -o body.txt -D hdr.txt -w '%{http_code}\n'
# 200 + Set-Cookie: hermes_session_at=… ; hermes_session_rt=… ; hermes_session_provider=basic
# body: {"ok":true,"next":"/"}
# old/wrong password: 401 {"detail":"Invalid credentials"}
# missing "provider" field: 422 (field required) — the most common false alarm
```

Then repeat the same POST against the public URL to prove the tunnel and the auth both work.

## Public link rotation (Cloudflare quick tunnel)

- `~/.hermes20/scripts/dash_tunnel.sh` runs `cloudflared tunnel --url http://127.0.0.1:9119` and writes
  the first non-API `https://<random-words>.trycloudflare.com` it sees to
  `~/.hermes20/dashboard_url.txt`.
- **Every restart of cloudflared yields a new random hostname.** Old links die silently; the user
  keeps a link that no longer exists.
- Distinguish a stale link from a network problem with curl's timing:

```bash
curl -s -m 12 -o /dev/null \
  -w 'http=%{http_code} dns=%{time_namelookup}s connect=%{time_connect}s total=%{time_total}s\n' \
  "https://<link>/api/ping"
# stale hostname: dns=0.000s total≈0.01s http=000   (name does not exist)
# healthy tunnel: http=302/401, dns≈0.05s, total≈0.9s
```

- Notify on change: `dash_url_notify.sh` compares the current file against `~/.hermes20/.dash_url_last`
  and stays silent unless it differs; the cron job that runs it must have `deliver: telegram` (or
  `origin`) — a job with `deliver: local` updates the file and tells nobody.

## Stable access options, ranked by effort

| Option | Address | Limits |
|---|---|---|
| LAN | `http://192.168.0.11:9119` | same Wi-Fi only; DHCP may change the IP (reserve it in the router) |
| Tailscale | `http://100.x.y.z:9119` | needs the Android app on both devices; Termux cannot run the binary — the official linux-arm64 build is `Type: EXEC` and Android refuses it with `error: … unexpected e_type: 2` |
| Cloudflare named tunnel | `https://dashboard.<domain>` | needs a domain on Cloudflare; stable forever, no app |
| ngrok free static domain | `https://<name>.ngrok-free.app` | free tier limits, one static domain |

Dashboard already binds `0.0.0.0`, so LAN/Tailscale work without config changes:
`grep -o 'host [0-9.]*' $PREFIX/var/service/hermes-dashboard/run`.

## Pitfalls

- **Google does not give free domains.** Google Domains was discontinued (migrated to Squarespace),
  Google One/Pro includes no domain, and Google Cloud requires buying one. Do not send the user
  hunting for a "free Google domain".
- **`/api/ping` stays public** while `/` redirects to `/login` — a 200 on ping proves the process is
  alive, not that the link is usable end-to-end.
- **Test the login from the public URL, not just localhost.** Tunnel up + origin down looks identical
  to a bad password from the user's side.
- **Never print the password into a report or a git-tracked file.** Keep it in
  `~/.hermes20/secrets/dashboard_login.txt` (0600) and say only where it lives.
