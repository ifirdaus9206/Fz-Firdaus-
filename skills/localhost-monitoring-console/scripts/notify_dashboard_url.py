#!/usr/bin/env python3
"""Email the current console/dashboard URL + login WITHOUT leaking the secret to the agent.

Why this exists: quick tunnels (trycloudflare) change hostname on every restart, and the user
often asks for the new URL *and* the login to be "emailed" while also asking for the password in
chat. Splicing the password in here keeps it out of the transcript, logs and state.db.

Inputs read straight from disk (nothing secret passes through the caller):
  <home>/dashboard_url.txt            one line, the live public URL   (source of truth)
  <home>/secrets/dashboard_login.txt  lines: "url : …", "username: …", "password: …"
  <home>/.env                         GMAIL_USER, GMAIL_APP_PASSWORD  (Gmail App Password)

Usage:
    python notify_dashboard_url.py --to me@example.com --home ~/.hermes20
    python notify_dashboard_url.py --to me@example.com --dry-run      # no SMTP, no secret

Prints only a verdict. Verify delivery separately with an IMAP listing (subject + uid).
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


def load_env(path: Path) -> dict:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def read_login(path: Path) -> dict:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        m = re.match(r"\s*(url|username|password)\s*:\s*(\S+)", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def sync_url_line(path: Path, url: str) -> bool:
    """Keep the credential note's 'url :' line from rotting. Returns True if rewritten."""
    if not path.exists():
        return False
    text = path.read_text()
    new, n = re.subn(r"(?m)^(\s*url\s*:\s*)\S+", lambda m: m.group(1) + url, text)
    if n and new != text:
        path.write_text(new)
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", required=True)
    ap.add_argument("--home", default=os.path.expanduser("~/.hermes20"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    home = Path(os.path.expanduser(args.home))
    url_file = home / "dashboard_url.txt"
    login_file = home / "secrets" / "dashboard_login.txt"

    if not url_file.exists():
        print(f"GAGAL: {url_file} tiada", file=sys.stderr)
        return 2
    url = url_file.read_text().strip()
    if not url.startswith("https://"):
        print("GAGAL: dashboard_url.txt tidak mengandungi URL sah", file=sys.stderr)
        return 2

    synced = sync_url_line(login_file, url)
    creds = read_login(login_file)
    user = creds.get("username", "")
    pw = creds.get("password", "")
    if not pw:
        print("GAGAL: kata laluan tiada dalam fail kelayakan", file=sys.stderr)
        return 2

    env = load_env(home / ".env")
    sender = env.get("GMAIL_USER", "")
    app_pw = env.get("GMAIL_APP_PASSWORD", "")
    if not (sender and app_pw):
        print("GAGAL: GMAIL_USER / GMAIL_APP_PASSWORD tiada dalam .env", file=sys.stderr)
        return 2

    body = f"""Dashboard - URL BAHARU

URL baharu:
{url}

Log masuk:
  pengguna    : {user}
  kata laluan : {pw}

Nota:
- URL lama sudah MATI. Tunnel quick (trycloudflare) bertukar URL setiap kali servis dimulakan
  semula; aplikasi tidak rosak.
- URL semasa sentiasa boleh dibaca pada peranti di: {url_file}
- Untuk URL kekal, guna tunnel bernama (cloudflared) + domain.
"""
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = args.to
    msg["Subject"] = "Dashboard - URL baharu (tunnel dimulakan semula)"
    msg.set_content(body)

    if args.dry_run:
        print(f"DRY-RUN: tidak dihantar. url disegerakkan={synced}")
        return 0

    ctx = ssl.create_default_context()
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=45) as s:
        s.starttls(context=ctx)
        s.login(sender, app_pw)
        s.send_message(msg)
    print(f"OK: emel dihantar kepada {args.to} | url disegerakkan={synced}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
