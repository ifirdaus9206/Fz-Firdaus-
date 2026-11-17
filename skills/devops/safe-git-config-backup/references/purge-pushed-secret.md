# Purging a pushed secret from a git remote (recipe + evidence shapes)

Session: 2026-11-12, `~/.hermes20` → `git@github.com:ifirdaus9206/Fz-Firdaus-` (**public**),
GitHub account password written as prose into `memories/MEMORY.md` and two skill docs.

## 1. Find every occurrence before touching anything

```bash
git grep -l '<secret>' HEAD                                   # files in HEAD (tracked copies)
git grep -l '<secret>' --cached                               # index
git log --all --oneline -S'<secret>' --                        # commits that touched it
grep -rIl '<secret>' . --exclude-dir=.git --exclude-dir=archive \
  --exclude-dir=cache --exclude-dir=node_modules               # working tree
```

`-S` (pickaxe) is the cheap history probe. Expect noise from vendored trees
(`archive/`, `legacy-*`, npm cache) — exclude them or the "hit list" is unreadable.

## 2. Visibility + tooling

```bash
curl -s -o /dev/null -w 'HTTP %{http_code}\n' https://api.github.com/repos/<o>/<r>
pip install --quiet git-filter-repo && which git-filter-repo
ssh -o StrictHostKeyChecking=no -T git@github.com   # "Hi <login>! You've successfully authenticated"
```

`gh auth status` said "not logged into any GitHub hosts" — irrelevant, SSH push worked. Do not
stall the incident on `gh auth login` when a key is already loaded.

## 3. Rewrite

```bash
printf '<secret>==><REDACTED-PASSWORD>\n' > ~/tmp/redact.txt
cd <repo> && git filter-repo --replace-text ~/tmp/redact.txt --force
# NOTICE: Removing 'origin' remote; ... (was git@github.com:<o>/<r>.git)
git remote add origin git@github.com:<o>/<r>.git
git add -A && git commit -q -m 'selamat: buang password GitHub daripada fail sandaran'
git push --force origin main
#  + 984b44f...ceac4f8 main -> main (forced update)
```

`--force` was needed because the repo was not a fresh clone (dirty working tree with unrelated
cron churn). filter-repo reported `Parsed 1 commits / 16 / 18` and finished in ~3 s on a 30 MB
repo; no need for `filter-branch` fallbacks.

## 4. Prove it from the remote (never from local git)

```bash
B=https://raw.githubusercontent.com/<o>/<r>/main
for p in memories/MEMORY.md skills/.../SKILL.md skills/.../references/x.md; do
  echo "$p -> padanan:$(curl -s $B/$p | grep -c '<secret>') $(curl -s -o /dev/null -w 'HTTP %{http_code}' $B/$p)"
done
# padanan:0 + HTTP 200 = branch is clean and the file really exists (not a 404 false pass)

# images / binaries never tracked?
curl -s "https://api.github.com/repos/<o>/<r>/git/trees/main?recursive=1" \
  | grep -Eio '"[^"]+\.(png|jpg|jpeg|webp)"' | head; echo '[tamat]'
git log --all --pretty=format: --name-only --diff-filter=A | sort -u \
  | grep -Ei '\.(png|jpg|jpeg|webp)$' | head; echo '[tamat senarai imej dlm sejarah]'

# residual: old commits still readable by SHA?
for s in 984b44f f0b2cc1; do
  curl -s -o /dev/null -w "$s: HTTP %{http_code}\n" \
    https://api.github.com/repos/<o>/<r>/commits/$s
done      # 200/200 in this session → exposure NOT closed by force push alone
```

Two empty greps together prove "no image was ever in this repo"; report that as a finding, not
as work performed.

## 5. Honest closing statement

- Branch `main` clean; local HEAD == remote HEAD.
- Old commits still fetchable by SHA until GitHub GC → credential must be treated as leaked.
- Owner-only actions: rotate password; or delete+recreate repo (only guaranteed purge);
  or GitHub Support cache removal.
- Never paste the recovered secret into the chat while reporting — name the file and the count.
