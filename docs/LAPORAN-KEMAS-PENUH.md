# LAPORAN PENUH — Kemas & Susun `~/.hermes20`

**Tarikh:** 2026-11-24 · **Pelaksana:** Ketua · **Status:** SIAP
**Hasil:** 17 GB → **6.1 GB** · cakera bebas 83 GB → **95 GB**

---

## 1. Ringkasan

| Fasa | Kerja | Hasil |
|---|---|---|
| 1 | Baca & bina semula dokumen teras | 28 fail dibaca, 9 dokumen baharu/dibina semula |
| 2 | Baca semua skrip | 35 → 29 skrip, 0 rosak |
| 3 | Buang cache, pendua, kebergantungan | −10.6 GB |
| 4 | Rotate log | 27 MB → 4.6 MB |
| 5 | Profil → symlink | 121 MB → 54 MB |
| 6 | Kemas `backups/` | 94 MB → 26 MB |

---

## 2. Apa yang DIPADAM dan KENAPA

### 2.1 `archive/` — 8.0 GB dibuang

| Item | Saiz | Kenapa dibuang | Boleh pulih? |
|---|---|---|---|
| `ultimate-2026-10/root-cleanup/` | 4.9 GB | Cache alat bina sahaja: `.npm` 1.8G · `.cargo` 1.1G · `.bun` 837M · `.local` 725M · `.cache` 327M. Semua dijana semula automatik bila alat dipasang. | Ya — jalankan semula `npm/cargo/bun install` |
| `ultimate-2026-10/caches/` | 2.3 GB | Cache npm/cargo/pip snapshot Okt. Tiada nilai selepas 1 bulan. | Ya |
| `code-server-2026-10/` | 939 MB | Snapshot code-server lama. code-server **masih hidup** di `~/.local/lib/code-server`. | Ya — salinan baru boleh dibuat |
| Salinan separuh di `/sdcard` | separa | Pemindahan terhenti, fail tidak lengkap — tidak boleh dipakai. | Tidak perlu |

**Dikekalkan:** `projects-repo` 572 MB · `aina-downloads` 36 MB · `downloads` 32 MB · `aina-other` 16 MB · `legacy-*` 56 MB.

### 2.2 `legacy-ultimate/` — 1.6 GB dibuang

Projek lama "ULTIMATE AI PROJECT (Aina)". **Hanya kebergantungan** dibuang, **kod sumber kekal**.

| Dibuang | Saiz | Kenapa |
|---|---|---|
| `projects/pascal-editor/node_modules` | 789 MB | Pakej npm — `npm install` menjana semula |
| `projects/ai-agent-dashboard/node_modules` | 329 MB | Sama |
| `projects/.venv` | 202 MB | Virtualenv Python — `python -m venv` menjana semula |
| `kisarasa` + `jobboard` + `coding-agent` node_modules | 179 MB | Sama |
| `.next` + `__pycache__` | 41 MB | Hasil bina & cache Python |

**Yang tinggal (539 MB):** semua kod sumber, `identity/` 69 MB, `tests/` 128 MB, `docs/` 25 MB, `config/` 42 MB.

### 2.3 `tools/others/` — 962 MB dibuang (pendua disahkan hash)

| Dibuang | Saiz | Bukti ia pendua |
|---|---|---|
| `bun-install/` | 316 MB | 19,635 fail — **semua nama & MD5 sama** dengan `bun-repo/` |
| `cline-install/` | 628 MB | 4,225 fail — semuanya ada dalam `cline-repo/` (8,450 fail, ada folder tambahan `00-DOCS`, `01-CFG-*`) |
| `OpenHands-main/` | 18 MB | 2,025 fail — semua hash sama dengan `openhands-main/` |

### 2.4 Log — 22 MB dibuang

| Item | Saiz | Kenapa |
|---|---|---|
| `web-server.log` | 6.6 MB | Dikosongkan — log lama; fail dikekalkan |
| `agent.log` | 4.5 MB | Dikosongkan |
| `agent.log.1` | 5.0 MB | Arkib putaran lama — dibuang |
| `hermes-dash-tunnel.log` | 3.8 MB | Dikosongkan |
| `errors.log.1` | 2.0 MB | Arkib lama — dibuang |
| `dashboard-tunnel.log` | 582 KB | Dikosongkan |

Log servis svlogd (`hermes-console/`, `hermes-keeper/`) **tidak disentuh** — dikendalikan runit.

### 2.5 Profil — 67 MB dijimat (bukan dipadam)

7 profil menyimpan **salinan penuh 71 skill lama** (45 fail berbeza daripada versi terkini).
`skills/` setiap profil ditukar menjadi **symlink** ke `~/.hermes20/skills`.

- Sandaran skill lama: `backups/profiles-skills-lama-2026-11-24.tar.gz` (17 MB)
- Ujian: `HERMES_PROFILE=finance hermes skills list` → **111 aktif** (dulu 71)

### 2.6 `backups/` — 68 MB dibuang

