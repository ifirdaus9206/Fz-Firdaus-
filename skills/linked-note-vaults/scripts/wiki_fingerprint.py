#!/usr/bin/env python3
"""Fingerprint a markdown wiki so a before/after diff proves you did not touch it.

Use when only a *report* may be edited: run this before and after the report
edits, then paste both blocks. Identical md5 + counts = proof of non-mutation.

Usage:
    python3 wiki_fingerprint.py knowledge_base
    python3 wiki_fingerprint.py knowledge_base --keys tajuk,jenis,kemas_kini
    python3 wiki_fingerprint.py knowledge_base --links-only

Prints:
    fail .md: N
    jumlah pautan .md: N | rosak: M
    <md5>  <path>            (one line per .md page, sorted)
Optional --keys also reports YAML frontmatter presence/parse errors per page.
Exit code 1 if any relative .md link is broken (so it doubles as a gate).
"""
import hashlib
import os
import re
import sys

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def walk(root):
    pages = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            if name.endswith(".md"):
                pages.append(os.path.join(dirpath, name))
    return sorted(pages)


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = [a for a in argv[1:] if a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    root = args[0]
    if not os.path.isdir(root):
        print("not a directory: %s" % root)
        return 2

    keys = None
    for f in flags:
        if f.startswith("--keys="):
            keys = [k.strip() for k in f.split("=", 1)[1].split(",") if k.strip()]

    pages = walk(root)
    total = 0
    broken = []
    for page in pages:
        with open(page, encoding="utf-8") as fh:
            text = fh.read()
        for m in LINK_RE.finditer(text):
            target = m.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            rel = target.split("#")[0].strip()
            if not rel.lower().endswith(".md"):
                continue
            total += 1
            resolved = os.path.normpath(os.path.join(os.path.dirname(page), rel))
            if not os.path.isfile(resolved):
                broken.append((page, rel))

    print("fail .md: %d" % len(pages))
    print("jumlah pautan .md: %d | rosak: %d" % (total, len(broken)))
    for page, rel in broken:
        print("ROSAK %s -> %s" % (page, rel))

    if "--links-only" not in flags:
        for page in pages:
            print("%s  %s" % (md5(page), page))

    if keys:
        try:
            import yaml
        except ImportError:
            print("yaml: PyYAML tiada — langkau semakan frontmatter")
        else:
            for page in pages:
                with open(page, encoding="utf-8") as fh:
                    text = fh.read()
                if not text.startswith("---"):
                    print("FM %s: tiada frontmatter" % page)
                    continue
                _, fm, _ = text.split("---", 2)
                try:
                    data = yaml.safe_load(fm) or {}
                except Exception as exc:  # noqa: BLE001 - report, do not crash
                    print("FM %s: RALAT %s" % (page, exc))
                    continue
                missing = [k for k in keys if k not in data]
                status = "OK" if not missing else "KURANG %s" % ",".join(missing)
                print("FM %s %s" % (page, status))

    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
