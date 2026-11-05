---
name: hermes-conversation-context-recovery
description: Recover a prior user request in a fresh Hermes session.
---

# Hermes Conversation Context Recovery

Guna bila pengguna merujuk sesuatu yang "tadi" / "semalam" / "macam aku minta tadi" tetapi sesi
semasa bermula baru (`history=0`). Jangan teka dan jangan terus tanya kosong — cari bukti dahulu.

## Bila skill ini dipakai
- Pengguna membalas mesej lama tetapi sesi baru tiada konteks (`history=0` dalam `agent.log`).
- Pengguna kata "tadi bukan aku minta X ke", "macam mana dengan Y yang aku suruh".
- `session_search` tidak menemui apa-apa atau hanya menemui ringkasan tanpa mesej asal.

## Langkah

1. **Dapatkan `reply_to_id` dari log gateway** (paling cepat, ini kunci utama):
   ```bash
   grep -n "inbound message: platform=telegram" ~/.hermes20/logs/gateway.log | tail -5
   ```
   Baris itu mengandungi `chat=`, `msg='...'`, `reply_to_id=`. Kalau `reply_to_text` kosong,
   mesej yang dibalas berada dalam sesi lain — cari ikut `reply_to_id`/`msg` dalam `state.db`.

2. **Cari mesej asal dalam `state.db`** — JANGAN `grep -rl ~/.hermes20`; ia recurse
   `agency-agents-app/node_modules` dan timeout lebih 180s. Guna query SQL read-only:
   ```python
   import sqlite3
   con = sqlite3.connect("file:~/.hermes20/state.db?mode=ro", uri=True)
   rows = con.execute("""
       SELECT id, role, timestamp, substr(content,1,800)
       FROM messages
       WHERE session_id=? AND role=? AND lower(content) LIKE ?
       ORDER BY id
   """, ("<session_id>", "user", "%format%")).fetchall()
   ```
   Untuk sesi tidak diketahui: `ORDER BY id DESC LIMIT 40` tanpa penapis session, atau
   `scripts/find_message.py --recent 5 --contains "kata kunci"`.

3. **Semak run store konsol** untuk arahan yang diberi melalui UI, bukan chat:
   - `~/hermes-console/runs/` — setiap run (`<id>/` mengandungi brief, jawapan ejen, inbox).
   - `~/hermes-console/data/reports`, `~/hermes-console/data/steps`.
   - `~/hermes-console/agency_runner.py` — `load(run_id)` / `append_inbox()`.

4. **Semak fail hasil kerja** yang mungkin menjadi rujukan "format masing-masing":
   - `~/<projek>/README.md`, `LAPORAN-QA.md`, `INVENTORY.json`
   - `~/.hermes20/system/*.md` (modul prompt sistem)

5. **Baru jawab.** Jika konteks masih kabur selepas carian, jangan beri senarai panjang —
   beri **pilihan bernombor dalam Bahasa Melayu mudah**, satu baris setiap pilihan, minta pengguna
   balas dengan nombor. Ini mengikut profil pengguna: suka langkah bernombor, benci jargon.

## Pitfalls
- `grep -rl` merentas `~/.hermes20` masuk `node_modules` dan timeout. Hadkan carian kepada
  `state.db`, `logs/gateway.log`, `~/hermes-console/runs`.
- `session_search(query=...)` guna FTS5; kata sendi Melayu ("masing-masing", "tadi") sering tidak
  sepadan. Cari perkataan kandungan sebenar (nama projek, nama fail, "format", "deliverable").
- Jangan andaikan "tadi" = sesi terakhir dalam senarai. Sesi Telegram berpecah bila gateway mula
  sesi baru; `reply_to_id` dalam `gateway.log` lebih dipercayai daripada senarai sesi.
- Jangan bina semula jawapan lama daripada ringkasan `bookend_end` sahaja — ringkasan hilang
  butiran arahan. Ambil mesej penuh pengguna dari jadual `messages`.
- Jika `reply_to_text` kosong dalam log, mesej asal mungkin tiada dalam DB. Dalam kes itu, tanya
  dengan pilihan bernombor — jangan reka.

## Pengesahan
- Petik sekurang-kurangnya satu ayat mesej asal pengguna sebelum membuat kesimpulan.
- Nyatakan sumber: session id + id mesej, atau laluan fail brief/run.
- Jika tiada bukti ditemui, katakan terus "tiada rekod" dan tanya dengan pilihan bernombor.
