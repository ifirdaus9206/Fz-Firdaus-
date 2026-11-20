---
name: hermes-gateway-session-routing
description: Diagnose split/duplicate chat sessions in Hermes gateway.
category: devops
---

# Hermes gateway session routing — fragmentation, duplication, phantom resume

Class of complaint: *"kenapa dia masuk mesej baru padahal topik sembang belum habis"* — the bot
answers as if the conversation just started, an extra unprompted message appears, or the same
chat shows a pile of separate sessions. The model is fine; the **session key** is wrong, or the
gateway died and replayed a turn.

## Fast triage (do this before touching code)

```bash
cd <hermes home>
grep -oE "agent:main:[a-z]+:[a-z]+:[0-9]+(:[0-9]+)?" logs/gateway.log | sort -u | tail -8
grep -nE "UNCLEAN|SIGKILL|resume|auto-resume|inbound message" logs/gateway.log | tail -20
python -c "import json;d=json.load(open('sessions/sessions.json'));print(len(d));print([k for k in d if k.count(':')>4][:6])"
```

Read the answer like this:

| Evidence | Meaning |
|---|---|
| Many keys with a trailing `:<number>` for one chat | Per-message/per-topic differentiation leaked into the session key — fragmentation |
| `exited UNCLEANLY (no exit path ran — SIGKILL / OOM)` | Android/host killed the process; runsv restarted it |
| `Scheduled auto-resume for N restart-interrupted session(s)` right after | The "extra message" the user sees is a replayed turn |
| Every `origin.thread_id` differs while `chat_type` is `dm` | Telegram sent `message_thread_id` + `is_topic_message` for a plain DM |

Confirm with the *current* session itself: if your own context starts cold with the user's latest
message and holds no earlier turns, the session key changed between messages.

## Where session keys are built

- `gateway/session.py → build_session_key()` — the DM branch appends `source.thread_id` whenever
  it is non-empty; the group/forum branch treats it as a thread lane. A thread id on a DM
  therefore means "new session per thread".
- `plugins/platforms/telegram/adapter.py → _source_from_message_for_auth()` — where the Telegram
  `thread_id` is decided:

  ```python
  elif chat_type == "dm" and is_topic_message:
      thread_id = str(thread_id_raw)          # ← fires for plain DMs too
  ```

  `getChat` on such a DM returns **no** `has_topics_enabled`/`is_forum`, so the chat is not really
  topic-enabled. Gate it on the bot's own topic config instead:

  ```python
  elif chat_type == "dm" and is_topic_message:
      if str(getattr(chat, "id", "")) in getattr(self, "_dm_topic_chat_ids", set()):
          thread_id = str(thread_id_raw)
  ```

  `_dm_topic_chat_ids` is precomputed in `__init__` from `config.extra["dm_topics"]`, so a bot
  that genuinely manages DM topics keeps its lanes and every other DM collapses to one session.
- `agent.gateway_auto_continue_freshness` (default **3600 s**) is the freshness window for
  replaying an interrupted turn. `agent.auto_continue.enabled` is honoured by the **TUI only** —
  it does not stop gateway auto-resume. Don't promise a config toggle that does not exist; remove
  the cause (the crash) instead.

## Patch safely — three rules

1. **Patch the tree the launcher actually runs.** Find it, don't assume:
   `ls -l $PREFIX/bin/hermes` → e.g. `.../tools/hermes-source/hermes-agent/hermes`. A repo often
   carries an identical second copy (`tools/hermes-source/plugins/...` vs
   `tools/hermes-source/hermes-agent/plugins/...`); `md5sum` both and patch **both**, so a later
   update or re-install cannot resurrect the bug.
2. **Prove the fix with a real run, not a diff.** Use the live venv python and fake message
   objects (`scripts/probe_dm_thread_id.py`). Assert all three branches: plain DM → `None`,
   configured DM topic → the id, forum group → the id.
3. **Say plainly that the patch needs a gateway restart** and schedule it after the current reply
   (console API `POST /api/svc/hermes-gateway`, or a one-shot cron — see
   `termux-runit-services`). Never restart mid-turn: the gateway dies before delivering.

## DM topics in a private chat — mode OFF is worse than no topics at all

