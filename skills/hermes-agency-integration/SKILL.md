---
name: hermes-agency-integration
description: Integration of Agency Agents with Hermes Agent.
version: 1.0.0
author: Hermes Agent + Nous Research
license: MIT
platforms: [linux, macos, windows, termux]
metadata:
  hermes:
    tags: [hermes, agency, agents, integration, installation, scripts]
    related_skills: [hermes-agent]
---
# Hermes Agency Agents Integration

This skill covers integrating The Agency agent roster with Hermes Agent, enabling use of 282+ specialized AI agents with personalities, processes, and deliverables.

## Quick Start

### Option 1: Native app (recommended)
Visit [agencyagents.app](https://agencyagents.app) for the native desktop app (macOS, Linux, Windows) — no clone, no terminal, auto-updates.

### Option 2: Script-based installation
```bash
git clone https://github.com/msitarzewski/agency-agents.git
cd agency-agents
./scripts/install.sh --tool hermes --no-interactive
```

## Platform Notes

### Termux (Android)
Homebrew is unavailable. Use the script method — it works on Termux's aarch64 Linux environment.

**What we learned**: In Termux, `brew install --cask msitarzewski/agency-agents/agency-agents` will NOT work because Homebrew is not installed. The script-based installation is the correct method:

```bash
git clone https://github.com/msitarzewski/agency-agents.git ~/agency-agents
cd ~/agency-agents
./scripts/install.sh --tool hermes --no-interactive
```

This clones the repo, runs the install script which generates integration files, and enables the `agency-agents-router` plugin in your Hermes config.

### macOS with Homebrew
```bash
brew tap msitarzewski/agency-agents
brew install --cask agency-agents
```

## Installation Steps (Termux/Linux)

1. Clone repo: `git clone https://github.com/msitarzewski/agency-agents.git ~/agency-agents`
2. Install: `cd ~/agency-agents && ./scripts/install.sh --tool hermes --no-interactive`
3. Verify: Check `~/.hermes20/config.yaml` has `agency-agents-router` in `plugins.enabled`
4. Restart: `hermes doctor` or restart session/gateway
5. Test: `hermes chat --query "list agency agents"` — should show 192+ agents

## Plugin Details

The `agency-agents-router` plugin provides 4 tools:
- `agency_agents_search` — Search agents by name/division/capabilities
- `agency_agents_inspect` — View detailed agent info
- `agency_agents_load` — Load agent personality and workflow
- `agency_agents_delegate` — Delegate tasks to specific agent

Installed at: `~/.hermes20/plugins/agency-agents-router/`
Agent data: `~/.hermes20/plugins/agency-agents-router/data/agents.json` (282 agents)

## Troubleshooting

- **Plugin not discovered**: Ensure `agency-agents-router` is in `config.yaml` under `plugins.enabled`; run `hermes doctor`
- **Convert failed**: Run `./scripts/convert.sh --tool hermes`
- **Agents not appearing**: Confirm Hermes restarted after installation; check `hermes tools` shows agency toolset

## References

- Agency Agents App: https://agencyagents.app
- GitHub: https://github.com/msitarzewski/agency-agents
- Hermes Docs: https://hermes-agent.nousresearch.com/docs/

## Local Knowledge Files

- `references/installation-recipes.md` — Platform-specific install recipes (Termux, macOS, Linux)
- `references/soul-md-creation.md` — Process for creating SOUL.md registry from agency-agents repo