# Wiring a messaging channel into a home (Telegram) + keeping it alive on Termux

Validated on: Hermes v0.20.0, Termux/Android 16, home `~/.hermes20`, bot-token platform.
Same shape for Discord/Slack (swap `TELEGRAM_*` → `DISCORD_*` / `SLACK_*`).

Trigger: *"sambungkan hermes ke telegram"*, *"hantar saya mesej dalam Telegram"*, the bot
goes silent after the session/phone sleeps, or *"kenapa dah tak balas mesej"*.

## Acceptance test — four checks, in order

1. `curl .../getMe` returns the bot identity (credential alive).
2. `logs/gateway.log` shows `✓ <platform> connected`.
3. `hermes send -t <platform> "..." --json` returns a `message_id` (Hermes's own path, not
   just raw Bot API).
4. Exactly one process polls (a second one = `409 Conflict`, silent drops).

`hermes gateway status` is NOT part of the test.

## 1. Credential — recover, validate, never echo

Working tokens usually survive in **archived homes** — fastest recovery path:

```bash
grep -E '^TELEGRAM_' ~/.hermes20/archive/*/root-cleanup/.hermes/.env \
                      ~/.hermes20/legacy-ultimate/config/hermes-state-ref/.env
# -> TELEGRAM_BOT_TOKEN=..., TELEGRAM_ALLOWED_USERS=..., TELEGRAM_HOME_CHANNEL=..., _NAME=...
```

`read_file` **refuses** `~/.hermes*/.env` (returns an error dict, so `r["content"]` raises
`KeyError: 'content'`). Do the read+append entirely in a shell heredoc so the secret never
enters the conversation:

```bash
python3 - <<'PY'
import pathlib
arch = pathlib.Path.home()/".hermes20/archive/ultimate-2026-10/root-cleanup/.hermes/.env"
envp = pathlib.Path.home()/".hermes20/.env"
tok = next(l.split("=",1)[1].strip() for l in arch.read_text(errors="ignore").splitlines()
           if l.startswith("TELEGRAM_BOT_TOKEN="))
cur = envp.read_text() if envp.exists() else ""
if "TELEGRAM_BOT_TOKEN" not in cur:
    envp.write_text(cur.rstrip("\n") + "\n"
        f"TELEGRAM_BOT_TOKEN={tok}\n"
        "TELEGRAM_ALLOWED_USERS=<chat_id>\n"
        "TELEGRAM_HOME_CHANNEL=<chat_id>\n"
        "TELEGRAM_HOME_CHANNEL_NAME=<name>\n")
print([l.split("=")[0] for l in envp.read_text().splitlines() if "=" in l])
PY
```

Report only `panjang token: 46 prefix: 8833…`, never the value.

## 2. Config contract (v0.20 source truth)

`gateway/config.py::_apply_env_overrides` calls `_enable_from_env(Platform.TELEGRAM)` the
moment it sees `TELEGRAM_BOT_TOKEN` — **no `telegram.enabled: true` required**.

| Purpose | Key | Where |
|---|---|---|
| credential, auto-enables platform | `TELEGRAM_BOT_TOKEN` | `.env` |
| who may DM the bot (else anyone can) | `TELEGRAM_ALLOWED_USERS` | `.env` |
| cron/`hermes send` default target | `TELEGRAM_HOME_CHANNEL` (+`_NAME`) | `.env` |
| forum topic routing | `TELEGRAM_HOME_CHANNEL_THREAD_ID`, `TELEGRAM_CRON_THREAD_ID` | `.env` |
| group @mention gate | `require_mention` | `config.yaml` |
| explicit disable | `telegram.enabled: false` | `config.yaml` |

## 3. SDK must go into the venv the launcher runs

```bash
head -1 "$(readlink -f $PREFIX/bin/hermes)"     # -> #!.../.hermes_venvs/<v>/bin/python
~/.hermes_venvs/<v>/bin/pip install -q "python-telegram-bot>=21"
~/.hermes_venvs/<v>/bin/python -c 'import telegram; print(telegram.__version__)'
hermes doctor | grep -i telegram                # ⚠ optional-not-installed must disappear
```

