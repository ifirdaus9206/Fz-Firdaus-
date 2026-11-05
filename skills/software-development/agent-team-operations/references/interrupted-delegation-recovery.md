# Resuming a delegation that died mid-job

Observed 2026-11-06 (`deleg_eb4c2c58`, home `~/.hermes20`): a child was told to align
`docs/PELAN-AI-TEAM.md` + all of `knowledge_base/` with a rewritten persona. It wrote 3 of 6
files, then the transcript stopped on a tool result at 01:17 with no verdict and no report.
A later session was asked "tegur tugasan lepas apa yang belum selesai … kalau belum jalankan
sampai siap". This file is the recipe that finished it.

## 1. Diagnose from disk, not from the transcript

The transcript tells you *where* it stopped; only the filesystem tells you *what* it left.

```bash
cd ~/.hermesNN
# what changed since the job started
find docs knowledge_base -name '*.md' -newermt '<YYYY-MM-DD HH:MM>' -printf '%TH:%TM %s %p\n' | sort
# the deliverable the brief demanded — absent means the job did not finish
ls -l docs/LAPORAN-<job>.md
# last events of the child
tail -5 cache/delegation/live/deleg_<id>/task-0.log
```

Cross-check the brief item by item. Partial state typically looks like: new page created, one
existing page patched, **index/log/SOP untouched, report missing**. mtime alone is enough to
separate "done at 01:16" from "never touched since 00:20".

## 2. Re-dispatch one child, scoped to the remainder

Do not re-run the original brief. A child that repeats finished work duplicates rows
(the classic artefact: the same wiki page listed twice in `index.md`, or the same link printed
twice inside one line).

Structure of the recovery brief:

- **context**: an explicit `SUDAH SIAP (jangan ulang, jangan ubah lagi)` list with file + mtime,
  the durable facts the new child cannot infer (persona table, line numbers verified by `wc -l`),
  and the prohibition list (`SOUL.md`, `OPERASI.md`, `docs/KETUA.md`, `config.yaml`, `.env`,
  `memories/`, plus the already-finished files).
- **goal**: numbered remainder only — each item names the file, the exact insertion text, and the
  count it must reach (`"Jumlah halaman: 8" → 9`, verified with `find … | wc -l`).
- "Cepat: jangan baca seluruh wiki berulang kali. Baca fail yang perlu diubah sahaja." — a child
  that re-reads 18 KB per file burns minutes and truncates its own tail.

## 3. Stay in the turn until the artefact exists

`delegate_task` is background; the owner still reads "dihantar" as unfinished. Poll on the
deliverable, not on the clock:

```bash
cd ~/.hermesNN
for i in $(seq 1 100); do
  if [ -f docs/LAPORAN-<job>.md ]; then echo "SIAP selepas ${i}0s"; break; fi
  sleep 10; printf '.'
done
```

Foreground budget 600 s covers ~10 minutes; the loop exits the moment the file appears. Then
verify — the child's summary is a self-report.

## 4. Verification that catches duplicates (and the child did not)

The first recovery child returned **PASS** while `index.md` carried the page twice and one line
held the same link twice. Its own link check reported `47 pautan, 0 rosak` because existence is
not uniqueness. Assert counts as well:

```bash
grep -c '<slug>' knowledge_base/index.md      # expected number of references, not ">0"
wc -l knowledge_base/index.md                 # line count must match the brief's prediction
find knowledge_base -name '*.md' | wc -l      # page total vs "Jumlah halaman: N"
```

```python
# no link may repeat inside a single line
import re
for i, line in enumerate(open("index.md"), 1):
    links = re.findall(r'\]\(([^)\s]+)\)', line)
    if len(links) != len(set(links)):
        print("DUPLIKAT baris", i, links)
```

Also re-verify the invariants every time, cheap and decisive:

```bash
sha256sum SOUL.md OPERASI.md docs/KETUA.md    # must equal the hashes recorded in the earlier report
grep -rn '<old-term>' docs knowledge_base | grep -v 'LAPORAN-'   # only historical reports may match
```

## 5. Report shape the owner accepts

A two-table board: (i) every child by delegation id with status `terputus / siap / gagal (P1)` and
its live transcript path, (ii) every file with line count and status. Then a third table of the
checks **you** ran yourself, then the still-open items the session did not touch (missing cron,
unfixed persona gap, unresolved naming decision) as a numbered 3–4 option list.

## Lessons

- "Siap" claimed by a child at 6/6 while its report path is missing = the job died, not passed.
- Never dedupe by hand when a child caused it — re-dispatch the two-line fix and record it as P1;
  otherwise the same child keeps producing duplicates and nobody sees the pattern.
- Polling on the artefact file keeps the lead honest: the turn cannot end with work in flight.
