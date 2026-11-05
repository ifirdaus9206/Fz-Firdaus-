# Session Reference: Isolating Hermes 0.19.0 and 0.20.0 in Termux

## Environment
- Device: Android (Termux)
- Target versions: Hermes 0.19.0 and 0.20.0
- Goal: Run both versions in parallel with zero cross-talk

## Key Commands Executed

### 1. Setup directories
```bash
mkdir -p ~/.hermes19 ~/.hermes20 ~/.hermes_venvs
```

### 2. Create virtual environment for 0.19.0 (using system packages)
```bash
python3 -m venv ~/.hermes_venvs/hermes19 --system-site-packages
~/.hermes_venvs/hermes19/bin/pip install --upgrade pip setuptools wheel
~/.hermes_venvs/hermes19/bin/pip install ~/.hermes/hermes_agent-0.19.0-py3-none-any.whl
```

### 3. Add aliases to ~/.bashrc
```bash
# Hermes version aliases
hermes19() {
    HERMES_HOME="$HOME/.hermes19" \
    HERMES_TERMUX_DISABLE_FAST_CLI=1 \
    "$HOME/.hermes_venvs/hermes19/bin/hermes" "$@"
}

hermes20() {
    HERMES_HOME="$HOME/.hermes20" \
    hermes "$@"
}
```
Then: `source ~/.bashrc`

### 4. Create executable wrapper scripts in ~/bin
**~/bin/hermes19**
```bash
#!/usr/bin/env bash
HERMES_HOME="$HOME/.hermes19" HERMES_TERMUX_DISABLE_FAST_CLI=1 "$HOME/.hermes_venvs/hermes19/bin/hermes" "$@"
```

**~/bin/hermes20**
```bash
#!/usr/bin/env bash
HERMES_HOME="$HOME/.hermes20" hermes "$@"
```
Then: `chmod +x ~/bin/hermes19 ~/bin/hermes20`

### 5. Run in tmux (final working command)
```bash
tmux kill-session -t hermes-dual 2>/dev/null; tmux new-session -s hermes-dual -n chat -d 'hermes19 chat' \; split-window -h 'hermes20 chat' \; select-pane -t 0
```

## Verification Outputs

### hermes19 version
```
Hermes Agent v0.19.0 (2026.7.20)
Install directory: /data/data/com.termux/files/home/.hermes_venvs/hermes19/lib/python3.13/site-packages
Install method: pip
Python: 3.13.13
OpenAI SDK: 2.24.0
Up to date
```

### hermes20 version
```
Hermes Agent v0.20.0 (2026.8.3)
Install directory: /data/data/com.termux/files/home/ULTIMATE_AI_PROJECT/tools/hermes-agent-source/hermes-agent
Python: 3.13.13
OpenAI SDK: 2.24.0
Up to date
```

### Isolation check (doctor)
Each shows different config paths:
- hermes19: Config file: /data/data/com.termux/files/home/.hermes19/config.yaml
- hermes20: Config file: /data/data/com.termux/files/home/.hermes20/config.yaml

## Pitfalls Encountered & Solutions

1. **Fast-CLI version check failure**  
   Symptom: `NameError: name 'PROJECT_ROOT' is not defined`  
   Fix: Set `HERMES_TERMUX_DISABLE_FAST_CLI=1` when calling older versions

2. **Package build failures on Android**  
   Symptom: Errors building `psutil`, `cryptography`, `uvloop` from source  
   Fix: Use `--system-site-packages` to reuse system-installed versions

3. **Configuration bleed-over**  
   Symptom: Both versions reading/writing same config/skills  
   Fix: Ensure `HERMES_HOME` is set to different directories before any Hermes call

## Working Session Flow
1. Open Termux
2. Run: `tmux kill-session -t hermes-dual 2>/dev/null; tmux new-session -s hermes-dual -n chat -d 'hermes19 chat' \; split-window -h 'hermes20 chat' \; select-pane -t 0`
3. Attach: `tmux attach -t hermes-dual`
4. Left pane: Hermes 0.19.0 (isolated to ~/.hermes19)
5. Right pane: Hermes 0.20.0 (isolated to ~/.hermes20)