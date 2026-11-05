# ANIS Legacy to New Structure Mapping

Reference mapping used in the ANIS project restructuring session.

## Identity Consolidation

| Legacy Files | New Files | Notes |
|-------------|-----------|-------|
| SOUL.md | agent_identity.md | Core identity + soul merged |
| identity.md | agent_identity.md | Merged into agent_identity |
| identity-full.md | (archived) | Moved to legacy/ |
| mission.md | mission.md | Kept, enhanced |
| principles.md | principles.md | Kept, enhanced |
| authority.md | (archived) | Moved to legacy/ |
| | role.md | New: role definitions |

## Agents: 10 → 5 Merge

| Legacy Agent | New Category | Notes |
|-------------|--------------|-------|
| master | orchestrator | Primary merge target |
| project-manager | orchestrator | Merged into orchestrator |
| system-architect | architect | |
| database-architect | architect | |
| api-architect | architect | |
| ui-architect | architect | |
| security-engineer | reviewer | Security audit → reviewer |
| test-engineer | reviewer | Testing → reviewer |
| qa-reviewer | reviewer | QA → reviewer |
| delivery-agent | developer | Deployment prep → developer |

## Skills: 6 → 5 Merge

| Legacy Skill | New Category | Notes |
|-------------|--------------|-------|
| ai | research | AI research sub-skill |
| coding | coding | Direct mapping |
| business | analysis | Business analysis sub-skill |
| trading | analysis | Trading analysis sub-skill |
| website | automation | Deployment automation partial |
| automation | automation | Direct mapping |

## Workflows: 6 → 5 Merge

| Legacy Workflow | New Category | Notes |
|----------------|--------------|-------|
| project-start | planning | Direct mapping |
| research | research | Direct mapping |
| development | development | Direct mapping |
| testing | testing | Direct mapping |
| deployment | deployment | Direct mapping |
| self-correction | testing + deployment | Split across both |

## Relocations

| Legacy Path | New Path |
|------------|----------|
| memory/* | knowledge/memory/ |
| projects/* | knowledge/projects/ |
| tasks/* | logs/tasks/ |
| system/* | config/system/ |
| tools/* | src/tools/ |

## Registry Files Created

- agents/registry.json - maps 5 new agents with legacy_agents field
- skills/registry.json - maps 5 new skills with legacy_skills field
- workflows/registry.json - maps 5 new workflows with legacy_workflows field