# Transient network failures inside a `no_agent` cron script

Measured 2026-11-23 on the Gmail autosort job (`email_autosort.sh`, `*/15`): one tick died with

```
socket.gaierror: [Errno 7] No address associated with hostname
```

and the user got a red "Susun email GAGAL (exit 1)" alert. Ten minutes later the same command ran
fine: `socket.gethostbyname("imap.gmail.com") -> 173.194.41.108`, `ping 8.8.8.8` OK. So the job was
never broken — the phone had a connectivity/DNS blip, and the alert was noise.

## Pattern: bounded retry inside the script, alert only on the last attempt

```bash
for i in 1 2 3; do
  OUT=$(<command> 2>&1); RC=$?
  [ "$RC" -eq 0 ] && break
  case "$OUT" in
    *gaierror*|*"No address associated"*|*"Temporary failure"*|*"timed out"*|*"Connection reset"*)
      [ "$i" -lt 3 ] && { sleep 60; continue; } ;;
  esac
  break
done
STAMP=$(date "+%Y-%m-%d %H:%M:%S")
[ "$RC" -ne 0 ] && {
  echo "$STAMP GAGAL rc=$RC (cubaan $i/3)" >> "$LOG"
  echo "$OUT" | tail -5 >> "$LOG"
  echo "⚠️ <job> GAGAL (exit $RC, cubaan $i/3)"
  echo "$OUT" | tail -5
}
```

Rules that make it trustworthy:

1. **Match only transient classes.** A real bug (bad credentials, missing file, syntax error) must
   fail on the first attempt — retrying it three times just delays the alert by two minutes.
2. **Keep the retry inside the one script.** A second cron entry that re-runs the job doubles load
   instead of smoothing a blip, and the two runs can overlap.
3. **Silence is the success signal** for `no_agent` deliveries: exit 0 with empty stdout means the
   user sees nothing. Do not print a "recovered ✓" line — a daily summary job already exists for
   reporting.
4. **Log the attempt count** (`cubaan 2/3`) so a later reader can tell a recovered blip from a
   persistent outage.

## Verification

```bash
bash -n script.sh                     # syntax after editing the loop
bash script.sh; echo "rc=$?"          # network healthy now → rc=0 and NO stdout
tail -3 "$LOG"                        # last good line carries the timestamp, no GAGAL
python3 -c "import socket;print(socket.gethostbyname('imap.gmail.com'))"
ping -c 1 -W 3 8.8.8.8 | tail -2
```

If the failure line appears while the probes above answer normally, the incident is closed: the
retry covers it. If the probes fail too, the problem is connectivity (WiFi/data/VPN toggle), not
the script — say that instead of editing code again.
