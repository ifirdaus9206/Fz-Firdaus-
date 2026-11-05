# The runbook pair — `OPERASI.md` + `docs/KETUA.md`

Recipe for the job: *"SOUL.md references two runbooks that do not exist. Write them, with command
evidence."* Produced and verified in one home on 2026-11-05 (134 + 166 lines).

## 0. Why this job is legitimate

The lead persona's header names the guides (`pelan bertulis: OPERASI.md, docs/KETUA.md`). If they are
missing, every "plan" the lead cites is a dead path and P1 is unfinished. Writing them is NOT inventing
doctrine as long as every rule is traceable to a file you read in step 1. The prohibition is on
**plausible prose from memory**, not on authorship.

## 1. Read first — the whole set, no exceptions

| Source | What it gives you |
|---|---|
| `SOUL.md` | 7 fixed laws, 7-step flow, dispatch endpoints, exact reference line numbers |
| `SOUL.md.bak-*` | dropped doctrine (8-system table, completion boxes, max-3-attempts, output dirs) |
| `knowledge_base/sop/*.md` | the same rules already phrased for agents — quote, don't re-derive |
| `knowledge_base/templat/*.md` | the 8-field brief block, copy verbatim |
| `knowledge_base/index.md` | page inventory; may itself record the runbooks as "tidak dijumpai" |
| `docs/PELAN-*.md` | priority ladder (P1–P8) + the 6 role slugs the owner chose |
| `docs/LAPORAN-*.md` | workspace layout, evidence-report style already used in this home |
| `workspaces/README.md` | per-agent scope table + folder rules (single-writer discipline) |
| vault `README.md` | memory-vs-facts split, so you place content in the right store |

## 2. `OPERASI.md` — shape that passes a rubric

Six `##` sections, in this order:

1. **Struktur pasukan** — table: `# | Ejen (slug) | Skop | Folder kerja | Tulis hasil ke`; row 0 = Ketua
   with "tidak buat kerja tangan". Follow with numbered team rules (one task = one named agent,
   write only in own folder, lowest adequate tier, lead never takes over).
2. **Aliran kerja 7 langkah** — state the sequence as one bold line
   `**1. Faham → 2. Pecah → 3. Pilih ejen → 4. Brief 8 medan → 5. Hantar → 6. Semak → 7. Lapor.**`
   *then* the table (`# | Langkah | Apa Ketua buat | Output langkah`), then dispatch block
   (`/plan` → `/run/{id}` → `GET /run/{id}`) and the 8-system chain "run by agents, not the lead".
3. **Jadual eskalasi P1–P4** — `Peringkat | Bila dicetuskan | Tindakan | Siapa boleh luluskan`;
   close with "max 3 attempts before P3; P4 owner-only".
4. **Di mana fail hidup** — `Lokasi | Isi | Siapa tulis` covering persona, runbooks, workspaces,
   knowledge_base, vault, `docs/LAPORAN-*`, `system/`. Add the split in one line: facts → knowledge_base,
   experience → vault, output → outbox, evidence → LAPORAN.
5. **Senarai semak harian (6 kotak)** — exactly six `- [ ]` items, each with a failure meaning.
6. **Kemas kini** — date, author, provenance block.

## 3. `docs/KETUA.md` — shape that passes a rubric

1. **7 undang-undang tetap** — table `# | Undang-undang | Ringkasan 1 baris | Rujukan penuh`, the last
   column linking `SOUL.md` §UNDANG-UNDANG TETAP #N. One line per law, no paragraphs.
2. **Templat brief 8 medan** — fenced ```markdown``` block copied from `templat/brief-ejen.md`, all 8
   numbered fields, `<...>` placeholders, plus a pre-send check line.
3. **Contoh BAIK vs BURUK** — two pairs (one file/code job, one data/analysis job). BURUK = one vague
   sentence + an explicit "salah kerana:" listing which of the 8 fields are missing. BAIK = the same
   task fully briefed.
4. **Peraturan bukti** — two-column table `Dikira bukti | Tidak dikira bukti` (path+`wc -l`, real command
   output, `12 passed`, diff, `run_id` status ↔ "dah siap", "nampak okay", "ejen cakap"). Add 3 audit
   questions (can I open it / reproduce it / do the numbers match).
5. **Apa Ketua TIDAK buat** — table `Tidak buat | Sebab | Siapa buat`, 8–10 rows, each tracing to a law.
6. **Kemas kini** — same provenance block.

## 4. Verify like a grader, not like an author

```bash
cd ~/.hermesNN
wc -l OPERASI.md docs/KETUA.md          # sizes for the report
wc -c OPERASI.md docs/KETUA.md
ls -la OPERASI.md docs/KETUA.md         # exact case-sensitive paths
grep -c '^## ' OPERASI.md docs/KETUA.md # section count
ls -la SOUL.md                          # mtime proof the source was untouched
grep -n 'OPERASI.md' SOUL.md            # line number for the fulfilment table
```

**Pitfall — regex-counting enumerated items undercounts.** `grep -oP '\*\*[1-7]\. '` returned 6 for a
7-step flow because one cell was `**Brief 8 medan**` with no leading number. Fix inside the document,
not in the grep: put one explicit bold sequence line (`1. Faham → … → 7. Lapor`) in the section so both
a human and a checker see all seven. Same rule for the 6 agents, 4 escalation levels, 7 laws — make the
count textual, not implied by table rows alone.

**Pitfall — case and directory.** `OPERASI.md` is uppercase at home root; `KETUA.md` lives in `docs/`.
Linux is case-sensitive: `operasi.md`/`Docs/KETUA.md` silently create duplicates that satisfy no
reference.

## 5. Evidence report shape (`docs/LAPORAN-RUNBOOK.md`)

1. Status line: SIAP, paths, sizes, and "SOUL.md tidak diubah".
2. `(a)` real `wc -l` + `wc -c` blocks with the `$` prompt shown.
3. `(b)` real `ls -la`.
4. `(c)` section inventory (`grep -c '^## '`).
5. `(d)` criteria table — one row per rubric item: Kriteria | Keadaan (LULUS) | Bukti dalam fail.
6. `(e)` reference-fulfilment table — every `SOUL.md` line that named a path: Baris | Rujukan | Sebelum
   (TIADA) | Selepas (ADA + size).
7. `(f)` numbered sources read.
8. `(g)` files created (only the two runbooks + the report).

## 6. Don't

- Don't rewrite `SOUL.md` to match the new docs — the docs serve the persona, never the reverse.
- Don't update `knowledge_base/index.md` when it still says the runbooks are missing: that page is a
  dated snapshot and editing it is outside the assigned scope. Note the staleness in the report's last
  paragraph and leave it for a wiki task.
- Don't create profiles, cron jobs, or `workspaces/*` content as a side effect.
- Don't pad with new policy (SLA numbers, cost tables) that no source states.
