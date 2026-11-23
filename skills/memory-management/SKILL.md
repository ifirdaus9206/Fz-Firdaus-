---
name: memory-management
description: Two-layer agent memory — daily short-term log distilled into durable long-term facts.
---

# Two-layer agent memory (short-term → long-term)

Class of task: "make the agent learn more every day" without letting memory bloat the prompt.
Built and measured on a Termux/Hermes home (`~/.hermes20` + `~/vault`), 2026-11.

The shape that works is **files on disk, two layers, one nightly distillation** — not a vector
DB, and not "just write more into MEMORY.md". `MEMORY.md` is injected on *every* turn, so it has
a hard character budget (the store rejects an add at ~2.2k chars). Durable learning therefore
needs a place that is *not* injected, plus a compaction step that promotes only what survives.

## Layout

```
~/vault/memori/
  01-pendek/YYYY-MM-DD.md    # append-only, one line per event  → NOT injected
  02-panjang/MEMORI-PANJANG.md  # durable facts, deduped, capped (~4k chars)
  03-pelajaran/YYYY-MM.md    # 3–5 lessons per month (the "what I got wrong" file)
```

Why three: daily lines are cheap to write and safe to lose; the long-term file is what a future
session actually reads; the lessons file is the only layer that changes *behaviour*.

## Write path — short-term (every event, no LLM)

`scripts/memori_pendek.sh "teks fakta" [tag]` appends `- HH:MM | [tag] teks` to today's file,
creating it with a `# Memori Pendek YYYY-MM-DD` header if missing. Append-only means a crash can
never corrupt earlier days. Call it from the agent after any decision worth remembering
("X dipadam", "port 8790 dibersarakan", "bos benci blok hitam").

## Read path — long-term digest (script + agent)

`scripts/memori_panjang.py [hari]` (default 7) prints three sections in one blob: current
long-term file, the short-term archive for the window, and the target paths. The cron job then
rewrites the long-term file from that blob.

Split it this way because the *script* must stay deterministic (no model, no cost, testable) and
the *agent* only does the summarising. A single script that calls an API is neither.

Nightly cron (23:30, `deliver: local` — silent, never messages the owner):

> Jalankan `python3 ~/.hermes20/scripts/memori_panjang.py 7`. Baca output. Kemudian tulis semula
> `02-panjang/MEMORI-PANJANG.md`: gabungkan fakta penting, buang duplikasi, kekalkan di bawah
> 4000 aksara, susun ikut kategori (sistem, bos, projek, pelajaran). Tulis juga
> `03-pelajaran/YYYY-MM.md` dengan 3–5 pelajaran bulan ini. Jangan hantar mesej; kerja senyap.

## Pitfalls (all measured)

- **An empty `02-panjang/` is normal on day one — seed it by hand.** The digest only runs at
  23:30, so a fresh install reports "belum ada" for a whole day. Write the first long-term file
  yourself from what is already known, otherwise the first distillation has nothing to merge into
  and tends to restate the daily log verbatim.
- **The digest must rewrite, not append.** Appending grows without bound and duplicates every
  fact once per run. Require an explicit char budget in the prompt ("di bawah 4000 aksara") and
  say "buang duplikasi" — otherwise the model copies lines across.
- **Keep it out of the injected prompt.** Anything in `MEMORY.md` costs tokens on every turn.
  Long-term memory belongs in a file the agent reads on demand; only the 3–5 highest-value
  one-liners get promoted into `MEMORY.md`/`USER.md` by the foreground agent.
- **Never put secrets in either layer.** These files are inside the home that gets backed up to
  git. A password in a "lesson" line is a leak — see `safe-git-config-backup` tier 0.
- **Cron must be silent on success.** A nightly job that messages the owner every night gets
  muted within a week; set `deliver: local` and let the report cron (21:00) carry the news.
- **Don't schedule the digest before you have a digest script.** Creating the job first means the
  first tick runs an empty prompt; build script → test with a manual run → then schedule.

## Verifying it works

```bash
~/.hermes20/scripts/memori_pendek.sh "ujian memori" sistem
cat ~/vault/memori/01-pendek/$(date +%Y-%m-%d).md      # one new line, header intact
python3 ~/.hermes20/scripts/memori_panjang.py 7 | head # shows long-term + archive + paths
hermes cron list | grep -A3 memori                     # job listed, next run tomorrow
```

Prove the *distillation* separately by running the cron job once
(`cronjob action=run job_id=…`) and then checking that `02-panjang` shrank or stayed under
budget — not merely that a file exists.
