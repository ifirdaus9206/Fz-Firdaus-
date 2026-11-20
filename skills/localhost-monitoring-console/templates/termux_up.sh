#!/data/data/com.termux/files/usr/bin/bash
# termux_up.sh — TEMPLATE "satu arahan" untuk pengguna bukan-terminal.
# Salin ke ~/bin/hermes-up, chmod +x, ubah SERVICES/URLF ikut projek.
#   hermes-up          → hidupkan semua + papar status/pautan/alamat
#   hermes-up status   → papar sahaja
#
# Kenapa perlu: pengguna yang diminta menaip ~/projek/tools/skrip.sh akan
# tersalah (contoh sebenar: "/hermes-console/tools/wake_ctl.sh" tanpa ~/,
# dan tampal output "auto-mode: ON" sebagai arahan). Satu perkataan lebih baik.
set -u
SERVICES="${SERVICES:-hermes-dashboard hermes-dash-tunnel hermes-console hermes-gateway}"
URLF="${URLF:-$HOME/.hermes20/dashboard_url.txt}"
LOGIN="${LOGIN:-$HOME/.hermes20/secrets/dashboard_login.txt}"
PORT="${PORT:-9119}"

status() {
  command -v termux-wake-lock >/dev/null 2>&1 && printf '%-22s %s\n' "wake-lock" \
    "$([ -f "$HOME/.hermes20/.wake_held" ] && echo 'HELD' || echo 'RELEASED')"
  for s in $SERVICES; do
    printf '%-22s %s\n' "$s" "$(sv status "$s" 2>/dev/null | head -1 | cut -c1-40)"
  done
  echo
  echo "Pautan : $(cat "$URLF" 2>/dev/null || echo '(tiada)')"
  echo "Login  : $(sed -n 's/^username: //p' "$LOGIN" 2>/dev/null) (kata laluan: $LOGIN)"
  echo "Tempat : http://127.0.0.1:$PORT (peranti ini sahaja)"
  LAN=$(ifconfig 2>/dev/null | grep -oE 'inet 192\.168\.[0-9]+\.[0-9]+' | awk '{print $2}' | head -1)
  if [ -n "$LAN" ]; then
    echo "Wi-Fi  : http://$LAN:$PORT (PC/telefon lain, Wi-Fi sama)"
  else
    echo "Wi-Fi  : tiada Wi-Fi (sedang guna data selular)"
  fi
}

case "${1:-up}" in
  status) status ;;
  *)
    termux-wake-lock 2>/dev/null || true
    service-daemon start >/dev/null 2>&1 &
    sleep 1
    for s in $SERVICES; do sv up "$s" >/dev/null 2>&1 || true; done
    sleep 2
    echo "== UP =="
    status
    ;;
esac
