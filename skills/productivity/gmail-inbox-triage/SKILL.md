---
name: gmail-inbox-triage
description: Use when inbox sorting misses most emails.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, termux, windows]
metadata:
  hermes:
    tags: [email, gmail, imap, labels, triage, cron, backfill]
    related_skills: [himalaya, hermes-telegram-topic-sessions]
---

# Gmail inbox triage (IMAP label sorting)

Classify incoming mail into Gmail labels and **archive it out of INBOX**, on a cron. The recurring
failure is not a broken classifier — it is a **limit inside the cron invocation** that quietly leaves
years of mail untouched while the job reports success every ten minutes.

## When to use

- *"susun emel aku"*, *"kenapa bukan semua emel kau susun?"*, *"atau perlu cara lain untuk susun
  kesemuanya"*.
- A sorting job reports `ok` every tick but the user still sees a huge INBOX.
- You are about to build or tune a `no_agent` cron that labels mail.

## Shape of the pipeline (this user's install)

```
~/vault/email-inbox/
  autosort.py            # classifier + IMAP mover
  auto.sh                # second pipeline (downloads/indexes)
  _autosort.log          # one line per run: "RINGKASAN: {...}"
  1-PENTING/ 2-KERJA/ 3-PROMOSI/ 0-LAIN/   # local mirrors, not the source of truth
~/.hermesNN/scripts/email_autosort.sh   # cron wrapper (must live in <HERMES_HOME>/scripts/)
```

`autosort.py` subcommands: `folders`, `make-labels`, `peek`, `preview`, `apply`.
`apply` flags: `--max N` (how many messages this run), `--days N` (**only** messages newer than N
days, via `X-GM-RAW newer_than:Nd`), `--dry`, `--archive-lain` (unmatched → `0-LAIN`).

Mechanics worth knowing before tuning:

- It selects **INBOX**, takes the last `--max` UIDs from the search result — i.e. the **newest N**, not
  the oldest. Repeated runs therefore walk backwards through history.
- For every classified message: `COPY` to the label folder, then `STORE +FLAGS (\Deleted)` and
  `EXPUNGE` — so sorted mail **leaves INBOX**. INBOX size is the progress bar.
- Messages that match no rule stay in INBOX and are **re-scanned on every run** unless
  `--archive-lain` sends them to `0-LAIN`.

## Diagnose "bukan semua disusun" in one shot

Count the real mailbox before touching the script (read-only IMAP):

```python
M = imaplib.IMAP4_SSL("imap.gmail.com"); M.login(user, app_password)
for box in ("INBOX", "1-PENTING", "2-KERJA", "3-PROMOSI", "0-LAIN"):
    typ, data = M.select(f'"{box}"', readonly=True)
    print(box, int(data[0]))
```

Measured 2026-11-20: `INBOX 17585`, sorted total **244** (31 + 32 + 115 + 66). The cron was running:

```
python autosort.py apply --max 80 --days 2
```

80 messages per tick **and only the last 2 days** — so nothing older than two days was ever
eligible, and the job still exited 0. That is the whole bug; say it that way instead of "classifier
lemah".

## Fix that was applied

1. **Drop the `--days` filter and raise `--max`.** `apply --max 800` — every run now walks further
   back through history, and new mail is still picked up (it is the newest slice).
2. **Keep the 15-minute cadence.** Measured throughput: **400 messages ≈ 3–4 minutes**; raise to 800
   only after watching one run finish inside the tick.
3. **Backfill math to quote the ETA:** ~240 sorted per 400-message batch (60%) ⇒ 17.5k INBOX ÷ ~480
   per 800-batch ≈ **36 runs ≈ 9 hours** at 15-minute spacing. The user needs that number or they
   assume it is stuck.
4. **Prove the first batch immediately** instead of waiting for cron: run one `apply` in the
   foreground and print the summary line, e.g.
   `{"PROMOSI": 150, "KERJA": 50, "PENTING": 41, "INBOX": 159}`.
5. **Back up before editing** (`email_autosort.sh.bak-<date>`), keep the wrapper in
   `<HERMES_HOME>/scripts/`, and keep it silent when nothing was classified:
   `case "$RING" in *'"PROMOSI": 0, "KERJA": 0, "PENTING": 0'*) exit 0 ;; esac`.

## The `--archive-lain` trade-off (offer, do not decide alone)

~40% of a real INBOX matches no rule (`INBOX: 159` of 400). Those stay put and get re-scanned every
run, so progress slows. `--archive-lain` copies them to `0-LAIN` and clears them from INBOX — INBOX
empties and throughput roughly doubles, at the cost of important-but-unmatched mail landing in
`0-LAIN`. Present both, let the owner choose; that is exactly the kind of decision they answer with a
digit.

## Pitfalls

- **A cron that reports `ok` proves the script ran, not that it did work.** Check the log's
  `RINGKASAN` counts and the IMAP folder counts before believing "sedang berjalan".
- **`--days N` is a filter, not a batch size.** With a 2-day window, old-mail backfill is impossible
  no matter how large `--max` is.
- **`--max` slices the newest N.** Raising it does not make one run sort the oldest mail; it makes
  each run cover more history from the recent end. Progress must be measured by INBOX shrinking.
- **Do not run two sorting jobs over the same mailbox at once.** Existing jobs `email_autosort.sh`
  (labels) and `email_auto.sh` (download/index) are separate; adding a third that also `COPY`+
  `EXPUNGE` will race and duplicate labels.
- **`uids = search[-maxn:]` means unmatched mail is retried forever.** If the same 159 messages
  reappear in every summary, that is expected behaviour, not a loop bug — decide `--archive-lain`
  instead of editing the classifier blindly.
- **Cron script location:** a bare `script=` name resolves to `<HERMES_HOME>/scripts/<name>`, so a copy
  in `~/bin/` produces "Script not found" every tick. Keep exactly one copy and `chmod +x` it.
- **`/tmp` is not writable on Termux** — staging files and `curl -o /tmp/...` silently produce
  nothing. Use `$HOME` or the project dir.
- **Never print `GMAIL_APP_PASSWORD`.** Read `.env` into a dict in-process, use it for
  `smtplib.SMTP_SSL(..., 465)` / `imaplib.IMAP4_SSL`, and report only key names or `sha256[:8]`.

## Verification to quote in the report

- IMAP counts before/after (`INBOX 17585 → …`, each label grew).
- One batch's raw `RINGKASAN` line, with the elapsed time.
- The cron wrapper's next tick: `last_status: ok` **and** `_autosort.log` has a new line (a manual
  `cronjob(action='run')` alone is not proof of the scheduler).
- State plainly which limits you changed (`--max 80 --days 2` → `--max 800`) so "kenapa bukan semua"
  is answered with a before/after, not a promise.
