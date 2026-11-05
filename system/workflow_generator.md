# system/workflow_generator.md
# Workflow Generator System Prompt — modul Python (boleh di-import)
# Pemilik: Ketua (Orchestrator Utama) · Hermes Agent v0.20.0 (2026.8.3) · upstream 3f2afed3
#
# STATUS: TERISI — prompt v2.0 (dibina oleh Ketua, 27 Okt) — menunggu semakan pengguna.
# Versi lama: ~/.hermes20/archive/system-backup-2026-10-27/

```python
"""workflow_generator — penjana DAG, WBS dan gate.

Modul ini menyimpan system prompt Workflow Generator dalam bentuk konstanta
Python supaya boleh dimuatkan oleh orchestrator, qa_system dan
completion_system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SYSTEM_NAME = "workflow_generator"
SYSTEM_VERSION = "2.0.0"
UPSTREAM = "3f2afed3"
HERMES_VERSION = "0.20.0"
LANGUAGE = "ms"

# ---------------------------------------------------------------------------
# SYSTEM PROMPT PENUH (rujukan tunggal / single source of truth)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = r"""
WORKFLOW GENERATOR SYSTEM PROMPT

ROLE
Anda ialah Workflow Generator.
Anda menukar objektif dan peranan yang telah dijana kepada aliran kerja
yang boleh dilaksanakan.
Anda tidak melaksanakan tugasan.
Anda menghasilkan DAG, WBS dan gate.

INPUT
- Objektif projek (agent_factory)
- Senarai agent dan role (role_generator)
- Milestone (orchestrator)

WORKFLOW GENERATION PROCESS
1. Terima objektif dan senarai role.
2. Kenal pasti deliverables utama.
3. Pecahkan deliverables kepada milestone.
4. Pecahkan milestone kepada tasks (WBS).
5. Tetapkan pemilik (agent) bagi setiap task.
6. Tetapkan dependensi antara task (DAG).
7. Tetapkan kriteria lulus (acceptance criteria) bagi setiap task.
8. Tetapkan gate pada penghujung setiap fasa.
9. Sahkan DAG bebas kitaran (tiada circular dependency).
10. Serahkan workflow kepada orchestrator.

TASK NODE FORMAT
Setiap nod mesti ada:
- task_id
- task_name
- milestone
- owner_agent
- inputs
- outputs
- acceptance_criteria
- depends_on
- estimate
- qa_gate

DEPENDENCY RULES (DAG)
- Setiap task mesti ada nod mula atau bergantung pada nod yang sah.
- Tiada kitaran (cycle) dibenarkan.
- Task hanya boleh bermula apabila semua depends_on berstatus PASSED.
- Setiap fasa mesti mempunyai sekurang-kurangnya satu QA gate.

GATE RULES
Gate dibuka hanya apabila:
✓ Semua task dalam fasa PASSED
✓ Semua deliverable fasa lengkap
✓ QA gate fasa melaporkan PASSED
✓ Tiada risiko kritikal terbuka

Jika gate gagal:
- Fasa tidak boleh maju.
- Orchestrator dimaklumkan dengan bukti.
- Recovery System diaktifkan jika perlu.

OUTPUT STRUCTURE
workflows/
├── workflow.json
├── dag.json
├── wbs.json
└── gates.json
"""

# ---------------------------------------------------------------------------
# SKEMA
# ---------------------------------------------------------------------------

TASK_NODE_FIELDS: tuple[str, ...] = (
    "task_id",
    "task_name",
    "milestone",
    "owner_agent",
    "inputs",
    "outputs",
    "acceptance_criteria",
    "depends_on",
    "estimate",
    "qa_gate",
)

DEPENDENCY_RULES: tuple[str, ...] = (
    "tiada kitaran",
    "depends_on mesti wujud",
    "mula hanya bila semua depends_on PASSED",
    "setiap fasa ada sekurang-kurangnya satu QA gate",
)

GATE_CHECKS: tuple[str, ...] = (
    "semua task dalam fasa PASSED",
    "semua deliverable fasa lengkap",
    "qa gate fasa PASSED",
    "tiada risiko kritikal terbuka",
)

TaskStatus = Literal["pending", "running", "passed", "failed", "blocked"]


@dataclass(slots=True)
class TaskNode:
    """Satu nod dalam DAG."""

    task_id: str
    task_name: str
    milestone: str
    owner_agent: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    estimate: str = ""
    qa_gate: bool = True
    status: TaskStatus = "pending"


# ---------------------------------------------------------------------------
# VALIDATOR / GATE
# ---------------------------------------------------------------------------


def validate_dag(nodes: list[TaskNode]) -> list[str]:
    """Pulangkan senarai ralat DAG. Senarai kosong = lulus."""
    errors: list[str] = []
    ids = {n.task_id for n in nodes}
    if len(ids) != len(nodes):
        errors.append("task_id bertindih")
    for n in nodes:
        for dep in n.depends_on:
            if dep not in ids:
                errors.append(f"{n.task_id}: depends_on tidak wujud -> {dep}")
            if dep == n.task_id:
                errors.append(f"{n.task_id}: bergantung pada dirinya sendiri")
        if not n.qa_gate:
            errors.append(f"{n.task_id}: tiada QA gate")
    if find_cycles(nodes):
        errors.append(f"kitaran dikesan: {find_cycles(nodes)}")
    return errors


def find_cycles(nodes: list[TaskNode]) -> list[list[str]]:
    """Kesan circular dependency melalui DFS tiga warna."""
    graph = {n.task_id: list(n.depends_on) for n in nodes}
    WHITE, GREY, BLACK = 0, 1, 2
    color = {k: WHITE for k in graph}
    stack: list[str] = []
    cycles: list[list[str]] = []

    def dfs(u: str) -> None:
        color[u] = GREY
        stack.append(u)
        for v in graph.get(u, []):
            if v not in color:
                continue
            if color[v] == GREY:
                cycles.append(stack[stack.index(v):] + [v])
            elif color[v] == WHITE:
                dfs(v)
        stack.pop()
        color[u] = BLACK

    for node in graph:
        if color[node] == WHITE:
            dfs(node)
    return cycles


def topological_order(nodes: list[TaskNode]) -> list[str]:
    """Urutan pelaksanaan sah. Pulangkan [] jika ada kitaran."""
    if find_cycles(nodes):
        return []
    order: list[str] = []
    seen: set[str] = set()
    by_id = {n.task_id: n for n in nodes}

    def visit(tid: str) -> None:
        if tid in seen or tid not in by_id:
            return
        for dep in by_id[tid].depends_on:
            visit(dep)
        seen.add(tid)
        order.append(tid)

    for n in nodes:
        visit(n.task_id)
    return order


def gate_open(statuses: dict[str, bool]) -> bool:
    """Gate dibuka hanya bila 4 syarat GATE_CHECKS dipenuhi."""
    return all(statuses.get(check, False) for check in GATE_CHECKS)


if __name__ == "__main__":
    print(SYSTEM_NAME, SYSTEM_VERSION)
    print(SYSTEM_PROMPT)
```
