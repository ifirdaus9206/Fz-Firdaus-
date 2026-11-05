#!/usr/bin/env python3
"""Per-line duplicate-link audit for markdown-link wikis (index.md, README tables).

Why this exists: `grep -c "x.md" file` counts *lines* containing x.md, not
occurrences -- so it can never prove "no duplicated link on one line". Only a
per-line Counter can. Task briefs routinely quote a grep -c number that is
internally inconsistent with that requirement; measure, don't inherit.

Usage:
    python3 audit_md_link_dupes.py <file-or-dir> [--resolve]

Prints:
    baris / jumlah_pautan / duplikat_dalam_baris / rujukan_ke:<target> / sasaran_hilang
Exit code 1 if any duplicate exists on a single line or (with --resolve) a
relative fakta|sop|templat target is missing.
"""
import os
import re
import sys
import collections

LINK = re.compile(r"\[[^\]]*\]\(([^)]+\.md)\)")


def audit(path, resolve=False):
    text = open(path, encoding="utf-8").read()
    lines = text.split("\n")
    total = 0
    targets = []
    dupes = []
    for i, line in enumerate(lines, 1):
        links = LINK.findall(line)
        total += len(links)
        targets.extend((i, t) for t in links)
        for target, n in collections.Counter(links).items():
            if n > 1:
                dupes.append((i, target, n))
    print(f"fail: {path}")
    print(f"baris: {len([l for l in lines if l])}")
    print(f"jumlah_pautan_md: {total}")
    print("duplikat_dalam_baris:",
          dupes if dupes else "tiada pautan berganda dalam baris")
    by_target = collections.Counter(t for _, t in targets)
    for target, n in sorted(by_target.items()):
        rows = [i for i, t in targets if t == target]
        print(f"rujukan_ke:{target} = {n} kemunculan di baris {rows}")
    missing = []
    if resolve:
        base = os.path.dirname(os.path.abspath(path))
        for _, t in targets:
            if t.startswith(("fakta/", "sop/", "templat/", "docs/", "../")):
                if not os.path.exists(os.path.normpath(os.path.join(base, t))):
                    missing.append(t)
    print("sasaran_hilang:", sorted(set(missing)) if missing else "tiada")
    return 1 if dupes or missing else 0


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    args = [a for a in argv if not a.startswith("--")]
    resolve = "--resolve" in argv
    files = []
    for a in args:
        if os.path.isdir(a):
            for root, _, names in os.walk(a):
                files += [os.path.join(root, n) for n in names if n.endswith(".md")]
        else:
            files.append(a)
    rc = 0
    for f in sorted(files):
        rc |= audit(f, resolve)
        print("-" * 60)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
