---
name: filesystem-tree-relocation
description: Move/merge directory trees safely, repair path deps, verify.
category: file-operations
tags: [move, relocation, mv, symlink, migration, filesystem, termux, verification]
---

# Filesystem Tree Relocation

Use when: the user wants a whole directory / project tree **moved** (not copied) into
another location — "pindahkan X ke dalam Y", "move this folder into that home",
consolidating trees, relocating a tree that hosts a running runtime, or splitting
sub-projects out of a tree into a different destination.

Companion knowledge: `references/live-runtime-tree-move.md` (worked example: moving a
17GB project tree that also hosted the running CLI, plus extracting sub-projects and
identity folders into a second destination).

Companion knowledge: `references/merge-into-existing-home.md` (worked example: splitting
an 18GB legacy tree into a home's existing 22 folders — file-level collision audit, boxed
layout, deferring the launcher-hosted subtree).

## Non-negotiable rules

1. **Same mount ⇒ rename, not copy.** Check first: `df -h <src_parent> <dst_parent>`.
   Same filesystem ⇒ `mv` is an instant rename, needs 0 extra bytes, cannot
   partially fail. Never `cp -r` + `rm -rf` for a same-mount relocation.
2. **No backup copy is needed for a pure rename.** The bytes never leave the mount.
   (A backup is still right for *merges* or content rewrites, not for a rename.)
3. **Never `du -sh` a multi-GB tree to "size it up" as a gate.** It blows the
   foreground timeout (17GB tree timed out at 180s). Either skip it — rename
   preserves everything by definition — or size one level with
   `for d in *; do echo -n "$d "; du -sh "$d" | cut -f1; done`.
4. **Clarify ambiguous destinations before touching anything.** When a name
   ("hermes19", "backup", "project") matches several real things
   (a Python venv, an empty placeholder dir, an archived profile, a not-yet-created
   home), enumerate them and ask with concrete options. Dropping projects into a
   venv dir breaks the environment; guessing wrong is expensive to undo.
5. **Move and repair inside ONE command** (`set -e`) so nothing is left pointing at
   a path that no longer exists.

## Phase 0 — "split tree X into Y's existing folders": audit before moving

When the ask is *merge this tree into the folders that already exist* (not "move it as one
child"), the real question is **collision**, and the answer must be at file level:

```python
import os
def files(p):
    return {os.path.relpath(os.path.join(r, f), p) for r, _, fs in os.walk(p) for f in fs}
for d in [x for x in os.listdir(src) if os.path.isdir(os.path.join(dst, x))]:
    a, b = files(os.path.join(dst, d)), files(os.path.join(src, d))
    print(d, len(a), len(b), len(a & b))          # last number must be 0
```

Name-level overlap ("both have `docs/`, `tools/`, `skills/`") is **not** overlap. Report
both numbers plainly (`6 folder names shared, 0 file paths shared`) so the user can see
nothing will be overwritten.

Then judge whether merging is even *right*: same folder name ≠ same meaning. A legacy
`config/` (project config) is not the runtime's `config.yaml`; a legacy `tools/` (vendor
binaries) is not the runtime's tools dir. Splaying those into the home root re-creates the
exact clutter the user asked you to fix. Prefer a **boxed layout** that keeps the root
count flat:

```
<home>/legacy-<name>/                 # everything project-ish, one child
<home>/archive/<name>-<YYYY-MM>/      # bulk / archived subtrees
<home>/tools/others/                  # third-party tools
<home>/tools/<x>-old/                 # superseded tool copy
```

Rules: never overwrite (rename the incoming file if a name would clash), keep the home root
count stable, and list what went where in the report.

## Deferring the subtree the launcher points into

The tree may contain the source dir that `$PREFIX/bin/<cli>` resolves through. Find it with
`readlink -f $PREFIX/bin/<cli>` and **leave that subtree in place** while moving everything
else. Present the remaining cutover as a 3-step operation the user must approve: move
subtree → re-point the symlink to the real new path → full restart. Never do it mid-session;
it kills the session doing the work.

## Workflow

### Phase 1 — Recon (all read-only, run in parallel)
```bash
df -h <src_parent> <dst_parent>                 # same mount?
ls -la <src_parent>                             # what moves, what collides
ls -ld <dst_parent>; ls -la <dst_parent>        # existing children, name clashes
readlink -f <launcher or symlink touching src>  # symlinks that will dangle
ps -o pid,args -p $$                            # is cwd/argv inside the tree?
```

### Phase 2 — Dependency sweep (only if the tree is code / a runtime)
```bash
grep -rl "<oldpath>" <venv>/lib/python*/site-packages/*.pth <venv>/lib/python*/site-packages/*.egg-link
grep -rn "<oldpath>" <home>/config.yaml <home>/profiles/*/config.yaml <home>/cron <home>/skills
```
Anything that hits is a path you must repair or accept as broken.

### Phase 3 — Move + repair (one shot)
```bash
set -e
mv <src> <dst>/<NAME>
ln -sfn <dst>/<NAME>/<entrypoint> $PREFIX/bin/<cli>     # re-point launcher to REAL new path
ln -sfn <dst>/<NAME> <src>                              # compat symlink at OLD path
```
The compat symlink is mandatory when the **currently running process** was started
from inside the tree: its `sys.path` still holds the old absolute path, and lazy
imports will fail without it. Drop it only after a full restart of that process —
tell the user it is a link (0 bytes), not a duplicate.

