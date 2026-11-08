# Attaching an existing local repo to a fresh GitHub remote (no `gh` login)

Session 2026-11-06, `~/.hermes20` (4,674 tracked files, 28 MB `.git`) → new GitHub repo
`ifirdaus9206/Fz-Firdaus-`. SSH key auth already worked; `gh auth status` said "not logged in"
and no token existed. Everything below worked with SSH only.

## 1. Find out whether the remote repo actually exists

`gh` is not authenticated, so `gh repo view` is useless. Private repos also return 404 from the
unauthenticated REST API — so the API cannot prove existence either. The reliable probe is
`ls-remote` over the SSH key you just proved works:

```bash
GIT_SSH_COMMAND='ssh -o BatchMode=yes -o ConnectTimeout=12' \
  git ls-remote git@github.com:<owner>/<repo>.git
```

- repo exists (empty or not) → prints refs and exits 0; an **empty repo** prints nothing but
  still exits 0. Capture the exit code: `… ; echo "exit=$?"`.
- repo missing, or exists but the key has no access → `ERROR: Repository not found.` +
  `fatal: Could not read from remote repository.` exit 128.

Probe a shortlist of plausible names in one pass rather than asking the user again; GitHub repo
names are case-insensitive for SSH access, so `Fz-Firdaus-`/`fz-firdaus-` behave the same.

## 2. Parse the URL the user pastes — keep the trailing punctuation

The owner pasted `https://github.com/ifirdaus9206/Fz-Firdaus-#fz-firdaus-`. The `#…` part is a
browser fragment (a GitHub heading anchor), **not** part of the name. The real repo is
`Fz-Firdaus-` — with a trailing hyphen. Two traps:

- Strip everything from `#` onward before using the path.
- Do **not** "tidy" punctuation. `Fz-Firdaus` (hyphen dropped) → `Repository not found`.
  Verify by probe, never by intuition, and echo the exact name you used in the report.

## 3. Merge the repo the web UI created with README

Creating a repo with "Add a README" gives it an initial commit that shares no history with the
local repo, so a plain push is rejected (non-fast-forward / unrelated histories).

```bash
git remote add origin git@github.com:<owner>/<repo>.git
git fetch origin main
git ls-tree -r --name-only FETCH_HEAD      # know exactly what is already there
git merge origin/main --allow-unrelated-histories -m "gabung README dari GitHub"
```

Check for a same-named file first (`git ls-files | grep -iE '^readme'`). If the local repo has
its own README, this merge is a real content conflict and needs a human decision — not a silent
`-X ours`.

Never `--force` here. The initial commit is the owner's content.

## 4. PITFALL #5 — `git push origin HEAD` lands on a branch named after the local branch

`templates/backup_github.sh` pushes `git push origin HEAD`. That means "push the current branch
to the remote branch **of the same name**". Local branch was `master`, GitHub's default was
`main`, so the run produced:

```
log:  2026-11-06 04:37  push berjaya: f0b2cc1        ← script says success
$ git ls-remote origin
6abbb65  refs/heads/main                               ← old README-only commit
f0b2cc1  refs/heads/master                             ← all 4,683 files, invisible
```

The script's success line is technically true and completely misleading: the repo page still
showed a two-line README, because the default branch (`main`) never moved. **Always verify with
`git ls-remote origin` and compare the SHA against `git rev-parse HEAD` of the branch GitHub
displays** — not against the script's log line.

Fix (fast-forward path, keeps the initial commit):

```bash
git branch -m master main                       # align local name with GitHub default
git push -u origin main                         # 6abbb65..f0b2cc1  main -> main
git push origin --delete master                 # remove the stray branch
git ls-remote origin                            # expect exactly one refs/heads/main
git status -sb                                  # ## main...origin/main
```

Then re-run the backup script: with names aligned, `git push origin HEAD` is correct forever.
Alternative if renaming is unwanted: change the script to `git push origin HEAD:main`.

## 5. Prove visibility without a token

The REST API returns 200 for public and 404 for private-or-missing, which is enough to answer
"is my backup readable by strangers?":

```bash
curl -s -o /dev/null -w 'HTTP %{http_code}\n' \
  https://api.github.com/repos/<owner>/<repo>
```

`HTTP 200` = **public**. A repo created from the web form defaults to public, and a backup of an
agent home ships `SOUL.md`, `memories/`, `profiles/`, cron reports — private data. Report it as
a named risk with the exact curl output, and give the owner the manual path (Settings → General
→ Danger Zone → Change visibility → Private) or offer a PAT if they want it done for them. Do
not quietly accept public because the push succeeded.

## 6. Verification block that actually settles it

```bash
git ls-remote origin                                  # ONE ref, matches local HEAD
git log --oneline -3 origin/main
git ls-tree -r --name-only origin/main | wc -l        # compare with local git ls-files | wc -l
git ls-tree -r --name-only origin/main \
  | grep -E '(^|/)(\.env$|auth\.json$|config\.yaml$|state\.db$|id_ed25519$)'   # must be empty
git show origin/main:README.md                        # owner's content survived the merge
```

Also re-run the backup script once and require silence (`exit=0`, empty stdout) — that is the
only proof the nightly cron will be quiet, since a fresh repo with a renamed branch is exactly
where the script's assumptions break.
