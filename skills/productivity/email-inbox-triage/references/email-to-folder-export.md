# IMAP → markdown files in category folders (the "fail, bukan label" pipeline)

Class of task: user wants mail **as files they can open**, one folder per category, and new mail
"terus pergi ke tempat dia tanpa duduk di peti masuk". Labels alone are not the deliverable —
labels are the archive mechanism, folders are what the user looks at.

Working implementation for this account:

| Path | Role |
|---|---|
| `~/vault/email-inbox/autosort.py` | classify + `COPY <label>` + archive (`apply --days 3 --max 400 --archive-lain`) |
| `~/vault/email-inbox/rules.json` | domain & keyword rules, `PENTING → KERJA → PROMOSI` |
| `~/vault/email-inbox/export_files.py` | `sync` (labels → `.md` per folder) and `count` |
| `~/vault/email-inbox/auto.sh` | both steps + delta counting, silent when nothing new |
| `~/.hermes20/scripts/email_auto.sh` | 2-line cron wrapper (`exec bash "$HOME/vault/email-inbox/auto.sh"`) |
| cron `*/10 * * * *`, `no_agent=True` | stdout becomes the chat message |

## Folder layout

```
~/vault/email-inbox/
  1-PENTING/ 2-KERJA/ 3-PROMOSI/ 0-LAIN/    # one .md per email
  _index.csv    _auto.log    rules.json    BACA-DULU.md
  _lama/                                    # pre-migration flat files, deletable later
```

`BACA-DULU.md` in the folder is not optional for this user: plain-Malay "what this is / where
files live / how it runs itself / useful commands". It is the handoff document.

File name: `YYYY-MM-DD_<uid>_<slug>.md`, front-matter `label, uid, tarikh, dari, kepada, subjek`,
then a short human header (`**Dari**`, `**Tarikh**`, `**Kategori**`) before the body.

## Index schema (the part that caused a data bug)

```csv
label,uid,tarikh,dari,subjek,fail,msgid
```

- Dedupe key: `f"{label}:{uid}"` — **not** bare `uid` (label mailboxes restart UIDs at 1).
- Second key: `Message-ID` — catches the same message exported from INBOX and from a label.
- Rewrite the whole CSV on each `sync` (`DictWriter` over the old rows) instead of appending, so a
  schema change never produces mixed headers; `extrasaction="ignore"` keeps old rows harmless.
- When renaming a folder/label, migrate the index in the same breath (`INBOX → LAIN`,
  `0-INBOX/ → 0-LAIN/`) or msgs with a blank `msgid` get re-exported as duplicates.

## Verification that actually convinces

```bash
python export_files.py count                 # per-folder totals
# inside python: SELECT each label, UID SEARCH ALL, compare len(uids) to file count per folder
```

Per-folder file count must equal `UID SEARCH ALL` for the matching label. Do **not** trust
`SELECT` `MESSAGES` counts for the archive step (they lag), but they are fine for the "did the
inbox empty" story: quote `INBOX 17627 → 17588`.

Delta counting for the silent cron:

```bash
kira() { find 1-PENTING 2-KERJA 3-PROMOSI 0-LAIN -name '*.md' | wc -l; }
sebelum=$(kira); ...; selepas=$(kira); baru=$((selepas-sebelum))
[ "$baru" -gt 0 ] && echo "📥 $baru e-mel baharu terus masuk folder ..."
exit 0   # always 0; empty stdout = silence
```

## Sequence that worked

1. Read one sample email and confirm the user's phrasing ("fail, bukan label") before building —
   this user corrects direction mid-task, so restate the target folder tree in 3 lines first.
2. Build `export_files.py`, test with `--limit 3`, **then clear the poisoned index rows** before the
   real run (see UID pitfall in SKILL.md).
3. Archive old flat files to `_lama/`, keep the old index as `_lama/_index_lama.csv`.
4. Full `sync`, then diff per-folder counts against `UID SEARCH ALL`.
5. Add `--archive-lain` so INBOX empties (only after the user asks for it).
6. Wire cron via real wrapper file in `~/.hermes/scripts/`; run the wrapper by hand once and check
   exit 0 with empty stdout.
7. Pause any older overlapping cron (label-only job) instead of leaving two jobs racing.
8. Leave the 17k legacy inbox alone; present it as a numbered decision (ignore / backfill /
   archive all / rebuild files with cleaner text).

## Reporting shape

Board with real numbers, not adjectives: per-folder counts, `INBOX before → after`, cron id and
interval, one line of test evidence ("24 + 13 emails filed, exit 0"), then 3–4 numbered options.
Say plainly when legacy mail was left untouched.
