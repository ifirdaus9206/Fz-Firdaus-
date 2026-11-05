# Balasan bernombor sahaja — pulihkan senarai asal dahulu

Kes sebenar (Telegram, sesi baru): bos membalas
`1.ya.  2.ya tukar nama Siti.  3. ya tukar nama kau .cuba berikan cadangan nama pada aku untuk kau 4 .ya`

Tiada konteks lain. Nombor-nombor itu merujuk senarai pilihan dalam mesej TERAKHIR sesi SEBELUM ini.

## Kenapa FTS5 gagal di sini

`session_search(query="tukar nama Siti")` → 0 hasil, walaupun "Siti" baru sahaja disebut.
Sebab: perkataan itu hanya wujud dalam mesej bos yang SEMASA (belum diindeks sebagai sejarah
berguna), manakala senarai pilihan yang dirujuk ada dalam sesi lain. Nombor dan "ya" pula tiada
nilai carian langsung — ia bukan kandungan, ia penunjuk.

## Resipi yang berkesan

1. `session_search()` — tanpa argumen. Pulangkan sesi terbaru (tajuk + preview).
2. Pilih sesi terakhir sebelum sesi semasa, buka penuh:
   `session_search(session_id="<id>")` → semua mesej, termasuk mesej akhir assistant yang membawa
   senarai bernombor **verbatim**.
3. Petik semula pemetaan dalam jawapan sebagai jadual:

   | # | Jawapan bos | Apa aku akan buat |
   |---|---|---|
   | 1 | ya | … |
   | 2 | ya + "tukar nama Siti" | … |

4. Rekod tambahan bos sebagai baris sendiri. "2. ya tukar nama Siti" bukan sekadar "ya pada pilihan
   2" — ia membawa keputusan baharu (nama sasaran) yang tiada dalam pilihan asal.
5. Semak sama ada dua pilihan itu sebenarnya **alternatif**. Contoh sebenar: pilihan 2 = "1 home +
   6 profil", pilihan 3 = "6 home berasingan". Bos kata `ya` pada kedua-duanya — mustahil, kerana
   itu satu kerja dengan dua jalan. Tegur terus dan minta pilih satu; jangan lancar dua kerja.
6. Item yang bergantung pada keputusan belum dibuat (nama, laluan fail) **ditahan** dan dinyatakan:
   "aku tahan item 4 sebab nama yang kau pilih akan ubah laluan fail backup". `ya` bos tidak hilang,
   cuma ditangguh dengan sebab.

## Bila `session_search(session_id=...)` terpotong (PENTING)

Resipi langkah 2 di atas **gagal pada sesi panjang**. Kes sebenar: sesi 56 mesej dengan satu tool
output 142k aksara — pembacaan penuh memulangkan `[Truncated: tool response …]` dan hanya
menghantar mesej dari **awal** sesi. Mesej akhir assistant (yang membawa senarai 1/2/3/4) tidak
keluar langsung, jadi aku nampak sejarah tetapi bukan soalan yang aku perlu jawab.

Ganti langkah 2 dengan query SQL terus — satu panggilan, tepat pada ekor sesi:

```bash
sqlite3 ~/.hermes20/state.db "SELECT id, role, substr(content,1,2500) FROM messages \
WHERE session_id='<id>' AND role IN ('user','assistant') ORDER BY id DESC LIMIT 8;"
```

- `ORDER BY id DESC LIMIT 8` = ekor sesi; itulah tempat senarai pilihan berada.
- Tapis `role IN ('user','assistant')` supaya tool output (punca truncation) tidak memenuhi hasil.
- Jika mesej assistant sangat panjang, `substr` memotong hujungnya — dalam kes itu naikkan had
  (5000+) atau ambil `id` dulu, kemudian `SELECT content FROM messages WHERE id=<id>`.
- Sahkan dengan `role='user'` terakhir sekali sebelum mula kerja: di situlah arahan sebenar bos.

## "Jalankan 1,2,3 sampai siap" — mod laksana penuh

Frasa **"sampai siap"** menukar mod kerja: bos tidak mahu berhenti untuk kelulusan setiap langkah
(berbeza daripada tabiat lalai "satu langkah, tunggu aku ok"). Yang tetap tidak berubah:

1. Petik semula senarai asal dalam balasan pertama — buktikan nombor mana yang dimaksudkan.
2. Semak cakera dahulu: senarai itu mungkin ditulis berjam lalu dan keadaannya sudah berubah
   (contoh sebenar: item "6 profil ejen" masih 1 profil, `gh` masih belum login).
3. Satu item = satu ejen bernama, dihantar serentak; jangan buat kerja tangan sendiri.
4. **Gate kekal.** "Sampai siap" bukan "lulus tanpa bukti". Lapor setiap item sebagai
   siap / jalan / gagal / blok, dan jika satu item memerlukan tindakan manusia (login akaun,
   URL repo, kebenaran) nyatakan sebagai **blok + satu langkah tepat** yang tinggal — jangan
   sembunyikan atau bulatkan sebagai siap.

## Tanda amaran

- Jangan tanya bos "nombor apa maksudnya?" — senarai itu ada dalam DB; bertanya bermakna gagal
  membaca sejarah sendiri, dan bos sudah penat menaip semula.
- Jangan gabungkan dua pilihan alternatif menjadi satu senarai kerja. Ia menghasilkan wave kerja
  yang separuh daripadanya akan dibuang.
- Selepas memetakan, **ulang semula** keputusan dalam satu ayat sebelum mula kerja. Bos membalas
  ringkas; pengesahan semula inilah yang menangkap salah faham awal (contoh sebenar: "Siti" ialah
  nama profil, bukan nama bot — hanya disahkan selepas dinyatakan semula).
