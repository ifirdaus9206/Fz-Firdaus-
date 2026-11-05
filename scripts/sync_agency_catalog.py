#!/usr/bin/env python3
"""
sync_agency_catalog.py — jadikan korpus agency-agents-app sebagai sumber rujukan
untuk katalog router Hermes, tanpa merosakkan katalog yang sedang dipakai.

Sumber (app):   ~/.hermes20/agency-agents-app/src-tauri/resources/corpus-baseline
Katalog aktif:  ~/.hermes20/plugins/agency-agents-router/data/agents.json
Korpus git:     ~/.hermes20/agency-agents  (susun atur subfolder)

Mod:
  --check                (lalai) bandingkan korpus app dengan katalog aktif, tulis laporan
  --build <output.json>  bina katalog baharu daripada korpus app (TIDAK menimpa katalog aktif)
  --fix-paths            betulkan source_path dalam katalog aktif supaya padan fail sebenar
                         pada cakera (backup .bak-<tarikh> dibuat dahulu)

Perbandingan dibuat mengikut (divisi, slug), bukan path mentah — korpus app menyimpan
path rata (game-development/unity-architect.md) manakala repo git menyimpan subfolder
(game-development/unity/unity-architect.md). Perbezaan susun atur dilaporkan berasingan
sebagai "layout", bukan drift.

Contoh:
  python3 sync_agency_catalog.py
  python3 sync_agency_catalog.py --fix-paths
  python3 sync_agency_catalog.py --build /tmp/agents-from-app.json
"""

import argparse
import glob
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone

HOME = os.path.expanduser("~/.hermes20")
CORPUS = os.path.join(HOME, "agency-agents-app", "src-tauri", "resources", "corpus-baseline")
ACTIVE = os.path.join(HOME, "plugins", "agency-agents-router", "data", "agents.json")
DISK = os.path.join(HOME, "agency-agents")
REPORT = os.path.join(HOME, "logs", "agency-catalog-drift.txt")

FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)


def parse_frontmatter(text):
    m = FM.match(text)
    meta, body = {}, text
    if m:
        body = text[m.end():]
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    return meta, body.strip()


def slug_for(path, meta):
    stem = os.path.splitext(os.path.basename(path))[0]
    division = os.path.basename(os.path.dirname(path))
    prefix = division + "-"
    if stem.startswith(prefix):
        stem = stem[len(prefix):]
    return stem


def load_corpus():
    entries = []
    for division in sorted(os.listdir(CORPUS)):
        d = os.path.join(CORPUS, division)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".md"):
                continue
            p = os.path.join(d, fn)
            meta, body = parse_frontmatter(open(p, encoding="utf-8").read())
            entries.append({
                "slug": slug_for(p, meta),
                "name": meta.get("name", os.path.splitext(fn)[0]),
                "description": meta.get("description", ""),
                "division": division,
                "color": meta.get("color", ""),
                "emoji": meta.get("emoji", ""),
                "vibe": meta.get("vibe", ""),
                "source_path": f"{division}/{fn}",
                "body": body,
            })
    return entries


def key_of(entry):
    return (entry.get("division") or "?", entry.get("slug") or "?")


def disk_index():
    """Peta (divisi, slug) -> path relatif sebenar pada cakera repo git."""
    idx = {}
    for p in glob.glob(os.path.join(DISK, "**", "*.md"), recursive=True):
        rel = os.path.relpath(p, DISK)
        parts = rel.split(os.sep)
        if len(parts) < 2:
            continue
        division = parts[0]
        stem = os.path.splitext(parts[-1])[0]
        prefix = division + "-"
        slug = stem[len(prefix):] if stem.startswith(prefix) else stem
        idx[(division, slug)] = rel
    return idx


def fix_paths():
    active = json.load(open(ACTIVE, encoding="utf-8"))
    idx = disk_index()
    changed, unresolved = [], []
    for a in active:
        k = key_of(a)
        real = idx.get(k)
        if not real:
            unresolved.append(f"{k[0]}/{k[1]}")
            continue
        if a.get("source_path") != real:
            changed.append((a.get("source_path"), real))
            a["source_path"] = real
    if changed:
        stamp = datetime.now().strftime("%Y-%m-%d")
        bak = f"{ACTIVE}.bak-{stamp}"
        if not os.path.exists(bak):
            shutil.copy2(ACTIVE, bak)
        json.dump(active, open(ACTIVE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"path dibetulkan : {len(changed)}")
    for old, new in changed[:20]:
        print(f"  {old} -> {new}")
    if unresolved:
        print(f"tidak dapat dipadankan ({len(unresolved)}): " + ", ".join(unresolved[:20]))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", metavar="OUTPUT")
    ap.add_argument("--fix-paths", action="store_true")
    args = ap.parse_args()

    if args.fix_paths:
        return fix_paths()

    corpus = load_corpus()
    if args.build:
        json.dump(corpus, open(args.build, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"dibina: {args.build} ({len(corpus)} agent)")
        return 0

    active = json.load(open(ACTIVE, encoding="utf-8"))
    by_key = {key_of(a): a for a in active}
    corpus_keys = {key_of(e) for e in corpus}

    only_app = sorted(corpus_keys - set(by_key))
    only_active = sorted(set(by_key) - corpus_keys)
    body_diff = []
    for e in corpus:
        a = by_key.get(key_of(e))
        if a and a.get("body", "").strip() != e["body"].strip():
            body_diff.append(e["source_path"])

    # susun atur: path katalog vs path korpus app (bukan drift kandungan)
    layout = [e["source_path"] for e in corpus
              if key_of(e) in by_key and by_key[key_of(e)].get("source_path") != e["source_path"]]

    # path katalog yang tidak wujud pada cakera repo git
    missing_disk = [a.get("source_path") for a in active
                    if a.get("source_path") and not os.path.exists(os.path.join(DISK, a["source_path"]))]

    def fmt(keys):
        return ", ".join(f"{d}/{s}" for d, s in keys[:20]) or "-"

    lines = [
        f"Laporan drift katalog agency — {datetime.now(timezone.utc).isoformat()}",
        f"korpus app      : {CORPUS}  ({len(corpus)} fail)",
        f"katalog aktif   : {ACTIVE}  ({len(active)} entri)",
        f"korpus git      : {DISK}  ({len(disk_index())} fail)",
        "",
        f"hanya dalam app    ({len(only_app)}): " + fmt(only_app),
        f"hanya dalam aktif  ({len(only_active)}): " + fmt(only_active),
        f"badan berbeza      ({len(body_diff)}): " + (", ".join(body_diff[:20]) or "-"),
        f"beza susun atur    ({len(layout)}): " + (", ".join(layout[:20]) or "-"),
        f"path hilang cakera ({len(missing_disk)}): " + (", ".join(missing_disk[:20]) or "-"),
    ]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    open(REPORT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nlaporan ditulis: {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
