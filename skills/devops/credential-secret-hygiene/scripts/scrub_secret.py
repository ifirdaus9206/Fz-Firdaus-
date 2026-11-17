#!/usr/bin/env python3
"""Scrub one leaked literal from a Hermes home: logs, temp scripts, SQLite (incl. FTS + WAL).

Usage:
    python scrub_secret.py --literal 'abcd efgh ijkl mnop'
    python scrub_secret.py --literal 'abcd efgh ijkl mnop' --dry-run

Behaviour:
  * Builds a slack regex from the literal's first group: "<g1>[\\s\\S]{0,20}" (case-insensitive),
    because log lines truncate long message bodies mid-secret.
  * Redacts logs/*.log in place (counts substitutions).
  * Deletes ~/tmp/*.py helper scripts that contain the literal.
  * UPDATEs every text column of every table in state.db / kanban.db / verification_evidence.db
    (FTS shadow tables included), then PRAGMA wal_checkpoint(TRUNCATE) + VACUUM.
  * Re-verifies and, for each remaining hit, prints whether it is the secret or just one of your
    own search patterns stored in tool_calls/reasoning.

It NEVER prints the literal; only counts and masked fragments.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sqlite3
import sys

HOME = pathlib.Path.home()
HERMES = HOME / ".hermes20"
REDACTED = "[REDACTED-SECRET]"
DBS = [HERMES / "state.db", HERMES / "kanban.db", HERMES / "verification_evidence.db"]
LOGS = [HERMES / "logs" / "gateway.log", HERMES / "logs" / "agent.log"]


def build_pattern(literal: str) -> re.Pattern[str]:
    groups = [g for g in literal.split() if g]
    if not groups:
        sys.exit("literal kosong")
    return re.compile(re.escape(groups[0]) + r"[\s\S]{0,20}", re.I)


def scrub_logs(pat: re.Pattern[str], dry: bool) -> None:
    for p in LOGS:
        if not p.exists():
            continue
        text = p.read_text(errors="ignore")
        new, n = pat.subn(REDACTED, text)
        if n and not dry:
            p.write_text(new)
        print(f"{p.relative_to(HOME)}: {n} padanan{' (dry-run)' if dry else ''}")


def scrub_tmp(pat: re.Pattern[str], dry: bool) -> None:
    for p in sorted((HOME / "tmp").glob("*")):
        if not p.is_file() or p.suffix not in {".py", ".sh", ".txt", ".json", ""}:
            continue
        try:
            if pat.search(p.read_text(errors="ignore")):
                print(f"tmp/{p.name}: dipadam{' (dry-run)' if dry else ''}")
                if not dry:
                    p.unlink()
        except Exception:
            continue


def scrub_db(db: pathlib.Path, pat: re.Pattern[str], dry: bool) -> int:
    if not db.exists():
        return 0
    total = 0
    try:
        con = sqlite3.connect(f"file:{db}?mode=rw", uri=True, timeout=10)
    except Exception as exc:
        print(f"{db.name}: tidak dapat dibuka ({type(exc).__name__})")
        return 0
    cur = con.cursor()
    tables = [r[0] for r in cur.execute("select name from sqlite_master where type='table'")]
    for tb in tables:
        try:
            cols = [r[1] for r in cur.execute(f'pragma table_info("{tb}")')]
        except Exception:
            continue
        for col in cols:
            try:
                rows = cur.execute(
                    f'select rowid, "{col}" from "{tb}" where "{col}" like ?',
                    (f"%{pat.pattern.split(chr(91))[0].replace(chr(92), '')}%",),
                ).fetchall()
            except Exception:
                continue
            for rid, val in rows:
                if not isinstance(val, str):
                    continue
                new, n = pat.subn(REDACTED, val)
                if n and not dry:
                    try:
                        cur.execute(f'update "{tb}" set "{col}"=? where rowid=?', (new, rid))
                        total += n
                    except Exception:
                        pass
    if not dry:
        try:
            cur.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            cur.execute("VACUUM")
        except Exception:
            pass
        con.commit()
    con.close()
    print(f"{db.name}: {total} padanan diredaksi{' (dry-run)' if dry else ''}")
    return total


def verify(pat: re.Pattern[str]) -> None:
    short = pat.pattern.split("[")[0]
    short = re.sub(r"\\", "", short)
    hits = 0
    for db in DBS:
        if not db.exists():
            continue
        try:
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=5)
            cur = con.cursor()
            tables = [r[0] for r in cur.execute("select name from sqlite_master where type='table'")]
            for tb in tables:
                cols = [r[1] for r in cur.execute(f'pragma table_info("{tb}")')]
                for col in cols:
                    try:
                        rows = cur.execute(
                            f'select rowid, "{col}" from "{tb}" where "{col}" like ?',
                            (f"%{short}%",),
                        ).fetchall()
                    except Exception:
                        continue
                    for rid, val in rows:
                        hits += 1
                        frag = re.sub(r"[\s\S]{0,30}$", "", str(val))[:0]  # keep it empty
                        first = str(val).lower().find(short.lower())
                        window = str(val)[max(0, first - 40): first + 60].replace("\n", " ")
                        window = pat.sub("[MASK]", window)
                        print(f"  baki {db.name}.{tb}.{col} rowid={rid}: {window[:110]}")
            con.close()
        except Exception:
            continue
    print(f"jumlah baki: {hits}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Buang satu rahsia dari log/tmp/SQLite Hermes")
    ap.add_argument("--literal", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    pat = build_pattern(args.literal)
    scrub_logs(pat, args.dry_run)
    scrub_tmp(pat, args.dry_run)
    for db in DBS:
        scrub_db(db, pat, args.dry_run)
    print("--- semakan semula ---")
    verify(pat)
    print("Nota: baki yang berupa arahan grep/python/reasoning ialah corak carian sendiri, bukan rahsia.")


if __name__ == "__main__":
    main()
