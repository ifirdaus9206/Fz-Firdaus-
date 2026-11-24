---
tajuk: "SOP Konsol 8787"
jenis: sop
kemas_kini: 2026-11-24
sumber: ["~/.hermes20/docs/SERVIS.md", "~/hermes-console/app.py"]
---

# SOP — Konsol Pemantauan (8787)

## 1. Akses

| Dari mana | URL |
|---|---|
| Peranti sendiri (Termux) | `http://127.0.0.1:8787/?tab=pusat` |
| Telefon dalam LAN | `http://<IP-LAN>:8787/?tab=pusat` |
| Luar | URL tunnel dalam `~/.hermes20/dashboard_url.txt` |

`127.0.0.1` **tidak boleh** dibuka dari telefon — itu loopback telefon itu sendiri.

## 2. Tab

Pusat · Watak (282 ejen, CRUD) · Skill (114) · Kerja · Cron · Email · MCP ·
Agency · Organisasi · Trading · Panduan · Sistem · Web UI · Gudang.

## 3. API utama

| Laluan | Fungsi |
|---|---|
| `GET /api/ping` | Semakan hidup |
| `GET /api/fleet` | Status gateway + skill + RAM + cakera |
| `GET /api/watak` · `POST` · `PUT` · `DELETE` | Katalog ejen |
| `GET /api/skills` · `GET /api/skill?path=` | Senarai & pembaca skill |
| `GET /api/cron` · `POST /api/cron/{id}` | Kerja berjadual: run/pause/resume |
| `POST /api/task` | Hantar kerja kepada ejen |
| `GET /api/mcp` · `POST` · `DELETE` · `/test` · `/catalog` | Pelayan MCP |

## 4. Tema

Enam pilihan: `light` · `cream` · `blue` · `grey` · `mint` · `dark`.
Lalai `light`. Pilihan disimpan dalam `localStorage` kunci `console_theme_v3`.

Selepas ubah CSS/JS, **naikkan versi** dalam `index.html`
(`theme.css?v=N`, `app.js?v=N`) supaya pelayar tidak guna cache lama.

## 5. Peraturan

1. Satu konsol sahaja — 8787. Jangan hidupkan 9119 atau 8790.
2. Bind `0.0.0.0` melalui `CONSOLE_BIND` supaya boleh diakses dari LAN.
3. Rahsia tidak dipaparkan dalam UI.
4. Setiap tindakan bertulis (tambah/padam watak, hentikan kerja) mesti disahkan.
