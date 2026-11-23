#!/usr/bin/env python3
"""memori_panjang.py - himpun memori pendek untuk penyulingan jangka panjang.

Keluaran: teks ringkas (untuk prompt ejen cron) + tulis senarai fail.
Guna: memori_panjang.py [hari]   (lalai 7 hari)
"""
import sys, os, datetime, pathlib

base = pathlib.Path(os.path.expanduser("~/vault/memori"))
pendek = base / "01-pendek"
panjang = base / "02-panjang" / "MEMORI-PANJANG.md"
pelajaran = base / "03-pelajaran"

days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
today = datetime.date.today()

chunks = []
for i in range(days):
    d = today - datetime.timedelta(days=i)
    f = pendek / f"{d.isoformat()}.md"
    if f.exists():
        body = [l for l in f.read_text().splitlines() if l.startswith("- ")]
        if body:
            chunks.append(f"### {d.isoformat()}\n" + "\n".join(body))

print("=== MEMORI JANGKA PANJANG SEMASA ===")
print(panjang.read_text() if panjang.exists() else "(belum ada)")
print("\n=== MEMORI PENDEK (ARKIB) ===")
print("\n\n".join(chunks) if chunks else "(tiada rekod)")
print("\n=== FAIL ===")
print(f"panjang: {panjang}")
print(f"pelajaran: {pelajaran}")
print(f"hari_disemak: {days}")
