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

### Once the owner approves the rewrite

PITFALL #2b says never run it unprompted — it does **not** say never run it. When the owner answers
"buat" after seeing the blast radius, follow `references/history-rewrite-approved.md`. The shape:

1. **Bundle first** (`git bundle create … --all` + `git bundle verify`) and record a baseline triple:
   `HEAD`, `HEAD^{tree}`, `git ls-files | wc -l`, and one aggregate `sha256sum` of every tracked file.
2. `git filter-repo --invert-paths --path …` over the **already-untracked** heavy paths only, then
   `reflog expire` + `gc --prune=now`; re-add `origin` (filter-repo deletes it).
3. **Three gates before any push:** tree hash, file count, aggregate hash. If the tip tree moved
   because files were committed after the baseline, reconcile against the bundle with `comm -23`
   and require "nothing lost, N added" — never just abandon the run.
4. `push --force`, then prove it from the remote with a `--depth 1` clone whose tree hash and file
   count match local. A local "push berjaya" line is not evidence.
5. **If the delegated run dies mid-rewrite** (`Delegation owner exited before recording a terminal
   result`), do **not** re-run it. Verify read-only: `.git` size, blob absence, `ls-remote` == HEAD,
   `git status`, bundle present — then run the gates. Measured: 27.5 MB → 5.4 MB, 26 commits, all
   SHAs new, 0 files lost.

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

## INCIDENT — a real secret is already pushed (do this, don't just `git rm --cached`)

Trigger: owner says "jangan simpan password di GitHub" / you find a literal credential in
`git grep -l <secret> HEAD`. Check visibility first — the answer changes the urgency:

```bash
curl -s -o /dev/null -w 'HTTP %{http_code}\n' https://api.github.com/repos/<owner>/<repo>
# 200 = PUBLIC → treat as leaked now; 404 = private/missing
```

Order that worked (public backup repo, password in 3 tracked files):

1. **Redact the working files** (memory files + skill docs count — `memories/*.md` are tracked).
   Replace the literal with a marker (`<password-akaun>`, `<REDACTED-PASSWORD>`) and keep the
   *lesson* while dropping the value. If the value lives in Hermes memory, use the `memory` tool's
   `replace` so the injected copy is cleaned too — patching the file alone leaves it in memory.
2. **Purge history** (SHAs change — a backup repo tolerates this; a shared repo does not):

   ```bash
   pip install git-filter-repo            # Termux: fine, installs to $PREFIX/bin
   printf '<secret>==><REDACTED>\n' > ~/tmp/redact.txt
   git filter-repo --replace-text ~/tmp/redact.txt --force
   ```
   `--replace-text` is substring-based, so it also rewrites any longer string containing the
   secret — good. `filter-repo` **removes `origin`** by design; re-add it:
   `git remote add origin git@github.com:<owner>/<repo>.git`. SSH-only push avoids storing a PAT.
3. **Commit the redaction, then force push**: `git add -A && git commit -m 'selamat: buang
   password' && git push --force origin main`.
4. **Verify from GitHub, not from local git** — see `references/purge-pushed-secret.md` for the
   exact curl probes (raw file grep count, API tree scan, dangling-commit probe).

**Residual exposure you must report, not hide:** after a force push the old commits stay
fetchable by SHA (`GET /repos/<o>/<r>/commits/<old-sha>` → 200) until GitHub garbage-collects.
So "sudah tiada di GitHub" is false; the honest statement is "branch bersih, commit lama masih
boleh dibuka melalui SHA". Offer, in numbered form: (1) rotate the credential now, (2) delete and
recreate the repo (only guaranteed removal), (3) GitHub Support cache purge, (4) nothing further.

Also verify images/binaries were never tracked at all — `git log --all --diff-filter=A
--name-only | grep -Ei '\.(png|jpg|jpeg|webp)$'` and the API tree scan; report "0 imej, tiada
dalam sejarah" rather than "aku dah buang" when nothing was ever there.

**The repo is only half the leak.** The same literal also sits in `logs/gateway.log`,
`logs/agent.log`, `state.db` (+ `-wal`, FTS shadow tables) and any `tmp/` helper script that wrote
it. After the git purge, run the local scrub in `credential-secret-hygiene`
(`scripts/scrub_secret.py --literal '<value>'`) before telling the owner the secret is contained —
and remember the account password vs App-Password distinction before recommending a rotation.

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
   **Weakest tier — drop it if docs are in the repo.** Any markdown hash block, checksum list
   or signature sample is one long token per line, so this tier fires on documentation that has
   nothing to do with credentials. Real key formats are already covered by tier 1.

