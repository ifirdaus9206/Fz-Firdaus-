# Layer 9 — building `knowledge_base/` (SOP + facts wiki)

Recipe for turning a Hermes home's own prose docs into a queryable wiki that agents can read
instead of carrying facts in memory. Built and verified on `~/.hermes20` (8 pages, 29 internal
links, 0 broken) for the Ketua team.

## Why a separate layer

Memory = experience (what happened). Knowledge = stable reference (SOP, status table, templates).
When facts live in memory they bloat context and skew answers; when they live in a wiki an agent
can be pointed at one page ("baca `knowledge_base/sop/arahan-ejen.md`") and get the same answer
every time. Do not duplicate `memories/` content here.

## Layout that works

```
knowledge_base/
├── index.md            # catalog: sectioned table, one row per page
├── SCHEMA.md           # conventions + frontmatter contract + structure rules
├── log.md              # append-only action log (create / ingest / lint entries)
├── sop/                # procedures: briefs, dispatch, backup, escalation
├── fakta/              # status tables, role lists
└── templat/            # copy-paste artifacts (brief template, checklists)
```

Keep page count small and semantic. `index.md` is the entry point every other page links back to;
`SCHEMA.md` is what stops the next session from inventing a different convention.

## Frontmatter (Malay, when the owner writes in Malay)

```yaml
---
tajuk: "SOP Arahan Ejen"
jenis: sop              # sop | fakta | templat | meta | indeks
kemas_kini: 2026-11-05
sumber: ["~/.hermes20/SOUL.md", "~/.hermes20/docs/PELAN-AI-TEAM.md"]
---
```

`sumber` is the provenance contract: every claim must be traceable to a listed file. If a fact
cannot be traced, it does not go on the page.

## Links: relative markdown, not `[[wikilinks]]`

The owner opens these in whatever editor is at hand (Termux, Obsidian maybe later). Relative
markdown links (`[SOP arahan](../sop/arahan-ejen.md)`) work everywhere; `[[wikilinks]]` only work
in Obsidian. Every page links back to `index.md` in its first lines.

## Evidence discipline (the part that makes it trustworthy)

- **Read every source file before writing.** Do not paraphrase from memory of the doc.
- **Quote the source inline** for each load-bearing fact, in blockquote form with the file path
  after it (`> "..." — SOUL.md, Undang-Undang Tetap #3`). This makes review possible without
  re-reading everything.
- **Missing sources are a finding, not a gap to fill.** `SOUL.md` referenced `docs/KETUA.md` and
  `OPERASI.md`; neither existed. Record "tidak dijumpai" in `index.md` and the report — never
  reconstruct the missing doc from plausibility.
- **Copy status tables verbatim** and keep the source's own labels (`ADA` / `SEPARA` / `TIADA` /
  `PALSU` / `BARU DIBETULKAN`). Add your counts in a separate table, and if the source contradicts
  itself (heading said "11 lapisan", table had 14 rows) keep both numbers and flag it explicitly.
- **Do not silently upgrade a status row** because your new work fills it. The table is a snapshot
  of the source; note "status still says TIADA; needs separate update with evidence" instead.
- **No invented numbers, dates, prices, or scopes.** If the source names six roles but gives no
  per-role duties, write "skop tidak ditulis dalam sumber" rather than inventing duties.

## Template page

`templat/brief-ejen.md` holds the 8-field brief as a fenced block with `<placeholders>` so an agent
can copy it, plus the reminders that matter (named agent, evidence for pass, P1–P4 escalation).
Templates are the highest-reuse pages — write them for copy-paste, not for reading.

## Verify before reporting

Run a link + frontmatter audit programmatically (not by eye) and paste the real output into the
report. `scripts/verify_wiki.py` does this: frontmatter fields present, every page links to
`index.md`, every `](*.md)` target exists.

Pitfalls found while doing it:

- **Regex link checks produce false positives from prose.** Writing the link *format* as an
  example (`` `[teks](laluan.md)` ``) creates a "broken link" to a file that was never meant to
  exist. Describe the format in words, or expect one known-false hit.
- **`index.md` is not exempt from "must link to index".** Add a one-line self-reference
  (`> Halaman ini: [index.md](index.md)`) so a mechanical check passes on every file.
- **Counts must be recomputed after edits.** A "SEPARA | 3" row contradicted its own list of four
  layers; derive counts from the table, then re-read them.
- **Report with the actual `find ... | sort` output**, file sizes from `stat -c %s`, and one quote
  per major fact. The owner audits the report, not the prose.

## Deliverable shape the owner accepts

`docs/LAPORAN-WIKI.md` containing: file list + sizes (real command output), the raw `find` output,
a table of every internal link with "target exists", a quote per major fact mapped to the page that
carries it, and an explicit "isu / had" section listing missing sources and source contradictions.
