#!/usr/bin/env bash
# evidence_baseline.sh — capture before/after evidence for a docs/wiki edit, without git.
#
#   ./evidence_baseline.sh snapshot <dir> <file...>   # run FIRST, before any edit
#   ./evidence_baseline.sh diff     <dir> <file...>   # run after edits; prints the report table
#
# Snapshot stores "<lines>\t<sha256>\t<path>" in <dir>/.evidence-baseline.txt.
# diff prints: | file | baris sebelum | baris selepas | sha256 | STATUS |
# STATUS is SAMA (unchanged), DIUBAH, or BAHARU (file absent from snapshot).
# Protected files listed in the snapshot but not in the diff args still get reported.
set -u

mode="${1:-}"; dir="${2:-}"; shift 2 2>/dev/null || true
[ -z "$mode" ] || [ -z "$dir" ] && { echo "usage: $0 {snapshot|diff} <dir> <file...>" >&2; exit 2; }
cd "$dir" || exit 2
snap=".evidence-baseline.txt"

hash_of() { sha256sum "$1" 2>/dev/null | cut -d' ' -f1; }
lines_of() { wc -l < "$1" 2>/dev/null | tr -d ' '; }

case "$mode" in
  snapshot)
    : > "$snap"
    for f in "$@"; do
      if [ -f "$f" ]; then
        printf '%s\t%s\t%s\n' "$(lines_of "$f")" "$(hash_of "$f")" "$f" >> "$snap"
      else
        printf '0\t-\t%s\n' "$f" >> "$snap"   # file does not exist yet (to be created)
      fi
    done
    echo "snapshot -> $PWD/$snap"
    cat "$snap"
    ;;
  diff)
    [ -f "$snap" ] || { echo "no snapshot in $PWD ($snap missing) — before-hash unavailable" >&2; exit 1; }
    echo "| Fail | Baris sebelum | Baris selepas | sha256 | Status |"
    echo "|---|---|---|---|---|"
    # union of snapshot paths and current args, snapshot order first
    list=$( { cut -f3 "$snap"; printf '%s\n' "$@"; } | awk '!seen[$0]++' )
    while IFS= read -r f; do
      [ -z "$f" ] && continue
      before_l=$(awk -F'\t' -v p="$f" '$3==p{print $1}' "$snap")
      before_s=$(awk -F'\t' -v p="$f" '$3==p{print $2}' "$snap")
      now_l=$(lines_of "$f"); now_s=$(hash_of "$f")
      [ -z "$now_s" ] && now_s="-"; [ -z "$now_l" ] && now_l="-"
      if [ "$before_s" = "-" ] || [ -z "$before_s" ]; then st="BAHARU"; before_l="${before_l:-0}"
      elif [ "$before_s" = "$now_s" ]; then st="SAMA"
      else st="DIUBAH"; fi
      printf '| `%s` | %s | %s | `%s` | %s |\n' "$f" "$before_l" "$now_l" "$now_s" "$st"
    done <<< "$list"
    ;;
  *) echo "usage: $0 {snapshot|diff} <dir> <file...>" >&2; exit 2 ;;
esac
