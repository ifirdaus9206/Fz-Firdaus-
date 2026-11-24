# LAPORAN FASA 1 — Baca, Bina, Tambah Isi

**Tarikh:** 2026-11-24 · **Skop:** dokumen teras `~/.hermes20` (root + `docs/` + `system/` + `knowledge_base/`)
**Status:** SIAP · **Tiada fail dipadam** dalam fasa ini

---

## 1. Fail yang dibaca (28) — untuk semakan bos

### Peringkat atas (3)
| Fail | Saiz | Tajuk | Status |
|---|---|---|---|
| `README.md` | 2,518 b | Fz-Firdaus- · UIM | **DIBINA SEMULA** (dulu 39 b) |
| `OPERASI.md` | 11,007 b | Runbook Operasi Harian Ketua | Lengkap, 12 seksyen |
| `SOUL.md` | 5,562 b | KETUA — 4 peranan bertingkat | Lengkap |

### docs/ (6)
| Fail | Saiz | Status |
|---|---|---|
| `docs/README.md` | 1,615 b | **BARU** — indeks dokumen |
| `docs/KETUA.md` | 8,864 b | Lengkap (manual 4 peranan) |
| `docs/PELAN-AI-TEAM.md` | 6,493 b | Lengkap |
| `docs/STORAN-UIM.md` | 4,886 b | Lengkap |
| `docs/DASHBOARD.md` | 5,486 b | Lengkap |
| `docs/hermes-agent-summary.md` | 3,468 b | Lengkap (rujukan pemasangan Oct) |

### system/ (9)
| Fail | Saiz | Status |
|---|---|---|
| `system/README.md` | 2,077 b | **BARU** — indeks 8 modul + rajah aliran |
| `agent_factory.md` | 6,138 b | TERISI v2.0 |
| `role_generator.md` | 4,502 b | TERISI v2.0 |
| `workflow_generator.md` | 6,456 b | TERISI v2.0 |
| `orchestrator.md` | 4,761 b | TERISI v2.0 |
| `qa_system.md` | 5,051 b | TERISI v2.0 |
| `recovery_system.md` | 5,407 b | TERISI v2.0 |
| `completion_system.md` | 5,722 b | TERISI v2.0 |
| `memory_manager.md` | 5,649 b | TERISI v2.0 |

### knowledge_base/ (10 → 12)
| Fail | Saiz | Status |
|---|---|---|
| `index.md` | 2,309 b | **DIKEMAS KINI** — pautan + tarikh |
| `SCHEMA.md` | 1,396 b | Lengkap |
| `log.md` | 2,855 b | Lengkap |
| `fakta/empat-peranan.md` | 3,819 b | Lengkap |
| `fakta/enam-peranan.md` | 3,111 b | Lengkap |
| `fakta/status-sistem.md` | 4,803 b | Lengkap |
| `sop/arahan-ejen.md` | 5,277 b | Lengkap |
| `sop/backup.md` | 2,173 b | Lengkap |
| `sop/email-freelance.md` | 3,520 b | Lengkap |
| `templat/brief-ejen.md` | 1,678 b | Lengkap |
| `sop/konsol-8787.md` | **baru** | **BARU** — SOP konsol |
| `sop/memori-dua-lapis.md` | **baru** | **BARU** — SOP memori |

**Keputusan pemeriksaan:** tiada `TODO` / `TBD` / `FIXME` / placeholder dalam mana-mana fail.
Kata "kosong" yang dikesan hanyalah teks biasa (contoh: "folder kosong"), bukan fail tidak siap.

---

## 2. Isi yang ditambah

| Fail | Apa ditambah | Sebab |
|---|---|---|
| `README.md` | Halaman repo penuh: struktur folder, 5 servis, konsol, memori, sandaran | Dulu hanya satu baris — tidak berguna sebagai paparan GitHub |
| `docs/README.md` | Jadual 5 manual + 8 laporan arkib + 4 peraturan dokumen | Tiada indeks sebelum ini |
| `docs/SERVIS.md` | Peta 5 servis runit, arahan `hermes-status/up/down/restart`, `sv` asas, prosedur pulih | Pengetahuan servis hanya ada dalam kepala, tiada dokumen |
| `docs/SUSUNAN.md` | Peta folder: hidup / sokongan / arkib + peraturan susunan | Untuk elak tersalah padam |
| `system/README.md` | Indeks 8 modul + rajah aliran brief→factory→qa→completion→memory | Modul wujud tetapi tiada peta |
| `knowledge_base/sop/konsol-8787.md` | Akses, tab, API, 6 tema, peraturan versi CSS/JS | SOP konsol belum ada dalam wiki |
| `knowledge_base/sop/memori-dua-lapis.md` | Struktur 3 lapis, aliran 23:30, jadual apa masuk/tidak | Sistem memori baharu belum didokumenkan |
| `knowledge_base/index.md` | 2 pautan SOP baharu, tarikh 2026-11-24, jumlah 11 halaman | Indeks lapuk |
| `bin/hermes19` | Shim → `hermes20` + amaran | Dulu halakan ke home yang sudah dipadam (rosak) |

---

## 3. Penyusunan (bukan pemadaman)

| Kerja | Hasil |
|---|---|
| 8 `*.bak` di root (`SOUL.md`, `config.yaml`, `state.db`) | → `backups/` (77 MB) |
| 8 laporan bukti dalam `docs/` | → `docs/arkib/` |
| 2 `.bak` skrip + 5 `agents.json.bak` | → `backups/` |
| `__pycache__` (scripts, plugins) | dibuang (boleh dijana semula) |
| Root `~/.hermes20` | tiada lagi `*.bak` bertaburan |

---

## 4. Cadangan lanjutan (untuk fasa berikut)

| Cadangan | Faedah | Risiko |
|---|---|---|
| `docs/ARKITEKTUR.md` — satu rajah penuh: Hermes → gateway → konsol → ejen → memori | Satu gambar faham seluruh sistem | Rendah |
| `docs/RUNBOOK-INSIDEN.md` — senarai gejala → punca → tindakan (gateway mati, tunnel 502, konsol tak jawab, port digenggam) | Pulih tanpa fikir panjang | Rendah |
| `docs/API-KONSOL.md` — semua 20+ laluan API dengan contoh `curl` | Rujukan pembangunan | Rendah |
| `knowledge_base/fakta/servis-runit.md` | Fakta servis dalam wiki, bukan hanya docs | Rendah |
| `OPERASI.md` — tambah seksyen "Susunan folder" yang merujuk `docs/SUSUNAN.md` | Runbook harian lengkap | Rendah |
| `AGENTS.md` di root — panduan untuk ejen yang bekerja dalam repo ini | Elak ejen buat silap struktur | Sederhana (perlu disemak) |

---

## 5. Belum disentuh (fasa berikut)

| Item | Saiz | Fasa |
|---|---|---|
| `archive/` → storan luar | 8.7 GB | sedang berjalan |
| `legacy-ultimate/` | 2.1 GB | Fasa 3 |
| `tools/others` pendua | ~660 MB | Fasa 4 |
| `logs/` rotate | 18 MB | Fasa 5 |
| `profiles/` symlink skill | 100 MB | Fasa 6 (opsyenal) |
| Fail kosong runtime (254) | — | tiada tindakan (normal) |

---

## 6. Semakan pantas untuk bos

```bash
ls ~/.hermes20/docs            # 7 fail + README + arkib/
ls ~/.hermes20/system          # 8 modul + README
ls ~/.hermes20/knowledge_base/sop
ls ~/.hermes20/backups
head -30 ~/.hermes20/README.md
```
