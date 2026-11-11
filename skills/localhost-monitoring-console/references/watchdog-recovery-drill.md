# Recovery drill — proving a console keeper actually restores service

Written after a live drill on Termux (Android, no root), consoles on **8787** (`~hermes-console`,
home `hermes20`) and **8790** (home `hermes19`), keeper at
`~/.hermes20/scripts/console_keeper.sh` → `~/hermes-console/tools/keeper.sh`.

The point of a drill is not "the keeper ran" — it is a **measured recovery time** plus proof that
nothing was left hanging. A supervisor that is only ever observed while healthy is not verified.

## Measured result (2026-11-10, one cycle)

| t (s) from `kill -TERM` | event | evidence |
|---|---|---|
| 0 | `kill -TERM 24861` (app.py, 8787) | exit 0 |
| 2 | death confirmed | HTTP `000`, curl rc=7, PID gone |
| 4 | keeper started (wrapper → `keeper.sh`) | t0 marker |
| 12 | keeper finished: exit 0, **8s**, printed `8787 dipulihkan` | ping already 200 |
| **16** | recovery confirmed by poll | HTTP 200 |

Keeper cost = `sleep 6` + uvicorn boot ≈ 8 s. Total-from-kill includes the operator's own gap
between "death confirmed" and "keeper launched" — report both numbers, and say which is which, or
the keeper looks 2× slower than it is.

## Procedure (one cycle only)

```bash
# 1 baseline — BOTH ports must be 200, else stop and report
curl -s -m 3 -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8787/api/ping
curl -s -m 3 -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8790/api/ping

# 2 take the pid from the pid file and PROVE it is the right process
cat ~/hermes-console/server-8787.pid
ps -o pid,ppid,args -p <pid>          # must be python3 ... app.py

# 3-4 kill and confirm death (max 10s)
t0=$(date +%s); kill -TERM <pid>
for i in $(seq 1 10); do
  code=$(curl -s -m 2 -o /dev/null -w '%{http_code}' http://127.0.0.1:8787/api/ping)
  echo "t+${i}s code=$code"
  [ "$code" != "200" ] && { echo "mati disahkan"; break; }; sleep 1
done

# 5 run the keeper under an outer timeout, as cron would
start=$(date +%s); timeout 70 ~/.hermes20/scripts/console_keeper.sh; rc=$?
echo "exit=$rc masa=$(( $(date +%s)-start ))s"

# 6 poll 1s for up to 90s, report "PULIH dalam Ns"
# 7 final: both ports 200, no keeper leftovers, NEW pid + pidfile content match
```

Bound the keeper with `timeout 70` in the drill even though the wrapper already uses
`timeout 55`: the outer bound is what turns "hung again" into a number instead of a stuck call.

## Trap 1 — two identical `python3 app.py` rows are NOT a duplicate

`ps -eo pid,args | grep app.py` on a two-port setup prints two indistinguishable lines. That reads
as "the keeper double-started the console", and the instinct is to kill one — which is how you take
down the other home's console.

Resolve by port, never by name:

```bash
for p in 25498 25549; do
  echo "=== $p ==="
  tr '\0' '\n' < /proc/$p/environ | grep -E '^CONSOLE_(PORT|HOST)='
  ls -l /proc/$p/cwd
  ps -o pid,ppid,lstart,etime,args -p $p
done
# 25498 → CONSOLE_PORT=8790   (untouched, ~2h old)
# 25549 → CONSOLE_PORT=8787   (the replacement, pidfile matches)
```

On Android `ss -ltnp` is useless: **`Cannot open netlink socket: Permission denied`**, and
`/proc/net/tcp` is `Permission denied` too. `lsof` is present but rejects `-nP`, and socket-fd
*counts* are identical for both processes, so fds prove nothing either. `/proc/<pid>/environ` plus
`cwd` is the reliable discriminator. Corroborate with `etime` — the 8790 process was ~103 min old,
i.e. it predated the drill, so it cannot be a keeper artifact.

## Trap 2 — a transient `keeper.sh` in `ps` is the cron tick, not an orphan

`ps -eo pid,args | grep -c '[k]eeper.sh'` returned **2** once and **0** thirty seconds later. The
5-minute cron legitimately spawns a keeper that lives a few seconds. Decide "hanging" only from a
**sampled window**:

```bash
for i in 1 2 3 4 5; do
  echo "[$i] $(ps -eo pid,ppid,args | grep -E '[k]eeper\.sh|[t]imeout 55' | tr '\n' '|')"
  sleep 2
done
```

Five empty samples over 10 s = clean. A real orphan from the old bug looks different and is
identifiable: `PPID 1`, `wchan = do_wait` (see `cron-failure-forensics.md`), i.e. it persists across
every sample.

## Trap 3 — report the pid file, not just "it's up"

The replacement must be checked three ways: live process exists, `server-8787.pid` contains the new
pid, and that pid's `ppid` is `1` (proves `setsid --fork` detached properly). A pidfile pointing at a
dead pid is the failure mode that makes the *next* stop/start hit the wrong process.

## If the keeper fails

Do not hide it. Recover manually with the detached launcher and then read the log:

```bash
cd ~/hermes-console && setsid --fork ./run.sh >> server.log 2>&1 < /dev/null &
sleep 15; curl -s -m 3 -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8787/api/ping
tail -n 20 ~/hermes-console/server.log
```

Report the keeper failure and the log tail as the cause; never present the manual restore as a pass.
