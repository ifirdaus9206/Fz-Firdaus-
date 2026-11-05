# Merging N role prompts into one tiered identity

Trigger: the owner pastes a numbered list of role statements —

```
1  Anda ialah Master Prompt Architect ...
2  Anda ialah AI Systems Architect ...
3  Anda ialah Multi-Agent Architect ...
4  Anda ialah Agent Factory Architect ...
```

— usually with a correction attached: *"untuk nama kau dan kerja kau tadi aku tersilap tulis"*, i.e. the
persona currently in `SOUL.md` carries the wrong job title. This is **not** a rename (`identity-rename.md`)
and **not** a new agent. It is one person, several competences, and the owner has to choose the shape
before you touch a file.

## 1. Get the shape approved first

Ask exactly one question with 4 selectable options (this owner answers by number and dislikes forms):

1. Merge all into ONE lead identity with N tiered roles.
2. Pick one as primary; the rest become supporting capabilities.
3. Keep the name, list the roles as a job title only.
4. Full rewrite, old file kept as `.bak`.

"Gabung keempat-empat jadi SATU identiti Ketua (4 peranan bertingkat)" is the option that wins in
practice — it matches how the owner thinks about the lead: one voice, escalating competences.

## 2. Build the tiers so each is testable

A tier that is only a title is decoration. Every tier gets three lines: **what it does**, **Output**,
**Penanda lulus** (pass marker). Without a pass marker the owner cannot tell T2 from T4 later.

```markdown
**Tahap 1 — MASTER PROMPT ARCHITECT** (reka fikiran)
<what it does>
Output: fail arahan 8 medan + prompt peranan ejen.
Penanda lulus: tiada arahan kabur, tiada medan tertinggal, output boleh diuji.
```

Order them so each tier feeds the next (thinking → architecture → team → factory). Then map the tiers
onto the existing 7-step dispatch flow so the doctrine stays executable — e.g. T1 owns steps 1 & 4,
T2 steps 2 & 6, T3 steps 3 & 7, T4 step 5 (dispatch through the console engine).

## 3. Do not delete an existing law — relocate it

The old persona's law 6 usually said *"the 8-system flow runs inside the agents"*. Merging adds a law
("empat tahap mesti lengkap sebelum lulus"), so the 8-system sentence has to **move** under the tier
that owns it (T4 Agent Factory), not vanish. Keep the numbering at seven laws; add the new one and set
the old text — verbatim — inside the tier block.

## 4. Sync every dependent doc in the same wave

A persona change breaks three documents at once. Grep for the old title and for cross-references:

```bash
cd ~/.hermesNN
grep -rn "Arkitek Sistem AI Utama" SOUL.md OPERASI.md docs/KETUA.md   # stale title must return nothing
grep -n '§' OPERASI.md docs/KETUA.md                                   # cross-refs after renumbering
```

| Doc | What breaks | Fix |
|---|---|---|
| `SOUL.md` | identity block, law 6 | rewrite tiers, relocate 8-system flow |
| `OPERASI.md` | no tier section; checklist count | add `## 1. Empat peranan bertingkat`, add a `Tahap` column to the 7-step table, checklist 6 → 7 boxes, renumber §4/§5 refs |
| `docs/KETUA.md` | law table row 6 still quotes the old text; `§3`/`§5` cross-refs point at moved sections | update the row, insert the same §1, add prohibitions ("hantar brief kabur", "melangkau tahap") |

**Second wave — the plan doc and the wiki.** A lead persona is also quoted in `docs/PELAN-AI-TEAM.md`
(layer 5 "Lead agent", the P1 paragraph) and across `knowledge_base/`. Do this as a *separate*
`delegate_task` after the three runbook-persona files are already signed off, and forbid the child from
touching `SOUL.md` / `OPERASI.md` / `docs/KETUA.md` / the previous `LAPORAN-*.md`:

