# Worked example — moving a live runtime tree, then splitting sub-projects out

Environment: Termux/Android, single home `/data/data/com.termux/files/home`,
`HERMES_HOME=~/.hermes20`, launcher `$PREFIX/bin/hermes` (a symlink),
python venv at `~/.hermes_venvs/hermes19`.

## Case A — "pindahkan ULTIMATE_AI_PROJECT ke dalam hermes20, semuanya"

Source tree: `~/ULTIMATE_AI_PROJECT` ≈ 17GB
(`tools` 6.5G, `archive` 8.5G, `projects` 1.8G, `config` 637M, `tests` 130M,
`src` 108M, `identity` 69M, `docs` 25M, rest small).

### What recon found (all in parallel, read-only)
```
$PREFIX/bin/hermes -> .../home/ULTIMATE_AI_PROJECT/tools/hermes-agent-source/hermes-agent/hermes
```
So the CLI being used was *itself inside the tree being moved* — the running
process (`ps` showed `hermes <venv>/bin/python $PREFIX/bin/hermes`, cwd inside the
tree) had the old absolute path on `sys.path`.

Also checked, and clean:
- no `.pth` / `.egg-link` in `~/.hermes_venvs/hermes19/lib/python3.13/site-packages`
  pointing at the tree;
- no `ULTIMATE_AI_PROJECT` references in `~/.hermes20/config.yaml`,
  `profiles/*/config.yaml`, or rc files (only prose in a few skill references).

`du -sh ~/ULTIMATE_AI_PROJECT` **timed out at 180s** — do not use it as a gate.

### The one-shot command that worked
```bash
set -e
cd ~
mv ULTIMATE_AI_PROJECT .hermes20/ULTIMATE_AI_PROJECT
ln -sfn /data/data/com.termux/files/home/.hermes20/ULTIMATE_AI_PROJECT/tools/hermes-agent-source/hermes-agent/hermes $PREFIX/bin/hermes
ln -sfn /data/data/com.termux/files/home/.hermes20/ULTIMATE_AI_PROJECT /data/data/com.termux/files/home/ULTIMATE_AI_PROJECT
```
- `mv` was a rename (same mount) → instant, all 22 top-level entries intact.
- Launcher re-pointed at the **real** new path.
- `~/ULTIMATE_AI_PROJECT` left as a **compat symlink** (0 bytes) purely so the
  running session's `sys.path` imports keep resolving; removable after a full
  restart of hermes.

Verification that was actually run:
```bash
ls ~/.hermes20/ULTIMATE_AI_PROJECT | wc -l      # 22
readlink -f $PREFIX/bin/hermes                  # -> .hermes20/.../hermes
ls ~/ULTIMATE_AI_PROJECT/README.md              # resolves through compat link
hermes --version                                # Python 3.13.13, SDK 2.24.0
```

## Case B — "keluarkan projek trading ke hermes19, dan ANIS / ANIS_backup juga"

Ambiguity gate: `hermes19` matched four real things —
`~/.hermes_venvs/hermes19` (228M Python venv), `~/hermes19_source` (empty),
`~/.hermes20/archive/legacy-hermes19-2026-10-21` (archived home), and a
not-yet-created `~/.hermes19`. Asked the user with those four options; they chose
"create `~/.hermes19` as a new home and put everything directly inside".

### Identification
```
projects/meta5            34M    mt5_trader.py, zigzag_mt5.py, mt5_web.py, EA_ZZ_Color_Reporter.mq5
projects/mt5-backtest     51M
projects/strategy-engines 193K
projects/bots             35K    (telegram bots — not trading-specific, left in place)
~/ANIS                    905K   (outside the tree)
~/ANIS_backup             539K
```
No ANIS existed inside the tree; a `find -iname '*ANIS*' -o -iname '*trading*' -o
-iname '*mt5*'` sweep avoided assuming.

Pre-move check: no references to `/ANIS` in `~/.hermes20/config.yaml`, `profiles/`,
`cron/`, `skills/`, `SOUL.md` — safe to relocate.

### Execution
```bash
set -e
mkdir -p .hermes19
P=.hermes20/ULTIMATE_AI_PROJECT/projects
mv "$P/meta5" "$P/mt5-backtest" "$P/strategy-engines" .hermes19/
mv ANIS ANIS_backup .hermes19/
```

### Stale absolute paths inside the moved folders (found + fixed)
```
ANIS/identity/agent_identity.md : - **Location:** /data/data/com.termux/files/home/ANIS/
ANIS/persona.md                 : **Lokasi Fail:** .../home/ANIS/
ANIS/docs/installation.md       : cd .../home/ANIS
ANIS_backup/persona.md          : **Lokasi Fail:** .../home/ANIS/
```
Rewritten to `/data/data/com.termux/files/home/.hermes19/ANIS/` with four `patch`
calls. Trading projects had zero references to `ULTIMATE_AI_PROJECT`.

### Verification
```
ANIS 120 files, ANIS_backup 76, meta5 2560, mt5-backtest 72, strategy-engines 36
ls -d ~/ANIS ~/ANIS_backup      -> No such file or directory
projects/ now has 24 entries    -> the three moved ones gone
```

### Caveat told to the user
`~/.hermes19` has no `config.yaml` / `skills/`, so it is **storage, not a runnable
HERMES_HOME**. To make it a real home: `HERMES_HOME=~/.hermes19 hermes setup`
(and note the venv stays separately at `~/.hermes_venvs/hermes19`).
