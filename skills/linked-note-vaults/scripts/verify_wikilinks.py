#!/usr/bin/env python3
"""Audit every [[wikilink]] in a markdown vault. Exit 1 if any target is missing.

Usage: python3 verify_wikilinks.py [vault_path]

Resolution rules (mirrors Obsidian's practical behaviour):
  folder/nota        -> folder/nota.md
  nota               -> any file named nota.md; if several, prefer vault root, else first sorted
  alias              -> ignored here; pass --alias map only if you need alias resolution
  [[nota#Seksyen]]   -> heading stripped before resolving
  [[nota|teks]]      -> display text stripped before resolving

Prints one row per link, a unique-target summary, and a per-file link count.
"""
import os
import re
import sys
from collections import Counter

LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def collect(vault):
    files = []
    for root, _dirs, names in os.walk(vault):
        for n in names:
            if n.endswith(".md"):
                files.append(os.path.relpath(os.path.join(root, n), vault))
    return sorted(files)


def main(argv):
    vault = os.path.abspath(argv[1] if len(argv) > 1 else ".")
    if not os.path.isdir(vault):
        print(f"not a directory: {vault}")
        return 2
    files = collect(vault)
    rel = set(files)
    if not files:
        print(f"no markdown files under {vault}")
        return 2

    def resolve(target):
        if "/" in target:
            cand = target if target.endswith(".md") else target + ".md"
            return cand if cand in rel else None
        cands = sorted(f for f in rel if os.path.basename(f) == target + ".md")
        if not cands:
            return None
        root_copy = target + ".md"
        return root_copy if root_copy in cands else cands[0]

    rows, unique, per_file = [], {}, Counter()
    for f in files:
        with open(os.path.join(vault, f), encoding="utf-8") as fh:
            text = fh.read()
        for raw in LINK_RE.findall(text):
            target = raw.split("|")[0].split("#")[0].strip()
            if not target:
                continue
            dest = resolve(target)
            rows.append((f, raw, dest))
            unique.setdefault(target, dest)
            per_file[f] += 1

    print(f"vault: {vault}")
    print(f"files: {len(files)}   links: {len(rows)}   unique targets: {len(unique)}\n")
    width = max((len(r[0]) for r in rows), default=4)
    for f, raw, dest in rows:
        status = "ADA" if dest else "TIADA"
        print(f"{f:<{width}}  [[{raw}]]  ->  {dest or '???'}  {status}")

    print("\n-- unique targets --")
    for t, dest in sorted(unique.items()):
        print(f"[[{t}]] -> {dest or 'TIADA'}")

    print("\n-- links per file --")
    for f in files:
        print(f"{f}: {per_file[f]}")

    broken = [u for u, d in unique.items() if d is None]
    print(f"\nRESULT: {len(unique) - len(broken)}/{len(unique)} unique targets exist; {len(broken)} broken")
    if broken:
        print("BROKEN: " + ", ".join(f"[[{b}]]" for b in broken))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
