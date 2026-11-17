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
