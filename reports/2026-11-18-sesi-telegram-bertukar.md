# Laporan: Sesi Telegram bertukar setiap mesej — punca & pembetulan

Tarikh: 2026-11-18 · Oleh: Ketua · Status: **kod dibetulkan + diuji; menunggu 1 restart gateway**

## Gejala
Setiap kali mesej dihantar di Telegram, sesi sembang bertukar (konteks hilang, mesej nampak
"baru"). Hanya menekan `/new` sepatutnya memulakan sesi baharu.

## Punca
`~/.hermes20/tools/hermes-source/hermes-agent/plugins/platforms/telegram/adapter.py`
→ fungsi `_effective_message_thread_id()` baris 7989:

```python
if chat_type == "private" and is_topic_message:
    return str(raw)      # <-- thread id DM diterima bulat-bulat
```

Telegram menghantar `is_topic_message=True` + `message_thread_id` pada DM. Fungsi inilah yang
membina **kunci sesi**, jadi setiap thread id berbeza = sesi baharu.
Nota: tampalan 2026-11-17 dulu hanya membaiki `_source_from_message_for_auth()` (laluan
kebenaran), bukan laluan routing ini — sebab itu gejala berterusan.

Bukti: 8 sesi terakhir bagi chat 1312929583 mempunyai kunci
`agent:main:telegram:dm:1312929583:<thread>` dengan thread berbeza (26248, 26154, 26139, 26127…).

## Pembetulan
1. `_effective_message_thread_id()` kini **menggerbang** thread id DM pada konfigurasi
   `extra.dm_topics` sahaja (sama seperti fungsi auth). DM biasa → `None` → satu sesi.
2. `_dm_topic_chat_ids` dicermin ke peringkat kelas (`type(self)._dm_topic_chat_ids = …`)
   kerana fungsi itu `classmethod`.
3. Kedua-dua salinan fail dikemas kini (md5 sama): `hermes-agent/plugins/...` dan
   `tools/hermes-source/plugins/...`.
4. Migrasi `state.db` (sandaran: `state.db.bak-pra-migrasi-1328`):
   - sesi semasa `20261118_130639_99d6d976` → kunci kanonik `agent:main:telegram:dm:1312929583`,
     `thread_id=NULL` (sejarah 116 mesej kekal)
   - sesi lama 20261110_…3109309a → `…:legacy-20261110`, `archived=1`
   - `gateway_routing` → menunjuk ke sesi semasa
5. `~/hermes-console/app.py`: butang **restart** untuk `hermes-gateway` kini melakukan
   *handover* sebenar (`pkill` proses gateway; penunggu runit menghidupkan semula ~5s), kerana
   skrip `run` baharu menunggu dan `sv restart` sahaja tidak menggantikan gateway.

## Ujian (lulus)
`~/.hermes20/scripts/probe_dm_thread_gate.py`:
```
DM topic-flag tanpa konfigurasi -> None   (mesti None)      OK
DM topic-flag DENGAN konfigurasi -> 26248 (mesti 26248)     OK
Forum group -> 77                         (mesti 77)        OK
exit=0
```

## Baki satu langkah
Proses gateway yang sedang berjalan bermula **13:08**, fail ditampal **13:28** — kod lama masih
dalam memori. Satu restart diperlukan (butang di konsol 8787 → Servis → Gateway → Restart, atau
`hermes gateway restart` dari shell Termux). Selepas itu semua mesej Telegram masuk ke SATU sesi.
