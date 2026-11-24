# LAPORAN — Workspace Ejen (P3)

Tarikh: 2026-11-05 · Skop: `~/.hermes20/workspaces/` sahaja
Rujukan: `docs/PELAN-AI-TEAM.md` fasal P3

## Status

6 folder ejen dicipta. Setiap satu ada `README.md`, `AGENTS.md`, dan subfolder
`inbox/`, `outbox/`, `notes/` (setiap satu dengan `.gitkeep`). Jumlah fail: **31**.

Tiada profil Hermes dicipta. Tiada perubahan pada `config.yaml`, `SOUL.md`,
`skills/`, `plugins/`, `memories/`.

## (a) Senarai penuh laluan fail yang dicipta

```
~/.hermes20/workspaces/README.md
~/.hermes20/workspaces/assistant/AGENTS.md
~/.hermes20/workspaces/assistant/README.md
~/.hermes20/workspaces/assistant/inbox/.gitkeep
~/.hermes20/workspaces/assistant/notes/.gitkeep
~/.hermes20/workspaces/assistant/outbox/.gitkeep
~/.hermes20/workspaces/engineering/AGENTS.md
~/.hermes20/workspaces/engineering/README.md
~/.hermes20/workspaces/engineering/inbox/.gitkeep
~/.hermes20/workspaces/engineering/notes/.gitkeep
~/.hermes20/workspaces/engineering/outbox/.gitkeep
~/.hermes20/workspaces/finance/AGENTS.md
~/.hermes20/workspaces/finance/README.md
~/.hermes20/workspaces/finance/inbox/.gitkeep
~/.hermes20/workspaces/finance/notes/.gitkeep
~/.hermes20/workspaces/finance/outbox/.gitkeep
~/.hermes20/workspaces/marketing/AGENTS.md
~/.hermes20/workspaces/marketing/README.md
~/.hermes20/workspaces/marketing/inbox/.gitkeep
~/.hermes20/workspaces/marketing/notes/.gitkeep
~/.hermes20/workspaces/marketing/outbox/.gitkeep
~/.hermes20/workspaces/ops/AGENTS.md
~/.hermes20/workspaces/ops/README.md
~/.hermes20/workspaces/ops/inbox/.gitkeep
~/.hermes20/workspaces/ops/notes/.gitkeep
~/.hermes20/workspaces/ops/outbox/.gitkeep
~/.hermes20/workspaces/sales/AGENTS.md
~/.hermes20/workspaces/sales/README.md
~/.hermes20/workspaces/sales/inbox/.gitkeep
~/.hermes20/workspaces/sales/notes/.gitkeep
~/.hermes20/workspaces/sales/outbox/.gitkeep
```

Jumlah: 31 fail (6 folder termasuk 6 folder ejen + 18 subfolder).

Folder peringkat atas:
```
~/.hermes20/workspaces/assistant
~/.hermes20/workspaces/engineering
~/.hermes20/workspaces/finance
~/.hermes20/workspaces/marketing
~/.hermes20/workspaces/ops
~/.hermes20/workspaces/sales
```

Struktur folder:
```
workspaces
workspaces/assistant
workspaces/assistant/inbox
workspaces/assistant/notes
workspaces/assistant/outbox
workspaces/engineering
workspaces/engineering/inbox
workspaces/engineering/notes
workspaces/engineering/outbox
workspaces/finance
workspaces/finance/inbox
workspaces/finance/notes
workspaces/finance/outbox
workspaces/marketing
workspaces/marketing/inbox
workspaces/marketing/notes
workspaces/marketing/outbox
workspaces/ops
workspaces/ops/inbox
workspaces/ops/notes
workspaces/ops/outbox
workspaces/sales
workspaces/sales/inbox
workspaces/sales/notes
workspaces/sales/outbox
```

## (b) Output sebenar `find ~/.hermes20/workspaces -type f | sort`

