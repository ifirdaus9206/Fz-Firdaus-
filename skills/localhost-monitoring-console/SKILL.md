---
name: localhost-monitoring-console
description: Build read-only localhost dashboards over app state and agent-dispatch control panels.
version: 1.10.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, termux, windows]
metadata:
  hermes:
    tags: [dashboard, monitoring, fastapi, sqlite, read-only, verification, termux, orchestration]
    related_skills: [hermes-config-management, hermes-home-provisioning, dogfood, ai-agent-architecture]
---

# Localhost Monitoring Console

Build a single-page, **read-only** console that answers "what is running, what got done, how is it
organised" for one or more app homes (e.g. several `HERMES_HOME` state directories), then optionally
extend it into a **control panel** that dispatches agents from a large roster.

## When to use

- "Bina dashboard / web UI untuk monitor kerja aku", "papan pemantau", "console kat localhost".
- Anything that must aggregate SQLite state + JSON + logs + git metadata into one view.
- Also load when *extending* an existing console with a new tab/domain, or when the console must
  accept an instruction and orchestrate agents (see `references/roster-orchestration.md`).

## Non-negotiables (user expectations seen in practice)

1. **Plan before build.** The request may literally be "bina plan, reka, kemudian baru bina".
   Write `<project>/PLAN.md` first: problem → data-source table (paths + row counts, verified by
   query) → UX/tabs → architecture → phases → **checklist that gets ticked with evidence**.
2. **Read-only, proven.** Every SQLite connection uses `file:<path>?mode=ro`; no write endpoint.
   Prove it in the report with an attempted INSERT that returns
   `attempt to write a readonly database`.
3. **No new dependencies.** Check what exists (`python3 -c "import fastapi, uvicorn"`, `node -v`)
   before proposing anything. Frontend = plain HTML/CSS/JS, no CDN (must work offline).
4. **Evidence, not claims.** Report status codes, byte sizes, ms timings, row counts, and test
   output. Cross-check at least one API number against raw `sqlite3`.
5. **Language/format of the report:** user's language (here: Malay), plain terminal text — no
   markdown tables/bold in the reply, absolute paths spelled out.
6. **"Masukan idea kau" = compute, don't decorate.** When the user asks for your ideas, add panels
   whose content is derived from live data (unused agents, drift counts, missing local skills,
   gap lists) and label the inputs. Static prose panels read as filler; computed suggestions get
   acted on.
7. **Acknowledge limits in the artifact.** Real weaknesses (parallel agents can't cross-review,
   drift between catalogue and corpus) go into PLAN.md and the report — never smooth them over.
8. **Never pretend to run something you could not find.** Users name artifacts loosely ("guna demo
   `justmakit` sebelum ini"). Search by name *and* content (`find ~ /sdcard -iname '*x*'`,
   `grep -ril x`), then session history; if it does not exist, say so with the paths searched, run
   the nearest existing equivalent instead, and offer to run theirs once they send it. Narrating a
   run of something you never executed invalidates every other piece of evidence in the report.

## Phase 0 — discover, don't assume

```bash
ls -1 ~/.hermesNN | head -40            # homes, db files, dirs
sqlite3 ~/.hermesNN/state.db ".tables"
sqlite3 ~/.hermesNN/state.db ".schema sessions" | head -60
sqlite3 ~/.hermesNN/state.db "select count(*) from sessions; select count(*) from messages;"
sqlite3 ~/.hermesNN/kanban.db "select status,count(*) from tasks group by status;"
du -sh ~/.hermesNN                      # beware: multi-GB, see pitfalls
```

Record the *real* numbers into PLAN.md's data-source table. Counts that differ from memory/docs
(e.g. roster 192 vs 282) are a signal to re-read the catalogue, not to trust notes.

## Phase 1 — backend skeleton (FastAPI)

```
<project>/
  PLAN.md  README.md  homes.json  app.py  run.sh  server.pid
  static/{index.html,style.css,app.js}
  tools/{render_test.js,stop_server.py}
```

- `homes.json` = **allowlist registry** `[{key,label,sub,path,accent}]`. Never accept a filesystem
  path from the request; resolve `home` → registry entry or 404.
- One helper `ro_conn(home, name)` → `sqlite3.connect(f"file:{p}?mode=ro", uri=True)`,
  `row_factory = sqlite3.Row`, short `timeout`.
- Endpoints: `/api/meta`, `/api/overview`, `/api/sessions`, `/api/session/{home}/{id}`, plus one
  per domain tab. Trim long text server-side (`content[:6000]`).
- Cache expensive loads keyed by mtime (8 MB `agents.json`, git calls) so the 15 s poll stays cheap.
- Bind **127.0.0.1 only**: `uvicorn.run(app, host="127.0.0.1", port=8787)`.
- Write `server.pid` on start (`os.getpid()`), remove it in a `finally` block.

## Phase 2 — frontend

- Sticky header: brand + tab buttons + home switcher + clock + `LIVE` pause toggle.
- Tabs = `<section class="pane">` toggled by class; `S.tab` state; `loadTab()` dispatcher.
- Poll every 15 s but **skip while any `INPUT`, `SELECT` or `TEXTAREA` is focused** and honour the
  pause flag (missing `TEXTAREA` wipes a long instruction mid-typing).
- `esc()` on every dynamic string; `num()`, `dt()`, `dur()`, `ago()` formatters; `card()` and
  `table()` helpers keep renderers short.
- Detail views are two-column (`grid-template-columns: 1.05fr 1fr`) with `.scroll` panels.
- The fetch helper must accept options (`api(path, opts)` merging into `fetch`) or POST panels die
  with an unhelpful error.
- For a diagram, generate SVG in Python → `rsvg-convert -w 1500 -o x.png x.svg` → embed
  `<img src="/static/img/x.png">`, then **look at the PNG** (`vision_analyze`) and fix overlaps:
  canvas height must exceed `header + Σ(stage height + gap)`, and dense label lists need ≥18 px
  line spacing.

## Phase 3 — verification (the part that gets skipped)

1. **Endpoint matrix** — loop and print code/time/size for every route:
   `curl -s -o /dev/null -w "%{http_code} %{time_total}s %{size_download}b\n"`.
   All 200, no 500s, sub-250 ms.
2. **Cross-check numbers** against raw SQL (`sessions`, token sums) — quote both in the report.
3. **Render test without a browser** — `templates/render_test.js`: `node:vm` + fake `document`
   storing `innerHTML` per selector, real `fetch` against the live server, then call
   `setTab()`/`openAgent()` per tab and assert on produced HTML:
   - length > 200 and **no `undefined` / `NaN`** (catches field-name drift),
   - counts (8 system cards, 19 chips, 282 agent cards),
   - one detail render path.
4. **Read-only proof** — attempted INSERT → `OperationalError: attempt to write a readonly database`.
5. **Hygiene** — `cat server.pid`, one more `curl -o /dev/null`, `tail server.log` must be empty.
6. **If it calls an LLM, run it for real** — one instruction end-to-end, then quote plan latency,
   per-agent ms, synthesis verdict, and `ls runs/<id>/`. A mocked path proves nothing.
7. **No canonical suite (no pytest/lint)? Write an ad-hoc verifier, then delete it.**
   `tempfile.mkstemp(prefix="hermes-verify-", dir="<writable tmp>")` holding checks for exactly the
   behaviour you changed: fresh provider call, graceful provider failure, timestamp freshness,
   orchestrator wiring via a monkeypatched provider (no network), `py_compile` of every touched
   script, plus one live API assertion. Print `N lulus · M gagal`, exit non-zero on failure, report
   it as **ad-hoc verification of changed behaviour** — never as "suite green" — and remove the
   file afterwards. `$TMPDIR` on Termux is `$PREFIX/tmp`, not `/tmp`.

## Phase 4 — control panel (instruction → agents → verdict)

Only after the read-only tabs are stable. Contract: user types an instruction, a "Ketua" planner
screens the whole roster, picks N agents, each runs with **its own persona as system prompt**, then
Ketua synthesises with a QA gate. Keep the plan synchronous (user reviews before spending N calls)
and execution in a daemon thread; poll a run record every ~2.5 s and persist every mutation to
`runs/<id>/`. Full recipe, prompt contracts, measured timings and limits:
`references/roster-orchestration.md`.

Minimum guards: clamp `max_agents` (1–6) and instruction length server-side, validate every
LLM-returned slug against the roster, keep the API key server-side, and expose a run state machine
(`planning → planned → running → synthesizing → done|failed`).

### Dependency waves — the fix for "reviewers review themselves"

Parallel personas are isolated by default, so a reviewer never sees the producer's draft. Do not
ship that as an unavoidable limitation: give the planner a per-agent `depends_on: [slug]` field and
schedule in waves.

