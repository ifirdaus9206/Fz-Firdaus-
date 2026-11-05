---
name: hermes-config-management
description: "Edit Hermes config.yaml safely - models, fallbacks, plugins; consolidate legacy homes."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows, termux]
metadata:
  hermes:
    tags: [hermes, config, models, fallback, providers, troubleshooting, clarify, gateway]
    related_skills: [hermes-agent]
---

# Hermes Config Management

How to change Hermes Agent's `config.yaml` safely, verify the change landed, and diagnose
model/provider failures. Use this whenever the task is "change the model", "add a fallback",
"why does Hermes keep timing out", "enable a plugin", or any edit to the Hermes home.

## Locate the live config first

Never assume `~/.hermes`. The profile directory name is whatever the install chose
(`~/.hermes`, `~/.hermes20`, …). Ask Hermes:

```bash
hermes config show        # ◆ Paths → Config / Secrets / Install
hermes config path        # just the config path
```

Use the path it prints for every subsequent command.

## The write guard — read this before editing

`write_file` and `patch` **refuse** to modify the Hermes config file:

```
Refusing to write to Hermes config file: .../config.yaml
Agent cannot modify security-sensitive configuration.
```

This is a deliberate guard, not a bug and not a permissions problem. Do not fight it, do not
try to route around it with `sed`. Use the two supported paths:

### Scalars → `hermes config set`

```bash
hermes config set model.default "deepseek/deepseek-v4.1-flash-1017"
hermes config get model.default
hermes config check          # validates the whole file
```

### Nested structures → python3 + PyYAML in terminal

`hermes config set` stringifies JSON, which is silently useless for keys that expect a real
list. `fallback_providers` is the classic case: its reader calls `_iter_fallback_entries()`
which accepts only `dict` or `list` and returns `[]` for a `str`. A JSON-in-a-quote value
writes fine and does nothing.

```bash
python3 - <<'PY'
import yaml
p = "/data/data/com.termux/files/home/.hermes20/config.yaml"   # from `hermes config show`
with open(p) as f:
    cfg = yaml.safe_load(f) or {}
cfg["fallback_providers"] = [
    {"provider": "openrouter", "model": "nvidia/nemotron-3-super-120b-a12b:free"},
    {"provider": "openrouter", "model": "openai/gpt-4o-mini"},
]
with open(p, "w") as f:
    yaml.safe_dump(cfg, f, sort_keys=False, default_flow_style=False)
print(open(p).read())
PY
```

Then confirm it reads back as a list, not a quoted blob:

```bash
hermes config get fallback_providers
# - provider: openrouter
#   model: nvidia/...
```

`hermes config edit` also exists but is interactive — avoid it in automated sessions.
`hermes config set` alone cannot express nested lists; that is why the YAML path is needed.

## Fallback chain schema

Top-level key, either a single mapping or a list of mappings:

```yaml
fallback_providers:
  - provider: openrouter
    model: openai/gpt-4o-mini
    # optional: base_url, api_key, key_env (name of env var holding the key)
```

Each entry needs non-empty `provider` and `model` or it is dropped. Legacy `fallback_model`
still works and is appended after `fallback_providers`. Entries are de-duplicated on
`(provider, model, base_url)`.

## File vs runtime — `config get` proves the file, not the process

`hermes config set` validates and writes. Gateways, cron workers, the desktop app and the
TUI read their config **at startup**, so a change can sit on disk with zero effect. The
tell for "I set it but nothing changed" is exactly that split: `config get` returns the new
value while behaviour is unchanged. Restart the reader, then verify behaviour from a log
line — never re-issue the `config set`.

```bash
hermes config set agent.clarify_timeout 180
sv restart hermes-gateway        # gateway/cron/desktop/TUI only pick it up here
```

Long-running readers to restart after touching `model.default`/`fallback_providers`,
`display.*`, `gateway.*`, `plugins.enabled`, `agent.*`, `auxiliary.*`.

### `agent.clarify_timeout` (default 3600 s) — the runaway-hang knob