User's words: *"dalam topik mesej aku saja"* — inside a Telegram DM topic they see only their own
messages, while the bot's replies appear in the root / "All Messages" view; or work from an earlier
topic bleeds into the current task and comes out wrong.

Why: Telegram sends `message_thread_id` + `is_topic_message` for DM topics, but Hermes honours them
only when it **manages** topics for that chat (`config.extra.dm_topics`, or user-driven `/topic`
mode). With mode off, `_dm_topic_chat_ids` is empty → `thread_id` is dropped, so **every topic
collapses into one session** and outbound replies carry no thread id, landing outside the topic.
From inside, the agent believes it is continuing a single conversation — that is how unrelated
tasks get mixed and the delivered work is wrong.

Three checks that settle it (never print the token):

```bash
# 1. bot capability
curl -s "https://api.telegram.org/bot$TOKEN/getMe" \
  | jq '.result|{username,has_topics_enabled,allows_users_to_create_topics}'
# 2. is topic mode actually on?
python - <<'EOF'
import sqlite3, os
c = sqlite3.connect(f"file:{os.path.expanduser('~/.hermes20/state.db')}?mode=ro", uri=True)
for t in ("telegram_dm_topic_mode", "telegram_dm_topic_bindings"):
    try: print(t, c.execute(f"select * from {t}").fetchall())
    except Exception as e: print(t, "TIADA:", e)
EOF
# 3. are thread ids arriving, and used?
grep -oE "chat=[0-9]+ thread=[0-9]+" logs/gateway.log | tail -5
```

`has_topics_enabled: True` + **tables absent** = user has topics, Hermes is not in topic mode → the
collapse above. `chat_type=dm` rows carrying a `thread` id in `gateway.log` are the second tell.

Remedy is a **user action, not a code patch**: send `/topic` once in the **root** DM. Hermes checks
the BotFather Threads Settings flags (`has_topics_enabled`, `allows_users_to_create_topics`), creates
a pinned System topic, and from then on each topic is an independent session
(`agent:main:telegram:dm:<chat>:<thread>`) with replies delivered inside that topic. `/topic off`
returns to one continuous session. After enabling, the root DM is a lobby: plain prompts are
rejected there, so say so explicitly or the user thinks the bot broke.

Working rule for this user: **finish one topic before starting the next.** Do not switch topic or
task mid-way because a new topic/message arrived; a new topic is new work only after the user says
the previous one is done. Ask which topic a reply belongs to when it is ambiguous.

## Pitfalls

- **`/tmp` is not writable on Termux.** Write probe scripts to `$HOME/…`;
  `/tmp/x.py` fails with `can't open file … No such file or directory`.
- **`git status --short | head -20` hides new files.** A truncated listing once made a staged
  script look unmodified; re-check with `git diff --cached --name-only`.
- **A silent `git status -sb` (`## main`)** does not prove a push landed — compare
  `git ls-remote origin main` with `git rev-parse HEAD`.
- **Grepping for a guessed config name wastes the session.** `auto_resume` does not exist; grep
  the exact log string (`"Scheduled auto-resume for"`) and follow it to the function instead.
- **Don't edit Hermes core for a per-user symptom** before checking `config.extra`: DM topics,
  group/thread isolation and reply modes are all config-driven.
- **A split conversation never shows up as an unhealthy service.** `sv status`, `/api/agency/health`
  and the gateway log all look fine while the user sees "my messages and yours in different
  places". When the complaint is about *where* replies appear, check thread routing first — do not
  start with restarts, keeper scripts or model quality.
- **"Messages were partial / I got half" is a routing symptom, not truncation.** Two topics folded
  into one session make the agent answer the wrong thread with the wrong context. Confirm by
  comparing the topic ids in `gateway.log` against the session key before touching token limits.

## References
- `references/telegram-dm-thread-fragmentation.md` — worked case with measured numbers, the exact
  diff, test output and the evidence table used in the report.
- `references/telegram-dm-topics-mode.md` — "inside the topic I only see my own messages": `/topic`
  mode off vs on, `has_topics_enabled` + missing `telegram_dm_topic_*` tables as proof, the
  user-driven remedy and the post-activation verification.
- `scripts/probe_dm_thread_id.py` — run with the live venv python to prove which branch a
  Telegram message source takes; exits non-zero on regression.
