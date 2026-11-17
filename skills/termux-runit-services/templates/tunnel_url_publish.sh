#!/data/data/com.termux/files/usr/bin/bash
# Template: run a Cloudflare quick tunnel under runit and keep the CURRENT public URL in one file.
# Copy → edit TARGET/OUT/PORT → chmod 755 → point the service `run` at it.
# Why: quick-tunnel hostnames change on every start, so consumers must read a file the tunnel
# rewrites, never a value copied into a doc or chat message.
set -u
export HOME=/data/data/com.termux/files/home
export PATH=/data/data/com.termux/files/usr/bin:$PATH

TARGET="http://127.0.0.1:9119"          # local service the tunnel exposes
OUT="$HOME/.hermes20/dashboard_url.txt" # single source of truth for the public URL
LOG="$HOME/.hermes20/logs/tunnel.log"

mkdir -p "$(dirname "$LOG")" "$(dirname "$OUT")"
: > "$LOG"

publish() { # last-resort publish on exit
  local url
  url=$(grep -o "https://[a-z0-9-]*\.trycloudflare\.com" "$LOG" | grep -v '^https://api' | tail -1)
  [ -n "$url" ] && printf '%s\n' "$url" > "$OUT"
}
trap publish EXIT

cloudflared tunnel --url "$TARGET" --no-autoupdate 2>&1 | while IFS= read -r line; do
  printf '%s\n' "$line" >> "$LOG"
  case "$line" in
    *trycloudflare.com*)
      u=$(printf '%s' "$line" | grep -o "https://[a-z0-9-]*\.trycloudflare\.com" \
            | grep -v '^https://api' | head -1)
      [ -n "${u:-}" ] && printf '%s\n' "$u" > "$OUT"
      ;;
  esac
  printf '%s\n' "$line"        # keep feeding the runit log
done
