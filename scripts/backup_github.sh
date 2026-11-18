#!/usr/bin/env bash
# Sandaran malam ~/.hermes20 ke GitHub (SOP: knowledge_base/sop/backup.md)
#
# Prinsip keselamatan:
#   1. Jika ada fail rahsia tersenarai (fail .env, auth.json, config.yaml, DB, sessions/, logs/)
#      → unstage semua, AMARAN ke stdout+log, exit 3. Tiada commit.
#   2. Jika ada corak kelayakan dalam baris yang ditambah → unstage, AMARAN, exit 3.
#   3. Push HANYA jika remote 'origin' wujud; tiada --force, tiada token disimpan.
#   4. stdout senyap apabila semuanya sihat (selamat untuk cron).
#   5. Kegagalan push tidak memadam commit tempatan.
#
# exit: 0 = ok/senyap, 1 = ralat git, 3 = rahsia ditemui (commit dibatalkan), 4 = push gagal

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

# --- pastikan ini repo git ---
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  printf 'AMARAN: %s bukan repo git — jalankan "git init" dahulu.\n' "$HERMES_HOME"
  LOG_MSG "GAGAL: bukan repo git"
  exit 1
fi

# --- stage semua perubahan (fail dalam .gitignore tidak diambil) ---
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

# --- pengawal 2: imbasan rahsia DUA PERINGKAT pada baris yang ditambah ---
#
# PERINGKAT 1 — corak keras sahaja (bentuk kelayakan sebenar yang tidak boleh
#   tersilap). Dipindai pada SEMUA fail yang di-stage, TERMASUK *.md dan docs/.
#   Tiada pengecualian: padanan peringkat 1 sentiasa membatalkan commit (exit 3).
#
# PERINGKAT 2 — tugasan `nama=nilai` sensitif. HANYA pada fail BUKAN-dokumentasi.
#   Dokumentasi sah memang memetik contoh seperti `PASSWORD=xxxxxxxx` atau
#   `token: <nilai>`, jadi *.md, docs/, references/, templates/ serta fail
#   *.example|*.sample|*.dist dikecualikan DI PERINGKAT INI SAHAJA (peringkat 1
#   masih memindai semuanya). Nilai ditapis dahulu: placeholder, nilai < 12
#   aksara, nilai dalam <...>/$()/${...} dan satu aksara berulang diabaikan.
#
# Nota: corak "token bogel" (satu baris aksara rawak panjang) dibuang kerana ia
#   palsu-positif pada blok hash/signatur dalam dokumentasi; bentuk kunci
#   sebenar sudah ditangkap oleh peringkat 1.

# PERINGKAT 1: corak keras (AKIA dikendalikan berasingan — lihat di bawah)
HARD_RE='(sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|ghs_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{30,}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})'
# AKIA: dipadankan penuh (tamak) supaya akhiran boleh diperiksa.
# AWS menetapkan bahawa pseudo-kelayakan dalam DOKUMENTASI sentiasa berakhir
# dengan "EXAMPLE" (cth AKIAIOSFODNN7EXAMPLE) dan tidak memberi apa-apa akses;
# kunci akses sebenar tidak pernah berakhir dengan "EXAMPLE". Jadi hanya bentuk
# itu dikecualikan — setiap AKIA sebenar (16+ aksara, bukan EXAMPLE) tetap exit 3.
AKIA_RE='AKIA[0-9A-Z]{16,}'

# PERINGKAT 2: tugasan nama=nilai sensitif
ASSIGN_RE="(password|passwd|secret|token|api[_-]?key|app_password|client_secret)[\"']?[[:space:]]*[:=][[:space:]]*[\"']?[^\"'[:space:]]+"

