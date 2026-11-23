#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  tg_watch.sh — PENJAGA LALUAN MASUK TELEGRAM
#  Cron no_agent setiap 5 minit. SENYAP bila sihat.
#  Amaran bila: (a) ada mesej menunggu di pelayan Telegram tetapi gerbang
#  tidak mengambilnya 2 kali berturut, (b) gerbang mati, (c) Bot API gagal.
#  Mesej dihantar ke Telegram (stdout) DAN e-mel (saluran kedua).
#  Ujian: TG_WATCH_ROOT=<dir> TG_WATCH_NO_EMAIL=1 bash tg_watch.sh
# ============================================================
export HOME=/data/data/com.termux/files/home
export PATH=/data/data/com.termux/files/usr/bin:$PATH
ROOT="${TG_WATCH_ROOT:-$HOME/.hermes20}"
STATE="$ROOT/.tg_watch_state"
STAMP="$ROOT/.tg_watch_stamp"
LOG="$ROOT/logs/tg_watch.log"
say() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$LOG"; }

TOKEN=$(grep -m1 '^TELEGRAM_BOT_TOKEN=' "$ROOT/.env" 2>/dev/null | cut -d= -f2- | tr -d '"'"'"' ')
if [ -z "$TOKEN" ]; then echo "AMARAN: TELEGRAM_BOT_TOKEN tiada dalam $ROOT/.env"; exit 0; fi

RESP=$(curl -s -m 20 "https://api.telegram.org/bot$TOKEN/getWebhookInfo" 2>/dev/null)
PEND=$(printf '%s' "$RESP" | python3 -c 'import sys,json
try:
    d=json.load(sys.stdin); r=d.get("result",{}) if d.get("ok") else {}
    print(r.get("pending_update_count","ERR"))
except Exception: print("ERR")' 2>/dev/null)
ALIVE=0
# 1) pid daripada nadi/lifecycle (paling tepat)
PIDH=$(python3 - "$ROOT/state/gateway.heartbeat" "$ROOT/state/gateway.lifecycle.json" <<'PY'
import json, sys
for f in sys.argv[1:]:
    try:
        d = json.load(open(f)); pid = d.get("pid")
        if pid: print(int(pid)); raise SystemExit
    except SystemExit: raise
    except Exception: pass
PY
)
[ -n "$PIDH" ] && kill -0 "$PIDH" 2>/dev/null && ALIVE=1
# 2) sandaran: cari proses yang cmdline-nya mengandungi 'gateway run'
if [ "$ALIVE" = 0 ]; then
  for p in /proc/[0-9]*; do
    tr '\0' ' ' < "$p/cmdline" 2>/dev/null | grep -q "gateway run" && { ALIVE=1; PIDH="${p#/proc/}"; break; }
  done
fi

PREV=$(cat "$STATE" 2>/dev/null); PREV=${PREV:-0}
case "$PEND" in ''|*[!0-9]*) PEND=0; API_BAD=1 ;; *) API_BAD=0 ;; esac
# cangkuk ujian (jangan set dalam cron): TG_WATCH_FAKE_PEND=2
[ -n "${TG_WATCH_FAKE_PEND:-}" ] && { PEND="$TG_WATCH_FAKE_PEND"; API_BAD=0; }
echo "$PEND" > "$STATE"

PROB=""
[ "$API_BAD" = 1 ] && PROB="Bot API tidak menjawab"
[ "$ALIVE" = 0 ] && PROB="${PROB:+$PROB; }gerbang mati"
if [ "${PEND:-0}" -gt 0 ] && [ "${PREV:-0}" -gt 0 ]; then
  PROB="${PROB:+$PROB; }$PEND mesej menunggu di Telegram (2 semakan berturut)"
fi
[ -z "$PROB" ] && exit 0                     # SENYAP

SIG="tg|$PROB|$PEND"
[ "$(cat "$STAMP" 2>/dev/null)" = "$SIG" ] && exit 0
say "INSIDEN: $SIG"

MSG="AMARAN LALUAN MASUK TELEGRAM · $(date '+%d/%m %H:%M')
Masalah: $PROB
pending_update_count: $PEND (semakan sebelum: $PREV)
gerbang: $([ "$ALIVE" = 1 ] && echo hidup || echo MATI)
Konsol: $(cat "$ROOT/dashboard_url.txt" 2>/dev/null || echo http://127.0.0.1:8787)/?tab=pusat (butang RESET GERBANG)
Nota: jika telefon anda menunjukkan ikon jam pada mesej, mesej itu belum sampai ke pelayan Telegram — masalah di app/rangkaian telefon, bukan bot."
printf '%s\n' "$MSG"

if [ "${TG_WATCH_NO_EMAIL:-0}" != "1" ]; then
  python3 - "$ROOT/.env" "$MSG" <<'PY' 2>/dev/null || say "e-mel GAGAL"
import sys, smtplib
from email.message import EmailMessage
env_path, body = sys.argv[1], sys.argv[2]
conf = {}
try:
    for line in open(env_path, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1); conf[k.strip()] = v.strip().strip('"').strip("'")
except Exception: sys.exit(1)
user, pwd = conf.get("GMAIL_USER"), conf.get("GMAIL_APP_PASSWORD")
if not (user and pwd): sys.exit(1)
m = EmailMessage()
m["From"] = user; m["To"] = conf.get("ALERT_EMAIL") or user
m["Subject"] = "[UIM] Amaran laluan masuk Telegram"
m.set_content(body)
with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=25) as s:
    s.login(user, pwd); s.send_message(m)
PY
fi
echo "$SIG" > "$STAMP"
