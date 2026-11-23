# Exposing a localhost console on a tunnel + making text legible

Two bugs that look like "the UI is broken" but are actually **the wrong page** and **a theme
layer that never resets its background**. Both were diagnosed on the SATU PUSAT console
(FastAPI + static HTML/CSS/JS, port 8787) after the user reported "tulisan hitam tak nampak"
and "watak tak nampak" on a `*.trycloudflare.com` URL.

## 1. Symptom: missing tabs / invisible text on the public URL only

Root cause found: the tunnel was started with the **wrong target port**.

```bash
# dash_tunnel.sh had:
cloudflared tunnel --url http://127.0.0.1:9119   # the Hermes dashboard
# but the console (with WATAK / KERJA / SKILL tabs) is on 8787
```

The user was looking at a completely different application. No amount of CSS or nav work on the
console could ever show up there.

**Diagnose in this order — never start with CSS:**

```bash
# 1. what port does the tunnel actually publish?
grep -n "cloudflared tunnel" ~/.hermes20/scripts/*tunnel*.sh
ps -eo pid,args | grep cloudflared | grep -v grep

# 2. does the local app answer?
curl -s -o /dev/null -w "local=%{http_code}\n" http://127.0.0.1:8787/

# 3. does the tunnel URL answer, and with WHICH title?
U=$(cat ~/.hermes20/dashboard_url.txt)
curl -s -m 20 --compressed -D ~/tmp/h.txt "$U/" -o ~/tmp/t.html
grep -o "<title>[^<]*</title>" ~/tmp/t.html
grep -c "WATAK" ~/tmp/t.html        # 0 = you are serving the wrong app
```

If the title/tab markers do not match the app you edited, fix the tunnel target, not the UI.
Point the tunnel at the console port so "one place" really is one place.

### Pitfall: `/tmp` does not exist on Termux

`curl -o /tmp/t.html` fails with `curl: (23) Failed writing body`. Use `~/tmp/` (`mkdir -p ~/tmp`).

## 2. Symptom: tunnel URL returns 403 while localhost returns 200

The app had a Host allowlist middleware:

```python
ALLOWED_HOSTS = {"127.0.0.1:8787", "localhost:8787", ...}
if host not in ALLOWED_HOSTS and not LAN_TOKEN:
    return JSONResponse({"error": "host tidak dibenarkan"}, status_code=403)
```

`curl -H "Host: <random>.trycloudflare.com" http://127.0.0.1:8787/` reproduces the 403 locally —
that is the proof it is the allowlist, not the tunnel.

Fix: make the allowlist extensible from the environment, and accept the tunnel suffix:

```python
for _h in os.environ.get("CONSOLE_ALLOWED_HOSTS", "").split(","):
    _h = _h.strip().lower()
    if _h:
        ALLOWED_HOSTS.add(_h)
```

and in the guard:

```python
_tunnel = request.headers.get("host", "").lower().endswith(".trycloudflare.com")
if host not in ALLOWED_HOSTS and not _tunnel and not LAN_TOKEN:
    return JSONResponse({"error": "host tidak dibenarkan"}, status_code=403)
```

Also relax `ALLOWED_ORIGINS` for the same host, or POSTs are rejected even after GET works.
Security note: a public tunnel to a console with write endpoints is an unauthenticated control
panel — set a LAN token (`?t=<token>` → cookie) before publishing, or keep the tunnel as a
view-only fallback.

## 3. Symptom: light theme shows dark text on a dark background

The theme had a light-mode token block:

```css
body.light { --ink:#f4f4f6; ... }   /* tokens only */
```

but the dark rules were declared later with `!important` on the *element*:

```css
body { background: radial-gradient(...) #0b0b0c !important; }
```

So switching to light changed the text colour while the background stayed dark → invisible text.
Token overrides alone cannot beat an `!important` background rule.

**Rule: a light theme must reset the background in the same layer that sets the text.**

```css
body.light {
  background: radial-gradient(...) #f7f7f8 !important;
  color: #1a1a1a !important;
}
body.light .panel, body.light .card { background: #ffffff !important; color: #1a1a1a !important; }
body.light .muted, body.light .dim { color: #52525b !important; }
```

