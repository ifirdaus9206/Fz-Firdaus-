#!/data/data/com.termux/files/usr/bin/bash
# HERMES CONSOLE — mula SATU instance sahaja.
#   8787 = hermes20 (Ketua / Agent Factory)
#   8790 = hermes19 (Trading Desk) — DIBERSARAKAN 2026-11-24, hermes19 sudah dipadam.
# Selamat dijalankan berulang kali: yang sudah hidup dilangkau.
set -u
HOME_DIR="$HOME"

ping_ok() { curl -s -m 3 -o /dev/null "http://127.0.0.1:$1/api/ping"; }

start20() {
  if ping_ok 8787; then echo "8787 sudah hidup"; return 0; fi
  cd "$HOME_DIR/hermes-console" || return 1
  rm -f server.pid
  setsid ./run.sh >> server.log 2>&1 < /dev/null &
  echo "8787 dimulakan (pid $!)"
}

/data/data/com.termux/files/home/hermes-console/tools/wake_ctl.sh auto 2>/dev/null || true

start20

# tunggu sampai siap (maks 20s)
for i in $(seq 1 20); do
  ping_ok 8787 && break
  sleep 1
done

echo "--- status ---"
ping_ok 8787 && echo "8787 HIDUP  http://127.0.0.1:8787/" || echo "8787 MATI"