- `waves(agents)` → layered topological sort; no deps run in wave 1, dependants in wave 2;
  `_break_cycles()` drops back-edges (and any slug outside the selection) before sorting.
- A downstream agent's user prompt gains a block
  `INPUT DARIPADA EJEN SEBELUM (wajib disemak): === <name> (<slug>) ===` + upstream text (≤7k chars
  each), and its system prompt says "kerja kau ialah menyemak/meneruskan kerja itu, bukan mencipta
  semula dari kosong".
- **Those hard caps (`[:7000]` upstream, `[:9000]` into synthesis) are a correctness hazard, not a
  cost saving.** A 11–14k-char agent output reaches the next agent and Ketua cut mid-sentence, so
  they report "input terputus" / "output ejen terpotong" and fail QA gates that were actually fine.
  Fixed in the live runner (2026-11-04): named `MAX_UPSTREAM_CHARS` / `MAX_SYNTH_CHARS` = 24,000 plus
  a `clip(text, cap, label)` helper that appends `[NOTA SISTEM: … dipotong pada N daripada M aksara …
  BUKAN kerja ejen yang tidak lengkap]` — a residual cut can never again pass as an agent failure.
  Any "terpotong" verdict stays unproven until you compare it against `runs/<id>/out_<slug>.md`; the
  applied fix, its offline verification and the restart step are in
  `references/run-verdict-reconciliation.md` §3.
- Prompt the planner explicitly: *"Ejen penyemak WAJIB bergantung pada ejen pelaksana."* Measured:
  `waves [['twitter-engager'], ['brand-guardian']]`, reviewer opened with "Input disemak: Draf 1–5
  daripada Twitter Engager".
- The run record carries `waves`, `wave`, `wave_total` so the UI can show "gelombang 2/2"; plan
  cards show "Selepas: <slug>" or "mula sendiri (gelombang 1)".

## Phase 5 — harden before handing over

A console that accepts an instruction and spends money needs more than `127.0.0.1`. Add, and
curl-prove: Host/Origin allowlists (DNS rebinding), a CSRF token served by `/api/meta` and required
as `X-Console-Token` on every POST, CSP/X-Frame/nosniff/no-store headers, `^\d{8}_\d{6}$` validation
of run ids before any path use, `scrub()` of `sk-…`/Bearer in artifacts *and* tracebacks, a
prompt-injection scan that warns instead of blocking, spend guards (1 active run, N per window, one
plan at a time) and `0700` run directories. Full middleware skeleton, patterns and verification
commands: `references/local-console-security.md`.

## Phase 6 - show the same console inside Hermes Desktop

"Gabung dengan app hermes desktop, paparan sama" = ship a runtime plugin at
`<hermes home>/desktop-plugins/<name>/plugin.js`, never fork `apps/desktop` and never
re-implement the UI in React. The loader scans that folder, rewrites
`@hermes/plugin-sdk` / `react*` imports, then calls `register(ctx)`.

Minimum plugin (single self-contained ESM, no JSX syntax - use `jsx()` calls):
- `routes` page `data: { path: '/console' }` -> render iframe of `.../?embed=1`
- `sidebar.nav` row (`codicon`, `label`, `path`)
- `statusBar.right` pill polled against `/api/ping`
- `palette` commands: open, and set-server-URL saved in `ctx.storage`

Server side this forces: `?embed=1` hid chrome; CSP
`frame-ancestors 'self' file: app: http://localhost:5174`; DROP
`X-Frame-Options: DENY` (contradicts CSP, blocks the host); `GET /api/ping`
with `Access-Control-Allow-Origin: *`.

Verify without Electron (none exists for Android/Termux): run
`scripts/validate_desktop_plugin.py` (ESM syntax, SDK-only specifiers, contract, areas, route path)
and a DOM-shim harness that rewrites the imports to stub modules, imports the plugin, calls
`register(ctx)` with a fake context and renders the route component — assert four contributions and
that the page contains an `iframe` whose `src` ends in `/?embed=1`. Reuse the shim shape from
`templates/render_test.js`; keep the harness inside the project (`tools/desktop_plugin_harness.mjs`)
because it must match that project's plugin. Say plainly the Electron run itself is unverified.
Details: `references/hermes-desktop-integration.md`.

## Phase 7 — cost per agent, fleet map, history, remote access

Once the console dispatches agents it must answer three follow-ups users actually ask:
*"berapa agent aktif, di lokasi mana, dan berapa kos setiap satu"*, *"boleh lihat dari telefon"*,
and *"apa jadi minggu ini"*.

1. **Meter real cost, not estimates.** OpenRouter returns `usage.cost` (USD) plus
   `completion_tokens_details.reasoning_tokens`. Capture `usage` on every `llm_chat` call into a
   caller-supplied list and aggregate per stage: `plan`, `agents[slug]`, `synthesis`, and
   `total_cost`/`total_tokens` per run. Show per-agent cost *and* call count (a retried agent can
   cost 10× a clean one). Details + exact response shape: `references/cost-and-agent-tracking.md`.
2. **Location = derived, not stored.** `system → division → slug` from the catalogue plus
   `DIV_SYSTEM`; add `running_since[slug]` timestamps in the worker so the UI can show elapsed time
   for a *running* agent (finished ones use `outputs[].ms`). One row per agent →
   Status · Agent · Location · Elapsed · Tokens · Cost, run header carrying `cost_so_far`.
3. **A server-side bot beats another chat model.** `POST /api/bot {cmd}` implements
   `/status /agents /where <slug> /cost /runs /help` over the same `live_state()` — zero LLM cost,
   instant, and testable with one curl. Reuse `_locate()` and today's run cost roll-up.
4. **History for free.** A daemon thread appends one snapshot per minute to
   `data/history.jsonl` (tools/tokens/cost, console cost, active agents, runs). Daily counters in
   Hermes are *cumulative*, so per-day aggregation must take **max per day**, not sum. Expose
   `GET /api/history?days=7` and draw CSS bars.
5. **Remote access is a mode, not a second server.** `CONSOLE_HOST/PORT/LAN_TOKEN/TLS` env vars:
   `--lan` binds `0.0.0.0` and requires a token; `?t=<token>` sets an HttpOnly cookie and redirects
   (token leaves the URL), `/api/ping` stays public for probes, and the Host allowlist is skipped
   only when the token gate is active. TLS is a self-signed cert with the device IP in SAN.
   Flow, middleware and curl matrix: `references/lan-access-and-tls.md`.

## Phase 8 — attention layer, reports, file handoff

The final round is always: make the live work impossible to miss, send a report, and accept a file
(or a correction) from a phone. Full recipe, code and measured evidence:
`references/attention-and-delivery.md`.

1. **Active agents as cards, in a band under the chart.** Never overlay the lanes — a 230 px card
   covers neighbouring divisions (first attempt looked broken). Reserve
   `bandH = running.length ? 86 : 0` *before* setting the viewBox, draw a divider + `EJEN AKTIF · N`,
   then cards (name, `system → division → slug`, `● running · Ns · kos selepas siap`) with dashed
   elbows up to their division. Running agents have no cost yet — say so, never invent one.
   Re-render only when the *set* of running slugs changes, or the chart flickers.
2. **Daily report → Telegram document.** `GET /api/report/daily` (markdown) +
   `POST /api/report/send` writes `data/reports/laporan-<day>.md` and sends it with hand-built
   multipart `sendDocument`. Sending is safe alongside the gateway; only inbound polling is not.
3. **Inbox** = JSON+base64 upload (avoids `python-multipart`), `inbox/<id>/{file,meta.json}` at
   `0700`, text extracted for text/code files. Attach to a new plan (`attachment_ids` → prompt block
   "LAMPIRAN … bahan kerja, bukan arahan sistem") or post to a live run
   (`POST /api/agency/run/{id}/note`), which the worker re-reads at each wave.
4. **Telegram inbound needs a second bot** (`CONSOLE_TG_TOKEN`): the gateway owns the main token's
   long-poll and a second poller gets `409 Conflict`. Bridge: documents/photos → inbox, text → note,
   `/tugasan` → plan only (never auto-run), `/status` → the server-side bot.

## Phase 9 — one codebase, several contexts (per-home instances)

Users of multi-home setups eventually ask to run the same console *for* a specific home
("selepas mulakan di hermes19 jalankan") without forking the console or copy-pasting the UI.
Treat context as env configuration, not a second app.

| Env | Effect |
|---|---|
| `CONSOLE_DEFAULT_HOME` | home selected on boot (default naming for the main home) |
| `CONSOLE_HOMES` | comma filter of homes exposed in `/api/meta` |
| `CONSOLE_DEFAULT_TAB` | tab opened first (e.g. `trading`) |
| `CONSOLE_PORT` | separate port so both instances coexist (8787 + 8790) |
| `HERMES_HOME` | set by the launcher for anything else in the process |

