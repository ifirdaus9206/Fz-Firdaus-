Config guard: write/patch refuse ~/.hermes/*/config.yaml; guna `hermes config set` atau python+yaml untuk senarai nested.
§
~/.hermes19 = trading home (config/.env/auth sendiri, trading SOUL.md, skills trading/, ATC, meta5, mt5-backtest, strategy-engines, ANIS). Jalan: `hermes19` atau HERMES_HOME=~/.hermes19 hermes. Catalog: ~/.hermes20/scripts/sync_agency_catalog.py.
§
OpenRouter *:free models often fail 'Upstream idle timeout'; use deepseek-v4.1-flash + fallback_providers.
§
ATC ~/.hermes19/autonomous_trading_controller: XAUUSD/XAGUSD/EURUSD/GBPUSD/WTI, lev 100/100/50/50/20, risk 2%/trade 5%/hari. MetaAPI demo 1300009388 (mt5-backtest/.env), live 1400073582 (meta5/.env) — kedua UNDEPLOYED. Feed: metaapi→yahoo GC=F.
§
~/.hermes20 = home utama; ULTIMATE_AI_PROJECT hanya tools/hermes-source; arkib legacy-ultimate/.
§
Telegram: bot @ainafz_bot (Aina), home chat 1312929583 (firdaus). Token+allowlist dalam ~/.hermes20/.env. Gateway pegang long-poll (poller kedua = 409); log ~/.hermes20/logs/gateway.log; uji `hermes send -t telegram`.
§
Runbook OPERASI.md + docs/KETUA.md. Pasukan: workspaces/<ejen>, ~/vault (memori), knowledge_base (SOP). Ejen roster 282 = teks sahaja; kerja fail sebenar guna delegate_task. Papan + /api/agency/health; cron ujian Isnin 09:00.
§
Android: 25080RABDG = REDMI Note 15 Pro 5G, HyperOS 3/A16, tiada root. Pilihan pembangun DISEKAT: dialog 'Disekat oleh penyedia kredit anda' → ADB pair mustahil; am start dari Termux latar = no-op. Konsol 8787 = runit hermes-console.
§
Suka kendalikan dari UI web 127.0.0.1:8787 (butang jelas, langkah bernombor); mudah salah faham istilah teknikal; mahu penjelasan mudah tanpa jargon serta bukti dalam fails (DEVICE.md).
§
Persona ejen ada 3 salinan: agency-agents/*.md, corpus-baseline (sumber build), body agents.json — ubah ketiga-tiga; skill agency-roster-curation.
§
GitHub: **ifirdaus9206** (Firdaus, id 224862779), ifirdaus9206@gmail.com; `firdaus<REDACTED-PASSWORD>` = PASSWORD bukan username. Sandaran ~/.hermes20 → repo **Fz-Firdaus-** (branch main) via scripts/backup_github.sh + cron 43c3baafa834 02:00.