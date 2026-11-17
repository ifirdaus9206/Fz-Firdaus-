#!/data/data/com.termux/files/usr/bin/bash
# uim_semak.sh — audit peraturan storan: Termux = kilang, /sdcard/Documents/UIM = gudang sehala
# Keluar senyap (exit 0, tiada output) bila semua betul — sesuai untuk cron watchdog.
# Keluar output + exit 1 bila ada langgaran.
set -u

AKAR="/sdcard/Documents/UIM"
MASALAH=0
LAPOR=""

tambah() { LAPOR="${LAPOR}$1
"; MASALAH=$((MASALAH+1)); }

# 1. Tiada symlink di dalam $HOME yang menunjuk ke storan telefon
# Dikecualikan: ~/storage (dibuat termux-setup-storage) dan ~/phone — bukan hasil kerja.
while IFS= read -r p; do
  case "$p" in
    "$HOME/storage"|"$HOME/storage/"*|"$HOME/phone") continue ;;
  esac
  [ -n "$p" ] && tambah "SYMLINK TERLARANG: $p -> $(readlink "$p")"
done < <(find "$HOME" -maxdepth 6 -type l 2>/dev/null | while read -r l; do
           t="$(readlink -f "$l" 2>/dev/null || true)"
           case "$t" in /sdcard/*|/storage/emulated/*) echo "$l" ;; esac
         done)

# 2. Tiada symlink dalam gudang yang menunjuk balik ke kilang
if [ -d "$AKAR" ]; then
  while IFS= read -r p; do
    [ -n "$p" ] && tambah "SYMLINK BALIK KE KILANG: $p -> $(readlink "$p")"
  done < <(find "$AKAR" -maxdepth 3 -type l 2>/dev/null | while read -r l; do
             t="$(readlink -f "$l" 2>/dev/null || true)"
             case "$t" in "$HOME"/*) echo "$l" ;; esac
           done)
fi

# 3. Fail kerja (.env, kunci, config) tidak boleh ada di storan telefon
if [ -d "$AKAR" ]; then
  while IFS= read -r p; do
    [ -n "$p" ] && tambah "FAIL SULIT DI TELEFON: $p"
  done < <(find "$AKAR" -maxdepth 4 -type f \( -name '.env*' -o -name 'id_rsa*' -o -name 'id_ed25519*' -o -name '*token*' -o -name 'auth.json' -o -name 'config.yaml' \) 2>/dev/null)
fi

if [ "$MASALAH" -gt 0 ]; then
  echo "AUDIT STORAN UIM — $MASALAH langgaran"
  printf '%s' "$LAPOR"
  echo "Betulkan: padam symlink / pindahkan fail sulit balik ke \$HOME."
  exit 1
fi
exit 0
