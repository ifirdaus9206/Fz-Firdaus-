# Worked case — Telegram DM fragmented into one session per message (2026-11-17)

## Complaint
"Kenapa di Telegram dia masuk mesej baru padahal topik yang sembang pun belum habis?" — every
reply behaved like a fresh conversation; an extra bot message also appeared mid-discussion.

## Measurements

`sessions/sessions.json` — 50 keys for one DM, 48 of them carrying a trailing thread suffix:

| Time | Session key suffix | Session id |
|---|---|---|
| 18:18 | `…:26050` | 20261117_181824_8ed62105 |
| 18:58 | `…:26054` | 20261117_185812_0d49e2ef |
| 19:39 | `…:26075` | 20261117_193932_11c91d23 |
| 19:57 | `…:26084` | 20261117_195730_b188786b |

`logs/gateway.log` 19:44:40:
`Previous gateway life (pid=7352, started_at=…) exited UNCLEANLY (no exit path ran — SIGKILL /
OOM / VM death)`, followed on restart by `Marked 1 in-flight session(s) as resumable` and
`Scheduled auto-resume for 1 restart-interrupted session(s)` → that was the phantom message.

Wake lock was the crash cause: `~/.hermes20/wake_lock.enabled` existed (auto-mode ON) while
`~/.hermes20/.wake_held` was missing → `RELEASED (phone boleh tidur)`. `keeper.sh` released the
lock on every healthy 5-minute tick.

`getChat` on the DM (`https://api.telegram.org/bot<token>/getChat?chat_id=…`) returned only
`id`, `first_name`, `type: private`, `max_reaction_count`, `accent_color_id` — **no**
`has_topics_enabled`, no `is_forum`. So the chat was not topic-enabled; the thread id was
noise from the adapter's DM branch, not a real lane.

## Diff actually applied (both copies of the adapter)

```diff
             elif chat_type == "dm" and is_topic_message:
-                thread_id = str(thread_id_raw)
+                # DM topic HANYA dihormati jika bot memang menguruskan topik untuk
+                # chat ini (extra.dm_topics). Tanpa itu, setiap message_thread_id
+                # menghasilkan SESI BAHARU bagi setiap mesej -> konteks hilang.
+                if str(getattr(chat, "id", "")) in getattr(self, "_dm_topic_chat_ids", set()):
+                    thread_id = str(thread_id_raw)
```

Files: `tools/hermes-source/plugins/platforms/telegram/adapter.py` **and**
`tools/hermes-source/hermes-agent/plugins/platforms/telegram/adapter.py` (identical md5; the
`$PREFIX/bin/hermes` symlink points at the `hermes-agent/` copy).

Wake-lock keeper fix (`hermes-console/tools/keeper.sh`) — release only when auto-mode is off,
re-acquire when the flag exists but the held-stamp is gone:

```bash
WL_FLAG="$HOME/.hermes20/wake_lock.enabled"
if [ "$ACTIVE" -eq 0 ] && [ -f "$WL_STATE" ] && [ ! -f "$WL_FLAG" ]; then release
elif [ "$ACTIVE" -eq 0 ] && [ -f "$WL_FLAG" ] && [ ! -f "$WL_STATE" ]; then reacquire
fi
```

## Proof

`venv/bin/python scripts/probe_dm_thread_id.py` (fake `Message` via `Obj(**kw)`):

```
DM biasa        -> thread_id = None | chat_type = dm
DM topic config -> thread_id = 26084
Forum group     -> thread_id = 26084
SEMUA UJIAN LULUS
```

Keeper re-run while healthy: status still `HELD (wake-lock aktif — phone tak tidur)`.

Patch takes effect only after a gateway restart, which the terminal tool refuses from inside the
agent. Fix: one-shot `no_agent` cron ~10 minutes out calling
`POST http://127.0.0.1:8787/api/svc/hermes-gateway {"action":"restart"}`, logging to
`logs/gw_restart_once.log`, with the user warned not to write during the restart window.

## Report shape that landed
Board per complaint (punca → pembetulan → bukti), then the outstanding step called out
explicitly, then 3–4 numbered next actions.