The durable shape is **two independent axes, not three severity tiers**: *which patterns* (hard
credential shapes vs. `name=value` assignments) × *which files* (everything vs. non-docs only).
Full design, exact shell functions and measured test results:
`references/two-tier-secret-scan.md`. Re-runnable regression harness:
`scripts/scan_matrix_test.sh`.

### Running the regression harness

```bash
bash skills/devops/safe-git-config-backup/scripts/scan_matrix_test.sh   # dari akar repo
bash ~/.hermes20/skills/devops/safe-git-config-backup/scripts/scan_matrix_test.sh  # dari mana-mana cwd
```

25 kes: 10 blok peringkat 1, 11 placeholder/dokumentasi (termasuk `AKIA…EXAMPLE`), 4 tugasan
sebenar; cetak `LULUS=x GAGAL=y` dan exit bukan-sifar jika ada kegagalan. Skrip mencari akar
repo daripada lokasi dirinya sendiri, mencipta **repo buangan** dalam folder sementara dalam
repo (`git init`, tiada remote ⇒ tiada push) dan memadamkannya melalui `trap`. Kunci palsu
**dibina semasa runtime** melalui pemboleh ubah berasingan (`PFX_SK='sk-'` + `PJG=…` →
`KUNCI_SK="${PFX_SK}${PJG}"`, begitu juga ghp_/github_pat_/AIza/AKIA/xox/JWT/tajuk PRIVATE KEY)
supaya fail harness itu sendiri tidak mencetuskan pengawal peringkat 1 dan selamat di-commit.

Dua perangkap yang hanya muncul apabila harness duduk **di dalam** repo:

- **Peringkat 2 juga menembak fail harness sendiri.** Fixture `db_password=Qz7…` /
  `client_secret: "Rk4…"` ialah tugasan sah dengan nilai 16 aksara, jadi guard menamakan
  `scan_matrix_test.sh (peringkat 2)` dan backup exit 3. Bina nilai melalui pemboleh ubah dan
  tulis `"db_password=${N1}"` dalam sumber: shell mengembangkan ke fail ujian, tetapi baris
  sumber hanya mengandungi `${…}` yang ditapis `REAL_VALUE`. Bukti akhir mesti
  `bash scripts/backup_github.sh` → exit 0 **dengan harness di-stage**; exit 3 yang menamakan
  harness = masih ada literal.
- **Reset setiap kes mesti `reset --hard "$BASE"` + `clean -fd`.** `git reset` sahaja
  meninggalkan fail kes "diterima" yang telah di-commit, jadi `git add -A` kes berikutnya
  mengesan semula fail itu dan memberi 3 palsu pada kes yang sepatutnya 0. Simpan
  `BASE=$(git rev-parse HEAD)` selepas commit asas sandbox.

Scan **added lines of staged files**, not `git diff --cached` as a blob, so you can print
offending paths; and keep `.gitignore` prose free of the trigger words (write the reason in
Malay: "kelayakan", "rahsia") so the guard never flags its own rule file.

Guard defensively even with .gitignore: if `git ls-files --cached` still lists a forbidden
path (`.env`, `auth.json`, `config.yaml`, `state.db*`, `sessions/`, `logs/`, `pastes/`),
`git reset` and refuse — belt and braces.

### Tier-2 false positive: placeholders in docstrings block the backup for days

Measured case: the nightly job exited `3` for several nights, HEAD frozen at the last good
commit, and nobody noticed because the guard's stdout only reaches the chat when a human is
awake. Offending lines were **documentation placeholders**, not secrets:

```
GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx      # App Password 16 aksara
```

Tier 2 (`keyword [:=] value ≥12 chars`) matches `xxxxxxxxxxxxxxxx` perfectly — 16 x's are
`[A-Za-z0-9]`. Same trap for `<your-token-here>`-style samples, `AKIAIOSFODNN7EXAMPLE`, and
commented-out example configs.

Correct fix — **change the placeholder, never weaken the regex**:

```diff
-    GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx      # App Password 16 aksara
+    GMAIL_APP_PASSWORD=<16-aksara>           # App Password 16 aksara
```

