# Restarting a uvicorn/FastAPI runit service without hanging the turn

Measured 2026-11-23 on the Hermes console (`hermes-console`, uvicorn on 127.0.0.1:8787).

## Symptom

```
sv restart hermes-console   → "timeout: run: hermes-console: (pid 25331) 1005s, got TERM"   (exit 1)
sv status hermes-console    → "run: hermes-console: (pid 25331) 1023s, got TERM"
curl 127.0.0.1:8787         → 000   (service is DOWN, and runsv is still waiting)
```

`sv down` behaves the same way: TERM is delivered, the process does not exit, runsv keeps
waiting, and the port stops answering. So the "safe" restart recipe from the main skill
(`sv down; sleep 2; sv up`) is *not* safe for uvicorn on this device — it takes the service down
and leaves it there.

## Recovery that works

```bash
P=$(sv status hermes-console | sed -n 's/^run: hermes-console: (pid \([0-9][0-9]*\)).*/\1/p')
echo "app_pid=$P"            # verify this is the uvicorn pid, not the logger
[ -n "$P" ] && kill -9 "$P"
sleep 3
sv up hermes-console
sleep 8
curl -s -m 10 -o /dev/null -w "konsol=%{http_code}\n" http://127.0.0.1:8787/
```

## Two traps in that one-liner

1. **`sv status` prints TWO pids.** Format:
   `run: <name>: (pid 12345) 37s; run: log: (pid 67890) 16s`
   The first is the app; the second is the svlogd logger. A sloppy
   `sed -n 's/.*pid \([0-9]*\).*/\1/p' | head -1` happened to work, but killing the *second*
   pid (the logger) leaves the app untouched while looking like a successful restart — the old
   code kept serving, so a code patch appeared "not applied". Anchor the regex with `^run: <name>:`
   so only the supervised process matches.
2. **Never derive a kill target from a pattern typed in the same command line.**
   `pgrep -f "python3 -u app.py"` matches the agent's own `bash -c` wrapper, whose command line
   *contains that pattern*; the following `kill -9 $(pgrep …)` therefore kills the calling
   command (exit `-9`, empty output, no restart). Same family as the `pkill -f` pitfall, but it
   also bites `pgrep` + `kill`. Parse the pid from `sv status` (or `ps -eo pid,args` piped through
   `grep -v grep`) instead.

## Verification after any restart

```bash
sv status hermes-console | head -1     # "run: … (pid NEW) 1–10s", uptime must be small = fresh
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8787/          # 200
curl -s http://127.0.0.1:8787/api/<new-endpoint> | head -c 120         # proves the NEW code loaded
```

The third probe is the one that matters after a code change: a 200 alone only proves the old
process is alive. If the new endpoint is still missing (or returns the old shape, e.g. a cron
`schedule` still rendered as an object), the restart never took effect.
