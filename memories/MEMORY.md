Config guard: write/patch refuse ~/.hermes/*/config.yaml; guna `hermes config set` / python+yaml.
§
~/.hermes19 = trading home (config/.env/auth sendiri, trading SOUL.md, skills trading/, ATC, meta5, strategy-engines). Jalan: `hermes19` atau HERMES_HOME=~/.hermes19 hermes. Catalog: ~/.hermes20/scripts/sync_agency_catalog.py.
§
OpenRouter :free kerap timeout; guna deepseek-v4.1-flash + fallback_providers.
§
ATC ~/.hermes19/autonomous_trading_controller: 5 pair, lev 100→20, risk 2%/trade 5%/hari. MetaAPI demo 1300009388 / live 1400073582, kedua UNDEPLOYED. Feed metaapi→yahoo GC=F.
§
~/.hermes20 = home utama; ULTIMATE_AI_PROJECT=tools/hermes-source; arkib legacy-ultimate/.
§
Telegram: bot @ainafz_bot (Aina), chat 1312929583 (firdaus). Token+allowlist di ~/.hermes20/.env. Long-poll (poller kedua=409); log logs/gateway.log; uji `hermes send -t telegram`. Tree HIDUP = tools/hermes-source/hermes-agent (symlink /usr/bin/hermes). Wake-lock auto = fail ~/.hermes20/wake_lock.enabled.
§
Runbook OPERASI.md + docs/KETUA.md. Pasukan: workspaces/<ejen>, ~/vault (memori), knowledge_base (SOP). Roster 282 = teks sahaja; kerja fail guna delegate_task. Papan + /api/agency/health.
§
Android 25080RABDG (Redmi Note 15 Pro 5G, HyperOS3/A16, tiada root): pembangun DISEKAT → ADB pair & am start mustahil. Konsol 8787 = runit hermes-console.
§
Persona ejen ada 3 salinan: agency-agents/*.md, corpus-baseline (sumber build), body agents.json — ubah ketiga-tiga; skill agency-roster-curation.
§
GitHub: ifirdaus9206, ifirdaus9206@gmail.com; nama yang dia bagi dulu = password akaun, bukan username. Sandaran ~/.hermes20 → Fz-Firdaus- (main) via scripts/backup_github.sh + cron 02:00.
§
E-mel Gmail ifirdaus9206: IMAP stdlib; simpan HANYA ~/vault/email-inbox (1-PENTING/2-KERJA/3-PROMOSI/0-LAIN), jangan ke GitHub; cron 10 min.
§
Gudang telefon = /sdcard/Documents/UIM (akar /sdcard tak boleh tulis). Sehala: uim_hantar (sha256), audit uim_semak cron 08:00.
§
Telefon: runit konsol 8787 + dashboard 9119 + tunnel; dashboard_url.txt, dashboard.basic_auth; sshd 8022 (kunci sofia-pc). Sofia=PC, token Telegram sendiri. Tab SOFIA·PC baca ~/sofia-status/status.json (relay repo sofia-status + cron 5min).