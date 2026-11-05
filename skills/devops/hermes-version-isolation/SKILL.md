---
name: hermes-version-isolation
description: Run multiple Hermes versions isolated in Termux.
category: devops
---
# Hermes Version Isolation Skill

Run multiple Hermes Agent versions in parallel (e.g., 0.19.0 and 0.20.0) without cross‑talk of configuration, logs, memori­es, or skills.

## When to use
- You need to test or compare different Hermes versions side‑by‑side.
- You want to keep each version’s data completely separate (config.yaml, MEMORY.log, skills/, cron/, etc.).
- You are on Android/Termux where building from source can fail due to missing toolchain.

## Steps

1. **Prepare isolated directories**
   ```bash
   mkdir -p ~/.hermes_v19 ~/.hermes_v20
   ```

2. **Create a virtual environment for the older version**  
   (Use `--system-site-packages` to reuse already‑installed system packages like `psutil`, `cryptography`, etc., which often fail to build on Android.)
   ```bash
   python3 -m venv ~/.hermes_venvs/v19 --system-site-packages
   ~/.hermes_venvs/v19/bin/pip install --upgrade pip setuptools wheel
   ~/.hermes_venvs/v19/bin/pip install /path/to/hermes_agent-0.19.0-py3-none-any.whl
   ```

   For the newer version you can rely on the already‑installed system Hermes (or install into another venv the same way).

3. **Create wrapper scripts** (place them in `~/bin` and ensure `~/bin` is in `$PATH`)

   *hermes19*
   ```bash
   #!/usr/bin/env bash
   HERMES_HOME="$HOME/.hermes_v19" \
   HERMES_TERMUX_DISABLE_FAST_CLI=1 \
   "$HOME/.hermes_venvs/v19/bin/hermes" "$@"
   ```

   *hermes20*
   ```bash
   #!/usr/bin/env bash
   HERMES_HOME="$HOME/.hermes_v20" \
   hermes "$@"
   ```

   Make them executable: `chmod +x ~/bin/hermes19 ~/bin/hermes20`

4. **Run the versions in parallel**  
   - Option A: Use `tmux` (or `screen`) to split a session:
     ```bash
     tmux new-session -s hermes-dual -n chat -d 'hermes19 chat' \; \
         split-window -h 'hermes20 chat' \; select-pane -t 0
     tmux attach -t hermes-dual
     ```
   - Option B: Open two separate Termux sessions and run `hermes19 chat` in one and `hermes20 chat` in the other.

5. **Verify isolation**
   In each pane run:
   ```bash
   hermes19 doctor   # or hermes20 doctor
   ```
   Confirm that:
   - `Install directory:` points to the correct venv or source tree.
   - `Config file:` shows `.../.hermes_v19/config.yaml` or `.../.hermes_v20/config.yaml`.
   - Logs (`hermes19 logs`, `hermes20 logs`) are stored under their respective `~/.hermes_v*/logs/`.

## Pitfalls
- **Missing `HERMES_TERMUX_DISABLE_FAST_CLI=1`** for older versions leads to a `NameError: PROJECT_ROOT` when the fast‑cli version check runs.
- **Sharing the same `HERMES_HOME`** causes config, logs, and skills to clobber each other.
- **Attempting to pip‑install the older wheel in a clean venv without `--system-site-packages`** can fail on Android because wheels like `psutil` and `cryptography` need to compile native extensions; using the system packages avoids this.
- **Running both versions in the same terminal pane** without separating output will mix messages; always use separate panes, tabs, or tmux splits.

## Reference
- The exact commands used in this session are captured in `references/hermes-version-isolation-session.md`.