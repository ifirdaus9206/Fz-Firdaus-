# Phone-first entity dashboard + fleet-wide verification

Session evidence: 2026-11-04, `~/hermes-console` — 282-agent roster, new `EJEN` tab,
`/api/agency/health`, 282-entity API sweep. Numbers below are measured on the phone
(Termux), not estimated.

## 1. When this shape applies

The user asks for "papan ejen / dashboard untuk monitor tugasan, data, prestasi" over a
**large roster** (hundreds of entities) and reads it **on a phone**. Two deliverables:

1. one entity page that answers *who is this, what has it done, what does it know, is it healthy*;
2. a fleet-level proof that **every** entity's API works — not a sample.

## 2. Data-model trap: roster JSON ≠ API payload

The roster file and the endpoint that normalises it use different keys. Reading the wrong
one silently produced a report claiming `tier A/B/C = 0/0/0` and `api_gagal: 1` while all
282 endpoints were returning `200`.

| Roster JSON (`data/ketua_roster.json`) | API payload (`/api/agent/<slug>/dashboard`) |
|---|---|
| `name` | `nama` |
| `kualiti.tier`, `kualiti.skor`, `kualiti.pangkat` | `tier`, `skor`, `pangkat` |
| `badan_kata` | `persona.kata` |
| `archetype_bukti` | `archetype_bukti` (same) |

Rule: before writing a verifier, print `list(agent.keys())` from the roster and the top-level
keys of one API response. Then compute every headline number from **one** source and say which.

Second rule: a verifier must split failures into two counters.

```python
http_gagal = [h for h in hasil if h["status"] != 200]      # broken endpoint
isu_data   = [h for h in hasil if h["masalah"] and h["status"] == 200]  # short body, empty vibe…
return 1 if http_gagal else 0     # data-quality issues are reported, not fatal
```

Otherwise "1 gagal" reads as a broken API and sends you debugging a healthy server.

## 3. Backend: three cache layers, 18× faster

Per-entity dashboard endpoints are slow when they re-read the world on every request. The
first version took **~2,170 ms median**; after caching **~120 ms warm**, and a cold 282-entity
sweep measured **median 424 ms / p95 1,211 ms / max 3,249 ms, 19.0 s total**.

```python
# (a) catalogue load cached by mtime — 1.5 MB JSON, unchanged for days
_ROSTER = {"mt": None, "data": None}
def load_roster():
    mt = CATALOG.stat().st_mtime
    if _ROSTER["data"] is not None and _ROSTER["mt"] == mt:
        return _ROSTER["data"]
    _ROSTER.update({"mt": mt, "data": json.loads(CATALOG.read_text())})
    return _ROSTER["data"]

# (b) slug -> tasks index, TTL 15 s (replaces reading ~80 run.json per request)
_TIDX = {"at": 0.0, "data": {}}
def _task_index():
    if time.time() - _TIDX["at"] < 15:
        return _TIDX["data"]
    idx = {}
    for meta in ar.latest(80):
        run = ar.load(meta["id"]) or {}
        for picked in (run.get("plan") or {}).get("ejen") or []:
            out = next((o for o in run.get("outputs") or [] if o["slug"] == picked["slug"]), None)
            idx.setdefault(picked["slug"], []).append({...})
    _TIDX.update(at=time.time(), data=idx)
    return idx

# (c) whole payload per slug, TTL 20 s
_DASHC = {}
def api_agent_dashboard(slug):
    hit = _DASHC.get(slug)
    if hit and time.time() - hit[0] < 20:
        return hit[1]
    payload = {...}
    _DASHC[slug] = (time.time(), payload)
    return payload
```

Cache invalidation is by TTL, not by write hooks — a 15–20 s staleness window is invisible
to a human and keeps the code free of "forgot to invalidate" bugs.

## 4. `/api/agency/health` — one cheap fleet snapshot

Answers "are the agents okay?" without opening 282 pages. Cache 15 s.

```json
{"roster": {"ejen": 282, "divisi": 18, "archetype": 8,
            "tier": {"A": 43, "B": 127, "C": 112}, "kata_badan": 533650,
            "dijana": "2026-11-04T23:01:13"},
 "runs":   {"jumlah": 18, "selesai": 14, "gagal": 3, "aktif": 0, "status": {...}},
 "penggunaan": {"jumlah": 9, "terpakai": [{"slug": "...", "panggilan": 3, "terakhir": "..."}]},
 "masa": "2026-11-04T23:55:00"}
```

UI: a 2×2 grid (4 columns ≥760 px) above the entity list — roster, tier split, run
done/total, tool calls — plus a **"Uji 12 ejen rawak"** button that fetches 12 dashboards
client-side and prints `12/12 lulus · median 73 ms`. That button is the difference between
"the panel says healthy" and "the fleet answered just now".

## 5. Mobile-first entity UI (phone, one thumb)

Layout that worked, in order: hero (counts) → health strip → sticky search + sort →
horizontal archetype chips → one-column rows → entity page.

- Rows are `<button>` (`min-height: 68px`), emoji + name + `archetype · division · tags` +
  two-line clamped summary + tier pill. Every tap target ≥44 px.
- Sticky search bar: `position: sticky; top: 52px` (96 px on ≤700 px where tabs wrap to a
  second line), `backdrop-filter: blur(8px)`, input `min-height: 44px`.
