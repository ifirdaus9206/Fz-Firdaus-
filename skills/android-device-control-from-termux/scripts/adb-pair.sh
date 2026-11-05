#!/data/data/com.termux/files/usr/bin/bash
# adb-pair — pasangkan ADB wayarles (Android 11+).
#
#   adb-pair                                   # status + arahan
#   adb-pair <ip:port_pair> <kod6> [ip:port_connect]
#
# Kod di telefon: Seting → Pilihan pembangun → Nyahpepijat wayarles →
#                 "Pasangkan peranti dengan kod" (IP:port + kod 6 digit).
set -u
command -v adb >/dev/null || { echo "adb tiada — pkg install android-tools"; exit 1; }

if [ $# -eq 0 ]; then
  adb start-server >/dev/null 2>&1
  echo "Peranti tersambung:"; adb devices | sed '1d'
  echo; echo "mDNS (jika build adb menyokong):"
  adb mdns services 2>&1 | grep -v "unknown host service" | sed -n '1,8p' || true
  echo; echo "Guna: adb-pair <ip:port_pair> <kod6> [ip:port_connect]"
  exit 0
fi

PAIR="$1"; CODE="${2:-}"; CONN="${3:-}"
[ -n "$CODE" ] || { echo "kod 6 digit diperlukan"; exit 1; }

echo "→ pair $PAIR"
printf '%s\n' "$CODE" | timeout 60 adb pair "$PAIR" 2>&1 | tail -3

if [ -z "$CONN" ]; then
  HOST="${PAIR%%:*}"
  CONN=$(adb mdns services 2>/dev/null | awk '/_adb-tls-connect/ {print $3}' | head -1)
  if [ -z "$CONN" ]; then
    echo "nota: mdns tidak disokong build adb ini — ambil port dari skrin Nyahpepijat wayarles"
    CONN="$HOST:5555"
  fi
fi

echo "→ connect $CONN"
timeout 30 adb connect "$CONN" 2>&1 | tail -2
sleep 2
adb devices | sed '1d'
if adb devices | grep -q "device$"; then
  echo "SIAP — cuba: ui shot"
else
  echo "Belum bersambung. Pastikan nyahpepijat wayarles aktif dan port connect betul."
  exit 2
fi
