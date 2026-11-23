# Tema konsol: kontras teks, cache-bust, dan panel berganda

Rujukan ringkas untuk konsol pelbagai tab (contoh: FastAPI + `static/index.html`
+ `static/app.js` + `static/theme.css`) yang dipakai lama; gejala biasa ialah
"aku dah tukar tema tetapi pengguna nampak sama sahaja".

## 1. Pengguna nampak tema lama → cache pelayar, bukan kod
Pelbagai punca, tetapi yang paling kerap ialah `index.html` merujuk
`style.css` tanpa versi, jadi pelayar guna salinan cache.

Ubat: **versi pada pautan fail**, bukan hanya `Ctrl+Shift+R`.
```html
<link rel="stylesheet" href="/static/theme.css?v=3">
```
Naikkan nombor setiap kali CSS berubah. Semak:
```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8787/static/theme.css?v=3
```

## 2. Tulisan tidak nampak (hitam atas hitam)
Jangan tulis semula semua warna. Tambah **lapisan kontras di hujung** fail tema —
ia menang atas peraturan lama tanpa memadam apa-apa:

```css
/* Mod gelap: paksa teks cerah */
:root[data-theme="dark"] .panel, :root[data-theme="dark"] .card,
:root[data-theme="dark"] td, :root[data-theme="dark"] th,
:root[data-theme="dark"] label, :root[data-theme="dark"] .hint { color: var(--ink); }

/* Mod terang: paksa teks gelap, kad putih */
:root[data-theme="light"] { --ink: #141414; --panel: #ffffff; }
:root[data-theme="light"] .panel, :root[data-theme="light"] .card,
:root[data-theme="light"] td, :root[data-theme="light"] th { color: #141414; }

/* Kawalan borang — mudah terlupa */
input::placeholder, select, option { color: inherit; }
pre, code { color: var(--ink); }
```

Perangkap: `select`/`option` dan `::placeholder` tidak mewarisi warna kad pada
kebanyakan pelayar mudah alih — set warna secara eksplisit, jika tidak medan
nampak kosong walaupun berisi.

## 3. Panel berganda selepas refactor
Bila panel baharu menggantikan panel lama yang masih dirujuk oleh kod live
(`loadWork()` dan seumpamanya), **jangan padam** elemen lama — sembunyikan sahaja:

```html
<div id="sedang-jalan" style="display:none">…</div>
```

Padam elemen akan memecahkan `getElementById` yang masih dipanggil setiap kitaran
kemas kini; menyembunyikan mengekalkan DOM tanpa pertindihan visual.

## 4. Urutan pengesahan selepas ubah UI
1. `node --check static/app.js` → tiada ralat sintaks.
2. `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8787/` → 200.
3. Kira `id`/penanda dalam HTML: `grep -c 'id="tab-skill"' static/index.html` → 1.
4. Setiap endpoint baharu diuji dengan `curl` sebenar, termasuk kes negatif
   (input tidak sah mesti pulang JSON `{"error": …}`, bukan 500).
5. Beritahu pengguna naik taraf `?v=` sekali; jika masih sama, minta muat semula keras.
