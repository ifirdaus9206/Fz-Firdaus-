#!/data/data/com.termux/files/usr/bin/bash
# Penjaga ruang storan — senyap kalau cukup, lapor bila hampir penuh.
# Ambang: <15GB = AWAS, <8GB = KRITIKAL. Diarah oleh firdaus 2026-11-12.
set -u
WARN_GB=15
CRIT_GB=8

free_kb=$(df -k /data/data/com.termux/files/home 2>/dev/null | awk 'NR==2{print $4}')
free_gb=$(( ${free_kb:-0} / 1048576 ))
home=$(du -sh /data/data/com.termux/files/home 2>/dev/null | awk '{print $1}')

if [ "$free_gb" -ge "$WARN_GB" ]; then
  exit 0   # cukup ruang, senyap
fi

top=$(du -sh /data/data/com.termux/files/home/.hermes20/archive \
             /data/data/com.termux/files/home/.hermes20/tools \
             /data/data/com.termux/files/home/.hermes20/legacy-ultimate \
             /data/data/com.termux/files/home/.cargo \
             /data/data/com.termux/files/home/.local \
             /data/data/com.termux/files/home/.cache 2>/dev/null | sort -hr | head -4)

if [ "$free_gb" -lt "$CRIT_GB" ]; then
  tahap="KRITIKAL"
else
  tahap="AWAS"
fi

echo "RUANG TERMUX $tahap — tinggal ${free_gb} GB kosong"
echo "Termux home: ${home:-?}"
echo ""
echo "Pemakan terbesar:"
echo "$top"
echo ""
echo "Cadangan: buang .hermes20/archive/ultimate-2026-10 + code-server-2026-10 + .cache (~8.9 GB)."
