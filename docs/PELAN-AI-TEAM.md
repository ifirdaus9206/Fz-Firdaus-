# PELAN AI TEAM — apa yang video itu ajar vs apa yang kita ada

Sumber: YouTube `oZh7SpRN1sk` (Bahasa Indonesia) — "full setup AI team guna Hermes".
Transkrip disimpan: `~/tmp/yt_oZh7.txt` (24,012 aksara). Ditulis 2026-11-05.

## Inti video (1 ayat)

Hermes hanyalah **satu lapisan**. Yang menjadikan ejen berguna ialah 11 lapisan sistem di sekelilingnya:
mesin → otak → saluran → struktur pasukan → papan → memori → pengetahuan → workspace → SOP → backup → tool/MCP.

## Empat peranan Ketua (bertingkat)

Ketua bukan satu peranan. Dia **empat arkitek bertingkat**, dijalankan ikut urutan —
Tahap 1 mesti lulus sebelum Tahap 2, dan seterusnya. Rujukan penuh: `SOUL.md` baris 20–47,
ringkasan dalam `OPERASI.md` §1 dan `docs/KETUA.md` §1, bukti dalam `docs/LAPORAN-4-PERANAN.md`.

| Tahap | Peranan | Kerja | Output | Penanda lulus |
|---|---|---|---|---|
| 1 | Master Prompt Architect | Reka fikiran — prompt modular: prompt utama, prompt peranan, prompt gate, pembolehubah | Fail arahan 8 medan + prompt peranan ejen | Tiada arahan kabur, tiada medan tertinggal, output boleh diuji |
| 2 | AI Systems Architect | Reka bangunan — komponen, aliran data, titik simpan, lapisan kegagalan, kos/had | Rajah komponen + kontrak antara bahagian + pelan berperingkat | Setiap komponen ada pemilik, input, output, cara uji |
| 3 | Multi-Agent Architect | Reka pasukan — siapa ketua/pekerja/pemeriksa, urutan, kebergantungan, elak pertindihan | Papan tugasan (ejen · slug · tugasan · kebergantungan · gate) | Tiada ejen tanpa tugasan, tiada tugasan tanpa ejen bernama |
| 4 | Agent Factory Architect | Reka kilang — acuan persona, tier, ujian lulus/gagal, pendaftaran roster, persaraan | Ejen baharu berdaftar + bukti ujian + rekod tier | Ejen baharu lulus ujian tanpa Ketua sentuh failnya |

Undang-undang tetap #6 (`SOUL.md` baris 64): **empat tahap mesti lengkap sebelum lulus** —
prompt jelas (T1) → seni bina kukuh (T2) → pasukan lengkap (T3) → kilang berjalan (T4).
Melangkau tahap = `NEEDS_WORK`.

### Pemetaan: peranan Ketua ↔ lapisan video

| Tahap | Lapisan video yang dijawab | Sebab |
|---|---|---|
| 1 | 11 (SOP = skill), 12 (backup) | Prompt/SOP ialah arahan bertulis yang menentukan bila skill & rutin dipanggil |
| 2 | 1 (infrastruktur), 2 (otak/model), 10 (workspace) | Seni bina menetapkan mesin, model per ejen, dan pengasingan workspace |
| 3 | 4 (struktur pasukan), 5 (lead agent), 6 (papan) | Pasukan, lead, dan papan tugasan ialah satu reka bentuk yang sama |
| 4 | 7 (memori pendek), 8 (memori panjang), 9 (pengetahuan), 13 (MCP), 14 (automasi) | Kilang menjana, mendaftar, menguji, dan mempersarakan ejen melalui aliran 8 sistem + memori |

Nota: lapisan 3 (saluran) ialah prasyarat di luar keempat-empat tahap — ia saluran
komunikasi bos, bukan kerja arkitek.

## 11 lapisan video itu, dan status kita

