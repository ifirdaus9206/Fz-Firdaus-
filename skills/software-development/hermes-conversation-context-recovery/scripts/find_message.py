#!/usr/bin/env python3
"""Cari mesej lama dalam state.db Hermes (read-only, selamat masa gateway jalan).

Contoh:
  python3 find_message.py --contains "format" --role user --recent 40
  python3 find_message.py --session 20261103_211812_c4b32abe --role user --contains "format"
  python3 find_message.py --id 862

Nota: jangan guna `grep -rl ~/.hermes20` — ia masuk node_modules dan timeout.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys

DEFAULT_DB = os.path.expanduser("~/.hermes20/state.db")


def connect(path: str) -> sqlite3.Connection:
    uri = f"file:{os.path.expanduser(path)}?mode=ro"
    con = sqlite3.connect(uri, uri=True, timeout=10)
    con.row_factory = sqlite3.Row
    return con


def fetch(args: argparse.Namespace) -> list[sqlite3.Row]:
    con = connect(args.db)
    where: list[str] = []
    params: list[object] = []
    if args.id is not None:
        where.append("id = ?")
        params.append(args.id)
    if args.session:
        where.append("session_id = ?")
        params.append(args.session)
    if args.role:
        where.append("role = ?")
        params.append(args.role)
    if args.contains:
        where.append("lower(content) LIKE ?")
        params.append(f"%{args.contains.lower()}%")
    sql = "SELECT id, session_id, role, timestamp, substr(content,1,?) AS body FROM messages"
    params.insert(0, args.chars)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(args.recent)
    return con.execute(sql, params).fetchall()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--session", default=None)
    ap.add_argument("--role", default=None, choices=[None, "user", "assistant", "tool"])
    ap.add_argument("--contains", default=None)
    ap.add_argument("--id", type=int, default=None)
    ap.add_argument("--recent", type=int, default=20)
    ap.add_argument("--chars", type=int, default=800)
    args = ap.parse_args()

    if not os.path.exists(os.path.expanduser(args.db)):
        print(f"DB tidak dijumpai: {args.db}", file=sys.stderr)
        return 2
    try:
        rows = fetch(args)
    except sqlite3.Error as exc:
        print(f"Ralat SQL: {exc}", file=sys.stderr)
        return 1

    if not rows:
        print("TIADA REKOD sepadan.")
        return 0

    for r in reversed(rows):
        body = (r["body"] or "").replace("\n", " | ")
        print(f"[{r['id']}] {r['role']} {r['timestamp']} session={r['session_id']}")
        print(body)
        print("---")
    print(f"jumlah: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
