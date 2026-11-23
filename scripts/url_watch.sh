#!/data/data/com.termux/files/usr/bin/bash
# url_watch.sh — beritahu HANYA bila URL tunnel berubah. Senyap jika sama.
set -u
H="$HOME/.hermes20"
CUR_FILE="$H/dashboard_url.txt"
LAST="$H/.url_last_seen"
CUR="$(grep -o 'https://[^ ]*trycloudflare.com' "$CUR_FILE" 2>/dev/null | head -1)"
[ -z "$CUR" ] && CUR="$(grep -o 'https://[^ ]*' "$CUR_FILE" 2>/dev/null | head -1)"
[ -z "$CUR" ] && exit 0

# sentiasa salin URL semasa ke storan telefon supaya bos boleh buka tanpa cari
SD="/sdcard/Documents/UIM"
if [ -d "$SD" ] && [ -w "$SD" ]; then
  printf '%s/?tab=pusat\n' "$CUR" > "$SD/KONSOL-URL.txt" 2>/dev/null || true
fi
LASTV="$(cat "$LAST" 2>/dev/null)"
if [ "$CUR" != "$LASTV" ]; then
  printf '%s' "$CUR" > "$LAST"
  [ -n "$LASTV" ] && echo "🔑 URL BERTUKAR — KUNCI BAHARU: $CUR"
fi
exit 0
