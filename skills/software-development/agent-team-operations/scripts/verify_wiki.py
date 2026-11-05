#!/usr/bin/env python3
"""Audit a markdown knowledge_base: frontmatter, index back-links, broken internal links.

Usage:  python3 verify_wiki.py ~/.hermes20/knowledge_base
Exit 0 = clean, 1 = issues found. Prints one line per issue; paste the output in the report.

Checks
  1. every *.md has frontmatter with the required keys
  2. every *.md links to index.md (directly or via ../index.md)
  3. every ](....md) target resolves on disk
  4. per-file byte size (for the report table)
"""
import os
import re
import sys

REQUIRED = ("tajuk:", "jenis:", "kemas_kini:", "sumber:")
# Strip fenced code blocks first: examples of link syntax inside fences are not real links.
FENCE = re.compile(r"```.*?```", re.S)
LINK = re.compile(r"\]\(([^)\s]+\.md)(?:#[^)]*)?\)")


def frontmatter_ok(text):
    if not text.startswith("---"):
        return False
    end = text.find("\n---", 3)
    if end == -1:
        return False
    head = text[3:end]
    return all(k in head for k in REQUIRED)


def main(base):
    base = os.path.abspath(os.path.expanduser(base))
    if not os.path.isdir(base):
        print(f"ERROR: not a directory: {base}")
        return 1

    pages = sorted(
        os.path.join(root, f)
        for root, _dirs, files in os.walk(base)
        for f in files
        if f.endswith(".md")
    )
    if not pages:
        print("ERROR: no markdown files found")
        return 1

    issues = []
    link_count = 0
    for page in pages:
        rel = os.path.relpath(page, base)
        text = open(page, encoding="utf-8").read()
        if not frontmatter_ok(text):
            issues.append(f"FRONTMATTER {rel}: missing one of {', '.join(REQUIRED)}")
        if "index.md" not in text:
            issues.append(f"NO-INDEX-LINK {rel}")
        body = FENCE.sub("", text)
        for target in LINK.findall(body):
            if target.startswith(("http://", "https://")):
                continue
            link_count += 1
            resolved = os.path.normpath(os.path.join(os.path.dirname(page), target))
            if not os.path.exists(resolved):
                issues.append(f"BROKEN {rel} -> {target}")
        print(f"{rel:34} {os.path.getsize(page):>7} bytes")

    print(f"\nfiles={len(pages)} links={link_count} issues={len(issues)}")
    for issue in issues:
        print("  " + issue)
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "~/.hermes20/knowledge_base"))