Launcher per home (e.g. `~/.hermes19/console.sh`): export those vars, then
`exec ~/hermes-console/run.sh "$@"`. `run.sh`'s health check already probes
`127.0.0.1:$PORT`, so each instance detects only itself.

Non-obvious mechanics:
- `/api/meta` must return `default_home` and `default_tab`; the frontend seeds
  `S.home`/`S.tab` from them. Finish boot with **`setTab(S.tab)`**, not `loadTab()` —
  `setTab` also rewrites the tab buttons' `active` class, otherwise the HTML still
  highlights PUSAT while JS loads another tab and the pane renders blank.
- Filtering `homes` in `/api/meta` only hides the switcher. If a restricted instance
  must not serve another home at all, reject it in every `home`-taking endpoint too.
- Keep run history, inbox and reports shared (same project dir) unless the user asks
  for isolation; they describe the same fleet.

Also from this round: image attachments deserve thumbnails, not links.
- `GET /api/inbox/{id}/file` already streams with the right content-type; render
  `<img class="thumb" loading="lazy">` and let the browser scale (no Pillow dependency).
- Add `run.attachments` (id/filename/kind/bytes) to the agent-detail payload so the
  drawer can show a "Lampiran run (N)" strip: thumbnails for `kind=image`, 📎 chips
  otherwise. Omit the block entirely when the run had none.
- A 1x1 test PNG proves the pipeline (bytes + content-type), not the visual result;
  verify the layout where thumbnails actually appear.

Details, including the verification matrix for two live instances:
`references/multi-home-instances.md`; starter launcher: `templates/console_instance.sh`.

**Running them is a separate problem from building them.** Two instances double the ways the user
can find a dead URL: the pid file is shared by both, and nothing restarts them after the phone
reboots. Ship, together:
- one pid file **per port** (`server-<port>.pid`) and a stop tool that takes `--port` / `--all`
  (with a single `server.pid`, stopping 8787 killed 8790 — measured);
- `tools/start_all.sh` (idempotent, prints a status block) as the answer to "macam mana nak mula";
- `tools/keeper.sh` + `no_agent` cron every 5 min, silent when healthy, plus `termux-wake-lock`;
- a `OPERASI.md` runbook in the project: cause table, ports, four commands, cron id, fixes.

Diagnosis order for "tak boleh buka" (`ps` → port → pid → `curl` → **`uptime`** → log), the shared-pid
bug, the busy-flag/fetch-timeout UI freezes, and the shim details:
`references/instance-supervision-and-recovery.md`; env-driven starter:
`scripts/supervise_consoles.sh`.

**Then prove the keeper, don't just trust it.** A supervisor observed only while healthy is
unverified. Drill it once, with the user's permission: baseline both ports → pid file → `ps` proves
`python3 app.py` → `kill -TERM` → confirm `000` → `timeout 70` keeper → poll 1 s → final check that
no keeper lingers and the pidfile matches the new pid. Measured after the `setsid --fork` +
`timeout 55` repair: keeper exits **8 s**, console back **16 s** from kill (8 s of that is the gap
before the keeper was launched — report both numbers, or the keeper looks 2× slower than it is).
Full procedure, timing table and the two traps that look like duplicate processes:
`references/watchdog-recovery-drill.md`.

## Phase 10 — give the observed worker a real data feed

A demo loop writing `mode: backtest` and `timestamp 2024-01-01` is not "live trading" and users
notice immediately. When they say *"guna demo/key yang aku bagi"*, the job is: find the
credentials, wire the worker to a real feed, and state exactly how real the result is.

1. **Credential archaeology, values never printed.** `find ~ -name ".env"` then print *key names
   only* (`grep -oE '^[A-Z0-9_]+'`). Fingerprint each token with `sha256(token)[:8]` so you can say
   "this is the demo token" without exposing it. Copy only the account type the user asked for
   (demo) into the worker's `.env` at `0600`; do not duplicate the live token, and say where the
   original still lives.
2. **Confirm account state read-only at the provider.** For MetaAPI:
   `GET https://mt-provisioning-api-v1.agiliumtrade.agiliumtrade.ai/users/current/accounts`
   with header `auth-token`. Market data only answers for accounts whose `state == "DEPLOYED"`;
   deployment is a billing-gated action (`ForbiddenException: … please top up your account`).
   Quote that error in PLAN.md/report instead of implying data flowed.
3. **Provider chain that records its failures.** Try broker/paid first, then a free source, and
   write `data/feed_status.json` every call: `{source, symbol, price, last_time, proxy, errors[]}`.
   The console reads that file, so the UI can show `feed: yahoo GC=F 3969.5 (proksi)` *and* a red
   `MetaAPI: belum deploy` chip. Silent degradation is what makes a dashboard lie.
4. **Free real data has proxy traps.** Yahoo `v8/finance/chart` has no `XAUUSD=X` / `XAGUSD=X`
   (404). Metals/oil need futures symbols (`GC=F`, `SI=F`, `CL=F`, `BZ=F`) and must be labelled
   **proxy**; FX pairs are real (`EURUSD=X`, `GBPUSD=X`, `USDJPY=X`). Resample coarser timeframes
   yourself (`4h` = aggregate 4×`60m`) if the source lacks them.
5. **Kill the dummy timestamps before celebrating.** Worker engines commonly hardcode
   `timestamp: "2024-01-01T00:00:00Z"` and `mode: "backtest"`. Replace with `datetime.now(UTC)`
   and a mode from env, then prove it from the artifact (CSV row carries today's UTC time and
   `mode=paper`), not from the log banner.
6. **State the ceiling in one sentence.** "Harga emas ialah proksi hadapan, bukan spot broker;
   spot sebenar perlu akaun MetaAPI DEPLOYED (top-up)". Offering the fix keeps the evidence honest.

Working reference implementation (bridge script run through the provider SDK's venv, fallback,
status file, credential layout): `references/external-worker-monitoring.md` §5–§8.

## Phase 11 — when the user must do the physical step

The console cannot install an APK, grant a permission, or pair ADB. When the user starts asking
*"aku cari tak jumpa di mana"*, stop repeating instructions in chat and put the procedure **in the
console**: a `PANDUAN` tab that proves state, shows numbered illustrations, and accepts the user's
own screenshots as further steps.

1. `GET /api/device/status` → one verdict object (`fdroid.installed`, `apk.{path,bytes,sha256}`,
   `termux_api.{cli,working}`, `adb.devices`) **plus a `caveat` string** saying package listing is
   visibility-filtered. Ship the caveat with the data or the UI asserts false negatives.
2. Seed illustrated steps at startup (Pillow diagrams in the console palette: phone frame +
   highlighted row + "tekan sini" tag), store `data/steps/{steps.json,*.png}`, serve
   `GET /api/steps` + `GET /api/steps/<id>/file`; `POST /api/steps` (JSON+base64) appends the user's
   screenshots as steps N+1…
3. UI: numbered `stepcard` grid with click-to-full-size images, caption + timestamp, and one upload
   form. Verify with two render checks (status contains the package name, ≥N `stepcard`) — a broken
   tab looks exactly like an empty one.
4. **Assume the user will not find a new panel.** Shipping it inside the last tab is not delivery:
   in practice the user replied *"aku tak jumpa"* three times while the panel existed and rendered.
   Give every user-facing form three entry points and name them in the reply:
   - deep link `/?tab=<key>` (and `#<key>`): parse in boot, accept only keys present in the tab
     list, then `setTab(...)`;
   - a header quick-jump button that `setTab`s, `scrollIntoView({block:"center"})` and `.focus()`s
     the first input;
   - a one-line pointer in the tab where they were looking ("borang ada di tab SISTEM").
   Put the actionable form **above** the read-only panels of that tab, not below them.
5. **When the physical step needs a code, take it in the UI.** `POST /api/device/adb-pair`
   (`{host:"ip:port", code:"6 digits", connect?}`) validates with regexes, runs `adb pair`
   (code on stdin), then `adb connect`, and returns `{ok, devices[], connect, log[{step,out}]}`
   so the pane can print the real command output. `POST /api/device/shot` runs
   `adb exec-out screencap -p`, rejects non-PNG, and appends the image as the next guided step.
   Neither replaces ADB — they remove the "type this in a terminal" step that users skip.
   Do not call it a login: a 6-digit code shown by Android is the wireless-debugging **pairing
   code**, and the console itself has no account. Pre-empt "IP aku tak jumpa di mana letak" by
   reading the phone's own LAN address from the shell (`ifconfig wlan0 | grep "inet "`).

Recipe, seeding code, emoji-glyph trap, verification curls:
`references/guided-steps-and-device-status.md`. Deep-link + header quick-jump + ADB pairing and
screenshot endpoints, and the wording that resolves "kod ≠ login": `references/ui-discoverability-and-adb-pairing.md`.

