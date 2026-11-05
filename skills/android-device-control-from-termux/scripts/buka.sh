#!/data/data/com.termux/files/usr/bin/bash
# buka — lancar app / URL / carian Play Store dari terminal Termux.
#
#   buka fdroid | buka com.whatsapp      # alias atau nama pakej
#   buka url https://f-droid.org
#   buka play "kalkulator"               # carian Play Store
#   buka apk /storage/emulated/0/Download/x.apk   # buka FOLDER dalam app Files
#   buka --list [corak] | --aliases | --component <pkg>
#
# Pasang: cp scripts/buka.sh $PREFIX/bin/buka && chmod +x $PREFIX/bin/buka
set -u

CACHE_DIR="$HOME/.cache/buka"
CACHE="$CACHE_DIR/components.tsv"
mkdir -p "$CACHE_DIR"

declare -A ALIAS=(
  [fdroid]="org.fdroid.fdroid" [play]="com.android.vending" [termux]="com.termux"
  [wa]="com.whatsapp" [whatsapp]="com.whatsapp"
  [tg]="org.telegram.messenger" [telegram]="org.telegram.messenger"
  [kamera]="com.android.camera" [camera]="com.android.camera"
  [galeri]="com.miui.gallery" [gallery]="com.miui.gallery"
  [seting]="com.android.settings" [settings]="com.android.settings"
  [nota]="com.miui.notes" [notes]="com.miui.notes"
  [fail]="com.mi.android.globalFileexplorer" [files]="com.mi.android.globalFileexplorer"
  [explorer]="com.mi.android.globalFileexplorer"
  [claude]="com.anthropic.claude" [grok]="ai.x.grok"
)

# aapt gagal bagi sesetengah app sistem — komponen yang diketahui
declare -A KNOWN=(
  [com.android.settings]="com.android.settings/.Settings"
  [com.android.vending]="com.android.vending/com.google.android.finsky.activities.MainActivity"
  [org.fdroid.fdroid]="org.fdroid.fdroid/.views.main.MainActivity"
)

usage() { sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

component_of() {
  local pkg="$1" comp=""
  comp=$(grep -m1 -P "^$pkg\t" "$CACHE" 2>/dev/null | cut -f2)
  [ -n "$comp" ] && { echo "$comp"; return 0; }

  if [ -n "${KNOWN[$pkg]:-}" ]; then
    printf '%s\t%s\n' "$pkg" "${KNOWN[$pkg]}" >> "$CACHE"
    echo "${KNOWN[$pkg]}"; return 0
  fi

  local apk
  apk=$(pm path "$pkg" 2>/dev/null | head -1 | sed 's/^package://')
  [ -n "$apk" ] && [ -r "$apk" ] || return 1
  comp=$(aapt dump badging "$apk" 2>/dev/null \
    | sed -n "s/^launchable-activity: name='\([^']*\)'.*/\1/p" | head -1)
  [ -n "$comp" ] || return 1
  case "$comp" in
    */*) : ;;
    *) comp="$pkg/$comp" ;;
  esac
  printf '%s\t%s\n' "$pkg" "$comp" >> "$CACHE"
  echo "$comp"
}

[ $# -eq 0 ] && usage 1

case "$1" in
  -h|--help) usage 0 ;;
  --aliases) for k in "${!ALIAS[@]}"; do printf "%-12s %s\n" "$k" "${ALIAS[$k]}"; done | sort; exit 0 ;;
  --list)
    if [ -n "${2:-}" ]; then pm list packages 2>/dev/null | sed 's/^package://' | grep -i -- "$2" | sort
    else pm list packages 2>/dev/null | sed 's/^package://' | sort; fi
    exit 0 ;;
  --component)
    p="${2:-}"; [ -n "$p" ] || exit 1
    c=$(component_of "$p") && echo "$c" || { echo "tidak dapat kesan activity: $p"; exit 4; }
    exit 0 ;;
  url)
    [ $# -ge 2 ] || { echo "guna: buka url <https://…>"; exit 1; }
    am start -a android.intent.action.VIEW -d "$2" >/dev/null 2>&1 \
      && echo "dibuka: $2" || { echo "gagal buka URL"; exit 1; }
    exit 0 ;;
  play)
    [ $# -ge 2 ] || { echo "guna: buka play <kata carian>"; exit 1; }
    am start -a android.intent.action.VIEW \
      -d "market://search?q=$(printf '%s' "$2" | sed 's/ /%20/g')" >/dev/null 2>&1 \
      && echo "carian Play Store: $2" || { echo "gagal buka Play Store"; exit 1; }
    exit 0 ;;
  apk)
    [ $# -ge 2 ] || { echo "guna: buka apk <laluan-fail.apk>"; exit 1; }
    f="$2"; [ -f "$f" ] || { echo "fail tidak wujud: $f"; exit 1; }
    d=$(cd "$(dirname "$f")" && pwd)
    case "$d" in
      "$HOME"/storage/*) rel=${d#"$HOME"/storage/} ;;
      /storage/emulated/0/*) rel=${d#/storage/emulated/0/} ;;
      /sdcard/*) rel=${d#/sdcard/} ;;
      *) rel="$d" ;;
    esac
    rel=${rel%/}
    am start -a android.intent.action.VIEW \
      -d "content://com.android.externalstorage.documents/document/primary%3A$(printf '%s' "$rel" | sed 's|/|%2F|g')" \
      -t "vnd.android.document/directory" >/dev/null 2>&1
    echo "Folder dibuka dalam app Files: $rel"
    echo "Tekan fail: $(basename "$f") → Install"
    echo "Nota: Termux tiada REQUEST_INSTALL_PACKAGES — pemasangan mesti dari app Files/ADB."
    exit 0 ;;
esac

pkg="${ALIAS[$1]:-$1}"
if ! pm list packages 2>/dev/null | grep -qx "package:$pkg"; then
  echo "tidak dipasang/kelihatan: $pkg"; echo "cari: buka --list <corak>"; exit 2
fi

comp=$(component_of "$pkg") || { echo "tidak dapat kesan activity pelancar: $pkg"; exit 4; }
out=$(am start -n "$comp" 2>&1)
if printf '%s' "$out" | grep -qiE "error:|exception|unable to resolve"; then
  echo "gagal: $out"; exit 3
fi
echo "dibuka: $pkg · $comp"
