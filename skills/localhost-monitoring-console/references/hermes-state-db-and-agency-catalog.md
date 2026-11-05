# Hermes state.db and the agency roster on disk

Verified against Hermes Agent v0.20.0 homes (`~/.hermes20`, `~/.hermes19`), 2026-11.

## 1. Files worth reading (per home)

| Path | What |
|---|---|
| `<home>/state.db` | sessions, messages, tokens, cost, tool calls (WAL) |
| `<home>/kanban.db` | tasks, task_runs, task_events, task_comments |
| `<home>/cron/executions.db` | cron run history (`claimed/running/completed/failed`) |
| `<home>/cron/ticker_heartbeat` | unix ts text; age = scheduler alive |
| `<home>/gateway_state.json` | pid, gateway_state, per-platform state (telegram/…) |
| `<home>/processes.json` | background process registry (`[]` when idle) |
| `<home>/logs/{gateway,errors,agent}.log` | log tails |
| `<home>/config.yaml` | model default (regex `^\s+default:` under `model:`) |
| `<home>/skills/`, `<home>/system/*.md`, `SOUL.md` | organisation/prompt surface |

## 2. sessions / messages

```sql
-- sessions: id, source, chat_id, chat_type, display_name, model, parent_session_id,
--   started_at REAL, ended_at, end_reason, message_count, tool_call_count,
--   input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, reasoning_tokens,
--   estimated_cost_usd, actual_cost_usd, title, last_activity_at,
--   last_activity_description, archived, pinned
-- messages: id INTEGER PK, session_id, role (user|assistant|tool), content, tool_name,
--   tool_calls JSON, timestamp REAL, token_count, active, compacted, display_kind
```

Overview totals (28 sessions / 1,744 messages / 822 tool calls / $0.86 on `.hermes20`):

```sql
SELECT COUNT(*) sessions, COALESCE(SUM(message_count),0) messages,
       COALESCE(SUM(tool_call_count),0) tools,
       COALESCE(SUM(input_tokens),0) tin, COALESCE(SUM(output_tokens),0) tout,
       COALESCE(SUM(estimated_cost_usd),0) cost
FROM sessions;
```

14-day series (local dates, fill gaps in Python — SQL only returns days with rows):

```sql
SELECT date(started_at,'unixepoch','localtime') d, COUNT(*) s,
       COALESCE(SUM(tool_call_count),0) t, COALESCE(SUM(input_tokens+output_tokens),0) tok
FROM sessions WHERE started_at >= ? GROUP BY d ORDER BY d;
```

Session timeline for a detail pane: `WHERE session_id=? AND active=1 ORDER BY id ASC LIMIT 400`
(active=1 excludes compacted rows).

### tool_calls shapes (the one that bites)

```json
[{"type":"function","function":{"name":"terminal","arguments":"{\"command\":\"ls\"}"}}]
[{"type":"function","function":{"name":"tool_call",
  "arguments":"{\"name\":\"agency_agents_load\",\"arguments\":{\"slug\":\"frontend-developer\"}}"}}]
```

Always: `name = fn.name`; `args = json.loads(fn.arguments or "{}")`; then **if `name == "tool_call"`
unwrap once more** (`args["name"]`, `args["arguments"]`). Filter by prefix (`agency_agents`,
`mcp_*`) *after* unwrapping. Tool results appear as separate rows with `role='tool'`,
`tool_name` set, and a JSON string body.

## 3. Agency roster (`~/<home>/agency-agents` + router plugin)

| Path | Content |
|---|---|
| `plugins/agency-agents-router/data/agents.json` | **282** entries, ~8 MB, each with `slug, name, description, division, color, emoji, vibe, source_path, body` |
| `agency-agents/divisions.json` | 18 divisions → `{label, icon, color}` |
| `agency-agents/<division>/*.md` | source agents; 267 carry frontmatter, 325 `.md` total incl. docs |
| `agency-agents/.git` | real clone (e.g. `4e3ac3c`, branch `main`) — not a brew cask install |
| `agency-agents-app/src-tauri/resources/corpus-baseline/` | the app's copy: **282** `.md`, paths **flat** (`game-development/unity-architect.md`) |
| `logs/agency-catalog-drift.txt` | last catalogue-vs-corpus comparison — **a snapshot, not live truth** |
| `<other home>/plugins/.../agents.json` | filtered subset (e.g. 21 trading agents in `.hermes19`) |

