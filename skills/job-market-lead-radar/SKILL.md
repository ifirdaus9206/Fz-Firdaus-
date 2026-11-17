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
- **A scheduled cron prompt that starts with "Kau ejen Radar Kerja"** and pastes a pre-run job list.
  That prompt is a thin wrapper (read `PROFIL.md` → draft top 3 → report); *this* skill holds the
  draft file shape, the 120-word cap and the report shape. Load it before writing anything — the
  wrapper does not restate them, and running from the wrapper alone loses the dedupe and word-count
  checks.

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
   **In a cron run the wrapper's own step list wins** (title → ≤5 jobs → full draft #1 → other draft
   filenames → stop): there is nobody to answer numbered options, so end on the blockers instead.
10. **The pre-run job list can contain the same job twice.** On 2026-11-10 the prompt listed
   `WhatsApp-Shopify Automation Setup` as both #7 and #8 with an identical URL — the scanner dedupes
   on source id, but one project matching two keywords (`automation`, `api integration`) can still
   surface twice in a single report. Dedupe on **pautan/URL** before picking the top N, then say it in
   the report (`#7 dan #8 ialah iklan yang sama — dikira sekali sahaja`). Otherwise you write two
   drafts for one job and the job count in your header is wrong. On 2026-11-12 it recurred (#2/#3 and
   #4/#5, same URLs) — always URL-dedupe first, then count, then draft. On 2026-11-16 the twins
   differed *only* in `kata_kunci_asal` (`python` vs `automation`) while `id` (`fl-40816064`) and URL
   were identical: the authoritative key is `id` in `data/<stamp>.json`, so key on that (URL second)
   and say it in the header (`#1 dan #2 ialah iklan yang sama (fl-40816064) — didedup`).
11. **Fetching the project page can hand you a competitor's bid, not the brief.** The report truncates
   `penerangan` at ~100 chars, so for the top 3 it is worth reading the full ad — but selectors like
   `class="project-description"` / `id="project-description"` / `"description":"..."` return *bid text*
   (2026-11-12: "Hi, I run A2Z Research Consultant, a small team of certified penetration testers...").
   Any block starting `Hi,` / `Dear` or ending `Best regards` is a rival's proposal — drop it. Safe
   extraction (meta description + client-voice anchor), the tested script, and the gating requirements
   it surfaced: `references/fetch-deskripsi-kerja.md`.
12. **Gated requirements decide whether to bid at all — put them in the checklist.** Ads hide hard
   gates in the body: "5 WhatsApp numbers you control", "verifiable CEH/OSCP/CREST required". Put a
   bracketed placeholder in the pitch (`**[X] Malaysian WhatsApp numbers**`, `**[CERT + VERIFICATION
   LINK]**`) plus a hard checklist line: fill the real number, or **do not bid** if you lack the
   credential. A placeholder must never read as a claim.

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

Checklist items that are easy to forget and change the price — or kill the bid — a lot:
- **Posting in another language** (French, Spanish, Romanian): ask whether the *deliverable* must be
  in that language. It is a scope item — more prompt work and QA — not a detail.
- **Document conversion**: ask whether the source is digital text or scans needing OCR (3–5x the
  time). Same for scraping: ask records × mandatory fields.
- **A gated requirement** (own 5 phone numbers, hold a verifiable CEH/OSCP/CREST, on-site in a given
  city): this is a go/no-go, not a price item. Bracket the placeholder in the body and write
  `JANGAN hantar` in the checklist when the owner cannot meet it.

Price anchors per job class (per page / per record / build vs monthly, and what an 8x budget range
signals): `references/semak-skop-dan-harga.md`. Write the *question*, never "terlalu murah, tolak".

**Verify the word count with a command, never by eye.** First drafts routinely land at 120–125
because the greeting and signature count too:

```bash
python3 ~/.hermes20/skills/job-market-lead-radar/scripts/semak_draf.py drafts/*.md
```

It prints `file | N words | ok/OVER` and exits non-zero if any draft exceeds the cap. Trim the
closing line, not the problem statement — the problem sentence is what earns the reply.

If the script is not to hand (or you want a check with no Python), the same count in shell — it
slices out the `## Draf proposal` block, drops the signature placeholder, and counts:

```bash
cd drafts && for f in <YYYY-MM-DD>-*.md; do
  n=$(awk '/^## Draf proposal/{p=1;next}/^## Checklist/{p=0}p' "$f" | sed 's/\[NAMA ANDA\]//' | wc -w)
  echo "$f = $n words"; done
```

`Hi,` and the blank greeting still count, so aim for ≤115 to leave headroom. On 2026-11-10 the
chatbot draft measured 128 and was fixed by deleting one trailing sentence (13 words) — never by
cutting the problem statement. On 2026-11-16 a draft landed at 122 and was trimmed to 118 by two
small edits (`output quality swings` → `quality swings`, `Google Docs, Word, or straight into your
CMS?` → `Docs, Word, or your CMS?`); the header's `NNN patah perkataan` must be updated to the
measured number in the same patch, or the file contradicts itself.

**The question must be the LAST line — verify, don't assume.** Writing "With that I can split the
work into phases" *after* the question leaves the pitch ending on a statement, which kills the reply.
Check it with the same run that counts words:

```bash
python3 - <<'EOF'
import re, glob
for f in sorted(glob.glob('drafts/<YYYY-MM-DD>-*.md')):
    body = re.search(r'## Draf proposal.*?\n(.*?)\n## ', open(f).read(), re.S).group(1).strip()
    print(f, len(body.split()), 'words | akhir:', body.split('\n')[-1][-70:])
EOF
```

Read the `akhir:` column: it must end in `?`. Fix by moving the stray sentence *before* the question,
not by deleting the question.

**Do not silently overwrite an existing draft.** A job re-appears on later runs (it stays in the
report even when `baharu: false`), and the earlier draft may already carry the owner's hand edits
(name, real experience, price). If `drafts/<date>-<slug>.md` exists, either skip it and say
"sudah ada draf" in the report, or write `<slug>-v2.md` and state the old file was kept.

**When the wrapper says "top 3" and a top job is already drafted, skip it and take the next unique
undrafted lead** — then say which one was skipped and why (`#1 sudah ada draf 2026-11-15 — diganti
dengan #5`). Do not re-draft yesterday's gig under today's date just to satisfy the count: it burns
the run, creates near-duplicate files, and the owner may already have edited the old one. Only
re-draft it as `<slug>-v2.md` when the ad itself changed (budget, scope, deadline) — state that.

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
