# Renaming the lead or a profile — three places, one decision

Trigger: owner says "tukar nama kau jadi X" / "tukar nama profil jadi Y". It sounds like one edit and
is actually three independent surfaces. Renaming one leaves a split identity the owner will notice
within a day (persona says one name, chat header says another, folder says a third).

## The three surfaces

| # | Surface | Where it actually lives | What the owner sees if you skip it |
|---|---|---|---|
| 1 | Persona / self-name | `SOUL.md` in the home (`~/.hermesNN/SOUL.md`), plus `profiles/<p>/SOUL.md` if that profile has its own | Answers still introduce themselves with the old name |
| 2 | Chat display name | `.env` → `TELEGRAM_HOME_CHANNEL_NAME` is only the **home-channel label**, not the bot's name. The bot's own name is set through the Bot API (`setMyName`) or BotFather | Telegram header still shows the old name while the persona uses the new one |
| 3 | Profile directory | `~/.hermesNN/profiles/<name>/` and every config/cron/report that hard-codes that path | `hermes --profile <old>` fails, cron jobs point at a dead path |

**Do not promise #2 from a config edit alone.** Confirm how this install sets it before telling the
owner it is done: grep the runtime source for `setMyName` / `set_my_name` / `bot_name`, and check the
`display` block in `config.yaml`. If it is BotFather-only, say so plainly and hand the owner the exact
steps — that is the one part they must press themselves.

## Name-as-self vs job-title-as-noun

`grep -c 'Ketua' SOUL.md` over-counts: the same word is the persona's name *and* the job title in
prose ("Ketua tidak melaksanakan", "Ketua hanya memegang gate"). Replacing every hit produces
nonsense like "Fatin hanya memegang gate" where the doctrine meant the office, not the person.

Before proposing an edit, split the hits:

```bash
grep -n 'Ketua' ~/.hermesNN/SOUL.md
```

- Hits in the identity block (`Aku **Ketua** — pengarah`), the header, and self-introductions → rename.
- Hits describing the office in doctrine sentences → keep, or rewrite to "aku" if the sentence is
  first-person anyway.

Present the split to the owner as a count ("7 sebagai nama diri, 12 sebagai jawatan — aku cadang tukar
7 sahaja") and let them approve the number, not just the name.

## Profile directory rename

```bash
du -sh ~/.hermesNN/profiles/<old>                      # size before touching anything
grep -rl '<old>' ~/.hermesNN --include=*.yaml --include=*.json --include=*.md --include=*.env 2>/dev/null | head -40
mv ~/.hermesNN/profiles/<old> ~/.hermesNN/profiles/<new>
```

The profile's `state.db`, `sessions/`, `skills/`, `cron/`, `memories/` move with the folder — no data
is lost. What breaks is anything **outside** the folder that spells the old name: gateway state,
cron job definitions, console home registries (`homes.json`), reports. The `grep -rl` above is the
actual risk list; do not rename until you have read it, and update each hit in the same wave.

Rollback: `mv` back. Keep the old name in the report as the one-line undo.

## Show-files-first review pack (when the owner asks to see before approving)

One child, read-only, output in `~/semakan-<topik>-<date>/`:

```
00-BACA-DULU.md            # plain Malay; recipient matrix; what changes / what does not;
                           # 3 numbered self-check steps; loud "belum ada apa-apa diubah"
01-SOUL.md                 # full copy behind a 3-line SALINAN header (date + original path)
02-OPERASI.md              # same
03-KETUA.md                # same
04-PROFILES.md             # ls -la, du -sh, grep -rl for the old name (the risk list)
05-RENCANA-TUKAR-NAMA.md   # per change: path, line number, BEFORE, AFTER, risk, rollback
```

Prohibitions in the brief: no writes to `SOUL.md`/`OPERASI.md`/`docs/`/`.env`/`config.yaml`/`profiles/`,
no `hermes config set`, no calls to the Telegram API. Copies only.

Lead verification — the copies must be genuine:

```bash
tail -n +4 ~/semakan-*/01-SOUL.md | diff - ~/.hermesNN/SOUL.md   # must print nothing
ls -l --time-style=+%Y-%m-%d\ %H:%M ~/.hermesNN/SOUL.md ~/.hermesNN/.env   # mtime unchanged
```

## Pitfall that cost a false failure report

After a child "removes a stale sentence", `grep -rn` still matches the append-only `log.md`, where the
old sentence is quoted as history. That is not a defect — deleting it would falsify the record. Scope
the check (`--exclude=log.md`) and write the exception into the verdict instead of failing the agent.
