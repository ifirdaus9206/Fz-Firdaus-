# Why the user "cannot find" the APK you downloaded — and pairing with only a code

Two follow-ups that arrive right after the prepare-to-one-tap handoff (Phase "APK install reality").
Measured 2026-11-11 on HyperOS / Android 16, Play-signed Termux, Files by Google.

---

## 1. The file exists, the file manager does not show it

Report: *"di Files › Download › TermuxBoot nama ni tak ada, cuma ada termuxapi.apk saja"*.

Both statements were true at the same time:

```bash
ls -l /storage/emulated/0/Download/TermuxBoot.apk      # -rw-rw---- 26000 bytes  ← exists
find /storage/emulated/0/Download -iname '*termux*'
#   26000  …/Download/TermuxBoot.apk
#   3956196 …/Download/hermes-apk/TermuxApi.apk        ← the only one Files listed
```

Cause: files created by Termux through the shell land on the filesystem but are **not registered in
MediaStore**, and modern file managers (Files by Google, MIUI/HyperOS File Manager in "Downloads"
view) list **MediaStore**, not the raw directory. A file the user previously installed through the
browser/F-Droid is indexed; the one you just `curl`-ed is not.

`am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:///…` still prints
`Broadcast sent without waiting for result` and changes nothing (the scanner broadcast has been a
no-op since Android 10). Do not treat exit 0 as "indexed".

### What to do instead, in order

1. **Download/copy into a folder the user has already browsed successfully.** In this session
   `Download/hermes-apk/` was visible (it contained `TermuxApi.apk`), so a plain
   `cp …/Download/TermuxBoot.apk …/Download/hermes-apk/TermuxBoot.apk` gave the user a file they
   could actually tap. Prefer this over telling them to "refresh".
2. **`adb install -r <apk>`** once pairing exists — no file manager involved, and it is verifiable.
3. **A filesystem-browsing terminal** (`ls`, `cp` from Termux) proves the file to you, not to them;
   only use it as evidence in the reply, never as the user's path to the install.

Say which of the three you used. "Fail ada, tetapi Files tak nampak sebab ia ditulis oleh Termux dan
tidak didaftarkan dalam MediaStore" is an answer; "cuba refresh" is not.

## 2. Pairing when the user sends only the 6-digit code

The dialog shows `IP address & Port` **and** `Wi-Fi pairing code`, but users paste just the code
(*"saya rasa port kod 6 digit ini 482913 cuba test"*). The port is required by `adb pair`, and
`adb mdns services` is unsupported in the `1.0.41 / 35.0.2-android-tools` build. So scan for it.

`scripts/adb-pair-scan.py <code> [ip]` does: TCP-scan 30000–50000 in parallel (0.08 s timeout,
400 workers) → `adb pair ip:port <code>` on each open port → on success `adb connect` + `adb devices`.

### Reading the results (each message means something different)

| Output | Meaning |
|---|---|
| `error: protocol fault (couldn't read status message): Success` | not the pairing service — keep scanning |
| hangs, `timeout (kod mungkin tamat tempoh)` | pairing port found, but the code was rejected/expired |
| `Successfully paired to …` | done → immediately `adb connect <connect port>` |
| `adb connect` → device listed as `offline` | port is the wireless-debugging port but this host is not paired yet |

Other rules learned the hard way:

- **The code lives ~2 minutes.** A code the user typed even a few minutes ago always lands in the
  "hang" row. Ask for a *fresh* code and run the scan immediately; if it hangs, say the code expired
  rather than "pairing is broken".
- **Scan again before each attempt** — the open-port set changes (`[38972, 39097, 45278]` →
  `[39097]` → `[33998, 39097, 45314]` within minutes). Never reuse a port from an earlier scan.
- `adb kill-server` before a scan when the previous `adb connect` left a stale entry, and
  `adb disconnect <ip:port>` to clear `offline` rows so `adb devices` stays readable.
- One port usually survives every scan (39097 here) — it is the wireless-debugging service; the
  others are other apps' ephemeral ports. That is why the wrong ports answer with a protocol fault
  rather than a timeout.
- **State the honest end condition.** In this session pairing never completed (every code arrived
  expired), and the report said so: the scanner identified the pairing port deterministically, but
  success still needs a code delivered within its lifetime. Do not present the scan as a way to
  bypass the code or the user's taps.

## 3. Diagnostic that separates the three "nothing happened" cases

When no install dialog appears, one command set decides which story is true:

```bash
pm path <pkg>                     # empty → not installed (dialog never accepted)
ls -l <apk>                       # size/bytes → download fine?
python3 - <<'EOF'                 # valid APK? package + receiver + v2 signature
import zipfile, re
z = zipfile.ZipFile("/path/x.apk")
print(sorted({s for s in re.findall(r"[ -~]{6,}", z.read("AndroidManifest.xml").decode("utf-16-le","ignore")) if "termux" in s.lower()}))
print(b"APK Sig Block 42" in open("/path/x.apk","rb").read())
EOF
ls -l /storage/emulated/0/Download/  # file present where the user is looking?
```

Valid APK + empty `pm path` + file not visible in the file manager = the user could not have
installed it, whatever they tapped. Lead with that, then hand them the visible copy or ADB.
