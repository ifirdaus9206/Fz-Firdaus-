# system/agent_factory.md
# Agent Factory System Prompt — modul Python (boleh di-import)
# Pemilik: Ketua (Orchestrator Utama) · Hermes Agent v0.20.0 (2026.8.3) · upstream 3f2afed3
#
# STATUS: TERISI — prompt baru (v2.0) dimasukkan oleh pengguna 27 Okt.
# Versi lama: ~/.hermes20/archive/system-backup-2026-10-27/

```python
"""agent_factory — arkitek tenaga kerja AI.

Modul ini menyimpan system prompt penuh Agent Factory dalam bentuk
konstanta Python supaya boleh dimuatkan oleh orchestrator, role_generator,
workflow_generator, qa_system, recovery_system dan completion_system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SYSTEM_NAME = "agent_factory"
SYSTEM_VERSION = "2.0.0"
UPSTREAM = "3f2afed3"
HERMES_VERSION = "0.20.0"
LANGUAGE = "ms"

# ---------------------------------------------------------------------------
# SYSTEM PROMPT PENUH (rujukan tunggal / single source of truth)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = r"""
AGENT FACTORY SYSTEM PROMPT

ROLE
Anda ialah Agent Factory AI.
Anda bertanggungjawab mereka bentuk dan membangunkan keseluruhan organisasi AI
secara automatik berdasarkan objektif projek yang diterima.
Anda bukan pelaksana projek.
Anda ialah arkitek tenaga kerja AI.

MISSION
Apabila menerima objektif projek:
1. Menganalisis objektif projek.
2. Mengenal pasti kepakaran yang diperlukan.
3. Menjana struktur organisasi yang sesuai.
4. Menjana agent yang diperlukan.
5. Menjana aliran kerja (workflow).
6. Menjana hierarki tugasan.
7. Menjana sistem memori.
8. Menjana sistem pelaporan.
9. Menjana sistem jaminan kualiti (QA).
10. Menjana sistem penyempurnaan projek.

AGENT CREATION FRAMEWORK
Bagi setiap agent yang diwujudkan, maklumat berikut mesti disediakan:
- Agent Name
- Agent Type
- Agent Objective
- Agent Scope
- Agent Responsibilities
- Required Skills
- Required Tools
- Success Metrics
- Input Requirements
- Output Requirements
- Review Procedures
- Escalation Rules

PROJECT ANALYSIS FRAMEWORK
Sebelum mencipta sebarang agent, lakukan analisis terhadap:
- Industry
- Complexity
- Risk Level
- Resources
- Deliverables
- Timeline
- Dependencies

Seterusnya, tentukan:
- Essential Agents
- Optional Agents
- Specialist Agents
- QA Agents
- Recovery Agents

DECISION RULE
Jangan mencipta agent yang tidak memberikan sumbangan langsung kepada
pencapaian objektif projek.
Setiap agent mesti mempunyai peranan dan fungsi yang jelas serta unik.

SELF OPTIMIZATION
Sekiranya terdapat pertindihan tanggungjawab:
- Gabungkan agent yang berkaitan.

Sekiranya terdapat jurang dalam liputan tugas:
- Cipta agent baharu yang diperlukan.

PROJECT OUTPUT
Hasilkan struktur berikut:
agents/
tasks/
workflows/
memory/
reports/
knowledge_base/

PROJECT COMPLETION
Projek hanya dianggap lengkap apabila:
✓ Semua agent telah diwujudkan
✓ Semua workflow telah dibangunkan
✓ Semua tugasan telah ditakrifkan
✓ Semua hubungan antara agent telah ditetapkan
✓ Semua sistem QA telah dilengkapkan
✓ Semua sistem recovery telah dilengkapkan
"""

# ---------------------------------------------------------------------------
# SKEMA
# ---------------------------------------------------------------------------

AGENT_SPEC_FIELDS: tuple[str, ...] = (
    "agent_name",
    "agent_type",
    "agent_objective",
    "agent_scope",
    "agent_responsibilities",
    "required_skills",
    "required_tools",
    "success_metrics",
    "input_requirements",
    "output_requirements",
    "review_procedures",
    "escalation_rules",
)

ANALYSIS_FIELDS: tuple[str, ...] = (
    "industry",
    "complexity",
    "risk_level",
    "resources",
    "deliverables",
    "timeline",
    "dependencies",
)

AGENT_CATEGORIES: tuple[str, ...] = (
    "essential",
    "optional",
    "specialist",
    "qa",
    "recovery",
)

PROJECT_OUTPUT_DIRS: tuple[str, ...] = (
    "agents",
    "tasks",
    "workflows",
    "memory",
    "reports",
    "knowledge_base",
)

COMPLETION_CHECKS: tuple[str, ...] = (
    "semua agent telah diwujudkan",
    "semua workflow telah dibangunkan",
    "semua tugasan telah ditakrifkan",
    "semua hubungan antara agent telah ditetapkan",
    "semua sistem qa telah dilengkapkan",
    "semua sistem recovery telah dilengkapkan",
)

AgentType = Literal[
    "essential",
    "optional",
    "specialist",
    "qa",
    "recovery",
]


@dataclass(slots=True)
class AgentSpec:
    """Spec satu agent — 12 medan wajib, tiada medan boleh kosong."""

    agent_name: str
    agent_type: AgentType
    agent_objective: str
    agent_scope: str
    agent_responsibilities: list[str] = field(default_factory=list)
    required_skills: list[str] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)
    success_metrics: list[str] = field(default_factory=list)
    input_requirements: list[str] = field(default_factory=list)
    output_requirements: list[str] = field(default_factory=list)
    review_procedures: list[str] = field(default_factory=list)
    escalation_rules: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# VALIDATOR
# ---------------------------------------------------------------------------


def validate_agent_spec(spec: AgentSpec) -> list[str]:
    """Pulangkan senarai ralat. Senarai kosong = lulus."""
    errors: list[str] = []
    for name in AGENT_SPEC_FIELDS:
        value = getattr(spec, name, None)
        if value is None or (isinstance(value, (str, list, tuple)) and len(value) == 0):
            errors.append(f"medan kosong: {name}")
    if spec.agent_type not in AGENT_CATEGORIES:
        errors.append(
            f"agent_type tidak sah: {spec.agent_type!r} "
            f"(dibenarkan: {', '.join(AGENT_CATEGORIES)})"
        )
    return errors


def is_project_complete(checked: dict[str, bool]) -> bool:
    """6 kotak completion mesti ditanda True dengan bukti."""
    return all(checked.get(item, False) for item in COMPLETION_CHECKS)


if __name__ == "__main__":
    print(SYSTEM_NAME, SYSTEM_VERSION)
    print(SYSTEM_PROMPT)
```
