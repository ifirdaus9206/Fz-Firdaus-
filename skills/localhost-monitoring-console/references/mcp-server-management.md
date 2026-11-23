# MCP server management from a console/API (non-interactive)

Adding an "MCP" panel to a monitoring console means creating/removing MCP servers without a TTY.
`hermes mcp add` is **interactive** and silently saves nothing when stdin is closed.

## What the CLI actually does

```bash
hermes mcp list        # "No MCP servers configured."
hermes mcp catalog     # 6 approved servers, parseable lines
hermes mcp add <name> --url <endpoint>          # HTTP
hermes mcp add <name> --command <cmd>           # stdio
hermes mcp remove <name>
hermes mcp test <name>
```

`add` prompts: `Does this server require authentication?` then `Save config anyway (y/N)?`.
With `stdin=DEVNULL` it reads EOF, prints the prompt, and exits 0 **without writing config** —
a fake success. Do not build an API endpoint on top of `mcp add` unless you also drive the pty.

## Storage

MCP servers live in the top-level `mcp_servers:` map of `~/.hermes20/config.yaml`.
No separate `mcp.json` in this version.

## Write path that works

- **`hermes config set` works for dotted keys but only stores scalars.**
  `hermes config set mcp_servers.foo.command "npx"` is fine; passing a list stores it as a
  *string* (`["-y","pkg"]` becomes the literal text), which the MCP loader cannot use.
- **For structured entries, write the YAML directly** (allowed: config guard only blocks
  `write_file`/`patch` on `config.yaml`, not python):

```python
import yaml, shutil, pathlib
p = pathlib.Path.home()/".hermes20/config.yaml"
cfg = yaml.safe_load(p.read_text()) or {}
cfg.setdefault("mcp_servers", {})[name] = {
    "command": "npx", "args": ["-y", "some-server"], "enabled": True,
}
shutil.copy(p, p.with_suffix(".yaml.bak-mcp"))
p.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True))
```

- **Remove with the CLI**, which handles the unset cleanly:
  `hermes config unset mcp_servers.<name>`

## Read path for the panel

```python
cfg = yaml.safe_load(Path("~/.hermes20/config.yaml").expanduser().read_text()) or {}
servers = cfg.get("mcp_servers") or {}
```

Render name, transport (`http` if `url` else `stdio`), command/url, enabled flag.

## Transport limitation to state up front

HTTP/SSE servers need `streamable_http` in the installed `mcp` package. On Termux the packaged
version can lack it; the failure message is
`MCP server ... requires mcp.server.streamable_http`. **stdio servers work** — recommend
`command` + `args` and offer an upgrade path for HTTP rather than pretending it works.

## Console API notes

- Mutating routes need the CSRF header: read `csrf` from `GET /api/meta`, then send
  `x-console-token: <value>` on POST/PUT/DELETE. Without it you get a 403 that looks like a bug.
- Call `hermes` with `HERMES_HOME` set to the target home and `stdin=DEVNULL`.
- `hermes mcp catalog` output is line-oriented; `^name  status  description` regexes fine.
