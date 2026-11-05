---
name: linked-note-vaults
description: Build and audit linked markdown vaults & SOP fact wikis.
platforms: [linux, macos, windows, android]
---

# Linked-note vaults (Obsidian-compatible)

Use when the task is to **create, structure, audit or correct** a markdown vault with two-way links —
long-term memory vaults, Zettelkasten/team-memory hubs, project/decision/lesson archives, and
`knowledge_base/` SOP+fact wikis — especially when Obsidian is not installed and the deliverable must be
plain markdown Obsidian can open later.

For day-to-day note CRUD inside an existing vault, the bundled `obsidian` skill still applies. This skill
covers architecture and proof.

## Vault validity without Obsidian

Obsidian needs nothing but markdown: YAML frontmatter, wikilinks, plain folders. No app, index file or
plugin required. Never install Obsidian to satisfy a vault task; gate delivery on a link audit instead.

Resolve the vault path to a concrete absolute path first (`$OBSIDIAN_VAULT_PATH`, else `~/vault`). File
tools do not expand `$VAR`.

## Folder scheme that scales

- `00-Inbox/` raw capture, emptied weekly
- `10-Projek/` one note per active project
- `20-Ejen/` one note per agent/role — experience log, not a job description
- `30-Keputusan/` dated decisions + reasons (never delete; supersede)
- `40-Pelajaran/` repeatable patterns
- `90-Arkib/` dead notes, kept for reference
- `templates/` copy-me skeletons

Rules that make it memory rather than a dump: one note = one event/decision; dated filenames
(`YYYY-MM-DD-short-title.md`) for decisions; **note = experience, facts go to a separate
`knowledge_base/` wiki** (prices, SOPs, API lists are knowledge, not memory) — state that rule in the
vault README so future writers inherit it.

## Link discipline

- `[[folder/Nota|display]]` for anything crossing folders; path-qualified links survive duplicate basenames.
- README collision: if every folder has `README.md`, a bare `[[README]]` is ambiguous and Obsidian picks
  the nearest match — a "back to hub" line can link to itself. Mitigate with path links plus a unique hub
  alias (`aliases: [Rumah, Vault]` → `[[Rumah]]`); disclose the ambiguity if a spec demands `[[README]]`.
- Each role/agent note: hub link, folder-index link, project link, template link, lesson link, decision
  link — ~6 links clears a "≥2 links" bar comfortably.
- Two-way proof means both directions shown: `20-Ejen/ops.md → [[README]]` AND `README.md → [[20-Ejen/ops]]`.

## Two link styles — match the vault, don't mix

