# Telegram DM topics — measured forensics (2026-11-20)

Device: Xiaomi 25080RABDG · HyperOS 3 · Android 16 · Play-signed Termux · no root, ADB pairing blocked.
Bot: `@ainafz_bot` · chat `1312929583` (the user's DM).

## 1. Bot capability (`getMe`)

```
ok: True
username: ainafz_bot
has_topics_enabled: True
allows_users_to_create_topics: True
medan lain: supports_guest_queries, can_connect_to_business, has_main_web_app,
            has_topics_enabled, allows_users_to_create_topics, can_manage_bots,
            supports_join_request_queries
```

Both flags true ⇒ BotFather side is ready; topics can exist in the DM **before** Hermes manages them.
Do not read this as "topic mode is on".

## 2. State tables (`~/.hermes20/state.db`)

Before any `/topic`: both tables **absent**.

```
telegram_dm_topic_mode ERR no such table: telegram_dm_topic_mode
telegram_dm_topic_bindings ERR no such table: telegram_dm_topic_bindings
```

After the user sent `/topic`, the tables existed with one row:

```
telegram_dm_topic_mode
  {'chat_id': '1312929583', 'user_id': '1312929583', 'enabled': 0,
   'activated_at': 1795087581.47, 'updated_at': 1795141392.22,
   'has_topics_enabled': 1, 'allows_users_to_create_topics': None,
   'capability_checked_at': 1795088695.82,
   'intro_message_id': None, 'pinned_message_id': None}

telegram_dm_topic_bindings (schema)
  ['chat_id','thread_id','user_id','session_key','session_id','managed_mode',
   'linked_at','updated_at']            # 0 rows at that moment
```

Lessons: a row with **`enabled: 0`** means the mode is *off* (it can be toggled by `/topic off`),
and `0 rows` in bindings right after enabling is normal — a binding is written the first time a
message arrives **inside** a topic. Always print the row, never assume from table existence.

## 3. Gateway log signature

```
INFO gateway.run: Watch pattern notification — injecting for telegram chat=1312929583 thread=24285
INFO gateway.run: Watch pattern notification — injecting for telegram chat=1312929583 thread=26054
INFO gateway.run: Watch pattern notification — injecting for telegram chat=1312929583 thread=23939
```

Thread ids are present on inbound messages, while the user still saw "my messages only, yours
elsewhere" — proof that the id is received and then dropped (mode off), not that Telegram failed to
send it.

## 4. Adapter rule that causes the split

`plugins/platforms/telegram/adapter.py`, DM branch:

```python
elif chat_type == "dm" and is_topic_message:
    # DM topic HANYA dihormati jika bot memang menguruskan topik untuk chat ini
    # (extra.dm_topics). Tanpa konfigurasi itu, setiap message_thread_id dari
    # Telegram menghasilkan SESI BAHARU bagi setiap mesej -> konteks sembang hilang
    if str(chat.id) in self._dm_topic_chat_ids:
        thread_id = str(thread_id_raw)
```

With topic mode off and no `extra.dm_topics` entry, `thread_id` stays `None`: every topic joins one
session (`agent:main:telegram:dm:{chat_id}`) and the reply is sent without a thread id, so it appears
in the root DM. That single branch explains both halves of the complaint.

## 5. Session keys

- no thread: `agent:main:telegram:dm:1312929583`
- inside a managed topic: `agent:main:telegram:dm:1312929583:{thread_id}`
- cron delivery targets: `origin` (chat/topic the job was created from), `telegram` (home channel),
  `local`, or explicit `platform:chat_id:thread_id`.

## 6. Queries used

```bash
sqlite3 -readonly ~/.hermes20/state.db ".tables" | tr ' ' '\n' | grep -i topic
sqlite3 -readonly ~/.hermes20/state.db "select * from telegram_dm_topic_mode;"
sqlite3 -readonly ~/.hermes20/state.db "pragma table_info(telegram_dm_topic_bindings);"
```

Opening with `sqlite3.connect("file:...?mode=ro", uri=True)` also works and is safer than a shell
heredoc when the caller only needs to read.

## 7. Reporting shape that worked

1. Symptom in the user's words ("mesej aku saja dalam topik").
2. One evidence table (capability / table presence / `enabled` value / log line).
3. One sentence of mechanism, no jargon.
4. The single command that fixes it (`/topic`), plus the fallback (`/topic off`).
5. Acknowledge the earlier damage plainly ("that is why the work came out wrong") and state the
   going-forward rule: one topic finished before the next.
