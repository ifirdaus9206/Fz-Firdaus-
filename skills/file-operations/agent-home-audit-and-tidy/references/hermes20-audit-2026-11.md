# Measured audit — `~/.hermes20` (Termux, 2026-11)

Snapshot taken before any tidying. Keep these numbers as the comparison baseline for a repeat run
so the next session skips a multi-minute scan and can quote real deltas.

## Headline

```
du -sh ~/.hermes20   →   17G
files               →   215,476 in archive/ alone
```

## Per-folder (size · file count · class)

| Size | Folder | Files | Class | What it was |
|---|---|---|---|---|
| 8.7 G | `archive/` | 215,476 | SNAPSHOT | `ultimate-2026-10` 7.7 G, `code-server-2026-10` 939 M, three `legacy-*` trees |
| 5.5 G | `tools/` | 111,206 | LIVE + DUPLICATE | `hermes-source` 2.8 G (live engine) + `others` 2.8 G (vendored repos) |
| 2.1 G | `legacy-ultimate/` | 121,637 | SNAPSHOT | old project: projects 1.8 G, tests 130 M, src 108 M |
| 125 M | `agency-agents-app/` | 10,198 | LIVE | app + `node_modules` |
| 121 M | `profiles/` | 4,403 | LIVE (duplicated) | 7 profiles × 71 skill files, md5-identical to `skills/` |
| 75 M | `state.db` | 1 | LIVE | main DB |
| 64 M | `lsp/` | 7,818 | LIVE | language server |
| 56 M | `state.db.bak-pra-migrasi-1328` | 1 | SNAPSHOT | pre-migration DB dump |
| 33 M | `bin/` | 3 | LIVE | 3 large binaries |
| 26 M | `logs/` | 80 | LIVE | 6.6 M web-server, 5.1 M agent.log.1, 4.4 M agent.log |
| 25 M | `skills/` | 909 | LIVE | 114 `SKILL.md` in 30 categories |
| 25 M | `plugins/` | 9 | LIVE | agency-agents-router + 5 `agents.json.bak` |
| 24 M | `.git/` | 143 | LIVE | backup repo |
| 16 M | `agency-agents/` | 422 | LIVE | 329 `.md`, 21 divisions |
| 13 M | `sandboxes/` | 885 | LIVE | venv |
| 3.6 M | `sessions/` · 2.6 M `cron/` · 1.5 M `cache/` | small | LIVE | runtime |

## Largest single files

```
1079 MB  tools/hermes-source/hermes-agent/.git/objects/pack/pack-eca3….pack
 609 MB  tools/hermes-source/.git/objects/pack/pack-2158….pack
 546 MB  tools/others/cline-repo/.git/…/pack-ae95….pack      ← same hash as cline-install
 546 MB  tools/others/cline-install/.git/…/pack-ae95….pack   ← duplicate
 116 MB  archive/ultimate-2026-10/root-cleanup/.local/lib/code-server/lib/node
```

`git gc --prune=now` on the two `hermes-source` repos is the cheapest several-hundred-MB win that
touches nothing live.

## Confirmed duplicates

| A | B | Evidence |
|---|---|---|
| `tools/others/cline-repo` 702 M | `tools/others/cline-install` 628 M | identical `.git` pack name `pack-ae95f9ee…` |
| `tools/others/bun-repo` 316 M | `tools/others/bun-install` 316 M | identical size |
| `tools/others/openhands-main` 18 M | `tools/others/OpenHands-main` 18 M | identical size, case-only name difference |
| `skills/<div>/<skill>/SKILL.md` | `profiles/*/skills/<div>/<skill>/SKILL.md` (7×) | `md5sum` equal, e.g. `4e2d80126124eac4455ec1673bd26dad` |

Vendor duplicate ≈ 1.3 GB. Profile copies ≈ 100 MB; symlink dedupe is possible but each profile
needs the files, so it stays a proposed decision, not an action.

## Zero-byte and near-zero files — triage result

```
find . -type f -empty … | wc -l        → 254
find . -type d -empty … | wc -l        → 115
```

| Kind | Examples | Verdict |
|---|---|---|
| Locks | `cron/.tick.lock`, `cron/.jobs.lock`, `memories/*.md.lock`, `skills/.usage.json.lock`, `auth.lock`, `kanban.db.init.lock` | leave |
| Python markers | `*/__init__.py`, `*.py.typed` (in `sandboxes/venv`) | leave |
| svlogd | `logs/<svc>/lock`, `logs/<svc>/current` | leave |
| State markers | `.wake_held`, `.uim_sync_state`, `.gw_alert_stamp`, `wake_lock.enabled` | leave |
| Real debris | `logs/hermes-dashboard/`, `logs/hermes-dash-tunnel/` (services retired) | safe to remove |
| Real stubs | `README.md` 39 B; `bin/hermes19` pointing at deleted `~/.hermes19` | rebuild |

## Repair done in that pass

- `README.md` 39 B → 2.5 KB landing page (folder map, services+ports, console URL, memory layout,
  backup policy, "no secrets here").
- `bin/hermes19` → shim with stderr warning, forwards to `HERMES_HOME=~/.hermes20`.
- `backups/` created: 4 `SOUL.md*` copies, 3 `config.yaml.bak*`, `state.db.bak-pra-migrasi-1328`,
  2 script `.bak`, 5 `agents.json.bak` → 77 MB out of the root and out of `plugins/`.
- `docs/arkib/` created for 7 evidence reports + 1 incident note; `docs/README.md` index added.
- `system/README.md` index added for the 8 prompt modules.
- `scripts/` validated: 35 files, `bash -n` / `py_compile` → 0 broken; `__pycache__` removed.
- `skills/` validated: 114/114 have frontmatter with `name` + `description`, 0 empty.

## Commands that produced the numbers

```bash
du -sh . ; du -sh --exclude=venv * .[!.]* | sort -hr | head -40
find . -type f -size +100M -not -path './.git/*' -printf '%s %p\n' | sort -nr | head -15
find . -type f -empty -not -path './.git/*' | wc -l
find . -type d -empty -not -path './.git/*' | wc -l
find tools/others -name '*.pack' -printf '%s %f %h\n' | sort -nr | head
md5sum skills/software-development/plan/SKILL.md profiles/*/skills/software-development/plan/SKILL.md
df -h /data /storage/emulated/0
```

## Transfer lesson

`mv archive/ultimate-2026-10 archive/code-server-2026-10 /sdcard/Documents/UIM/arkib-h20/`
(8.7 GB, FUSE) ran **>35 minutes** in the background; `du -sh archive` inside the same command hit
`exit 124` while it copied. Run the move with
`terminal(background=true, notify_on_complete=true)` and verify both sides afterwards
(`du -sh <source> <dest>`) instead of polling with `du` mid-copy.
