#!/usr/bin/env python3
"""Pemandu PTY untuk `gh auth login --web` dalam Termux.
Tujuan: prompt interaktif gh tidak boleh dijawab melalui pipe biasa.
Skrip ini membuka pty, menjawab prompt, memaparkan kod sekali-guna,
dan mengekalkan proses sehingga kebenaran diberi di github.com/login/device.
"""
import os
import pty
import re
import select
import subprocess
import sys
import time

CMD = ["gh", "auth", "login", "--hostname", "github.com",
       "--git-protocol", "https", "--web"]

master, slave = pty.openpty()
proc = subprocess.Popen(CMD, stdin=slave, stdout=slave, stderr=slave,
                        close_fds=True)
os.close(slave)

buf = b""
answered = False
entered = False
code_reported = False
start = time.time()

while time.time() - start < 900:
    ready, _, _ = select.select([master], [], [], 1.0)
    if ready:
        try:
            data = os.read(master, 4096)
        except OSError:
            break
        if not data:
            break
        buf += data
        sys.stdout.write(data.decode(errors="replace"))
        sys.stdout.flush()

        if not answered and b"Authenticate Git" in buf:
            os.write(master, b"Y\r")
            answered = True
            time.sleep(0.5)

        if answered and not entered and b"Press Enter" in buf:
            os.write(master, b"\r")
            entered = True

        if not code_reported:
            m = re.search(rb"one-time code:\s*([A-Z0-9]{4}-[A-Z0-9]{4})", buf)
            if m:
                print("\n===KOD-SEKALI-GUNA=== " + m.group(1).decode(), flush=True)
                code_reported = True

    if proc.poll() is not None:
        break

print("\n===PROSES-TAMAT exit=%s===" % proc.poll(), flush=True)
