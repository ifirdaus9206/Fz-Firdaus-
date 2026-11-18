#!/data/data/com.termux/files/usr/bin/bash
# [KETUA 2026-11-18] Penyerahan gateway terkawal selepas tampalan sesi Telegram.
# Ia melepaskan diri (setsid) supaya TIDAK terbunuh bersama gateway lama.
set -u
LOG="$HOME/.hermes20/logs/gw_handover.log"

if [ "${1:-}" != "--worker" ]; then
  setsid bash "$0" --worker >>"$LOG" 2>&1 </dev/null &
  exit 0
fi

PING() { curl -s -m 5 -o /dev/null -w "%{http_code}" http://127.0.0.1:8787/api/ping; }
echo "=== $(date '+%F %T') handover mula (pid lama: $(pgrep -f 'hermes gateway run' | tr '\n' ' ')) ==="
pkill -f "hermes gateway run" 2>/dev/null || true
sleep 12
for i in $(seq 1 12); do
  pgrep -f "hermes gateway run" >/dev/null 2>&1 && break
  sleep 3
done
sleep 12
echo "$(date '+%F %T') pid baru: $(pgrep -f 'hermes gateway run' | tr '\n' ' ')"
echo "$(date '+%F %T') konsol8787: $(PING)"
sv status hermes-gateway 2>&1
echo "=== selesai ==="
exit 0
