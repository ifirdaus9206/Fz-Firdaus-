# Pruning `backups/` and executing the profile symlink

Measured on a Termux agent home (`~/.hermes20`, 2026-11-24), as the last two phases of a
17 GB → 6.1 GB tidy. Both phases were explicitly requested by the owner *after* the main
deletion phase ("nombor 2", "jalankan nombor 1"), which is the correct sequencing — never fold
them into the earlier passes.

---

## 1. Pruning `backups/` (94 MB → 26 MB)

### Contents found

```
56M  state.db.bak-pra-migrasi-1328       ← DB backup from a migration weeks earlier
17M  profiles-skills-lama-<date>.tar.gz  ← created minutes earlier by the symlink phase
57K  SOUL.md.bak  +  SOUL.md.agency-backup   ← identical twins
4.1M ×5  plugins/agents.json.bak-*       ← a backup series with no retention rule
2.6K config.yaml.bak-2026-11-18 · 789B config.yaml.bak-mcp · 2.2K config.yaml.bak.<plugin>
3.4K/2.4K SOUL.md.bak-ketua-<date> ×2
1.2K email_autosort.sh.bak · 214B console_keeper.sh.bak
```

### The three verdicts and their proofs

**Verdict A — DB backup is redundant because the live DB is provably healthy.**

```bash
python3 -c "
import sqlite3
c=sqlite3.connect('/data/data/com.termux/files/home/.hermes20/state.db')
print('integrity:', c.execute('PRAGMA integrity_check').fetchone()[0])
print('jadual:', c.execute(\"select count(*) from sqlite_master where type='table'\").fetchone()[0])
print('mesej:', c.execute('select count(*) from messages').fetchone()[0])
"
```

Output that justified the delete:

```
integrity: ok
jadual: 23
mesej: 12301
```

That triple is the whole argument: the file opens, the schema survived, and the row count is
plausible for a live agent home. A backup that predates a completed migration adds nothing once
those three hold. **Do not** delete on `ls -l` size alone, and do not delete the backup of a DB
you have not opened in this session.

**Verdict B — an exact twin, proven by hash, not by name.**

```bash
md5sum backups/SOUL.md.bak backups/SOUL.md.agency-backup
# 9dc457a233fd408dc0d2a6d92e96d9ef  backups/SOUL.md.bak
# 9dc457a233fd408dc0d2a6d92e96d9ef  backups/SOUL.md.agency-backup
```

Different filenames, same bytes. Keep one. Names like `-backup`, `-bak`, `-old`, `-copy` are
*claims* about provenance, never evidence of difference.

**Verdict C — a backup series with no retention rule: keep the two ends.**

Five `agents.json.bak-<date>` files (4.0–4.1 MB each, 20 MB total) accumulated from repeated CRUD
tests. The oldest and the newest bracket the whole history; the three middles are strictly
redundant for any realistic recovery question.

Rule of thumb worth applying to every `*.bak-<date>` series:

| Members | Keep |
|---|---|
| 1–2 | all |
| 3–5 | oldest + newest |
| 6+ | oldest + newest + the last one before any big structural change |

### End state

```
26M  total
17M  profiles-skills-lama-<date>.tar.gz   ← intentionally kept ~1 week
57K  SOUL.md.bak (+2 small persona versions)
 3.4K plugins/ (oldest 2026-10-22 + newest bak-watak)
 2.6K config.yaml.bak-2026-11-18 (+2 small)
 1.4K two script .bak
```

Report the number as a delta with the proof beside it: "94 MB → 26 MB; DB disahkan
`integrity_check = ok`, 23 jadual, 12,301 mesej". The owner audits proof, not intentions.

---

## 2. Executing the profile symlink (121 MB → 54 MB)

### Precondition — establish that the copies are *stale*, not *duplicated*

A single `md5sum` on one skill file is not enough. Compare the whole relative-path set:

