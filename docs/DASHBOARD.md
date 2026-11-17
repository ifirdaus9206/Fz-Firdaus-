# DASHBOARD HERMES — dijalankan di Termux (telefon)

Tarikh bina: 2026-11-17 · Home: `~/.hermes20` · Versi Hermes: 0.20.0

Sama dengan dashboard yang bos jalankan di PC — tetapi ini pada telefon (Redmi Note 15 Pro 5G).

## URL

| Jenis | URL | Nota |
|---|---|---|
| Publik (sementara) | lihat `~/.hermes20/dashboard_url.txt` | Quick tunnel Cloudflare; URL **bertukar** setiap tunnel mula semula |
| LAN (WiFi sama) | `http://192.168.0.11:9119/` | PC/telefon lain dalam WiFi yang sama |
| Tempatan | `http://127.0.0.1:9119/` | Dari dalam telefon sahaja |

## Log masuk

- Username: `firdaus`
- Password: **tidak ditulis di sini** — baca fail `~/.hermes20/secrets/dashboard_login.txt` (chmod 600)
- Kaedah: plugin `dashboard_auth/basic` (scrypt hash dalam `config.yaml` → `dashboard.basic_auth`)

## Servis (runit — hidup semula sendiri, mula automatik bila boot)

| Servis | Fungsi | Log |
|---|---|---|
| `hermes-dashboard` | web UI pada `0.0.0.0:9119` | `~/.hermes20/logs/hermes-dashboard.log` |
| `hermes-dash-tunnel` | Cloudflare quick tunnel → 9119 | `~/.hermes20/logs/hermes-dash-tunnel.log` |

Perintah:

```bash
sv status hermes-dashboard hermes-dash-tunnel     # tengok status
sv restart hermes-dashboard                        # mula semula UI
sv restart hermes-dash-tunnel                      # mula semula tunnel (URL baharu)
cat ~/.hermes20/dashboard_url.txt                  # URL publik semasa
bash ~/.hermes20/scripts/dash_verify.sh            # uji penuh: pagar login + login + API
```

Skrip sokongan: `~/.hermes20/scripts/dash_tunnel.sh`

## Sebab bind 0.0.0.0 (bukan 127.0.0.1)

Hermes menolak Host header bukan-loopback (`400 Invalid Host header`) bila bind loopback.
Bind `0.0.0.0` + `dashboard.basic_auth` = satu-satunya cara tunnel berfungsi **dengan** login.
Tanpa auth dikonfigurasi, Hermes enggan bind awam (fail-closed).

## Bukti ujian (2026-11-17)

- `GET /` → `302 → /login?next=%2F`
- `GET /login` → `200`, `<title>Sign in — Hermes Agent</title>`
- `POST /auth/password-login` → `200 {"ok":true,"next":"/"}`
- `GET /` dengan cookie → `200`, `<title>Hermes Agent - Dashboard</title>`
- `/assets/index-*.js` → `200`, `/api/status` → `200` (`version 0.20.0`, `gateway_running true`)

## Web UI dibina dari sumber

`web_dist` tiada pada mula; dibina dengan:

```bash
cd ~/.hermes20/tools/hermes-source/hermes-agent/web
npm install && npm run build     # output → hermes_cli/web_dist
```

Servis guna `--skip-build` supaya mula pantas (~3s).

## Had / amaran

1. Quick tunnel **tiada jaminan uptime** dan URL bertukar bila restart. Untuk URL tetap:
   guna named tunnel Cloudflare (perlu akaun Cloudflare + domain) — belum dibuat.
2. Telefon mesti kekal hidup & ada internet; Android mungkin bunuh proses bila bateri
   optimisasi — tambah Termux ke senarai "tanpa had" jika tunnel mati sendiri.
3. Jangan kongsikan URL + password dalam kumpulan/chat awam.

## Nota teknikal (pelajaran sebenar)

1. `svlogd` (log/run) tidak mahu hidup untuk servis baharu di peranti ini — `supervise/ok`
   tidak pernah tercipta. Penyelesaian dipakai: redirect terus dalam `run`
   (`exec >> ~/.hermes20/logs/<servis>.log 2>&1`). Rotation belum ada; log kecil.
2. Jangan guna `pkill -f "hermes dashboard"` dari dalam shell Hermes — corak itu padan
   dengan shell pemanggil sendiri dan membunuh sesi. Bunuh ikut PID.
3. Selepas `sv restart`, pastikan hanya SATU proses memegang port 9119; proses orphan
   dari ujian manual akan buat servis runit crash-loop (port sudah dipakai).

## Konsol 8787 — tab WEB UI (dibina 2026-11-17)

Tab baharu dalam konsol `127.0.0.1:8787` untuk urus dashboard tanpa terminal:

| Bahagian | Fungsi |
|---|---|
| Kad atas | port 9119 buka/mati · status 2 servis · URL dikemas kini bila |
| URL PUBLIK | URL penuh + butang **BUKA**, **SALIN URL**, **UJI PENUH** |
| SERVIS | HIDUP / MULA SEMULA / LOG untuk `hermes-dashboard` + `hermes-dash-tunnel` |
| TANGGUH MATI | 4 langkah semak selepas reboot |
| LOG UJIAN | output `dash_verify.sh` (5 tanda) terus di skrin |

API sokongan: `GET /api/web`, `POST /api/web/verify` (perlu `X-Console-Token`),
servis didaftar dalam `SVC_ALLOW` supaya butang `/api/svc/{name}` berfungsi.

Fail disentuh: `app.py` (SVC_ALLOW + 2 endpoint), `static/index.html` (tab + pane),
`static/app.js` (loadWeb/webSvc/webVerify + routing). Sandaran: `hermes-console/.bak-webtab/`.

## Tahan mati (reboot)

`~/.termux/boot/10-hermes-gateway.sh` kini turut menjalankan:

```sh
sv up "$PREFIX/var/service/hermes-dashboard"
sv up "$PREFIX/var/service/hermes-dash-tunnel"
```

Syarat: app **Termux:Boot** dipasang (APK ada di `~/storage/downloads/TermuxBoot.apk`).
Selepas reboot: buka tab WEB UI → dua servis mesti `run` → tekan UJI PENUH.

## Notifikasi URL (cron)

Quick tunnel tukar URL bila restart. Cron `*/15 * * * *` (job `b3aa5823840f`,
no-agent) jalankan `~/.hermes20/scripts/dash_url_notify.sh`:

- URL sama → senyap (tiada mesej)
- URL berubah → uji `/login` dulu; jika `200`, hantar URL baharu ke Telegram
- URL berubah tetapi mati → hantar amaran dengan kod HTTP

## Had tetap: URL kekal?

URL **tetap** perlukan salah satu daripada ini (kedua-duanya belum ada di telefon):

1. Akaun Cloudflare + domain dalam akaun itu → named tunnel (`cloudflared tunnel create`,
   DNS CNAME ke `<uuid>.cfargotunnel.com`). `~/.cloudflared/cert.pem` tiada = belum login.
2. Akaun Tailscale + Funnel → URL tetap `https://<nama>.<tailnet>.ts.net`.

Selagi tiada, quick tunnel + notifikasi cron di atas adalah penyelesaian terbaik.
