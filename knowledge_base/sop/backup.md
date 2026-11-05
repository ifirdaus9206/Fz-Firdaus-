---
tajuk: "SOP Sandaran ke GitHub"
jenis: sop
kemas_kini: 2026-11-05
sumber: ["~/.hermes20/docs/PELAN-AI-TEAM.md"]
---

# SOP Sandaran ke GitHub

Kembali ke [index.md](../index.md) · Lihat juga [status sistem](../fakta/status-sistem.md).

Status lapisan ini pada 2026-11-05: **TIADA** — tiada repo sandaran automatik.
Halaman ini mencatat SOP yang **dirancang** (P6) dalam `docs/PELAN-AI-TEAM.md`,
bukan prosedur yang sudah berjalan.

## 1. Matlamat

Ejen menjaga dirinya: salinan `~/.hermes20` dihantar ke GitHub setiap malam
supaya kehilangan telefon/proses tidak memusnahkan konfigurasi, skill, dan pengetahuan.

> "Backup | Cron malam → GitHub, ejen jaga dirinya | **TIADA** | Tiada repo backup automatik"
> — `docs/PELAN-AI-TEAM.md`, jadual 11 lapisan, baris 12

## 2. Jadual

- **Masa:** 2:00 pagi (cron).
- **Arahan:** `git add -A && commit && push` untuk `~/.hermes20`.
- **Syarat:** **tanpa token/rahsia**.

> "Cron 2:00 pagi: `git add -A && commit && push` untuk ~/.hermes20 (tanpa token/rahsia)."
> — `docs/PELAN-AI-TEAM.md`, P6

## 3. Peringatan rahsia — JANGAN commit

Repo mesti disandarkan **tanpa token atau rahsia**. Fail yang dikenal pasti
mengandungi kelayakan dalam home ini (disemak 2026-11-05):

- `~/.hermes20/.env`
- `~/.hermes20/auth.json`
- `~/.hermes20/config.yaml` (boleh mengandungi kunci API)

Langkah wajib sebelum `git add -A`:

1. Tambah `.gitignore` yang mengecualikan sekurang-kurangnya:
   `.env`, `auth.json`, `*.lock`, `gateway.pid`, `state.db*`, `kanban.db*`,
   `models_dev_cache.json`, `sessions/`, `logs/`.
2. Jalankan semakan rahsia (`git diff --cached | grep -iE 'api[_-]?key|token|secret|password'`)
   dan batalkan commit jika ada padanan.
3. Sahkan `git status` tidak menyenaraikan fail rahsia sebelum `push`.
4. Jika rahsia ter-commit: **putar (rotate) kunci itu** — memadam commit tidak cukup.

> Amaran: butiran senarai fail di atas ialah pemerhatian sistem tempatan,
> bukan petikan daripada pelan. Prinsip "tanpa token/rahsia" ialah petikan P6.

## 4. Belum disahkan

Sumber tidak menyatakan repo, cawangan, atau kelayakan GitHub yang digunakan.
Jangan reka nilai tersebut — sahkan dengan bos sebelum mengaktifkan cron.
