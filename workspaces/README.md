# Workspaces Ejen — ~/.hermes20/workspaces/

Satu folder = satu ejen = satu rumah kerja. Fail tidak bercampur antara ejen.

## Jadual Indeks

| Ejen | Skop | Folder Masuk | Folder Keluar |
|---|---|---|---|
| `finance` | Kewangan & perakaunan | `finance/inbox/` | `finance/outbox/` |
| `sales` | Jualan & saluran prospek | `sales/inbox/` | `sales/outbox/` |
| `marketing` | Pemasaran & kandungan | `marketing/inbox/` | `marketing/outbox/` |
| `ops` | Operasi & proses dalaman | `ops/inbox/` | `ops/outbox/` |
| `engineering` | Kejuruteraan & kod | `engineering/inbox/` | `engineering/outbox/` |
| `assistant` | Pembantu peribadi & penyelaras | `assistant/inbox/` | `assistant/outbox/` |

## Struktur Piawai (setiap ejen)

```
<ejen>/
├── README.md      # skop kerja + apa ejen TIDAK buat
├── AGENTS.md      # arahan tegas untuk ejen
├── inbox/         # fail masuk (sumber mentah, belum diproses)
├── outbox/        # hasil siap untuk bos
└── notes/         # nota kerja, log, keputusan
```

## Peraturan

1. Ejen hanya menulis dalam `workspaces/<ejen>/` sendiri.
2. Jangan sentuh folder ejen lain (baca pun hanya jika diarah).
3. Jangan sentuh `config.yaml`, `SOUL.md`, `skills/`, `plugins/`, `memories/`.
4. Fail masuk → `inbox/`. Hasil siap → `outbox/`. Nota kerja → `notes/`.
5. Tiada profil Hermes baharu dicipta di sini. Ini folder fail sahaja.

Rujukan: `docs/PELAN-AI-TEAM.md` fasal P3.