- **`[[wikilink]]`** — personal/Obsidian vaults (this skill's `scripts/verify_wikilinks.py`).
- **`[teks](../fail.md)`** — SOP / `knowledge_base/` wikis meant to be readable in any editor.
  Regex `\]\(([^)]+\.md)\)`; resolve with `os.path.normpath(os.path.join(os.path.dirname(file), target))`
  — always relative to the *file's* directory, never cwd. Audit with
  `python3 scripts/verify_md_links.py <dir> --fm tajuk,jenis,kemas_kini,sumber` (also checks frontmatter
  keys + H1). Add new links in the style the vault already uses; a `[[...]]` dropped into a
  markdown-link wiki is invisible to its own audit.

## Reports must not trip their own acceptance test

Failure modes that make a finished job read as failed:

- **The evidence report contaminates its own grep.** If the criterion is "grep for `<old term>` outside
  the historical report must be empty", quoting the term or the hit lines inside the report you are
  writing puts it right back into `docs/`. Search with a case-insensitive spaced regex
  (`grep -rniE "arkitek +sistem +ai +utama" … | cut -d: -f1 | sort | uniq -c`), publish the per-file
  tally instead of the lines, and rerun the criterion **last**, on the report itself.
- **A `patch` warning naming a partial read is also a re-read signal.** The tool says the file was last
  read with offset/limit — trust it and re-read before the next edit, otherwise the next anchored
  `old_string` may match the wrong occurrence.
- **An external writer can edit the file between your writes.** Observed: `index.md` dropped from 49 to
  48 lines ~20 s after a successful patch (a legitimate `- Peranan Ketua: …` note deleted, not a
  duplicate), mtime and size moving with no tool call from this session. Detect drift, don't rationalise
  it: poll `md5sum <f>; stat -c '%Y %s' <f>` three times a few seconds apart. If the hash moved without
  your write, re-read, decide whether the removed line was legitimate, restore only that, and state in
  the report that a concurrent write occurred at mtime T (restored / not restored). Never claim every
  change in the diff as yours.
- **Sibling subagents edit the same files.** Duplicate table rows / duplicate link lines and a second
  append to an append-only log are the usual damage; dedupe, never double-append, then re-measure line
  counts and links after the final write (they churn: 46 → 50 → 48 → 49 — 49 came back after a
  concurrently-deleted `- Peranan Ketua:` source note was restored; 47 → 44 links here).

## Duplicate-link repair: audit per line, not with `grep -c`

`grep -c "empat-peranan.md" index.md` counts **lines** containing the string, not occurrences — so it
cannot certify "no link repeated on one line", and a brief that demands `grep -c` → 4 *and* no
per-line duplicates is self-contradictory (deduping one line necessarily drops the count). Measure three
distinct things and report which is which:

```bash
grep -c  '<target>' index.md         # lines containing it
grep -o  '<target>' index.md | wc -l # occurrences (label text + URL in one link = 2)
grep -c  '^| \[<target>\]' index.md  # rows in the table (want exactly 1)
python3 scripts/audit_md_link_dupes.py index.md --resolve   # authoritative test
```

`scripts/audit_md_link_dupes.py <file|dir> [--resolve]` prints line count, total `.md` links, and every
target repeated **within the same line** (the only real definition of a duplicate), plus each target's
occurrence count with its line numbers and any missing relative target. It exits 1 on a duplicate, so it
doubles as the acceptance gate.

Repair shape when a task says "delete the second of two identical table rows, keep the better summary":

- Use `patch` with the **two rows together** as `old_string` and the surviving row as `new_string` —
  anchoring on one row alone can hit the wrong copy since the rows differ only in the summary text.
- Fix duplicate link **inside one line** by replacing the whole line: `[t](t) · [t](t)` →
  single `[t](t)`. Trailing separators (` · `) must go with it, or the line ends in a dangling joiner.
- After the edit, `wc -l` must equal the old count minus the deleted rows; a second, unexplained drop
  means an external writer, not your patch (see the sibling/concurrent-writer bullets above).

## Correcting stale facts in an SOP wiki

The stale sentence usually sits in a `## Nota Sumber` / source-note section claiming a file was
"tidak dijumpai" (not found). Before writing anything, **verify on disk**: `wc -l` + mtime for every file
the note names, `find <wiki> -type f | wc -l` for the page count claimed in the header.

- Replace the claim with a dated, checkable line + real relative link:
  `[OPERASI.md](../OPERASI.md) (134 baris)` — path relative to the wiki file, verified by the audit.
- **Do not rewrite dates in copied source tables.** If a table is a verbatim copy of a source doc dated
  earlier, its "TIADA / belum di-setup" rows may now be false, but editing the copy destroys provenance.
  Add a dated blockquote *beneath* the table (`**Kemas kini YYYY-MM-DD:** lapisan N kini ADA — <bukti>`)
  and say the summary counts below still describe the source table.
- Also fix the header claims the stale note contradicts: `jumlah halaman` (count `.md` files, including
  `index.md`), `kemas_kini` in frontmatter of every file you edit, and add the newly confirmed files to
  `sumber:` so the provenance claim stays traceable.
- **Append-only logs stay append-only.** Never edit the old entry, even when it states the falsehood;
  append a new `## [YYYY-MM-DD] fix | ...` entry that names the correction. Implement it as a `patch`
  anchored on the file's last lines (`old_string` = tail block, `new_string` = tail + new entry) so no
  earlier byte is rewritten.
- **Count links only after the log entry lands** — log entries contain markdown links and silently
  change N. Writing "31 pautan" from a pre-append measurement, then appending two links, produces a
  wrong number in the very log you just wrote. Re-run the audit last and paste its number.
- Prove non-modification outside scope: `ls -l --time-style='+%Y-%m-%d %H:%M' <protected files>` (mtime
  unchanged) and `find <wiki> -type f -newermt '<today> 00:00'` (should list only the files you edited).

## Baseline before you edit (hash evidence)

Evidence tables want a **before → after** column, so capture the baseline in the *first* tool call, not
after editing:

```
sha256sum <protected files> <files you are about to edit>   # write to .evidence-baseline.txt
wc -l <same list>
grep -c '^## ' <main doc>          # heading count before structural additions
find <wiki> -name '*.md' | wc -l   # page count before
```

`scripts/evidence_baseline.sh` does snapshot + diff (`snapshot` then later `diff` prints a
before/after/sha table). Without a baseline, a "protected files unchanged" claim can still be proven by
comparing against a hash you already recorded elsewhere (e.g. an earlier evidence report), but the
before-hash of *edited* files is unrecoverable — check `git rev-parse --is-inside-work-tree`; if the
vault is not a repo, say so plainly in the report and fall back to line counts. Never invent a
before-hash to make the table look complete.

Trust your own measurement over numbers quoted in the task brief: briefs say "67 baris" / "8 halaman"
when `wc -l` says 66 and `find` says 9. Measure, use the measured value everywhere, and add one line to
the report naming the discrepancy (it is the brief that is stale, not the vault).

## Verify before claiming success

Run `scripts/verify_wikilinks.py <vault>` for `[[wikilink]]` vaults, or
`scripts/verify_md_links.py <dir>` for markdown-link wikis: prints every link with resolved target, a
unique-target tally, and exits non-zero on dangling links. Then prove the tree with real output: `find <vault> -type f | sort`,
`find <vault> -type d | sort`, `find <vault> -type f | wc -l`. Generate the audit table from the same parse
that validated the files — never retype it from memory.

## Frontmatter pitfalls

- `tarikh: {{date:YYYY-MM-DD}}` is invalid YAML (the `{` opens a flow mapping). Quote it:
  `tarikh: "{{date:YYYY-MM-DD}}"`.
- Parse every note's frontmatter with a YAML loader after writing; Obsidian silently drops bad properties.
- Backticked prose like a wikilink example inside backticks is still matched by naive regexes; reword it
  or the audit reports a phantom broken link.

## Round-trip editing pitfalls (table-heavy wikis)

- **`read_file` returns `N|content` — those prefixes are not part of the file.** Never rebuild a file
  from that string: splitting on `|` destroys every markdown table cell, and table-heavy fact pages are
  almost all cells. For a byte-faithful append or rewrite, read with `open(path).read()` inside
  `execute_code`; for surgical changes use `patch` with an anchored `old_string`.
- **Do not assume a trailing newline when appending.** Check the real tail first
  (`tail -c 300 log.md | od -c | tail -5`); an append-only log may end without `\n`. Normalise with
  `raw.rstrip("\n") + "\n" + entry` rather than asserting `endswith("\n")` — that assertion is exactly
  what fails mid-task and costs a round-trip.
- Appending a page's worth of markdown moves the link count and the line count; re-measure *after* the
  last write and use that number in the report (both were stale once in this class of work).
- Re-hash any file you touch a second time. Editing `kemas_kini` after you recorded a sha256 leaves the
  evidence table lying about the file it describes.

## Running the audit from `execute_code`

**First choice — run the Python inline in the `execute_code` sandbox.** The sandbox shares the session
cwd and the real filesystem, so `open()`, `glob`, `os.path` and `yaml` all work on the vault directly.
This skips the shell-quoting layer entirely and is what produced the trustworthy link/frontmatter tally:

```python
import os, re, glob, yaml
os.chdir(os.path.expanduser("~/.hermes20/knowledge_base"))
for f in sorted(glob.glob("**/*.md", recursive=True)):
    ...  # parse, print "jumlah pautan: N | rosak: M"
```

**Second choice — heredoc through `terminal()`**, when you specifically need the command recorded as a
shell invocation: `terminal("cd <dir> && python3 - <<'PYEOF'\n" + script + "\nPYEOF")` where
`script = r'''...'''` is a **plain raw string**. Do not build that command as an f-string — the checker's
own braces (`{...}` in dicts, f-strings, format specs) are parsed as f-string replacement fields and the
outer script dies with `SyntaxError: f-string: valid expression required before '}'`. Use `%` formatting
or concatenation for the cd path. Keep the heredoc quoted (`<<'PYEOF'`) so `$` and backticks survive.

If a heredoc call comes back empty or as a bare newline, **do not debug the heredoc** — rerun the same
body inline (first choice) and move on. A swallowed audit is not evidence; an unquoted re-run is
30 seconds. Note in the report which method actually produced the numbers.

**Do not stage helper scripts from inside the sandbox.** A `write_file` to `/tmp/x.py` issued from
`execute_code` can report success yet the path does not exist for `terminal("python /tmp/x.py")` — the
sandbox and the shell do not share `/tmp`. Either run the audit inline (first choice), or write the
script with the top-level `write_file` tool to a real home-directory path
(`~/.hermes20/_lc.py`), run it via `terminal`, then delete it. Also avoid reusing the variable name you
use for the script body (`script = ...; open(script, "w")` overwrites the content with the path).

When scoping a `find` for evidence, parenthesise `-o`: `find . -name '*.md' -path '*knowledge_base*' -o
-path './SOUL.md'` without `\( ... \)` matches far more than intended and dumped 51 KB of unrelated
node_modules paths into the transcript. Prefer `stat -c '%Y %n' <explicit file list>` for mtime proof.

## Reconciling a stale report with the disk (report-only repair)

Common follow-up: the wiki is **already correct** and the only editable file is the evidence report
whose numbers were measured before a concurrent write landed. The deliverable is "the report no longer
contradicts the disk", not a wiki edit. Rules:

- **Fingerprint the wiki BEFORE touching the report.** `md5sum` the 3–4 wiki files named in the report,
  plus `wc -l`, `find … | wc -l`, and the link tally. After the report edits, re-run the same four
  commands and paste both blocks: identical hashes are the proof that a doc-only fix changed no content.
  `scripts/wiki_fingerprint.py <dir>` emits exactly that block (per-file md5, pages, links, broken) for
  before/after diffing.
- **A changed total cascades into every dependent line number.** Fixing `48 → 49` left
  `baris 44: 134/166 → 154/191` stale, because that note now sits at line 45; the report also quoted
  `baris 48` for the link that had moved to 49. After any count change, re-derive *every* `baris N`
  claim in the report against the real file (`grep -n '<distinctive text>' <file>`), and re-read the
  region around the old number instead of trusting the delta.
- **Re-measure counts the brief did not mention.** Briefs enumerate a subset: this one said index 49 /
  links 45 but left "(14 pautan)" in a test row, and the real count was 15 (a self-link on line 13).
  Every number in the report is a claim; sweep the whole file for digits that describe disk state.
- **Regenerate list blocks by running a script and pasting its output**, do not hand-edit the list.
  A script printing `ADA baris N: target` per occurrence produced 15 lines in source order — one line
  per link, duplicates only where two distinct lines really link the same target — which is both honest
  "raw output" and satisfies "list each link once, by its line". Hand-patching such a block is how the
  duplicated `ADA fakta/empat-peranan.md` tail happened.
- **Keep the history the criterion seems to forbid.** "No stale 48 may remain" collides with "record
  honestly that it went 46 → 50 → 48 → 49". Resolve by labelling: historical state belongs in an
  explicit `## N. Nota pembetulan laporan (<time>)` section and the §nota/had paragraph, phrased as a
  timeline, never as a current count. Then triage every surviving match of the old number and say why
  each is right — other files' line numbers (`PELAN:48`), sha256 hex fragments containing the digits,
  real current line numbers of the file, historical timeline.
- **`grep -c "<n>"` is the closing argument, not a verdict.** Report the count *and* the per-line
  reason; a bare `0` is impossible once hex hashes and timelines live in the same file.
- **Scratch scripts are files too.** If the task says "only this file may change", write helper scripts
  to a real home path, run them, then `rm` them — and say so in the summary. Leaving `scripts/_lc.py`
  behind is a scope violation even when the wiki is byte-identical.

Worked transcript, patch set and grep triage: `references/report-disk-reconciliation.md`.

## Reporting

Order: outcome → file list → real `find` output → link table with ADA/TIADA (exists/missing) → unique-target
tally → two-way proof → design caveats. Embed verbatim command output.

For a **correction/maintenance** task the report is shorter and proof-first: one-line verdict, table of
files touched with `wc -l` before → after, the replacement lines quoted verbatim, the audit line
(`jumlah pautan: N rosak: 0`), then mtime/`find -newermt` output proving untouched files stayed untouched.
Answer in the language the user wrote in (Malay for this user's `~/.hermes20` SOP work); note explicitly
when a link count changed because you added links, so the rise from N to N+k isn't read as a regression.

See `references/vault-structure-memory.md` for skeletons and the report template,
`references/knowledge-base-freshness-audit.md` for a worked stale-fact correction (commands, classification
table, traps), and `references/spec-sync-across-docs.md` for the multi-doc variant — an upstream
definition (persona, policy, schema field) changed and the plan doc + wiki must catch up, with the
edit order, content shape, and evidence-report skeleton that pass review — plus §5–6 on the
self-contaminating grep and sibling-agent collisions.

`scripts/evidence_baseline.sh snapshot|diff <dir> <files...>` captures the before/after line-count +
sha256 table for that report when the tree is not a git repo.
`scripts/wiki_fingerprint.py <dir> [--links-only] [--keys=tajuk,jenis]` prints the page/link/md5 block to
run before and after a **report-only** edit — identical output proves the wiki was not touched.
`scripts/audit_md_link_dupes.py <file|dir> [--resolve]` is the per-line duplicate/link-count gate for
index-style files — run it before and after any dedupe edit.
