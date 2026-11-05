# Instance supervision & "the console won't open"

Two things every multi-instance localhost console eventually hits: the user says
*"kenapa di sini pun tak boleh buka http://127.0.0.1:8787"*, and one of the two
instances silently stops being reachable. Both are process-lifecycle problems,
not app bugs — diagnose in this order, then fix permanently.

## 1. Diagnosis order (do not guess, do not restart first)

Run these as separate small commands (compound one-liners get rejected):

```bash
cat <project>/server.pid                 # is the pid even alive?
ps -ef | grep -E "app\.py|uvicorn" | grep -v grep
(ss -ltnp || netstat -ltnp) | grep -E "8787|8790"
curl -s -m 5 -o /dev/null -w "http=%{http_code}\n" http://127.0.0.1:8787/api/ping
uptime                                   # <-- the decisive one
tail -30 <project>/server.log
```

Real case (measured): pid file said `23946`, `ps` empty, no listening port,
`curl` → `http=000`, and `uptime` → **up 28 min**. Conclusion in one line: the
phone/Termux restarted and killed the daemons; the stale pid file meant nothing
restarted them. `server.log` held only `WARNING: Invalid HTTP request received.`
— that line means somebody hit the **HTTP** port with `https://` or otherwise
non-HTTP bytes; it is a symptom of the user retrying, not the cause.

Report the table, not prose: symptom → command → result. Users accept "pelayan
mati" only when they can see `http=000` and the uptime.

## 2. One pid file per port (the shared-pid bug)

Both instances are the same `app.py`, so with a single `server.pid` the second
start overwrites the first's pid. Consequence, proven by test: `stop_server.py`
was asked to stop 8787 and killed **8790** instead (`dihentikan: [9808]`, 8787
still `200`, 8790 `000`). Anyone debugging "why did my other instance die"
loses an hour here.

Fix inside `app.py`:

```python
pidf = Path(__file__).resolve().parent / f"server-{CONSOLE_PORT}.pid"
pidf.write_text(str(os.getpid()))
if CONSOLE_PORT == 8787:                      # backward compatible
    (Path(__file__).resolve().parent / "server.pid").write_text(str(os.getpid()))
```

And in the stop tool: `--port N` / `--all`, reading `server-<port>.pid` first,
and when falling back to a `/proc` scan, confirm the port via
`/proc/<pid>/environ` (`CONSOLE_PORT=`) before signalling. Never `pkill -f`.

Verification that proves isolation (quote it):

```
python3 tools/stop_server.py --port 8790
8790 dihentikan: [9804]        # 8787=200  8790=000
bash tools/keeper.sh
8790 dipulihkan                # 8787=200  8790=200
```

## 3. Startup + supervision scripts

`tools/start_all.sh` — idempotent: `ping_ok PORT || start`, then wait up to 20 s
and print a status block. Safe to run any number of times, so it can be the
answer to "how do I start it" without apologising for failures.

`tools/keeper.sh` — the supervisor. Per port: `ping_ok || (start; sleep 6;
ping_ok ? print "PORT dipulihkan" : print "PORT GAGAL dipulihkan — semak log")`.
**Print nothing when both are healthy.** That silence is what makes it safe to
schedule: an empty stdout means no message.

Schedule it with `no_agent` cron (`*/5 * * * *`), delivering to the origin chat:

- Hermes cron rejects absolute script paths (`Script path must be relative to
  ~/.hermes/scripts/`). Put a 3-line wrapper in
  `~/.hermes20/scripts/console_keeper.sh` that `exec`s the real script.
- Verify with `cronjob action='run'` → expect `last_status: ok` **and no message
  arriving in chat** (healthy = silent). A job that chats every 5 minutes gets
  muted by the user and then a real alert is missed.
- Hold `termux-wake-lock` in both scripts, or Android dozes the process anyway.

Both scripts live in the project (`tools/`), not in the skill, because their
paths are project-specific — `scripts/supervise_consoles.sh` in this skill is the
env-driven starting point.

## 4. UI freezes that look like "the server is down"

Two frontend bugs found in the same session; both present as a pane that stays
on `memuat…` forever.

1. **Busy-flag drops render requests.** `loadTab()` started with
   `if (S.busy) return;` — switching tabs while a slow fetch was in flight threw
   the new request away, so the new tab never rendered. Fix: remember and re-run.

```js
if (S.busy) { S.pending = true; return; }
S.busy = true;
try {
  do { S.pending = false; try { /* ...per-tab branches... */ } catch (e) { ... } }
  while (S.pending);
} finally { S.busy = false; }
```

2. **No fetch timeout.** A single hung endpoint froze every tab, because the
   in-flight `loadTab()` never resolved and `busy` stayed true. Wrap `api()`:

```js
const ac = new AbortController();
const timer = setTimeout(() => ac.abort(), opts.timeout || 25000);
try { r = await fetch(path, {...o, headers, signal: ac.signal}); }
catch (e) { throw new Error(e.name === "AbortError" ? `tamat masa: ${path}` : e.message); }
finally { clearTimeout(timer); }
```

Consequence for the DOM-shim harness: it must stub `AbortController` next to
`URLSearchParams`/`performance`, or every tab fails with
`AbortController is not defined` and it reads like a total app crash.

## 5. Slow endpoint vs test wait

`/api/device/status` shells out (`pm list packages`) and measured **1.4 s, 4.3 s,
2.2 s** on consecutive calls. A render test that waits 1200 ms after
`setTab("panduan")` fails 2 checks every run — and the failure is in the harness,
not the page. Raise that specific wait to ~6 s and comment why.

## 6. Instrumenting a shim run without leaving debris

When a tab renders fine when called directly but not through `setTab`, prove
where it is stuck rather than guessing:

1. add `S.stage = "<tab>"` before each branch in `loadTab()`;
2. expose a read-only hook at the end of `app.js`
   `try { globalThis.__hcState = () => ({tab:S.tab, stage:S.stage, busy:S.busy, pending:!!S.pending}); } catch(_e){}`
   (`const S` never appears on the vm global, so a hook is the only way to read it);
3. print `ctx.__hcState()` in the test at the failure point;
4. **remove both** once diagnosed — verify with
   `grep -c "S.stage\|__hcState" static/app.js` → `0`, then re-run the suite.

Measured value of this: `{"tab":"panduan","stage":"panduan","busy":true}` proved
the work *had* started (so not the busy flag this time) and pointed at timing.

## 7. What to hand the user

A runbook file in the project (`OPERASI.md`) beats chat prose: cause table,
the two ports, the four commands (`start_all.sh`, `keeper.sh`,
`stop_server.py --port`, `stop_server.py --all`), the cron id/schedule, the list
of fixes with their evidence, and a "kalau masih tak terbuka" section covering
`http://` vs `https://` and LAN mode (`run.sh --lan` + token URL).
