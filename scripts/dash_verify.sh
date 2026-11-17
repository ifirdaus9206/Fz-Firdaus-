#!/data/data/com.termux/files/usr/bin/bash
# Sahkan dashboard + tunnel: URL publik, pagar login, login berjaya, API hidup.
# Password dibaca dari fail rahsia — tidak pernah dipaparkan.
set -u
BASE=$(cat "$HOME/.hermes20/dashboard_url.txt")
PASS=$(grep -m1 '^password:' "$HOME/.hermes20/secrets/dashboard_login.txt" | awk '{print $2}')
JAR=$(mktemp "$HOME/.hermes20/tmp_cookies.XXXXXX")
trap 'rm -f "$JAR"' EXIT

echo "URL        : $BASE"
echo -n "GET /      : "; curl -s -m 20 -o /dev/null -w "%{http_code} -> %{redirect_url}\n" "$BASE/"
echo -n "login page : "; curl -s -m 20 -o /dev/null -w "%{http_code}\n" "$BASE/login"
echo -n "login POST : "; curl -s -m 25 -c "$JAR" -o /dev/null -w "%{http_code}\n" \
  -X POST "$BASE/auth/password-login" -H "Content-Type: application/json" \
  --data "{\"provider\":\"basic\",\"username\":\"firdaus\",\"password\":\"$PASS\"}"
echo -n "dashboard  : "; curl -s -m 25 -b "$JAR" -o /dev/null -w "%{http_code}\n" "$BASE/"
echo -n "api/status : "; curl -s -m 25 -b "$JAR" -o /dev/null -w "%{http_code}\n" "$BASE/api/status"
