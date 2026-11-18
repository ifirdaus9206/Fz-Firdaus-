---
name: termux-runit-services
description: Supervise Termux daemons with runit (sv), logs, boot.
category: devops
---

# Termux runit services (runsvdir / termux-services)

Long-running servers in Termux (web consoles, gateways, tunnels, dashboards) must live under
runsvdir, not inside an agent shell session. An agent-started background process dies with the
session; a runit service restarts itself and comes back after reboot.

## When to use
- A server/tunnel must keep running after the chat turn, after a crash, and after reboot.
- You need to replace an ad-hoc `setsid … &` / `nohup` launch with a supervised service.
- Existing services live at `$PREFIX/var/service/<name>/` (on this device: `hermes-console`,
  `hermes-gateway`, `jobboard-*`, `code-server`, `httpd`).
- You need a stable, always-publishable URL/endpoint file that other tools can read.

## Anatomy of a service

```
$PREFIX/var/service/<name>/run        # executable (755) — must `exec` the long-running process
$PREFIX/var/service/<name>/log/run    # optional svlogd logger
```

Minimal `run`:

```sh
#!/bin/sh
export HOME=/data/data/com.termux/files/home
export PATH=/data/data/com.termux/files/usr/bin:$HOME/.local/bin:$PATH
export <APP>_HOME=...            # if the app needs its own home
cd "$HOME" || exit 1
exec <binary> <args>             # exec, never fork-and-background
```

## Steps

1. **Probe first.** `ls $PREFIX/var/service`, `sv status <svc>`,
   `ps -eo pid,etime,args | grep <name>`, `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:<port>/`.
2. **Write `run`** with absolute paths; `chmod 755`.
3. **Pick a logging mode** (see pitfall 1): prefer a plain redirect for NEW services —
   `exec >> $HOME/<home>/logs/<name>.log 2>&1` immediately before the final `exec`.
4. **Bring it up:** `sv up <name>`; verify `sv status <name>` shows `run:` with a single PID and
   the port answers.
5. **Boot enable:** `sv-enable <name>` so termux-services starts it at boot. Also add an explicit
   `sv up "$PREFIX/var/service/<name>"` line to every `~/.termux/boot/*.sh` that already exists —
   Termux:Boot runs those scripts, and one of them is usually the only reason services come back.
6. **Verify again 20–30 s later and after a restart** — a crash-loop still looks "up" in a single
   status read.

## Verification (never report "running" without this)

```bash
sv status <name>                                        # run: <name>: (pid N) <uptime>
ps -eo pid,etime,args | grep "<name>" | grep -v grep     # exactly ONE process
curl -s -m 6 -o /dev/null -w "%{http_code}\n" http://127.0.0.1:<port>/
tail -5 $HOME/<home>/logs/<name>.log
```

If uptime keeps resetting to `0s`/`1s`, the service is crash-looping — read the log, do not
declare success.

## Publishing an endpoint that changes (quick tunnels, ephemeral ports)

Cloudflare quick tunnels mint a **new hostname on every start**, so "the URL" is not a constant and
the user cannot bookmark it. Two halves, both proven on this device:

1. **The service owns the file.** The tunnel's `run` script greps its own output and writes the
   current URL to one file (`~/.hermes20/dashboard_url.txt`) on every start — no second writer
   (pitfall 6).
2. **A `no_agent` cron announces changes** (`templates/url_change_notify.sh`): compare the file with
   a stamp (`~/.hermes20/.dash_url_last`), and only when it differs, curl `GET <url>/login`
   **first**, then print either the new URL (HTTP 200) or an explicit
   `AMARAN: URL bertukar tetapi belum hidup (HTTP nnn)`. Unchanged → empty stdout → silent
   delivery, which is the whole point of no-agent mode.

```bash
hermes cron create "*/15 * * * *" --name "URL dashboard berubah" \
  --script url_change_notify.sh --no-agent --deliver telegram
hermes cron run <job-id>      # run twice: first prints, second MUST be silent
```

Create the job through the CLI when the `cronjob` tool call is rejected for a missing field; the
script must live in `<hermes home>/scripts/`. Prove **both** branches (message, then silence) — a
watcher seen only in its silent state is unverified — and never announce a URL you have not curled
in the same run.

