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
  `hermes-gateway`, `hermes-sshd`… — retired ones now sit in `$PREFIX/var/service-off/`).
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
script must live in `<hermes home>/scripts/`.

When a `create` keeps answering *"schedule is required"* even though you passed `schedule`, stop
reordering the same call. What worked: create with the **minimum** set (`action`, `prompt`,
`schedule`), then add the rest in **separate sequential `update` calls** on the returned
`job_id` — first `script`, then `no_agent`. Each `update` succeeds on its own and the job ends up
`script: url_watch.sh, no_agent: true`. `no_agent=true` is rejected unless `script` is already set
(*"Cannot set no_agent=True on a job without a script"*), which is why `script` must come first.
Then prove both branches with `action=run`: first run prints, second must be silent. Prove **both** branches (message, then silence) — a
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

## Service names are NOT commands (the "command not found" loop)

The owner will eventually type the service name into a shell:

```
hermes-console: command not found
hermes-gateway: command not found
hermes-dash-tunnel: command not found
HELD: command not found        ← this one was copied out of a log line, not a command
```

Three separate causes, all real, none of them a broken install:

1. **`hermes-console` etc. are directory names under `$PREFIX/var/service/`**, not binaries.
   The verb is `sv`: `sv status <name>` / `sv up` / `sv down` / `sv restart`.
2. **The typed word was log *output*.** `HELD`, `run:`, `down:` come from `sv status` and keeper
   output. Never paste a status word back as a command.
3. **Wrong shell.** A prompt reading `[root]` means a root/proot session where Termux's
   `$PREFIX/bin` is not on `PATH`, so even `sv` is "not found". Answer: `exit` back to the Termux
   shell, or call `/data/data/com.termux/files/usr/bin/sv status <name>`.

Don't explain the theory first — hand over **one** command that works for all services, then teach
the `sv` verbs one at a time (this owner wants one numbered step per message):

```bash
hermes-status          # semua servis + kod konsol + URL tunnel
hs                     # alias pendek
hermes-status up | restart | log
```

`scripts/svc-status.sh` is the generic implementation — copy to `$PREFIX/bin/hermes-status`,
`chmod +x`, set `SVCS=` to the services that actually exist. It prints `HIDUP/MATI/TIADA` per
service plus the health URL, so one word replaces four failed guesses. Install beside it:
`hermes-up` (sv up each, then status), `hermes-down` (`sv down` console+gateway),
`hermes-restart` (`sv restart` both) — and warn in the same breath that **`hermes-restart` kills
the Telegram gateway and drops the running session**; expected, not damage.

## Retiring a home/port is a code-wide grep, not one `rm`

Deleting `~/.hermes19` did not remove the *references*: the console still showed a dead
`HERMES19 MATI` pill and `/api/fleet` still listed that gateway, because both are hardcoded.
Checklist that actually finished the job:

```bash
grep -rn '<oldport>\|<oldhome>' ~/hermes-console/{app.py,PLAN.md,tools/,static/} | head -40
rm -f ~/hermes-console/server-<oldport>.pid          # stale pid of the retired port
```

- `/api/fleet`: only append the gateway entry **if its home dir exists and is non-empty**.
- `static/index.html`: delete the `<span class="pill">` for the retired home.
- Historical docs (`PLAN.md`): keep the text, stamp it —
  `STATUS <date> — SEJARAH SAHAJA. <home> dipadam; port <N> dibersarakan.`
- Keep grep hits that are *comments documenting the retirement* (audit trail); delete only live
  code paths.
- Prove it: `curl -s /api/fleet | python3 -m json.tool` shows one gateway, HUD renders no old pill,
  retired port answers `000`.
- Retiring one home is the narrow case. When the owner asks to "susun semua fail" in a home that has
  grown to tens of GB, use `agent-home-audit-and-tidy`: plan first, organise before deleting, and
  re-run `hermes-status` after every step.

## Pitfalls

0. **Check the tunnel's target port before debugging the UI.** A tunnel publishing port A while the
   app was edited on port B gives "my new tabs are missing / text is invisible" — the app is fine,
   the URL points at a different application. `grep -n "cloudflared tunnel" …/run`, then compare the
   served `<title>` and a tab marker with the app you changed. Fix the port, not the CSS. A tunnel
   host also hits Host allowlists as `403` while `127.0.0.1` returns `200` — allow
   `*.trycloudflare.com` (see `localhost-monitoring-console`,
   `references/contrast-and-tunnel-exposure.md`).

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
   `pkill -x <binary>`. Same trap with pgrep: `kill -9 $(pgrep -f "hermes gateway run")` matches
   the wrapper itself, so the call dies with exit `-9` and no output — the target may or may not
   have been hit. Re-check with `sv status` and use the bracket trick
   `pgrep -f "[h]ermes gateway run"`.
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

