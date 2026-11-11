---
name: android-device-control-from-termux
description: Control Android apps, APKs, and UI from Termux.
version: 1.3.0
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
- MacroDroid / automation-app questions ("Pencetus", "Tindakan", "Kekangan", "webhook tak jalan",
  "makro tak jalan bila aku buka kunci") → Step 7 + `references/macrodroid-bridge-and-actuator-isolation.md`.
- "kenapa Termux tutup / tidur di latar belakang", gateway/console mati bila skrin off, wake-lock
  questions, Doze or battery-optimisation complaints → follow
  `references/background-survival-diagnostics.md`.

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

Two workarounds that look promising and are **not** worth retrying (measured 2026-11-11):
a SAF content URI (`am start -a VIEW --grant-read-uri-permission -d
"content://com.android.externalstorage.documents/document/primary%3ADownload%2Fx.apk"`) throws
`java.lang.reflect.InvocationTargetException` through termux-am's `CrossVersionReflectedMethod`,
and `content query --uri content://com.termux.fileprovider/` is refused with
`SecurityException: … requires android.permission.ACCESS_CONTENT_PROVIDERS_EXTERNALLY`. The
broadcast form `am broadcast -n com.termux/com.termux.app.TermuxOpenReceiver …` reports
`Broadcast sent without waiting for result` either way, so it can never confirm delivery.
Budget one attempt, then stop and ask for the tap or the pairing code.

### Prove the APK is good before blaming the platform

When no install dialog appears, split "bad download" from "Android blocked it" *before* answering.
`aapt` may not be installed; a 10-line stdlib check is enough:

```python
import zipfile, re
z = zipfile.ZipFile("x.apk")
txt = z.read("AndroidManifest.xml").decode("utf-16-le", "ignore")   # binary AXML → readable runs
print(sorted({s for s in re.findall(r"[ -~]{6,}", txt) if "termux" in s.lower()}))
data = open("x.apk", "rb").read()
print("v2 sig:", b"APK Sig Block 42" in data, "| bytes:", len(data))
```

Output confirms `package`, activity/receiver names and `RECEIVE_BOOT_COMPLETED`, plus the v2
signing block Android 14+ requires. A valid APK + empty `pm path <pkg>` = the install never
happened (dialog dismissed or blocked), which is an honest sentence you can tell the user.

### Prepare-to-one-tap handoff (the pattern that actually lands)

The install cannot be automated, but everything *around* it can. Do all of it, then ask for exactly
one tap:

```bash
curl -sL -m 120 -o ~/storage/downloads/TermuxBoot.apk \
  https://f-droid.org/repo/com.termux.boot_1000.apk       # 26,000 bytes, verify size + unzip -l
curl -s https://f-droid.org/api/v1/packages/com.termux.boot   # suggestedVersionCode, name, versions
termux-open --content-type application/vnd.android.package-archive ~/storage/downloads/X.apk
am start -a android.intent.action.VIEW -d "file://$HOME/storage/downloads/X.apk" \
         -t application/vnd.android.package-archive         # both exit 0 — see pitfall 1
pm list packages com.termux.boot                            # the ONLY proof of success
```

If a local console exists, wrap this as `POST /api/device/boot-install` (returns the command log +
fresh `installed` flag) plus `GET /api/device/boot` (`installed`, `apk{path,bytes}`, `boot_dir`,
`boot_scripts[]`), and put a **BUKA PEMASANG APK** button beside illustrated steps. Tell the user
plainly: *Android does not let Termux install silently; tap PASANG once, then open the app once.*

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

Caveat measured 2026-11-11 (HyperOS / Android 16, Play-signed Termux): both
`ip -4 addr show wlan0` and `ifconfig wlan0` returned **empty output**, and `adb mdns services` is
unsupported, so the address cannot always be pre-filled. Treat the shell read as best-effort: ask
the user for the `IP:port` shown in the pairing dialog (it displays both), and say plainly that the
code expires in ~2 minutes rather than guessing a port.

### When the user sends only the 6-digit code (no port)

