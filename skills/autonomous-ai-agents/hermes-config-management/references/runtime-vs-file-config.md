# File vs runtime config — why "I set it but nothing changed"

`hermes config set` writes and validates the **file**. It says nothing about a process that
is already running. Gateways, the cron scheduler, cron workers, the desktop app and the
TUI load their config at startup, so a change lands on disk and keeps having zero effect
until the reader is restarted.

```bash
hermes config set agent.clarify_timeout 180
hermes config get agent.clarify_timeout            # file: 180
sv status hermes-gateway; sv restart hermes-gateway  # process: still 3600 until this
grep -E "telegram connected" $HERMES_HOME/logs/gateway.log | tail -1
```

The tell for "I set it but nothing changed" is exactly this split: `config get` shows the
new value, behaviour is unchanged. Restart, then re-verify **behaviour from a log line** —
never re-issue the `config set` (a second identical set proves nothing and hides the real
cause).

Keys that live in a long-running process and therefore need a restart: `model.default` /
`fallback_providers` (gateway keeps its client), `display.*`, `gateway.*`,
`plugins.enabled`, `agent.*` limits, `auxiliary.*`.

## Case study — `agent.clarify_timeout` and the bot that "stopped replying"

`clarify` blocks the current turn until the user answers or the timeout fires. In the
gateway that means the whole **session** is parked: later inbound messages queue and are
never processed, while every liveness check still passes (process up, `✓ telegram
connected`, no `409`, token valid).

Resolution order (source: `tools/clarify_gateway.py::resolve_clarify_timeout`):

1. legacy top-level `clarify.timeout`, if explicitly set
2. else `agent.clarify_timeout`
3. else default **3600 s**; `<= 0` means wait forever

```bash
hermes config set agent.clarify_timeout 180   # 3 min, then the turn unblocks by itself
```

Verify the *runtime* took it by reproducing the silence once and watching the log: the
turn should now end with a timeout instead of hanging for an hour.

### Recognising a parked clarify from data, not from the log alone

```bash
python3 - <<'PY'
import sqlite3, os, json
c = sqlite3.connect(f"file:{os.path.expanduser('~/.hermes20/state.db')}?mode=ro", uri=True)
sid = "<session id from the 'inbound message' log line>"
for mid, role, txt, fin, tc in c.execute(
        """select id, role, content, finish_reason, tool_calls from messages
           where session_id=? order by id desc limit 4""", (sid,)):
    print(mid, role, fin, repr(txt[:80]))
    if tc: print("   tool:", json.loads(tc)[0]["function"]["name"])
print("non-empty assistant rows:",
      c.execute("""select count(*) from messages where session_id=? and role='assistant'
                   and length(content)>0""", (sid,)).fetchone()[0])
PY
```

Signature: **0** non-empty assistant rows, last row `finish_reason='tool_calls'`, tool name
`clarify`. The question and its choices are recoverable from that row's `tool_calls` JSON —
restate them to the user after unsticking, don't silently drop the abandoned question.

Recovery: `sv restart hermes-gateway` (or `hermes gateway restart`). Queued platform
updates are usually re-delivered after the restart; confirm with a fresh
`inbound message ...` → `Sending response` pair in the log.

Related: `hermes-home-provisioning` skill,
`references/gateway-telegram-channel.md` §7–§8 (silence post-mortem + red-herring log lines
that do NOT stop replies: `nemo_relay`, `tirith` exit `-6`, `check_*_requirements`).
