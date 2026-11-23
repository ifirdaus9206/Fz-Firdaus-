---
name: agent-team-operations
description: Operate a lead/worker AI agent team with briefs and gates.
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, termux, windows]
metadata:
  hermes:
    tags: [orchestration, agents, ketua, delegation, console, roster, soul]
    related_skills: [localhost-monitoring-console, ai-agent-architecture, hermes-agency-integration]
---

# Agent Team Operations

How to *operate* a multi-agent team: who gives orders, what a brief contains, how work is
dispatched, how failures escalate, and how the owner sees who is working. This is the operating
doctrine, not the dashboard build (for building the console see `localhost-monitoring-console`).

## When to use

- The owner says "kau ketua, arahkan ejen — jangan buat sendiri".
- The console/roster shows no agents assigned although hundreds are installed.
- A session where the agent has been doing the handiwork itself and the owner noticed.
- Deciding how many roles to create, what each one owns, and what the lead may not do.

## The core mistake: roster ≠ team

Installing N agents installs N **personas inside one process**. No per-agent memory, workspace,
model, or process — so nothing can appear as "working", and any answer that counts the roster
("282 ejen!") is misleading.

A real team is 4–6 roles, each with its **own** Hermes profile/home, short-term memory
(`profile`/`soul`/`user`/`memory`/`agent.md`), workspace directory, skills (= SOP), model
(cheap for light roles, strongest for the lead), and channel (Telegram for owner-facing work).
Layer-by-layer checklist and how to score an existing setup against it:
`references/ai-team-layers.md`.

**"Bagi kau memori masa pendek dan masa panjang supaya belajar setiap hari"** — that is a separate,
durable tier *outside* `memories/`: a daily append-only log plus a nightly distillation cron that
rewrites one categorised long-term file. Layout, scripts, cron prompt and the
`hermes cron create` parameter-drop workaround: `references/memory-tiers.md`.

## Lead-agent doctrine (write it into SOUL.md, not into a reminder)

1. **The lead does not execute.** Handiwork (code, scans, tests, documents) belongs to agents.
   The only permitted lead activities are writing the brief and reading evidence.
2. **No instruction without a named agent** — slug, task, dependencies, gate.
3. **No agent starts cold** — 8-field brief: objective · context · input · scope · prohibitions ·
   output format · pass criteria · deadline.
4. **No pass without evidence** — path, command output, or test count. Claims = NEEDS_WORK.
5. **Agent wrong → escalate, don't take over.** P1 re-brief · P2 re-run with more context ·
   P3 drop tier / rewrite persona · P4 retire (owner approval only). Max 3 attempts before P3.
6. **The 8-system flow runs inside the agents** (factory → role → workflow → orchestrator → QA →
   recovery → completion + memory); the lead only holds gates and signs the verdict.
7. **Report as a board** — agent · task · status · evidence — never "I did it".

Install it: back up first (`cp SOUL.md SOUL.md.bak-ketua-$(date +%F)`), rewrite `SOUL.md`, and tell
the owner exactly which file changed and where the backup is. A persona change only takes effect on
the next session, so demonstrate the new behaviour immediately with one real dispatch.

When the owner redefines the lead's own identity — pasting numbered role statements, merging several
roles into one tiered persona, or renaming — follow `references/role-tier-merge.md` (tiers → runbook
pair → plan doc → wiki, in that order) or `references/identity-rename.md`. Both include the
doc-alignment waves, the stale-title grep that must stay honest, and the line-count traps that make a
child's evidence table wrong by one.

## Two machines, two agents — one voice, not one agent