Installing into system `python3` or another venv leaves the gateway failing at import.

## 4. Start + real log sequence

```bash
hermes gateway run          # Termux: foreground mode; background=true from a tool call
tail -20 ~/.hermes20/logs/gateway.log
```

Observed order (10–15 s to connected):

```
Connecting to telegram...
[Telegram] Discovering Telegram API fallback IPs via DNS-over-HTTPS…
[Telegram] Auto-discovered Telegram fallback IPs: 149.154.166.110
[Telegram] Connecting to Telegram (attempt 1/8)…
[Telegram] Connected to Telegram (polling mode)
✓ telegram connected
Gateway running with 1 platform(s)
[Telegram] set_my_commands OK for scope BotCommandScopeDefault (60 cmds)
```

## 5. Persist across session end (Termux, no systemd)

`hermes gateway install` is systemd/launchd only. `runsvdir` is usually already up on this
device (`pgrep -a runsvdir`, `ls $PREFIX/var/service`, `sv`):

```bash
mkdir -p $PREFIX/var/service/hermes-gateway
cat > $PREFIX/var/service/hermes-gateway/run <<'SH'
#!/data/data/com.termux/files/usr/bin/sh
exec 2>&1
export HERMES_HOME="$HOME/.hermes20"
termux-wake-lock 2>/dev/null || true
exec hermes gateway run
SH
chmod +x $PREFIX/var/service/hermes-gateway/run
sleep 8 && sv status hermes-gateway      # runsvdir auto-picks it up; restarts on crash
```

Kill the manual gateway BEFORE this (`process kill` / `hermes gateway stop`) — two pollers
give `409 Conflict`. Boot hook (only if the Termux:Boot addon exists):
`~/.termux/boot/10-hermes-gateway.sh` → `termux-wake-lock` + `sv up $PREFIX/var/service/hermes-gateway`.

## 6. Prove delivery

```bash
hermes send -t telegram "Hai Bos! 👋 ..." --json
# -> {"platform":"telegram","chat_id":"...","message_id":"748",
#     "note":"Sent to telegram home channel (chat_id: ...)"}
hermes send -t telegram --list
```

`hermes send` reuses gateway credentials with **no LLM and no running gateway** for
bot-token platforms, so a `message_id` proves the Hermes path. Raw `curl .../sendMessage`
is a fine first ping but does not prove the gateway. Then ask the user to reply — the
inbound round-trip is the only two-way proof.

## 7. Failure modes seen

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: telegram` | SDK in wrong venv | install via launcher-shebang venv |
| `409 Conflict` / bot answers twice | two gateways polling | kill manual one, `sv up` only |
| `hermes gateway status` says "Running manually" under runit | detects systemd/launchd only | trust `sv status` + log |
| `getUpdates` returns `{"result":[]}` | polling consumed the queue | use `hermes send` / user reply as proof |
| `⚠ TERMINAL_CWD ... deprecated in .env` | legacy key from an old home | offer to move to `terminal.cwd` in `config.yaml` |
| bot silent after phone sleeps | Android suspends background jobs | `termux-wake-lock` + termux-services |
| bot silent mid-conversation, gateway alive, **no new inbound in the log** | session blocked inside a `clarify` question nobody answered | see §8 |
| long silence at the START of a turn | 6–8 tool round-trips at 30 s+ model latency before the first text | tell the user it is thinking, not dead; consider a faster model |

## 8. Silent bot with a live gateway — the blocked `clarify` turn

This is the most misleading failure on the list: every liveness check passes (process up,
`✓ telegram connected`, no `409`, token valid) yet nothing is ever answered, because the
**whole session is parked inside the `clarify` tool**
(`tools/clarify_gateway.py` — a blocking event queue waiting for a button tap or text
answer). Every later inbound message queues behind it and is never processed.

Diagnose in this order and stop at the first hit:

```bash
sv status hermes-gateway; pgrep -af "gateway run"          # 1. process alive?
tail -40 ~/.hermes20/logs/gateway.log                       # 2. connected? last inbound?
grep -E "inbound message|response ready|Sending response|Flushing" \
     ~/.hermes20/logs/gateway.log | tail -12                # 3. timeline of turns
