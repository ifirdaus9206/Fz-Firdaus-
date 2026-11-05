# Sources, endpoints and JSON shapes (measured 2026-11)

All probed from a Termux phone with `curl`/urllib and a browser UA.

## Freelancer.com — public API, no auth

```
GET https://www.freelancer.com/api/projects/0.1/projects/active/
    ?query=<keyword>&limit=20&full_description=true&sort=time_updated&language=en
```

Status 200, ~10 KB for `limit=3` (≈2–4 KB per project). Response:

```json
{"status":"success","result":{
  "projects":[{ "id":40803504, "title":"…", "seo_url":"c-programming/Enterprise-…",
    "preview_description":"…", "description":null, "submitdate":1793842175,
    "time_submitted":1793842175, "time_updated":1793842175,
    "type":"fixed|hourly",
    "currency":{"code":"USD","sign":"$","exchange_rate":1.0},
    "budget":{"minimum":750.0,"maximum":1500.0},
    "bid_stats":{"bid_count":105,"bid_avg":1195.66},
    "jobs":null }],
  "users":{…}, "selected_bids":{…}, "total_count":N }}
```

Project URL = `https://www.freelancer.com/projects/<seo_url>`.
`description` can be `null` — fall back to `preview_description`.
**Always convert the budget:** `bmax_usd = budget.maximum * currency.exchange_rate`.

One request per keyword is enough; dedupe afterwards by `id` because the same project matches
several keywords.

## RemoteOK

```
GET https://remoteok.com/api        (UA required; ~650 KB)
```
JSON array; element 0 is a legal notice (no `position` key) — skip items without `position`.
Fields used: `id`, `slug`, `position`, `company`, `tags[]`, `url`, `epoch`, `salary_min/max`,
`description` (HTML → strip tags). These are **full-time remote jobs**, so label them
`jenis: sepenuh_masa` and never present them as short freelance projects.

## We Work Remotely (RSS)

```
GET https://weworkremotely.com/categories/remote-programming-jobs.rss
```
~185 KB XML; parse with `xml.etree.ElementTree`, `item` children: `title`, `link`,
`description` (HTML), `pubDate` (`%a, %d %b %Y %H:%M:%S %z`).

## Blocked / unavailable

| Attempt | Result |
|---|---|
| `https://my.jobstreet.com/jobs?keywords=flutter` | **403** + `Just a moment...` (Cloudflare) |
| Upwork API | partner approval; no proposal-submission endpoint |
| Fiverr | no public API |

Do not loop on a Cloudflare block: one probe, record it, move on.

## Scoring reference (worked, produced sensible results)

```
score  = 6 * min(len(keyword_hits_in_text), 3)
       + 8   if any keyword hit is in the title
       + 6   if budget_usd within [min, max]
       + 6   if bid_count <= 10      (  -6 if > 60 )
       + 6   if age <= 6h            (  +3 if <= 24h )
gate:   title hit OR >= 2 keyword hits in body, else "padanan_lemah"
        budget_usd < min → "bajet_rendah"
        age > 7 days → "terlalu_lama"
```

Measured on one run: 124 raw items → 8 kept, and the two irrelevant items that had slipped through
before the title gate (a video editor and a B2B sales closer) dropped out.

## Dedupe store

`memory/seen.json` = `{project_id: first_seen_epoch}`; prune entries older than `simpan_hari`
(default 14). Never delete the file to "refresh" — that replays already-seen jobs as new.