- Chips: `display:flex; overflow-x:auto; scrollbar-width:none`, `white-space:nowrap`,
  active chip in accent colour with dark text.
- **Render cap.** 282 rows = 168 KB of HTML; on a phone that is a visible jank. Render 60,
  append a full-width "Tunjuk lagi 60 · N baki" button that raises the limit. Reset the
  limit on every search/chip change.
- Picker ↔ entity page are two views of the same tab (`display:none` toggling), with a
  `← Semua ejen` button at the top of the entity page and `window.scrollTo({top:0})` on
  switch. No modal, no second tab, no history API — a phone user just wants to go back.
- Entity page sections in the order a user asks the questions: identity (emoji, name,
  division/archetype/tier pills, vibe, "pilih bila") → 2×2 KPI (tasks, completion %,
  mean ms, cost) → task list (status dot + date + ms + instruction + scope + verdict) →
  persona data (words/sections/bullets/originality, deliverable bullets, section table,
  source path) → performance → archetype evidence chips → actions.
- Tab bar on ≤700 px: `overflow-x:auto; flex-wrap:nowrap`, tabs `flex:0 0 auto` — seven tabs
  do not fit and wrapping pushes the sticky offsets out of alignment.

## 6. Verifying all 282 entities (not a sample)

```python
with ThreadPoolExecutor(max_workers=8) as ex:
    hasil = list(ex.map(check_one, agents))
lat = [h["ms"] for h in hasil if h["status"] == 200]
report = {"api_ok": …, "api_gagal": …, "isu_data": …,
          "latensi_ms": {"min": min(lat), "median": median(lat),
                         "p95": sorted(lat)[int(len(lat) * .95)], "maks": max(lat)}}
```

8 workers keeps Termux responsive; 282 requests finish in ~19 s. Write **both**
`reports/VERIFIKASI.json` (machine) and `reports/VERIFIKASI.md` (human, Malay, with a
"what failed and why" table). Exit non-zero only on HTTP failures.

Checks that caught real problems: `badan_kata >= 200`, non-empty `vibe`, valid `tier`,
`persona.ada_badan`, unique slugs, and `tugasan` is a list.

Honest reporting of the one outlier (`xr-interface-architect`, 192 words) as **source data,
not an API bug** matters more than a clean 282/282 headline.

## 7. Browserless UI harness for this page

Reuse `templates/render_test.js` shape, plus these specifics:

```js
const src = fs.readFileSync("static/app.js", "utf8");
const head = src.slice(0, src.indexOf("boot().catch("));   // never run boot()
vm.runInContext(head, ctx, {filename: "app.js"});
```

Stubs required by this page: `AbortController`, `performance`, `navigator.clipboard.writeText`,
`window.scrollTo`, `matchMedia`, and **`setTimeout: () => 0`**.

> The `setTimeout` stub must be a no-op. An "invoke immediately" stub fires the `api()`
> AbortController timer at t=0, so every check fails with `tamat masa (25s)` and the page
> looks broken while the server is fine.

Assertions that earned their place: list renders (`avrow`, length > 5,000), chips contain an
archetype label, all five entity sections present, tier regex `TIER [ABC]`, switching entity
changes the heading, health card contains `ROSTER` + `GUNA TOOL`, the random-12 button prints
`N/N lulus` with no `gagal:`, roster cards render with tiers.

## 8. End-to-end agent runs: how not to strand them

- **Never wrap an in-process run in `timeout`.** `timeout 300 python3 tools/test_agents.py`
  kills the process that owns the runner thread; `run.json` stays at `synthesizing` forever
  and the transcript is empty because `tail` buffers. Use `background=true` +
  `notify_on_complete`, poll the run files separately.
- Add a **janitor** thread (start + every 5 min, `recover_stale(max_age_s=420)`) so an
  orphaned `synthesizing` run becomes `failed` with a reason instead of hanging the UI.
- Rebuild the summary from `runs/*/run.json` (`tools/report_agents.py`), not from the
  process that ran them — that process may be gone, and it is the only way to re-score old
  runs after fixing the scorer.
- Verdict lines are claims: parse tolerantly (`"STATUS AKHIR" in line.upper()`, not
  `startswith` — models bold it as `**STATUS AKHIR: …**`), and when the model omits the line
  entirely, append one **marked as inferred**:

```python
def ensure_verdict(txt):
    if "STATUS AKHIR" in txt.upper():
        return txt
    v = "BLOCKED" if "BLOCKED" in txt.upper() else (
        "NEEDS_WORK" if ("NEEDS_WORK" in txt.upper() or "GAGAL" in txt.upper()) else "DONE")
    return txt.rstrip() + f"\n\nSTATUS AKHIR: {v} (disimpulkan daripada teks; model tidak menulis baris ini)"
```

## 9. Deliverables this user expects

- `docs/KETUA.md` — plain-Malay reference: real counts, four layers per entity with a real
  example (copy the actual `vibe`/`hasil` strings; do not paraphrase), file map, API table
  with measured ms, numbered phone steps, every test + its result, maintenance, limits.
- `reports/VERIFIKASI.md` — generated, never hand-written.
- `OPERASI.md` gains a short "rujukan pantas" table pointing at both.
- Chat reply: status per request, a table of measured numbers, the bugs found and fixed,
  then **3–4 numbered next-step options** (the user answers by number).
