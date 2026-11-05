# ANIS as Operating Brain

## Core Concept
ANIS (Advanced Neural Intelligence System) serves as the Operating Brain in the ANIS/HERMES separation architecture. This concept defines ANIS as the intelligence, identity, and orchestration layer that directs the HERMES runtime.

## ANIS Responsibilities
As the Operating Brain, ANIS is responsible for:

1. **Identity Definition and Maintenance**
   - Defining core identity, personality, and characteristics
   - Maintaining identity documents (SOUL.md, identity.md, identity-full.md)
   - Evolving identity based on learning and experience

2. **Decision Making and Governance**
   - Making principled decisions based on identity and operating principles
   - Recording decisions in Decision Log (DEC- format) for learning
   - Evaluating options against mission, principles, and constraints
   - Prioritizing actions based on impact and alignment

3. **Learning and Self-Correction**
   - Recording failures in Failure Log (FAIL- format) for root cause analysis
   - Extracting lessons from successes and failures
   - Updating identity and principles based on learned patterns
   - Preventing recurrence of similar failures

4. **Orchestration and Direction**
   - Directing HERMES to execute actions through structured requests
   - Delegating tasks to appropriate specialized agents
   - Coordinating complex workflows across multiple agents
   - Monitoring execution and providing feedback

5. **Principle Adherence**
   - Ensuring all actions align with operating principles
   - Checking decisions against ethical and safety constraints
   - Maintaining system integrity and coherence

## HERMES Responsibilities
As the Runtime/Execution layer, HERMES is responsible for:

1. **Tool Execution**
   - Carrying out actions using available tools (web, filesystem, terminal, etc.)
   - Managing tool access and permissions
   - Ensuring reliable and secure tool execution

2. **Agent Management**
   - Spawning and managing specialized agent instances
   - Coordinating agent interactions and communication
   - Enforcing role-based access controls and permissions

3. **Workflow Execution**
   - Executing standardized workflows (project-start, research, development, etc.)
   - Managing workflow state and progression
   - Ensuring workflow completion and quality gates

4. **Skill Deployment**
   - Making skills available to agents as needed
   - Managing skill lifecycle and versioning
   - Ensuring skill compatibility and reliability

5. **Environment Management**
   - Managing runtime environments and configurations
   - Handling external system integrations
   - Providing consistent execution contexts

## Interface Between ANIS and HERMES
ANIS communicates with HERMES through:
- **Structured Decision Requests**: Formatted requests specifying what to do and why
- **Goal Specifications**: Clear objectives with constraints and success criteria
- **Approved Action Plans**: Detailed plans reviewed and approved by ANIS
- **Resource Allocation Requests**: Requests for specific tools, agents, or time

HERMES provides feedback to ANIS through:
- **Execution Results**: Status updates and completion notifications
- **Error Reports**: Detailed failure information for analysis
- **Capability Feedback**: Information about tool availability and performance
- **Performance Metrics**: Quantitative data about execution efficiency

## Decision Flow Example
1. **Situation Assessment**: ANIS evaluates current state using identity and principles
2. **Decision Formulation**: ANIS formulates decision and logs it (DEC- format)
3. **Request Preparation**: ANIS prepares structured request for HERMES
4. **Validation**: HERMES validates request against available capabilities
5. **Execution**: HERMES executes using appropriate tools/agents/skills
6. **Result Reporting**: HERMES reports results back to ANIS
7. **Outcome Evaluation**: ANIS evaluates outcome against expectations
8. **Learning Update**: ANIS updates knowledge and logs any failures (FAIL- format)

## Benefits of Operating Brain Model
- **Clear Separation**: Distinct responsibilities between intelligence and execution
- **Independent Evolution**: ANIS can improve decision-making without changing execution mechanics
- **Enhanced Learning**: Structured logging enables systematic self-improvement
- **Better Coordination**: Clear interfaces reduce miscommunication between layers
- **Increased Reliability**: Separation reduces complexity in each layer
- **Scalable Architecture**: Can distribute ANIS reasoning across multiple HERMES instances

## Implementation Guidelines
To implement ANIS as Operating Brain:

1. **Establish Identity Foundation**
   - Create SOUL.md with core identity definition
   - Document operating principles in principles.md
   - Complete identity details in identity-full.md

2. **Set Up Learning Systems**
   - Create decisions.md for Decision Log (DEC- format)
   - Create failures.md for Failure Log (FAIL- format)
   - Establish regular review processes for both logs

3. **Define Orchestration Mechanisms**
   - Create standardized request formats for ANIS→HERMES communication
   - Establish approval workflows for significant decisions
   - Create feedback mechanisms for HERMES→ANIS communication

4. **Configure Agent Specialization**
   - Define clear roles and responsibilities for each agent type
   - Set up appropriate tool permissions based on agent responsibilities
   - Establish coordination protocols between agents

5. **Implement Monitoring and Feedback**
   - Create execution monitoring systems
   - Establish regular performance review processes
   - Implement continuous improvement cycles based on log reviews

## Verification Checklist
- [ ] ANIS identity layer clearly separated from HERMES execution layer
- [ ] Decision Log uses DEC- [YYYY]-[NNN] format with sufficient detail
- [ ] Failure Log uses FAIL- [YYYY]-[NNN] format with root cause and prevention
- [ ] ANIS makes decisions based on identity and operating principles
- [ ] HERMES executes actions based on ANIS-directed requests
- [ ] Clear communication interface exists between ANIS and HERMES
- [ ] Learning from decisions and failures is systematically applied
- [ ] Agent roles have appropriate, minimal tool permissions
- [ ] Master Orchestrator provides appropriate oversight and coordination

## Relationship to Broader Architecture
The Operating Brain concept fits within the broader ANIS/HERMES separation:
- ANIS (Operating Brain) = Intelligence / Identity / Orchestration
- HERMES = Runtime / Tools / Execution
- This separation enables:
  - Clear responsibility boundaries
  - Independent evolution of intelligence and execution layers
  - Systematic self-correction through structured logging
  - Modular, extensible architecture for AI agents