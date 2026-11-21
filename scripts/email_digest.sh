#!/data/data/com.termux/files/usr/bin/bash
# email_digest.sh — LAPORAN SEKALI SEHARI (21:00) tentang susunan emel.
# Senyap jika tiada apa-apa. Cetak satu blok ringkas.
set -u
LOG="$HOME/vault/email-inbox/_autosort.log"
DIR="$HOME/vault/email-inbox"
TODAY=$(date '+%Y-%m-%d')

# 1) Jumlah disusun hari ini daripada log
PENT=0; KERJA=0; PROM=0; RUNS=0
if [ -f "$LOG" ]; then
  while IFS= read -r line; do
    case "$line" in
      *"$TODAY"*RINGKASAN*)
        p=$(printf '%s' "$line" | sed -n 's/.*"PENTING": \([0-9]*\).*/\1/p')
        k=$(printf '%s' "$line" | sed -n 's/.*"KERJA": \([0-9]*\).*/\1/p')
        r=$(printf '%s' "$line" | sed -n 's/.*"PROMOSI": \([0-9]*\).*/\1/p')
        PENT=$((PENT + ${p:-0})); KERJA=$((KERJA + ${k:-0})); PROM=$((PROM + ${r:-0}))
        RUNS=$((RUNS + 1))
        ;;
    esac
  done < "$LOG"
fi

# 2) Jumlah semasa dalam setiap label (IMAP, baca sahaja)
COUNTS=$(cd "$DIR" && python3 - <<'PY' 2>/dev/null
import imaplib, os
env={}
for line in open(os.path.expanduser("~/.hermes20/.env")):
    line=line.strip()
    if "=" in line and not line.startswith("#"):
        k,v=line.split("=",1); env[k]=v.strip().strip('"')
try:
    M=imaplib.IMAP4_SSL("imap.gmail.com"); M.login(env["GMAIL_USER"], env["GMAIL_APP_PASSWORD"])
    out=[]
    for box in ("INBOX","1-PENTING","2-KERJA","3-PROMOSI","0-LAIN"):
        t,d=M.select(f'"{box}"', readonly=True)
        out.append(f"{box}={int(d[0])}" if t=="OK" else f"{box}=?")
    M.logout()
    print(" ".join(out))
except Exception:
    print("")
PY
)

JUM=$((PENT + KERJA + PROM))
if [ "$JUM" -eq 0 ] && [ -z "$COUNTS" ]; then
  exit 0     # senyap: tiada apa dilaporkan
fi

echo "📬 LAPORAN EMEL — $(date '+%d/%b %H:%M')"
echo "Hari ini disusun: $JUM  (Penting $PENT · Kerja $KERJA · Promosi $PROM) · $RUNS kitaran"
[ -n "$COUNTS" ] && echo "Jumlah semasa: $COUNTS"
exit 0
