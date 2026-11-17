# Gmail App Password setup, end to end (session-verified 2026-11-12)

Context: user is on Android/Termux, has a Google account on PC + phone, wants the agent to read
mail and file it. No Google Cloud project exists and none is needed for mail.

## What the user has to do (one thing)

`myaccount.google.com/apppasswords` → name it (e.g. `Ketua`) → **Buat** → copy the 16 characters
Google shows (it renders them space-separated, e.g. `xxxx xxxx xxxx xxxx`).

Prerequisite: 2-Step Verification must already be on, otherwise the page refuses to issue one.

## What the agent does (never echoes the value)

1. Strip the spaces, write both keys into `~/.hermes20/.env` via a throwaway script, then delete
   that script — do **not** put the value on a command line that lands in `logs/agent.log`:

   ```python
   # ~/tmp/set_env.py  (delete after running)
   vals = {"GMAIL_USER": "<addr>", "GMAIL_APP_PASSWORD": "<16 chars, spaces removed>"}
   ```
   `python ~/tmp/set_env.py && rm -f ~/tmp/set_env.py`

2. Probe: `python scripts/email_fetch.py check` →
   `{"status":"OK","user":"...","inbox_total":17653,"unread":6778}` (real numbers from the run).
   A `LOGIN_GAGAL` here almost always means the account password was used instead of the App
   Password.
3. Save a bounded batch (`--max 5`), show the file list, then propose 50.

## Things that surprised this user

- Three `Google <no-reply@accounts.google.com>` "Makluman keselamatan" mails arrived immediately.
  Their body read *"Kata laluan apl dibuat … untuk Ketua Termux Hermes"* — i.e. Google confirming
  the key creation, **not** an intrusion. Read one before raising alarm; then say what it says.
- They asked "kena tukar password Google tak?" — answer: no. Only the App Password exists as a
  revocable key; the account password was never seen by the agent.
- They asked "telefon/PC aku dah ada Google, perlu Google Cloud lagi?" — yes, for the agent to
  *write* into Drive/Docs/Sheets (API OAuth). Having the account is not API access. Mail needs
  neither.
- They will leave the pasted App Password in the Telegram chat unless told; ask for the bubble to
  be deleted after the value is confirmed working in `.env`.

## Revoke path (offer it, don't push it)

`myaccount.google.com` → Security → App passwords → **Batalkan** the `Ketua` entry. Access dies
immediately; nothing else in the account changes.
