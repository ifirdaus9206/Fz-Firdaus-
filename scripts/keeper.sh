#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# keeper.sh — PENJAGA HIDUP HERMES (gateway Telegram + konsol)
# Setiap 60s: pastikan wake-lock dipegang, servis runit hidup,
# dan konsol menjawab. Hanya tulis log bila ia bertindak.
# ============================================================
export HOME=/data/data/com.termux/files/home
export PATH=/data/data/com.termux/files/usr/bin:$HOME/.local/bin:$PATH
LOG="$HOME/.hermes20/logs/keeper.log"
FLAG="$HOME/.hermes20/wake_lock.enabled"
HELD="$HOME/.hermes20/.wake_held"
say() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >>"$LOG"; }

fails=0
while true; do
  # 1) wake-lock — Android tak benarkan CPU tidur, proses tak dibunuh
  #    PENTING: panggil SEKALI sahaja. Setiap panggilan termux-wake-lock
  #    menyebabkan Android MEMAPARKAN SEMULA notifikasi "N sessions (wake lock
  #    held)" — panggilan setiap 60s = ribut notifikasi yang dikeluhkan bos.
  #    Lock dipegang oleh proses app Termux; kalau app mati, keeper pun mati,
  #    jadi tidak perlu acquire semula setiap kitaran.
  if [ -f "$FLAG" ] && [ ! -f "$HELD" ]; then
    termux-wake-lock >/dev/null 2>&1 || true
    touch "$HELD" 2>/dev/null || true
    say "wake-lock: dipegang SEKALI (bukan setiap kitaran)"
  fi

  # 1b) SUPERVISOR TUNGGAL: hanya satu runsvdir dibenarkan.
  #     runsv yatim (PPID 1) = pokok lama yang tertinggal selepas runsvdir mati.
  #     Ia bergaduh dengan runsvdir baharu (konsol/gerbang berganda, app.py yatim).
  #     NOTA: pgrep -x TIDAK boleh dipakai (binari Termux jalan melalui linker64,
  #     comm="linker64"), dan pgrep -f pula menangkap shell yang cuma MENYEBUT
  #     corak itu. Kesan melalui /proc/PID/exe — tepat, tiada positif palsu.
  for p in /proc/[0-9]*; do
    [ "$(readlink "$p/exe" 2>/dev/null)" = "$PREFIX/bin/runsv" ] || continue
    pp=$(awk '{print $4}' "$p/stat" 2>/dev/null)
    if [ "$pp" = "1" ]; then
      kill "${p#/proc/}" 2>/dev/null && say "BUNUH runsv yatim pid=${p#/proc/} (pokok lama)"
    fi
  done
  nd=0
  for p in /proc/[0-9]*; do
    [ "$(readlink "$p/exe" 2>/dev/null)" = "$PREFIX/bin/runsvdir" ] && nd=$((nd+1))
  done
  [ "$nd" -gt 1 ] && say "AMARAN: $nd runsvdir hidup (patut 1)"

  # 1c) HAD PROSES: Android membunuh app bila anak proses > 32.
  #     Ambang 30 + mesti 2 kitaran berturut (kiraan termasuk shell sementara
  #     daripada panggilan agent, jadi sekali-sekala naik ke 29-30 tanpa bahaya).
  np=$(ls /proc 2>/dev/null | grep -c '^[0-9]')
  pv=$(cat "$HOME/.hermes20/.proc_prev" 2>/dev/null); pv=${pv:-0}
  printf '%s' "$np" > "$HOME/.hermes20/.proc_prev"
  if [ "${np:-0}" -gt 30 ] && [ "${pv:-0}" -gt 30 ]; then
    now_h=$(date '+%Y-%m-%d %H')
    if [ "$(cat "$HOME/.hermes20/.proc_warn_hour" 2>/dev/null)" != "$now_h" ]; then
      say "AMARAN: proses $np (>30 dua kitaran, had android 32) — servis tak terpakai patut dipindah keluar"
      printf '%s' "$now_h" > "$HOME/.hermes20/.proc_warn_hour"
    fi
  fi

  # 2) servis runit mesti 'run'; kalau tidak, naikkan
  for svc in hermes-gateway hermes-console; do
    if ! sv status "$svc" 2>/dev/null | grep -q '^run:'; then
      sv up "$svc" >/dev/null 2>&1 || true
      say "NAIK $svc (status bukan run)"
    fi
  done

  # 2b) KONSOL: pastikan HANYA satu app.py, dan ia anak runsv.
  #     Proses yatim (PPID 1) memegang port 8787 → anak runit gagal bind
  #     dan berulang-alik setiap ~1s (crash-loop). Bunuh yang yatim.
  rpid=$(pgrep -f "runsv hermes-console" 2>/dev/null | head -1)
  for p in $(pgrep -f "python3 -u app.py" 2>/dev/null); do
    c=$(tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null)
    case "$c" in
      *bash*|*"sh -c"*|*pgrep*|*grep*|*source*) continue ;;   # shell/alat, bukan pelayan
    esac
    case "$c" in
      *"python3 -u app.py"*) : ;;
      *) continue ;;
    esac
    ppid=$(awk '{print $4}' "/proc/$p/stat" 2>/dev/null)
    if [ -n "$rpid" ] && [ -n "$ppid" ] && [ "$ppid" != "$rpid" ]; then
      kill "$p" 2>/dev/null && say "BUNUH app.py yatim pid=$p (ppid=$ppid, runsv=$rpid)"
    fi
  done

  # 3) konsol mesti jawab HTTP; 3 kali gagal berturut → restart
  code=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8787/ 2>/dev/null)
  if [ "$code" = "200" ]; then
    fails=0
  else
    fails=$((fails+1))
    say "konsol tidak jawab ($code) cubaan $fails"
    if [ "$fails" -ge 3 ]; then
      sv restart hermes-console >/dev/null 2>&1 || true
      say "RESTART hermes-console kerana tidak jawab"
      fails=0
    fi
  fi

  # 4) gerbang Telegram: proses mesti ada
  if ! pgrep -f "hermes gateway run" >/dev/null 2>&1; then
    sv up hermes-gateway >/dev/null 2>&1 || true
    say "NAIK hermes-gateway (proses tiada)"
  fi

  sleep 60
done
