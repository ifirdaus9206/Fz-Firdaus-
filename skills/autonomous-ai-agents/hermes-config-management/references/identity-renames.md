# Renaming Hermes identities — and the approval pack that precedes them

Worked case: owner decided "persona Ketua → Fatin", "profile sofia → Siti", and asked to
**see the files before anything changed**. Nothing was executed. Everything below is the
repeatable procedure.

## 1. Four names, four mechanisms

Never let one stand in for another. The most common failure is changing the persona name and
telling the owner their bot will now be called X — it won't.

| Name | Lives in | Visible where | Changed by |
|---|---|---|---|
| Persona self-name | `SOUL.md` (+ prose in `OPERASI.md`, `docs/<NAME>.md`) | agent's replies ("Aku Fatin") | editing the markdown |
| Home-channel label | `.env` → `TELEGRAM_HOME_CHANNEL_NAME` | nowhere on the phone; internal prompt/session context | edit `.env` + `hermes gateway restart` |
| Profile id | `profiles/<id>/`, wrapper `~/.local/bin/<id>` | CLI (`hermes -p <id>`, typing the wrapper name) | `hermes profile rename` |
| Telegram bot display name | BotFather | name above the chat | BotFather `/setname` (owner must do it) |

Evidence for the bot line: `grep -rn 'setMyName\|set_my_name' <hermes-source>` returns **0
hits** — Hermes only *reads* identity (`getMe`, `_current_bot_username`) for `@mention`
routing. `config.yaml`'s `display:` block is UI tool-progress, not the bot name. The adapter
re-learns the handle from inbound updates with a 300 s TTL, so a BotFather rename needs no
restart and no new token.

## 2. Inventory the old name before proposing anything

```bash
grep -rn "<oldname>" ~/.hermes20 --include=*.yaml --include=*.json --include=*.md --include=*.env -l 2>/dev/null | head -40
grep -rn "<oldname>" ... | grep -v node_modules
```

Then **classify every hit**. Do not paste a raw file list at the owner — a 8-file list where
6 are noise reads as "this is dangerous" and stalls the decision.

| Class | Real examples seen | Action |
|---|---|---|
| Live reference | `profiles/<id>/SOUL.md`, wrapper script | must be updated |
| Documentation example | a skill's `references/*.md` showing the profile as a sample | optional, cosmetic |
| False positive | font metrics JSON (`"sofia"`, `"sofiaSans"`), Portuguese "filosofia" in a README | never touch |

Two blind spots of that grep, both of which bite:

- `~/.local/bin/<id>` is an **extensionless** script — `--include=*.md …` never matches it, yet
  it is the thing that actually breaks (`exec .../hermes -p <id> "$@"`).
- `cron/jobs.json` *is* a `.json` and *does* get matched — so state explicitly when it has no
  hits ("no scheduled work references the profile").

## 3. Byte-exact copies (the part that gets graded)

`write_file` is for prose. For "copy of the real file, unaltered", read/write **bytes**:

```python
body = open(src, "rb").read()
header = (f"SALINAN — bukan fail asal\nTarikh salinan: {stamp}\nLaluan asal: {src}\n").encode()
open(dst, "wb").write(header + body)
```

Three header lines, then the original from line 4. Verify with the same offset:

```bash
tail -n +4 01-SOUL.md | diff -q - ~/.hermes20/SOUL.md && echo OK
```

Record `md5sum` of the body at copy time so a later mismatch can be attributed rather than
guessed.

## 4. The approval pack

Six files in one dated folder (`~/semakan-<topic>-<YYYY-MM-DD>/`):

| File | Job |
|---|---|
| `00-BACA-DULU.md` | what this pack is, recipient matrix, the N changes (old → new), what will **not** change, 3 phone-friendly check steps, decision word |
| `01..03-<SRC>.md` | byte-exact copies of every file that would be edited |
| `04-PROFILES.md` | verbatim `ls -la` / `du -sh` / risk-grep results, with a plain-language "what happens to sessions/skills/cron" table |
| `05-RENCANA-*.md` | per change: path, line number, SEBELUM, SELEPAS, risk, rollback |

Rules that made it land:

- **Banner at the very top**: "Belum ada apa-apa diubah. Pek ini untuk dibaca sahaja." Repeat
  it at the bottom. The owner's fear is that reading = triggering.
- **Recipient matrix** (`Fail | Untuk siapa | Apa di dalamnya | Perlu baca?`) so a
  non-technical reader knows which two of six files matter.
- **"What the owner sees" column** on the change table. For a `.env` label the honest answer
  is "nothing on screen" — say it, or they wait for a change that never appears.
- **A named decision**: one word to reply (`LULUS` / `JANGAN`), plus "or approve item numbers".
- **Separate the non-system actions**: the BotFather step is not a file edit, so it can never
  be part of "the 3 changes". Call it out as the owner's own manual step.
- **Rollback per change**, not one global "we can revert": backup path + the exact restore
  command, and the inverse command for renames (`hermes profile rename siti sofia`).

## 5. Editing the persona file

Count real self-name hits; separate them from filename references.

```bash
grep -n 'Ketua\|KETUA\|ketua' SOUL.md
grep -o 'Ketua' SOUL.md | wc -l
```

In the worked case: 5 × `Ketua` + 2 × `KETUA`, of which 1 was a heading → **6 self-name
sites**, and 2 hits were paths (`docs/KETUA.md`, `SOUL.md.bak-ketua-2026-11-05`) that must
**not** be edited. Renaming a file path inside prose breaks the reference; that's a different
job with its own fan-out (`OPERASI.md` points at `docs/KETUA.md` too).

Judgement to state in the plan: in other docs the word is often a **job title** ("Tindakan
Ketua", "Siapa boleh luluskan: Ketua"). Recommend leaving those, or adding one clarifying
line (`> Ketua = Fatin (nama diri).`), rather than a 30-site sweep. Offer the sweep as a
separate decision, never bundled.

## 6. Profile rename

```bash
hermes profile rename sofia siti          # 5 steps in one: stop gateway, mv dir,
                                          # rewrite wrapper, update active_profile, honcho
```

- Ids are lowercased on disk (`Siti` → `siti`): `normalize_profile_name`, `profiles.py:306`.
  Valid: `[a-z0-9][a-z0-9_-]{0,63}`; `hermes/test/tmp/root/sudo` reserved.
- Manual fallback, if the command refuses: `mv profiles/sofia profiles/siti`, then delete
  `~/.local/bin/sofia` and recreate `~/.local/bin/siti` with the same two-line wrapper
  (`chmod 700`).
- Refs to fix afterwards: `profiles/<new>/SOUL.md` (it usually names its own path), the
  provisioning skill's example doc, and any dashboard alias. Sessions/skills/cron live
  **inside** the folder and move with it — say plainly that no history is lost; that is the
  owner's actual worry.

## 7. Pitfall that cost real time: the source is being edited under you

`SOUL.md` changed **twice mid-task** (00:30:27, then 00:34:55) by another agent working a
different change, shifting every line number after line 3.

- Copy **last**, verify immediately, and keep the md5.
- Re-grep line numbers right before writing the plan, and tell the reader that numbers are a
  snapshot: "if the file moved again, match on the SEBELUM text, not the number".
- If a system file's mtime is newer than the owner's stated baseline, say who/when, and prove
  your copies still match (`tail -n +4 | diff`). Do **not** claim "no file was touched" from
  memory — check `stat`, then report the delta you did not cause.
