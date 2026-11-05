# LAPORAN WIKI — knowledge_base

Tarikh: 2026-11-05 · Skop: `~/.hermes20/knowledge_base/` (SOP, fakta, templat)
Kaedah: baca sumber → tulis halaman → sahkan pautan secara program → jalankan `find`.

## 1. Senarai fail + saiz

Output sebenar:

```
knowledge_base/SCHEMA.md                   1436 bytes
knowledge_base/fakta/enam-peranan.md       3143 bytes
knowledge_base/fakta/status-sistem.md      3888 bytes
knowledge_base/index.md                    1702 bytes
knowledge_base/log.md                       674 bytes
knowledge_base/sop/arahan-ejen.md          4826 bytes
knowledge_base/sop/backup.md               2188 bytes
knowledge_base/templat/brief-ejen.md       1688 bytes
```

Jumlah: 8 fail markdown (>= 6 diperlukan).

## 2. Output sebenar `find ~/.hermes20/knowledge_base -type f | sort`

```
/data/data/com.termux/files/home/.hermes20/knowledge_base/SCHEMA.md
/data/data/com.termux/files/home/.hermes20/knowledge_base/fakta/enam-peranan.md
/data/data/com.termux/files/home/.hermes20/knowledge_base/fakta/status-sistem.md
/data/data/com.termux/files/home/.hermes20/knowledge_base/index.md
/data/data/com.termux/files/home/.hermes20/knowledge_base/log.md
/data/data/com.termux/files/home/.hermes20/knowledge_base/sop/arahan-ejen.md
/data/data/com.termux/files/home/.hermes20/knowledge_base/sop/backup.md
/data/data/com.termux/files/home/.hermes20/knowledge_base/templat/brief-ejen.md
```

## 3. Pautan dalaman + pengesahan sasaran

Disemak secara program: 29 pautan `*.md`, **0 rosak**, semua sasaran wujud.
Setiap fail (termasuk `index.md`, `SCHEMA.md`, `log.md`) mengandungi pautan ke `index.md`.

| Fail | Pautan keluar | Semua sasaran wujud |
|---|---|---|
| `index.md` | sop/arahan-ejen.md, sop/backup.md, fakta/status-sistem.md, fakta/enam-peranan.md, templat/brief-ejen.md, SCHEMA.md, log.md, index.md | ya |
| `SCHEMA.md` | index.md (x2) | ya |
| `log.md` | index.md | ya |
| `sop/arahan-ejen.md` | ../index.md, ../templat/brief-ejen.md (x2), ../fakta/enam-peranan.md | ya |
| `sop/backup.md` | ../index.md, ../fakta/status-sistem.md | ya |
| `fakta/status-sistem.md` | ../index.md, ../fakta/enam-peranan.md, ../sop/arahan-ejen.md, ../sop/backup.md | ya |
| `fakta/enam-peranan.md` | ../index.md, status-sistem.md, ../sop/arahan-ejen.md (x2) | ya |
| `templat/brief-ejen.md` | ../index.md, ../sop/arahan-ejen.md | ya |

Frontmatter disemak: 8/8 fail ada `tajuk`, `jenis`, `kemas_kini: 2026-11-05`, `sumber`.

## 4. Petikan terus sumber bagi setiap fakta utama

### Fakta A — Brief 8 medan
> "Tiada ejen bermula sejuk. Brief 8 medan: objektif, konteks, input, skop,
> larangan, format output, kriteria lulus, tarikh akhir."
> — `~/.hermes20/SOUL.md`, Undang-Undang Tetap #3
→ `sop/arahan-ejen.md` §2, `templat/brief-ejen.md`

### Fakta B — Aliran dispatch
> "Hantar — melalui enjin agensi (bukan kerja sendiri):
> `POST http://127.0.0.1:8787/api/agency/plan` {instruction, max_agents}
> → `POST http://127.0.0.1:8787/api/agency/run/{run_id}`
> → semak `GET /api/agency/run/{run_id}`"
> — `~/.hermes20/SOUL.md`, Cara Menghantar Arahan #5
→ `sop/arahan-ejen.md` §4

