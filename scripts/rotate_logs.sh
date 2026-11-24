#!/data/data/com.termux/files/usr/bin/bash
# rotate_logs.sh — putaran log mingguan (senyap bila tiada apa dilakukan)
# Peraturan:
#   - fail *.log melebihi 5 MB  → dipotong ke 0 (proses terus menulis)
#   - arkib *.log.1 lebih 7 hari → dibuang
#   - log servis svlogd (logs/<servis>/) TIDAK disentuh — runit uruskan
# Guna: bash rotate_logs.sh [--dry-run]
set -u
LOG_DIR="${ROTATE_ROOT:-$HOME/.hermes20/logs}"
MAX=$((5 * 1024 * 1024))
DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1
acted=0

for f in "$LOG_DIR"/*.log; do
  [ -f "$f" ] || continue
  sz=$(stat -c%s "$f" 2>/dev/null || echo 0)
  if [ "$sz" -gt "$MAX" ]; then
    mb=$((sz / 1048576))
    if [ "$DRY" -eq 1 ]; then
      echo "[dry] akan potong $f (${mb}MB)"
    else
      : > "$f"
      echo "dipotong: $(basename "$f") (${mb}MB → 0)"
    fi
    acted=1
  fi
done

# arkib lama
find "$LOG_DIR" -maxdepth 1 -type f -name '*.log.[0-9]*' -mtime +7 2>/dev/null | while read -r f; do
  if [ "$DRY" -eq 1 ]; then echo "[dry] akan buang $f"; else rm -f "$f"; echo "dibuang: $(basename "$f")"; fi
done

# senyap bila tiada tindakan (untuk cron no_agent)
if [ "$DRY" -eq 0 ] && [ "$acted" -eq 0 ]; then
  # masih mungkin ada arkib dibuang; jika tiada output langsung, senyap
  :
fi
exit 0
