# Bot senyap walaupun proses gerbang hidup

Keluhan: "di Telegram tak boleh jalan lagi" sementara `sv status hermes-gateway` = `run:` dan
heartbeat sentiasa baru. Urutan siasatan di bawah berjaya mengecilkan punca dan memisahkan
"gerbang mati" daripada "rangkaian Telegram" daripada "mesej tidak pernah keluar dari telefon".

## 1. Gerbang benar-benar hidup?

```bash
sv status hermes-gateway
ls -l ~/.hermes20/state/gateway.heartbeat      # mtime mesti < 2 minit
cat ~/.hermes20/state/gateway.lifecycle.json   # {"phase":"running","pid":...}
cat ~/.hermes20/gateway.lock                   # pid mesti sama dengan proses hidup
pgrep -af "hermes gateway run"
```

Heartbeat baru + `phase=running` bermakna loop induk hidup. Ia **tidak** bermakna poll Telegram
hidup — dua perkara berbeza.

Jangan uji hayat gerbang dengan `readlink /proc/PID/exe == $PREFIX/bin/hermes`: gerbang berjalan
di bawah venv python (`…/venv/bin/python …/bin/hermes gateway run`), jadi ujian itu memberi
**0 proses → "gerbang mati" palsu** dalam watchdog. Ambil `pid` daripada heartbeat/lifecycle dan
`kill -0`, dan hanya jatuh ke imbasan `cmdline` sebagai sandaran:

```bash
PIDH=$(python3 -c "import json;print(json.load(open('$HOME/.hermes20/state/gateway.heartbeat'))['pid'])")
kill -0 "$PIDH" 2>/dev/null && echo HIDUP
# sandaran: for p in /proc/[0-9]*; do tr '\0' ' ' < "$p/cmdline" 2>/dev/null \
#             | grep -q "gateway run" && echo "HIDUP ${p#/proc/}"; done
```

## 2. Pangkalan data: adakah mesej masuk direkod?

`messages` menyimpan setiap turn. Kalau tiada `inbound message` dalam `gateway.log` DAN tiada
baris baharu dalam `messages` untuk sesi Telegram sejak masa X, mesej bos tidak pernah diproses:

```bash
grep -n "inbound message" ~/.hermes20/logs/gateway.log | tail -3
python3 -c "
import sqlite3,os
c=sqlite3.connect('file:'+os.path.expanduser('~/.hermes20/state.db')+'?mode=ro',uri=True)
for r in c.execute('select id,session_id,role,datetime(timestamp,\"unixepoch\",\"localtime\") from messages order by timestamp desc limit 5'): print(r)"
```

## 3. Bot API: token, webhook, baris gilir

```bash
set -a; . ~/.hermes20/.env; set +a
curl -s -m 15 "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"          # ok + username
curl -s -m 15 "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo" # url="" = polling
curl -s -m 20 "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getUpdates?offset=-1&limit=1&timeout=0"
```

Tafsiran yang penting:

- `url` bukan kosong → webhook aktif; polling akan dapat **409 Conflict** dan bot senyap.
- `pending_update_count` > 0 dengan `url` kosong → tiada sesiapa mengambil update.
- `getUpdates?offset=-1` memulangkan **ok** tanpa 409 → gerbang tidak sedang long-poll pada saat
  itu (sama ada mati, atau di antara pusingan). Panggil dua tiga kali berasingan sebelum membuat
  kesimpulan.
- `offset=-1` **tidak** mengesahkan update, jadi ia selamat dijalankan; jangan guna offset positif
  pada bot yang sedang di-poll gerbang.

## 4. Rangkaian — jangan tuduh DNS/IP fallback tanpa ujian

Gerbang ini log `Primary api.telegram.org connection failed … trying fallback IPs`. Uji IP itu
sendiri sebelum menganggapnya punca:

```bash
curl -s -o /dev/null -m 8 -w "HTTP %{http_code}\n" --resolve api.telegram.org:443:149.154.166.110 https://api.telegram.org/
curl -4 -s -o /dev/null -m 8 -w "HTTP %{http_code} ip=%{remote_ip}\n" https://api.telegram.org/
```

`302` pada kedua-dua = rangkaian sihat; jangan buang masa pada konfigurasi fallback. (Jangan guna
`getent` — tiada dalam Termux.) Lakukan 8–10 cubaan berturut: 9/10 lulus dengan 1× `000` adalah
kehilangan paket biasa, bukan punca bot senyap.

## 5. Bukti keluar vs bukti masuk

- Keluar: `hermes send -t telegram "..."` → print `Sent to telegram home channel (chat_id: …)`.
  Ini membuktikan token + rangkaian + allowlist tujuan, dan boleh dijalankan tanpa bos.
