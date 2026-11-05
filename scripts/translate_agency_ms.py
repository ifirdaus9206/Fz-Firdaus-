#!/usr/bin/env python3
"""
translate_agency_ms.py — terjemah korpus agency-agents (Inggeris) ke Bahasa Melayu.

Sumber : ~/.hermes20/agency-agents/<divisi>/*.md
Sasaran: ~/.hermes20/agency-agents-ms/<divisi>/*.md   (pokok berasingan, asal kekal)
Log    : ~/.hermes20/logs/translate-agency-ms.log

Ciri:
  - boleh sambung semula (skip fail sasaran yang sudah ada dan tidak kosong)
  - selari (default 4 pekerja)
  - frontmatter: KUNCI kekal Inggeris, NILAI diterjemah
  - blok kod, slug, laluan fail, URL, nama arahan TIDAK diterjemah

Contoh:
  python3 translate_agency_ms.py --limit 3
  python3 translate_agency_ms.py --workers 4
  python3 translate_agency_ms.py --only engineering/engineering-backend-architect.md
"""

import argparse
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

HOME = os.path.expanduser("~/.hermes20")
SRC = os.path.join(HOME, "agency-agents")
DST = os.path.join(HOME, "agency-agents-ms")
LOG = os.path.join(HOME, "logs", "translate-agency-ms.log")
ENV = os.path.join(HOME, ".env")

MODEL = "deepseek/deepseek-v4.1-flash-1017"
API = "https://openrouter.ai/api/v1/chat/completions"

DIVISIONS = [
    "academic", "design", "engineering", "finance", "game-development", "gis",
    "healthcare", "marketing", "paid-media", "product", "project-management",
    "research", "sales", "security", "spatial-computing", "specialized",
    "support", "testing",
]

SYSTEM = (
    "Anda penterjemah profesional Inggeris->Bahasa Melayu untuk dokumentasi teknikal AI. "
    "Peraturan wajib:\n"
    "1. Kekalkan struktur markdown sepenuhnya: tajuk (#, ##), senarai, jadual, petikan, garis pemisah.\n"
    "2. Kekalkan blok kod (```...```) dan kod inline TIDAK diterjemah, termasuk komen kod.\n"
    "3. Dalam YAML frontmatter: KUNCI (name, description, color, emoji, vibe, dll) kekal Inggeris; "
    "hanya NILAI diterjemah. Nilai warna/nama teknikal (contoh: cyan, #FF0000) kekal.\n"
    "4. Jangan terjemah: slug, nama fail, laluan, URL, nama arahan terminal, nama model, "
    "nama pemboleh ubah, tag HTML, atau nama alat.\n"
    "5. Istilah teknikal piawai dikekalkan dalam Inggeris dalam kurungan jika perlu, "
    "contoh: 'pengurus projek (Project Manager)'.\n"
    "6. Nada: profesional, jelas, seperti dokumen rasmi Bahasa Melayu. Bukan bahasa pasar.\n"
    "7. Jangan tambah, jangan buang, jangan ringkaskan mana-mana bahagian. Terjemah SEMUA teks.\n"
    "8. Output HANYA fail terjemahan penuh, tiada mukadimah, tiada nota, tiada ```pembalut."
)

_lock = threading.Lock()
_stat = {"ok": 0, "skip": 0, "fail": 0}


def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    with _lock:
        print(line, flush=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def api_key():
    for line in open(ENV, encoding="utf-8"):
        line = line.strip()
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("OPENROUTER_API_KEY tidak dijumpai dalam " + ENV)


def translate(text, key, retries=3):
    body = json.dumps({
        "model": MODEL,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": text},
        ],
    }).encode()
    last = None
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(API, data=body, headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://local.hermes",
            "X-Title": "agency-ms-translator",
        })
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.loads(r.read().decode())
            out = data["choices"][0]["message"]["content"].strip()
            if out.startswith("```"):
                out = out.split("\n", 1)[1] if "\n" in out else out
                if out.rstrip().endswith("```"):
                    out = out.rstrip()[:-3]
            return out.strip() + "\n"
        except Exception as e:
            last = e
            time.sleep(2 * attempt)
    raise RuntimeError(f"gagal selepas {retries} cubaan: {last}")


def jobs():
    out = []
    for d in DIVISIONS:
        base = os.path.join(SRC, d)
        if not os.path.isdir(base):
            continue
        for root, _, files in os.walk(base):
            for fn in sorted(files):
                if fn.endswith(".md") and fn != "README.md":
                    out.append(os.path.relpath(os.path.join(root, fn), SRC))
    return sorted(out)


def work(rel, key):
    dst = os.path.join(DST, rel)
    if os.path.exists(dst) and os.path.getsize(dst) > 200:
        with _lock:
            _stat["skip"] += 1
        return rel, "skip"
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    src_text = open(os.path.join(SRC, rel), encoding="utf-8").read()
    try:
        ms = translate(src_text, key)
    except Exception as e:
        with _lock:
            _stat["fail"] += 1
        log(f"GAGAL {rel}: {e}")
        return rel, "fail"
    open(dst, "w", encoding="utf-8").write(ms)
    with _lock:
        _stat["ok"] += 1
        n = _stat["ok"]
    log(f"OK {rel} ({len(src_text)}->{len(ms)} aksara) [{n}]")
    return rel, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="")
    args = ap.parse_args()

    key = api_key()
    todo = [args.only] if args.only else jobs()
    if args.limit:
        todo = todo[: args.limit]

    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    log(f"MULA: {len(todo)} fail | pekerja={args.workers} | model={MODEL}")

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(work, rel, key) for rel in todo]
        for f in as_completed(futs):
            f.result()

    log(f"TAMAT: ok={_stat['ok']} skip={_stat['skip']} gagal={_stat['fail']} daripada {len(todo)}")
    return 0 if _stat["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
