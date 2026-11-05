# Observing an external worker (demo loop, trading bot, cron job)

The console often has to show a process it does **not** own: a paper-trading demo, a
scraper loop, a simulation. The worker writes CSV/JSONL/logs and knows nothing about the
console. Model it as a read-only observer, never as an import.

## 1. Data sources: prefer the worker's own artifacts

| Source | Use |
|---|---|
| `paper_trading_log.csv` (header + rows) | table + `rows_total` = live progress counter |
| `<worker>.log` (stdout tail) | recent cycles with timestamps → event feed |
| pid / cmdline | liveness only (never for state) |
| worker's `.pid` file | convenience; **do not trust it** (see §4) |

Shape returned by the API (`paper_live` in practice):

```python
{"alive": bool, "procs": [{"pid": int, "cmd": str}],
 "header": [...], "rows": [...last 12...], "rows_total": int,
 "events": [...last 8 "[ts] STATUS ..." lines...],
 "csv": "~/…/paper_trading_log.csv", "csv_mtime": "2026-11-03T02:19:11"}
```

Read the file fresh each request (they are small); no cache, no DB. Parse leniently:
`split(",")`, strip, skip blank lines, tolerate a CRLF header (Excel-style exports do).

## 2. Liveness without pgrep

`pgrep` is not guaranteed and `pkill -f` is banned in this project (it kills the caller).
Scan `/proc`:

```python
def _proc_alive(pattern: str) -> dict:
    hits = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            cmd = Path(f"/proc/{pid}/cmdline").read_bytes().decode("utf-8", "replace")
        except Exception:
            continue
        if pattern in cmd.replace("\x00", " "):
            hits.append({"pid": int(pid), "cmd": cmd.replace("\x00", " ").strip()[:160]})
    return {"alive": bool(hits), "procs": hits[:3]}
```

Match on a distinctive script name (`run_paper.py`), not on a language (`python3`).

## 3. UI: a status strip plus a cycle feed

Two elements are enough, and both must show real numbers:

- strip: `HIDUP|MATI` tag · `pid N` · interval · `N paper trade` · `csv_mtime`
  (the mtime is the cheapest proof the worker is *advancing* right now);
- feed: last 8 log cycles `HH:MM:SS · ATC · TRADE_CANDIDATE BUY conf=0.9`, colour by
  `NO_TRADE|VETO` vs trade.

Add one render-test assertion (`#tr-pl-strip` non-empty) so a rename can't silently blank it.

## 4. Pitfall: the pid file lies in both directions

- Started manually (`setsid python3 -u run_paper.py &`) → no pid file → `status` prints
  **MATI while the process is alive**, and the user believes the demo is dead.
- Failed start on a busy port leaves a stale pid → `stop` targets nothing.

Fix: a control script that **adopts** an existing process before deciding anything.

```bash
find_pid() {                       # first matching /proc cmdline
  for d in /proc/[0-9]*; do
    tr '\0' ' ' < "$d/cmdline" 2>/dev/null | grep -q "run_paper.py" && { basename "$d"; return 0; }
  done
  return 1
}
adopt() { alive || { p=$(find_pid) || return 1; echo "$p" > "$PIDF"; }; }
```

Then `start` = `adopt && already-running`; `stop` = `adopt && kill`; `status` = `adopt; …`.
Give the user one script with `start|stop|status [interval]` rather than a raw python
command line — the console then has a stable contract it can point at.

## 5. Prove it is live, not a snapshot

Two readings ≥ one cycle apart, same pid, growing counters:

```
02:19  alive true · pid 22204 · 7 trades · 2 events
02:21  alive true · pid 22204 · 9 trades · 4 events
02:23  alive true · pid 22204 · 11 trades · 6 events
```

