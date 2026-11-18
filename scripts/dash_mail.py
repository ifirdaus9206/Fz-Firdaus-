#!/usr/bin/env python3
"""Hantar emel dashboard (URL baharu + kelayakan log masuk) tanpa memaparkan rahsia.

Rahsia dibaca terus daripada fail pada peranti, tidak melalui chat/log:
  - URL dashboard   : ~/.hermes20/dashboard_url.txt
  - pengguna/kata laluan : ~/.hermes20/secrets/dashboard_login.txt

Kelayakan SMTP diambil daripada ~/.hermes20/.env (GMAIL_USER, GMAIL_APP_PASSWORD).

Guna:
    python scripts/dash_mail.py --to firdaus@contoh.com [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import re
import smtplib
import ssl
import sys
from email.message import EmailMessage
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
HHOME = HOME / ".hermes20"
URL_FILE = HHOME / "dashboard_url.txt"
LOGIN_FILE = HHOME / "secrets" / "dashboard_login.txt"
ENV_FILE = HHOME / ".env"


def load_env() -> dict:
    env = {}
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def read_login() -> dict:
    out = {}
    for line in LOGIN_FILE.read_text().splitlines():
        m = re.match(r"\s*(url|username|password)\s*:\s*(\S+)", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def sync_login_url(url: str) -> bool:
    """Kemas kini baris url di dalam fail kelayakan supaya tidak basi."""
    text = LOGIN_FILE.read_text()
    new, n = re.subn(r"(?m)^(\s*url\s*:\s*)\S+", lambda m: m.group(1) + url, text)
    if n and new != text:
        LOGIN_FILE.write_text(new)
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    url = URL_FILE.read_text().strip()
    if not url.startswith("https://"):
        print("GAGAL: dashboard_url.txt tidak mengandungi URL sah", file=sys.stderr)
        return 2
    changed = sync_login_url(url)
    creds = read_login()
    user = creds.get("username") or "firdaus"
    pw = creds.get("password")
    if not pw:
        print("GAGAL: kata laluan tidak dijumpai dalam fail kelayakan", file=sys.stderr)
        return 2

    env = load_env()
    sender = env.get("GMAIL_USER", "")
    app_pw = env.get("GMAIL_APP_PASSWORD", "")
    if not sender or not app_pw:
        print("GAGAL: GMAIL_USER / GMAIL_APP_PASSWORD tiada dalam .env", file=sys.stderr)
        return 2

    body = f"""Dashboard UIM - URL BAHARU

URL baharu:
{url}

Log masuk:
  pengguna    : {user}
  kata laluan : {pw}

Nota:
- URL lama (deny-twiki-doc-announcement / shopzilla-northwest-agent-showers) sudah MATI.
  Tunnel trycloudflare bertukar URL setiap kali servis dimulakan semula.
- URL semasa sentiasa boleh dibaca pada telefon di: ~/.hermes20/dashboard_url.txt
- Selepas log masuk, dashboard berjalan 24 jam melalui runit (hermes-dashboard + hermes-dash-tunnel).

Dijana automatik oleh Ketua.
"""
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = args.to
    msg["Subject"] = "Dashboard UIM - URL baharu (tunnel dimulakan semula)"
    msg.set_content(body)

    if args.dry_run:
        print("DRY-RUN: emel tidak dihantar. URL:", url, "| url disegerakkan:", changed)
        return 0

    ctx = ssl.create_default_context()
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=45) as s:
        s.starttls(context=ctx)
        s.login(sender, app_pw)
        s.send_message(msg)
    print("OK: emel dihantar kepada", args.to, "| url disegerakkan:", changed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