### "URL lama dah tak boleh buka" — diagnose before touching the app

A released quick-tunnel hostname answers **`000`** (no response at all), while the app still answers
`200` on `127.0.0.1:<port>` and the new URL answers `302 → /login`. That combination means **the app
is healthy and only the bookmark is stale** — lead with that, because a `302` reads as breakage to
the user. Probe order: `ps | grep cloudflared` (how many tunnels, to which port) → `curl` old URL →
`curl` new URL → `curl` local port → `grep -c "Registered tunnel connection"` in the tunnel log.
One `cloudflared` = one web app; two on the same port is the real "dua web" bug.

Two durable traps: (a) `: > "$LOG"` in the publisher erases every previous hostname, so append the
outgoing URL to a `*_url_history.txt` before truncating or a stale bookmark can never be dated;
(b) reconnects *inside* one process keep the same hostname, so repeated `Registered tunnel
connection` lines are not URL churn.

**Multi-device is not a second deployment.** Phone and PC can open the same URL at the same time with
the same login. Offer, in order: LAN `http://<192.168.x.x>:<port>` (needs the app bound `0.0.0.0`),
the public tunnel URL when away, and SSH on 8022 only if the user wants to *work* (files/terminal)
rather than view. Never hand out a `100.x.y.z` address — carrier-grade NAT, reachable from nowhere.
Full probe table, Android IP-reading commands and reply shape:
`references/tunnel-url-lifecycle-and-multi-device-access.md`.

## SSH on 8022: "PC nak kerja fail/terminal pada telefon"

SSH is a runit service like any other, and on Termux it ships **disabled**: the package drops a
`down` file into `$PREFIX/var/service/sshd/`, so `sv status sshd` reads `down:` and nothing listens.

```bash
rm -f "$PREFIX/var/service/sshd/down"; sv up sshd; sv status sshd
sv up "$PREFIX/var/service/sshd" 2>/dev/null || true   # add to ~/.termux/boot/*.sh too
```

Then verify the port **without** `ss`/`netstat` (they print nothing useful here): a Python
`socket.connect(("127.0.0.1",8022))` plus the daemon log line
`Server listening on 0.0.0.0 port 8022.` Port 22 is closed — Termux's compiled default is 8022, bound
to all interfaces, so the same WiFi can reach it directly (`ssh -p 8022 <user>@192.168.x.x`).

One command also tells you whether credentials are the blocker:

```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -p 8022 "$(whoami)"@127.0.0.1 true
# "Permission denied (publickey,password,keyboard-interactive)" = daemon fine, no credential yet
```

Prefer **key auth** — ask only for the PC's *public* key and append it to `~/.ssh/authorized_keys`.
Password auth is on by default but the Termux account starts with **no password** (`/etc/shadow`
entry absent), and `passwd` has no non-interactive mode: it must be driven over a **pty**
(`terminal(pty=true, background=true)` → `process(action="submit")`), with the generated password
written straight into a `chmod 600` secrets file, never into the chat. Send the user to the file or
the mail channel for the value. Full recipe, security posture and IP-reading commands:
`references/termux-sshd-8022-provisioning.md`.

## Pitfalls

1. **svlogd refuses to start for newly created services** on this device: `sv status` prints
   `warning: <name>/log: unable to open supervise/ok: file does not exist` and no `svlogd` process
   appears, while pre-existing services still log fine. Creating `log/supervise`, `chmod 755`,
   `sv down`/`sv up` and `sv up <name>/log` all failed to fix it; running `sh log/run` by hand works,
   so the logger itself is healthy — runsv simply never spawned it. Do not burn time: drop `log/`,
   redirect inside `run` instead. (Existing services with a working `log/` are worth copying the
   whole directory from, perms included, if rotation really matters.)
2. **`pkill -f "<pattern>"` kills the agent's own shell.** Each terminal call runs inside a
   `bash -c` wrapper whose command line contains your pattern, so `pkill -f "hermes dashboard"`
   terminates the calling session (exit `-15`) mid-command. Kill by PID (`kill <pid>`) or
   `pkill -x <binary>`.
