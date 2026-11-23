#!/data/data/com.termux/files/usr/bin/bash
# Susun email masuk ke label 1-PENTING / 2-KERJA / 3-PROMOSI.
# Senyap bila berjaya (hanya tulis log). Bercakap hanya bila GAGAL.
set -u
LOG="$HOME/vault/email-inbox/_autosort.log"
DIR="$HOME/vault/email-inbox"

# Cuba semula bila rangkaian/DNS gagal sementara (gaierror, timeout).
for i in 1 2 3; do
  OUT=$(cd "$DIR" && python autosort.py apply --max 800 2>&1)
  RC=$?
  [ "$RC" -eq 0 ] && break
  case "$OUT" in
    *gaierror*|*"No address associated"*|*"Temporary failure"*|*"timed out"*|*"Connection reset"*)
      if [ "$i" -lt 3 ]; then
        sleep 60
        continue
      fi
      ;;
  esac
  break
done

STAMP=$(date "+%Y-%m-%d %H:%M:%S")

if [ "$RC" -ne 0 ]; then
  echo "$STAMP GAGAL rc=$RC (cubaan $i/3)" >> "$LOG"
  echo "$OUT" | tail -5 >> "$LOG"
  echo "⚠️ Susun email GAGAL (exit $RC, cubaan $i/3)"
  echo "$OUT" | tail -5
  exit 0
fi

RING=$(echo "$OUT" | grep -- "RINGKASAN" | tail -1)
echo "$STAMP ${RING:-tiada ringkasan}" >> "$LOG"

# SENYAP bila berjaya. Laporan hanya sekali sehari (21:00) oleh email_digest.sh.
# Hanya kegagalan (di atas) yang bercakap segera.
exit 0
