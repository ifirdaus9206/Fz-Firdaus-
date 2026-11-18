#!/usr/bin/env python3
"""Pengeksport data tab SANDARAN (baca-sahaja).

Menulis 5 fail ke ~/.hermes20/reports/sandaran/:
  status.json, sejarah.json, larian.json, cron.json, insiden-2026-11-18.md

Setiap bahagian tahan ralat: satu bahagian gagal tidak menggagalkan yang lain.
Tiada kelayakan dibaca atau ditulis.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

HOME = Path.home()
HERMES = Path(os.environ.get("HERMES_HOME") or HOME / ".hermes20")
OUT = HERMES / "reports" / "sandaran"
LOG = HERMES / "logs" / "backup.log"
JOBS = HERMES / "cron" / "jobs.json"
JOB_ID = "43c3baafa834"
OUT.mkdir(parents=True, exist_ok=True)


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def git(*args, timeout: int = 25):
    """Jalankan git dalam repo. Pulang (ok, teks)."""
    try:
        p = subprocess.run(["git", *args], cwd=str(HERMES), capture_output=True,
                           text=True, timeout=timeout)
        if p.returncode != 0:
            return False, (p.stderr or p.stdout or "").strip()
        return True, (p.stdout or "").strip()
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"


def tulis(nama: str, obj) -> None:
    (OUT / nama).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


# ---------------------------------------------------------------- status.json
def buat_status() -> dict:
    d = {"ok": True, "dijana_pada": now(), "repo_tempatan": str(HERMES)}
    ok, url = git("remote", "get-url", "origin")
    d["remote_url"] = url if ok else "tiada-remote"
    m = re.search(r"[:/]([^/:]+/[^/]+?)(?:\.git)?$", d["remote_url"])
    d["repo"] = m.group(1) if m and ok else d["remote_url"]
    ok, br = git("rev-parse", "--abbrev-ref", "HEAD")
    d["cawangan"] = br if ok else "tidak diketahui"

    ok, head = git("rev-parse", "HEAD")
    d["commit_tempatan"] = head if ok else "tidak diketahui"
    d["commit_tempatan_pendek"] = head[:7] if ok else "tidak diketahui"
    ok, subj = git("log", "-1", "--pretty=%s")
    d["commit_tempatan_subjek"] = subj if ok else ""

    # remote: jangan gagal keseluruhan jika SSH/ rangkaian tiada
    ok, ls = git("ls-remote", "origin", "HEAD", timeout=25)
    if ok and ls:
        rh = ls.split()[0]
        d["commit_remote"] = rh
        d["commit_remote_pendek"] = rh[:7]
        d["segerak"] = bool(d.get("commit_tempatan") == rh)
        d["nota_remote"] = "Remote diperiksa pada " + d["dijana_pada"]
    else:
        d["commit_remote"] = "remote_tidak_dapat_disemak"
        d["commit_remote_pendek"] = "remote_tidak_dapat_disemak"
        d["segerak"] = None
        d["nota_remote"] = ("Remote tidak dapat disemak (SSH/rangkaian). "
                            "Commit tempatan tetap sah.")

    ok, n = git("ls-files")
    d["fail_tracked"] = len(n.splitlines()) if ok else None
    g = HERMES / ".git"
    try:
        saiz = sum(f.stat().st_size for f in g.rglob("*") if f.is_file())
        d["saiz_git_bytes"] = saiz
        d["saiz_git_mb"] = round(saiz / 1048576, 1)
    except Exception:  # noqa: BLE001
        d["saiz_git_bytes"] = None
        d["saiz_git_mb"] = None
    return d


# --------------------------------------------------------------- sejarah.json
def buat_sejarah() -> dict:
    ok, out = git("log", "-20", "--pretty=%H%x1f%ad%x1f%s", "--date=format:%Y-%m-%d %H:%M")
    commits = []
    if ok:
        for baris in out.splitlines():
            bahagian = baris.split("\x1f")
            if len(bahagian) == 3:
                commits.append({"hash": bahagian[0], "pendek": bahagian[0][:7],
                                "tarikh": bahagian[1], "subjek": bahagian[2]})
    return {"ok": True, "dijana_pada": now(), "bilangan": len(commits), "commits": commits}


# ---------------------------------------------------------------- larian.json
def jenis_larian(baris: str) -> str:
    b = baris.lower()
    if "commit" in b and "dibuat" in b:
        return "commit"
    if "dibatalkan" in b:
        return "dibatalkan"
    if "tiada remote" in b or "tiada-remote" in b or "bukan repo git" in b:
        return "tiada-remote"
    if "push" in b and ("gagal" in b or "tidak berjaya" in b):
        return "push-gagal"
    if "abaikan" in b:
        return "diabaikan"
    if "push berjaya" in b:
        return "push-berjaya"
    if "gagal" in b:
        return "gagal"
    return "lain"


def buat_larian() -> dict:
    baris_semua = []
    try:
        baris_semua = LOG.read_text(errors="replace").splitlines()
    except Exception:  # noqa: BLE001
        pass
    larian = []
    for b in baris_semua[-20:]:
        if not b.strip():
            continue
        m = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s+(.*)", b)
        masa, mesej = (m.group(1), m.group(2)) if m else ("", b)
        larian.append({"masa": masa, "jenis": jenis_larian(b), "mesej": mesej[:300]})
    return {"ok": True, "dijana_pada": now(), "fail_log": str(LOG),
            "jumlah_baris_log": len(baris_semua), "larian": larian}


# ----------------------------------------------------------------- cron.json
def buat_cron() -> dict:
    d = {"ok": False, "dijana_pada": now(), "id": JOB_ID}
    try:
        data = json.loads(JOBS.read_text())
        job = next((j for j in data.get("jobs", []) if j.get("id") == JOB_ID), None)
        if not job:
            d["sebab"] = "job tidak dijumpai dalam jobs.json"
            return d
        d |= {
            "ok": True,
            "nama": job.get("name"),
            "jadual": (job.get("schedule") or {}).get("expr") or job.get("schedule_display"),
            "jadual_baca": "setiap hari 2:00 pagi",
            "skrip": job.get("script"),
            "log": str(LOG),
            "enabled": job.get("enabled"),
            "last_status": job.get("last_status"),
            "last_run_at": job.get("last_run_at"),
            "next_run_at": job.get("next_run_at"),
        }
        err = (job.get("last_error") or "").strip()
        d["last_error_ringkas"] = err.splitlines()[0][:200] if err else ""
    except Exception as e:  # noqa: BLE001
        d["sebab"] = f"{type(e).__name__}: {e}"
    return d


# ------------------------------------------------------------------ insiden md
INSIDEN = """# Insiden Sandaran GitHub — 18 November 2026

