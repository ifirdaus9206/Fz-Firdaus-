---
name: termux-launch-apps-am-start
description: Buka app Android dari Termux dengan am start.
---

# Lancar app Android dari Termux (am start)

## Bila guna
- Telefon tanpa root, ADB pairing mustahil, `input tap` disekat (`INJECT_EVENTS`).
- Perlu buka app / URL / halaman Tetapan dari Termux, cron, atau konsol web.
- MacroDroid ada tetapi trigger broadcast tidak boleh dipercayai.

## Fakta penting (Android 11+)
1. `am start` **berfungsi** dari Termux; `am broadcast` berfungsi; `input` disekat.
2. `am start -a MAIN -c LAUNCHER -p <pkg>` GAGAL "unable to resolve Intent" kerana
   **package visibility** — app lain tidak kelihatan.
3. Penyelesaian: **explicit component** `am start -n pkg/Activity`. Nama salah →
   `Error type 3 ... does not exist`.
4. `pm dump`, `cmd package resolve-activity`, `dumpsys`, `wm size`, `screencap`
   disekat untuk app biasa — jangan bergantung padanya.
5. Nama activity digali dari APK: `pm path <pkg>` → baca `AndroidManifest.xml` (AXML)
   dan ekstrak rentetan UTF-16LE berakhir `Activity`.

## Langkah
1. Senarai pakej: `pm list packages` (`-3` untuk app pihak ketiga).
2. `pm path <pkg>` → baris pertama `base.apk`.
3. Ekstrak calon activity:
   ```python
   import zipfile, re
   d = zipfile.ZipFile(apk).read("AndroidManifest.xml")
   pat = re.compile(rb'(?:[\x20-\x7e]\x00){5,}')
   names = set()
   for m in pat.finditer(d):
       s = re.sub(r'^[^A-Za-z]+', '', m.group(0).decode("utf-16le", "ignore"))
       s = re.sub(r'[^A-Za-z0-9_.]+$', '', s)
       if s.endswith("Activity") and "/" not in s and 6 < len(s) < 120:
           names.add(s if "." in s else pkg + "." + s)
   ```
   AXML simpan panjang rentetan pada bait pertama — buang aksara bukan-huruf di
   hadapan, jika tidak nama activity rosak dan semua cubaan gagal.
4. Susun calon: `MainActivity`/`LauncherActivity` → `*Launcher*` → `Main*` →
   `*Splash*` → `*Home*` → lain-lain.
5. Cuba `am start -W -n pkg/cls`; berjaya jika tiada `Error type 3` dan ada
   `Status: ok` atau `Starting:`.
6. Simpan yang berjaya dalam cache JSON (`~/.cache/buka.json`).

## Skrip siap pakai
`~/bin/buka` (Python 3, tiada dependensi):
```
buka chrome | buka claude | buka set | buka home | buka url https://…
buka senarai whats      # cari pakej
```

## Perangkap
- APK **split** (AAB: Chrome, Claude, Grok): manifest dalam `base.apk`, tetapi nama
  activity tidak ikut pola biasa (Chrome: `com.google.android.apps.chrome.Main`,
  Grok: `ai.x.grok.main.GrokActivity`). Tambah peta `SPECIAL[pkg]` untuk kes ini.
- Jangan cedok nama activity dari internet tanpa uji — versi berubah.
- `am start` tidak boleh mengetuk dalam app; ketukan perlukan kebolehcapaian.
- HyperOS: app sideload dikawal "Tetapan Terhad" (Play Store tidak). Pilihan
  "Benarkan tetapan terhad" di hujung halaman Info apl, bukan dalam menu ⋮.

## Integrasi konsol web 8787 (FastAPI)
Rujuk `hermes-console/tools/patch_bukatab.py`:
- `GET /api/buka` → senarai app + butang tetap
- `POST /api/buka` `{target}` atau `{url}`
- POST perlu header `X-Console-Token` (CSRF dari `GET /api/meta`)

## Pengesahan
```
~/bin/buka chrome   → OK com.android.chrome/com.google.android.apps.chrome.Main
curl -s http://127.0.0.1:8787/api/buka | head -c 200
```
App mesti kelihatan terbuka pada **skrin telefon**, bukan pada klien Telegram/PC.
