#!/usr/bin/env python3
"""Pair Android wireless debugging when the user supplies ONLY the 6-digit code.

The pairing dialog shows `IP address & Port` and `Wi-Fi pairing code`, but users usually paste just
the code. `adb pair` needs a port, and `adb mdns services` is unsupported in some adb builds
(1.0.41 / 35.0.2-android-tools), so scan the ephemeral range and try each open port.

Usage:
    python3 adb-pair-scan.py 482913                 # default ip 192.168.0.8
    python3 adb-pair-scan.py 482913 192.168.1.7

Result semantics (they differ, read them):
  "protocol fault (couldn't read status message)"  -> not the pairing service, keep scanning
  hang / timeout                                   -> pairing port, but code wrong or EXPIRED (~2 min)
  "Successfully paired"                             -> then adb connect <connect port> and adb devices

Notes: re-scan before every attempt (the open-port set changes), and run
`adb kill-server` if a previous `adb connect` left a stale/offline entry.
"""
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

LO, HI = 30000, 50001
TIMEOUT = 0.08
WORKERS = 400


def scan(ip):
    def probe(p):
        s = socket.socket()
        s.settimeout(TIMEOUT)
        try:
            return p if s.connect_ex((ip, p)) == 0 else None
        except Exception:
            return None
        finally:
            s.close()

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        return [p for p in ex.map(probe, range(LO, HI)) if p]


def pair(ip, port, code):
    try:
        r = subprocess.run(["adb", "pair", f"{ip}:{port}"], input=code + "\n",
                           capture_output=True, text=True, timeout=45)
        out = ((r.stdout or "") + (r.stderr or "")).strip()
        return ("Successfully paired" in out or "Already paired" in out), out[:300]
    except subprocess.TimeoutExpired:
        return False, "timeout (kod mungkin tamat tempoh / bukan port pairing)"
    except Exception as e:  # adb missing, etc.
        return False, str(e)[:200]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    code = sys.argv[1].strip()
    ip = sys.argv[2] if len(sys.argv) > 2 else "192.168.0.8"
    print(f"imbas {ip}:{LO}-{HI - 1} …")
    ports = scan(ip)
    print("port terbuka:", ports or "tiada")
    if not ports:
        print("Tiada port terbuka. Pastikan 'Nyahpepijat wayarles' HIDUP dan dialog "
              "'Pasangkan peranti dengan kod' masih terbuka.")
        return 1
    for p in ports:
        ok, out = pair(ip, p, code)
        print(f"pair {ip}:{p} -> {'BERJAYA' if ok else 'gagal'} :: {out}")
        if ok:
            c = subprocess.run(["adb", "connect", f"{ip}:{p}"], capture_output=True, text=True, timeout=45)
            print("connect:", ((c.stdout or "") + (c.stderr or "")).strip()[:200])
            print(subprocess.run(["adb", "devices", "-l"], capture_output=True, text=True).stdout)
            return 0
    print("Semua port gagal. Minta kod 6 digit BAHARU (hidup ~2 minit) dan ulang segera.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
