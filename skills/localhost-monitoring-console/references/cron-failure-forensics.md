# Forensics for a failed `no_agent` cron health check

Symptom the user pastes in chat:

```
⚠️ Cron 'Ujian Mingguan Ejen Ketua' failed: Script exited with code 1
❌ API console tidak menjawab: URLError: <urlopen error [Errno 111] Connection refused>
❌ Dashboard ejen: 0/282 lulus · median Nonems
❌ Paparan (UI): 2 lulus, 15 gagal
✅ Pemulihan respons kosong + baris verdict lulus
```

Three red lines look like three broken subsystems. In practice they were **one**
transient cause: the check ran while the console was not yet listening (boot race).
Do not start fixing subsystems until you have placed the run on a timeline.

## 1. Place the run on a timeline (the decisive step)

`cronjob action='list'` gives `last_run_at`, and
`~/.hermesNN/cron/output/<job_id>/<timestamp>.md` holds the report.

**`Run Time:` in that file is when the run FINISHED, not when it started.** The
report itself usually ends with `Masa: NNNs` (its own duration). Subtract:

```
Run Time 15:30:20 − Masa 304s  →  started ≈ 15:25:16
```

Then compare that computed start against everything else that has a start time:

```bash
tail -30 ~/.hermesNN/logs/gateway.log        # "Gateway running" / boot
ps -o pid,lstart,etime,args -C python3 | grep app.py   # etime of the console
ls -l --time-style='+%F %T' <project>/reports/VERIFIKASI.json <project>/data/*.json
```

Real numbers from the case above: weekly check started **15:25:16**; gateway
started **15:25:00**; console `app.py` pids had `etime` putting their start at
**15:25:10 / 15:25:19**; `reports/VERIFIKASI.json` was written **15:25:17** with
`api_gagal: 282`. The verification ran the same second the server was still
coming up. Because the weekly slot was Monday 09:00 and the phone had been off,
cron fired the missed job as **catch-up immediately on boot** — it raced startup.

`/proc/uptime` is unreadable on Android/Termux, so use `ps -o etime`/`lstart`
and `uptime` instead.

## 2. Prove the cascade, then prove current health

Cascade rule of thumb: every line that needs the HTTP API fails, and any line that
does not (offline unit test) still passes. That pattern means one root cause.

Prove health **now**, with fresh numbers, before recommending any repair:

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8787/api/ping
curl -s http://127.0.0.1:8787/api/agency/health
cd <project> && python3 tools/verify_roster.py     # expect api_ok == ejen
cd <project> && node tools/test_ui.js              # expect zero GAGAL
```

Measured after the incident: `ping 200`, roster 282, `282/282 lulus · median 574ms`,
`SEMUA UJIAN PAPAN LULUS`. The previous week's report (same job, console already
running) was all-green, which confirms the difference was timing, not code.

A verdict line such as `E2E: 2/2 ejen selesai · STATUS AKHIR: NEEDS_WORK` is **not**
a failure — the step is marked ✅ and the verdict is payload. Say so explicitly or
the user reads it as a fourth fault.

## 3. Measure startup cost instead of guessing — without touching the live port

Start a second instance on a spare port and poll it:

```bash
cd <project> && CONSOLE_PORT=8799 ./run.sh > ~/probe8799.log 2>&1   # background=true
for i in $(seq 1 120); do curl -s -m 2 -o /dev/null http://127.0.0.1:8799/api/ping \
  && echo "SIAP dalam ${i}s" && break; sleep 1; done
