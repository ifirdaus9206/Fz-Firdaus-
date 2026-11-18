# Purging heavy blobs from history — the approved-rewrite run

PITFALL #2b in SKILL.md says a history rewrite is a **decision, not a default**. This file is what
to run *after* the owner approves it, with the proof gates that make "nothing was lost" a measured
claim instead of a promise.

Measured case (2026-11-18, `~/.hermes20` → private GitHub repo, 4,730 tracked files):
`.git` **27.5 MB → 5.4 MB**, 26 commits, every SHA rewritten, remote force-pushed, zero files lost.

## Why the owner has to approve first

- Every commit SHA changes. Any external reference to a SHA (chat messages, docs, deploy pins)
  becomes dangling.
- The push must be `--force`; on a shared repo that is how other people's work disappears.
- A backup repo with no collaborators tolerates it. Ask about collaborators before assuming that.

## 1. Safety net BEFORE anything

```bash
cd <home>
git bundle create ~/tmp/<name>-sebelum-rewrite.bundle --all
git bundle verify ~/tmp/<name>-sebelum-rewrite.bundle      # must print "ok"
```

Record a baseline triple — this is what step 4 compares against:

```bash
git rev-parse HEAD
git rev-parse 'HEAD^{tree}'
git ls-files | wc -l
git ls-files -z | xargs -0 sha256sum | sha256sum            # one aggregate hash
du -sh .git; git count-objects -vH
```

Commit any pending work first (`bash scripts/backup_github.sh` until `git status --short` is empty),
then **stop calling the backup script** — it commits and pushes, which must not happen mid-rewrite.

## 2. Find what is actually heavy

```bash
git rev-list --objects --all \
  | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | awk '$1=="blob" && $3>1000000 {print $3, $4}' | sort -rn | head -20
```

Cross-check against what `.gitignore` + `git rm --cached` already evicted from the index. Those are
exactly the blobs that survive in history and keep `.git` fat: binaries, `*.bak-*` catalogue copies,
curator tarballs, runtime DBs.

## 3. Rewrite

```bash
git filter-repo --force --invert-paths \
  --path bin/tirith \
  --path 'plugins/agency-agents-router/data/agents.json.bak-*' \
  --path skills/.curator_backups/ \
  --path cron/executions.db \
  --path gateway_state.json \
  --path verification_evidence.db

git reflog expire --expire=now --all && git gc --prune=now --aggressive
```

`filter-repo` removes `origin` by design — re-add it (`git remote add origin git@…`) before pushing.
Never include a path that is still tracked in HEAD; that would delete real content from the tip.

## 4. Proof gates — all three must pass before the push

| Gate | Command | Expectation |
|---|---|---|
| Tree unchanged | `git rev-parse 'HEAD^{tree}'` | equals baseline (or differs only by files committed after the baseline snapshot — see below) |
| No file lost | `git ls-files | wc -l` | equals baseline |
| Content unchanged | `git ls-files -z \| xargs -0 sha256sum \| sha256sum` | equals baseline |
| Blobs gone | `git rev-list --objects --all \| grep -E 'tirith\|agents\.json\.bak\|curator_backups\|executions\.db'` | empty |

If a gate fails: **do not push.** Restore from the bundle
(`git clone ~/tmp/<name>-sebelum-rewrite.bundle`) and report.

### The tree hash can legitimately move

`filter-repo` rewrites history only — but if the run committed new files *after* the baseline was
captured (derived reports, a renamed skill reference), the tip tree changes for honest reasons and
the tree/count gates will "fail". Reconcile against the bundle instead of abandoning the rewrite:

```bash
git clone -q ~/tmp/<name>-sebelum-rewrite.bundle ~/tmp/bndl
git -C ~/tmp/bndl ls-tree -r --name-only <old-HEAD> > ~/tmp/lama.txt
git ls-files > ~/tmp/baru.txt
comm -23 <(sort ~/tmp/lama.txt) <(sort ~/tmp/baru.txt)   # MUST be empty (nothing lost)
comm -13 <(sort ~/tmp/lama.txt) <(sort ~/tmp/baru.txt)   # additions are fine, name them
```

"Nothing lost, N added" is the pass condition. Say which N and why.

## 5. Force push and verify from the remote, not from the log

```bash
git push --force origin main
git ls-remote origin | head -2                  # must show the new HEAD

git clone --depth 1 git@github.com:<owner>/<repo>.git ~/tmp/verify-clone
git -C ~/tmp/verify-clone rev-parse 'HEAD^{tree}'   # equals local tree
git -C ~/tmp/verify-clone ls-files | wc -l          # equals local count
```

A local `push berjaya` line is not evidence; the clone is. Delete the clone afterwards.

Then refresh anything that caches the SHA (dashboard exporter, status files) and let the backup
script run until `git status --short` is empty again.

## 6. When the subagent dies mid-rewrite

Observed: the delegated run returned
`Delegation owner exited before recording a terminal result; outcome unknown` — the work had in fact
completed. **Do not re-run the rewrite** (a second pass on an already-rewritten repo finds nothing
and risks a half state). Verify instead, read-only:

```bash
du -sh .git; git count-objects -vH                  # did it shrink?
git rev-list --objects --all | grep -E 'tirith|agents\.json\.bak|curator_backups'   # blobs gone?
git remote -v; git ls-remote origin | head -2        # remote back and matching HEAD?
git status --short                                  # tree sane?
ls -lh ~/tmp/*.bundle                               # safety net still on disk?
```

Then run the §4/§5 gates. Report "ejen terputus, aku uji sendiri" with the numbers — that is a
stronger report than a subagent's summary, and it is the only honest one when the summary is missing.

## 7. While you are in there

- Purge **runtime churn** the same way if it was ever tracked (`state/gateway.lifecycle.json`,
  `verification_evidence.db`). Add both to `.gitignore` *and* `git rm --cached` so the nightly job
  stops minting a commit per DB write.
- Keep derived JSON out of the repo entirely (see the `localhost-monitoring-console` skill,
  Phase 2b-ii): an exporter that writes `status.json` into a backed-up home both dirties the tree and
  pins a stale commit id.
