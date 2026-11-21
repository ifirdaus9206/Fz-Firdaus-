# Worked case — "mesej tak boleh dah ikut arahan pun tak balas" (bot silent, gateway healthy)

Date of case: 2026-11-20. Chat: Telegram DM `1312929583` (@ainafz_bot), Hermes home `~/.hermes20`.
Outcome: cause found and fixed in ~10 minutes without restarting the gateway.

## What the user reported

"pergi ke telegram buat semakan kenapa mesej tak boleh dah ikut arahan pun tak balas" — messages are
not obeyed and nothing comes back. Two messages sent 10:14 and 10:16.

## What the shallow checks said (all green — misleading)

```
sv status hermes-gateway        -> run: hermes-gateway: (pid 7028) 567s
logs/gateway.log                -> [Telegram] Connected to Telegram (polling mode)
                                   ✓ telegram connected, 1 platform(s), 55 targets
logs/errors.log                 -> only registry check_fn noise, nemo_relay ModuleNotFoundError,
                                   tirith exit -6 (all pre-existing, unrelated)
```

If you stop here you conclude "network fine, nothing to fix" — which is wrong.

## The tell

```
2026-11-20 10:14:24 [Telegram] Sending response (304 chars) to 1312929583
2026-11-20 10:14:59 [Telegram] Flushing text batch agent:main:telegram:dm:1312929583 (37 chars)
2026-11-20 10:14:59 [Telegram] Sending response (267 chars) to 1312929583
2026-11-20 10:15:55 [Telegram] Sending response (304 chars) to 1312929583
2026-11-20 10:16:12 [Telegram] Flushing text batch agent:main:telegram:dm:1312929583 (8 chars)
2026-11-20 10:16:12 [Telegram] Sending response (267 chars) to 1312929583
```

Same 267 twice, and the earlier 19/11 19:57, 20:09 replies were also 267. A model answer never keeps
an identical length; a template does. Note there is **no thread id** in the batch key — the inbound
messages had no `message_thread_id`, i.e. they were typed in the root DM.

## Template mapping (lengths measured, use them as a fingerprint)

| chars | function | fires when |
|---|---|---|
| 267 | `_telegram_topic_root_lobby_message()` in `gateway/run.py` (~L6777) | any prompt in the root DM while topic mode is ON |
| 304 | `_telegram_topic_root_new_message()` | `/new` typed in the root DM while topic mode is ON |
| 223 | `_telegram_topic_new_header()` | `/new` inside an existing topic |
| 1644 | topic-mode activation intro | `/topic` just enabled (also creates/pins the System topic) |

Locate with: `grep -rn "reserved for system commands" tools/hermes-source/hermes-agent`.

## State evidence (state.db)

`delivery_obligations` held the exact delivered text, `thread_id=None`, state `delivered`, one row per
rejected message — the single best artifact to quote in the report:

```
('…', 'agent:main:telegram:dm:1312929583', 'telegram', '1312929583', None,
 'This main chat is reserved for system commands.\n\nTo start a new Hermes chat, open the All Messages
  topic at the top of this bot interface and send any message there. Telegram will create a new topic
  for that message; each topic works as an independent Hermes session.', 'delivered', 0, …)
```

`sessions` proved the agent never ran: the newest `source='telegram'` row was
`20261110_163224_3109309a`, `thread_id=None`, `last_activity_at` 19/11 19:12 — nothing for 20/11.

`telegram_dm_topic_mode` → `('1312929583','1312929583', 1, 1795087581…)` = enabled since 19/11 19:26;
`telegram_dm_topic_bindings` → **0 rows**. Topic mode had been switched on (gateway log 19:26:21
"Created DM topic 'System' … thread_id=26359") but the user never typed inside a topic, so every one
of his messages fell into the reserved root lobby for ~15 hours.

## Fix applied

```python
UPDATE telegram_dm_topic_mode SET enabled=0, updated_at=<now> WHERE chat_id='1312929583'
DELETE FROM telegram_dm_topic_bindings WHERE chat_id='1312929583'
```

Safe to do live: `hermes_state.is_telegram_topic_mode_enabled()` runs a fresh `SELECT` per inbound
message (no in-process cache), so the next message already routes normally — **no gateway restart**.
The clean alternative is telling the user to send `/topic off` in the root DM, which runs
`disable_telegram_topic_mode(clear_bindings=True)` and sends a confirmation.

## Verification that counts

Ask for one test message, then check all three: a `Flushing text batch …` line, a response with a
length that is *not* 267, and a new/updated `source='telegram'` row in `sessions`. Do not claim
success from the DB write alone.

## Side effect worth flagging

Cron delivery in this chat also broke while topic mode was on:

```
WARNING cron.scheduler: Job 'b3aa5823840f': origin has thread_id=26054 but delivery target lost it
(deliver=telegram, target={'chat_id':'1312929583','thread_id':None})
```

Cron output lands in the root lobby in topic mode. Once topic mode stays on permanently, the durable
answer is a dedicated cron topic: create one and set `TELEGRAM_CRON_THREAD_ID=<thread_id>` (or
`TELEGRAM_HOME_CHANNEL_THREAD_ID`). Note this in the report — the user will hit it next.