`clarify` blocks the turn until answered or timed out; in the gateway it parks the whole
session, so later inbound messages queue and are never processed while every liveness
check still passes. Resolution order: legacy `clarify.timeout` → `agent.clarify_timeout` →
3600; `<= 0` waits forever.

```bash
hermes config set agent.clarify_timeout 180      # 3 min, then the turn unblocks
```

Detecting it from data (0 non-empty assistant rows, last row `finish_reason='tool_calls'`
with tool `clarify`) and the full recovery sequence:
`references/runtime-vs-file-config.md`.

## Diagnosing "API call failed after 3 retries: Upstream idle timeout exceeded"

This is a provider/model symptom, not a Hermes bug and not a network fault on the machine.

1. Read the configured default: `hermes config get model.default`.
2. Check for `:free` / `:beta` model ids. Free-tier upstreams on OpenRouter idle out regularly
   under long generations.
3. Fix by moving the default to a paid/stable model **and** adding a fallback chain, so one
   bad upstream degrades instead of failing the turn:

```bash
hermes config set model.default "deepseek/deepseek-v4.1-flash-1017"
# then the python3 YAML block above for fallback_providers
```

4. Smoke-test end to end — the config check alone does not prove the model answers:

```bash
hermes -z "Reply with exactly: OK"
```

`hermes -z "<prompt>"` is the one-shot non-interactive form. `hermes -p` does **not** exist and
is parsed as a subcommand, producing `invalid choice`.

Note that the in-session `/model` switch is ephemeral. If the user switched models and the
problem returns next session, the persisted `model.default` was never changed — that is the
tell.

## Safe edits to the Hermes home directory

Bulk copies into the Hermes profile clobber quietly:

```bash
cp -r ~/.oldprofile/* ~/.hermes20/     # overwrites SOUL.md and anything else matching
```

- Back up a file you generated **immediately** after generating it (`cp X X.bak`), before any
  other copy operation.
- Merge with `rsync -av --ignore-existing src/ dest/`, or test collisions first:
  `for f in src/*; do [ -e "dest/$(basename "$f")" ] && echo "COLLISION: $f"; done`
- After any write or copy, verify **content** not just size: `head -2`, `tail -3`, plus the byte
  count. A file that shrank is the only warning you get.
- Never "repair" a damaged registry/notes file by substituting a different document that merely
  has overlapping content. Regenerate the real one.

## Renaming an identity: persona, channel label, profile, bot

Four different "names" exist and they are not interchangeable. Change one and the others stay
put — so state which one the owner is actually looking at, or they wait for a screen change
that never comes.

| Name | Lives in | Visible where | Changed by |
|---|---|---|---|
| Persona self-name | `SOUL.md` (+ prose in `OPERASI.md`, `docs/*.md`) | agent's replies | editing the markdown |
| Home-channel label | `.env` `TELEGRAM_HOME_CHANNEL_NAME` | nothing on the phone — internal label | edit + `hermes gateway restart` |
| Profile id | `profiles/<id>/` + wrapper `~/.local/bin/<id>` | the CLI name | `hermes profile rename old new` |
| Telegram bot display name | BotFather | name above the chat | BotFather `/setname` — owner's own step |

- **Profile:** use `hermes profile rename`. A bare `mv` leaves `~/.local/bin/<old>` pointing at
  a profile that no longer exists — and that wrapper is extensionless, so a
  `grep --include=*.md --include=*.yaml` sweep never sees it. Ids are lowercased on disk
  (`Siti` → `siti`).
- **Bot:** Hermes has no `setMyName` call at all; it only reads identity for `@mention` routing.
  No config key, no API path. BotFather only, and no restart is needed afterwards.
- **Persona:** count real self-name hits, not string matches. `docs/KETUA.md` and
  `SOUL.md.bak-ketua-...` are paths — editing them breaks links. Where the old word is a job
  title in other docs, prefer leaving it (or one clarifying line) over a 30-site sweep.

When the owner asks to *see* changes before approving them, the deliverable is a read-only
review pack — byte-exact copies plus a line-level before/after plan — not a description of
one. Recipe, verification (`tail -n +4 copy | diff - original`) and the concurrent-edit
pitfall: `references/identity-renames.md`.

