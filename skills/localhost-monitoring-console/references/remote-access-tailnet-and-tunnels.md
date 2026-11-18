# Remote access from outside the LAN — tunnels, tailnets, and delivering the link

Written after the 2026-11-18 incident: the user said *"tak boleh buka, aku guna data untuk buka
di luar rumah"* and pasted `https://montreal-continuity-walnut-cons.trycloudflare.com`. The tunnel
was healthy; the **hostname was dead**.

## 1) Triage a "link tidak boleh dibuka" report in one curl

```bash
curl -s -m 12 -o /dev/null -w 'http=%{http_code} dns=%{time_namelookup}s connect=%{time_connect}s total=%{time_total}s\n' "$URL/api/ping"
```

| Pattern | Meaning | Where to look |
|---|---|---|
| `http=000 dns=0.000000 connect=0.000000 total=0.009` | **DNS name does not exist** — stale tunnel hostname (or typo). Nothing to do with the user's mobile data | the URL file, not the network |
| `http=502/1033` | tunnel is up, origin is not | `curl 127.0.0.1:<port>`, `sv status <app>` |
| `http=302 → /login?next=/` | tunnel + origin fine, it is an **auth** question | `dashboard.basic_auth` in config |
| `http=401` | basic auth required (WWW-Authenticate absent on `/` when a login page redirect is used) | same |
| timeout / connect slow | genuinely network or the phone is asleep | `uptime`, `sv status <tunnel>` |

Never answer "your data is the problem" before the DNS/HTTP split above is measured.

## 2) Cloudflare quick tunnels rotate their hostname on every start

`cloudflared tunnel --url http://127.0.0.1:9119 --no-autoupdate` (no account, no token) prints a
random `https://<words>.trycloudflare.com`. Every **process start** — including a runit restart
after a crash or an Android kill — prints a *different* name. The old name stops resolving
immediately, so a link saved in chat, email, or a browser bookmark dies **silently**.

Implementation used here (`~/.hermes20/scripts/dash_tunnel.sh`, runit service
`hermes-dash-tunnel`):

- `: > "$LOG"` truncates, then the pipe tees every cloudflared line to the log;
- the first non-`api.` `https://*.trycloudflare.com` seen is written to
  `~/.hermes20/dashboard_url.txt`;
- a `trap publish EXIT` catches the URL on restart too.

So: **read `dashboard_url.txt`, never a URL from conversation history.** Confirm liveness with the
table in §1 before handing it to the user.

Log noise that is *not* a fault: `ERR failed to accept incoming stream ... timeout: no recent
network activity` every few minutes followed by `Registered tunnel connection` — the phone slept,
the tunnel re-registered. The hostname survives; only a process restart changes it.

## 3) Options for a link that does not rot (ordered by user cost)

| Option | Stable? | What the user must do |
|---|---|---|
| Named Cloudflare tunnel + own domain | yes, forever | Cloudflare account, domain, `cloudflared tunnel login/create/route dns` |
| ngrok free **static domain** (1 per account) | yes | sign up, put authtoken in the tunnel service |
| Tailscale (tailnet `100.x.y.z` or MagicDNS) | yes | install the app on the host phone **and** the viewing device, log into the same account |
| Quick tunnel + auto-push new URL | no, but self-healing | nothing, if the URL is pushed on change |
| Quick tunnel alone | no | user must re-ask every time it restarts |

If the user says "buat secara kekal", the quick tunnel is not an answer — say plainly that it
changes name, and offer the durable rows above.

## 4) Tailscale on an Android phone that hosts the service

**The Linux binary does not run in Termux.** `pkgs.tailscale.com/stable/tailscale_latest_arm64.tgz`
unpacks a static Go binary with `Type: EXEC` (non-PIE):

```
error: "/data/data/com.termux/files/home/tailscale/tailscaled" has unexpected e_type: 2
```

Android only executes PIE (`ET_DYN`). There is also **no `tailscale` package** in the Termux repos,
and `tailscaled` wants `/dev/net/tun` (root). Do not spend a second attempt on ELF patching.

Working design instead:

1. Install the **Tailscale Android app** on the phone running Termux; log in once.
2. Anything already bound to `0.0.0.0:<port>` (e.g. `hermes dashboard --host 0.0.0.0 --port 9119`)
   is then reachable at the device's stable tailnet address — `http://100.x.y.z:9119` or
   `http://<magicdns-name>:9119`.
3. The viewing device installs the same app, same account. No domain, no expiring link.
4. Termux **cannot see** the VPN interface (`ip`/`ifconfig` show nothing useful without root), so the
   `100.x.y.z` value has to be read from the app's main screen and sent back by the user.
5. Set the **Tailscale app's** battery mode to unrestricted too — otherwise the tunnel app is
   frozen exactly like Termux was, and the tailnet goes dark while the phone sleeps.

Checklist before declaring success: `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:<port>/`
is 200 locally, the service binds `0.0.0.0` (grep the runit `run` script), and auth is configured so
the open tailnet port is not anonymous.

## 5) Delivering the link by email (no mail client needed)

`~/.hermes20/.env` already carries `GMAIL_USER` + `GMAIL_APP_PASSWORD` (16 chars). Send with stdlib:

```python
with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context(), timeout=45) as s:
    s.login(user, pw)
    refused = s.send_message(msg)      # {} == all recipients accepted
```

Read the `.env` in-process, print **only** `GMAIL_USER` and `bool(app_password)` — never the value.
Put the URL, the username, the "this link is temporary" caveat and a "reply with what appears on
screen" line in the body; the user reads it on the phone and replies in chat.

## 6) Reporting shape that worked

Four short blocks: (1) evidence table with the curl numbers, (2) what it means in plain words,
(3) the new link + exact login, (4) numbered options. When the earlier diagnosis turns out wrong
("peranti reboot" → `uptime` says 4 days), say **"aku silap"** in the same message and correct the
artefact (`DEVICE.md`) — the user tolerates a wrong guess, not a hidden one.
