#!/data/data/com.termux/files/usr/bin/bash
# Supervisor + starter for N localhost console instances (same codebase, several contexts).
#
#   HC_DIR=~/hermes-console PORTS=8787,8790 bash supervise_consoles.sh
#   HC_DIR=~/hermes-console PORTS=8787,8790 bash supervise_consoles.sh --start-all
#
# Modes:
#   (default)      keeper: start ONLY what is down, print ONLY what it repaired.
#                  Empty stdout when healthy -> safe under `no_agent` cron.
#   --start-all    start both, wait, then print a status block (idempotent).
#
# Per-port launcher: <HC_DIR>/launchers/<port>.sh must exist and exec the app
# with that context (CONSOLE_PORT, CONSOLE_DEFAULT_HOME, CONSOLE_DEFAULT_TAB).
# Fall back to <HC_DIR>/run.sh for the primary port.
set -u
HC_DIR="${HC_DIR:-$HOME/hermes-console}"
PORTS="${PORTS:-8787,8790}"
MODE="${1:-keeper}"
WAIT="${WAIT:-6}"

log_for() {  # per-port log so two instances never interleave
  echo "$HC_DIR/server-$1.log"
}

launcher_for() {
  if [ -x "$HC_DIR/launchers/$1.sh" ]; then echo "$HC_DIR/launchers/$1.sh"
  elif [ "$1" = "8787" ]; then echo "$HC_DIR/run.sh"; fi
}

ping_ok() { curl -s -m 3 -o /dev/null "http://127.0.0.1:$1/api/ping"; }

start_one() {
  local port=$1 l
  l=$(launcher_for "$port")
  [ -n "$l" ] || { echo "port $port: tiada launcher"; return 1; }
  ( cd "$HC_DIR" && rm -f "server-$port.pid" && CONSOLE_PORT="$port" \
      setsid "$l" >> "$(log_for "$port")" 2>&1 < /dev/null & )
}

termux-wake-lock 2>/dev/null || true

IFS=',' read -r -a LIST <<< "$PORTS"
msg=""

for port in "${LIST[@]}"; do
  if [ "$MODE" = "--start-all" ]; then
    if ping_ok "$port"; then echo "$port sudah hidup"; continue; fi
    start_one "$port"; echo "$port dimulakan"
  else
    ping_ok "$port" && continue
    start_one "$port"; sleep "$WAIT"
    if ping_ok "$port"; then msg="$msg
$port dipulihkan"
    else msg="$msg
$port GAGAL dipulihkan — semak $(log_for "$port")"; fi
  fi
done

if [ "$MODE" = "--start-all" ]; then
  for _ in $(seq 1 20); do
    all=1
    for port in "${LIST[@]}"; do ping_ok "$port" || all=0; done
    [ "$all" = 1 ] && break
    sleep 1
  done
  echo "--- status ---"
  for port in "${LIST[@]}"; do
    ping_ok "$port" && echo "$port HIDUP  http://127.0.0.1:$port/" || echo "$port MATI"
  done
elif [ -n "$msg" ]; then
  echo "PENJAGA CONSOLE — $(date '+%Y-%m-%d %H:%M')$msg"
fi
