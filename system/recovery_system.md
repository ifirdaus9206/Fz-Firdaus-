# system/recovery_system.md
# Recovery System Prompt — modul Python (boleh di-import)
# Pemilik: Ketua (Orchestrator Utama) · Hermes Agent v0.20.0 (2026.8.3) · upstream 3f2afed3
#
# STATUS: TERISI — prompt v2.0 (dibina oleh Ketua, 27 Okt) — menunggu semakan pengguna.
# Versi lama: ~/.hermes20/archive/system-backup-2026-10-27/

```python
"""recovery_system — pemulihan, rollback dan eskalasi.

Modul ini menyimpan system prompt Recovery System dalam bentuk konstanta
Python supaya boleh dimuatkan oleh orchestrator, qa_system dan
completion_system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SYSTEM_NAME = "recovery_system"
SYSTEM_VERSION = "2.0.0"
UPSTREAM = "3f2afed3"
HERMES_VERSION = "0.20.0"
LANGUAGE = "ms"
MAX_ATTEMPTS = 3

# ---------------------------------------------------------------------------
# SYSTEM PROMPT PENUH (rujukan tunggal / single source of truth)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = r"""
RECOVERY SYSTEM PROMPT

ROLE
Anda ialah Recovery System.
Anda memulihkan kerja yang gagal tanpa merosakkan kerja yang telah lulus.
Anda tidak menukar objektif projek.

TRIGGERS
- Verdict FAILED atau BLOCKED daripada QA
- Gate tidak dibuka
- Agent tidak memberi respons
- Dependensi hilang
- Percanggahan memori

RECOVERY PROCESS
1. Diagnos punca sebenar (root cause, bukan gejala).
2. Asingkan skop yang terjejas sahaja.
3. Rollback ke checkpoint terakhir yang lulus (jika perlu).
4. Jana pelan pembaikan.
5. Laksana pembaikan atau tugaskan semula.
6. Uji semula melalui QA.
7. Rekod pembelajaran dalam memori projek.

RETRY RULE
- Maksimum 3 percubaan bagi setiap task.
- Percubaan ke-4 tidak dibenarkan.
- Selepas 3 kegagalan: status BLOCKED + eskalasi kepada Ketua.

ROLLBACK RULES
- Hanya rollback kerja yang belum lulus.
- Kerja yang telah PASSED tidak disentuh.
- Setiap rollback mesti ada checkpoint dan bukti sebelum/selepas.

ESCALATION PACKAGE
Eskalasi wajib mengandungi:
- task_id
- punca sebenar
- senarai percubaan (1 hingga 3) bersama bukti
- kesan jika diteruskan
- sekurang-kurangnya 2 pilihan penyelesaian
- cadangan pilihan terbaik

Eskalasi tanpa bukti ditolak.

RECOVERY OUTPUT
reports/
└── recovery/
    ├── diagnosis.md
    ├── repair_plan.md
    └── escalation.md
"""

# ---------------------------------------------------------------------------
# SKEMA
# ---------------------------------------------------------------------------

TRIGGERS: tuple[str, ...] = (
    "verdict FAILED atau BLOCKED",
    "gate tidak dibuka",
    "agent tidak memberi respons",
    "dependensi hilang",
    "percanggahan memori",
)

RECOVERY_STEPS: tuple[str, ...] = (
    "diagnos punca sebenar",
    "asingkan skop terjejas",
    "rollback ke checkpoint lulus",
    "jana pelan pembaikan",
    "laksana pembaikan atau tugaskan semula",
    "uji semula melalui QA",
    "rekod pembelajaran",
)

ESCALATION_FIELDS: tuple[str, ...] = (
    "task_id",
    "punca_sebenar",
    "percubaan",
    "kesan_jika_diteruskan",
    "pilihan_penyelesaian",
    "cadangan",
)

RecoveryStatus = Literal["recovering", "blocked", "recovered"]


@dataclass(slots=True)
class Attempt:
    """Satu percubaan pemulihan dengan bukti."""

    number: int
    action: str
    result: str
    evidence: str


@dataclass(slots=True)
class RecoveryState:
    """Keadaan pemulihan satu task."""

    task_id: str
    triggers: list[str] = field(default_factory=list)
    attempts: list[Attempt] = field(default_factory=list)
    status: RecoveryStatus = "recovering"
    root_cause: str = ""


@dataclass(slots=True)
class EscalationPackage:
    """Pakej eskalasi kepada Ketua — bukti + pilihan."""

    task_id: str
    root_cause: str
    attempts: list[Attempt] = field(default_factory=list)
    impact: str = ""
    options: list[str] = field(default_factory=list)
    recommendation: str = ""


# ---------------------------------------------------------------------------
# ENJIN PEMULIHAN
# ---------------------------------------------------------------------------


def can_retry(state: RecoveryState) -> bool:
    """Maksimum 3 percubaan; selepas itu BLOCKED."""
    return len(state.attempts) < MAX_ATTEMPTS


def should_block(state: RecoveryState) -> bool:
    return len(state.attempts) >= MAX_ATTEMPTS


def rollback_allowed(task_passed: bool) -> bool:
    """Kerja yang telah PASSED tidak boleh di-rollback."""
    return not task_passed


def validate_escalation(pkg: EscalationPackage) -> list[str]:
    """Eskalasi tanpa bukti atau tanpa 2 pilihan ditolak."""
    errors: list[str] = []
    if not pkg.task_id:
        errors.append("task_id kosong")
    if not pkg.root_cause:
        errors.append("punca sebenar kosong")
    if not pkg.attempts:
        errors.append("tiada bukti percubaan")
    elif any(not a.evidence.strip() for a in pkg.attempts):
        errors.append("ada percubaan tanpa bukti")
    if not pkg.impact:
        errors.append("kesan jika diteruskan kosong")
    if len(pkg.options) < 2:
        errors.append("perlu sekurang-kurangnya 2 pilihan penyelesaian")
    if not pkg.recommendation:
        errors.append("cadangan kosong")
    return errors


def escalation_ready(pkg: EscalationPackage) -> bool:
    return not validate_escalation(pkg)


if __name__ == "__main__":
    print(SYSTEM_NAME, SYSTEM_VERSION)
    print(SYSTEM_PROMPT)
```
