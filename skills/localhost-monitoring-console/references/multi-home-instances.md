# Multi-home instances of one console

Context from a real request: *"selepas mulakan di hermes19 jalankan"* — run the same console for a
second Hermes home (a trading desk) with its own default tab, without forking the code or the UI.

## Principle

One project directory, one `app.py`, one `static/`. The *context* (which home is selected, which
homes the UI is allowed to see, which tab opens first, which port) is environment configuration.
A per-home launcher script is 8 lines and can live inside that home (`~/.hermesNN/console.sh`).

## Environment contract

| Var | Default | Effect |
|---|---|---|
| `CONSOLE_DEFAULT_HOME` | `hermes20` | home preselected at boot; echoed by `/api/meta` |
| `CONSOLE_HOMES` | empty (all) | comma list filtering `/api/meta.homes` |
| `CONSOLE_DEFAULT_TAB` | `pusat` | tab opened first (`trading`, `kerja`, …) |
| `CONSOLE_PORT` | `8787` | distinct port per instance |
| `CONSOLE_HOST` | `127.0.0.1` | `0.0.0.0` only with LAN token |
| `HERMES_HOME` | — | set by launcher, for anything else in-process |

Backend:

```python
DEFAULT_HOME = os.environ.get("CONSOLE_DEFAULT_HOME", "hermes20").strip() or "hermes20"
DEFAULT_TAB  = os.environ.get("CONSOLE_DEFAULT_TAB", "pusat").strip() or "pusat"
ONLY_HOMES   = [x.strip() for x in os.environ.get("CONSOLE_HOMES", "").split(",") if x.strip()]

@app.get("/api/meta")
def api_meta():
    return {
        "default_home": DEFAULT_HOME if DEFAULT_HOME in HOMES else "hermes20",
        "default_tab": DEFAULT_TAB,
        "homes": [h for h in REG["homes"] if not ONLY_HOMES or h["key"] in ONLY_HOMES],
        ...
    }
```

Keep the full `HOMES` registry server-side for path resolution; filtering the meta list only hides
the switcher. If the restricted instance must not answer for another home at all, reject in each
`home`-taking endpoint:

```python
if ONLY_HOMES and home not in ONLY_HOMES:
    raise HTTPException(404, "home tidak tersedia pada instance ini")
```

## Frontend boot ordering (the blank-pane trap)

```js
S.meta = await api("/api/meta");
S.home = S.pendingHome || S.meta.default_home || "hermes20";
S.tab  = S.pendingHome ? "pusat" : (S.meta.default_tab || "pusat");
...
setTab(S.tab);          // NOT loadTab()
```

`setTab` toggles the `.active` class on the tab buttons *and* calls `loadTab()`. Calling `loadTab()`
directly leaves the HTML's original `active` class (e.g. PUSAT highlighted) while the JS state has
moved on, so the visible pane stays empty until the user clicks a tab. Symptom seen in the DOM-shim
test: `#hl-chips` empty and `#oc-meta` blank even though the API worked.

Also seed `S.tab` before binding the 15 s auto-refresh, or the first tick can re-render the wrong tab.

## Launcher

See `templates/console_instance.sh`. It exports the vars and `exec`s the shared `run.sh`; `run.sh`
probes `127.0.0.1:$CONSOLE_PORT/api/ping`, so an instance only detects itself.

## Verification matrix (two live instances)

```bash
# main
curl -s http://127.0.0.1:8787/api/meta | jq '{default_home,default_tab,homes:[.homes[].key]}'
#   -> hermes20 / pusat / ["hermes20","hermes19"]

# second home (launched by ~/.hermes19/console.sh)
curl -s http://127.0.0.1:8790/api/meta | jq '{default_home,default_tab,homes:[.homes[].key]}'
#   -> hermes19 / trading / ["hermes19"]

curl -s http://127.0.0.1:8790/api/trading | jq '{symbols:(.symbols|length),decisions:(.decisions|length)}'
curl -s "http://127.0.0.1:8790/api/overview?home=hermes19" | jq '{sessions:.totals.sessions,model}'
grep -ci traceback ~/.hermes19/console.log      # must be 0
```

Both instances may run simultaneously; they only need distinct ports. History/inbox/reports stay
shared because they describe the same fleet — say so explicitly rather than duplicating state.

## Image thumbnails (same round)

- `GET /api/inbox/{id}/file` already streams with the stored content-type; render
  `<img class="thumb" loading="lazy" src="/api/inbox/<id>/file">`, CSS
  `.thumb{width:64px;height:64px;object-fit:cover;border-radius:6px}`.
- Agent drawer: extend `/api/agent-live/{slug}` with
  `run.attachments = [{id, filename, kind, bytes}]`, then draw a "Lampiran run (N)" strip:
  thumbnails for `kind=image`, `📎 filename` chips for the rest, all linked to the file endpoint.
  Render nothing when the list is empty.
- A 1×1 test PNG (70 bytes) proves storage/serving, not layout — check the CSS in context.

## Pitfalls specific to this mode

- Two instances on the same port: the second bind raises `[Errno 98] address already in use`, and
  the `server.pid` it wrote before dying stays behind. Confirm liveness with `/api/meta`
  (`default_home` proves *which* instance) instead of trusting the pid file.
- A filtered instance still serves `/api/agency` etc. from the Ketua home (the roster is a
  catalogue, not per-home state). That is fine; don't "fix" it by copying the catalogue.
- Do not clone the project per home. If you feel tempted, the thing you actually need is another
  env var.
