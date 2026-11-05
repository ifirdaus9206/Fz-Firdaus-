# Consolidation pre-flight: mega-tree → existing git repo

Validated on Termux: a 18 GB `ULTIMATE_AI_PROJECT` scheduled to be merged into the
16 MB `agency-agents` git repo (282 agents). The user asked "check first, tell me if
there is a problem, otherwise just do it" — six real blockers existed, so the correct
output was a blocker report + a proposed layout, **not** the move.

## Audit commands (run before touching anything)

```bash
# 1. what is actually there, per child (bare du -sh on 18G blows a 180s timeout)
cd <big-tree> && for f in $(ls -A); do printf "%-24s %s\n" "$f" "$(du -sh "$f" | cut -f1)"; done
du -sh archive/* | sort -rh | head -10

# 2. name collisions with the destination (checked with comm, not eyeballing)
comm -12 <(ls -A <big-tree> | sort) <(ls -A <dest> | sort)

# 3. is the destination a git repo, and is it clean?
cd <dest> && git status --porcelain | head; git fsck --no-progress | head -5

# 4. duplicate runtime trees inside the source
du -sh <big-tree>/tools/hermes-agent-source <big-tree>/tools/hermes-agent-local

# 5. nested homes smuggled inside an archive
find <big-tree>/archive -maxdepth 3 -name ".hermes" -type d
du -sh <big-tree>/archive/root-cleanup/.hermes      # was 920M — a whole old home

# 6. what does the launcher depend on?
readlink -f $PREFIX/bin/hermes
```

## Blocker taxonomy — report these before moving

| # | Blocker | Why it bites | Mitigation |
|---|---|---|---|
| 1 | Launcher target lives **inside** the tree | `$PREFIX/bin/hermes → <tree>/tools/hermes-agent-source/...` (2.3G). Moving kills `hermes` and the running session | move, re-point symlink, restart; or leave the runtime subtree in place |
| 2 | Destination is a clean **git repo** | adding 18G of untracked files makes `git status`/`pull` unusable | put payload under `_workspace/` + `_archive/` and add both to `.gitignore` |
| 3 | **Name collisions** | `README.md`, `LICENSE`, `scripts/` exist on both sides; naive merge overwrites | never overwrite: incoming copy becomes `README.ultimate.md` etc., log every rename |
| 4 | **Nested `.hermes`** inside archive | a full old home (config/skills/sessions) becomes a third home inside a repo | keep it under `_archive/`, never register it as a home |
| 5 | **Duplicates** | `hermes-agent-source` 2.3G vs `hermes-agent-local` 1.6G; code-server trio 939M already re-homed | archive or delete one side with the user's decision, don't merge both |
| 6 | **Size ratio** | 18G into 16M ≈ 1000×; every git operation scans tens of thousands of files | same `_workspace/`+`_archive/` split, and say the ratio out loud |

## Layout that keeps the repo usable

```
<dest-repo>/
├── (unchanged) divisions/, strategy/, docs/, examples/, integrations/, tools.json
├── _workspace/          # gitignored
│   ├── projects/  identity/  docs/  src/  tests/  config/
│   └── myd/              # workflows, prompts, knowledge, database, deployment, logs
└── _archive/            # gitignored
    └── root-cleanup/, caches/, projects-repo/
```

Anything that is runtime (launcher target, live venv) stays OUT of the repo.

## Reporting shape the user accepted

1. What was done (translation cancelled / server started) with evidence.
2. Numbered blocker list, each with the concrete size or path that proves it.
3. Proposed layout as a tree diagram.
4. Explicit "what I will NOT move" list.
5. Numbered questions (A/B/C) for the decisions only the user can make.

Never report a blocker list and then start moving anyway — the user's instruction was
conditional ("if there is a problem, tell me").

## Bonus findings from the same session

- **Static-page verification**: serve a legacy page to prove it works rather than
  describing it —
  `python3 -m http.server 8080 --bind 127.0.0.1` (background), then
  `curl -s -o /dev/null -w "%{http_code} %{size_download}b\n" http://127.0.0.1:8080/login.html`.
  200 + byte count is proof; `ss`/`netstat` are often absent in Termux, so curl is the
  portable check. Say plainly when the "login" form is a static demo (alert-only, no
  password validation) instead of implying real auth.
- **pkill self-kill**: `pkill -f translate_agency_ms.py` matches the shell whose own
  command line contains that string, so the tool call dies with exit `-15`. Always use a
  bracket pattern so the pattern cannot match itself:
  `pkill -f '[t]ranslate_agency_ms'`.
- **Translation is opt-in only.** The user cancelled a 282-file Malay translation pass
  mid-run: agent personas must stay English so the agents themselves parse the
  instructions; a translated mirror is for human reading, never for the tool catalog.
  Ask before starting any bulk translation of agent/prompt content.
