---
tajuk: "Enam Peranan Ejen"
jenis: fakta
kemas_kini: 2026-11-05
sumber: ["~/.hermes20/docs/PELAN-AI-TEAM.md", "~/.hermes20/docs/hermes-agent-summary.md"]
---

# Enam Peranan Ejen

Kembali ke [index.md](../index.md) · Lihat juga [status sistem](status-sistem.md) ·
[SOP arahan ejen](../sop/arahan-ejen.md).

## Asal

Pelan P2: buat **4–6 ejen SEBENAR** dahulu, bukan 282 persona.

> "P2 — Buat 4–6 ejen SEBENAR dahulu, bukan 282
> - `finance`, `sales`, `marketing`, `ops`, `engineering`, `assistant`
> - Setiap satu: profil Hermes sendiri (memori, skill, workspace, model)
> - Lead = Ketua (profil `default`)"
> — `docs/PELAN-AI-TEAM.md`

## Jadual peranan

| # | Slug | Peranan | Skop | Status |
|---|---|---|---|---|
| 1 | `finance` | Kewangan | Profil sendiri: memori, skill, workspace, model | Dirancang (P2) |
| 2 | `sales` | Jualan | Profil sendiri: memori, skill, workspace, model | Dirancang (P2) |
| 3 | `marketing` | Pemasaran | Profil sendiri: memori, skill, workspace, model | Dirancang (P2) |
| 4 | `ops` | Operasi | Profil sendiri: memori, skill, workspace, model | Dirancang (P2) |
| 5 | `engineering` | Kejuruteraan | Profil sendiri: memori, skill, workspace, model | Dirancang (P2) |
| 6 | `assistant` | Pembantu | Profil sendiri: memori, skill, workspace, model | Dirancang (P2) |

Nota ketepatan: sumber **hanya** menyenaraikan slug dan satu deskripsi generik
("profil Hermes sendiri (memori, skill, workspace, model)"). Skop terperinci
setiap peranan **tidak ditulis** dalam sumber — jangan reka senarai tugas.
Satu-satunya peranan dengan skop bertulis ialah Ketua.

## Ketua (lead, bukan salah satu daripada enam)

Ketua ialah **pengarah**, profil `default`, dan **tidak bekerja dengan tangan sendiri**.

> "Aku **Ketua** — pengarah. Aku **tidak bekerja dengan tangan sendiri**.
> Aku faham apa bos mahu, pecahkan jadi tugasan, pilih ejen, beri arahan,
> semak hasil, dan lulus atau tolak."
> — `SOUL.md`, Identiti

Tugas Ketua: faham → arah → semak → putus. Pengecualian: tulis brief dan baca bukti.

## Bezakan dengan roster 282

`docs/hermes-agent-summary.md` menerangkan 282 ejen yang dipasang melalui plugin
`agency-agents-router` — ini **persona** yang dipanggil melalui tool, bukan proses
ejen berasingan.

> "282 agents installed via agency-agents-router plugin."
> — `docs/hermes-agent-summary.md`, Status

> "282 "ejen" kita **bukan** pasukan seperti dalam video. Ia **satu** Hermes yang
> memakai 282 teks persona." — `docs/PELAN-AI-TEAM.md`

Divisyen roster (contoh daripada sumber): engineering 65+, design 10, academic 6,
finance 5, game-development 21. Roster ini digunakan untuk **memilih persona**
dalam RUN (lihat [SOP arahan ejen](../sop/arahan-ejen.md)), manakala enam peranan
di atas ialah profil Hermes sebenar yang akan dibina.

## Keperluan setiap peranan

Daripada P2 dan P3:
- Profil Hermes sendiri: memori, skill, workspace, model.
- Workspace: `~/.hermes20/workspaces/<ejen>/`, dan arahan "hanya tulis dalam folder sendiri".

> "P3 — Workspace per ejen: `~/.hermes20/workspaces/<ejen>/` + arahan: hanya tulis
> dalam folder sendiri." — `docs/PELAN-AI-TEAM.md`
