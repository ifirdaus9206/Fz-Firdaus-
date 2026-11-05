---
name: job-market-lead-radar
description: Watch freelance/job boards for leads; draft pitches.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [freelance, job-boards, lead-generation, cron, proposals, freelancer, upwork]
    related_skills: [blogwatcher, hermes-cron-scheduling]
---

# Job Market / Freelance Lead Radar

Build a recurring radar that finds work (freelance projects or remote jobs), filters it against the
user's keywords and budget, and prepares proposal drafts the user sends manually.

## Use when

- "cari kerja", "monitor Upwork/Fiverr/Freelancer", "radar kerja", "auto apply", "cari projek".
- The user asks whether the agent can watch a job board, or "ambik kerja" for them.

## Rule 0 — never auto-submit, and say why in one line

Upwork and Fiverr prohibit automated bidding in their ToS; accounts get suspended. Offer three modes:

| Mod | Apa ia buat | Risiko |
|---|---|---|
| A — pemantau | scan + ringkasan sahaja | tiada (tak sentuh akaun) |
| B — draf siap | + draf proposal, user tekan Hantar | rendah (disyorkan) |
| C — auto-hantar | isi borang + tekan hantar (ADB/browser) | tinggi: ban, CAPTCHA |

Default to **B**. Build C only after explicit written acceptance of the risk. Never log in on the
user's behalf to a marketplace and never edit their profile.

## Source reality (verified 2026-11-05 — probe before trusting)

| Source | Status | Endpoint |
|---|---|---|
| Freelancer.com | ok, no auth | `GET /api/projects/0.1/projects/active/?query=<kw>&limit=20&full_description=true&sort=time_updated` |
| RemoteOK | ok | `GET https://remoteok.com/api` (JSON array; item[0] is a licence notice) |
| We Work Remotely | ok | `https://weworkremotely.com/categories/remote-programming-jobs.rss` |
| JobStreet MY | HTTP 403 Cloudflare | needs a real browser |
| Upwork | no public bidding API | monitor via the user's own session |
| Fiverr | no API | same |

`curl -s -o /dev/null -w "%{http_code}"` each source before building, and put the codes in the
report. Field maps, scoring rules and probe commands: `references/sumber-api-kerja.md`.

## Architecture that works

```
<project>/
  config.yaml      # kata_kunci, tolak_kata, bajet_min/max, maks_kerja, skor_min, sumber{}
  PROFIL.md        # user's pitch material — ASK, never invent
  scripts/scan.py  # fetch → normalise → filter/score → dedupe → reports/*.md + data/*.json
  memory/seen.json # id → first-seen epoch (dedupe)
  reports/         # YYYY-MM-DD_HHMM.md human report
  drafts/          # per-job proposal drafts (written by the cron agent)
  BACA-DULU.md     # plain-language guide + source status + cron ids
  LAPORAN-BINA.md  # build log: what was tested, with numbers
```

A tested engine lives at `~/freelance-radar/scripts/scan.py` — copy and re-point it rather than
rewriting fetch/score logic.

## Pitfalls (each cost a rebuild cycle)

1. **Multi-currency budgets silently pass a USD filter.** Freelancer returns `currency.code` +
   `currency.exchange_rate`; `INR 601–1000` is ~USD 7, not USD 600. Normalise to `bajet_usd`
   first. Symptom: cheap jobs from the wrong market dominate the report.
2. **Description-only keyword hits produce garbage.** "Video Editor" and "B2B Sales Closer" matched
   because "automation" appeared in the body. Require a title hit, or >=2 keyword hits in total.
3. **Hand-rolled YAML parsers break on inline comments and bullets.** `freelancer: true  # note`
   becomes the string `"true  # note"` and `  - python` gets dropped, so the scan returns zero rows
   with no error. Use `yaml.safe_load` (PyYAML ships on Termux) merged over defaults.