```
$ find ~/.hermes20/workspaces -type f | sort
/data/data/com.termux/files/home/.hermes20/workspaces/README.md
/data/data/com.termux/files/home/.hermes20/workspaces/assistant/AGENTS.md
/data/data/com.termux/files/home/.hermes20/workspaces/assistant/README.md
/data/data/com.termux/files/home/.hermes20/workspaces/assistant/inbox/.gitkeep
/data/data/com.termux/files/home/.hermes20/workspaces/assistant/notes/.gitkeep
/data/data/com.termux/files/home/.hermes20/workspaces/assistant/outbox/.gitkeep
/data/data/com.termux/files/home/.hermes20/workspaces/engineering/AGENTS.md
/data/data/com.termux/files/home/.hermes20/workspaces/engineering/README.md
/data/data/com.termux/files/home/.hermes20/workspaces/engineering/inbox/.gitkeep
/data/data/com.termux/files/home/.hermes20/workspaces/engineering/notes/.gitkeep
/data/data/com.termux/files/home/.hermes20/workspaces/engineering/outbox/.gitkeep
/data/data/com.termux/files/home/.hermes20/workspaces/finance/AGENTS.md
/data/data/com.termux/files/home/.hermes20/workspaces/finance/README.md
/data/data/com.termux/files/home/.hermes20/workspaces/finance/inbox/.gitkeep
/data/data/com.termux/files/home/.hermes20/workspaces/finance/notes/.gitkeep
/data/data/com.termux/files/home/.hermes20/workspaces/finance/outbox/.gitkeep
/data/data/com.termux/files/home/.hermes20/workspaces/marketing/AGENTS.md
/data/data/com.termux/files/home/.hermes20/workspaces/marketing/README.md
/data/data/com.termux/files/home/.hermes20/workspaces/marketing/inbox/.gitkeep
/data/data/com.termux/files/home/.hermes20/workspaces/marketing/notes/.gitkeep
/data/data/com.termux/files/home/.hermes20/workspaces/marketing/outbox/.gitkeep
/data/data/com.termux/files/home/.hermes20/workspaces/ops/AGENTS.md
/data/data/com.termux/files/home/.hermes20/workspaces/ops/README.md
/data/data/com.termux/files/home/.hermes20/workspaces/ops/inbox/.gitkeep
/data/data/com.termux/files/home/.hermes20/workspaces/ops/notes/.gitkeep
/data/data/com.termux/files/home/.hermes20/workspaces/ops/outbox/.gitkeep
/data/data/com.termux/files/home/.hermes20/workspaces/sales/AGENTS.md
/data/data/com.termux/files/home/.hermes20/workspaces/sales/README.md
/data/data/com.termux/files/home/.hermes20/workspaces/sales/inbox/.gitkeep
/data/data/com.termux/files/home/.hermes20/workspaces/sales/notes/.gitkeep
/data/data/com.termux/files/home/.hermes20/workspaces/sales/outbox/.gitkeep
```

## (c) Kiraan fail

```
$ find ~/.hermes20/workspaces -type f | wc -l
31
```

## (d) Contoh kandungan `AGENTS.md`

Dua baris sebenar dari `~/.hermes20/workspaces/finance/AGENTS.md`:

```
$ grep -n 'Tulis \*\*hanya\*\*' finance/AGENTS.md
6:- Tulis **hanya** dalam `~/.hermes20/workspaces/finance/`.
$ grep -n 'ejen-lain' finance/AGENTS.md
7:- **JANGAN** sentuh `~/.hermes20/workspaces/<ejen-lain>/` — tiada tulis, tiada padam, tiada pindah.
```

Kedua-dua baris ini ada dalam kesemua 6 fail `AGENTS.md` (nama ejen berbeza).

## (e) Senarai semak kriteria lulus

- [x] 6 folder ejen wujud: finance, sales, marketing, ops, engineering, assistant
- [x] Setiap ejen: README.md + AGENTS.md + inbox/ + outbox/ + notes/
- [x] `.gitkeep` dalam setiap subfolder kosong
- [x] README akar dengan jadual indeks (ejen | skop | folder masuk | folder keluar)
- [x] Laporan memuatkan output arahan sebenar
- [x] Tiada fail dicipta di luar `~/.hermes20/workspaces/` kecuali laporan ini
