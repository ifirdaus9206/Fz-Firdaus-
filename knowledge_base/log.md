---
tajuk: "Log Wiki"
jenis: meta
kemas_kini: 2026-11-06
sumber: ["~/.hermes20/docs/PELAN-AI-TEAM.md"]
---

# Log Wiki

> Rekod kronologi tindakan wiki. Append-only.
> Format: `## [YYYY-MM-DD] tindakan | subjek`
> Kembali ke [index.md](index.md).

## [2026-11-05] create | Wiki pengetahuan dimulakan
- Domain: SOP + fakta pasukan ejen AI (`~/.hermes20`).
- Sumber dibaca: `SOUL.md`, `docs/PELAN-AI-TEAM.md`, `docs/hermes-agent-summary.md`.
- Sumber tiada: `docs/KETUA.md`, `OPERASI.md` (tidak dijumpai).
- Fail dicipta: `index.md`, `SCHEMA.md`, `log.md`, `sop/arahan-ejen.md`,
  `sop/backup.md`, `fakta/status-sistem.md`, `fakta/enam-peranan.md`,
  `templat/brief-ejen.md`.

## [2026-11-06] fix | Fakta sumber lapuk dibetulkan
- `index.md` §Nota Sumber: ayat "`docs/KETUA.md` dan `OPERASI.md` **tidak dijumpai**"
  dibuang. Fakta betul: kedua fail **wujud** di cakera —
  [OPERASI.md](../OPERASI.md) 134 baris dan [KETUA.md](../docs/KETUA.md) 166 baris,
  kedua-duanya dikemas kini 2026-11-05.
- `index.md`: `kemas_kini` → 2026-11-06; "Jumlah halaman: 6" → 8 (8 fail `.md` dalam wiki).
- `fakta/status-sistem.md`: nota kemas kini lapisan 9 (Pengetahuan) — `knowledge_base/`
  kini wujud, jadi status "TIADA / belum di-setup" tidak lagi tepat; jadual asal dikekalkan
  sebagai salinan sumber 2026-11-05.
- Semakan pautan: **33 pautan `.md` disemak, 0 rosak** (skrip Python, `os.path.normpath`).
- Tidak disentuh: `OPERASI.md`, `docs/KETUA.md` (mtime kekal 2026-11-05 21:53), `SOUL.md`.

## [2026-11-06] update | Selaraskan PELAN-AI-TEAM.md + knowledge_base dengan 4 peranan bertingkat Ketua
- Perubahan persona: Ketua kini **empat peranan bertingkat** — T1 Master Prompt Architect,
  T2 AI Systems Architect, T3 Multi-Agent Architect, T4 Agent Factory Architect
  (`SOUL.md` 20–47; undang-undang tetap #6 `SOUL.md` 64).
- `docs/PELAN-AI-TEAM.md`: seksyen baharu "Empat peranan Ketua (bertingkat)" (jadual 4 tahap +
  pemetaan ke 14 lapisan video); lapisan 5 (Lead agent) kini merujuk 4 tahap; nota P1 ditambah.
- `knowledge_base/fakta/empat-peranan.md`: **halaman baharu** — jadual ringkasan + 1 perenggan
  setiap tahap + peraturan lulus #6.
- `knowledge_base/fakta/status-sistem.md`: baris lapisan 5 + nota kemas kini 4 peranan;
  pautan "lihat juga" dan status P1 diselaraskan.
- `knowledge_base/index.md`: baris `fakta/empat-peranan.md` dalam jadual Fakta; "Jumlah halaman:
  8" → 9; nota sumber dikemas kini (OPERASI.md 154 baris, KETUA.md 191 baris — angka sebenar
  `wc -l`, bukan 134/166 yang lapuk).
- `knowledge_base/sop/arahan-ejen.md`: nota 4 tahap pada langkah 7 (Lapor) — T1 → T2 → T3 → T4
  mesti lulus sebelum verdict; `kemas_kini` → 2026-11-06.
- Tidak disentuh (hash kekal): `SOUL.md`, `OPERASI.md`, `docs/KETUA.md`, `docs/LAPORAN-4-PERANAN.md`,
  `config.yaml`, `.env`, `memories/`.
- Bukti penuh: `docs/LAPORAN-KNOWLEDGE-4-PERANAN.md`.