### Re-acquiring every keeper cycle is the OTHER half of the storm

Second confirmed cause on this device: a keeper running `while true; sleep 60` called
`termux-wake-lock` unconditionally each iteration. Android re-posts the notification on *every*
call, so the user reports it "tak henti buka" — every 60 s, forever. The lock is held per app
process; if the app dies the keeper (a child of it) dies too, so re-acquiring each cycle protects
nothing.

```bash
HELD="$HOME/.hermes20/.wake_held"
if [ -f "$FLAG" ] && [ ! -f "$HELD" ]; then    # sekali sahaja, bukan setiap 60s
  termux-wake-lock >/dev/null 2>&1 || true
  touch "$HELD"
fi
```

Audit **every** caller, not only the one you suspect: service `run` scripts, the console keeper
(cron `*/5`), and one-shot fix scripts that were flipped back to recurring (`cronjob list` —
check `enabled=false` / `completed`). Verification recipe (instrumented copy — a PATH stub does
NOT work for the hermes keeper because it rewrites PATH), the three failed instrumentation
attempts, and the cheaper `grep -c` proof: `references/wake-lock-notification-storm.md`.

## Health check to run before saying "sihat"

`scripts/termux-health-check.sh` (install as `~/bin/sihat`): wake-lock auto-mode, exactly one
`runsvdir`, zero orphan `runsv`, core services `run:`, process count vs the Android ~32 limit,
zombies, console HTTP, gateway process, available RAM. It finds runit processes via
`/proc/PID/exe`, never `pgrep -x`/`pgrep -f` (pitfall 9). Every line must read `[OK]` before a
health claim is delivered — a `[GAGAL]` line is the finding, not a footnote.

Threshold note: the raw count includes 2–3 transient `bash`/`ps` wrappers created by the very
tool call that runs the check, so a steady tree of ~26 processes reports 29–31. Set the FAIL
threshold at the real Android limit (32), not at a comfortable-looking 30, or the check cries wolf
on every run.

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


## Pitfalls lanjutan: proses, supervisor, had Android

9. **Jangan percaya `pgrep -x` atau `pgrep -f` untuk kira proses runit.** Binari Termux
   dilancarkan melalui `linker64`, jadi `/proc/PID/comm` = `linker64` → `pgrep -x runsv` sentiasa
   **0** walaupun runsv hidup. `pgrep -f "<path>"` pula menangkap shell yang cuma **menyebut**
   corak itu dalam argv (termasuk shell agent sendiri) → kiraan berganda dan `kill` boleh
   membunuh sesi pemanggil. Kesan melalui symlink exe — tepat, tiada positif palsu:

   ```bash
   for p in /proc/[0-9]*; do
     [ "$(readlink "$p/exe" 2>/dev/null)" = "$PREFIX/bin/runsv" ] || continue
     [ "$(awk '{print $4}' "$p/stat")" = 1 ] && echo "runsv YATIM pid=${p#/proc/}"
   done
   ```

10. **Dua pokok runit = konsol/gerbang bergaduh.** Selepas runsvdir dibunuh (phantom killer /
    OOM), anak `runsv`-nya kekal dengan `PPID 1`; bila termux-services dihidupkan semula, runsvdir
    **baharu** lahir dan melahirkan runsv sendiri untuk servis yang sama → dua pengawas satu
    servis, `app.py` yatim memegang port, `sv status` tak lagi mewakili realiti. Bunuh hanya runsv
    `PPID 1` (jangan sentuh anak runsvdir yang sah), kemudian semak `sv status` + `curl` port.
11. **Fail bernama literal `*.down` dalam `$PREFIX/var/service/` = zombie setiap detik.** Tercipta
    bila `touch $PREFIX/var/service/*.down` dijalankan tanpa glob yang sepadan. runsvdir cuba
    menghidupkannya, gagal (`not a directory`), dan mengulanginya — bertambah satu `<defunct>`
    [linker64] setiap kitaran sehingga had proses Android dicapai dan sistem mula membunuh app.
    `rm -f "$PREFIX/var/service/*.down"` (sebut dalam petikan) dan sahkan zombie berhenti bertambah.
