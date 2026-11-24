---
tajuk: "Fakta Servis Runit"
jenis: fakta
kemas_kini: 2026-11-24
sumber: ["~/.hermes20/docs/SERVIS.md", "$PREFIX/var/service/"]
---

# Fakta — Servis Runit Hermes

## Lima servis hidup

| Servis | Fungsi | Port | Log |
|---|---|---|---|
| `hermes-console` | Konsol pemantauan | 8787 | `logs/hermes-console/` |
| `hermes-gateway` | Telegram | — | `logs/gateway.log` |
| `hermes-keeper` | Wake-lock + pulih servis | — | `logs/hermes-keeper/` |
| `hermes-dash-tunnel` | Cloudflare → 8787 | — | `logs/dashboard-tunnel.log` |
| `sshd` | SSH | 8022 | — |

## Dua servis dibersarakan (kekal mati)

| Servis | Port | Sebab |
|---|---|---|
| `hermes-dashboard` | 9119 | Diganti konsol 8787 |
| konsol hermes19 | 8790 | `~/.hermes19` dipadam 2026-11-24 |

## Fakta penting

1. `sv` berada di `$PREFIX/bin/sv`; `SVDIR=$PREFIX/var/service`.
2. Nama servis **bukan** arahan — mesti guna `sv status <nama>` atau `hs`.
3. `hermes-keeper` semak `http://127.0.0.1:8787/` setiap 60 saat dan
   naikkan semula konsol/gateway jika mati; ia juga tahan wake-lock **sekali**
   sahaja (bukan setiap kitaran).
4. Jika proses yatim (PPID 1) menggenggam 8787, anak runit gagal bind —
   keeper akan bunuhnya.
5. `sv restart` boleh tergantung; prosedur selamat: `kill -9 <pid>` → `sv up`.
6. `hermes-restart` memutuskan gateway Telegram sekejap — jangkaan, bukan rosak.
7. Fail `down` dalam folder servis = servis sengaja dimatikan.
