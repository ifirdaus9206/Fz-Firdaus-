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

## Phased execution — "buat fasa 1 sampai siap"

Owner's instruction that set the shape of this whole class of work:

> "buat fasa-berfasa 1 sampai siap … **aku nak tahu kau baca fail mana untuk aku semak** …
> fasa satu: fail bina tambah isi, buat cadangan untuk lebih advance kita perlu tambah fail ini
> … selepas semak ke seluruh fail ini perlu di padam baru mula."

Rules that follow from it:

- **One phase = one coherent subtree**, and the phase order goes from documents inward:
  1. root files + `docs/` + `system/` + `knowledge_base/`
  2. `scripts/`
  3. `tools/` (+ duplicate vendors)
  4. `logs/`, `cache/`, `sessions/`
  5. `profiles/`
  6. deletion (only after every phase report has been read)
- **Every phase ends with a written report** at `docs/LAPORAN-FASA-<N>.md` containing, in this order:
  a table of **every file read** (path · size · status), what was added or rebuilt, what was moved
  (organised, not deleted), *advanced suggestions* — new files that should exist and why — and an
  explicit "belum disentuh" list. The owner audits the **file list**, so a phase that cannot name
  what it read is not finished.
- **No deletions inside a phase.** Deletion is its own final phase, after the owner has read the
  reports. Say this out loud in the report ("tiada fail dipadam dalam fasa ini").
- **Close each phase with 3–4 copy-paste spot-check commands** (`ls docs/`, `ls system/`,
  `head -30 README.md`) and wait for "sahkan" before starting the next phase.
- Phase scope is decided *before* typing: state which folders are in and out, or the owner will
  assume "semua fail" and ask why `tools/` was skipped.

Full command set, the phase-report skeleton and the doc baseline the owner accepted:
`references/phased-documentation-pass.md`.

## Documentation baseline worth producing in Phase 1

When a home has manuals but no map, these seven files ended the owner's "fail becelaru" complaint.
Produce them as part of the phase, not as an afterthought:

| File | Answers |
|---|---|
| `README.md` (root) | what this repo/home *is* — folder map, services, ports, backup policy, "no keys here" |
| `docs/README.md` | index: which manual to read when |
| `docs/ARKITEKTUR.md` | one diagram: inbound → brain → capability → workers → memory → control → storage |
| `docs/SERVIS.md` | every service: function, port, log path, `sv` verbs, recovery procedure |
| `docs/SUSUNAN.md` | folder map split into LIVE / SUPPORT / DEAD + "never move these" |
| `docs/RUNBOOK-INSIDEN.md` | symptom → check → cause → action table (16 rows earned their place) |
| `docs/API-KONSOL.md` | every route, grouped, with CSRF/auth note and one `curl` example |
| `AGENTS.md` (root) | rules for the next agent: forbidden folders, secret bans, conventions, reporting style |

`docs/SKRIP.md` (phase 2) does the same for scripts: **AUTO-cron · AUTO-service · MANUAL · SEKALI**.

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
were byte-identical trees (~1.3 GB of waste).

**Profile `skills/` copies are a different verdict — check before calling them duplicates.** They
are not junk (each profile needs its own tree), and on this home they were **not** copies at all:
the default tree held **115** skills while every profile held **71**, with **45 files differing**
and newer skills (`localhost-monitoring-console`) missing entirely. They were a *stale snapshot*,
so symlinking would not dedupe — it would silently upgrade seven profiles' behaviour. Compare
relative-path sets plus hashes (`references/runtime-tidy-and-profile-dedupe.md`), then present it as
a **decision for the owner** (`symlink = 115 skills terkini + 57 MB`, `refresh copies`,
`leave as-is`), never as housekeeping you perform on your own.

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

# runtime logs: truncate the big ones, drop the rotated ones — 27 MB → 4.6 MB
cd logs && rm -f *.log.1
for f in web-server.log agent.log hermes-dash-tunnel.log dashboard-tunnel.log; do
  [ -f "$f" ] && : > "$f"
