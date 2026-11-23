---
name: hermes-gateway-session-routing
description: Diagnose gateway session splits, silent bot, canned replies.
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

## "Terputus" / bot mati sekejap — proses dibunuh, bukan routing

Symptom words: *"kenapa jadi macam terputus"*, *"buat semakan dulu terputus atau sedang bekerja agen"*.
Split the claim into three read-only questions **before** touching anything:

```bash
curl -s 127.0.0.1:8787/api/agency/health                 # 1) any agent actually running?
curl -s 127.0.0.1:8787/api/health \
  | jq '.homes[0].gateway|{gateway_state,pid_alive,platforms,updated_at}'   # 2) alive now?
grep -nE "UNCLEAN|SIGKILL|Starting Hermes Gateway|Connected to Telegram" logs/gateway.log | tail -25
grep -c "Starting Hermes Gateway" logs/gateway.log
grep -c "All connection attempts failed" logs/gateway.log
sv status hermes-gateway hermes-console; uptime; free -m | head -3
```

Reading the evidence:

| Evidence | Meaning |
|---|---|
| `runs.aktif` > 0 but the entries are old `planned`/`cancelled` | No agent is running — say "0 aktif" plainly; do not imply work in progress |
| `gateway.platforms.telegram.state=connected` but `updated_at` only minutes old | The gateway just restarted — the cut the user saw is real, not a routing artefact |
| `exited UNCLEANLY … SIGKILL / OOM` + `last_heartbeat_at` | Android killed the process. `suspected_oom=False` does **not** mean no kill — only that the log could not prove OOM |
| gap last_heartbeat → next `Starting Hermes Gateway` = **10–30 s** | runsv restarted a killed child; Telegram reconnects; only messages sent inside that window are lost |
| gap of **tens of minutes to hours** | the whole Termux tree died (Android killed Termux); runsv cannot restart it until Termux is reopened — this is the long "terputus" |

Causes measured on this phone: RAM/swap exhaustion (`mem_available` ~3 GB while swap has 7+ GB used,
load average ~20) plus hundreds of `All connection attempts failed` escalating to
`Fatal telegram adapter error (telegram_network_error)`.

Prove direction separately, never by assumption:
- outbound: `hermes send -t telegram "…"` → `Sent to telegram home channel` proves token + network **out** only;
- inbound: `grep -n "inbound message" logs/gateway.log | tail -5`. **No** inbound line after the restart
  timestamp means the message was sent while the process was dead, or never reached the gateway.

Report in this user's shape: plain-Malay evidence board — numbered lines, exact log quotes with
timestamps, an explicit "Agen: 0 aktif" line, a one-line conclusion, then a numbered 3–4 option list
(he answers by number). No prose paragraphs, and no fix installed without his approval.

Check the console in the same pass: `sv status hermes-console` is usually restarted by the same kill,
and `hermes-console/app.py → _size_worker()` runs `du -sk` over the entire ~17 GB home every 300 s —
measurable CPU/IO on a phone, and a prime suspect whenever load average is high.

See `references/gateway-killed-by-android.md` for the worked numbers (two kills in one night, 36
restarts, 610 connect errors) and the exact log lines to quote.

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

## Silent bot: canned reply, zero agent turns (topic mode ON, user typing in the root DM)

Symptom words: *"mesej tak boleh dah ikut arahan pun tak balas"* / "bot tak balas langsung".
The service is healthy, Telegram is connected, and `gateway.log` shows `Sending response (N chars)`
— so a naive check says "it replied". Look at **N**: the same N repeating for every message is a
canned template, not the agent. The agent never ran, so nothing is wrong with the model or the session.

Fast proof (no restart, no token):

```bash
grep -n "Sending response" logs/gateway.log | tail -10   # identical char counts = template
grep -rn "reserved for system commands" tools/hermes-source/hermes-agent | head -3
```

| observed N | template | meaning |
|---|---|---|
| 267 | "This main chat is reserved for system commands…" (`_telegram_topic_root_lobby_message`) | root DM prompt, topic mode ON |
| 304 | "To start a new parallel Hermes chat…" (`_telegram_topic_root_new_message`) | `/new` typed in the root DM |
| 1644 | topic-mode activation intro | `/topic` was just enabled |

Confirm with read-only state, then fix:

```python
import sqlite3, os
c = sqlite3.connect(f"file:{os.path.expanduser('~/.hermes20/state.db')}?mode=ro", uri=True)
c.row_factory = sqlite3.Row
for r in c.execute("select chat_id,thread_id,content,created_at from delivery_obligations order by created_at desc limit 5"):
    print(r["thread_id"], len(r["content"]), r["content"][:80])          # 1) the canned text
print(c.execute("select id,thread_id,last_activity_at from sessions where source='telegram' "
                "order by last_activity_at desc limit 3").fetchall())     # 2) no new row = agent never ran
print(c.execute("select * from telegram_dm_topic_mode").fetchall())        # 3) enabled=1?
```

Fix — the user sends `/topic off` in the root DM (clean path, also clears bindings), or toggle the
flag directly. `is_telegram_topic_mode_enabled()` re-reads the DB on every message, so an `UPDATE`
takes effect **without restarting the gateway**:

```python
import sqlite3, os, time
c = sqlite3.connect(os.path.expanduser('~/.hermes20/state.db'), timeout=15)
c.execute("update telegram_dm_topic_mode set enabled=0, updated_at=? where chat_id=?", (time.time(), CHAT))
c.execute("delete from telegram_dm_topic_bindings where chat_id=?", (CHAT,))
c.commit()
```

