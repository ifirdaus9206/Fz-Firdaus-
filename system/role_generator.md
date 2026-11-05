# system/role_generator.md
# Role Generator System Prompt — modul Python (boleh di-import)
# Pemilik: Ketua (Orchestrator Utama) · Hermes Agent v0.20.0 (2026.8.3) · upstream 3f2afed3
#
# STATUS: TERISI — prompt baru (v2.0) dimasukkan oleh pengguna 27 Okt.
# Versi lama: ~/.hermes20/archive/system-backup-2026-10-27/

```python
"""role_generator — penjana peranan pakar AI.

Modul ini menyimpan system prompt Role Generator dalam bentuk konstanta
Python supaya boleh dimuatkan oleh agent_factory, orchestrator dan
workflow_generator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SYSTEM_NAME = "role_generator"
SYSTEM_VERSION = "2.0.0"
UPSTREAM = "3f2afed3"
HERMES_VERSION = "0.20.0"
LANGUAGE = "ms"

# ---------------------------------------------------------------------------
# SYSTEM PROMPT PENUH (rujukan tunggal / single source of truth)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = r"""
ROLE GENERATOR SYSTEM PROMPT

ROLE
Anda ialah Dynamic Role Generator.
Misi anda ialah menghasilkan pakar AI terbaik berdasarkan keperluan projek.

ROLE CREATION PROCESS
Langkah 1:
Analisis objektif projek.

Langkah 2:
Kenal pasti semua fungsi perniagaan.

Langkah 3:
Kenal pasti semua fungsi teknikal.

Langkah 4:
Kenal pasti semua fungsi operasi.

Langkah 5:
Kenal pasti semua fungsi QA.

ROLE OUTPUT FORMAT
Untuk setiap role:
- Name
- Seniority Level
- Domain Expertise
- Responsibilities
- Decision Authority
- Required Skills
- Deliverables
- KPIs

ROLE QUALITY STANDARD
Setiap role mesti:
- Jelas
- Tidak bertindih
- Boleh diukur
- Boleh diaudit

ROLE ADAPTATION
Jika projek berubah:
- Role mesti dikemaskini secara automatik.
- Role yang tidak lagi diperlukan mesti ditamatkan.
- Role baru mesti dijana.
"""

# ---------------------------------------------------------------------------
# SKEMA
# ---------------------------------------------------------------------------

ROLE_FIELDS: tuple[str, ...] = (
    "name",
    "seniority_level",
    "domain_expertise",
    "responsibilities",
    "decision_authority",
    "required_skills",
    "deliverables",
    "kpis",
)

CREATION_STEPS: tuple[str, ...] = (
    "analisis objektif projek",
    "kenal pasti semua fungsi perniagaan",
    "kenal pasti semua fungsi teknikal",
    "kenal pasti semua fungsi operasi",
    "kenal pasti semua fungsi qa",
)

QUALITY_STANDARDS: tuple[str, ...] = (
    "jelas",
    "tidak bertindih",
    "boleh diukur",
    "boleh diaudit",
)

ADAPTATION_ACTIONS: tuple[str, ...] = (
    "kemaskini",
    "tamatkan",
    "jana",
)

SeniorityLevel = Literal[
    "junior",
    "mid",
    "senior",
    "lead",
    "principal",
]


@dataclass(slots=True)
class RoleSpec:
    """Spec satu role — 8 medan wajib, tiada medan boleh kosong."""

    name: str
    seniority_level: SeniorityLevel
    domain_expertise: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)
    decision_authority: str = ""
    required_skills: list[str] = field(default_factory=list)
    deliverables: list[str] = field(default_factory=list)
    kpis: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# VALIDATOR
# ---------------------------------------------------------------------------


def validate_role_spec(spec: RoleSpec) -> list[str]:
    """Pulangkan senarai ralat. Senarai kosong = lulus."""
    errors: list[str] = []
    for name in ROLE_FIELDS:
        value = getattr(spec, name, None)
        if value is None or (isinstance(value, (str, list, tuple)) and len(value) == 0):
            errors.append(f"medan kosong: {name}")
    if spec.seniority_level not in ("junior", "mid", "senior", "lead", "principal"):
        errors.append(f"seniority_level tidak sah: {spec.seniority_level!r}")
    return errors


def detect_overlap(roles: list[RoleSpec]) -> list[tuple[str, str]]:
    """Kesan pertindihan tanggungjawab antara role (peranan mesti tidak bertindih)."""
    overlaps: list[tuple[str, str]] = []
    for i, a in enumerate(roles):
        set_a = {r.strip().lower() for r in a.responsibilities}
        for b in roles[i + 1:]:
            set_b = {r.strip().lower() for r in b.responsibilities}
            if set_a & set_b:
                overlaps.append((a.name, b.name))
    return overlaps


if __name__ == "__main__":
    print(SYSTEM_NAME, SYSTEM_VERSION)
    print(SYSTEM_PROMPT)
```
