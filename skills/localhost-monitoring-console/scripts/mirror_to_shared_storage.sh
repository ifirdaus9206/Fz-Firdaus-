#!/data/data/com.termux/files/usr/bin/bash
# mirror_to_shared_storage.sh — one-way mirror of notes/reports from Termux (app-private)
# into the phone's shared storage, so the owner can open them in Files / Drive.
#
# Contract: copy only changed files (sha256), never delete in DEST, print ONE line only
# when something was copied (silent otherwise), so a daily no_agent cron stays quiet.
#
# Cron:  0 3 * * *   no_agent=true   script=mirror_to_shared_storage.sh
# Run:   bash mirror_to_shared_storage.sh [--dry]
set -u
DRY=0
[ "${1:-}" = "--dry" ] && DRY=1

SRC_HOME="${SRC_HOME:-$HOME}"
DEST="${DEST:-/sdcard/Documents/UIM/01-LAPORAN}"
LOG_DIR="${HERMES_HOME:-$HOME/.hermes20}/logs"
LOG="$LOG_DIR/mirror_shared.log"
STATE="${HERMES_HOME:-$HOME/.hermes20}/.mirror_state"

mkdir -p "$LOG_DIR" 2>/dev/null || true
mkdir -p "$DEST" 2>/dev/null || { echo "⚠️ mirror: tidak boleh tulis $DEST"; exit 0; }
touch "$STATE" 2>/dev/null || true

copied=0; skipped=0; failed=0; names=""

copy_one() {
  local src="$1" name="$2" h_src h_dst dst
  dst="$DEST/$name"
  h_src=$(sha256sum "$src" 2>/dev/null | awk '{print $1}')
  [ -z "$h_src" ] && { failed=$((failed+1)); return; }
  if [ -f "$dst" ]; then
    h_dst=$(sha256sum "$dst" 2>/dev/null | awk '{print $1}')
    [ "$h_src" = "$h_dst" ] && { skipped=$((skipped+1)); return; }
  fi
  if [ "$DRY" = "1" ]; then
    copied=$((copied+1)); names="$names$name "; return
  fi
  if cp -p "$src" "$dst" 2>/dev/null; then
    h_dst=$(sha256sum "$dst" 2>/dev/null | awk '{print $1}')
    if [ "$h_src" = "$h_dst" ]; then
      copied=$((copied+1)); names="$names$name "
      printf '%s OK %s -> %s (%s)\n' "$(date '+%F %T')" "$src" "$dst" "${h_src:0:12}" >> "$LOG"
    else
      failed=$((failed+1)); printf '%s ROSAK %s\n' "$(date '+%F %T')" "$src" >> "$LOG"
    fi
  else
    failed=$((failed+1)); printf '%s GAGAL %s\n' "$(date '+%F %T')" "$src" >> "$LOG"
  fi
}

# 1) notes / handoff PDFs sitting in $HOME
while IFS= read -r f; do
  [ -n "$f" ] && copy_one "$f" "$(basename "$f")"
done < <(find "$SRC_HOME" -maxdepth 1 -type f \
           \( -name 'NOTA-*.pdf' -o -name 'NOTA-*.txt' -o -name '*LAPORAN*.pdf' \) 2>/dev/null)

# 2) report folders (prefix the folder name so two reports/ dirs don't collide)
for d in "$SRC_HOME/hermes-console/reports" "$SRC_HOME/reports" \
         "${HERMES_HOME:-$HOME/.hermes20}/reports"; do
  [ -d "$d" ] || continue
  while IFS= read -r f; do
    [ -n "$f" ] && copy_one "$f" "$(basename "$d")-$(basename "$f")"
  done < <(find "$d" -maxdepth 1 -type f \( -name '*.pdf' -o -name '*.md' \) 2>/dev/null)
done

printf '%s copied=%s skipped=%s failed=%s%s\n' "$(date '+%F %T')" \
  "$copied" "$skipped" "$failed" "$([ "$DRY" = 1 ] && echo ' (dry)')" >> "$LOG"

[ "$copied" -gt 0 ] && echo "📁 $copied fail disalin ke storan kongsi ($(basename "$DEST")) · $names"
[ "$failed" -gt 0 ] && echo "⚠️ mirror: $failed fail gagal — semak $LOG"
exit 0
