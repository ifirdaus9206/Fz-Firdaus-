# STORAN-UIM.md — Kilang vs Gudang (aliran sehala)

**Tarikh:** 2026-11-12 · **Penulis:** Ketua · **Status:** berjalan, disahkan ujian

## 1. Dua kawasan, satu arah

| | Kilang | Gudang & kaunter hantar |
|---|---|---|
| Lokasi | `$HOME` (Termux) — `~/.hermes20`, `~/vault`, `~/workspaces`, skrip, cron, git, `.env`, kunci SSH, fail Python | `/sdcard/Documents/UIM/` |
| Status | **Sumber kebenaran** — satu-satunya tempat kerja sebenar | **Salinan sahaja** — boleh dipadam bila-bila tanpa kerosakan |
| Arah | Sumber | Tujuan |
| Cara pindah | `uim_hantar.sh` (cp + sahkan sha256) | — |
| Dilarang | symlink ke `/sdcard` untuk benda penting | edit hasil kerja di sini, tarik balik ke Termux, simpan rahsia |

Aliran: **Termux → telefon sahaja.** Sebab: `/sdcard` tiada kawalan versi, tiada git, mudah dipadam app pembersih, dan senang dibaca app lain. Kalau hasil kerja hanya ada di telefon, ia bukan lagi sumber kebenaran.

Nota teknikal: `/sdcard` (bukan `/sdcard/Documents`) **tidak boleh** dicipta folder baharu pada Android ini — `mkdir /sdcard/UIM` ditolak `Permission denied`. Jadi akar sebenar ialah `/sdcard/Documents/UIM` (kelihatan dalam app Files → Documents → UIM).

## 2. Struktur gudang

```
/sdcard/Documents/UIM/
├── BACA-DULU.md      ← penerangan ringkas untuk bos
├── 01-LAPORAN/       pdf · md · txt · csv · json · docx · xlsx · pptx · html
├── 02-GAMBAR/        png · jpg · jpeg · webp · svg · bmp
├── 03-AUDIO/         mp3 · ogg · wav · m4a · opus · flac
├── 04-VIDEO/         mp4 · mkv · webm · mov · gif
└── 05-HANTAR/        zip · apk · lain-lain (untuk dihantar keluar)
```

Kategori ditentukan automatik ikut sambungan fail; boleh paksa dengan `--ke`.

## 3. Skrip

### `~/.hermes20/scripts/uim_hantar.sh`
```
uim_hantar.sh <fail|folder> [--ke KATEGORI] [--ganti] [--nama NAMA]
```
Pagar keselamatan (semua diuji):
1. Sumber mesti wujud dan **mesti di dalam `$HOME`** — kalau di luar, ditolak (kod 3).
2. Sumber **symlink → ditolak** (kod 3). Tiada symlink untuk benda penting.
3. Sumber yang sudah berada dalam gudang → ditolak (aliran hanya satu arah).
4. Kategori mesti salah satu daripada 5 folder sah — tak boleh tulis ke lokasi lain.
5. Nama sudah wujud → simpan dengan cap masa (`-YYYYmmdd-HHMMSS`), **tidak menimpa** kecuali `--ganti`.
6. Selepas salin: **sha256 + saiz dibandingkan**. Tak sama → salinan telefon dipadam, keluar kod 6.
7. Setiap salinan berjaya dicatat dalam `~/.hermes20/logs/uim_hantar.log`.

Baris terakhir output: `HANTAR-TELEGRAM: MEDIA:<laluan>` — laluan telefon sedia untuk dihantar ke Telegram/WhatsApp.

### `~/.hermes20/scripts/uim_semak.sh`
Audit senyap (untuk cron). Menangkap:
- symlink dalam `$HOME` yang menunjuk ke `/sdcard` (langgaran peraturan),
- symlink dalam gudang yang menunjuk balik ke `$HOME`,
- fail sulit tersasar ke telefon (`.env*`, `id_rsa*`, `id_ed25519*`, `*token*`, `auth.json`, `config.yaml`).

Senyap + kod 0 = bersih. Ada output + kod 1 = ada langgaran.

## 4. Ujian yang dijalankan (bukti)

| Ujian | Jangkaan | Keputusan |
|---|---|---|
| Salin `docs/LAPORAN-VAULT.md` | masuk `01-LAPORAN/`, sha256 sama | lulus |
| Salin fail `.png` | auto masuk `02-GAMBAR/` | lulus |
| Salin fail luar `$HOME` (`/tmp/x`) | ditolak kod 3 | lulus |
| Sumber symlink | ditolak kod 3 | lulus |
| Nama sama tanpa `--ganti` | simpan ber-cap masa | lulus |
| `uim_semak.sh` selepas setup | senyap, kod 0 | lulus |

Rekod penuh: `~/.hermes20/logs/uim_hantar.log` dan bahagian 5 dokumen ini.

## 5. Log ujian

Lihat `docs/LAPORAN-STORAN-UIM.md` untuk transkrip arahan + keluaran sebenar.

## 6. Rutin

- Setiap laporan/gambar yang perlu dilihat bos → `uim_hantar.sh`, bukan simpan dalam Telegram sahaja.
- Cron `uim_semak.sh` setiap hari 08:00 — lapor hanya bila ada langgaran.

## 7. Tukar Markdown → PDF

Saluran baharu: fail `.md` di `$HOME` → PDF dalam gudang, satu arahan sahaja.

```
uim_pdf.sh <fail.md> [--nama NAMA.pdf]
uim_pdf.sh ~/.hermes20/docs/STORAN-UIM.md
uim_pdf.sh ~/.hermes20/docs/KETUA.md --nama LAPORAN-KETUA.pdf
```

- Enjin: `markdown` (extensions: tables, fenced_code, sane_lists, nl2br) → HTML → `fpdf2 write_html`. Tiada pandoc/wkhtmltopdf/LaTeX.
- Font DejaVu (aksara `→` `…` `—` `·` selamat). Saiz A4, margin 15mm, footer setiap halaman: `UIM · <nama fail> · halaman N`.
- PDF dijana sementara dalam `~/.hermes20/tmp/`, dihantar melalui `uim_hantar.sh --ke 01-LAPORAN`, disahkan sha256 dua hala, kemudian fail sementara dipadam.
- Baris terakhir: `SIAP-PDF: /sdcard/Documents/UIM/01-LAPORAN/<nama>.pdf`.
- Input tiada / di luar `$HOME` / symlink → `GAGAL:` + kod 2 atau 3. Penjanaan PDF gagal → `GAGAL:` + kod 6.
- Boleh panggil penukar terus: `python3 ~/.hermes20/scripts/md_to_pdf.py <in.md> <out.pdf> [--tajuk TAJUK]`.

Bukti ujian 2026-11-12: `STORAN-UIM.pdf` 54,115 bait (2 halaman) dan `UJIAN-KETUA.pdf` 74,642 bait (5 halaman); teks diekstrak semula mengandungi "STORAN" dan "Ketua".