### Drift: never show a stale snapshot as if it were live

`logs/agency-catalog-drift.txt` is written by `~/.hermes20/scripts/sync_agency_catalog.py`, so it
only describes the moment someone last ran that script. A dashboard that regexes numbers out of it
will happily display `badan berbeza (60)` weeks after the catalogue was already synced — measured:
the file was dated 22 Oct, current truth was 0/0/0, and the console kept warning the user about 60
mismatched agent bodies. Fix the class, not the number:

- compute drift **live** in the endpoint (282 files is ~100 ms) and cache on
  `(agents.json mtime, corpus-dir mtime, len(roster))`;
- show the report file only as metadata with its **age** (`age_h`), labelled "rujukan sahaja";
- return a `"live": true` flag so the UI can say which mode produced the numbers.

**Compare by `(division, slug)`, never by raw `source_path`.** The two corpora disagree on layout:
the app copy is flat (`game-development/unity-architect.md`), the git repo nests
(`game-development/unity/unity-architect.md`). Path-keyed comparison manufactures 15 phantom
"only in app" + 15 "only in active" entries and hides real body drift behind them. Report layout
differences separately as `beza susun atur` (harmless) and repairable path mismatches as
`path hilang cakera`.

Repair mode worth shipping in the sync script (`--fix-paths`): build a `(division, slug) -> relpath`
index by walking the real corpus, rewrite `source_path`, copy `agents.json.bak-<date>` first.
Measured result: 15 paths fixed, then `hanya dalam app 0 | hanya dalam aktif 0 | badan berbeza 0 |
beza susun atur 15 | path hilang cakera 0`.

### Making "no real delegation yet" true or false from evidence

Usage counting comes from `state.db` tool_calls, so it is **live and self-updating**: one genuine
`agency_agents_delegate` call flipped `delegate 0 -> 1` and `unused 278 -> 277` in `/api/agency`
within the same session. When the panel says "belum ada delegasi", either (a) render the measured
count instead of prose, and (b) if the user wants it cleared, actually delegate a small real task
through the router — never hand-edit the counter. Also state the ceiling: work done by pasting a
persona prompt by hand is invisible to this counter.

Usage counting (read-only, from `state.db`):

```sql
SELECT session_id, tool_name, tool_calls, timestamp FROM messages
WHERE tool_calls LIKE '%agency_agents%' OR tool_name LIKE 'agency%' ORDER BY timestamp;
```
Then unwrap as above; count per `(tool, slug)`. Observed: search 5, inspect 2, load 1,
delegate 0 over 4 distinct agents out of 282 — i.e. ~1.4 % of the roster ever used. Report
"dipakai / belum dipakai" as measured, and derive recommendations from it rather than prose.

## 4. Division → role mapping used in the console

Written by Ketua so the roster is *actionable* inside the 8-system org model:

| Division | Role in the orchestration model |
|---|---|
| academic | concept/reference feed into `agent_factory` |
| design | visual spec before build (workflow design phase) |
| engineering | technical execution, consumes DAG from `workflow_generator` |
| finance / paid-media | cost and spend control |
| game-development / gis / spatial-computing / healthcare | domain specialists (extra compliance) |
| marketing / sales / support | outward-facing output |
| product | scope/PRD before task split |
| project-management | WBS + schedule, pairs with `orchestrator` |
| research | source recon + citations |
| security | mandatory gate before `completion_system` |
| specialized | cross-audit / orchestrator agents |
| testing | evidence for `qa_system` (default NEEDS_WORK until proven) |

Also cross-reference each division with the installed `skills/` names to flag divisions that can
only produce advice (no local skill to execute).

## 5. Sanity anchors (from a real run)

- `.hermes20`: 28 sessions, 1,744 messages, 822 tool calls, 6.48 M in / 0.53 M out tokens, $0.8644,
  `state.db` ≈ 12 MB, home ≈ 16.3 GB (`du -s`).
- `.hermes19`: 4 sessions, 21 messages, home ≈ 104 MB, ATC `decisions.log.jsonl` 25 lines,
  `paper_trading_log.csv` 2 data rows, doctrine 7 rules, symbols XAUUSD/XAGUSD/EURUSD/GBPUSD/WTI
  with leverage 100/100/50/50/20.
- Agency: 282 agents / 18 divisions / 21 in `.hermes19` / git `4e3ac3c`.
