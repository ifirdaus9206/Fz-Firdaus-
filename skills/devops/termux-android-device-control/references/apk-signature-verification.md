# APK download, signature verification and version probing (Termux)

Goal: you may download and stage an APK, but the human must tap Install. Your job is to prove the
file is the publisher's build before handing it over — a self-signed cert alone proves nothing.

## 1. Fetch and test integrity

```bash
mkdir -p ~/storage/downloads/hermes-apk && cd ~/storage/downloads/hermes-apk
curl -sSL -o F-Droid.apk https://f-droid.org/F-Droid.apk
ls -l F-Droid.apk && sha256sum F-Droid.apk
python3 -c "import zipfile; z=zipfile.ZipFile('F-Droid.apk'); print('zip OK', len(z.namelist()), 'files')"
```

`/sdcard` itself may refuse writes (scoped storage); `~/storage/downloads` works after
`termux-setup-storage`.

## 2. Extract the v1 signer certificate

```bash
unzip -o -q F-Droid.apk 'META-INF/*.RSA' -d sig
f=$(ls sig/META-INF/*.RSA | head -1)
openssl pkcs7 -inform DER -in "$f" -print_certs -noout -text | grep -iE 'Subject:|Issuer:' | head -4
openssl pkcs7 -inform DER -in "$f" -print_certs | openssl x509 -noout -fingerprint -sha256
```

Report `sha256 Fingerprint` **and** the subject CN.

If `META-INF/*.RSA` is missing the APK only carries v2/v3 signatures — then use
`apksigner verify --print-certs app.apk` (ships with android-tools in some builds) or say the
v1 chain is unavailable rather than inventing a fingerprint.

## 3. Known published fingerprints (reference values)

| Artifact | SHA-256 cert fingerprint | Subject |
|---|---|---|
| `org.fdroid.fdroid` (F-Droid 1.x) | `43:23:8D:51:2C:1E:5E:B2:D6:56:9F:4A:3A:FB:F5:52:34:18:B8:2E:0A:3E:D1:55:27:70:AB:B9:A9:C9:CC:AB` | `CN=Ciaran Gultnieks` (F-Droid founder) |
| `com.termux.api` 0.53.0 (Termux:API) | `22:8F:B2:CF:E9:08:31:C1:49:9E:C3:CC:AF:61:E9:6E:8E:1C:E7:07:66:B9:47:46:72:CE:42:73:34:D4:1C:42` | Termux project key |

Notes:
- Termux apps are signed with the **Termux key**, not the F-Droid key. `Termux:API` must come from the
  same distribution channel as the installed Termux app, otherwise the broadcast permission is not
  granted and every `termux-*` call fails.
- F-Droid publishes the APK signing fingerprint on its site; compare against that published value,
  not against this table alone (tables rot).
- Compare sha256 of the download only as a change-detector; it is not a signature.

## 4. Resolve the newest version without scraping HTML

```bash
curl -s https://f-droid.org/api/v1/packages/com.termux.api
# {"packageName":"com.termux.api","suggestedVersionCode":1002,
#  "packages":[{"versionName":"0.53.0","versionCode":1002}, ...]}
curl -sSL -o TermuxApi.apk https://f-droid.org/repo/com.termux.api_1002.apk
```

Pattern: `https://f-droid.org/repo/<packageName>_<versionCode>.apk`.
Fast facts from the APK: `aapt dump badging app.apk | head -3` → package, versionCode, versionName,
targetSdkVersion.

## 5. Hand over the install, then verify

```bash
termux-open F-Droid.apk          # system installer dialog
pm list packages | grep -c fdroid    # still 0 until the human taps Install
```

Never report "installed" from the download or from the installer opening. Re-check `pm list packages`
afterwards, and remember that package visibility can hide packages from Termux — if an expected API
works (e.g. `termux-battery-status` returns JSON) the companion app is present even when `pm list`
does not show it.

## What this proves / does not prove

- Proves: the APK was signed by the holder of that certificate, and the zip is intact.
- Does not prove: that the cert is the publisher's (that is what the published fingerprint comparison
  is for), or that the APK matches what the publisher serves today.
