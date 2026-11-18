#!/data/data/com.termux/files/usr/bin/bash
# [KETUA 2026-11-18] Restart gateway BERSIH di bawah runit.
# Punca: gateway orphan (pid 5292) pegang gateway.lock; runsv cuba hidupkan
# gateway baru setiap ~2s -> gagal -> gelung. Setiap cubaan panggil
# termux-wake-lock (dari run script lama) -> notifikasi berulang.
set -u
LOG="$HOME/.hermes20/logs/gw_fix_result.txt"
exec >"$LOG" 2>&1
echo "=== $(date '+%F %T') mula pembetulan gateway ==="

sv down hermes-gateway 2>/dev/null || true
sleep 1
pkill -f "hermes gateway run" 2>/dev/null || true
sleep 4
# buang lock basi jika masih ada
if [ -f "$HOME/.hermes20/gateway.lock" ] && ! pgrep -f "hermes gateway run" >/dev/null; then
  rm -f "$HOME/.hermes20/gateway.lock"
  echo "gateway.lock basi dibuang"
fi
sv up hermes-gateway
sleep 30

echo "--- proses gateway ---"
pgrep -af "hermes gateway run"
echo "--- status runit ---"
sv status hermes-gateway
echo "--- panggilan wake-lock (patut 0) ---"
pgrep -af "termux-wake-lock" || echo "0 (tiada)"
echo "--- 40 baris log gateway terakhir ---"
tail -12 "$HOME/.hermes20/logs/gateway.log"
echo "=== $(date '+%F %T') selesai ==="
