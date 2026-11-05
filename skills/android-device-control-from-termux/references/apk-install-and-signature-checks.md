# APK verification & install paths (Termux, no root)

## 1. Verify the APK is genuine before telling the user to install it

```bash
cd ~/storage/downloads
curl -sSL -o F-Droid.apk https://f-droid.org/F-Droid.apk
sha256sum F-Droid.apk
python3 -c "import zipfile;z=zipfile.ZipFile('F-Droid.apk');print('zip OK',len(z.namelist()))"

# v1 signature block -> signer certificate
python3 -c "import zipfile;print([n for n in zipfile.ZipFile('F-Droid.apk').namelist()
  if n.upper().endswith(('.RSA','.DSA','.EC'))])"
unzip -o -q F-Droid.apk 'META-INF/*.RSA' -d sig
openssl pkcs7 -inform DER -in sig/META-INF/*.RSA -print_certs -noout -text | grep -E "Subject:|Issuer:"
openssl pkcs7 -inform DER -in sig/META-INF/*.RSA -print_certs | openssl x509 -noout -fingerprint -sha256
```

Known SHA-256 certificate fingerprints seen in practice:

| App | Fingerprint | Subject |
|---|---|---|
| F-Droid (official) | `43:23:8D:51:2C:1E:5E:B2:D6:56:9F:4A:3A:FB:F5:52:34:18:B8:2E:0A:3E:D1:55:27:70:AB:B9:A9:C9:CC:AB` | CN=Ciaran Gultnieks |
| Termux apps (Termux, Termux:API) | `22:8F:B2:CF:E9:08:31:C1:49:9E:C3:CC:AF:61:E9:6E:8E:1C:E7:07:66:B9:47:46:72:CE:42:73:34:D4:1C:42` | Termux project key |

F-Droid publishes its APK signing fingerprint; matching it is the strongest offline check.
`aapt dump badging <apk>` gives `package: name=… versionCode=…` for the content check.
Modern APKs may carry only v2/v3 blocks (no `.RSA` in META-INF) — then unzip-based
verification is unavailable without `apksigner`, and the SHA-256 of the file plus the
publisher's published hash is the fallback.

## 2. Install path decision table

| Situation | Do this |
|---|---|
| `adb` paired | `adb install -r <apk>` — silent, prints `Success` |
| No adb, user can tap | `buka apk <apk>` → user taps the file in Files → Install |
| "Install blocked / unknown sources" | allow “Install unknown apps” for the **file manager**, not Termux |
| `termux-open x.apk` exits 0, nothing happens | expected: Termux has no `REQUEST_INSTALL_PACKAGES` |
| Play Store app | impossible programmatically; `buka play "<name>"` only opens the listing |

## 3. Why `termux-open` is a dead end for APKs

```bash
apk=$(pm path com.termux | head -1 | sed 's/package://')
aapt dump permissions "$apk" | grep -i INSTALL   # -> (no output)
aapt dump permissions "$apk" | grep -c uses-permission   # ~13, none for install
```

Without the manifest permission, Android's PackageInstaller never shows a dialog; the intent is
dropped silently and the command still exits 0. Also `file://` URIs have been blocked since
Android 7 (FileUriExposure), so `am start -a VIEW -d file://…apk` cannot substitute.

## 4. Package-visibility evidence (why `pm list packages` cannot be trusted alone)

On a device with Termux targetSdk 37:

- `pm list packages | grep -c fdroid` → `0` even after the user installed it in some cases,
  because the package is outside Termux's visibility set.
- `pm path <pkg>` → empty for invisible packages.
- `am start -n <pkg>/<activity>` → `Error type 3 … Activity class does not exist`, which reads
  like "not installed" but can also mean "not visible".
- `ls -d /sdcard/Android/data/*<name>*` → only appears after the app has actually been launched.
- The truth is only available as shell uid: `adb shell pm list packages | grep <pkg>`.

So: when the user says "it's installed now", do not argue from `pm list`; either say the check is
inconclusive from Termux, or pair ADB and check as shell.
