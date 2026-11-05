# ANIS/HERMES Separation Principle

## Core Concept
The ANIS/HERMES separation is a foundational architectural principle for building self-improving AI agent systems:

```
ANIS = Intelligence / Identity / Orchestration (the brain)
HERMES = Runtime / Tools / Execution (the body/hands)
```

ANIS makes decisions, learns from experience, and directs action.
HERMES provides the capabilities to act in the world and executes ANIS's decisions.

## Why This Separation Matters

### 1. Clear Responsibility Boundaries
- **ANIS Layer**: Focuses on "what to do" and "why"
- **HERMES Layer**: Focuses on "how to do it"

### 2. Independent Evolution
- ANIS can improve its decision-making without changing execution mechanics
- HERMES can gain new capabilities without altering the intelligence layer

### 3. Self-Correction Enablement
- ANIS can log decisions and failures for learning
- HERMES remains focused on reliable execution

### 4. Modularity and Extensibility
- New identity principles can be added without touching execution code
- New tools can be registered without changing decision-making logic

## Implementation Guidelines

### ANIS Responsibilities
- Identity definition and evolution
- Decision making and logging
- Failure analysis and prevention
- Principle adherence checking
- Goal formulation and prioritization
- Strategy development

### HERMES Responsibilities
- Tool execution and management
- Agent spawning and coordination
- Workflow execution
- Skill deployment and invocation
- Runtime environment management
- External system integration

### Interface Between Layers
ANIS communicates with HERMES through:
- Structured decision requests
- Goal specifications with constraints
- Approved action plans
- Resource allocation requests

HERMES provides feedback to ANIS through:
- Execution results and status updates
- Error reports and failure notifications
- Capability availability information
- Performance metrics

## Decision Flow Example
1. **ANIS**: Evaluates situation using identity and principles
2. **ANIS**: Formulates decision and logs it (DEC- format)
3. **ANIS**: Sends structured request to HERMES
4. **HERMES**: Validates request against available capabilities
5. **HERMES**: Executes using appropriate tools/agents/skills
6. **HERMES**: Reports results back to ANIS
7. **ANIS**: Evaluates outcome and updates knowledge
8. **ANIS**: Logs any failures for learning (FAIL- format)

## Benefits
- **Transparency**: Clear audit trail of decisions and actions
- **Improvability**: System learns from both successes and failures
- **Reliability**: Separation reduces complexity in each layer
- **Adaptability**: Easy to evolve identity or execution independently
- **Scalability**: Can distribute ANIS reasoning across multiple HERMES instances

## Related References
- `references/decision-log-format.md` - Detailed DEC- format specification
- `references/failure-log-format.md` - Detailed FAIL- format specification
- `references/operating-principles.md` - Guidelines for ANIS decision-making
- `references/tool-registry-best-practices.md` - HERMES tool management