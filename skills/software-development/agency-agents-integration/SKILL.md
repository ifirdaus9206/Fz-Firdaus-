---
name: agency-agents-integration
description: Integrate agency agent content into SOUL.md and profile.md
version: 1.0.0
author: Hermes Agent
license: MIT
categories: [software-development, ai-assistants]
---

# Agency Agents Integration

**Trigger:** Use when user requests search of agency agent files and needs guidance on which agents are suitable for SOUL.md identity sections and profile.md role definitions.

**Overview:** This skill provides a methodology for searching, selecting, and integrating content from the `agency-agents` directory into personal AI assistant files (SOUL.md and profile.md). It is useful for agents operating in multi-agent systems or users who want to adopt specialized agent personas.

**Steps:**
1. **Directory Exploration:** Navigate to agency-agents and list specialized agents: `ls agency-agents/specialized/`
2. **Agent Selection:** Review agents for SOUL.md (rich identity/mission/rules) vs profile.md (role/specialization/methods/metrics)
3. **Recommended for SOUL.md:** sales-outreach.md, identity-graph-operator.md, agentic-identity-trust.md, agents-orchestrator.md, change-management-consultant.md
4. **Recommended for profile.md:** identity-graph-operator.md, agentic-identity-trust.md, sales-outreach.md
5. **Content Extraction:** Extract Identity & Memory, Core Mission, Critical Rules, Technical Deliverables, Success Metrics sections
6. **Integration Pattern:** Insert using SOUL.md pattern: "You are the [Agent Name] — a [specialized role]... " and profile.md pattern with role, specialization, methods, and metrics
7. **Verification:** Ensure content maintains formatting, complements existing structure, provides actionable guidance, follows preferred style

**Pitfalls to Avoid:**
- ❌ Selecting generic agents without specific expertise
- ❌ Including entire agent files (extract only relevant sections)
- ❌ Overwriting existing SOUL.md/profile.md without review
- ❌ Selecting agents conflicting with user's established identity

**Support Files:**
- `references/agent-selection-criteria.md` - Selection criteria with cross-reference matrix
- `templates/soul-insertion-template.md` - SOUL.md integration template
- `templates/profile-insertion-template.md` - profile.md integration template

## ⚠️ New: ATC (Autonomous Trading Controller) Integration Notes

When integrating agency agents into an Autonomous Trading Controller (ATC) context, consider these additional guidelines:

### ATC-Specific Agent Recommendations:

**For SOUL.md (Trading Agent Identity):**
- `identity-graph-operator.md` - For entity resolution (symbols, contracts, counterparties)
- `agentic-identity-trust.md` - For cryptographic identity & trust verification of agents
- `sales-outreach.md` - If trading includes client outreach / proposal writing

**For profile.md (Trading Agent Profile):**
- **Primary Role**: Trading System Orchestrator
- **Specialization**: Multi-agent market analysis & execution
- **Key Methods**: Identity resolution, risk assessment, pipeline quality gates
- **Success Metrics**: Trade approval rate, risk compliance, execution latency

### ATC Directory Structure (from session):
```
autonomous_trading_controller/
├── SOUL.md              # Trading agent identity
├── profile.md           # Agent profile & roles
├── AGENTS.md            # Senarai agent yang terlibat
├── config/              # Environment & settings
├── orchestrator/        # Core trading logic
├── market/              # Market data & analysis
├── risk/                # Risk management
├── execution/           # Trade execution
├── monitoring/          # Live monitoring scripts
└── papers/              # Paper trading logs
```

**Integration Pattern for ATC:**
- SOUL.md: Focus on deterministic identity, evidence-based decisions, risk compliance
  - Include agent's canonical entity_id, confidence scores, and merge/split decision history
  - Document the agent's role in the identity graph (entity resolution, not generation)
- profile.md: Emphasize agent coordination, trust verification, audit trail maintenance
  - Primary Role: Trading System Orchestrator
  - Specialization: Multi-agent market analysis & execution
  - Key Methods: Identity resolution, risk assessment, pipeline quality gates
  - Success Metrics: Trade approval rate, risk compliance, execution latency
  - Position sizing: Risk-based calculation (2% max per trade of account equity)
- AGENTS.md: List all active agents (market analyst, risk manager, executor, monitor)
  - Each agent entry includes: name, role, confidence threshold, last verification

**ATC Directory Structure (from session)::**
``` 
autonomous_trading_controller/
├── SOUL.md              # Trading agent identity
├── profile.md           # Agent profile & roles
├── AGENTS.md            # Senarai agent yang terlibat
├── config/              # Environment & settings
├── orchestrator/        # Core trading logic
├── market/              # Market data & analysis
├── risk/                # Risk management
├── execution/           # Trade execution
├── monitoring/          # Live monitoring scripts
└── papers/              # Paper trading logs
```

**ATC .env Configuration Template (from session):**
- Critical user-fill fields: ATC_MODE, ACCOUNT_BALANCE, ACCOUNT_CURRENCY, MT5_BRIDGE_TOKEN
- Leverage settings: XAUUSD=100, XAGUSD=100, EURUSD=50, GBPUSD=50, WTI=20
- Risk parameters: MAX_RISK_PER_TRADE=2.0, MAX_DAILY_DRAWDOWN=5.0
- Learning configuration: ENABLE_TRADE_LEARNING=true, MIN_CONFIDENCE=0.55

**Learning Agent Pattern (from session):**
- Agent records every trade outcome (WIN/LOSS/NO_TRADE)
- Win rate tracked across sessions; confidence threshold auto-adjusted
- Consecutive losses trigger pause (max 5 before forced NO_TRADE)
- Position size calculated: (equity × risk%) / |entry - stop_loss|
- Confidence below 0.55 automatically defaults to NO_TRADE

**Verification Scripts (from session):**
- `hermes-verify-env-config`: Validates .env completeness and critical fields
- `hermes-verify-structure`: Checks all 14 required directories exist
- `hermes-verify-files`: Confirms key files (AGENTS.md, SYSTEM_PROMPT.md, run scripts)
- `hermes-verify-agent`: Tests learning agent position sizing and confidence logic

**Integration Checklist for New ATC Sessions:**
1. ✓ Copy .env template, fill: ATC_MODE, ACCOUNT_BALANCE, ACCOUNT_CURRENCY, MT5_BRIDGE_TOKEN
2. ✓ Verify 14/14 directories present in autonomous_trading_controller/
3. ✓ Confirm AGENTS.md lists all active agents with roles
4. ✓ Review SYSTEM_PROMPT.md for fail-closed decision rules
5. ✓ Run verification: `python3 hermes-verify-env-config.py`
6. ✓ Paper trade: `python3 run_paper.py --interval 30`
7. ✓ Monitor: Check decisions.log.jsonl and paper_trading_log.csv output