The owner will eventually name a second agent living on another machine (*"di PC ada agent nama dia
Sofia … kau dan Sofia setiap seorang ada tugas masing-masing, atau perlu buang satu?"*). The question
is a false binary: **do not retire either.** Answer with the split of duties, then name the one thing
that must stay singular.

| | Lead on the phone (Termux) | Second agent on the PC |
|---|---|---|
| Uptime | 24 h, always with the owner | only while the machine is on |
| Owns | gateway/Telegram, cron, backup, email, vault, console | heavy work: project code, builds, big files, browser automation, machine health |
| Reports to | the owner | **the lead**, not the owner |

Rules that keep it a team instead of two competing narrators:

- **One voice to the owner.** Two agents messaging the owner independently produce two chats and two
  versions of the truth — exactly what the owner was trying to avoid. Write into the second agent's
  `SOUL.md`: report to the lead, accept 8-field briefs, no daily reports to the owner.
- **A separate Telegram bot token is mandatory** (two pollers on one token = `409 Conflict`, both go
  deaf), but the token is not permission for a second conversation: that bot carries **emergency
  alerts only** (machine down, build failed, disk full); routine status goes to a status file the
  lead's console reads. Say it plainly: *"token berasingan wajib; suara berasingan tidak."*
- **One screen is not one origin.** "Monitor satu tempat" is satisfied by the lead's console reading
  the other machine's status through a relay — `homes.json` holds only local paths, so never claim
  "dah masuk dashboard" without building the remote read path. Recipe:
  `localhost-monitoring-console` → `references/multi-machine-agent-relay.md`.
- **Check reachability before designing the link.** A phone on mobile data (CGNAT `100.64.0.0/10`,
  e.g. only `100.85.34.233` in `ifconfig`) has no route to the house LAN, and a peer key sitting in
  `authorized_keys` only proves the key was *installed* — not that the peer ever connected. Put both
  facts on the board before proposing SSH; the answer changes the plan.
- **Board shape for this decision:** one row per check with its evidence → duties table → honest
  ceiling (*"relay lewat 5 minit — cukup untuk tahu PC hidup, bukan tengok skrinnya"*) → 3–4 numbered
  options. A `3.ya`-style reply resumes that list; recover it from the session DB before acting.

## Knowledge layer (`knowledge_base/`) — facts live outside memory

Once the doctrine exists, the team still needs a place for **SOP and facts** that is not memory:
brief format, dispatch flow, escalation ladder, backup procedure, status table, templates.
Put it in `~/.hermesNN/knowledge_base/` as interlinked markdown (`index.md` + `SCHEMA.md` +
`log.md` + `sop/`, `fakta/`, `templat/`) so an agent can be pointed at one page instead of being
told the rules again in every brief.

Build rules that keep it auditable: every page carries frontmatter (`tajuk`, `jenis`, `kemas_kini`,
`sumber`), links back to `index.md`, uses relative markdown links (not `[[wikilinks]]`), and quotes
the source file inline for each load-bearing claim. **Build it by reading the owner's docs, never
from memory of them** — a referenced doc that does not exist is a finding to report *inside a wiki
page*; do not dress the gap in plausible prose there. Filling that gap is a separate, owner-assigned
job with its own discipline (see the runbook pair below). Status tables get copied verbatim,
including source-internal contradictions, and are *not* silently upgraded when your new work fills
a `TIADA` row.

Full recipe, page-level conventions and the review checklist: `references/knowledge-base-wiki.md`.
Verify mechanically with `python3 scripts/verify_wiki.py ~/.hermesNN/knowledge_base` (frontmatter,
back-links, broken links, sizes), and paste its real output plus one source quote per fact into
`docs/LAPORAN-*.md`.

## The runbook pair: `OPERASI.md` + `docs/KETUA.md`

A lead-agent `SOUL.md` usually points at two written guides the owner expects to exist: `OPERASI.md`
(daily runbook) and `docs/KETUA.md` (the lead's manual). If the header says
`pelan bertulis: OPERASI.md, docs/KETUA.md` and `ls` shows neither, P1 is unfinished — the persona
cites dead paths.

Authoring them is allowed without "inventing rules" **only if every line traces to a source you
actually read**:

- Read the whole set first: persona + `SOUL.md.bak-*`, `knowledge_base/sop/*`, `templat/*`,
  `docs/PELAN-*.md`, `docs/LAPORAN-*.md`, `workspaces/README.md`, vault `README.md`. The backup
  persona carries doctrine the current one dropped (max-3-attempts, completion boxes, output dirs).
- End each file with a **`Kemas kini`** block: date, author, status ("dicipta — sebelum ini dirujuk
  oleh SOUL.md baris N tetapi tidak wujud"), numbered sources read, and the line
  "Tiada peraturan baharu direka."
- Touch nothing else — no `SOUL.md`, `config.yaml`, `memories/`, `skills/`, `plugins/`, `system/`, no
  profiles. Prove it with `ls -la SOUL.md` (mtime), not a promise.
- Produce exactly one evidence report with real command output and a table mapping each `SOUL.md`
  path reference from TIADA → ADA.

Skeletons, verification commands, and the enumeration-counting pitfall:
`references/runbook-pair.md`.

## Dispatching work to the console engine

The console (`~/hermes-console`, FastAPI on 127.0.0.1:8787) plans and runs agent teams:

- `POST /api/agency/plan {instruction, max_agents ≤ 6}` → run record with `plan.ejen[]`
  (slug, nama, division, sebab, skop, depends_on), `waves`; `POST /api/agency/run/{id}` executes.
- `GET /api/agency/runs` lists recent runs (id, created, status, instruction, agents).
- `GET /api/agency/health` = roster counts + run done/failed/active + per-agent usage.

**Pitfall — POST from the shell gets `403 token konsol tiada atau salah` while GET returns 200.**
`app.py` mints `CSRF_TOKEN = secrets.token_urlsafe(24)` per process and requires it as
`x-console-token` on every POST. It **is** served: `GET /api/meta` returns it as `csrf`, so shell
dispatch needs no import at all:

```bash
cd ~/hermes-console
CSRF=$(curl -s http://127.0.0.1:8787/api/meta | python3 -c 'import sys,json;print(json.load(sys.stdin)["csrf"])')
curl -s -X POST http://127.0.0.1:8787/api/agency/plan \
  -H 'Content-Type: application/json' -H "x-console-token: $CSRF" \
  --data-binary @/data/data/com.termux/files/home/brief.json
curl -s -X POST http://127.0.0.1:8787/api/agency/run/<run_id> -H "x-console-token: $CSRF"
curl -s http://127.0.0.1:8787/api/agency/run/<run_id>     # poll: running → synthesizing → done
```

The token rotates on every console restart — fetch it fresh, never hard-code it. Write the plan
payload to a file and pass `--data-binary @file`: heredocs plus long Malay instructions mangle
quotes. If `/api/meta` is unreachable (LAN-token mode on), fall back to importing the runner in the
console directory:

```bash
cd ~/hermes-console && python3 -c "
import agency_runner as ar
r = ar.plan_run(open('/path/brief.json').read(), 3)
print(r['id'], [e['slug'] for e in r['plan']['ejen']])
print(ar.start_run(r['id']))"
```

**Pitfall — the SISTEM tab answers "what is running", never "who is working".** `/api/health`
`processes` only sees Popen children, while agency runs execute in daemon threads. Add a
`EJEN BERTUGAS` panel fed by `/api/agency/runs`, and enrich `agency_runner.latest()` with
`ejen_nama`, `bil_ejen`, `outputs`, `error`, `wave`, `wave_total` — the stored run only carries
`plan.ejen[].slug`, so without mapping the UI shows bare slugs and the owner still cannot tell who
did what. Restart the instance after editing console modules (Python imports at boot).

**Cron scripts must live under `~/.hermesNN/scripts/`** — `hermes cron create` rejects absolute or
home-relative paths. Keep a 3-line wrapper there that `cd`s and `exec`s the real script.

## Roster runs produce prose; they do not touch the disk

Two executors exist and they are **not** interchangeable:

| Executor | What it actually does | Use for |
|---|---|---|
| console runner / agency plan+run (`agency_runner.py`) | LLM call per slug → **text** in the run record. No `write_file`, no `mkdir`. | design proposals, reviews, choose-an-approach |
| `delegate_task` subagents | full tool loop (`terminal`, `write_file`, `patch`) → real files + command output | every build: workspaces, vaults, wikis, profiles, cron, config |

A brief like "build 6 workspaces" sent to the roster returns a paragraph *describing* workspaces; the
same 8-field brief sent to `delegate_task` returned 31 files and a `find | sort` transcript. State this
plainly when the owner asks why "282 ejen" built nothing — and never pass a roster run off as a build,
or handiwork off as a roster run. `delegate_task` concurrency is 3, so split 4+ role builds into waves
and give each wave its own board.

**When the roster agent refuses, that is NEEDS_WORK — not a pass.** A text-only roster agent asked to
write a file will sometimes answer honestly ("saya tiada alat untuk membaca fail / jalankan grep") and
hand back a ready-to-run command protocol. Do not score that as done, and do not paste its protocol to
the owner as the deliverable: put it on the board as **gagal / P1**, then re-send the *same* brief to
`delegate_task` (real shell + `write_file`) and verify the artifact yourself. Honest refusal is the
right behaviour for that executor; it is still a failed task, and the doctrine says escalate the brief
rather than take the pen.

`delegate_task` argument shape: pass `tasks: [{goal, context, role: "leaf"}]`. A call that carries only
`context` fails instantly with *"Provide either 'goal' (single task) or 'tasks' (batch)"* — the batch
shape survives long Malay contexts, and the goal must be self-contained because the child sees nothing
of the conversation.

## Parallel children: fix the interface first, split by FILE

When one request decomposes into features that touch the **same** files, the unit of delegation is the
file set, not the feature. Two children each editing `app.py` + `app.js` overwrite each other — merge
those features into one child. Parallel dispatch is safe only across disjoint paths: a
"Markdown → PDF" child owning `~/.hermes20/scripts/*` ran alongside a console child owning
`~/hermes-console/*` with no conflict.

Before dispatching in parallel, put the contract in **both** briefs:

- **Exact paths and CLI shape** the other child will create — e.g.
  `uim_pdf.sh <file.md> [--nama NAMA.pdf]`, last line `SIAP-PDF: <path>`, non-zero exit on failure —
  so the consumer can be written against a script that does not exist yet.
- **Ownership boundary in the prohibitions field**: "jangan sentuh `~/hermes-console` — pekerja lain
  sedang edit fail itu". Restating it in both briefs is what keeps the split real.
- **Each child backs up the critical files it will edit** (`~/backups/<area>-<date>/`), and the lead
  keeps its own copy of every file about to be touched *before* dispatching.

Then verify yourself, and **do not wait for the consolidated delegation message**: children can be
finished for minutes while their summaries are still being assembled. Poll the artefacts (tail the
live transcripts, then `curl` / `ls` / `sha256sum` the outputs) and report once the evidence exists.
A child's PASS on its own endpoint is a self-report — replay the call yourself, including the CSRF
header, or the `403` looks like a broken endpoint and the real guards (400 on `/etc/hostname`, 400 on
a symlink pointing out of `$HOME`) stay untested.

## When a child dies mid-job — resume, don't restart

A `delegate_task` child can stop mid-run (session ended, provider timeout) *after* writing some
files and *before* any verdict. Symptoms: the live transcript ends on a tool result, the
`docs/LAPORAN-*.md` it was told to write does not exist, and only part of the target files moved.

```bash
find docs knowledge_base -name '*.md' -newermt '<start time>' -printf '%TH:%TM %s %p\n' | sort
ls -l docs/LAPORAN-<job>.md                    # absent → the job did not finish
tail -5 cache/delegation/live/deleg_<id>/task-0.log
```

Re-dispatch **one** child whose context opens with `SUDAH SIAP (jangan ulang, jangan ubah lagi)`
plus the file+mtime list of what already landed, and whose goal lists only the remainder with the
exact count each file must reach. Re-running the original brief duplicates rows — the signature is
the same wiki page listed twice in `index.md`.

**Never dispatch the correction while the original child is still alive.** A "dead" child may only be
slow — its report arrived ~7 minutes after the deliverable appeared, and it was still writing
`index.md` when the corrective child was editing the same file (46 → 50 → 48 lines, two writers).
Before re-briefing, confirm the child is finished, not just quiet: the run's completion message has
arrived, **or** the transcript ends with a final assistant summary rather than a tool result. If you
must correct a defect spotted early, wait for the terminal state first, then dispatch one child whose
goal names the file mtimes it may edit. After *any* concurrent write, re-verify the artefact from
scratch (line count, duplicate rows, link count) instead of trusting either child's PASS.

Then **stay in the turn until the artefact exists** — the owner reads "dihantar" as unfinished
("kalau belum jalankan sampai siap"). Poll on the deliverable, not the clock:

```bash
for i in $(seq 1 100); do [ -f docs/LAPORAN-<job>.md ] && { echo "siap ${i}0s"; break; }; sleep 10; done
```

Full diagnosis → re-brief → verify → board recipe, including the dedupe tests:
`references/interrupted-delegation-recovery.md`.

## Build in waves, additive first

1. **Wave 1 — additive only**: `workspaces/<role>/`, Obsidian vault, `knowledge_base/`. No config
   edits, nothing rewritten, fully reversible. Three children in parallel, each with the 8-field brief,
   its own report path (`docs/LAPORAN-*.md`), and an explicit prohibition list (no `config.yaml`,
   `SOUL.md`, `memories/`, `skills/`, no package installs).
2. **Wave 2 — decisions first**: real per-role profiles (`~/.hermesNN` homes vs `profiles/<role>`),
   night GitHub backup (needs `gh auth` + a chosen repo), MCP. Each changes routing or touches
   credentials — put the choice to the owner as a numbered list, then dispatch.
3. **Verify every wave yourself** before the verdict; children's summaries are self-reports.

Folder trees, `AGENTS.md` write-scope wording, vault scheme, verification one-liners:
`references/team-layer-waves.md`.

## Verify like a lead, not a stenographer

```bash
find ~/.hermesNN/workspaces -type f | wc -l   # must equal the count the child claimed
find ~/vault -name '*.md' | wc -l
find ~/.hermesNN/knowledge_base -type f | wc -l
ls -la ~/.hermesNN/SOUL.md                    # mtime unchanged, as promised
```

Then spot-check content (`grep -n '^## ' file`) — a 166-line file can still omit the escalation table
the brief demanded. A stale claim elsewhere (e.g. `index.md` still saying a doc "tidak dijumpai" after
a later wave created it) is a real finding: report it, and fix it in the next wave by an agent.

**Broken-link checks need Obsidian semantics.** Bare `[[note-name]]` resolves anywhere in the vault, so
a checker that only looks beside the file reports false breakage, and `[[Alias]]` pointing at the
file's own alias is not a break either. Confirm the target exists anywhere in the vault, then say
"not broken" rather than "2 rosak".

**Existence ≠ uniqueness.** A checker that only asks "does this link resolve" happily returns
`47 pautan, 0 rosak` on an `index.md` that lists the same page twice and repeats one link inside a
single line — and a child will quote that as PASS. Always assert counts too: `grep -c '<slug>' file`
against the number the brief predicted, `wc -l` before/after, page total vs the `Jumlah halaman: N`
the file claims, and a "no link twice in one line" regex. Duplicates are the tell-tale of a
re-dispatched brief; fix them by re-briefing the child, and log it as P1 so the pattern is visible.

## Working with this owner (observed, non-negotiable)

- **Guide one step at a time and get approval before building.** "Pandu aku satu-satu, aku setuju
  baru kita bina" — ask exactly one question, wait, then the next. Dumping a 5-question form or
  building ahead of approval is read as ignoring the instruction.
- **They are the final button.** Search/recommend/draft is fine; committing an external action
  (sending an application, posting, paying) waits for an explicit yes.
- Plain Malay, no jargon, evidence in files (a `BACA-DULU.md` / `LAPORAN-BINA.md`), and a numbered
  3–4 option list at the end of each reply — they answer by number.
- **A reply that is only a number (e.g. `3.ya`) is a resume, not a question.** Because the option list
  lives in the *previous* session, recover it before acting: `session_search()` (browse) → newest
  session → `session_search(session_id=…)` → read the last assistant message and its numbered list.
  Then confirm in one line which option that is, dispatch it, and keep the same numbering authority.
  Never guess an option's meaning from the number alone, and never answer "which option do you mean?"
  before searching — the list is on disk in the session DB.
- **Partial selections are normal and keep their gaps.** `Jalankan 1,2,,4` (note the stray comma) means
  run 1, 2 and 4: read the digits, ignore the punctuation, and state on the board which numbers were
  skipped — `3 — tidak dijalankan, ikut arahan bos` — instead of quietly folding it in or silently
  dropping it. The owner checks the board against the list he gave.
- When the owner says "masuk bilik bos" / "jangan masuk campur", stop and persist state to a file
  (e.g. `SIMPAN-STATUS.md`: decisions locked, where we stopped, how to resume) before going quiet.
- **"Dihantar" is not "siap".** When they say *"kalau belum jalankan sampai siap"*, a dispatched
  child does not end the turn: poll on the deliverable file, verify it yourself, then report the
  board. An unfinished job left hanging from a previous session is *the* first thing to check when
  they say "tegur tugasan lepas apa yang belum selesai" — reconstruct it from disk mtimes plus the
  previous session's board, not from memory of the chat.

## Pitfalls

- **Don't store SOPs or status facts in `memories/`.** Every brief then has to restate them, and
  the same fact drifts into three versions. Write the page once in `knowledge_base/`, point the
  brief at the path.
- **Don't answer a "no agents are working" complaint with a roster count.** Count what is
  *assigned and running* (`/api/agency/runs`, active runs), not what is installed.
- **Don't silently do the work then describe it as delegation.** The owner checks the console.
- **Model choice is not the value.** A team's worth is its SOPs, workflows and accumulated context;
  swapping models rarely explains a bad result. Say this when asked "model mana paling bagus".
- **One giant profile doing everything mixes context and lowers accuracy** — split by job, not by
  tool.
