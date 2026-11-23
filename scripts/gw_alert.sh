#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  gw_alert.sh — AMARAN TELEGRAM BILA GERBANG MATI / MATI TIDAK BERSIH
#  Dipanggil cron no_agent setiap 5 minit.
#  SENYAP bila sihat (stdout kosong = tiada mesej dihantar).
#  Bertindak: cuba `sv restart hermes-gateway`, kemudian lapor hasil.
#
#  Ujian: GW_ALERT_ROOT=<dir> GW_ALERT_NO_ACTION=1 bash gw_alert.sh
# ============================================================
export HOME=/data/data/com.termux/files/home
export PATH=/data/data/com.termux/files/usr/bin:$PATH
ROOT="${GW_ALERT_ROOT:-$HOME/.hermes20}"
LIFE="$ROOT/state/gateway.lifecycle.json"
HB="$ROOT/state/gateway.heartbeat"
GLOG="$ROOT/logs/gateway.log"
STAMP="$ROOT/.gw_alert_stamp"
OFF="$ROOT/.gw_alert_unclean_off"
SVC="hermes-gateway"
SERVICE_LOG="$ROOT/logs/gw_alert.log"
say() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$SERVICE_LOG"; }

# --- 1. baca nadi & lifecycle ---
read -r PHASE PID HBAGE HBTS <<EOF
$(python3 - "$LIFE" "$HB" <<'PY'
import json, sys, time, os
life, hb = sys.argv[1], sys.argv[2]
phase, pid, age, hbts = "tiada-fail", "", 999999, 0
try:
    d = json.load(open(life)); phase = d.get("phase", "?"); pid = d.get("pid", "")
except Exception: pass
try:
    h = json.load(open(hb)); hbts = h.get("updated_at", 0)
    if isinstance(hbts, str):
        import datetime
        hbts = datetime.datetime.fromisoformat(hbts).timestamp()
    age = int(time.time() - float(hbts))
except Exception: pass
print(phase, pid or "-", age, int(hbts or 0))
PY
)
EOF

# --- 2. proses hidup? ---
ALIVE=0
[ -n "$PID" ] && [ "$PID" != "-" ] && kill -0 "$PID" 2>/dev/null && ALIVE=1
if [ "$ALIVE" = 0 ]; then
  for p in /proc/[0-9]*; do
    [ "$(readlink "$p/exe" 2>/dev/null)" = "$PREFIX/bin/hermes" ] || continue
    tr '\0' ' ' < "$p/cmdline" 2>/dev/null | grep -q "gateway run" && ALIVE=1 && PID="${p#/proc/}" && break
  done
fi
SVST=$(sv status "$SVC" 2>/dev/null | head -1)

# --- 3. kematian TIDAK BERSIH (ledger dalam gateway.log) ---
UNCLEAN_TOTAL=$(grep -c "exited UNCLEANLY" "$GLOG" 2>/dev/null)
UNCLEAN_TOTAL=${UNCLEAN_TOTAL:-0}
UNCLEAN_OLD=$(cat "$OFF" 2>/dev/null)
UNCLEAN_OLD=${UNCLEAN_OLD:-0}
case "$UNCLEAN_TOTAL" in ''|*[!0-9]*) UNCLEAN_TOTAL=0 ;; esac
case "$UNCLEAN_OLD"   in ''|*[!0-9]*) UNCLEAN_OLD=0 ;; esac
UNCLEAN_NEW=$(( UNCLEAN_TOTAL - UNCLEAN_OLD ))
[ "$UNCLEAN_NEW" -lt 0 ] && UNCLEAN_NEW=0
UNCLEAN_LAST=""
[ "$UNCLEAN_NEW" -gt 0 ] && UNCLEAN_LAST=$(grep "exited UNCLEANLY" "$GLOG" | tail -1 | cut -c1-19)

# --- 4. nilai masalah ---
PROB=""
[ "$PHASE" != "running" ] && PROB="$PROB;lifecycle=$PHASE"
[ "$ALIVE" = 0 ] && PROB="$PROB;proses-tiada"
case "$SVST" in run:*) : ;; *) PROB="$PROB;sv=${SVST%%:*}" ;; esac
[ "$HBAGE" -gt 300 ] && PROB="$PROB;nadi-beku=${HBAGE}s"

if [ -z "$PROB" ] && [ "$UNCLEAN_NEW" -eq 0 ]; then
  : > "$STAMP"                       # sihat → reset tanda supaya insiden baharu dihubungi
  echo "${UNCLEAN_TOTAL:-0}" > "$OFF"
  exit 0                             # SENYAP
fi

# --- 5. sekali sahaja bagi setiap insiden ---
SIG="${PROB}|${PID}|${HBTS}|${UNCLEAN_LAST}"
if [ "$(cat "$STAMP" 2>/dev/null)" = "$SIG" ]; then
  echo "${UNCLEAN_TOTAL:-0}" > "$OFF"
  exit 0
fi

# --- 6. cuba pulihkan sendiri ---
ACT="tiada tindakan"
if [ -n "$PROB" ] && [ "${GW_ALERT_NO_ACTION:-0}" != "1" ]; then
  sv restart "$SVC" >/dev/null 2>&1 || sv up "$SVC" >/dev/null 2>&1
  sleep 10
  if sv status "$SVC" 2>/dev/null | grep -q '^run:'; then
    ACT="sv restart dihantar → sekarang RUN"
  else
    ACT="sv restart dihantar → MASIH TIDAK RUN: $(sv status "$SVC" 2>/dev/null | head -1)"
  fi
  say "INSIDEN: $SIG → $ACT"
fi

# --- 7. mesej amaran (stdout → Telegram; salinan → e-mel) ---
MSG="AMARAN GERBANG TELEGRAM · $(date '+%d/%m %H:%M')"
[ -n "$PROB" ] && MSG="$MSG
Masalah: ${PROB#;}"
[ "$UNCLEAN_NEW" -gt 0 ] && MSG="$MSG
Kematian tidak bersih baharu: $UNCLEAN_NEW (terakhir $UNCLEAN_LAST)"
MSG="$MSG
Status sv: ${SVST:-tiada jawapan}
nadi: ${HBAGE}s lalu · pid: ${PID:--}
Tindakan: $ACT
Konsol: $(cat "$ROOT/dashboard_url.txt" 2>/dev/null || echo 'http://127.0.0.1:8787')/?tab=pusat (butang RESET GERBANG)"
printf '%s\n' "$MSG"

# saluran kedua: e-mel (jika Telegram sendiri yang rosak, amaran tetap sampai)
if [ "${GW_ALERT_EMAIL:-1}" != "0" ]; then
  python3 - "$ROOT/.env" "$MSG" <<'PY' 2>/dev/null || say "e-mel GAGAL dihantar"
import os, sys, smtplib
from email.message import EmailMessage
env_path, body = sys.argv[1], sys.argv[2]
conf = {}
try:
    for line in open(env_path, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            conf[k.strip()] = v.strip().strip('"').strip("'")
except Exception:
    sys.exit(1)
user = conf.get("GMAIL_USER"); pwd = conf.get("GMAIL_APP_PASSWORD")
if not (user and pwd):
    sys.exit(1)
to = conf.get("ALERT_EMAIL") or user
m = EmailMessage()
m["From"] = user; m["To"] = to
m["Subject"] = "[UIM] Amaran gerbang Telegram " + body.split("\n")[0][-5:]
m.set_content(body)
with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=25) as s:
    s.login(user, pwd); s.send_message(m)
PY
fi
echo "$SIG" > "$STAMP"
echo "${UNCLEAN_TOTAL:-0}" > "$OFF"