## Consolidating a legacy Hermes home into the live one

Same guard rails as above, at directory scale. Typical ask: "move my old `.AINA` / `.hermesN`
home into the current one". The risk here is not lost content, it is **overwritten content** —
a blanket `cp -r old/* live/` will replace a good `SOUL.md`, `config.yaml`, or skill with an
older stub. Order is always: **inventory → diff → selective copy → archive → hash gate → delete**.

```bash
du -sh .OLD .OLD/.nested .LIVE
find .OLD -type f -exec stat -c '%s %n' {} + | sort -k2 > /tmp/old_inventory.txt
diff -rq .OLD/profiles/x .LIVE/profiles/x     # empty output = skip that whole subtree
```

Classify every subtree into one of four buckets before copying anything:

| Bucket | Hermes examples | Action |
|--------|-----------------|--------|
| Identical duplicate | project dir already present (0 diff), same skill, `bin/tirith` binary | skip, record as "skipped, identical" |
| Unique & valuable | skills absent live, `pastes/`, `profiles/<proj>/`, `memories/` | merge into the correct category, not at the root |
| Regenerable | `models_dev_cache.json` (~6 MB), `cache/`, `provider_models_cache.json`, `ollama_cloud_models_cache.json` | archive under `_regenerable_cache/`, never merge |
| Stale / superseded | old `state.db*`, old `auth.json`, stub `SOUL.md`, `interrupt_debug.log`, `.update_check` | archive under `home-<name>/` |

Check secrets before any old `.env` is set aside — `sed 's/=.*/=***/' .OLD/.env` on both sides,
and carry over any key the live file lacks. State the outcome in the manifest.

Archive with a manifest instead of dumping at the root:

```
.LIVE/archive/legacy-<NAME>-<YYYY-MM-DD>/
├── README.md          ← source table, "merged → where", "skipped & why", secrets statement,
│                        layout tree, and the one-line command to delete it
├── home-<top>/        ← stale state/logs/sessions/memories
├── home-<nested>/     ← same for a home nested inside it
├── pastes/            ← user content, verbatim
└── _regenerable_cache/ ← renamed with a prefix so filenames don't collide
```

Then rewrite stale paths in the merged skills (`~/.hermes19` → the live home), confirm they
register with `skills_list(category=...)`, and only delete the source after
`scripts/verify_merge_completeness.py` reports **0 unaccounted files** (it indexes the
destination by `(filename, size)`, applies a rename map, and SHA256-compares renamed items).
Finish with a live round-trip — `hermes config check` plus `hermes -z "Reply with exactly: OK"` —
because removing a sibling home can still break the live one.

Full worked example, home-layout reference and manifest template: `references/hermes-home-consolidation.md`.

## Verification checklist

```bash
hermes config show                    # paths, model, keys all sane
hermes config get model.default       # the value you set
hermes config get fallback_providers  # a real list, not a quoted string
hermes config check                   # no validation errors
hermes -z "Reply with exactly: OK"    # live round-trip
```

For anything consumed by a long-running process (gateway, cron, desktop, TUI), add: restart
it, then read one log line proving the new value is in force.

## References

- `references/config-recipes.md` — copy-paste recipes: fallback chain, model swap, plugin enable,
  one-shot smoke tests.
- `references/hermes-home-consolidation.md` — worked legacy-home merge: what to merge vs archive vs
  drop, secrets check, manifest shape, stale-path rewrite, the unaccounted-file traps.
- `references/runtime-vs-file-config.md` — file-vs-runtime config: which keys need a process
  restart, the `agent.clarify_timeout` runaway-hang case, and how to prove a parked `clarify`
  turn from `state.db` instead of guessing from logs.
- `references/identity-renames.md` — persona / home-channel label / profile id / Telegram bot
  name: where each one actually lives, `hermes profile rename` and its wrapper trap, the
  byte-exact approval-pack recipe, and the "source file changed under me" pitfall.
- `scripts/verify_merge_completeness.py` — run before deleting a merged source. Indexes the
  destination by `(filename, size)`, SHA256-compares, applies `--rename` / `--allow`, and exits
  non-zero unless every source file is accounted for.