```python
import os, hashlib, glob
H = os.path.expanduser("~/.hermes20")

def snap(d):
    out = {}
    for p in glob.glob(d + "/**/SKILL.md", recursive=True):
        out[os.path.relpath(p, d)] = hashlib.md5(open(p, 'rb').read()).hexdigest()
    return out

base = snap(H + "/skills")
print("default:", len(base))          # 115
for prof in sorted(os.listdir(H + "/profiles")):
    d = f"{H}/profiles/{prof}/skills"
    if not os.path.isdir(d):
        continue
    s = snap(d)
    diff = [k for k in set(s) | set(base) if s.get(k) != base.get(k)]
    print(f"{prof:12} {len(s):3} fail | sama: {s == base} | beza: {len(diff)}")
```

Result that changed the plan:

```
default: 115
assistant     71 fail | sama sepenuhnya: False | beza: 45
finance       71 fail | sama sepenuhnya: False | beza: 45
...
```

`beza: 45` plus 44 skills that exist only in the default tree (`localhost-monitoring-console`,
newer `hermes-console`) means the profiles hold a **stale snapshot**, not a duplicate. Symlinking
therefore *changes behaviour* — it upgrades every profile from 71 to 115 skills. That is a
decision for the owner, and the reply must say so in those terms, with the size delta attached
(67 MB), not be performed as housekeeping.

### Execution

```bash
cd ~/.hermes20
tar czf "backups/profiles-skills-lama-$(date +%F).tar.gz" profiles/*/skills
# 121 MB of markdown → 17 MB archive; this is what makes the swap reversible

for p in profiles/*/; do
  if [ -d "$p/skills" ] && [ ! -L "$p/skills" ]; then
    rm -rf "$p/skills"
    ln -s "$HOME/.hermes20/skills" "$p/skills"
    echo "  $p → symlink"
  fi
done
```

Verify two ways, because they prove different things:

```bash
# (a) the filesystem: the link resolves and the full set is visible
for p in profiles/*/; do
  printf '  %-24s %s skill\n' "$p" "$(find -L "$p/skills" -name SKILL.md | wc -l)"
done
#   115 for each of the seven profiles

# (b) the loader: Hermes itself now sees them
HERMES_PROFILE=finance hermes skills list | tail -1
#   0 hub-installed, 67 builtin, 44 local — 111 enabled, 0 disabled
#   (that profile reported 71 skills before the swap)
```

### Traps

1. **`find` without `-L` reports 0 skills** through a symlinked directory — it does not follow
   the link, which looks exactly like a broken swap. Always `find -L`.
2. **Relative link targets break on move.** Use the absolute `$HOME/.hermes20/skills`.
3. **File count alone is not acceptance.** A wrong-but-readable target (e.g. an old backup tree)
   also yields a count. The `hermes skills list` line is what proves the agent resolved it.
4. **Don't delete the tarball in the same phase.** Keep it ~a week; it is 17 MB and it is the only
   copy of the profiles' previous behaviour.
5. **`du -sh profiles` after the swap only moves if the originals are gone** — verify with
   `ls -l profiles/finance/skills` showing `->`, not just by re-measuring.

---

## 3. Reporting shape the owner accepted

Two short tables, each row carrying size + proof, then the end-state number block:

```
backups/   94 MB → 26 MB
  state.db.bak    56 MB  → dibuang; state.db disahkan integrity ok, 23 jadual, 12,301 mesej
  SOUL twin       57 KB  → dibuang; MD5 sama tepat
  agents.json ×3  12.3MB → dibuang; dikekalkan asal + terkini

profiles/  121 MB → 54 MB
  7 profil × 71 skill (stale, 45 fail beza) → symlink ke 115 skill
  sandaran: backups/profiles-skills-lama-<date>.tar.gz (17 MB)
  bukti: HERMES_PROFILE=finance hermes skills list → 111 enabled
```

Then the "apa yang masih tinggal" list, because a tidy report that claims completion while
`legacy-ultimate/` still sits at 539 MB reads as a cover-up.
