---
name: hermes-home-provisioning
description: Provision extra Hermes homes; relocate assets safely.
version: 1.2.0
category: devops
metadata:
  hermes:
    tags: [hermes, hermes-home, provisioning, relocation, termux, soul-md, verification, cleanup, deletion-audit, gateway, telegram, clarify]
---

# Hermes Home Provisioning, Relocation & Retirement

Use when the user wants an additional `HERMES_HOME` (a "trading home", "research home",
a second profile-as-home), wants existing project trees relocated into / out of a
Hermes home, wants stale/leftover Hermes installs audited and cleaned up, or wants a
messaging channel wired into a home and kept alive.
Complements the version-isolation skills: those cover running different Hermes
*versions*; this covers making an extra home **actually functional**, moving large asset
trees between homes without breaking a running session, retiring what is no longer
needed without destroying data, and connecting the home to a messaging platform.

## Core Rule

A home is functional only when `HERMES_HOME=<path> hermes chat -q "..."` returns a real
model answer. `hermes doctor` passing is necessary but NOT proof — without `.env` +
`auth.json` the home boots happily and every API call fails.

## 1. Provision a second functional home (no TTY, no `hermes setup`)

`hermes setup` is an interactive prompt_toolkit wizard. Driving it from a tool call
hangs or corrupts state — do not pipe answers into it. Use sanctioned commands:

```bash
H=$HOME/.hermesNN; mkdir -p "$H"
cp <source-home>/.env <source-home>/auth.json "$H/"
chmod 600 "$H/.env" "$H/auth.json"

export HERMES_HOME="$H"
hermes config set model.default   <provider>/<model>
hermes config set model.provider  <provider>
hermes config set model.base_url  <api-url>
hermes config set model.api_mode  chat_completions
hermes config set agent.max_turns 150
```

`hermes config set` creates `config.yaml` for you (the file-edit guard blocks hand
writing `~/.hermes*/config.yaml` anyway). For nested lists such as `fallback_providers`,
set them with python3 + yaml — a JSON **string** is rejected by the loader, it needs a
real list of dicts:

```bash
~/.hermes_venvs/<venv>/bin/python - <<'PY'
import yaml
p="/home/<user>/.hermesNN/config.yaml"
d=yaml.safe_load(open(p))
d["fallback_providers"]=[{"provider":"openrouter","model":"openai/gpt-4o-mini"}]
d["display"]={"tool_progress":"all"}
d["_config_version"]=33
yaml.safe_dump(d, open(p,"w"), sort_keys=False)
PY
```

Then give it identity and capability, selectively:

```bash
cp -a <source-home>/skills/<category>/<skill> "$H/skills/<category>/"   # selective, not whole tree
# author $H/SOUL.md scoped to that home's purpose
HERMES_HOME=$H hermes skills list     # also initialises the Skills Hub dir
HERMES_HOME=$H hermes doctor
HERMES_HOME=$H hermes chat -q "state your SOUL.md rules in one line"   # real proof
```

A good second-home SOUL.md states: purpose/scope, domain parameter tables, hard limits,
workflow phases, data-provenance discipline, integration paths, report format, and
explicit prohibitions. Keep it under ~5 KB and terminal-readable.

## 2. Relocate a large tree into a Hermes home

Same filesystem → `mv` is an instant rename. Never `cp -a` + `rm` for 10–20 GB, and
never assume "move" needs a copy. Order matters because a live process and the launcher
symlink may sit *inside* the tree being moved:

1. **Inventory + size first.** `for d in *; do du -sh "$d"; done` — a bare
   `du -sh <huge-dir>` can blow a 180 s foreground timeout; loop per child or raise it.
2. **Find live references.** grep `config.yaml`, `profiles/*/config.yaml`, `cron/`,
   `skills/`, `SOUL.md` for the old absolute path before touching anything.
3. `mv <old> <new>`.
4. **Re-point the launcher.** `ln -sfn <new>/…/hermes $PREFIX/bin/hermes`, confirm with
   `readlink -f $PREFIX/bin/hermes`.
