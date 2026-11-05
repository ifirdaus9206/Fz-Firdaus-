#!/usr/bin/env python3
"""Stop a local dev server WITHOUT `pkill -f` (which matches the calling shell and
kills your own terminal session).

Usage:
    python3 tools/stop_server.py [--dir <project dir>] [--pid-file server.pid]

Strategy, in order:
  1. pid file (written by app.py on start) — SIGTERM if the pid is alive;
  2. /proc scan for a python process whose cmdline ends with app.py AND whose cwd
     equals the project dir (skips own pid + parent, skips other projects).
Exit code 0 always; prints what it stopped.
"""
import argparse
import os
import signal
import sys
from pathlib import Path


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--pid-file", default="server.pid")
    a = ap.parse_args()
    base = Path(a.dir).resolve()
    pidf = base / a.pid_file
    killed: list[int] = []

    if pidf.exists():
        try:
            pid = int(pidf.read_text().strip())
            if alive(pid):
                os.kill(pid, signal.SIGTERM)
                killed.append(pid)
            pidf.unlink()
        except Exception:
            pass

    if not killed:
        me = {os.getpid(), os.getppid()}
        for d in Path("/proc").iterdir():
            if not d.name.isdigit():
                continue
            pid = int(d.name)
            if pid in me:
                continue
            try:
                parts = [p.decode("utf-8", "replace")
                         for p in (d / "cmdline").read_bytes().split(b"\0") if p]
            except Exception:
                continue
            if not parts or "python" not in parts[0]:
                continue
            if not any(p.endswith("app.py") for p in parts):
                continue
            try:  # confirm the process belongs to THIS project dir
                if Path(os.readlink(f"/proc/{pid}/cwd")).resolve() != base:
                    continue
            except Exception:
                continue
            try:
                os.kill(pid, signal.SIGTERM)
                killed.append(pid)
            except Exception:
                pass

    print("dihentikan:", killed or "tiada proses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
