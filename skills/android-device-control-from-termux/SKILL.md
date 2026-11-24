---
name: android-device-control-from-termux
description: Control Android apps, APKs, and UI from Termux.
version: 1.4.0
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

### When `aapt`, `pm dump` and `resolve-activity` are all blocked

Guessing activity names is expensive: measured 2026-11-20, seven guesses for MacroDroid
(`MainActivity`, `.ui.MainActivity`, `.ui.home.HomeActivity`, `.MacroDroidActivity`,
`.SplashActivity`, `.macro.MacroListActivity`, `.activities.MainActivity`) all returned
`Error type 3 — Activity class … does not exist`, while the real one was `.LauncherActivity`.
`pm path <pkg>` still works, and the APK is world-readable, so read the manifest yourself:

```bash
python3 scripts/apk-activities.py com.arlosoft.macrodroid            # list candidates
python3 scripts/apk-activities.py com.arlosoft.macrodroid --start    # + launch validation
python3 scripts/apk-activities.py <pkg> --keys extra_ macro guid     # extra key names (dex)
```

Two details that decide whether the scan works:

- **Scan both encodings of the AXML string pool.** AndroidManifest.xml is binary; string runs
  appear as UTF-16LE *and* as plain 8-bit runs. Decoding only one way yields offset garbage
  (`!.homescreen.NewHomeScreenActivity`, `$com.termux.api`) that looks almost right. Taking the
  union of `[\x20-\x7e]{6,}` and `(?:[\x20-\x7e]\x00){6,}` gave 968 usable strings.
- **Validate by launching, and read the LAST line.** `am start -n pkg/.Name` prints
  `Starting: Intent {…}` first even for a component that does not exist, then
  `Error type 3` / `Error: Activity class … does not exist` and exits 2. Grepping `head -1` makes
  every wrong name look like a success.

Same technique mines `classes*.dex` for extra/config key names (`macroGuid`,
`quick_run_macro_guids`) when an activity needs an extra you do not have.

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

### Background activity launches are dropped silently (BAL, Android 10+)

