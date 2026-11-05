# Termux Session Summary: Managing Multiple Hermes Versions

This reference documents the specific steps taken in the session to run Hermes 0.19.0 and 0.20.0 in parallel on Android/Termex.

## Environment Details
- Device: Android (Termux)
- Python: 3.13.13
- Hermes versions: 0.19.0 (from wheel), 0.20.0 (from source)

## Key Commands Executed

### 1. Directory Setup
```bash
mkdir -p ~/.hermes19 ~/.hermes20 ~/.hermes_venvs
```

### 2. Virtual Environment Creation (with system-site-packages for hard-to-build deps)
```bash
python3 -m venv ~/.hermes_venvs/hermes19 --system-site-packages
python3 -m venv ~/.hermes_venvs/hermes20 --system-site-packages
```

### 3. Installing Hermes 0.19.0 from Wheel
```bash
~/.hermes_venvs/hermes19/bin/pip install --upgrade pip setuptools wheel
~/.hermes_venvs/hermes19/bin/pip install ~/.hermes/hermes_agent-0.19.0-py3-none-any.whl
```

### 4. Installing Hermes 0.20.0 from Source
```bash
cd ~/ULTIMATE_AI_PROJECT/tools/hermes-agent-source/hermes-agent
~/.hermes_venvs/hermes20/bin/pip install -e .
```

### 5. Running Versions with Proper Isolation
```bash
# Hermes 0.19.0 (requires TERMUX_DISABLE_FAST_CLI on Termux)
HERMES_HOME=~/.hermes19 HERMES_TERMUX_DISABLE_FAST_CLI=1 \
    ~/.hermes_venvs/hermes19/bin/hermes version

# Hermes 0.20.0
HERMES_HOME=~/.hermes20 \
    ~/.hermes_venvs/hermes20/bin/hermes version
```

### 6. Convenience Aliases Added to ~/.bashrc or ~/.zshrc
```bash
alias hermes19='HERMES_HOME=$HOME/.hermes19 HERMES_TERMUX_DISABLE_FAST_CLI=1 $HOME/.hermes_venvs/hermes19/bin/hermes'
alias hermes20='HERMES_HOME=$HOME/.hermes20 $HOME/.hermes_venvs/hermes20/bin/hermes'
```

## Critical Fixes Applied

### Termux Ultrafast Version Check Issue
When running Hermes from a virtual environment on Termux, the ultrafast version check (`_try_termux_ultrafast_version`) would fail with `NameError: PROJECT_ROOT` because it tried to access `PROJECT_ROOT` before the venv's hermes_cli was properly initialised.

**Solution**: Set `HERMES_TERMUX_DISABLE_FAST_CLI=1` when invoking Hermes from a venv on Termux.

### Dependency Build Failures on Android
Attempting to build packages like `psutil` and `cryptography` from source in a pure venv would fail due to missing Android toolchain.

**Solution**: Use `--system-site-packages` when creating the venv to reuse already-installed system versions of these packages.

## Verification
After setup, verify isolation with:
```bash
hermes19 doctor   # Check Install directory points to venv
hermes20 doctor   # Check Install directory points to venv or source
```

Logs, memories, skills, and cron data remain isolated under respective HERMES_HOME directories (~/.hermes19 and ~/.hermes20).