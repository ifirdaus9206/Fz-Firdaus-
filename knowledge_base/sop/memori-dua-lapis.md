---
tajuk: "SOP Memori Dua Lapis"
jenis: sop
kemas_kini: 2026-11-24
sumber: ["~/.hermes20/scripts/memori_panjang.py", "~/.hermes20/scripts/memori_pendek.sh"]
---

# SOP — Memori Dua Lapis

## 1. Struktur

```
~/vault/memori/01-pendek/YYYY-MM-DD.md   ← catatan harian
~/vault/memori/02-panjang/MEMORI-PANJANG.md  ← fakta kekal (< 4000 aksara)
~/vault/memori/03-pelajaran/YYYY-MM.md   ← pengajaran bulanan
```

## 2. Aliran

1. **Sepanjang hari** — setiap fakta baharu ditulis satu baris dalam `01-pendek`
   dengan format: `HH:MM | [kategori] fakta`.
2. **23:30 setiap malam** — cron menjalankan `memori_panjang.py 7`:
   - himpun 7 hari terakhir daripada `01-pendek`
   - tulis semula `02-panjang/MEMORI-PANJANG.md` di bawah 4000 aksara
   - tambah ringkasan bulanan ke `03-pelajaran/YYYY-MM.md`
   - kerja senyap (tiada mesej jika tiada perubahan)
3. **Setiap sesi baharu** — `MEMORI-PANJANG.md` disuntik sebagai konteks.

## 3. Apa masuk memori panjang

| Masuk | Tidak masuk |
|---|---|
| Keutamaan & gaya kerja bos | "Siap kerja X hari ini" |
| Fakta persekitaran (port, laluan, servis) | Nombor PR, commit, ID sementara |
| Pelajaran daripada kegagalan | Data mentah / log panjang |
| Konvensyen & peraturan | Perkara yang lapuk dalam 7 hari |

## 4. Peraturan

1. Memori panjang mesti **padat** — jika lebih 4000 aksara, ringkaskan, jangan buang fakta.
2. Fakta lapuk mesti diganti, bukan ditambah berlapis.
3. Memori bukan log kerja — log ada di `sessions/`.
4. Jangan simpan rahsia (kunci, token, kata laluan) dalam memori.
