#!/data/data/com.termux/files/usr/bin/bash
# Susun email masuk ke label 1-PENTING / 2-KERJA / 3-PROMOSI.
# Senyap bila berjaya (hanya tulis log). Bercakap hanya bila GAGAL.
set -u
LOG="$HOME/vault/email-inbox/_autosort.log"
DIR="$HOME/vault/email-inbox"

OUT=$(cd "$DIR" && python autosort.py apply --max 800 2>&1)
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

# SENYAP bila berjaya. Laporan hanya sekali sehari (21:00) oleh email_digest.sh.
# Hanya kegagalan (di atas) yang bercakap segera.
exit 0
