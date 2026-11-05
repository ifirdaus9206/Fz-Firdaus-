---
tajuk: "Skema Wiki"
jenis: meta
kemas_kini: 2026-11-05
sumber: ["~/.hermes20/skills/research/llm-wiki/SKILL.md"]
---

# Skema Wiki

Kembali ke [index.md](index.md).

## Domain

SOP operasi dan fakta sistem untuk pasukan ejen AI dalam `~/.hermes20`.
Pengetahuan di sini **berasingan daripada memori** — ia jawapan stabil
(SOP, fakta status, templat), bukan catatan sesi.

## Konvensyen

- Nama fail: huruf kecil, sempang, tiada ruang (`arahan-ejen.md`).
- Setiap halaman bermula dengan frontmatter YAML: `tajuk`, `jenis`, `kemas_kini`, `sumber`.
- `jenis` mesti salah satu: `sop` | `fakta` | `templat` | `meta` | `indeks`.
- Setiap halaman mesti paut ke [index.md](index.md).
- Pautan dalaman guna format relatif markdown (kurungan segi empat + kurungan biasa
  + laluan fail `.md`), bukan `[[wikilink]]`, supaya boleh dibaca dari mana-mana editor
  tanpa Obsidian.
- Setiap fakta mesti boleh dikesan ke fail sumber dalam medan `sumber`.
- Tarikh `kemas_kini` diubah bila kandungan berubah.
- Tiada nombor, harga, atau tarikh yang tidak ada dalam sumber.

## Struktur

```
knowledge_base/
├── index.md
├── SCHEMA.md
├── log.md
├── sop/        # prosedur operasi
├── fakta/      # status & fakta sistem
└── templat/    # templat sedia guna
```

## Tag

Tiada taksonomi tag berasingan pada peringkat ini — `jenis` sudah cukup
untuk penapisan. Jika tag ditambah kelak, senaraikan di sini dahulu.
