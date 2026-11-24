# docs/SUSUNAN.md — Peta Folder `~/.hermes20`

**Dikemas kini:** 2026-11-24

## Folder hidup (jangan gerak)

| Folder | Fungsi | Jangan sentuh kerana |
|---|---|---|
| `skills/` | 114 skill / 30 kategori | Hermes baca pada laluan tetap |
| `plugins/` | Plugin (agency-agents-router) | Dimuatkan masa mula |
| `sessions/` | Rekod sesi | Dibaca `session_search` |
| `cron/` | 13 kerja berjadual | Penjadual menulis di sini |
| `memories/` | Memori Ketua | Disuntik setiap pusingan |
| `state.db` | Pangkalan data utama | DB hidup |
| `config.yaml` · `SOUL.md` · `OPERASI.md` | Konfigurasi & arahan | Teras identiti |
| `scripts/` | 35 skrip operasi | Dirujuk cron & servis |
| `knowledge_base/` | SOP, fakta, templat | Wiki rujukan |
| `workspaces/` | Ruang kerja ejen | Setiap ejen ada folder |
| `system/` | 8 modul prompt sistem | Dirujuk aliran Ketua |

## Folder sokongan

| Folder | Fungsi |
|---|---|
| `backups/` | Semua `*.bak` + `state.db` lama + `profiles-skills-lama-2026-11-24.tar.gz` |
| `docs/` | Manual + `arkib/` untuk laporan bukti lama |
| `agency-agents/` | Sumber persona ejen (329 dokumen, 21 divisi) |
| `agency-agents-app/` | Aplikasi paparan persona |
| `tools/hermes-source/` | Sumber enjin Hermes (hidup) |
| `tools/others/` | Alat pihak ketiga (semak sebelum simpan) |
| `desktop-plugins/hermes-console/` | Salinan kod konsol untuk GitHub |
| `profiles/` | 7 profil kerja; `skills/` setiap satu ialah **symlink** ke `~/.hermes20/skills` (115 skill). Jangan tukar balik kepada salinan — jimat 67 MB. |
| `arkib-ketua/` | **1.3 GB** - semua projek lama di bawah nama Ketua (ultimate-2026-10, projek-ultimate-aina, legacy-*, system-backup). Baca sahaja. |
| `bin/` | Binari besar + pembungkus `hermes20` |
| `lsp/` | Language server |
| `sandboxes/` | venv sandbox |
| `cache/`, `tmp/`, `logs/` | Runtime — selamat dipadam isinya |

## Folder mati / arkib

| Folder | Status |
|---|---|
| (arkib) | `archive/` dan `legacy-ultimate/` telah digabung ke `arkib-ketua/` |
| `legacy-ultimate/` | 539 MB — kod projek lama tanpa `node_modules`/`venv` |
| `ULTIMATE_AI_PROJECT/` | Kosong — calon buang |
| `platforms/pairing/` | Dicipta runtime, kekal kosong |

## Peraturan susunan

1. Satu folder = satu tujuan. Jangan campur dokumen dengan data.
2. `*.bak` tidak kekal di root — masuk `backups/`.
3. Laporan bukti > 30 hari → `docs/arkib/`.
4. Sebelum padam apa-apa: baca, sahkan tiada rujukan (`grep -r <nama>`), baru padam.
