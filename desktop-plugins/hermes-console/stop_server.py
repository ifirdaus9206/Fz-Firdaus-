#!/usr/bin/env python3
"""Hentikan server console dengan selamat.

    python3 tools/stop_server.py            # hentikan 8787 (hermes20)
    python3 tools/stop_server.py --all       # sama (hanya satu instance kini)

Nota: 8790 (hermes19) sudah dibersarakan 2026-11-24 — hermes19 dipadam.

Guna fail pid `server-<port>.pid` jika ada; jika tiada, imbas /proc untuk
proses python yang menjalankan app.py dalam folder ini DAN (bila diketahui)
port yang betul melalui /proc/<pid>/environ.

TIDAK menggunakan `pkill -f` — corak itu memadankan shell pemanggil sendiri
dan boleh membunuh sesi terminal.

PENTING (runit): konsol diselia oleh servis runit `hermes-console`. Selepas
skrip ini membunuh proses, runsv akan menghidupkannya semula dalam ~2 saat —
jadi kesan bersihnya ialah **restart**, bukan berhenti. Untuk benar-benar
hentikan, jalankan `sv down hermes-console` dahulu.
"""
import os
import signal
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PORTS = [8787]  # 8790 dibersarakan (hermes19 dipadam)


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def env_port(pid: int):
    try:
        raw = (Path(f"/proc/{pid}/environ")).read_bytes()
    except Exception:
        return None
    for item in raw.split(b"\0"):
        if item.startswith(b"CONSOLE_PORT="):
            return item.split(b"=", 1)[1].decode("utf-8", "replace").strip()
    return None


def stop_port(port: int):
    killed = []
    pidf = BASE / f"server-{port}.pid"
    legacy = BASE / "server.pid"
    candidates = []
    if pidf.exists():
        candidates.append(pidf)
    if port == 8787 and legacy.exists():
        candidates.append(legacy)
    for f in candidates:
        try:
            pid = int(f.read_text().strip())
        except Exception:
            f.unlink(missing_ok=True)
            continue
        if alive(pid) and env_port(pid) in (None, str(port)):
            os.kill(pid, signal.SIGTERM)
            killed.append(pid)
        f.unlink(missing_ok=True)

    if not killed:  # fallback: imbas /proc
        me = {os.getpid(), os.getppid()}
        for d in Path("/proc").iterdir():
            if not d.name.isdigit():
                continue
            pid = int(d.name)
            if pid in me:
                continue
            try:
                parts = [a.decode("utf-8", "replace")
                         for a in (d / "cmdline").read_bytes().split(b"\0") if a]
            except Exception:
                continue
            if not parts or "python" not in parts[0]:
                continue
            if not any(p.endswith("app.py") for p in parts):
                continue
            try:
                if Path(os.readlink(f"/proc/{pid}/cwd")).resolve() != BASE:
                    continue
            except Exception:
                continue
            p = env_port(pid)
            if p is not None and p != str(port):
                continue
            try:
                os.kill(pid, signal.SIGTERM)
                killed.append(pid)
            except Exception:
                pass
    print(f"{port} dihentikan:", killed or "tiada proses")
    return killed


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--all" in args:
        targets = PORTS
    elif "--port" in args:
        i = args.index("--port")
        targets = [int(args[i + 1])]
    else:
        targets = [8787]
    for p in targets:
        stop_port(p)
    sys.exit(0)