`<…>` is outside the value charset, so the line stops looking like an assignment while the doc
still reads correctly. Apply it to **every copy** (top-level `scripts/` *and* the skill copy
under `skills/**/scripts/` — both are tracked and both fire).

### Better than editing docs: make tier 2 document-aware

Rewriting the placeholder works but is fragile — docs legitimately quote canonical examples
(`GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx`, `AKIAIOSFODNN7EXAMPLE`), and the next author re-adds
them. If the same doc files block the night job more than once, fix the **scanner** instead:

- tier 1 (hard shapes) keeps scanning **every** file, `.md` and `docs/` included — no exceptions;
- tier 2 (`name=value`) skips `*.md`, `docs/`, `references/`, `templates/`,
  `*.example|*.sample|*.dist`, then filters the captured value (ignore `<…>`, `$(…)`, `${…}`,
  one repeated char only, `REDACTED|DIMASK|PLACEHOLDER|CHANGEME|YOUR_|example|contoh`, <12 chars).

This is not a loosening: `.md` still gets tier 1, which is what catches `sk-…`/`ghp_…` — proven by
a matrix case where `sk-…` inside a `.md` still exits 3. Design, exact functions and measured
results: `references/two-tier-secret-scan.md`.

Doc prose can still trip tier 1 by accident: a filename that ends in `task` + hyphen + a long
word matches the `sk-` rule (a real occurrence was a concurrency-diagnosis note).
Don't "fix" that by weakening `sk-`; reword or accept the hit.

### Tier-2 false positive: persona JSON and env-var reads block the backup

Two more measured offenders, both structural rather than prose:

1. **Agent persona catalogs** (`plugins/agency-agents-router/data/agents.json`) embed whole code
   samples — `token = data.tenant_access_token`, `apiKey: 'YOUR_...'`, `app_token: appToken`,
   `password = "..."`. Tier 2 fires on dozens of them and the night job exits 3 with
   `agents.json (peringkat 2)`.
2. **Env-var reads in the app source** (`app.py`):
   `LAN_TOKEN = os.environ.get("CONSOLE_LAN_TOKEN", "")` — the value is 20+ chars and contains no
   `$()`/`<…>`, so `REAL_VALUE` accepts it as a real assignment.

Fix, both narrower than weakening the regex:

```bash
# 1) exempt the persona data file from TIER 2 only (tier 1 still scans it — real keys still block)
IS_DOC() {
  case "$1" in
    *.md|docs/*|*/docs/*|references/*|*/references/*|templates/*|*/templates/*|*.example|*.sample|*.dist)
      return 0 ;;
    plugins/agency-agents-router/data/agents.json|*/plugins/agency-agents-router/data/agents.json)
      return 0 ;;
  esac
  return 1
}

# 2) treat env lookups as non-secrets inside REAL_VALUE, next to the placeholder case
case "$v" in
  os.environ*|os.getenv*|process.env*|getenv*|ENV\[*|secrets.*|getpass*) return 1 ;;
esac
```

Do **not** special-case the app file by name — env reads recur in every service module, so the
value filter is the durable fix. After patching, prove it: `bash scripts/backup_github.sh` must
exit 0 and `git rev-parse HEAD` must match `git ls-remote origin main`.

### Fixing false positives mints new false positives — budget three rounds

Measured case: the guard blocked the night job three runs in a row, each time on **text written
to explain the previous false positive**:

1. a reference doc (`references/two-tier-secret-scan.md`) quoting full fake keys for the test
   matrix — tier 1 cannot tell `sk-<32 fake chars>` from the real thing;
2. a skill paragraph naming a real filename that happens to spell `sk-` + 21 chars;
3. a one-shot helper (`scripts/redact_reference_once.py`) whose regex literals
   (`sk-[A-Za-z0-9_-]{20,}`) are themselves matches.

Rules that stop the carousel:

- **Docs never carry a full literal, not even labelled "fake".** Write `sk-<28-aksara>`,
  `AKIA<16-aksara>`, `ghp_<36-aksara>`, `<JWT-tiga-bahagian>`. A scanner can't tell fake from
  real, and neither can a reviewer skimming the repo.
- **One-shot helpers go to `~/tmp/`**, never `<home>/scripts/`; delete them before the next
  backup run. (`/tmp` is not writable in Termux — `~/tmp` is the scratch space.)
