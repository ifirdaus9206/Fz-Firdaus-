---
name: termux-android-device-control
description: Use when driving Android apps, APKs or ADB from Termux.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [termux]
metadata:
  hermes:
    tags: [android, termux, am, intents, apk, adb, termux-api, device-control]
    related_skills: [localhost-monitoring-console, file-retrieval-from-android-storage]
---

# Termux to Android device control (no root)

Answer "kau boleh masuk app / jalankan app dalam telefon aku?" with a capability matrix backed by
probes on THIS device, then deliver working helpers. Honest answer: shell, files, intents and APK
staging yes; in-app taps, silent installs and other apps' data no (without ADB pairing or an
accessibility app).

## When to use

- "Boleh kau buka app X / lancar dari terminal?", "install F-Droid/Termux:API", "kenapa toast tak keluar".
- Any request to automate taps, screenshots or app launches on the phone.
- "Developer options tak boleh dibuka" / "Pair device with pairing code tak ada" on a financed or
  carrier-subsidised handset -> Recipe 5 (financing lock) before any ADB recipe.
- When a skill claims it can "control the phone": verify the boundary here first.

## Capability matrix (probe, don't assume)

| Capability | Works | How / why |
|---|---|---|
| Shell, files, network | yes | Termux uid |
| Read /sdcard | yes | direct writes may fail |
| Write shared storage | yes via ~/storage/downloads | scoped storage blocks raw /sdcard |
| Launch app / open URL | only with Termux foreground | am start -n pkg/activity, am start -a VIEW -d url — background activity start is silently blocked (see Pitfalls) |
| List installed packages | partial | pm list packages is filtered by package visibility |
| Download + verify APK | yes | curl + openssl pkcs7 cert chain |
| Install APK | user taps in a Files app, or `adb install` | **NOT** `termux-open x.apk` - that is a silent no-op here (see Recipe 2) |
| Install from Play Store | no | market:// deep link only |
| Read other apps' data | no | /data/data/<pkg> is 0700 other-uid |
| Tap/scroll inside an app | only via ADB | android-tools + wireless pairing -> input tap, uiautomator dump |
| dumpsys / cmd package resolve-activity / /system/bin/am | no | SecurityException: com.android.shell does not belong to uid=<termux> |

## Recipe 1 - launch any app (buka)

`am` on Termux is Termux's own wrapper, not /system/bin/am. It accepts -n <component> but needs a
fully qualified component; there is no -p <package> launch path.

1. Resolve the launcher activity without cmd package (blocked):
   apk=$(pm path "$pkg" | head -1 | sed 's/^package://')
   aapt dump badging "$apk" | sed -n "s/^launchable-activity: name='\([^']*\)'.*/\1/p" | head -1
   aapt lives at $PREFIX/bin/aapt; installed APKs are world-readable under /data/app/.../base.apk.
2. Normalise: com.foo.bar.MainActivity -> com.foo.bar/com.foo.bar.MainActivity (or com.foo/.MainActivity).
   A bare class name fails with "Bad component name".
3. am start -n "$comp", then CHECK THE OUTPUT: am prints "Starting: Intent ..." even when it then
   reports "Error: Activity not started", and a malformed component dumps the whole usage text.
   Grep for error:|exception|unable to resolve.
4. Cache resolved components (~/.cache/buka/components.tsv); keep a small KNOWN map for system apps
   (com.android.settings/.Settings) where aapt reports no launchable-activity.

Ready-made launcher: scripts/buka (aliases, URL, Play search, --list, --component, cache).

## Recipe 2 - verify an APK, then hand the install to the user