| Dibuang | Saiz | Kenapa |
|---|---|---|
| `state.db.bak-pra-migrasi-1328` | 56 MB | **`state.db` disahkan `integrity_check = ok`**, 23 jadual, 12,301 mesej. Backup pra-migrasi tidak perlu lagi. |
| `SOUL.md.agency-backup` | 57 KB | **MD5 sama tepat** dengan `SOUL.md.bak` |
| `agents.json.bak-20261106-0154` + `-20261105` + `-2026-11-04` | 12.3 MB | Pendua pertengahan — dikekalkan `bak-watak` (terkini) + `2026-10-22` (asal) |

### 2.7 Skrip sekali-guna — dipindah, bukan dipadam

| Skrip | Apa dia |
|---|---|
| `fix_gateway_once.sh` | Restart gateway bersih (18 Nov) |
| `gw_restart_once.sh` | Restart gateway sekali (17 Nov) |
| `gw_handover.sh` | Penyerahan gateway terkawal |
| `probe_env.py` | Uji pemboleh ubah persekitaran |
| `probe_dm_thread_gate.py` | Uji laluan topik DM Telegram |
| `repro_runner.py` | Ulang satu ujian |

Disahkan tiada cron/servis/skrip lain memanggil mereka. Disimpan di
`/sdcard/Documents/UIM/arkib-h20/skrip-sekali/` — **boleh pulih**.

---

## 3. Apa yang TIDAK disentuh (sengaja)

| Folder / fail | Sebab |
|---|---|
| `skills/` (115 skill) | Hermes baca pada laluan tetap |
| `plugins/` | Dimuatkan masa mula |
| `sessions/`, `cron/` (15 kerja), `memories/` | Ditulis runtime |
| `state.db` 77 MB | DB hidup — disahkan sihat |
| `config.yaml`, `SOUL.md`, `OPERASI.md` | Teras identiti |
| `secrets/`, `.env`, `auth.json` | Rahsia |
| `workspaces/`, `knowledge_base/`, `system/` | Kerja & rujukan |

---

## 4. Fail baharu / dibina semula

| Fail | Saiz | Kenapa |
|---|---|---|
| `README.md` | 2.5 KB | Dulu 39 bait — kini halaman repo penuh |
| `AGENTS.md` | 2.9 KB | Panduan ejen (tiada sebelum ini) |
| `docs/ARKITEKTUR.md` | 4.9 KB | Tiada rajah penuh sistem |
| `docs/SERVIS.md` | 3.3 KB | Pengetahuan servis tiada dokumen |
| `docs/SUSUNAN.md` | 2.1 KB | Peta folder |
| `docs/RUNBOOK-INSIDEN.md` | 3.4 KB | 16 gejala → tindakan |
| `docs/API-KONSOL.md` | 4.7 KB | 72 laluan API |
| `docs/SKRIP.md` | 4.0 KB | Daftar 29 skrip |
| `docs/README.md`, `system/README.md` | — | Indeks folder |
| `knowledge_base/sop/konsol-8787.md`, `sop/memori-dua-lapis.md`, `fakta/servis-runit.md` | — | SOP baharu |
| `bin/hermes19` | 245 b | Dulu rosak (halakan ke home dipadam) |

---

## 5. Pengesahan akhir

```
~/.hermes20        6.1 GB        (asal 17 GB)
cakera bebas       95 GB         (asal 83 GB)
konsol 8787        200
servis             5 HIDUP
skills             115
cron               15 aktif
scripts            29 fail, 0 rosak
profiles           7 × 115 skill (symlink)
state.db           integrity ok · 12,301 mesej
GitHub             commit terakhir selepas push
```

---

## 6. Apa yang MASIH TINGGAL

| # | Perkara | Saiz | Cadangan |
|---|---|---|---|
| 1 | `legacy-ultimate/` | 539 MB | Bos mahu kekal dulu — semak bila ada masa |
| 2 | `archive/ultimate-2026-10/projects-repo` | 572 MB | Kekal — kod projek lama |
| 3 | `tools/others/delphitools-cli` | 784 MB | Semak sama ada masih dipakai |
| 4 | `tools/others/cline-repo` + `bun-repo` | 1.0 GB | Alat pihak ketiga — buang jika tidak dipakai |
| 5 | `backups/profiles-skills-lama-*.tar.gz` | 17 MB | Boleh dibuang selepas 1 minggu stabil |
| 6 | Folder hantu `/sdcard/.../ultimate-2026-10` | 26 KB, 0 fail | Bos akan padam sendiri dari aplikasi Fail |
| 7 | Log tidak berputar automatik | — | Cadang cron rotate mingguan (simpan 7 hari) |
| 8 | `sessions/` + `cache/` | 5 MB | Kecil — biarkan |

---

## 7. Peraturan yang dipatuhi

1. **Baca sebelum padam** — setiap folder diperiksa isinya.
2. **Bukti sebelum padam** — pendua disahkan MD5, DB disahkan `integrity_check`.
3. **Kod kekal, kebergantungan dibuang** — boleh dijana semula.
4. **Tiada fail hidup disentuh** — skills, plugins, cron, DB, config.
5. **Boleh pulih** — sandaran dalam `backups/` & `/sdcard/Documents/UIM/arkib-h20/`.
6. **Servis disahkan** selepas setiap langkah — konsol kekal 200.