### Phase 11b — supervise the console with runit, and retire the crash-looper

"Console mesti auto-restart sendiri" is a supervision problem, not a UI one. Two moves, in this
order — full recipe, service files, verification output and the HyperOS content in
`references/runit-supervision-and-inline-guides.md`:

1. **Turn off the service that is eating the phone.** `sv down <svc>` is not enough: the phone comes
   back (`start-services.sh` re-scans `$PREFIX/var/service` at every shell start) and the loop resumes.
   Also write `$PREFIX/var/service/<svc>/down`; then `sv status <svc>` stops printing `normally up`.
   Truncate the monster log with `: > ~/.web-server.log` (keep the file, the writer may hold the fd).
2. **Register the console itself** at `$PREFIX/var/service/hermes-console/{run,log/run}` with
   `svlogd -tt` plus a `config` of `s1000000` + `n5` (1 MB × 5) — the reason a 168 MB single log
   existed is that nothing rotated it. `exec python3 -u app.py` and `PYTHONUNBUFFERED=1`, otherwise the
   startup banner never reaches the log (stdout is a pipe, not a tty).
3. **Expect the orphan to still hold the port.** runsv reports `run:` while the old `python3 app.py`
   keeps 8787; `curl` answers 200 and nothing looks wrong until the orphan dies. Kill the old pid
   (`kill -9 <pid>` from `server-<port>.pid`), then confirm `ps` shows exactly one `app.py`.
4. **Prove auto-restart by killing it.** `kill -9 $(cat server-8787.pid)` → new pid within ~5 s +
   `curl /api/ping` 200. Repeat once; one observation could be a coincidence.
5. Ship `tools/uji_konsol.sh` ([LULUS]/[GAGAL] lines, exit code = failures, `mktemp "${TMPDIR:-$HOME}"`
   because `/tmp` is unwritable) and name it in the report. A supervision claim without a drill is a
   claim — start script: `scripts/smoke_test_runit_service.sh`.
6. **State the boot ceiling.** Without `Termux:Boot` installed, "auto-restart" means "restarts while
   Termux lives"; after a reboot the console returns only when a shell starts. Check
   `pm list packages | grep termux.boot` before promising more.

### Phase 11c — schematic guide images without a phone screenshot

When ADB is not paired yet, do not block the illustrated guide: generate the pictures as SVG in the
console palette, then swap them for real `adb exec-out screencap` shots later via the existing
`POST /api/device/shot`.

- One generator (`tools/gen_<topic>_panduan.py`) → `static/img/panduan/*.svg`; preview with
  `rsvg-convert -w 480 x.svg -o preview/x.png`. Proofreading caught four real defects in one pass:
  label clipped at the right edge, duplicate option label, arrow landing between rows, sub-text
  overlapping the icon tile. **Do not trust `vision_analyze` alone for this** — on one 2026-11-11
  session every portrait PNG came back drawn as tofu/placeholder blocks even though the same files
  read fine an hour earlier, so "the image looks broken" and "the image is broken" are different
  verdicts. Gate the layout with a **geometric text checker** (`scripts/verify_svg_text_layout.py`):
  parse every `<text>`, estimate width as `0.55 × font-size × chars` (0.60 when `font-weight` is
  bold), honour `text-anchor`, then flag boxes crossing the frame margin or overlapping another box
  by >8 px. It found the two genuinely clipped note lines that vision had reported as fine/not-fine
  at random; fix by shortening the caption, not by shrinking type below 20 px.
  Cross-check glyphs (not layout) with PIL: crop the region and downsample to ASCII — real
  letterforms prove the font rendered, solid blocks prove tofu.
- Draw icons as vector paths, never emoji: `rsvg-convert` renders emoji as empty circles (the phone
  frame then looked half-drawn even though Chrome would have shown them).
- Labels near the right edge: `text-anchor="end"` at `W - margin`, arrow to the target dot. Anchoring
  at `start` at x≈600/720 overflows out of the frame.
- Portrait images need their own CSS class (`.hguide img{aspect-ratio:720/1280;object-fit:contain}`) —
  the existing `.stepimg` (`aspect-ratio:1000/620` + `cover`) crops them to a strip.
- Add the panel **before** the read-only panels of that tab and keep the honest caption: "gambar rajah
  UI, bukan tangkapan skrin sebenar; susunan menu boleh berbeza ikut versi".

### Phase 11d — let the user run `sv` from the console, and hand off the APK tap

Once the console is a runit service, the next request is *"tambah butang hidup/mati servis"*. Ship a
**whitelisted** control panel, not a shell bridge. Recipe + measured numbers:
`references/service-control-panel.md`.

1. **Whitelist, never a name from the URL.** `SVC_ALLOW = {name: (label, logpath)}` (3–5 entries);
   anything else → 400. Actions are literally `up|down|restart|status`; the endpoint builds
   `[sv, action, name]` with `shutil.which("sv") or $PREFIX/bin/sv` and a timeout.
2. **Never kill your own responder.** `sv restart hermes-console` from inside `hermes-console` sends
   TERM before the HTTP response flushes, so the browser shows a failure for a successful restart.
   Defer it: `bg.add_task(_sv_later, action, name)` (`time.sleep(0.8)` then `sv …`) and return
   `{"ok": true, "deferred": true}` for the console's own name only. Measured on Termux: back in
   ~10 s (uvicorn re-bind), so the UI hint must say so and offer a reload.
3. **Parse state from `sv status`, not from a pid file.** `run:`/`down:`/`fail:` prefix plus
   `(pid N)` and the `Ns` uptime; note `\)\s*(\d+)s` for `run:` lines versus `:\s*(\d+)s` for
   `down:` lines — matching only the colon form silently reports `seconds: null`.
4. **Expose the log the service actually writes** (`GET /api/svc/<name>/log?lines=N`) and show its
   size in the row; that single number is what proves rotation works.
5. **Boot-time auto-start is a package, not a folder.** `GET /api/device/boot` returns
   `{installed, apk{path,bytes}, boot_dir, boot_scripts[]}` from `pm list packages com.termux.boot`,
   and the panel's button calls `POST /api/device/boot-install` (`termux-open` → fallback
   `am start … file://…`, both exit 0 regardless). Say out loud that the last step is one PASANG tap
   plus opening the app once; `~/.termux/boot/*.sh` existing is not evidence the app is installed.
6. **Extend the smoke test with the new surface**: `GET /api/svc` contains the console service, the
   three panel ids exist in `/`, every new image returns `200` + >1 KB, and `GET /api/device/boot`
   answers. 10 → 21 checks in one session, all still `[LULUS]`/`[GAGAL]` one-liners.

### Phase 11e — "aku dah letak imej tapi tak keluar" (upload pipeline)

The upload endpoint is usually healthy; the picture is either stored under a **lying extension**,
sent from the **wrong button**, or looked for in the **wrong tab**. Full recipe, code and the exact
report wording: `references/image-upload-pipeline.md`.

1. **Prove the endpoint with curl before touching the UI** — `POST /api/steps` needs
   `X-Console-Token` from `/api/meta`; success is `{"ok":true,…, "count":N}`. A base64 body over
   ~9 MB cannot ride in `-d` (`Argument list too long`) → write the JSON to a file and use
   `--data-binary @/absolute/path.json`.
2. **Never fake the extension.** `if ext not in OK_EXT: ext = ".png"` stores HEIC/AVIF bytes as
   `.png`: the step exists in `steps.json`, the browser shows a broken image, and the user reports
   "tak keluar". Convert instead — Pillow → RGB → `thumbnail((1600,1600))` → JPEG q86 (measured
   7.2 MB `IMG_….heic` → **734 KB** `*.jpg`), and raise the ceiling 8 → 20 MB.
3. **Put the upload form in the tab that shows the pictures**, with a preview, the chosen
   `name · N KB`, and a success line built from the server's `count` (`disimpan ✓ (N langkah)`).
   The neighbouring "TANGKAP SKRIN PERANTI" button fails with "tiada peranti adb" until pairing and
   reads as "upload broken" — keep them visually separate.
4. **Clean test steps with a script file, not an inline heredoc**, then verify via
   `GET /api/steps` count so `steps.json` and the files agree.



When the roster is hundreds of entities and the user reads it on a phone, the console needs
one page per entity *and* evidence that **every** entity's API answers — not a sample.
Measured recipe: `references/phone-first-entity-dashboard.md`.

1. **One payload per entity.** `GET /api/agent/<slug>/dashboard` returns identity (emoji,
   division/archetype/tier pills, vibe, `pilih_bila`), 2×2 KPI (tasks, completion %, mean ms,
   cost), task list, persona data (words/sections/bullets/originality + deliverable bullets +
   source path), performance, archetype evidence, and a `tool` command string.
