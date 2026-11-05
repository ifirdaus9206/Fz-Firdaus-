---
name: safe-git-config-backup
description: Nightly git backup of a config/home dir, secret-safe.
---

# Safe git backup of a config/home directory

Class of task: "back this home directory up to git/GitHub every night, without leaking
secrets and without committing gigabytes of derived data." Applies to `~/.hermes20`,
dotfile repos, config vaults, agent homes.

## Non-negotiable order

1. **Read the SOP first** if one exists (`knowledge_base/sop/*.md`) — it usually names the
   exact secret files. Follow it over your instincts.
2. **Measure before writing .gitignore** (`du -sh * | sort -hr | head -25`). You cannot
   write a defensible exclusion list without sizes.
3. **Write .gitignore, then `git init`, then `git add -A`, then verify the index** — never
   commit before the index has been inspected.
4. **Verify with raw output**, not with intent: `git ls-files | grep -E '(\.env$|…)'`.

## PITFALL #1 (cost: 20 min + a 1.6 GB .git) — no inline comments in .gitignore

Git does **not** support trailing comments. This is silently catastrophic:

```gitignore
.env                      # rahsia: kelayakan API     ← BROKEN
config.yaml               # rahsia: kunci API          ← BROKEN
archive/                  # berat: 8.7GB              ← BROKEN
```

The whole line becomes the pattern (`".env                      # rahsia…"`), so **no rule
matches**, `.git add -A` walks the 8.7 GB tree, and `.env`/`config.yaml` get staged.
Symptom to recognise: `git check-ignore -v .env` prints nothing while the file clearly
exists, and `git add -A` runs for minutes.

Correct form — reason on its own line above the pattern:

```gitignore
# rahsia: kelayakan API/model
.env
# berat: 8.7GB arkib lama
archive/
```

Sanity check before `git add` (cheap, catches the whole class):

```bash
for p in .env auth.json config.yaml state.db archive/ tmp/ foo.log; do
  printf '%s => ' "$p"; git check-ignore -v "$p" || echo "TIDAK"
done
```
If every probe says `TIDAK`, the file is being parsed as garbage — fix it before adding.

If you already staged gigabytes, delete `.git` and re-init (nothing committed yet) rather
than trying to unstage a 1.6 GB object store.

## PITFALL #2 — ignore rules never apply to already-tracked files

Adding a pattern after a file is committed does nothing. Staged files must be removed
explicitly, and `git rm --cached` does **not** delete the file from disk:

```bash
git rm --cached bin/tirith cron/executions.db
git rm -r --cached -q pastes skills/.curator_backups
```
Re-check `git ls-files | grep -E '…'` after every round.

## PITFALL #3 — churn files make the nightly commit noisy

Heartbeats and usage counters change every minute, so "silent when nothing changed" never
holds. Find them from the first real commit (`git log -1 --name-only --oneline`) and exclude:
`channel_directory.json`, `cron/ticker_heartbeat`, `cron/ticker_last_success`,
`skills/.usage.json`, `state/gateway.heartbeat`.

## PITFALL #4 — embedded git repos show permanent ` m` status

`agency-agents/`, `*/.git` subprojects get added as gitlinks; their dirty worktrees keep
`git status --short` non-empty forever and their content is *not* backed up either way.
Drop the gitlink (`git rm --cached <dir>`) and ignore the directory — it has its own remote.

## What to exclude, by category (annotate every line)

| Category | Examples | Reason |
|---|---|---|
| Secrets | `.env`, `.env.*`, `auth.json`, `config.yaml`, `config.yaml.bak*`, `*.lock`, `gateway.pid` | credentials |
| User pastes | `pastes/` | unpredictable content, may hold leaked keys |
| State | `state.db*`, `kanban.db*`, `*.db`, `sessions/`, `logs/`, `cache/`, `*.log`, `processes.json` | secret-bearing + always changing |
| Per-profile copies | `profiles/*/state.db*`, `profiles/*/sessions/`, `profiles/*/logs/`, `profiles/*/audio_cache/`, `profiles/*/image_cache/`, `profiles/*/models_dev_cache.json` | duplicates of the above |
| Derived | `node_modules/`, `.venv/`, `venv/`, `__pycache__/`, `*.pyc`, `*/src-tauri/target/`, `*.tar.gz` backup archives | regenerable, heavy |
| Vendor trees | `archive/`, `legacy-*`, `tools/<vendored-source>/`, downloaded binaries (33 MB `bin/tirith`) | heavy, not live config |

