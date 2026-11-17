#!/data/data/com.termux/files/usr/bin/bash
# uim_hantar.sh — kaunter hantar SEHALA: Termux (kilang) -> telefon (gudang)
# Peraturan: sumber MESTI fail sebenar di dalam $HOME. Tiada symlink. Tiada dua hala.
# Salinan disahkan sha256; kalau tak sama, salinan telefon DIPADAM dan arahan gagal.
#
# Guna:
#   uim_hantar.sh <fail|folder> [--ke KATEGORI] [--ganti] [--nama NAMA]
# Contoh:
#   uim_hantar.sh ~/.hermes20/docs/LAPORAN-VAULT.md
#   uim_hantar.sh /tmp/laporan.pdf --ke 01-LAPORAN --nama LAPORAN-HARIAN-1211.pdf
#   uim_hantar.sh ~/gambar.png --ganti
set -u -o pipefail

AKAR="/sdcard/Documents/UIM"
LOG="$HOME/.hermes20/logs/uim_hantar.log"
mkdir -p "$(dirname "$LOG")"

bunuh() { echo "GAGAL: $*" >&2; exit "${2:-1}"; }

[ $# -ge 1 ] || bunuh "guna: uim_hantar.sh <fail|folder> [--ke KATEGORI] [--ganti] [--nama NAMA]" 64

SUMBER=""
KATEGORI=""
GANTI=0
NAMA=""

while [ $# -gt 0 ]; do
  case "$1" in
    --ke)    KATEGORI="${2:-}"; shift 2 ;;
    --ganti) GANTI=1; shift ;;
    --nama)  NAMA="${2:-}"; shift 2 ;;
    -h|--help) echo "guna: uim_hantar.sh <fail|folder> [--ke KATEGORI] [--ganti] [--nama NAMA]"; exit 0 ;;
    *) [ -z "$SUMBER" ] || bunuh "hanya satu sumber dibenarkan: '$1'" 64; SUMBER="$1"; shift ;;
  esac
done

[ -n "$SUMBER" ] || bunuh "tiada sumber diberi" 64
[ -e "$SUMBER" ] || bunuh "sumber tidak wujud: $SUMBER" 2
[ -L "$SUMBER" ] && bunuh "sumber ialah SYMLINK ($SUMBER). Peraturan: tiada symlink untuk benda penting. Salin fail sebenar dahulu." 3

AKAR_SEBENAR="$(cd "$AKAR" && pwd -P)"
SUMBER_SEBENAR="$(realpath "$SUMBER")"
case "$SUMBER_SEBENAR" in
  "$AKAR_SEBENAR"*) bunuh "sumber sudah berada di storan telefon. Aliran hanya Termux -> telefon." 3 ;;
esac
case "$SUMBER_SEBENAR" in
  "$HOME"/*) : ;;
  *) bunuh "sumber di luar \$HOME ($SUMBER_SEBENAR). Kilang hanya \$HOME. Guna --ke hanya untuk fail dalam \$HOME." 3 ;;
esac

[ -n "$KATEGORI" ] || {
  ext="${SUMBER_SEBENAR##*.}"; ext="$(echo "$ext" | tr 'A-Z' 'a-z')"
  case "$ext" in
    pdf|md|txt|csv|json|docx|xlsx|pptx|html) KATEGORI="01-LAPORAN" ;;
    png|jpg|jpeg|webp|svg|bmp)               KATEGORI="02-GAMBAR" ;;
    mp3|ogg|wav|m4a|opus|flac)               KATEGORI="03-AUDIO" ;;
    mp4|mkv|webm|mov|gif)                    KATEGORI="04-VIDEO" ;;
    *)                                       KATEGORI="05-HANTAR" ;;
  esac
}

case "$KATEGORI" in
  01-LAPORAN|02-GAMBAR|03-AUDIO|04-VIDEO|05-HANTAR) : ;;
  *) bunuh "kategori tidak sah: $KATEGORI (pilih 01-LAPORAN|02-GAMBAR|03-AUDIO|04-VIDEO|05-HANTAR)" 64 ;;
esac

DEST_DIR="$AKAR/$KATEGORI"
mkdir -p "$DEST_DIR" || bunuh "tak boleh cipta folder destinasi: $DEST_DIR" 5

asas="$(basename "$SUMBER_SEBENAR")"
[ -n "$NAMA" ] && asas="$NAMA"
DEST="$DEST_DIR/$asas"

if [ -e "$DEST" ]; then
  if [ "$GANTI" -eq 1 ]; then
    rm -f "$DEST" || bunuh "tak boleh ganti: $DEST" 5
  else
    cap="$(date +%Y%m%d-%H%M%S)"
    kes="$asas"; ext2=""
    case "$asas" in *.*) ext2=".${asas##*.}"; kes="${asas%.*}" ;; esac
    DEST="$DEST_DIR/${kes}-${cap}${ext2}"
    echo "NOTA: nama sudah ada, disimpan sebagai $(basename "$DEST") (guna --ganti untuk menimpa)"
  fi
fi

if [ -d "$SUMBER_SEBENAR" ]; then
  mkdir -p "$DEST"
  cp -R "$SUMBER_SEBENAR/." "$DEST/" || bunuh "cp folder gagal" 5
  jumlah="$(find "$DEST" -type f | wc -l | tr -d ' ')"
  saiz="$(du -sh "$DEST" | cut -f1)"
  printf '%s | FOLDER | %s | %s | %s | %s fail\n' "$(date '+%F %T')" "$SUMBER_SEBENAR" "$DEST" "folder" "$jumlah" >> "$LOG"
  echo "SIAP (folder): $DEST"
  echo "  fail : $jumlah"
  echo "  saiz : $saiz"
  echo "HANTAR-TELEGRAM: MEDIA:$DEST"
  exit 0
fi

cp -p -- "$SUMBER_SEBENAR" "$DEST" || bunuh "cp gagal: $DEST" 5
H1="$(sha256sum "$SUMBER_SEBENAR" | cut -d' ' -f1)"
H2="$(sha256sum "$DEST" | cut -d' ' -f1)"
if [ "$H1" != "$H2" ]; then
  rm -f "$DEST"
  bunuh "sha256 tak sama — salinan telefon dipadam. cuba lagi." 6
fi
S1="$(stat -c %s "$SUMBER_SEBENAR")"
S2="$(stat -c %s "$DEST")"
[ "$S1" = "$S2" ] || { rm -f "$DEST"; bunuh "saiz tak sama ($S1 vs $S2) — dipadam." 6; }

printf '%s | %s | %s | %s | %s bait | %s\n' \
  "$(date '+%F %T')" "$SUMBER_SEBENAR" "$DEST" "${H1:0:16}" "$S2" "$KATEGORI" >> "$LOG"

echo "SIAP: $DEST"
echo "  saiz   : $S2 bait"
echo "  sha256 : ${H1:0:16}…  (disahkan dua hala)"
echo "  kategori: $KATEGORI"
echo "HANTAR-TELEGRAM: MEDIA:$DEST"
