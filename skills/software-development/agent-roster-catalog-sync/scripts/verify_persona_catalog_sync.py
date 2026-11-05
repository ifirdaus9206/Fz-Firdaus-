#!/usr/bin/env python3
"""Pengesah bebas: persona .md <-> korpus baseline <-> agents.json.

Guna:
    python3 verify_persona_catalog_sync.py master-plan-architect specialized
    python3 verify_persona_catalog_sync.py <slug> <division> [--backup PATH]

Mencetak bukti mentah yang boleh disalin terus ke laporan:
  - jumlah entri katalog
  - description & body JSON == fail persona (True/False)
  - semakan frasa larangan/kebenaran (boleh diubah melalui --forbid/--require)
  - cmp dua fail kembar (identik atau tidak)
  - senarai slug yang berubah berbanding backup, dan jumlah tidak berubah

Exit code 0 hanya jika semua semakan lulus.
"""

import argparse
import json
import os
import re
import sys

HOME = os.path.expanduser("~/.hermes20")
ACTIVE = os.path.join(HOME, "plugins/agency-agents-router/data/agents.json")
CORPUS = os.path.join(HOME, "agency-agents-app/src-tauri/resources/corpus-baseline")
DISK = os.path.join(HOME, "agency-agents")
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


def find_disk_file(division, slug):
    base = os.path.join(DISK, division)
    if not os.path.isdir(base):
        return None
    for root, _dirs, files in os.walk(base):
        for fn in files:
            if fn == f"{division}-{slug}.md":
                return os.path.join(root, fn)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("division")
    ap.add_argument("--backup", default=None, help="agents.json.bak-* untuk banding")
    ap.add_argument("--forbid", action="append", default=["ZERO CODE EXECUTION"])
    ap.add_argument("--require", action="append", default=["read-only shell"])
    a = ap.parse_args()

    ok = True
    disk = find_disk_file(a.division, a.slug)
    corpus = os.path.join(CORPUS, a.division, f"{a.division}-{a.slug}.md")
    print("fail git   :", disk)
    print("fail korpus:", corpus)

    same_files = False
    if disk and os.path.exists(corpus):
        same_files = open(disk, "rb").read() == open(corpus, "rb").read()
        print("dua fail identik:", same_files)
        ok &= same_files

    src = disk if disk else corpus
    meta, body = parse_frontmatter(open(src, encoding="utf-8").read())

    data = json.load(open(ACTIVE, encoding="utf-8"))
    print("jumlah entri katalog:", len(data))
    hits = [e for e in data if e.get("slug") == a.slug]
    print("entri dijumpai:", len(hits))
    if len(hits) != 1:
        sys.exit(1)
    e = hits[0]
    d_ok = e.get("description") == meta.get("description")
    b_ok = e.get("body") == body
    print("description JSON == frontmatter:", d_ok)
    print("body JSON == body fail        :", b_ok)
    print("kunci entri                   :", sorted(e.keys()))
    print("body 200 aksara pertama       :", repr(e["body"][:200]))
    ok &= d_ok and b_ok

    for f in a.forbid:
        present = f in e["body"]
        print(f"body mengandungi {f!r}:", present, "(mesti False)")
        ok &= not present
    for r in a.require:
        present = r in e["body"]
        print(f"body mengandungi {r!r}:", present, "(mesti True)")
        ok &= present

    if a.backup and os.path.exists(a.backup):
        old = {x["slug"]: x for x in json.load(open(a.backup, encoding="utf-8"))}
        new = {x["slug"]: x for x in data}
        changed = [s for s in new if s not in old or old[s] != new[s]]
        print("backup                        :", a.backup)
        print("slug berubah                  :", changed)
        print("bilangan berubah / kekal      :", len(changed), "/", len(new) - len(changed))
        ok &= changed == [a.slug]
    else:
        print("backup                        : (tiada --backup diberikan)")

    print("KEPUTUSAN:", "LULUS" if ok else "GAGAL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
