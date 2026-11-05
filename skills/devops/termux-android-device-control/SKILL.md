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
- When a skill claims it can "control the phone": verify the boundary here first.

## Capability matrix (probe, don't assume)

| Capability | Works | How / why |
|---|---|---|
| Shell, files, network | yes | Termux uid |
| Read /sdcard | yes | direct writes may fail |
| Write shared storage | yes via ~/storage/downloads | scoped storage blocks raw /sdcard |
| Launch app / open URL | yes | am start -n pkg/activity, am start -a VIEW -d url |
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

## Honest limits

No root means: no /data/data of other apps, no silent APK install, no Play Store automation, no
bypassing Play Protect, and no in-app tapping without ADB pairing or an accessibility service
(Tasker/AutoInput). A su in $PREFIX/bin is Termux's stub that prints "No su program found on this
device" - it is not root.

## Pitfalls

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
- references/apk-signature-verification.md - openssl chain, published fingerprints, version probing.
