---
name: agent-home-audit-and-tidy
description: Audit a bloated agent home; tidy before deleting.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, termux]
metadata:
  hermes:
    tags: [housekeeping, disk-space, inventory, dedupe, termux, plan-first]
    related_skills: [filesystem-tree-relocation, hermes-home-provisioning, safe-git-config-backup, termux-runit-services]
---

# Agent home audit & tidy

Class of task: *"this home directory has grown to tens of gigabytes and hundreds of thousands of
files — sit down with it, read what is there, rebuild what is broken, put it in order, and only
then remove what is truly dead."*

Applies to `~/.hermes20`, `~/.hermes*`, dotfile repos, agent homes, project monorepos that have
accumulated snapshots and vendored copies.

## Hard rule from this owner

> "Jangan buat apa-apa — bina /plan dulu … kita perlu rancang, susun baru, kita mula kerja."

Sequence is **plan → approve → organise → verify → delete last**, never "clean up" as the first
move:

1. Read-only inventory first (no `mv`, no `rm`, no `rmdir`).
2. Write the plan to `.hermes/plans/YYYY-MM-DD_HHMMSS-<slug>.md` (see `plan` skill) with the
   inventory table, the target structure, bite-sized tasks, and the open decisions that need the
   owner's answer.
3. Wait for approval. Then do one task per message and re-verify services after each one.
4. **Organise before deleting.** Move to `backups/`, `docs/arkib/`, or external storage first; a
   path only gets `rm` after the owner confirms it is unused *and* something else proves it is
   reproducible.

Deleting first and explaining later destroys the only copy of a decision.

## Inventory pass (read-only)

```bash
cd ~/.hermes20
du -sh .                                    # headline number
du -sh --exclude=venv * .[!.]* 2>/dev/null | sort -hr | head -40
for d in */ .[!.]*/; do
  printf "%-24s %7s %7s fail\n" "$d" "$(du -sh "$d" 2>/dev/null | cut -f1)" \
                                 "$(find "$d" -type f 2>/dev/null | wc -l)"
done | sort -k2 -hr | head -32
find . -type f -size +100M -not -path './.git/*' -printf '%s %p\n' | sort -nr | head -15
```

`du -sh *` is not enough: a 17 GB home was 8.7 GB in `archive/`, 5.5 GB in `tools/`, 2.1 GB in a
`legacy-*` tree — three folders, no mystery.

## Classify each top-level entry

| Class | Test | Action |
|---|---|---|
| **LIVE** | Hermes/service reads it by fixed path (`skills/`, `plugins/`, `sessions/`, `cron/`, `memories/`, `state.db`, `config.yaml`, `SOUL.md`, `scripts/`, `knowledge_base/`, `workspaces/`, `system/`, `secrets/`) | never move |
| **SNAPSHOT** | `archive/<name>-YYYY-MM`, `legacy-*`, `*-backup-*` | move to external storage first |
| **DUPLICATE** | same md5 / same git pack hash / identical dir size | keep one, defer the rest |
| **DERIVED** | `node_modules/`, `__pycache__/`, `venv/`, `.pyc`, `*.tar.gz` | safe to remove, regenerable |
| **STUB** | file < 200 B holding a title only, or a wrapper pointing at a deleted path | **rebuild it** |
| **NOISE** | `*.lock`, `.wake_held`, `.stamp`, empty `__init__.py`, `py.typed` | leave alone (see pitfall 1) |

### Finding duplicates that actually matter

```bash
# vendored repos: identical git pack name = identical history
find tools/others -name '*.pack' -printf '%s %f %h\n' | sort -nr | head
# profile copies of the shared skill set
md5sum skills/software-development/plan/SKILL.md \
       profiles/*/skills/software-development/plan/SKILL.md 2>/dev/null
```

Measured: `cline-repo`/`cline-install`, `bun-repo`/`bun-install`, `openhands-main`/`OpenHands-main`
were byte-identical trees (~1.3 GB of waste), and all 7 profiles carried a 71-file copy of the
default `skills/` (121 MB). Profile copies are **not** junk — each profile needs them — so symlink
dedupe is a *decision to offer*, not an action to take.

### Finding stubs (what "banyak fail kosong" usually means)

