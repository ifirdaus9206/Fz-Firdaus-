#!/usr/bin/env python3
"""Hash-gated completeness check for merging one directory into others.

Answers exactly one question before you `rm -rf` a source directory:

    "Is every file in --src represented in --dst by an identical copy?"

It indexes each destination by (filename, size), walks the source, then SHA256-compares
every candidate match, so a same-name/same-size coincidence cannot pass. Files that were
deliberately renamed during the merge (caches archived as `AINA-models_dev_cache.json`,
etc.) are handled with an explicit --rename map. Files you intentionally skipped
(`--allow`) are reported separately rather than counted as failures.

Exit codes: 0 = every source file accounted for, 1 = gaps found, 2 = bad usage.

Usage
-----
    # simple: verify .OLD is fully present in the live home
    python3 verify_merge_completeness.py --src .AINA --dst .hermes20

    # with renames and intentional skips
    python3 verify_merge_completeness.py \
        --src .AINA --dst .hermes20 \
        --rename models_dev_cache.json=.hermes20/archive/x/_regenerable_cache/AINA-models_dev_cache.json \
        --rename .aina/models_dev_cache.json=.hermes20/archive/x/_regenerable_cache/nested-models_dev_cache.json \
        --allow tirith --allow '*.lock'

    # list the unaccounted files as a copy-pasteable plan instead of failing
    python3 verify_merge_completeness.py --src .AINA --dst .hermes20 --report

Only point this at a source you are ready to delete; it is read-only either way.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import os
import sys
from pathlib import Path

CHUNK = 1 << 20


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(CHUNK)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def index_dest(dest_roots: list[Path]) -> dict[tuple[str, int], list[Path]]:
    """Map (filename, size) -> candidate paths in every destination root."""
    index: dict[tuple[str, int], list[Path]] = {}
    for root in dest_roots:
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                path = Path(dirpath) / name
                try:
                    size = path.stat().st_size
                except OSError:
                    continue
                index.setdefault((name, size), []).append(path)
    return index


def walk_source(src: Path):
    for dirpath, _dirnames, filenames in os.walk(src):
        for name in filenames:
            yield Path(dirpath) / name


def is_allowed(rel: str, name: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(rel, pat) for pat in patterns)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, action="append", help="source dir to account for (repeatable)")
    ap.add_argument("--dst", required=True, action="append", help="destination dir to search (repeatable)")
    ap.add_argument(
        "--rename",
        action="append",
        default=[],
        metavar="REL=ABSPATH",
        help="source file, relative to --src, that was deliberately renamed/moved",
    )
    ap.add_argument(
        "--allow",
        action="append",
        default=[],
        metavar="GLOB",
        help="basename or relative-path glob that was intentionally skipped (e.g. a duplicate binary)",
    )
    ap.add_argument("--report", action="store_true", help="exit 0 and print the gap list instead of failing")
    ap.add_argument("-v", "--verbose", action="store_true", help="print every verified file")
    args = ap.parse_args()

    dst_roots = [Path(d).expanduser() for d in args.dst]
    for root in dst_roots:
        if not root.is_dir():
            print(f"error: --dst is not a directory: {root}", file=sys.stderr)
            return 2

    index = index_dest(dst_roots)
    renamed: dict[str, Path] = {}
    for spec in args.rename:
        if "=" not in spec:
            print(f"error: --rename expects REL=ABSPATH, got {spec!r}", file=sys.stderr)
            return 2
        rel, target = spec.split("=", 1)
        renamed[rel.strip().lstrip("./")] = Path(target).expanduser()

    verified = 0
    hashed = 0
    allowed = 0
    missing: list[tuple[str, int]] = []
    mismatched: list[tuple[str, str]] = []

    for src_root in (Path(s).expanduser() for s in args.src):
        if not src_root.is_dir():
            print(f"error: --src is not a directory: {src_root}", file=sys.stderr)
            return 2

        for path in walk_source(src_root):
            rel = str(path.relative_to(src_root))
            try:
                size = path.stat().st_size
            except OSError:
                continue

            # 1. deliberate rename/move
            if rel in renamed:
                target = renamed[rel]
                if not target.exists():
                    mismatched.append((rel, f"rename target missing: {target}"))
                elif target.stat().st_size != size:
                    mismatched.append((rel, f"rename target size {target.stat().st_size} != {size}"))
                elif sha256(path) != sha256(target):
                    mismatched.append((rel, f"rename target content differs: {target}"))
                else:
                    verified += 1
                    hashed += 1
                    if args.verbose:
                        print(f"ok (renamed)  {rel} -> {target}")
                continue

            # 2. identical copy present in a destination
            candidates = index.get((path.name, size), [])
            match = None
            for cand in candidates:
                try:
                    if sha256(path) == sha256(cand):
                        match = cand
                        break
                except OSError:
                    continue
            if match is not None:
                verified += 1
                hashed += 1
                if args.verbose:
                    print(f"ok            {rel}  ==  {match}")
                continue

            # 3. intentionally skipped
            if is_allowed(rel, path.name, args.allow):
                allowed += 1
                if args.verbose:
                    print(f"skipped       {rel}  (--allow)")
                continue

            missing.append((rel, size))

    total = verified + allowed + len(missing) + len(mismatched)
    print(f"source files scanned : {total}")
    print(f"verified identical   : {verified}  (sha256 checked: {hashed})")
    print(f"intentionally skipped: {allowed}")
    print(f"unaccounted          : {len(missing)}")
    print(f"rename mismatches    : {len(mismatched)}")

    for rel, detail in mismatched:
        print(f"  MISMATCH  {rel}  ->  {detail}")
    for rel, size in missing[:200]:
        print(f"  MISSING   {rel}  ({size} bytes)")
    if len(missing) > 200:
        print(f"  … and {len(missing) - 200} more")

    if not missing and not mismatched:
        print("\nRESULT: complete — safe to delete the source.")
        return 0

    print("\nRESULT: gaps found — DO NOT delete the source yet.")
    return 0 if args.report else 1


if __name__ == "__main__":
    sys.exit(main())
