# Hermes Desktop integration — runtime plugins (no core fork)

Goal: the same localhost console appears **inside** the Hermes Desktop app (Electron)
without forking `apps/desktop`. Verified against Hermes v0.20.0 source at
`~/.hermes20/tools/hermes-source/apps/desktop`.

## Decision rule (state it before building)

| Option | Verdict |
|---|---|
| Fork `apps/desktop`, paste the page in | No — every `hermes update` conflicts |
| Re-implement the UI in React desktop | No — two sources of truth, guaranteed drift |
| **Runtime plugin in `<hermes home>/desktop-plugins/<name>/plugin.js` + embed the console** | **Yes** — official loader door, zero core edits, one UI |

The repo's own `AGENTS.md` says capability belongs at the edges and plugins must not
touch core files; quoting that settles the design argument.

## How the loader works (so you match it exactly)

`apps/desktop/src/contrib/runtime-loader.ts` + `contrib/plugins.ts`:

1. scan `<hermes home>/desktop-plugins/<name>/plugin.js`
2. rewrite bare import specifiers to live shim blobs
3. `import()` the blob, validate `default` export
4. call `register(ctx)`, auto-tagging `source: 'plugin:<id>'`

Allowed bare specifiers — **only these four**:
`@hermes/plugin-sdk`, `react`, `react/jsx-runtime`, `react/jsx-dev-runtime`.
Relative imports are NOT resolved: keep the plugin a single self-contained file.

Consequence: no bundler, no JSX syntax. Use `jsx()` / `jsxs()` calls and inline
`style` objects (Tailwind classes also work but inline styles survive theme changes).

## Plugin contract

```js
import { PALETTE_AREA, ROUTES_AREA, SIDEBAR_NAV_AREA, host } from '@hermes/plugin-sdk'
import { jsx, jsxs } from 'react/jsx-runtime'
import { useCallback, useEffect, useState } from 'react'

export default {
  id: 'hermes-console',          // becomes plugin:<id> and the id namespace
  name: 'Hermes Console',
  defaultEnabled: true,
  register(ctx) {
    ctx.registerMany([
      { id: 'page', area: ROUTES_AREA, title: 'Console',
        data: { path: '/console' }, render: () => jsx(ConsolePage, {}) },
      { id: 'nav', area: SIDEBAR_NAV_AREA, order: 60,
        data: { codicon: 'pulse', label: 'Console', path: '/console' } },
      { id: 'pill', area: 'statusBar.right', order: 90, render: () => jsx(Pill, {}) },
      { id: 'open', area: PALETTE_AREA,
        data: { id: 'console.open', label: 'Console: Buka papan pemantau',
                keywords: ['console'], run: () => host.navigate('/console') } }
    ])
  }
}
```

`ctx` surface actually needed: `register/registerMany`, `onDispose`, `os`
(`openExternal`, `writeClipboard`, `revealPath`, `notify`), `storage`
(`get/set/remove`), plus `rest`/`socket` for a plugin backend namespace (not needed
for an iframe). `host.navigate(path)` moves the shell; `host.state.gateway` is an atom.

Page contributions need `data: { path: '/one-segment' }` — no params, and the path
must not collide with a reserved core route.

## Embedding the console (server side)

1. `?embed=1` → add `body.embed`; hide brand / home switcher / clock, tighten padding,
   shorten `.scroll` max-height. The console then looks like part of the shell.
2. CSP: `frame-ancestors 'self' file: app: http://localhost:5174 http://127.0.0.1:5174`.
3. **Remove `X-Frame-Options: DENY`** — it contradicts the CSP and blocks the Electron
   host outright. Keep CSP as the single framing control.
4. Add `GET /api/ping` returning `{ok:true,...}` with `Access-Control-Allow-Origin: *`
   (GET only, no data) so the plugin can show a live/dead dot via cross-origin `fetch`.
   A `file://` renderer sends `Origin: null`; a wildcard on this one endpoint is fine.
5. Plugin page = status bar (dot + host label + **Muat semula** + **Pelayar**) over
   `<iframe src="…/?embed=1">`; when ping is down render a "start the server" panel
   with the copy-command button instead of a blank frame.
6. Remote desktop (different machine): store the base URL in `ctx.storage` and expose a
   palette command that prompts and saves it. Default `http://127.0.0.1:8787`; console
   still binds loopback unless the user deliberately exposes it.

## Verifying without Electron (mandatory on Termux/Android)

There is no Electron runtime for Android — you cannot boot the desktop app there.
Do not claim runtime verification. Instead run two checks that exercise the real
contract, and say plainly in the report that the Electron run is unverified.

- `scripts/validate_desktop_plugin.py` — copies the plugin to `.mjs` and runs
  `node --check`; verifies bare specifiers ⊆ the four allowed, no relative imports,
  `export default {` with `id` + `register(ctx)`, areas ∈ known set (map constants:
  `ROUTES_AREA→routes`, `SIDEBAR_NAV_AREA→sidebar.nav`, `PALETTE_AREA→palette`),
  and that a `/path` is registered.
- `scripts/desktop_plugin_harness.mjs` — mirrors the loader: rewrite specifiers to stub
  files, import the module, build a fake `ctx` (register/registerMany/onDispose/storage/os),
  call `register(ctx)`, then render each function component recursively and assert the
  page tree contains an `iframe` whose `src` matches `<base>/?embed=1`.

Grep proof that the door is real:
`grep -rn "desktop-plugins" apps/desktop/src apps/desktop/electron` → hits in
`contrib/runtime-loader.ts`, `contrib/plugins.ts`, `contrib/controller.tsx`.

## Evidence to quote in the report

- validator: N/N OK, LULUS
- harness: N/N OK — contributions by area, iframe src string
- `curl -sI` on `/`: `frame-ancestors 'self' file: app: …`, no `x-frame-options`
- `curl` on `/api/ping`: 200 + `access-control-allow-origin: *`
- existing `render_test.js` still green (the console must not regress for browser use)