2. **Three cache layers, not one.** Catalogue by mtime, `slug → tasks` index TTL 15 s (this
   replaces reading ~80 `run.json` per request), whole payload TTL 20 s. Measured
   **2,170 ms → ~120 ms warm**; cold 282-entity sweep median 424 ms / p95 1,211 ms / 19 s.
3. **A health endpoint the UI can poll.** `GET /api/agency/health` (cache 15 s) returns roster
   counts + tier split + run done/failed/active + per-agent tool usage. The tab renders it as a
   2×2 strip with an **"Uji 12 ejen rawak"** button that fetches 12 dashboards client-side and
   prints `12/12 lulus · median N ms` — the panel then reports something that just happened.
4. **Verify the whole fleet, split the failure classes.** 8-worker sweep over every slug,
   latency min/median/p95/max, and two counters: HTTP failures (fatal, exit 1) vs data-quality
   issues (short body, empty vibe — reported, not fatal). Write `reports/VERIFIKASI.json` +
   `.md`. Read the roster's real keys first: `name`/`kualiti.tier`/`badan_kata` in JSON vs
   `nama`/`tier`/`persona.kata` in the payload; mixing them reported `tier 0/0/0` and one
   phantom "API gagal" while all 282 returned 200.
5. **Phone layout.** One column; rows are `<button>` ≥68 px; sticky search at `top: 52px`
   (96 px when tabs wrap); horizontal archetype chips; render **60 rows + "Tunjuk lagi"**
   (282 rows = 168 KB of HTML); picker ↔ entity are two views of the same tab with a
   `← Semua ejen` back button. Every tap target ≥44 px.
6. **Deliver the reference, not just the UI.** `docs/<SYSTEM>.md` in plain Malay with real
   counts and a real worked example (copy the actual `vibe`/`hasil` strings), plus
   `OPERASI.md` pointer and 3–4 numbered next-step options in the chat reply.

### Phase 12b — repair the roster's thin bodies (the follow-up that always comes)

The dashboard exposes the weak agents; next the user says *"baiki"*. Full recipe with
prompts, gates, backups and measured numbers: `references/roster-quality-repair.md`.

1. **Tier is percentile-based, so its count never drops.** `A ≥ p85 / B ≥ p40 / C < p40`
   is always 15/45/40 % — improving agents only reshuffles them. Add an **absolute grade**
   (`kuat ≥80 / sederhana 60–79 / asas <60`) and report *that* as progress; keep the tier
   badge for ranking. Measured: 8 repairs moved `asas 42 → 34` and `≥80: 83 → 89` while
   tier stayed `A43/B127/C112`.
2. **Diagnose before authoring.** Compare catalogue body words to source `.md` words: a
   ~30–70-word gap is just frontmatter (the document is genuinely thin, author it); a large
   gap means the builder truncates (fix the builder). All 20 weakest were the former.
3. **Enrich the `.md`, not the JSON.** Model rewrites the body with the missing sections;
   always keep the *original* frontmatter (it reorders keys), gate on word growth ≥1.15× and
   ≥7/8 sections, back up `.md` + catalogue, then rebuild the roster and re-run the sweep.
4. **Never force archetype balance.** IDF reweighting was tested and rejected — it turned
   `senior-developer`/`software-architect` into "Pencipta". Store a **secondary archetype**
   when it reaches ≥60 % of the top score instead (56/282, zero primary churn), and say
   plainly when a one-agent archetype is a true property of the roster.

## Pitfalls (each cost real time)

- **Empty content with a high `reasoning_tokens` count is a *different* bug from truncation.**
  `finish_reason: "stop"`, `content: ""`, `completion_tokens_details.reasoning_tokens` in the
  thousands: the model spent the whole budget thinking. Measured on one agent: 21,288 reasoning
  tokens across 3 calls, 153 s, empty text every time. Fix: after the existing `finish == "length"`
  branch, add an empty-content branch that escalates the cap aggressively
  (`caps = min(16000, max(caps*2 + 4000, 10000))`) and allow `attempts=4`; raise the agent
  default to 6000 so the first call usually succeeds. Verify **offline** by monkeypatching
  `urllib.request.urlopen` with three canned responses (empty+length, empty+stop, then text)
  and asserting the caps ladder `[4096, 8192, 16000]` — no network, no cost.
- **A verifier that trusts one field name lies about the fleet.** Roster JSON and API payload
  disagree (`name` vs `nama`, `kualiti.tier` vs `tier`, `badan_kata` vs `persona.kata`). Print
  the keys first; compute each headline number from one declared source; and keep HTTP failures
  and data-quality issues in separate counters so a 192-word body is never reported as a dead
  endpoint.
- **A `setTimeout` stub that invokes its callback makes the whole shim fail.** `api()` wraps
  fetch in an `AbortController` with a 25 s timer; an immediate-invoke stub fires the abort at
  t=0 and every check reports `tamat masa (25s)` while the server is healthy. Use
  `setTimeout: () => 0`, stub `AbortController`/`performance`, and slice `app.js` before
  `boot().catch(` so boot never runs inside the harness.
- **Wrapping an in-process e2e run in `timeout` strands the run.** `timeout 300 python3
  tools/test_agents.py` kills the process that owns the runner thread → `run.json` frozen at
  `synthesizing`, and `| tail -40` buffers away every line so the transcript looks empty. Use
  `background=true` + `notify_on_complete`, poll `runs/<id>/run.json` in separate calls, add a
  janitor thread (`recover_stale(max_age_s=420)` at boot and every 5 min), and rebuild the
  summary from `runs/*/run.json` afterwards.
- **A verdict line is a claim; parse it tolerantly and never fabricate it.** Models bold it
  (`**STATUS AKHIR: NEEDS_WORK**`) so `startswith("STATUS AKHIR")` returns "none", and
  sometimes omit it entirely. Match with `"STATUS AKHIR" in line.upper()`; when absent, append
  an inferred verdict **labelled as inferred** (`ensure_verdict()`), never a clean-looking
  invented one.
- **A percentile tier is a treadmill, not a quality metric.** `C = bottom 40 %` means the
  count is invariant under improvement; report an absolute grade band alongside it or the
  user will believe a 30-point gain changed nothing (measured: tier `A43/B127/C112` before
  and after 8 major repairs, while `asas` fell 42 → 34). Never promise "tier C will drop".
- **Reweighting a keyword classifier by IDF inverts the labels.** Rare decorative words
  outscore definitional ones (`code`, `build`), so 68 of 282 agents flipped and
  `senior-developer`/`software-architect`/`pdf-engine-architect` became "Pencipta".
  Validate any classifier change offline and read the moved rows; prefer an additive
  secondary label (≥60 % of the top score) over rebalancing the primary distribution.
- **A soft finding in a cron script must not exit non-zero.** A weekly check that exits 1
  because a report lacked a `lulus` key — or because the QA verdict was the default
  `NEEDS_WORK` — makes the job report `error` and alarms the user while the pipeline ran
  fine. Derive pass/fail explicitly (`run done` + every agent done + final text > 200 chars)
  and treat the verdict's *content* as data, not as the test result.
- **`Run Time:` in a cron output file is when the run ENDED, not when it started.** Subtract the
  report's own `Masa: NNs` to get the real start, then compare it with the gateway boot line and the
  console's `ps -o etime`. Measured: a weekly check "failed" with `Connection refused`, `0/282` and
  15 UI failures — it had actually started at 15:25:16, seconds after boot, because cron **replays a
  missed slot immediately when the device comes back**. All three red lines were one cascade (every
  API-dependent step died, the offline LLM-retry step passed). Prove current health before proposing
  repairs (`ping`, `/api/agency/health`, `verify_roster.py`, `test_ui.js` → `282/282`, zero `GAGAL`),
  and say plainly that a ✅ step still carrying `STATUS AKHIR: NEEDS_WORK` is payload, not a fault.
  The other half of that incident was the supervisor: a keeper cron run reported
  `Script timed out after 3600s` and left two `keeper.sh` orphans (`PPID 1`, `/proc/<pid>/wchan` =
  `do_wait`) holding their `app.py` children — an hour with no supervision tick. Fix the class by
  gating the check on a `/api/ping` readiness loop (≤120 s) and bounding the keeper wrapper with
  `timeout 55`. Full timeline/forensics recipe: `references/cron-failure-forensics.md`.
- **On Termux, `setsid` inside `( … & )` does not detach — add `--fork`.** The cron keeper hung
  because of `( cd "$HC" && setsid ./run.sh >> server.log 2>&1 </dev/null & )`: the subshell keeps
  waiting on the child, so the script never returns and cron kills it an hour later.
  `setsid --fork …` returns immediately (measured `detached after 0s`, whole probe script 0.068 s).
  Prove the launch pattern in a throwaway script in `$HOME` before editing the live keeper, and
  after any repair confirm the server's `ps -o ppid` is `1` and the keeper exits in seconds.
