#!/data/data/com.termux/files/usr/bin/bash
# sofia-tarik.sh — telefon tarik status.json dari repo relay 'sofia-status'.
# Dijalankan oleh cron setiap 5 minit. SENYAP bila sihat (tiada output).
# Gagal = cetak 1 baris supaya bos tahu (cron no_agent hantar ke Telegram).

set -u
DIR="$HOME/sofia-status"
LOG="$DIR/tarik.log"

[ -d "$DIR/.git" ] || exit 0          # repo belum wujud — senyap sahaja

cd "$DIR" || exit 0
OUT=$(git pull --quiet --ff-only 2>&1)
KOD=$?
MASA=$(date "+%Y-%m-%d %H:%M:%S")

if [ $KOD -ne 0 ]; then
  echo "$MASA GAGAL: $OUT" >> "$LOG"
  tail -n 40 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
  echo "SOFIA: tarikan status PC GAGAL — $OUT"
  exit 1
fi

echo "$MASA ok ${OUT:-tiada perubahan}" >> "$LOG"
tail -n 40 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
exit 0