- **A harness may live under `skills/**` only if it builds its fake keys at runtime.** A
  *literal* full key is a match forever; `scripts/scan_matrix_test.sh` shows the safe form
  (pieces joined from variables inside the job). It still runs against a throwaway
  `HERMES_HOME` sandbox, never the live repo.
- **Stop condition is behavioural, not analytical:** two consecutive silent runs with empty
  `git status --short`. Editing the scanner is not evidence; the next quiet run is.

Then triage the whole hit list rather than only the first file: real login artefacts
(`secrets/*`, `dashboard_login.txt`, `.dash_url_last` stamp files) belong in `.gitignore`, not
in a "fix the false positive" patch. Re-run until `EXIT=0` and prove the push travelled:

```bash
git rev-parse HEAD
timeout 60 git ls-remote origin main     # must equal HEAD; "## main" with no ahead/behind is weaker
```

A silent `## main` only means local is not behind — it does not prove the push landed. Quote
the matching SHA from `ls-remote`.

### Tier 0 — the three tiers cannot see a *short* secret written as prose (real leak)

All three tiers above are shape-based, so a plain password sitting in normal sentences passes
cleanly. Measured case: a **6-digit account password** inside the tracked
`memories/MEMORY.md` prose (`… = PASSWORD bukan username`) and two skill docs shipped to a
**public** backup repo across several nightly commits. Why each tier missed it:

- tier 1 — no `sk_/ghp_/AIza…` shape;
- tier 2 — `ASSIGN_RE` needs `keyword [:=] value` **and ≥12 chars**, and a bare 6-digit run has
  neither;
- tier 3 — the line is prose, not a lone 32+ token.

Fix: keep a **denylist of known secret literals outside the repo** (`~/.secrets-denylist`, one
value per line, never committed) and grep the staged tree for those exact values before commit:

```bash
while IFS= read -r v; do
  [ -n "$v" ] || continue
  git grep -lF -- "$v" -- . ':!*.lock' 2>/dev/null | sed 's/^/  - /'
done < ~/.secrets-denylist | sort -u
```

Treat these paths as high-risk regardless of shape: `memories/*.md`, `skills/**/*.md`,
`knowledge_base/sop/*.md`, `PROFIL.md`. Anything that reads like a credential lesson
("… itu password, bukan username") belongs in prose **without the value** from the start — the
lesson is what matters, and `git grep` on a phrase like `password` is how you find such lines
during review.

## The backup script contract

Copy `templates/backup_github.sh` and adapt. Contract that matters:

- `set -uo pipefail`; `cd` to the home; log to `<home>/logs/backup.log` (mkdir -p).
- `git add -A` → forbidden-path guard → secret scan → `git reset` + exit 3 on hit.
- No staged changes ⇒ exit 0 **silently** (cron must not mail on healthy nights).
- Commit message `sandaran auto YYYY-MM-DD HH:MM`.
- Push only when `git remote get-url origin` succeeds; never `--force`; push failure exits
  nonzero (use a distinct code, e.g. 4) but leaves the local commit intact. No remote ⇒ one
  log line (`tiada remote — commit tempatan sahaja`), not stdout.