### Fakta C — Eskalasi P1–P4
> "Peringkat hukuman: P1 tegur + ulang brief · P2 ulang dengan konteks/bukti tambahan ·
> P3 turun tier + tulis semula persona · P4 bersara (keluar roster).
> Maksimum 3 cubaan sebelum P3; P4 hanya dengan kebenaran bos."
> — `~/.hermes20/SOUL.md`, Undang-Undang Tetap #5
→ `sop/arahan-ejen.md` §6

### Fakta D — Backup malam
> "Cron 2:00 pagi: `git add -A && commit && push` untuk ~/.hermes20 (tanpa token/rahsia)."
> — `~/.hermes20/docs/PELAN-AI-TEAM.md`, P6
→ `sop/backup.md` §2

### Fakta E — Status lapisan (contoh baris 9 & 12)
> "| 9 | Pengetahuan | LLM Wiki = SOP/FAQ/fakta (bukan memori) | **TIADA** | skill llm-wiki ada, belum di-setup |"
> "| 12 | Backup | Cron malam → GitHub, ejen jaga dirinya | **TIADA** | Tiada repo backup automatik |"
> — `~/.hermes20/docs/PELAN-AI-TEAM.md`, jadual 11 lapisan
→ `fakta/status-sistem.md` (jadual disalin penuh, 14 baris)

### Fakta F — Enam peranan
> "P2 — Buat 4–6 ejen SEBENAR dahulu, bukan 282
> - `finance`, `sales`, `marketing`, `ops`, `engineering`, `assistant`
> - Setiap satu: profil Hermes sendiri (memori, skill, workspace, model)
> - Lead = Ketua (profil `default`)"
> — `~/.hermes20/docs/PELAN-AI-TEAM.md`
→ `fakta/enam-peranan.md`

### Fakta G — Ketua tidak buat kerja tangan
> "Ketua tidak melaksanakan. Kerja tangan (tulis kod, jalankan ujian, scan data,
> karang laporan) milik ejen. Ketua hanya: faham → arah → semak → putus."
> — `~/.hermes20/SOUL.md`, Undang-Undang Tetap #1
→ `sop/arahan-ejen.md` §1, `fakta/enam-peranan.md`

### Fakta H — 282 persona vs pasukan sebenar
> "282 agents installed via agency-agents-router plugin." — `~/.hermes20/docs/hermes-agent-summary.md`
> "282 \"ejen\" kita **bukan** pasukan seperti dalam video. Ia **satu** Hermes yang memakai 282 teks persona."
> — `~/.hermes20/docs/PELAN-AI-TEAM.md`
→ `fakta/enam-peranan.md` §"Bezakan dengan roster 282"

## 5. Isu / had

1. **Sumber tiada:** `~/.hermes20/docs/KETUA.md` dan `~/.hermes20/OPERASI.md` **tidak wujud**
   pada 2026-11-05 (rujukan `SOUL.md` kepada kedua-duanya sudah lapuk). Wiki dibina daripada
   `SOUL.md`, `docs/PELAN-AI-TEAM.md`, `docs/hermes-agent-summary.md`, dan `SOUL.md.bak-ketua-2026-11-05`.
   Nota ini juga dicatat dalam `index.md`.
2. **Skop 6 peranan:** sumber hanya beri slug + deskripsi generik; tiada senarai tugas per peranan.
   Halaman `fakta/enam-peranan.md` menyatakan ini secara eksplisit dan tidak mengisi skop rekaan.
3. **Percanggahan dalam sumber:** tajuk "11 lapisan" tetapi jadual ada 14 baris. Kedua-dua angka
   dikekalkan dan percanggahan ditandakan dalam `fakta/status-sistem.md`.
4. **Status pengetahuan:** halaman ini menjadikan lapisan 9 (Pengetahuan) mula berisi, tetapi jadual
   status dalam `fakta/status-sistem.md` masih menyebut **TIADA** — kerana ia salinan sumber dan
   belum dikemas kini dengan bukti baharu. Perlu kemas kini berasingan jika bos mahu status ditukar.
5. Tiada fail di luar `knowledge_base/` dan `docs/LAPORAN-WIKI.md` disentuh. `config.yaml`, `SOUL.md`,
   `memories/`, `skills/` tidak diubah.
