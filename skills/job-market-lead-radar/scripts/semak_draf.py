#!/usr/bin/env python3
"""Semak draf proposal radar kerja: had 120 patah perkataan + blok wajib.

Guna:  python3 semak_draf.py drafts/*.md
Keluar 1 kalau ada draf melebihi had atau tiada blok wajib.
"""
import re
import sys

HAD = 120
WAJIB = ["**Tajuk:**", "**Pautan:**", "**Bajet:**", "## Draf proposal", "## Checklist sebelum hantar"]


def badan(teks: str) -> str:
    """Ambil bahagian proposal sahaja (antara tajuk Draf proposal dan Checklist)."""
    if "## Draf proposal" not in teks:
        return ""
    b = teks.split("## Draf proposal", 1)[1]
    b = b.split("## Checklist", 1)[0]
    # buang baris tajuk kecil "(English, 114 patah perkataan)"
    b = re.sub(r"^\s*\(.*?\)\s*$", "", b, flags=re.M)
    return b.strip()


def main(paths):
    gagal = 0
    for p in paths:
        try:
            teks = open(p, encoding="utf-8").read()
        except OSError as e:
            print(f"{p} | RALAT: {e}")
            gagal += 1
            continue
        b = badan(teks)
        n = len(b.split())
        hilang = [w for w in WAJIB if w not in teks]
        status = "ok" if (b and n <= HAD and not hilang) else "OVER/ROSak"
        print(f"{p} | {n} patah perkataan | {status}")
        if hilang:
            print(f"    tiada blok: {', '.join(hilang)}")
            gagal += 1
        elif n > HAD:
            print(f"    lebih {n - HAD} — potong ayat penutup, bukan ayat masalah klien")
            gagal += 1
        elif not b:
            gagal += 1
    return 1 if gagal else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1:]))
