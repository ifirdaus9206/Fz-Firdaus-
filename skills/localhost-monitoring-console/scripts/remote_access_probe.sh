#!/data/data/com.termux/files/usr/bin/bash
# remote_access_probe.sh — satu laporan: adakah dashboard boleh dicapai, dari mana,
# dan pautan awam mana yang masih hidup. Selamat dijalankan bila-bila masa (read-only).
#   Guna: bash scripts/remote_access_probe.sh [PORT]
set -u
PORT="${1:-9119}"
SVC_DASH="${SVC_DASH:-hermes-dashboard}"
SVC_TUN="${SVC_TUN:-hermes-dash-tunnel}"
URLF="${URLF:-$HOME/.hermes20/dashboard_url.txt}"

echo "== PORT $PORT =="
grep -ho "host [0-9.]*" "$PREFIX/var/service/$SVC_DASH/run" 2>/dev/null | sed 's/^/bind: /'

echo "== SERVIS =="
for s in "$SVC_DASH" "$SVC_TUN"; do printf '%-24s %s\n' "$s" "$(sv status "$s" 2>/dev/null | head -1)"; done

echo "== LOOPBACK =="
curl -s -m 5 -o /dev/null -w '127.0.0.1:%{http_code}\n' "http://127.0.0.1:$PORT/"

echo "== RANGKAIAN =="
ifconfig 2>/dev/null | grep -oE 'inet (192\.168|10\.|172\.(1[6-9]|2[0-9]|3[01]))\.[0-9.]*' \
  | awk '{print "LAN: "$2}' || true
ifconfig 2>/dev/null | grep -q '^ccmni' && echo "nota: ccmni hadir = data selular (tiada LAN, tiada capaian luar)"
for ip in $(ifconfig 2>/dev/null | grep -oE 'inet 192\.168\.[0-9]+\.[0-9]+' | awk '{print $2}'); do
  curl -s -m 4 -o /dev/null -w "LAN $ip:%{http_code}\n" "http://$ip:$PORT/"
done

echo "== PAUTAN AWAM =="
URL="$(cat "$URLF" 2>/dev/null || true)"
echo "fail: ${URL:-(tiada)}"
[ -n "$URL" ] && curl -s -m 12 -o /dev/null \
  -w 'awam: http=%{http_code} dns=%{time_namelookup}s total=%{time_total}s\n' "$URL/"
echo "nota: http=000 + dns=0.000s = nama sudah luput (quick tunnel bertukar), bukan masalah data pengguna"
