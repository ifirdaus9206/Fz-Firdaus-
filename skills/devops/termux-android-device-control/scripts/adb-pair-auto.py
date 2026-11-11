#!/usr/bin/env python3
"""Pair wireless ADB when only the 6-digit code is known.

Guna:  python3 adb-pair-auto.py <kod-6-digit> [ip]

1. parallel TCP scan of ports 30000-50000 on the phone IP
2. `adb pair ip:port <code>` on each open port, classify the reply
3. on success: `adb connect ip:port` and print `adb devices -l`

Codes expire in ~2 minutes and are single-use: if every port times out, ask the user for a
FRESH code with the Pair-with-code dialog still open instead of retrying the old digits.
Requires: pkg install -y android-tools
"""
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor


def imbas(ip: str, lo: int = 30000, hi: int = 50000) -> list[int]:
    def cuba(p: int):
        s = socket.socket()
        s.settimeout(0.08)
        try:
            return p if s.connect_ex((ip, p)) == 0 else None
        except Exception:
            return None
        finally:
            s.close()

    with ThreadPoolExecutor(max_workers=400) as ex:
        return [p for p in ex.map(cuba, range(lo, hi + 1)) if p]


def pair(ip: str, port: int, kod: str) -> tuple[bool, str]:
    try:
        r = subprocess.run(["adb", "pair", f"{ip}:{port}"], input=kod + "\n",
                           capture_output=True, text=True, timeout=45)
        out = ((r.stdout or "") + (r.stderr or "")).strip()
        return ("Successfully paired" in out or "Already paired" in out), out[:300]
    except subprocess.TimeoutExpired:
        return False, "timeout (port pairing? kod mungkin tamat tempoh)"
    except Exception as e:  # noqa: BLE001
        return False, str(e)[:200]


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    kod = sys.argv[1].strip()
    ip = sys.argv[2] if len(sys.argv) > 2 else "192.168.0.8"
    print(f"imbas {ip} port 30000-50000 …")
    ports = imbas(ip)
    print("port terbuka:", ports or "tiada")
    if not ports:
        print("Tiada port terbuka: pastikan 'Nyahpepijat wayarles' HIDUP dan dialog "
              "'Pasangkan peranti dengan kod' masih terbuka.")
        return 1
    for p in ports:
        ok, out = pair(ip, p, kod)
        print(f"pair {ip}:{p} -> {'BERJAYA' if ok else 'gagal'} :: {out}")
        if ok:
            c = subprocess.run(["adb", "connect", f"{ip}:{p}"], capture_output=True, text=True, timeout=45)
            print("connect:", ((c.stdout or "") + (c.stderr or "")).strip()[:200])
            print(subprocess.run(["adb", "devices", "-l"], capture_output=True, text=True).stdout)
            return 0
    print("Semua port gagal — minta kod 6 digit BAHARU (kod tamat ~2 minit).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