1. curl -sSL -o app.apk <url>; sha256sum; test the zip (zipfile.ZipFile(...).testzip()).
2. Extract the v1 signer cert and fingerprint it:
   unzip -o -q app.apk 'META-INF/*.RSA' -d sig
   openssl pkcs7 -inform DER -in sig/META-INF/*.RSA -print_certs | openssl x509 -noout -fingerprint -sha256
3. Compare with the publisher's published fingerprint (F-Droid key in references/) and report the
   subject CN too - a matching fingerprint with a strange CN is a red flag.
4. **Do not rely on `termux-open app.apk` for the installer.** Verified here: it exits 0 and nothing
   appears, because the Termux APK does not declare
   `android.permission.REQUEST_INSTALL_PACKAGES`. Prove it before blaming the file:
   `p=$(pm path com.termux | head -1 | sed 's/^package://'); aapt dump permissions "$p" | grep -i INSTALL`
   (empty = Termux cannot trigger an install; the "Install unknown apps" toggle will not exist for it).
5. Hand off through a Files app that *can* install, and say exactly where to tap:
   ```bash
   cp app.apk ~/storage/downloads/          # top of Downloads, easy to find
   am start -a android.intent.action.VIEW \
     -d "content://com.android.externalstorage.documents/document/primary%3ADownload" \
     -t "vnd.android.document/directory"    # opens that folder in Files
   # MIUI file manager: com.mi.android.globalFileexplorer/com.android.fileexplorer.FileExplorerTabActivity
   ```
   Say: Files -> Downloads -> `app.apk` -> Install. One human tap, the only route without ADB.
   `buka apk <path>` (scripts/buka) performs this folder handoff.
6. With ADB already paired, skip the tap: `adb install -r ~/storage/downloads/app.apk`.
7. Version facts: `aapt dump badging app.apk | head -3`. After install verify by LAUNCHING
   (`buka <alias>`), not by `pm list packages | grep -c` (visibility-filtered).

If the user says "aku cari tak jumpa" after you claimed to open the installer, the cause is step 4,
not their eyes: re-check the manifest permission, then reopen the **folder**, not the APK.

## Recipe 3 - Termux:API

pkg install -y termux-api installs only the CLI. The companion app answers over a broadcast service;
when present, termux-battery-status returns JSON. Test by CALLING AN API, not by grepping
pm list packages (visibility filtering hides it).

Verified working: battery, wifi-connectioninfo, camera-info, sensor, telephony-deviceinfo, audio-info,
vibrate, toast, notification, clipboard-get. termux-torch needs Camera permission for the API app.
termux-toast exits 0 even when nothing appears - confirm visually, never by exit code.

## Recipe 4b - package installed? pairing port?

See `references/package-presence-and-adb-pairing.md`: `pm list`/`pm path` are visibility-filtered, so
prove presence with an activity probe plus a control package; and auto-discover the wireless-debugging
pairing port instead of asking the user for it.

## Recipe 4 - ADB wireless (the only real in-app control path)

pkg install -y android-tools
adb start-server; adb devices         # empty until paired
# phone: Settings -> Developer options -> Wireless debugging -> Pair device with pairing code
adb-pair <ip:pair_port> <6-digit-code> [ip:connect_port]
# do NOT depend on `adb mdns services`: Termux android-tools 35.0.2 replies
# "error: unknown host service 'mdns:services'". Read both ports off the Wireless
# debugging screen (pairing port on the Pair-with-code dialog, connect port on the
# main screen), then pass the connect port explicitly.

Once adb devices shows "device", commands run as shell uid: am start, input tap, uiautomator dump,
screencap, dumpsys window. Helper: scripts/ui (shot|dump|tap|swipe|text|key|open|cur).
Notes: input text needs spaces as %s; adb connect 127.0.0.1:5555 is refused unless adbd is already in
TCP mode; pairing codes are short-lived and single-use.

### Recipe 4c - read wireless-debugging STATE before you have a code

Blind until paired, but the phone is its own host: wireless adbd listens on a high local port. Scan
127.0.0.1 instead of asking the user to read the port off the screen:

```bash
python3 - <<'EOF'
import socket, concurrent.futures
def probe(p):
    s = socket.socket(); s.settimeout(0.05)
    try:
        return p if s.connect_ex(("127.0.0.1", p)) == 0 else None
    finally: s.close()
with concurrent.futures.ThreadPoolExecutor(max_workers=400) as ex:
    print([r for r in ex.map(probe, range(30000, 50001)) if r])
EOF
adb connect 127.0.0.1:<port>; adb devices -l
```

- `offline` = TCP reachable but NOT authenticated -> **wireless debugging is already ON**, pairing is
  the only thing missing. Say this out loud when the user insists "the button isn't there"; it stops
  the hunt for a wrong toggle. Verified on HyperOS 3 / Android 16: port 39097 -> `offline`,
  `init.svc.adbd` still `stopped`, `ro.adb.secure: 1`.
- `failed to connect` = nothing adb-like on that port; widen the range.
- The 6-digit code is screen-only: `screencap` from the Termux uid fails ("Capturing failed") and
  `settings get global adb_wifi_enabled` is refused (INTERACT_ACROSS_USERS), so the **human** reads
  the code and the **agent** runs `adb pair 127.0.0.1:<pair_port> <code>`. The pairing port only
  exists while the Pair-with-code dialog is open — rescan at that moment.
- Full HyperOS/Malay navigation map and the screenshot-guided protocol:
  `references/hyperos-wireless-debugging-navigation.md`.

## Recipe 5 - STOP: financing-locked phones cannot enable developer options

Before walking anyone through Recipe 4, ask one screenshot of what happens when they tap
`Versi OS` ×7. If the modal reads **"Disekat oleh penyedia kredit anda"** (padlock icon, buttons
Tutup / Ketahui lebih lanjut), the handset is an instalment/subsidised unit and the provider's
device-owner policy disables Developer options:

- No Developer options -> no Wireless debugging -> no pairing code -> **ADB is impossible on that
  device**. `input tap`, `screencap`, `uiautomator` are all gone with it.
- Stop immediately. Do not hunt more toggles, menus or activity names; it is a policy, not a UI bug.
- Do not attempt a bypass: the lock belongs to the device owner, it is a legal matter, and without
  root it cannot work. Offer to draft the unlock request (IMEI + contract + proof of payment).
- `Pentadbir peranti -> Telecoms Client` with a greyed `Nyahtifkan` is a red herring, a normal system
  component; correct the user if they blame it.
- Remaining option = accessibility automation (MacroDroid webhook on 127.0.0.1 + UI Interaction),
  which needs no Developer options but is a costed experiment, not a guaranteed path. Full detail:
  `references/hyperos-wireless-debugging-navigation.md` §6.

## Recipe 6 - accessibility-automation bridge (only when ADB is impossible)

For financing-locked handsets (Recipe 5) the sole remaining control path is an accessibility automation
app driven from Termux over localhost HTTP. Treat it as a costed experiment: the Termux half is
testable by you, the app half is 15-20 human taps.

1. **Install from Play Store, not sideload.** Sideloading needs the human to find the APK in Files
   (`termux-open` is a no-op, Recipe 2 step 4); a Play link in chat costs two taps:
   `https://play.google.com/store/apps/details?id=<pkg>` sent as a markdown link (`market://` via
   `am start` is blocked while Termux is backgrounded).
2. **Prove the install from the shell** — a Play-installed app IS resolvable, unlike filtered system
   apps:
   ```bash
   pm path com.arlosoft.macrodroid           # -> /data/app/~~.../base.apk
   pm list packages | grep -i macrodroid     # -> package:com.arlosoft.macrodroid
   aapt dump badging $(pm path com.arlosoft.macrodroid | sed 's/^package://') | head -3
   # launchable-activity: name='com.arlosoft.macrodroid.intro.IntroActivity'
   ```
   Do not probe `com.arlosoft.macrodroid/.MainActivity` — it does not exist and "does not exist"
   reads like "app not installed". Take the launcher activity from `aapt dump badging`.
3. **Build and test the Termux side against a mock first**, so the only unknown left is the app:
   `scripts/webhook-bridge/mdr.sh` (shot | tap "text" | swipe | key | ping) +
   `scripts/webhook-bridge/mock_webhook.py`. Verified: `ping` → HTTP 200 and the mock logs
   `{"act": "tap", "text": "Nyahpepijat wayarles"}` — spaces and Malay text survive
   `curl --data-urlencode`. Point `BASE=` in `webhook.conf` at the URL MacroDroid prints once the
   human builds the macro.
4. **Human enables accessibility**: phone `Tetapan` → scroll to the very bottom → `Kebolehaksesan` →
   `Apl yang dimuat turun` / `Perkhidmatan yang dimuat turun` → app → toggle on → `Benarkan`.
5. Hand over the macro spec: `templates/macrodroid-bridge-macros.md`.

Report status honestly: "Termux side verified, app side not yet" — a passing mock must never be
reported as "the phone can be tapped now".

## Honest limits

No root means: no /data/data of other apps, no silent APK install, no Play Store automation, no
bypassing Play Protect, and no in-app tapping without ADB pairing or an accessibility service
(Tasker/AutoInput). A su in $PREFIX/bin is Termux's stub that prints "No su program found on this
device" - it is not root.

## Pitfalls

- **`am start` prints "Starting: Intent {…}" and NOTHING appears while Termux is backgrounded.**
  Android 10+ blocks background activity starts; the wrapper exits 0 with no `Error type 3`. Verified
  on Xiaomi 25080RABDG (HyperOS/Android 16): `-a android.settings.APPLICATION_DEVELOPMENT_SETTINGS`
  and `-n com.android.settings/.Settings$DevelopmentSettingsActivity` both "succeed" while the phone
  keeps showing the old Seting page. Never claim a screen was opened — hand navigation to the human
  (one tap at a time, screenshot back) or ask them to foreground Termux first.
- **HyperOS Settings has no `WirelessDebuggingFragment` / `Settings$WirelessDebuggingActivity`.**
  Dump the manifest string pool instead of aapt (aapt reports "resource table is invalid/corrupt"
  for /system_ext/priv-app/Settings/Settings.apk): `unzip -p Settings.apk AndroidManifest.xml` then
  regex UTF-16LE runs. Only `com.android.settings.development.AdbQrCodeActivity` and the QS tile
  `DevelopmentTiles$WirelessDebugging` exist — reach the pairing dialog via Developer options row or
  QS-tile long-press, never by guessing an activity name.
- **"Nyahpepijat wayarles" is absent when Developer options were never enabled.** On HyperOS the
  bottom of Seting (above "Tetapan tambahan") has no "Pilihan pembangun" row at all; enable it first
  (Mengenai telefon → tap Versi OS ×7 → lock-screen PIN). Check this before hunting for a 3-dot menu.
  The OTG toggle inside "Lebih banyak pilihan sambungan" is a different switch users mistake for it.
- **"Buka Tetapan" is ambiguous — users open the app's own Settings, not the phone's.** Told to
  enable accessibility, a user inside MacroDroid went `Tetapan` tab → `Pelayanan SMTP` and reported
  they were "already in settings". Telltale of the wrong screen: bottom tabs `Utama / Makro / Templat
  / Tetapan`. Say "Tetapan **telefon**" and describe the icon (grey gear, not the app icon) plus the
  expected row (`Kebolehaksesan`, last row of the phone's list).
- **A greyed-out `Nyahtifkan` on a device-admin page is not the blocker.** `Pentadbir peranti →
  Telecoms Client` is a normal system component; users conclude "my monthly-contract line is blocking
  me". Name the real cause (financing lock, Recipe 5) instead of debating the red herring.
- pm list packages is not ground truth; visibility hides most apps.
- am is not /system/bin/am; the real one fails with SecurityException (com.android.shell).
- monkey -p pkg -c LAUNCHER 1 often fails with "Unable to connect to window manager" - use am start -n.
- /tmp is unwritable and rm -rf /tmp/... is refused on Termux; use $TMPDIR ($PREFIX/tmp).
- Direct /sdcard writes fail under scoped storage even when reads work; use ~/storage/downloads.
- Downloading an APK is not installing it; verify pm list packages afterwards.
- **`termux-open x.apk` can be a silent no-op** (Termux APK has no REQUEST_INSTALL_PACKAGES).
  `logcat -c; termux-open x.apk; logcat -d -t 500 | grep -iE "PackageInstaller|INSTALL_FAILED"`
  printing nothing = the install intent was never delivered. Stage the APK for a Files app or use
  `adb install`; re-issuing the same command cannot produce a different result.
- **`am start -a VIEW -d content://...` prints "Starting: Intent ..." even when nothing appears.**
  Without ADB you cannot read the foreground app (`dumpsys activity` and `cmd appops get` fail with
  SecurityException: INTERACT_ACROSS_USERS), so never call that "dialog dibuka" - say the folder/URL
  was handed to Files and let the human confirm what is visible.
- **Some system packages expose no `launchable-activity`** (DocumentsUI, package installers) even
  when `pm path` resolves and the APK is readable. Keep a KNOWN component map; for file handoff use
  the OEM file manager (`com.mi.android.globalFileexplorer/com.android.fileexplorer.FileExplorerTabActivity`).
- A "verified" signature needs a reference: print the fingerprint AND compare to the publisher's value.

## Verification (report as evidence)

buka seting            -> dibuka: com.android.settings - .Settings
buka claude            -> dibuka: com.anthropic.claude - .mainactivity.MainActivity
buka url https://...   -> dibuka
termux-battery-status  -> {"present": true, "technology": "Li-poly", ...}
aapt dump permissions $(pm path com.termux | sed 's/package://') | grep -c INSTALL -> 0
pm list packages | grep -c fdroid -> 0   (APK staged in Downloads; human still has to tap Install)
adb devices            -> (empty until paired)

## Files

- scripts/buka - app/URL/Play launcher with aapt resolution + cache.
- scripts/ui - ADB UI control (shot, dump, tap, swipe, text, key, open, cur).
- scripts/adb-pair - wireless pairing + connect + verify.
- scripts/axml-classnames.py - list activity/class names from an APK manifest when aapt reports
  "resource table is invalid/corrupt" (HyperOS Settings).
- references/hyperos-wireless-debugging-navigation.md - HyperOS 3 / Android 16 path to the pairing
  dialog, Malay label map, the OTG-toggle trap, and the one-step + screenshot protocol for
  non-technical users.
- scripts/webhook-bridge/mdr.sh - fire an automation app's webhook from Termux (shot/tap/swipe/key/ping).
- scripts/webhook-bridge/mock_webhook.py - stand-in HTTP trigger, so the Termux half is provable before
  any macro is built; a 200 from it is NOT evidence the phone can be tapped.
- templates/macrodroid-bridge-macros.md - the three macros to hand a human, plus Play link,
  accessibility path and acceptance test.
- references/apk-signature-verification.md - openssl chain, published fingerprints, version probing.
