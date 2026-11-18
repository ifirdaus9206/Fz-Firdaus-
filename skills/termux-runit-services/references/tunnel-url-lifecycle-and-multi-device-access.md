# Tunnel URL lifecycle + "boleh buka dari PC juga?" (mobile-hosted app)

Worked session: user reported *"URL yang aku bagi dah tak boleh buka, cuma yang ni boleh —
kau jadi satu web sahaja ke atau ada masalah di app?"*. Answer was: one web app, old URL dead
because the quick tunnel restarted. This file is the fast diagnosis and the multi-device answer.

## 1. Diagnose "old URL dead" in four probes

```bash
ps aux | grep -i cloudflared | grep -v grep          # how many tunnels, to what port
curl -s -o /dev/null -w "old=%{http_code}\n" --max-time 12 https://old-name.trycloudflare.com/
curl -s -o /dev/null -w "new=%{http_code}\n" --max-time 12 https://new-name.trycloudflare.com/
curl -s -o /dev/null -w "local=%{http_code}\n" --max-time 8  http://127.0.0.1:9119/login
grep -c "Registered tunnel connection" ~/.hermesNN/logs/<tunnel>.log
```

Interpretation table:

| old | new | local | verdict |
|---|---|---|---|
| `000` | `302`/`200` | `200` | App healthy. Old hostname released — quick tunnel restarted. Nothing to fix in the app. |
| `000` | `000` | `200` | Tunnel process down → `sv status <tunnel svc>`, read log. |
| `000` | `000` | `000` | App down too → app problem, not tunnel. |

`000` = no HTTP response at all (DNS name gone / connection refused), which is what a released
`*.trycloudflare.com` hostname looks like. A `302 → /login` on a basic-auth dashboard is **healthy**,
not an error — say so explicitly, or the user reads the redirect as breakage.

Confirm which process owns the current URL: only one `cloudflared` should exist, and its target port
must match the app (`cloudflared tunnel --url http://127.0.0.1:9119`). Two cloudflareds on the same
port is the real "dua web" bug; one cloudflared means "satu web sahaja" and the user's question is
about a stale bookmark.

## 2. Why the old URL cannot be recovered

Quick tunnels (`cloudflared tunnel --url`, no account) mint a **new random hostname on every start**
and Cloudflare gives no uptime guarantee — its own startup banner says so. So:

- redirect/`sv restart` of the tunnel service = new URL;
- phone reboot / killer event / `sv up` after a crash = new URL;
- reconnects **inside one process** keep the same hostname (log can show 4×
  `Registered tunnel connection` with one URL) — so repeated re-registration is not URL churn;
- the old hostname is gone from Cloudflare's edge; no config on the phone can bring it back.

Announce it as a property of the tool, never as "app rosak". Fix for a stable URL = named tunnel
(Cloudflare account + domain), ngrok reserved domain, or Tailscale Funnel — not more restarts.

## 3. Log-truncation destroys the URL audit trail

The publisher pattern `: > "$LOG"` at service start (needed so `publish()` greps a clean file) also
erases every previous hostname. Symptom: after rotation, `grep old-name log` returns nothing and you
cannot tell when or how often the URL changed.

Keep a rotation history instead of only truncating:

```bash
[ -s "$LOG" ] && grep -o "https://[a-z0-9-]*\.trycloudflare\.com" "$LOG" | grep -v '^https://api' | tail -1 \
  >> "$HOME/.hermesNN/logs/dashboard_url_history.txt"
: > "$LOG"
```

Then "when did it change / how many times today" is a `cat` away, and a stale bookmark can be dated.

## 4. Multi-device access: one URL, many devices

A web app behind a tunnel is an ordinary HTTP server — phone and PC can use it **at the same time**,
with independent sessions and the same login. There is no "one device only" limit. Give the user the
three paths in this order:

1. **Same WiFi (fastest, no tunnel):** `http://<phone-LAN-IP>:<port>`. Requires the app to bind
   `0.0.0.0` (Hermes dashboard runs `--host 0.0.0.0 --port 9119`; verify with
   `curl 127.0.0.1:9119/login` → 200). Print the IP you actually read from the device, e.g.
   `http://192.168.0.41:9119`.
2. **Away from home / mobile data:** the current public tunnel URL, same login.
3. **Real remote *work* (files/terminal, not just viewing):** that needs SSH and Termux `sshd`
   listening on 8022 — a viewing dashboard does not grant it. Check
   `ss -ltn | grep 8022` / `pgrep -a sshd` before promising it, and offer to enable it as a separate step.

### Reading the device IP on Android Termux

`ip -4 addr` and `ss` output can be filtered/denied on a stock phone. Reliable:

```bash
ifconfig 2>/dev/null | grep "inet " | grep -v 127.0.0.1
python3 -c "import socket;s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.connect(('8.8.8.8',80));print(s.getsockname()[0])"
```

**Never hand out a `100.x.y.z` address.** On mobile data that is carrier-grade NAT — reachable from
nowhere, and the user will report "PC tak boleh buka" while blaming the app. Give the `192.168.*`
(LAN) address for same-WiFi and the tunnel URL otherwise.

## 5. Secrets

Dashboard credentials live in `config.yaml` as `dashboard.basic_auth.{username,password_hash}` —
there is no plaintext password to read or echo. Report only
`username = <SET len N>` / `password_hash = <SET len N>` (86 chars = a hash). Never print the value,
and never suggest "reset by reading the file".

## 6. Reply shape that worked

One-line verdict first ("app tidak rosak; URL lama mati sebab quick tunnel"), then a bullet list of
measured probes with codes (`old=000`, `new=302`, `local=200`), then the cause in one paragraph,
then numbered options (use current URL / named tunnel / cron URL announcer / LAN + SSH). The user
answers by number.