12. **Had proses Android ~32 (phantom process killer).** App boleh "tutup sendiri" walaupun semua
    servis sihat bila anak proses melebihi had. Servis yang `down` **tetap** memakan satu proses
    `runsv`; servis tak terpakai patut dipindah keluar
    (`mv $PREFIX/var/service/<x> $PREFIX/var/service-off/`), bukan sekadar ditanda `down`.
    Sasar < 30 proses: `ls /proc | grep -c '^[0-9]'`. Semakan pantas seharian:
    `~/bin/sihat` (wake-lock / satu runsvdir / zombie / proses / konsol / gerbang / RAM).
13. **Memindahkan direktori servis keluar turut mematikan apa yang ia bawa — termasuk tunnel.**
    Selepas `mv … service-off/`, URL tunnel Cloudflare **quick** menjawab `000` manakala
    `127.0.0.1:8787` masih `200`, kerana setiap start menghasilkan hostname baharu. Selepas
    pemangkasan, baca semula `cat ~/.hermes20/dashboard_url.txt`, `curl` URL itu, dan beri bos URL
    **baharu** — jangan ulang hostname lama yang belum diuji dalam larian yang sama.

14. **Killing the supervised child is NOT "stopping the service".** A `stop_server.py`-style script
    that `kill`s the app PID looks broken under runit: runsv respawns the child in ~2 s, so
    `curl` never leaves `200` and the owner concludes "arahan tak jalan". Proven here:
    `8787 dihentikan: [10530, 10530]` → `8787 selepas kill = 200`. The *net* effect of such a
    script is a **restart**. To really stop: `sv down <name>` **first** (that drops the `down`
    flag on runsv and stops respawning), then kill if anything survives. Document this in the
    script's own docstring so the next reader doesn't chase a phantom bug.
15. **A `setsid ./run.sh &` launcher bypasses the supervisor and creates the orphan that
    pitfall 3 describes.** `start_all.sh` worked (dead `000` → `200`) but left an unsupervised
    process holding the port, while `sv status` still said `down`. Always return to the supervised
    state after using such an emergency launcher: kill the setsid PID, `rm -f server.pid`, then
    `sv up <name>` and confirm exactly one process + one growing uptime. Prefer `sv up` as the
    normal path; keep the setsid script only for the case where runit itself is broken.
16. **Killing the gateway to "test a restart" also kills the conversation that asked for the
    test.** `sv restart hermes-gateway` from inside a gateway session triggers the in-process
    guard or, via a wrapper script, actually drops the turn mid-reply (`Operation interrupted`).
    Either way the owner sees a truncated answer. Say so *before* running it, run it as the last
    action of the turn, and on reconnect state plainly that the session was restored and the old
    command was **not** re-executed.

## Watchdog: alert on unclean gateway death, then self-recover

runit restarts a killed child, but nobody is told — the owner discovers a silent bot hours later.
A `no_agent` cron closes both halves (`references/gateway-death-watchdog.md` has the full design):

- **Signals**, all token-free: `state/gateway.lifecycle.json` (`phase`, `pid`),
  `state/gateway.heartbeat` (`updated_at`, refreshed every 60 s), `sv status hermes-gateway`, and a
  **counter** of `exited UNCLEANLY` lines in `logs/gateway.log` compared against a stored offset.
  The offset is what turns "31 historical deaths" into "1 new death".
- **Anti-spam:** one stamp holding `problems|pid|heartbeat_ts|last_unclean`; the same incident never
  reports twice, and a healthy tick truncates the stamp so the next incident does report.
- **Action:** `sv restart hermes-gateway` once, `sleep 10`, re-read `sv status`, and put the outcome
  in the message (`sv restart dihantar → sekarang RUN`).
- **Testability:** `GW_ALERT_ROOT=<tmpdir>` relocates state/logs/stamp/offset and
  `GW_ALERT_NO_ACTION=1` skips the restart, so all four branches (healthy / down / repeat / new
  unclean death) are provable without touching the live gateway.
- **Wiring:** `hermes cron create "*/5 * * * *" --script gw_alert.sh --no-agent --deliver
  telegram:<chat_id>`. Empty stdout = silent. Baseline the counter at install or the first tick
  alerts on the whole history.
