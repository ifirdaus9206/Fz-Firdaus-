# Retiring stale Hermes installs / leftover homes — audit playbook

Validated on Termux, Oct 2026, when asked "berapa hermes yang ada dalam ini" and then
"analisis dulu sebelum padam — kalau tak ada yang bahaya, padam".

Outcome of that run: 6 suspected leftovers; 4 provably safe (deleted, ~1.6 GB);
2 were **not** junk — archived Hermes homes holding 86 and 63 sessions of history.
Stripping their bundled source (not deleting them) freed another ~1.43 GB.

---

## Phase 1 — enumerate the class

```bash
which -a hermes
readlink -f "$PREFIX/bin/hermes"
ls -d ~/.hermes* ~/.hermes_venvs/* 2>/dev/null
ls -la ~/.hermes20/bin            # per-home wrappers
```

Then version-stamp every candidate — never assume the global `hermes` is any given home:

```bash
hermes --version | head -3
~/.hermes20/bin/hermes19 --version | head -3
cat ~/.hermes_venvs/<venv>/pyvenv.cfg          # command= shows the path it was built from
```

Classify each hit into exactly one bucket:

| Bucket | Evidence | Default action |
|---|---|---|
| live home | `HERMES_HOME` / wrapper / launcher points at it, `--version` works | keep |
| stale source clone | `.git` clean, HEAD == live HEAD, remote = upstream | delete (rebuildable) |
| unusable venv | `bin/` has only pip, no `hermes`, no wrapper references | delete |
| broken wrapper | script execs a path that no longer exists | delete |
| archived HOME | contains `state.db`, `sessions/`, `memories/`, `.env`, `auth.json` | **never blind-delete** |

## Phase 2 — never trust the directory name

The trap that nearly cost real data: two dirs described as "source copies" were full homes.

```
archive/ultimate-2026-10/root-cleanup/.hermes       920 MB
legacy-ultimate/config/hermes-state-ref             636 MB
```

Probe before writing the word "copy" in any report:

```bash
for d in "$CANDIDATE"/*; do du -sh "$d" 2>/dev/null | sort -hr | head -8; done
find "$H" -maxdepth 1 \( -name 'state.db*' -o -name 'auth.json' -o -name '.env' \
  -o -name 'sessions' -o -name 'memories' -o -name 'cron' -o -name 'skills' \) -print
```

Both turned out to hold `state.db` + `.env` (203 keys incl. `TELEGRAM_BOT_TOKEN`) +
`auth.json` + 65 cron files + 22–24 skill dirs. `.env`/`auth.json` in an archive also
means plaintext credentials sitting on disk — report it, do not "clean" it unasked.

## Phase 3 — prove a git clone is redundant

```bash
g=none
for g in "$LIVE/hermes-agent" "$CANDIDATE/hermes-agent"; do
  echo "--- $g"
  git -C "$g" log -1 --format='HEAD %h %ad %s' --date=short
  echo -n "uncommitted: "; git -C "$g" status --porcelain | wc -l
  echo -n "stash: ";       git -C "$g" stash list | wc -l
  git -C "$g" remote -v | head -1
done
```

- `status --porcelain` includes untracked, so `0` means nothing local to lose.
- `--ignored` only listing `__pycache__/`, `hermes_agent.egg-info/` is regenerable noise.
- Same HEAD as the live tree + upstream remote reachable = `rm -rf` is safe; say
  "boleh dibina semula dari GitHub" in the report.
- A different HEAD (e.g. `aaf9688` vs `863e3131`) is not automatically junk either —
  that copy was still an archived home, judged by its state, not its git log.

## Phase 4 — references, symlinks, live processes

```bash
for pat in hermes-source-old hermes19_alt hermes-state-ref hermes19_source hermes.backup; do
  echo "--- $pat"
  grep -rIl --exclude-dir=.git --exclude-dir=archive --exclude-dir=cache \
    "$pat" "$HOME/.hermes20/config.yaml" "$HOME/.hermes20/bin" "$HOME/.hermes20/scripts" \
    "$HOME/.hermes20/cron" "$HOME/.hermes20/plugins" "$HOME/.hermes19/config.yaml" \
    "$PREFIX/bin" 2>/dev/null | head -5
done
find "$HOME/.hermes20" "$HOME/.hermes19" "$PREFIX/bin" -maxdepth 3 -type l | while read -r l; do
  t=$(readlink -f "$l"); case "$t" in *<candidate>*) echo "$l -> $t";; esac; done
ps -ef | grep -E '<candidate>' | grep -v grep
```

Pitfall hit here: a shell loop written with `$por` instead of `$pat` printed six empty
results, which reads exactly like "no references found". Always sanity-check that the
probe *can* find something (grep for a known-good string first) before trusting silence.

## Phase 5 — prove state is unique (read-only)

```bash
python3 - <<'PY'
import sqlite3, os
for n,p in {
 "archive A":"/path/root-cleanup/.hermes/state.db",
 "archive B":"/path/hermes-state-ref/state.db",
 "live .hermes20":"/path/.hermes20/state.db",
}.items():
    c=sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    print(n, os.path.getsize(p)//1024//1024, "MB",
          {t: c.execute(f"select count(*) from {t}").fetchone()[0]
           for t in ("sessions","messages")})
PY
```

Result: A = 86 sessions / 8,323 messages, B = 63 / 2,458, the smaller
`archive/legacy-hermes-2026-10-21` = 7 / 549. Conclusion: A and B are the only copy of
149 sessions → deleting them is data loss, regardless of how "old" the folder looks.

## Phase 6 — strip instead of delete

Size split is the whole insight: the bundled source dominates, the history is small.

```
root-cleanup : total 920 MB = hermes-agent 760 + lsp 43 + bin 19 + logs 6.8 + checkpoints 7
               history    = state.db 48 + wal 5.9 + sessions 4 + skills 21 + cron 0.9
state-ref    : total 636 MB = hermes-agent 529 + lsp 43 + bin 19 + logs 3.6
               history    = state.db 16 + wal 4 + sessions 2.4 + skills 14 + cron 0.9
```

```bash
for h in "$A" "$B"; do
  rm -rf "$h"/hermes-agent "$h"/lsp "$h"/bin "$h"/checkpoints "$h"/logs "$h"/cache
done
```

920 → 85 MB and 636 → 41 MB. Kept: `state.db*`, `sessions/`, `memories/`, `cron/`,
`skills/`, `config.yaml*`, `SOUL.md`, `kanban.db*`, `.env`, `auth.json`.

## Phase 7 — verification that must appear in the report

```bash
python3 -c 'import sqlite3;c=sqlite3.connect("file:.../state.db?mode=ro",uri=True);
print(c.execute("pragma integrity_check").fetchone()[0],
      c.execute("select count(*) from sessions").fetchone()[0],
      c.execute("select count(*) from messages").fetchone()[0])'
find "$h/sessions" -type f | wc -l; find "$h/cron" -type f | wc -l
hermes --version | head -2; ~/.hermes20/bin/hermes19 --version | head -2
df -h "$HOME" | tail -1
```

Expected shape: `integriti=ok sesi=86 mesej=8323` unchanged, session/cron counts unchanged,
every surviving install still printing a version, and `df` showing the freed GB.
Never report freed space from the `rm` exit code alone — `df` before/after is the evidence.

## Phase 8 — when a clarify prompt times out

The user was asked to choose among strip / strip+credentials / keep / delete-all and did
not answer in time. Chosen default: **the least destructive option that still solves the
stated ask** — strip bundled code, keep all history, leave `.env`/`auth.json` untouched
(credentials are the user's decision), then report exactly what was held back and why.
