#!/usr/bin/env bash
# Sandaran malam <HOME_DIR> ke GitHub — template yang sudah diuji.
# Ganti HERMES_HOME dengan direktori yang hendak disandarkan (cth $HOME/.hermes20).
#
# Prinsip:
#   1. Fail rahsia ter-stage (/.env, auth.json, config.yaml, *.db, sessions/, logs/, pastes/)
#      → unstage semua, AMARAN ke stdout+log, exit 3. Tiada commit.
#   2. Corak kelayakan dalam baris yang ditambah → unstage, AMARAN, exit 3.
#   3. Push HANYA jika remote 'origin' wujud; tiada --force, tiada token disimpan.
#   4. stdout senyap apabila sihat (selamat untuk cron).
#   5. Push gagal tidak memadam commit tempatan.
#
# exit: 0 = ok/senyap, 1 = ralat git, 3 = rahsia ditemui, 4 = push gagal

set -uo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes20}"
LOG_DIR="$HERMES_HOME/logs"
LOG="$LOG_DIR/backup.log"
STAMP() { date '+%Y-%m-%d %H:%M'; }
LOG_MSG() { printf '%s %s\n' "$(STAMP)" "$*" >>"$LOG" 2>/dev/null || true; }

mkdir -p "$LOG_DIR" 2>/dev/null || true

cd "$HERMES_HOME" 2>/dev/null || {
  printf 'AMARAN: tidak dapat masuk %s\n' "$HERMES_HOME"
  exit 1
}

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  printf 'AMARAN: %s bukan repo git — jalankan "git init" dahulu.\n' "$HERMES_HOME"
  LOG_MSG "GAGAL: bukan repo git"
  exit 1
fi

if ! git add -A 2>>"$LOG"; then
  printf 'AMARAN: git add gagal — lihat %s\n' "$LOG"
  LOG_MSG "GAGAL: git add"
  exit 1
fi

# --- pengawal 1: fail terlarang tidak boleh berada dalam index ---
FORBIDDEN="$(git ls-files --cached 2>/dev/null \
  | grep -E '(^|/)(\.env|\.env\..*|auth\.json|auth\.lock|config\.yaml|config\.yaml\.bak.*|state\.db.*|kanban\.db.*|gateway\.pid)$|^(sessions|logs|cache|pastes)/' \
  || true)"

if [ -n "$FORBIDDEN" ]; then
  git reset -q 2>/dev/null || true
  printf 'AMARAN: fail rahsia ter stage — commit DIBATALKAN.\n'
  printf '%s\n' "$FORBIDDEN" | sed 's/^/  - /'
  LOG_MSG "DIBATALKAN (fail rahsia ter stage): $(printf '%s' "$FORBIDDEN" | tr '\n' ' ')"
  exit 3
fi

# --- tiada perubahan? senyap, keluar 0 ---
if git diff --cached --quiet 2>/dev/null; then
  exit 0
fi

# --- pengawal 2: imbasan rahsia pada baris yang ditambah ---
HARD_RE='(sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|ghs_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{30,}|xox[bpas]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)'
ASSIGN_RE='(api[_-]?key|api[_-]?secret|access[_-]?token|auth[_-]?token|client[_-]?secret|secret|password|passwd|token)["'"'"']?[[:space:]]*[:=][[:space:]]*["'"'"']?[A-Za-z0-9_./+=-]{12,}'
BARE_RE='^\+[A-Za-z0-9_/+=-]{32,}$'

HIT_FILES=""
while IFS= read -r f; do
  [ -n "$f" ] || continue
  added="$(git diff --cached -- "$f" 2>/dev/null | grep -E '^\+' || true)"
  [ -n "$added" ] || continue
  if printf '%s\n' "$added" | grep -qE "$HARD_RE" \
     || printf '%s\n' "$added" | grep -qiE "$ASSIGN_RE" \
     || printf '%s\n' "$added" | grep -qE "$BARE_RE"; then
    HIT_FILES="${HIT_FILES}${f}"$'\n'
  fi
done < <(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null)

if [ -n "$HIT_FILES" ]; then
  git reset -q 2>/dev/null || true
  printf 'AMARAN: imbasan rahsia menemui padanan — commit DIBATALKAN.\n'
  printf '%s' "$HIT_FILES" | sed 's/^/  - /'
  printf 'Semak fail di atas, pindahkan rahsia ke .env, dan tambah corak ke .gitignore.\n'
  LOG_MSG "DIBATALKAN (imbasan rahsia): $(printf '%s' "$HIT_FILES" | tr '\n' ' ')"
  exit 3
fi

if ! git commit -q -m "sandaran auto $(STAMP)" 2>>"$LOG"; then
  printf 'AMARAN: git commit gagal — lihat %s\n' "$LOG"
  LOG_MSG "GAGAL: git commit"
  exit 1
fi
SHA="$(git rev-parse --short HEAD)"
LOG_MSG "commit $SHA dibuat"

if git remote get-url origin >/dev/null 2>&1; then
  if PUSH_OUT="$(git push origin HEAD 2>&1)"; then
    LOG_MSG "push berjaya: $SHA"
  else
    printf 'AMARAN: git push gagal — commit %s kekal setempat.\n' "$SHA"
    printf '%s\n' "$PUSH_OUT" | tail -3
    LOG_MSG "PUSH GAGAL ($SHA): $(printf '%s' "$PUSH_OUT" | tr '\n' ' ' | cut -c1-300)"
    exit 4
  fi
else
  LOG_MSG "tiada remote — commit tempatan sahaja ($SHA)"
fi

exit 0
