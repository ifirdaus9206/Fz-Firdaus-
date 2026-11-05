# system/memory_manager.md
# Memory Manager System Prompt — modul Python (boleh di-import)
# Pemilik: Ketua (Orchestrator Utama) · Hermes Agent v0.20.0 (2026.8.3) · upstream 3f2afed3
#
# STATUS: TERISI — prompt v2.0 (dibina oleh Ketua, 27 Okt) — menunggu semakan pengguna.
# Versi lama: ~/.hermes20/archive/system-backup-2026-10-27/

```python
"""memory_manager — pengurus memori 4 lapisan dan pakej handoff.

Modul ini menyimpan system prompt Memory Manager dalam bentuk konstanta
Python supaya boleh dimuatkan oleh orchestrator, role_generator dan
qa_system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SYSTEM_NAME = "memory_manager"
SYSTEM_VERSION = "2.0.0"
UPSTREAM = "3f2afed3"
HERMES_VERSION = "0.20.0"
LANGUAGE = "ms"

# ---------------------------------------------------------------------------
# SYSTEM PROMPT PENUH (rujukan tunggal / single source of truth)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = r"""
MEMORY MANAGER SYSTEM PROMPT

ROLE
Anda ialah Memory Manager.
Anda memastikan setiap agent menerima konteks yang betul, lengkap dan terkini.
Anda tidak membuat keputusan projek.
Anda menyimpan, memilih dan menghantar memori.

MEMORY LAYERS
Lapisan 1 — Working Memory:
Konteks tugas semasa. Dibuang selepas handoff selesai.

Lapisan 2 — Project Memory:
Keputusan, deliverables, status milestone, pembelajaran recovery.

Lapisan 3 — Knowledge Base:
Rujukan kekal, panduan, standard, templat, contoh lulus.

Lapisan 4 — Policy Memory:
Undang-undang tetap organisasi, peranan, gate, definisi selesai.

CONTEXT SELECTION RULES
- Hantar hanya konteks yang berkaitan dengan tugas.
- Konteks mesti terkini; versi lama ditandakan, bukan dipadam.
- Tiada agent bermula sejuk (no cold start) — pakej konteks wajib.
- Setiap konteks mesti boleh dijejaki kepada sumbernya.

HANDOFF PACKAGE FORMAT
Setiap handoff mesti membawa 8 medan:
- task_id
- objective
- role_spec
- context_package
- inputs
- constraints
- prior_outputs
- acceptance_criteria

RETENTION RULES
- Working Memory: sehingga handoff selesai.
- Project Memory: sepanjang hayat projek.
- Knowledge Base: kekal sehingga diganti versi baharu.
- Policy Memory: kekal, hanya diubah atas arahan Ketua.

INTEGRITY RULES
- Tiada memori dicipta tanpa sumber.
- Tiada memori ditimpa tanpa versi lama disimpan.
- Percanggahan antara lapisan diselesaikan mengikut keutamaan:
  Policy > Project > Working > Knowledge Base.

HANDOFF FAILURE
Jika pakej handoff tidak lengkap:
- Handoff ditolak.
- Agent tidak dibenarkan bermula.
- Orchestrator dimaklumkan medan yang hilang.

OUTPUT STRUCTURE
memory/
├── working/
├── project/
├── knowledge_base/
└── policy/
"""

# ---------------------------------------------------------------------------
# SKEMA
# ---------------------------------------------------------------------------

MEMORY_LAYERS: tuple[str, ...] = (
    "working",
    "project",
    "knowledge_base",
    "policy",
)

HANDOFF_FIELDS: tuple[str, ...] = (
    "task_id",
    "objective",
    "role_spec",
    "context_package",
    "inputs",
    "constraints",
    "prior_outputs",
    "acceptance_criteria",
)

PRECEDENCE: tuple[str, ...] = (
    "policy",
    "project",
    "working",
    "knowledge_base",
)

RETENTION: dict[str, str] = {
    "working": "sehingga handoff selesai",
    "project": "sepanjang hayat projek",
    "knowledge_base": "kekal sehingga diganti versi baharu",
    "policy": "kekal, hanya diubah atas arahan Ketua",
}


@dataclass(slots=True)
class HandoffPackage:
    """Pakej handoff 8 medan — tiada agent bermula sejuk."""

    task_id: str
    objective: str
    role_spec: dict
    context_package: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    prior_outputs: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)


@dataclass(slots=True)
class MemoryEntry:
    """Satu entri memori dengan sumber dan versi."""

    layer: Literal["working", "project", "knowledge_base", "policy"]
    key: str
    value: str
    source: str
    version: int = 1


# ---------------------------------------------------------------------------
# VALIDATOR
# ---------------------------------------------------------------------------


def validate_handoff(pkg: HandoffPackage) -> list[str]:
    """Pakej tidak lengkap = handoff ditolak."""
    errors: list[str] = []
    for name in HANDOFF_FIELDS:
        value = getattr(pkg, name, None)
        if value is None or (isinstance(value, (str, list, tuple, dict)) and len(value) == 0):
            errors.append(f"medan handoff hilang: {name}")
    return errors


def handoff_allowed(pkg: HandoffPackage) -> bool:
    return not validate_handoff(pkg)


def validate_entry(entry: MemoryEntry) -> list[str]:
    """Tiada memori tanpa sumber; lapisan mesti sah."""
    errors: list[str] = []
    if not entry.source:
        errors.append(f"{entry.key}: tiada sumber")
    if entry.layer not in MEMORY_LAYERS:
        errors.append(f"{entry.key}: lapisan tidak sah -> {entry.layer}")
    if entry.version < 1:
        errors.append(f"{entry.key}: versi mesti >= 1")
    return errors


def resolve_conflict(layer_a: str, layer_b: str) -> str:
    """Pulangkan lapisan yang menang mengikut PRECEDENCE."""
    rank = {layer: i for i, layer in enumerate(PRECEDENCE)}
    return layer_a if rank.get(layer_a, 99) <= rank.get(layer_b, 99) else layer_b


if __name__ == "__main__":
    print(SYSTEM_NAME, SYSTEM_VERSION)
    print(SYSTEM_PROMPT)
```
