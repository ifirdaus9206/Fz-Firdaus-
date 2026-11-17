# LAPORAN-STORAN-UIM.md — Bukti peraturan kilang/gudang berjalan

**Tarikh ujian:** 2026-11-12 13:37–13:39 · **Pelaksana:** Ketua · **Status:** SIAP, semua ujian lulus

## 1. Apa yang dibina

| # | Komponen | Lokasi | Keadaan |
|---|---|---|---|
| 1 | Akar gudang + 5 kategori | `/sdcard/Documents/UIM/` | wujud |
| 2 | Nota untuk bos | `/sdcard/Documents/UIM/BACA-DULU.md` | wujud |
| 3 | Skrip hantar sehala | `~/.hermes20/scripts/uim_hantar.sh` | laku (chmod +x) |
| 4 | Skrip audit | `~/.hermes20/scripts/uim_semak.sh` | laku |
| 5 | Pintasan PATH | `~/.hermes20/bin/uim_hantar`, `~/.hermes20/bin/uim_semak` | symlink dalam `$HOME` sahaja |
| 6 | Log salinan | `~/.hermes20/logs/uim_hantar.log` | 4 baris ujian |
| 7 | Spesifikasi penuh | `docs/STORAN-UIM.md` | wujud |
| 8 | Kemas kini runbook | `OPERASI.md` §5 + §5a | wujud |
| 9 | Cron audit | `8a0f32323c27`, `0 8 * * *`, `no_agent` | `last_status = ok` |

Akar sebenar ialah `/sdcard/Documents/UIM`, bukan `/sdcard/UIM`: Android 16 (HyperOS 3) menolak penciptaan folder di peringkat atas kad storan.
```
$ mkdir -p /sdcard/UIM/_uji
mkdir: cannot create directory 'UIM': Permission denied
$ mkdir -p /sdcard/Documents/UIM/_uji && echo ok > .../t.txt
ok        # BOLEH
```

## 2. Ujian pagar — keluaran sebenar

| # | Ujian | Keluaran | Kod | Verdict |
|---|---|---|---|---|
| U1 | salin `docs/STORAN-UIM.md` | `SIAP: /sdcard/Documents/UIM/01-LAPORAN/STORAN-UIM.md … sha256 7f9ed20e3e520153… (disahkan dua hala)` | 0 | LULUS |
| U2 | salin `~/uji_gambar.png` | auto masuk `02-GAMBAR/` | 0 | LULUS |
| U3 | sumber di luar `$HOME` (`$PREFIX/tmp/luar.txt`) | `GAGAL: sumber di luar $HOME … Kilang hanya $HOME.` | 3 | LULUS (ditolak) |
| U4 | sumber symlink (`~/pautan.md`) | `GAGAL: sumber ialah SYMLINK … tiada symlink untuk benda penting` | 3 | LULUS (ditolak) |
| U5 | nama sama tanpa `--ganti` | `NOTA: nama sudah ada, disimpan sebagai uji_gambar-20261112-133752.png` | 0 | LULUS |
| U6 | kategori haram `--ke ../../etc` | `GAGAL: kategori tidak sah` | 64 | LULUS (ditolak) |
| U7 | salin folder | `SIAP (folder): …05-HANTAR/uji_folder — 2 fail, 15K` | 0 | LULUS |
| U8 | `uim_semak.sh` keadaan bersih | senyap, tiada output | 0 | LULUS |
| U9 | `uim_semak.sh` + symlink `~/gudang_pautan → /sdcard/Documents/UIM` | `SYMLINK TERLARANG: …/gudang_pautan -> /sdcard/Documents/UIM` | 1 | LULUS (ditangkap) |
| U10 | `uim_semak.sh` + `.env.uji` dalam gudang | `FAIL SULIT DI TELEFON: …/05-HANTAR/.env.uji` | 1 | LULUS (ditangkap) |
| U11 | cron `run` manual | `last_status = ok`, `execution_success = true`, senyap | — | LULUS |

Nota pembetulan semasa ujian: versi pertama `uim_semak.sh` tersalah menandakan 12 symlink
Termux biasa (`~/storage/*`, `~/phone` dari `termux-setup-storage`) sebagai langgaran.
Pagar dikecualikan untuk laluan itu; selepas pembetulan U8 senyap (kod 0) dan U9 tetap ditangkap.

## 3. Log salinan sebenar

```
2026-11-12 13:37:52 | ~/.hermes20/docs/STORAN-UIM.md | /sdcard/.../01-LAPORAN/STORAN-UIM.md | 7f9ed20e3e520153 | 3846 bait | 01-LAPORAN
2026-11-12 13:37:52 | ~/uji_gambar.png | /sdcard/.../02-GAMBAR/uji_gambar.png | 818090838dc7138d | 9 bait | 02-GAMBAR
2026-11-12 13:37:52 | ~/uji_gambar.png | /sdcard/.../02-GAMBAR/uji_gambar-20261112-133752.png | 818090838dc7138d | 9 bait | 02-GAMBAR
2026-11-12 13:37:57 | FOLDER | ~/uji_folder | /sdcard/.../05-HANTAR/uji_folder | folder | 2 fail
```

Artifak ujian (`uji_gambar*.png`, `uji_folder`, `/tmp` luar) sudah dipadam pada 13:38.
Keadaan akhir gudang: `01-LAPORAN/STORAN-UIM.md` + `BACA-DULU.md`. Audit terakhir: kod 0.

## 4. Peraturan yang kini berkuat kuasa

1. Kerja sebenar **hanya** dalam `$HOME`. Hasil kerja yang hanya ada di telefon = bukan sumber kebenaran.
2. Pindah ke telefon **hanya** melalui `uim_hantar.sh` (cp + sahkan sha256), bukan `mv`, bukan symlink.
3. Telefon **tidak** diedit dan **tidak** ditarik balik ke Termux.
4. `.env`, kunci SSH, `auth.json`, `config.yaml`, token **tidak** dibenarkan masuk gudang.
5. Audit automatik 08:00 setiap hari; lapor hanya bila ada langgaran.

## 5. Had yang diketahui

- `/sdcard` peringkat atas tidak boleh ditulis → akar gudang di `Documents/UIM`.
- Fail `.md` dalam gudang boleh dibaca app Files, tetapi PDF lebih mesra bos; tukar bila perlu (`pdf` skill).
- `uim_hantar.sh` tidak memadam salinan lama dalam gudang — pembersihan manual atau ikut `--ganti`.
