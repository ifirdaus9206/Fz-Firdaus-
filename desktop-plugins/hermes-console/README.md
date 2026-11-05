# Hermes Console — plugin DESKTOP

Plugin runtime untuk app **Hermes Desktop** yang memaparkan papan pemantau
`http://127.0.0.1:8787` **dalam app**, dengan paparan yang sama seperti di pelayar.

Pintu rasmi: `<hermes home>/desktop-plugins/<name>/plugin.js` — loader desktop
mengimbas folder ini, menulis semula import SDK, kemudian `register(ctx)`.
Jadi **tiada suntingan pada apps/desktop** dan naik taraf Hermes tidak memecahkannya.

## Apa yang didaftarkan

| Kontribusi | Area | Kesan |
|---|---|---|
| `page` | `routes` | halaman `/console` (iframe ke console) |
| `nav` | `sidebar.nav` | baris "Console" (codicon `pulse`) dalam sidebar |
| `pill` | `statusBar.right` | penunjuk hijau/merah: console hidup atau tidak |
| `open` | `palette` | perintah "Console: Buka papan pemantau" |
| `set-url` | `palette` | "Console: Tetapkan URL pelayan" (untuk akses jauh/LAN) |

Halaman memaparkan bar status (dot + host + butang **Muat semula** / **Pelayar**)
dan iframe `…/?embed=1`. Mod `embed` menyembunyikan brand/home/clock console
supaya nampak seperti sebahagian shell desktop, bukan halaman luar.

Jika pelayan console mati, halaman tunjuk arahan + butang **salin** arahan
`~/hermes-console/run.sh`.

## Pasang / hidupkan

1. Pelayan console mesti wujud pada mesin yang sama (atau LAN):
   ```bash
   ~/hermes-console/run.sh          # 127.0.0.1:8787
   ```
2. Folder ini sudah berada di `~/.hermes20/desktop-plugins/hermes-console/`.
3. Buka Settings ▸ Plugins dalam Hermes Desktop — plugin **Hermes Console**
   sepatutnya muncul (kind: disk). `defaultEnabled: true`, jadi ia daftar automatik.
4. Sidebar → **Console**, atau Command Palette → "Console: Buka papan pemantau".

## Semak tanpa Electron

Plugin ini disahkan dengan dua alat (boleh dijalankan di mana-mana, termasuk Termux):

```bash
cd ~/hermes-console
python3 tools/validate_desktop_plugin.py     # sintaks ESM + specifier + kontrak + area
node tools/desktop_plugin_harness.mjs        # register(ctx) + render halaman (stub SDK/react)
```

Harness meniru laluan loader sebenar: tulis semula import → import modul →
`register(ctx)` → render pokok elemen → pastikan `iframe src` mengandungi
`127.0.0.1:8787/?embed=1`.

## Had yang diakui

- **Electron tidak boleh dibina/dijalankan pada Android/Termux.** Plugin ini
  aktif apabila Hermes Desktop dijalankan pada macOS/Linux/Windows. Di peranti
  ini, console kekal digunakan melalui pelayar (paparan sama, mod biasa).
- Desktop yang berjalan di mesin lain perlu tetapkan URL pelayan ke IP peranti
  (Command Palette → "Console: Tetapkan URL pelayan"), dan console perlu
  didedahkan di LAN — secara lalai ia bind `127.0.0.1` sahaja.
- Plugin runtime berjalan dengan kepercayaan penuh renderer (bukan sandbox);
  ia hanya membingkaikan localhost dan tidak menghantar data ke luar.
