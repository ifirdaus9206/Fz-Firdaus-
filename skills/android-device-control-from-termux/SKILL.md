---
name: android-device-control-from-termux
description: Control Android apps, APKs, and UI from Termux.
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [termux]
metadata:
  hermes:
    tags: [android, termux, adb, apk, intents, aapt, termux-api, device-control]
    related_skills: [localhost-monitoring-console, file-retrieval-from-android-storage]
---

# Android Device Control from Termux

Operate the user's own phone from a Termux shell (no root): launch apps, verify APKs, read
package state, and drive UI when ADB wireless is paired. This is about the *device*, not about
building dashboards.

## Use when

- "buka app X", "lancar dari terminal", "pasang APK ni", "tangkap skrin", "tekan butang".
- The user asks whether the agent can "masuk dalam app", control UI, or install from Play.
- Any APK download, signature check, or ADB pairing request.

## Capability matrix — state this before promising anything

| Task | Works? | Mechanism |
|---|---|---|
| Shell, read `~`, read `/sdcard` | yes | POSIX |
| Write `/sdcard` root | no (scoped storage) | write via `~/storage/downloads` |
| Launch app / open URL / Play search | yes | `am start` (Termux wrapper) |
| Enumerate installed packages | partial | `pm list packages` is visibility-filtered |
| Install an APK | never silently | Files-app tap or `adb install` |
| Read another app's data | no | sandbox |
| Screen / taps inside apps | only with ADB wireless | `screencap`, `input tap`, `uiautomator dump` |
| Root | no | `su` is a stub; normal app uid |

## Step 1 — installed? and what is its launcher activity?

Cross-check three ways, because each alone lies:

```bash
pm list packages | grep -i <name>
pm path <pkg>                        # empty => not visible / not installed
am start -n <pkg>/<pkg>.<Activity>   # "Starting:" vs "Error type 3"
ls -d /sdcard/Android/data/*<name>*  # data dir exists if the app ever ran
```

Resolve the real activity instead of guessing:

```bash
apk=$(pm path "$pkg" | head -1 | sed 's/^package://')
aapt dump badging "$apk" | sed -n "s/^launchable-activity: name='\([^']*\)'.*/\1/p"
# -> com.anthropic.claude.mainactivity.MainActivity   (no slash in aapt output)
am start -n "$pkg/$activity"        # component form REQUIRES pkg/class
```

Cache in `~/.cache/buka/components.tsv`; `aapt` on a 58 MB APK costs a second. System apps
(`com.android.settings`, Play Store) often expose no `launchable-activity` — keep a small
known-component map (`com.android.settings/.Settings`).

## Step 2 — `buka` launcher

`scripts/buka.sh` → `$PREFIX/bin/buka`:

```bash
buka seting | buka claude | buka com.whatsapp   # alias or package
buka url https://…                              # ACTION_VIEW
buka play "carian"                              # market://search?q=
buka --list <pattern> | --aliases | --component <pkg>
buka apk /storage/emulated/0/Download/x.apk     # open the FOLDER in Files app
```

`buka apk` opens a folder on purpose: Termux cannot install.

## Step 3 — APK install reality

Termux's APK does not declare `REQUEST_INSTALL_PACKAGES` (prove it:
`aapt dump permissions "$(pm path com.termux | sed 's/package://')"`). So:

- `termux-open file.apk` exits 0 and nothing appears — no dialog, no log line.
- `am start -a VIEW -d file://…apk` dies on modern Android (FileUriExposure).
- Working paths, in order:
  1. `adb install -r <apk>` (ADB wireless) — silent and verifiable.
  2. `buka apk …` then user taps the APK in Files; if blocked, allow "Install unknown apps"
     for the **file manager** (Termux has no such toggle).
  3. Never claim the installer is "waiting on screen" after path 0.

Verify the file before handover: see `references/apk-install-and-signature-checks.md`
(unzip `META-INF/*.RSA`, `openssl pkcs7`, compare SHA-256 fingerprint: F-Droid
`43:23:8D:…:CC:AB`, Termux apps `22:8F:B2:…:1C:42`).

## Step 4 — Termux:API matrix (measure, don't assume)

`pkg install termux-api` gives CLIs; the app `com.termux.api` must also exist (battery
answering is the proof). Observed on a normal device:

| Command | Result |
|---|---|
| battery, toast, notification, vibrate | OK |
| camera-info, audio-info, clipboard-get | OK |
| sensor -l, wifi-connectioninfo | fail: "Termux:API is not yet available on Google Play" (visibility / Location) |
| torch | fails until Camera permission is granted to Termux:API |

That Play-Store string is a misleading visibility message, not proof the app is missing.

## Step 5 — ADB wireless for real UI control

```bash
pkg install android-tools
# user: Settings → Developer options → Wireless debugging → Pair device with pairing code
adb-pair 192.168.1.7:37123 483920 [192.168.1.7:40001]
ui shot | ui dump | ui tap X Y | ui swipe … | ui text "…" | ui key HOME | ui open <pkg> | ui cur
```

This adb build rejects `adb mdns services` (`unknown host service 'mdns:services'`) — take the
connect port from the Wireless-debugging screen. Once paired, `adb shell` runs as shell uid:
`pm list packages` becomes truthful, `dumpsys activity` works, screenshots and `input tap`
work. That is the only honest way to answer "apa yang ada di skrin sekarang".

