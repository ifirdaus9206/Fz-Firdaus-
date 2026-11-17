# SOP — Email → Susun satu per satu → Simpan (Drive / Docs / Sheets)

Tarikh: 2026-11-12 · Pemilik: Ketua · Pelaksana: ejen (Ketua tidak buat kerja tangan)

## 1. Prinsip

1. Satu email = satu rekod. Tidak dicampur, tidak diringkas dalam satu fail besar.
2. Rekod mesti boleh dijejak: UID email + tarikh + fail simpanan.
3. Tiada kelayakan (App Password, token) ditulis dalam repo, skrip, atau chat — hanya dalam `~/.hermes20/.env`.
4. Tiada email dihantar / difail-kan / dipadam tanpa kebenaran bos.

## 2. Aliran kerja

```
Gmail (IMAP)
   │  baca satu per satu (UID)
   ▼
~/vault/email-inbox/<YYYY-MM-DD>_<uid>_<slug>.md      ← satu email = satu fail
~/vault/email-inbox/_index.csv                         ← satu baris = satu email (indeks induk)
   │
   ├─► Google Sheets  : salinan indeks (boleh semak dari telefon, ada status)
   ├─► Google Docs     : satu dok per lead penting (butiran + draf balasan)
   └─► Google Drive    : folder per klien → lampiran (PDF/gambar/resume)
```

## 3. Di mana simpan apa (pilih ikut jenis)

| Jenis bahan | Tempat sesuai | Sebab |
|---|---|---|
| Senarai email/lead (tarikh, dari, subjek, status) | **Google Sheets** | senang scan, tapis, tanda status dari telefon |
| Butiran satu lead + draf balasan/proposal | **Google Docs** | teks panjang, senang edit & kongsi pautan |
| Lampiran asal (PDF, gambar, fail kerja) | **Google Drive** (folder per klien) | fail binari; Docs/Sheets tak sesuai untuk simpan fail |
| Rekod induk tempatan (backup) | `~/vault/email-inbox/` | tahan walaupun tiada internet/Google |

Larangan: jangan simpan lampiran besar dalam Sheets; jangan simpan teks panjang dalam Drive sebagai .txt (guna Docs).

## 4. Lajur Sheet `Email & Lead`

| Lajur | Isi |
|---|---|
| A Tarikh | tarikh email diterima |
| B Dari | alamat pengirim |
| C Subjek | subjek asal (jangan ubah) |
| D Kategori | freelance / klien / bil / undangan / sampah |
| E Ringkasan | satu ayat, apa yang diminta |
| F Tindakan | apa perlu dibuat (balas / tawar harga / fail) |
| G Status | BARU → SEDANG → HANTAR → TUTUP |
| H Pautan | pautan Doc atau fail Drive |
| I UID email | untuk jejak balik ke Gmail |

## 5. Perintah (skrip tempatan)

```bash
cd ~/.hermes20
python scripts/email_fetch.py check                      # uji login
python scripts/email_fetch.py list --days 7 --max 20     # senarai sahaja (tiada simpan)
python scripts/email_fetch.py save --days 7 --tag freelance
python scripts/email_fetch.py save --uid 1234 --tag klien
```

Kelayakan dalam `~/.hermes20/.env`:

```
GMAIL_USER=nama@gmail.com
GMAIL_APP_PASSWORD=<16 aksara dari myaccount.google.com/apppasswords>
```

Nota: kata laluan login Gmail **tidak** boleh dipakai untuk IMAP. Google mewajibkan
App Password (perlu 2-Langkah Pengesahan dihidupkan).

## 6. Naik taraf ke Google Drive / Docs / Sheets

Perlu kebenaran OAuth sekali sahaja (Google Cloud → OAuth client → token di `~/.hermes20/google_token.json`).
Selepas itu:

```bash
GAPI="python ~/.hermes20/skills/productivity/google-workspace/scripts/google_api.py"
$GAPI sheets append SHEET_ID "Sheet1!A:I" --values '[["tarikh","dari","subjek",...]]'
$GAPI docs create --title "Lead: <klien>" --body "..."
$GAPI drive upload ~/vault/email-inbox/<fail> --parent FOLDER_ID
```

## 7. Semakan pematuhan

- [ ] Setiap email baharu ada fail sendiri dalam `~/vault/email-inbox/`
- [ ] Setiap fail ada baris dalam `_index.csv`
- [ ] Tiada App Password / token dalam git (`git grep -i 'app_password'` kosong)
- [ ] Sheet disegarkan selepas setiap kelompok simpanan