```bash
find . -maxdepth 2 -type f -size -200c -not -name '*.lock' \
     -not -path './.git/*' -not -path './logs/*' -not -path './cache/*' \
     -not -path './sessions/*' -not -path './sandboxes/*' -not -path './tools/*' \
| while read f; do printf '%5s  %s\n' "$(stat -c%s "$f")" "$f"; done
```

Real hits from one home: `README.md` at 39 bytes (repo landing page = one line), and a
`bin/hermes19` wrapper still pointing at a deleted `~/.hermes19`. Both got rebuilt, not deleted.

## Stub repair patterns

- **Repo README** — rebuild as a real landing page: purpose, folder map, services table, ports,
  how to check health, backup policy, and an explicit "no keys, no tokens, no databases here" line.
  It is the first thing a human sees, so it is worth more than a title.
- **Wrapper pointing at a deleted home** — do not silently delete it (the owner may still type it).
  Turn it into a shim that warns and forwards to the live home:
  `exec env HERMES_HOME="$HOME/.hermes20" hermes "$@"` plus a one-line `⚠ <old> dipadam` on stderr.
- **Folder index** — when a folder has 8+ docs/modules, add `README.md` with a table
  (file · purpose · when to read it) and per-folder rules ("evidence reports move to `arkib/` after
  30 days").

## Organise in place (no deletion)

```bash
mkdir -p backups
mv SOUL.md.bak* config.yaml.bak* state.db.bak-* backups/     # root stops looking cluttered
mkdir -p docs/arkib && mv docs/LAPORAN-*.md docs/INSIDEN-*.md docs/arkib/
mv plugins/*/data/*.bak* backups/plugins/ 2>/dev/null
rm -rf scripts/__pycache__ plugins/*/__pycache__            # regenerable
```

Keep a `README-SUSUNAN.md` (or `docs/README.md`) that names every folder's job and every path
that must never be moved. The next session needs the map more than it needs the space.

## Verify after every organising step

```bash
hermes-status                                   # every service HIDUP, console 200
python3 -c "import ast,glob;[ast.parse(open(f).read()) for f in glob.glob('app.py')]"
for f in scripts/*.sh; do bash -n "$f" || echo "ROSAK $f"; done
```

Then prove it in the reply with raw output — "dah susun" without a status block is a claim.

## Pitfalls

1. **Zero-byte files are usually not damage.** 254 empty files in one home were `.lock` files,
   `__init__.py`, `py.typed` and svlogd `lock`/`current` markers. "Fill every empty file" would have
   corrupted the runtime. Triage by name before touching: `*.lock`, `auth.lock`, `*.db-wal`,
   `__init__.py`, `py.typed`, `logs/*/lock` → leave.
2. **Empty directories are usually caches.** `cache/{documents,audio,videos,screenshots,vision}`,
   `image_cache/`, `audio_cache/`, `profiles/*/{memories,sessions,skins}` exist to be filled at
   runtime. Only `logs/<retired-service>/` and `ULTIMATE_AI_PROJECT/`-style leftovers are real
   debris.
3. **`mv` across filesystems on Android/FUSE is slow, and `du` during the copy hangs.** Measured:
   8.7 GB to `/sdcard` took >35 minutes, and any `du -sh` on the source timed out while it ran
   (`exit 124`). Run it as `terminal(background=true, notify_on_complete=true)`, and never `du` the
   source in the same command. Do not kill a cross-FS `mv` mid-flight — it deletes source files as
   it goes, so a kill can leave both sides partial.
4. **`du` on a 200k-file tree can exceed a 180 s foreground timeout** — raise the timeout or scope
   the path (`du -sh archive/*` instead of `du -sh archive`).
5. **Never move a LIVE path to make the tree "look tidy".** `skills/`, `plugins/`, `state.db`,
   `sessions/`, `cron/`, `memories/` are resolved by absolute convention; relocating them silently
   breaks the agent. Tidy around them, not through them.
6. **A cleanup that leaves services down is a failure.** Re-run `hermes-status` after every task;
   a tidy home with a dead console is worse than a messy one.

## References

- `references/hermes20-audit-2026-11.md` — measured inventory of a 17 GB / 215k-file Termux agent
  home: per-folder sizes, the three duplicate vendors, the 7×71 profile copies, the stub list, and
  the exact commands that produced each number.
