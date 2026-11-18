#!/data/data/com.termux/files/usr/bin/bash
# [KETUA 2026-11-17] Mula semula gateway SEKALI sahaja selepas tampalan
# DM-thread (plugins/platforms/telegram/adapter.py) supaya ia dimuatkan.
# Dipanggil oleh cron one-shot; bukan dari dalam proses gateway.
LOG="$HOME/.hermes20/logs/gw_restart_once.log"
STAMP=$(date '+%Y-%m-%d %H:%M:%S')
OUT=$(curl -s -m 20 -X POST http://127.0.0.1:8787/api/svc/hermes-gateway \
      -H 'Content-Type: application/json' -d '{"action":"restart"}' 2>&1)
echo "$STAMP restart-diminta: $(printf '%s' "$OUT" | head -c 300)" >> "$LOG"
# senyap kepada Telegram (no_agent: stdout kosong = tiada mesej)
exit 0
