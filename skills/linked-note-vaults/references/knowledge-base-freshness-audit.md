# Worked example — freshness audit of `~/.hermes20/knowledge_base`

Case: 8-page SOP wiki whose `index.md §Nota Sumber` claimed two source files were
"tidak dijumpai" (not found). Both existed. Goal: correct the note, prove the rest of the wiki is
healthy, touch nothing outside the wiki.

## 1. Establish the ground truth first (read-only)

```bash
find ~/.hermes20/knowledge_base -type f | sort          # 8 .md files
wc -l ~/.hermes20/knowledge_base/*.md ~/.hermes20/knowledge_base/*/*.md
wc -l ~/.hermes20/OPERASI.md ~/.hermes20/docs/KETUA.md  # 134 / 166  <- numbers the note must cite
ls -l --time-style='+%Y-%m-%d %H:%M' ~/.hermes20/OPERASI.md ~/.hermes20/docs/KETUA.md
```

Record the `ls` output **before** editing; it is the anti-tampering evidence for the final report.

## 2. Classify each hit before changing it

`grep -rn -iE 'tidak dijumpai|tiada|2026-11-0'` returns three kinds of line — only one is a fix:

| Kind | Example | Action |
|---|---|---|
| Stale factual claim | "`OPERASI.md` **tidak dijumpai**" | fix |
| Legitimate negation | "**Tiada lulus tanpa bukti**" (a rule) | leave |
| Verbatim copy of a dated source table | status table row "TIADA / belum di-setup" | dated note beneath, not an edit |

## 3. Edits (all inside the wiki)

- `index.md`: stale bullet → two bullets — a dated, link-checkable fact line, plus what the wiki's facts
  actually derive from (don't claim the newly-found files are the wiki's sources if they never were).
- `index.md`: `kemas_kini` → today, page count → real file count (8, index included), `sumber:` extended.
- `fakta/status-sistem.md`: `kemas_kini` + blockquote `**Kemas kini <date>:** lapisan 9 kini ADA — <bukti>`
  after the table, stating the table/rumusan remain a copy of the earlier source.
- `log.md`: append only. `patch(old_string=<last 2 lines>, new_string=<same + new entry>)`.

## 4. Audit last, then report

```bash
cd ~/.hermes20/knowledge_base && python3 scripts/verify_md_links.py . --fm tajuk,jenis,kemas_kini,sumber
# jumlah pautan: 33 rosak: 0
find . -type f -newermt '<today> 00:00' | sort   # only the 3 edited files
```

## Traps actually hit

1. Log entry written with `31 pautan` — measured before the entry itself added two links. Final truth was
   33. Always audit after the append and paste that number.
2. `execute_code` building the heredoc command as an f-string → `SyntaxError: f-string: valid expression
   required before '}'` from the checker's own `{}`. Use `r'''...'''` + `%` formatting.
3. Page count "6" in the header vs 8 real files: count *all* `.md`, `index.md` included, and say so.
