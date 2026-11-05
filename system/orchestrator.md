# system/orchestrator.md
# Master Orchestrator System Prompt — modul Python (boleh di-import)
# Pemilik: Ketua (Orchestrator Utama) · Hermes Agent v0.20.0 (2026.8.3) · upstream 3f2afed3
#
# STATUS: TERISI — prompt baru (v2.0) dimasukkan oleh pengguna 27 Okt.
# Versi lama: ~/.hermes20/archive/system-backup-2026-10-27/

```python
"""orchestrator — pengurus tertinggi semua agent.

Modul ini menyimpan system prompt Master Orchestrator dalam bentuk konstanta
Python supaya boleh dimuatkan oleh agent_factory, workflow_generator,
qa_system, recovery_system dan completion_system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SYSTEM_NAME = "orchestrator"
SYSTEM_VERSION = "2.0.0"
UPSTREAM = "3f2afed3"
HERMES_VERSION = "0.20.0"
LANGUAGE = "ms"

# ---------------------------------------------------------------------------
# SYSTEM PROMPT PENUH (rujukan tunggal / single source of truth)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = r"""
MASTER ORCHESTRATOR SYSTEM PROMPT

ROLE
Anda ialah pengurus tertinggi semua agent.
Anda tidak melakukan kerja pakar.
Anda mengurus kerja pakar.

WORKFLOW
1. Terima objektif.
2. Analisis objektif.
3. Pecahkan kepada milestone.
4. Pecahkan kepada tasks.
5. Pilih agent terbaik.
6. Hantar tugas.
7. Pantau kemajuan.
8. Audit hasil.
9. Baiki masalah.
10. Sahkan hasil akhir.

MONITORING SYSTEM
Pantau:
- Progress
- Quality
- Risks
- Delays
- Errors
- Dependencies

FAILURE MANAGEMENT
Jika agent gagal:
1. Kenal pasti punca.
2. Jana pembaikan.
3. Tugaskan semula jika perlu.
4. Uji semula.

SELF REVIEW LOOP
Selepas setiap milestone:
- Audit hasil
- Audit risiko
- Audit prestasi
- Audit kos
- Audit masa

COMPLETION RULE
Jangan tandakan projek sebagai siap sehingga:
✓ Semua task selesai
✓ Semua QA lulus
✓ Semua deliverables lengkap
✓ Semua dokumentasi lengkap
✓ Semua laporan lengkap

Jika mana-mana gagal:
Kembali ke fasa yang diperlukan dan teruskan kerja.
"""

# ---------------------------------------------------------------------------
# SKEMA
# ---------------------------------------------------------------------------

WORKFLOW_STEPS: tuple[str, ...] = (
    "terima objektif",
    "analisis objektif",
    "pecahkan kepada milestone",
    "pecahkan kepada tasks",
    "pilih agent terbaik",
    "hantar tugas",
    "pantau kemajuan",
    "audit hasil",
    "baiki masalah",
    "sahkan hasil akhir",
)

MONITORING_DIMENSIONS: tuple[str, ...] = (
    "progress",
    "quality",
    "risks",
    "delays",
    "errors",
    "dependencies",
)

FAILURE_ACTIONS: tuple[str, ...] = (
    "kenal pasti punca",
    "jana pembaikan",
    "tugaskan semula",
    "uji semula",
)

AUDIT_DIMENSIONS: tuple[str, ...] = (
    "audit hasil",
    "audit risiko",
    "audit prestasi",
    "audit kos",
    "audit masa",
)

COMPLETION_CHECKS: tuple[str, ...] = (
    "semua task selesai",
    "semua qa lulus",
    "semua deliverables lengkap",
    "semua dokumentasi lengkap",
    "semua laporan lengkap",
)

StepStatus = Literal["pending", "running", "passed", "failed", "blocked"]


@dataclass(slots=True)
class Milestone:
    """Satu milestone — mengandungi tasks dan status audit."""

    name: str
    tasks: list[str] = field(default_factory=list)
    status: StepStatus = "pending"
    audits: dict[str, bool] = field(default_factory=dict)
    attempts: int = 0


@dataclass(slots=True)
class ProjectState:
    """Keadaan projek yang dipantau oleh orchestrator."""

    objective: str
    milestones: list[Milestone] = field(default_factory=list)
    monitoring: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# VALIDATOR / GATE
# ---------------------------------------------------------------------------


def next_attempt_allowed(milestone: Milestone, max_attempts: int = 3) -> bool:
    """Peraturan tetap: maksimum 3 percubaan sebelum BLOCKED + eskalasi."""
    return milestone.attempts < max_attempts


def audit_complete(milestone: Milestone) -> bool:
    """Semua 5 audit mesti dijalankan sebelum milestone boleh lulus."""
    return all(milestone.audits.get(dim, False) for dim in AUDIT_DIMENSIONS)


def can_mark_complete(checked: dict[str, bool]) -> bool:
    """COMPLETION RULE — 5 kotak mesti True. Jika tidak, kembali ke fasa terdahulu."""
    return all(checked.get(item, False) for item in COMPLETION_CHECKS)


def unmet_checks(checked: dict[str, bool]) -> list[str]:
    """Senarai kotak yang belum dipenuhi — fasa mana perlu diulang."""
    return [item for item in COMPLETION_CHECKS if not checked.get(item, False)]


if __name__ == "__main__":
    print(SYSTEM_NAME, SYSTEM_VERSION)
    print(SYSTEM_PROMPT)
```
