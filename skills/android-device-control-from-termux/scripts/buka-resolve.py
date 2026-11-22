#!/data/data/com.termux/files/usr/bin/python3
"""Resolve + launch an Android app from Termux when aapt/resolve-activity are blocked.

Usage:
  python3 buka-resolve.py <query>              # resolve then launch (cached)
  python3 buka-resolve.py --list <query>       # packages matching query
  python3 buka-resolve.py --component <pkg>    # print launcher component only
  python3 buka-resolve.py --url https://x      # ACTION_VIEW
  python3 buka-resolve.py --home | --settings

Cache: ~/.cache/buka.json   (pkg -> activity)

Why this exists: `cmd package resolve-activity` needs INTERACT_ACROSS_USERS, `pm dump` needs DUMP,
`am start -a MAIN -c LAUNCHER -p <pkg>` answers "unable to resolve Intent" under package visibility,
and guessing class names returns "Error type 3". The APK manifest is world-readable, so read the
string pool and validate candidates with `am start -W` (prints "Status: ok" only on a real launch).
"""
import json
import os
import re
import subprocess
import sys
import zipfile

CACHE = os.path.expanduser("~/.cache/buka.json")
# launcher classes that do NOT start with the package name
SPECIAL = {"com.android.chrome": "com.google.android.apps.chrome.Main"}


def sh(*args):
    try:
        return subprocess.run(list(args), capture_output=True, text=True, timeout=60).stdout
    except Exception as exc:  # pragma: no cover
        return "ERR:%s" % exc


def packages():
    out = sh("pm", "list", "packages")
    return [l.split(":", 1)[1].strip() for l in out.splitlines() if l.startswith("package:")]


def find_pkg(query):
    q = query.lower()
    exact = [p for p in packages() if p.lower() == q]
    if exact:
        return exact[0]
    hits = [p for p in packages() if q in p.lower()]
    hits.sort(key=lambda p: (p.count("."), len(p)))
    return hits[0] if hits else None


def activities(pkg):
    lines = sh("pm", "path", pkg).strip().splitlines()
    if not lines:
        return []
    apk = lines[0].replace("package:", "")          # split installs: first line = base.apk
    if not os.path.isfile(apk):
        return []
    try:
        data = zipfile.ZipFile(apk).read("AndroidManifest.xml")
    except Exception:
        return []
    names = set()
    for m in re.finditer(rb"(?:[\x20-\x7e]\x00){5,}", data):
        s = re.sub(r"^[^A-Za-z]+", "", m.group(0).decode("utf-16le", "ignore"))
        s = re.sub(r"[^A-Za-z0-9_.]+$", "", s)
        if s.endswith("Activity") and "/" not in s and 6 < len(s) < 120:
            if "." not in s:
                s = pkg + "." + s
            if s.startswith(pkg):
                names.add(s)

    def score(n):
        low = n.rsplit(".", 1)[-1].lower()
        if low in ("mainactivity", "launcheractivity"):
            return 0
        if "launcher" in low:
            return 1
        if low.startswith("main"):
            return 2
        if "splash" in low:
            return 3
        if "home" in low:
            return 4
        return 5

    return sorted(names, key=lambda n: (score(n), len(n)))[:15]


def attempt(pkg, cls):
    out = sh("am", "start", "-W", "-n", "%s/%s" % (pkg, cls))
    return "Status: ok" in out


def resolve(pkg):
    cache = {}
    if os.path.exists(CACHE):
        try:
            cache = json.load(open(CACHE))
        except Exception:
            cache = {}
    if pkg in cache and attempt(pkg, cache[pkg]):
        return cache[pkg]
    cands = ([SPECIAL[pkg]] if pkg in SPECIAL else []) + activities(pkg)
    for cls in cands:
        if attempt(pkg, cls):
            cache[pkg] = cls
            os.makedirs(os.path.dirname(CACHE), exist_ok=True)
            json.dump(cache, open(CACHE, "w"), indent=1)
            return cls
    return None


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    flag = argv[0]
    if flag == "--list":
        q = argv[1].lower() if len(argv) > 1 else ""
        for p in packages():
            if q in p.lower():
                print(p)
        return 0
    if flag == "--url" and len(argv) > 1:
        print(sh("am", "start", "-a", "android.intent.action.VIEW", "-d", argv[1]).strip())
        return 0
    if flag == "--home":
        print(sh("am", "start", "-a", "android.intent.action.MAIN",
                 "-c", "android.intent.category.HOME").strip())
        return 0
    if flag == "--settings":
        print(sh("am", "start", "-a", "android.settings.SETTINGS").strip())
        return 0
    if flag == "--component":
        pkg = find_pkg(argv[1]) if len(argv) > 1 else None
        if not pkg:
            print("pakej tidak dijumpai")
            return 1
        print("%s/%s" % (pkg, resolve(pkg) or "TIDAK DIJUMPAI"))
        return 0
    pkg = find_pkg(flag)
    if not pkg:
        print("Tidak jumpa app untuk '%s' — cuba --list <kata>" % flag)
        return 1
    cls = resolve(pkg)
    print("OK %s/%s" % (pkg, cls) if cls else "GAGAL: tiada launcher activity untuk %s" % pkg)
    return 0 if cls else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
