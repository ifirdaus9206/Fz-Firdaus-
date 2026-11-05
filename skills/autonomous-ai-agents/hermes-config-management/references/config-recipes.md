# Hermes Config Recipes

Copy-paste recipes. Substitute the config path that `hermes config show` prints — do not
hardcode `~/.hermes20` on another machine.

---

## 1. Point Hermes at a different default model

```bash
hermes config set model.default "deepseek/deepseek-v4.1-flash-1017"
hermes config set model.provider "openrouter"
hermes config set model.base_url "https://openrouter.ai/api/v1"
hermes config set model.api_mode "chat_completions"

hermes config get model.default
hermes -z "Reply with exactly: OK"
```

`api_mode: chat_completions` is the safe default for OpenRouter. Leave it alone unless the
provider needs the responses API.

---

## 2. Add a fallback chain (survives provider hiccups)

`hermes config set fallback_providers '[{...}]'` writes a **string**, and the reader
(`_iter_fallback_entries` in `hermes_cli/fallback_config.py`) rejects strings — it accepts only
`dict` or `list`. So the JSON form looks successful and does nothing. Write real YAML:

```bash
python3 - <<'PY'
import os, yaml
p = os.path.expanduser("~/.hermes20/config.yaml")
with open(p) as f:
    cfg = yaml.safe_load(f) or {}
cfg["fallback_providers"] = [
    {"provider": "openrouter", "model": "nvidia/nemotron-3-super-120b-a12b:free"},
    {"provider": "openrouter", "model": "openai/gpt-4o-mini"},
]
with open(p, "w") as f:
    yaml.safe_dump(cfg, f, sort_keys=False, default_flow_style=False)
PY

hermes config get fallback_providers     # must print a "- provider:" list, not one quoted blob
```

Optional per-entry fields: `base_url`, `api_key` (inline), `key_env` (name of env var holding
the key). Entries missing `provider` or `model` are silently dropped.

A single mapping also works:

```yaml
fallback_model:
  provider: openrouter
  model: openai/gpt-4o-mini
```

---

## 3. Diagnose an "Upstream idle timeout exceeded" loop

Symptom: `API call failed after 3 retries: Upstream idle timeout exceeded`, often after the
model had been working earlier in the session.

```bash
hermes config get model.default          # is it a :free or :beta id?
hermes config show | grep -i timeout     # terminal timeout is a different knob
```

Free-tier upstreams idle out on long generations. Two-part fix:

```bash
hermes config set model.default "<stable-model>"
# + fallback chain from recipe 2
hermes -z "Reply with exactly: OK"
```

Why it recurs after an in-session switch: `/model` inside a session is ephemeral. Only
`model.default` in `config.yaml` persists, so a session that "works now" will regress on the
next launch if the persisted default was never updated.

Do not chase this as a network or terminal-timeout problem. The terminal timeout in
`hermes config show` governs command execution, not model streaming.

---

## 4. Enable a plugin

```bash
hermes config get plugins.enabled          # current list
```

`plugins.enabled` is a list, so `hermes config set` will stringify it — use the python3 YAML
pattern:

```bash
python3 - <<'PY'
import os, yaml
p = os.path.expanduser("~/.hermes20/config.yaml")
with open(p) as f:
    cfg = yaml.safe_load(f) or {}
plugins = cfg.setdefault("plugins", {})
enabled = plugins.setdefault("enabled", [])
if "agency-agents-router" not in enabled:
    enabled.append("agency-agents-router")
with open(p, "w") as f:
    yaml.safe_dump(cfg, f, sort_keys=False, default_flow_style=False)
PY

hermes doctor        # confirms the plugin is discovered
hermes tools         # its toolset should appear
```

---

## 5. Non-interactive one-shots (for smoke tests and cron-style checks)

```bash
hermes -z "Reply with exactly: OK"      # -z is the one-shot prompt flag
hermes -z "Reply with exactly: OK" -m "openai/gpt-4o-mini"     # override model for one call
hermes -z "..." -t "web,terminal"                              # restrict toolsets
```

`hermes -p` is not a flag — it is parsed as a subcommand and errors with
`invalid choice: 'Reply with exactly: OK'`. The `--help` list confirms `-z PROMPT`.

---

## 6. Reading the config without the CLI

```bash
python3 -c 'import yaml,os;print(yaml.safe_dump(yaml.safe_load(open(os.path.expanduser("~/.hermes20/config.yaml"))),sort_keys=False))'
```

Useful when `hermes config get <dotted.key>` says `Config key not set` and you want to see the
actual tree, or to check whether a value landed as a string instead of a list.

---

## 7. Backup discipline for anything under the Hermes home

```bash
cp ~/.hermes20/SOUL.md ~/.hermes20/SOUL.md.bak        # right after generating it
cp -r src dest/                                        # NO: silently clobbers matches
rsync -av --ignore-existing src/ dest/                 # YES: merge without overwriting
```

Collision pre-check before any bulk copy:

```bash
for f in src/*; do [ -e "dest/$(basename "$f")" ] && echo "COLLISION: $f"; done
```

Verify content after every write — size alone hides a downgrade:

```bash
ls -la dest/SOUL.md
head -2 dest/SOUL.md
tail -3 dest/SOUL.md
```
