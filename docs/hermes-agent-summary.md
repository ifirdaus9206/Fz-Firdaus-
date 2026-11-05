# Hermes Agent + Agency-E Agents: Summary & Guide

## Status: Installation Complete ✅

282 agents installed via agency-agents-router plugin.

## Plugin Configuration
- Plugin: `agency-agents-router`
- Location: `/data/data/com.termux/files/home/.hermes20/plugins/agency-agents-router/`
- Tools provided: 4 main tools
  - `agency_agents_search` - Search for agents
  - `agency_agents_inspect` - Inspect agent details
  - `agency_agents_load` - Load agent
  - `agency_agents_delegate` - Delegate work to agent

## Available Divisions (Categories)

| Division | Count | Example Agents |
|----------|-------|----------------|
| engineering | 65+ | frontend-developer, ai-engineer, backend-architect |
| design | 10 | ui-designer, visual-storyteller, whimsy-injector |
| academic | 6 | anthropologist, historian, researcher |
| finance | 5 | financial-analyst, fp-a-analyst, tax-strategist |
| game-development | 21 | game-designer, level-designer, narrative-designer |

## Concept: "One Project, One Persona"

Each project should use only ONE agent persona. Choose based on project needs:

### Agent Selection Guide:

| Project Type | Recommended Agent | Slug |
|-------------|------------------|------|
| Website/Frontend | Frontend Developer | `frontend-developer` |
| UI/UX Design | UI Designer | `ui-designer` |
| Mobile App | Mobile App Builder | `mobile-app-builder` |
| Code Review | Code Reviewer | `code-reviewer` |
| Research | Researcher | `researcher` |
| Financial Analysis | Financial Analyst | `financial-analyst` |
| Game Development | Game Designer | (game-development division) |

## How to Use Each Agent

### A) Search for an Agent:
```bash
hermes agency_agents_search --query "frontend developer"
```

### B) Inspect Agent Details:
```bash
hermes agency_agents_inspect --agent frontend-developer
# or using slug
hermes agency_agents_inspect --agent frontend-developer
```

### C) Delegate Task to Agent:
```bash
hermes agency_agents_delegate \
  --agent frontend-developer \
  --task "Buat README.md untuk projek React saya" \
  --context "Website portfolio dengan React dan TailwindCSS"
```

## How to Restart Hermes

### METHOD 1: Stop & Start Manual
```bash
hermes logout
hermes chat    # Start fresh session
```

### METHOD 2: Using Reset Command
```bash
hermes --reset    # atau hermes --restart
```

### METHOD 3: Session Recovery
```bash
hermes --resume <session_id>
# Contoh: hermes --resume 20261020_204339_a1b2c3
```

### METHOD 4: Re-enable Plugin
```bash
hermes config set plugins.enabled '[agency-agents-router]'
```

## Configuration File
- Location: `/data/data/com.termux/files/home/.hermes20/config.yaml`
- Current state shows: `agency-agents-router` already in `plugins.enabled`

## Quick Test: "One Project, One Persona"

**Step 1:** Choose agent (e.g., `frontend-developer` for web projects)
**Step 2:** Get agent details (use inspect)
**Step 3:** Give the agent one project task
**Step 4:** Receive output from the agent

**Example workflow:**
```bash
# Step 1: Select frontend-developer for a React project
# Step 2: Inspect the agent
hermes agency_agents_inspect --agent frontend-developer

# Step 3: Delegate the project task
hermes agency_agents_delegate \
  --agent frontend-developer \
  --task "Susunan struktur folder untuk aplikasi E-commerce React Native" \
  --context "Butuh folder: components, screens, services, utils, assets"
```

---

**Guide completed: All systems operational. Ready for agent delegation tasks.**