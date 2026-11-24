# Runtime tidy-up: logs, `node_modules`, profile skill trees

Measured on a Termux agent home after the big deletions (17 GB → 6.2 GB). These are the
"phase 4" leftovers — small individually, and each one has a wrong-headed shortcut that looks
obvious.

## 1. Logs — truncate, don't archive

```
before: 27 MB            after: 4.6 MB
  web-server.log            6.6 M   -> truncated to 0
  agent.log.1               5.0 M   -> deleted
  agent.log                 4.5 M   -> truncated
  hermes-dash-tunnel.log    3.8 M   -> truncated
  errors.log.1              2.0 M   -> deleted
  dashboard-tunnel.log      582 K   -> truncated
  gateway.log               1.4 M   -> left alone (live, small)
```

```bash
cd ~/.hermes20/logs
rm -f *.log.1
for f in web-server.log agent.log hermes-dash-tunnel.log dashboard-tunnel.log; do
  [ -f "$f" ] && : > "$f"
done
du -sh .                       # 27M -> 4.6M
du -sh hermes-console hermes-keeper   # svlogd dirs still there, untouched
```

Rules:

- `: > file` (truncate) is correct for a log a running process holds open — it keeps appending at
  the new offset. `rm` would leave the process writing to a deleted inode and the space
  unreclaimed until restart.
- Delete `*.log.1` freely — those are already-rotated copies.
- **Never** delete `logs/<service>/` (`lock`, `current`, `@*.s`): svlogd owns them. Deleting `lock`
  breaks the logger for that service.
- Keep the live `gateway.log` — 1.4 MB is cheaper than losing the restart/unclean-exit history the
  watchdog counts.

## 2. `npm prune` — the honest no-op

```
node_modules before : 91M
npm prune --no-audit --no-fund
node_modules after  : 91M      ← unchanged
```

`prune` only drops *extraneous* packages (installed but not reachable from `package.json`). An app
built by `npm run build`/`dev` has none, so the tree stays. Reply with the measurement instead of a
saving; offer the real options (delete the app, or `rm -rf node_modules` and accept that it cannot
run until `npm install`).

## 3. Profile `skills/` — compare, don't assume "duplicate"

The assumption ("7 profiles × 71 skills = one shared set, so symlink it") was false. Hash-compare
the relative path sets:

```python
import os, hashlib, glob
H = os.path.expanduser("~/.hermes20")
def snap(d):
    return {os.path.relpath(p, d): hashlib.md5(open(p,'rb').read()).hexdigest()
            for p in glob.glob(d + "/**/SKILL.md", recursive=True)}
base = snap(H + "/skills")
for prof in sorted(os.listdir(H + "/profiles")):
    d = f"{H}/profiles/{prof}/skills"
    if not os.path.isdir(d): continue
    s = snap(d)
    diff = [k for k in set(s) | set(base) if s.get(k) != base.get(k)]
    print(f"{prof:12} {len(s):3} fail | sama: {s == base} | beza: {len(diff)}")
```

Result on this home:

```
default: 115 skills
assistant/engineering/finance/marketing/ops/sales/siti: 71 each
  sama sepenuhnya : False
  beza            : 45      ← 45 files differ, plus 44 skills absent from profiles
  contoh          : localhost-monitoring-console/SKILL.md (missing)
                    software-development/hermes-console/SKILL.md (older copy)
```

So the three possible states are:

| State | Test | Meaning |
|---|---|---|
| identical | path sets equal **and** all hashes equal | pure duplicate → symlink/copy delete is housekeeping |
| stale subset | paths mostly shared, hashes differ, new skills missing | **behavioural upgrade** — needs owner approval |
| divergent | profiles have skills the main tree lacks | never symlink; merge would destroy work |

Offer, in this order, and let the owner choose:

1. `ln -s ~/.hermes20/skills <profile>/skills` → 115 skills, −57 MB, all 7 profiles change at once.
2. `cp -a` the current tree into each profile → same content, no space saved, no symlink risk.
3. leave as-is.

Do the swap only after an explicit yes, and afterwards verify one profile resolves a `SKILL.md`
that did not exist before the change (proof the symlink is followed, not just created).

## 4. FUSE phantom directory

```
$ du -sh /sdcard/.../ultimate-2026-10
26K
$ find … -type f | wc -l
0
$ find … -type d | wc -l
6
$ rm -rf …                     # fails again
rm: cannot remove '…/blob-stream@0.1.3@@@1': Directory not empty
$ rmdir …                      # same message on an empty path
```

Cause: Android `/sdcard` is `/dev/fuse`; entries can linger after their contents are gone. It has
**no files**, costs **no space in the home**, and disappears when removed from the Files app (or
sometimes after a remount). Retrying destructive variants is worse than useless — the approval
layer blocks the retry and the turn stalls:

> `BLOCKED: Command timed out without user response. … Silence is not consent.`

Sequence that stays safe: one `chmod -R u+w` + `rm -rf`, then report the three facts and hand the
path to the owner.

## 5. Numbers to quote at the end of such a pass

Publish only from a completed state (a `du` taken mid-delete was wrong three times: 8.2 G → 3.7 G
→ 6.2 G actual).

```
~/.hermes20          17 GB -> 6.2 GB
  tools/             5.5 -> 4.4 G   (dedupe 962 M + git gc ~800 M)
  archive/           8.7 G -> 714 M (caches + root-cleanup)
  legacy-ultimate/   2.1 G -> 539 M (node_modules/.venv only)
  logs/              27 M -> 4.6 M
cakera bebas         83 GB -> 95 GB
scripts/             35 -> 29 (six one-shot scripts moved to external arkib, 0 broken)
services             5 HIDUP, konsol 8787 = 200
```
