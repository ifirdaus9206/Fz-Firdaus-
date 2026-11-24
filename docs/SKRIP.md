# docs/SKRIP.md — Daftar 35 Skrip

**Dikemas kini:** 2026-11-24 · **Lokasi:** `~/.hermes20/scripts/`
**Semakan sintaks:** 35/35 lulus (0 rosak)

Kelas: **AUTO** = dijalankan cron/servis · **MANUAL** = guna bila perlu · **SEKALI** = satu kali sahaja, calon arkib.

## 1. AUTO — dijalankan cron (14)

| Skrip | Jadual | Kerja |
|---|---|---|
| `backup_github.sh` | 02:00 harian | Sandaran `~/.hermes20` → GitHub, senyap bila sihat, imbasan rahsia 2 peringkat |
| `uim_semak.sh` | 08:00 harian | Audit storan: kilang (Termux) vs gudang (`/sdcard`) |
| `email_auto.sh` | setiap 10 min | Pembalut: ambil + susun e-mel ke `~/vault/email-inbox` |
| `email_autosort.sh` | setiap 15 min | Susun ke 1-PENTING / 2-KERJA / 3-PROMOSI |
| `email_digest.sh` | 21:00 harian | Laporan sekali sehari tentang susunan e-mel |
| `url_watch.sh` | setiap 15 min | Beritahu **hanya** bila URL tunnel berubah |
| `gw_alert.sh` | setiap 5 min | Amaran bila gateway mati / mati tidak bersih; cuba `sv restart` |
| `tg_watch.sh` | setiap 5 min | Amaran bila mesej Telegram menunggu tetapi gateway tidak ambil |
| `console_keeper.sh` | setiap 5 min | Pembalut cron → jalankan `keeper.sh` |
| `ruang_alert.sh` | setiap 6 jam | Amaran bila cakera hampir penuh |
| `sofia-tarik.sh` | setiap 5 min | Tarik `status.json` SOFIA dari repo relay |
| `uim_sync.sh` | 03:00 harian | Salin nota/laporan baharu ke storan kongsi |
| `radar_kerja.sh` | 09:00 & 21:00 | Pembalut freelance-radar |
| `ketua_weekly.py` | Isnin 09:00 | Pembalut `~/hermes-console/tools/weekly_check.py` |

## 2. AUTO — dijalankan servis runit (2)

| Skrip | Servis | Kerja |
|---|---|---|
| `keeper.sh` | `hermes-keeper` | Setiap 60 s: tahan wake-lock, naikkan servis mati, buang proses yatim |
| `dash_tunnel.sh` | `hermes-dash-tunnel` | `cloudflared tunnel --url http://127.0.0.1:8787` |

## 3. MANUAL — alat untuk bos/Ketua (13)

| Skrip | Kerja |
|---|---|
| `dash_verify.sh` | Sahkan konsol + tunnel: URL awam, pagar login, API |
| `dash_url_notify.sh` | Hantar mesej Telegram bila URL bertukar (manual) |
| `dash_mail.py` | E-mel URL + kelayakan log masuk tanpa mendedahkan rahsia |
| `email_fetch.py` | Ambil Gmail → satu e-mel = satu fail markdown + CSV indeks |
| `memori_panjang.py` | Himpun memori pendek 7 hari untuk penyulingan panjang |
| `memori_pendek.sh` | Tulis satu fakta ke memori harian |
| `uim_hantar.sh` | Hantar fail ke gudang telefon (sehala + sha256) |
| `uim_pdf.sh` | Markdown → PDF → gudang telefon |
| `md_to_pdf.py` | Penukar Markdown → PDF (enjin di sebalik `uim_pdf.sh`) |
| `export_sandaran.py` | Eksport data tab Sandaran ke `reports/sandaran/` |
| `sync_agency_catalog.py` | Banding katalog router dengan korpus app (check/build/fix-paths) |
| `translate_agency_ms.py` | Terjemah korpus persona → `agency-agents-ms/` (boleh sambung) |
| `gh_login_driver.py` | Pemandu PTY untuk `gh auth login --web` |

## 4. SEKALI — SUDAH DIPINDAH ke arkib (6)

| Skrip | Kerja | Sebab calon arkib |
|---|---|---|
| `fix_gateway_once.sh` | Restart gateway bersih (18 Nov) | Pembetulan sekali |
| `gw_restart_once.sh` | Restart gateway sekali (17 Nov) | Pembetulan sekali |
| `gw_handover.sh` | Penyerahan gateway terkawal | Pembetulan sekali |
| `probe_env.py` | Uji pemboleh ubah persekitaran mana perlu | Diagnostik sekali |
| `probe_dm_thread_gate.py` | Uji laluan topik DM Telegram | Diagnostik sekali |
| `repro_runner.py` | Ulang satu ujian tertentu | Diagnostik sekali |

**Status 2026-11-24:** keenam-enamnya disahkan **tiada rujukan** dalam cron, runit,
servis atau skrip lain. Dipindahkan ke
`/sdcard/Documents/UIM/arkib-h20/skrip-sekali/` (boleh pulih jika perlu).
`scripts/` kini **29 fail**, sintaks 29/29 lulus.

## 5. Peraturan skrip

1. Nama: `kata-kerja-kata-nama.sh` (contoh `uim_hantar.sh`, `gw_alert.sh`).
2. Setiap skrip ada komen tajuk + cara guna di 15 baris pertama.
3. Cron mesti senyap bila sihat (`stdout` kosong).
4. Skrip cron **mesti** berada dalam `scripts/` (cron Hermes cari di sini).
5. Tiada rahsia dalam skrip — baca daripada `.env` atau `secrets/`.
6. Selepas tambah skrip baharu, kemas kini jadual di atas.
