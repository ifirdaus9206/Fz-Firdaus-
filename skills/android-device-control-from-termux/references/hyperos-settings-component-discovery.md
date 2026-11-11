# Enumerating Settings components on HyperOS (and what the agent cannot see)

Measured 2026-11-11 on Xiaomi 25080RABDG, HyperOS / Android 16, Play-signed Termux, no root,
wireless debugging ON but **unpaired**. Context: user could not find "Pasangkan peranti dengan kod"
and the agent kept guessing menu paths instead of looking.

## 1. `aapt dump xmltree` fails on the Settings APK — use a string-pool scan instead

```bash
p=$(pm path com.android.settings | head -1 | sed 's/^package://')   # /system_ext/priv-app/Settings/Settings.apk
aapt dump xmltree "$p" --file AndroidManifest.xml
# ERROR: dump failed because the resource table is invalid/corrupt.
```

That is a 207 MB priv-app with a split/invalid-for-this-aapt resource table, so the manifest route
via aapt is closed. Termux `strings` also has no `-e` (`strings: error: unknown argument '-e'`), so
UTF-16 pools need Python:

```bash
unzip -p "$p" AndroidManifest.xml > $TMPDIR/m.bin
python3 - <<'EOF'
import re
d = open('/data/data/com.termux/files/usr/tmp/m.bin','rb').read()
names = sorted({m.decode('utf-16le') for m in re.findall(rb'(?:[\x20-\x7e]\x00){4,}', d)})
print("\n".join(n for n in names if 'ireless' in n or 'ebug' in n or 'airing' in n))
EOF
```

Filter on the *class-name* strings; this lists activities/fragments/receivers/settings-keys in one
pass without any ADB.

## 2. What this build actually contains (and what it does not)

Present:

- `com.android.settings.development.AdbQrCodeActivity`
- `com.android.settings.development.qstile.DevelopmentTiles$WirelessDebugging`
- `com.android.settings.Settings$DevelopmentSettingsActivity`
- `com.android.settings.development.DevelopmentSettingsDashboardFragment`
- `"Pair device with pairing code"` / `"Pair device with QR code"` strings (probe them with
  `grep -a -o "Pair device with[^\"]*" /system_ext/priv-app/Settings/Settings.apk`)

**Absent** (AOSP-only names — do not build a walkthrough around them):

- `com.android.settings.development.WirelessDebuggingFragment`
- `com.android.settings.Settings$WirelessDebuggingActivity`
- `com.android.settings.Settings$DevelopmentSettingsDashboardActivity`

Probe proof, and the caveat that `am` prints "Starting" either way:

```
=== com.android.settings/.Settings$WirelessDebuggingActivity
Starting: Intent { cmp=com.android.settings/.Settings$WirelessDebuggingActivity }
Error type 3
Error: Activity class {com.android.settings/com.android.settings.Settings$WirelessDebuggingActivity} does not exist.
```

Consequence for the user's screen: **only a switch is rendered.** Tapping the row label toggles the
switch (`dia tutup buka saje`), there is no ⋮ overflow, and no sub-screen with the pairing row —
i.e. the AOSP "wireless debugging page" does not exist here. Options left: the Settings **search
box** with `pair`, the QS tile (`DevelopmentTiles$WirelessDebugging`), or `AdbQrCodeActivity`.

## 3. `-d` vs `-e` when opening a Settings fragment

```bash
# WRONG on this build: the data URI is truncated at the first colon
am start -n com.android.settings/.SubSettings \
  -d ":settings:show_fragment=com.android.settings.development.WirelessDebuggingFragment"
# -> Starting: Intent { dat=: cmp=com.android.settings/.SubSettings }   (fragment arg lost)

# RIGHT: pass the fragment as an extra
am start -n com.android.settings/.SubSettings \
  -e ":settings:show_fragment" com.android.settings.development.WirelessDebuggingFragment
```

`Starting:` is not proof the target fragment rendered — with `dat=:` truncation it can be a blank
SubSettings page. Only claim the screen opened if the user confirms or ADB (`dumpsys window`) says so.

## 4. You cannot read the screen before pairing — say so early

```bash
screencap -p "$TMPDIR/t.png"     # Failed to take take screenshot. Capturing failed.
settings get global adb_wifi_enabled
# SecurityException: getCurrentUser() … requires android.permission.INTERACT_ACROSS_USERS
```

Working pre-pairing probes:

```bash
getprop | grep -i adb        # [init.svc.adbd]: [stopped]  [ro.adb.secure]: [1]  (needs a code)
python3 - <<'EOF'            # loopback scan finds the wireless-debugging port for you
import socket, concurrent.futures
def probe(p):
    s = socket.socket(); s.settimeout(0.05)
    try:
        return p if s.connect_ex(("127.0.0.1", p)) == 0 else None
    finally: s.close()
with concurrent.futures.ThreadPoolExecutor(max_workers=400) as ex:
    print([r for r in ex.map(probe, range(30000, 50001)) if r])
EOF
adb connect 127.0.0.1:39097  # -> "offline" = ON, unpaired; a 2nd open port = pairing dialog open
```

Division of labour to state in plain Malay: the **6-digit code only exists on the phone screen**, so
the user reads it; the agent types it into `adb pair`. Two failed menu-path guesses in a row is the
signal to stop guessing and ask for a screenshot (`power + vol-down`) — vision reads it in one turn.
