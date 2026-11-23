#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  termux-health-check.sh — SEMAKAN KESIHATAN TERMUX + HERMES (baca sahaja)
#  Pasang: cp ke ~/bin/sihat && chmod +x ~/bin/sihat   (guna: sihat)
#  Lapor: wake-lock, pokok runit, proses, zombie, konsol, gerbang, RAM
#  Semua baris mesti [OK] sebelum melaporkan "sihat" kepada pengguna.
# ============================================================
export HOME=/data/data/com.termux/files/home
export PATH=/data/data/com.termux/files/usr/bin:$PATH
FLAG="$HOME/.hermes20/wake_lock.enabled"
ok()  { printf '  [OK]   %s\n' "$1"; }
bad() { printf '  [GAGAL] %s\n' "$1"; }

echo "== SEMAKAN $(date '+%Y-%m-%d %H:%M:%S') =="

# 1) wake-lock — acquire SEKALI di sini pun boleh; ia tool idempoten tetapi
#    setiap panggilan memaparkan semula notifikasi, jadi jangan panggil dalam gelung.
if [ -f "$FLAG" ]; then
  termux-wake-lock >/dev/null 2>&1
  ok "wake-lock: auto ON — semak notifikasi 'Termux wake lock held'"
else
  bad "wake-lock: auto OFF (tiada $FLAG)"
fi

# 2) pokok runit — mesti SATU runsvdir, tiada runsv yatim.
#    JANGAN guna pgrep -x (comm=linker64) atau pgrep -f (positif palsu pada shell sendiri).
nd=0; ny=0
for p in /proc/[0-9]*; do
  e=$(readlink "$p/exe" 2>/dev/null)
  case "$e" in
    */bin/runsvdir) nd=$((nd+1)) ;;
    */bin/runsv)    [ "$(awk '{print $4}' "$p/stat" 2>/dev/null)" = "1" ] && ny=$((ny+1)) ;;
  esac
done
[ "$nd" = "1" ] && ok "runsvdir: 1 pokok" || bad "runsvdir: $nd pokok (patut 1)"
[ "$ny" = "0" ] && ok "runsv yatim: 0" || bad "runsv yatim: $ny (pokok lama tertinggal)"

# 3) servis teras
for s in hermes-console hermes-gateway hermes-keeper sshd; do
  if sv status "$s" 2>/dev/null | grep -q '^run:'; then ok "servis $s: run"; else bad "servis $s: BUKAN run"; fi
done

# 4) proses & zombie (had 'phantom process' Android ~32)
np=$(ls /proc 2>/dev/null | grep -c '^[0-9]')
nz=$(ps -e -o stat 2>/dev/null | grep -c '^Z')
[ "$np" -lt 30 ] && ok "proses: $np (bawah had 32)" || bad "proses: $np (hampir/lebih had 32 phantom)"
[ "$nz" -le 2 ] && ok "zombie: $nz" || bad "zombie: $nz"

# 5) konsol + gerbang
code=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8787/ 2>/dev/null)
[ "$code" = "200" ] && ok "konsol 8787: HTTP 200" || bad "konsol 8787: HTTP $code"
if pgrep -f "gateway run" >/dev/null 2>&1; then ok "gerbang Telegram: proses hidup"; else bad "gerbang Telegram: proses TIADA"; fi

# 6) RAM
av=$(awk '/MemAvailable/{printf "%d", $2/1024}' /proc/meminfo)
sw=$(awk '/SwapFree/{printf "%d", $2/1024}' /proc/meminfo)
[ "$av" -gt 800 ] && ok "RAM tersedia: ${av} MB" || bad "RAM tersedia: ${av} MB (sesak — Android boleh bunuh app)"
echo "  swap bebas: ${sw} MB"
echo "== TAMAT =="
