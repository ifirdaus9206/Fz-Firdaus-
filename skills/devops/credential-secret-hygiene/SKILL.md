---
name: credential-secret-hygiene
description: Secret in chat, logs or DB — store once, scrub, verify.
---

# Credential & secret hygiene on a shared home directory

Class of task: "a real credential (app password, API token, account password) has just been
typed into a chat, pasted into a config, or found on disk — where is it allowed to live, how do
I remove every other copy, and how do I prove it?" Also the standing rules for handling one in
the first place. Applies to Hermes homes (`~/.hermes20`), dotfile repos, and any agent workspace
that mirrors into git/GitHub.

## Non-negotiable rules

1. **One home only: `<home>/.env`**, mode `600`, gitignored, never tracked:
   ```bash
   ls -l ~/.hermes20/.env          # -rw------- (must be 600)
   git -C ~/.hermes20 check-ignore -v .env
   git -C ~/.hermes20 ls-files --error-unmatch .env   # must fail
   ```
2. **Never echo the secret back** in a reply, report table, or code block — not even masked
   partially with real characters. Masked echoes are how it ends up in `logs/agent.log` and the
   session DB again.
3. **Never invent a reason the user must rotate.** Say what the credential can do, then let them
   choose. Distinguish account password from derived key (see table below).
4. **Don't fake UI affordances.** If the user asks "why is there no 'typing…' marker now?", the
   honest answer is that it is a platform action sent by the gateway (`sendChatAction`), it can
   go silent during cooldown, and you will not type a fake "(sedang menulis…)" line to imitate
   it. Never simulate liveness you do not have.

## Account password vs derived credential — get this right before advising

| Kind | Example | Can the agent see it? | Advice |
|---|---|---|---|
| Account password | Google/GitHub login password | No, and it is never needed | **Do not ask for it, do not store it.** No change required just because a key leaked |
| App password / app-specific key | Google 16-char App Password, Gmail IMAP password | Yes (user pastes it) | Store in `.env`; revocable independently at the provider; revoke != change account password |
| API token / PAT | `ghp_...`, provider keys | Yes | `.env` only, prefer SSH keys where possible |

Users conflate these ("kena tukar password Google tak?"). Answer with the two rows explicitly:
account password stays theirs; the derived key can be revoked in one tap at the provider.

Mail/IMAP note: Gmail **rejects the account password** for IMAP regardless of what the user
prefers — an App Password (16 chars, requires 2-Step Verification) is mandatory. That is a
provider rule, not a preference; say so instead of trying the account password.

## Where the copies actually are (measured on a Hermes home)

A pasted secret lands in more places than the `.env`. Scan these, in this order:

```bash
cd ~ && for d in .hermes20/logs .hermes20/sessions .hermes20/cache .hermes20/pastes \
                .hermes20/memories vault tmp; do
  [ -e "$d" ] && rg -l -uu --no-ignore --text -F -e '<literal>' -e '<literal with spaces>' "$d" 2>/dev/null
done
```

- `logs/gateway.log`, `logs/agent.log` — inbound message text is logged (often **truncated**, so a
  full-literal regex misses it; see regex below).
- `state.db` **plus `state.db-wal`** — every chat message, tool call and reasoning block.
  Also the FTS shadow tables (`messages_fts`, `messages_fts_trigram`) copy the same text.
- `tmp/` — throwaway helper scripts written to set the value (`set_env.py` and friends).
- `~/vault`, `memories/`, `knowledge_base/` — user-facing notes that quote it.
- git history — see `safe-git-config-backup` (`references/purge-pushed-secret.md`).

Widen scope carefully: `grep -r` across `~/.hermes_venvs` or `archive/` takes minutes and times
out; pin the directories above and use `rg -uu --no-ignore --text` (the `--text` flag is what
makes it look inside SQLite files).

## Scrub procedure

`scripts/scrub_secret.py` does the whole pass (logs -> tmp -> SQLite incl. FTS + WAL checkpoint +
VACUUM -> re-verify). Run it instead of hand-writing SQL each time:

```bash
python ~/.hermes20/skills/devops/credential-secret-hygiene/scripts/scrub_secret.py --literal '<value>'
```

What it encodes, and why:

1. **Regex with slack, not the exact string.** Loggers truncate message bodies
   (`... untuk peranti anda (  dpuw aamp zoux'` — the line ends mid-secret), so a pattern
   requiring all four groups matches **nothing** while `<first-group>[\s\S]{0,20}`
   (case-insensitive) catches both the truncated and the spaced form. Redact generously: the goal
   is that no prefix of the secret survives.
2. **Logs**: rewrite in place, count substitutions, report the count.
3. **Temp scripts**: delete the file, not just its contents.
4. **SQLite**: iterate `sqlite_master` tables x `pragma table_info` columns, `UPDATE ... SET col=?
   WHERE col LIKE '%<prefix>%'`, then `PRAGMA wal_checkpoint(TRUNCATE)` and `VACUUM`. Without the
   checkpoint/VACUUM the old pages stay in `state.db-wal` and a re-scan still "finds" the secret.
   FTS shadow tables need the same UPDATE pass; if an FTS table refuses, `INSERT INTO
   messages_fts(messages_fts) VALUES('rebuild')` after cleaning the source table.
5. **Re-verify** and read the hits before declaring victory — see the trap below.

### Trap: your own search patterns become the remaining "leak"

After scrubbing, the scan still matched — because the *commands you ran* (containing the prefix as
a search pattern) were themselves stored in `messages.tool_calls` and mirrored into the FTS
tables. Before reporting a failure, print the surrounding fragment of each remaining hit; if it is
a grep command, a Python snippet, or reasoning text quoting the pattern, the secret itself is
gone. Say "baki padanan ialah corak carian saya sendiri, bukan rahsia" instead of reporting a
stubborn leak.

## Chat bubble deletion — what is and isn't possible

The user's pasted message stays in the Telegram conversation. A bot generally **cannot** be
relied on to delete the *user's* incoming message (needs the platform message id, which
`platform_message_id` often leaves NULL in `messages`), so:

- Ask the user to long-press -> **Padam**, framed as one clear step.
- Do not claim you deleted it if you only scrubbed local stores.
- Do not attempt `getUpdates` to find the id while the gateway holds the long-poll — you will
  get a 409 conflict and steal the running session's updates.

## Report shape (this user)

Board first — `| Tempat | Tindakan | Bukti |` with substitution counts and the re-scan result —
then one "ini yang aku tak boleh buat" line for the human step, then numbered options
(1 continue work / 2 revoke the key at the provider / 3 rotate account password / 4 nothing).
Bahasa Melayu, no jargon, no partial echoes of the value.

## Related

- `safe-git-config-backup` — the git/GitHub half: redact tracked files, `git filter-repo
  --replace-text`, force push, dangling-SHA residual exposure.
- `git-host-ssh-provisioning` — credential *setup* on a phone; keep prose lessons free of values.