5. **Leave a compat symlink at the OLD path** if any session is running from that tree
   (`ln -sfn <new> <old>`). The interpreter's `sys.path` holds the absolute old path;
   without it, lazily-imported modules fail mid-session. Costs 0 bytes; drop after a
   full restart. Tell the user it is a link, not a duplicate.
6. **Verify:** `ls <new>`, `ls <old>/<known-file>` through the link, `hermes --version`.
7. **Sweep stale self-references inside the moved content:**
   `grep -rn "files/home/<old-name>" <new>` → patch docs that state their own location
   (persona.md, installation.md, agent_identity.md). Paths frozen into documentation rot
   silently and mislead later sessions.

## 3. Auditing a home for a class of asset

When the user says "check whether there is more X in that home", search by *content*,
not only by folder name — valuable assets hide in archives:

```bash
grep -rln "MetaTrader5\|XAUUSD\|MT5_BRIDGE" --include="*.py" --include="*.md" --include="*.json" .
find . -maxdepth 6 -type d \( -iname "*trad*" -o -iname "*mt5*" -o -iname "*backtest*" \) \
     -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "./cache/*"
```

Look inside `archive/` and nested `.hermes/skills/` copies too — archived homes are
where the oldest, most detailed skills survive. Also check `profiles/<name>/` before
declaring something "just a project": a folder there may be the only content of that
profile. Moving it out is fine once you confirm nothing (config, cron) points at it —
then remove the emptied profile dir.

Report findings as a table (path, size, file count), state explicitly whether you
**moved** or **copied** (archive originals should normally be copied, not destroyed),
and let the user decide about deleting originals.

## 4. Ambiguous destinations: stop and ask

Before moving anything into a path named by the user, prove the destination exists and
is the right *kind* of thing. `~/.hermesNN` may be: a real home, a Python venv
(`~/.hermes_venvs/hermesNN` — never store projects there), an empty stub dir, or an
archived legacy home under `archive/legacy-*`. Offer concrete options and let the user
pick; never guess and never silently create a second live home.

## 5. Reporting to the user

- Reply in the user's language (this user works in **Bahasa Melayu**) and in plain,
  terminal-readable text — no heavy markdown decoration on CLI.
