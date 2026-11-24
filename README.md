# Fz-Firdaus- · UIM (Ultimate Intelligence Machine)

Rumah kerja **Ketua** — seorang arkitek AI (Master Prompt Architect · AI Systems Architect ·
Multi-Agent Architect · Agent Factory Architect) yang mengarah ejen, bukan membuat kerja tangan.

> Repo ini memaparkan **struktur, dokumen dan kod paparan**.
> Kunci API, token, `.env`, pangkalan data dan fail rahsia **tidak** disimpan di sini.

---

## Apa yang ada di sini

| Folder | Fungsi |
|---|---|
| `SOUL.md` | Persona & undang-undang tetap Ketua |
| `OPERASI.md` | Runbook operasi harian |
| `docs/` | Dokumen arkitektur: 4 peranan, runbook, storan, vault, AI team |
| `system/` | 8 modul sistem: agent_factory · role_generator · workflow_generator · orchestrator · qa · recovery · completion · memory |
| `knowledge_base/` | SOP, fakta dan templat (wiki) |
| `scripts/` | Skrip operasi: sandaran GitHub, penjaga konsol, e-mel, memori, UIM |
| `skills/` | 114 skill dalam 30 kategori |
| `plugins/` | Plugin Hermes (agency-agents-router, dll.) |
| `agency-agents/` | Sumber persona ejen — 21 divisi, 329 dokumen |
| `desktop-plugins/hermes-console/` | Kod konsol pemantauan (FastAPI + statik) |
| `memories/` | Memori jangka panjang Ketua |
| `profiles/` | Profil kerja berasingan (assistant, engineering, finance, …) |

---

## Perkhidmatan (runit)

| Servis | Fungsi | Port |
|---|---|---|
| `hermes-console` | Konsol pemantauan & pengurusan | 8787 |
| `hermes-gateway` | Gateway Telegram | — |
| `hermes-keeper` | Penjaga: wake-lock + hidupkan semula servis | — |
| `hermes-dash-tunnel` | Tunnel Cloudflare ke konsol | — |
| `sshd` | SSH | 8022 |

Semak status: `hermes-status`

---

## Konsol

Satu tempat pemantauan: **`http://127.0.0.1:8787/?tab=pusat`**
Akses dari telefon: `http://<IP-LAN>:8787/?tab=pusat`

Tab: Pusat · Watak (282 ejen) · Skill (114) · Kerja · Cron · Email · MCP · Agency ·
Organisasi · Trading · Panduan · Sistem · Web UI · Gudang.

Enam tema: light · cream · blue · grey · mint · dark.

---

## Memori dua lapis

```
~/vault/memori/01-pendek/    ← rekod harian (satu baris = satu fakta)
~/vault/memori/02-panjang/   ← fakta kekal, disuling setiap malam 23:30
~/vault/memori/03-pelajaran/ ← ringkasan pelajaran bulanan
```

---

## Sandaran

`scripts/backup_github.sh` — harian 02:00, senyap bila sihat.
Imbasan rahsia dua peringkat: commit dibatalkan jika corak kredensial ditemui.

---

## Lesen & had

Dokumen dan kod di sini untuk kegunaan peribadi pemilik repo.
Tiada data pelanggan, tiada kredensial, tiada pangkalan data sesi.