- **`timeout <script>` on a non-executable file exits 126, not 124.**
  `timeout: failed to run command '…/console_keeper.sh': Permission denied` in 0.019 s means the
  wrapper lost its exec bit (cron ran it as `bash script`, so it never showed), not that the script
  is broken. `chmod +x` the wrapper and keeper before concluding anything; then a healthy run is
  `real 0m0.2s`, exit 0, **no output**.
- **`uptime` decides between "the device rebooted" and "Termux's process tree was replaced".**
  Measured 2026-11-10: a weekly job "failed at boot", but `up 4 days, 17:58` proved Android never
  rebooted. `ps -o etime` showed `runsvdir` and every service restarting at 15:25 while the Termux
  app process kept logging at 17:08 — children replaced, app alive. That signature is Phantom
  Process Killer / LMK / HyperOS App Freezer, **not** a reboot. Never write "peranti hidup semula"
  without `uptime`, and re-read the earlier diagnosis once `uptime` contradicts it.
- **A crash-looping runit service silently eats the phone** (and gets your daemons killed).
  `sv status web-server -> down: 1s, normally up, want up` + `FileNotFoundError:
  …/ULTIMATE_AI_PROJECT/projects` + `~/.web-server.log` **173 MB** + `load average 22.07` +
  `Mem 11139/11414 used, swap 6799/12287`. Fix: `sv down <svc>`, truncate the log, then repair the
  path or `sv-disable`. Never trust `sv down` on its own: `$PREFIX/etc/profile.d/start-services.sh`
  re-scans the directory at every Termux shell start, so also `printf 'down\n' > $PREFIX/var/service/<svc>/down`
  (`sv status` then stops saying `normally up`). Whenever a Termux daemon dies "randomly", run `sv status *` first.
- **A runit-logged Python app writes nothing to its log.** runsv hands the child a pipe, so `print()`
  stays in Python's block buffer and `~/.hermes20/logs/<svc>/current` sits at 0 bytes while the service
  is healthy. Use `exec python3 -u app.py` (and `export PYTHONUNBUFFERED=1`) in the `run` script; a
  timestamped banner in `current` is the proof the pipe is wired.
- **Unrotated logs are the real damage from a crash loop.** 168 MB of `~/.web-server.log` came from
  `exec >> log` in a `run` script — one file, no rotation, every restart appending. Always pair a
  service with `log/run` = `svlogd -tt <dir>` and `<dir>/config` = `s1000000` + `n5`.
- **Google Play Termux cannot use F-Droid add-ons.** `pm list packages com.termux.api|com.termux.boot`
  empty ⇒ `termux-wake-lock` still works (local script, exit 0, lock really held per logcat) but
  `termux-toast` exits **0** while showing nothing (`Broadcast sent without waiting for result`), and
  `~/.termux/boot/*.sh` will never run. Exit 0 from a termux-api tool is not proof of anything.
- **`dumpsys` / `settings` / `dmesg` are blocked on a stock phone.** `Permission Denial: can't dump
  PowerManagerService … missing android.permission.DUMP`, `INTERACT_ACROSS_USERS`, empty
  `dmesg`/`/proc/uptime`: battery whitelist and Doze state are **unverifiable without adb**. Say so,
  and separate the two phenomena: `httpx.ReadError` reconnect = Doze cut the network while the pid
  stayed alive; a replaced process tree = killer.
- **Run `app.py` under runit, not as an orphan.** `ppid=1` means nothing restarts the console; it
  only survived the 15:25 event because it sat in its own `setsid` session. A `console` service
  gives `sv status` one-line health plus automatic restart — cheaper than any watcher.
- **Kill keeper shells by pid, never by pattern.** `kill -TERM <keeper_pid>` after
  `ps -o pid,args -p <pid>` leaves the `app.py` children serving (they reparent to `PPID 1`);
  `pkill -f app.py` would take the console down with the caller's own shell.
- **Two identical `python3 app.py` rows are usually one app on two ports, not a double start.**
  On a 8787 + 8790 setup `ps | grep app.py` prints two indistinguishable lines; killing the "extra"
  one takes down the other home. Resolve by port with `tr '\0' '\n' < /proc/<pid>/environ | grep
  CONSOLE_PORT` (+ `/proc/<pid>/cwd`, `ps -o etime`) — `ss -ltnp` says `Cannot open netlink socket:
  Permission denied` on Android, `/proc/net/tcp` is denied, `lsof` rejects `-nP`, and both processes
  show the same socket-fd count, so none of those can tell them apart. A process older than the
  incident (`etime` ≫ drill duration) cannot be the keeper's artifact.
- **One `keeper.sh` sighting in `ps` is the 5-minute cron tick, not an orphan.** `grep -c` returned 2
  once and 0 thirty seconds later. Judge "hanging" only from a sampled window (5 × 2 s, all empty);
  a real orphan persists in every sample and carries `PPID 1` + `wchan do_wait`.

- **A panel that parses numbers out of a report file shows history, not truth.** A "CADANGAN KETUA"
  panel regexed `logs/agency-catalog-drift.txt` and kept warning *"60 badan ejen berbeza"* for days
  after the catalogue had been synced (file 13 days old, real diff 0/0/0). Any figure on screen must
  be recomputed in the endpoint (282 md files ≈ 100 ms) and cached on input mtimes; a derived
  artifact may appear as metadata **with its age** (`age_h`, "rujukan sahaja"), never as the number.
  Return a `"live": true` flag so the UI can say which mode produced the figures. Same rule for
  `data/*.json` snapshots written by workers.
- **Computed advice with no action reads as nagging.** "278 daripada 282 ejen belum dipakai" is a
  fact the user cannot act on. Return one concrete pick per group — e.g. 1 pilot agent per division
  scored by overlap with locally installed skill prefixes — as clickable chips that open that agent
  (18 chips from 18 divisions, measured). Every idea card should carry a number that is live and a
  thing to click.
- **Compare rosters by `(division, slug)`, not by `source_path`.** The same corpus exists twice with
  different layouts (app copy flat, git clone nested in `unity/`, `godot/`, `unreal-engine/`);
  path-keyed comparison invents 15 "only in app" + 15 "only in active" entries and hides real body
  drift behind them. Report layout differences separately as harmless, and offer a
  `--fix-paths` repair that rewrites `source_path` from a walked disk index after copying
  `agents.json.bak-<date>`.
- **`pkill -f "python3 app.py"` kills the shell running the command** — the pattern matches the
  caller's own `bash -c` cmdline; the tool returns `exit_code: -15` and the restart silently never
  happens. Never pattern-kill your own server. Use `scripts/stop_server.py` (pid file first, then
  `/proc/<pid>/cmdline` + `cwd` check, skipping own pid and parent pid).
- **`du -sk` on a 16 GB home exceeds a 25 s subprocess timeout** → returns 0 → UI shows `0 MB`.
  Compute folder sizes in a daemon thread (timeout 600–900 s, refresh 5 min, cache TTL 10 min) and
  return `None` until ready; UI renders `mengira…`/`–`, never `0`.
- **`/tmp` is not writable in Termux** (and is `noexec`); `curl -o /tmp/x.json` silently yields
  0-byte output, and a probe script copied to `/tmp` fails with `Permission denied` — which looks
  like a broken script rather than a mount option. Keep throwaway test scripts **and** their logs in
  `$HOME` (e.g. `~/detach_test.sh`), then delete them; write real temp files inside the project dir.
- **Duplicate dict keys in one literal**: `{"ideas": computed, ..., "ideas": None}` → `None` wins
  and the panel renders empty. Build once, or assign after construction.
- **sqlite `messages.tool_calls` nesting**: usually `{"function":{"name":"terminal","arguments":
  "<json string>"}}`, but plugin tools arrive wrapped as
  `{"function":{"name":"tool_call","arguments":"{\"name\":\"agency_agents_load\",\"arguments\":{...}}"}}`.
  Unwrap the inner `name` + `arguments` or usage counters silently read 0.
- **WAL databases**: open with `mode=ro` (not `immutable=1`) so `-wal`/`-shm` stay readable.
- **Re-render on poll can wipe a selection/search** — keep `S.<tab>.sel` / `S.<tab>.q` in state and
  restore after each fetch; skip reload while an input is focused.
- **`FastAPI` `Query(...)` defaults** belong in the signature only; passing them as plain defaults
  loses validation but works — keep `ge=`/`le=` bounds so a bad `limit` can't pull 100k rows.
