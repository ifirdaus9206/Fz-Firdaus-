# SENARAI PROJEK LAMA — satu fail untuk cari

> Template. Copy to `<archive-root>/SENARAI-PROJEK.md` and fill from reading each project's own
> `README.md` — the owner forgets what the folders are called, and a folder table (`du -sh *`) does
> not answer "what was this?". One row per project, plain language, plus the revive command.

**Dikemas kini:** YYYY-MM-DD · **Lokasi induk:** `~/.hermes20/<archive-root>/`
**Status:** semua projek di sini **TIDAK dijalankan**. Baca sahaja.

## Cara guna fail ini

1. Cari nama projek dalam jadual di bawah.
2. Salin keluar ke folder kerja:
   `cp -r ~/.hermes20/<archive-root>/<folder> ~/kerja/<nama>`
3. Pasang semula kebergantungan (sudah dibuang untuk jimat ruang):
   - Node: `npm install`
   - Python: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
   - Rust: `cargo build`

---

## A. Projek aplikasi

| # | Projek | Saiz | Apa dia | Teknologi |
|---|---|---|---|---|
| 1 | **<nama>** | 1.1 MB | one line: what it does, for whom | frontend + backend |
| 2 | … | | | |

### Folder sokongan
| Folder | Saiz | Isi |
|---|---|---|
| `identity/` | 69 MB | identiti + repo git dalaman |
| `src/` | 77 MB | kod sumber utama |
| `tests/` | 128 MB | ujian |

---

## B. Salinan bertarikh

| Folder | Saiz | Isi |
|---|---|---|
| `<snapshot>-YYYY-MM/` | 659 MB | senarai projek di dalamnya |

---

## C. Legasi sistem

| Folder | Saiz | Isi |
|---|---|---|
| `legacy-<app>-YYYY-MM-DD/` | 31 MB | config / cache / hooks snapshot |

---

## D. Ringkasan saiz

| Bahagian | Saiz |
|---|---|
| … | … |
| **Jumlah** | **1.3 GB** |

---

## E. Nota penting

- `node_modules`, `.venv`, `target/`, `.next` **sudah dibuang** — semua boleh dijana semula.
- Folder arkib **dikecualikan** daripada sandaran GitHub (besar + ada repo git bersarang).
- Jika sesuatu projek disahkan tidak diperlukan, padam foldernya — tiada kesan pada sistem hidup.
- Untuk projek besar, baca `README.md` di dalamnya dahulu sebelum cuba bina.
