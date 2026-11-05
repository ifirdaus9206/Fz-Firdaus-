# Installation Recipes for Hermes Agency Integration

## Termux (Android) - Script Method (No Homebrew)

This recipe covers installing The Agency agents via scripts when Homebrew is unavailable.

### Prerequisites
- Termux on Android (aarch64 Linux environment)
- Git installed (`pkg install git`)
- Hermes Agent already installed

### Step-by-Step

```bash
# 1. Clone the agency-agents repository
git clone https://github.com/msitarzewski/agency-agents.git ~/agency-agents

# 2. Navigate into the repo
cd ~/agency-agents

# 3. Install Hermes integration (no-interactive mode skips wizard)
./scripts/install.sh --tool hermes --no-interactive

# Expected output:
# The Agency -- Installing agents
#   Repo:       /data/data/com.termux/files/home/agency-agents
#   Installing: hermes
#
#   [====================] 1/1
#
#   [1/1] hermes
#   [!!]  hermes: integration files missing — running convert.sh --tool hermes
#   [OK]  hermes: generated integration files
#   [OK]  Hermes: enabled plugin agency-agents-router in config.yaml
#   [OK]  Hermes: lazy-router plugin (282 agents on disk) -> ~/.hermes20/plugins/agency-agents-router
#   [!!]  Hermes: restart sessions/gateway so the new plugin toolset is discovered.

# 4. Verify plugin in config
cat ~/.hermes20/config.yaml
# Should show:
# plugins:
#   enabled:
#     - agency-agents-router

# 5. Restart Hermes
hermes doctor

# 6. Test agent accessibility
hermes chat --query "list agency agents"
# Should return 192+ agents available
```

### Troubleshooting

| Issue | Resolution |
|-------|------------|
| `brew: command not found` | Use script method — Homebrew not available in Termux |
| Plugin not discovered after restart | Run `hermes doctor`; verify `agency-agents-router` in `~/.hermes20/config.yaml` |
| Convert script failed | Run `./scripts/convert.sh --tool hermes` manually |
| Agents not appearing in chat | Confirm Hermes session restarted after plugin installation |
| `hermes tools` doesn't show agency toolset | Check `~/.hermes20/plugins/agency-agents-router/` exists |

### Post-Installation Verification

```bash
# List available agents
hermes --dev chat --query "list agency agents"

# Search for specific agent type
hermes --dev chat --query "search agent frontend developer"

# Inspect a specific agent
hermes --dev chat --query "inspect agent anthropologist"
```

## macOS with Homebrew

```bash
brew tap msitarzewski/agency-agents
brew install --cask agency-agents
# Then restart Hermes to discover the plugin
```

## Linux / macOS (Generic Script Method)

Works universally without Homebrew — same steps as Termux.