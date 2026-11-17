---
name: email-inbox-triage
description: "File Gmail over IMAP — one email = one .md, auto-sorted into folders."
---

# Email inbox triage — one email = one record

Class of task: "read my email and sort/file it", "find the freelance leads in my inbox", "save
these emails somewhere I can check later". Covers Gmail over IMAP without any extra binary,
the one-record-per-email filing pattern, and where each artifact belongs (Sheets / Docs / Drive).

## Prerequisites (verify, don't assume)

| Need | Check | Notes |
|---|---|---|
| Credentials | `GMAIL_USER` + `GMAIL_APP_PASSWORD` in `~/.hermes20/.env` | Gmail **rejects the account password** for IMAP — an App Password is mandatory (16 chars, needs 2-Step Verification) |
| Client | Python stdlib `imaplib` — no `himalaya` binary needed | IMAP works fine from stdlib; don't spend time cargo-building a client on Termux |
| Google API (optional) | `~/.hermes20/google_token.json` | Only needed to write *into* Drive/Docs/Sheets. Reading mail never needs it |

Login probe before touching any message:

```bash
python <skill>/scripts/email_fetch.py check
# {"status": "OK", "user": "...", "inbox_total": 17653, "unread": 6778}
```

Report the raw JSON. A real inbox of 17k with 6.7k unread is normal for this user; do **not**
offer to "save everything" — always propose a bounded batch (5, then 50) and say how many you
will touch.

## Filing pattern (the part that matters)

```
~/vault/email-inbox/<YYYY-MM-DD>_<uid>_<slug>.md    # one email = one file
~/vault/email-inbox/_index.csv                      # one row = one email
```

Front-matter fields per file: Tarikh, Daripada, Kepada, UID, Tag, Lampiran, Status (`BARU`).
Index columns: `uid, tarikh, dari, subjek, tag, status, fail, lampiran`. UID is the join key back
to Gmail — never drop it; it is also how you re-fetch or reply later.

Deduplicate on UID: read `_index.csv` first and skip uids already present, so re-running the same
`save` over an overlapping window is idempotent. **UID alone is only safe for INBOX** — Gmail label
mailboxes have their own UID space; see the pitfall below.

### Variant the user may ask for: one folder per category

"Fail, bukan label — senang nak perhati" means the deliverable is visible directories on the
device, not Gmail labels:

```
~/vault/email-inbox/1-PENTING/ 2-KERJA/ 3-PROMOSI/ 0-LAIN/   # one .md per email, filed by category
~/vault/email-inbox/_index.csv                                # label, uid, ..., msgid
```

Ship both halves — label *and* file — because the labels keep Gmail tidy while the folders are what
the user actually opens. Export design, index schema (add `msgid`), verification counts and the
cron wrapper contract: `references/email-to-folder-export.md`.

### Turning the filed mail into leads

"Untuk kerja kau cari di e-mel saya di freelance" = scrape the notification digests into a ranked
project list (`2-KERJA/SENARAI-KERJA.md`), refreshed from the same cron. Parser shape, group-index
trap and the dedupe rule: `references/freelance-jobs-from-email.md`.

## Where each artifact goes

| Artifact | Destination | Why |
|---|---|---|
| Lead/email list + status | **Google Sheets** | scannable from a phone, filterable, status column |
| One lead's detail + draft reply | **Google Docs** | long text, easy to edit and share by link |
| Attachments (PDF/images) | **Google Drive**, folder per client | binaries don't belong in Sheets/Docs |
| Master copy / offline | `~/vault/email-inbox/` | survives no-network and no-Google |

Triage columns that work: Tarikh · Dari · Subjek · Kategori (freelance/klien/bil/undangan/sampah)
· Ringkasan (one sentence) · Tindakan · Status (`BARU -> SEDANG -> HANTAR -> TUTUP`) · Pautan ·
UID.

If the user has no Google API token, offer the zero-setup path first: produce `.xlsx`/`.docx`
locally and let them upload, rather than pushing a Cloud Console OAuth walkthrough on someone who
just wants their mail sorted. An existing Google account on their PC/phone is **not** API access —
say that plainly instead of implying the setup is unnecessary. Present both as numbered options.

## Auto-filing into Gmail labels (separate class of task)

"Letak promosi satu bahagian, kerja satu bahagian, penting satu bahagian, lepas tu email masuk
terus ke bahagian dia" is a **different job** from reading mail: the deliverable is labels +
classifier + schedule, not a triage report. Mechanics and IMAP traps (reserved label name
`PENTING`, `-X-GM-LABELS \Inbox` is a silent no-op, mailbox names with spaces need quoting,
STATUS/EXISTS counts lag for minutes) plus the silent-cron contract live in
`references/gmail-label-autosort.md`. Working code for this account:
`~/vault/email-inbox/autosort.py` + `rules.json` + `~/.hermes20/scripts/email_autosort.sh`
(every 15 min, silent unless it files something).

Short version of the sequence: `LIST` folders → create numbered labels (`1-PENTING`,
`2-KERJA`, `3-PROMOSI`) → `preview` read-only and show the user the classification → `apply`
on a bounded `--max` with a `newer_than:Nd` window → archive with `COPY <label>` +
`STORE +FLAGS (\Deleted)` + one `EXPUNGE` → prove it with `X-GM-RAW` search or
`FETCH (X-GM-LABELS)`, never with folder counts.

