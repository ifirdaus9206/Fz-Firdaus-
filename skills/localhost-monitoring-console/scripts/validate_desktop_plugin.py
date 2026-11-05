#!/usr/bin/env python3
"""
Validate a Hermes Desktop runtime plugin against the loader's rules.

Checks:
  1. ESM syntax (node --check on a .mjs copy)
  2. every bare import is in the SDK import map (no third-party packages)
  3. no relative imports (the loader cannot resolve them)
  4. default export with `id` and `register(ctx)`
  5. registered areas are known (maps SDK constants to their area ids)
  6. a route path starting with '/' is registered

Usage: python3 validate_desktop_plugin.py [path/to/plugin.js]
Default: ~/.hermes20/desktop-plugins/hermes-console/plugin.js
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT = Path.home() / ".hermes20" / "desktop-plugins" / "hermes-console" / "plugin.js"
SDK_SPECIFIERS = {"@hermes/plugin-sdk", "react", "react/jsx-runtime", "react/jsx-dev-runtime"}
KNOWN_AREAS = {
    "routes", "sidebar.nav", "statusBar.right", "statusBar.left", "palette",
    "rightColumn.panel", "secondarySidebar", "capabilities.detail.actions",
}
CONST_AREAS = {
    "ROUTES_AREA": "routes",
    "SIDEBAR_NAV_AREA": "sidebar.nav",
    "PALETTE_AREA": "palette",
    "STATUSBAR_AREAS.right": "statusBar.right",
    "STATUSBAR_AREAS.left": "statusBar.left",
}
IMPORT_RE = re.compile(r"(?:from\s*|import\s*\(\s*|import\s+)(['\"])([^'\"]+)\1")
AREA_RE = re.compile(r"area:\s*['\"]([a-zA-Z.]+)['\"]")
PATH_RE = re.compile(r"path:\s*['\"](/[^'\"]*)['\"]")


def ok(cond: bool, msg: str) -> bool:
    print(("OK   " if cond else "GAGAL ") + msg)
    return cond


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    if not path.exists():
        print(f"GAGAL  fail tidak wujud: {path}")
        return 2
    src = path.read_text(encoding="utf-8")
    good = True

    tmpdir = Path(tempfile.mkdtemp())
    tmp = tmpdir / "plugin.mjs"
    shutil.copyfile(path, tmp)
    r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
    good &= ok(r.returncode == 0, f"sintaks ESM ({path.name}, {len(src)} bait)")
    if r.returncode != 0:
        print(r.stderr.strip()[:500])
    shutil.rmtree(tmpdir, ignore_errors=True)

    specs = {m.group(2) for m in IMPORT_RE.finditer(src)}
    bare = {s for s in specs if not s.startswith((".", "/")) and ":" not in s}
    bad = bare - SDK_SPECIFIERS
    good &= ok(not bad, f"import sahaja daripada SDK/react (dijumpai: {', '.join(sorted(specs))})")
    if bad:
        print("       luar peta:", ", ".join(sorted(bad)))
    rel = {s for s in specs if s.startswith(".")}
    good &= ok(not rel, "tiada import relatif")

    good &= ok(bool(re.search(r"export\s+default\s*\{", src)), "ada `export default { ... }`")
    good &= ok("id:" in src, "ada medan `id`")
    good &= ok("register(ctx)" in src or "register:" in src, "ada fungsi `register(ctx)`")

    areas = set(AREA_RE.findall(src))
    for name, area in CONST_AREAS.items():
        if name in src:
            areas.add(area)
    unknown = areas - KNOWN_AREAS
    good &= ok(not unknown, f"area dikenali ({', '.join(sorted(areas))})")
    if unknown:
        print("       tidak dikenali:", ", ".join(sorted(unknown)))

    paths = PATH_RE.findall(src)
    good &= ok(bool(paths) and all(p.startswith("/") for p in paths),
               f"laluan halaman didaftarkan ({', '.join(paths) or 'tiada'})")

    print()
    print("LULUS" if good else "GAGAL — betulkan di atas")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
