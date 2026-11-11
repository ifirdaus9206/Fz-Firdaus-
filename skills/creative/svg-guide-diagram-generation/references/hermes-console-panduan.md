# Hermes Console — aset panduan bergambar (`static/img/panduan/`)

Projek: FastAPI + HTML di `~/hermes-console` (Termux, Android 16, HyperOS,
Xiaomi 25080RABDG). Semua label panduan dalam **Bahasa Melayu**.

## Struktur aset

```
tools/gen_hyperos_panduan.py     # penjana asal (4 SVG) — SUMBER helper
tools/gen_boot_adb_panduan.py    # penjana aliran boot + ADB (6 SVG)
static/img/panduan/*.svg         # 720x1280, tema gelap
preview/*.png                    # rsvg-convert -w 480 (atau 460)
```

Jangan sentuh `index.html`, `app.py`, `style.css`, `app.js`, servis runit
apabila tugasan hanya minta aset + penjana.

## API helper (jangan salin — import)

```python
from gen_hyperos_panduan import (W, H, BG, PANEL, LINE, INK, MUT, GREEN, YEL,
    ICO, MARGIN, OUT, kotak, teks, ikon, baris, label_anak_panah, shell)
```

- `W,H = 720,1280`; `BG #0d1512`, `PANEL #16241d`, `LINE #24382f`,
  `INK #e8f4ee`, `MUT #93a8a0`, `GREEN #4ade80`, `YEL #ffd166`,
  `ICO #8ee0b0`, `MARGIN = 56`.
- `kotak(x,y,w,h,fill,stroke,r,sw)` — segi empat bulat.
- `teks(x,y,s,size=26,fill=INK,weight="normal",anchor="start")` — auto-escape.
- `ikon(nama,cx,cy,color,sc)` — `gear grid shield battery screen storage up
  bell lock key` sahaja (tiada emoji).
- `baris(y,ikon,tajuk,sub,kanan,sorot,h=112)` — `kanan` = `"on"` (suis hijau)
  atau `"chev"`; `sorot=True` = kad hijau bertepi.
- `label_anak_panah(x_teks,y_teks,x_hujung,y_hujung,s,anchor="end")` — mula
  garis pada `(x_teks-4, y_teks+8)`.
- `shell(tajuk, isi, [(teks, warna), ...])` — bingkai telefon + bar status +
  tajuk + kotak LANGKAH.

### Zon tetap `shell()`

| Zon | Koordinat |
|---|---|
| Garis header | y=108 |
| Baris senarai pertama | y=228, langkah 132, tinggi 112 |
| Kotak LANGKAH | `y=H-206` (1074), tinggi 164, label pada 1104 |
| Baris nota | `H-136 + i*38` → 1144 / 1182 / 1220, saiz 24, x=48 |

Nota saiz 24 pada x=48 mula terpotong melepasi 680 pada ~47 aksara — hadkan
~45 aksara setiap baris LANGKAH.

## Helper tambahan dalam `gen_boot_adb_panduan.py`

- `pil(x,y,w,h,s,fill=YEL,ink="#3a2c05",size=20)` — label pil kuning (guna
  dalam baris disorot bila jurang antara baris hanya ~20px).
- `suis(x,cy,on)` — togol 76x40; `on` hijau + knob kanan.
- `tanda_semak(cx,cy,r,warna,latar)` — bulatan + ✓ dilukis sebagai path.
- `jubin(cx,cy,glyph,label,fill,glyph_fill,high)` — ikon apl 88x88 + label 20.

## Spesifikasi aliran yang telah dilaksana

**A — Pasang Termux:Boot** (APK sudah ada di `/sdcard/Download/TermuxBoot.apk`, 26 KB)
1. `boot-01-fail.svg` "Muat turun" — chip `Fail › Download / 3 item`, baris
   F-Droid.apk / TermuxBoot.apk (sorot + pil "TEKAN FAIL INI") /
   autonomous_trading + `controller_blueprint · folder` (nama panjang dipecah
   antara tajuk dan sub), kad "Fail kecil, 26 KB sahaja".
2. `boot-02-install.svg` "Pasang" — kad putih: ikon hijau `>_` 92x92,
   "Termux:Boot", "Versi 0.8.1 · 26 KB", kebenaran ✓, blok "Benarkan
   pemasangan daripada sumber ini" + suis, BATAL kelabu / PASANG hijau,
   anak panah "TEKAN PASANG" dari bawah kad.
3. `boot-03-selesai.svg` "Selesai" — laci apl 4x3 (jubin 88, lajur x=132/287/
   442/597, baris cy=212/398/584), Termux:Boot berbingkai YEL + pil
   "BUKA SEKALI" (clearance ~18px ke baris 2), kad ✓ `com.termux.boot
   terpasang`, kad nota `~/.termux/boot/*.sh`.

