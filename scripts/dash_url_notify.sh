#!/data/data/com.termux/files/usr/bin/bash
# Beritahu URL dashboard bila bertukar (quick tunnel Cloudflare tukar URL setiap restart).
# Senyap bila tiada perubahan — sesuai untuk cron no_agent (watchdog pattern).
set -u
export HOME=/data/data/com.termux/files/home

URL_FILE="$HOME/.hermes20/dashboard_url.txt"
STAMP="$HOME/.hermes20/.dash_url_last"

[ -s "$URL_FILE" ] || exit 0
URL=$(tail -1 "$URL_FILE" | tr -d '[:space:]')
[ -n "$URL" ] || exit 0

PREV=""
[ -f "$STAMP" ] && PREV=$(cat "$STAMP")

if [ "$URL" = "$PREV" ]; then
  exit 0
fi

printf '%s\n' "$URL" > "$STAMP"

# Uji dulu — jangan beritahu URL yang mati.
CODE=$(curl -s -m 20 -o /dev/null -w "%{http_code}" "$URL/login" 2>/dev/null || echo 000)
if [ "$CODE" != "200" ]; then
  echo "AMARAN: URL dashboard bertukar tetapi belum hidup (HTTP $CODE)"
  echo "$URL"
  exit 0
fi

cat <<EOF
URL DASHBOARD BAHARU (bertukar sebab tunnel dimulakan semula)

$URL

Ujian: /login → HTTP 200 ✓
Log masuk: pengguna firdaus · kata laluan dalam ~/.hermes20/secrets/dashboard_login.txt
EOF
