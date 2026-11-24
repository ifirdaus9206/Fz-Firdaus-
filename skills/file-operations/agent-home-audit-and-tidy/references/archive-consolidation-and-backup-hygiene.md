# Archive consolidation, backup hygiene, and log rotation

Measured on a Termux agent home (`~/.hermes20`), pass that took **17 GB → 5.4 GB**.
This file covers the *closing* moves of that pass: gathering old projects under one root,
keeping the nightly git backup working, and automating log rotation so the tidy sticks.

---

## 1. Why the pass was not finished at 6.4 GB

After the deletion phase the owner answered the open list item by item:

| Item | Owner's answer | Action taken |
|---|---|---|
| `legacy-ultimate/` 539 MB | keep | moved into archive root |
| `archive/ultimate-2026-10` 659 MB | keep | moved into archive root |
| `tools/others/delphitools-cli` 784 MB | "semak" (check) | `target/` was 782 MB of it → deleted, tool now **1.9 MB** |
| `cline-repo` + `bun-repo` 1.0 GB | keep | untouched |
| `profiles-skills-lama.tar.gz` 17 MB | "ok buang" | deleted |
| FUSE phantom dir | "nanti aku padam" | left alone |
| no log rotation | "cadang cron mingguan" | `rotate_logs.sh` + weekly job |
| `sessions/` + `cache/` 5 MB | "ok" | untouched |

Lesson: an itemised "masih tinggal" table is what lets the owner answer in one message. A prose
summary gets questions instead of decisions.

---

## 2. `target/` — the build tree that masquerades as a tool

```
tools/others/delphitools-cli   784M   total
  target/                      782M   cargo build output
  src/                         656K   actual source
  .git/                        484K
```

`du -sh <tool>` says "784 MB, probably too big to keep". `du -sh * .[!.]* | sort -hr` inside it
says "1.9 MB of content". Always scan inside a vendored tool before proposing its deletion — the
build tree is never the tool.

---

## 3. Consolidating snapshots under one owner-named root

Owner's instruction: *"semua projek lama tukar nama pada nama kau"* — the archive is named after
the owner, not after the task.

```bash
cd ~/.hermes20
mkdir -p arkib-ketua
mv legacy-ultimate arkib-ketua/projek-ultimate-aina
mv archive/* arkib-ketua/
rmdir archive
```

Result:

```
arkib-ketua/                     1.3 GB
├── README.md                    rules + folder table
├── ultimate-2026-10/            659 MB
├── projek-ultimate-aina/        539 MB
├── legacy-hermes-2026-10-21/     31 MB
├── legacy-AINA-2026-10-17/       24 MB
├── legacy-hermes19-2026-10-21/  291 KB
└── system-backup-2026-10-27/     64 KB
```

`arkib-ketua/README.md` contents that mattered:

1. Table: folder · size · origin · state.
2. **Read-only** — no service, cron or script references it.
3. Source kept, dependencies removed and **rebuildable** (`npm install`, `python -m venv`,
   `cargo build`).
4. Deleting any folder here has **no effect** on the live system.

Also rewrite the archived project's own README header:

```markdown
# ULTIMATE AI PROJECT — Arkib Ketua

> **Status:** ARKIB (2026-11-24). Projek lama AI agent Aina.
> Kini disimpan di `~/.hermes20/arkib-ketua/projek-ultimate-aina/`.
> Kebergantungan dibuang — kod sumber kekal.
```

Without that, the next session reads "# ULTIMATE AI PROJECT" and treats a dead project as live.

---

## 4. Backup broke exactly when the archive moved in

First `backup_github.sh` run after consolidation:

```
error: '<archive>/projek-ultimate-aina/projects/agent-factory/' does not have a commit checked out
error: unable to index file '<archive>/projek-ultimate-aina/projects/agent-factory/'
fatal: adding files failed
2026-11-24 23:34 GAGAL: git add
```

Cause: the archived projects contain their **own `.git` directories** (and paths that look like
embedded repos/submodules), so `git add` refuses the tree.

Fix — an archive is not config history:

```bash
printf '\n# Arkib projek lama — besar & ada repo git bersarang\narkib-ketua/\ntools/others/\n' >> .gitignore
bash scripts/backup_github.sh 2>&1 | tail -3
git log --oneline -1        # a NEW hash is the only proof the backup worked
```

Observed side benefit: excluding 1.3 GB of archive made the push noticeably faster.

**Rule:** the backup script reports failure only into `logs/backup.log`. Every tidy pass must end
with `git log --oneline -1` showing a fresh timestamp, not with "script exited 0".

---

## 5. `scripts/rotate_logs.sh` — tested shape

```bash
#!/data/data/com.termux/files/usr/bin/bash
# rotate_logs.sh — putaran log mingguan (senyap bila tiada apa dilakukan)
#   - *.log melebihi 5 MB      → dipotong ke 0 (proses terus menulis)
#   - arkib *.log.N > 7 hari   → dibuang
#   - logs/<servis>/ TIDAK disentuh — svlogd/runit uruskan
set -u
LOG_DIR="${ROTATE_ROOT:-$HOME/.hermes20/logs}"
MAX=$((5 * 1024 * 1024))
DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1

for F in "$LOG_DIR"/*.log; do
  [ -f "$F" ] || continue
  SZ=$(stat -c%s "$F" 2>/dev/null || echo 0)
  if [ "$SZ" -gt "$MAX" ]; then
    MB=$((SZ / 1048576))
    if [ "$DRY" -eq 1 ]; then echo "[dry] akan potong $F (${MB}MB)"
    else : > "$F"; echo "dipotong: $(basename "$F") (${MB}MB → 0)"; fi
  fi
done

find "$LOG_DIR" -maxdepth 1 -type f -name '*.log.[0-9]*' -mtime +7 2>/dev/null | while read -r F; do
  if [ "$DRY" -eq 1 ]; then echo "[dry] akan buang $F"; else rm -f "$F"; echo "dibuang: $(basename "$F")"; fi
done
exit 0
```

Run `--dry-run` immediately after a manual truncation: **no output** is the acceptance test.

### Registering it (three calls, in order)

```
create(schedule="0 4 * * 0", name="Putaran log mingguan (Ahad 04:00)", no_agent=true, script="rotate_logs.sh")
   → rejected: "Cannot set no_agent=True on a job without a script"

create(schedule="0 4 * * 0", prompt="...", name="...")        # job id returned
update(job_id, script="rotate_logs.sh")
update(job_id, no_agent=true)
cronjob list → "script": "rotate_logs.sh", "no_agent": true    # verify, don't assume
```

Silent-when-healthy is the contract: empty stdout means no message is delivered, which is what a
rotation job should produce on a normal week.

---

## 6. Final numbers from the pass

| | Before | After |
|---|---|---|
| whole home | 17 GB | **5.4 GB** |
| `tools/` | 5.5 GB | 3.6 GB |
| `arkib-ketua/` (was `archive/` + `legacy-ultimate/`) | 10.8 GB | 1.3 GB |
| `backups/` | 94 MB | 8.2 MB |
| `logs/` | 27 MB | 4.6 MB |
| `profiles/` | 121 MB | 54 MB |
| scripts | 35 | 30 (6 one-off moved out, 1 rotation script added) |
| cron jobs | 15 | 16 |

Everything above was verified with `hermes-status` (console 200, 5 services up) and a new git
commit — not with the script's exit code.