Then re-check every element that hardcodes a light colour (`#fff`, `#eee`) — those are the ones
that vanish on a light background. Bump the CSS URL (`theme.css?v=3`) so browsers do not serve
the cached old file.

**Verification that actually proves contrast** (do not rely on "looks fine"): read the computed
style of body and one panel after toggling the class, and assert the pair differs in luminance:

```python
# in the browser console / CDP
const b = getComputedStyle(document.body);
const p = getComputedStyle(document.querySelector('.panel'));
[b.backgroundColor, b.color, p.backgroundColor, p.color]
```

If `body` background and `body` colour are both dark, the light layer is still leaking.

## 4. Stale localStorage key beats every CSS fix

If the user still sees dark after the CSS default changed, the browser is re-applying a saved
preference. Version the storage key (`console_theme_v2`) so the old value is never read again.

## 5. Checklist before telling the user "fixed"

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8787/          # local 200
U=$(cat ~/.hermes20/dashboard_url.txt); curl -s -o /dev/null -w "%{http_code}\n" "$U/"   # tunnel 200
curl -s "$U/" | grep -c "WATAK"                                          # >0 = right app
curl -s "$U/" | grep -o 'theme.css?v=[0-9]*'                             # bumped version
```

Report the tunnel URL only after curling it in the same turn — a URL from an earlier run may
already be dead.

## 6. "One block still black" — sweep the stylesheet instead of guessing

When the user keeps circling **one** dark element after a light theme landed (status pills,
a chart, log/preview box), do not hand-pick selectors. The leftover is almost always a class
that has a hardcoded dark background in the base stylesheet and **no matching light override**.

Mechanical sweep (run it from the repo, no browser needed):

```python
import re, pathlib
base = pathlib.Path("static")
style = (base/"style.css").read_text()
theme = (base/"theme.css").read_text()
for sel, body in re.findall(r'([^{}]+)\{([^{}]*)\}', style):
    b = body.lower()
    if re.search(r'background[^;]*:(#0[0-9a-f]{2,5}|#1[0-9a-f]{2,5}|rgba\(0,\s*0,\s*0|rgba\(5,|rgba\(7,)', b):
        print(sel.strip())   # every rule with a near-black background
```

Then check each selector for an existing `body.light <sel>` rule in `theme.css`. Whatever is
missing is your culprit. Generate the missing overrides programmatically rather than by eye:

```
body.light <sel>{background:#ffffff!important;border-color:#e4e4e7!important;color:#18181b!important}
```

Interactive/selected states (`.on`, `.sel`, `:hover`, `:active`, `.over`) get a tinted variant
(`background:#ecfdf5!important;color:#14532d!important`) so state remains visible on white.

### Lessons that cost several rounds

- **Status pills** (`.chip-live`) were the last invisible block: translucent dark
  `rgba(5,12,10,.72)` plus dim text. A light theme must override the pill **and** its `b`
  child, plus `.warn` / `.bad` variants (amber-50 / red-50 backgrounds with dark text).
- **Inline SVG charts** (`renderChart` in JS) hardcode `fill="#0b1311"` etc. CSS cannot reach
  them. Move the palette to CSS variables (`--oc-node`, `--oc-text`, `--oc-link`, …) and emit
  `style="fill:var(--oc-node)"` instead of `fill="#hex"`. Define both dark and `body.light`
  values for every `--oc-*` token.
- **Never leave `body.light svg text{fill:#27272a}`**: dark text over still-dark chart rects is
  exactly the "blok hitam kosong" the user reports.
- **Inline `style="background:#0a1210"` in the HTML template** also survives theme switching.
  Either strip the inline colour or cover it with a `body.light input,body.light textarea`
  rule carrying `!important` (stylesheet `!important` beats inline styles).
- **`.bodytext` / `pre.log` previews** (daily report) have a fixed dark background + light
  green text in the base sheet: override both background and `color` or the report reads blank.
- After the sweep, bump the static version (`theme.css?v=N`, `app.js?v=N`) so the browser
  cannot serve the old sheet, and re-fetch the served CSS to confirm the new block exists:
  `curl -s "$U/static/theme.css?v=N" | grep -c 'TERANG v'`.
