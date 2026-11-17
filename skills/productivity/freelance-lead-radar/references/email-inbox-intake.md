# Email inbox intake → local vault → Google Workspace

Session: 2026-11-12 (Termux/Android, owner wants freelance work handled from Gmail only).

## What the owner asked for, restated as requirements

1. Read the mailbox **one email at a time** — no merged digest, no "top 10 emails" summary.
2. Each email becomes **its own saved record** with a trail back to Gmail (UID).
3. Freelance work can be run entirely from email; other kinds of work follow the same pattern.
4. Save the result to **Google Drive / Docs / Sheets only** — pick whichever fits the material.
5. Nothing is sent, filed, or deleted without the owner's approval.

## Tooling reality on this device

| Option | State | Verdict |
|---|---|---|
| `himalaya` | not in Termux `pkg` (only `msmtp`, `notmuch`), would need a cargo build | skip |
| Bundled `email/himalaya` + `productivity/google-workspace` skills | shipped by Hermes → **protected**, read-only for the curator | follow, don't edit |
| Google API python libs | install with `google-workspace/scripts/setup.py --install-deps` (took ~16s) | do this early |
| OAuth token | was absent (`NOT_AUTHENTICATED`) — needs the human login step | blocks Sheets/Docs/Drive |
| stdlib `imaplib` + App Password | works with **zero** installs | chosen for the read path |

So the read path never needs a new binary; only the *write* path to Drive/Docs/Sheets needs OAuth.

## Script: `~/.hermes20/scripts/email_fetch.py`

Stdlib only (`imaplib`, `email`, `csv`, `argparse`). Credentials come from `~/.hermes20/.env`
(`load_env` reads it, real env wins) — never from the script body.

```bash
cd ~/.hermes20
python scripts/email_fetch.py check                      # {"status":"OK","inbox_total":N,"unread":N}
python scripts/email_fetch.py list  --days 7 --max 20    # JSON per line: uid,date,from,subject,attachments
python scripts/email_fetch.py save  --days 7 --tag freelance
python scripts/email_fetch.py save  --uid 1234 --tag klien
```

Design choices that matter (keep them if the script is rewritten):

- `IMAP4_SSL("imap.gmail.com")` + `select("INBOX", readonly=True)` — the intake must never mutate
  the mailbox.
- UIDs, not sequence numbers: `m.uid("SEARCH", None, "SINCE", "<dd-Mon-yyyy>")` and
  `m.uid("FETCH", uid, "(RFC822)")`.
- Headers decoded with `make_header(decode_header(...))`; prefer the `text/plain` part, fall back to
  `text/html` stripped of tags; collect `get_filename()` parts as the attachment list.
- One file per message: `~/vault/email-inbox/<YYYY-MM-DD>_<uid>_<slug>.md` with a fixed header
  block (Tarikh / Daripada / Kepada / UID / Tag / Lampiran / Status) then `## Isi`.
- Append to `_index.csv` (`uid, tarikh, dari, subjek, tag, status, fail, lampiran`) and skip UIDs
  already present — the save command is therefore idempotent and safe to re-run.
- Exit with a named failure, not a traceback: `TIADA_KELAYAKAN: set GMAIL_USER and
  GMAIL_APP_PASSWORD` / `LOGIN_GAGAL: …(App Password 16 aksara diperlukan)`.

## Where each material belongs

| Material | Store | Why |
|---|---|---|
| Email/lead list with status | **Google Sheets** | scannable on a phone, filterable, status column |
| One lead's detail + reply/proposal draft | **Google Docs** | long text, editable, shareable link |
| Attachments (PDF, images, work files) | **Google Drive**, folder per client | binary; Sheets/Docs are wrong containers |
| Master local copy | `~/vault/email-inbox/` + `_index.csv` | survives no-internet / no-Google |

Sheet columns used: `Tarikh | Dari | Subjek | Kategori | Ringkasan | Tindakan | Status | Pautan | UID`.
Status flow: `BARU → SEDANG → HANTAR → TUTUP`.

## Pitfalls

- **The account password is not an IMAP credential.** Google removed "less secure apps"; only a
  16-char App Password works (`myaccount.google.com/apppasswords`, requires 2-step verification).
  Say this *before* the owner pastes anything, and never echo the value back into chat or a file.
- **Do not conflate credentials across services.** In this session the owner offered "that password"
   meaning the GitHub one; GitHub ≠ Google. Name which account a secret belongs to explicitly.
- **Don't claim inbox access before probing.** `setup.py --check` → `NOT_AUTHENTICATED` and
  `which himalaya` → empty were the honest evidence used in the status board.
- **A "5 emails first" pilot beats a full sync.** Owners accept the pipeline faster after seeing one
  real saved record with a real UID.
- Termux: `/tmp` is read-only — scratch files go to `~/tmp`.
- Pyright flags `imaplib` calls as `bytes`/`None` type errors; they are runtime-fine. Do fix real
  ones it catches, e.g. `import email.utils` before using `email.utils.parsedate_to_datetime`.

## Verified output shape

```
$ python scripts/email_fetch.py check
TIADA_KELAYAKAN: set GMAIL_USER and GMAIL_APP_PASSWORD dalam ~/.hermes20/.env   (exit 1)
```

That failure line is the acceptance test for the un-credentialed state: named cause, no traceback.
