#!/usr/bin/env bash
# Matriks regresi untuk pengawal imbasan rahsia dalam scripts/backup_github.sh
#
# Guna (dari mana-mana folder):
#   bash skills/devops/safe-git-config-backup/scripts/scan_matrix_test.sh
#
# Reka bentuk:
#   - Skrip mencari akar repo daripada lokasi fail ini, jadi ia boleh dijalankan
#     dari mana-mana cwd.
#   - Repo buangan (git init) dicipta di dalam folder sementara DALAM repo, dan
#     backup_github.sh dijalankan dengan HERMES_HOME menunjuk ke repo buangan itu.
#     Oleh sebab repo buangan tiada remote 'origin', tiada commit/push berlaku pada
#     repo sebenar. Folder sementara dipadam semula (trap) selepas ujian.
#   - Setiap kes: tulis fail -> jalankan skrip -> bandingkan exit dengan jangkaan.
#     Jangkaan 3 = rahsia dikesan (blok), 0 = diabaikan (placeholder/dokumentasi).
#
# Nota keselamatan: TIADA baris dalam fail ini mengandungi corak kunci yang lengkap.
# Setiap kunci palsu dibina semasa runtime melalui pemboleh ubah berasingan, supaya
# fail ini sendiri tidak mencetuskan pengawal peringkat 1 jika ia di-commit.
set -uo pipefail

SKRIP_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(git -C "$SKRIP_DIR" rev-parse --show-toplevel 2>/dev/null || true)"
[ -n "$REPO" ] || REPO="$HOME/.hermes20"
cd "$REPO" || { echo "RALAT: tidak dapat masuk $REPO" >&2; exit 1; }

GUARD="scripts/backup_github.sh"
[ -f "$GUARD" ] || { echo "RALAT: skrip tidak dijumpai: $REPO/$GUARD" >&2; exit 1; }

SB="$(mktemp -d "$REPO/.scan-matrix.XXXXXX")" || { echo "RALAT: mktemp gagal" >&2; exit 1; }
cleanup() { rm -rf "$SB"; }
trap cleanup EXIT INT TERM

# --- repo buangan ---
(
  cd "$SB" || exit 1
  git init -q . || exit 1
  printf 'logs/\n' > .gitignore      # jika tidak, pengawal fail-terlarang menembak log sendiri
  git add -A >/dev/null 2>&1
  git -c user.email=t@t -c user.name=t commit -qm asas >/dev/null 2>&1
) || { echo "RALAT: gagal menyediakan repo buangan" >&2; exit 1; }
BASE="$(git -C "$SB" rev-parse HEAD)"

# --- kunci palsu: dibina runtime, tiada corak lengkap dalam fail ini ---
PFX_SK='sk-'
PFX_GHP='ghp_'
PFX_PAT='github_pat_'
PFX_GCP='AIza'
PFX_AWS='AKIA'
PFX_XOX='xoxb-'
PFX_JWT='eyJ'
PJG='abcdefghijklmnopqrstuvwxyz123456'
HURUF='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
AWS_BODY='IOSFODNN7'
AWS_EX='EXAMPLE'
HDR_A='-----BEGIN RSA PRIVATE'
HDR_B=' KEY-----'

KUNCI_SK="${PFX_SK}${PJG}"
KUNCI_GHP="${PFX_GHP}${PJG}"
KUNCI_PAT="${PFX_PAT}${PJG}_${PJG}"
KUNCI_GCP="${PFX_GCP}${PJG}${HURUF:0:8}"
KUNCI_AWS="${PFX_AWS}${AWS_BODY}${HURUF:0:7}"
KUNCI_AWS_EX="${PFX_AWS}${AWS_BODY}${AWS_EX}"
KUNCI_XOX="${PFX_XOX}${PJG}"
KUNCI_JWT="${PFX_JWT}${PJG:0:12}.${PJG:0:12}.${PJG:0:12}"
HDR="${HDR_A}${HDR_B}"
# nilai ujian peringkat 2 juga melalui pemboleh ubah: baris sumber mengandungi ${...}
# sahaja, jadi penapis REAL_VALUE mengabaikannya dan fail ini tidak menghalang dirinya.
N1='Qz7TmLp2RvXk9Wn4'
N2='Kp9Xm2Qr7Tz4Wn8B'
N3='Rk4Wm9Zt2Lp7Xq1B'
N4='Zx8Nv3Qm5Rt1Lp7W'

lulus=0; gagal=0
kes() { # <nama> <fail> <kandungan> <jangkaan>
  local nama="$1" f="$2" isi="$3" jang="$4" got s
  mkdir -p "$SB/$(dirname "$f")"
  printf '%s\n' "$isi" > "$SB/$f"
  ( cd "$REPO" && HERMES_HOME="$SB" bash "$GUARD" ) >/dev/null 2>&1
  got=$?
  git -C "$SB" reset -q --hard "$BASE" >/dev/null 2>&1
  git -C "$SB" clean -qfd >/dev/null 2>&1
  if [ "$got" = "$jang" ]; then s="LULUS"; lulus=$((lulus+1)); else s="GAGAL"; gagal=$((gagal+1)); fi
  printf '%-6s jangka=%s dapat=%s  %-16s %s\n' "$s" "$jang" "$got" "$nama" "$f"
}

echo "== PERINGKAT 1 (mesti 3) =="
kes sk-            a.txt        "$KUNCI_SK"      3
kes ghp_           b.txt        "$KUNCI_GHP"     3
kes github_pat_    c.txt        "$KUNCI_PAT"     3
kes AIza           d.txt        "$KUNCI_GCP"     3
kes AKIA-sebenar   e.txt        "$KUNCI_AWS"     3
kes xoxb-          f.txt        "$KUNCI_XOX"     3
kes PRIVATE-KEY    g.txt        "$HDR"           3
kes JWT            h.txt        "$KUNCI_JWT"     3
kes sk-dlm-md      i.md         "$KUNCI_SK"      3
kes ghp-dlm-docs   docs/j.txt   "$KUNCI_GHP"     3

echo "== AKIA EXAMPLE + penapis peringkat 2 (mesti 0) =="
kes AKIA-EXAMPLE   k.txt        "$KUNCI_AWS_EX"                 0
kes sudut          l.conf       'api_key=<token-anda-di-sini>'  0
kes dollar-ku      m.conf       'password=${DB_PASSWORD_KU}'     0
kes bintang        n.conf       'secret=****************'        0
kes REDACTED       o.conf       'token=REDACTED-BY-SCRUBBER'     0
kes pendek         p.conf       'passwd=abc123'                  0
kes YOUR_          q.conf       'api_key=YOUR_KEY_HERE_1234'     0
kes contoh         r.conf       'client_secret=contoh-nilai-rahsia' 0
kes example        s.env        'app_password=example-value-123' 0
kes doc-md         t.md         "password=${N1}"               0
kes doc-refs       references/u.md "token=${N1}"               0

echo "== tugasan nilai sebenar (mesti 3) =="
kes conf           v.conf       "db_password=${N1}"                  3
kes petikan        w.yaml       "  app_password: ${N2}"              3
kes json           x.json       "{\"client_secret\": \"${N3}\"}"      3
kes skrip          y.sh         "export API_KEY=${N4}"               3

echo "----------------------------------------"
printf 'LULUS=%s GAGAL=%s\n' "$lulus" "$gagal"
[ "$gagal" -eq 0 ] || exit 1
