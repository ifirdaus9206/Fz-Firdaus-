# docs/SERVIS.md — Peta Perkhidmatan (runit)

**Dikemas kini:** 2026-11-24 · **Home:** `~/.hermes20` · **Satu konsol sahaja: 8787**

## Lima servis

| Servis | Fungsi | Port | Log |
|---|---|---|---|
| `hermes-console` | Konsol pemantauan & pengurusan (FastAPI) | **8787** | `logs/hermes-console/` |
| `hermes-gateway` | Gateway Telegram (bot) | — | `logs/gateway.log` |
| `hermes-keeper` | Penjaga: tahan wake-lock, hidupkan semula servis, buang proses yatim | — | `logs/hermes-keeper/` |
| `hermes-dash-tunnel` | Tunnel Cloudflare → `127.0.0.1:8787` | — | `logs/dashboard-tunnel.log` |
| `sshd` | SSH | 8022 | — |

**Dibersarakan:** `hermes-dashboard` (port 9119) dan konsol hermes19 (port 8790).
Kedua-duanya **mati secara sengaja**. Jangan hidupkan semula.

## Arahan harian

| Arahan | Kerja |
|---|---|
| `hermes-status` atau `hs` | Status semua servis + kod konsol + URL tunnel |
| `hermes-up` | Naikkan semua servis yang mati |
| `hermes-down` | Hentikan konsol + gateway (penjaga kekal) |
| `hermes-restart` | Mula semula konsol + gateway |

⚠️ `hermes-restart` memutuskan gateway Telegram — sesi chat terhenti sekejap. Itu normal.

## Arahan runit asas

```
sv status hermes-console     # tengok status
sv up hermes-console         # naikkan
sv down hermes-console       # hentikan (kekal mati)
sv restart hermes-console    # mula semula
```

`sv restart` kadang tergantung. Prosedur selamat:
```bash
P=$(sv status hermes-console | grep -o 'pid [0-9]*' | grep -o '[0-9]*'); kill -9 $P; sv up hermes-console
```

## Prosedur pulih

1. `hs` — kenal pasti servis mana mati.
2. `hermes-up` — cuba naikkan semua.
3. Masih mati → semak log servis itu di `logs/`.
4. Konsol tak jawab tetapi servis `run:` → proses yatim memegang port 8787.
   Penjaga akan bunuhnya dalam 60 saat; atau buat manual seperti di atas.
5. Tunnel 502 → cloudflared mati. `sv restart hermes-dash-tunnel`, kemudian baca
   URL baharu dalam `dashboard_url.txt` (quick tunnel bertukar setiap mula).

## Peraturan

1. **Satu konsol** — 8787 sahaja. 9119 dan 8790 kekal mati.
2. Jangan tambah servis baharu tanpa memadam yang lama.
3. Setiap servis mesti ada log yang boleh dibaca.
