# Retiring a second instance (zombie homes, ports, and pills)

One codebase can serve several `HERMES_HOME`s on different ports
(`CONSOLE_PORT`, `CONSOLE_DEFAULT_HOME`, `CONSOLE_HOMES`). Deleting one home **does not** remove
it from the console: the UI keeps advertising a dead instance and the operator reads that as
"you did not delete it". Measured case: `~/.hermes19` removed, yet the HUD still showed a
`HERMES19 · MATI` pill, `/api/fleet` still returned a `hermes19 · Trading` gateway, and
`start_all.sh` still tried to boot a 8790 that no longer had a script.

## The five places a retired instance hides

| Place | Symptom | Fix |
|---|---|---|
| HUD / sidebar markup | permanent `MATI` pill | delete the `<span class="pill">…</span>` from `index.html` |
| Loader that fills it | `set("hud-gw2", …)` writes to a missing node | leave (guarded by `if (el)`) or remove |
| `/api/fleet` (or equivalent) | returns the dead home in the list | build the list conditionally |
| Start / stop scripts | `start19()` boots a path that no longer exists; `PORTS=[8787,8790]` | rewrite for the surviving port only |
| Plan / docs | operators re-provision the dead thing | banner the section as historical |

## API: filter by "does the home exist and is it non-empty"

```python
_gw = [gateway("hermes20 · Ketua", h20, "hermes-source.*gateway|hermes gateway")]
# hermes19 sudah dipadam — jangan papar jika home tiada
if h19.is_dir() and any(h19.iterdir()):
    _gw.append(gateway("hermes19 · Trading", h19, "HERMES_HOME=.*hermes19|hermes19"))
return {
    "gateways": _gw,
    "skills": {"hermes20": skills(h20 / "skills"),
               "hermes19": skills(h19 / "skills") if h19.is_dir() else 0},
}
```

`any(h19.iterdir())` matters: an empty directory left behind by a partial delete still exists,
and `is_dir()` alone would keep showing the pill. On Termux `ls -A <dir> | wc -l` printing `1`
(just `..`) is the same signal.

## Scripts: remove the port, not just the branch

`start_all.sh` and `stop_server.py` are the usual stragglers:

- rewrite `PORTS = [8787, 8790]` → `PORTS = [8787]  # 8790 dibersarakan (hermes19 dipadam)`
- delete the `start19()`/`ping_ok 8790` branches and the "wait for both" loop
- keep a one-line comment in each file saying *when* and *why* it was retired — otherwise the
  next reader re-adds it

## Docs: banner, don't rewrite history

A plan file that still documents the two-instance design is useful archaeology. Add a banner at
the top of that section rather than deleting the rows:

```markdown
> **STATUS 2026-11-24 — BAHAGIAN INI SEJARAH SAHAJA.**
> `hermes19` sudah dipadam sepenuhnya. Port **8790 dibersarakan**; hanya **8787**
> yang digunakan. Jangan hidupkan semula 8790 atau `~/.hermes19`.
```

Leave the remaining `8790` strings only where they are *explanatory comments* — then say so
explicitly in the report, because a bare `grep 8790` still finds them and the operator will ask.

## Verification (paste raw output)

```bash
for p in 8787 8790; do printf "%s=" "$p"; curl -s -o /dev/null -w '%{http_code}\n' -m 3 http://127.0.0.1:$p/ || echo 000; done
curl -s http://127.0.0.1:8787/api/fleet | python3 -c "import sys,json;d=json.load(sys.stdin);print([g['name'] for g in d['gateways']])"
bash -n tools/start_all.sh && python3 -c "import ast;ast.parse(open('tools/stop_server.py').read())"
grep -n '8790' tools/start_all.sh tools/stop_server.py app.py | grep -v 'dibersarakan'
```

Expect `8787=200`, `8790=000`, the fleet list containing **only** the surviving home, and the
last grep printing nothing.

## Wave-lock / supervisor is not per-port

A keeper service ("Penjaga") usually holds the wake-lock and re-`sv up`s the console and gateway
every 60s, checking **one** health URL. When a port is retired the keeper needs no change —
confirm it references only the surviving port (`grep -n '8787\|8790' scripts/keeper.sh`) and tell
the operator that one keeper is enough for one console. Do not add a second keeper per instance.