- Push to a **named** ref unless the local branch name equals the remote default branch. Bare
  `git push origin HEAD` pushes to the branch *of the same name*; local `master` + GitHub default
  `main` silently strands the whole backup on a branch nobody looks at (PITFALL #5).
- stdout only on problems.

`templates/backup_github.sh` is the tested implementation (guards, tiers, exit codes) —
start from it instead of re-deriving the regexes. **Its scan block is the older single-layer
version**; when docs live in the repo, replace it with the two-tier block in
`references/two-tier-secret-scan.md` and prove it with `scripts/scan_matrix_test.sh`. `references/hermes20-inventory.md` records
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
- **Check `git remote -v` BEFORE running the script as a test.** The script pushes whenever
  `origin` exists, so a "clean" test run can publish commits to a real GitHub repo. Measured
  case: context said "tiada remote sekarang", but `origin` existed and two test commits
  (`sandaran auto …`) went up mid-test, one carrying a probe file
  (`api_key=xxxxxxxxxxxxxxxx` — harmless, but *published*). Probe first; if a remote exists,
  either accept-and-disclose or point `HERMES_HOME` at a throwaway repo.
- **Matrix tests belong in a throwaway repo, not the live one.** The script honours
  `HERMES_HOME`, so `HERMES_HOME=$HOME/.uji-repo` + `git init` gives a sandbox for 20+
  positive/negative cases without touching the real backup. Put `logs/` in that sandbox's
  `.gitignore` or the forbidden-path guard fires on the log file it just wrote. Harness:
  `scripts/scan_matrix_test.sh`.
- **Tool output elides long tokens — never trust the echoed match.** A real
  `AKIAIOSFODNN7EXAMPLE` in a doc was displayed as `AKIAIO...MPLE`, which sent a whole detour
  chasing "how can a 13-char string match `AKIA[0-9A-Z]{16}`?". Confirm the bytes before
  theorising: `grep -n 'AKIA' file.md | od -c | head -5`, or `awk '/AKIA/{print length($0)}'`.
  Quote lengths and prefixes as evidence, not the elided string.

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

## Attaching the repo to a fresh GitHub remote (PITFALL #5)

Full recipe: `references/github-remote-bootstrap.md`. Short form:

- **Does the remote exist?** `gh` unauthenticated cannot tell you (private ⇒ 404 from the API).
  Probe with the SSH key: `git ls-remote git@github.com:<owner>/<repo>.git` — refs/exit 0 means it
  exists (an empty repo prints nothing but still exits 0); `ERROR: Repository not found` + exit
  128 means it does not. Probe a shortlist of candidate names instead of asking the owner again.
- **Parse pasted URLs.** Strip the `#fragment`, keep trailing punctuation exactly
  (`Fz-Firdaus-`, not `Fz-Firdaus`). Verify by probe, never by intuition.
- **Repo created with a README** ⇒ unrelated histories: `git fetch origin main`, then
  `git merge origin/main --allow-unrelated-histories`. Never `--force` over the owner's commit.
- **PITFALL #5 — `git push origin HEAD` creates a branch named after the local branch.**
  Local `master` + GitHub default `main` = the script logs `push berjaya` while
  `refs/heads/master` holds every file and the repo page still shows the 2-line README. Verify
  with `git ls-remote origin` against the branch GitHub displays, never against the log line.
  Fix: `git branch -m master main` → `git push -u origin main` → `git push origin --delete
  master` → re-run the script and require silence.
- **Visibility check without a token:**
  `curl -s -o /dev/null -w '%{http_code}' https://api.github.com/repos/<owner>/<repo>` —
  200 = public, 404 = private-or-missing. A web-UI repo defaults to **public**, and this backup
  ships `SOUL.md`, `memories/`, `profiles/`. Report the raw code and offer the Danger Zone path
  (Settings → General → Change visibility → Private) or a PAT; never quietly ship it public.
- Final proof is always: one ref in `git ls-remote origin` matching local HEAD, tracked-file
  count at parity with `git ls-files`, forbidden-path grep empty, owner's README still present.

## Reporting

- Lead with outcomes, then raw verification blocks, then the single remaining human step.
- Write the report in **Bahasa Melayu** for this user; keep commit/log strings Malay too
  (`sandaran awal — <tarikh>`, `tiada remote — commit tempatan sahaja`).
- Never invent repo name, branch, or account. With no `gh` login, the closing line is one
  step: `gh auth login` + the repo URL from the boss.
- Flag residual privacy risks you chose to keep (e.g. docs containing a Telegram chat ID)
  instead of silently shipping them.

### Delivering the incident report by email

When the owner says "semak dan emel", the report itself is a deliverable and needs the same
proof standard as the fix:

1. **Send** through the SMTP already configured in the home (`GMAIL_USER` /
   `GMAIL_APP_PASSWORD` in `.env`, `smtp.gmail.com:587` + STARTTLS). Read the credentials
   inside the script; never echo them, never paste them into chat.
2. **Verify by fetching, not by trusting the send call** — log in over IMAP
   (`imap.gmail.com:993`), `SEARCH SUBJECT "<subject fragment>"`, fetch the newest hit and
   print subject/from/date. "Emel dihantar" is a claim; "dijumpai dalam INBOX" is evidence.
3. **Delete the throwaway sender/verifier scripts** afterwards (`~/tmp/send_report.py`,
   `~/tmp/verify_mail.py`) — they sit outside the repo but still read credentials.
4. Body format that worked here: what happened → root cause (state plainly that it was a false
   positive, not a leak) → what changed → raw evidence table → GitHub/cron status → cleanup
   notes → signature "— Ketua (UIM)". Malay, no jargon.