Growing counters prove the *loop* is alive — they do not prove the *data* is real. A worker can
advance happily while stamping every row `mode: backtest`, `timestamp 2024-01-01` with stub
prices. Until you replace that with a real feed and real clock (§7) and prove it from the artifact
(CSV row carries today's UTC time and `mode=paper`), say: "pipeline proven; market data is not."
Never let "demo running" imply live prices.

## 6. When the named demo does not exist

`find ~ /sdcard -iname '*name*'`, `grep -ril name`, then session history. If all empty:
say it plainly with the paths searched, run the nearest existing equivalent, and offer to
run theirs once they send it. Do not invent a run.

## 7. Giving the worker a real market feed

Shape that worked (ATC + MetaAPI + Yahoo), portable to any "demo loop needs real prices":

```
market/data_feed.py        # provider chain, cache, status file
market/metaapi_bridge.py   # runs INSIDE the provider SDK venv, prints JSON on stdout
market/ (worker .py)       # worker imports data_feed.candles(symbol, tf, limit)
data/feed_status.json      # last source/price/errors — read by the console
```

- **Bridge, don't install.** The worker runs on system python; the provider SDK
  (`metaapi_cloud_sdk`) lives in a project venv (`~/.hermes19/meta5/venv/bin/python`).
  Call it as a subprocess and parse the last stdout line as JSON — no dependency surgery on the
  worker, and a bridge failure is a string, not a crash:

  ```python
  p = subprocess.run([VENV_PY, BRIDGE, symbol, tf, str(limit)], capture_output=True,
                     text=True, timeout=120)
  data = json.loads((p.stdout or "").strip().splitlines()[-1])
  if not data.get("ok"): raise RuntimeError(data.get("error"))
  ```

- **Chain with recorded failure + short TTL cache (20 s).** Each provider that fails appends
  `{name: "ExceptionType: msg"}` to `errors[]`; the successful meta carries `source`, `price`,
  `last_time`, `proxy`, `errors`. Write `data/feed_status.json` on every resolution *and* on total
  failure — the UI reads it either way.
- **Free fallback: Yahoo chart API** (no key):

  ```
  https://query1.finance.yahoo.com/v8/finance/chart/<sym>?range=1d&interval=1m
  → chart.result[0].timestamp[] + indicators.quote[0].{open,high,low,close,volume}
  ```

  `XAUUSD=X` / `XAGUSD=X` **404**. Map metals & oil to futures (`GC=F`, `SI=F`, `CL=F`, `BZ=F`) and
  set `proxy: true` + a note; FX (`EURUSD=X`, `GBPUSD=X`, `USDJPY=X`) is genuine spot. Sentiment:
  a `User-Agent` header is required or you get an HTML error page.
- **Resample missing timeframes yourself**: `4h` from four `60m` bars (max high / min low / last
  close / summed volume). Brains that only read the last candle still need the right shape.
- **MetaAPI specifics**: provisioning API answers `GET /users/current/accounts` with `auth-token`;
  market data needs `state == "DEPLOYED"`; deployment is billing-gated
  (`ForbiddenException: … please top up your account`). Quote that verbatim in the report and label
  the fallback in the UI (`feed: yahoo GC=F 3969.5 (proksi)` + red `MetaAPI: belum deploy`).
- **Fix the worker's clock too.** `decision_engine`-style placeholders (`timestamp: 2024-01-01`,
  `mode: backtest`, `symbol: XAUUSD` hardcoded) keep every row fake even with real candles. Use
  `datetime.now(timezone.utc).isoformat()`, a mode from `ATC_MODE`, and pass the requested symbol
  through. Prove it by tailing the CSV, not the banner.

## 8. Credential archaeology (demo vs live)

The user "already gave" keys months ago; they live in some project `.env`, not in memory.

1. **Enumerate without leaking**: `find ~ -maxdepth 5 -name ".env"`, then per file
   `grep -oE '^[A-Z0-9_]+'` → key names only. Never `cat` an env file into the transcript.
2. **Fingerprint**: `sha256(token)[:8]` distinguishes the demo token from the live one in a report
   without printing either ("token `e7cf25cd`, akaun 1300009388 demo").
3. **Copy the requested account only** into the worker's `.env`, `chmod 600`, and state that the
   live token was deliberately left where it was. Keep `*_ACCOUNT_TYPE=demo` visible.
4. **Verify state at the provider before promising data** (see §7); if it is `UNDEPLOYED`, that is
   the headline, not an afterthought.
5. **Report the fix, not a verdict**: "top-up → `deploy()` → feed switches to `metaapi-demo`
   automatically" is actionable; "MetaAPI tak boleh guna" is not.
