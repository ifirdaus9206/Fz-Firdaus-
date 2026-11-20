# Telegram DM topics: mode off, replies land outside the topic (worked case, 19 Nov 2026)

## Complaint, verbatim
> "kenapa dalam Telegram ini di satu-satu topik mesej aku saje ... aku tekan /new baru kau tukar
> topik mesej lain ... semalam tak abis lagi topik dan kau buat tiba tukar topik lain ... jadi kerja
> itu salah. mesej yang kau dapat tak cukup dan separuh-separuh"

Two symptoms in one report: (a) inside a topic only the user's messages are visible, (b) work from
one topic was applied to another task and came out wrong.

## Evidence collected

| Check | Result | Meaning |
|---|---|---|
| `getMe` on the bot | `username: ainafz_bot`, `has_topics_enabled: True`, `allows_users_to_create_topics: True` | Telegram side is ready; DM topics exist |
| `state.db` tables `telegram_dm_topic_mode`, `telegram_dm_topic_bindings` | **both absent** ("no such table") | Hermes never entered topic mode for this chat |
| `gateway.log` (`chat=… thread=…`) | rows like `chat=1312929583 thread=26054`, `thread=23939` | thread ids arrive, and were being ignored |
| Adapter branch | `elif chat_type == "dm" and is_topic_message:` → gated on `_dm_topic_chat_ids` (empty here) | `thread_id` set to `None` |
| Session key | `agent:main:telegram:dm:<chat>` (no trailing thread id) | all topics shared **one** session |

Consequence chain:
1. every topic's messages enter the same session → the agent answers the current task with another
   topic's context (that is the "kerja itu salah" and "separuh-separuh" complaint);
2. replies are sent without `message_thread_id` → Telegram places them in the root chat
   ("All Messages"), so inside the topic the user sees only their own messages.

## Where it is implemented / documented
- `plugins/platforms/telegram/adapter.py` — `_source_from_message_for_auth()`, ~line 1022-1046:
  the DM-topic branch plus the comment block explaining that without `extra.dm_topics` every
  `message_thread_id` used to create a new session per message.
- `gateway/run.py` — `_is_telegram_dm_topic_target()`, `telegram_dm_topic_reply_fallback`
  metadata, `_create_dm_topic` / `rename_dm_topic` (the `/topic` machinery).
- `hermes_state.py` — `telegram_dm_topic_mode`, `telegram_dm_topic_bindings` tables.
- Docs: `website/docs/user-guide/messaging/telegram.md` §"Multi-session DM mode (`/topic`)",
  incl. the BotFather prerequisite table and the "isolation key" line.

## Remedy (user-driven, no code change)
1. Prereqs: @BotFather → Bot Settings → **Threads Settings** → Threaded Mode **ON**, users allowed
   to create topics (verify with `getMe`; both flags were already ON here).
2. User sends **`/topic`** once in the root DM → Hermes creates a pinned **System** topic; root DM
   becomes a lobby that rejects plain prompts.
3. Each topic is now `agent:main:telegram:dm:<chat>:<thread>`: own history, own model state, replies
   delivered inside the topic. `/new` or the **+** button starts the next topic.
4. `/topic off` reverts to one continuous session and clears bindings.

## Verification after the user runs `/topic`
```bash
# tables now exist and have rows
python - <<'EOF'
import sqlite3, os
c = sqlite3.connect(f"file:{os.path.expanduser('~/.hermes20/state.db')}?mode=ro", uri=True)
print(c.execute("select * from telegram_dm_topic_mode").fetchall())
print(c.execute("select * from telegram_dm_topic_bindings").fetchall())
EOF
# new inbound line carries a thread, and the reply is sent into it
grep -E "inbound message|Flushing text batch" logs/gateway.log | tail -6
```
Do not claim it worked until a bindings row exists **and** a fresh reply appears inside the topic
(the user is the only one who can confirm the visual result — ask them).

## Interaction rule extracted for this user
- Finish the current topic before opening another; never re-task mid-topic.
- When a message could belong to either of two topics, ask which one before acting.
- Repeat the decision rule in plain Malay ("satu topik dihabiskan dulu, baru /new").
