# Ambil deskripsi penuh projek (Freelancer.com) untuk draf yang tepat

Laporan radar memotong `penerangan` pada ~100 aksara, cukup untuk satu hook tetapi tidak cukup
apabila iklan mengandungi **syarat keras** (bilangan nombor telefon, sijil wajib, skop sebenar).
Halaman projek boleh dibaca tanpa log masuk.

## Resepi yang berfungsi (Termux, 2026-11-12)

```python
# simpan dalam direktori projek — JANGAN guna /tmp (tidak writable pada Termux)
import re, html, subprocess

u = "https://www.freelancer.com/projects/<kategori>/<slug>"
t = subprocess.run(["curl", "-sL", "--max-time", "25",
                    "-A", "Mozilla/5.0 (Linux; Android 16)", u],
                   capture_output=True, text=True, timeout=40).stdout

m = re.search(r'<meta name="description" content="(.*?)"', t, re.S)
print(html.unescape(m.group(1))[:600] if m else "tiada meta")
```

- Saiz halaman ~1 MB; had masa 25 s cukup.
- `<meta name="description">` memberi 1–2 ayat pertama iklan + julat harga — selamat, tidak pernah
  bercampur dengan bidaan pesaing.
- Untuk badan penuh, cari teks yang **mula dengan suara klien** (`About the project`, `I am extending`,
  `I need`, `We need`) dan ambil ~3000 aksara selepas indeks itu, buang tag HTML.

## Perangkap: teks bidaan pesaing ada dalam halaman yang sama

Pemilih ini **tidak** selamat — ia memulangkan cadangan pesaing, bukan iklan:

- `class="[^"]*project-description[^"]*"` → pada 2026-11-12 memulangkan
  `"Hi, I run A2Z Research Consultant, a small team of certified penetration testers..."` (bidaan orang lain)
- `id="project-description"` dan `"description":"..."` → sama, kadang-kadang teks bidaan
- `alt=` / atribut imej → teks meta berulang, bukan badan iklan

Kesan: draf menjawab brief yang salah, atau lebih teruk menyalin ayat pesaing (termasuk tawaran harga
dan dakwaan sijil mereka). Tanda amaran: teks bermula `Hi,` / `Dear` / ada `Best regards` / sebut
`I can start within 24 hours` → itu **bidaan**, buang.

## Peraturan praktikal

1. Draf mesti boleh ditulis daripada laporan sahaja; ambil halaman projek **hanya untuk 3 teratas**.
2. Kalau teks yang dijumpai bermula dengan sapaan atau tandatangan → jangan guna; jatuh balik ke
   `meta description` + snippet laporan.
3. Petikan keperluan klien ke dalam badan draf hanya jika ayat itu jelas suara klien (contoh:
   "40 test cases", "5 WhatsApp numbers", "verifiable CEH/OSCP/CREST required").
4. Jangan salin ayat pesaing — bukan sahaja tidak beretika, ia mendedahkan harga dan dakwaan yang
   belum tentu benar tentang diri kita.

## Keperluan berpagar (gating) yang ditemui melalui deskripsi penuh

| Iklan | Syarat keras | Tindakan dalam draf |
|---|---|---|
| Manual E2E tester app WhatsApp (Jejak, MY) | 5 nombor WhatsApp Malaysia, 40 test case | letak `**[X] Malaysian WhatsApp numbers**` dalam badan; checklist: isi bilangan sebenar sebelum hantar |
| Grey-box pentest SP-API | sijil CEH/OSCP/CREST yang boleh disahkan | letak `**[CERT + VERIFICATION LINK]**`; checklist: **JANGAN hantar** jika tiada sijil sahih |

Syarat jenis ini mengubah sama ada kerja itu boleh diambil sama sekali — ia mesti muncul dalam
checklist, bukan disembunyikan dalam badan draf sebagai dakwaan.
