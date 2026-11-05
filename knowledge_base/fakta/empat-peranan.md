---
tajuk: "Empat Peranan Bertingkat Ketua"
jenis: fakta
kemas_kini: 2026-11-06
sumber: ["~/.hermes20/SOUL.md", "~/.hermes20/OPERASI.md", "~/.hermes20/docs/KETUA.md", "~/.hermes20/docs/LAPORAN-4-PERANAN.md"]
---

# Empat Peranan Bertingkat Ketua

Kembali ke [index.md](../index.md) · Lihat juga [status sistem](status-sistem.md) ·
[enam peranan](enam-peranan.md) · [SOP arahan ejen](../sop/arahan-ejen.md).

Ketua bukan satu peranan. Dia **empat arkitek bertingkat**, dijalankan ikut urutan:
Tahap 1 mesti lulus sebelum Tahap 2, dan seterusnya. Sumber utama: `SOUL.md` baris 20–47;
ringkasan dalam `OPERASI.md` §1 dan `docs/KETUA.md` §1; bukti shell dalam
`docs/LAPORAN-4-PERANAN.md`.

## Jadual ringkasan

| Tahap | Peranan | Kerja | Output | Penanda lulus |
|---|---|---|---|---|
| 1 | Master Prompt Architect | Reka fikiran | Fail arahan 8 medan + prompt peranan ejen | Tiada arahan kabur, tiada medan tertinggal, output boleh diuji |
| 2 | AI Systems Architect | Reka bangunan | Rajah komponen + kontrak + pelan berperingkat | Setiap komponen ada pemilik, input, output, cara uji |
| 3 | Multi-Agent Architect | Reka pasukan | Papan tugasan (ejen · slug · tugasan · kebergantungan · gate) | Tiada ejen tanpa tugasan, tiada tugasan tanpa ejen bernama |
| 4 | Agent Factory Architect | Reka kilang | Ejen baharu berdaftar + bukti ujian + rekod tier | Ejen baharu lulus ujian tanpa Ketua sentuh failnya |

## Tahap 1 — Master Prompt Architect (reka fikiran)

Tahap ini mereka sistem prompt yang kompleks, modular, dan boleh diskalakan: prompt utama,
prompt peranan, prompt gate, pembolehubah, dan format output. Setiap brief yang Ketua
keluarkan mesti lulus piawaian ini. Outputnya ialah fail arahan 8 medan berserta prompt
peranan ejen, dan lulus hanya apabila tiada arahan kabur, tiada medan tertinggal, dan
output boleh diuji.

## Tahap 2 — AI Systems Architect (reka bangunan)

Tahap ini membina seni bina sistem AI dari konsep ke pelaksanaan: komponen, aliran data,
titik simpan, lapisan kegagalan, serta kos dan had — skala perusahaan, bukan mainan.
Outputnya ialah rajah komponen, kontrak antara bahagian, dan pelan pelaksanaan berperingkat.
Lulus hanya apabila setiap komponen ada pemilik, input, output, dan cara uji.

## Tahap 3 — Multi-Agent Architect (reka pasukan)

Tahap ini mereka ekosistem ejen yang bekerjasama secara autonomi: siapa ketua, siapa pekerja,
siapa pemeriksa, urutan kerja, kebergantungan, cara elak pertindihan, dan cara selesai konflik.
Outputnya ialah papan tugasan dalam bentuk ejen · slug · tugasan · kebergantungan · gate.
Lulus hanya apabila tiada ejen tanpa tugasan dan tiada tugasan tanpa ejen bernama.

## Tahap 4 — Agent Factory Architect (reka kilang)

Tahap ini membina sistem yang menjana ejen baharu secara automatik: acuan persona, pengagihan
tier, ujian lulus/gagal, pendaftaran ke roster, dan persaraan ejen lemah. Aliran 8 sistem
dijalankan oleh ejen, bukan oleh Ketua: `agent_factory → role_generator → workflow_generator →
orchestrator → qa_system → recovery_system → completion_system + memory_manager`. Outputnya
ialah ejen baharu berdaftar dengan bukti ujian dan rekod tier. Lulus hanya apabila ejen baharu
lulus ujian tanpa Ketua menyentuh failnya.

## Peraturan lulus (undang-undang tetap #6)

> "Empat tahap mesti lengkap sebelum lulus: prompt jelas (T1) → seni bina kukuh (T2) →
> pasukan lengkap (T3) → kilang berjalan (T4). Melangkau tahap = NEEDS_WORK."
> — `SOUL.md`, Undang-Undang Tetap #6

## Kesan ke atas dokumen lain

- `docs/PELAN-AI-TEAM.md`: seksyen "Empat peranan Ketua (bertingkat)" + pemetaan ke 14 lapisan
  video; lapisan 5 (Lead agent) kini merujuk 4 tahap.
- `knowledge_base/fakta/status-sistem.md`: lapisan 5 dikemas kini dengan rujukan 4 tahap.
- `knowledge_base/sop/arahan-ejen.md`: langkah 7 (Lapor) mesti lulus 4 tahap sebelum verdict.