**B — ADB wayarles**
4. `adb-01-pembangun.svg` "Perihal telefon" — Versi HyperOS / Versi Android /
   Nombor binaan (sorot + pil "TEKAN 7 KALI"), toast hijau "Anda kini seorang
   pembangun", kad "Pilihan pembangun tersembunyi".
5. `adb-02-wayarles.svg` "Pilihan pembangun" — Nyahpepijat USB (suis mati),
   Nyahpepijat wayarles (suis hidup + sorot), anak panah "HIDUPKAN" mendarat
   pada suis (tip ~(598,442), dalam baris), kad IP `192.168.1.7` / PORT
   `37123`, kad `adb connect 192.168.1.7:37123`.
6. `adb-03-kod.svg` "Pasangkan peranti" — dialog putih: medan IP:port, pil
   "SALIN DUA-DUA" sebaris label "Kod 6 digit", 6 kotak digit 76x80 (langkah
   88, mula x=96), strip kuning "Salin IP:port DAN kod 6 digit", nota
   "Kod tamat dalam 60 saat.", kad konsol `tab SISTEM › PASANG ADB WAYARLES ›
   PASANGKAN`.

## Arahan peranti (untuk teks panduan)

- Pemasang APK: Seting › Apl › akses khas › "Pasang apl tidak diketahui" /
  "Benarkan dari sumber ini".
- Pilihan pembangun: Seting › Perihal telefon › ketik "Nombor binaan" 7 kali.
- ADB wayarles: Seting › Pilihan pembangun › Nyahpepijat wayarles (Wi-Fi sama);
  pasangkan guna "Pasangkan peranti dengan kod" → salin IP:port + kod 6 digit.
- Termux:Boot mesti dibuka SEKALI selepas dipasang; skrip
  `~/.termux/boot/*.sh` hanya berjalan selepas itu pada setiap boot.

## Semakan yang telah lulus

`python3 tools/gen_boot_adb_panduan.py` → 6 SVG (4.3–7.7 KB) →
`check_svg_text_fit.py` 0 isu → `rsvg-convert -w 480` → 6 PNG (63–93 KB) →
`vision_analyze` setiap satu: tiada teks terpotong/bertindih. Satu-satunya
pembetulan metrik: baris nota boot-02 dipendekkan kepada
`1.  Jika disekat: hidupkan  'Benarkan sumber'`.

Keadaan akhir (2026-11-11): **10 SVG** dalam `static/img/panduan/` (4 HyperOS +
3 boot + 3 ADB), `python3 tools/cek_teks_svg.py` → **10/10 OK**. Dua baris nota
yang benar-benar terkeluar bingkai dibetulkan dengan **memendekkan ayat**, bukan
mengecilkan saiz fon:

- `2.  Skrip ~/.termux/boot/*.sh berjalan setiap boot` → `… /boot/ jalan setiap boot`
- `3.  Tekan ikon kunci → kad kekal walaupun 'clear all'` → `… → kad tak ditutup`

## Jangan percaya "tofu" daripada vision tanpa bukti kedua

Sesi 2026-11-11: setiap PNG potret (720×1280) dipaparkan sebagai blok tofu oleh
`vision_analyze`, termasuk fail yang **sama** dibaca jelas sejam sebelumnya
(md5 identik). Ia artifak laluan imej, bukan SVG rosak. Susunan bukti yang
betul: **pemeriksa metrik > keratan PIL > vision**.

```python
from PIL import Image
im = Image.open("preview/boot-02-install.png").convert("L")
crop = im.crop((x0, y0, x1, y1)).resize((60, 12))   # satu jalur teks
# cetak ASCII: " .:-=+*#%@" untuk (255 - nilai piksel)
```

Huruf sebenar kelihatan dalam dump ⇒ fon dirender. Kotak berongga seragam dalam
setiap sel ⇒ tofu betul. Dalam sesi itu dump ASCII menunjukkan "Termux:Boot"
yang sah, jadi 10 PNG dihantar kepada pengguna tanpa mengulang penjanaan.

## Pendawaian UI (jangan tertinggal)

- Kelas CSS baharu `.hguides` / `.hguide` dengan `aspect-ratio:720/1280;
  object-fit:contain`. Kelas sedia ada `.stepimg` (`1000/620` + `cover`)
  memotong imej potret jadi jalur.
- Tiga panel: `#panel-hyperos` (4 kad), `#panel-boot` (status + butang
  `#boot-go` + 3 kad), `#panel-adb-guide` (butang lompat `#adb-guide-go` + 3 kad).
  Letak **sebelum** panel NOTA/read-only dalam tab yang sama.
- Imej dirujuk terus sebagai `.svg` (`<img src="/static/img/panduan/x.svg">`);
  tiada penukaran PNG diperlukan untuk paparan browser.