# Fail dokumentasi? (hanya mengecualikan PERINGKAT 2, bukan peringkat 1)
IS_DOC() {
  case "$1" in
    *.md|docs/*|*/docs/*|references/*|*/references/*|templates/*|*/templates/*|*.example|*.sample|*.dist)
      return 0 ;;
  esac
  return 1
}

# Nilai calon: pulangkan 0 = rahsia sebenar (lulus tapisan), 1 = abaikan.
REAL_VALUE() {
  local v="$1" first rest
  v="${v%$'\r'}"
  # buang tanda baca/petikan penutup
  while [ "${#v}" -gt 0 ]; do
    case "${v: -1}" in
      '"'|"'"|','|';'|')'|']'|'}') v="${v%?}" ;;
      *) break ;;
    esac
  done
  [ "${#v}" -ge 12 ] || return 1                  # terlalu pendek
  case "$v" in
    '<'*|'$('*|'${'*) return 1 ;;                # <...> / $(...) / ${...}
  esac
  case "$v" in                                     # placeholder
    *REDACTED*|*DIMASK*|*PLACEHOLDER*|*CHANGEME*|*YOUR_*|*example*|*contoh*)
      return 1 ;;
  esac
  first="${v:0:1}"
  rest="${v//"$first"/}"
  [ -z "$rest" ] && return 1                       # satu aksara berulang (xxxx, ****)
  return 0
}

HIT_FILES=""
while IFS= read -r f; do
  [ -n "$f" ] || continue
  added="$(git diff --cached -U0 -- "$f" 2>/dev/null \
    | grep -E '^\+' | grep -vE '^\+\+\+' | sed 's/^+//' || true)"
  [ -n "$added" ] || continue

  tier=""
  # --- PERINGKAT 1: semua fail, tiada pengecualian ---
  if printf '%s\n' "$added" | grep -qE "$HARD_RE"; then
    tier=1
  elif printf '%s\n' "$added" | grep -oE "$AKIA_RE" | grep -qvE 'EXAMPLE$'; then
    # AKIA sebenar (bukan pseudo-kelayakan dokumentasi AWS berakhir EXAMPLE)
    tier=1
  elif printf '%s\n' "$added" | grep -qE "$AKIA_RE"; then
    LOG_MSG "ABAIKAN (pseudo-kelayakan AWS EXAMPLE, bukan rahsia): $f"
  # --- PERINGKAT 2: fail bukan-dokumentasi sahaja ---
  elif ! IS_DOC "$f"; then
    while IFS= read -r line; do
      [ -n "$line" ] || continue
      vals="$(printf '%s\n' "$line" \
        | grep -oiE "$ASSIGN_RE" \
        | sed -E "s/^[^:=]*[:=][[:space:]]*[\"']?//" || true)"
      [ -n "$vals" ] || continue
      while IFS= read -r val; do
        if [ -n "$val" ] && REAL_VALUE "$val"; then
          tier=2
          break
        fi
      done <<< "$vals"
      [ -n "$tier" ] && break
    done <<< "$added"
  fi

  [ -n "$tier" ] && HIT_FILES="${HIT_FILES}${f} (peringkat ${tier})"$'\n'
done < <(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null)


if [ -n "$HIT_FILES" ]; then
  git reset -q 2>/dev/null || true
  printf 'AMARAN: imbasan rahsia menemui padanan — commit DIBATALKAN.\n'
  printf '%s' "$HIT_FILES" | sed 's/^/  - /'
  printf 'Semak fail di atas, pindahkan rahsia ke .env, dan tambah corak ke .gitignore.\n'
  LOG_MSG "DIBATALKAN (imbasan rahsia): $(printf '%s' "$HIT_FILES" | tr '\n' ' ')"
  exit 3
fi

# --- commit ---
if ! git commit -q -m "sandaran auto $(STAMP)" 2>>"$LOG"; then
  printf 'AMARAN: git commit gagal — lihat %s\n' "$LOG"
  LOG_MSG "GAGAL: git commit"
  exit 1
fi
SHA="$(git rev-parse --short HEAD)"
LOG_MSG "commit $SHA dibuat"

# --- push hanya jika remote origin wujud ---
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
