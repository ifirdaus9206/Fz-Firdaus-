#!/data/data/com.termux/files/usr/bin/bash
# svc-status.sh — one-word status for a set of runit services (+ optional health URL).
#
# Install:  cp scripts/svc-status.sh "$PREFIX/bin/hermes-status"; chmod +x "$PREFIX/bin/hermes-status"
# Alias:    printf '#!/data/data/com.termux/files/usr/bin/bash\nexec %s "$@"\n' \
#             "$PREFIX/bin/hermes-status" > "$PREFIX/bin/hs"; chmod +x "$PREFIX/bin/hs"
#
# Why this exists: owners type the SERVICE NAME as if it were a command
# ("hermes-console: command not found") because the names also look like binaries.
# One wrapper that lists every service removes that whole class of confusion.
#
# Configure via env (or edit the defaults below):
#   SVCS="hermes-console hermes-gateway hermes-keeper hermes-dash-tunnel sshd"
#   HEALTH_URL="http://127.0.0.1:8787/"
#   URL_FILE="$HOME/.hermes20/dashboard_url.txt"

set -u

SV="${SV:-/data/data/com.termux/files/usr/bin/sv}"
export SVDIR="${SVDIR:-/data/data/com.termux/files/usr/var/service}"
SVCS="${SVCS:-hermes-console hermes-gateway hermes-keeper hermes-dash-tunnel sshd}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8787/}"
URL_FILE="${URL_FILE:-$HOME/.hermes20/dashboard_url.txt}"

st() {
  for s in $SVCS; do
    line="$("$SV" status "$s" 2>/dev/null | head -1)"
    case "$line" in
      run:*)
        pid="$(printf '%s' "$line" | sed -n 's/.*(pid \([0-9]*\)).*/\1/p')"
        printf '  %-20s HIDUP   pid %s\n' "$s" "${pid:-?}" ;;
      down:*) printf '  %-20s MATI   (fail down)\n' "$s" ;;
      *)      printf '  %-20s TIADA\n' "$s" ;;
    esac
  done
  printf '\n  health %-18s : %s\n' "$HEALTH_URL" \
    "$(curl -s -o /dev/null -m 4 -w '%{http_code}' "$HEALTH_URL" 2>/dev/null || echo 000)"
  if [ -f "$URL_FILE" ]; then
    printf '  tunnel              : %s\n' "$(grep -o 'https://[^ ]*' "$URL_FILE" 2>/dev/null | head -1)"
  fi
}

case "${1:-status}" in
  status)  st ;;
  up)      for s in $SVCS; do "$SV" up "$s" 2>/dev/null; done; sleep 3; st ;;
  down)    for s in $SVCS; do "$SV" down "$s" 2>/dev/null; done; sleep 2; st ;;
  restart) for s in $SVCS; do "$SV" restart "$s" 2>/dev/null; done; sleep 4; st ;;
  *)       echo "Guna: $(basename "$0") [status|up|down|restart]" ;;
esac
