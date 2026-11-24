# docs/RUNBOOK-INSIDEN.md — Gejala → Punca → Tindakan

**Dikemas kini:** 2026-11-24 · Guna bersama `docs/SERVIS.md`

## Cara guna

1. Cari gejala dalam jadual.
2. Jalankan **Semak** dahulu — jangan terus baiki.
3. Ikut **Tindakan** satu langkah demi satu langkah.
4. Sahkan dengan `hs` selepas setiap pembetulan.

## Jadual insiden

| # | Gejala | Semak | Punca biasanya | Tindakan |
|---|---|---|---|---|
| 1 | Bot Telegram tidak jawab | `hs` · `tail -20 logs/gateway.log` | Gateway mati / token tamat / long-poll kedua (409) | `sv restart hermes-gateway` → tunggu 10 s → uji mesej |
| 2 | Konsol tidak boleh dibuka | `hs` · `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8787/` | Konsol mati / proses yatim genggam port | `hermes-restart`; jika masih → bunuh PID yatim, `sv up hermes-console` |
| 3 | Konsol dibuka tetapi kosong/putih | DevTools → Console | Cache CSS/JS lama | Naikkan `theme.css?v=N` & `app.js?v=N`, muat semula keras |
| 4 | Teks tidak nampak (blok hitam) | Bandingkan dengan `--oc-*` | Kelas baharu tiada override cerah | Tambah blok `TERANG vN` dalam `theme.css`, naikkan versi |
| 5 | Tunnel 502 / 1033 | `curl -I <url>` · `ps aux \| grep cloudflared` | cloudflared mati atau menghala 9119 | `sv restart hermes-dash-tunnel` → URL baharu dalam `dashboard_url.txt` |
| 6 | URL tunnel bertukar tiba-tiba | `cat dashboard_url.txt` | Quick tunnel dapat nama baharu setiap mula | Maklumkan bos; jangka named tunnel bila domain ada |
| 7 | `127.0.0.1:8787` gagal dari telefon | — | `127.0.0.1` ialah telefon itu sendiri | Guna `http://<IP-LAN>:8787` atau tunnel |
| 8 | "command not found: hermes-console" | `command -v sv` | Nama servis ditaip sebagai arahan, atau berada dalam shell `[root]` | Guna `hs` / `sv status hermes-console`; keluar shell root |
| 9 | Cron tidak jalan | `hermes cron list` · `ls cron/` | Job pause / konsol mati ketika trigger | `hermes cron resume <id>`; uji `POST /api/cron/{id}` `{"action":"run"}` |
| 10 | E-mel tidak disusun | `ls ~/vault/email-inbox` · `tail logs/email*.log` | IMAP gagal / kata laluan app tamat | Uji `scripts/email_fetch.py`; kemas kini app password |
| 11 | Kerja ejen tersangkut `running` | `GET /api/agency/run/{id}` | Ejen gagal tanpa lapor | `POST /api/run/{id}/stop` → hantar semula dengan konteks tambahan |
| 12 | `sv restart` tergantung | `sv status <svc>` | runsv menunggu anak yang tersekat | `kill -9 <pid>` kemudian `sv up <svc>` |
| 13 | Cakera penuh | `df -h /data` · `du -sh ~/.hermes20/*` | `archive/`, log, snapshot lama | Pindah arkib ke `/sdcard`, rotate log |
| 14 | Memori tidak dikemas kini | `ls ~/vault/memori/02-panjang/` | Cron 23:30 terlepas / skrip gagal | `python3 scripts/memori_panjang.py 7` manual |
| 15 | Sandaran GitHub senyap tetapi tiada commit | `cd ~/.hermes20 && git log -1` · `git status` | Imbasan rahsia batalkan commit / tiada perubahan | Baca amaran skrip, betulkan corak, jalankan semula |
| 16 | `agents.json` rosak selepas CRUD | `GET /api/watak` | Tulis separuh jalan | Pulih `backups/plugins/agents.json.bak-watak` |

## Prinsip pulih

1. **Jangan panik-padam.** Sandaran dahulu.
2. **Satu perubahan satu ujian** — jangan baiki 3 benda serentak.
3. **Baca log sebelum teka.** `logs/gateway.log`, `logs/errors.log`, `logs/hermes-console/`.
4. **Catat dalam `knowledge_base/log.md`** selepas insiden selesai.