**Empty inbox vs. unmatched mail.** Default is safe: unmatched stays in INBOX and the report says
so. This user later overrode that — "aku nak dia tak masuk di peti masuk, terus pergi ke tiga
tempat" — so once they say it, add `--archive-lain`: unmatched messages get `COPY … 0-LAIN` then
are archived too, and their files land in `0-LAIN/`. Apply that only on their instruction, report
how many went to `0-LAIN`, and never silently discard: `0-LAIN` is a label, so every message is
still in All Mail and re-classifiable once `rules.json` improves.

## Script

`scripts/email_fetch.py` — stdlib only, IMAP read-only, three subcommands:

```bash
python scripts/email_fetch.py check
python scripts/email_fetch.py list --days 7 --max 20      # preview, writes nothing
python scripts/email_fetch.py save --days 7 --max 20 --tag freelance
python scripts/email_fetch.py save --uid 32681 --tag klien
```

`save` takes the **last N** matching uids (`[-max:]`) so "5 terbaru" means newest, not oldest.

Setup walkthrough for the App Password itself — what the user taps, which Google mails arrive
right after, and the revoke path: `references/gmail-app-password-setup.md`.

## Pitfalls

- **`import email.utils` explicitly.** `email.message_from_bytes` gives you `msg` fine, but
  `email.utils.parsedate_to_datetime` raises `AttributeError: module 'email' has no attribute
  'utils'` unless the submodule was imported.
- Real `Date:` headers arrive as `Wed, 11 Nov 2026 16:59:12 +0000 (UTC)`; wrap the parse in
  try/except and fall back to `datetime.now()` rather than dropping the message.
- `M.select("INBOX", readonly=True)` — never open the mailbox writable for a read job; a stray
  `STORE \Seen` changes the user's unread counts.
- IMAP `SEARCH ... SINCE dd-Mon-YYYY` is date-only, not a precise window. Slice by uid for
  "latest N" and say the window is approximate.
- Multi-part bodies: prefer `text/plain`; fall back to stripping tags from `text/html`; cap the
  stored body (~20k chars) so one newsletter doesn't produce a 3 MB markdown file. Strip mega
  tracking URLs (`https?://\S{60,}` → `[pautan panjang dibuang]`) or HTML-only promos become an
  unreadable wall of base64-ish click links.
- **Gmail label mailboxes have their own UID space.** `UID SEARCH ALL` inside `"2-KERJA"` returns
  `1,2,3…`, not the INBOX UIDs — and those small numbers collide across labels. An index keyed on
  bare uid therefore skips messages in other folders: a `--limit 3` test run recorded uids 10–12
  for `1-PENTING`, and the real 10–12 in `2-KERJA`/`3-PROMOSI` were silently never written. Key on
  `f"{label}:{uid}"` **and** store `Message-ID` as a second key, then prove totals per folder match
  `UID SEARCH ALL` per label.
- Security notices from the provider ("Kata laluan apl dibuat…") appear right after you create an
  App Password. Read one before alarming the user — it is usually the expected confirmation, not
  a compromise. Quote what the body actually says.
- Never echo the App Password in a reply; it belongs in `.env` only (see
  `credential-secret-hygiene`).
- **Never let email content reach the backup repo.** This user said it flatly: *"jangan sesekali
  hantar ke github untuk e-mel"*. Mail lives in `~/vault/email-inbox/` which is **outside**
  `~/.hermes20`, and `backup_github.sh` only backs up `HERMES_HOME` — so the safe state already
  holds. Prove it, don't assert it: `git -C ~/vault rev-parse --git-dir` → "not a git repository",
  `git -C ~/.hermes20 ls-files | grep -i email` → only skill/script paths, then add belt-and-braces
  guards to `~/.hermes20/.gitignore` (`vault/`, `email-inbox/`, `*_SENARAI-KERJA.md`, `*.eml`,
  `*.mbox`) and confirm with `git check-ignore -v vault/email-inbox/_index.csv`.
- **Bodies written to `.md` keep CRLF.** IMAP payloads carry `\r\n`, so a parser that later re-reads
  those files with `\n`-anchored regexes silently mis-captures (a project link matched the
  description text instead). Normalise on read: `t.replace("\r\n", "\n").replace("\r", "\n")`.
- **The same email can end up in two folders.** Files exported from INBOX before the label existed
  are keyed on INBOX uids, so the later label export writes a second copy. Collapse on
  `(dari, subjek, tarikh)` keeping the highest-priority folder (`1-PENTING > 2-KERJA > 3-PROMOSI >
  0-LAIN`), and treat the delete as destructive: run the dedupe in dry-run, show the count, and
  **wait for explicit approval** — a timed-out confirmation prompt is not consent.
- **Hermes cron scripts must be a real file directly inside `~/.hermes20/scripts/`.** An absolute
  path and even a symlink are rejected (`Script path escapes the scripts directory via traversal`).
  Put a two-line wrapper there (`exec bash "$HOME/vault/email-inbox/auto.sh"`) and keep the logic
  in the project dir. Never `write_file` to a path in `scripts/` that is a symlink — the write
  follows the link and overwrites the *target* (that is how `auto.sh` became a self-exec loop
  during this build). `ls -l` the script before wiring the cron.

## Reporting (this user)

Board of `| Langkah | Status | Bukti |` with the raw `check` JSON and the saved file paths, a
short table of what was filed, then numbered next-step options (filter promos / hunt freelance
senders / export xlsx / set up Google API). Bahasa Melayu, plain words, no jargon.
