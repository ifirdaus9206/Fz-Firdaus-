# Worked case — "tak habis satu-satu mesej, dia lupa arahan lama"

Complaint (20/11/2026, DM 1312929583): *"kadang-kadang tak habis satu-satu mesej dia buat yang
lain… tiba-tiba mesej kerja masuk, yang sebelum ini dia dah lupa."* Plus: *"dah hantar tak balas."*

Two separate faults were stacked. Both had to be named before the user could see progress.

## Fault 1 — interrupt cancels the turn in flight

`display.busy_input_mode` was `interrupt` (the default). Every message typed while the agent was
working cancelled the running turn and started fresh from the new text. The agent never "forgot" in
the model sense — its previous turn was killed mid-way and never resumed.

Fix, live only after restart:

```bash
hermes config set display.busy_input_mode queue
hermes config get display.busy_input_mode        # → queue
sv restart hermes-gateway                        # config.yaml is read at start
```

Choice of value: `queue` for this user (finish one item, then the next). `interrupt` = current
behaviour. `steer` = fold new text into the running turn — wrong for someone who wants items
finished one at a time.

## Fault 2 — topic-mode lobby ate the messages

`telegram_dm_topic_mode.enabled = 1` since 19/11 19:26. Root-DM prompts got the 267-char lobby
template and the agent never ran. Fixed with a direct `UPDATE ... set enabled=0` (effective without
restart because `is_telegram_topic_mode_enabled()` re-reads the DB per message).

After that, one real message at 10:29:16 got a genuine 614-char reply at 10:29:24 — proof the agent
worked once topic mode was off.

## Fault 3 — "dah hantar tak balas" was unproven, not observed

No `inbound message` line appeared after 10:29:24 up to the restart at 10:47:56. So the claimed
later message never reached the gateway. Evidence split:

| Test | Command | Result |
|---|---|---|
| Outbound | `hermes send -t telegram "..."` | `Sent to telegram home channel` → token/allowlist/net OK |
| Inbound | `grep -n "inbound message" logs/gateway.log \| tail -5` | last line 10:29:16, nothing after |
| Queue peek | `getUpdates?offset=-1&limit=3` | `ok True`, 0 results → inconclusive while the poller runs |

Lesson: report "no inbound logged" as a fact and ask for one test message; do not accept "it
replied" or "it didn't reply" from either side without the log triple
(`inbound message` → `response ready` → `Sending response`).

## Cron reports in the wrong place

With topic mode on, cron deliveries to the root chat land in the system-only lobby. Created topic
`KRON` (thread 26409) via `createForumTopic`, then:

```bash
echo 'TELEGRAM_CRON_THREAD_ID=26409' >> ~/.hermes20/.env
```

`TELEGRAM_CRON_THREAD_ID` overrides `TELEGRAM_HOME_CHANNEL_THREAD_ID` for cron deliveries only, and
needs a gateway restart to load. Replies in that topic continue its own session.

## The answer the user actually needed about topics

Asked for *"mesej 1 topik 1, mesej 2 topik 2, dia auto letak di mana sesuai"*. Hermes has no
content classifier that routes a message into a topic. Said so plainly, then offered a fixed
3-topic scheme (KERJA / KRON / UMUM) where the user picks the topic. Do not build or promise a
router for this; the honest limit is the deliverable.

## Order of operations that worked

1. Restart only after the config change, never mid-turn.
2. Prove outbound, then prove inbound, then judge.
3. State which fixes are live-now (DB flag) vs restart-needed (config.yaml, .env).
4. End with numbered options and one concrete test the user can run in 30 seconds.
