# system/<NAME>.md
# <TITLE> System Prompt — modul Python (boleh di-import)
# Pemilik: Ketua (Orchestrator Utama) · Hermes Agent v0.20.0 (2026.8.3) · upstream 3f2afed3
#
# STATUS: TERISI — prompt baru (v2.0) dimasukkan oleh pengguna <TARIKH>.
# Versi lama: ~/.hermes20/archive/system-backup-<TARIKH>/

```python
"""<NAME> — <one-line role of this system.

Modul ini menyimpan system prompt <TITLE> dalam bentuk konstanta Python
supaya boleh dimuatkan oleh sistem lain dalam pipeline Ketua.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SYSTEM_NAME = "<NAME>"
SYSTEM_VERSION = "2.0.0"
UPSTREAM = "3f2afed3"
HERMES_VERSION = "0.20.0"
LANGUAGE = "ms"

# ---------------------------------------------------------------------------
# SYSTEM PROMPT PENUH (rujukan tunggal / single source of truth)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = r"""
<PROMPT USER, VERBATIM>

Pengecualian: kemas format sahaja — nombor senarai, bullet `-`, dan setiap `✓` pada baris
sendiri. Jangan ubah, tambah, atau buang satu perkataan pun.
"""

# ---------------------------------------------------------------------------
# SKEMA
# ---------------------------------------------------------------------------

# Satu tuple[str, ...] per senarai dalam prompt (field output, langkah proses, dll.)
FIELDS: tuple[str, ...] = (
    "field_satu",
    "field_dua",
)


@dataclass(slots=True)
class Spec:
    """Spec satu unit kerja — semua medan wajib, tiada medan boleh kosong."""

    field_satu: str
    field_dua: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# VALIDATOR
# ---------------------------------------------------------------------------


def validate_spec(spec: Spec) -> list[str]:
    """Pulangkan senarai ralat. Senarai kosong = lulus."""
    errors: list[str] = []
    for name in FIELDS:
        value = getattr(spec, name, None)
        if value is None or (isinstance(value, (str, list, tuple)) and len(value) == 0):
            errors.append(f"medan kosong: {name}")
    return errors


if __name__ == "__main__":
    print(SYSTEM_NAME, SYSTEM_VERSION)
    print(SYSTEM_PROMPT)
```