### Pairing without the terminal (users who won't paste commands)

When the user is operating from a phone/browser, a shell one-liner is a dead end — they will not
find it, and asking again erodes trust. If a local console exists, expose the pairing as a form:
`POST /api/device/adb-pair {host:"ip:port", code:"6 digits", connect?}` → server runs
`adb pair` (code on stdin) then `adb connect`, returning `{ok, devices[], connect, log[]}`;
`POST /api/device/shot` → `adb exec-out screencap -p`, saved as a documented step. Snippets:
`localhost-monitoring-console` → `references/ui-discoverability-and-adb-pairing.md`.

Getting the phone's own LAN address is a shell job, not a user question:
`ifconfig wlan0 | grep "inet "` (or `ip route get 1.1.1.1`); quote it so "IP aku tak jumpa di mana"
never happens. Only the pairing **port** and the 6-digit code are on the Android screen.

### Explaining the steps to the phone's owner ("dari tetapan sampai siap")

When the user must do the work on another phone (spouse's, a second device) and asks for a
step-by-step, the short 4-line version is not enough — it produced "aku pun tak faham" and a repeat
request. Lead with the **two-ports table** (pair port from the dialog vs connect port from the main
screen; console field mapping `adb-host` = pair IP:port, `adb-code` = 6 digits, `adb-conn` =
connect IP:port), then number every tap from **Tetapan → Tentang telefon → tap 7× → Tetapan
tambahan → Pilihan pembangun → Nyahpepijat wayarles → Pasangkan peranti dengan kod**, then the
console form, then a failure→cause table. Rules for this user: Malay, one action per numbered line,
no jargon, split into "their phone" vs "this phone", point at visible button labels rather than
shell commands, and save the walkthrough to a file (e.g. `~/hermes-console/PANDUAN-ADB.md`) naming
the path in the reply. Full script: `references/wireless-pairing-walkthrough.md`.

## Pitfalls

1. **Exit 0 is not evidence of a UI action.** `termux-open` on an APK and `am start` with a bad
   component both exit 0. Check output (`Starting: Intent …` vs `Error type 3` /
   `Activity class … does not exist`) and prefer state checks (package path, data dir, logcat).
   Claiming a dialog opened when the platform dropped the intent destroys trust faster than
   admitting the limit.
2. **`am` in Termux is a wrapper, not `/system/bin/am`.** The system binary needs shell uid:
   `SecurityException: package=com.android.shell does not belong to uid=…`. Use plain `am`.
3. **`cmd package resolve-activity` / `dumpsys package` are blocked** for app uid
   (`INTERACT_ACROSS_USERS`, missing `DUMP`). Use `aapt dump badging` on the APK path.
4. **`pm list packages` is visibility-filtered** (targetSdk 37): an installed app can be absent
   from the list, and an invisible app makes `am start` report "Activity class does not exist".
   Need certainty → ADB.
5. **`/sdcard` root is not writable**; `~/storage/downloads` is. Handle `~/storage/*`,
   `/storage/emulated/0/*`, `/sdcard/*` explicitly when computing folder URIs.
6. **`/tmp` is not writable on Termux** — use `$PREFIX/tmp` / `$TMPDIR`.
7. **`monkey -p pkg 1` fails** ("Unable to connect to window manager"); not a launcher fallback.
8. **Never promise Play Store automation.** `market://` opens a listing; installing needs the
   Play UI plus an account.
9. **A 6-digit code on screen is not a login.** Android's wireless-debugging dialog shows
   `Wi-Fi pairing code: 701862` next to `IP address & Port`; users read it as a console password and
   ask where to "log masuk". Say explicitly: the console has no account, this code is consumed by
   `adb pair`, the IP is on the same screen (and can be read from the shell), and a *second* port on
   the Wireless-debugging screen is what `adb connect` needs.
10. **`pm list packages` is a filter, not an inventory.** Across a session it showed 271 packages
    while missing a just-installed app; `am start` then reported "Activity class does not exist".
    Before telling a user "belum dipasang", add `/sdcard/Android/data/<pkg>` existence and a logcat
    grep; for certainty pair ADB (`pm list` as shell uid is unfiltered).

## Verification before reporting

```bash
pm path <pkg>                      # truthy = installed and visible
am start -n <pkg>/<activity> 2>&1   # must not contain "Error"
ls -l /sdcard/Android/data/<pkg>    # app has run at least once
logcat -d -t 3000 | grep -i <pkg>   # install/launch traces (noisy with avc audits)
```

Separate proven facts from inference, and end with the one physical step the user must do
(which folder, which file, where the pairing code lives). If the answer depends on the current
screen, say "aku tak boleh lihat skrin tanpa ADB" and offer pairing.

## Files

- `scripts/buka.sh` — launcher (alias → package → aapt component → `am start -n`), URL/Play/apk modes.
- `scripts/adb-pair.sh` — pair + connect + verify, mDNS-unsupported fallback.
- `scripts/ui.sh` — screenshot/dump/tap/swipe/text/key/open/current-app over ADB.
- `references/apk-install-and-signature-checks.md` — signature recipe, known fingerprints,
  visibility evidence, install-path decision table.
- `references/wireless-pairing-walkthrough.md` — 11-step Settings→done script for a phone you do
  not hold, two-ports/console-field table, failure→cause table, delivery rules for non-technical
  users.
