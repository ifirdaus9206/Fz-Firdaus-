#!/data/data/com.termux/files/usr/bin/bash
# Susun email masuk ke label 1-PENTING / 2-KERJA / 3-PROMOSI.
# Senyap bila berjaya (hanya tulis log). Bercakap hanya bila GAGAL.
set -u
LOG="$HOME/vault/email-inbox/_autosort.log"
DIR="$HOME/vault/email-inbox"

OUT=$(cd "$DIR" && python autosort.py apply --max 80 --days 2 2>&1)
RC=$?

STAMP=$(date "+%Y-%m-%d %H:%M:%S")

if [ "$RC" -ne 0 ]; then
  echo "$STAMP GAGAL rc=$RC" >> "$LOG"
  echo "$OUT" | tail -5 >> "$LOG"
  echo "⚠️ Susun email GAGAL (exit $RC)"
  echo "$OUT" | tail -5
  exit 0
fi

RING=$(echo "$OUT" | grep -- "RINGKASAN" | tail -1)
echo "$STAMP ${RING:-tiada ringkasan}" >> "$LOG"

# Senyap bila tiada email baharu disusun
case "$RING" in
  *'"PROMOSI": 0, "KERJA": 0, "PENTING": 0'*) exit 0 ;;
esac

# Ada email disusun -> beritahu ringkas (satu baris sahaja)
PROM=$(echo "$RING" | sed -n 's/.*"PROMOSI": \([0-9]*\).*/\1/p')
KERJA=$(echo "$RING" | sed -n 's/.*"KERJA": \([0-9]*\).*/\1/p')
PENT=$(echo "$RING" | sed -n 's/.*"PENTING": \([0-9]*\).*/\1/p')
JUM=$(( ${PROM:-0} + ${KERJA:-0} + ${PENT:-0} ))
[ "$JUM" -eq 0 ] && exit 0

echo "📬 $JUM email disusun — Penting ${PENT:-0} · Kerja ${KERJA:-0} · Promosi ${PROM:-0}"
