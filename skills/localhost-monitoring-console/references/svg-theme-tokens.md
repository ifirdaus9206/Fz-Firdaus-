# Inline SVG charts that ignore the light theme (black bars, invisible labels)

Symptom seen on the SATU PUSAT console: user in light mode reported "carta organisasi
nampak blok hitam" — the org chart rendered as solid black rectangles with no readable text,
while the rest of the page was correctly light. Two separate light-theme fixes had already
been applied and "worked" everywhere except the chart.

## Root cause (two bugs stacked)

1. **Chart colours were hardcoded in the JS template literal**, not in CSS:

```js
<rect ... fill="${active ? "#12241c" : "#0b1311"}" stroke="${active ? "#5ee3a1" : "#1c2a26"}"/>
<text ... fill="#d7e4df">${label}</text>
```

   So the rects stayed dark in light mode no matter what the theme did.

2. **A light-mode rule forced SVG text dark**:

```css
body.light svg text{fill:#27272a!important}
```

   Dark text + dark rect = invisible label. The user sees "black blocks" because the
   rectangle survives and the text does not.

Diagnose with a grep before touching CSS:

```bash
grep -n 'fill="#\|stroke="#' static/app.js | head -40        # hardcoded colours in the chart
grep -n 'svg text' static/theme.css                          # blanket text override
```

## Fix: drive SVG colours through CSS custom properties

SVG presentation attributes (`fill="..."`) are overridden by CSS rules, but **inline `style`
attributes beat CSS rules**. So put the variable in a `style` attribute — that way the value
follows the theme without needing `!important` gymnastics.

```js
// dark defaults in :root, light overrides in body.light
<rect style="fill:var(--oc-node);stroke:var(--oc-link)"/>
<text style="fill:var(--oc-text)">${label}</text>
```

```css
:root{
  --oc-link:#1c2a26; --oc-node:#0b1311; --oc-node-active:#12241c;
  --oc-accent:#5ee3a1; --oc-text:#d7e4df; --oc-dim:#6f8a81;
  --oc-float:#121a12; --oc-float-text:#e8f5ef;
}
body.light{
  --oc-link:#d4d4d8; --oc-node:#ffffff; --oc-node-active:#ecfdf5;
  --oc-accent:#16a34a; --oc-text:#18181b; --oc-dim:#52525b;
  --oc-float:#ffffff; --oc-float-text:#18181b;
}
```

Then delete the blanket `body.light svg text{...}` rule — it is the thing that made labels
invisible.

### Pitfalls

- **`fill="none"` elements** (pulse outlines, connectors) must keep `fill:none`; a blanket
  `body.light #oc rect{fill:#fff}` would paint them solid. That is why the variable approach
  is better than a CSS selector sweep.
- **Data-driven colours are fine on light** if they are mid-tone hexes (`#0EA5E9`, `#10B981`,
  `#EF4444`). Check them first: `curl -s .../api/orgchart | python3 -c "import sys,json;print(sorted({v.get('color') for s in json.load(sys.stdin)['systems'] for v in s['divisions']}))"`.
- **Helper functions outside the main renderer** hold more hardcoded colours (floating
  "running agent" cards were in a separate `floatCards()`). Grep the whole file, not just the
  function you already edited.
- **Light palettes must be one palette.** Mixing cream/amber blocks with white/grey blocks
  reads as "still broken". Pick one: bg `#f6f7f9`, card `#ffffff`, border `#e4e4e7`,
  text `#18181b`, dim `#52525b`, accent `#16a34a`.
- **Pills/tags** have their own dark base rule; add a `body.light .pill` / `.tag` override or
  the HUD bar stays black while the rest of the page is light.

## Verification (server-side, no eyeballing)

```bash
sed -i 's/theme.css?v=7/theme.css?v=8/; s/app.js?v=7/app.js?v=8/' static/index.html
node --check static/app.js
PID=$(sv status hermes-console | grep -o 'pid [0-9]*' | awk '{print $2}'); kill -9 $PID; sv up hermes-console
curl -s -o /dev/null -w "konsol=%{http_code}\n" http://127.0.0.1:8787/?tab=pusat
curl -s "http://127.0.0.1:8787/static/theme.css?v=8" | grep -c '\-\-oc-'      # >0 = vars served
curl -s "http://127.0.0.1:8787/static/app.js?v=8"    | grep -c 'var(--oc-'    # >0 = chart themed
curl -s "http://127.0.0.1:8787/?tab=pusat" | grep -o 'body class="[a-z]*"'    # light applied server-side
```

Bump BOTH `?v=` strings in `index.html` (CSS and JS) on every theme change — a stale JS file
keeps re-rendering the old dark chart even when the CSS is correct.
