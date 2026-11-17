#!/data/data/com.termux/files/usr/bin/bash
# uim_pdf.sh — Markdown -> PDF -> gudang telefon (satu arahan).
# Saluran: $HOME/*.md  --md_to_pdf-->  $HOME/.hermes20/tmp/*.pdf  --uim_hantar-->  /sdcard/Documents/UIM/01-LAPORAN/
# Tiada dua hala. Tiada symlink. Fail sementara dipadam selepas hantar.
#
# Guna:
#   uim_pdf.sh <fail.md> [--nama NAMA.pdf]
# Contoh:
#   uim_pdf.sh ~/.hermes20/docs/STORAN-UIM.md
#   uim_pdf.sh ~/.hermes20/docs/KETUA.md --nama UJIAN-KETUA.pdf
set -u -o pipefail

SKRIP="$(cd "$(dirname "$0")" && pwd -P)"
MD2PDF="$SKRIP/md_to_pdf.py"
HANTAR="$SKRIP/uim_hantar.sh"
TMPDIR_UIM="$HOME/.hermes20/tmp"
KATEGORI="01-LAPORAN"
AKAR="/sdcard/Documents/UIM"

gagal() { echo "GAGAL: $*" >&2; exit "${2:-1}"; }

[ $# -ge 1 ] || gagal "guna: uim_pdf.sh <fail.md> [--nama NAMA.pdf]" 64

SUMBER=""
NAMA=""
while [ $# -gt 0 ]; do
  case "$1" in
    --nama) NAMA="${2:-}"; [ -n "$NAMA" ] || gagal "--nama perlukan nilai" 64; shift 2 ;;
    -h|--help) echo "guna: uim_pdf.sh <fail.md> [--nama NAMA.pdf]"; exit 0 ;;
    *) [ -z "$SUMBER" ] || gagal "hanya satu fail input dibenarkan: '$1'" 64
       SUMBER="$1"; shift ;;
  esac
done

[ -n "$SUMBER" ] || gagal "tiada fail input diberi" 64
[ -e "$SUMBER" ] || gagal "input tidak wujud: $SUMBER" 2
[ -f "$SUMBER" ] || gagal "input bukan fail biasa: $SUMBER" 2
[ -L "$SUMBER" ] && gagal "input ialah SYMLINK ($SUMBER) — peraturan: tiada symlink." 3

SEBENAR="$(realpath "$SUMBER")" || gagal "tak boleh resolusi laluan input: $SUMBER" 3
case "$SEBENAR" in
  "$HOME"/*) : ;;
  *) gagal "input di luar \$HOME ($SEBENAR). Kilang hanya \$HOME." 3 ;;
esac

[ -f "$MD2PDF" ] || gagal "penukar hilang: $MD2PDF" 5
[ -x "$HANTAR" ] || [ -f "$HANTAR" ] || gagal "skrip hantar hilang: $HANTAR" 5

mkdir -p "$TMPDIR_UIM" || gagal "tak boleh cipta tmp: $TMPDIR_UIM" 5

ASAS="$(basename "$SEBENAR")"
ASAS="${ASAS%.*}"
[ -n "$ASAS" ] || ASAS="dokumen"
PDF_TMP="$TMPDIR_UIM/${ASAS}.pdf"

bersih() { rm -f -- "$PDF_TMP" 2>/dev/null || true; }
trap bersih EXIT INT TERM

echo "MD   : $SEBENAR"
echo "JANA : $PDF_TMP"

# (b) jana PDF di dalam $HOME
ERRMSG="$(python3 "$MD2PDF" "$SEBENAR" "$PDF_TMP" 2>&1 >/dev/null)"
RC=$?
if [ "$RC" -ne 0 ]; then
  ralat="$(printf '%s' "$ERRMSG" | tail -n 3 | tr '\n' ' ')"
  bersih
  gagal "penjanaan PDF gagal: ${ralat:-tiada butiran}" 6
fi

[ -s "$PDF_TMP" ] || { bersih; gagal "PDF kosong (0 bait) — penjanaan gagal" 6; }
SAIZ_TMP="$(stat -c %s "$PDF_TMP")"

# (c) hantar ke gudang melalui kaunter sedia ada
ARGS=("$PDF_TMP" --ke "$KATEGORI")
[ -n "$NAMA" ] && ARGS+=(--nama "$NAMA")

OUT="$(bash "$HANTAR" "${ARGS[@]}" 2>&1)"
RC=$?
if [ "$RC" -ne 0 ]; then
  printf '%s\n' "$OUT" >&2
  bersih
  gagal "uim_hantar gagal (kod $RC)" "$RC"
fi

DEST="$(printf '%s\n' "$OUT" | sed -n 's/^SIAP: //p' | head -n1)"
[ -n "$DEST" ] || { printf '%s\n' "$OUT" >&2; bersih; gagal "tak jumpa laluan gudang dalam output uim_hantar" 7; }
[ -f "$DEST" ] || { bersih; gagal "fail tiada di gudang selepas hantar: $DEST" 7; }

SAIZ_DEST="$(stat -c %s "$DEST")"
H1="$(sha256sum "$PDF_TMP" | cut -d' ' -f1)"
H2="$(sha256sum "$DEST" | cut -d' ' -f1)"
if [ "$H1" != "$H2" ]; then
  bersih
  gagal "sha256 PDF tak sama di gudang — salinan tidak dipercayai" 8
fi

# (d) padam fail sementara
bersih
trap - EXIT INT TERM

echo "GUDANG: $DEST"
echo "  saiz   : $SAIZ_DEST bait"
echo "  sha256 : ${H1:0:16}…  (disahkan dua hala)"
echo "  sumber : $(du -h --apparent-size "$SEBENAR" 2>/dev/null | cut -f1) markdown -> PDF"
echo "SIAP-PDF: $DEST"
exit 0
