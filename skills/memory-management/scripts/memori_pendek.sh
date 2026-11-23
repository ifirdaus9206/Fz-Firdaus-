#!/data/data/com.termux/files/usr/bin/bash
# memori_pendek.sh — rekod memori jangka pendek (satu baris = satu fakta/peristiwa)
# Append-only: tidak pernah menulis semula baris lama, jadi crash tidak merosakkan sejarah.
# Guna: memori_pendek.sh "teks fakta" [tag]
set -u
BASE="${MEMORI_BASE:-$HOME/vault/memori}"
DAY="$(date +%Y-%m-%d)"
F="$BASE/01-pendek/$DAY.md"
TAG="${2:-umum}"
TXT="${1:-}"
if [ -z "$TXT" ]; then echo "Guna: memori_pendek.sh \"teks\" [tag]"; exit 2; fi
mkdir -p "$BASE/01-pendek" "$BASE/02-panjang" "$BASE/03-pelajaran"
[ -f "$F" ] || printf '# Memori Pendek %s\n\n' "$DAY" > "$F"
printf -- '- %s | [%s] %s\n' "$(date +%H:%M)" "$TAG" "$TXT" >> "$F"
echo "ok: $F"
