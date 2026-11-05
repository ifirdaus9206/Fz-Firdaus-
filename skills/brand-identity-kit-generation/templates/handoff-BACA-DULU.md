# BACA DULU — Serahan Jenama <BRAND> (<VERSI>)

Untuk sesiapa yang akan guna fail jenama ini: pereka grafik, kedai cetak, pembuat papan tanda,
orang web / sosial media.

**Perkara paling penting:** setiap folder ada **satu jenis fail sahaja**. Jangan tukar format.
Hantar folder yang betul kepada orang yang betul (rujuk bahagian 5).

---

## 1) Isi setiap folder

| Folder | Isi | Untuk siapa |
|---|---|---|
| `01-LOGO-SVG` | <N> fail logo vektor (.svg) — warna, hitam, putih, songsang, ikon, wordmark, stacked | pereka, web, pembuat papan tanda |
| `02-LOGO-PDF` | <N> fail logo vektor sedia cetak | kedai cetak |
| `03-PNG` | <N> fail gambar 128px → 1600px, latar lutsinar | sosial media, WhatsApp, e-mel |
| `04-PALET` | Kad warna (.svg + .pdf) | pereka + cetak |
| `05-TIPOGRAFI` | Contoh huruf (.svg + .pdf) | pereka |
| `06-KAD-PERNIAGAAN` | Kad depan & belakang (.svg + .pdf 300dpi) | kedai cetak |
| `07-GARIS-PANDUAN` | Buku panduan <P> halaman + setiap halaman berasingan | klien, pereka baru, pembekal |
| `08-MOCKUP` | Contoh guna pada <trak/papan/sosial> | pembentangan / jualan |
| `09-FON` | Fail fon (.ttf) + lesen (OFL) | pereka & web |
| `10-SUMBER` | Skrip penjana — **dalaman, jangan hantar kepada pembekal** | untuk tukar jenama nanti |

## 2) Warna rasmi (salin tepat, jangan agak)

| Nama | HEX | RGB | CMYK (cetak) | Bila guna |
|---|---|---|---|---|
| <Utama> | `#______` | _ / _ / _ | _ / _ / _ / _ | <...> |
| <Latar> | `#______` | _ / _ / _ | _ / _ / _ / _ | <...> |
| <Neutral> | `#______` | _ / _ / _ | _ / _ / _ / _ | <...> |
| <Aksen> | `#______` | _ / _ / _ | _ / _ / _ / _ | hanya elemen besar / garis |
| <Aksen gelap> | `#______` | _ / _ / _ | _ / _ / _ / _ | teks kecil atas latar cerah |

**Amaran cetak:** <aksen> di atas <latar> = <x>:1 — gagal AA untuk teks kecil. Guna <aksen gelap>.

## 3) Fon rasmi

- Tajuk: <Fon A> · Teks badan: <Fon B> · Lesen: <OFL/nama lesen> (fail dalam `09-FON`).

## 4) Peraturan ringkas jenama

1. Nama penuh: **<BRAND>** untuk papan tanda, trak, web, sosial.
2. **"Inc." hanya untuk dokumen sah** — kontrak, invois, lesen, kad perniagaan.
3. Jangan tulis: <salah ejaan yang dilarang>.
4. Jarak lapang di sekeliling logo = tinggi huruf <X>. Tiada apa-apa dalam ruang itu.
5. Saiz minimum: <__> mm (cetak) / <__> px (skrin); ikon sahaja <__> px.
6. Jangan ubah bentuk, tambah warna, bayang atau gradien.

## 5) Siapa dapat apa

| Penerima | Hantar |
|---|---|
| Kedai cetak kad | `06-KAD-PERNIAGAAN` + `09-FON` |
| Pembuat papan tanda / trak | `01-LOGO-SVG` atau `02-LOGO-PDF` + `04-PALET` |
| Pereka grafik baru | semua folder + `07-GARIS-PANDUAN` |
| Orang web / sosial | `03-PNG` + `09-FON` + `04-PALET` |
| Klien / pembentangan | `07-GARIS-PANDUAN` + `08-MOCKUP` |

## 6) Bila mahu tukar jenama

Fail dalam `10-SUMBER` menjana semula SEMUA fail di atas. Untuk jenama baru:

1. Nama jenama — `gen_logo.py` (baris ~<n>) dan teks tajuk dalam `gen_guidelines.py`.
2. Warna — `brand_lib.py` (baris <n1>–<n2>).

Selepas ubah: `bash build_all.sh`.

## 7) Status fail ini

- Semua <N> fail SVG dalam `01-LOGO-SVG` diuji — boleh dibuka tanpa ralat (<fail rosak> dikeluarkan
  ke `source/_rosak/`).
- PDF garis panduan: <P> halaman, lengkap. PNG: <N> fail.
- Belum ada: fail sumber Illustrator (.ai) / EPS — SVG boleh dibuka dalam Illustrator dan disimpan
  sebagai `.ai`. Fakta terbuka: <[TBC] items>.