3. **Orphan holds the port → supervised copy crash-loops.** A manually started process keeps the
   port; runit's instance dies on bind and restarts every second, so `sv status` shows a fresh pid
   while `curl` still answers from the orphan. Find the oldest PID via
   `ps -eo pid,etime,args`, kill it, then confirm exactly one process remains.
4. **`/tmp` is not writable on Android Termux.** `curl -o /tmp/x` fails with
   `curl: (23) client returned ERROR on write`. Write probe output to `$HOME/tmp_probe/` or
   `mktemp` — affects every script assuming POSIX `/tmp`.
5. **Editing `run` then `sv restart` may not reload.** Use
   `sv down <name>; sleep 2; sv up <name>` after changing the script.
6. **One writer per endpoint file.** If a service rewrites an endpoint file (URL, port), have it
   write on start and log it, so consumers never read a stale value after a restart.
7. **`ss -ltn` / `netstat -ltn` are not evidence on Termux.** They can print nothing at all while
   the daemon is healthy, which reads as "port closed". Confirm with a real TCP connect
   (`python3` socket to `127.0.0.1:<port>`) plus the auth-method refusal from
   `ssh -o BatchMode=yes … true`, or the daemon's own `Server listening on … port N` log line.
8. **Interactive `passwd` mid-turn will eat the turn.** A `passwd` prompt blocks, and the login
   banner (\`Created By HTR-TECH … Welcome\`) is printed **before** `New password:`, so a blind
   two-submit sequence races it. Start it as a background pty, `process(action="poll")` until the
   real prompt appears, submit, poll again — and finish that flow before starting any other work,
   otherwise the deliverable ends half-done with a live process still waiting for input.

## Wake lock: runit keeps the service alive, only the wake lock keeps the *phone* awake

runit restarts a killed daemon, but it cannot stop Android from killing the whole Termux
process. Symptom in the log: `Previous gateway life (pid=…) exited UNCLEANLY (no exit path ran —
SIGKILL / OOM / VM death)` repeating roughly daily, clustered around screen-off hours. Each
unclean death costs a restart, and Hermes-side "auto-resume restart-interrupted sessions" then
replays the interrupted turn — the user sees an unprompted new message mid-conversation.

**The trap is a well-meaning health-keeper.** A keeper script (cron `*/5`, "acquire the lock
only when something is broken, release it when everything is healthy") releases the lock on the
first healthy tick, so the lock is held for ~5 minutes out of every day. Check the *held* state,
not the intent flag:

```bash
grep -q . ~/.hermes20/wake_lock.enabled && echo "auto-mode ON"
[ -f ~/.hermes20/.wake_held ] && echo HELD || echo RELEASED     # this is the one that matters
bash ~/hermes-console/tools/wake_ctl.sh status
```

Rule: **two states, one owner.** If `wake_lock.enabled` exists, the keeper may *re-acquire* a
missing lock but must never release it; release only when the owner explicitly turns auto-mode
off (`wake_ctl.sh off`). Patch the release branch to be conditional:

```bash
[ "$ACTIVE" -eq 0 ] && [ -f "$WL_STATE" ] && [ ! -f "$WL_FLAG" ] && release
[ "$ACTIVE" -eq 0 ] && [ -f "$WL_FLAG" ] && [ ! -f "$WL_STATE" ] && reacquire
```

Then prove it: run the keeper by hand while everything is healthy and re-read the status — it
must still print `HELD`. Also keep `wake_ctl.sh auto` in `~/.termux/boot/*.sh` so a reboot
restores the lock.

### Never call `wake_ctl.sh` from a service `run` script (notification storm)

Symptom the user reports: Termux notification **`3 sessions (wake lock held)` keeps popping up
non-stop**. Android re-posts that notification on *every* `termux-wake-lock` invocation, so the
question is always "who calls it repeatedly?", not "why is the lock held".

Found on this device: `$PREFIX/var/service/hermes-gateway/run` had
`wake_ctl.sh auto` **before** `exec hermes gateway run`. Because an orphan gateway still held
`gateway.lock`, runsv's child exited in ~1 s (`✗ Another gateway instance is already running
(PID N)`), so runsv re-ran the script every ~2 s → one `termux-wake-lock` per attempt → the
notification re-appeared every couple of seconds. Diagnostic order:

```bash
sv status hermes-gateway          # pid uptime resetting to 0–3s = crash loop
pgrep -af "hermes gateway run"    # >1 process, oldest is the orphan holding the lock
hermes gateway run 2>&1 | tail -3 # run by hand: "Another gateway instance is already running"
cat "$PREFIX/var/service/hermes-gateway/run"   # the wake_ctl line lives here
```

Two rules that fix it for good:

1. **Wake lock is acquired once, at boot/keeper level — never inside `run`.** A supervised
   service restarts by design; anything in `run` runs again on every restart.
2. **A `run` script must never exit instantly when a peer already holds the lock.** Make it wait,
   otherwise runsv turns one conflict into a hot loop:

```sh
i=0
while pgrep -f "hermes gateway run" >/dev/null 2>&1 && [ "$i" -lt 360 ]; do
  sleep 5; i=$((i + 1))
done
exec hermes gateway run
```

Verify with the same pid across ~60 s (`sv status` elapsed keeps growing) and
`pgrep -af termux-wake-lock` empty. The notification that remains is a single *persistent* one —
that is correct and required while the lock is held; only the repeated popping is the bug. The
"N sessions" count is the number of open Termux terminal sessions, not a leak.


## Restarting the gateway from inside a gateway session

The terminal tool refuses any command that could restart or stop the gateway while the agent
runs inside it (`Blocked: … cannot restart or stop the gateway from inside the gateway process`).
`sv restart hermes-gateway`, `sv status`, and anything matching those patterns are rejected —
this is a guard, not a missing tool.

Two working paths, both external to the agent process:

1. **The console's service API** (same thing the UI button calls):
   `curl -s -X POST http://127.0.0.1:8787/api/svc/hermes-gateway -H 'Content-Type: application/json' -d '{"action":"restart"}'`
   Allowed names: `hermes-console`, `hermes-gateway`, `hermes-dashboard`, `hermes-dash-tunnel`,
   `web-server`; actions `up|down|restart|status`.
2. **A one-shot `no_agent` cron** that curls that API a few minutes out — the right pattern when
   a code patch must be loaded but the current turn still has to deliver its answer. Empty stdout
   keeps it silent; log the API response to a file for evidence:

```bash
OUT=$(curl -s -m 20 -X POST http://127.0.0.1:8787/api/svc/hermes-gateway \
      -H 'Content-Type: application/json' -d '{"action":"restart"}' 2>&1)
echo "$(date '+%F %T') restart-diminta: $(printf '%s' "$OUT" | head -c 300)" >> "$HOME/.hermes20/logs/gw_restart_once.log"
```

Never call that API mid-turn: the gateway dies before the reply is delivered and the user sees
nothing. Tell the user when it will happen and confirm the new PID/uptime afterwards.

## Deliverables that make a service auditable

- `docs/<NAME>.md`: URL(s), where the login secret lives, service names, exact `sv` commands,
  an evidence block (status codes, PIDs, log tail).
- A re-runnable verify script in `~/.hermes20/scripts/` printing PASS/FAIL lines.
- Secrets in a `chmod 600` file; the doc names the path, never the value.

## References / templates
- `references/hermes-dashboard-cloudflare-tunnel.md` — worked example: Hermes web dashboard on
  9119 + Cloudflare quick tunnel + `dashboard.basic_auth`, including the bind/Host-header rule.
- `templates/tunnel_url_publish.sh` — copy-adapt pattern that starts a tunnel and publishes its
  current public URL into one file.
- `templates/url_change_notify.sh` — `no_agent` cron reporter for a URL that changes: probes
  `/login` before announcing, silent when unchanged, explicit warning when the new URL is dead.
- `references/tunnel-url-lifecycle-and-multi-device-access.md` — "URL lama dah tak boleh buka":
  `000` vs `302` probe table, why a quick-tunnel hostname cannot be recovered, the log-truncation
  audit-trail trap, and the one-URL-many-devices answer (LAN IP, CGNAT `100.x` warning, SSH 8022).
- `references/termux-sshd-8022-provisioning.md` — enabling the `down`-flagged `sshd` service,
  verifying 8022 without `ss`/`netstat`, key auth vs. pty-driven `passwd`, LAN-IP reading, and the
  "anyone on the WiFi can try to log in" warning to state plainly.
