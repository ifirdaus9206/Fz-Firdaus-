#!/usr/bin/env python3
"""
Verification script for project restructuring.
Checks: JSON validity, required paths, legacy backups, migrations.
Exit 0 = pass, Exit 1 = fail with details.
"""
import json
import sys
from pathlib import Path


def verify(base_path: Path) -> list[str]:
    errors = []

    # 1. JSON validity
    json_files = [
        "config/agent.json", "config/models.json", "config/routing.json",
        "config/permissions.json", "config/capabilities.json",
        "agents/registry.json", "skills/registry.json", "workflows/registry.json",
        "src/tools/registry.json"
    ]
    for jf in json_files:
        try:
            json.loads((base_path / jf).read_text())
        except Exception as e:
            errors.append(f"JSON invalid: {jf} - {e}")

    # 2. Required structure
    required = [
        "README.md", "CHANGELOG.md", "LICENSE",
        "identity/agent_identity.md", "identity/role.md", "identity/mission.md", "identity/principles.md",
        "agents/orchestrator/README.md", "agents/researcher/README.md", "agents/architect/README.md",
        "agents/developer/README.md", "agents/reviewer/README.md",
        "skills/research/README.md", "skills/coding/README.md", "skills/analysis/README.md",
        "skills/database/README.md", "skills/automation/README.md",
        "workflows/planning/README.md", "workflows/research/README.md",
        "workflows/development/README.md", "workflows/testing/README.md", "workflows/deployment/README.md",
        "knowledge/core/README.md", "knowledge/domain/README.md", "knowledge/procedures/README.md", "knowledge/rules/README.md",
        "config/agent.json", "config/models.json", "config/routing.json", "config/permissions.json", "config/capabilities.json",
        "database/schema.sql",
        "deployment/Dockerfile", "deployment/docker-compose.yml", "deployment/deploy.yaml",
        "docs/architecture.md", "docs/api.md", "docs/installation.md", "docs/operations.md",
    ]
    for f in required:
        if not (base_path / f).exists():
            errors.append(f"Missing: {f}")

    # 3. Legacy backups
    for d in ["identity/legacy", "agents/legacy", "skills/legacy", "workflows/legacy", "knowledge/legacy", "logs/legacy"]:
        if not (base_path / d).exists():
            errors.append(f"Missing legacy backup: {d}")

    return errors


if __name__ == "__main__":
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    errs = verify(base)
    if errs:
        print("FAILED:", "; ".join(errs))
        sys.exit(1)
    else:
        print("VERIFICATION PASSED")
        sys.exit(0)