- Masuk: **tiada cara** membuktikannya tanpa satu mesej sebenar daripada pengguna. Jangan tulis
  "Telegram sudah pulih" selepas hanya membuktikan keluar; minta satu mesej dan sahkan baris
  `inbound message:` muncul dalam `gateway.log`.

## 6. Ikon jam pada mesej pengguna = mesej belum keluar dari telefon

Bila bos berkata mesejnya "sedang menunggu" / bergambar jam, itu penunjuk **klien** Telegram, bukan
pelayan. Tiga bukti yang mesti dikumpul serentak sebelum menyalahkan bot:

| Bukti | Nilai | Makna |
|---|---|---|
| `pending_update_count` | `0` | Pelayan Telegram tidak menyimpan apa-apa untuk bot ini |
| `grep "inbound message"` | tiada baris baharu | Gerbang tidak menerima apa-apa |
| TCP 443 ke IP DC (`149.154.175.50`, `149.154.167.51`, `91.108.56.130`, `149.154.175.100`) | semua OK | Rangkaian peranti boleh sampai ke Telegram |
| `sv status` + heartbeat | `run:` + nadi baru | Gerbang sendiri sihat |

Gabungan itu = mesej tidak pernah meninggalkan app Telegram. Punca lazim di telefon: proksi mati
dalam Settings → Data and Storage → Proxy, app tersekat selepas berjam di latar, atau sekatan
data/bateri per-app. Jangan tawarkan "restart gateway" sebagai penyelesaian untuk gejala ini —
ia tidak menyentuh punca.

Ujian TCP tanpa `nc`:

```bash
python3 - <<'EOF'
import socket
for name, ip in {"DC2":"149.154.167.51","DC4":"149.154.167.91","DC5":"91.108.56.130","BotAPI":"149.154.166.110"}.items():
    s=socket.socket(); s.settimeout(6)
    try: s.connect((ip,443)); print(name, ip, "OK")
    except Exception as e: print(name, ip, "GAGAL", e)
    finally: s.close()
EOF
```

## 7. Jadikan kejadian ini dikesan automatik (bukan dijumpai berjam kemudian)

Dua watchdog berasingan, kedua-duanya `no_agent` cron `*/5`, senyap bila sihat:

- `gw_alert.sh` — gerbang mati / nadi beku / kematian tidak bersih (lihat
  `gateway-death-watchdog.md`).
- `tg_watch.sh` — **laluan masuk**: `pending_update_count` > 0 pada **dua semakan berturut**
  (satu semakan sahaja boleh jadi saat gerbang sedang sibuk) dan/atau gerbang mati.
  Anti-spam guna stamp `tg|$PROB|$PEND`; hook ujian `TG_WATCH_FAKE_PEND=<n>` +
  `TG_WATCH_ROOT=<tmpdir>` + `TG_WATCH_NO_EMAIL=1` supaya cabang amaran boleh dibuktikan tanpa
  menyentuh API sebenar.

**Saluran kedua (e-mel) wajib** apabila amaran itu sendiri tentang Telegram: kalau bot yang rosak,
amaran melalui bot tidak sampai. Guna Gmail SMTP SSL dari kredensial yang sudah ada dalam `.env`
(`GMAIL_USER`, `GMAIL_APP_PASSWORD`), hantar ke diri sendiri; jangan simpan kata laluan dalam
skrip dan jangan cetak nilai dalam chat. Sahkan penghantaran dengan membaca balik IMAP
(`SEARCH (SUBJECT "…")`) — `smtplib` pulang tanpa ralat hanyalah "diterima pelayan", bukan
"ada dalam peti masuk". Nota: pada akaun ini `imaplib` gagal `SELECT "[Gmail]/All Mail"` dan
`"[Gmail]/Sent Mail"`, tetapi `INBOX` memadankan salinan yang dihantar ke diri sendiri.

Kedua-dua skrip menulis mesej yang sama ke stdout (dihantar cron) dan ke e-mel; mesej mesti
menyebut butang **RESET GERBANG** dan URL konsol semasa supaya bos boleh bertindak dari telefon.

## Punca yang disahkan vs belum (sesi 2026-11-24)

- Disahkan: gerbang lama dibunuh tidak bersih (SIGKILL/OOM) lalu tinggal `gateway.lock` dan proses
  yatim; selepas dibunuh + satu pokok runit dibina semula, gateway baharu naik, `getMe`/`send`
  lulus. Mesej yang dihantar semasa tetingkap gerbang mati berkemungkinan sudah "confirmed" oleh
  `getUpdates` instance yang nazak — ia hilang, bukan tertangguh.
- Belum disahkan: laluan masuk selepas restart (perlu mesej bos). Bos melaporkan ikon jam pada dua
  mesej, iaitu bukti mesej tidak keluar dari telefon — bukan bukti bot gagal.
