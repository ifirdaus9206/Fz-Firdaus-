#!/usr/bin/env python3
"""Ambil butiran PENUH satu/lebih projek Freelancer.com untuk menulis draf proposal.

Sebab: laporan radar memotong `penerangan` pada ~100 aksara, jadi draf yang ditulis
daripada laporan sahaja akan meneka skop. Endpoint butiran memberi deskripsi penuh,
kemahiran diminta, dan statistik bidaan.

Guna:
    python3 project_detail.py 40814698 40815260
    python3 project_detail.py fl-40814698          # awalan 'fl-' dibuang automatik

Tiada auth. Keluaran: teks biasa ke stdout (selamat dibaca terus ke dalam konteks).
"""
import json
import sys
import urllib.request

API = "https://www.freelancer.com/api/projects/0.1/projects/{id}/?full_description=true&job_details=true"
UA = "Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"


def detail(raw_id: str) -> dict:
    pid = raw_id.replace("fl-", "").strip()
    req = urllib.request.Request(API.format(id=pid), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.loads(r.read().decode("utf-8", "replace"))
    return payload.get("result", {}) or {}


def main(ids: list) -> int:
    if not ids:
        print(__doc__)
        return 2
    for raw in ids:
        try:
            r = detail(raw)
        except Exception as exc:                      # noqa: BLE001 - laporkan, jangan mati
            print(f"=== {raw}: GAGAL ({exc})")
            continue
        b = r.get("budget") or {}
        s = r.get("bid_stats") or {}
        print(f"=== {raw}")
        print("title  :", r.get("title"))
        print("budget :", b.get("minimum"), "-", b.get("maximum"),
              "| jenis:", b.get("project_type"), "| mata wang id:", b.get("currency_id"))
        print("bids   :", s.get("bid_count"), "| avg:", s.get("bid_avg"))
        print("skills :", [j.get("name") for j in (r.get("jobs") or [])][:10])
        print("desc   :")
        print((r.get("description") or "(tiada deskripsi)")[:2500])
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
