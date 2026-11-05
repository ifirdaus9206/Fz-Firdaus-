---
name: hermes-version-management
description: Manage multiple Hermes versions in isolated environments.
version: 1.0.0
category: devops
---

# Hermes Version Management

Manage multiple versions of Hermes Agent in parallel on the same system, isolating configuration, data, and environments.

## When to Use

You need to run different versions of Hermes Agent (e.g., 0.19.0 and 0.20.0) side‑by‑side for testing, comparison, or stable production use without interfering with each other's configuration, logs, memories, or skills.

## Steps

### 1. Prepare Isolation Directories

Create separate directories for each version's HERMES_HOME and virtual environment.

```bash
mkdir -p ~/.hermes19        # Config/data for Hermes 0.19.0
mkdir -p ~/.hermes20        # Config/data for Hermes 0.20.0
mkdir -p ~/.hermes_venvs    # Parent for virtualenvs
```

### 2. Set Up Virtual Environments

Create a venv for each version. Use `--system-site-packages` to reuse already‑installed system packages (e.g., `psutil`, `cryptography`) that are difficult to build on Android/Termex.

```bash
# For Hermes 0.19.0
python3 -m venv ~/.hermes_venvs/hermes19 --system-site-packages

# For Hermes 0.20.0 (if you also want a venv; otherwise use system/in‑place)
python3 -m venv ~/.hermes_venvs/hermes20 --system-site-packages
```

### 3. Install the Desired Version

Install from the wheel file (for 0.19.0) or from source/pip (for 0.20.0).

```bash
# Install Hermes 0.19.0 from wheel
~/.hermes_venvs/hermes19/bin/pip install --upgrade pip setuptools wheel
~/.hermes_venvs/hermes19/bin/pip install ~/.hermes/hermes_agent-0.19.0-py3-none-any.whl

# Install Hermes 0.20.0 (example from source checkout)
# Assuming you have the source at ~/ULTIMATE_AI_PROJECT/tools/hermes-agent-source/hermes-agent
cd ~/ULTIMATE_AI_PROJECT/tools/hermes-agent-source/hermes-agent
~/.hermes_venvs/hermes20/bin/pip install -e .
# Or install from PyPI if available:
# ~/.hermes_venvs/hermes20/bin/pip install hermes-agent
```

### 4. Configure HERMES_HOME and Disable Fast Version Check (Termux)

When invoking Hermes, set `HERMES_HOME` to the appropriate directory. On Termux, also set `HERMES_TERMUX_DISABLE_FAST_CLI=1` to avoid the ultrafast version check that can fail when the venv's site‑packages layout differs.

```bash
# Run Hermes 0.19.0
HERMES_HOME=~/.hermes19 HERMES_TERMUX_DISABLE_FAST_CLI=1 \
    ~/.hermes_venvs/hermes19/bin/hermes <subcommand> [args]

# Run Hermes 0.20.0
HERMES_HOME=~/.hermes20 \
    ~/.hermes_venvs/hermes20/bin/hermes <subcommand> [args]
# If you installed 0.20.0 globally and it's in PATH, you can also use:
# HERMES_HOME=~/.hermes20 hermes <subcommand> [args]
```

### 5. Create Convenience Aliases (Optional)

Add these to your shell rc file (`~/.bashrc` or `~/.zshrc`) for easy access:

```bash
alias hermes19='HERMES_HOME=$HOME/.hermes19 HERMES_TERMUX_DISABLE_FAST_CLI=1 $HOME/.hermes_venvs/hermes19/bin/hermes'
alias hermes20='HERMES_HOME=$HOME/.hermes20 $HOME/.hermes_venvs/hermes20/bin/hermes'
```

After reloading the shell, use:

```bash
hermes19 chat   # Starts 0.19.0 with its isolated data
hermes20 chat   # Starts 0.20.0 with its isolated data
```

### 6. Verify Isolation

Check that each version uses its own configuration and data:

```bash
hermes19 doctor   # Look for Install directory pointing to the 0.19.0 venv
hermes20 doctor   # Look for Install directory pointing to the 0.20.0 venv or source
```

Logs, memories, skills, cron jobs, etc., will be stored under the respective `HERMES_HOME` (`~/.hermes19` and `~/.hermes20`) and will not interfere.

## Pitfalls

- **Forgetting `HERMES_TERMUX_DISABLE_FAST_CLI=1` on Termux** can cause a `NameError: PROJECT_ROOT` when the ultrafast version check runs before the venv's `hermes_cli` is fully initialised. Always set this environment variable when invoking a Hermes version from a virtual environment on Termux.
- **Using the same HERMES_HOME for two versions** will cause configuration, logs, and skill data to clash, leading to unpredictable behaviour. Keep `HERMES_HOME` distinct.
- **Attempting to build problematic dependencies (e.g., psutil) from source in a pure venv** will fail on Android because the platform lacks a suitable toolchain. Use `--system-site-packages` or pre‑install the dependency via the system package manager (`pkg install psutil`) before creating the venv.
- **Assuming the global `hermes` command is the version you expect** – always verify with `hermes version` after setting `HERMES_HOME`.

## References

- Hermes configuration isolation: https://hermes-agent.nousresearch.com/docs/profiles/#profile-isolation
- Managing HERMES_HOME: https://hermes-agent.nousresearch.com/docs/hermes-constants/#hermes-home
- Termux-specific notes: https://hermes-agent.nousresearch.com/docs/installation/#termux

## Related Skills

- `hermes-agent` – Core Hermes usage and configuration.
- `python-venv` – Managing virtual environments (if available).