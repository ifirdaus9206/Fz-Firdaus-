---
name: hermes-chat-session-routing
description: Diagnose and fix chat session/topic routing (Telegram).
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, termux]
metadata:
  hermes:
    tags: [telegram, gateway, sessions, topics, threads, delivery, routing]
    related_skills: [localhost-monitoring-console, agent-team-operations]
---

# Hermes chat session routing (topics, threads, delivery targets)

Answers "why are my messages and your replies in different places?", "why did you change topic
mid-task?", "why did the cron message land in another chat?" — for Telegram first, same model for
other thread-capable platforms.

## Use when

- "mesej aku saja dalam topik ni, mesej kau tak ada", "kau tukar topik lain", "konteks tak cukup",
  "mesej separuh-separuh".
- `/new`, `/topic`, DM topics, forum topics, `message_thread_id`, `thread=`, session-per-topic.
- Cron output that appears in the wrong chat/topic (`deliver: origin|telegram|local|platform:chat:thread`).
- Deciding whether one long task should live in one session or be split.

## Mental model — three layers, one key

| Layer | What it decides | Where to look |
|---|---|---|
| Platform adapter | Does this message carry a `thread_id`? | `plugins/platforms/telegram/adapter.py` (`_effective_message_thread_id`) |
| Gateway session key | Which conversation it joins | `agent:main:telegram:dm:{chat_id}:{thread_id}` (no thread ⇒ `agent:main:telegram:dm:{chat_id}`) |
| Outbound send | Whether the reply carries the same `thread_id` | send path; logging line `Watch pattern notification — injecting for telegram chat=… thread=…` |

A reply is only "in the topic" when **both** inbound and outbound carry the thread id. When the
adapter drops the id, every topic collapses into one session **and** replies land in the root DM —
i.e. exactly the "I see only my own messages, and you mixed my topics" complaint.

## Diagnostic ladder (stop at the first true answer)

```bash
# 1. What the bot itself reports (needs the token from .env)
curl -s "https://api.telegram.org/bot$TOKEN/getMe" \
  | python3 -c "import sys,json;r=json.load(sys.stdin)['result'];print(r.get('has_topics_enabled'),r.get('allows_users_to_create_topics'))"

# 2. Is multi-session topic mode ON?  (tables absent = never enabled in this home)
python3 - <<'EOF'
import sqlite3, os
c=sqlite3.connect(f"file:{os.path.expanduser('~/.hermes20/state.db')}?mode=ro", uri=True)
t=[r[0] for r in c.execute("select name from sqlite_master where type='table' and name like '%dm_topic%'")]
print("tables:", t)
for n in t:
    for r in c.execute(f"select * from {n}"): print(n, r)
EOF

# 3. What the gateway saw
grep -E 'thread=|topic' ~/.hermes20/logs/gateway.log | tail -8
```

Reading it:

- `getMe` both `True` ⇒ the chat *may* use topics, but Hermes is not managing them yet.
- table missing ⇒ `/topic` was never enabled; `enabled: 0` ⇒ it was enabled then turned off.
- log shows `thread=24285` while the user still sees split messages ⇒ the adapter is receiving an id
  that is being dropped downstream (or the reply path is not echoing it).

## Enable / disable (user-driven, one command)

Prerequisites are in **@BotFather → Bot Settings → Threads Settings**: *Threaded Mode* ON and users
allowed to create topics. Then, from the **root DM**:

```
/topic          # enable multi-session mode, pin a System topic, list restorable sessions
/topic off      # disable, clear all bindings for this chat
/topic help     # inline usage
```

After enabling, the **root DM becomes a lobby** (plain prompts are rejected; system commands still
work) and each topic is an independent session: own history, own model state, own tool runs.
`/new` (or the **+** button) opens the next topic. Auto-rename makes the Telegram topic title follow
the Hermes session title (best-effort).

## Symptom → cause

| Symptom | Cause | Fix |
|---|---|---|
| Only the user's messages visible inside a topic | replies sent without `thread_id` (adapter dropped it) | enable `/topic`; verify a binding row appears after the next topic message |
| Topics mixed, "you did the wrong task" | all topics collapsed into one session ⇒ context interleaved | same fix; then keep one task per topic |
| "Context not enough / messages half" | earlier turns live in another session (or were compressed) | say which session the work is in; summarise before switching |
| Cron message in the wrong place | job `deliver` target | set `deliver: origin` for the origin chat, `telegram` for the home channel, `platform:chat_id:thread_id` for a specific topic |
| Topic list exists but Hermes never binds | `/topic` never run in *that* chat | run it from the root DM of that chat |

## Working rules for this user (learned from correction)

- **One topic at a time.** Finish the current topic, report, and only then let them `/new`. Switching
  topics to "get on with other work" is what produced *"kau buat tiba tukar topik lain … kerja itu
  salah"*.
- Because topics are separate sessions, **context does not leak between them**. When resuming, state
  which topic/session holds the work instead of pretending to remember.
- When they ask "kenapa mesej aku saja", lead with the mechanism and one line of evidence, then the
  single command that fixes it (`/topic`). Do not open with a settings tour.

## Pitfalls

- **Do not diagnose from the chat layout.** Telegram can show topics in a DM before Hermes manages
  them; the DB row (`enabled`) and the log (`thread=`) are the evidence.
- **`has_topics_enabled: True` is not "topic mode is on".** It only means BotFather allows topics.
- **Absent tables ≠ broken DB.** They are created on first `/topic`; missing rows mean "feature never
  used in this home", not corruption.
- **A topic binding appears only after a message inside that topic.** Zero bindings right after
  `/topic` is normal.
- **Never move a cron job's `deliver` to `origin` to "fix" routing** without checking which chat the
  job was created from; `origin` follows the creating chat/topic, `telegram` follows the home channel.
- **Compression is not a routing bug.** Long sessions lose middle turns to summarisation; if the user
  says "separuh-separuh", check session length before blaming the adapter.

## Support files

- `references/telegram-dm-topics-forensics.md` — measured state on this device (table schema, row
  values, log lines, session-key forms) and the exact queries used to prove each step.
