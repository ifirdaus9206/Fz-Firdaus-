#!/usr/bin/env python3
"""Audit a markdown-link wiki (`[teks](../fail.md)`) — the style used by SOP /
knowledge_base vaults that must stay readable outside Obsidian.

Usage:
    python3 verify_md_links.py [path] [--fm tajuk,jenis,kemas_kini,sumber]

Checks, per file:
  * relative markdown links ending in .md resolve on disk
    (os.path.normpath(join(dirname(file), target)) — never cwd-relative)
  * optional: YAML frontmatter parses and contains every required key
  * optional: H1 title present

Exit 1 on any broken link or missing frontmatter key. Prints the one-line
verdict the report format needs:  "jumlah pautan: N rosak: 0"
"""
import os
import re
import sys

LINK_RE = re.compile(r"\]\(([^)]+\.md)\)")


def main(argv):
    path = "."
    fm_keys = []
    for a in argv[1:]:
        if a.startswith("--fm"):
            continue
        if argv[argv.index(a) - 1] == "--fm":
            fm_keys = [k.strip() for k in a.split(",") if k.strip()]
        elif not a.startswith("-"):
            path = a
    root = os.path.abspath(path)
    if not os.path.isdir(root):
        print(f"not a directory: {root}")
        return 2

    files, links, bad, fm_bad = [], 0, [], []
    for dirpath, _dirs, names in os.walk(root):
        for n in sorted(names):
            if not n.endswith(".md"):
                continue
            p = os.path.join(dirpath, n)
            rel = os.path.relpath(p, root)
            files.append(rel)
            with open(p, encoding="utf-8") as fh:
                text = fh.read()

            for target in LINK_RE.findall(text):
                links += 1
                dest = os.path.normpath(os.path.join(os.path.dirname(p), target))
                if not os.path.exists(dest):
                    bad.append((rel, target))

            if fm_keys:
                if not text.startswith("---"):
                    fm_bad.append((rel, "frontmatter hilang"))
                    continue
                body = text.split("---", 2)[1]
                try:
                    import yaml

                    data = yaml.safe_load(body) or {}
                except Exception as exc:  # noqa: BLE001
                    fm_bad.append((rel, f"YAML rosak: {exc}"))
                    continue
                missing = [k for k in fm_keys if k not in data]
                if missing:
                    fm_bad.append((rel, "kunci hilang: " + ",".join(missing)))
                if not re.search(r"^# .+$", text, re.M):
                    fm_bad.append((rel, "H1 tiada"))

    print(f"root: {root}")
    print(f"fail .md: {len(files)}")
    for rel, target in bad:
        print(f"ROSAK: {rel} -> {target}")
    for rel, why in fm_bad:
        print(f"FRONTMATTER: {rel} -> {why}")
    print(f"jumlah pautan: {links} rosak: {len(bad)}")
    return 1 if (bad or fm_bad) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
