#!/usr/bin/env bash
# Starter launcher: run the SHARED console project for one specific home/tab/port.
# Copy to the home it serves, e.g. ~/.hermes19/console.sh, then chmod +x.
#
#   ./console.sh            localhost only
#   ./console.sh --lan      adds the token gate (delegated to run.sh)
#
# One codebase, several contexts: no project copy, no UI fork.
set -u

# ---- edit these four lines per instance -------------------------------------
CONSOLE_HOME_KEY="hermes19"          # key in the console's homes.json
CONSOLE_TAB="trading"                # tab opened first (pusat|overview|kerja|org|agency|trading|system)
CONSOLE_INSTANCE_PORT="8790"         # distinct port per instance
CONSOLE_PROJECT="$HOME/hermes-console"
# -----------------------------------------------------------------------------

export HERMES_HOME="${HERMES_HOME:-$HOME/.${CONSOLE_HOME_KEY}}"
export CONSOLE_DEFAULT_HOME="$CONSOLE_HOME_KEY"
export CONSOLE_HOMES="$CONSOLE_HOME_KEY"     # UI only sees this home
export CONSOLE_DEFAULT_TAB="$CONSOLE_TAB"
export CONSOLE_PORT="${CONSOLE_PORT:-$CONSOLE_INSTANCE_PORT}"

exec "$CONSOLE_PROJECT/run.sh" "$@"
