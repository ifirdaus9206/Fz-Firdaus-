#!/data/data/com.termux/files/usr/bin/bash
# sshd-login-audit.sh — who entered this phone over SSH, from where, with which key.
# Tested on Termux (runit sshd on 8022, svlogd log).
#   sshd-login-audit.sh          # summary: 8 last logins, 8 last failures
#   sshd-login-audit.sh penuh    # 20 / 20
#   sshd-login-audit.sh kunci    # installed keys + fingerprints only
# Exit 0 always; it is a report, not a gate.

LOG="$PREFIX/var/log/sv/sshd/current"
AK="$HOME/.ssh/authorized_keys"
N=8
case "$1" in
  penuh) N=20 ;;
  kunci) N=0 ;;
esac

garis() { printf '%s\n' "------------------------------------------------------------"; }

echo "╔══════════════════════════════════════════════════════════╗"
echo "║              PAPAN MASUK SSH — $(date '+%Y-%m-%d %H:%M')             ║"
echo "╚══════════════════════════════════════════════════════════╝"

echo
echo "▶ 1. KEADAAN SSHD"
if sv status sshd 2>/dev/null | grep -q '^run:'; then
  echo "   Status   : HIDUP"
else
  echo "   Status   : MATI  → jalankan: sv up sshd"
fi
echo "   Port     : 8022 (0.0.0.0 + ::)"
echo "   Log      : $LOG"
echo "   Saiz log : $(wc -l < "$LOG" 2>/dev/null || echo 0) baris"

echo
echo "▶ 2. SESI AKTIF SEKARANG"
senarai=$(ps -ef 2>/dev/null | grep '[s]shd:' | grep -v 'listener' | grep -v 'privilege')
if [ -n "$senarai" ]; then
  printf '%s\n' "$senarai" | awk '{print "   " $0}'
else
  echo "   Tiada sesi masuk aktif (hanya listener menunggu)."
fi

echo
echo "▶ 3. LOGIN BERJAYA TERAKHIR (kunci awam)"
if [ "$N" -gt 0 ]; then
  jay=$(grep -h 'Accepted publickey' "$LOG" 2>/dev/null | tail -$N)
  if [ -n "$jay" ]; then
    # svlogd line: 2026-11-17_15:00:37.56741 Accepted publickey for <user> from <ip> port N ssh2: ...
    # tr -d '\r' first: svlogd lines carry a CR, which corrupts the last awk field.
    printf '%s\n' "$jay" | tr -d '\r' \
      | sed -E 's/^([0-9-]+)_([0-9:]+)\.[0-9]+ /\1 \2  /; s/ ssh2:.*SHA256:/  kunci=SHA256:/' \
      | awk '{printf "   %s %s  user=%-12s dari=%-16s port=%-6s %s\n", $1, $2, $6, $8, $10, $11}'
  else
    echo "   Tiada rekod login berjaya."
  fi
  echo
  echo "▶ 4. PERCUBAAN GAGAL / DITOLAK TERAKHIR (keselamatan)"
  gagal=$(grep -hE 'Connection closed by|Invalid user|Failed|Bad protocol|banner exchange' "$LOG" 2>/dev/null | tail -$N)
  if [ -n "$gagal" ]; then
    printf '%s\n' "$gagal" | tr -d '\r' | sed -E 's/^([0-9-]+)_([0-9:]+)\.[0-9]+ /\1 \2  /' | awk '{print "   " $0}'
  else
    echo "   Tiada percubaan gagal direkod."
  fi
fi

echo
echo "▶ 5. KUNCI DIBENARKAN MASUK ($AK)"
if [ -s "$AK" ]; then
  i=0
  while IFS= read -r k; do
    [ -z "$k" ] && continue
    case "$k" in \#*) continue ;; esac
    i=$((i+1))
    fp=$(printf '%s\n' "$k" | ssh-keygen -lf - 2>/dev/null | awk '{print $2}')
    nama=$(printf '%s\n' "$k" | awk '{print $NF}')
    jenis=$(printf '%s\n' "$k" | awk '{print $1}')
    echo "   $i. $nama"
    echo "      jenis=$jenis  cap jari=$fp"
    # grep -c exits 1 on zero matches, so `|| echo 0` would print "0" twice — pipe to head -1 instead.
    kali=$(grep -c "$fp" "$LOG" 2>/dev/null | head -1)
    [ -z "$kali" ] && kali=0
    echo "      digunakan dalam log: $kali kali"
  done < "$AK"
else
  echo "   TIADA kunci — sesiapa yang tahu kata laluan boleh masuk!"
fi

echo
echo "▶ 6. KESELAMATAN RINGKAS"
pub=$(sshd -T 2>/dev/null | awk '/^pubkeyauthentication/{print $2}')
pw=$(sshd -T 2>/dev/null | awk '/^passwordauthentication/{print $2}')
echo "   PubkeyAuthentication   : $pub"
echo "   PasswordAuthentication : $pw"
[ "$pw" = "yes" ] && echo "   ⚠ Kata laluan masih diterima — sesiapa di WiFi sama boleh cuba teka."
[ "$pub" = "yes" ] && echo "   ✔ Log masuk guna kunci dibenarkan."

garis
echo "Selesai. Untuk senarai lebih panjang: $(basename "$0") penuh"
