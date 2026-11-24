# docs/API-KONSOL.md — Rujukan API Konsol 8787

**Dikemas kini:** 2026-11-24 · **Sumber:** `~/hermes-console/app.py` · **72 laluan**

Asas: `http://127.0.0.1:8787`
Jika `CONSOLE_LAN_TOKEN` diset, semua laluan (kecuali `/api/ping`) perlukan
`?t=<token>` atau cookie `console_auth`. POST juga perlukan `X-CSRF` daripada `/api/meta`.

```bash
CSRF=$(curl -s http://127.0.0.1:8787/api/meta | python3 -c 'import sys,json;print(json.load(sys.stdin)["csrf"])')
curl -s -X POST http://127.0.0.1:8787/api/task -H "X-CSRF: $CSRF" -H 'Content-Type: application/json' -d '{...}'
```

## 1. Asas & status

| Laluan | Kaedah | Fungsi |
|---|---|---|
| `/` | GET | Halaman konsol (HTML) |
| `/api/ping` | GET | Semakan hidup — tiada token |
| `/api/meta` | GET | Versi, CSRF, senarai home |
| `/api/health` | GET | Kesihatan sistem |
| `/api/fleet` | GET | Gateway, bilangan skill, RAM, cakera |
| `/api/overview` | GET | Ringkasan papan pemuka |
| `/api/org` · `/api/orgchart` | GET | Carta organisasi (8 sistem) |
| `/api/sessions` · `/api/session/{home}/{sid}` | GET | Senarai & isi sesi |
| `/api/history` | GET | Sejarah ringkas |

## 2. Ejen & agensi (282)

| Laluan | Kaedah | Fungsi |
|---|---|---|
| `/api/watak` | GET · POST | Senarai ejen (282) · tambah ejen |
| `/api/watak/{slug}` | PUT · DELETE | Kemas kini · padam ejen |
| `/api/agency` | GET | Katalog agensi |
| `/api/agency/agent/{slug}` | GET | Butiran satu ejen |
| `/api/agency/ketua` | GET | Ejen bertanda `ketua` |
| `/api/agency/health` | GET | Kesihatan enjin agensi |
| `/api/agency/analysis` · `/workflow` · `/guard` | GET | Analisis, aliran, pengawal |
| `/api/agency/plan` | POST | Pecah arahan → pelan ejen |
| `/api/agency/run/{run_id}` | POST · GET | Jalankan · semak run |
| `/api/agency/run/{run_id}/note` | POST | Tambah nota pada run |
| `/api/agency/runs` | GET | Senarai semua run |
| `/api/agent/{slug}/dashboard` · `/api/agent-live/{slug}` | GET | Papan pemuka ejen |

## 3. Skill (114)

| Laluan | Kaedah | Fungsi |
|---|---|---|
| `/api/skills` | GET | Senarai + kategori |
| `/api/skill?path=skills/...` | GET | Baca `SKILL.md` (hanya dalam `skills/`) |

## 4. Kerja & langkah

| Laluan | Kaedah | Fungsi |
|---|---|---|
| `/api/task` | POST | Hantar kerja kepada ejen |
| `/api/run/{run_id}/{action}` | POST | `stop` · `retry` · `delete` (ke `cache/run-trash/`) |
| `/api/steps` | GET · POST | Senarai · tambah langkah |
| `/api/steps/{sid}/file` | GET | Fail langkah |

## 5. Cron (13 kerja)

| Laluan | Kaedah | Fungsi |
|---|---|---|
| `/api/cron` | GET | Senarai kerja berjadual |
| `/api/cron/{job_id}` | POST | `run` · `pause` · `resume` |

## 6. E-mel

| Laluan | Kaedah | Fungsi |
|---|---|---|
| `/api/email` | GET | Folder + log susunan |
| `/api/inbox` | GET · POST | Senarai mel · tindakan mel |
| `/api/inbox/{iid}/file` | GET | Baca fail mel |

## 7. MCP

| Laluan | Kaedah | Fungsi |
|---|---|---|
| `/api/mcp` | GET · POST | Senarai · tambah pelayan MCP |
| `/api/mcp/catalog` | GET | 6 pelayan disyorkan |
| `/api/mcp/{name}` | DELETE | Buang pelayan |
| `/api/mcp/{name}/test` | POST | Uji sambungan |

## 8. Servis runit

| Laluan | Kaedah | Fungsi |
|---|---|---|
| `/api/svc` | GET | Status 5 servis |
| `/api/svc/{name}` | POST | `up` · `down` · `restart` |
| `/api/svc/{name}/log` | GET | 100 baris log terakhir |

## 9. Peranti Android

| Laluan | Kaedah | Fungsi |
|---|---|---|
| `/api/device/status` | GET | Status peranti |
| `/api/device/adb-pair` | POST | Pairing ADB |
| `/api/device/shot` | POST | Tangkap skrin |
| `/api/device/boot` · `boot-open` · `boot-install` | GET/POST | Urus autostart |

## 10. Storan & dokumen

| Laluan | Kaedah | Fungsi |
|---|---|---|
| `/api/uim/state` | GET | Status gudang `/sdcard/Documents/UIM` |
| `/api/uim/hantar` | POST | Hantar fail (sha256, sehala) |
| `/api/uim/pdf` | POST | Tukar teks → PDF |
| `/api/sandaran` · `/api/sandaran/fail/{nama}` | GET | Sandaran & isi fail |
| `/api/buka` | GET · POST | Buka fail/folder |
| `/api/web` · `/api/web/verify` | GET · POST | URL awam & pengesahan |

## 11. Laporan & lain-lain

| Laluan | Kaedah | Fungsi |
|---|---|---|
| `/api/report/daily` · `/api/report/send` | GET · POST | Laporan harian · hantar |
| `/api/live/state` · `/api/live/stream` | GET | Keadaan langsung · SSE |
| `/api/trading` · `/api/sofia` | GET | Modul trading & Sofia |
| `/api/bot` | POST | Kawalan bot |

## Nota

1. Semua laluan `POST/PUT/DELETE` perlukan `X-CSRF`.
2. Ralat input → `400`; laluan sensitif di luar `skills/` → `403`.
3. Padam run tidak kekal — dipindah ke `cache/run-trash/<id>`.
4. Jangan tambah laluan tanpa kemas kini dokumen ini.
