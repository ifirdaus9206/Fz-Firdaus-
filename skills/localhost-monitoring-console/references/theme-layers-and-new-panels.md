# Light theme across EVERY layer + adding a new panel (MCP)

Follow-up to `contrast-and-tunnel-exposure.md`. That file fixes "the background is still dark".
This file fixes "the page is light but *one block* is still black", plus the LAN-bind and
non-interactive-CLI lessons that came out of the same console.

## 1. "Page is light, one block is still black" = hardcoded colours in a SECOND layer

The console loaded two stylesheets:

```html
<link rel="stylesheet" href="/static/style.css?v=...">   <!-- original app -->
<link rel="stylesheet" href="/static/theme.css?v=...">   <!-- theme layer -->
```

`theme.css` only overrode the classes it knew about. `style.css` still hardcoded dark values on
`.dropzone`, `.inbox-item`, `#inbox-note`, `.abadge`, `.divchip`, `.body-log`, `.cmdk`, etc. Those
survived every light-theme change — the user circled them as "blok hitam".

**Rule: a light theme is a layer over ALL stylesheets, not a rewrite of one.**

```bash
# find every remaining hardcoded dark background in the ORIGINAL css
grep -n 'background:#0\|background:#1\|background:#2' static/style.css
```

Then append one block to the theme file (loaded last, so it wins) listing those selectors:

```css
/* ===== TERANG: komponen yang masih gelap dalam style.css ===== */
body.light .inbox-item, body.light .dropzone, body.light #inbox-note,
body.light .divchip, body.light .abadge, body.light .cmdk {
  background:#fff !important; border-color:#e4e4e7 !important; color:#18181b !important;
}
body.light .workbar input, body.light textarea { background:#fff !important; color:#18181b !important; }
```

Do not touch `style.css` itself — keep the override in one dated block so the next theme change
is a single edit.

## 2. Inline SVG charts ignore CSS unless you convert them to variables

The org chart was generated in JS with colours baked into the markup:

```js
`<rect ... fill="#0b1311" stroke="#1c2a26"/>`
`<text ... fill="#d7e4df">`
```

A light theme that only sets `body.light svg text{fill:#27272a}` makes the text dark **on top of a
dark rect** → solid black bars with invisible labels. Exactly the reported symptom.

Fix: define chart tokens once and render with `style="fill:var(--oc-…)"` (a `style` attribute is a
real CSS declaration, so `var()` works and beats the presentation attribute):

```css
:root{ --oc-node:#0b1311; --oc-text:#d7e4df; --oc-link:#1c2a26; --oc-accent:#5ee3a1; }
body.light{ --oc-node:#ffffff; --oc-text:#18181b; --oc-link:#d4d4d8; --oc-accent:#16a34a; }
```

```js
`<rect style="fill:var(--oc-node);stroke:var(--oc-link)"/>`
`<text style="fill:var(--oc-text)">`
```

Pitfalls:
- Replace colours **only inside the render function**. A naive global replace hits unrelated
  helpers (`floatCards`, legend chips) — find the function boundary first
  (`s.index("function renderChart(")` → `s.index("function collectRunning(")`) and rewrite that slice.
- Keep `fill="none"` rects as attributes; a blanket `fill:#fff` rule fills the pulse outlines.
- Division colours arriving from the API (`#06B6D4`, `#10B981`, …) are mid-tone and readable on
  white — leave them as data, only the fallback should be a token.

## 3. Binding for LAN access without breaking generated URLs

`127.0.0.1` only accepts connections from the device itself. To let the phone browse over Wi-Fi,
bind all interfaces — but keep the *advertised* host as `127.0.0.1` so links/API payloads do not
start pointing at `0.0.0.0`:

```python
CONSOLE_HOST = os.environ.get("CONSOLE_HOST", "127.0.0.1")   # used in URLs
CONSOLE_BIND = os.environ.get("CONSOLE_BIND", CONSOLE_HOST)  # used by uvicorn
uvicorn.run(app, host=CONSOLE_BIND, port=CONSOLE_PORT)
```

Plus the allowlist needs the LAN host **with its port**:

```bash
CONSOLE_BIND=0.0.0.0
CONSOLE_ALLOWED_HOSTS=192.168.0.41:8787
CONSOLE_ALLOWED_ORIGINS=http://192.168.0.41:8787
```

Verify all three in one turn: `127.0.0.1`, LAN IP, tunnel URL → all `200`.

## 4. Write-endpoint auth header is `x-console-token`, not `X-CSRF-Token`

The guard reads `request.headers.get("x-console-token")` and compares to the CSRF token from
`GET /api/meta` (`csrf`). Sending `X-CSRF-Token` returns 200-looking JSON with
`{"error":"token konsol salah"}` — easy to misread as a broken endpoint. Always:

```bash
T=$(curl -s http://127.0.0.1:8787/api/meta | python3 -c "import sys,json;print(json.load(sys.stdin)['csrf'])")
curl -s -X POST ... -H "x-console-token: $T"
```

## 5. New panel: MCP servers — `hermes mcp add` is interactive, so don't call it from an API

`hermes mcp add` prompts ("Does this server require authentication? [y/N]", "…[y/N]") and with
stdin closed it silently exits without writing anything. Driving it from a background HTTP handler
therefore "succeeds" while adding nothing. Two working paths:

```bash
# add: write config.yaml directly (backup first). ~/.hermes20/config.yaml has no comments.
python3 - <<'PY'
import json, pathlib, shutil
p = pathlib.Path.home()/".hermes20/config.yaml"
shutil.copy2(p, p.with_suffix(".yaml.bak-mcp"))
import yaml; d = yaml.safe_load(p.read_text()) or {}
d.setdefault("mcp_servers", {})["n8n"] = {"command":"npx","args":["-y","n8n-mcp"],"enabled":True}
p.write_text(yaml.safe_dump(d, sort_keys=False, allow_unicode=True))
PY

# remove: the CLI is non-interactive and safe
hermes config unset mcp_servers.n8n
```

Notes:
- `hermes config set mcp_servers.x.args "-y pkg"` stores the value as a **string**, not a list —
  MCP clients then fail to launch. Use YAML for anything structured.
- `hermes mcp catalog` lists Nous-approved servers (JSON-able lines: name, availability, blurb) —
  good source for a "disyorkan" list in the UI.
- HTTP/SSE servers need `streamable_http` in the installed `mcp` package; if it is missing the
  connection fails and the add path may write nothing. Prefer stdio (`command` + `args`) until the
  package is upgraded, and say so in the UI rather than pretending the add worked.

## 6. runit restart can hang — kill by PID instead

`sv restart hermes-console` sometimes blocks. Reliable sequence:

```bash
PID=$(sv status hermes-console | grep -o 'pid [0-9]*' | awk '{print $2}'); kill -9 "$PID"; sleep 2; sv up hermes-console
```

Then verify `curl -s -o /dev/null -w "%{http_code}"` on local, LAN and tunnel in the same turn.
