# Inventori `~/.hermes20` (diukur 2026-11-06, Termux Android)

Rujukan ukuran supaya sandaran akan datang tidak perlu mengimbas semula 16 GB.

## Folder >50MB

| Path | Saiz | Keputusan |
|---|---|---|
| `archive/` | 8.7G | kecuali — arkib lama |
| `tools/others/` | 2.8G | kecuali — repo/install pihak ketiga (delphi 784M, cline 702M/628M, bun 316M×2) |
| `tools/hermes-source/` | 2.3G | kecuali — salinan sumber, bukan konfigurasi |
| `legacy-ultimate/` | 2.1G | kecuali — projek lama + node_modules |
| `agency-agents-app/` | 125M | kecuali — repo git berasingan (node_modules 91M) |
| `state.db` (+ `-wal`) | 35M + 2.2M | kecuali — DB sesi |
| `bin/tirith` | 33M | kecuali — binari, muat turun semula |
| `lsp/`, `skills/`, `profiles/`, `plugins/` | 27M / 18M / 17M / 17M | **disandarkan** |
| `logs/` 10M, `cache/` 7.3M, `models_dev_cache.json` 5.7M, `sessions/` 3.6M | — | kecuali |

Jumlah repo selepas pengecualian: **4,686 fail, `.git` 28MB**.

## Fail rahsia disahkan wujud (jangan sekali-kali di-track)

`~/.hermes20/.env` (299B) · `auth.json` (687B) · `config.yaml` (546B) ·
`config.yaml.bak.agency-agents-plugin.30801` (2153B, salinan config).

## Churn yang memaksa pengecualian tambahan

`channel_directory.json`, `cron/ticker_heartbeat`, `cron/ticker_last_success`,
`skills/.usage.json`, `state/gateway.heartbeat` — berubah setiap minit; tanpa pengecualian
setiap larian cron menghasilkan commit.

## Sisa yang masih di-track selepas sesi pertama (belum dibersihkan)

`bin/tirith` (32MB), 4× `plugins/agency-agents-router/data/agents.json.bak-*` (4MB setiap
satu), `skills/.curator_backups/*.tar.gz` (~7MB), `cron/executions.db`,
`verification_evidence.db`. Corak untuk membuangnya: `*.db`, `skills/.curator_backups/`,
`plugins/agency-agents-router/data/*.bak-*`, `bin/tirith` + `git rm --cached`.

## Status kelayakan GitHub

`gh` belum login, tiada remote, nama repo tidak diketahui (SOP §4 melarang mereka nilai).
Langkah tinggal: `gh auth login` → cipta repo → `git remote add origin <URL>`; skrip mula
push tanpa perubahan kod.
