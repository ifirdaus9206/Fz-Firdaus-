# SOUL.md Creation from Agency Agents Repository

## Overview
Created a comprehensive registry file (SOUL.md) capturing all 266 agents from the agency-agents repository, organized by 17 divisions, with NEXUS orchestration doctrine and contributing principles.

## Process

### 1. Discover All Agent Files
```bash
# Find all markdown files in the repo
search_files(pattern="*.md", target="files", path="/data/data/com.termux/files/home/agency-agents")
# Returns 328 files (266 agents + docs, integrations, examples, strategy)
```

### 2. Count Agents Per Division
```python
# Script to scan division folders and count .md files
agent_dirs = [
    "engineering", "design", "paid-media", "sales", "marketing", 
    "product", "project-management", "testing", "security", "support",
    "spatial-computing", "specialized", "finance", "game-development",
    "academic", "healthcare", "gis"
]
# Results: 266 total agents across 17 divisions
```

### 3. Read Key Source Files
- `CONTRIBUTING.md` — Agent design guidelines, template structure, tool integrations
- `README.md` — Complete roster table, quick start, installation commands
- `strategy/nexus-strategy.md` — 7-phase pipeline, command structure, activation modes
- Sample agents (Frontend Developer, Reddit Community Builder, Whimsy Injector, Chief of Staff, Backend Architect, Mobile App Builder, AI Engineer) — understand structure

### 4. Generate SOUL.md Structure
```markdown
# SOUL.md — The Agency's Collective Consciousness
## Complete Registry of All 266 Specialized AI Agents

Sections:
1. Agency Overview (table: division, count, focus)
2. Complete Agent Registry (by division with emoji, color, specialty)
3. NEXUS Strategy (7-phase pipeline, command structure, activation modes)
4. Contributing Principles (from CONTRIBUTING.md)
5. Tool Integrations (13 supported tools)
6. Quick Reference: Agent Activation Triggers
7. Core Philosophy
8. Usage Guide
```

### 5. Deploy to Hermes
```bash
# Copy to Hermes config directory
cp SOUL.md ~/.hermes20/SOUL.md

# Copy entire agency-agents repo for local access
cp -r ~/agency-agents ~/.hermes20/agency-agents

# Remove original (cleanup)
rm -rf ~/agency-agents
```

## Resulting Files
- `~/.hermes20/SOUL.md` — 49KB, 669 lines, complete agent registry
- `~/.hermes20/agency-agents/` — Full repo copy (all 266 agent files + docs)

## Usage in Hermes
- SOUL.md serves as canonical registry for all agents
- Local repo copy enables direct file access without GitHub
- Can be used with agency-agents-router plugin for agent discovery
- Supports NEXUS multi-agent orchestration workflows