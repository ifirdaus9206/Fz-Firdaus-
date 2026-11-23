# Worked case — "kenapa jadi macam terputus": gateway killed by Android, no agent running

User's words (CLI): *"buat semakan di telegram kenapa jadi macam terputus. buat semakan dulu terputus
atau sedang bekerja agen2 di dalam"*. He was not sure whether the bot was down or simply busy.

## Evidence collected (all read-only, ~3 tool rounds)

```
/api/agency/health → active_agents=0, runs {"jumlah":31,"selesai":24,"gagal":4,"aktif":2},
                     status {"done":24,"cancelled":1,"planned":2,"failed":4}, terakhir 2026-11-23T21:10
```

The `aktif: 2` entries were old `planned` rows — **no live work**. That single number ends the
"sedang bekerja" branch of the question; say it out loud in the report.

```
/api/health → homes[0].gateway:
  gateway_state=running, pid_alive=true,
  platforms.telegram.state=connected, updated_at=2026-11-23T16:05:27Z   (= 00:05 local, ~4 min before)
```

A `connected` platform with an `updated_at` four minutes old already hints at a fresh restart.

```
logs/gateway.log:
00:05:10 WARNING gateway.lifecycle_ledger: Previous gateway life (pid=16419, started_at=2026-11-23T09:49:03Z)
         exited UNCLEANLY (no exit path ran — SIGKILL / OOM).
         last_heartbeat_at=2026-11-23T16:05:02Z last_mem={'rss_kib':76308,'mem_total_kib':11688520,
         'mem_available_kib':3043988,'swap_used_kib':7941916} suspected_oom=False
00:05:13 Starting Hermes Gateway…
00:05:26 [Telegram] Connected to Telegram (polling mode)
```

```
17:49:03 WARNING gateway.lifecycle_ledger: Previous gateway life (pid=28139, started_at=06:34:39Z)
         exited UNCLEANLY … last_heartbeat_at=08:36:59Z
```

Two very different outages, same wording:

| kill detected | last heartbeat | restart | downtime | interpretation |
|---|---|---|---|---|
| 00:05:10 | 00:05:02 | 00:05:26 | ~24 s | runsv restarted the killed child |
| 17:49:03 | 16:36:59 | 17:49:05 | **73 min** | whole Termux tree was dead; runsv could not act until Termux was reopened |

Aggregate counts for the day: `grep -c "Starting Hermes Gateway"` = 36;
`grep -c "All connection attempts failed"` = 610.

```
free -m → Mem 11414 total, 7486 used, available 3497; Swap 12287 total, 7358 used
uptime  → up 3 days, load average: 20.65 22.90 21.88
ps aux --sort=-rss → gateway 177 MB; a `du -sk /…/.hermes20` at 29 % CPU (17 GB scan)
```

`hermes-console/app.py` `_size_worker()` loops `du -sk` over every registered home and
`time.sleep(300)` — the recurring du, plus six hermes processes, explains a load average of 20 on a
phone. Android LMK then SIGKILLs the gateway; `suspected_oom=False` only means the log could not
prove OOM, not that nothing was killed.

## Direction proof

- Outbound: `hermes send -t telegram "Ujian sambungan …"` → `Sent to telegram home channel
  (chat_id: 1312929583)` — token, allowlist and network fine going out.
- Inbound: last `inbound message` line was 23:49, last `Sending response` 00:02:06 (1760 chars).
  Nothing inbound after the 00:05:26 restart → messages sent during a dead window were never
  processed. `delivery_obligations` newest row `attempts=0` at 00:02 confirms nothing was left
  undelivered by the live process.

## Report shape that worked

Plain-Malay numbered evidence board: agents 0 aktif → gateway alive + uptime → outbound OK → kill
lines with timestamps → downtime table → machine pressure numbers → "mesej masuk terakhir 23:49" →
one-line conclusion ("Android membunuh proses kerana RAM/CPU sesak") → numbered 3–4 options
(test two-way now / reduce load / install wake-lock + boot keeper / all). He answers by number.
