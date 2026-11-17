#!/data/data/com.termux/files/usr/bin/bash
# Cloudflare quick tunnel → Hermes dashboard pada 127.0.0.1:9119.
# URL publik ditulis ke ~/.hermes20/dashboard_url.txt setiap kali tunnel dibuat semula.
# Dijalankan oleh runit (hermes-dash-tunnel) — jangan jalankan dua kali.
set -u
export HOME=/data/data/com.termux/files/home
export PATH=/data/data/com.termux/files/usr/bin:$PATH

OUT="$HOME/.hermes20/dashboard_url.txt"
LOG="$HOME/.hermes20/logs/dashboard-tunnel.log"
mkdir -p "$(dirname "$LOG")"

publish() {
  # ambil URL trycloudflare pertama (bukan api.trycloudflare.com) dan simpan
  local url
  url=$(grep -o "https://[a-z0-9-]*\.trycloudflare\.com" "$LOG" | grep -v '^https://api' | tail -1)
  if [ -n "$url" ]; then
    printf '%s\n' "$url" > "$OUT"
  fi
}

: > "$LOG"
trap publish EXIT

cloudflared tunnel --url http://127.0.0.1:9119 --no-autoupdate 2>&1 | while IFS= read -r line; do
  printf '%s\n' "$line" >> "$LOG"
  case "$line" in
    *trycloudflare.com*)
      u=$(printf '%s' "$line" | grep -o "https://[a-z0-9-]*\.trycloudflare\.com" | grep -v '^https://api' | head -1)
      [ -n "${u:-}" ] && printf '%s\n' "$u" > "$OUT"
      ;;
  esac
  printf '%s\n' "$line"
done