## Apa yang berlaku
Sandaran malam 2:00 pagi pada 18 November berhenti sendiri (kod keluar 3).
Tiada data hilang dan tiada fail dihantar ke GitHub: commit dibatalkan
sebelum dibuat, jadi repo kekal seperti sebelumnya.

## Punca sebenar
Pengawal rahsia membaca dua fail dokumentasi sebagai "kunci sebenar":
- `docs/INSIDEN-2026-11-17.md` — contoh seperti `GMAIL_APP_PASSWORD=xxxx`
- `skills/devops/safe-git-config-backup/SKILL.md` — ayat penerangan, bukan kunci

Kedua-duanya contoh/prosa — tiada kebocoran, tiada push pada larian itu.

## Pembetulan — pengawal dua peringkat
1. Corak keras (bentuk kunci sebenar: `sk-...`, `ghp_...`, kunci peribadi,
   token JWT) — dipindai pada SEMUA fail, termasuk `.md` dan `docs/`.
2. `nama=nilai` sensitif — HANYA pada fail bukan dokumentasi. Fail `.md`,
   `docs/`, `references/`, `templates/` dikecualikan di peringkat ini sahaja.
   Nilai pendek, placeholder dan `<...>` diabaikan.

## Bukti ujian
- Kunci sebenar dalam fail ujian → exit 3, commit HEAD tidak berubah.
- Fail bersih → exit 0, commit dan push berjaya.
- Larian berulang tanpa perubahan → senyap, tiada commit berganda.

## Selepas pembetulan
Commit `cf40661` berjaya dipush ke `github.com/ifirdaus9206/Fz-Firdaus-`.
Laporan insiden dihantar ke ifirdaus9206@gmail.com dan disahkan masuk inbox.
Jadual 2:00 pagi kekal seperti biasa.
"""


def main() -> int:
    hasil = {}
    for nama, fn in (("status.json", buat_status), ("sejarah.json", buat_sejarah),
                     ("larian.json", buat_larian), ("cron.json", buat_cron)):
        try:
            tulis(nama, fn())
            hasil[nama] = "ok"
        except Exception as e:  # noqa: BLE001
            hasil[nama] = f"gagal: {e}"
    try:
        (OUT / "insiden-2026-11-18.md").write_text(INSIDEN)
        hasil["insiden-2026-11-18.md"] = "ok"
    except Exception as e:  # noqa: BLE001
        hasil["insiden-2026-11-18.md"] = f"gagal: {e}"
    print(json.dumps({"ok": True, "folder": str(OUT), "fail": hasil}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
