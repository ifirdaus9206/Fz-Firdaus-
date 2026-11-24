# docs/ARKITEKTUR.md — Gambaran Penuh Sistem

**Dikemas kini:** 2026-11-24 · **Home:** `~/.hermes20` · **Hermes:** v0.20.0

## 1. Rajah besar

```
                        ┌──────────────────────────────┐
   Bos (Telegram) ─────►│  hermes-gateway (runit)      │
                        │  bot · sesi · DM/topik       │
                        └───────────┬──────────────────┘
                                    │ mesej
                                    ▼
                        ┌──────────────────────────────┐
                        │  Ketua (SOUL.md)             │
                        │  4 peranan bertingkat:       │
                        │  Prompt→Systems→Multi-Agent  │
                        │  →Agent Factory              │
                        └───┬───────────┬───────────┬──┘
                            │           │           │
              ┌─────────────▼──┐  ┌─────▼──────┐  ┌─▼─────────────┐
              │ system/ 8 modul│  │ skills/114 │  │ agency 282 ejen│
              │ factory·role·  │  │ 30 kategori│  │ 21 divisi      │
              │ workflow·orch· │  └────────────┘  └─┬──────────────┘
              │ qa·recovery·   │                    │
              │ completion·mem │◄───────────────────┘
              └───┬────────────┘   brief 8 medan → kerja
                  │
      ┌───────────▼────────────┐        ┌────────────────────────┐
      │ Memori dua lapis       │        │ Konsol 8787 (FastAPI)  │
      │ 01-pendek (harian)     │◄──────►│ 72 laluan API          │
      │ 02-panjang (kekal)     │        │ 14 tab · 6 tema        │
      │ 03-pelajaran (bulanan) │        └───────────┬────────────┘
      └────────────────────────┘                    │
                                                    ▼
      ┌────────────────────────┐        ┌────────────────────────┐
      │ state.db (SQLite)      │        │ Tunnel Cloudflare      │
      │ sesi · cron · kanban   │        │ → 127.0.0.1:8787       │
      └────────────────────────┘        └────────────────────────┘
```

## 2. Lapisan

| Lapisan | Komponen | Tanggungjawab |
|---|---|---|
| **Masuk** | `hermes-gateway` | Terima mesej Telegram, jaga sesi & topik |
| **Fikir** | `SOUL.md` + `system/` 8 modul | Pecah arahan → brief → pilih ejen → semak |
| **Keupayaan** | `skills/` 114 · `plugins/` | Alat boleh guna semula |
| **Pekerja** | `agency-agents/` 282 ejen | Laksana kerja mengikut brief |
| **Ingatan** | `~/vault/memori/` 3 lapis | Belajar daripada kerja lepas |
| **Kawalan** | Konsol 8787 | Pantau, hantar kerja, urus ejen/cron/email |
| **Data** | `state.db`, `kanban.db`, `projects.db` | Sesi, jadual, papan tugas |
| **Keluar** | `/sdcard/Documents/UIM` | Hasil untuk bos (sehala, sha256) |
| **Jaga** | `hermes-keeper` | Wake-lock + hidupkan semula servis |

## 3. Aliran satu kerja

```
bos mesej
  → gateway
  → Ketua faham & pecah (T1)
  → reka seni bina jika perlu (T2)
  → pilih ejen mengikut tier (T3)
  → tulis brief 8 medan
  → POST /api/agency/plan → POST /api/agency/run/{id}
  → ejen laksana
  → qa_system semak bukti
  → completion_system sahkan
  → lapor papan kepada bos
  → memory_manager simpan pelajaran
```

## 4. Prinsip seni bina

1. **Ketua tidak buat kerja tangan** — hanya faham, arah, semak, putus.
2. **Tiada arahan tanpa ejen bernama** — setiap tugasan keluar sebagai RUN.
3. **Tiada lulus tanpa bukti** — laluan fail, keluaran arahan, nombor ujian.
4. **Satu servis satu tugas** — tiada pertindihan port.
5. **Satu konsol** — 8787 sahaja (9119 & 8790 dibersarakan).
6. **Memori dua lapis** — pendek untuk hari ini, panjang untuk selama-lamanya.
7. **Rahsia tidak keluar** — `.env`, token, DB tidak masuk GitHub.
8. **Pulih sendiri** — keeper bangkitkan servis dalam 60 saat.
