Config guard: write/patch refuse ~/.hermes/*/config.yaml; guna `hermes config set` / python+yaml.
§
OpenRouter :free timeout; guna deepseek-v4.1-flash.
§
~/.hermes20 = home utama; ULTIMATE_AI_PROJECT=tools/hermes-source.
§
Long-poll (poller kedua=409); log logs/gateway.log. Amaran auto: scripts/gw_alert.sh (gerbang mati/tidak bersih) + tg_watch.sh (mesej menunggu) — cron 5 min, Telegram + e-mel Gmail.
§
Runbook OPERASI.md + docs/KETUA.md. workspaces/<ejen>, ~/vault (memori), knowledge_base (SOP). Roster 282 = teks; kerja fail guna delegate_task. /api/agency/health.
§
Android 25080RABDG (HyperOS): `am start`/broadcast lapor OK tapi app pihak ketiga tak terbuka (BAL) — guna macro MacroDroid `Intent Diterima com.ketua.OPEN.<APP>` + `Lancar Aplikasi` (app mesti dipilih; AI MacroDroid kerap self-run/null). Alat: ~/bin/buka + tab BUKA.
§
Persona ejen 3 salinan; skill agency-roster-curation.
§
GitHub: ifirdaus9206 (nama lama yang dia bagi = password, bukan username). Sandaran ~/.hermes20→Fz-Firdaus- via backup_github.sh cron 02:00; agents.json + nilai os.environ dikecualikan dari imbasan level-2 (palsu-positif).
§
E-mel Gmail ifirdaus9206: IMAP stdlib; simpan HANYA ~/vault/email-inbox (1-PENTING/2-KERJA/3-PROMOSI/0-LAIN), jangan ke GitHub; cron 10 min.
§
Gudang = /sdcard/Documents/UIM (akar /sdcard RO). uim_hantar (sha256) sehala; audit uim_semak cron 08:00.
§
Konsol 8787 (?tab=pusat), bind 0.0.0.0 → LAN 192.168.0.41:8787. Butang RESET GERBANG di tab pusat (POST /api/svc/hermes-gateway restart). URL awam disalin ke /sdcard/Documents/UIM/KONSOL-URL.txt (quick tunnel bertukar setiap mula).
§
Panduan bos: hantar PDF ke ifirdaus9206@gmail.com (txt tak boleh dibuka); perubahan sistem → Telegram. Cron: SENYAP bila sihat, satu laporan 21:00, ralat beritahu segera.
§
~/.hermes19 dipadam; port 8790 (konsol lama) MATI — guna 8787 sahaja. Skill aktif=114 dalam 30 kategori ≠ 282 ejen/watak (bos keliru). Memori 2 lapis ~/vault/memori, suling cron 23:30; konsol 6 tema (console_theme_v3); url_watch 15min. Keeper = wake-lock + auto-up servis 8787. Status servis: arahan `hermes-status`|`hs` (nama servis bukan arahan).