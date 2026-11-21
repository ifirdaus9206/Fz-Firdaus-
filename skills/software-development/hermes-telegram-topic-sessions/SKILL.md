---
name: hermes-telegram-topic-sessions
description: Use when Telegram replies land outside the user's topic.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, termux, windows]
metadata:
  hermes:
    tags: [telegram, gateway, topics, threads, sessions, routing, diagnosis]
    related_skills: [hermes-config-management, localhost-monitoring-console, agent-team-operations]
---

# Hermes Telegram DM topic sessions

Telegram private chats can carry **topics** (threads). Hermes has two ways to make each topic its own
session, and **if neither is active the thread id is silently dropped** — which produces a very
specific, easy-to-misread bug report.

## When to use

Any of these user phrasings:

- *"dalam topik ini mesej aku saja, mesej kau tak sekali"* — they see only their own messages in a topic.
- *"kau tukar topik lain, kerja itu jadi salah"* — work came out wrong and context looked half-missing.
- *"mesej yang kau dapat tak cukup / separuh-separuh"* — replies arrive in a different place than the question.
- *"aku nak macam ChatGPT, satu topik satu perbualan"* — they want parallel sessions.
- You are about to answer "why are our messages split?" and the chat is a Telegram DM.

## What is actually happening

| State | Inbound `message_thread_id` | Result |
|---|---|---|
| Neither mode active | dropped by the adapter | **all topics share one session**; replies are sent with no thread id, so the client shows them in the root/All-Messages view — the topic looks one-sided |
| `extra.dm_topics` (config, operator-curated) | kept for the listed chat ids only | fixed topic names, each its own session |
| `/topic` multi-session (user-driven) | kept once `telegram_dm_topic_mode.enabled = 1` | user creates topics freely; root DM becomes a **lobby** |

Isolation key when active: `agent:main:telegram:dm:{chat_id}:{thread_id}`. Consequence that matters:
**each topic has its own history**, so work started in topic A is invisible from topic B. That is the
mechanical reason a task "became wrong" after the conversation moved to a new topic — not a model
failure.

## Diagnose in three checks (no guessing)

1. **Bot capability** (never print the token):
   ```bash
   TOKEN=$(grep -oP '(?<=^TELEGRAM_BOT_TOKEN=).*' ~/.hermesNN/.env | tr -d '"'"'"' ')
   curl -s "https://api.telegram.org/bot$TOKEN/getMe" | python3 -c "
   import sys,json; r=json.load(sys.stdin)['result']
   print({k: r.get(k) for k in ('username','has_topics_enabled','allows_users_to_create_topics')})"
   ```
   Both flags must be true. They come from **@BotFather → Bot Settings → Threads Settings →
   Threaded Mode ON**, plus "allow users to create topics" not disabled. If false, no amount of
   configuration on the Hermes side helps.

2. **Mode state** in the home's state DB (read-only):
   ```python
   sqlite3.connect("file:…/.hermesNN/state.db?mode=ro", uri=True)
   # tables missing → feature never activated
   select * from telegram_dm_topic_mode;        -- look at `enabled` (0 = OFF)
   select * from telegram_dm_topic_bindings;    -- one row per bound topic
   ```
   `enabled: 0` with a row present means it was turned on and later off (`/topic off`), not "never
   used".

3. **Gateway log** shows what arrived: `grep -iE 'thread|topic' logs/gateway.log | tail`.
   Inbound messages can carry `thread=24285` while the mode is off — proof the client is using topics
   and Hermes is discarding the id, rather than "Telegram didn't send it".

## Fix

- **Enable:** the owner sends `/topic` **in the root DM** (authorized users only). Hermes checks
  `getMe`, creates/pins a System topic, and lists unlinked sessions that can be restored with
  `/topic <session-id>`. Re-run the DB check: `enabled = 1`; a binding row appears after the first
  message inside a topic.
- **Disable:** `/topic off` in the root DM — clears bindings, single continuous session again.
- **Operator-curated alternative:** `platforms.telegram.extra.dm_topics` in config.yaml, with fixed
  names and optional `ignore_root_dm: true` (root becomes a lobby). Use when the owner wants
  permanent workspaces, not ad-hoc topics.
- **Restoring an old conversation** into a topic: `/topic <session-id>` from inside that topic.

The agent **cannot** enable this itself — `/topic` must come from the owner's account. Say that
plainly instead of pretending to flip a switch; what you can do is verify and report the DB state.

## Working agreement once topics are on

Embed this in behaviour, not just in the reply:

1. **One topic = one task.** Finish it, report, then let the owner open the next topic. Never start
   unrelated work mid-topic because a cron message or a new idea arrived.
2. Before switching, post a **3–5 line state summary** (what was done, what is pending, next step) —
   the next topic starts with zero context and that summary is the only bridge.
3. If the owner asks something unrelated inside a running topic, say so and ask whether to park it.
4. Never assume the other topic's instructions exist here; ask for the missing detail instead of
   inventing it.

## Pitfalls

- **Do not diagnose this as "the bot is broken" or "Telegram is dropping messages."** The pipe is
  fine; the thread id is being dropped by design until a mode is active.
- **Replies without a thread id look like a dead topic.** The user's screen is the evidence: their
  messages in the topic, yours in the root. Confirm with the DB check, not with a screenshot request.
- **`enabled: 0` is not proof it was never configured.** Check `activated_at` / `updated_at`; a
  `/topic off` leaves the row behind.
- **Turning mode on changes root behaviour**: the root DM becomes a lobby and normal prompts are
  rejected there. Warn the owner *before* they run `/topic`, or the "error" looks like a regression.
- **Bot API version matters.** Threaded mode predates topics support in some bot versions; if
  `has_topics_enabled` is false after enabling in BotFather, the bot build is too old — nothing on
  the Hermes side fixes that.
- **Do not write topic state into config.yaml by hand.** Mode + bindings are SQLite-managed; editing
  config only affects `extra.dm_topics`. Use `hermes config set` if you must, never a text patch of
  the YAML file.

## Report shape that worked

Short table of the three checks (flags / `enabled` / bindings count), one paragraph explaining the
mechanical consequence, the single command the owner must send, then numbered options. The owner
replies with a digit.
