# LAPORAN — Runbook Ketua (OPERASI.md + docs/KETUA.md)

Tarikh: 2026-11-05 · Skop: dua fail runbook yang dirujuk `SOUL.md` tetapi tidak wujud
Rujukan: `SOUL.md` baris 3 · `docs/PELAN-AI-TEAM.md` fasal P1

## Status

**SIAP.** Dua fail dicipta di laluan tepat (case-sensitive). `SOUL.md` **tidak diubah**.
Tiada perubahan pada `config.yaml`, `memories/`, `skills/`, `plugins/`, `system/`, dan tiada profil dicipta.

| Fail | Laluan | Saiz | Baris |
|---|---|---|---|
| Runbook operasi | `~/.hermes20/OPERASI.md` | 6,688 bait | 134 |
| Manual Ketua | `~/.hermes20/docs/KETUA.md` | 7,041 bait | 166 |

---

## (a) Output sebenar `wc -l`

```
$ cd ~/.hermes20 && wc -l OPERASI.md docs/KETUA.md
  134 OPERASI.md
  166 docs/KETUA.md
  300 total
```

```
$ cd ~/.hermes20 && wc -c OPERASI.md docs/KETUA.md
 6688 OPERASI.md
 7041 docs/KETUA.md
13729 total
```

## (b) Output sebenar `ls -la`

```
$ cd ~/.hermes20 && ls -la OPERASI.md docs/KETUA.md
-rw-------. 1 u0_a221 u0_a221 6688 Nov  5 21:53 OPERASI.md
-rw-------. 1 u0_a221 u0_a221 7041 Nov  5 21:53 docs/KETUA.md
```

## (c) Struktur bahagian

```
$ cd ~/.hermes20 && grep -c '^## ' OPERASI.md docs/KETUA.md
OPERASI.md:6
docs/KETUA.md:7
```

`OPERASI.md` — 1. Struktur pasukan · 2. Aliran kerja 7 langkah · 3. Jadual eskalasi P1–P4 ·
4. Di mana fail hidup · 5. Senarai semak harian (6 kotak) · Kemas kini

`docs/KETUA.md` — 1. Tujuh undang-undang tetap · 2. Templat brief 8 medan · 3. Contoh BAIK vs BURUK ·
4. Peraturan bukti · 5. Apa Ketua TIDAK buat · Kemas kini

---

## (d) Kriteria lulus

| Kriteria | Keadaan | Bukti dalam fail |
|---|---|---|
| Dua fail wujud di laluan tepat | **LULUS** | `ls -la` di (b) |
| `OPERASI.md` ada 7 langkah | **LULUS** | §2 — jadual 7 baris + urutan bernombor 1–7 |
| `OPERASI.md` ada 4 peringkat eskalasi | **LULUS** | §3 — jadual P1, P2, P3, P4 + had 3 cubaan |
| `OPERASI.md` ada 6 ejen | **LULUS** | §1 — finance, sales, marketing, ops, engineering, assistant |
| `OPERASI.md` ada senarai semak 6 kotak | **LULUS** | §5 — enam `- [ ]` |
| `KETUA.md` ada 7 undang-undang | **LULUS** | §1 — jadual 7 baris + pautan `SOUL.md` #1–#7 |
| `KETUA.md` ada templat 8 medan | **LULUS** | §2 — blok `markdown` sedia salin, medan 1–8 |
| `KETUA.md` ada contoh BAIK vs BURUK | **LULUS** | §3 — 2 pasangan (fail/kod + analisis/data) |
| `KETUA.md` ada peraturan bukti | **LULUS** | §4 — jadual "dikira / tidak dikira" + 3 ujian pantas |
| `KETUA.md` ada jadual "apa Ketua TIDAK buat" | **LULUS** | §5 — 10 baris |
| Bahagian "Kemas kini" + tarikh + sumber | **LULUS** | kedua-dua fail, bahagian terakhir |
| Laporan memuatkan output arahan sebenar | **LULUS** | (a), (b), (c) di atas |
| `SOUL.md` tidak diubah | **LULUS** | Tiada operasi tulis ke `SOUL.md` dijalankan |

---

## (e) Rujukan dalam `SOUL.md` yang kini dipenuhi

| Baris `SOUL.md` | Rujukan | Sebelum | Selepas |
|---|---|---|---|
| 3 | `pelan bertulis: OPERASI.md` | TIADA | **ADA** — `~/.hermes20/OPERASI.md` (134 baris) |
| 3 | `pelan bertulis: docs/KETUA.md` | TIADA | **ADA** — `~/.hermes20/docs/KETUA.md` (166 baris) |
| 4 | `SOUL.md.bak-ketua-2026-11-05` | ADA | ADA (tidak disentuh) — dibaca sebagai sumber |

Kedua-dua rujukan fail dalam `SOUL.md` baris 3 kini diselesaikan. Tiada lagi pautan mati
dalam blok pengepala `SOUL.md`. (Rujukan lain dalam `SOUL.md` ialah perintah API
`/api/agency` dan roster ejen — bukan fail, jadi di luar skop.)

Nota: `knowledge_base/index.md` baris 44 mencatat bahawa `docs/KETUA.md` dan `OPERASI.md`
"tidak dijumpai" semasa pembinaan wiki. Catatan itu **tidak diubah** (di luar skop tugas ini),
tetapi kini tidak lagi tepat dan patut dikemas kini dalam kerja wiki akan datang.

---

## (f) Sumber yang dibaca sebelum menulis

1. `~/.hermes20/SOUL.md`
2. `~/.hermes20/SOUL.md.bak-ketua-2026-11-05`
3. `~/.hermes20/knowledge_base/sop/arahan-ejen.md`
4. `~/.hermes20/knowledge_base/templat/brief-ejen.md`
5. `~/.hermes20/knowledge_base/index.md`
6. `~/.hermes20/docs/PELAN-AI-TEAM.md`
7. `~/.hermes20/docs/LAPORAN-WORKSPACE.md`
8. `~/.hermes20/workspaces/README.md`
9. `~/vault/README.md`

Tiada peraturan direka. Contoh dalam `docs/KETUA.md` §3 ialah ilustrasi bentuk arahan
(proses brief), bukan polisi baharu.

## (g) Fail yang dicipta

```
~/.hermes20/OPERASI.md
~/.hermes20/docs/KETUA.md
~/.hermes20/docs/LAPORAN-RUNBOOK.md   (laporan ini)
```