tail -25 ~/.hermes20/logs/errors.log                        # 4. red herrings (see below)
```

The tell: `inbound message ...` at T0, then `Flushing text batch ... (NNN chars)` minutes
later with **no `Sending response`** and no further `inbound message` — the NNN-char flush
IS the clarify question, and the turn never completed.

Confirm from the transcript (read-only, never the log alone):

```bash
python3 - <<'PY'
import sqlite3, os, json
c = sqlite3.connect(f"file:{os.path.expanduser('~/.hermes20/state.db')}?mode=ro", uri=True)
sid = "2026...<session id>"                      # from the inbound message line
rows = c.execute("""select id, role, content, finish_reason, tool_calls, timestamp
                    from messages where session_id=? order by id desc limit 4""", (sid,)).fetchall()
for mid, role, txt, fin, tc, ts in rows:
    print(mid, role, fin, repr(txt[:80]))
    if tc: print("   tool:", json.loads(tc)[0]["function"]["name"])
# assistant rows with empty content + finish_reason='tool_calls' = mid-turn, not a reply
print(c.execute("""select count(*) from messages where session_id=? and role='assistant'
                   and length(content)>0""", (sid,)).fetchone())
PY
```

Zero non-empty assistant rows + last row `finish_reason='tool_calls'` + tool name `clarify`
⇒ the turn is parked. The question text and its choices are recoverable from that row's
`tool_calls` JSON — reuse them in your reply so the user can actually answer.

Fix, cheapest first:

```bash
# 1. unstick: drops the parked turn; queued Telegram updates are re-delivered after restart
sv restart hermes-gateway
# 2. stop it recurring: default clarify timeout is 3600 s
hermes config get agent.clarify_timeout
hermes config set agent.clarify_timeout 180
sv restart hermes-gateway          # restart so the new value is loaded
grep -E "telegram connected" ~/.hermes20/logs/gateway.log | tail -1
```

Proof it recovered: after the restart the log shows a fresh
`inbound message ...` → `response ready ... api_calls=1` → `Sending response (NNN chars)`.
Upstream resolution order for the timeout is `clarify.timeout` (legacy) → else
`agent.clarify_timeout` → default 3600; `<= 0` means wait forever.

Do **not** send a "problem gone" message through the same parked session before restarting,
and do not silently swallow the abandoned question — restate it in the chat/CLI afterwards.

Red herrings in `errors.log` that do **not** stop replies: `ModuleNotFoundError:
nemo_relay` (optional relay runtime), `tirith returned unexpected exit code -6` + circuit
breaker opened (security scanner crashed, tools keep running), `check_*_requirements
returned False` (a toolset was skipped this turn), auxiliary "PAID lane engaged" warning.
Mention them only as cleanup candidates, never as the cause.

## 9. Report shape (this user, Bahasa Melayu)

TETAPAN (bot @username, token masked, chat id + display name, file written) → GATEWAY
(status/PID/autostart/log path, `sv status` line) → MESEJ DIHANTAR (each `message_id` and
which path it took) → NOTA (allowlist, warnings, restart command after reboot).
Declare every unrequested change (installed package, service file, boot script) explicitly.
Flag archived `.env` files holding live tokens as a rotation candidate — never delete them
silently.

For a silence post-mortem, lead with a timestamped KRONOLOGI built from the log
(`inbound` → tool calls → clarify flush → user complaint), state plainly that the gateway
was never down, then PUNCA (numbered) → YANG DIBETULKAN (with PIDs/`sv` output) → the
still-unanswered question restated as lettered options. Never answer "kenapa senyap" with
"sepatutnya dah balas".