done
# NEVER touch logs/<service>/ — svlogd owns lock/current there
```

Keep a `README-SUSUNAN.md` (or `docs/README.md`) that names every folder's job and every path
that must never be moved. The next session needs the map more than it needs the space.

## Pruning `backups/` — the folder you just filled

`backups/` becomes the next 90 MB problem if nothing ever leaves it (measured: 94 MB → 26 MB in one
pass). Three removals are safe, and each needs its own proof:

| Target | Proof required before `rm` | Measured |
|---|---|---|
| Database backup (`state.db.bak-*`) | the **live** DB answers: `PRAGMA integrity_check` → `ok`, plus a row count that matches reality (23 tables, 12,301 messages) | 56 MB |
| Config/persona twin (`SOUL.md.agency-backup`) | `md5sum` proves it is byte-identical to the copy being kept | 57 KB |
| Middle members of a backup series (`agents.json.bak-<date>` ×5) | keep **oldest + newest** — they bracket the history; the middles add nothing | 12.3 MB |

```bash
python3 -c "
import sqlite3
c=sqlite3.connect('state.db')
print('integrity:', c.execute('PRAGMA integrity_check').fetchone()[0])
print('jadual:', c.execute(\"select count(*) from sqlite_master where type='table'\").fetchone()[0])
"
md5sum backups/SOUL.md.bak backups/SOUL.md.agency-backup   # identical → drop one, keep one
```

Never delete a DB backup on a hunch — `integrity_check` plus a plausible row count is one command
and it is the only thing that makes the deletion defensible. Quote the check output in the report;
"database nampak ok" is not evidence.

## Executing the profile symlink (only after the owner approves)

The framing above says present it as a decision — this is the executed, verified recipe once the
answer is "ya". Measured 121 MB → 54 MB.

```bash
cd ~/.hermes20
# 1) keep the stale tree recoverable — 121 MB of markdown compresses to 17 MB
tar czf "backups/profiles-skills-lama-$(date +%F).tar.gz" profiles/*/skills

# 2) swap each profile's copy for a symlink to the single shared set
for p in profiles/*/; do
  [ -d "$p/skills" ] && [ ! -L "$p/skills" ] || continue
  rm -rf "$p/skills"
  ln -s "$HOME/.hermes20/skills" "$p/skills"
done

# 3) prove the tree resolves, then prove Hermes itself agrees
for p in profiles/*/; do
  printf '%-24s %s skill\n' "$p" "$(find -L "$p/skills" -name SKILL.md | wc -l)"
done
HERMES_PROFILE=finance hermes skills list | tail -1     # → 67 builtin, 44 local — 111 enabled
```

- Use an **absolute** link target; a relative one breaks the moment a profile moves.
- `find` needs `-L`, otherwise the symlinked tree reports **0** skills and looks like a failure.
- The loader check is mandatory: the file count proves the link resolves, `hermes skills list`
  proves the *agent* sees it. That profile printed 71 skills before the swap, 111 enabled after.
- Keep the tarball about a week, then delete it with the usual proof habit.

## Verify after every organising step

```bash
hermes-status                                   # every service HIDUP, console 200
python3 -c "import ast,glob;[ast.parse(open(f).read()) for f in glob.glob('app.py')]"
for f in scripts/*.sh; do bash -n "$f" || echo "ROSAK $f"; done
```

Then prove it in the reply with raw output — "dah susun" without a status block is a claim.

## Deletion phase — measure after, never during

Deletion only starts once every phase report has been read, and it runs as its own phase with these
rules:

1. **Delete the DERIVED trees before considering the move.** Inside a "snapshot" or legacy project
   the bulk is usually build cache, not data. `root-cleanup/` at 4.9 GB was `.npm` 1.8 G +
   `.cargo` 1.1 G + `.bun` 837 M + `.local` 725 M + `.cache` 327 M; `legacy-ultimate/` at 2.1 GB was
   1.6 GB of `node_modules`/`.venv`/`.next`. Removing those can make an 8.7 GB external copy
   unnecessary — check before commissioning a multi-hour transfer.
2. **Inspect hidden directories before judging a snapshot.** `du -sh *` hides the real weight:
   `cd snapshot && du -sh .[!.]* | sort -hr | head`.
3. **Kill only what you can verify is regenerable.** `node_modules`, `.venv`, `.next`, `__pycache__`,
   `.npm`/`.cargo`/`.bun` caches, `dist` — all rebuildable. Source, `identity/`, `docs/`, `tests/`,
   `config/` stay.
4. **Prove dedupe with content, not size.** See the three outcomes below.
5. **Confirm services after the phase, and re-measure the total** — then report the number once,
   from a completed state.

```bash
# one pass: drop every regenerable tree in a legacy project, keep the source
find . -type d \( -name node_modules -o -name .venv -o -name venv \
                 -o -name __pycache__ -o -name .next \) -prune -exec rm -rf {} + 2>/dev/null
```

### Duplicate verdicts: identical, subset, disjoint

"Same size" is not proof and "different size" is not disproof. Compare the **relative-path set**
and then hash a few shared files:

| Verdict | Signature | Action |
|---|---|---|
| **identical** | all paths shared, then hashes match (`bun-repo` / `bun-install`: 19,635 files each) | delete one |
| **subset** | one side's paths are fully contained in the other (`cline-install` 4,225 of `cline-repo` 8,450), hashes match on every shared file | delete the smaller |
| **disjoint** | shared paths ≈ 0 | keep both, they are different tools |

Measured this session: 962 MB recovered only because the subset case was caught — a size/summary
comparison would have kept both. Script and per-pair evidence:
`references/deletion-phase-measured.md`.

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
7. **`du` while a delete is running reports fiction — and it will be quoted to the user.** A
   background `rm -rf` of 4.9 GB had `du -sh ~/.hermes20` print **8.2 G**; after it finished the
   same command printed **14 G**. Never publish a total measured mid-deletion: run the report only
   from the completion notification, and if a number already escaped, correct it explicitly
   ("angka tadi salah — dibaca ketika fail sedang dipadam").
8. **Killing a cross-FS `mv` mid-flight leaves both sides partial, and FUSE `rm -rf` can fail with
   `Directory not empty`.** Removing the half-copy needed a second pass; verify with `ls` on the
   destination rather than trusting the first `rm`. Decide *before* starting: if the payload is
   mostly DERIVED cache, delete it in place instead of copying the snapshot out.
9. **After deleting the directory your shell is sitting in, the next `cd ~/other` fails pointing at
   the dead path** (`cd: …/root-cleanup: No such file or directory`, exit `126`) even though the
   target exists — the shell's cwd is gone. Start the next command with `cd ~ && …`.
10. **A retired port lives in cron job *names* too.** Code grep finds `app.py`/`PLAN.md`/pids but not
    the scheduled-job title; rename it (`cronjob update <id> name="Penjaga … (8787)"`) so the owner
    does not keep seeing `(8787 + 8790)` in the console after 8790 is gone.
11. **`npm prune` does not shrink a real app's `node_modules`.** Offered as a tidy-up, it printed
    notice text and left `node_modules` at **91 MB** — zero extraneous packages, because every
    package is reachable from `npm run build`/`dev`. Never quote `npm prune` as a saving; the only
    things that free that space are `rm -rf node_modules` (then the app cannot build until
    `npm install`) or deleting the whole unused app. Say which, and measure before/after with `du`.
12. **A FUSE phantom directory survives `rm -rf`, and retrying is the wrong move.** After clearing
    `/sdcard/.../ultimate-2026-10` the parent still existed with **0 files and 6 empty dirs (26 KB)**;
    `rm -rf` failed again and `rmdir` answered *"Directory not empty"* on an apparently empty path.
    That is an Android FUSE artifact. State three facts and stop: it holds **no files**, it lives on
    **external storage** (so the home's `du` is unaffected), and the owner can remove it from the
    Files app. Do **not** loop destructive variants — the approval layer can block the retry
    (`BLOCKED: … Silence is not consent`) and the turn ends with an unrelated stall. One retry after
    `chmod -R u+w`, then hand it over.
13. **The `du` total is only publishable from a completed process.** Corollary of pitfall 7 that
    caught this session twice: `du -sh <home>` during a background `rm` reported 8.2 G, then 3.7 G,
    then the true 6.2 G. Quote the number from the completion notification only, and when a figure
    escaped early, correct it in the next reply in one line rather than quietly restating it.

## References

- `references/hermes20-audit-2026-11.md` — measured inventory of a 17 GB / 215k-file Termux agent
  home: per-folder sizes, the three duplicate vendors, the 7×71 profile copies, the stub list, and
  the exact commands that produced each number.
- `references/phased-documentation-pass.md` — the "fasa 1 sampai siap" method: completeness scan
  that separates stubs from prose, script-usage cross-reference (cron + runit + callers), FastAPI
  route inventory, the `LAPORAN-FASA-N.md` skeleton the owner audits, and the doc baseline
  (`ARKITEKTUR` / `SERVIS` / `SUSUNAN` / `RUNBOOK-INSIDEN` / `API-KONSOL` / `SKRIP` / `AGENTS.md`).
- `references/deletion-phase-measured.md` — the deletion phase with real numbers: 17 GB → 6.4 GB
  breakdown, the hidden-dir scan that exposed a 4.9 GB snapshot of pure build cache, the
  identical/subset/disjoint duplicate comparator (Python, copy-paste) with the `cline-install`
  subset case that saved 962 MB, the `node_modules`-prune one-liner (2.1 GB → 539 MB), and the four
  traps (du mid-delete lies, killed cross-FS `mv` → FUSE `Directory not empty`, cwd inside a deleted
  dir, 180 s timeouts).
- `references/runtime-tidy-and-profile-dedupe.md` — the small leftovers phase: log truncation
  (27 M → 4.6 M, and why `logs/<service>/` is off-limits), the measured `npm prune` no-op (91 M
  before *and* after), the hash-set script that proved the 7 profiles were **stale (71) not
  duplicated (115)** with the three verdicts and the three options to offer, the FUSE phantom-dir
  signature (0 files / 6 dirs / 26 K, retry gets `BLOCKED`), and the end-of-pass number block.
- `references/backups-prune-and-profile-symlink.md` — the two closing phases: pruning `backups/`
  itself (94 M → 26 M) with the three verdicts and their proofs — `PRAGMA integrity_check` + table
  and row counts before deleting a `state.db.bak-*`, `md5sum` twins, and the "keep oldest + newest"
  rule for `*.bak-<date>` series — plus the executed profile-symlink recipe (tar the stale tree
  first, absolute link target, `find -L`, and the mandatory `HERMES_PROFILE=<p> hermes skills list`
  acceptance check, 71 → 111 enabled).
