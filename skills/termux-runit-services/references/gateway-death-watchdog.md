# Watchdog for gateway death: alert on Telegram + self-recover (worked design)

Complaint this answers: *"tambah amaran Telegram automatik bila gateway mati tidak bersih"* — runit
restarts the killed child, but nobody is told, and the owner discovers it hours later by finding a
silent bot.

## Signals (all read-only, no bot token needed)

| File / command | What it proves |
|---|---|
| `state/gateway.lifecycle.json` → `phase`, `pid` | `running` vs `stopped`; the pid the ledger thinks owns the gateway |
| `state/gateway.heartbeat` → `updated_at`, `mem` | refreshed every ~60 s by housekeeping; age > 300 s = frozen |
| `sv status hermes-gateway` | `run: … (pid N) Ns` vs `down:`/`fail:` |
| `grep -c "exited UNCLEANLY" logs/gateway.log` | cumulative count; compare against a stored offset for *new* deaths |
| `ps`/`/proc/PID/exe` | the process is really there (a pid in a JSON file proves nothing) |

`exited UNCLEANLY (no exit path ran — SIGKILL / OOM / VM death)` in `gateway.log` is the unclean
death marker; the *next* startup writes it, so a death is only visible after the process came back.

## Shape of the script (`~/.hermes20/scripts/gw_alert.sh`)

1. Read lifecycle + heartbeat with `python3 -c` (print `phase pid age timestamp` on one line and
   `read` them into bash) — avoids `jq` dependency and handles the ISO-8601 `updated_at`.
2. Resolve aliveness by **pid**, then fall back to scanning `/proc/*/exe` for `$PREFIX/bin/hermes`
   whose cmdline contains `gateway run` (never `pgrep -x`, see pitfall 9 in SKILL.md).
3. Compute `UNCLEAN_NEW = total - offset`; an offset file is what turns the 31 historical deaths on
   this device into "1 new death".
4. Build a `PROB` string (`lifecycle=stopped;proses-tiada;sv=down;nadi-beku=900s`). Empty `PROB`
   **and** `UNCLEAN_NEW=0` → `exit 0` with no stdout = silent delivery.
5. Anti-spam stamp: `SIG="$PROB|$PID|$HBTS|$UNCLEAN_LAST"`. Same `SIG` as last time → silent. A
   healthy tick truncates the stamp so the next incident reports again.
6. Action: `sv restart hermes-gateway`, `sleep 10`, re-read `sv status`, and put the outcome in the
   message (`sv restart dihantar → sekarang RUN` / `→ MASIH TIDAK RUN: …`).
7. Print the message; cron delivers stdout verbatim.

Message content that proved useful to the owner (plain Malay, evidence-first):

```
AMARAN GERBANG TELEGRAM · 24/11 01:12
Masalah: lifecycle=stopped;nadi-beku=900s
Kematian tidak bersih baharu: 1 (terakhir 2026-11-24 00:36:01)
Status sv: run: hermes-gateway: (pid 26013) 1116s
nadi: 900s lalu · pid: 26013
Tindakan: sv restart dihantar → sekarang RUN
Semak: http://127.0.0.1:8787/?tab=pusat (butang RESET GERBANG)
```

## Make every branch testable without touching the live service

```bash
GW_ALERT_ROOT=<tmpdir> GW_ALERT_NO_ACTION=1 bash gw_alert.sh
```

`GW_ALERT_ROOT` relocates `state/`, `logs/gateway.log`, the stamp and the offset into a temp tree;
`GW_ALERT_NO_ACTION=1` skips the restart. Four scenarios to prove, each with a temp root:

1. `phase=running` + fresh heartbeat + empty log → **0 bytes stdout**.
2. `phase=stopped` + heartbeat 900 s old → message contains `lifecycle=stopped`, `nadi-beku`, and
   the console hint; no `arithmetic`/`integer expected` on stderr.
3. same scenario twice → second run silent (stamp works).
4. one `exited UNCLEANLY` line + offset 0 → exactly one message saying `baharu: 1`, second run silent.

## Cron wiring

```bash
hermes cron create "*/5 * * * *" --name "Amaran gerbang Telegram mati" \
  --script gw_alert.sh --no-agent --deliver telegram:<chat_id>
hermes cron run <job-id>          # must print nothing while healthy
```

Silent-when-healthy means `hermes cron run` on a healthy box is *not* evidence the delivery path
works — prove delivery separately with `hermes send -t telegram "…"` → `Sent to telegram home
channel`.

Baseline the counter at install (`echo "$(grep -c 'exited UNCLEANLY' ~/.hermes20/logs/gateway.log)"
> ~/.hermes20/.gw_alert_unclean_off`) or the first tick alerts on the whole history.

## Ad-hoc test-harness traps hit while building this (all cost a cycle)

- **`grep -c … || echo 0` yields "0\n0".** `grep -c` prints `0` *and* exits 1, so the fallback also
  runs → `$((0\n0 - 0))` → `arithmetic syntax error` and `[: : integer expected`. Assign, then
  sanitise: `N=$(grep -c pat file); case "$N" in ''|*[!0-9]*) N=0 ;; esac`.
- **A PATH stub cannot intercept `termux-wake-lock` in the hermes keeper** — the script re-exports
  `PATH=$PREFIX/bin:…`, so `$PREFIX/bin/termux-wake-lock` always wins. Instrument a *copy* of the
  script with `sed` redirecting the call to a counter file, and point `LOG`/`FLAG`/`HELD` at a temp
  dir in the same `sed`.
- **`sed -e 's#…#echo … >> "$T/calls"#'`** with single quotes leaves `$T` unexpanded inside the
  generated copy (writes to `/calls`, silently permission-denied). Interpolate the temp path into the
  replacement in double quotes, or export a variable the copy inherits.
- **Never nest `"$( … "$( … )" … )"`** in a PASS/FAIL harness: the inner quotes terminate the outer
  string and the assertion silently evaluates garbage (it produced a false FAIL that took a manual
  reproduction to clear). Assign to a variable first, then test the variable.
- **A decoy process must outlive the whole window** — `sleep 40` under a 70 s keeper cycle expires on
  its own and reads as "the keeper killed it". Use `sleep 200`, then `kill` it.
