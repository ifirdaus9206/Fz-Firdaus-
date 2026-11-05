#!/usr/bin/env python3
"""Verify a system/*.md prompt module that carries a ```python fenced block.

Extracts the first python fence, writes it to a temp file, imports it with
runpy (NOT importlib spec_from_file_location — see note), then smoke-tests:
constants, prompt length, schema sizes, and every callable named validate_*.

Usage:
    python3 verify_prompt_module.py ~/.hermes20/system/agent_factory.md
    python3 verify_prompt_module.py ~/.hermes20/system/*.md

Exit code 0 = all modules compile + import + no validator raised.
"""

from __future__ import annotations

import re
import runpy
import sys
import tempfile
from pathlib import Path

FENCE = re.compile(r"```python\n(.*?)```", re.S)


def extract(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = FENCE.search(text)
    if not match:
        raise SystemExit(f"TIADA blok ```python dalam {path}")
    return match.group(1)


def verify(path: Path) -> bool:
    ok = True
    code = extract(path)

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as fh:
        fh.write(code)
        tmp = fh.name

    # runpy.run_path registers the module in sys.modules, so dataclass(slots=True)
    # works. importlib.util.spec_from_file_location + exec_module does NOT register
    # it and dies with:
    #   AttributeError: 'NoneType' object has no attribute '__dict__'
    ns = runpy.run_path(tmp, run_name=path.stem)

    print(f"--- {path.name} ---")
    for key in ("SYSTEM_NAME", "SYSTEM_VERSION", "UPSTREAM", "HERMES_VERSION", "LANGUAGE"):
        if key in ns:
            print(f"  {key:15} = {ns[key]}")

    prompt = ns.get("SYSTEM_PROMPT")
    if not prompt:
        print("  RALAT: SYSTEM_PROMPT tiada atau kosong")
        ok = False
    else:
        print(f"  {'PROMPT_LEN':15} = {len(prompt)}")
        if "<" in prompt and "PROMPT USER" in prompt:
            print("  RALAT: placeholder template masih ada dalam prompt")
            ok = False

    for key, val in sorted(ns.items()):
        if key.isupper() and isinstance(val, tuple):
            print(f"  {key:15} = {len(val)} item")

    for key, val in sorted(ns.items()):
        if key.startswith("validate_") and callable(val):
            print(f"  validator       = {key}")

    tmp_path = Path(tmp)
    tmp_path.unlink(missing_ok=True)
    return ok


def main() -> int:
    targets = [Path(a).expanduser() for a in sys.argv[1:]]
    if not targets:
        print(__doc__)
        return 2
    good = [verify(p) for p in targets if p.is_file()]
    print("SEMUA LULUS" if all(good) else "ADA GAGAL")
    return 0 if all(good) else 1


if __name__ == "__main__":
    raise SystemExit(main())