Measured 2026-11-22 (HyperOS 3 / A16, console in the phone's own Chrome): `buka notes` from a
Termux background process printed `pakej: com.miui.notes` + `OK (cache) … SnsEditActivity` and
exited 0, while the screen stayed on Chrome — three apps in a row "succeeded" and none appeared.
In the same window `am start -a android.settings.SETTINGS` *did* open Settings. So the split is:
system activities pass, **third-party app launches from a background caller are silently
cancelled** (no `Error`, no log line, exit stays 0). `am start -W` does not detect it either.

What the agent cannot verify is the phone screen — say so and have the owner look at the
**device**, not at the chat client (a Telegram/PC client shows nothing, which reads as "tak
jalan"). Reporting `OK · exit 0` as success is the round-burner here; report "intent dihantar,
skrin belum berubah".

Candidate remedies, one of which is now **confirmed** (2026-11-22, same HyperOS 3 device):
(a) grant Termux *Paparan di atas apl lain* / `SYSTEM_ALERT_WINDOW` — on this Play build the
toggle is **absent** from both `Info apl` and `Kebenaran lain` (the user was walked through
`Notifikasi` by mistake, then `Kebenaran lain`: nothing), so treat it as unavailable instead of
sending the owner hunting;
(b) **let MacroDroid perform the launch — VERIFIED WORKING.** A macro `BUKA NOTA` with
`Pencetus: Intent Diterima → com.ketua.OPEN.NOTES` and exactly one action
`Lancar Aplikasi: Nota` opened Mi Notes from `am broadcast -a com.ketua.OPEN.NOTES`, while
`buka notes` (`am start` of the resolved activity) had failed silently minutes earlier in the
same session. One macro per app, unique action string per app (`com.ketua.OPEN.<APP>`); the
accessibility service must be on and past `Tetapan Terhad` (see
`references/hyperos-restricted-settings-accessibility.md`). Recipe, AI prompt template and the
`Lancar null` trap: `references/macrodroid-launch-application-bridge.md`;
(c) have Termux itself in the foreground when the button is pressed (untested).
Design consequence: **Termux is the brain, MacroDroid is the hands.** Anything that must move the
screen belongs in a `Lancar Aplikasi` action, not in `am start`.

### Expose the launcher as a console tab (users press, they do not type)

`hermes-console/tools/patch_bukatab.py` (additive, idempotent, backs up three files) adds a **BUKA**
tab: `GET /api/buka` → third-party packages + fixed buttons (`home`, `set`), `POST /api/buka`
`{target}` or `{url}` → runs `~/bin/buka` and returns `{ok, exit, out}`. Two gotchas: POST must carry
`X-Console-Token` from `GET /api/meta` (CSRF middleware rejects otherwise), and the new tab needs
both the `data-tab` button in `index.html` and an entry in the tab-title map in `app.js`. Verify with
`sv restart hermes-console`, `curl /api/buka`, and `node --check static/app.js`.

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

**Component map, measured 2026-11-20 (HyperOS 3 / Android 16, Play build):**

| Component | Behaviour |
|---|---|
| `com.arlosoft.macrodroid.LauncherActivity` | exported, launches with rc=0 — use this to open the app for the user |
| `com.arlosoft.macrodroid.ShortcutDispatchActivity` | exported, starts, but needs a `macroGuid` extra (keys `macroGuid` / `macro_guid` / `quick_run_macro_guids` in `classes*.dex`) that lives in app-private storage |
| `com.arlosoft.macrodroid.SelectForceRunMacroActivity` | **not exported** → `SecurityException` from `am start` |

**Isolate trigger vs action before claiming a bridge works.** `am broadcast -a <action>` (plain,
`-p <pkg>`, `-f 32`, or both) always answers `Broadcast sent without waiting for result` — that is
the wrapper acknowledging the call, not MacroDroid receiving it. On this build all four variants
produced no visible effect while the macro looked correct (`Intent Diterima` + one `Mesej Popup`
action, 0 constraints). Order of proof:

1. `▶ Test` inside the macro edit screen — does the action fire at all?
2. Trigger → `Pintasan Dilancarkan` (shortcut) — does the *action* work when launched locally?
3. Only then the intent/broadcast trigger.

A background `Toast` is a bad test action: Android 11+ drops toasts from background apps, so the
in-app "ujian berjaya" and the absence of a toast tell you nothing. Use **`Lancar Aplikasi` →
`Tetapan`** (or `Lancar Skrin Utama`) instead — Settings/home appearing on screen is unambiguous.

**But do not conclude "needs no accessibility service".** Measured 2026-11-21: with the
accessibility service still locked (`Dikawal oleh Tetapan Terhad`), a macro whose only action was
`Lancar Skrin Utama` fired nothing at all, while `am start -a android.settings.SETTINGS` from Termux
opened Settings in the same minute. MacroDroid routes `Lancar Aplikasi` / `Lancar Skrin Utama`
through the accessibility service to bypass the Android 10+ background-activity-launch block, so
without it they fail **identically to a dead trigger**. Version proof: after the restricted-settings
unlock + service ON, the same macro ran and the screen changed on the user's own test.

Fastest local test that needs no broadcast at all: **long-press the action row → `Uji tindakan` /
`Uji tindakan dari sini`** (per-action) — a menu with `Konfigurasi`, `Uji tindakan`, `Uji tindakan
dari sini`, `Tambah label`, `Potong`, `Salin`, `Tampal`, `Ekstrak ke Blok`, `Padam`, `Lumpuhkan`.
`Uji tindakan dari sini` runs that one action in place, which separates action-vs-trigger in a single
tap. `Padam` in the same menu is also the only reliable way to delete an action — there is no trash
icon on the macro screen (`+` and the clipboard icon are all the header offers).

So the independent control is: `am start -a android.settings.SETTINGS` from Termux. If that works but
the macro's launch does nothing, the break is on the MacroDroid side — check accessibility state
(`references/hyperos-restricted-settings-accessibility.md`) before touching the trigger.

**MacroDroid's AI builder is usable only with a strict prompt — and only if the saved rows are read
back.** The owner may explicitly ask for it ("guna macrodroid LLM, lebih cepat, bagi arahan betul"):
comply, but send a prompt that names the **package**, says *exactly ONE action*, and forbids
`Run Macro` / `UI Interaction` (template:
`references/macrodroid-launch-application-bridge.md`), then verify the literal row text
(`Lancar <app>`, never `Lancar null`). Without those three constraints the AI produces macros that
look finished and do nothing. Measured 2026-11-21: asked for
`Intent Diterima com.ketua.TAP` + Toast + a UI-interaction tap at 540/1200, the AI's chat reply claimed
it had added the tap, while the saved `Tindakan` list contained only
`1. Mesej Popup` and `2. Jalankan Makro → <the same macro>` — a **self-call instead of any tap**, so
nothing on screen could ever move. The AI also silently omitted the accessibility caveat into a note
instead of a real action. Read the action rows, never the AI's prose.

**Rebuild protocol when the macro must be deleted and remade by the user** (they will do it by hand,
so make divergence impossible to miss):

1. Delete the old macro first and say the list must show no macro with that name.
2. New empty macro (`Makro Kosong`, not AI), exact name, e.g. `TAP UJIAN`.
3. `Pencetus` → search `intent` → `Intent Diterima`, Action typed exactly (`com.ketua.TAP`), other
   fields untouched. Expect `Pencetus: 1`.
4. `Tindakan` → search `lancar` → `Lancar Aplikasi` → `Tetapan`. Expect `Tindakan: 1` and a row that
   reads `Lancar Aplikasi: Tetapan`.
5. Only then fire `am broadcast`; add the UI-tap action last, after the launch proof passes.

**The Malay action name for a tap is not `Sentuh`.** Searching `sentuh` returns exactly one hit —
`Sekat Sentuhan Skrin` (Block Screen Touches) — and users read that as "the tap action is missing".
Measured label path on MacroDroid 6.1.5 / Malay:

```
Carian "interaksi"  → Interaksi UI            (the action you want)
  Interaksi UI → Pilih Opsyen:
      Klik · Klik lama · Klik kanan · Salin · Potong · Tampal ·
      Kosongkan pilihan · Gerak isyarat · Jujukan Gerak Isyarat ·
      Tekan Enter · Cubit Zum · Putar Dua Jari
  Klik (radio) → OK → choose the coordinate target
      Koordinat Skrin / X/Y Coordinates   (NOT "Pilih Elemen")
  X = 540 · Y = 1200 → OK → Save
```

`Klik` = tap, `Klik lama` = long-press. Confirm by finding the coordinate mode first — the X/Y fields
only appear after it is selected — and read the saved row back (it must say the coordinates, not
`Lancar Skrin Utama`).

**The coordinate dialog is where taps silently go wrong (measured 2026-11-22, 1280×2772).** The
`Lokasi X,Y` screen has `Piksel` / `Peratusan` radios, a `Tunjukkan lokasi sentuhan` checkbox, a
`Togol tindakan lokasi sentuhan` button and prints `Resolusi skrin: <w>, <h>` — that line is the only
free way to learn the device resolution from the phone screen. Two failure modes seen live:

- Default is **`Piksel`**. With `X=50, Y=75` the tap lands 50 px from the left / 75 px from the top —
  the status bar. MacroDroid still reports the tap as successful, so \"ketukan berjaya\" + no visible
  change means *wrong coordinate mode*, not a broken action.
- A leftover action **above** the tap (`Lancar Skrin Utama`) fires first, so the tap lands on the home
  screen and the user reports \"dia keluar pergi menu utama\". Make them delete it and confirm
  `Tindakan` drops from 2 → 1 before any test.

Ask for `Peratusan` + `Tunjukkan lokasi sentuhan` ticked, then X/Y as percentages (e.g. `50` / `78` =
bottom centre, relies on no resolution knowledge). With the circle shown, one screenshot answers
\"did it tap where we meant\" without ADB.

`am start -a android.intent.action.MAIN -c android.intent.category.HOME` opens the launcher from
Termux, which gives a neutral, predictable screen for a tap test (dock icons open on a hit; empty
desktop means the coordinate missed).

One step per message, ends with "balas **N siap**", then wait. Before diagnosing anything, **read the
macro title in the next screenshot** — a session where the user re-opened the old macro (`Ujian Tap`,
single `Mesej Popup`) and did step 4 on it burned two rounds; the giveaway is a name that does not
match the one you asked for and a `Tindakan` count of 1 with the wrong action type. Say which macro the
screenshot shows and ask for the macro **list** (names + toggle colours) before continuing.

**Control test first when one macro fires and its twin does not (measured 2026-11-22).** With the
same shape (`Intent Diterima com.ketua.OPEN.<APP>` + one `Lancar Aplikasi`), `BUKA NOTA` opened Mi
Notes from `am broadcast` twice, while `BUKA CLAUDE` (visually identical, `Lancar Claude — Paksa
baru`, 0 constraints) did nothing — and the owner reported the same macro *does* open Claude when he
presses `▶ Test`. So the trigger path was healthy and the fault was per-macro/per-app. Ladder that
settles it in two rounds instead of ten:

1. Fire the **known-good** macro and the suspect macro ~10 s apart in one call
   (`am broadcast -a com.ketua.OPEN.NOTES; sleep 10; am broadcast -a com.ketua.OPEN.CLAUDE`) and ask
   which won. "Nota buka, Claude tak" = not a bridge problem — stop touching the trigger.
2. Then compare the two macros side by side: **toggle colour in the macro list** (a manual `▶` test
   still runs a macro that is switched off, an external broadcast does not), and whether the target
   app was ever opened since boot (HyperOS pauses unused apps; opening it once un-freezes it).
3. Only if both are identical, suspect the app itself (`Paksa baru` vs normal launch, deep link,
   hibernation/battery restriction) — not `Intent Diterima`.

Report the split ("pencetus berfungsi, app X sahaja gagal") instead of restating "tak jalan".

## `RUN_COMMAND` intent — verify build provenance before promising it

`RUN_COMMAND` is Termux's official "another app asks Termux to run a shell command" channel — the
tempting BAL bypass (MacroDroid/our own APK triggers it, Termux runs `~/bin/buka <app>`). It has
**four** preconditions, and three of them are invisible when missing:

1. `~/.termux/termux.properties` contains `allow-external-apps = true` **on its own line**.
2. `termux-reload-settings` is called afterwards (the running app caches properties).
3. The sending app holds `com.termux.permission.RUN_COMMAND`.
4. **The installed Termux build permits it** — Play-Store builds disable the receiver; F-Droid/GitHub
   builds enable it.

Probe the build *first*, because a silent failure looks identical to a mis-typed extras bundle:

```bash
pm list packages -i | grep com.termux      # installer=com.android.vending → Play build → give up
grep -n 'allow-external-apps' ~/.termux/termux.properties && tail -3 ~/.termux/termux.properties
```

Shape of the broadcast (use a **side effect** as the proof, never the command's own output):

```bash
am broadcast --user 0 -a com.termux.RUN_COMMAND \
  --es com.termux.RUN_COMMAND_PATH /data/data/com.termux/files/usr/bin/touch \
  --esa com.termux.RUN_COMMAND_ARGUMENTS '/data/data/com.termux/files/home/rc_probe' \
  --ez com.termux.RUN_COMMAND_BACKGROUND true
sleep 4; ls -l ~/rc_probe        # the ONLY evidence it ran
```

`Broadcast sent without waiting for result` is printed by the wrapper regardless of whether anything
received it — treat it as "nothing proven". Measured 2026-11-24 on this Play-signed build: property
set, reload sent, three broadcast variants (plain, `-p com.termux`, `touch`), **no probe file** →
the receiver never acted. Report that as "belum berjaya, punca paling mungkin build Play" and check
provenance before spending more rounds. Do not present RUN_COMMAND as a working BAL workaround until
a probe file appears; MacroDroid `Lancar Aplikasi` remains the verified actuator (Step 7).

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

23. **The first line of `am start` output is not the verdict.** `Starting: Intent {…}` is printed
    before the platform resolves anything; the truth (`Error type 3` /
    `Error: Activity class … does not exist`) comes last and the command exits **2**. A loop that
    piped through `head -1` reported four of four MacroDroid components as launched when all four
    were missing — and that wrong "it started" reached the user. Always read the last line plus
    `rc`, e.g. `out=$(am start -n "$c" 2>&1); rc=$?; printf '%s | rc=%s\n' "$(printf '%s' "$out" | tail -1)" "$rc"`.

24. **Termux's `am` wrapper rejects the two flags that would fix BAL and background delivery.**
    Measured 2026-11-22:
    `am broadcast --receiver-include-background` → `Error: Unknown option`,
    `am start --allow-background-activity-starts` → `Error: Unknown option` (both exist in
    `/system/bin/am`, which needs shell uid you do not have). Do not spend rounds hunting flags —
    route screen-moving work through MacroDroid actions instead. Related: `systemctl`-style flag
    guesses (`-f 0x…`, `-p <pkg>`) are accepted by the wrapper yet change nothing.

25. **Inside `execute_code`, shelling out is not available.** `subprocess.run(...shell=True)` fails
    with `PermissionError: … /usr/bin/sh`, and `pm path <pkg>` run via `subprocess.run(["pm", …])`
    returns empty output even when the package is installed. Do the shell step with the `terminal`
    tool, then feed the resulting literal path to the Python parser (that combination read
    MacroDroid's 91 MB APK fine).

26. **`>>`-appending to `~/.termux/termux.properties` can silently corrupt the last line.** The file
    often ends without a trailing newline, so `echo 'allow-external-apps = true' >> …` produced
    `extra-keys = [[…]]allow-external-apps = true` — one broken line, and the setting never existed.
    Fix by writing through Python with an explicit `\n`, then read `tail -3` back before trusting it:
    ```bash
    python3 - <<'EOF'
    p='/data/data/com.termux/files/home/.termux/termux.properties'
    s=open(p).read().replace("]]allow-external-apps", "]]\nallow-external-apps")
    if 'allow-external-apps' not in s: s = s.rstrip()+"\nallow-external-apps = true\n"
    open(p,'w').write(s)
    EOF
    termux-reload-settings
    ```
    Same habit applies to any Termux config the app parses line-by-line (`.bashrc`, `boot/*.sh`): a
    merged line is accepted silently and the feature just never turns on.

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
- `scripts/apk-activities.py` — enumerate an APK's activities/receivers/services and its
  `extra_*`/`*guid*` keys by string-scanning the binary AndroidManifest and `classes*.dex` when
  `aapt` / `pm dump` / `cmd package resolve-activity` are all denied; `--start` validates each
  candidate with `am start` and only a missing `Error type 3` counts as existing.
- `references/macrodroid-bridge-and-actuator-isolation.md` — using MacroDroid as a free
  tap/vibrate/screenshot bridge when ADB pairing is blocked: Malay UI label map (Pencetus / Tindakan /
  Kekangan), **cloud webhook facts** (`https://trigger.macrodroid.com/<device-id>/<identifier>`, FCM
  delivery, query params only fill existing variables, one-identifier-per-command design) with the
  HTTP `200`/`404`/`000` verdict table and the 404 state ladder, premium Webhook vs free
  `Pemberitahuan diterima` (`Termux:API` as source app), the actuator-isolation test protocol,
  per-port `curl %{http_code}` listener probe when `ss`/`netstat` are absent, and the silent
  IP-constraint trap.
- `references/macrodroid-launch-application-bridge.md` — **verified** BAL bypass: one macro per app
  (`Intent Diterima com.ketua.OPEN.<APP>` + `Lancar Aplikasi`), action-string/package table,
  MacroDroid-AI prompt template in English, and the two AI failure modes that look complete but do
  nothing (`Jalankan Makro` self-call, `Lancar null`).
- `references/hyperos-restricted-settings-accessibility.md` — `Dikawal oleh Tetapan Terhad`: why every
  accessibility-dependent action (UI tap **and** `Lancar Aplikasi` / `Lancar Skrin Utama`) fails
  silently, `pm list packages -i` proof the app is Play-installed, the confirmed unlock location
  (`Info apl → Tetapan lanjutan → Benarkan tetapan terhad`), the `⋮`-menu dead end, the
  `SHOW_RESTRICTED_SETTING_DIALOG` intent, and the state reads that are denied for app uid.
- `references/hyperos-settings-component-discovery.md` — when the pairing row simply is not on the
  screen: `aapt dump xmltree` fails ("resource table is invalid/corrupt") so enumerate Settings
  components with a Python UTF-16LE string-pool scan; the AOSP component names that do **not** exist
  on HyperOS; `-e` (not `-d`) for `:settings:show_fragment`; `screencap`/`settings get` denials; the
  loopback 30000–50000 port scan that proves "wireless debugging ON but unpaired" without a user
  question; and the two-guesses-then-ask-for-a-screenshot rule.
