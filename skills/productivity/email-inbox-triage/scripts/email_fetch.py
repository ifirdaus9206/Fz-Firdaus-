#!/usr/bin/env python3
"""Baca Gmail satu per satu, simpan setiap email jadi satu fail markdown + indeks CSV.

Kelayakan diambil daripada fail .env (TIDAK ditulis dalam repo/chat):
    GMAIL_USER=nama@gmail.com
    GMAIL_APP_PASSWORD=<16-aksara>          # App Password 16 aksara, bukan kata laluan akaun

Guna:
    python email_fetch.py check
    python email_fetch.py list --days 7 --max 20
    python email_fetch.py save --days 7 --max 20 --tag freelance
    python email_fetch.py save --uid 1234 --tag freelance

Simpanan:
    ~/vault/email-inbox/<YYYY-MM-DD>_<uid>_<slug>.md   (satu email = satu fail)
    ~/vault/email-inbox/_index.csv                      (satu baris = satu email)
"""
from __future__ import annotations

import argparse
import csv
import email
import email.utils
import imaplib
import json
import os
import re
import sys
from datetime import datetime, timedelta
from email.header import decode_header, make_header
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
ENV_CANDIDATES = [HOME / ".hermes20" / ".env", HOME / ".env"]
OUT_DIR = HOME / "vault" / "email-inbox"
INDEX = OUT_DIR / "_index.csv"
IMAP_HOST = "imap.gmail.com"


def load_env() -> dict:
    env = {}
    for p in ENV_CANDIDATES:
        if not p.exists():
            continue
        for line in p.read_text(errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return env


def creds() -> tuple[str, str]:
    env = {**load_env(), **os.environ}
    user = env.get("GMAIL_USER") or env.get("EMAIL_USER") or ""
    pw = env.get("GMAIL_APP_PASSWORD") or env.get("EMAIL_APP_PASSWORD") or ""
    if not user or not pw:
        sys.exit("TIADA_KELAYAKAN: set GMAIL_USER dan GMAIL_APP_PASSWORD dalam ~/.hermes20/.env")
    return user, pw


def connect() -> imaplib.IMAP4_SSL:
    user, pw = creds()
    m = imaplib.IMAP4_SSL(IMAP_HOST)
    try:
        m.login(user, pw)
    except imaplib.IMAP4.error as exc:
        sys.exit(f"LOGIN_GAGAL: {exc} (App Password 16 aksara diperlukan, bukan kata laluan akaun)")
    return m


def hdr(msg, key: str) -> str:
    raw = msg.get(key, "")
    try:
        return str(make_header(decode_header(raw)))
    except Exception:
        return raw


def body_text(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(
                part.get("Content-Disposition")
            ):
                payload = part.get_payload(decode=True) or b""
                return payload.decode(part.get_content_charset() or "utf-8", "replace")
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True) or b""
                html = payload.decode(part.get_content_charset() or "utf-8", "replace")
                return re.sub(r"<[^>]+>", " ", html)
        return ""
    payload = msg.get_payload(decode=True) or b""
    return payload.decode(msg.get_content_charset() or "utf-8", "replace")


def attachments(msg) -> list[str]:
    names = []
    for part in msg.walk():
        fn = part.get_filename()
        if fn:
            names.append(str(make_header(decode_header(fn))))
    return names


def slug(text: str, limit: int = 48) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", text.lower()).strip("-")
    return (s[:limit] or "email").strip("-")


def fetch(uids: list[bytes]) -> list[dict]:
    m = connect()
    m.select("INBOX", readonly=True)
    out = []
    for uid in uids:
        typ, data = m.uid("FETCH", uid, "(RFC822)")
        if typ != "OK" or not data or not data[0]:
            continue
        msg = email.message_from_bytes(data[0][1])
        out.append(
            {
                "uid": uid.decode(),
                "date": hdr(msg, "Date"),
                "from": hdr(msg, "From"),
                "to": hdr(msg, "To"),
                "subject": hdr(msg, "Subject"),
                "message_id": hdr(msg, "Message-ID"),
                "attachments": attachments(msg),
                "body": body_text(msg).strip(),
            }
        )
    m.logout()
    return out


def search_recent(days: int, maximum: int) -> list[bytes]:
    m = connect()
    m.select("INBOX", readonly=True)
    since = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
    typ, data = m.uid("SEARCH", None, "SINCE", since)
    uids = (data[0].split() if typ == "OK" and data[0] else [])[-maximum:]
    m.logout()
    return uids


def cmd_check(_args) -> None:
    user, _pw = creds()
    m = connect()
    _typ, data = m.select("INBOX", readonly=True)
    typ2, unseen = m.uid("SEARCH", None, "UNSEEN")
    n_unseen = len(unseen[0].split()) if typ2 == "OK" and unseen[0] else 0
    print(json.dumps({"status": "OK", "user": user, "inbox_total": int(data[0] or 0), "unread": n_unseen}))
    m.logout()


def cmd_list(args) -> None:
    for item in fetch(search_recent(args.days, args.max)):
        print(json.dumps({k: item[k] for k in ("uid", "date", "from", "subject", "attachments")}, ensure_ascii=False))


def cmd_save(args) -> None:
    uids = [args.uid.encode()] if args.uid else search_recent(args.days, args.max)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = fetch(uids)
    existing = set()
    if INDEX.exists():
        with INDEX.open(newline="", encoding="utf-8") as fh:
            existing = {r["uid"] for r in csv.DictReader(fh)}

    saved, skipped = [], []
    for it in rows:
        if it["uid"] in existing:
            skipped.append(it["uid"])
            continue
        try:
            dt = email.utils.parsedate_to_datetime(it["date"])
        except Exception:
            dt = datetime.now()
        path = OUT_DIR / f"{dt:%Y-%m-%d}_{it['uid']}_{slug(it['subject'])}.md"
        lampiran = ", ".join(it["attachments"]) or "tiada"
        path.write_text(
            f"# {it['subject']}\n\n"
            f"- **Tarikh:** {it['date']}\n"
            f"- **Daripada:** {it['from']}\n"
            f"- **Kepada:** {it['to']}\n"
            f"- **UID:** {it['uid']}\n"
            f"- **Tag:** {args.tag}\n"
            f"- **Lampiran:** {lampiran}\n"
            f"- **Status:** BARU\n\n"
            f"## Isi\n\n{it['body'][:20000]}\n",
            encoding="utf-8",
        )
        new_file = not INDEX.exists()
        with INDEX.open("a", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            if new_file:
                w.writerow(["uid", "tarikh", "dari", "subjek", "tag", "status", "fail", "lampiran"])
            w.writerow([it["uid"], it["date"], it["from"], it["subject"], args.tag, "BARU", path.name, lampiran])
        saved.append({"uid": it["uid"], "fail": str(path), "subjek": it["subject"]})

    print(json.dumps({"status": "OK", "disimpan": saved, "dilangkau": skipped}, ensure_ascii=False, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser(description="Baca Gmail satu per satu -> fail markdown + indeks CSV")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check")
    p.set_defaults(func=cmd_check)
    p = sub.add_parser("list")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--max", type=int, default=20)
    p.set_defaults(func=cmd_list)
    p = sub.add_parser("save")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--max", type=int, default=20)
    p.add_argument("--uid")
    p.add_argument("--tag", default="umum")
    p.set_defaults(func=cmd_save)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
