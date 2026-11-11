#!/usr/bin/env bash
# Health + supervision proof for a runit-managed console (runit on Termux).
#
#   ./console-runit-smoke.sh                                   # svc hermes-console, port 8787
#   SERVICE=myconsole PORT=8080 KILL_DRILL=1 ./console-runit-smoke.sh
#   ASSETS="/static/index.html /static/style.css" ./console-runit-smoke.sh
#
# One line per check (LULUS/GAGAL) with evidence inline; exit code = number of failures,
# so the report quotes real output instead of a claim.
# KILL_DRILL=1 kills the app pid once to prove sv really restarts it (opt-in).
set -uo pipefail

SVC="${SERVICE:-hermes-console}"
PORT="${PORT:-8787}"
BASE="http://127.0.0.1:${PORT}"
PIDFILE="${PID_FILE:-$HOME/hermes-console/server-$PORT.pid}"
ASSETS="${ASSETS:-/api/status}"
LOGDIR="${LOGDIR:-$HOME/.hermes20/logs/$SVC}"
FAIL=0

ok()  { printf '[LULUS] %-42s (%s)\n' "$1" "$2"; }
bad() { printf '[GAGAL] %-42s (%s)\n' "$1" "$2"; FAIL=$((FAIL + 1)); }

# fetch <path> -> prints "<code> <tmpfile>"; $TMPDIR because /tmp is unwritable on Termux
fetch() {
  local tmp code
  tmp=$(mktemp "${TMPDIR:-$HOME}/smoke.XXXXXX")
  code=$(curl -s -m 8 -o "$tmp" -w '%{http_code}' "$BASE$1" 2>/dev/null) || code=000
  printf '%s %s' "$code" "$tmp"
}

# 1. runit state -------------------------------------------------------------
ST=$(sv status "$SVC" 2>/dev/null || echo "tiada")
case "$ST" in
  run:*) ok "sv status $SVC" "$ST" ;;
  *)     bad "sv status $SVC" "$ST" ;;
esac

# 2. app answers -------------------------------------------------------------
read -r CODE TMP <<< "$(fetch /api/ping)"
if [ "$CODE" = "200" ]; then ok "GET /api/ping" "200 $(head -c 110 "$TMP" 2>/dev/null)"; else bad "GET /api/ping" "kod=$CODE"; fi
rm -f "$TMP"

# 3. routes/assets the user was promised -------------------------------------
for a in $ASSETS; do
  read -r C T <<< "$(fetch "$a")"
  S=$(wc -c < "$T" 2>/dev/null | tr -d ' ')
  if [ "$C" = "200" ] && [ "${S:-0}" -gt 200 ]; then ok "GET $a" "$C ${S}b"; else bad "GET $a" "$C ${S}b"; fi
  rm -f "$T"
done

# 4. log is rotated, not one growing file ------------------------------------
if [ -d "$LOGDIR" ]; then
  SZ=$(du -sm "$LOGDIR" 2>/dev/null | cut -f1)
  N=$(find "$LOGDIR" -maxdepth 1 -type f 2>/dev/null | wc -l | tr -d ' ')
  if [ "${SZ:-99}" -lt 8 ]; then ok "log $SVC" "${SZ} MB · ${N} fail"; else bad "log $SVC" "${SZ} MB"; fi
else
  bad "direktori log $SVC" "tiada: $LOGDIR"
fi

# 5. exactly one app process (orphans hide here) ------------------------------
NPROC=$(pgrep -f "app.py" 2>/dev/null | wc -l | tr -d ' ')
if [ "$NPROC" = "1" ]; then ok "bilangan proses app.py" "1"; else bad "bilangan proses app.py" "${NPROC:-0}"; fi

# 6. supervision drill (opt-in): kill, expect new pid + 200 -------------------
if [ "${KILL_DRILL:-0}" = "1" ]; then
  PID=$(cat "$PIDFILE" 2>/dev/null || true)
  if [ -z "$PID" ]; then
    bad "drill auto-restart" "fail pid tiada: $PIDFILE"
  else
    kill -9 "$PID" 2>/dev/null
    C=000
    for _ in 1 2 3 4 5 6 7 8 9 10; do
      sleep 1
      C=$(curl -s -m 3 -o /dev/null -w '%{http_code}' "$BASE/api/ping" 2>/dev/null) || C=000
      [ "$C" = "200" ] && break
    done
    NEW=$(cat "$PIDFILE" 2>/dev/null || true)
    if [ "$C" = "200" ] && [ "$NEW" != "$PID" ]; then
      ok "drill auto-restart" "pid $PID -> $NEW, ping 200"
    else
      bad "drill auto-restart" "pid $PID -> ${NEW:-?}, ping $C"
    fi
  fi
fi

echo
echo "Gagal: $FAIL"
[ "$FAIL" -eq 0 ] && echo "SEMUA LULUS" || echo "ADA YANG GAGAL"
exit "$FAIL"
