---
name: agency-roster-curation
description: Edit agent personas + sync the 282-agent catalog safely.
version: 1.0.0
author: Ketua (curator)
license: MIT
platforms: [linux, macos, termux]
metadata:
  hermes:
    tags: [agency, agents, catalog, persona, drift, hermes]
    related_skills: [agent-team-operations, hermes-conversation-context-recovery]
---

# Kurasi roster agensi (persona + katalog router)

Guna bila kerja menyentuh **ejen agensi** itu sendiri: membaiki persona ejen yang lemah,
menambah keupayaan (contoh akses shell baca-sahaja), menaik/turun tier, atau memastikan
`agents.json` segerak dengan fail persona. Bukan untuk menyalin teks ejen ke `SOUL.md` —
itu kelas lain (`agency-agents-integration`, milik pengguna).

## Fakta struktur (disahkan pada `~/.hermes20`)

Katalog aktif: `~/.hermes20/plugins/agency-agents-router/data/agents.json` — **282 entri**,
setiap satu: `slug, name, description, division, color, emoji, vibe, source_path, body`.

**Tiga salinan persona.** Ubah satu sahaja = router masih hidang teks lama:

| # | Lokasi | Peranan |
|---|---|---|
| 1 | `~/.hermes20/agency-agents/<divisi>/<divisi>-<slug>.md` | korpus git, dibaca manusia |
| 2 | `~/.hermes20/agency-agents-app/src-tauri/resources/corpus-baseline/…` | **sumber build** `sync_agency_catalog.py` |
| 3 | `…/plugins/agency-agents-router/data/agents.json` | yang benar-benar dipakai router |

Skrip: `~/.hermes20/scripts/sync_agency_catalog.py`
- `--check` (lalai) — banding korpus app vs katalog aktif → `logs/agency-catalog-drift.txt`
- `--build <out.json>` — bina daripada corpus-baseline, **tidak** menimpa katalog aktif
- `--fix-paths` — betulkan `source_path`, backup `.bak-<tarikh>` dahulu

Perbandingan ikut `(divisi, slug)`, bukan path mentah: korpus app simpan path rata
(`game-development/unity-architect.md`), repo git simpan subfolder
(`…/unity/unity-architect.md`). Beza susun atur dilapor sebagai **layout**, bukan drift —
jangan "baiki" layout, ia bukan kerosakan.

## Langkah menyunting satu ejen

1. **Baca persona penuh dahulu** (`sed -n '1,200p'`) — faham nada sebelum mengubah satu ayat.
2. **Sunting fail (1)** dengan `patch` (bukan tulis semula). Frontmatter medan yang sah:
   `name, description, color, emoji, vibe` (+ `tools:` untuk ejen yang perlu had tool).
3. **Salin kandungan sama ke fail (2)** — dua fail kembar mesti sama bait-demi-bait.
4. **Kemas kini `description` + `body` entri (3)** dengan Python (lihat `scripts/sync_agent_entry.py`).
   Backup dahulu: `cp agents.json agents.json.bak-$(date +%Y%m%d-%H%M)`.
5. Jalankan `python3 ~/.hermes20/scripts/sync_agency_catalog.py` → drift bagi slug itu mesti hilang.
6. Sahkan 282 entri masih ada dan 281 ejen lain tidak berubah (hash 3 ejen rawak sebelum/selepas).

## Pitfalls

- **Jangan tambah kunci `tools` ke `agents.json`.** Tiada entri lain ada kunci itu; build
  seterusnya tidak menjananya → drift skema. Medan `tools` hanya dalam frontmatter `.md`.
- **Jangan tulis semula seluruh fail persona.** Ejen agensi ada bahagian panjang (deliverables,
  workflow); tulis semula = kehilangan kandungan yang tidak diminta.
- **`grep -rl` merentas `~/.hermes20` akan masuk `node_modules`/`archive` dan timeout.** Hadkan
  carian kepada folder yang relevan.
- **Ejen "tidak boleh buat X" biasanya masalah persona, bukan tool.** Contoh sebenar:
  `master-plan-architect` dilaporkan tiada akses shell — frontmatter tiada `tools`, dan persona
  melarang mutlak (`ZERO CODE EXECUTION`, "only author the Markdown blueprint"). Menambah
  kebenaran pada config tidak menewaskan ayat larangan. Betulkan ayat itu, kemudian katalog.
- **Jangan tukar peranan asal ejen untuk "membaiki" ia.** Penyelesaian betul selalunya: kekalkan
  larangan teras, tambah kebenaran sempit yang disahkan (contoh Bash baca-sahaja).
- Selepas suntingan, jangan percaya bacaan sendiri — semak semula `agents.json` dengan Python,
  bukan dengan mata, dan jangan andaikan proses lain tidak memegang fail itu.

## Pola bacaan-sahaja untuk ejen perancang

Beri kebenaran senarai tepat, bukan "Bash" kosong:
`ls, cat, head, tail, wc, grep, find, stat, git status, git log, curl -I, python3 -c` (baca sahaja).
Tulis garisan jelas: arahan yang menulis/menghapus/install/push **dilarang** semasa fasa perancangan —
cadangkan dalam pelan, jangan jalankan. Setiap dakwaan mesti disokong output arahan sebenar.

## Sokongan

- `scripts/sync_agent_entry.py` — kemas kini satu entri `agents.json` daripada fail `.md` + cetak kiraan.
- `references/verified-2026-11.md` — keadaan disahkan Nov 2026 (kiraan, path, contoh kes).
