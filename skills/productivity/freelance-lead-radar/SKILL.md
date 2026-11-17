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
- "Semak email aku untuk kerja freelance" / "susun email satu per satu, simpan ke Drive/Docs/Sheets"
  → use the inbox intake below; the inbox is a source too, not a separate project.
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

## Inbox intake — leads that arrive by email

Many freelance jobs never appear on a marketplace board: they land in the owner's Gmail. Same
discipline as the radar — **read one by one, one record per email, owner presses Send** — but the
storage is Google Drive/Docs/Sheets.

```
Gmail (IMAP, UID)  →  ~/vault/email-inbox/<YYYY-MM-DD>_<uid>_<slug>.md   (satu email = satu fail)
                   →  ~/vault/email-inbox/_index.csv                     (satu baris = satu email)
                   →  Sheets: indeks induk (tarikh, dari, subjek, kategori, tindakan, status, pautan, uid)
                   →  Docs:   satu dok per lead (butiran + draf balasan)
                   →  Drive:  folder per klien untuk lampiran (PDF/gambar)
```

- Working script already on this device: `~/.hermes20/scripts/email_fetch.py`
  (`check` / `list --days --max` / `save --days --max --tag`, stdlib `imaplib` only).
- Credentials: `GMAIL_USER` + `GMAIL_APP_PASSWORD` in `~/.hermesNN/.env`. **The account password
  cannot be used** — Google requires a 16-char App Password (2FA on), and the value must never be
  written into a repo, script, or chat.
- Where each material belongs, the Sheet columns, and the credential trap:
  `references/email-inbox-intake.md`.
- Do not promise Drive/Docs/Sheets writes before OAuth exists — probe first
  (`setup.py --check` prints `NOT_AUTHENTICATED`), then ask for one login step.

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

Companion probe: `scripts/project_detail.py <id>…` (in this skill) prints the full description,
budget, bid stats and skill tags for chosen project ids — run it between scan and drafting.

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

### Drafting from a scan run — proven sequence

The scan stores `penerangan` truncated to ~100 chars, so a draft written from the report alone has to
guess the scope. Each run, in this order:

1. Read `PROFIL.md` **and** the report `reports/<stamp>.md` (or `data/<stamp>.json`).
2. **Dedupe by source id before ranking.** A project matched by several query keywords is appended
   once per keyword (`fl-40815260` appeared ×3 in one run), so a raw "top 3" can be three copies of
   one gig. Rank the unique ids, then say in the report that duplicates were removed.
3. **Skip ids that already have a draft** — `ls drafts/ | grep <lead-slug>`. Re-drafting yesterday's
   gig creates duplicate files and wastes the run; name the existing draft file in the report instead.
4. Pull full text for the 3 chosen ids: `python3 scripts/project_detail.py <id> [<id>…]`
   (endpoint `/api/projects/0.1/projects/<id>/?full_description=true&job_details=true`, no auth).
   It also returns the requested skill tags and `bid_avg` — a `bid_avg` far below `budget.maximum`
   means the market is bidding low, not that the gig pays well.
5. Write `drafts/<YYYY-MM-DD>-<slug>.md`; keep the proposal ≤120 words and state the word count.
   Aim it at the client's *stated* pain, not the job title.
6. Report in Malay: numbered list of ≤5 unique leads (tajuk | bajet | sumber | skor), full text of
   draft #1, filenames of the rest, honesty flags (empty profile, commission-only, budget below the
   work), then a numbered 3–4 option list.

Draft file shape: `**Tajuk**`, `**Pautan**`, `**Bajet**` (+ bid count and age), then
`## Draf proposal (English, N patah perkataan)`, then `## Checklist sebelum hantar` with tick boxes
for scope, price, off-platform payment, and "hantar melalui butang platform sahaja".

Write red flags into the checklist instead of silently accepting them: commission-only gigs (no fixed
pay — demand the rate and the payment trigger in writing), and budgets that cannot cover the requested
duty cycle (USD 10–30 for a 24/7 VPS scraper → propose a phased scope).

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
- **Duplicate rows in the report are a scan bug, not extra leads.** The same project id repeats once
  per query keyword that matched it, and `dedupe against memory/seen.json` does not catch repeats
  *within* one run. Dedupe the list by `id` before ranking or reporting; fix `scan.py` if the report
  is what the owner reads.
- **Truncated `penerangan` produces generic drafts.** ~100 chars is enough to pick a lead, never
  enough to write to. Fetch the detail endpoint (`scripts/project_detail.py`) before drafting.
- **`execute_code` is blocked under cron** (`approvals.cron_mode`) — a cron run cannot use it for
  quick JSON shaping. Use `read_file` on `data/<stamp>.json`, or a `python3 - <<'EOF'` heredoc via
  `terminal`, which smart-approval allows.
- **Don't claim the Telegram delivery of a manual `cron run`** — run with `source=direct` writes the
  output file but is not the scheduler path; confirm on the next scheduled fire instead.
