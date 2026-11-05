---
tajuk: "Templat Brief Ejen (8 Medan)"
jenis: templat
kemas_kini: 2026-11-05
sumber: ["~/.hermes20/SOUL.md"]
---

# Templat Brief Ejen (8 Medan)

Kembali ke [index.md](../index.md) · Prosedur penuh: [SOP arahan ejen](../sop/arahan-ejen.md).

Salin blok di bawah untuk setiap ejen dalam satu RUN. Ganti semua `<...>`.
Jangan tinggalkan medan kosong — "panjang pun boleh; kabur tidak boleh".

```markdown
## BRIEF — <slug ejen> (<peranan>)

1. OBJEKTIF
   <Satu ayat: hasil yang dikehendaki.>

2. KONTEKS
   <Latar belakang, sistem terlibat, batasan persekitaran (cth: Termux Android, tiada root).>

3. INPUT
   - <laluan fail 1>
   - <laluan fail 2>
   (Baca fail ini; jangan reka fakta di luar sumber.)

4. SKOP
   Buat:
   - <item>
   Tidak buat:
   - <item>

5. LARANGAN
   - Jangan sentuh <fail/config/rahsia>.
   - Jangan tulis di luar <laluan dibenarkan>.
   - Jangan reka nombor/harga/tarikh.

6. FORMAT OUTPUT
   - <fail/laluan output>
   - <bentuk: jadual / laporan markdown / diff>

7. KRITERIA LULUS
   - <ujian objektif 1, cth: fail wujud dan ada frontmatter>
   - <ujian objektif 2, cth: output arahan sebenar disertakan>
   (Tiada bukti = NEEDS_WORK.)

8. TARIKH AKHIR
   <YYYY-MM-DD HH:MM> atau <N minit>
```

## Peringatan

- Brief tanpa senarai ejen bernama tidak sah — setiap tugasan mesti keluar sebagai
  RUN dengan `slug`, kebergantungan, dan gate.
- Lulus hanya atas bukti: laluan fail, keluaran arahan, atau nombor ujian.
- Jika ejen gagal: P1 tegur + ulang brief; P2 tambah konteks/bukti; P3 turun tier +
  tulis semula persona; P4 bersara (kebenaran bos). Maksimum 3 cubaan sebelum P3.
- Laporan akhir kepada bos: **ejen · tugasan · status · bukti**.
