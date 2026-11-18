#!/data/data/com.termux/files/usr/bin/bash
# relay_pull.sh — TEMPLATE: pull a private relay repo so the console can read it locally.
#
# Install: cp to <hermes home>/scripts/<name>.sh, chmod +x, then
#   cronjob(action='create', schedule='*/5 * * * *', no_agent=true,
#           script='<name>.sh', name='pull remote status')
#
# Contract that makes it safe as a no_agent job:
#   * healthy → exit 0 with EMPTY stdout (no delivery, no noise);
#   * repo not cloned yet → exit 0 silent (the feature simply is not wired up);
#   * failure → ONE line on stdout (delivered to the owner) and non-zero exit;
#   * its own log is capped, so a broken pull cannot grow forever.
set -u
DIR="$HOME/sofia-status"          # local clone of the relay repo
LOG="$DIR/tarik.log"

[ -d "$DIR/.git" ] || exit 0      # not wired up yet — stay silent

cd "$DIR" || exit 0
OUT=$(git pull --quiet --ff-only 2>&1)
KOD=$?
MASA=$(date "+%Y-%m-%d %H:%M:%S")

if [ $KOD -ne 0 ]; then
  echo "$MASA GAGAL: $OUT" >> "$LOG"
  tail -n 40 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
  echo "REMOTE: status pull GAGAL — $OUT"
  exit 1
fi

echo "$MASA ok ${OUT:-tiada perubahan}" >> "$LOG"
tail -n 40 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
exit 0