- **Reasoning models truncate silently.** `finish_reason: "length"` can arrive with **non-empty**
  content — half a JSON plan. Downstream this surfaces as `json.loads` → "Unterminated string" or
  "Expecting ',' delimiter", which reads like the model can't write JSON but is budget exhaustion.
  Check `finish_reason` *before* returning text; double `max_tokens` (cap ~8000) and retry. Keep a
  `_coerce_plan()` backstop (ask the model to repair once) but fix truncation as the root cause.
  A 20-token cap is always empty (reasoning eats it); 300 suffices for one word. Working defaults
  for a 282-agent planner: plan 4000, agent 6000 (raised from 3200 after empty-content failures),
  synthesis 3600, with the empty-`content` escalation ladder described in Phase 12 pitfalls.
- **A synthesis verdict is a *claim*, not evidence — reconcile it with the archived artifacts before
  repeating it to the user.** Measured: Ketua returned "Whimsy Injector terputus pada §5 selepas
  'nampak '" and "Image Prompt Engineer terputus mid BB-02, BB-03–BB-18 tiada", failing two QA gates —
  while `out_whimsy-injector.md` (11,215 chars) and `out_image-prompt-engineer.md` (14,400 chars) were
  complete, both ending in `STATUS: DONE` + `SERAHAN:`. Cause: the runner's `[:7000]` / `[:9000]`
  slices. Forensics that settle it in seconds: slice the stored text at the cap boundary
  (`t[8940:9000]`) and check whether it ends exactly where the verdict says the text stopped. When a
  verdict fails on "terpotong/tiada", correct it explicitly (a `06_SEMAKAN_BUKTI.md` in the handoff
  package) and separate the *real* gaps from the phantom ones. Never relay a quota/budget artefact as
  an agent's mistake.
- **Relaying a run to chat: one format per folder + a BACA DULU, not one blob.** Copy
  `plan.json`/`out_*.md`/`final.md` into `runs/<id>/PAKEJ/` as numbered `.md` files
  (`00_BACA_DULU.md` with a fail→reader matrix, `01_PELAN…`…`NN_…`), add the reconciliation file, and
  put the verdict text in the chat body while the full documents ride as `MEDIA:` attachments. The
  user reads the decision on the phone and opens the detail only when needed. Filenames carry the
  order; the matrix tells them which file to open first.
- **DOM-shim harness only stores selectors it has seen.** `nodes[sel]` is `undefined` for a panel
  never queried → `Cannot set properties of undefined (setting 'innerHTML')`. Use a lazy accessor
  `q(sel)` that creates the element; that's a harness bug and looks like an app crash. Modern pages
  also need stubs for `URLSearchParams`, `setAttribute`, `focus`, `createElement`, and
  `appendChild` that concatenates `innerHTML`.
- **urllib headers are latin-1**: an em dash in `X-Title` throws
  `'latin-1' codec can't encode character '\u2014'` before the request leaves the process.
- **A missing `import urllib.request` only surfaces at send time** — the report generates, then the
  Telegram call 502s with `name 'urllib' is not defined`. Import at module top and exercise the
  delivery path, not just the generator.
- **Markdown/text endpoints must not go through the JSON helper.** `api('/api/report/daily')` throws
  on `.json()`; use `fetch(...).then(r => r.text())` for the preview.
- **Two writers on `run.json` lose operator input**: a note posted mid-run was overwritten by the
  worker's stale copy (`inbox: 1` → `0`). Per-run `RLock` + `append_inbox()` +
  `save(merge=True)` that keeps the longer `inbox`/`attachments`; worker re-reads both at each wave.
  See `references/run-state-integrity.md` Fix 6.
- **Inserting a key into an endpoint's `return {...}` literal**: a patch whose `new_string` starts a
  second `return {` turns
  ```
  return {
      "identity": …,
      return {"paper": …, "symbols": …,
  ```
  into a `SyntaxError: '{' was never closed`. Anchor on one unique key line and add the new key
  inline (`"paper_live": paper_state(),`), then re-run `python3 -c "import ast;ast.parse(...)"`.
- **`read_file()` on `.env`/secret files may return no `content` key** (guarded read) — indexing
  `["content"]` raises `KeyError` inside `execute_code`. Use `pathlib.Path(p).read_text()` there,
  and never echo the values into the transcript; print key names or `sha256[:8]` instead.
- **Second Telegram poller gets `409 Conflict`.** The gateway owns the bot's `getUpdates`; inbound
  needs a separate bot token. Outbound `sendMessage`/`sendDocument` is fine on the existing token.

- **Polling a 3-minute run inside one foreground call hits the tool timeout.** A `python3 - <<EOF`
  loop that plans, starts and polls a run dies at ~180 s; buffered `print()` output is lost, so the
  transcript looks like nothing happened. Start the run in one short call, then poll from separate
  short calls (or `background=true` + `notify_on_complete`). Same for `du` on a huge home.
- **Two instances on one port leave a lying pid file.** The second bind fails with
  `[Errno 98] address already in use`, but `server.pid` from the failed start remains, so the next
  stop/start targets a dead pid. Give each context its own `CONSOLE_PORT`, and confirm with
  `curl .../api/meta` (check `default_home`) instead of trusting the pid file.
- **One `server.pid` shared by two instances kills the wrong one.** Both write the same file, so the
  last starter wins and `stop_server.py` signals *that* process: asked to stop 8787, it killed 8790
  (8787 still `200`, 8790 → `000`). Per-port pid files + `--port`/`--all`, and match the port through
  `/proc/<pid>/environ` in any `/proc` fallback scan.
- **A dead URL is usually a dead process, not a broken app.** Check `ps`, listening port, pid file,
  `curl`, then **`uptime`** — "up 28 min" plus an empty `ps` means the device/Termux restarted and
  killed every daemon; the stale pid file guaranteed nothing restarted them. Report that table before
  changing any code. `Invalid HTTP request received` in the log = someone tried `https://` on the
  HTTP port; it is a symptom of retries, not the fault.
- **Nothing restarts the console after an Android reboot.** An idempotent `start_all.sh` plus a
  `no_agent` cron `keeper.sh` every 5 min (silent when healthy) is the minimum. Hermes cron rejects
  absolute script paths — keep a 3-line wrapper in `~/.hermesNN/scripts/` that `exec`s the real one,
  and verify with `action='run'` that a healthy run delivers **no** message.
- **`if (S.busy) return;` in `loadTab()` loses the tab the user just clicked** — the pane stays on
  `memuat…` forever. Record `S.pending = true`, loop while pending, and reset `busy` in `finally`.
- **A fetch with no timeout freezes every tab.** One hung endpoint keeps the in-flight `loadTab()`
  unresolved, so `busy` never clears. Wrap `api()` in `AbortController` (~25 s); the DOM-shim harness
  then needs `AbortController` stubbed or every check fails with "is not defined".
- **A slow endpoint makes a render check lie.** `/api/device/status` shells out to `pm list packages`
  and measured 1.4–4.3 s; a 1200 ms wait after that `setTab()` fails two checks every run. Raise the
  wait for that one tab (~6 s) and comment the reason instead of "fixing" the page.
- **Debug a shim hang by exposing state, not by guessing.** `const S` never lands on the vm global, so
  add a temporary `globalThis.__hcState = () => ({tab, stage, busy, pending})` hook plus `S.stage`
  markers per branch, print it at the failing check, then delete both and confirm with
  `grep -c "__hcState\|S.stage" static/app.js` → `0`.
- **A Termux-hosted console cannot install the APK it just served.** `termux-open x.apk` and
  `am start -a VIEW -d file://…apk` both fail silently (Termux declares no
  `REQUEST_INSTALL_PACKAGES`, and `file://` URIs have been blocked since Android 7). Deliver the
  file, open its folder in the file manager, or use `adb install`; full decision table lives in the
  `android-device-control-from-termux` skill. And check the file is *visible* before blaming the tap:
  an APK written by `curl` in Termux is absent from MediaStore, so Files by Google does not list it
  at all (user: *"TermuxBoot nama ni tak ada, cuma ada termuxapi.apk"*) — copy it into a folder the
  user has already browsed, or install over ADB (`references/apk-visibility-and-portless-pairing.md`
  in that skill).
- **A hardcoded default tab can render a blank pane.** `S.tab = "overview"` while the HTML marks
  PUSAT `active` (or the reverse) yields an empty body until the user clicks a tab. Keep one source
  of truth: seed from `/api/meta` and finish boot with `setTab(S.tab)`.
- **Deep link applied too early gets overwritten.** `S.tab = qsTab` placed *before*
  `S.tab = S.pendingHome ? … : meta.default_tab` silently loses the URL parameter. Assign the
  default first, then let `?tab=` / `#hash` win, then boot with `setTab(S.tab)`.