### Phase 4 — Extract sub-items (second destination)
```bash
mkdir -p <dst2>
mv <tree>/sub/a <tree>/sub/b <tree>/sub/c <dst2>/
mv ~/X ~/X_backup <dst2>/          # folders living outside the tree too
```
Then verify sources are gone: `ls <tree>/sub` and `ls -d ~/X` must show them absent.

### Phase 5 — Rewrite stale absolute paths inside moved files
```bash
grep -rn "<oldpath>" <dst>/<NAME> | head -20
```
Docs/persona/install files commonly hardcode the old absolute path. Update them with
`patch` (one call per file) and say so in the report — it is a fix the user did not
ask for but will otherwise trip over.

**A moved Python venv stays broken until you rewrite its own absolute paths.** The venv
freezes `<oldpath>` into its scripts, so `pip`/`activate` exec a path that no longer
exists. Rewrite every text file under it (skip symlinks, skip binaries):

```python
import os
root, old, new = "<dst>/venv", "<oldpath>", "<dst>/venv"
for dp, _, fs in os.walk(root):
    for f in fs:
        p = os.path.join(dp, f)
        if os.path.islink(p):
            continue
        data = open(p, "rb").read()
        if old.encode() in data and b"\x00" not in data[:4096]:
            open(p, "wb").write(data.replace(old.encode(), new.encode()))
```
Expect ~7 files: `pyvenv.cfg`, `bin/pip`, `bin/pip3`, `bin/pip3.13`, `bin/activate`,
`activate.fish`, `activate.csh`. Verify with `./bin/python -V` **and** `./bin/pip -V`
(pip proves the shebang rewrite; python alone can pass because it is a symlink to the
system interpreter — leave that symlink alone).

**A pre-existing incompatibility is not a move failure.** If a moved binary refuses to
run, check whether it could ever run there: a glibc-linked app on Termux/Android (bionic)
dies with `unexpected e_type: 2` before and after the move. Report it as a pre-existing
limitation and offer to delete/archive — don't let the user think the relocation broke it.

### Phase 6 — Evidence-based report
Report only what you can show:
- entry list / `find <dst> -type f | wc -l` per moved item (integrity: same counts)
- emptied source (`ls` output showing absence)
- `readlink -f` of the repaired launcher
- a real invocation of the CLI (`<cli> --version`) proving it still runs
- what remains as a symlink and when it can be removed

## Pitfalls

| Pitfall | Consequence | Guard |
|---|---|---|
| Moving the tree the session runs from, no compat symlink | lazy imports fail mid-session | compat symlink at old path |
| Re-pointing launcher at the *compat symlink* instead of the real path | chained symlink; breaks once compat link is deleted | `readlink -f` and point at the real path |
| Dropping data into `~/.<tool>_venvs/<name>` | corrupts / pollutes the venv | enumerate candidates, ask first |
| Nested move into a home with same-named children (`skills/`, `archive/`, `config/`) | silent merge/overwrite | move as a single named child dir (`<home>/<TREE>`), never splatter children |
| `du -sh` as a pre-check on huge trees | 180s timeout, wasted turn | skip it; rename preserves all |
| Forgetting stale paths inside moved docs | install/persona docs point at nothing | Phase 5 grep + patch |
| Moving a Python venv without rewriting its frozen paths | `pip`/`activate` exec a dead path | Phase 5 python rewrite + `./bin/pip -V` |
| Blaming the move for a binary that never ran there | wrong root cause, user thinks relocation broke it | test the binary and state glibc-vs-bionic / missing-lib as pre-existing |
| Reporting "moved successfully" from the `mv` exit code alone | unverified claim | counts + source-absence + launcher check |
| Deleting the compat symlink on a hunch | breaks lazy imports in the live process | prove it is unused first: `grep -c "<oldpath>" /proc/<pid>/maps` = 0 and `readlink -f $PREFIX/bin/<cli>` already points at the real path |
| Splaying a legacy tree's subtrees straight into the home root | root folder count explodes, system vs project files mix again | boxed layout (`legacy-<name>/`, `archive/<name>-<date>/`, `tools/others/`) |
| `pkill -f <script.py>` while your own shell command line contains that string | pkill matches your own shell and kills the command (exit -15), leaving `rm -rf` half-done | bracket trick `pkill -f '[t]ranslate_agency'`, then re-verify the delete actually happened |
| Quoting a count from a search/query tool as the size of a dataset | tool `count` = matches after `limit`, not inventory | read the source of truth (JSON/SQL/file list) for inventory claims; say which one you used |

## Communication style (this user)

- Reply in **Bahasa Melayu**; keep the technical tokens (paths, commands, sizes) verbatim.
- Structure the report as: apa yang dipindah (with real sizes/file counts) → sumber
  sudah kosong → apa yang dibaiki → keadaan akhir. Short headers, plain terminal text,
  no markdown decoration beyond simple lines and indentation.
- Exact compliance is expected: case-sensitive names, exact placement, no renaming or
  "tidying" beyond fixing broken paths — and state explicitly any change you made that
  was not requested.
- Ask one focused question with concrete choices when the destination is ambiguous;
  do not pick a destination silently.

## Related skills

- `project-restructuring` — content-level restructuring/merging (user-owned; its
  backup-first workflow applies to merges, not to rename-based relocation).
- `hermes-version-management` — when the destination is meant to become a working
  `HERMES_HOME` (venv + `hermes setup`), not just storage.
