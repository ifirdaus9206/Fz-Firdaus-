---
tajuk: "Status Lapisan Sistem AI Team"
jenis: fakta
kemas_kini: 2026-11-06
sumber: ["~/.hermes20/docs/PELAN-AI-TEAM.md"]
---

# Status Lapisan Sistem AI Team

Kembali ke [index.md](../index.md) · Lihat juga [empat peranan Ketua](../fakta/empat-peranan.md) ·
[enam peranan](../fakta/enam-peranan.md) · [SOP arahan ejen](../sop/arahan-ejen.md).

Disalin daripada `docs/PELAN-AI-TEAM.md` (ditulis 2026-11-05). Jangan ubah status
tanpa bukti baharu.

> "Hermes hanyalah **satu lapisan**. Yang menjadikan ejen berguna ialah 11 lapisan sistem
> di sekelilingnya: mesin → otak → saluran → struktur pasukan → papan → memori →
> pengetahuan → workspace → SOP → backup → tool/MCP."

Nota: tajuk sumber menyebut "11 lapisan", tetapi jadualnya menyenaraikan **14 baris**.
Kedua-dua angka dikekalkan seperti dalam sumber; percanggahan ini belum diselesaikan.

## Jadual status (salinan penuh)

| # | Lapisan | Maksud dalam video | Status kita | Bukti |
|---|---|---|---|---|
| 1 | Infrastruktur | Mesin 24 jam (mini PC / VPS) | **SEPARA** | Telefon Termux — Android boleh bunuh proses |
| 2 | Otak / model | Model berbeza per ejen; model terbaik untuk lead | **SEPARA** | Semua guna deepseek-v4.1-flash; tiada model per ejen |
| 3 | Saluran | Telegram untuk bos, WhatsApp untuk pelanggan | **ADA** | @ainafz_bot, gateway aktif |
| 4 | Struktur pasukan | Satu profil per kerja + 1 lead agent | **PALSU** | 282 "ejen" hanya teks persona dalam satu proses |
| 5 | Lead agent | Manage sub-ejen + onboarding ejen baru | **BARU DIBETULKAN** | `SOUL.md` 20–47: Ketua = **4 peranan bertingkat** (T1 Master Prompt Architect → T2 AI Systems Architect → T3 Multi-Agent Architect → T4 Agent Factory Architect); tak buat kerja tangan. Lihat [empat peranan](empat-peranan.md) |
| 6 | Papan / dashboard | Kanban, pejabat 2D, status bekerja/tidur | **SEPARA** | 127.0.0.1:8787 + panel EJEN BERTUGAS (baru) |
| 7 | Memori pendek | profile / soul / user / memory / agent.md | **ADA** | ~/.hermes20/memories, SOUL.md |
| 8 | Memori panjang | Obsidian + pautan dua hala | **TIADA** | skill obsidian ada, vault belum disambung |
| 9 | Pengetahuan | LLM Wiki = SOP/FAQ/fakta (bukan memori) | **TIADA** | skill llm-wiki ada, belum di-setup |
| 10 | Workspace | Fail kerja berasingan per ejen | **TIADA** | Semua ejen tulis ke folder yang sama |
| 11 | SOP = skill | Skill dipanggil bila tugas tertentu | **ADA** | ~/.hermes20/skills (100+) |
| 12 | Backup | Cron malam → GitHub, ejen jaga dirinya | **TIADA** | Tiada repo backup automatik |
| 13 | Tool luar (MCP) | Port universal ke sistem pihak ketiga | **TIADA** | Tiada MCP server didaftar |
| 14 | Automasi | Cron + workflow | **SEPARA** | 6+ cron; workflow DAG hanya dalam runner |

> **Kemas kini 2026-11-06 (4 peranan):** lapisan 5 (Lead agent) kini bukan satu peranan —
> Ketua ialah **empat arkitek bertingkat** yang dijalankan ikut urutan (T1 prompt → T2 seni bina
> → T3 pasukan → T4 kilang), ditakrifkan dalam `SOUL.md` 20–47 dan undang-undang tetap #6
> (`SOUL.md` 64). Rujukan: [empat peranan](empat-peranan.md), `OPERASI.md` §1, `docs/KETUA.md` §1,
> `docs/LAPORAN-4-PERANAN.md`.

> **Kemas kini 2026-11-06:** lapisan 9 (Pengetahuan) kini **ADA** — wiki
> `knowledge_base/` (8 fail, P5) sudah wujud dan semua pautannya sah. Baris 9
> dalam jadual di atas kekal sebagai salinan sumber bertarikh 2026-11-05, dan
> rumusan di bawah kekal kiraan jadual sumber tersebut.

## Rumusan kiraan

| Status | Bilangan | Lapisan |
|---|---|---|
| ADA | 3 | 3, 7, 11 |
| SEPARA | 4 | 1, 2, 6, 14 |
| TIADA | 5 | 8, 9, 10, 12, 13 |
| PALSU | 1 | 4 |
| BARU DIBETULKAN | 1 | 5 |

Nota: lajur di atas dikira daripada jadual sumber; `SEPARA` muncul 4 kali
(1, 2, 6, 14), jumlah keseluruhan 14 baris.

## Kesimpulan sumber

> ""282 ejen" kita **bukan** pasukan seperti dalam video. Ia **satu** Hermes yang
> memakai 282 teks persona. Sebab itu tiada ejen kelihatan "bekerja" di papan:
> tiada proses, tiada memori sendiri, tiada workspace sendiri."

## Keutamaan seterusnya (P1–P8, daripada sumber)

| # | Tindakan | Status dalam sumber |
|---|---|---|
| P1 | Jadikan Ketua benar-benar pengarah | siap: `SOUL.md` baharu (4 peranan bertingkat) + panel EJEN BERTUGAS |
| P2 | Buat 4–6 ejen SEBENAR dahulu, bukan 282 | dirancang |
| P3 | Workspace per ejen `~/.hermes20/workspaces/<ejen>/` | dirancang |
| P4 | Memori panjang (Obsidian) vault `~/vault/` | dirancang |
| P5 | Pengetahuan (LLM Wiki) → `knowledge_base/` | halaman ini ialah langkah P5 |
| P6 | Backup malam ke GitHub | dirancang — lihat [SOP backup](../sop/backup.md) |
| P7 | MCP untuk sistem luar | bila perlu |
| P8 | Mesin 24 jam (VPS / telefon dicas + `termux-wake-lock`) | belum |

> "P5 — Pengetahuan (LLM Wiki): SOP, FAQ, harga, templat → `knowledge_base/`
> dalam format wiki, bukan memori." — `docs/PELAN-AI-TEAM.md`