Rule of thumb: any single tracked file >5 MB needs a written reason to stay.

## Secret scan that doesn't drown in false positives

The SOP's plain keyword grep (`api[_-]?key|token|secret|password`) matches documentation
prose ("tanpa token/rahsia", "~42,885 tokens"). Use three tiers, and report **file names
only** — never echo the matched value:

1. **Hard shapes** (block): `sk-[A-Za-z0-9_-]{20,}`, `ghp_/gho_/ghs_/github_pat_`,
   `AIza[0-9A-Za-z_-]{30,}`, `xox[bpas]-`, `-----BEGIN … PRIVATE KEY-----`.
2. **Assignment with a real value** (block): keyword + `[:=]` + ≥12 token chars, e.g.
   `KUNCI=‹nilai›` (contoh 12+ aksara), `password: ‹12+ aksara›`. Vars kosong (`KEY=`) tak padan.
3. **Bare token line** (block): a single added line that is nothing but 32+ `[A-Za-z0-9_/+=-]`.

Scan **added lines of staged files**, not `git diff --cached` as a blob, so you can print
offending paths; and keep `.gitignore` prose free of the trigger words (write the reason in
Malay: "kelayakan", "rahsia") so the guard never flags its own rule file.

Guard defensively even with .gitignore: if `git ls-files --cached` still lists a forbidden
path (`.env`, `auth.json`, `config.yaml`, `state.db*`, `sessions/`, `logs/`, `pastes/`),
`git reset` and refuse — belt and braces.

## The backup script contract

Copy `templates/backup_github.sh` and adapt. Contract that matters:

- `set -uo pipefail`; `cd` to the home; log to `<home>/logs/backup.log` (mkdir -p).
- `git add -A` → forbidden-path guard → secret scan → `git reset` + exit 3 on hit.
- No staged changes ⇒ exit 0 **silently** (cron must not mail on healthy nights).
- Commit message `sandaran auto YYYY-MM-DD HH:MM`.
- Push only when `git remote get-url origin` succeeds; never `--force`; push failure exits
  nonzero (use a distinct code, e.g. 4) but leaves the local commit intact. No remote ⇒ one
  log line (`tiada remote — commit tempatan sahaja`), not stdout.
- stdout only on problems.

`templates/backup_github.sh` is the tested implementation (guards, tiers, exit codes) —
start from it instead of re-deriving the regexes. `references/hermes20-inventory.md` records
the already-measured folder sizes, confirmed secret files, and churn list for the
`~/.hermes20` home, so a repeat run skips the 16 GB scan.

## Pitfalls when testing the script

- A test file written to `~/foo.txt` is **outside** a `~/.hermes20` repo and proves nothing.
  Put probe files inside the repo root; say so explicitly in the report.
- Do the three tests in order: (a) run twice → second run silent; (b) add a small file →
  commit with empty stdout, delete it → commit the deletion; (c) drop a file containing a
  real-shaped key → exit 3, HEAD unchanged, `git log --all -- <file>` empty, stdout shows
  the warning plus filename.
- Shell wrapper `$(...)` capture is the cleanest way to prove "stdout empty": `out=$(bash
  script.sh); echo "exit=$? stdout=[$out]"`.

## Verification (paste raw output in the report)

```bash
git status --short                                   # empty
git log --oneline | head -5
git ls-files | wc -l
git ls-files | grep -E '(\.env$|auth\.json|config\.yaml|state\.db|sessions/|logs/)'; echo "padanan=$?"
du -sh .git
git ls-tree -r -l HEAD | sort -k4 -nr | head -10     # real largest blobs
```

Use `git ls-tree -r -l` for the "biggest tracked files" list — `git ls-files | xargs du`
expands gitlink directories and reports misleading 91 MB `node_modules` totals that are not
tracked at all.

## Reporting

- Lead with outcomes, then raw verification blocks, then the single remaining human step.
- Write the report in **Bahasa Melayu** for this user; keep commit/log strings Malay too
  (`sandaran awal — <tarikh>`, `tiada remote — commit tempatan sahaja`).
- Never invent repo name, branch, or account. With no `gh` login, the closing line is one
  step: `gh auth login` + the repo URL from the boss.
- Flag residual privacy risks you chose to keep (e.g. docs containing a Telegram chat ID)
  instead of silently shipping them.
