---
name: freelance-lead-radar
description: Monitor freelance/job marketplaces and draft proposals.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, termux, windows]
metadata:
  hermes:
    tags: [freelance, jobs, marketplace, monitoring, proposals, cron, radar]
    related_skills: [youtube-content, agent-team-operations, localhost-monitoring-console]
---

# Freelance Lead Radar

Find freelance work automatically, score it against the owner's keywords and budget, and prepare
proposal drafts — **the owner sends**. Never auto-bid.

## When to use

- "Cari kerja freelance untuk aku", "monitor Upwork/Freelancer", "sediakan proposal".
- Building or extending a job monitor: new source, better filtering, draft generation, cron wiring.
- Any request to *apply* on the owner's behalf (see the hard gate below).

## Hard gate — never auto-submit

Marketplaces forbid automated bidding and will suspend accounts. The safe product is:
**scan → filter → draft → human presses Send.** State this plainly and keep the draft path obvious
(`drafts/<date>-<slug>.md`). If the owner insists on auto-fill, say the risk (ban, CAPTCHA) once,
then implement only with an explicit written yes.

## Sources (verified from a Termux phone)

| Source | Works? | Notes |
|---|---|---|
| Freelancer.com public API | **yes, no auth** | real freelance projects, budget + bid count |
| RemoteOK `/api` | yes | full-time remote jobs, not short projects |
| We Work Remotely RSS | yes | full-time remote |
| Upwork | no public API | no proposal endpoint; partner approval only |
| Fiverr | no public API | — |
| JobStreet MY (`my.jobstreet.com`) | **403 Cloudflare** | needs a real browser; don't retry in a loop |

Endpoints, JSON field names, currency normalisation and scoring rules:
`references/sumber-kerja-dan-api.md`.

## Pipeline (working shape)

```
config.yaml (keywords, blocked words, budget USD, max items, sources)
  → fetch each source (urllib + UA)
  → normalise to one schema: sumber, id, tajuk, pautan, penerangan, budget_usd,
    bidders, time, kata_kunci_asal, jenis
  → filter: blocked words → keyword hit → title-match gate → budget → age
  → score: keyword richness, title hit, budget in range, few bids, recency
  → dedupe against memory/seen.json (prune after N days)
  → reports/YYYY-MM-DD_HHMM.md  +  data/<same>.json  +  stdout summary
```

Reference implementation: `~/freelance-radar/` (`scripts/scan.py`, `config.yaml`, `PROFIL.md`,
`BACA-DULU.md`, `drafts/`). Reuse it rather than rewriting.

### Filtering rules that mattered

- **Normalise money to USD before comparing budgets.** Freelancer returns
  `currency.exchange_rate`; without it an INR 600 project passes a "USD 30 minimum" filter.
- **Require a keyword in the *title*, or ≥2 keywords in the body.** Otherwise a video-editing gig
  scores high because its description mentions "automation" once.
- **Few bids = opportunity, many bids = noise.** `bid_stats.bid_count` ≤10 adds score, >60 subtracts.
- **Age gate.** Drop anything older than a week; add score for <6 h.
- **Dedupe on the source id**, not the title (titles get edited).

## Drafting (the deliverable that makes this useful)

Each draft is ≤120 words in the marketplace's language, and contains: one sentence naming the
client's real problem → one concrete approach → one capability claim that is **true** → one closing
question. Plus a "checklist sebelum hantar" (scope, price, never pay off-platform).

**Never invent experience.** If the owner's profile is empty (`PROFIL.md` with `TODO`), write the
draft without personal claims and say so in the report. Fabricated credentials in a proposal is the
one unrecoverable failure here.

## Cron wiring

Owner-facing cadence (e.g. `0 9,21 * * *`) delivering to their chat, plus 3 drafts per run. Hermes
cron rejects absolute script paths, so keep a wrapper under `~/.hermesNN/scripts/`:

```bash
#!/data/data/com.termux/files/usr/bin/bash
cd "$HOME/freelance-radar" || exit 1
exec python3 scripts/scan.py
```

Then `hermes cron create "0 9,21 * * *" "<prompt>" --name radar-kerja --deliver origin
--script radar_kerja.sh --workdir ~/freelance-radar`. The CLI form works when the cronjob tool's
arguments are being dropped — verify with `hermes cron runs <id>` and by checking
`~/.hermesNN/cron/output/<id>/*.md`.

## Working with this owner

- **One question at a time, approval before building.** They explicitly asked to be guided step by
  step ("pandu aku satu-satu, aku setuju baru kita bina"). Ask Q1, wait, then Q2.
- **They press the final button** — always. Drafts, never submissions.
- Plain Malay, evidence in files, numbered options at the end of the reply.
- ADB-based UI automation of a marketplace app is possible once paired, but it does not remove the
  ToS/ban risk; offer it only as a *manual-assist* (screenshot + tap) path, never as auto-bid.

## Pitfalls

- **A hand-rolled YAML parser will silently return empty lists.** Inline `# comments` and `- item`
  blocks break naive parsers, and the run then "finds 0 jobs" while the sources are fine. Use
  PyYAML (`import yaml; yaml.safe_load`) and print the parsed config once to prove it loaded.
- **`/tmp` is not writable on Termux** — `curl -o /tmp/x.json` yields 0 bytes and a confusing
  `head: cannot open`. Write inside the project dir.
- **Exit 0 with 0 bytes is not a fetch success.** Check the byte count and parse the JSON; a blocked
  source (Cloudflare 403 HTML) looks like an empty result otherwise.
- **Report the filter drop counts** (`tiada_kata_kunci`, `bajet_rendah`, `padanan_lemah`). Without
  them an empty report is indistinguishable from a broken scraper.
- **Don't claim the Telegram delivery of a manual `cron run`** — run with `source=direct` writes the
  output file but is not the scheduler path; confirm on the next scheduled fire instead.