- Evidence first: paste the real numbers you got back (sizes, file counts, `readlink -f`
  output, the model's actual answer). Never claim a move/setup succeeded without a
  verification command that you ran.
- Say **moved** vs **copied** explicitly for every asset, and flag anything left behind
  in an archive.
- Name the exact absolute paths touched, and list follow-up options (delete the compat
  symlink, add a shell alias, `hermes curator adopt`) as concrete choices.
- When a step is destructive or ambiguous, ask with concrete options before acting;
  this user wants exact compliance, not improvisation.
- Never label a directory "junk", "copy" or "leftover" in a report before opening it —
  see §10 for how badly that can go wrong.

## 6. Equipping the new home: filtered specialist roster (agency-agents-router)

A second home with only config + SOUL.md is a bare model. When the home has a domain
(trading, research, GIS), give it the agency specialists that domain actually needs —
**filtered**, not all 282. Recipe and probes: `references/filtered-agency-roster.md`.

```bash
# 1. copy the plugin skeleton, then replace its data/agents.json with a subset
mkdir -p $H/plugins/agency-agents-router/data
cp <src-home>/plugins/agency-agents-router/{__init__.py,plugin.yaml} $H/plugins/agency-agents-router/
# filter by source_path from the source catalog (keeps slug/name/body intact)

# 2. enable it — plugins.enabled is a nested list, so use python3 + yaml
#    (do NOT hand-edit config.yaml; hermes config set cannot build a list)

# 3. verify
HERMES_HOME=$H hermes plugins list          # -> agency-agents-router | enabled | user
HERMES_HOME=$H hermes chat -q "use agency_agents_search for 'risk' and list 3 finance agents"
```

The live call must show real slugs, not invented names — that is the only proof the
filtered roster loaded.

**Roster size comes from `data/agents.json`, never from the tool.** `agency_agents_search`
returns `{"count": N, "results": [...]}` where `count` is the number of *query hits*,
truncated by `limit` (default 8, max 25) — three queries against the same roster give
three different totals, and there is no list-all/size tool. So answer "how many agents"
with `len(json.load(open(.../data/agents.json)))` and say the number came from the file;
use the tool only for "which agent fits this task". Volunteering the source distinction
up front avoids the "kenapa bukan dari tool?" correction.

**Adding agents later — append, don't hand-write.** Build each new entry from the source
corpus with the tool's schema (`slug/name/description/division/color/emoji/vibe/
source_path/body`), load the current subset, `extend`, dump, then assert
`len == old + new`, unique slugs, every `body` non-empty. Slugs derive from the filename
minus the `<division>-` prefix, which sometimes differs from the catalog form
(`fpa-analyst` vs `fp-a-analyst`, `model-qa` vs `model-qa-specialist`).
**Copy slugs out of the built JSON into SOUL.md; never type them from memory** — and
update the roster count in the SOUL.md heading in the same edit, or doc and data drift.

## 7. Keeping the home root clean (standing user requirement)

This user's rule: **all work lives inside a Hermes home** — never in `~` and never outside
both homes. New files/folders go into the relevant home following whatever structure that
asset already has; if a genuinely new location is needed, **say so and ask first** rather
than creating it in the home root. Apply this to every future task without being reminded.

When auditing `~`, classify instead of moving blindly, and present the classification:

| Class | Examples | Action |
|---|---|---|
| Termux essentials — leave | `.bashrc/.bash_profile`, `.cache/.cargo/.cpan/.local/.npm`, `.config/.termux/.gnupg/.w3m`, `.hermes_venvs` (launcher runtime), `storage`/`phone` symlinks, `termux-key`, `termux-ohmyzsh`, `buildAPKs` | never move; say why |
| Movable work | project trees, downloads/ZIPs, test-history JSON, one-off scripts, logs, venvs, tool bundles | move to owning home, confirm count/size |
| Compat symlink | old tree path kept for a live process | keep until full restart, then offer removal |

Make a second home convenient by putting its wrapper on `PATH`: script
`~/.hermes20/bin/hermes19` calling `HERMES_HOME=$HOME/.hermes19 hermes`, then check
`command -v hermes19`. A `~/bin` directory is often **not** on Termux `PATH` — verify with
`echo $PATH` before trusting the wrapper to resolve.

## 8. Consolidating a mega-tree into an existing repo — audit, then ask

When the instruction is "move everything from <huge tree> into <existing repo> — check
first, and if there is a problem tell me, otherwise go ahead", the audit IS the
deliverable when blockers exist. Six blocker classes reliably appear (launcher target
inside the tree, destination is a clean git repo, name collisions, nested `.hermes`
homes in archives, duplicate runtime trees, 1000× size ratio). Commands, taxonomy,
a repo-safe `_workspace/` + `_archive/` layout and the accepted report shape:
`references/consolidation-preflight.md`.

Rule: never answer a conditional instruction with "I found problems, and moved it
anyway". Report, propose the layout, list what will NOT move, and ask the A/B/C
questions.

## 9. Explaining "which SOUL.md / profiles are you actually reading?"

After a second home exists the user will ask this, usually phrased as "ada dua SOUL.md,
yang mana kau baca?". Answer with the single rule and the evidence, not with prose:

```bash
echo "HERMES_HOME=${HERMES_HOME:-<unset>}"      # which home this session uses
readlink -f $PREFIX/bin/hermes                  # launcher -> real source tree
ls -la $HERMES_HOME/SOUL.md                     # the file actually loaded
ls -la $HOME/.hermesNN/SOUL.md                  # the other home's (not loaded here)
ls -la $HERMES_HOME/profiles                    # empty = no third layer
```

Phrase it as: **Hermes reads `$HERMES_HOME/SOUL.md`** — `hermes` → main home's SOUL,
`hermes19` (or `HERMES_HOME=... hermes`) → that home's SOUL. Two files = two homes, not two
versions of one file. An empty `profiles/` dir means there is no third layer; say so
explicitly, because the folder's presence makes users think a profile is active.

The same trick answers "kenapa fail X masih ada di luar?": check `ls -ld` + `stat -c '%F %s'`.
A 62-byte `symbolic link` pointing inward is not a copy of an 18GB tree — prove it with the
inode (`stat -c '%i' <link>/README.md <home>/X/README.md` → identical), and only then offer
removal once `/proc/<pid>/maps` shows no live reference (see `filesystem-tree-relocation`).

## 10. Retiring leftovers — audit before you delete anything

Trigger: "berapa hermes yang ada dalam ini", "buang sisa tak berfungsi", or
*"analisis dulu sebelum padam — kalau tak ada yang bahaya, padam"*.
Full playbook + this session's case numbers: `references/retiring-stale-hermes-installs.md`.

1. **Enumerate the class, not a folder.** `which -a hermes`,
   `readlink -f $PREFIX/bin/hermes`, `ls -d ~/.hermes* ~/.hermes_venvs/*`, then
   `--version` per home. Bucket each hit: live home / stale source clone / unusable
   venv / broken wrapper / archived home.
2. **Never classify by directory name.** `hermes-source-old`, `config/hermes-state-ref/`
   and `archive/.../root-cleanup/.hermes` can all be COMPLETE homes. Probe for
   `state.db`, `sessions/`, `memories/`, `cron/`, `skills/`, `.env`, `auth.json` before
   the word "copy" appears in the report. Two such "source copies" here held 86 and 63
   sessions (149 total) — the only copy of that history on the device.
3. **Git clones:** `git -C <d> log -1`, `status --porcelain` (includes untracked),
   `stash list`, `remote -v`. Clean tree + same HEAD as the live source + upstream
   remote = rebuildable, safe. Only ignored `__pycache__`/`*.egg-info` → also safe.
4. **Venvs:** `pyvenv.cfg`'s `command=` shows where it was created from; `bin/` may
   hold only `pip` (no `hermes`) — a stub, not an install.
5. **Reference sweep before deleting:** grep `config.yaml`, `bin/` wrappers, `scripts/`,
   `cron/`, `plugins/`, `skills/`; scan symlinks with `readlink -f`; `ps -ef`.
   Sanity-check the probe itself — a typo'd loop variable prints empty results that
   read exactly like "no references".
6. **Prove state uniqueness read-only:** `sqlite3.connect("file:...?mode=ro", uri=True)`
   → `count(*) from sessions/messages`. 86 vs 7 in another archive = not a duplicate.
7. **The size split decides the action.** Bundled `hermes-agent/` is 530–760 MB; real
   history is 50–80 MB. Strip `hermes-agent/ lsp/ bin/ logs/ checkpoints/ cache/`, keep
   `state.db* sessions/ memories/ cron/ skills/ config.yaml SOUL.md` → ~95% of the bulk
   gone, nothing lost (920→85 MB, 636→41 MB here).
8. **Delete only the provably safe set; hold anything containing `sessions`.** Report
   held items with the reason, offer lettered options (strip / strip+credentials / keep
   all / delete all) with exact GB, and note that archived `.env`/`auth.json` are
   plaintext credentials the user may want to rotate — never quietly delete those.
9. **If the clarify prompt times out, take the least destructive option that still
   answers the ask** (strip code, keep history, leave credentials) and say what was held.
10. **Verify and show it:** `pragma integrity_check` = ok, session/message counts
    unchanged, `--version` for every surviving install, `df` before/after for the space.

## 11. Connecting a messaging channel (Telegram) and keeping it alive

Trigger: "sambungkan hermes ke telegram", "hantar saya 'hai' dalam telegram", or the bot
going quiet later. Full playbook (token recovery without echoing it, env/config contract,
`agent.clarify_timeout`, runit service on Termux, `hermes send` proof, silence post-mortem
and the red-herring log lines): `references/gateway-telegram-channel.md`.

Order of operations that worked: recover token from an archived `.env` → `getMe` →
append creds to the active home's `.env` → install the SDK into the venv named by the
launcher shebang → `hermes gateway run` → watch `logs/gateway.log` for
`✓ telegram connected` → prove with `hermes send -t telegram ... --json` (returns
`message_id`) → convert to a runit service so it survives the session. Then ask the user
to reply: only the inbound round-trip proves two-way operation.

## Pitfalls

- **`hermes tools` needs a TTY.** Piped/`-c` invocations fail with
  `Error: 'hermes tools' requires an interactive terminal`. Use `hermes plugins list`,
  `hermes skills list`, or `hermes doctor` as the non-interactive verification surface.
- **Do not assume a bundled app corpus equals the installed plugin catalog.** Compare
  before regenerating: path layouts drift (e.g. a flattened `game-development/<agent>.md`
  in the app vs `game-development/unity/<agent>.md` in the repo) and bodies differ by
  version. Back up `data/agents.json` to `agents.json.bak-<date>` before any rewrite, and
  verify entry count + unique slugs + non-empty `body` afterwards.
- Copying only `config.yaml` into a new home → home boots, every call 401s. Copy
  `.env` + `auth.json` too.
- Writing `fallback_providers` as a JSON string → loader error (`get_fallback_chain`
  accepts dict/list only). Use python3 + yaml.
- Moving a tree out from under the running launcher without re-pointing
  `$PREFIX/bin/hermes` and without the compat symlink → `ModuleNotFoundError` mid-session.
- Trusting `hermes doctor` as the acceptance test. Always finish with `hermes chat -q`.
- Deleting archive originals after "moving" skills out of them. Copy archive content;
  move only active assets.
- Assuming two `~/.hermesNN` dirs are interchangeable — verify what
  `$PREFIX/bin/hermes` and `HERMES_HOME` actually resolve to before acting.
- Moving a Python venv and stopping at "it's on the new path" — `pyvenv.cfg`, `bin/pip*`
  and `bin/activate*` still exec the old absolute path. Rewrite them and prove with
  `./bin/pip -V` (see `filesystem-tree-relocation` Phase 5).
- Quoting a roster/asset count from a search tool's `count` field. That is query hits
  capped by `limit`; count the data file and name the source in the report.
- **`pkill -f <script>.py` kills the shell that runs it.** The pkill command line itself
  contains the pattern, so the tool call dies with exit `-15` and the follow-on `rm -rf`
  never runs. Use a bracket pattern: `pkill -f '[t]ranslate_agency_ms'`, then re-check
  with `pgrep -fc '[t]ranslate_agency_ms'` before deleting partial output.
- **Bulk-translating agent/prompt content without asking.** This user cancelled a
  282-file Malay pass: personas stay English so the agents parse their own instructions;
  a translated mirror is for human reading only. Ask first, and keep any mirror in a
  separate tree rather than overwriting the catalog the plugin loads.
- Verifying a served page by asserting it "should work". Start the server in background,
  then `curl -s -o /dev/null -w "%{http_code} %{size_download}b\n"` each route; 200 + a
  byte count is proof, and `ss`/`netstat` are frequently missing on Termux.
- **Hunting an old page by folder name only.** "activate my old login html" means search by
  content: `grep -rl 'type="password"' --include="*.html" .` across both homes (skip
  `node_modules`, `venv`, `.venv`), then confirm it is the user's own page rather than a
  vendor template (code-server ships its own `login.html`). Serve it with
  `python3 -m http.server 8080 --bind 127.0.0.1` from that page's directory and curl each
  route. Say plainly when the form is a static demo (`onsubmit -> alert(...)`, no auth
  check) — presenting it as a working login is a false claim.
- **Declaring a folder "junk" from its name, then acting on it.** Two dirs named
  `hermes-source-old` and `hermes-state-ref` looked like duplicate code but were archived
  homes with 149 sessions. Open first, classify second, report third — never the reverse.
- **Running recursive deletes through a sandboxed helper.** The approve/deny path lives on
  the foreground `terminal` tool; a helper call comes back as a refusal-shaped object
  without the usual `output` key (so `r["output"]` raises `KeyError: 'output'` — print
  `repr(r)` to see it). Issue `rm -rf` from the foreground terminal so approval runs and
  the result is reported, then verify with `df` and a `--version` check.
- **Accepting "the bot is alive" as the answer to "kenapa tak balas mesej".** A live
  gateway process, `✓ telegram connected` and a valid token coexist with total silence
  when a turn is parked inside the `clarify` tool: later inbound messages queue forever
  (default `agent.clarify_timeout` = 3600 s). Diagnose from the log timeline plus the
  session's own rows in `state.db` (empty assistant content + `finish_reason='tool_calls'`
  + tool `clarify`), then `sv restart` and lower the timeout — see
  `references/gateway-telegram-channel.md` §8.
- **Blaming the noisy optional subsystems in `errors.log`.** `ModuleNotFoundError:
  nemo_relay`, `tirith ... exit code -6`, `check_*_requirements returned False` and the
  auxiliary "PAID lane engaged" warning do not stop replies. Report them as cleanup
  candidates, not causes.

## References

- `references/second-home-verified-run.md` — the exact command sequence validated in a
  Termux session (trading home + relocation of project trees), including the
  launcher/compat-symlink dance and the verification output shape.
- `references/filtered-agency-roster.md` — install a 17-of-282 agency-agents-router
  roster into a second home, enable it via yaml, prove it with a live tool call, and
  rebuild a catalog from an agency-agents-app `corpus-baseline` (drift check + backup).
- `references/consolidation-preflight.md` — audit a 10–20 GB tree before merging it into
  an existing git repo: six blocker classes, `_workspace/`+`_archive/` layout, the report
  shape the user accepted, plus the pkill self-kill and static-server verification notes.
- `references/retiring-stale-hermes-installs.md` — audit stale installs / archived homes
  before deletion: classification table, git/venv/state probes, the strip-don't-delete
  size split, and the verification output a deletion report must show.
- `references/gateway-telegram-channel.md` — wire a bot-token channel (Telegram) into a
  home: token recovery from an archived `.env` without echoing it, the env/config
  contract, SDK-into-launcher-venv, runit persistence on Termux, `hermes send` as proof,
  and the "bot silent while the gateway is alive" diagnosis (turn parked inside
  `clarify`, timeout default 3600 s, restart then re-ask).

## Named profiles

`hermes profile create <name>` is the third kind of home: `profiles/<name>/` with its own
SOUL.md, keys, skills and a wrapper at `~/.local/bin/<name>`. Steps, verification and the
scoped identity-rename recipe: `references/named-profile-provisioning.md`.

### Multi-agent roster (rename + N role profiles)

When the ask is "rename profile X to Y and create N runnable agent profiles", treat it as
one home with N sibling profiles — not N homes. Order that passed review:

1. `hermes profile rename --help`, then `hermes profile rename <old> <new>`. Verify all
   three surfaces: `hermes profile list`, `ls -1 profiles/`, and `command -v <old>` must be
   empty while `command -v <new>` resolves. The rename does **not** rewrite SOUL.md — patch
   only the 3–4 identity lines and assert `grep -c -i <old> SOUL.md` → 0 with the line count
   unchanged.
2. `hermes profile create <name>` per profile, then ONE python pass that copies
   `.env` + `auth.json` + `config.yaml`, `chmod 600` the first two, and drops `plugins` from
   the copied config. Expected surviving key set: 7 keys
   (`_config_version, agent, display, fallback_providers, model, onboarding, session_reset`).
3. Generate role SOULs from a single template dict: identity, 6-item scope, explicit "what
   this agent does NOT do", workspace path, evidence rules (no invented numbers,
   SIAP/JALAN/GAGAL/BLOK), prohibitions, home map, report format. 100–110 lines each.
4. Prove globally: `profile list` (default ◆ + renamed + N roles), `wc -l */SOUL.md`,
   `--version` per wrapper, ONE `chat -q` (not N), and unchanged mtimes on the parent
   `SOUL.md` / `config.yaml`.

Full command sequence, template skeleton and the run's pitfalls (no `/tmp` for helpers,
strip `read_file` line numbers, one chat test only):
`references/named-profile-provisioning.md` §6.

## Related Skills

- `hermes-agent` (bundled) — core Hermes usage, config keys, provider setup.
- `hermes-version-management` / `hermes-version-isolation` (user-owned) — running
  different Hermes *versions* in parallel; read them for venv layout on Termux.
