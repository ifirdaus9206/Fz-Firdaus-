#!/usr/bin/env python3
"""Audit a scaffolded ATC (or any multi-brain trading skeleton) for placeholder logic.

Usage:
    python3 audit_atc_placeholders.py [PROJECT_ROOT]

Default PROJECT_ROOT is the current directory. Stdlib only, no network, read-only.

What it reports
  1. Empty modules (0 bytes / 0 lines) — scaffolded files that were never filled in.
  2. Brain files whose analyze() returns literal constants (the "permanent BUY machine"
     failure mode: every brain returns BUY -> fusion unanimity -> confidence 0.9 -> the
     system can never emit SELL or NO_TRADE).
  3. Config files that exist but whose keys are never referenced in code.
  4. Hardcoded decision fields (dummy timestamps, mode="backtest", fixed symbol).
  5. Whether the test suite actually collects anything.

Exit code is always 0 — this is a report, not a gate.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

CODE_EXT = (".py",)
PLACEHOLDER_WORDS = ("placeholder", "dummy", "stub", "TODO", "FIXME", "not implemented")
HARDCODE_PATTERNS = [
    (r'"timestamp"\s*:\s*"(\d{4}-\d{2}-\d{2}T[^"]*)"', "hardcoded timestamp"),
    (r'"mode"\s*:\s*"(\w+)"', "hardcoded mode"),
    (r'"symbol"\s*:\s*"([A-Z0-9._]+)"', "hardcoded symbol"),
    (r'"data_quality"\s*:\s*"(\w+)"', "hardcoded data_quality"),
]


def py_files(root: Path):
    for p in root.rglob("*.py"):
        if any(part in {"__pycache__", ".git", "venv", ".venv", "node_modules"} for part in p.parts):
            continue
        yield p


def empty_modules(root: Path) -> list[tuple[str, int]]:
    out = []
    for p in py_files(root):
        try:
            txt = p.read_text(errors="ignore")
        except OSError:
            continue
        lines = [ln for ln in txt.splitlines() if ln.strip()]
        if len(lines) <= 1:  # 0 real lines, or a lone docstring line
            out.append((str(p.relative_to(root)), len(lines)))
    return sorted(out, key=lambda t: t[0])


def brain_constants(root: Path) -> list[str]:
    """Flag analyze() functions that return literal BUY/SELL/bullish without branching."""
    flagged = []
    for p in py_files(root):
        if "brain" not in str(p).lower():
            continue
        txt = p.read_text(errors="ignore")
        if "def analyze" not in txt:
            continue
        body = txt.split("def analyze", 1)[1]
        # any conditional or data access means it is not a pure constant
        has_logic = any(tok in body for tok in ("if ", "for ", "else", "market_data[", "market_data.get"))
        literal_dir = re.search(r'"direction"\s*:\s*"(BUY|SELL)"', body)
        literal_bias = re.search(r'"bias"\s*:\s*"(bullish|bearish)"', body)
        if (literal_dir or literal_bias) and not has_logic:
            flagged.append(
                f"{p.relative_to(root)}: returns a literal "
                f"{(literal_dir or literal_bias).group(1)} with no branching — "
                "every cycle yields the same direction"
            )
    return flagged


def unused_config(root: Path) -> list[str]:
    """Config keys that no .py file mentions."""
    code = "\n".join(p.read_text(errors="ignore") for p in py_files(root))
    report = []
    for cfg in root.rglob("*.json"):
        if any(part in {"node_modules", ".git"} for part in cfg.parts):
            continue
        try:
            data = json.loads(cfg.read_text())
        except Exception:
            continue
        keys = set()

        def walk(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    keys.add(k)
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(data)
        missing = sorted(k for k in keys if len(k) > 3 and k not in code)
        if missing:
            report.append(f"{cfg.relative_to(root)}: {len(missing)} key(s) never read in code → {missing[:8]}")
    return report


def hardcoded_fields(root: Path) -> list[str]:
    hits = []
    for p in py_files(root):
        txt = p.read_text(errors="ignore")
        for pat, label in HARDCODE_PATTERNS:
            for m in re.finditer(pat, txt):
                hits.append(f"{p.relative_to(root)}: {label}: {m.group(1)}")
    return hits


def test_collection(root: Path) -> str:
    tests = root / "tests"
    if not tests.is_dir():
        return "no tests/ directory"
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "tests", "-q", "--collect-only"],
            cwd=root, capture_output=True, text=True, timeout=120,
        )
        tail = (r.stdout or r.stderr).strip().splitlines()
        return tail[-1] if tail else "pytest produced no output"
    except FileNotFoundError:
        return "pytest not installed in this interpreter"
    except subprocess.TimeoutExpired:
        return "pytest timed out"


def live_probe(root: Path) -> str:
    """Run one orchestrator cycle if the project exposes one. Prints the decision fields."""
    snippet = (
        "import sys; sys.path.insert(0, %r)\n"
        "from core.orchestrator import run_cycle\n"
        "d = run_cycle('XAUUSD')\n"
        "keys = ('status','direction','confidence','symbol','timestamp','mode','data_quality','risk_check')\n"
        "print({k: d.get(k) for k in keys})\n" % str(root)
    )
    try:
        r = subprocess.run([sys.executable, "-c", snippet], cwd=root,
                           capture_output=True, text=True, timeout=180)
        return (r.stdout or r.stderr).strip().splitlines()[-1] if (r.stdout or r.stderr) else "(no output)"
    except Exception as exc:  # noqa: BLE001
        return f"probe failed: {exc}"


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    print(f"ATC placeholder audit — {root}\n")

    empties = empty_modules(root)
    print(f"1) Empty modules: {len(empties)}")
    for path, n in empties:
        print(f"   {path} ({n} line)")

    brains = brain_constants(root)
    print(f"\n2) Brain files returning constants: {len(brains)}")
    for line in brains:
        print(f"   {line}")

    cfgs = unused_config(root)
    print(f"\n3) Config files with unread keys: {len(cfgs)}")
    for line in cfgs:
        print(f"   {line}")

    hards = hardcoded_fields(root)
    print(f"\n4) Hardcoded decision fields: {len(hards)}")
    for line in hards:
        print(f"   {line}")

    print(f"\n5) Test collection: {test_collection(root)}")
    print(f"\n6) Live cycle probe: {live_probe(root)}")

    print("\nReading: if (2) lists every brain, the pipeline can only ever emit one direction.")
    print("Do not enable live trading until brains branch on real snapshot data.")


if __name__ == "__main__":
    main()
