# LAPORAN FASA 3 — Kemas `archive/`, `legacy-ultimate/`, `tools/`

**Tarikh:** 2026-11-24 · **Hasil:** 17 GB → **6.4 GB** (jimat 10.6 GB)

## 1. `archive/` — 8.7 GB → 714 MB

| Item | Saiz asal | Tindakan | Sebab |
|---|---|---|---|
| `caches/` | 2.3 GB | **dibuang** | Cache lama Okt — boleh dijana semula |
| `code-server-2026-10/` | 939 MB | **dibuang** | code-server masih hidup di `~/.local` |
| `ultimate-2026-10/root-cleanup/` | 4.9 GB | **dibuang** | Cache alat bina: `.npm` 1.8G · `.cargo` 1.1G · `.bun` 837M · `.local` 725M · `.cache` 327M |
| Salinan separuh di /sdcard | separa | **dibuang** | Tidak lengkap, tiada guna |
| `projects-repo/` + `aina-*` + `downloads/` | 656 MB | **dikekalkan** | Kandungan kerja sebenar |
| `legacy-*` + `system-backup` | 56 MB | **dikekalkan** | Rekod kecil |

## 2. `legacy-ultimate/` — 2.1 GB → 539 MB

Projek lama "ULTIMATE AI PROJECT (Aina)", tiada git. Hanya **pergantungan** dibuang,
kod sumber kekal:

| Dibuang | Saiz |
|---|---|
| `projects/pascal-editor/node_modules` | 789 MB |
| `projects/ai-agent-dashboard/node_modules` | 329 MB |
| `projects/.venv` | 202 MB |
| `kisarasa` + `jobboard` + `coding-agent` node_modules | 179 MB |
| `.next`, `__pycache__`, lain-lain | 41 MB |
| **Jumlah** | **1.6 GB** |

Kod sumber, `identity/`, `docs/`, `tests/`, `config/` — **kekal 539 MB**.

## 3. `tools/others/` — 2.8 GB → 1.9 GB

Pendua **disahkan** dengan banding nama fail + hash MD5 sebelum dibuang:

| Dibuang | Saiz | Bukti |
|---|---|---|
| `bun-install/` | 316 MB | 19,635 fail **sama nama & hash** dengan `bun-repo/` |
| `cline-install/` | 628 MB | 4,225 fail, semua ada dalam `cline-repo/` (yang ada 8,450 fail) |
| `OpenHands-main/` | 18 MB | 2,025 fail sama hash dengan `openhands-main/` |
| **Jumlah** | **962 MB** | |

**Dikekalkan:** `delphitools-cli` 784M · `cline-repo` 702M · `bun-repo` 316M · `sqlmap` 26M ·
`openhands-main` 18M · `commix` 4.1M · `nikto` 3M · `aina-tools` 2.5M.

## 4. `tools/hermes-source/` — `git gc`

Dijalankan `git gc --prune=now` pada repo utama dan `hermes-agent`
(61,242 commit diperiksa semula).

| | Sebelum | Selepas |
|---|---|---|
| `tools/hermes-source/` | 2.8 GB | **2.6 GB** |
| `tools/` keseluruhan | 5.2 GB | **4.4 GB** |

Jimat tambahan: **~800 MB**.

## 5. Keadaan akhir

| | Saiz |
|---|---|
| Sebelum fasa | 17 GB |
| Selepas Fasa 3 + `git gc` | **6.2 GB** |
| Cakera bebas | 83 GB → **95 GB** |

```
4.4G  tools/
714M  archive/
539M  legacy-ultimate/
125M  agency-agents-app/
121M  profiles/
 77M  state.db
 77M  backups/
 64M  lsp/
```

## 6. Prinsip yang dipatuhi

1. **Baca sebelum padam** — setiap folder diperiksa isinya dahulu.
2. **Bukti sebelum padam** — pendua disahkan dengan hash, bukan andaian saiz.
3. **Kod kekal, pergantungan dibuang** — `node_modules`/`venv` boleh dijana semula.
4. **Tiada fail hidup disentuh** — `skills/`, `plugins/`, `sessions/`, `cron/`, DB.
5. **Servis disahkan selepas setiap langkah** — konsol 8787 kekal 200.
