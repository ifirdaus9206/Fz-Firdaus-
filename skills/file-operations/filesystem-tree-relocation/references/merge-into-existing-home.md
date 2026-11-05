# Worked example — splitting an 18GB legacy tree into a home's existing folders

Session: Termux/Android, `~/.hermes20` (Hermes home), legacy tree
`~/.hermes20/ULTIMATE_AI_PROJECT` (18GB). Ask: *before touching the legacy tree, tell me
whether the home's existing folders are complete or overlapping, then split the tree into
them.* Later decision: boxed layout (option 1), launcher subtree deferred.

## 1. Inventory that fits in one turn

```bash
cd ~/.hermes20
for f in $(ls -A); do printf "%-30s %s\n" "$f" "$(du -sh "$f" 2>/dev/null | cut -f1)"; done
```

Reading: 23 top-level folders incl. the legacy tree; 22 outside it. Legacy tree itself had
17 sub-folders.

## 2. Name-level vs file-level collision

```python
import os
H = "/data/data/com.termux/files/home/.hermes20"
U = os.path.join(H, "ULTIMATE_AI_PROJECT")
def files(p):
    return {os.path.relpath(os.path.join(r, f), p) for r, _, fs in os.walk(p) for f in fs}
cols = [d for d in os.listdir(U) if os.path.isdir(os.path.join(H, d))]
for d in cols:
    a, b = files(os.path.join(H, d)), files(os.path.join(U, d))
    print(f"{d:10s} home={len(a):6d} legacy={len(b):6d} same_paths={len(a & b)}")
```

Result that mattered:

| folder | home files | legacy files | identical paths |
|---|---|---|---|
| archive | 158 | 245,518 | 0 |
| docs | 1 | 399 | 0 |
| logs | 7 | 1 | 0 |
| scripts | 4 | 16 | 0 |
| skills | 599 | 1 | 0 |
| tools | 16,092 | 105,234 | 0 |

⇒ 6 shared *names*, **0 shared files**. That is the sentence to give the user.
Sub-check worth making: `skills/research` existed on both sides but was an empty shell on
the legacy side (`ls` shows nothing, `du` 3.5K) — an empty dir is not a collision.

## 3. Boxed layout actually applied

```bash
cd ~/.hermes20
U=ULTIMATE_AI_PROJECT
mkdir -p legacy-ultimate tools/others archive/ultimate-2026-10 archive/code-server-2026-10
mv $U/{agents,config,database,deployment,docs,identity,knowledge,projects,prompts,src,tests,workflows,logs,scripts,skills} legacy-ultimate/
mv $U/{CHANGELOG.md,LICENSE,README.md,RUMAH-AINA.md,SKILL.md} legacy-ultimate/
mv $U/archive/* archive/ultimate-2026-10/ && rmdir $U/archive
mv $U/tools/hermes-agent-local tools/hermes-source-old
for t in CMSeeK OpenHands-main TOOLSINSTALLERv3 aina-tools bun-install bun-repo \
         cline-install cline-repo commix delphitools-cli nikto openhands-main sqlmap; do
  mv "$U/tools/$t" tools/others/
done
mv tools/code-server archive/code-server-2026-10/code-server
```

Outcome: root 23 → 24 folders, legacy tree reduced to a single child
(`tools/hermes-agent-source`, 2.3GB) because the launcher resolves through it. Sizes after:
legacy-ultimate 2.7G, tools 4.3G, archive 9.5G.

## 4. Proving the compat symlink is safe to delete

```bash
PID=$(pgrep -f "bin/python .*bin/hermes" | head -1)
ls -l /proc/$PID/cwd
grep -c "files/home/ULTIMATE_AI_PROJECT" /proc/$PID/maps   # 0 = nothing mapped from old path
readlink -f $PREFIX/bin/hermes                              # already the real new path
```

With 0 matches and the launcher already on the real path, the 62-byte compat symlink was
removed and `hermes --version` + `hermes doctor` were re-run to prove the CLI survived.
Keep this order: prove unused → delete → re-verify. Never delete first.

## 5. What stayed behind on purpose

`$PREFIX/bin/hermes -> .../ULTIMATE_AI_PROJECT/tools/hermes-agent-source/hermes-agent/hermes`
(2.3GB). Moving it needs: move → `ln -sfn` to the real new path → full restart, in one
approved cutover. Mid-session it would kill the agent doing the work.
