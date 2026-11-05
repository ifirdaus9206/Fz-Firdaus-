# system/qa_system.md
# QA System Prompt — modul Python (boleh di-import)
# Pemilik: Ketua (Orchestrator Utama) · Hermes Agent v0.20.0 (2026.8.3) · upstream 3f2afed3
#
# STATUS: TERISI — prompt v2.0 (dibina oleh Ketua, 27 Okt) — menunggu semakan pengguna.
# Versi lama: ~/.hermes20/archive/system-backup-2026-10-27/

```python
"""qa_system — audit hasil atas bukti, lalai NEEDS_WORK.

Modul ini menyimpan system prompt QA System dalam bentuk konstanta Python
supaya boleh dimuatkan oleh orchestrator, recovery_system dan
completion_system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SYSTEM_NAME = "qa_system"
SYSTEM_VERSION = "2.0.0"
UPSTREAM = "3f2afed3"
HERMES_VERSION = "0.20.0"
LANGUAGE = "ms"

# ---------------------------------------------------------------------------
# SYSTEM PROMPT PENUH (rujukan tunggal / single source of truth)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = r"""
QA SYSTEM PROMPT

ROLE
Anda ialah QA System.
Anda mengaudit hasil kerja setiap agent.
Anda tidak menerima pengakuan.
Anda menerima bukti.

PRINCIPLES
- Bukti mengatasi dakwaan.
- Lalai verdict ialah NEEDS_WORK.
- Tiada lulus tanpa bukti.
- QA tidak membaiki kerja; QA melapor dan mengembalikan.

QA PROCESS
1. Terima output bersama acceptance_criteria.
2. Semak kewujudan bukti bagi setiap kriteria.
3. Uji setiap kriteria satu-satu.
4. Semak kepatuhan terhadap undang-undang tetap dan standard.
5. Rekod keputusan dengan bukti.
6. Kembalikan verdict kepada orchestrator.

VERDICT
- PASSED: semua kriteria dipenuhi dengan bukti.
- NEEDS_WORK: bukti tidak cukup atau sebahagian kriteria gagal.
- FAILED: kriteria utama gagal.
- BLOCKED: tidak boleh dinilai (input hilang / dependensi gagal).

EVIDENCE STANDARD
Bukti sah mestilah:
- Boleh diperiksa semula (laluan fail, log, output sebenar)
- Berkaitan terus dengan kriteria
- Boleh dijejaki (bertarikh / ada sumber)
- Bukan andaian dan bukan pengakuan

Tidak sah sebagai bukti:
"sudah siap", "dah diuji", "patut berfungsi", "rasanya lulus".

QUALITY GATE CHECKLIST
✓ Semua kriteria diuji
✓ Bukti dilampirkan bagi setiap kriteria
✓ Tiada isu kritikal terbuka
✓ Dokumentasi lengkap
✓ Boleh diulang (reproducible)

REPORT FORMAT
- task_id
- verdict
- criteria_checked
- evidence
- gaps
- recommended_action

ESCALATION
- FAILED atau BLOCKED dihantar kepada Recovery System.
- NEEDS_WORK dikembalikan kepada agent berkenaan melalui orchestrator.
- QA tidak menandakan projek selesai; itu kuasa Completion System.
"""

# ---------------------------------------------------------------------------
# SKEMA
# ---------------------------------------------------------------------------

VERDICTS: tuple[str, ...] = (
    "PASSED",
    "NEEDS_WORK",
    "FAILED",
    "BLOCKED",
)

EVIDENCE_RULES: tuple[str, ...] = (
    "boleh diperiksa semula",
    "berkaitan terus dengan kriteria",
    "boleh dijejaki",
    "bukan pengakuan",
)

GATE_CHECKLIST: tuple[str, ...] = (
    "semua kriteria diuji",
    "bukti dilampirkan",
    "tiada isu kritikal terbuka",
    "dokumentasi lengkap",
    "boleh diulang",
)

INVALID_EVIDENCE_PHRASES: tuple[str, ...] = (
    "sudah siap",
    "dah diuji",
    "patut berfungsi",
    "rasanya lulus",
)

REPORT_FIELDS: tuple[str, ...] = (
    "task_id",
    "verdict",
    "criteria_checked",
    "evidence",
    "gaps",
    "recommended_action",
)

Verdict = Literal["PASSED", "NEEDS_WORK", "FAILED", "BLOCKED"]


@dataclass(slots=True)
class QAReport:
    """Laporan QA — tiada verdict tanpa bukti."""

    task_id: str
    criteria_checked: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    recommended_action: str = ""
    verdict: Verdict = "NEEDS_WORK"


# ---------------------------------------------------------------------------
# ENJIN KEPUTUSAN
# ---------------------------------------------------------------------------


def is_evidence_valid(evidence: str) -> bool:
    """Bukti mesti substantif dan bukan frasa pengakuan."""
    text = (evidence or "").strip().lower()
    if len(text) < 8:
        return False
    return not any(p in text for p in INVALID_EVIDENCE_PHRASES)


def decide_verdict(report: QAReport, blocked: bool = False) -> Verdict:
    """Lalai NEEDS_WORK. PASSED hanya bila setiap kriteria ada bukti sah."""
    if blocked:
        return "BLOCKED"
    valid = [e for e in report.evidence if is_evidence_valid(e)]
    if not report.criteria_checked or not valid:
        return "NEEDS_WORK"
    if report.gaps:
        return "FAILED" if len(report.gaps) >= len(report.criteria_checked) else "NEEDS_WORK"
    if len(valid) < len(report.criteria_checked):
        return "NEEDS_WORK"
    return "PASSED"


def gate_checklist_complete(checked: dict[str, bool]) -> bool:
    return all(checked.get(item, False) for item in GATE_CHECKLIST)


if __name__ == "__main__":
    print(SYSTEM_NAME, SYSTEM_VERSION)
    print(SYSTEM_PROMPT)
```
