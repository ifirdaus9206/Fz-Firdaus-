#!/usr/bin/env python3
"""apk-activities.py — enumerate an APK's component names when ADB is unavailable.

Why: with app uid, `pm dump <pkg>`, `cmd package resolve-activity` and `dumpsys package`
are all denied (missing DUMP / INTERACT_ACROSS_USERS), and `aapt` may not be installed.
`pm path <pkg>` still returns the APK path, and the APK is world-readable, so the binary
AndroidManifest.xml can be string-scanned locally.

Usage:
    python3 apk-activities.py com.arlosoft.macrodroid
    python3 apk-activities.py /data/app/.../base.apk --keys extra_ shortcut guid
    python3 apk-activities.py <pkg> --start     # also try `am start -n pkg/.Name`

Output: candidate class names (activities, receivers, services) one per line, then
optional launch validation. "Starting:" alone is NOT success — only the absence of
"Error type 3 / Activity class ... does not exist" is.

Measured 2026-11-20 (HyperOS 3 / Android 16, MacroDroid 91 MB APK): 7 guessed names
(MainActivity, ui.home.HomeActivity, MacroDroidActivity, SplashActivity, …) all returned
Error type 3; the scan found `com.arlosoft.macrodroid.LauncherActivity`, which launched
with rc=0.
"""
from __future__ import annotations

import re
import subprocess
import sys
import zipfile

ASCII_RUN = re.compile(rb"[\x20-\x7e]{6,}")
UTF16_RUN = re.compile(rb"(?:[\x20-\x7e]\x00){6,}")
CLASSISH = re.compile(r"^[A-Za-z][\w$]*(\.[A-Za-z][\w$]*)+$")


def apk_path(arg: str) -> str:
    if arg.endswith(".apk"):
        return arg
    out = subprocess.run(["pm", "path", arg], capture_output=True, text=True).stdout
    first = out.strip().splitlines()[0] if out.strip() else ""
    if not first:
        sys.exit(f"pm path {arg} returned nothing (invisible or not installed)")
    return first.replace("package:", "", 1)


def manifest_strings(apk: str) -> set[str]:
    with zipfile.ZipFile(apk) as z:
        data = z.read("AndroidManifest.xml")
    found: set[str] = set()
    # AXML string pools are stored either as UTF-16LE or as plain 8-bit runs. Scan BOTH;
    # decoding the whole buffer one way only yields offset garbage on the other encoding.
    for m in UTF16_RUN.finditer(data):
        found.add(m.group(0).decode("utf-16-le", "ignore"))
    for m in ASCII_RUN.finditer(data):
        found.add(m.group(0).decode("ascii", "ignore"))
    return found


def main() -> None:
    args = [a for a in sys.argv[1:]]
    if not args:
        sys.exit(__doc__)
    do_start = "--start" in args
    args = [a for a in args if a != "--start"]
    extra_keys: list[str] = []
    if "--keys" in args:
        i = args.index("--keys")
        extra_keys = args[i + 1 :]
        args = args[:i]
    pkg_arg = args[0]
    apk = apk_path(pkg_arg)
    pkg = pkg_arg if not pkg_arg.endswith(".apk") else None
    if pkg is None:  # derive from apk path: .../<pkg>-<hash>/base.apk
        m = re.search(r"/([A-Za-z0-9_.]+)-[^/]+/base\.apk$", apk)
        pkg = m.group(1) if m else None

    strings = manifest_strings(apk)
    comps = sorted(s for s in strings if CLASSISH.match(s) and len(s) < 120)
    print(f"APK: {apk}\npackage: {pkg}\ncandidates: {len(comps)}")
    for c in comps:
        print("  ", c)

    if extra_keys:
        print("\nextra/config keys:")
        for s in sorted(strings):
            low = s.lower()
            if any(k.lower() in low for k in extra_keys) and len(s) < 80:
                print("  ", s)

    if do_start and pkg:
        print("\nlaunch validation (only a missing 'Error type 3' means it exists):")
        short = [c[len(pkg) + 1 :] for c in comps if c.startswith(pkg + ".")]
        for name in short:
            r = subprocess.run(
                ["am", "start", "-n", f"{pkg}/{name}"], capture_output=True, text=True
            )
            out = (r.stdout + r.stderr).strip().splitlines()
            verdict = "exists" if not any("Error" in ln for ln in out) else "missing"
            print(f"  {name:45s} {verdict}")


if __name__ == "__main__":
    main()