They will paste `482913` and say *"cuba test"*, because the dialog's second line (`IP address &
Port`) reads as decoration to them. Do not answer "I need the port" and stop — find it:

```bash
python3 scripts/adb-pair-scan.py 482913 192.168.0.8
# TCP-scan 30000-50000 (0.08 s, 400 workers) → adb pair on each open port → connect on success
```

Read the output as three different verdicts: `protocol fault (couldn't read status message)` = not the
pairing service; **hang / timeout** = the pairing port, but the code was rejected or has expired
(lifetime ≈ 2 minutes); `Successfully paired` = run `adb connect` and `adb devices`. `adb connect`
against an unpaired wireless-debugging port lists the device as `offline` — that is the "right port,
no trust yet" signature.

Re-scan before **every** attempt: the open-port set changed three times inside ten minutes
(`[38972, 39097, 45278]` → `[39097]` → `[33998, 39097, 45314]`); one stable port is usually the
wireless-debugging service itself. `adb kill-server` before a rescan and `adb disconnect <ip:port>`
clear stale `offline` rows.

Honest end condition: this removes the port question, **not** the code expiry or the user's tap. If
every code arrived expired, say so — the scanner proved the port deterministically, pairing still
needs a fresh code. Full transcript and the file-visibility trap it pairs with:
`references/apk-visibility-and-portless-pairing.md`.

### "Kod 6 digit tu aku cari tak jumpa" — the code lives in a dialog, not on the screen

Wireless debugging ON but no number anywhere is a **navigation** problem, not a port problem. Settle
the state with three probes from the phone, then answer the question:

```bash
nmap -p 30000-65535 --open -T4 --min-rate 4000 127.0.0.1   # 1 port = ON, dialog closed; 2 = dialog open
adb devices                                                # "<ip>:<port>  offline" = right port, no trust
grep -a -o "Pair device with[^\"]*" /system_ext/priv-app/Settings/Settings.apk
#   "Pair device with pairing code" + "Pair device with QR code" present = build HAS it -> user is lost
```

Then remove the searching entirely:

```bash
am start -n com.android.settings/.SubSettings \
  -e ":settings:show_fragment" com.android.settings.development.WirelessDebuggingFragment
```

**Use `-e`, never `-d`, for the fragment arg.** Measured on HyperOS / Android 16:
`-d ":settings:show_fragment=com.android.settings…WirelessDebuggingFragment"` returns
`Starting: Intent { dat=: cmp=com.android.settings/.SubSettings }` — the URI is truncated at the
colon, so the fragment name never reaches Settings while `am` still prints "Starting". `-e` carries
the fragment as an extra and survives.

**Probe the component name before guiding anyone.** Guessed activity names cost the user taps:

```bash
for c in 'com.android.settings/.Settings$WirelessDebuggingActivity' \
         'com.android.settings/.Settings$DevelopmentSettingsDashboardActivity'; do
  echo "=== $c"; am start -n "$c" 2>&1 | head -6; done
# both -> "Error type 3 / Activity class … does not exist." on HyperOS — those names are AOSP-only
```

When every launch form fails but the APK string scan proves the pairing UI exists on the build, stop
guessing menu paths and ask for a screenshot (pitfall 18). Enumerating this build's real Settings
components — and why `aapt dump xmltree` cannot do it — is in
`references/hyperos-settings-component-discovery.md`.

HyperOS 3 trap to spell out: the **switch** only turns the service on — the sub-screen (IP & port,
paired devices, the pairing row) opens when the user taps the **row text**. The pairing row is at the
**bottom** of that screen or in the **⋮ overflow**; the Settings **search box** with `pair` reaches it
too. Quote both label spellings (English and `Pasangkan peranti dengan kod`) — the same device renders
either. Never answer "phone kau tak ada ciri itu" before probe 3 proves it. Full path, evidence and
reporting pattern: `references/hyperos3-pairing-code-location.md`.

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

## Step 6 — "Termux mati di latar belakang": kill, sleep, or restart?

Full recipe + denial table: `references/background-survival-diagnostics.md`. Decisive moves:

```bash
uptime                                     # kernel uptime — works even when /proc/uptime is denied
ps -A -o pid,ppid,etimes,args | grep -E 'runsvdir|gateway'
sv status $PREFIX/var/service/*            # "run: … (pid N) 6280s" / "down: … 1s, normally up"
logcat -d | grep -E 'TermuxService' | tail -6
```

- `uptime` ≫ process `etimes` → **no reboot**; only app/service processes restarted. Correct the
  user if they assume the phone restarted.
- Same pid at both ends of the error window → the process never died; `httpx.ReadError` /
  socket timeouts are a **Doze network cut**, not a kill. A wake lock prevents CPU sleep but does
  **not** exempt the app from Doze network rules — "wake lock held + ReadError" is expected.
- Held-lock proof is the log line, not the exit code:
  `V TermuxService: Ignoring acquiring WakeLocks since they are already held`.
- Whole `runsvdir` tree sharing one `etimes` while the Termux app pid is far older → child tree
  killed/restarted, app survived (phantom process killer / LMK of children / manual
  `termux-services start`).
- `down: … 1s, normally up, want up` = crash-loop; read the `run` script and the service log.
  `ppid=1` + `readlink /proc/<pid>/cwd` = unsupervised orphan — nothing restarts it.
- Check `TERMUX_VERSION`: `googleplay.*` is Play-signed, so Termux:Boot / Termux:API from F-Droid
  **cannot** be installed. Never recommend them without naming the build migration first.

## Step 7 — MacroDroid as a free actuator bridge (when ADB pairing is blocked)

If pairing is impossible, a MacroDroid macro can stand in for `input tap` / `screencap`:
Termux sends a signal → MacroDroid acts. Full recipe, Malay UI label map and test script:
`references/macrodroid-bridge-and-actuator-isolation.md`.

- Order of assembly is **Pencetus (trigger) → Tindakan (action) → Kekangan empty**. Users build the
  action first (`Tambah Tindakan` is the button they find) and then ask for a test that cannot pass.
- `Kesambungan → Webhook (URL)` is **premium** and only what is on the phone screen is real. Current
  versions render a **cloud** URL `https://trigger.macrodroid.com/<device-id>/<identifier>`, delivered
  by Firebase Cloud Messaging (needs Google Play services + the phone online). Until a real URL is
  pasted into the bridge config (`~/phone_bridge/webhook.conf` in the usual layout), the placeholder
  `127.0.0.1:18080` has no listener and `curl` → `HTTP 000`; report that honestly instead of "dah
  diuji". Once you have the URL the status code **is** the diagnosis: `200` = registered + push
  queued (later silence is device-side), `404 {"error":"Not found"}` = this identifier is not
  registered for that device-id (macro unsaved / disabled / no action — not an encoding bug; see
  pitfall 22), `000` = no answer. Query params only fill variables that already exist, so prefer one
  identifier per command (`/ping`, `/shot`, `/tap`). Facts + 404 ladder:
  `references/macrodroid-bridge-and-actuator-isolation.md` §A0–A2.
- Free alternative: `termux-notification --title SIG --id 91 --priority high` + trigger
  `Pemberitahuan diterima` with app = **`Termux:API`** (the notification comes from `com.termux.api`,
  never from `Termux`).
- **Isolate the actuator when testing:** `termux-battery-status` proves Termux:API is alive, but in the
  MacroDroid round send the notification **only** — no `termux-vibrate`. Then a buzz can only have come
  from MacroDroid. Put the clock in the title (`KETUA-UJI-21:18:58`) so both sides point at one event.
- No `ss`/`netstat` on this Termux build: probe a listener with
  `curl -s -m 2 -o /dev/null -w "%{http_code}" http://127.0.0.1:<port>/` — `000` means nothing listens.

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
10. **Exit 0 from `termux-toast` / `termux-wake-lock` proves nothing on its own.** Both are local
    scripts; with `com.termux.api` absent the toast broadcast goes nowhere
    (`Broadcast sent without waiting for result`). Prove the wake lock via the `TermuxService` log
    line, not the exit code.
11. **`dumpsys power` / `deviceidle` / `activity` and `settings get` are all denied for app uid**
    (missing `DUMP`, `INTERACT_ACROSS_USERS`). Battery whitelist status cannot be verified without
    adb — report "tidak dapat disahkan", never "tidak di-whitelist".
12. **A short logcat buffer silences real kills.** `logcat -d` main can hold ~5k lines (minutes)
    while `crash` keeps days. Absence of `phantom` / `lmk` / `am_kill` lines is not proof of no
    kill; check the buffer's first line before concluding.
13. **`pm list packages` is a filter, not an inventory.** Across a session it showed 271 packages
    while missing a just-installed app; `am start` then reported "Activity class does not exist".
    Before telling a user "belum dipasang", add `/sdcard/Android/data/<pkg>` existence and a logcat
    grep; for certainty pair ADB (`pm list` as shell uid is unfiltered).
14. **`~/.termux/boot/` existing is NOT proof that Termux:Boot is installed.** Measured 2026-11-11:
    the folder held `10-hermes-gateway.sh`, yet `pm list packages com.termux.boot` was empty and
    `pm list packages | grep -i termux` showed only `com.termux`. A previously-created boot script therefore looked like a
    working auto-start while nothing ran at boot. Always gate the claim on `pm list packages
    com.termux.boot` (or `/sdcard/Android/data/com.termux.boot`), never on the folder.
15. **Do not hand the user a shell command when a one-tap affordance is possible.** For add-on APKs
    the deliverable is: APK downloaded, installer intent fired, illustrated steps in the UI, and a
    status chip that flips to TERPASANG after they tap. Re-read the status *after* they say they
    tapped — `installed: false` a minute later means the dialog never appeared (or they dismissed it),
    and the honest reply is "dialog tak muncul, cuba buka melalui app Files".
16. **A file you downloaded with `curl` is invisible to the user's file manager.** Termux-created
    files are not registered in MediaStore, and Files by Google / HyperOS Downloads list MediaStore,
    not the directory — measured: `ls -l /storage/emulated/0/Download/TermuxBoot.apk` → 26,000 bytes,
    while the user saw only `hermes-apk/TermuxApi.apk`. `am broadcast -a
    MEDIA_SCANNER_SCAN_FILE -d file://…` prints "Broadcast sent" and indexes nothing (no-op since
    Android 10). Fix by copying the APK into a folder the user has already browsed successfully
    (`cp … /storage/emulated/0/Download/hermes-apk/`), or install with `adb install -r`. Never answer
    "cuba refresh".
17. **"Dialog tak keluar" needs a state check, not a retry loop.** Four launch strategies were fired
    in one call (`termux-open`, `am start file://`, SAF + `--grant-read-uri-permission`, 
    `INSTALL_PACKAGE` + SAF); three exited 0 and the SAF `VIEW` form raised
    `java.lang.reflect.InvocationTargetException` through termux-am — yet `pm path com.termux.boot`
    stayed empty, so no dialog was ever accepted. Report per-strategy exit codes *and* the package
    state, then split the cause: file not visible in the file manager (pitfall 16) vs install blocked
    vs code/permission missing for the add-on.
18. **Two failed menu-path guesses in a row = ask for a screenshot, stop enumerating.** `screencap`
    from Termux fails (`Failed to take take screenshot. Capturing failed.`) and `settings get` is
    denied, so you are blind to the very screen you are describing. When the user answers "tak ada ⋮"
    then "ketuk tulisan tu pun cuma tutup-buka suis", a third Settings path is guesswork that burns
    their patience — ask for a `power + vol-down` screenshot instead (vision reads it next turn), and
    say plainly that the 6-digit code exists only on their screen: they read it, you `adb pair` it.
19. **Pre-pairing state, proven without ADB:** `getprop | grep -i adb` (`init.svc.adbd: stopped`,
    `ro.adb.secure: 1` ⇒ a pairing code is required) plus a loopback Python scan of ports
    30000–50000 on `127.0.0.1`: one open port + `adb connect 127.0.0.1:<port>` → `offline` proves
    wireless debugging is ON and merely unpaired; a second open port means the pairing dialog is open.
    Details: `references/hyperos-settings-component-discovery.md`.

20. **A MacroDroid `Kekangan` (constraint) of type `Alamat IP` set to `127.0.0.1:<port>` disables the
    macro forever, silently.** Loopback is never the device's own address, so the condition is never
    true: no error, no toast, no log line the user can see. Pasted template junk
    (`127.0.0.1:18080{model}{mode}`) is the usual cause. Read the green bar aloud and have it deleted
    before diagnosing anything else — the trigger may be perfectly fine.
21. **Never test a bridge with two actuators live at once.** Termux:API can vibrate on its own
    (`termux-vibrate`), so firing it in the same round as the MacroDroid notification makes the buzz
    meaningless — you cannot attribute it. Run the Termux:API round first, then a
    notification-**only** round, and say in the report which actuator you deliberately suppressed.
22. **A `trigger.macrodroid.com` 404 is a registration answer, not a network or encoding bug.**
    Measured 2026-11-11: `GET`/`POST` on `/hello%20world` (plus `+`, `_`, `helloworld`, case
    variants) all returned `{"error":"Not found"}` while the domain answered fine — so the URL was
    well-formed and the server simply had no `(device-id, identifier)` pair registered. Do not
    iterate encoding variants for more than one attempt each; walk the state ladder instead
    (macro saved ✓ → switch ON → identifier text identical → at least one `Tindakan`). Having the URL
    on screen proves nothing: the app renders it client-side before the macro is saved. Also note the
    cloud URL needs Google Play services + FCM, so `200` means *queued*, never *acted*.

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
- `references/background-survival-diagnostics.md` — kill vs Doze-sleep vs service-restart decision
  table, app-uid denial matrix (`dumpsys` / `settings` / `dmesg`), logcat buffer spans, wake-lock
  proof line, runit crash-loop and orphan checks, HyperOS battery/autostart menu paths, adb-only
  fixes.
- `references/apk-install-and-signature-checks.md` — signature recipe, known fingerprints,
  visibility evidence, install-path decision table.
- `references/wireless-pairing-walkthrough.md` — 11-step Settings→done script for a phone you do
  not hold, two-ports/console-field table, failure→cause table, delivery rules for non-technical
  users.
- `references/apk-visibility-and-portless-pairing.md` — why a `curl`-ed APK is missing from the
  user's Files app (MediaStore indexing, no-op scanner broadcast) with the three working handoffs,
  the port-less pairing ladder and its three distinct error verdicts, and the diagnostic set that
  separates "download bad" / "install blocked" / "file not visible".
- `references/hyperos3-pairing-code-location.md` — "kod 6 digit di mana?": loopback nmap listener probe
  (1 open port vs 2 = pairing dialog closed/open), Settings-APK string proof that the pairing dialog
  exists on the build, `am start … WirelessDebuggingFragment` to open the screen for the user, HyperOS 3
  switch-vs-row-text trap, ⋮ overflow and Settings-search fallbacks.
- `scripts/adb-pair-scan.py` — scan 30000–50000 and `adb pair` each open port when the user supplies
  only the 6-digit code; prints BERJAYA/gagal per port and connects on success.
- `references/macrodroid-bridge-and-actuator-isolation.md` — using MacroDroid as a free
  tap/vibrate/screenshot bridge when ADB pairing is blocked: Malay UI label map (Pencetus / Tindakan /
  Kekangan), **cloud webhook facts** (`https://trigger.macrodroid.com/<device-id>/<identifier>`, FCM
  delivery, query params only fill existing variables, one-identifier-per-command design) with the
  HTTP `200`/`404`/`000` verdict table and the 404 state ladder, premium Webhook vs free
  `Pemberitahuan diterima` (`Termux:API` as source app), the actuator-isolation test protocol,
  per-port `curl %{http_code}` listener probe when `ss`/`netstat` are absent, and the silent
  IP-constraint trap.
- `references/hyperos-settings-component-discovery.md` — when the pairing row simply is not on the
  screen: `aapt dump xmltree` fails ("resource table is invalid/corrupt") so enumerate Settings
  components with a Python UTF-16LE string-pool scan; the AOSP component names that do **not** exist
  on HyperOS; `-e` (not `-d`) for `:settings:show_fragment`; `screencap`/`settings get` denials; the
  loopback 30000–50000 port scan that proves "wireless debugging ON but unpaired" without a user
  question; and the two-guesses-then-ask-for-a-screenshot rule.
