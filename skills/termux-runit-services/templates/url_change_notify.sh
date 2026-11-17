#!/data/data/com.termux/files/usr/bin/bash
# Announce a changed public URL (quick tunnels mint a new hostname per start).
# Pattern: the tunnel service owns <url-file>; this script only *reports* changes.
# Designed for a Hermes `no_agent` cron: empty stdout = no delivery = silent.
set -u
export HOME=/data/data/com.termux/files/home

URL_FILE="${URL_FILE:-$HOME/.hermes20/dashboard_url.txt}"
STAMP="${STAMP:-$HOME/.hermes20/.dash_url_last}"
PROBE_PATH="${PROBE_PATH:-/login}"      # path that must answer 200 when healthy

[ -s "$URL_FILE" ] || exit 0
URL=$(tail -1 "$URL_FILE" | tr -d '[:space:]')
[ -n "$URL" ] || exit 0

PREV=""
[ -f "$STAMP" ] && PREV=$(cat "$STAMP")
[ "$URL" = "$PREV" ] && exit 0          # unchanged -> silent

# Probe BEFORE announcing: never publish a URL that is not serving.
CODE=$(curl -s -m 20 -o /dev/null -w "%{http_code}" "$URL$PROBE_PATH" 2>/dev/null || echo 000)
printf '%s\n' "$URL" > "$STAMP"

if [ "$CODE" != "200" ]; then
  echo "AMARAN: URL bertukar tetapi belum hidup (HTTP $CODE)"
  echo "$URL"
  exit 0
fi

cat <<EOF
URL BAHARU (bertukar sebab servis dimulakan semula)

$URL

Ujian: $PROBE_PATH -> HTTP 200
EOF
