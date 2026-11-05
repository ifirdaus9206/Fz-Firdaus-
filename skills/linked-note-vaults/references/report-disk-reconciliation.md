# Worked case: making a stale evidence report match the disk (report-only repair)

Scenario (Termux, `~/.hermes20`, 2026-11-06): two subagents wrote `knowledge_base/index.md`
concurrently, so it went **46 → 50 → 48 → 49** lines. `docs/LAPORAN-KNOWLEDGE-4-PERANAN.md` was written
while the file was 48 lines and was the **only** editable file. The wiki was already correct and had to
stay byte-identical. Language of delivery: Malay.

Task brief listed 8 edits and a verification block. Following it literally was not enough — see
"Numbers the brief did not list" below.

## 1. Baseline before the first keystroke

```bash
wc -l knowledge_base/index.md                      # 49
find knowledge_base -name '*.md' | wc -l           # 9
md5sum knowledge_base/index.md knowledge_base/log.md \
       knowledge_base/sop/arahan-ejen.md knowledge_base/fakta/empat-peranan.md
sha256sum SOUL.md OPERASI.md docs/KETUA.md         # persona files, must not move
ls -l --time-style=+%H:%M:%S knowledge_base/index.md docs/LAPORAN-KNOWLEDGE-4-PERANAN.md
```

The md5 block is the load-bearing one: it is taken **before** any report edit, so the post-edit re-run
proves "doc-only change". Worth recording mtimes too — the report at 01:28 vs `index.md` at 01:31 was the
literal evidence of which file was stale, and it went into §6 as such.

## 2. Link tally with a real script (not `grep -c`)

```python
import re, os, glob
root = "knowledge_base"
files = sorted(glob.glob(os.path.join(root, "**", "*.md"), recursive=True))
total, bad = 0, []
for f in files:
    for m in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', open(f, encoding="utf-8").read()):
        t = m.group(2).strip()
        if t.startswith(("http://", "https://", "mailto:", "#")): continue
        p = t.split("#")[0].strip()
        if not p: continue
        total += 1
        if not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(f), p))):
            bad.append((f, p))
print("fail .md:", len(files))
print("jumlah pautan .md:", total, "| rosak:", len(bad))
```

Result: `fail .md: 9` / `jumlah pautan .md: 45 | rosak: 0`. Scripts live in `scripts/` of this skill
(`wiki_fingerprint.py` prints the same block plus per-file md5).

Second script, for the list block the report quotes verbatim — one line per link occurrence, in source
order, with the real line number:

```python
import re, os
f = "knowledge_base/index.md"
for i, line in enumerate(open(f, encoding="utf-8"), 1):
    for m in re.finditer(r'\[[^\]]*\]\(([^)]+\.md)\)', line):
        p = m.group(1).split("#")[0]
        ap = os.path.normpath(os.path.join(os.path.dirname(f), p))
        print(("ADA " if os.path.isfile(ap) else "ROSAK ") + f"baris {i}: {p}")
```

Pasting that output replaced a hand-maintained `ADA …` list that had three duplicated targets at the
tail (`fakta/empat-peranan.md`, and `enam-peranan`/`status-sistem` twice). The regenerated block is 15
lines: 13, 19, 20, 26, 27, 28, 34, 40, 41, 45×2 (two links on one line: OPERASI + KETUA), 46, 48×2, 49.

## 3. Patch strategy

Eleven `patch` calls in one `execute_code` batch, each anchored on a multi-line unique string, printed
`success`/error per call. Anchors that matter:

- Table row: use the **whole row** (it is one long line) rather than a fragment; the row also carried
  three other claims that had to change together.
- Shell-output block: anchor on the 6 lines of numbers *including* `total`, so the arithmetic
  `100+69+86+49+122+51 = 477` is rewritten visibly (old `476` was the 48-line sum).
- Test-table rows: three separate one-line patches (`(14 pautan)` → `(15 pautan)`, `baris 48` → `baris 49`,
  `(44 pautan)` → `(45 pautan)`).
- New section: anchor on the final `**Verdict akhir: PASS**` and prepend §6 above it. Section numbering in
  that doc is `## 1. Verdict` … `## 5. Nota & had laporan`, so the new one is `## 6.` and must land
  *before* the verdict line, which is bold text, not a heading.

## 4. Numbers the brief did not list — the actual trap

The brief enumerated: 48→49, 44→45, `baris 48`→`baris 49`, rewrite the history paragraph, add §6.
Following only that would have shipped two fresh lies:

| Stale claim | Why stale | Fix |
|---|---|---|
| `baris 44: 134/166 → **154/191**` | that §Nota Sumber note sits at line **45** now; 44 is a blank line | `baris 45:` |
| `os.path.isfile (14 pautan)` | index.md now has **15** `.md` links — it gained a `[index.md](index.md)` self-link on line 13 | `(15 pautan)` |

Rule: after fixing a total, `grep -n` the file for **every** `baris N` in the report and re-verify each
against the real file. The delta between old and new totals tells you nothing about which *other* line
references shifted.

## 5. Closing argument: `grep -c` with a per-line reason

```bash
$ grep -n '48' docs/LAPORAN-KNOWLEDGE-4-PERANAN.md
76:  docs/PELAN-AI-TEAM.md:48:| 5 | Lead agent | …        # line 48 of a DIFFERENT file
99:  da0b908c…dc84…  OPERASI.md                            # sha256 hex contains "48"
136: ADA baris 48: fakta/enam-peranan.md                   # real current line of index.md
175: `PELAN:48`, `status-sistem:31`                        # different file again
201: → 48 baris (satu pautan pendua … dibuang)             # historical timeline (required)
$ grep -c '44' docs/LAPORAN-KNOWLEDGE-4-PERANAN.md
5      # 4 × sha256 hex (…0442…, …dc84…), 1 × "angka 44/48 dalam versi itu sudah basi"
```

The acceptance criterion said "no 48 for index.md may remain", yet the same brief demanded the honest
timeline `46 → 50 → 48 → 49`. Resolution: historical occurrences are labelled as history in §5 + §6,
and the summary enumerates every surviving match with its justification. Never silently purge the
history to make a grep return 0 — and never let a historical sentence read as a current count.

## 6. Cleanup and scope

Helper scripts were written to `~/.hermes20/scripts/`, run, then `rm`'d, because "this file only may be
changed" makes any leftover scratch file a violation. Final proof block:

```
md5 (before == after): f5934fe9… index.md | 88ef6bea… log.md | 8bb3a573… sop/arahan-ejen.md | 0c423f9a… empat-peranan.md
sha256: f2873f04… SOUL.md | da0b908c… OPERASI.md | be95f8e3… docs/KETUA.md
```

Note `/tmp` is not writable from the `execute_code` sandbox on Termux
(`PermissionError: '/tmp/linkcheck.py'`) — use the top-level `write_file` tool into a real home path.
That is a write-location fact, not a broken tool.