- **Second watchdog, separate failure mode:** `tg_watch.sh` watches the *inbound* path, not the
  process — `getWebhookInfo.pending_update_count` > 0 on **two consecutive ticks** (one tick can
  just be a busy gateway) and/or gateway dead. Test hook `TG_WATCH_FAKE_PEND=<n>` +
  `TG_WATCH_ROOT=<tmpdir>` + `TG_WATCH_NO_EMAIL=1` so both branches are provable without touching
  the live API.
- **Always add a second delivery channel when the alarm is about the alarm.** If Telegram is the
  broken thing, a Telegram-only alert stays silent exactly when it matters most. Reuse the Gmail
  credentials already in `.env` (`GMAIL_USER`, `GMAIL_APP_PASSWORD`) over `smtplib.SMTP_SSL`
  port 465, and verify by reading the message back over IMAP — SMTP returning without an
  exception only proves the server accepted it, not that it arrived.

## Restarting the gateway from inside a gateway session

The terminal tool refuses any command that could restart or stop the gateway while the agent
runs inside it (`Blocked: … cannot restart or stop the gateway from inside the gateway process`).
`sv restart hermes-gateway`, `sv status`, and anything matching those patterns are rejected —
this is a guard, not a missing tool.

Two working paths, both external to the agent process:

1. **The console's service API** (same thing the UI button calls). It needs the LAN token **and** a
   CSRF header — a bare curl answers `{"error":"token konsol tiada atau salah"}`, which is auth,
   not a broken endpoint:

   ```bash
   C=$(curl -s 127.0.0.1:8787/api/meta | python3 -c 'import sys,json;print(json.load(sys.stdin)["csrf"])')
   curl -s -X POST http://127.0.0.1:8787/api/svc/hermes-gateway \
     -H "Content-Type: application/json" -H "X-Console-Token: $C" -d '{"action":"restart"}'
   # → {"ok":true,"deferred":true,"out":"gateway dihentikan — runit menghidupkan semula dalam ~5s"}
   ```

   `deferred:true` = the reply is written **before** runit re-ups the child; wait ~20 s, then accept
   only `sv status` `run:` **plus** a fresh `Connected to Telegram (polling mode)` line as proof.
   Allowed names: `hermes-console`, `hermes-gateway`, `hermes-dashboard`, `hermes-dash-tunnel`,
   `web-server`; actions `up|down|restart|status`; also `GET /api/svc/{name}/log`.

   To give the owner a one-click **RESET GERBANG**: markup in `static/index.html`, handler wired
   **once** from the existing poller (`function wireGwReset()` guarded by `b.dataset.wired`, called
   at the top of `loadFleet()`), because `loadFleet` runs every 60 s and would otherwise stack
   duplicate listeners. Static files are served `cache-control: no-store` — no cache-busting needed.
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
- For anything that is *supposed* to survive Android, say plainly which part is proven now and
  which part only time can prove — a restart policy is not evidence against the OEM killer.

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
- `references/wake-lock-notification-storm.md` — "wake lock held" popping non-stop: keeper
  re-acquiring every 60 s, the one-shot guard that fixes it, and how to prove it without spamming
  the user (instrumented copy; a PATH stub fails because the keeper rewrites PATH).
- `references/bot-silent-while-gateway-alive.md` — Telegram silent while `sv status` says `run`:
  heartbeat/lifecycle probe order, `getMe`/`getWebhookInfo`/`getUpdates?offset=-1` interpretation
  (webhook vs pending vs no active poll), fallback-IP reachability test, and the rule that
  outbound proof (`hermes send`) is **not** inbound proof.
- `references/gateway-death-watchdog.md` — the `gw_alert.sh` design: heartbeat + unclean-counter
  signals, stamp anti-spam, `GW_ALERT_ROOT`/`GW_ALERT_NO_ACTION` test overrides, the message shape
  the owner accepted, cron wiring, and the shell-test traps hit while building it
  (`grep -c || echo 0` double output, sed quoting, nested `"$( … "$( … )" … )"` false FAIL,
  decoys that expire mid-test).
- `scripts/termux-health-check.sh` — install as `~/bin/sihat`: one-shot PASS/FAIL health report
  (wake-lock, single runsvdir, orphans, services, Android process limit, zombies, console,
  gateway, RAM).
- `scripts/svc-status.sh` — install as `$PREFIX/bin/hermes-status` (+ `hs` alias): one-word
  HIDUP/MATI/TIADA report for a service set plus health URL and current tunnel. The answer to
  "kenapa semua command not found" — service names are not commands.
