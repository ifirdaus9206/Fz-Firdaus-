# MCP servers in config.yaml (and why `hermes mcp add` is a trap in automation)

MCP servers are stored as a **top-level `mcp_servers:` map** in the live `config.yaml`
(there is no separate `mcp.json` in this version).

```yaml
mcp_servers:
  filesystem:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/sdcard"]
    enabled: true
  remote:
    url: https://example.com/mcp
    enabled: true
```

## `hermes mcp add` is interactive — do not script it

```bash
hermes mcp list        # "No MCP servers configured."
hermes mcp catalog     # approved servers, line-oriented: name  status  description
hermes mcp add <name> --url <endpoint>
hermes mcp add <name> --command <cmd> --args <...>
hermes mcp remove <name>
hermes mcp test <name>
```

`add` prompts twice: `Does this server require authentication?` and
`Save config anyway (y/N)?`. Run with `stdin=DEVNULL` and it reads EOF, prints the prompt,
exits **0**, and writes nothing. That is a false success — the server never appears in
`mcp list`. If an API/panel needs to create servers, bypass `add` and write the YAML.

## Write path

`hermes config set` works for dotted keys but **stringifies values** — a list written that way
becomes the literal text `["-y","pkg"]`, which the loader cannot use. Same failure mode as
`fallback_providers`. Use python3 + PyYAML for structured entries:

```python
import yaml, shutil, pathlib
p = pathlib.Path("/data/data/com.termux/files/home/.hermes20/config.yaml")
cfg = yaml.safe_load(p.read_text()) or {}
cfg.setdefault("mcp_servers", {})[name] = {
    "command": "npx", "args": ["-y", "pkg"], "enabled": True,
}
shutil.copy(p, p.with_suffix(".yaml.bak-mcp"))
p.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True))
```

Remove with the CLI: `hermes config unset mcp_servers.<name>` — cleaner than editing the map.
Read back with `yaml.safe_load(...).get("mcp_servers")` to render a list.

## Transport limitation

HTTP/SSE servers need `streamable_http` in the installed `mcp` package. When it is missing the
error is `MCP server ... requires mcp.server.streamable_http` and the server is unusable even
though the config is valid. stdio (`command` + `args`) works without it — recommend stdio and
offer an upgrade path for HTTP instead of claiming both work.

## Restart semantics

MCP servers are read at process start. After adding one, the running gateway/cron/desktop does
not see it until restarted — same file-vs-runtime split as the rest of this skill.
