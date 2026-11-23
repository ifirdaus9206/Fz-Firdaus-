# Light-theme full sweep: killing every remaining dark block in one pass

Companion to `contrast-and-tunnel-exposure.md`. That file explains *why* a light theme leaks;
this one is the **repeatable procedure** for "still got black blocks" rounds — the failure mode
where the user circles one element, you fix it, they circle another, and the loop never ends.

## Why the loop happens

The user reports **one** element per screenshot. If you patch only that element, the next
screenshot shows the next one. Three rounds of "I fixed the pill" / "now the chart" / "now the
input" is the symptom. The user's instruction is almost always "tukar SEMUA yang hitam" —
change *all* of them. Treat every report as "do a full sweep", not "fix this selector".

## Procedure

### 1. Identify the element from the screenshot before touching CSS

Say out loud which panel and which class the dark block is: "that is the EMAIL folder-count
pills (`.chip-live` inside `#em-chips`), not a chart". Then grep the render function to confirm
the class actually used. Guessing the class from the picture is how you fix the wrong thing.

```bash
grep -n "em-chips\|chip-live" static/index.html static/app.js | head
```

### 2. Sweep the base stylesheet for near-black backgrounds

```python
import re, pathlib
base = pathlib.Path("static")
style = (base/"style.css").read_text()
theme = (base/"theme.css").read_text()

dark = []
for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', style):
    sel, body = m.group(1).strip(), m.group(2)
    if 'background' in body and re.search(
            r'background[^;]*(#0[0-9a-fA-F]{2,5}|#1[0-9a-fA-F]{2,5}|rgba\([0-9]\s*,\s*[0-9]\s*,\s*[0-9]\s*,\s*0?\.?[0-9]*)',
            body):
        dark.append((sel, body.strip()[:90]))

missing = sorted({s.strip() for sel, _ in dark if '@' not in sel
                  for s in sel.split(',') if s.strip()
                  and f"body.light {s.strip()}" not in theme})
print(len(dark), "dark rules;", len(missing), "missing override")
for s in missing: print(" -", s)
```

Read the output with suspicion: selectors that are really CSS comments
(`/* panels */`) and grouped selectors (`body.light .panel,body.light .card{`) produce false
positives. Confirm each real candidate with `grep -c "body.light <sel>" static/theme.css`
before writing an override for it.

### 3. Emit ONE versioned layer, not scattered per-class edits

Append a single labelled block (`/* ===== TERANG vN ===== */`) covering every category at once:

```css
body.light .workbar input,body.light .workbar select,body.light .workbar textarea,
body.light input,body.light select,body.light textarea{
  background:#ffffff!important;border:1px solid #d4d4d8!important;color:#18181b!important;
  box-shadow:none!important
}
body.light #em-chips .chip-live,body.light .workbar .chip-live,body.light .hl-chips .chip-live{
  background:#ffffff!important;border:1px solid #d4d4d8!important;color:#3f3f46!important;
  backdrop-filter:none!important;box-shadow:none!important
}
body.light .svc-row{background:#ffffff!important;border-color:#e4e4e7!important}
```

Two selector shapes the base-sheet sweep misses and that keep biting:

- **Container-scoped instances** — the same class rendered into a different parent
  (`#em-chips .chip-live`) needs its own selector; `body.light .chip-live` alone may not be
  enough when the container itself paints.
- **Form controls** — `input`, `select`, `textarea` in a `.workbar` carry `background:#0d1513`
  in the base sheet. They are the dark rectangles users most often circle.

### 4. Bump and verify against the SERVED bytes, not the file on disk

```bash
sed -i 's/theme.css?v=13/theme.css?v=14/; s/app.js?v=13/app.js?v=14/' static/index.html
python3 -c "import ast;ast.parse(open('app.py').read())"   # syntax gate
P=$(sv status hermes-console | grep -o 'pid [0-9]*' | grep -o '[0-9]*'); [ -n "$P" ] && kill -9 $P
sleep 1; sv up hermes-console; sleep 3
curl -s -o /dev/null -w 'konsul=%{http_code}\n' http://127.0.0.1:8787/
curl -s 'http://127.0.0.1:8787/static/theme.css?v=14' | grep -c 'TERANG v14'
curl -s 'http://127.0.0.1:8787/?tab=pusat' | grep -o 'theme.css?v=[0-9]*'
```

`grep -c 'TERANG v14'` returning `1` on the *served* URL is the proof the layer reached the
browser path. A count of `0` means the file was appended but the server is still serving the
old copy — restart, do not re-edit.

### 5. Say "hard-reload" and name the version in the reply

A screenshot the user sends may be older than the fix you just shipped. Do not conclude the fix
failed from a screenshot alone — state the version now served (`theme.css?v=14`) and ask for one
hard reload (`Ctrl+Shift+R`) before the next screenshot. If they still circle a block after
that, the element is genuinely un-overridden: go back to step 2.

### 6. Reused-but-relevant facts

- `style.css` is the base dark sheet; `theme.css` is loaded *after* it and holds the light
  layer. Order matters only for equal specificity — `!important` in the light layer wins
  regardless, so prefer `!important` over reordering.
- Static files are mounted with `StaticFiles`; the app's HTTP middleware already sets
  `Cache-Control: no-store`, so a stale view is usually the browser's own memory/BFCache rather
  than a server header.
- `sv restart` / `sv down` for the console can hang; the reliable sequence is read the PID from
  `sv status`, `kill -9`, then `sv up`.
