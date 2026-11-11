#!/usr/bin/env python3
"""List class / activity / component names inside a system APK manifest, without aapt.

Why: `aapt dump xmltree /system_ext/priv-app/Settings/Settings.apk --file AndroidManifest.xml`
dies with "ERROR: dump failed because the resource table is invalid/corrupt" on HyperOS builds, and
`cmd package resolve-activity` / `dumpsys package` are blocked for the Termux uid. The manifest is
binary AXML, but every android:name lands in its UTF-16LE string pool, which is trivially grep-able.

Usage:
    python3 axml-classnames.py <apk-or-manifest> [substring ...]

    # what wireless/debug surfaces does HyperOS Settings even have?
    python3 axml-classnames.py /system_ext/priv-app/Settings/Settings.apk wireless debug

    # find the launcher activity of a user app
    python3 axml-classnames.py "$(pm path com.foo | head -1 | sed 's/^package://')" MainActivity

Then probe candidate components (see references/package-presence-and-adb-pairing.md):
    am start -n com.android.settings/.Settings$DevelopmentSettingsActivity
    # "Error type 3 / does not exist" = wrong guess; plain "Starting:" with no error = exists
    # (but a backgrounded Termux still may not get it on screen).

Exit codes: 0 ok (even with zero matches), 2 bad input.
"""
import re
import sys
import zipfile
from pathlib import Path

# UTF-16LE runs of printable ASCII, >= 4 chars. Class names are ASCII in practice.
UTF16_RUN = re.compile(rb"(?:[\x20-\x7e]\x00){4,}")


def manifest_bytes(path: Path) -> bytes:
    if path.is_file() and zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if name == "AndroidManifest.xml":
                    return z.read(name)
        raise SystemExit(f"no AndroidManifest.xml inside {path}")
    return path.read_bytes()


def strings(data: bytes) -> list[str]:
    return sorted({m.group().decode("utf-16le") for m in UTF16_RUN.finditer(data)})


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__.strip().splitlines()[0])
        return 2
    path = Path(argv[1])
    if not path.exists():
        print(f"not found: {path}")
        return 2
    needles = [a.lower() for a in argv[2:]]
    pool = strings(manifest_bytes(path))
    # Component-looking names: dotted, no spaces (package/class/resource ids).
    hits = [s for s in pool if "." in s and " " not in s]
    for n in needles:
        hits = [s for s in hits if n in s.lower()]
    for h in hits:
        print(h)
    print(f"# {len(hits)} match(es) of {len(pool)} pooled strings from {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
