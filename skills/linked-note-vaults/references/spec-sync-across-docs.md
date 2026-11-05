# Propagating a changed definition across a plan doc + SOP wiki

Class of task: an authoritative definition changed upstream — a persona/role, a policy, a schema field,
a status vocabulary — and **every downstream doc still describes the old one**. The deliverable is
usually: edit N files, add 1 wiki page, append 1 log entry, and prove you did not touch the protected
sources.

Worked instance: `~/.hermes20` persona "Ketua" went from one role ("Arkitek Sistem AI Utama") to
**four stacked roles** (T1 Master Prompt Architect → T2 AI Systems Architect → T3 Multi-Agent Architect →
T4 Agent Factory Architect). `SOUL.md` / `OPERASI.md` / `docs/KETUA.md` were already rewritten and
hash-verified; the plan doc and `knowledge_base/` were stale.

## 1. Map the blast radius before editing

```
grep -rn "<old term>" <root>/docs <root>/knowledge_base <root>/*.md
grep -rn "<new term>\|<tier 1 label>" <same paths>
grep -c '^## ' <plan doc> ; wc -l <every candidate file>
```

Sort hits into three buckets and write them down:

| Bucket | Action |
|---|---|
| Protected / historical (already-correct evidence report, signed persona files) | **read only**; a hit here is expected and must be explained in the report, not "fixed" |
| Stale copies of the old definition (status fact page row, index summary, plan-doc status column) | update in place, keep the surrounding structure |
| Missing (no page explains the new definition) | exactly **one** new page; never more than the task allows |

The old term surviving in an evidence report is normal: `grep` exits 0, so always state *which file* the
remaining hits live in and why. "grep clean" is the wrong claim; "0 hits outside `<historical file>`" is
the right one.

## 2. Edit order that avoids rework

1. Plan/status doc — the structural section (new `##` section + table), then the status row that pointed
   at the old definition, then the priority item's "siap" note.
2. New wiki page (frontmatter `tajuk/jenis/kemas_kini/sumber`, back-link to `index.md`, one table + one
   paragraph per tier, plus the pass rule quoted from the source).
3. Status/ledger page — row + a dated `**Kemas kini YYYY-MM-DD (<topic>):**` blockquote beneath the
   copied table (do not rewrite provenance rows).
4. `index.md` — new row, page count, source note, and any see-also lines.
5. SOP page — the note at the step where the definition gates the output
   (`setiap langkah 1–7 mesti lulus 4 tahap: T1 → T2 → T3 → T4`).
6. `log.md` — append last, after all links exist, so the link tally you quote is final.

Every file you touch also gets `kemas_kini:` bumped. Anything you did *not* touch keeps its date — that
asymmetry is itself evidence.

## 3. Content shape that satisfies "4 tiers" style specs

- One summary table: `Tahap | Peranan | Kerja | Output | Penanda lulus` — five columns, one row per tier,
  every cell filled. Empty cells read as an unfinished spec.
- One paragraph per tier in the page body: what it does, its output, its pass marker.
- A mapping table when a source enumerates layers/systems and each tier owns some of them
  (`T2 → layers 1,2,10`, `T3 → 4,5,6`, `T4 → 7,8,9,13,14`), plus a sentence for any layer deliberately
  left outside (`layer 3 = channel, prerequisite, not an architect duty`). Unowned items get challenged.
- Quote the fixed law that makes the sequence mandatory (`Empat tahap mesti lengkap sebelum lulus …
  Melangkau tahap = NEEDS_WORK`) with file+line, so the page is traceable.

## 4. Report shape (`docs/LAPORAN-<TOPIC>.md`)

1. Verdict line (`PASS` / `NEEDS_WORK`) — never PASS with an open doubt.
2. `Fail | Tindakan | Baris sebelum | Baris selepas | sha256` table.
3. Verbatim shell blocks: `wc -l`, `grep -c '^## '` before/after, the old-term grep **with its exit code
   explained**, `sha256sum` of protected files (before + after), link audit tally, `yaml.safe_load` output.
4. Pass/fail test table (one row per requirement in the brief, incl. "no files deleted", "no writes
   outside the two allowed folders").
5. Caveats: anything the brief got wrong (line counts, page counts), and whether a before-hash was
   obtainable (`git rev-parse` → not a repo → line counts only).

Keep a protected-file hash block identical to the one in the earlier evidence report, so a later reader
can diff the two reports and see zero drift.

## 5. Trap: the evidence report contaminates its own grep

When the acceptance criterion is *"`grep -rn "<old term>" docs knowledge_base` must only return
`docs/<HISTORICAL>.md`"*, the report you are writing **lives inside `docs/`** — quoting the term, the
command, or the raw hit lines verbatim makes the report appear in its own grep output and the criterion
fails on the file that was supposed to prove it passed (this happened: 6 self-hits, verdict would have
flipped to NEEDS_WORK).

Fix, while staying honest:

- Search with a case-insensitive spaced regex so the literal never appears in the report body:
  `grep -rniE "arkitek +sistem +ai +utama" docs knowledge_base | cut -d: -f1 | sort | uniq -c`
- Publish the **per-file tally**, not the matching lines:
  `4 docs/LAPORAN-4-PERANAN.md` — proves "one file only" without reproducing the phrase.
- In prose name the term with separators: *istilah lama (4 perkataan: Arkitek · Sistem · AI · Utama)*.
- One line of disclosure: "corak regex huruf kecil digunakan supaya laporan ini sendiri tidak memasukkan
  semula istilah lama; keputusan sama." A reader can rerun it.
- Forbidden-string checks apply to **every** file you write, including new ones. After writing the report,
  re-run the exact criterion grep — it is the last test, not the first.

## 6. Trap: sibling subagents editing the same four files

Multi-agent fan-out on one wiki means another agent may land edits in `index.md` / `log.md` /
`sop/*.md` while you are working. `patch` warns: *"modified by sibling subagent `<id>` at HH:MM — after
this agent's last read"*. Treat that warning as data, not noise:

- **Re-read the file immediately** before the next edit; never patch against the copy you read before the
  warning. Two agents adding "the same required row" yields a **duplicate table row and duplicate link
  line** — the file parses, links resolve, and only a human (or the next audit) notices.
- After the last edit, run a duplicate check: rows repeated verbatim in a table, the same `[x](y.md)`
  target twice in one section. Dedupe by keeping **one** line, preferring the wording the brief demanded.
- If a sibling already completed an item (log entry, SOP note with equivalent substance), **do not append
  a second one** — the log is append-only, so a duplicate entry is permanent damage. Verify substance
  covers the spec, keep theirs, and note the coverage in the report.
- Line counts churn while others edit: `index.md` went 46 → 50 → 48 (46 → 50 with the added rows, 48 after
  removing a duplicate link). Record the **final measured** value on disk, re-hash every file touched
  after the last write, and state the churn in the caveats instead of hiding it behind one number.
- Re-run the link audit *after* dedupe: the tally moves (47 → 44 here), and the report's number must be
  the one from the final state.