4. **Dedupe must be id-based and persisted.** Without `memory/seen.json` every run re-sends the same
   jobs and the user stops reading. Prune by age, never truncate.
5. **Mixed sources need a type label.** RemoteOK/WWR are full-time jobs, not short projects, yet
   score as high. Print the type on every line.
6. **Print the rejection drip.** End the report with `Ditapis keluar: bajet_rendah=12,
   padanan_lemah=40`. It is the only way to debug "kenapa kosong" without re-running.
7. **Do not fabricate pitch material.** If `PROFIL.md` still has `TODO`, drafts must contain no
   invented experience — say so in the delivery message and ask for the 5 fields.
8. **A cron run cannot call `execute_code`** — arbitrary Python is gated by approvals and no user is
   present to approve it. Do not retry it. Read `data/<stamp>.json` with `read_file` (tajuk, pautan,
   bajet, bidaan, skor are all there; descriptions are truncated at ~100 chars, which is enough for
   a draft hook), or run a `python3 -c` one-liner through `terminal`.
9. **Report shape is part of the deliverable.** Malay, then: title with date → numbered list of at
   most 5 jobs (`tajuk | bajet | sumber | skor`) → the full draft for #1 → the filenames of the other
   drafts → a one-line blocker (e.g. `PROFIL.md` still `TODO`) → numbered 3–4 next-step options.
   Do not paste all three drafts into chat; the user reads them from the files.

## Draf proposal — the mechanics that keep it honest

Per job, one file `drafts/<YYYY-MM-DD>-<slug>.md` with exactly these blocks (skeleton:
`templates/draf-proposal.md`):

1. `**Tajuk:**` · `**Pautan:**` · `**Bajet:**` (as posted **and** the USD conversion) · `**Sumber:**`
   with bid count and age · `**Skor radar:**`
2. `## Draf proposal (English, NNN patah perkataan)` — body only, ≤120 words
3. Body shape: client's real problem → concrete approach (what they receive) → one true capability
   claim → one question at the end. No self-praise, no price promise before scope is known.
4. `## Checklist sebelum hantar` — scope questions, price sanity (real hours vs posted budget),
   fill `[NAMA ANDA]`, and the fixed line: no login, no payment, nothing sent off-platform.
5. Nothing else. Doubt goes in the checklist, never into the pitch body.

**Verify the word count with a command, never by eye.** First drafts routinely land at 120–125
because the greeting and signature count too:

```bash
python3 ~/.hermes20/skills/job-market-lead-radar/scripts/semak_draf.py drafts/*.md
```

It prints `file | N words | ok/OVER` and exits non-zero if any draft exceeds the cap. Trim the
closing line, not the problem statement — the problem sentence is what earns the reply.

**Do not silently overwrite an existing draft.** A job re-appears on later runs (it stays in the
report even when `baharu: false`), and the earlier draft may already carry the owner's hand edits
(name, real experience, price). If `drafts/<date>-<slug>.md` exists, either skip it and say
"sudah ada draf" in the report, or write `<slug>-v2.md` and state the old file was kept.

## Deliverable rules for this user

- Malay, plain, evidence-first: HTTP codes, counts, sample titles, timings, absolute file paths.
- One folder, with `BACA-DULU.md` (what each file is, what to edit) and `LAPORAN-BINA.md`
  (what was actually tested). Both in Malay.
- End every hand-off with a numbered 3–4 option list; the user answers by number.
- State unverifiable steps as unverifiable (e.g. a manual cron run's Telegram delivery) — never
  report them as success.

## Verification before reporting done

```bash
python3 scripts/scan.py | head -12    # real titles, not "0 kerja lulus tapisan"
tail -3 reports/<latest>.md           # source log + rejection counters present
ls -lt drafts/ | head                 # drafts actually written
```

Three real runs minimum: the first may legitimately return 0 (parser/filters wrong) — fix, re-run,
and only then report. Record run count and what changed into `LAPORAN-BINA.md`.
