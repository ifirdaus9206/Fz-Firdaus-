#!/usr/bin/env python3
"""Measure the proposal body of each radar draft and check the 120-word cap.

The draft header says "## Draf proposal (English, N patah perkataan)". N written by
hand is wrong by a few words almost every time -- measure it instead.

Usage:
  python3 scripts/count_draft_words.py ~/freelance-radar/drafts/2026-11-20-*.md
  python3 scripts/count_draft_words.py --fix ~/freelance-radar/drafts/2026-11-20-*.md

--fix rewrites the header count to the measured value (keeps the rest of the file).
Exit code 1 if any draft exceeds 120 words.
"""
import glob
import re
import sys

CAP = 120
HEADER_RE = re.compile(r"(## Draf proposal[^\n]*?)\(\s*English,\s*\d+\s*patah perkataan\s*\)")


def body_words(text: str) -> int:
    if "## Draf proposal" not in text:
        return 0
    body = text.split("## Draf proposal", 1)[1]
    body = body.split("## Checklist", 1)[0]
    # drop the remainder of the heading line itself
    body = body.split("\n", 1)[1] if "\n" in body else ""
    body = re.sub(r"^\s*\(English.*?\)\s*$", "", body, flags=re.M)
    return len(body.split())


def main(argv):
    fix = "--fix" in argv
    paths = []
    for a in argv:
        if a == "--fix":
            continue
        paths.extend(sorted(glob.glob(a)) or [a])
    if not paths:
        print("usage: count_draft_words.py [--fix] <draft.md ...>")
        return 2

    over = 0
    for p in paths:
        try:
            text = open(p, encoding="utf-8").read()
        except OSError as e:
            print(f"SKIP {p}: {e}")
            continue
        n = body_words(text)
        flag = "OK" if n <= CAP else "TERLALU PANJANG"
        if n > CAP:
            over += 1
        if fix and HEADER_RE.search(text):
            text = HEADER_RE.sub(lambda m: f"{m.group(1)}(English, {n} patah perkataan)", text, count=1)
            open(p, "w", encoding="utf-8").write(text)
        print(f"{p} -> {n} kata {flag}")
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
