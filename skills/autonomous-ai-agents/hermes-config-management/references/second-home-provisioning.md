# Second functional Hermes home — verified recipe

Verified on Termux/Android (2026-10-22): turning `~/.hermes19` from a plain storage folder into a home
that holds a real conversation, while `~/.hermes20` stays primary.

## Why a copied directory is not a home

A home needs four things: `config.yaml` (settings), `.env` (secrets), `auth.json` (OAuth/credential
pools), and `skills/` (plus an optional `SOUL.md`). A directory missing `.env`/`auth.json` parses fine
and then cannot answer; a home with no skills has no procedures; a home with no `SOUL.md` has no
identity for its purpose.

## Exact sequence

```bash
H=$HOME/.hermes19
mkdir -p "$H"

# 1. secrets + credentials (never in config.yaml)
cp $HOME/.hermes20/.env       "$H/.env"
cp $HOME/.hermes20/auth.json  "$H/auth.json"
chmod 600 "$H/.env" "$H/auth.json"

# 2. config — `hermes config set` creates the file itself, so the write guard never fires
export HERMES_HOME="$H"
hermes config set model.default  deepseek/deepseek-v4.1-flash-1017
hermes config set model.provider openrouter
hermes config set model.base_url https://openrouter.ai/api/v1
hermes config set model.api_mode chat_completions
hermes config set agent.max_turns 150

# 3. nested lists need real YAML (config set stringifies JSON -> silently ignored)
python3 - <<'PY'
import os, yaml
p = os.path.expanduser("~/.hermes19/config.yaml")
d = yaml.safe_load(open(p)) or {}
d["fallback_providers"] = [
    {"provider": "openrouter", "model": "nvidia/nemotron-3-super-120b-a12b:free"},
    {"provider": "openrouter", "model": "openai/gpt-4o-mini"},
]
d["display"] = {"tool_progress": "all"}
yaml.safe_dump(d, open(p, "w"), sort_keys=False)
PY

# 4. only the skills that home needs (purpose-scoped, not a mirror of the main home)
mkdir -p "$H/skills/trading-systems" "$H/skills/research"
cp -a $HOME/.hermes20/skills/trading-systems/. "$H/skills/trading-systems/"
for s in arxiv polymarket grounded-citations; do
  cp -a $HOME/.hermes20/skills/research/$s "$H/skills/research/"
done

# 5. write a purpose-specific SOUL.md (identity, rules, output format) — do not copy the other home's
```

## Verification ladder — each rung proves a different layer

```bash
HERMES_HOME=$H hermes doctor            # python, venv, SSL, config parse
HERMES_HOME=$H hermes skills list       # also initialises the Skills Hub dir on first run
HERMES_HOME=$H hermes plugins list      # scripted-safe alternative to `hermes tools`
HERMES_HOME=$H hermes chat -q "Ikut SOUL.md awak: sebut <fakta yang hanya ada dalam SOUL.md>"
```

The last rung is the real proof: it exercises provider credentials **and** shows the home's own
`SOUL.md` was loaded, because the answer can only quote facts that exist in that file. `hermes doctor`
passing says nothing about the model path.

## Wrapper on PATH

`~/bin` was not on `PATH` in this environment; `~/.hermes20/bin` was. Put wrappers where `PATH`
already points:

```bash
cat > $HOME/.hermes20/bin/hermes19 <<'SH'
#!/usr/bin/env bash
HERMES_HOME="$HOME/.hermes19" "$HOME/.hermes_venvs/hermes19/bin/hermes" "$@"
SH
chmod +x $HOME/.hermes20/bin/hermes19
command -v hermes19 && hermes19 --version
```

## Gotchas

- `hermes tools` exits with `requires an interactive terminal` when piped. Not a broken install —
  use `hermes plugins list` / `hermes doctor` in scripts.
- `hermes doctor` will show warnings for unset tool keys (`EXA_API_KEY`, `DISCORD_BOT_TOKEN`, …).
  Compare against the source home: if it has the same gaps, nothing regressed.
- Filtered agent rosters in a second home: see the agency-agents integration skill
  (`scoped-roster-per-home.md`) — copy the plugin skeleton, then rebuild `data/agents.json` with only
  the chosen agents.
