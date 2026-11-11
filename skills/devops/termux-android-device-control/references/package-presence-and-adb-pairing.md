# Package presence (visibility-filtered pm) + wireless ADB pairing discovery

Verified on Xiaomi 25080RABDG (HyperOS / Android 16, no root) with Termux from Google Play.

## 1. `pm list packages` lies about installed packages

Android 11+ package visibility hides other apps from the Termux uid:

```
pm list packages | grep termux      -> package:com.termux          (Termux:Boot installed, invisible)
pm path com.termux.boot             -> (empty)
ls /data/data/com.termux.boot       -> No such file (other-uid 0700 — proves nothing)
dumpsys package com.termux.boot     -> Permission Denial: missing android.permission.DUMP
cmd package path com.termux.boot    -> SecurityException (com.android.shell / INTERACT_ACROSS_USERS)
```

Reporting "not installed" from `pm path` alone is a false negative; the user will correct you.
(Real case: Termux:Boot was installed all along and the user pasted the app's own help screen.)

### Reliable probe: activity + control

```bash
am start -n com.termux.boot/.BootActivity
# installed : Starting: Intent { cmp=com.termux.boot/.BootActivity }
am start -n com.foo.bar/.Baz
# missing   : Starting: Intent { cmp=com.foo.bar/.Baz }
#             Error type 3
#             Error: Activity class {com.foo.bar/com.foo.bar.Baz} does not exist.
```

Only `Error type 3` / `does not exist` means missing. `am start-service -n .../.BootJobService`
returns "Error: Not found; no service started." for BOTH installed and missing (service not
exported) — useless as a probe.

Side effects: the activity probe launches the app. In a status endpoint, cache the result so a panel
that polls does not reopen the app on every tab switch:

```python
def _boot_probe(ttl=600):
    cache = BASE / "data" / "boot_probe.json"
    # read float(ts) + ok from cache if fresh, else run `am start -n <pkg>/.<Activity>`,
    # ok = not ("does not exist" in out or "Error type 3" in out), then persist
```

Report which method decided it (`pm` vs `activity`) so a future session can tell a real "missing"
from a visibility artefact.

## 2. Wireless ADB: pair without the user reading the port

`adb mdns services` is unavailable in the Termux android-tools build ("unknown host service
'mdns:services'"), and users typically hand over only the 6-digit code. The pairing port is an
ephemeral high port (observed 30000–50000). Discovery that works:

1. Parallel TCP scan of 192.168.0.x ports 30000–50000 (socket connect_ex, 0.08 s timeout, ~400
   threads → about a minute on-device).
2. For each open port try `adb pair ip:port <code>` and classify the answer:

| Output | Meaning |
|---|---|
| `Successfully paired to …` | winner — then `adb connect ip:port` |
| `error: protocol fault (couldn't read status message): Success` | not the adb pairing service |
| hangs until timeout, or `Enter pairing code:` then nothing | pairing port, but the code is wrong/expired |

3. Pairing codes expire in ~2 minutes and are single-use — when the scan finds only a timeout, ask
   for a **fresh code** and keep the Pair-with-code dialog open; do not re-try the old digits.

```bash
python3 scripts/adb-pair-auto.py 482913 192.168.0.8
```

`adb connect ip:port` to a not-yet-paired port reports the device as `offline` — that means "TCP
reachable, not authenticated", i.e. pairing still required; it is not a failure of the scanner.

## 3. Files app cannot see files Termux wrote to /sdcard/Download

`~/storage/downloads` = `/storage/emulated/0/Download`. A file created there by Termux exists on
disk (`find` and `ls` see it, 26,000 bytes) but Files by Google lists from **MediaStore**, so it is
invisible — the user reports "fail tu tak ada" while an older APK in a previously-indexed subfolder
IS visible.

- `am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://...` is deprecated and
  did not make the file appear.
- Practical workaround: copy the file into an **already-indexed** folder the user can browse
  (observed working: `Download/hermes-apk/`), then ask them to open *that* folder — not the root.
- The reliable alternative is `adb install -r` once paired; the Files route stays a human tap.