kill "$(cat <project>/server-8799.pid)"; rm -f <project>/server-8799.pid
```

Measured **1 s** to first successful ping. That rules out "the app is slow to boot"
and leaves only "the check ran before/while the app was frozen or not spawned".
Note: `run.sh` writes `server-<port>.pid`, so cleanup is per-port.

## 4. Check whether the supervisor itself was stuck

A hung keeper is invisible in the check output but explains slow recovery. Look for
a cron run that never produced a normal report:

```
# Cron Job: Penjaga Hermes Console
**Status:** script failed
Script timed out after 3600s: /…/scripts/console_keeper.sh
```

Then look for survivors of that timed-out run — orphans reparent to pid 1:

```bash
ps -eo pid,ppid,etime,args | grep -E 'keeper\.sh|app\.py' | grep -v grep
cat /proc/<keeper_pid>/wchan        # "do_wait" = blocked waiting on a child
ls -l /proc/<keeper_pid>/fd         # stdout/stderr are the cron capture pipes
```

Measured: two `keeper.sh` processes alive ~70 min with `PPID 1`, each the direct
parent of an `app.py`, both in `do_wait`. Consequence to state plainly: the keeper
never returned, so cron timed it out after an hour and **no supervision tick ran in
that hour** — the console stayed unsupervised right when it was needed.

Magnitude check: a keeper cron run that normally finishes in seconds and produces
either silence or one "dipulihkan" line has no business running 3600 s.

## 4b. The applied, verified fix (2026-11-10)

Root cause of the hang is the **launch pattern**, not the keeper logic. This form does
*not* release the child on Termux/Android, so the keeper subshell keeps waiting on
`app.py` and cron never sees the script exit:

```bash
( cd "$HC" && rm -f server.pid && setsid ./run.sh >> server.log 2>&1 < /dev/null & )   # hangs
( cd "$HC" && rm -f server.pid && setsid --fork ./run.sh >> server.log 2>&1 < /dev/null & )  # correct
```

`setsid --fork` is supported on Termux (`setsid --help` shows `-f, --fork`). Verify the
pattern in isolation before touching the live keeper — script file in `$HOME`, never `/tmp`:

```bash
#!/data/data/com.termux/files/usr/bin/bash
s1=$(date +%s); ( setsid --fork sleep 4 </dev/null >/dev/null 2>&1 & ); s2=$(date +%s)
echo "detached after $((s2-s1))s"
```
Measured: `detached after 0s`, whole script `real 0m0.068s`. Inline `time ( ... & )` one-liners
through the terminal tool got mangled (`output " -1"`, no file written) — put the probe in a
script file and delete it afterwards.

Bound the cron wrapper so a stuck tick can never occupy an hour (keep shebang + comments):

```bash
exec /data/data/com.termux/files/usr/bin/timeout 55 /…/hermes-console/tools/keeper.sh
```

**The timeout wrapper fails with exit 126 if the target is not executable.** The wrapper in
`~/.hermesNN/scripts/` was mode `-rw-------` (cron ran it as `bash script`, so nothing noticed):

```
timeout: failed to run command '…/console_keeper.sh': Permission denied
real 0m0.019s   EXIT=126
```

`chmod +x` the wrapper and the keeper, then re-run. Measured after the fix: wrapper run
`real 0m0.211s`, exit 0, **no output** (healthy = silent), keeper pids gone, `app.py` pids
untouched at `PPID 1` serving 200.

Cleanup rule that made this safe: kill **only** the keeper pids (`ps -o pid,args -p 24854,25497`
first, then `kill -TERM`), never `pkill -f app.py` — the `app.py` children keep serving and are
reparented to 1 by themselves.

## 4c. Mitigations checklist (all four now confirmed)
- bound the cron wrapper: `timeout 55 <real keeper>` so a stuck tick cannot occupy
  an hour (55 keeps it inside a `*/5` slot);
- make the server launch fully detached and prove it: after a repair, the server's
  `ps -o ppid` must be `1`, and the keeper must exit within a few seconds;
- kill leftover keeper shells (they only hold the cron pipes; the `app.py` children keep serving);
- **re-run the job that actually failed** as the acceptance gate (see §5b) — a passing
  `tunggu_api()` sanity call only proves the helper, not the suite.

## 5. The durable fix for the class, not the instance

Any health check that talks to a service can race that service's startup after a
reboot. Give the script a readiness gate before step 1 and make "not up yet" a
distinct, non-alarming outcome. **Applied and verified in `tools/weekly_check.py`**
(2026-11-10): module-level `def tunggu_api(maks_saat: int = 120) -> bool:` reusing the
existing `BASE`, and a single `tunggu_api()` call in `main()` immediately before
`h = get("/api/agency/health")`. Do not touch the Telegram output format or the later
steps while adding it. Sanity check without running the whole suite:
`python3 -c "import time,weekly_check as w; t=time.time(); print(w.tunggu_api(), round(time.time()-t,2))"`
→ `True 0.05s` when the console is up.

```python
def wait_api(base, timeout=120):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(base + "/api/ping", timeout=3):
                return True
        except Exception:
            time.sleep(3)
    return False
```

If it still fails after the gate, that is a real fault and should exit non-zero.
Schedule hygiene that also prevents the false alarm: avoid slots the device is
likely to be off for, or accept that a missed slot will be replayed at boot and
gate the script accordingly.

## 5b. Acceptance gate — re-run the failing job, and know where to look while it runs

After `setsid --fork`, `timeout 55`, `chmod +x` and the readiness gate are in place, the proof is the
**real entrypoint**, not a helper probe:

```bash
cd <project> && python3 tools/weekly_check.py     # background=true + notify_on_complete
```

Measured green run (2026-11-10, after repair): `EXIT=0`, 5/5 steps ✅ — `API hidup · roster 282 ·
run 18/22`, `282/282 lulus · median 533ms`, `17 semakan lulus`, LLM-retry ✅,
`E2E 2/2 ejen selesai`, total `390s`. Quote those numbers; "semua lulus" alone is not evidence.

Two traps while waiting (both looked like a hang this session):

- **`| tee run.log` under `background=true` buffers — the log stays empty for the whole run.**
  Poll real state instead: `ps -eo pid,etime,args | grep test_agents` (which step is live), the
  newest `runs/<id>/` directory, and `/api/agency/health` → `runs.aktif` / `runs.terakhir`. The log
  lands in one chunk on exit.
- **`process(action='wait')` clamps to ~180 s** (`Requested wait of 420s was clamped to configured
  limit of 180s`). Repeat short waits; do not read a clamp as "still stuck".

Also re-run the supervisor itself as a unit: `timeout 70 ~/.hermesNN/scripts/console_keeper.sh`
must finish in ~0 s with **no output** while both ports answer 200 — silence is the healthy signal,
and any printed line means it had to repair something.


## 6. Report shape that worked

Malay, plain text: one-line conclusion ("sistem tidak rosak; ujian berlari masa
console belum hidup"), a table of evidence (time · what · proof), the cascaded
lines explained as one cause, the *separate* real problem (hung keeper) called out,
and 3–4 numbered options with the smallest-risk fix first. Do not report the
cascade as three faults and do not offer to change code before the user picks.
