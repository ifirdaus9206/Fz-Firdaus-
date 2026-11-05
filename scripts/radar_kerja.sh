#!/data/data/com.termux/files/usr/bin/bash
# Wrapper cron: jalankan freelance-radar scan.py
# (cron hanya terima skrip di bawah ~/.hermes20/scripts/)
set -u
DIR="/data/data/com.termux/files/home/freelance-radar"
cd "$DIR" || { echo "RADAR: folder $DIR tidak dijumpai"; exit 1; }
exec python3 "$DIR/scripts/scan.py"