| Target | Change |
|---|---|
| `docs/PELAN-AI-TEAM.md` | new `## Empat peranan Ketua (bertingkat)` section (Tahap·Peranan·Kerja·Output·Penanda lulus) + a second table mapping each tier to the video layers it answers; rewrite the layer-5 row to cite `SOUL.md <range>`; keep every existing row and the P1–P8 list |
| `knowledge_base/fakta/<tiers>.md` | **new** page: 1 table + one short section per tier, frontmatter per `SCHEMA.md` |
| `knowledge_base/fakta/status-sistem.md` | layer-5 row + any "one role only" sentence |
| `knowledge_base/index.md` | new row under Fakta, bump `kemas_kini` and "Jumlah halaman" to the real file count |
| `knowledge_base/sop/arahan-ejen.md` | note on the dispatch step: T1→T2→T3→T4 must all pass before a verdict |
| `knowledge_base/log.md` | **append** one dated entry; never rewrite old entries |
| `docs/LAPORAN-<topik>.md` | the evidence report (below) |

Pitfall of this wave: a tidy rewrite tempts the child to "clean up" the source's own contradictions
(the PELAN status table says `11 lapisan` while listing 14). Keep the source's numbers verbatim and add
a note; silently renumbering makes the report unauditable.

Also update the `Kemas kini` block in both docs (date, what changed, sources read) — the runbook pair
convention requires it.

## 5. Evidence the owner can audit

One agent, one report: `docs/LAPORAN-<topik>.md` with

- a table `Tahap | Peranan | Fail bukti | Nombor baris sebenar | Status`,
- the raw `grep -n` output in a code block,
- `sha256sum` of the three persona files (so later edits are detectable),
- verdict PASS only if every check passed.

Re-run the greps yourself before signing. Line numbers that arrive without matching your own `grep -n`
are fabricated, whatever the agent claims.

### Count claims: recompute, and count them twice

Two counting traps, both seen in one wave:

- **Never quote a line count you did not measure.** A brief that says "the file is 67 lines" when
  `wc -l` says 66 makes the child inherit a wrong baseline and honestly report the discrepancy.
  Measure before briefing: `wc -l <file>` plus `grep -c '^## ' <file>`.
- **`wc -l` ≠ content lines when the file lacks a trailing newline**, and agents routinely report
  `before → after` off by one (claimed 50, real 49, trailing `\n` present). Verify with both
  `wc -l` and `awk 'END{print NR}'`; when they disagree with the report, correct the number on the
  board and log it as **P1 tegur** (record, do not drop a tier, do not re-run the job) — the work is
  fine, the evidence arithmetic is not.
- **Count the artefact, not the folder listing.** Wiki size = `find knowledge_base -name '*.md' | wc -l`
  and it must equal the "Jumlah halaman" line in `index.md`.

### Making the stale-title grep honest

`grep -rn "Old Job Title" docs knowledge_base` will always hit the evidence reports that *quote* the
old title as a test result — the historical `LAPORAN-*.md` from the first wave plus the new report you
are writing now. Group by file before judging:

```bash
grep -rn "Arkitek Sistem AI Utama" docs knowledge_base | cut -d: -f1 | sort | uniq -c
```

Pass condition: hits appear **only** in `LAPORAN-*.md` files, zero in `SOUL.md`, `OPERASI.md`,
`KETUA.md`, `PELAN-*.md` and every `knowledge_base` page. Say exactly that in the verdict instead of
"grep bersih" (which would be false). Parse frontmatter with `yaml.safe_load` when PyYAML is present —
"semak manual" is a weaker claim and must be labelled as such.

## Pitfalls

- **Roster agents cannot do this job.** The console/agency executor is text-only: asked to write the
  report it may refuse ("saya tiada alat") and return a protocol. Score NEEDS_WORK, then re-send the
  same brief to `delegate_task`.
- **Persona changes only take effect next session** — tell the owner to `/new`, and demonstrate the new
  behaviour immediately with one real dispatch in the current session.
- **Don't rename the persona while merging roles.** If the owner also wants a new name, that is the
  three-surface job in `identity-rename.md`; do it in a separate pass with the count split shown.
- **Keep the UIM-style locked meanings in the header.** The owner pins acronym meanings; a rewrite that
  drops the pinned line reads as an unauthorised rebrand.
