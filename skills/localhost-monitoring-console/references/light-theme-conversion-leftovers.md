# Converting a dark console to a light theme: killing the leftover black blocks

The user kept reporting "masih ada blok hitam" after the light theme was "done". Root cause was
never the main theme file — it was **hardcoded dark colours in places the theme layer never
touched**. Three distinct sources, in the order they bit:

1. A **second stylesheet** (`style.css`) with literal dark fills (`#0b1311`, `#0a1210`, `#070d0b`).
2. **Inline SVG** produced by JavaScript with `fill="#0d1a15"` etc.
3. A blanket rule that made things worse: `body.light svg text{fill:#27272a!important}` — dark text
   on an SVG that still had dark rectangles → invisible labels that look like solid black bars.

## 1. Do not hand-list classes — scan the stylesheet

Hand-patching a dozen classes leaves 40 behind. Extract every rule whose background is dark and
generate the override block mechanically:

```python
import re, pathlib
css = pathlib.Path("static/style.css").read_text()
rules = re.findall(r'([^{}]+)\{([^}]*)\}', css)
plain, active = [], []
for sel, body in rules:
    sel = " ".join(re.sub(r'/\*.*?\*/', '', sel, flags=re.S).split())
    if not sel or "media" in sel:
        continue
    hexes = re.findall(r'background[^:]*:\s*(#[0-9a-fA-F]{3,6})', body)
    dark = False
    for h in hexes:
        h = h.lstrip('#')
        if len(h) == 3: h = "".join(c*2 for c in h)
        if (int(h[0:2],16)+int(h[2:4],16)+int(h[4:6],16))/3 < 90:
            dark = True
    if not dark:
        continue
    for one in sel.split(","):
        one = one.strip()
        if not one: continue
        (active if any(k in one for k in (":hover", ".on", ".sel", ".over")) else plain).append(one)
# emit: plain -> #ffffff / #18181b ; active -> #ecfdf5 / #14532d
```

Append the generated block to the theme file that loads **last**, with `!important` on
background, border-color and color. A stylesheet `!important` beats an inline `style="..."`,
so this also fixes elements styled from JS.

Count the selectors you produced and report that number — "58 kelas" is proof, "dah tukar" is not.

## 2. SVG: move fills into CSS variables

`fill="var(--x)"` as a presentation attribute is unreliable; use the style attribute:

```js
// before
`<rect fill="#0b1311" stroke="#1c2a26"/>`
// after
`<rect style="fill:var(--oc-node);stroke:var(--oc-link)"/>`
```

Define the variables in the base theme and override them in the light block:

```css
:root{ --oc-node:#0b1311; --oc-text:#d7e4df; --oc-link:#1c2a26; }
body.light{ --oc-node:#ffffff; --oc-text:#18181b; --oc-link:#d4d4d8; }
```

Then delete any `body.light svg text{fill:...}` blanket rule — it is what turns labels invisible.

## 3. Phone cannot open 127.0.0.1 even though it IS the server

The app bound `127.0.0.1`. Fix the binding, not the URL:

```python
HOST = os.environ.get("CONSOLE_BIND", "127.0.0.1")   # bind address
URLHOST = os.environ.get("CONSOLE_HOST", "127.0.0.1") # address printed in URLs
```

```bash
export CONSOLE_BIND=0.0.0.0
export CONSOLE_ALLOWED_HOSTS="192.168.1.23:8787"
export CONSOLE_ALLOWED_ORIGINS="http://192.168.1.23:8787"
```

The Host allowlist must contain the LAN `ip:port` too, or the page loads but every request 403s.
Verify all three in one turn and quote the codes:

```bash
curl -s -o /dev/null -w "local=%{http_code}\n" http://127.0.0.1:8787/
curl -s -o /dev/null -w "lan=%{http_code}\n"   http://<LAN_IP>:8787/
curl -s -o /dev/null -w "tunnel=%{http_code}\n" "$U/"
```

## 4. Bump versions on every theme change

`theme.css?v=N` and `app.js?v=N` in the HTML. A correct CSS file served under the old query string
still looks broken. Tell the user to close the old tab — a hard refresh on a cached tab is not
guaranteed on mobile browsers.

## Pitfalls

- The user's screenshot may be **stale**. Ask for a fresh one after the version bump before
  chasing the same block twice.
- A screenshot that "shows a black block" is often dark SVG text on a dark rect, not a background.
  Look for `fill` attributes in the render function, not only in CSS.
- Keep a light-mode palette that is genuinely neutral (`#f6f7f9` page, `#ffffff` cards,
  `#18181b` text, `#16a34a` accent). Mixing cream and grey blocks looks like a bug.
