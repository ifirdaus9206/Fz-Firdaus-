#!/data/data/com.termux/files/usr/bin/bash
# mdr.sh - fire an accessibility-automation app's webhook trigger from Termux.
# Usage: ./mdr.sh shot | tap "text on screen" | swipe up|down|left|right | key back|home | ping
# Config:  webhook.conf next to this script (BASE=..., DEFAULT_KEY=act).
CONF="${MDR_CONF:-$HOME/phone_bridge/webhook.conf}"
[ -f "$CONF" ] && . "$CONF"
BASE="${BASE:-http://127.0.0.1:8080/trigger}"
DK="${DEFAULT_KEY:-act}"

cmd="$1"; shift

case "$cmd" in
  shot)
    curl -s -G --max-time 8 "$BASE" --data-urlencode "$DK=shot"; echo ;;
  tap)
    [ -z "$*" ] && { echo "usage: $0 tap \"text\""; exit 1; }
    curl -s -G --max-time 8 "$BASE" --data-urlencode "$DK=tap" --data-urlencode "text=$*"; echo ;;
  swipe)
    curl -s -G --max-time 8 "$BASE" --data-urlencode "$DK=swipe" --data-urlencode "dir=${1:-up}"; echo ;;
  key)
    curl -s -G --max-time 8 "$BASE" --data-urlencode "$DK=key" --data-urlencode "key=${1:-back}"; echo ;;
  ping)
    curl -s -o /dev/null -w "webhook HTTP %{http_code}\n" --max-time 5 "$BASE" || echo "cannot reach $BASE" ;;
  *)
    echo "usage: shot | tap \"text\" | swipe up|down|left|right | key back|home | ping" ;;
esac
