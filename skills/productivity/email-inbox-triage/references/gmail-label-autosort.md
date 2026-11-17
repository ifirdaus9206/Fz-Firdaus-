# Gmail label auto-filing over IMAP (no Google API needed)

Class of task: "letak email promosi satu bahagian, kerja satu bahagian, penting satu
bahagian — lepas tu email masuk terus ke bahagian dia". Server-side Gmail filters need
OAuth (Google Cloud); this IMAP route works today with the App Password already in
`~/.hermes20/.env`, at the cost of a polling delay and needing the phone alive.

Reference implementation for this account:
`~/vault/email-inbox/autosort.py` (`folders`, `make-labels`, `peek`, `preview`, `apply`),
`~/vault/email-inbox/rules.json`, wrapper `~/.hermes20/scripts/email_autosort.sh`,
cron every 15 min (`no_agent=True`, script = wrapper).

## Hard-won IMAP facts

| Attempt | Result |
|---|---|
| `m.create("PROMOSI")` | OK — IMAP CREATE really does create a Gmail label |
| `m.create("PENTING")` + `STORE +X-GM-LABELS ("PENTING")` | BAD `Label name is not allowed` — collides with system label "Penting"/Important. Fix: number the labels (`1-PENTING`, `2-KERJA`, `3-PROMOSI`), which also sorts them in the sidebar |
| `STORE -X-GM-LABELS (\Inbox)` | returns OK, **INBOX count unchanged** — does not archive. Waste of time |
| `COPY <uid> <LABEL>` then `STORE +FLAGS (\Deleted)` + `EXPUNGE` | archives correctly: message gets the label, leaves INBOX, no duplicate |
| `m.select("[Gmail]/Semua Mel")` | BAD `Could not parse command` — mailbox names with spaces must be quoted: `m.select('"[Gmail]/Semua Mel"')`, same for `m.status('"1-PENTING"', "(MESSAGES)")` |
| `STATUS`/`SELECT` counts on label folders | lag for minutes, make a successful run look like a no-op. Do **not** judge success by them |
| `X-GM-RAW "from:shopee newer_than:3d"` inside the label folder | authoritative — this is how to prove filing worked |
| `FETCH (X-GM-LABELS)` | shows `(1-PENTING)` and whether `\Inbox` is gone — the cleanest per-message proof |
| `m.delete("PROMOSI")` while messages carry it | messages lose the label and sit in All Mail only → invisible to the user. Order: create new → move → verify → delete old |
| Removing one wrong label | `SELECT "<label>"` then `STORE +FLAGS (\Deleted)` + `EXPUNGE` — removes the label, message stays |

## Batch performance

100 messages one-at-a-time = ~2.5 min (one EXPUNGE each). Group first:

```python
for label, uids in gerak.items():
    m.uid("COPY", b",".join(uids), FOLDER[label])   # one COPY per label
m.uid("STORE", b",".join(semua), "+FLAGS", "(\\Deleted)")
m.expunge()                                          # one EXPUNGE total
```

## Rule design that survives real inboxes

- Evaluate `PENTING → KERJA → PROMOSI` (first match wins).
- Banks / telcos / e-wallets / brokers go in the **PROMOSI** domain list (their default
  output is marketing), and the **PENTING keywords** (`statement`, `penyataan`, `bil`,
  `otp`, `verification code`, `resit`) rescue the real notices. Putting the bank domain in
  PENTING instead sends "menangi Samsung Galaxy Tab" to PENTING.
- Skip bare `tax` — it matched a JustMarkets "Oil Tax" newsletter. Use `cukai`,
  `income tax`.
- Unmatched stays in INBOX by default. State this explicitly in the report; it is the difference
  between "auto-sorted" and "my mail disappeared". If the user then says they want an empty inbox
  ("tak masuk di peti masuk"), add an opt-in `--archive-lain` path: `m.create("0-LAIN")`, one
  `COPY` of the unmatched uids, one `STORE +FLAGS (\Deleted)`, one `EXPUNGE`. Keep it a flag, not
  the default, and report the count that landed in `0-LAIN`.
- `preview` (read-only) before `apply`, always on a bounded `--max`, and cap the crawl
  with `newer_than:2d` so the automation never tries to backfill a 17k inbox.

## Scheduling

`cronjob(action=create, schedule="*/10 * * * *", no_agent=True, script="email_auto.sh",
prompt="…")` — the script's stdout is the message. The label-only job (`email_autosort.sh`,
every 15 min) is superseded by the combined label + file job; pause it rather than running both.
The script argument must be a real file directly in `~/.hermes20/scripts/` (absolute paths and
symlinks are refused), so keep a 2-line wrapper there that `exec`s the project script.
Wrapper contract:

- exit 0 with **empty** stdout when nothing was filed → silent, no chat spam;
- one line when it filed (`📬 13 email disusun — Penting 3 · Kerja 2 · Promosi 8`);
- a `⚠️ … GAGAL` line on non-zero exit so a broken watchdog cannot fail silently;
- append every run to `_autosort.log` so history exists without messaging the user.

Honest limits to tell the user: up to 15 minutes delay, phone must be awake, and the real
instant/kill-proof fix is a server-side Gmail filter — which needs Google Cloud OAuth
(the follow-up option, not a substitute for shipping this now).