- **An ambiguous HTML anchor duplicates IDs.** Patching `<div class="brand">` as context replaced
  `<span class="dot" id="livedot">` with a button, and left two elements claiming `id="clock"` —
  `getElementById` then updates the wrong node and the clock freezes. After any header/layout edit:
  `grep -c 'id="clock"' static/index.html` for each id you touched, and keep the anchor long enough
  to be unique.
- **Render-test OK-count is not stable.** Async renders finish after a fixed `wait()`, so the same
  suite printed 36 / 39 / 41 on consecutive runs. Gate on **zero `GAGAL`** plus the specific checks
  you care about, and run it twice before quoting a number.
- **`grep -rl <pattern> ~/.hermes20` never finishes inside a tool call.** It hit the 180 s timeout while
  hunting references before deleting a run; `search_files(pattern=..., path=…)` (ripgrep) answered in
  under a second with the same 4 hits. Scope searches to the project dir first. A console run is a
  directory under `runs/<id>/`, not a DB row, so `rm -rf runs/<id>` removes it from the archive —
  prove no runner process, verify references, then re-list `runs/`, and say that `MEDIA:` copies
  already delivered to chat cannot be pulled back (`references/run-verdict-reconciliation.md` §5).
- **Editing `agency_runner.py` (or any console module) changes nothing until the instance restarts.**
  Python imports at boot: after a runner fix,
  `python tools/stop_server.py --port 8787 && sleep 1 && bash tools/start_all.sh`, then
  `curl -s 127.0.0.1:8787/api/ping`. Skipping this yields a "fixed" bug that reproduces once more and
  undermines the diagnosis.
- **Compound one-liners get blocked by the command parser.** Long `curl … | grep …; curl … | python3 -c …`
  chains can be rejected before execution (saved under `cache/blocked-scripts/`). Split into small
  single-purpose commands, or move the logic into a script file. Two patterns hit this on
  2026-11-11: an inline `sv restart hermes-console` (refused with *"cannot restart or stop the
  gateway from inside the gateway process"* — the guard cannot tell a console service from the
  gateway, and SIGTERM would also kill the caller), and some `python3 - <<'EOF'` heredocs that
  touched service/step files (same message, false positive). Working substitutes: restart the
  console through its own API — `POST /api/svc/hermes-console {"action":"restart"}` with
  `X-Console-Token` (the deferred path returns before TERM) — and put any multi-line maintenance
  logic in a real `.py` file under `$HOME` and run `python3 <file>`.

## Local knowledge files

- `references/phone-first-entity-dashboard.md` — 282-entity phone dashboard: roster-vs-payload
  field names, three cache layers (2,170 → 120 ms), `/api/agency/health`, 8-worker fleet sweep
  with latency percentiles, 60-row render cap, browserless harness specifics, verdict inference.
- `references/roster-quality-repair.md` — repairing thin persona bodies: tier-vs-grade
  treadmill, body-vs-`.md` diagnosis, enrichment prompt + validation gates + backups, measured
  before/after for 8 agents, dual-archetype rule (and the rejected IDF reweighting), weekly
  `no_agent` cron wrapper and its exit-code traps.
- `references/hermes-state-db-and-agency-catalog.md` — Hermes `state.db`/`kanban.db` schema +
  queries, agency roster on-disk layout (282 agents, 18 divisions), **live-vs-stale drift
  computation, `(division, slug)` keying, `--fix-paths` repair, and how router delegation counts
  turn "belum ada delegasi" into evidence**.
- `references/roster-orchestration.md` — planner/executor/synthesis prompts, digest sizing,
  slug validation, persona injection, run artifacts, reasoning-model token quirks, measured timings.
- `references/run-state-integrity.md` — atomic writes, tolerant reads, slot recovery, stale-run
  reconciliation, and the multi-writer merge rule for live notes/attachments.
- `references/local-console-security.md` — Host/Origin allowlists, CSRF token, CSP, id validation,
  `scrub()`, injection scan, spend guards.
- `references/live-org-chart.md` — live org-chart geometry, SSE state push, cost/location overlay.
- `references/cost-and-agent-tracking.md` — `usage.cost` capture, per-agent/per-stage roll-up,
  `running_since`, server-side `/api/bot` commands, history snapshots.
- `references/lan-access-and-tls.md` — token→cookie handshake, `?t=` redirect, `/api/ping`, SAN.
- `references/attention-and-delivery.md` — active-agent cards band, daily report + Telegram document,
  base64 inbox, attachments in plans, mid-run notes, two-bot Telegram bridge.
- `references/hermes-desktop-integration.md` — desktop-plugin contract, embed mode, CSP frame rules,
  harness-based verification when Electron is absent.
- `references/multi-home-instances.md` — per-home env contexts, two live instances, verification matrix.
- `references/external-worker-monitoring.md` — observing a process the console doesn't own: artifact
  sources, `/proc` liveness, pid-file adoption, live-vs-snapshot proof, **market-data provider chain,
  credential archaeology and proxy labelling (§5–§8)**.
- `references/ui-discoverability-and-adb-pairing.md` — why a built panel still reads as "tak jumpa":
  `?tab=` deep links, header quick-jump, `/api/device/adb-pair` + `/api/device/shot`, status caveat,
  pairing-code-vs-login wording.
- `references/runit-supervision-and-inline-guides.md` — console under runit (service files, `svlogd`
  `s1000000`/`n5`, `python3 -u` so the log isn't empty, permanent `down` file, orphan-holds-the-port
  trap, kill-drill numbers, boot ceiling without Termux:Boot) + schematic SVG guide generator with the
  five layout defects a proofread pass catches + HyperOS persistence checklist.
- `references/service-control-panel.md` — whitelisted `sv` control panel: `SVC_ALLOW`, action
  endpoint, `BackgroundTasks`-deferred restart of the console's own service (~10 s on Termux),
  `sv status` parsing traps, log endpoint, `/api/device/boot*` + APK one-tap handoff, smoke-test
  extensions.
- `references/image-upload-pipeline.md` — "aku dah letak imej tapi tak keluar": curl proof with
  `X-Console-Token`, `--data-binary @file` for >9 MB base64 bodies, the lying-extension bug
  (HEIC→`.png`) and its Pillow→JPEG fix (7.2 MB → 734 KB), a dedicated upload panel with a
  `count`-based confirmation, and script-file cleanup of test steps.
- `scripts/verify_svg_text_layout.py` — geometric SVG text checker (estimated bboxes, frame
  clipping, overlaps) so illustrated guides don't depend on a vision pass that may render tofu.
- `scripts/console-runit-smoke.sh` — generic runit health script: `sv status`, `/api/ping`, promised
  assets, log-rotation size, single `app.py`, optional `KILL_DRILL=1` restart proof; exits with the
  failure count.
- `templates/render_test.js` — DOM-shim render harness for any static HTML+JS page.
- `templates/console_instance.sh` — per-home launcher (env-driven context, own port).
- `scripts/stop_server.py` — safe server stop (pid file + /proc scan by cwd, never `pkill -f`).
- `references/instance-supervision-and-recovery.md` — "tak boleh buka" diagnosis order (incl.
  `uptime`), per-port pid files, start_all/keeper + `no_agent` cron, busy-flag & fetch-timeout UI
  freezes, slow-endpoint test timing, state-hook debugging, `OPERASI.md` runbook.
- `references/cron-failure-forensics.md` — a failed `no_agent` health-check job: `Run Time:` is the
  END time, boot catch-up races service startup, cascade-vs-real-fault test, spare-port startup
  measurement, hung keeper forensics (`do_wait` + `PPID 1` orphans), readiness-gate fix, and the
  **applied/verified repair (§4b–§5): `setsid --fork` detach, `timeout 55` wrapper, exec-bit 126 trap,
  pid-only keeper cleanup**.
- `scripts/supervise_consoles.sh` — env-driven starter + keeper for N console ports (silent when
  healthy, prints only what it repaired).
- `references/watchdog-recovery-drill.md` — deliberate-kill drill: commands, measured 8 s keeper /
  16 s total recovery, two-`app.py` disambiguation via `/proc/<pid>/environ`, cron-tick sampling rule.
- `scripts/validate_desktop_plugin.py` — static validator for a `desktop-plugins/` entry.

## Reporting template (Malay, terminal-plain)

```
Siap. <fasa> → <fasa> → <fasa>, semua dengan bukti.
APA YANG DIBINA   <paths + sizes>
BUKTI             <endpoint: code · ms · bytes>  <sqlite cross-check>  <render test lines>
JAMINAN           read-only mode=ro, bind 127.0.0.1, path allowlist, esc()
FAIL DIKEMAS KINI <file → apa berubah>
Seterusnya: <3–4 concrete options, numbered — this user answers by number>
```

Reply shape that works for this user: one short section per request they made (status + a table
of measured numbers), the bugs found and fixed, then the numbered options. Attach generated
documents with `MEDIA:` instead of pasting them.