Then have the user send one test message and judge the **new** log lines: a real turn shows a
`Flushing text batch agent:main:telegram:…` line, a variable-length response, and a fresh telegram
row in `sessions`. Only that proves the fix — a restart alone proves nothing.

## "Kerja tak habis, dia lupa arahan lama" — busy_input_mode=interrupt

Symptom words: *"tak habis satu-satu mesej, dia buat yang lain"*, *"tiba-tiba mesej kerja masuk,
yang sebelum ini dia dah lupa"*. Nothing is broken in routing: the gateway delivers every message,
and the newest one **cancels** the turn in flight. Default `display.busy_input_mode` is
`interrupt`, so a message typed while the agent is working kills the current turn and starts a new
one from the new text — the earlier instruction is never completed and its context is lost.

```bash
hermes config get display.busy_input_mode          # interrupt → the cause
hermes config set display.busy_input_mode queue    # new messages wait; current turn finishes first
```

`queue` is the right default for this user: work finishes one item at a time and follow-ups arrive
in order. `steer` folds the new text into the running turn — do not choose it for someone who
complains about interleaved or forgotten work.

**This one needs a restart** — unlike the topic-mode DB flag. Config.yaml is read at gateway start:

```bash
sv restart hermes-gateway && sleep 15 && sv status hermes-gateway
grep -n "Connected to Telegram" logs/gateway.log | tail -2
```

Same for `.env` changes (`TELEGRAM_CRON_THREAD_ID`): restart, then verify. Always state which
changes are live-immediately (DB flags) and which need a restart (config.yaml, .env) — mixing them
up makes the user think a fix failed when it simply was not loaded yet.

## "Dah hantar, tak balas" — prove inbound and outbound separately

When the user insists they sent a message and got nothing, do not argue from the template table
alone. Split the claim into two independent tests:

1. **Outbound alive?** `hermes send -t telegram "..."` → `Sent to telegram home channel`. If that
   works, the token, allowlist and network are fine.
2. **Inbound arriving?** `grep -n "inbound message" logs/gateway.log | tail -5`. No line after the
   user's timestamp means the message never reached the gateway — the agent cannot be blamed.

```bash
# read-only peek at the update queue (never print the token)
curl -s "https://api.telegram.org/bot$TOKEN/getUpdates?offset=-1&limit=3" \
  | jq '.ok, (.result|length)'
```

Read it carefully: an empty result while the gateway is long-polling is **inconclusive** — the
poller normally drains the queue first. It only proves something when the gateway is stopped. A
`409 Conflict` means a second poller is running. Neither result is evidence that a reply was
delivered; only the `inbound message` → `response ready` → `Sending response` triple is.

If the user is typing inside a DM topic while topic mode is OFF, say so plainly and ask them to
send in the **root** chat for the test — an unmanaged topic lane is the first thing to rule out,
not the model.

## Don't promise an auto-topic router — it does not exist

When the user asks for *"mesej 1 masuk topik 1, mesej 2 masuk topik 2, dia auto letak di mana
sesuai"*: Hermes has **no content classifier** that reads a message and files it into a topic.
Topic mode gives one topic = one independent session; the *human* picks the topic. Say that plainly
instead of inventing a router, then offer the closest real scheme — a small fixed set of topics
(e.g. KERJA / KRON / UMUM) where each topic keeps its own context and the user sends to the right
one. A dedicated cron topic plus `TELEGRAM_CRON_THREAD_ID=<thread_id>` keeps automated reports out
of the work conversation.

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
- **`httpx.ReadError` + "Primary api.telegram.org connection failed … sticky fallback IP" is normal
  noise in this gateway.** It reconnects within seconds and does not stop replies. Do not report it
  as the cause of a silent bot — check the response char counts first.
- **"It replied" is not proof.** Match the logged char count against a template string in the source
  (`grep -rn "<first words>" tools/hermes-source/hermes-agent`). A 267-char reply to a 37-char prompt
  is the lobby notice, not an answer.
- **"Messages were partial / I got half" is a routing symptom, not truncation.** Two topics folded
  into one session make the agent answer the wrong thread with the wrong context. Confirm by
  comparing the topic ids in `gateway.log` against the session key before touching token limits.

## References
- `references/telegram-dm-thread-fragmentation.md` — worked case with measured numbers, the exact
  diff, test output and the evidence table used in the report.
- `references/telegram-dm-topics-mode.md` — "inside the topic I only see my own messages": `/topic`
  mode off vs on, `has_topics_enabled` + missing `telegram_dm_topic_*` tables as proof, the
  user-driven remedy and the post-activation verification.
- `references/telegram-lobby-silent-bot.md` — worked case "bot tak balas langsung": identical 267-char
  replies as the tell, the 267/304/223/1644 template fingerprints, `delivery_obligations` + `sessions`
  evidence, the live `enabled=0` fix (no restart needed) and the cron-thread side effect.
- `scripts/probe_dm_thread_id.py` — run with the live venv python to prove which branch a
  Telegram message source takes; exits non-zero on regression.
- `references/telegram-busy-input-interrupt.md` — worked case "tak habis satu-satu mesej": the
  interrupt-vs-queue diagnosis, the evidence lines, the restart sequence and the honest answer
  about auto-topic routing.
- `references/gateway-killed-by-android.md` — worked case "kenapa jadi macam terputus": SIGKILL
  lifecycles, the 24 s vs 73 min downtime comparison, RAM/swap/load numbers, the `du -sk` console
  worker, direction-proof commands, and the evidence-board report shape.
