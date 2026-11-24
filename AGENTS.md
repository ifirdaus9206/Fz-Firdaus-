# AGENTS.md — Panduan Ejen Dalam Repo Ini

**Home:** `~/.hermes20` · **Dikemas kini:** 2026-11-24
Baca ini sebelum menyentuh apa-apa fail. Arahan Ketua dalam `SOUL.md` mengatasi fail ini.

## 1. Peranan

Ketua **tidak** membuat kerja tangan. Ketua: faham → arah → semak → putus.
Kerja tangan (kod, ujian, scan, laporan) milik ejen bernama.

## 2. Folder yang JANGAN disentuh tanpa arahan jelas

| Folder | Sebab |
|---|---|
| `skills/`, `plugins/` | Hermes baca pada laluan tetap; rosak = keupayaan hilang |
| `sessions/`, `cron/`, `memories/` | Ditulis oleh runtime |
| `state.db`, `kanban.db`, `projects.db` | DB hidup — jangan tulis terus |
| `config.yaml`, `SOUL.md`, `OPERASI.md` | Teras identiti & konfigurasi |
| `secrets/`, `.env`, `auth.json` | Rahsia — jangan baca, jangan salin, jangan commit |

## 3. Peraturan kerja

1. **Baca sebelum tulis.** Guna `search_files` untuk cari rujukan dahulu.
2. **Jangan cipta fail baharu** jika fail sedia ada boleh dikembangkan.
3. **Jangan padam** sehingga `grep -r <nama>` disahkan tiada rujukan.
4. **Satu perubahan, satu pengesahan.** Jangan gabung 3 operasi besar.
5. **Bukti wajib.** Lapor dengan laluan fail, keluaran arahan, atau nombor ujian.
6. **Sahkan servis selepas setiap perubahan struktur:** `hs` → konsol 200.

## 4. Rahsia — larangan keras

- Jangan tulis kunci/token dalam kod, dokumen, atau commit.
- Jangan salin `.env`, `auth.json`, `secrets/` ke mana-mana folder lain.
- `scripts/backup_github.sh` membatalkan commit jika corak kredensial ditemui —
  jangan lumpuhkan imbasan itu; betulkan fail yang salah.
- Nilai pemboleh ubah persekitaran (`os.environ.get(...)`) bukan rahsia — jangan
  tersalah tanda sebagai kredensial.

## 5. Servis

```bash
hs                      # status semua
hermes-up               # naikkan yang mati
hermes-restart          # mula semula konsol + gateway (putus sesi sekejap)
sv status hermes-console
```
Satu konsol sahaja: **8787**. 9119 dan 8790 dibersarakan — jangan hidupkan.

## 6. Konvensyen fail

| Jenis | Lokasi |
|---|---|
| Manual & arkitektur | `docs/` (laporan lama → `docs/arkib/`) |
| SOP & fakta | `knowledge_base/` (frontmatter wajib) |
| Modul prompt sistem | `system/` |
| Skrip operasi | `scripts/` (`.sh` / `.py`) |
| Sandaran `*.bak` | `backups/` — bukan di root |
| Hasil untuk bos | `/sdcard/Documents/UIM/` (sehala, sha256) |

## 7. Gaya laporan kepada bos

- Bahasa Melayu, ringkas, tepat.
- Papan: ejen · tugasan · status · bukti.
- Akhiri dengan 3–4 pilihan bernombor.
- Jangan sekali-kali reka keluaran yang tidak benar-benar dijalankan.

## 8. Rujukan pantas

| Perlu tahu | Baca |
|---|---|
| Gambaran sistem | `docs/ARKITEKTUR.md` |
| Servis & arahan | `docs/SERVIS.md` |
| Peta folder | `docs/SUSUNAN.md` |
| Bila rosak | `docs/RUNBOOK-INSIDEN.md` |
| API konsol | `docs/API-KONSOL.md` |
| Manual Ketua | `docs/KETUA.md` |
