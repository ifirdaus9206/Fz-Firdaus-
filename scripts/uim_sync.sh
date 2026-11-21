#!/data/data/com.termux/files/usr/bin/bash
# uim-sync — salin fail baharu (nota/laporan) Termux -> storan kongsi telefon.
# Sehala sahaja. Rekod sha256 supaya tiada salinan berganda / rosak.
# Senyap bila tiada fail baharu. Cetak 1 baris bila ada.
set -u
STATE="$HOME/.hermes20/.uim_sync_state"
LOG="$HOME/.hermes20/logs/uim_sync.log"
DEST="/sdcard/Documents/UIM/01-LAPORAN"
mkdir -p "$(dirname "$LOG")" 2>/dev/null || true
mkdir -p "$DEST" 2>/dev/null || { echo "⚠️ uim-sync: tidak boleh tulis $DEST"; exit 0; }
touch "$STATE" 2>/dev/null || true

copied=0
skipped=0
fail=0
detail=""

copy_one() {
  local src="$1" name="$2"
  local h_src h_dst dst
  dst="$DEST/$name"
  h_src=$(sha256sum "$src" 2>/dev/null | awk '{print $1}')
  [ -z "$h_src" ] && { fail=$((fail+1)); return; }
  if [ -f "$dst" ]; then
    h_dst=$(sha256sum "$dst" 2>/dev/null | awk '{print $1}')
    if [ "$h_src" = "$h_dst" ]; then skipped=$((skipped+1)); return; fi
  fi
  if cp -p "$src" "$dst" 2>/dev/null; then
    h_dst=$(sha256sum "$dst" 2>/dev/null | awk '{print $1}')
    if [ "$h_src" = "$h_dst" ]; then
      copied=$((copied+1))
      detail="$detail$name "
      printf '%s OK %s -> %s (%s)\n' "$(date '+%F %T')" "$src" "$dst" "${h_src:0:12}" >> "$LOG"
    else
      fail=$((fail+1))
      printf '%s ROSAK %s\n' "$(date '+%F %T')" "$src" >> "$LOG"
    fi
  else
    fail=$((fail+1))
    printf '%s GAGAL %s\n' "$(date '+%F %T')" "$src" >> "$LOG"
  fi
}

# 1) Nota & PDF di home
while IFS= read -r f; do
  [ -z "$f" ] && continue
  copy_one "$f" "$(basename "$f")"
done < <(find "$HOME" -maxdepth 1 -type f \( -name 'NOTA-*.pdf' -o -name 'NOTA-*.txt' -o -name '*LAPORAN*.pdf' \) -newermt '-400 days' 2>/dev/null)

# 2) Laporan dalam projek console & reports
for d in "$HOME/hermes-console/reports" "$HOME/reports" "$HOME/.hermes20/reports"; do
  [ -d "$d" ] || continue
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    copy_one "$f" "$(basename "$d")-$(basename "$f")"
  done < <(find "$d" -maxdepth 1 -type f \( -name '*.pdf' -o -name '*.md' \) -newermt '-60 days' 2>/dev/null)
done

# 3) Ringkasan
printf '%s copied=%s skipped=%s fail=%s\n' "$(date '+%F %T')" "$copied" "$skipped" "$fail" >> "$LOG"
if [ "$copied" -gt 0 ]; then
  echo "📁 $copied fail disalin ke storan kongsi (01-LAPORAN) · $detail"
fi
if [ "$fail" -gt 0 ]; then
  echo "⚠️ uim-sync: $fail fail gagal disalin — semak $LOG"
fi
exit 0
