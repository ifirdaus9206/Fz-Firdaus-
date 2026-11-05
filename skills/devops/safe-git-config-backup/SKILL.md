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
  printf '%s => ' "$p"; git check-ignore -v --no-index "$p" || echo "TIDAK"
done
```
If every probe says `TIDAK`, the file is being parsed as garbage — fix it before adding.

**`--no-index` is mandatory here.** Plain `git check-ignore` refuses to answer for
already-tracked paths: it prints nothing and exits 1 even when the pattern is perfect. Without
`--no-index` a cleanup run looks like "all my new rules are broken" when in fact the rules are
fine and the files are merely still in the index. Diagnose with `--no-index` first; only blame
the `.gitignore` syntax if the probe still misses.

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

## PITFALL #2b — `git gc` will NOT shrink `.git` if the blob is still in history

`git rm --cached` only removes the file from the *index*. The blob stays reachable from every
old commit, so `git gc --aggressive --prune=now` has nothing to drop and `du -sh .git` is
unchanged (measured this session: 28M before → 28M after; `size-pack` still 26.19 MiB, largest
packed object 33.8 MB = the already-removed `bin/tirith`).

Consequences to state honestly in the report:
- "`.git` mengecil" is a **weak pass criterion** for index-only cleanup — expect it to stay flat.
- Real shrinkage needs a history rewrite (`git filter-repo --path … --invert-paths`, or
  `filter-branch`) which **rewrites every commit SHA**. Never run it unprompted; surface it as a
  decision with the blast radius named (SHAs change, mirror backup + reflog required first).
- The honest metric after index cleanup is "no longer tracked":
  `git ls-files | grep -c <pattern>` → 0, plus `git count-objects -vH` for loose/garbage counts.
- Don't imply the repo got smaller when only the index did.

## PITFALL #2c — a global `*.bak` rule can evict deliberate backups

`*.bak` / `*.bak-*` are the right default for manual backups, but they also match `SOUL.md.bak`,
`SOUL.md.bak-ketua-<date>` and similar persona/config backups the user *does* want in the repo.
Add negations after the broad rules and prove them:

```gitignore
# terbitan: backup manual (bukan sumber hidup)
*.bak-*
*.bak
# kecualian: backup persona SOUL.md dikekalkan dalam sandaran (bukan terbitan)
!SOUL.md.bak
!SOUL.md.bak-*
```

```bash
git ls-files | grep '^SOUL.md.bak'            # kept backups must still be listed
git check-ignore -v --no-index SOUL.md.bak    # should name the !SOUL.md.bak line
```

Negation only works while the parent directory isn't itself excluded — don't hide `*.bak` behind
an `archive/` or `profiles/` ignore and expect `!` to rescue it.

## PITFALL #3 — churn files make the nightly commit noisy

Heartbeats and usage counters change every minute, so "silent when nothing changed" never
holds. Find them from the first real commit (`git log -1 --name-only --oneline`) and exclude:
`channel_directory.json`, `cron/ticker_heartbeat`, `cron/ticker_last_success`,
`skills/.usage.json`, `state/gateway.heartbeat`.

Runtime **databases** are the worst offender because their size changes, so every run produces a
binary diff and a commit even when "nothing" happened — `verification_evidence.db`
(`Bin 40960 -> 40960 bytes`) did exactly this. The list above is not exhaustive: after a
supposedly clean run, if HEAD moved, inspect `git log -1 --stat --oneline`, add the offending
path to `.gitignore`, `git rm --cached` it, then require empty `git status --short` on the next
run. See "Discovering unknown churn" under Verification.

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

### Post-cleanup verification (index removal)

Prove each claim with raw output; keep the "before" numbers from the initial survey so the
delta is real rather than asserted:

```bash
git status --short                                  # must be empty
git log --oneline | head -6
git ls-files | wc -l                                # compare against the "before" count
git ls-files | grep -E '^(bin/tirith|cron/executions\.db|…bak-|skills/\.curator_backups/|gateway_state\.json)' || echo '(tiada hasil)'
git count-objects -vH                               # count/size-pack/packs — honest gc metric
git ls-tree -r -l HEAD | sort -k4 -nr | head -10    # real largest tracked blobs
git remote -v                                       # empty when no remote
tail -5 logs/backup.log
```

File-count note: the count can move both ways — removals minus new tracked files committed in
the same run. Say so instead of pretending the delta equals the removed files.

### Prove the secret guard survived the cleanup

`git rm --cached` plus `git gc` is exactly the kind of surgery that can break a wrapper script,
so re-test the guard afterwards and quote the evidence:

```bash
B=$(git rev-parse HEAD)
out=$(bash scripts/backup_github.sh); rc=$?
printf 'exit=%s\nstdout=[%s]\n' "$rc" "$out"
[ "$B" = "$(git rev-parse HEAD)" ] && echo 'HEAD SAMA — tiada commit baharu'
git log --all --oneline -- bocor-uji2.txt | wc -l    # 0 = nothing leaked into history
```

Expect exit 3, HEAD identical, and the offending path named in stdout. If the guard fires but
names a *documentation* file instead of your probe, the probe never got staged — a file at
`~/x.txt` is outside a `~/.hermes20` repo. Write the probe at the repo root and delete it with
`rm -f` afterwards; confirm with `git log --all --oneline -- <file>` returning nothing.

### Discovering unknown churn (do this once per repo)

Runtime databases not covered by `.gitignore` defeat "silent when nothing changed" — each run
commits a binary diff (`verification_evidence.db | Bin 40960 -> 40960 bytes` in this session).
Method: run the script once, then `git log -1 --stat --oneline`; anything that appears there and
is not source code belongs in `.gitignore` plus `git rm --cached`. Re-run and require empty
`git status --short`.

## Unblocking the human step: `gh auth login` with no TTY

The closing line "bos cuma `gh auth login`" is *not* one command in an agent session. gh asks
`? Authenticate Git with your GitHub credentials? (Y/n)` first, and that survey prompt
re-prompts forever when stdin is a pipe or a pty that has reached EOF — `printf 'Y\n' | gh …`,
`script -qec …` and a hand-written pty driver all loop on the same line (three attempts, same
dead end this session).

Pre-answer the question through git config instead of through stdin:

```bash
git config --global credential.https://github.com.helper '!gh auth git-credential'
gh auth login --hostname github.com --git-protocol https --web
```

With the helper already configured the prompt disappears and the code prints immediately:

```
! First copy your one-time code: XXXX-XXXX
Open this URL to continue in your web browser: https://github.com/login/device
```

Rules that make this work:

- Relay **code + URL** to the owner; they authorize in a browser. Nothing else is required.
- **Never wrap it in `timeout`** — that process *is* the poller, and killing it invalidates the
  code. Start it as a background process and leave it alive while the owner authorizes.
- **Every restart mints a new code.** Quote the newest line, never an earlier one, and tell the
  owner it expires in ~15 minutes.
- After authorization only `git remote add origin <URL>` is needed — the backup script pushes on
  its next run, so no script change and no token in the repo.
- For a private repo, verify visibility afterwards (`gh repo view --json visibility`) rather
  than assuming it took effect.

Session transcript, including why the pty driver looped: `references/gh-login-without-tty.md`.

## Reporting

- Lead with outcomes, then raw verification blocks, then the single remaining human step.
- Write the report in **Bahasa Melayu** for this user; keep commit/log strings Malay too
  (`sandaran awal — <tarikh>`, `tiada remote — commit tempatan sahaja`).
- Never invent repo name, branch, or account. With no `gh` login, the closing line is one
  step: `gh auth login` + the repo URL from the boss.
- Flag residual privacy risks you chose to keep (e.g. docs containing a Telegram chat ID)
  instead of silently shipping them.
