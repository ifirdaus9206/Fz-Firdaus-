#!/usr/bin/env bash
# Capability audit for a social-commerce content kit.
# Prints CAN / CANNOT before any promise is made to the user.
set -u
ok()  { printf '  %-26s ADA    %s\n' "$1" "$2"; }
no()  { printf '  %-26s TIADA\n' "$1"; }

echo "=== AUDIT KEUPAYAAN ==="

if command -v ffmpeg >/dev/null 2>&1; then
  ok "ffmpeg (video 16s)" "$(ffmpeg -version 2>/dev/null | head -1 | cut -c1-40)"
else no "ffmpeg (video 16s)"; fi

if command -v ffprobe >/dev/null 2>&1; then ok "ffprobe (semakan)" "ada"; else no "ffprobe (semakan)"; fi

PIL=$(python3 -c "import PIL,sys;print(PIL.__version__)" 2>/dev/null)
if [ -n "${PIL:-}" ]; then ok "Pillow (imej)" "$PIL"; else no "Pillow (imej)"; fi

for t in rsvg-convert magick convert; do
  if command -v "$t" >/dev/null 2>&1; then ok "$t (SVG ke PNG)" "ada"; break; fi
done

BROWSER=""
for b in chromium chromium-browser google-chrome playwright; do
  command -v "$b" >/dev/null 2>&1 && BROWSER="$b" && break
done
if [ -n "$BROWSER" ]; then ok "pelayar automatik" "$BROWSER"; else no "pelayar automatik"; fi

KEYS=""
for f in "$HOME/.hermes20/.env" "$HOME/.env" "$HOME/.hermes19/.env"; do
  [ -f "$f" ] || continue
  k=$(grep -oE '^(OPENAI|GEMINI|GOOGLE|FAL|REPLICATE|STABILITY|HF)[A-Z_]*' "$f" 2>/dev/null | sort -u | tr '\n' ' ')
  [ -n "$k" ] && KEYS="$KEYS $k"
done
if [ -n "${KEYS// /}" ]; then ok "kunci API imej" "$KEYS"; else no "kunci API imej (jana imej AI)"; fi

echo
echo "=== RUANG ==="
df -h "$HOME" 2>/dev/null | awk 'NR==2{printf "  baki %s daripada %s (%s guna)\n",$4,$2,$5}'
du -sh "$HOME" 2>/dev/null | awk '{print "  home termux: "$1}'
echo
echo "Nota: tanpa pelayar/kredensial, login Shopee Seller Centre & Google Flow = kerja TANGAN pengguna."
