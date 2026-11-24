# TERMUX `RUN_COMMAND` — Kajian & Ujian

**Tarikh:** 2026-11-24 · **Status:** **BELUM BERJAYA** dalam persekitaran kita

## 1. Apa itu

`RUN_COMMAND` ialah intent rasmi Termux yang membolehkan **app lain menyuruh Termux
menjalankan arahan shell** — tanpa perlu app itu ada terminal sendiri.

Contoh kegunaan: MacroDroid/Tasker (atau APK kita sendiri) menghantar intent →
Termux menjalankan `~/bin/buka whatsapp` → app dibuka.

Ini menarik kerana `am start` dari skrip **disekat BAL** pada peranti ini.

## 2. Keperluan

1. `~/.termux/termux.properties` mesti ada:
   ```
   allow-external-apps = true
   ```
2. App penghantar mesti pegang permission `com.termux.permission.RUN_COMMAND`
3. Termux mesti **build yang membenarkan** RUN_COMMAND
   (build Play Store **mematikan** ciri ini; build F-Droid/GitHub membenarkannya)
4. Termux mesti hidup (perkhidmatan berjalan)

## 3. Bentuk arahan

```bash
am broadcast --user 0 -a com.termux.RUN_COMMAND \
  --es com.termux.RUN_COMMAND_PATH /data/data/com.termux/files/usr/bin/bash \
  --esa com.termux.RUN_COMMAND_ARGUMENTS '-lc,ARAhan ANDA DI SINI' \
  --es com.termux.RUN_COMMAND_WORKDIR /data/data/com.termux/files/home \
  --ez com.termux.RUN_COMMAND_BACKGROUND true \
  --es com.termux.RUN_COMMAND_COMMAND_LABEL uji
```

## 4. Ujian yang dijalankan (2026-11-24)

| Langkah | Hasil |
|---|---|
| Tambah `allow-external-apps = true` | ✅ ditulis ke `~/.termux/termux.properties` |
| `termux-reload-settings` | ✅ dihantar |
| Broadcast `com.termux.RUN_COMMAND` (3 variasi: tanpa `-p`, dengan `-p com.termux`, guna `touch`) | ❌ "Broadcast sent without waiting for result" — **tiada fail bukti tercipta** |
| `pkg list-installed` | `termux-am 0.8.0` ada, `$PREFIX/libexec/termux-am/am.apk` ada |
| `dumpsys package com.termux` | tidak dibenarkan (tanpa root) |

**Kesimpulan:** penerima RUN_COMMAND tidak bertindak balas. Punca paling mungkin:
build Termux yang dipasang **bukan build yang membenarkan** ciri ini
(Play Store), atau termux.properties belum dibaca semula oleh proses app.

## 5. Langkah seterusnya (belum dibuat)

1. Sahkan sumber pemasangan app Termux:
   `pm list packages -i | grep com.termux`
2. Jika build Play Store → pasang build **F-Droid** (data lama boleh dipindah).
3. Selepas itu uji semula arahan di seksyen 3.
4. Jika masih gagal → guna **ADB** sebagai jalan kawalan (sedang disediakan).

## 6. Jalan alternatif

| Jalan | Status |
|---|---|
| `am start` dari skrip | Disekat BAL — app pihak ketiga tak terbuka |
| MacroDroid macro | Berfungsi untuk buka app (pilihan bos sebelum ini) |
| `RUN_COMMAND` | **Belum berjaya** — perlu build Termux yang betul |
| ADB (`adb shell am start`) | Belum siap — peranti belum dipasangkan |
