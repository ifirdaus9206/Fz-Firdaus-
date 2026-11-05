---
name: ai-agent-architecture
description: "Design AI agents with separated brain/runtime."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [architecture, ai-agent, design-pattern, separation-of-concepts, self-correction, anis, hermes]
    related_skills: [hermes-agent, hermes-version-management, identity-aware-interaction, systematic-debugging, plan]
---

# AI Agent Architecture

## Description
Skills for designing and implementing AI agent system architectures with separated identity/brain and runtime/execution layers, including self-correction mechanisms through decision and failure logging.

## When to Use
Use when architecting AI agent systems that need:
- Clear separation of concerns between intelligence/identity/orchestration and runtime/tools/execution
- Self-correction capabilities through decision and failure tracking
- Modular organization of agents, skills, workflows, and tools
- Long-term knowledge persistence and learning

## Core Concept: ANIS/HERMES Separation
```
ANIS = Intelligence / Identity / Orchestration (the brain)
HERMES = Runtime / Tools / Execution (the body/hands)
```
ANIS directs HERMES; HERMES enables ANIS to act in the world.

### ANIS Components
- **Identity**: Core identity, personality, principles, mission (SOUL.md, identity.md, principles.md)
- **Expert Registry**: Catalog of specialized knowledge and capabilities
- **Command Banks**: Curated sets of executable commands and procedures
- **Operating Principles**: Fundamental guidelines for behavior and decision-making
- **Decision Framework**: Structured approach to making and recording choices

### HERMES Components
- **Tool Registry**: Available capabilities (web, filesystem, terminal, git, deployment, database, API)
- **Agent Permissions**: Tool access controls per agent type
- **Skills Registry**: Available skill domains
- **Workflow Engine**: Standardized processes (project-start, research, development, testing, deployment, self-correction)
- **Execution Layer**: Terminal, file system, API access, etc.

## Self-Correction Mechanism
Through structured logging, the system learns from experience:

### Decision Log (DEC- format)
```
Format: DEC-[YYYY]-[NNN]
- DEC-2026-001: Structure ANIS as Operating Brain - 2026-10-07 - Established foundation for self-orchestrating AI system
- DEC-2026-002: Adopt Hermes 0.20.0 as runtime - 2026-10-07 - Selected proven agent framework for execution layer
```
Each decision includes: description, date, outcome/impact.

### Failure Log (FAIL- format)
```
Format: FAIL-[YYYY]-[NNN]
- FAIL-2026-001: psutil Android unsupported - 2026-10-07 - Dependency incompatible with Android - Use existing compatible venv - Check platform compatibility before adding dependencies
```
Each failure includes: description, date, root cause, solution, prevention measures.

## Directory Structure
```
PROJECT_ROOT/
│
├── core/           # Orchestration layers
│   ├── orchestrator/
│   ├── router/
│   ├── planner/
│   ├── executor/
│   └── evaluator/
│
├── identity/       # ANIS - Intelligence layer
│   ├── SOUL.md
│   ├── identity.md
│   ├── identity-full.md
│   ├── mission.md
│   ├── principles.md
│   ├── authority.md
│   ├── expert_registry/
│   ├── command_banks/
│   └── decision_framework/
│
├── memory/         # Long-term knowledge
│   ├── MEMORY.md
│   ├── USER.md
│   ├── decisions.md      # Decision Log
│   ├── failures.md       # Failure Log
│   ├── lessons.md
│   ├── projects.md
│   └── knowledge/
│
├── agents/         # Expert agents (Master, Architects, Developers, etc.)
├── skills/         # Skill domains (AI, Coding, Business, etc.)
├── workflows/      # Standardized processes
├── projects/       # Project contexts
├── tasks/          # Current work tracking
├── knowledge/      # Reference materials
├── logs/           # Audit trail
├── system/         # System infrastructure
└── tools/          # Tool registry and definitions
```

## Implementation Steps

1. **Establish Identity Layer**
   - Define core identity in `identity/SOUL.md`
   - Document principles in `identity/principles.md`
   - Create identity-full.md with complete identity details

2. **Set Up Memory System**
   - Create Decision Log (`memory/decisions.md`) with DEC- format
   - Create Failure Log (`memory/failures.md`) with FAIL- format
   - Establish other memory components (USER.md, lessons.md, etc.)

3. **Define Tool & Agent Permissions**
   - Create `tools/registry.json` with available tools and their permissions
   - Set up agent-specific permissions in `agents/*/permissions.json`
   - Create `agents/registry.json` listing all agents with their capabilities

4. **Configure Skills and Workflows**
   - Create `skills/registry.json` for skill domains
   - Create `workflows/registry.json` for standardized processes
   - Implement workflow engines for each process type

5. **Establish Project Structure**
   - Set up project contexts in `projects/`
   - Create task tracking in `tasks/` (inbox, active, review, completed, failed)
   - Organize knowledge in `knowledge/`

6. **Implement Logging and Audit**
   - Set up system logs in `logs/` (decisions, executions, errors, audits)
   - Create system infrastructure in `system/` (registry, schemas, policies, versions)

## Key Principles

### Separation of Concerns
- Keep identity/brain logic separate from runtime/execution logic
- ANIS makes decisions; HERMES executes them
- Clear interfaces between layers

### Modularity
- Organize by concern: identity, memory, agents, skills, workflows, projects
- Each module has clear responsibilities and interfaces
- Easy to extend or replace individual components

### Learnability
- Decisions and failures are logged in structured formats
- System can query past experiences: "Pernahkah masalah ini berlaku?"
- Successful solutions are preserved and reused

### Extensibility
- New tools can be added to the registry
- New agent types can be defined with specific permissions
- New skills and workflows can be registered
- Project structures can be templated

## Verification
- Confirm Hermes version compatibility
- Validate directory structure completeness
- Test decision/failure logging mechanisms
- Verify tool and agent permission systems
- Check skill and workflow registry functionality

## Common Pitfalls
- **Mixing layers**: Don't put runtime logic in identity files or vice versa
- **Incomplete logging**: Always record decisions and failures with sufficient detail
- **Overly rigid structure**: Allow for evolution while maintaining core separation
- **Permission gaps**: Ensure agents have exactly the tools they need - no more, no less
- **Registry drift**: Keep registries synchronized with actual implementations

## Related Skills
- `hermes-agent`: For configuring and extending the Hermes runtime
- `hermes-version-management`: For managing multiple Hermes versions
- `identity-aware-interaction`: For personalizing responses using identity documents
- `systematic-debugging`: For root cause analysis when failures occur
- `plan`: For creating architectural plans before implementation

## References
- `references/anis-hermes-separation.md` - Detailed explanation of the ANIS/HERMES separation principle
- `references/anis-hermes-os-brain.md` - ANIS as Operating Brain: identity, decision-making, and orchestration layer