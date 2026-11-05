# Dewan Arahan — orchestrating a large agent roster from the console

Pattern: the user types an instruction in the console; a "Ketua" planner LLM surveys the whole
roster (hundreds of agents), picks a few, each runs **with its own persona as system prompt**,
then Ketua synthesises a verdict. Read-only console becomes a control panel; every run is
archived on disk.

Validated end-to-end against a 282-agent roster (2026-11):

| Phase | Call | Measured |
|---|---|---|
| plan (digest 282 agents + instruction → JSON plan) | 1 | ~13 s |
| execute (N personas in parallel, max 3 workers) | N | 28–35 s each |
| synthesize (all outputs → verdict) | 1 | ~45 s |
| total, 2 agents | 4 | ~80 s |

## 1. Roster digest — cheap enough for one call

282 × `slug | name | division | description[:105]` ≈ 20 KB ≈ 5k tokens. One call, no retrieval
needed. Do **not** send full persona bodies to the planner — that's 1,900 words × 282.

```python
def digest(roster):
    return "\n".join(f"{a['slug']} | {a['name']} | {a['division']} | {one_line(a['description'],105)}"
                     for a in roster)
```

Add a one-paragraph style digest (counts per archetype/length) so the planner knows the roster's
shape without reading it: "282 persona, avg 1892 words, archetypes {lengkap:219,...}".

## 2. Plan contract (force JSON, validate slugs)

System prompt: Ketua plans only, never executes; laws ("no agent without a direct contribution",
scope must fit one task, write assumptions instead of inventing facts, pick 2..max).
Shape: `faham, jenis_tugasan, andaian[], sistem_terlibat[], ejen[{slug,nama,sebab,skop,hasil_dijangka}], langkah[], risiko[], format_hasil`.

- `response_format={"type":"json_object"}` + strip ```` ```json ```` fences and fall back to
  `raw[raw.find("{"):raw.rfind("}")+1]`.
- **Validate every returned slug against the roster** and drop unknowns/duplicates. Models invent
  plausible slugs; without this the runner 404s or runs an empty persona.
- Reject empty selection with a clear error ("cuba arahan lebih spesifik"), not a stack trace.

## 3. Persona injection

```
system = <agent body verbatim> + "\n---\nKONTEXT ORKESTRASI: ... skop sahaja ...
          Akhiri dengan STATUS: DONE|NEEDS_WORK|BLOCKED / BUKTI: / SERAHAN:"
user   = ARAHAN ASAL (verbatim) + SKOP KAU (planner) + HASIL DIJANGKA
```

Keep the body verbatim — the roster is near-uniform ("You are X" + Identity/Mission/Rules/
Workflow/Metrics), so no rewriting is needed and altering it destroys the differentiation.
Force a trailing STATUS/BUKTI/SERAHAN block so the synthesis has machine-checkable claims.

## 4. Run state machine + artifacts

`planning → planned → running → synthesizing → done | failed`

- Plan is **synchronous** (user waits ~13 s and reviews before spending N agent calls).
- Execution is a daemon thread; frontend polls `GET /api/agency/run/{id}` every 2.5 s.
- Persist after every mutation: `runs/<id>/run.json` (+`plan.json`, `out_<slug>.md`,
  `final.md`). Thread-safety: single writer function `save(run)`.
- Frontend keeps `S.da.run` and only renders from polled state; steps indicator lights 1..8.

## 5. Independent agents cannot cross-review — say so

Parallel personas run in isolation: a "brand-guardian" never sees the "copywriter" output, so it
reviews its own draft. Ketua can (and did) detect this and returned `NEEDS_WORK` with the reason.
Capture it in PLAN.md as an acknowledged limitation and offer the fix: an optional `depends_on`
field so a reviewer agent receives the upstream output. Do not silently present isolated reviews
as cross-checks.

## 6. Reasoning models via OpenRouter

- `finish_reason == "length"` with **empty content** means reasoning tokens ate the budget:
  double `max_tokens` (cap ~8000) and retry once. A 20-token cap is always empty; 300 works for
  one word. Defaults used here: planner 1800 (retry to 3600), agent 1800, synthesis 2200.
- urllib headers are **latin-1**: an em dash in `X-Title` raises
  `'latin-1' codec can't encode character '\u2014'`. Keep header values ASCII.
- 429/5xx → sleep 2–3 s and retry; log HTTP body excerpt (300 chars) in the error.
- Read the key from `~/.hermesNN/.env` **server-side only**; never expose it in an endpoint or
  the frontend bundle.

## 7. Cost/limits guards

Clamp `max_agents` server-side (1..6), instruction length (12..4000 chars), and only start a run
from an existing `planned|failed` record. `ThreadPoolExecutor(max_workers=min(3, len(agents)))`
keeps rate limits sane while still finishing a 3-agent batch in one agent's latency.

## 8. Auditing the verdict before you relay it

`final.md` is generated from **truncated** inputs (`[:7000]` upstream at `run_agent`, `[:9000]` into
`synthesize`), so it can fail QA gates that were actually satisfied — measured: two agents reported
"terputus" while their `out_<slug>.md` files were complete and ended in `STATUS: DONE`.

Before repeating a verdict to the user:

1. Slice the stored text at the cap boundary (`t[8940:9000]`, `t[6940:7000]`) and check whether it
   ends exactly where the verdict claims the text stopped.
2. Compare `len(o["text"])` with the `out_<slug>.md` size — equal means nothing was lost.
3. Re-derive the gate table: gates failed only by the slice → LULUS; gates failed on genuinely
   missing content → keep GAGAL. The overall status may stay `NEEDS_WORK` with different reasons.
4. Raise both caps (≥24k) so the next run is judged on full text.

Full recipe, evidence table and the `PAKEJ/` handoff layout (numbered `.md` files + `00_BACA_DULU.md`
matrix + separate `SEMAKAN_BUKTI` correction file): `references/run-verdict-reconciliation.md`.
