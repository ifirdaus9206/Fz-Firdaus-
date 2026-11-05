#!/usr/bin/env bash
# verify-git-ssh.sh — one-shot SSH-to-git-host probe with evidence.
# Usage: bash verify-git-ssh.sh [github-username] [key-path]
# Exit: 0 = authenticated, 2 = key unknown to host (not added / wrong account),
#       3 = local key problem, 4 = username not found.
set -uo pipefail

USER_NAME="${1:-}"
KEY="${2:-$HOME/.ssh/id_ed25519}"

echo "== 1. kunci tempatan =="
if [ ! -f "$KEY" ]; then echo "TIADA kunci: $KEY"; exit 3; fi
ssh-keygen -lf "$KEY.pub" 2>/dev/null || ssh-keygen -lf "$KEY"

# blob-only comparison (ssh-keygen -y re-appends the comment -> false mismatch)
if [ -f "$KEY.pub" ]; then
  A=$(awk '{print $1" "$2}' "$KEY.pub")
  B=$(ssh-keygen -y -f "$KEY" 2>/dev/null | awk '{print $1" "$2}')
  if [ -n "$B" ] && [ "$A" = "$B" ]; then echo "kunci: PADAN (sah)"; else echo "kunci: TIDAK PADAN"; exit 3; fi
fi

echo
echo "== 2. identiti akaun =="
if [ -n "$USER_NAME" ]; then
  BODY=$(curl -s -m 20 "https://api.github.com/users/$USER_NAME")
  if echo "$BODY" | grep -q '"login"'; then
    echo "$BODY" | grep -E '"(login|name|id|created_at)"' | head -4
    echo "-- kunci awam berdaftar pada akaun ini:"
    curl -s -m 20 "https://api.github.com/users/$USER_NAME/keys" | head -12
  else
    echo "AKAUN '$USER_NAME' TIDAK WUJUD (404) — nama login salah"
    exit 4
  fi
fi

echo
echo "== 3. ujian SSH =="
OUT=$(timeout 25 ssh -o StrictHostKeyChecking=accept-new -o BatchMode=yes -T git@github.com 2>&1)
echo "$OUT" | tail -2
if echo "$OUT" | grep -q "successfully authenticated"; then
  echo "STATUS: LULUS"; exit 0
fi

echo "-- diagnosa verbose --"
ssh -o BatchMode=yes -T -v git@github.com 2>&1 \
  | grep -iE "Offering public key|Authentications that can continue|denied" | head -6
if echo "$OUT" | grep -q "Permission denied (publickey)"; then
  echo "STATUS: GAGAL — kunci dihantar tetapi host tidak mengenalinya (belum ditambah / akaun salah)"
  exit 2
fi
echo "STATUS: GAGAL — semak port 22 / ~/.ssh/config"
exit 3