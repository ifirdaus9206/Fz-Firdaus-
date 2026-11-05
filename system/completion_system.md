# system/completion_system.md
# Completion System Prompt — modul Python (boleh di-import)
# Pemilik: Ketua (Orchestrator Utama) · Hermes Agent v0.20.0 (2026.8.3) · upstream 3f2afed3
#
# STATUS: TERISI — prompt v2.0 (dibina oleh Ketua, 27 Okt) — menunggu semakan pengguna.
# Versi lama: ~/.hermes20/archive/system-backup-2026-10-27/

```python
"""completion_system — definisi selesai dan verdict akhir.

Modul ini menyimpan system prompt Completion System dalam bentuk konstanta
Python supaya boleh dimuatkan oleh orchestrator dan qa_system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SYSTEM_NAME = "completion_system"
SYSTEM_VERSION = "2.0.0"
UPSTREAM = "3f2afed3"
HERMES_VERSION = "0.20.0"
LANGUAGE = "ms"

# ---------------------------------------------------------------------------
# SYSTEM PROMPT PENUH (rujukan tunggal / single source of truth)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = r"""
COMPLETION SYSTEM PROMPT

ROLE
Anda ialah Completion System.
Anda mengesahkan projek selesai bagi pihak Ketua.
Anda tidak menerima status "hampir siap".
Anda tidak menutup projek atas dasar pengakuan.

DEFINITION OF DONE
Projek dianggap selesai hanya apabila semua 6 kotak ditanda dengan bukti:
✓ Semua task selesai dan berstatus PASSED
✓ Semua QA lulus
✓ Semua deliverables lengkap
✓ Semua dokumentasi lengkap
✓ Semua laporan lengkap
✓ Semua gate fasa telah dibuka

VERIFICATION PROCESS
1. Kumpul bukti bagi setiap kotak.
2. Semak setiap bukti boleh diperiksa semula.
3. Semak tiada task terbuka atau BLOCKED.
4. Semak tiada eskalasi belum selesai.
5. Semak laporan akhir lengkap.
6. Keluarkan verdict.

VERDICT
- COMPLETE: 6/6 kotak ditanda dengan bukti.
- INCOMPLETE: ada kotak tanpa bukti — senaraikan dan kembalikan ke fasa berkaitan.
- BLOCKED: ada kegagalan tidak dapat dipulihkan selepas 3 percubaan.

FINAL REPORT FORMAT
- project_objective
- agents_created
- tasks_completed
- qa_results
- deliverables
- documentation
- open_risks
- verdict
- evidence_index

CLOSING RULES
- Tiada verdict COMPLETE tanpa evidence_index.
- Tiada kotak ditanda atas dasar pengakuan.
- Jika satu kotak gagal, keseluruhan verdict bukan COMPLETE.
- Selepas COMPLETE: projek dikunci; perubahan hanya melalui projek baharu.

OUTPUT STRUCTURE
reports/
└── completion/
    ├── final_report.md
    └── evidence_index.md
"""

# ---------------------------------------------------------------------------
# SKEMA
# ---------------------------------------------------------------------------

DONE_CHECKS: tuple[str, ...] = (
    "semua task selesai dan PASSED",
    "semua qa lulus",
    "semua deliverables lengkap",
    "semua dokumentasi lengkap",
    "semua laporan lengkap",
    "semua gate fasa telah dibuka",
)

VERDICTS: tuple[str, ...] = (
    "COMPLETE",
    "INCOMPLETE",
    "BLOCKED",
)

FINAL_REPORT_FIELDS: tuple[str, ...] = (
    "project_objective",
    "agents_created",
    "tasks_completed",
    "qa_results",
    "deliverables",
    "documentation",
    "open_risks",
    "verdict",
    "evidence_index",
)

Verdict = Literal["COMPLETE", "INCOMPLETE", "BLOCKED"]

INVALID_EVIDENCE_PHRASES: tuple[str, ...] = (
    "sudah siap",
    "dah siap",
    "dah diuji",
    "patut berfungsi",
    "rasanya lulus",
    "hampir siap",
)


@dataclass(slots=True)
class FinalReport:
    """Laporan akhir — setiap kotak perlu bukti, bukan pengakuan."""

    project_objective: str
    agents_created: list[str] = field(default_factory=list)
    tasks_completed: list[str] = field(default_factory=list)
    qa_results: dict[str, str] = field(default_factory=dict)
    deliverables: list[str] = field(default_factory=list)
    documentation: list[str] = field(default_factory=list)
    open_risks: list[str] = field(default_factory=list)
    evidence_index: dict[str, str] = field(default_factory=dict)
    verdict: Verdict = "INCOMPLETE"


# ---------------------------------------------------------------------------
# ENJIN VERDICT
# ---------------------------------------------------------------------------


def is_evidence_valid(evidence: str) -> bool:
    """Bukti mesti substantif dan bukan frasa pengakuan."""
    text = (evidence or "").strip().lower()
    if len(text) < 8:
        return False
    return not any(p in text for p in INVALID_EVIDENCE_PHRASES)


def missing_checks(evidence: dict[str, str]) -> list[str]:
    """Kotak tanpa bukti sah — pengakuan tidak dikira."""
    return [c for c in DONE_CHECKS if not is_evidence_valid(evidence.get(c) or "")]


def decide_verdict(evidence: dict[str, str], blocked: bool = False) -> Verdict:
    """6/6 kotak dengan bukti = COMPLETE. Selain itu bukan COMPLETE."""
    if blocked:
        return "BLOCKED"
    return "INCOMPLETE" if missing_checks(evidence) else "COMPLETE"


def build_final_report(report: FinalReport, evidence: dict[str, str], blocked: bool = False) -> dict:
    """Hasilkan laporan akhir lengkap 9 medan dengan verdict dikira, bukan diakui."""
    report.verdict = decide_verdict(evidence, blocked=blocked)
    report.evidence_index = dict(evidence)
    payload = {name: getattr(report, name) for name in FINAL_REPORT_FIELDS}
    errors: list[str] = []
    for name in FINAL_REPORT_FIELDS:
        value = payload[name]
        if value is None or (isinstance(value, (str, list, dict)) and len(value) == 0):
            if name != "open_risks":
                errors.append(f"medan laporan kosong: {name}")
    payload["errors"] = errors
    payload["allowed_to_close"] = report.verdict == "COMPLETE" and not errors
    return payload


if __name__ == "__main__":
    print(SYSTEM_NAME, SYSTEM_VERSION)
    print(SYSTEM_PROMPT)
```
