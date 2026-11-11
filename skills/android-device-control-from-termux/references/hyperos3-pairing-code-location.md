# "Kod 6 digit tu di mana?" — locating the pairing code on HyperOS 3 / Android 16

Measured 2026-11-11 on REDMI Note 15 Pro 5G (`25080RABDG`), HyperOS `OS3.0.304.0.WPPMIDC`, Android 16,
Termux app uid, no root. The user had already switched Wireless debugging **ON** and still could not
find any 6-digit number: he was reading the main Wireless-debugging screen, which shows only
*IP address & port*.

## The rule

The code exists **only inside a dialog** that the user opens by tapping a row. Opening that dialog
starts a **second** listener port; closing the dialog kills it. So:

- 1 open port in 30000–65535 → wireless debugging is ON, dialog closed, no code on screen.
- 2 open ports → the pairing dialog is open right now; one of them is the pair service.

Nothing about the code can be read from the shell (no root, no accessibility service). The value must
be copied by eye; only the *port* can be discovered automatically.

## Probe set (all run from the phone itself)

```bash
# 1. is wireless debugging actually on? (loopback only, ~16 s)
nmap -p 30000-65535 --open -T4 --min-rate 4000 127.0.0.1
#   39097/tcp open   -> service up;  +45278 -> dialog open

# 2. device already trusted?  (this is the "right port, no trust" signature)
adb devices                     # 192.168.0.8:39097   offline
adb connect 127.0.0.1:39097     # failed to connect

# 3. does THIS build even have a pairing-code dialog?
APK=/system_ext/priv-app/Settings/Settings.apk
grep -a -o "Pair device with[^\"]*" "$APK" | sort -u
#   Pair device with QR code
#   Pair device with pairing code
grep -a -o "Got pairing code port=" "$APK"
grep -a -c "WirelessDebuggingFragment" "$APK"     # 2 -> fragment class is present
```

Probe 3 is what turns "user is lost" into a fact: if both labels are in `resources`/dex strings, the
feature is not missing and the answer is a navigation answer, not "your phone doesn't have it".

`/proc/net/tcp` is `Permission denied` for app uid, `ss -ltn` prints an empty table and
`ip -4 addr` / `ifconfig wlan0` can both come back blank — nmap on `127.0.0.1` is the reliable
listener check. `nmap` and `ifconfig` come from Termux (`pkg install nmap net-tools`), not Android.

## Open the exact screen for the user (no ADB needed)

```bash
am start -n com.android.settings/.SubSettings \
  -e ":settings:show_fragment" com.android.settings.development.WirelessDebuggingFragment
# prints: Starting: Intent { cmp=com.android.settings/.SubSettings (has extras) }
```

This jumps straight to the Wireless-debugging sub-screen and removes the "cari merata-rata" step.
Do it *before* explaining the path — then the numbered steps start from the screen already in front
of them.

## Navigation truth for HyperOS 3 (the part users miss)

1. Tetapan → **Tetapan tambahan** → **Pilihan pembangun** → **Nyahpepijat wayarles**
2. **Tap the row TEXT** ("Nyahpepijat wayarles"), not the switch. The switch only turns the service
   on; the sub-screen (device name, *IP address & port*, paired devices) opens from the text.
3. Scroll to the **bottom** → **"Pair device with pairing code"** (BM: *Pasangkan peranti dengan
   kod*). On some builds it lives in the **⋮ overflow** at the top-right instead.
4. The dialog shows `IP address & Port` + `Wi-Fi pairing code: ######`. Leave it open; ~2 minutes.
5. Shortcut worth telling them: Settings **search box** → type `pair` → the row appears directly.

Because labels can render in English or Malay on the same device (`Nyahpepijat` and
`Pair device with pairing code` both exist in the APK), quote **both** label spellings.

## Reporting pattern that worked

1. State the measured state first: `offline` + one open port = service on, dialog not open.
2. Say why the number is invisible (it lives in a dialog, not on the main screen).
3. Give the path with the toggle-vs-text warning and the ⋮ fallback.
4. Offer to run the port discovery so the user only has to send 6 digits
   (`scripts/adb-pair-scan.py <code> <lan-ip>`).
5. Write the evidence into the device doc (`DEVICE.md`) — user asks for proof in files, not claims.

## Pitfalls hit here

- An inline `for s in …; do grep …; done` one-liner (several greps + printf against a 58 MB APK) was
  refused by the command parser as an oversized payload; the same work ran fine from a small
  `.sh` file written with `write_file`. When probing an APK, write the probe script, then run it.
- `adb disconnect` the stale `offline` rows before re-scanning, otherwise the old port lingers in
  `adb devices` and looks like a live device.
- The LAN IP can change between sessions (`192.168.0.11` → `192.168.0.8`); re-read it, never reuse a
  remembered address in a handoff.