| # | Lapisan | Maksud dalam video | Status kita | Bukti |
|---|---|---|---|---|
| 1 | Infrastruktur | Mesin 24 jam (mini PC / VPS) | **SEPARA** | Telefon Termux — Android boleh bunuh proses |
| 2 | Otak / model | Model berbeza per ejen; model terbaik untuk lead | **SEPARA** | Semua guna deepseek-v4.1-flash; tiada model per ejen |
| 3 | Saluran | Telegram untuk bos, WhatsApp untuk pelanggan | **ADA** | @ainafz_bot, gateway aktif |
| 4 | Struktur pasukan | Satu profil per kerja + 1 lead agent | **PALSU** | 282 "ejen" hanya teks persona dalam satu proses |
| 5 | Lead agent | Manage sub-ejen + onboarding ejen baru | **BARU DIBETULKAN** | `SOUL.md` 20–47: Ketua = 4 peranan bertingkat (T1 prompt → T2 seni bina → T3 pasukan → T4 kilang); tak buat kerja tangan. Selaras: `OPERASI.md` §1, `docs/KETUA.md` §1, `docs/LAPORAN-4-PERANAN.md` |
| 6 | Papan / dashboard | Kanban, pejabat 2D, status bekerja/tidur | **SEPARA** | 127.0.0.1:8787 + panel EJEN BERTUGAS (baru) |
| 7 | Memori pendek | profile / soul / user / memory / agent.md | **ADA** | ~/.hermes20/memories, SOUL.md |
| 8 | Memori panjang | Obsidian + pautan dua hala | **TIADA** | skill obsidian ada, vault belum disambung |
| 9 | Pengetahuan | LLM Wiki = SOP/FAQ/fakta (bukan memori) | **TIADA** | skill llm-wiki ada, belum di-setup |
| 10 | Workspace | Fail kerja berasingan per ejen | **TIADA** | Semua ejen tulis ke folder yang sama |
| 11 | SOP = skill | Skill dipanggil bila tugas tertentu | **ADA** | ~/.hermes20/skills (100+) |
| 12 | Backup | Cron malam → GitHub, ejen jaga dirinya | **TIADA** | Tiada repo backup automatik |
| 13 | Tool luar (MCP) | Port universal ke sistem pihak ketiga | **TIADA** | Tiada MCP server didaftar |
| 14 | Automasi | Cron + workflow | **SEPARA** | 6+ cron; workflow DAG hanya dalam runner |

## Kesimpulan penting (punca rungutan bos)

"282 ejen" kita **bukan** pasukan seperti dalam video. Ia **satu** Hermes yang memakai 282 teks persona.
Sebab itu tiada ejen kelihatan "bekerja" di papan: tiada proses, tiada memori sendiri, tiada workspace sendiri.
Video itu buat satu profil Hermes per kerja — kita belum.

## Apa yang perlu ditambah (susunan keutamaan)

**P1 — Jadikan Ketua benar-benar pengarah** (siap: `SOUL.md` baharu + panel EJEN BERTUGAS)

> Nota 2026-11-06: empat tahap arkitek kini **ditakrifkan** dalam `SOUL.md` (baris 20–47,
> undang-undang tetap #6 baris 64), diringkaskan dalam `OPERASI.md` §1 dan `docs/KETUA.md` §1,
> dan disahkan dengan bukti shell dalam `docs/LAPORAN-4-PERANAN.md`. Lihat seksyen
> "Empat peranan Ketua (bertingkat)" di atas.

**P2 — Buat 4–6 ejen SEBENAR dahulu, bukan 282**
- `finance`, `sales`, `marketing`, `ops`, `engineering`, `assistant`
- Setiap satu: profil Hermes sendiri (memori, skill, workspace, model)
- Lead = Ketua (profil `default`)

**P3 — Workspace per ejen**
`~/.hermes20/workspaces/<ejen>/` + arahan: hanya tulis dalam folder sendiri.

**P4 — Memori panjang (Obsidian)**
Vault `~/vault/` + pautan dua hala; ejen tulis nota, bukan tampal dalam memori.

**P5 — Pengetahuan (LLM Wiki)**
SOP, FAQ, harga, templat → `knowledge_base/` dalam format wiki, bukan memori.

**P6 — Backup malam ke GitHub**
Cron 2:00 pagi: `git add -A && commit && push` untuk ~/.hermes20 (tanpa token/rahsia).

**P7 — MCP untuk sistem luar**
Bila perlu sentuh sistem pihak ketiga (Google Workspace, Kanban, app sendiri).

**P8 — Mesin 24 jam**
Termux telefon tak sesuai untuk 24/7. Pilihan: VPS murah, atau telefon dicas + `termux-wake-lock` (masih rapuh).

## Apa yang TIDAK perlu ditambah

- Model baru. Video itu sendiri kata model bukan nilai utama — SOP dan workflow yang bernilai.
- 282 profil. Kos dan penyelenggaraan melampaui guna.
