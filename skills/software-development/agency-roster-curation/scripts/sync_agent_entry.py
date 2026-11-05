#!/usr/bin/env python3
"""Kemas kini SATU entri agents.json daripada fail persona .md.

Guna:
    python3 sync_agent_entry.py <slug> <laluan-fail.md> [--dry-run]

Yang dikemas kini: description + body (frontmatter dibuang). Kunci lain tidak disentuh.
Backup agents.json dibuat dahulu. Cetak kiraan entri + checksum body untuk pengesahan.

Selepas ini jalankan:
    python3 ~/.hermes20/scripts/sync_agency_catalog.py
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time

HOME = os.path.expanduser("~/.hermes20")
ACTIVE = os.path.join(HOME, "plugins", "agency-agents-router", "data", "agents.json")
FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)
EXPECTED = 282  # katalog disahkan Nov 2026


def parse(path):
    text = open(path, encoding="utf-8").read()
    m = FM.match(text)
    meta, body = {}, text.strip()
    if m:
        body = text[m.end():].strip()
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    return meta, body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("md_path")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if not os.path.exists(a.md_path):
        sys.exit(f"FAIL: tidak jumpa {a.md_path}")
    meta, body = parse(a.md_path)
    if "description" not in meta:
        sys.exit("FAIL: frontmatter tiada medan description")
    if not body:
        sys.exit("FAIL: body kosong selepas frontmatter dibuang")

    data = json.load(open(ACTIVE, encoding="utf-8"))
    hits = [e for e in data if e.get("slug") == a.slug]
    if len(hits) != 1:
        sys.exit(f"FAIL: slug '{a.slug}' jumpa {len(hits)} kali (mesti 1)")
    e = hits[0]

    before = (e.get("description", ""), hashlib.sha256(e.get("body", "").encode()).hexdigest()[:12])
    e["description"] = meta["description"]
    e["body"] = body
    after = (e["description"], hashlib.sha256(e["body"].encode()).hexdigest()[:12])

    print(f"slug          : {a.slug}")
    print(f"desc sebelum  : {before[0][:100]}")
    print(f"desc selepas  : {after[0][:100]}")
    print(f"body sha      : {before[1]} -> {after[1]}")
    print(f"saiz body     : {len(e['body'])} bait")
    print(f"jumlah entri  : {len(data)}" + ("" if len(data) == EXPECTED else f"  !! jangkaan {EXPECTED}"))

    if a.dry_run:
        print("DRY-RUN: tiada fail ditulis")
        return

    bak = f"{ACTIVE}.bak-{time.strftime('%Y%m%d-%H%M')}"
    shutil.copy2(ACTIVE, bak)
    with open(ACTIVE, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    print(f"backup        : {bak}")
    print("OK. Seterusnya: python3 ~/.hermes20/scripts/sync_agency_catalog.py")


if __name__ == "__main__":
    main()
