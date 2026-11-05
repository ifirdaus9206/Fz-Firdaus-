# Live org chart + real-time panels (phase 7)

Goal: one "PUSAT" (mission-control) tab that shows **Ketua → 8 systems → 18 divisions → N agents**
with live highlighting of agents currently running, plus a feed, load sparkline and cost radar.
This is what "carta organisasi langsung … ejen mana yang sedang jalan secara live" asks for.

## 1. Hierarchy model (server)

Do not invent a hierarchy; derive it from two real sources and store the mapping explicitly.

```python
DIV_SYSTEM = {
    "agent_factory":    ["research", "academic", "product", "specialized"],
    "role_generator":   ["design", "spatial-computing", "game-development"],
    "workflow_generator": ["project-management", "gis"],
    "orchestrator":     ["engineering", "marketing", "sales", "paid-media", "finance"],
    "qa_system":        ["testing"],
    "recovery_system":  ["support"],
    "completion_system": ["security", "healthcare"],
    "memory_manager":   [],
}
```

- System keys come from parsing the SOUL "ENJIN" markdown table (`md_table(get_section(soul, "ENJIN"))`)
  — same source the ORGANISASI tab already uses, so the two tabs can never disagree.
- Division keys/counts/colours come from the agency catalogue (`divisions.json` + roster).
- `memory_manager` legitimately has no divisions: draw a dashed placeholder
  "modul memori · tiada divisi" instead of a blank column.
- Compute `totals.agents`, `totals.divisions`, `totals.active`, and `unmapped` (divisions that no
  system claimed). `unmapped: []` is the assertion that the mapping is complete.

`GET /api/orgchart` returns `{ketua:{title,sub,model}, systems:[{key,role,when,count,active,
divisions:[{key,label,color,count,used,active:[slug],top:[{slug,name,emoji}]}]}], totals, unmapped}`.

## 2. Deriving "who is running right now"

The only authoritative source is the orchestrator's run record, not the UI:

```python
done = {o["slug"] for o in run.get("outputs") or []}
wave = run.get("waves") or []
cur  = set(wave[min((run.get("wave") or 1) - 1, max(0, len(wave) - 1))]) if wave else set()
state = "done" if slug in done else ("running" if slug in cur else "queued")
```

`active_agents` = union of `running` across all runs with status in
`planned|running|synthesizing`. Feed this to the chart's per-division `active` list and to the
"SEDANG JALAN" panel. When nothing runs, the panel must say so explicitly, not render an empty card.

## 3. Push, don't poll, for the live view

```python
@app.get("/api/live/stream")
async def api_live_stream():
    import asyncio
    from fastapi.responses import StreamingResponse
    async def gen():
        for _ in range(300):                 # ~10 min, then EventSource reconnects by itself
            yield f"data: {json.dumps(live_state(), ensure_ascii=False)}\n\n"
            await asyncio.sleep(2)
    return StreamingResponse(gen(), media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no", "Connection": "keep-alive"})
```

Client:

```js
const es = new EventSource("/api/live/stream");
es.onmessage = (e) => applyLive(JSON.parse(e.data));
es.onerror = () => { es.close(); S.pusat.es = null; setTimeout(startLive, 8000); };
```

Keep `GET /api/live/state` as well — SSE is the accelerator, polling is the fallback.
`live_state()` shape that worked: `{now, gateway, runs[], active_agents[], stats{sessions_today,
tools_today, tokens_today, cost_today, active_sessions, series_60m[12]}, feed[20], guard}`.

The 60-minute series is 12 buckets of 5 minutes:

```sql
SELECT CAST((CAST(:now AS INTEGER) - CAST(timestamp AS INTEGER)) / 300 AS INTEGER) b, COUNT(*)
FROM messages WHERE role='tool' AND timestamp >= :now-3600 GROUP BY b
```
then place bucket `b` at index `11 - b` (oldest → newest, left → right).

## 4. Drawing the chart (client SVG, no library)

- Fixed viewBox `0 0 1400 H`; `H = 186 + maxDivisions * 66 + 10`, recomputed from data
  (`svg.setAttribute("viewBox", ...)`) — never hardcode a height that clips the last division row.
- 8 system slots: `cx = 20 + slot*i + slot/2`, `slot = 170`, system box `158×54`, division box
  `150×54`, vertical gap `66`.
- Root box `240×48` at `W/2`; connectors are elbow paths `M root V78 H cx V96` (cheap and legible).
- Truncate every label (`trunc(text, 17)`) — long division/system names overflow their box.
- Root subtitle (model name) also needs truncation (~32 chars) or it spills outside the box.
- Active systems/divisions: brighter fill + full-opacity stroke + an extra `<rect class="oc-pulse">`
  with CSS `@keyframes` scaling 1 → 1.45 and fading; plus a badge `<circle>` with the active count.
- `svg text { pointer-events: none }` so clicks land on the `<g class="oc-div">`.
- Click a division → set the AGENCY tab's filter state and `setTab("agency")`.

## 5. Verify the chart without a browser

Node DOM shim renders it, but you still can't *see* it. Dump it:

```js
// after boot(): const inner = q('#oc').innerHTML
const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="620"
  viewBox="${q('#oc').viewBox}"><style>text{font-family:monospace}</style>
  <rect width="1400" height="620" fill="#070a09"/>${inner}</svg>`
fs.writeFileSync('tools/preview-chart.svg', svg)
```

`rsvg-convert -w 1400 -o tools/preview-chart.png tools/preview-chart.svg` then inspect the PNG with
`vision_analyze` ("teks bertindih? kotak terpotong?"). This caught the model-name overflow and the
empty `memory_manager` column. Dump **during** a real run to prove the active highlight (the PNG
should show one glowing system + one glowing division + a count badge).

## 6. UX extras that pay for themselves

- `Ctrl/⌘K` command palette: tabs + top agents + actions, arrow keys, Enter, Esc.
- Number keys `1..7` switch tabs; skip when an INPUT/TEXTAREA/SELECT is focused.
- Toast on run `done`/`failed` so the user doesn't have to watch the AGENCY tab.
- Hero art: generate it (deterministic `random.Random(seed)` node graph on a grid → SVG →
  `rsvg-convert`), don't hotlink stock images — offline and theme-consistent.
- Rotating radar dial is pure CSS (`@keyframes spin`) — no JS timer.
- Make the monitoring tab the **default** tab (`S.tab = "pusat"`), and remember the HTML `.active`
  class must match that default or the first paint lies.

## 7. Checklist

- [ ] `/api/orgchart`: `unmapped == []`, totals match roster count.
- [ ] `/api/live/state`: `active_agents` non-empty **during** a run, empty after.
- [ ] SSE emits `data:` frames (prove with `curl -sN | head -c 200`).
- [ ] Chart PNG visual check with active highlight captured mid-run.
- [ ] `render_test.js` asserts chips, chart (`oc-div`, `KETUA`), radar, spark, feed.
