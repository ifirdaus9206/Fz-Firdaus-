#!/usr/bin/env python3
"""
HERMES CONSOLE — papan pemantau read-only untuk Hermes20 (Ketua) + Hermes19 (Trading Desk).

Jalankan:  python3 app.py        (bind 127.0.0.1:8787 sahaja)
Tiada endpoint menulis ke DB. Semua SQLite dibuka mode=ro.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sqlite3
import socket
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

import base64
import hashlib
import secrets
import shutil
import subprocess
import urllib.request
from typing import Optional

from fastapi import BackgroundTasks, Body, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent
STATIC = BASE / "static"
REG = json.loads((BASE / "homes.json").read_text())
HOMES = {h["key"]: h for h in REG["homes"]}

app = FastAPI(title="Hermes Console", version="1.1")
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

CSRF_TOKEN = secrets.token_urlsafe(24)
LAN_TOKEN = os.environ.get("CONSOLE_LAN_TOKEN", "").strip()
DEFAULT_HOME = os.environ.get("CONSOLE_DEFAULT_HOME", "hermes20").strip() or "hermes20"
DEFAULT_TAB = os.environ.get("CONSOLE_DEFAULT_TAB", "pusat").strip() or "pusat"
ONLY_HOMES = [x.strip() for x in os.environ.get("CONSOLE_HOMES", "").split(",") if x.strip()]
CONSOLE_HOST = os.environ.get("CONSOLE_HOST", "127.0.0.1").strip()
CONSOLE_PORT = int(os.environ.get("CONSOLE_PORT", "8787"))
CONSOLE_BIND = os.environ.get("CONSOLE_BIND", CONSOLE_HOST).strip() or CONSOLE_HOST
CONSOLE_TLS = os.environ.get("CONSOLE_TLS", "").strip() in ("1", "true", "yes")
SCHEME = "https" if CONSOLE_TLS else "http"
ALLOWED_HOSTS = {"127.0.0.1:8787", "localhost:8787", f"127.0.0.1:{CONSOLE_PORT}",
                 f"localhost:{CONSOLE_PORT}"}
# host tambahan (tunnel awam / LAN), dipisah koma: CONSOLE_ALLOWED_HOSTS=a.trycloudflare.com
for _h in os.environ.get("CONSOLE_ALLOWED_HOSTS", "").split(","):
    _h = _h.strip().lower()
    if _h:
        ALLOWED_HOSTS.add(_h)
ALLOWED_ORIGINS = {f"{SCHEME}://127.0.0.1:{CONSOLE_PORT}", f"{SCHEME}://localhost:{CONSOLE_PORT}",
                   "http://127.0.0.1:5174", "https://127.0.0.1:8787"}
for _o in os.environ.get("CONSOLE_ALLOWED_ORIGINS", "").split(","):
    _o = _o.strip().rstrip("/")
    if _o:
        ALLOWED_ORIGINS.add(_o)


@app.middleware("http")
async def _guard(request: Request, call_next):
    """Auth LAN + Host/Origin/CSRF + header keselamatan."""
    # --- mod LAN: token wajib untuk semua laluan kecuali /api/ping ---
    if LAN_TOKEN and request.url.path != "/api/ping":
        tok = (request.query_params.get("t") or request.cookies.get("console_auth")
               or request.headers.get("x-console-auth") or "")
        if tok != LAN_TOKEN:
            if request.url.path.startswith("/api/"):
                return JSONResponse({"error": "token LAN diperlukan (?t=...)"}, status_code=401)
            return JSONResponse({"error": "token LAN diperlukan — buka URL dengan ?t=<token>"},
                                status_code=401)
        if request.query_params.get("t") == LAN_TOKEN:
            from fastapi.responses import RedirectResponse

            url = request.url.remove_query_params("t")
            resp = RedirectResponse(url=str(url), status_code=303)
            resp.set_cookie("console_auth", LAN_TOKEN, httponly=True, samesite="lax",
                            secure=CONSOLE_TLS, max_age=7 * 24 * 3600)
            return resp
    else:
        host = request.headers.get("host", "")
        _tunnel = host.lower().endswith(".trycloudflare.com")
        if host not in ALLOWED_HOSTS and not LAN_TOKEN and not _tunnel:
            return JSONResponse({"error": "host tidak dibenarkan"}, status_code=403)
    origin = request.headers.get("origin")
    _otun = bool(origin) and origin.lower().endswith(".trycloudflare.com")
    if origin and origin not in ALLOWED_ORIGINS and not _otun:
        return JSONResponse({"error": "origin tidak dibenarkan"}, status_code=403)
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        if request.headers.get("x-console-token") != CSRF_TOKEN:
            return JSONResponse({"error": "token konsol tiada atau salah"}, status_code=403)
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    # X-Frame-Options: tiada — kawalan pembingkaian tunggal melalui CSP
    # frame-ancestors di atas (XFO DENY akan menyekat shell desktop).
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Cache-Control"] = "no-store"
    # frame-ancestors: benarkan hanya shell Hermes Desktop (file:// / dev vite)
    # menyemat console. Selain itu console tidak boleh di-iframe.
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; connect-src 'self'; frame-ancestors 'self' file: app: "
        "http://localhost:5174 http://127.0.0.1:5174; base-uri 'none'"
    )
    if request.url.path == "/api/ping":
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    return resp

_SIZE_CACHE: dict[str, tuple[float, int]] = {}


# --------------------------------------------------------------------------- #
# util
# --------------------------------------------------------------------------- #
def home_path(key: str) -> Path:
    if key not in HOMES:
        raise HTTPException(404, f"home tidak dikenali: {key}")
    return Path(HOMES[key]["path"])


def ro_conn(path: Path, name: str) -> sqlite3.Connection:
    p = path / name
    if not p.exists():
        raise HTTPException(404, f"tiada {name} dalam {path.name}")
    con = sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=3.0)
    con.row_factory = sqlite3.Row
    return con


def rows(con, sql, args=()) -> list[dict]:
    return [dict(r) for r in con.execute(sql, args).fetchall()]


def one(con, sql, args=()):
    r = con.execute(sql, args).fetchone()
    return dict(r) if r else None


def iso(ts) -> str | None:
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(float(ts)).isoformat(timespec="seconds")
    except Exception:
        return None


def dir_size_mb(p: Path, ttl: float = 600.0):
    """Saiz dibaca dari cache sahaja (dikemas kini thread latar). None = belum sedia."""
    hit = _SIZE_CACHE.get(str(p))
    if hit and time.time() - hit[0] < ttl:
        return round(hit[1] / 1048576, 1)
    return None


def _size_worker():
    while True:
        for h in REG["homes"]:
            p = Path(h["path"])
            if not p.exists():
                continue
            try:
                out = subprocess.run(["du", "-sk", str(p)], capture_output=True, text=True, timeout=900)
                kb = int(out.stdout.split()[0])
                _SIZE_CACHE[str(p)] = (time.time(), kb * 1024)
            except Exception:
                pass
        time.sleep(300)


def tail(path: Path, n: int = 60, limit: int = 60000) -> list[str]:
    if not path.exists():
        return []
    try:
        with path.open("rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - limit))
            data = f.read().decode("utf-8", "replace")
        return data.splitlines()[-n:]
    except Exception:
        return []


def read_text(p: Path, max_chars: int = 20000) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")[:max_chars]
    except Exception:
        return ""


def get_section(text: str, needle: str) -> str:
    """Ambil kandungan antara heading '## ...needle...' dan '## ' seterusnya."""
    lines = text.splitlines()
    out, grab = [], False
    for ln in lines:
        if ln.startswith("## "):
            if grab:
                break
            grab = needle.lower() in ln.lower()
            continue
        if grab:
            out.append(ln)
    return "\n".join(out).strip()


def md_table(section: str) -> list[list[str]]:
    tbl = []
    for ln in section.splitlines():
        s = ln.strip()
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            tbl.append(cells)
    return tbl


def _plain(s: str) -> str:
    return s.replace("**", "").replace("`", "").strip()


def md_dash_bullets(section: str) -> list[dict]:
    """'- `KUNCI = nilai` — teks' -> {n, title, text}"""
    items = []
    for ln in section.splitlines():
        s = ln.strip()
        if not s.startswith(("- ", "* ")):
            continue
        body = s[2:].strip()
        m = re.match(r"^`([^`]+)`\s*(.*)$", body)
        if m:
            items.append({"n": len(items) + 1, "title": _plain(m.group(1).strip(" .")),
                          "text": _plain(m.group(2).strip(" —-–"))})
        else:
            items.append({"n": len(items) + 1, "title": _plain(body), "text": ""})
    return items


def md_bullets(section: str) -> list[dict]:
    """'1. **Tajuk.** teks' -> {n, title, text}"""
    items = []
    for ln in section.splitlines():
        m = re.match(r"^\s*(\d+)\.\s+\*\*(.+?)\*\*\s*(.*)$", ln)
        if m:
            items.append({"n": int(m.group(1)), "title": _plain(m.group(2)).rstrip("."),
                          "text": _plain(m.group(3))})
    return items


def gateway_state(key: str) -> dict:
    p = home_path(key) / "gateway_state.json"
    if not p.exists():
        return {"state": "tiada gateway", "pid_alive": None, "platforms": {}}
    try:
        d = json.loads(p.read_text())
    except Exception:
        return {"state": "tidak terbaca"}
    pid = d.get("pid")
    alive = False
    if pid:
        try:
            os.kill(int(pid), 0)
            alive = True
        except Exception:
            alive = False
    d["pid_alive"] = alive
    return d


def default_model(key: str) -> str:
    txt = read_text(home_path(key) / "config.yaml", 40000)
    m = re.search(r"^model:\s*\n((?:\s+.*\n)+)", txt, re.M)
    if m:
        mm = re.search(r"^\s+default:\s*(\S+)", m.group(1), re.M)
        if mm:
            return mm.group(1).strip("'\"")
    mm = re.search(r"^\s*default:\s*(\S+)", txt, re.M)
    return mm.group(1).strip("'\"") if mm else "?"


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #
@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/ping")
def api_ping():
    """Probe ringan untuk plugin desktop (CORS terbuka; tiada data sensitif)."""
    return {"ok": True, "app": "hermes-console", "version": "1.1",
            "workflow": (STATIC / "img" / "workflow.png").exists()}


@app.get("/api/meta")
def api_meta():
    return {
        "app": "Hermes Console",
        "version": "1.1",
        "now": datetime.now().isoformat(timespec="seconds"),
        "csrf": CSRF_TOKEN,
        "lan": bool(LAN_TOKEN),
        "default_home": DEFAULT_HOME if DEFAULT_HOME in HOMES else "hermes20",
        "default_tab": DEFAULT_TAB,
        "tls": CONSOLE_TLS,
        "base": f"{SCHEME}://{CONSOLE_HOST}:{CONSOLE_PORT}",
        "homes": [
            {k: h[k] for k in ("key", "label", "sub", "path", "accent")}
            | {"model": default_model(h["key"])}
            for h in REG["homes"]
            if not ONLY_HOMES or h["key"] in ONLY_HOMES
        ],
    }


@app.get("/api/overview")
def api_overview(home: str = "hermes20"):
    p = home_path(home)
    con = ro_conn(p, "state.db")
    tot = one(con, """
        SELECT COUNT(*) sessions, COALESCE(SUM(message_count),0) messages,
               COALESCE(SUM(tool_call_count),0) tools,
               COALESCE(SUM(input_tokens),0) tin, COALESCE(SUM(output_tokens),0) tout,
               COALESCE(SUM(estimated_cost_usd),0) cost,
               MAX(started_at) last_start
        FROM sessions""")
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    today = one(con, "SELECT COUNT(*) n, COALESCE(SUM(tool_call_count),0) t FROM sessions WHERE started_at >= ?", (today_start,))
    last = one(con, """
        SELECT id, title, source, message_count, tool_call_count, started_at, last_activity_at,
               input_tokens, output_tokens, estimated_cost_usd, last_activity_description
        FROM sessions ORDER BY COALESCE(last_activity_at, started_at) DESC LIMIT 1""")

    since = (datetime.now() - timedelta(days=13)).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    per_day = rows(con, """
        SELECT date(started_at,'unixepoch','localtime') d,
               COUNT(*) sessions,
               COALESCE(SUM(tool_call_count),0) tools,
               COALESCE(SUM(input_tokens+output_tokens),0) tokens
        FROM sessions WHERE started_at >= ? GROUP BY d ORDER BY d""", (since,))
    have = {r["d"]: r for r in per_day}
    series = []
    for i in range(14):
        d = (datetime.now() - timedelta(days=13 - i)).strftime("%Y-%m-%d")
        r = have.get(d, {"sessions": 0, "tools": 0, "tokens": 0})
        series.append({"date": d, "sessions": r["sessions"], "tools": r["tools"], "tokens": r["tokens"]})
    con.close()

    db_size = round((p / "state.db").stat().st_size / 1048576, 1) if (p / "state.db").exists() else 0
    recent = []
    try:
        con = ro_conn(p, "state.db")
        recent = rows(con, """
            SELECT id, title, source, message_count, tool_call_count, started_at, ended_at,
                   model, estimated_cost_usd, last_activity_description
            FROM sessions ORDER BY started_at DESC LIMIT 6""")
        con.close()
    except Exception:
        pass

    return {
        "home": home, "label": HOMES[home]["label"],
        "totals": tot, "today": today,
        "last": last | {"started_iso": iso(last["started_at"])} if last else None,
        "series": series,
        "storage": {"home_mb": dir_size_mb(p), "state_db_mb": db_size},
        "gateway": gateway_state(home),
        "model": default_model(home),
        "recent": [r | {"started_iso": iso(r["started_at"])} for r in recent],
    }


@app.get("/api/sessions")
def api_sessions(home: str = "hermes20", limit: int = Query(60, ge=1, le=500), q: str = ""):
    p = home_path(home)
    con = ro_conn(p, "state.db")
    sql = """
        SELECT id, title, source, chat_type, model, message_count, tool_call_count,
               input_tokens, output_tokens, reasoning_tokens, estimated_cost_usd,
               started_at, ended_at, last_activity_at, archived, last_activity_description
        FROM sessions"""
    args: list = []
    if q:
        sql += " WHERE (title LIKE ? OR last_activity_description LIKE ? OR id LIKE ?)"
        args += [f"%{q}%"] * 3
    sql += " ORDER BY started_at DESC LIMIT ?"
    args.append(limit)
    data = rows(con, sql, tuple(args))
    con.close()
    for r in data:
        r["started_iso"] = iso(r["started_at"])
        r["ended_iso"] = iso(r["ended_at"])
        r["duration_s"] = int((r["ended_at"] or time.time()) - r["started_at"]) if r["started_at"] else None
    return {"home": home, "count": len(data), "sessions": data}


@app.get("/api/session/{home}/{sid}")
def api_session(home: str, sid: str, limit: int = Query(400, ge=1, le=2000)):
    p = home_path(home)
    con = ro_conn(p, "state.db")
    s = one(con, "SELECT * FROM sessions WHERE id = ?", (sid,))
    if not s:
        con.close()
        raise HTTPException(404, "sesi tidak dijumpai")
    msgs = rows(con, """
        SELECT id, role, content, tool_name, tool_calls, timestamp, token_count, finish_reason
        FROM messages WHERE session_id = ? AND active = 1
        ORDER BY id ASC LIMIT ?""", (sid, limit))
    con.close()
    out = []
    for m in msgs:
        tools = []
        if m.get("tool_calls"):
            try:
                for tc in json.loads(m["tool_calls"]):
                    fn = (tc or {}).get("function", {}) or {}
                    tools.append({"name": fn.get("name"), "args": (fn.get("arguments") or "")[:400]})
            except Exception:
                pass
        out.append({
            "id": m["id"], "role": m["role"],
            "content": (m["content"] or "")[:6000],
            "tool_name": m["tool_name"], "tools": tools,
            "ts": iso(m["timestamp"]), "tokens": m["token_count"],
        })
    s["started_iso"] = iso(s["started_at"])
    s["ended_iso"] = iso(s["ended_at"])
    s.pop("system_prompt", None)
    return {"session": s, "messages": out, "shown": len(out), "count": s.get("message_count")}


@app.get("/api/org")
def api_org():
    p = home_path("hermes20")
    soul = read_text(p / "SOUL.md", 30000)

    systems = []
    enjin = get_section(soul, "ENJIN")
    for row in md_table(enjin)[1:]:
        if len(row) < 3:
            continue
        fname = row[0].strip("`").replace("system/", "")
        fpath = p / "system" / fname
        systems.append({
            "file": f"system/{fname}",
            "name": fname.replace(".md", ""),
            "role": _plain(row[1]),
            "when": _plain(row[2]),
            "exists": fpath.exists(),
            "kb": round(fpath.stat().st_size / 1024, 1) if fpath.exists() else 0,
        })

    flow_raw = get_section(soul, "ALIRAN WAJIB")
    m = re.search(r"```(.*?)```", flow_raw, re.S)
    flow = []
    for ln in (m.group(1) if m else flow_raw).splitlines():
        s = ln.strip()
        if not s:
            continue
        s = s.lstrip("→").strip()
        if s:
            flow.append(s)

    laws = md_bullets(get_section(soul, "UNDANG-UNDANG"))

    skills = {}
    for k, h in HOMES.items():
        sd = Path(h["path"]) / "skills"
        names = sorted([d.name for d in sd.iterdir() if d.is_dir()]) if sd.exists() else []
        skills[k] = {"count": len(names), "names": names}

    gateway = gateway_state("hermes20")
    return {
        "identity": soul.splitlines()[0].lstrip("# ").strip() if soul else "",
        "systems": systems,
        "flow": flow,
        "laws": laws,
        "skills": skills,
        "gateway": gateway,
        "language": get_section(soul, "BAHASA"),
    }


@app.get("/api/trading")
def api_trading(limit: int = Query(25, ge=1, le=200)):
    p = home_path("hermes19")
    atc = p / "autonomous_trading_controller"
    soul = read_text(p / "SOUL.md", 30000)

    scope = md_table(get_section(soul, "SKOP PASARAN"))
    symbols = []
    for row in scope[1:]:
        if len(row) >= 4:
            symbols.append({"symbol": row[0], "class": row[1], "leverage": row[2], "session": row[3]})
    _dsec = get_section(soul, "DOKTRIN RISIKO")
    doctrine = md_bullets(_dsec) or md_dash_bullets(_dsec)

    decisions, err = [], None
    f = atc / "decisions.log.jsonl"
    if f.exists():
        try:
            lines = [ln for ln in f.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
            for ln in lines[-limit:]:
                r = json.loads(ln)
                d = r.get("decision", {}) or {}
                rr = d.get("risk_result", {}) or {}
                decisions.append({
                    "ts": r.get("timestamp_utc"),
                    "status": d.get("status"),
                    "symbol": d.get("symbol"),
                    "direction": d.get("direction"),
                    "confidence": d.get("confidence"),
                    "mode": d.get("mode"),
                    "data_quality": d.get("data_quality"),
                    "risk_check": d.get("risk_check"),
                    "risk_approved": rr.get("approved") if isinstance(rr, dict) else None,
                    "agreement": ((d.get("fused_signal") or {}).get("agreement")),
                })
            decisions.reverse()
        except Exception as e:
            err = str(e)

    paper, perr = [], None
    cf = atc / "paper_trading_log.csv"
    if cf.exists():
        try:
            with cf.open(newline="", encoding="utf-8", errors="replace") as fh:
                paper = [dict(r) for r in csv.DictReader(fh)][-limit:]
        except Exception as e:
            perr = str(e)

    counts = {}
    for d in decisions:
        counts[d["status"] or "?"] = counts.get(d["status"] or "?", 0) + 1

    return {
        "home": "hermes19",
        "identity": soul.splitlines()[0].lstrip("# ").strip() if soul else "",
        "symbols": symbols, "doctrine": doctrine,
        "decisions": decisions, "decision_error": err,
        "paper": paper, "paper_error": perr, "paper_live": paper_state(),
        "counts": counts,
        "logs": {"decisions_lines": len(decisions)},
        "gateway": gateway_state("hermes19"),
        "model": default_model("hermes19"),
    }


# ---------------------------------------------------------------- SOFIA (PC)
SOFIA_DIR = Path.home() / "sofia-status"
SOFIA_JSON = SOFIA_DIR / "status.json"


@app.get("/api/sofia")
def api_sofia():
    """Status ejen SOFIA di PC — dibaca daripada repo relay 'sofia-status'.

    Telefon menarik repo itu setiap 5 minit melalui cron (git pull SSH).
    Konsol tidak membuat permintaan keluar: ia baca fail tempatan sahaja.
    """
    out = {"ada": False, "folder": str(SOFIA_DIR), "fail": str(SOFIA_JSON)}
    if not SOFIA_JSON.is_file():
        out["nota"] = ("repo relay belum ada — buat LANGKAH-GITHUB.md dahulu, "
                       "selepas itu cron tarik akan mengisi folder ini")
        return out
    try:
        data = json.loads(SOFIA_JSON.read_text(encoding="utf-8"))
    except Exception as e:
        out["ralat"] = "status.json tidak boleh dibaca: %s" % str(e)[:160]
        return out
    age = int(time.time() - SOFIA_JSON.stat().st_mtime)
    out.update({"ada": True, "umur_s": age, "basi": age > 960, "data": data})
    logp = SOFIA_DIR / "tarik.log"
    if logp.is_file():
        try:
            lines = logp.read_text(encoding="utf-8", errors="replace").strip().splitlines()
            out["log"] = lines[-8:]
        except Exception:
            pass
    return out


@app.get("/api/health")
def api_health():
    out = {"homes": [], "cron": {}, "processes": [], "logs": {}}
    for k, h in HOMES.items():
        p = Path(h["path"])
        dbs = []
        for name in ("state.db", "kanban.db"):
            f = p / name
            if f.exists():
                dbs.append({"name": name, "mb": round(f.stat().st_size / 1048576, 2)})
        out["homes"].append({
            "key": k, "label": h["label"], "path": str(p),
            "exists": p.exists(),
            "home_mb": dir_size_mb(p),
            "dbs": dbs,
            "gateway": gateway_state(k),
            "model": default_model(k),
        })

    p20 = home_path("hermes20")
    hb = p20 / "cron" / "ticker_heartbeat"
    ls = p20 / "cron" / "ticker_last_success"
    out["cron"] = {
        "heartbeat": read_text(hb, 200).strip(),
        "heartbeat_age_s": int(time.time() - hb.stat().st_mtime) if hb.exists() else None,
        "last_success": read_text(ls, 200).strip(),
        "executions": [],
    }
    try:
        con = ro_conn(p20, "cron/executions.db")
        out["cron"]["executions"] = rows(con, """
            SELECT job_id, status, claimed_at, finished_at, error FROM executions
            ORDER BY claimed_at DESC LIMIT 15""")
        con.close()
    except Exception:
        pass

    try:
        out["processes"] = json.loads(read_text(p20 / "processes.json", 100000) or "[]")
    except Exception:
        out["processes"] = []

    for label, path in (
        ("errors", p20 / "logs" / "errors.log"),
        ("gateway", p20 / "logs" / "gateway.log"),
        ("agent", p20 / "logs" / "agent.log"),
    ):
        out["logs"][label] = tail(path, 40)
    out["now"] = datetime.now().isoformat(timespec="seconds")
    return out



# --------------------------------------------------------------------------- #
# AGENCY — roster msitarzewski/agency-agents yang ada di dalam hermes20
# --------------------------------------------------------------------------- #
DIV_ROLE = {
    "academic": "Rujukan konsep & kajian — suapan awal kepada agent_factory.",
    "design": "Spesifikasi visual sebelum bina (fasa reka bentuk workflow).",
    "engineering": "Pelaksana teknikal; terima DAG daripada workflow_generator.",
    "finance": "Analisis kos/pulangan; asas belanjawan projek.",
    "game-development": "Domain khusus enjin permainan (Unity/Unreal/Godot/Blender).",
    "gis": "Data spatial & peta; laporan berasaskan lokasi.",
    "healthcare": "Domain klinikal; wajib semakan pematuhan.",
    "marketing": "Kandungan & kempen; output ke saluran luar.",
    "paid-media": "Belanjawan iklan; kawalan perbelanjaan.",
    "product": "Takrif skop/PRD sebelum tugasan dipecah.",
    "project-management": "WBS & jadual; berganding dengan orchestrator.",
    "research": "Recon sumber & sitasi; suapan bukti.",
    "sales": "Bahan jualan & saluran prospek.",
    "security": "Gerbang wajib sebelum completion_system.",
    "spatial-computing": "AR/VR & spatial; domain khusus peranti.",
    "specialized": "Orkestrator/kritik silang — guna untuk audit kerja agent lain.",
    "support": "Jawapan pengguna & dokumen bantuan.",
    "testing": "Bukti untuk qa_system; lalai NEEDS_WORK sehingga diuji.",
}

DIV_SKILLS = {
    "academic": ["research", "note-taking"],
    "design": ["creative", "productivity"],
    "engineering": ["software-development", "devops", "github"],
    "finance": ["productivity", "trading-systems"],
    "game-development": ["creative"],
    "gis": ["research", "productivity"],
    "healthcare": ["productivity"],
    "marketing": ["creative", "social-media"],
    "paid-media": ["social-media"],
    "product": ["productivity", "project-management"],
    "project-management": ["project-management", "note-taking"],
    "research": ["research", "note-taking"],
    "sales": ["email", "productivity"],
    "security": ["software-development", "devops"],
    "spatial-computing": ["creative"],
    "specialized": ["autonomous-ai-agents", "software-development"],
    "support": ["email", "productivity"],
    "testing": ["software-development"],
}

_AG: dict = {"key": None, "agents": [], "divisions": {}, "files": 0}


def _load_agency() -> dict:
    """Muat roster + divisions.json (cache ikut mtime)."""
    base = home_path("hermes20") / "agency-agents"
    cat = home_path("hermes20") / "plugins" / "agency-agents-router" / "data" / "agents.json"
    if not cat.exists():
        raise HTTPException(404, "katalog agency json tiada")
    key = (cat.stat().st_mtime, base.stat().st_mtime if base.exists() else 0)
    if _AG["key"] == key and _AG["agents"]:
        return _AG
    try:
        agents = json.loads(cat.read_text(encoding="utf-8", errors="replace"))
    except Exception as e:
        raise HTTPException(500, f"katalog tidak terbaca: {e}")
    divisions = {}
    dj = base / "divisions.json"
    if dj.exists():
        try:
            divisions = json.loads(dj.read_text())["divisions"]
        except Exception:
            divisions = {}
    md_files = 0
    if base.exists():
        md_files = sum(1 for f in base.glob("*/*.md"))
        md_files += sum(1 for f in base.glob("*/*/*.md"))
    _AG.update({"key": key, "agents": agents, "divisions": divisions, "files": md_files})
    return _AG


def _agency_usage() -> dict:
    """Kira panggilan sebenar tool agency daripada state.db (baca-sahaja)."""
    events, calls, errors = [], {}, 0
    try:
        con = ro_conn(home_path("hermes20"), "state.db")
    except HTTPException:
        return {"events": [], "calls": {}, "sessions": 0}
    q = """
        SELECT session_id, tool_name, tool_calls, timestamp FROM messages
        WHERE tool_calls LIKE '%agency_agents%'
           OR tool_name LIKE 'agency%'
        ORDER BY timestamp ASC"""
    try:
        for r in con.execute(q).fetchall():
            sid = r["session_id"]
            ts = iso(r["timestamp"])
            if r["tool_calls"]:
                try:
                    for tc in json.loads(r["tool_calls"]):
                        fn = (tc or {}).get("function") or {}
                        name, args = fn.get("name"), {}
                        try:
                            args = json.loads(fn.get("arguments") or "{}")
                        except Exception:
                            args = {}
                        if name == "tool_call":  # pembalut generik
                            name = args.get("name") or name
                            args = args.get("arguments") or {}
                        if not str(name).startswith("agency_agents"):
                            continue
                        slug = args.get("slug") or args.get("name") or args.get("query")
                        calls[name] = calls.get(name, 0) + 1
                        events.append({"ts": ts, "session": sid, "tool": name, "ref": slug})
                except Exception:
                    errors += 1
            elif r["tool_name"] and str(r["tool_name"]).startswith("agency"):
                calls[r["tool_name"]] = calls.get(r["tool_name"], 0) + 0
    except Exception:
        errors += 1
    finally:
        con.close()
    return {
        "events": events[-120:],
        "calls": calls,
        "sessions": len({e["session"] for e in events}),
        "errors": errors,
    }


_DRIFT_CACHE: dict = {"key": None, "data": {}}


def _agency_drift(base: Path, roster: list[dict], md_files: int) -> dict:
    """Kira drift secara langsung (bukan percaya fail laporan lama).

    Laporan `logs/agency-catalog-drift.txt` hanya dipaparkan sebagai metadata;
    angka drift dikira semula daripada katalog + korpus app setiap kali cache luput.
    """
    corpus = home_path("hermes20") / "agency-agents-app" / "src-tauri" / "resources" / "corpus-baseline"
    cat = home_path("hermes20") / "plugins" / "agency-agents-router" / "data" / "agents.json"
    key = (cat.stat().st_mtime if cat.exists() else 0,
           corpus.stat().st_mtime if corpus.exists() else 0,
           len(roster))
    if _DRIFT_CACHE["key"] == key and _DRIFT_CACHE["data"]:
        return _DRIFT_CACHE["data"]

    def k(a):
        return (a.get("division") or "?", a.get("slug") or "?")

    by_key = {k(a): a for a in roster}
    corpus_entries = {}
    if corpus.exists():
        for p in corpus.glob("*/*.md"):
            try:
                txt = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", txt, re.S)
            body = txt[m.end():].strip() if m else txt.strip()
            div = p.parent.name
            stem = p.stem
            slug = stem[len(div) + 1:] if stem.startswith(div + "-") else stem
            corpus_entries[(div, slug)] = {"path": f"{div}/{p.name}", "body": body}

    only_app = sorted(set(corpus_entries) - set(by_key))
    only_active = sorted(set(by_key) - set(corpus_entries))
    body_diff = [f"{d}/{s}" for (d, s), e in corpus_entries.items()
                 if (d, s) in by_key and (by_key[(d, s)].get("body") or "").strip() != e["body"]]
    layout = [e["path"] for (d, s), e in corpus_entries.items()
              if (d, s) in by_key and by_key[(d, s)].get("source_path") != e["path"]]
    missing = [a["slug"] for a in roster
               if a.get("source_path") and not (base / a["source_path"]).exists()]

    report = None
    rp = home_path("hermes20") / "logs" / "agency-catalog-drift.txt"
    if rp.exists():
        report = {"file": "logs/agency-catalog-drift.txt", "at": iso(rp.stat().st_mtime),
                  "age_h": round((time.time() - rp.stat().st_mtime) / 3600, 1)}

    data = {
        "missing_source": len(missing),
        "missing_sample": missing[:10],
        "md_files_on_disk": md_files,
        "roster": len(roster),
        "corpus_files": len(corpus_entries),
        "report": report,
        "reported": {"only_app": len(only_app), "only_active": len(only_active),
                     "body_diff": len(body_diff), "layout": len(layout)},
        "live": True,
        "samples": {"only_app": [f"{d}/{s}" for d, s in only_app[:5]],
                    "only_active": [f"{d}/{s}" for d, s in only_active[:5]],
                    "body_diff": body_diff[:5]},
    }
    _DRIFT_CACHE.update({"key": key, "data": data})
    return data


@app.get("/api/agency")
def api_agency(q: str = "", division: str = "", limit: int = Query(300, ge=1, le=400)):
    base = home_path("hermes20") / "agency-agents"
    data = _load_agency()
    roster = data["agents"]
    usage = _agency_usage()
    used = {}
    for e in usage["events"]:
        if e.get("ref"):
            used[e["ref"]] = used.get(e["ref"], 0) + 1

    skills_root = home_path("hermes20") / "skills"
    skills = sorted([d.name for d in skills_root.iterdir() if d.is_dir()]) if skills_root.exists() else []

    counts: dict[str, int] = {}
    for a in roster:
        counts[a.get("division", "?")] = counts.get(a.get("division", "?"), 0) + 1

    divs = []
    for key, meta in (data["divisions"] or {}).items():
        hits = [s for s in skills if any(s.startswith(p) for p in DIV_SKILLS.get(key, []))]
        divs.append({
            "key": key, "label": meta.get("label", key), "color": meta.get("color", "#5ee3a1"),
            "icon": meta.get("icon"), "count": counts.get(key, 0),
            "role": DIV_ROLE.get(key, ""), "skills": hits,
        })
    for key, n in counts.items():
        if key not in (data["divisions"] or {}):
            divs.append({"key": key, "label": key, "color": "#5ee3a1", "count": n,
                         "role": "", "skills": []})
    divs.sort(key=lambda d: -d["count"])

    ql = q.lower().strip()
    items = []
    for a in roster:
        if division and a.get("division") != division:
            continue
        hay = f"{a.get('slug','')} {a.get('name','')} {a.get('description','')} {a.get('vibe','')}".lower()
        if ql and ql not in hay:
            continue
        sp = a.get("source_path") or ""
        items.append({
            "slug": a.get("slug"), "name": a.get("name"), "division": a.get("division"),
            "emoji": a.get("emoji"), "color": (a.get("color") or "").strip('"'),
            "description": a.get("description"), "vibe": a.get("vibe"),
            "source_path": sp, "has_source": bool(sp) and (base / sp).exists(),
            "uses": used.get(a.get("slug"), 0),
        })
    items.sort(key=lambda x: (-x["uses"], x["name"] or ""))

    drift = _agency_drift(base, roster, data["files"])
    used_slugs = len({e["ref"] for e in usage["events"] if e.get("ref")})
    _totals = {
        "agents": len(roster), "divisions": len(divs), "filtered": len(items),
        "uses": len(usage["events"]), "sessions": usage["sessions"],
        "used_agents": used_slugs, "unused_agents": max(0, len(roster) - used_slugs),
    }
    _pilots = _agency_pilots(roster, used, divs)
    _ideas = _agency_ideas(_totals, divs, drift, usage["calls"], _pilots)

    return {
        "totals": _totals,
        "ideas": _ideas,
        "pilots": _pilots,
        "calls": usage["calls"],
        "divisions": divs,
        "agents": items[:limit],
        "events": usage["events"][-25:][::-1],
        "drift": drift,
        "skills": skills,
        "hermes19": {**_agency_home19_count(),
                     "slugs": _agency_home19_slugs()},
        "git": _git_info(base),
        "source": {
            "catalog": "plugins/agency-agents-router/data/agents.json",
            "corpus": "agency-agents/",
        },
    }


_GIT_CACHE: dict = {"at": 0, "data": {}}


def _git_info(base: Path) -> dict:
    """Commit/remote sumber agency-agents (cache 5 min)."""
    if time.time() - _GIT_CACHE["at"] < 300 and _GIT_CACHE["data"]:
        return _GIT_CACHE["data"]
    out = {"repo": "msitarzewski/agency-agents", "path": str(base)}
    try:
        def g(*a):
            return subprocess.run(["git", "-C", str(base), *a], capture_output=True,
                                  text=True, timeout=6).stdout.strip()
        head = g("log", "-1", "--format=%H|%ad|%s", "--date=iso")
        if head:
            h, d, s = head.split("|", 2)
            out.update({"commit": h[:7], "commit_full": h, "date": d, "subject": s})
        out["remote"] = g("remote", "get-url", "origin") or "–"
        dirty = g("status", "--porcelain")
        out["dirty_files"] = len([x for x in dirty.splitlines() if x.strip()])
        out["branch"] = g("rev-parse", "--abbrev-ref", "HEAD") or "?"
    except Exception as e:
        out["error"] = str(e)
    _GIT_CACHE.update({"at": time.time(), "data": out})
    return out


def _agency_pilots(roster: list[dict], used: dict, divs: list[dict]) -> list[dict]:
    """1 ejen juruterbang per divisi, dipilih daripada data (belum dipakai + padan skill)."""
    by_div: dict[str, list[dict]] = {}
    for a in roster:
        by_div.setdefault(a.get("division"), []).append(a)
    out = []
    for d in divs:
        cands = [a for a in by_div.get(d["key"], []) if not used.get(a.get("slug"))]
        if not cands:
            continue
        tokens = set()
        for s in d["skills"]:
            tokens.update(t for t in s.replace("-", " ").split() if len(t) > 3)

        def score(a):
            hay = f"{a.get('slug','')} {a.get('description') or ''}".lower()
            hit = sum(1 for t in tokens if t in hay)
            return (-hit, len(a.get("slug") or ""), a.get("slug") or "")

        best = sorted(cands, key=score)[0]
        out.append({
            "division": d["key"], "label": d["label"], "slug": best.get("slug"),
            "name": best.get("name"), "emoji": best.get("emoji"),
            "skills": len(d["skills"]),
            "reason": ("padan skill tempatan: " + ", ".join(d["skills"][:2])) if d["skills"]
                      else "divisi tiada skill tempatan - guna untuk nasihat sahaja",
        })
    return out


def _agency_ideas(totals: dict, divs: list[dict], drift: dict, calls: dict,
                  pilots: list[dict] | None = None) -> list[dict]:
    """Cadangan yang dijana daripada data sebenar (bukan teks statik)."""
    ideas = []
    pilots = pilots or []
    unused = totals.get("unused_agents", 0)
    if unused:
        ideas.append({
            "kind": "warn", "title": f"{unused} daripada {totals['agents']} ejen belum pernah dipakai",
            "detail": f"Direkod daripada {totals['uses']} panggilan tool agency dalam {totals['sessions']} sesi. "
                      f"Mulakan dengan {len(pilots)} juruterbang (1 per divisi) di bawah: klik untuk buka, "
                      "kemudian guna agency_agents_delegate supaya kerja dijejak sebagai peristiwa.",
        })
    else:
        ideas.append({
            "kind": "ok", "title": f"Semua {totals['agents']} ejen pernah dipakai",
            "detail": f"{totals['uses']} panggilan dalam {totals['sessions']} sesi. Teruskan jejak melalui router.",
        })
    noskill = [d for d in divs if not d["skills"]]
    if noskill:
        ideas.append({
            "kind": "bad", "title": f"{len(noskill)} divisi tiada skill tempatan",
            "detail": "Tanpa skill sokongan, ejen ini hanya memberi nasihat teks: "
                      + ", ".join(f"{d['label']}({d['count']})" for d in noskill[:6])
                      + ". Bina skill dahulu atau elak tugasan yang perlu eksekusi.",
        })
    rep = drift.get("reported", {})
    bd = rep.get("body_diff", 0)
    if bd:
        ideas.append({
            "kind": "warn", "title": f"{bd} badan ejen berbeza daripada korpus app",
            "detail": "Katalog router dan korpus app tidak segerak. Jalankan "
                      "~/.hermes20/scripts/sync_agency_catalog.py untuk muat semula, kemudian semak laporan drift.",
        })
    else:
        ideas.append({
            "kind": "ok", "title": f"Katalog segerak: {drift.get('corpus_files', 0)}/{drift.get('roster', 0)} badan sama",
            "detail": "Dikira langsung daripada katalog + korpus app setiap muat, bukan daripada fail laporan lama.",
        })
    ms = drift.get("missing_source", 0)
    if ms:
        ideas.append({
            "kind": "warn", "title": f"{ms} path katalog tidak padan cakera",
            "detail": "Betulkan sekali gus: python3 ~/.hermes20/scripts/sync_agency_catalog.py --fix-paths "
                      "(backup .bak dibuat dahulu).",
        })
    else:
        ideas.append({
            "kind": "ok", "title": f"{drift.get('roster', 0)}/{drift.get('roster', 0)} path katalog padan cakera",
            "detail": "Setiap source_path dalam katalog merujuk fail .md yang benar-benar wujud.",
        })
    if rep.get("layout"):
        ideas.append({
            "kind": "ok", "title": f"{rep['layout']} beza susun atur (subfolder vs rata)",
            "detail": "Korpus app simpan path rata; repo git guna subfolder (unity/, godot/, unreal-engine/). "
                      "Badan prompt sama - bukan kehilangan fail.",
        })
    if calls.get("agency_agents_delegate", 0) == 0:
        ideas.append({
            "kind": "ok", "title": "Belum ada delegasi sebenar melalui router",
            "detail": "Setakat ini hanya search/inspect/load. Untuk tugasan berpasukan, guna "
                      "agency_agents_delegate supaya kerja dijejak sebagai satu peristiwa, bukan salinan prompt.",
        })
    else:
        ideas.append({
            "kind": "ok", "title": f"{calls['agency_agents_delegate']} delegasi sebenar dijejak",
            "detail": "Router merekod delegasi sebagai peristiwa; penggunaan ejen dikemas kini automatik.",
        })
    return ideas


def _agency_home19_slugs() -> list[str]:
    p = Path(HOMES["hermes19"]["path"]) / "plugins" / "agency-agents-router" / "data" / "agents.json"
    try:
        return [a.get("slug") for a in json.loads(p.read_text(encoding="utf-8", errors="replace"))]
    except Exception:
        return []


def _agency_home19_count() -> dict:
    p = Path(HOMES["hermes19"]["path"]) / "plugins" / "agency-agents-router" / "data" / "agents.json"
    if not p.exists():
        return {"agents": 0, "note": "tiada katalog"}
    try:
        return {"agents": len(json.loads(p.read_text(encoding="utf-8", errors="replace")))}
    except Exception:
        return {"agents": 0, "note": "tidak terbaca"}


@app.get("/api/agency/agent/{slug}")
def api_agency_agent(slug: str):
    data = _load_agency()
    a = next((x for x in data["agents"] if x.get("slug") == slug), None)
    if not a:
        raise HTTPException(404, f"ejen tidak dijumpai: {slug}")
    base = home_path("hermes20") / "agency-agents"
    body = a.get("body") or ""
    if not body and a.get("source_path"):
        body = read_text(base / a["source_path"], 20000)
    usage = _agency_usage()
    mine = [e for e in usage["events"] if e.get("ref") == slug]
    div = a.get("division")
    return {
        "slug": slug, "name": a.get("name"), "division": div,
        "division_label": (data["divisions"].get(div) or {}).get("label", div),
        "emoji": a.get("emoji"), "color": (a.get("color") or "").strip('"'),
        "description": a.get("description"), "vibe": a.get("vibe"),
        "body": body[:16000], "source_path": a.get("source_path"),
        "has_source": bool(a.get("source_path")) and (base / a["source_path"]).exists(),
        "role_in_org": DIV_ROLE.get(div, ""),
        "uses": len(mine), "sessions": sorted({e["session"] for e in mine}),
        "load_hint": f'agency_agents_load slug="{slug}"',
    }





# --------------------------------------------------------------------------- #
# ROSTER KETUA (282 ejen: archetype, tier, hasil) + PAPAN EJEN (mobile-first)
# --------------------------------------------------------------------------- #
def _ketua_agents() -> list[dict]:
    import agency_runner as ar

    return (ar.load_ketua().get("agents") or [])


@app.get("/api/agency/ketua")
def api_agency_ketua(q: str = "", archetype: str = "", tier: str = "",
                     division: str = "", limit: int = Query(400, ge=1, le=400)):
    """Daftar Ketua: 282 ejen dengan archetype, tier kualiti, hasil, bila dipilih."""
    import agency_runner as ar

    d = ar.load_ketua()
    agents = d.get("agents") or []
    ql = q.lower().strip()
    items = []
    for a in agents:
        if archetype and a.get("archetype") != archetype:
            continue
        if tier and (a.get("kualiti") or {}).get("tier") != tier:
            continue
        if division and a.get("division") != division:
            continue
        hay = (f"{a.get('slug','')} {a.get('name','')} {a.get('ringkas','')} "
               f"{a.get('vibe','')} {' '.join(a.get('tag') or [])}").lower()
        if ql and ql not in hay:
            continue
        k = a.get("kualiti") or {}
        items.append({
            "slug": a["slug"], "nama": a.get("name"), "division": a.get("division"),
            "emoji": a.get("emoji"), "color": a.get("color"),
            "archetype": a.get("archetype"), "archetype_label": a.get("archetype_label"),
            "archetype_kedua": a.get("archetype_kedua"),
            "archetype_kedua_label": a.get("archetype_kedua_label"),
            "vibe": a.get("vibe"), "ringkas": a.get("ringkas"),
            "hasil": a.get("hasil") or [], "pilih_bila": a.get("pilih_bila"),
            "tag": a.get("tag") or [], "tier": k.get("tier"), "skor": k.get("skor"),
            "gred": k.get("gred"),
            "pangkat": k.get("pangkat"), "badan_kata": a.get("badan_kata"),
            "bukti": a.get("archetype_bukti") or [],
        })
    items.sort(key=lambda x: (-(x.get("skor") or 0), x.get("nama") or ""))
    return {
        "generated_at": d.get("generated_at"), "totals": d.get("totals") or {},
        "archetypes": d.get("archetypes") or [], "divisions": d.get("divisions") or [],
        "filtered": len(items), "agents": items[:limit],
    }


_HEALTH = {"at": 0.0, "data": None}


@app.get("/api/agency/health")
def api_agency_health():
    """Kesihatan sistem Ketua: roster, run, dan penggunaan tool setiap ejen.

    Cache 15s supaya panel mudah alih boleh menyegar tanpa membebankan telefon.
    """
    import agency_runner as ar

    if _HEALTH["data"] is not None and time.time() - _HEALTH["at"] < 15:
        return _HEALTH["data"]
    d = ar.load_ketua()
    t = d.get("totals") or {}
    runs, status = [], {}
    for meta in ar.latest(80):
        r = ar.load(meta.get("id")) or {}
        runs.append(r)
        s = r.get("status") or "unknown"
        status[s] = status.get(s, 0) + 1
    done = sum(1 for r in runs if r.get("status") == "done")
    gagal = sum(1 for r in runs if r.get("status") == "failed")
    aktif = sum(1 for r in runs if r.get("status") in ("planning", "planned", "running", "synthesizing"))
    usage = _agency_usage()
    per = {}
    for e in usage["events"]:
        ref = e.get("ref")
        if not ref:
            continue
        p = per.setdefault(ref, {"slug": ref, "panggilan": 0, "terakhir": None})
        p["panggilan"] += 1
        if not p["terakhir"] or e["ts"] > p["terakhir"]:
            p["terakhir"] = e["ts"]
    terpakai = sorted(per.values(), key=lambda x: -x["panggilan"])[:8]
    data = {
        "roster": {"ejen": t.get("ejen"), "divisi": t.get("divisi"),
                   "archetype": len(t.get("archetype") or {}),
                   "tier": t.get("tier"), "kata_badan": t.get("kata_badan"),
                   "dijana": d.get("generated_at")},
        "runs": {"jumlah": len(runs), "selesai": done, "gagal": gagal,
                 "aktif": aktif, "status": status,
                 "terakhir": (runs[0].get("created") if runs else None)},
        "penggunaan": {"jumlah": len(usage["events"]), "terpakai": terpakai},
        "masa": datetime.now().isoformat(timespec="seconds"),
    }
    _HEALTH.update({"at": time.time(), "data": data})
    return data


def _sections_of(body: str) -> list[dict]:
    """Senarai tajuk + bilangan perkataan, untuk paparan 'data persona'."""
    out, cur, buf = [], None, []

    def flush():
        if cur:
            out.append({"tajuk": cur, "kata": len(" ".join(buf).split())})

    for ln in body.splitlines():
        m = re.match(r"^#{1,3}\s+(.*)$", ln)
        if m:
            flush()
            cur, buf = m.group(1).strip(), []
        else:
            buf.append(ln)
    flush()
    return [s for s in out if s["kata"] > 0][:14]


_TIDX = {"at": 0.0, "data": {}}
_DASHC: dict[str, tuple[float, dict]] = {}


def _task_index() -> dict[str, list[dict]]:
    """Indeks slug → senarai tugasan (cache 15s).

    Tanpa ini, setiap panggilan dashboard membaca ~80 fail run.json (2s+).
    """
    import agency_runner as ar

    if time.time() - _TIDX["at"] < 15:
        return _TIDX["data"]
    idx: dict[str, list[dict]] = {}
    for meta in ar.latest(80):
        run = ar.load(meta.get("id")) or {}
        plan = run.get("plan") or {}
        for picked in (plan.get("ejen") or []):
            s = picked.get("slug")
            if not s:
                continue
            out = next((o for o in (run.get("outputs") or []) if o.get("slug") == s), None)
            st = (out or {}).get("status") or (
                "queued" if run.get("status") in ("planning", "planned", "running", "synthesizing")
                else "unknown")
            usage = ((out or {}).get("usage")
                     or ((run.get("usage") or {}).get("agents") or {}).get(s) or {})
            idx.setdefault(s, []).append({
                "id": run.get("id"), "created": run.get("created"), "status": st,
                "run_status": run.get("status"), "ms": int((out or {}).get("ms") or 0),
                "arahan": (run.get("instruction") or "")[:160],
                "skop": (picked.get("skop") or "")[:200],
                "hasil_dijangka": picked.get("hasil_dijangka") or "",
                "tokens": int(usage.get("total") or 0),
                "kos": round(float(usage.get("cost") or 0), 6),
                "verdict": ((run.get("final") or "").strip().splitlines() or [""])[-1][:120],
            })
    _TIDX.update(at=time.time(), data=idx)
    return idx


@app.get("/api/agent/{slug}/dashboard")
def api_agent_dashboard(slug: str):
    """Papan ejen: identiti, tugasan, data persona, prestasi — satu payload.

    Sumber: data/ketua_roster.json (archetype/tier), katalog (badan penuh),
    runs/*/run.json (tugasan sebenar), state.db (penggunaan tool).
    """
    import agency_runner as ar

    a = next((x for x in _ketua_agents() if x.get("slug") == slug), None)
    if not a:
        raise HTTPException(404, f"ejen tidak dijumpai: {slug}")
    full = next((x for x in ar.load_roster() if x.get("slug") == slug), {})
    body = full.get("body") or ""
    k = a.get("kualiti") or {}

    cache = _DASHC.get(slug)
    if cache and time.time() - cache[0] < 20:
        return cache[1]

    tasks = _task_index().get(slug, [])
    total_ms = sum(t["ms"] for t in tasks)
    done = sum(1 for t in tasks if t["status"] == "done")
    failed = sum(1 for t in tasks if t["status"] == "error")

    usage = _agency_usage()
    mine = [e for e in usage["events"] if e.get("ref") == slug]
    div = a.get("division")
    payload = {
        "slug": slug, "nama": a.get("name"), "emoji": a.get("emoji"),
        "color": a.get("color"), "division": div,
        "division_label": (_load_agency()["divisions"].get(div) or {}).get("label", div),
        "archetype": a.get("archetype"), "archetype_label": a.get("archetype_label"),
        "archetype_bukti": a.get("archetype_bukti") or [],
        "archetype_kedua": a.get("archetype_kedua"),
        "archetype_kedua_label": a.get("archetype_kedua_label"),
        "vibe": a.get("vibe"), "ringkas": a.get("ringkas"),
        "hasil": a.get("hasil") or [], "pilih_bila": a.get("pilih_bila"),
        "tag": a.get("tag") or [],
        "kualiti": {"tier": k.get("tier"), "skor": k.get("skor"), "gred": k.get("gred"),
                    "pangkat": k.get("pangkat"), "kata": k.get("kata"),
                    "seksyen": k.get("seksyen"), "bullet": k.get("bullet"),
                    "originaliti": k.get("originaliti"), "spesifik": k.get("spesifik")},
        "persona": {
            "kata": len(body.split()), "aksara": len(body),
            "seksyen": _sections_of(body), "sumber": a.get("source_path"),
            "ada_badan": bool(body), "tool": f'agency_agents_load slug="{slug}"',
        },
        "tugasan": tasks,
        "prestasi": {
            "jumlah": len(tasks), "selesai": done, "gagal": failed,
            "aktif": sum(1 for t in tasks if t["status"] in ("running", "queued")),
            "purata_ms": round(total_ms / max(1, done)) if done else 0,
            "token": sum(t["tokens"] for t in tasks),
            "kos": round(sum(t["kos"] for t in tasks), 6),
            "kadar_selesai": round(100 * done / len(tasks)) if tasks else 0,
        },
        "penggunaan": {"panggilan": len(mine),
                       "sesi": sorted({e["session"] for e in mine})[:5],
                       "terakhir": mine[-1]["ts"] if mine else None},
    }
    _DASHC[slug] = (time.time(), payload)
    return payload

# --------------------------------------------------------------------------- #
# PUSAT PEMANTAU — carta organisasi hidup + data live
# --------------------------------------------------------------------------- #
DIV_SYSTEM = {
    "agent_factory": ["research", "academic", "product", "specialized"],
    "role_generator": ["design", "spatial-computing", "game-development"],
    "workflow_generator": ["project-management", "gis"],
    "orchestrator": ["engineering", "marketing", "sales", "paid-media", "finance"],
    "qa_system": ["testing"],
    "recovery_system": ["support"],
    "completion_system": ["security", "healthcare"],
    "memory_manager": [],
}


SYS_FALLBACK = {
    "agent_factory": ("Reka & lahir ejen baharu", "bila roster perlu ditambah"),
    "role_generator": ("Jana persona/peranan", "bila peranan baharu diperlukan"),
    "workflow_generator": ("Jana aliran kerja", "bila tugasan perlu urutan"),
    "orchestrator": ("Agih & selaras tugasan", "setiap RUN dijalankan"),
    "qa_system": ("Uji & nilai output", "sebelum lulus"),
    "recovery_system": ("Pulih daripada kegagalan", "bila ejen gagal"),
    "completion_system": ("Sahkan siap & tandatangan", "akhir RUN"),
    "memory_manager": ("Simpan memori & SOP", "selepas setiap lulus"),
}


def _systems_from_soul() -> list[dict]:
    soul = read_text(home_path("hermes20") / "SOUL.md", 30000)
    out = []
    for row in md_table(get_section(soul, "ENJIN"))[1:]:
        if len(row) >= 3:
            name = row[0].strip("`").replace("system/", "").replace(".md", "")
            out.append({"key": name, "role": _plain(row[1]), "when": _plain(row[2])})
    if not out:
        # SOUL.md versi baharu tiada jadual ENJIN → guna senarai lalai 8 sistem
        out = [{"key": k, "role": v[0], "when": v[1]} for k, v in SYS_FALLBACK.items()]
    return out


def _aged_h(ts) -> float:
    """Umur cap masa dalam jam (terima epoch atau ISO)."""
    try:
        if ts is None:
            return 0.0
        if isinstance(ts, (int, float)):
            return (time.time() - float(ts)) / 3600.0
        s = str(ts).strip().replace("Z", "+00:00")
        from datetime import datetime as _dt
        return (time.time() - _dt.fromisoformat(s).timestamp()) / 3600.0
    except Exception:
        return 0.0


def _active_runs() -> list[dict]:
    """Run belum selesai + keadaan, lokasi, masa, dan kos setiap ejen."""
    import agency_runner as ar

    now = time.time()
    out = []
    for meta in ar.latest(40):
        if meta.get("status") not in ("running", "synthesizing", "planned"):
            continue
        # run 'planned' yang tersangkut > 6 jam dianggap luput (bukan aktif)
        if meta.get("status") == "planned" and _aged_h(meta.get("created")) > 6:
            continue
        run = ar.load(meta["id"]) or {}
        agents = (run.get("plan") or {}).get("ejen") or []
        outs = {o["slug"]: o for o in (run.get("outputs") or [])}
        done = set(outs)
        wave = run.get("waves") or []
        cur = set(wave[min((run.get("wave") or 1) - 1, max(0, len(wave) - 1))]) if wave else set()
        since = run.get("running_since") or {}
        usage_map = (run.get("usage") or {}).get("agents") or {}
        rows, cost_by_agent = [], {}
        for a in agents:
            slug = a["slug"]
            st = "done" if slug in done else ("running" if slug in cur else "queued")
            loc = _locate(slug)
            u = (outs.get(slug) or {}).get("usage") or usage_map.get(slug) or {}
            if slug in done:
                elapsed = round((outs[slug].get("ms") or 0) / 1000, 1)
            elif slug in since:
                elapsed = round(now - float(since[slug]), 1)
            else:
                elapsed = None
            cost = round(float(u.get("cost") or 0), 6)
            if cost:
                cost_by_agent[slug] = cost
            rows.append({**loc, "state": st, "depends_on": a.get("depends_on") or [],
                         "elapsed_s": elapsed, "tokens": int(u.get("total") or 0),
                         "cost": cost if u else None})
        plan_u = (run.get("plan") or {}).get("usage") or {}
        cost_so_far = float(plan_u.get("cost") or 0) + sum(float(x.get("cost") or 0)
                                                           for x in ((o.get("usage") or {}) for o in outs.values()))
        tokens_so_far = int(plan_u.get("total") or 0) + sum(int((o.get("usage") or {}).get("total") or 0)
                                                            for o in outs.values())
        out.append({
            "id": meta["id"], "status": run.get("status"), "created": run.get("created"),
            "instruction": (run.get("instruction") or "")[:200],
            "wave": run.get("wave") or 1, "wave_total": run.get("wave_total") or len(wave) or 1,
            "agents": rows, "finished": len(done), "total": len(agents),
            "cost_so_far": round(cost_so_far, 6), "tokens_so_far": tokens_so_far,
            "cost_by_agent": cost_by_agent,
        })
    return out


def _feed(limit: int = 24) -> list[dict]:
    con = ro_conn(home_path("hermes20"), "state.db")
    try:
        rows_ = rows(con, """
            SELECT m.timestamp, m.session_id, m.role, m.tool_name, m.content, s.title
            FROM messages m LEFT JOIN sessions s ON s.id = m.session_id
            WHERE m.content IS NOT NULL AND length(m.content) > 0
            ORDER BY m.id DESC LIMIT ?""", (limit,))
    finally:
        con.close()
    out = []
    for r in rows_:
        txt = re.sub(r"\s+", " ", (r["content"] or ""))[:180]
        if r["role"] == "tool":
            txt = f"{r['tool_name'] or 'tool'}: {txt}"
        out.append({"ts": iso(r["timestamp"]), "session": (r["title"] or r["session_id"])[:60],
                    "role": r["role"], "tool": r["tool_name"], "text": txt})
    return out


def _today_stats() -> dict:
    con = ro_conn(home_path("hermes20"), "state.db")
    try:
        start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        t = one(con, """SELECT COUNT(*) sessions, COALESCE(SUM(tool_call_count),0) tools,
                        COALESCE(SUM(input_tokens+output_tokens),0) tokens,
                        COALESCE(SUM(estimated_cost_usd),0) cost
                        FROM sessions WHERE started_at >= ?""", (start,))
        active = one(con, "SELECT COUNT(*) n FROM sessions WHERE last_activity_at >= ?", (time.time() - 300,))
        buckets = rows(con, """
            SELECT CAST((CAST(? AS INTEGER) - CAST(timestamp AS INTEGER)) / 300 AS INTEGER) b, COUNT(*) c
            FROM messages WHERE role = 'tool' AND timestamp >= ?
            GROUP BY b""", (time.time(), time.time() - 3600))
        series = [0] * 12
        for b in buckets:
            i = 11 - int(b["b"])
            if 0 <= i < 12:
                series[i] = b["c"]
    finally:
        con.close()
    return {"sessions_today": t["sessions"], "tools_today": t["tools"], "tokens_today": t["tokens"],
            "cost_today": round(t["cost"] or 0, 3), "active_sessions": active["n"], "series_60m": series}


def live_state() -> dict:
    runs_ = _active_runs()
    active = sorted({a["slug"] for r in runs_ for a in r["agents"] if a["state"] == "running"})
    return {
        "now": datetime.now().isoformat(timespec="seconds"),
        "gateway": gateway_state("hermes20"),
        "runs": runs_,
        "active_agents": active,
        "stats": _today_stats(),
        "feed": _feed(20),
        "guard": __import__("agency_runner").guard_status(),
    }


@app.get("/api/live/state")
def api_live_state():
    return live_state()


@app.get("/api/live/stream")
async def api_live_stream():
    import asyncio

    from fastapi.responses import StreamingResponse

    async def gen():
        for _ in range(300):  # ~10 minit; EventSource akan sambung semula
            try:
                payload = json.dumps(live_state(), ensure_ascii=False)
            except Exception as e:
                payload = json.dumps({"error": str(e)})
            yield f"data: {payload}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no",
                                      "Connection": "keep-alive"})


@app.get("/api/orgchart")
def api_orgchart():
    data = _load_agency()
    roster = data["agents"]
    usage = _agency_usage()
    used = {}
    for e in usage["events"]:
        if e.get("ref"):
            used[e["ref"]] = used.get(e["ref"], 0) + 1
    by_div: dict[str, list] = {}
    for a in roster:
        by_div.setdefault(a.get("division"), []).append(a)

    live = live_state()
    active = set(live["active_agents"])

    systems = []
    for s in _systems_from_soul():
        divs = []
        for d in DIV_SYSTEM.get(s["key"], []):
            agents = sorted(by_div.get(d, []), key=lambda x: (-used.get(x["slug"], 0), x.get("name") or ""))
            divs.append({
                "key": d,
                "label": (data["divisions"].get(d) or {}).get("label", d),
                "color": (data["divisions"].get(d) or {}).get("color", "#5ee3a1"),
                "count": len(agents),
                "used": sum(1 for a in agents if used.get(a["slug"])),
                "active": [a["slug"] for a in agents if a["slug"] in active],
                "top": [{"slug": a["slug"], "name": a.get("name"), "emoji": a.get("emoji")} for a in agents[:4]],
            })
        systems.append({**s, "divisions": divs,
                        "count": sum(d["count"] for d in divs),
                        "active": sum(len(d["active"]) for d in divs)})

    unmapped = [d for d in by_div if d not in {x["key"] for s in systems for x in s["divisions"]}]
    return {
        "ketua": {"title": "KETUA", "sub": "Agent Factory Organization", "model": default_model("hermes20")},
        "systems": systems,
        "totals": {"agents": len(roster), "divisions": len(by_div), "systems": len(systems),
                   "active": len(active), "used": len(used)},
        "unmapped": unmapped,
        "gateway": live["gateway"],
        "runs": len(live["runs"]),
        "active_agents": sorted(active),
    }





# --------------------------------------------------------------------------- #
# PANDUAN — langkah bergambar + status peranti (F-Droid / Termux:API / adb)
# --------------------------------------------------------------------------- #
STEP_DIR = BASE / "data" / "steps"
STEP_META = STEP_DIR / "steps.json"
SEED_STEPS = [
    ("step1-files.png", "Buka app Files, kemudian folder Download"),
    ("step2-apk.png", "Cari fail F-Droid.apk (12.6 MB) dalam Download"),
    ("step3-install.png", "Tekan Install pada dialog Android"),
    ("step4-allow.png", "Jika disekat: benarkan 'Pasang apl tidak diketahui' untuk Files"),
]
_APK_PATH = Path.home() / "storage" / "downloads" / "F-Droid.apk"


def _steps_load() -> list[dict]:
    try:
        return json.loads(STEP_META.read_text())
    except Exception:
        return []


def _steps_save(items: list[dict]) -> None:
    STEP_DIR.mkdir(parents=True, exist_ok=True)
    STEP_META.write_text(json.dumps(items, ensure_ascii=False, indent=1))


def _steps_seed() -> int:
    """Salin imej panduan terbina ke storan langkah (sekali sahaja)."""
    STEP_DIR.mkdir(parents=True, exist_ok=True)
    items = _steps_load()
    have = {i.get("seed") for i in items}
    added = 0
    for idx, (fn, cap) in enumerate(SEED_STEPS, 1):
        if fn in have:
            continue
        src = BASE / "static" / "img" / "steps" / fn
        if not src.exists():
            continue
        sid = f"seed{idx}"
        dst = STEP_DIR / f"{sid}.png"
        dst.write_bytes(src.read_bytes())
        items.append({"id": sid, "seed": fn, "caption": cap, "order": idx,
                      "file": dst.name, "bytes": dst.stat().st_size,
                      "created": datetime.now().isoformat(timespec="seconds"),
                      "source": "panduan"})
        added += 1
    if added:
        _steps_save(items)
    return added


def _sha256(p: Path, limit: int | None = None) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def device_status() -> dict:
    """Status pemasangan + APK. Panggilan ringan; tiada perubahan sistem."""
    pm = subprocess.run(["pm", "list", "packages"], capture_output=True, text=True, timeout=30)
    pkgs = pm.stdout or ""
    fdroid = "package:org.fdroid.fdroid" in pkgs
    apk = {"path": str(_APK_PATH).replace(str(Path.home()), "~"), "exists": _APK_PATH.exists()}
    if _APK_PATH.exists():
        st = _APK_PATH.stat()
        apk.update({"bytes": st.st_size,
                    "mtime": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
                    "sha256": _sha256(_APK_PATH)})
    api_cli = shutil.which("termux-battery-status") is not None
    api_live = False
    if api_cli:
        try:
            r = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=20)
            api_live = bool((r.stdout or "").strip().startswith("{"))
        except Exception:
            api_live = False
    adb = shutil.which("adb") is not None
    adb_devs = []
    if adb:
        try:
            r = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=20)
            adb_devs = [l.split("\t")[0] for l in (r.stdout or "").splitlines()[1:] if "\tdevice" in l]
        except Exception:
            pass
    return {"checked_at": datetime.now().isoformat(timespec="seconds"),
            "fdroid": {"installed": fdroid, "package": "org.fdroid.fdroid"},
            "apk": apk,
            "termux_api": {"cli": api_cli, "working": api_live},
            "adb": {"binary": adb, "devices": adb_devs},
            "caveat": "pm list ditapis oleh Android package-visibility; kalau app baharu "
                      "tak muncul, sahkan melalui app drawer atau ADB sebagai shell."}


@app.get("/api/device/status")
def api_device_status():
    return device_status()



# --------------------------------------------------------------------------- #
# ADB wayarles dari UI + tangkapan skrin automatik
# --------------------------------------------------------------------------- #
def _adb_devices() -> list[str]:
    try:
        r = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=20)
        return [l.split("\t")[0] for l in (r.stdout or "").splitlines()[1:] if "\tdevice" in l]
    except Exception:
        return []


@app.post("/api/device/adb-pair")
def api_adb_pair(payload: dict = Body(...)):
    """Pasangkan ADB wayarles dari borang web (ganti taip terminal)."""
    host = (payload.get("host") or "").strip()
    code = str(payload.get("code") or "").strip()
    conn = (payload.get("connect") or "").strip()
    if not re.fullmatch(r"[0-9a-zA-Z][0-9a-zA-Z.\-]*:\d{2,5}", host):
        raise HTTPException(400, "IP:port tidak sah (contoh 192.168.1.7:37123)")
    if not re.fullmatch(r"\d{6}", code):
        raise HTTPException(400, "kod mesti 6 digit")
    out = []
    try:
        p = subprocess.run(["adb", "pair", host], input=code + "\n", capture_output=True,
                           text=True, timeout=90)
        out.append({"step": f"adb pair {host}", "out": ((p.stdout or "") + (p.stderr or "")).strip()[:800]})
    except Exception as e:
        raise HTTPException(500, f"adb pair gagal: {e}")
    if not conn:
        ip = host.split(":")[0]
        conn = f"{ip}:5555"
        try:
            m = subprocess.run(["adb", "mdns", "services"], capture_output=True, text=True, timeout=15)
            for line in (m.stdout or "").splitlines():
                if "_adb-tls-connect" in line:
                    parts = line.split()
                    if parts:
                        conn = parts[-1]
                        break
        except Exception:
            pass
    try:
        c = subprocess.run(["adb", "connect", conn], capture_output=True, text=True, timeout=45)
        out.append({"step": f"adb connect {conn}", "out": ((c.stdout or "") + (c.stderr or "")).strip()[:400]})
    except Exception as e:
        out.append({"step": f"adb connect {conn}", "out": str(e)[:200]})
    devs = _adb_devices()
    return {"ok": bool(devs), "devices": devs, "connect": conn, "log": out}


@app.post("/api/device/shot")
def api_device_shot(payload: dict = Body(default={})):
    """Tangkap skrin peranti melalui adb dan simpan sebagai langkah panduan."""
    devs = _adb_devices()
    if not devs:
        raise HTTPException(400, "tiada peranti adb — pasangkan dahulu (borang ADB)")
    try:
        p = subprocess.run(["adb", "exec-out", "screencap", "-p"], capture_output=True, timeout=60)
    except Exception as e:
        raise HTTPException(500, f"screencap gagal: {e}")
    raw = p.stdout or b""
    if len(raw) < 2000 or raw[:4] != b"\x89PNG":
        raise HTTPException(500, "screencap tidak pulang PNG yang sah")
    STEP_DIR.mkdir(parents=True, exist_ok=True)
    sid = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + secrets.token_hex(3)
    f = STEP_DIR / f"{sid}.png"
    f.write_bytes(raw)
    items = _steps_load()
    order = max([i.get("order") or 0 for i in items] or [0]) + 1
    cap = (payload.get("caption") or "Tangkapan skrin peranti").strip()[:300]
    items.append({"id": sid, "caption": cap, "order": order, "file": f.name,
                  "bytes": len(raw), "created": datetime.now().isoformat(timespec="seconds"),
                  "source": "adb"})
    _steps_save(items)
    return {"ok": True, "id": sid, "bytes": len(raw), "device": devs[0], "url": f"/api/steps/{sid}/file"}

@app.get("/api/steps")
def api_steps():
    items = sorted(_steps_load(), key=lambda x: (x.get("order") or 0, x.get("created") or ""))
    for i in items:
        i["url"] = f"/api/steps/{i['id']}/file"
    return {"steps": items, "count": len(items)}


@app.post("/api/steps")
def api_steps_add(payload: dict = Body(...)):
    b64 = payload.get("content_b64") or ""
    if not b64:
        raise HTTPException(400, "imej diperlukan (content_b64)")
    try:
        raw = base64.b64decode(b64.split(",")[-1])
    except Exception:
        raise HTTPException(400, "base64 tidak sah")
    if len(raw) > 20 * 1024 * 1024:
        raise HTTPException(400, "imej melebihi 20 MB — kecilkan dahulu")
    items = _steps_load()
    sid = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + secrets.token_hex(3)
    STEP_DIR.mkdir(parents=True, exist_ok=True)
    # Imej telefon selalunya besar / format tak disokong pelayar (HEIC, AVIF, BMP).
    # Tukar ke JPEG (maks 1600px) supaya SENTIASA boleh dipaparkan dalam galeri.
    ext = Path(payload.get("filename") or "step.png").suffix.lower() or ".png"
    if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif"} or len(raw) > 3 * 1024 * 1024:
        try:
            import io as _io

            from PIL import Image as _Image

            im = _Image.open(_io.BytesIO(raw))
            im = im.convert("RGB")
            im.thumbnail((1600, 1600))
            buf = _io.BytesIO()
            im.save(buf, "JPEG", quality=86, optimize=True)
            raw, ext = buf.getvalue(), ".jpg"
        except Exception:
            if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
                raise HTTPException(400, f"format {ext} tidak disokong — tukar ke JPG/PNG dahulu")
    f = STEP_DIR / f"{sid}{ext}"
    f.write_bytes(raw)
    order = max([i.get("order") or 0 for i in items] or [0]) + 1
    items.append({"id": sid, "caption": (payload.get("caption") or "").strip()[:300],
                  "order": order, "file": f.name, "bytes": len(raw),
                  "created": datetime.now().isoformat(timespec="seconds"),
                  "source": payload.get("source") or "pengguna"})
    _steps_save(items)
    return {"ok": True, "id": sid, "count": len(items)}


@app.get("/api/steps/{sid}/file")
def api_steps_file(sid: str):
    # id langkah: seed1, 20261111_130655_abc123, atau perihal-20261111_125919 (ada sengkang)
    if not re.fullmatch(r"[A-Za-z0-9_\-]{3,60}", sid or ""):
        raise HTTPException(400, "id tidak sah")
    for i in _steps_load():
        if i.get("id") == sid:
            f = STEP_DIR / i["file"]
            if f.exists():
                return FileResponse(f)
    raise HTTPException(404, "langkah tiada")

# --------------------------------------------------------------------------- #
# SANDARAN GITHUB — tab berasingan (BACA-SAHAJA)
# Data datang dari folder sendiri: ~/.hermes20/reports/sandaran/
# --------------------------------------------------------------------------- #
SANDARAN_DIR = Path.home() / ".hermes20" / "reports" / "sandaran"
SANDARAN_SKRIP = Path.home() / ".hermes20" / "scripts" / "export_sandaran.py"
SANDARAN_FILES = (
    "status.json",
    "sejarah.json",
    "larian.json",
    "cron.json",
    "insiden-2026-11-18.md",
)


def _sandaran_baca(nama: str):
    """Baca satu fail data. Pulang None jika tiada / rosak."""
    f = SANDARAN_DIR / nama
    try:
        if nama.endswith(".json"):
            return json.loads(f.read_text())
        return f.read_text()
    except Exception:  # noqa: BLE001
        return None


def _sandaran_eksport() -> dict:
    """Jalankan pengeksport SEKALI (timeout 60s). Pulang ringkasan ringkas."""
    try:
        p = subprocess.run(["python3", str(SANDARAN_SKRIP)], capture_output=True,
                           text=True, timeout=60, cwd=str(SANDARAN_SKRIP.parent))
        return {"kod": p.returncode,
                "output": ((p.stdout or "") + (p.stderr or "")).strip()[:400]}
    except Exception as e:  # noqa: BLE001
        return {"kod": None, "output": f"{type(e).__name__}: {e}"}


@app.get("/api/sandaran")
def api_sandaran():
    """JSON gabungan kelima-lima fail. Jika tiada, cuba eksport sekali."""
    data = {n: _sandaran_baca(n) for n in SANDARAN_FILES}
    eksport = None
    # Muat semula jika tiada ATAU data lebih tua daripada 5 minit,
    # supaya commit/keadaan sebenar dibaca, bukan nilai beku.
    basi = True
    try:
        umur = time.time() - (SANDARAN_DIR / "status.json").stat().st_mtime
        basi = umur > 300
    except Exception:  # noqa: BLE001
        basi = True
    if data["status.json"] is None or basi:
        eksport = _sandaran_eksport()
        data = {n: _sandaran_baca(n) for n in SANDARAN_FILES}

    if data["status.json"] is None:
        return {"ok": False,
                "sebab": "Fail data sandaran tiada dan pengeksport tidak menghasilkan apa-apa.",
                "folder": str(SANDARAN_DIR), "eksport": eksport}

    st = data["status.json"] or {}
    sj = data["sejarah.json"] or {}
    lr = data["larian.json"] or {}
    cr = data["cron.json"] or {}
    fail = []
    for n in SANDARAN_FILES:
        f = SANDARAN_DIR / n
        fail.append({"nama": n, "ada": f.exists(),
                     "saiz": f.stat().st_size if f.exists() else 0,
                     "url": f"/api/sandaran/fail/{n}"})
    return {
        "ok": True,
        "dijana_pada": st.get("dijana_pada"),
        "status": st,
        "sejarah": sj.get("commits", []),
        "larian": lr.get("larian", []),
        "cron": cr,
        "insiden_md": data["insiden-2026-11-18.md"] or "",
        "fail": fail,
        "eksport": eksport,
    }


@app.get("/api/sandaran/fail/{nama}")
def api_sandaran_fail(nama: str):
    """Muat turun fail data — SENARAI PUTIH KETAT, tiada path traversal."""
    if nama not in SANDARAN_FILES:
        raise HTTPException(400, "nama fail tidak dibenarkan")
    f = SANDARAN_DIR / nama
    if not f.is_file():
        raise HTTPException(404, "fail tiada")
    return FileResponse(f, filename=nama)


# --------------------------------------------------------------------------- #
# SERVIS RUNIT (hidup/mati/log) + TERMUX:BOOT (pasang APK) — tindakan dari UI
# --------------------------------------------------------------------------- #
PREFIX_DIR = Path(os.environ.get("PREFIX") or "/data/data/com.termux/files/usr")
SVDIR = PREFIX_DIR / "var" / "service"
SVC_ALLOW = {
    "hermes-console": ("Konsol 8787", Path.home() / ".hermes20" / "logs" / "hermes-console" / "current"),
    "hermes-gateway": ("Gateway Telegram", None),
    "hermes-dashboard": ("Dashboard web 9119", Path.home() / ".hermes20" / "logs" / "hermes-dashboard.log"),
    "hermes-dash-tunnel": ("Tunnel Cloudflare", Path.home() / ".hermes20" / "logs" / "hermes-dash-tunnel.log"),
    "web-server": ("AINA live 8081 (lama, sengaja mati)", Path.home() / ".web-server.log"),
}
SVC_ACTIONS = {"up", "down", "restart", "status"}


def _sv(*args, timeout: int = 25):
    exe = shutil.which("sv") or str(PREFIX_DIR / "bin" / "sv")
    return subprocess.run([exe, *args], capture_output=True, text=True, timeout=timeout)


def _svc_one(name: str) -> dict:
    label, logp = SVC_ALLOW[name]
    p = _sv("status", name)
    raw = ((p.stdout or "") + (p.stderr or "")).strip()
    state = "tiada"
    for k in ("run", "down", "fail", "finish"):
        if raw.startswith(k):
            state = k
            break
    pid = None
    m = re.search(r"\(pid (\d+)\)", raw)
    if m:
        pid = int(m.group(1))
    secs = None
    m2 = re.search(r"\)\s*(\d+)s", raw) or re.search(r":\s*(\d+)s", raw)
    if m2:
        secs = int(m2.group(1))
    logsize = None
    if logp and logp.exists():
        try:
            logsize = logp.stat().st_size
        except Exception:
            logsize = None
    return {"name": name, "label": label, "state": state, "pid": pid, "seconds": secs,
            "raw": raw, "log": str(logp) if logp else None, "log_bytes": logsize,
            "has_down_file": (SVDIR / name / "down").exists()}


@app.get("/api/svc")
def api_svc_list():
    out = []
    for n in SVC_ALLOW:
        try:
            out.append(_svc_one(n))
        except Exception as e:
            out.append({"name": n, "label": SVC_ALLOW[n][0], "state": "ralat", "raw": str(e)[:200]})
    return {"services": out, "svdir": str(SVDIR)}


def _sv_later(action: str, name: str) -> None:
    """Jalankan sv selepas respons dihantar — supaya UI tak terputus."""
    time.sleep(0.8)
    try:
        _sv(action, name)
    except Exception:
        pass


@app.post("/api/svc/{name}")
def api_svc_action(name: str, payload: dict = Body(default={}), bg: BackgroundTasks = None):
    if name not in SVC_ALLOW:
        raise HTTPException(400, "servis tidak dibenarkan (hanya: " + ", ".join(SVC_ALLOW) + ")")
    action = str(payload.get("action") or "").strip().lower()
    if action not in SVC_ACTIONS:
        raise HTTPException(400, "tindakan mesti up | down | restart | status")
    if name == "hermes-console" and action in ("restart", "down") and bg is not None:
        bg.add_task(_sv_later, action, name)
        return {"ok": True, "action": action, "name": name, "deferred": True,
                "out": f"sv {action} hermes-console akan dijalankan ~1s lagi",
                "status": _svc_one(name)}

    # [KETUA 2026-11-18] "restart" hermes-gateway = HANDOVER sebenar.
    # Skrip run khidmat gateway kini MENUNGGU selagi ada gateway lain berjalan
    # (supaya tiada gelung panas + spam notifikasi wake-lock). Kesannya
    # `sv restart` hanya menggantikan proses penunggu, gateway lama terus hidup
    # dan kod baharu TIDAK dimuatkan. Jadi restart sebenar = hentikan proses
    # gateway; penunggu runit akan mengambil alih dalam ~5 saat.
    if name == "hermes-gateway" and action == "restart":
        try:
            subprocess.run(["pkill", "-f", "hermes gateway run"],
                           capture_output=True, text=True, timeout=15)
        except Exception:
            pass
        return {"ok": True, "action": action, "name": name, "deferred": True,
                "out": "gateway dihentikan — runit menghidupkan semula dalam ~5s",
                "status": _svc_one(name)}
    p = _sv(action, name)
    time.sleep(1.2)
    return {"ok": p.returncode == 0, "action": action, "name": name,
            "out": ((p.stdout or "") + (p.stderr or "")).strip()[:600],
            "status": _svc_one(name)}


@app.get("/api/svc/{name}/log")
def api_svc_log(name: str, lines: int = Query(60, ge=1, le=400)):
    if name not in SVC_ALLOW:
        raise HTTPException(400, "servis tidak dibenarkan")
    logp = SVC_ALLOW[name][1]
    if not logp or not logp.exists():
        raise HTTPException(404, "fail log tiada untuk servis ini")
    try:
        data = logp.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as e:
        raise HTTPException(500, f"gagal baca log: {e}")
    return {"name": name, "file": str(logp), "bytes": logp.stat().st_size,
            "lines": data[-lines:]}


# --- Web UI dashboard (9119) ------------------------------------------------
DASH_URL_FILE = Path.home() / ".hermes20" / "dashboard_url.txt"
DASH_SECRET_FILE = Path.home() / ".hermes20" / "secrets" / "dashboard_login.txt"
DASH_VERIFY_SCRIPT = Path.home() / ".hermes20" / "scripts" / "dash_verify.sh"
DASH_SERVICES = ("hermes-dashboard", "hermes-dash-tunnel")


def _dash_url() -> str:
    try:
        lines = [x.strip() for x in DASH_URL_FILE.read_text(encoding="utf-8", errors="replace").splitlines()]
        return next((x for x in reversed(lines) if x.startswith("http")), "")
    except Exception:
        return ""


def _lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.6)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return ""


def _port_open(port: int = 9119) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.8)
    try:
        return s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()


@app.get("/api/web")
def api_web():
    user = ""
    try:
        for line in DASH_SECRET_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.lower().startswith("username:"):
                user = line.split(":", 1)[1].strip()
    except Exception:
        pass
    svcs = []
    for n in DASH_SERVICES:
        try:
            svcs.append(_svc_one(n))
        except Exception as e:
            svcs.append({"name": n, "state": "ralat", "raw": str(e)[:120]})
    upd = ""
    try:
        upd = time.strftime("%Y-%m-%d %H:%M", time.localtime(DASH_URL_FILE.stat().st_mtime))
    except Exception:
        pass
    return {
        "url": _dash_url(),
        "url_updated": upd,
        "lan": _lan_ip(),
        "port_open": _port_open(),
        "user": user,
        "secret_file": str(DASH_SECRET_FILE),
        "verify_script": str(DASH_VERIFY_SCRIPT),
        "services": svcs,
    }


@app.post("/api/web/verify")
def api_web_verify():
    if not DASH_VERIFY_SCRIPT.exists():
        raise HTTPException(404, "skrip ujian tiada: " + str(DASH_VERIFY_SCRIPT))
    try:
        p = subprocess.run(
            [shutil.which("bash") or "/system/bin/sh", str(DASH_VERIFY_SCRIPT)],
            capture_output=True, text=True, timeout=120,
        )
    except Exception as e:
        raise HTTPException(500, f"gagal jalankan ujian: {e}")
    out = ((p.stdout or "") + (p.stderr or "")).strip()
    ok = p.returncode == 0 and "login POST : 200" in out
    return {"ok": ok, "exit": p.returncode, "out": out[:4000]}


# --- FLEET: dua gerbang + skill + ATC ---------------------------------------
def _alive(pattern: str) -> bool:
    try:
        p = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True, timeout=8)
        return p.returncode == 0 and bool(p.stdout.strip())
    except Exception:
        return False


def _log_tail(path: Path, n: int = 1) -> tuple[str, float]:
    try:
        st = path.stat()
        lines = path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
        return ("\n".join(lines[-n:]) if lines else ""), st.st_mtime
    except Exception:
        return "", 0.0


@app.get("/api/fleet")
def api_fleet():
    h20 = home_path("hermes20")
    h19 = Path.home() / ".hermes19"

    def skills(p: Path) -> int:
        try:
            return sum(1 for f in p.rglob("SKILL.md"))
        except Exception:
            return 0

    def gateway(name: str, home: Path, pattern: str) -> dict:
        alive = _alive(pattern)
        tail, mt = _log_tail(home / "logs" / "gateway.log", 1)
        return {"name": name, "home": str(home), "alive": alive,
                "log_age_min": round((time.time() - mt) / 60, 1) if mt else None,
                "last": tail[-220:]}

    atc_state = ""
    for cand in (h19 / "atc_state.json", h19 / "data" / "atc_state.json"):
        if cand.exists():
            atc_state = read_text(cand, 400)
            break

    mem = {}
    try:
        for line in Path("/proc/meminfo").read_text().splitlines()[:3]:
            k, v = line.split(":", 1)
            mem[k] = int(v.strip().split()[0]) // 1024
    except Exception:
        pass

    disk = {}
    try:
        st = os.statvfs(str(h20))
        disk = {"total_gb": round(st.f_blocks * st.f_frsize / 1e9, 1),
                "free_gb": round(st.f_bavail * st.f_frsize / 1e9, 1)}
    except Exception:
        pass

    return {
        "gateways": [
            gateway("hermes20 · Ketua", h20, "hermes-source.*gateway|hermes gateway"),
            gateway("hermes19 · Trading", h19, "HERMES_HOME=.*hermes19|hermes19"),
        ],
        "skills": {"hermes20": skills(h20 / "skills"), "hermes19": skills(h19 / "skills")},
        "atc": {"running": _alive("atc|ATC"), "state": atc_state},
        "mem_mb": mem, "disk": disk, "now": time.strftime("%H:%M:%S"),
    }


@app.get("/api/skills")
def api_skills():
    base = home_path("hermes20") / "skills"
    out = []
    try:
        files = sorted(base.rglob("SKILL.md"))
    except Exception:
        files = []
    for f in files:
        if "node_modules" in str(f):
            continue
        txt = read_text(f, 6000)
        name = f.parent.name
        desc = ""
        for line in txt.splitlines():
            low = line.strip().lower()
            if low.startswith("description:"):
                desc = line.split(":", 1)[1].strip().strip('"').strip("'")
                break
        out.append({"name": name, "desc": desc[:160],
                    "category": f.parent.parent.name, "path": str(f)})
    return {"count": len(out), "skills": out}


@app.get("/api/cron")
def api_cron():
    p = home_path("hermes20") / "cron" / "jobs.json"
    jobs = []
    try:
        data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
        jobs = data if isinstance(data, list) else (data.get("jobs") or [])
    except Exception:
        jobs = []
    out = []
    for j in jobs:
        sc = j.get("schedule") or ""
        if isinstance(sc, dict):
            sc = sc.get("expr") or sc.get("cron") or sc.get("value") or sc.get("kind") or str(sc)
        out.append({
            "id": j.get("id") or j.get("job_id"),
            "name": j.get("name") or "",
            "schedule": str(sc),
            "enabled": bool(j.get("enabled", True)),
            "script": j.get("script") or "",
            "last": str(j.get("last_run_at") or ""),
            "status": j.get("last_status") or "",
        })
    out.sort(key=lambda x: (not x["enabled"], x["name"]))
    return {"count": len(out), "jobs": out}


@app.get("/api/email")
def api_email():
    inbox = Path.home() / "vault" / "email-inbox"
    log = inbox / "_autosort.log"
    lines = []
    try:
        lines = log.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    except Exception:
        pass
    counts = {}
    for d in ("1-PENTING", "2-KERJA", "3-PROMOSI", "0-LAIN"):
        try:
            counts[d] = sum(1 for _ in (inbox / d).glob("*.md"))
        except Exception:
            counts[d] = 0
    return {"log": lines[-12:], "counts": counts,
            "inbox": str(inbox), "updated": time.strftime("%H:%M:%S")}


_WATAK_CACHE = {"ts": 0.0, "data": []}


@app.get("/api/watak")
def api_watak():
    p = home_path("hermes20") / "plugins" / "agency-agents-router" / "data" / "agents.json"
    try:
        mt = p.stat().st_mtime
        if _WATAK_CACHE["ts"] != mt:
            raw = json.loads(p.read_text(encoding="utf-8", errors="replace"))
            out = []
            for a in raw:
                out.append({
                    "slug": a.get("slug") or a.get("id") or "",
                    "name": a.get("name") or a.get("title") or "",
                    "division": a.get("division") or a.get("category") or "",
                    "tier": a.get("tier") or "",
                    "emoji": a.get("emoji") or "",
                    "desc": (a.get("description") or a.get("desc") or a.get("when_to_use") or "")[:120],
                    "vibe": a.get("vibe") or "",
                    "ketua": bool(a.get("ketua")),
                })
            _WATAK_CACHE.update(ts=mt, data=out)
        data = _WATAK_CACHE["data"]
        live = live_state()
        active = set(live.get("active_agents") or [])
        for a in data:
            a["active"] = a["slug"] in active
        return {"count": len(data), "agents": data}
    except Exception as e:
        raise HTTPException(500, f"gagal baca katalog: {e}")


@app.post("/api/watak")
def api_watak_create(payload: dict = Body(...)):
    """Tambah persona baharu ke katalog ejen."""
    p = home_path("hermes20") / "plugins" / "agency-agents-router" / "data" / "agents.json"
    name = (payload.get("name") or "").strip()
    if len(name) < 2:
        raise HTTPException(400, "nama watak terlalu pendek")
    slug = (payload.get("slug") or "").strip().lower() or re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not slug:
        raise HTTPException(400, "slug tidak sah")
    try:
        raw = json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception as e:
        raise HTTPException(500, f"gagal baca katalog: {e}")
    if any((a.get("slug") or "") == slug for a in raw):
        raise HTTPException(409, f"slug '{slug}' sudah ada")
    rec = {
        "slug": slug,
        "name": name,
        "description": (payload.get("description") or "").strip(),
        "division": (payload.get("division") or "umum").strip(),
        "color": '"#22c55e"',
        "emoji": (payload.get("emoji") or "🧠").strip(),
        "vibe": (payload.get("vibe") or "").strip(),
        "tier": (payload.get("tier") or "C").strip().upper(),
        "ketua": bool(payload.get("ketua")),
        "source_path": (payload.get("source_path") or "").strip(),
        "body": (payload.get("body") or "").strip(),
    }
    raw.append(rec)
    try:
        shutil.copy2(p, p.with_suffix(".json.bak-watak"))
        p.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        raise HTTPException(500, f"gagal simpan katalog: {e}")
    _WATAK_CACHE["ts"] = 0.0
    return {"ok": True, "count": len(raw), "watak": rec}


@app.put("/api/watak/{slug}")
def api_watak_edit(slug: str, payload: dict = Body(...)):
    """Edit persona sedia ada (termasuk tandakan Ketua)."""
    p = home_path("hermes20") / "plugins" / "agency-agents-router" / "data" / "agents.json"
    try:
        raw = json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception as e:
        raise HTTPException(500, f"gagal baca katalog: {e}")
    hit = next((a for a in raw if (a.get("slug") or "") == slug), None)
    if not hit:
        raise HTTPException(404, f"watak '{slug}' tidak dijumpai")
    for k in ("name", "description", "division", "emoji", "vibe", "tier", "body", "source_path"):
        if payload.get(k) is not None:
            hit[k] = str(payload[k]).strip()
    if "ketua" in payload:
        hit["ketua"] = bool(payload["ketua"])
        if hit["ketua"]:
            for a in raw:
                if a is not hit:
                    a["ketua"] = False
    try:
        shutil.copy2(p, p.with_suffix(".json.bak-watak"))
        p.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        raise HTTPException(500, f"gagal simpan katalog: {e}")
    _WATAK_CACHE["ts"] = 0.0
    return {"ok": True, "count": len(raw), "watak": hit}


@app.delete("/api/watak/{slug}")
def api_watak_delete(slug: str):
    """Padam persona daripada katalog (sandaran automatik)."""
    p = home_path("hermes20") / "plugins" / "agency-agents-router" / "data" / "agents.json"
    try:
        raw = json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception as e:
        raise HTTPException(500, f"gagal baca katalog: {e}")
    keep = [a for a in raw if (a.get("slug") or "") != slug]
    if len(keep) == len(raw):
        raise HTTPException(404, f"watak '{slug}' tidak dijumpai")
    try:
        shutil.copy2(p, p.with_suffix(".json.bak-watak"))
        p.write_text(json.dumps(keep, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        raise HTTPException(500, f"gagal simpan katalog: {e}")
    _WATAK_CACHE["ts"] = 0.0
    return {"ok": True, "count": len(keep), "dipadam": slug}


# ---------------- MCP ----------------
def _hermes_cfg() -> Path:
    return home_path("hermes20") / "config.yaml"


def _read_mcp_servers() -> dict:
    try:
        import yaml
        d = yaml.safe_load(_hermes_cfg().read_text(encoding="utf-8", errors="replace")) or {}
    except Exception:
        return {}
    s = d.get("mcp_servers") or {}
    return s if isinstance(s, dict) else {}


def _run_hermes(args, timeout=120):
    env = dict(os.environ)
    env["HERMES_HOME"] = str(home_path("hermes20"))
    env["HERMES_ACCEPT_HOOKS"] = "1"
    exe = shutil.which("hermes") or "/data/data/com.termux/files/usr/bin/hermes"
    try:
        p = subprocess.run([exe] + args, capture_output=True, text=True,
                           timeout=timeout, env=env, stdin=subprocess.DEVNULL)
    except Exception as e:
        return 1, f"gagal jalankan hermes: {e}"
    return p.returncode, ((p.stdout or "") + (p.stderr or "")).strip()


@app.get("/api/mcp")
def api_mcp():
    srv = _read_mcp_servers()
    out = []
    for name, cfg in srv.items():
        cfg = cfg if isinstance(cfg, dict) else {}
        out.append({
            "name": name,
            "type": "http" if cfg.get("url") else "stdio",
            "url": cfg.get("url") or "",
            "command": cfg.get("command") or "",
            "args": cfg.get("args") or [],
            "enabled": cfg.get("enabled", True) is not False,
        })
    out.sort(key=lambda x: x["name"])
    return {"count": len(out), "servers": out, "config": str(_hermes_cfg())}


@app.post("/api/mcp")
def api_mcp_add(payload: dict = Body(...)):
    name = (payload.get("name") or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9._-]{2,40}", name):
        raise HTTPException(400, "nama MCP tidak sah (a-z, 0-9, . _ - ; 2-40 aksara)")
    url = (payload.get("url") or "").strip()
    cmd = (payload.get("command") or "").strip()
    args = payload.get("args") or []
    if isinstance(args, str):
        args = args.split()
    if not url and not cmd:
        raise HTTPException(400, "isi URL atau command")
    if name in _read_mcp_servers():
        raise HTTPException(409, f"MCP '{name}' sudah wujud")
    cfg = {"url": url} if url else {"command": cmd, "args": [str(a) for a in args]}
    cfg["enabled"] = True
    try:
        import yaml
        p = _hermes_cfg()
        d = yaml.safe_load(p.read_text(encoding="utf-8", errors="replace")) or {}
        srv = d.get("mcp_servers")
        if not isinstance(srv, dict):
            srv = {}
        srv[name] = cfg
        d["mcp_servers"] = srv
        shutil.copy2(p, p.with_suffix(".yaml.bak-mcp"))
        p.write_text(yaml.safe_dump(d, sort_keys=False, allow_unicode=True), encoding="utf-8")
    except Exception as e:
        raise HTTPException(500, f"gagal simpan config: {e}")
    return {"ok": True, "saved": name, "cfg": cfg,
            "nota": "HTTP/S SE mungkin perlu pakej mcp lebih baharu; stdio (command+args) paling stabil."}


@app.get("/api/mcp/catalog")
def api_mcp_catalog():
    code, out = _run_hermes(["mcp", "catalog"], timeout=60)
    items = []
    for line in (out or "").splitlines():
        m = re.match(r"^\s{2}([a-z0-9._-]+)\s{2,}(available|installed|configured|\S+)\s{2,}(.+)$", line)
        if m:
            items.append({"name": m.group(1), "status": m.group(2), "desc": m.group(3).strip()})
    return {"ok": code == 0, "count": len(items), "items": items}


@app.delete("/api/mcp/{name}")
def api_mcp_remove(name: str):
    if name not in _read_mcp_servers():
        raise HTTPException(404, f"MCP '{name}' tiada")
    code, out = _run_hermes(["config", "unset", f"mcp_servers.{name}"])
    return {"ok": code == 0, "exit": code, "out": out[-1200:]}


@app.post("/api/mcp/{name}/test")
def api_mcp_test(name: str):
    code, out = _run_hermes(["mcp", "test", name], timeout=90)
    return {"ok": code == 0, "exit": code, "out": out[-1200:]}


@app.post("/api/task")
def api_task(payload: dict = Body(...)):
    instr = (payload.get("instruction") or "").strip()
    if len(instr) < 12:
        raise HTTPException(400, "arahan terlalu pendek (minimum 12 aksara)")
    if len(instr) > 4000:
        raise HTTPException(400, "arahan terlalu panjang (maksimum 4000 aksara)")
    max_agents = max(1, min(6, int(payload.get("max_agents") or 3)))
    if _PLAN_LOCK["n"] >= 1:
        raise HTTPException(429, "Ketua sedang merancang arahan lain — tunggu sebentar")
    _PLAN_LOCK["n"] += 1
    try:
        import agency_runner as ar
        run = ar.plan_run(instr, max_agents, [])
        if run.get("status") == "failed":
            return JSONResponse(run, status_code=502)
        if payload.get("start", True):
            run = ar.start_run(run["id"])
    except Exception as e:
        raise HTTPException(500, f"gagal jana run: {e}")
    finally:
        _PLAN_LOCK["n"] -= 1
    run.pop("trace", None)
    return run


@app.post("/api/cron/{job_id}")
def api_cron_action(job_id: str, payload: dict = Body(...)):
    action = (payload.get("action") or "run").strip()
    if action not in ("run", "pause", "resume"):
        raise HTTPException(400, "action mesti run | pause | resume")
    env = dict(os.environ)
    env["HERMES_HOME"] = str(home_path("hermes20"))
    exe = shutil.which("hermes") or "/data/data/com.termux/files/usr/bin/hermes"
    try:
        p = subprocess.run([exe, "cron", action, job_id], capture_output=True,
                           text=True, timeout=90, env=env)
    except Exception as e:
        raise HTTPException(500, f"gagal jalankan hermes cron: {e}")
    out = ((p.stdout or "") + (p.stderr or "")).strip()
    return {"ok": p.returncode == 0, "exit": p.returncode, "out": out[-900:]}


@app.get("/api/skill")
def api_skill_text(path: str = Query(...)):
    base = (home_path("hermes20") / "skills").resolve()
    try:
        p = Path(path).resolve()
    except Exception:
        raise HTTPException(400, "path tidak sah")
    if not str(p).startswith(str(base)):
        raise HTTPException(403, "hanya fail dalam folder skills dibenarkan")
    if not p.is_file():
        raise HTTPException(404, "fail tidak dijumpai")
    return {"path": str(p), "name": p.parent.name, "text": read_text(p, 60000)}


@app.post("/api/run/{run_id}/{action}")
def api_run_action(run_id: str, action: str):
    import agency_runner as ar
    if not ar.valid_run_id(run_id):
        raise HTTPException(400, "id run tidak sah")
    run = ar.load(run_id)
    if not run:
        raise HTTPException(404, "run tidak dijumpai")
    if action == "stop":
        run["status"] = "cancelled"
        ar.save(run)
        try:
            ar.release_slot(run_id)
        except Exception:
            pass
        return {"ok": True, "id": run_id, "status": "cancelled"}
    if action == "rerun":
        run["status"] = "planned"
        run["outputs"] = []
        run["wave"] = 1
        run["error"] = None
        ar.save(run)
        out = ar.start_run(run_id)
        out.pop("trace", None)
        return out
    if action == "delete":
        d = ar._dir(run_id)
        trash = home_path("hermes20") / "cache" / "run-trash"
        trash.mkdir(parents=True, exist_ok=True)
        if d.exists():
            shutil.move(str(d), str(trash / run_id))
        return {"ok": True, "id": run_id, "moved_to": str(trash / run_id)}
    raise HTTPException(400, "action mesti stop | rerun | delete")


# --- BUKA APP (am start) ----------------------------------------------------
BUKA_BIN = Path.home() / "bin" / "buka"
BUKA_FIXED = [("home", "Skrin Utama"), ("set", "Tetapan")]


def _buka_exec(args, timeout=120):
    if not BUKA_BIN.exists():
        raise HTTPException(500, "skrip tiada: " + str(BUKA_BIN))
    try:
        p = subprocess.run([str(BUKA_BIN)] + args, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "exit": -1, "out": "tamat masa (%ds)" % timeout}
    out = ((p.stdout or "") + (p.stderr or "")).strip()
    return {"ok": p.returncode == 0, "exit": p.returncode, "out": out[-2500:]}


@app.get("/api/buka")
def api_buka_info():
    apps = []
    try:
        raw = subprocess.run(["pm", "list", "packages", "-3"], capture_output=True,
                             text=True, timeout=25).stdout
        apps = sorted(l.split(":", 1)[1].strip() for l in raw.splitlines() if l.startswith("package:"))
    except Exception as e:
        apps = []
        err = str(e)
    return {"apps": apps, "fixed": [{"t": t, "n": n} for t, n in BUKA_FIXED],
            "bin": str(BUKA_BIN), "exists": BUKA_BIN.exists()}


@app.post("/api/buka")
def api_buka_run(body: dict = Body(...)):
    target = (body.get("target") or "").strip()
    url = (body.get("url") or "").strip()
    if url:
        return _buka_exec(["url", url])
    if not target:
        raise HTTPException(400, "medan target/url kosong")
    return _buka_exec([target])


# --- Termux:Boot ------------------------------------------------------------
BOOT_PKG = "com.termux.boot"
BOOT_APK = Path.home() / "storage" / "downloads" / "TermuxBoot.apk"
BOOT_DIR = Path.home() / ".termux" / "boot"


def _pkg_installed(pkg: str) -> bool:
    try:
        r = subprocess.run(["pm", "list", "packages", pkg], capture_output=True, text=True, timeout=25)
        return f"package:{pkg}" in (r.stdout or "")
    except Exception:
        return False


BOOT_PROBE = BASE / "data" / "boot_probe.json"


def _boot_probe(ttl: int = 600) -> bool | None:
    """Android 11+ menyembunyikan pakej lain daripada `pm list` (package visibility).
    Jadi: cuba buka BootActivity — kalau activity tiada, Android balas 'does not exist'.
    Hasil dicache 10 minit supaya app tidak terbuka setiap kali tab dibuka."""
    try:
        if BOOT_PROBE.exists():
            d = json.loads(BOOT_PROBE.read_text())
            if time.time() - d.get("t", 0) < ttl:
                return d.get("ok")
    except Exception:
        pass
    ok = None
    try:
        r = subprocess.run(["am", "start", "-n", f"{BOOT_PKG}/.BootActivity"],
                           capture_output=True, text=True, timeout=25)
        out = (r.stdout or "") + (r.stderr or "")
        if "does not exist" in out or "Error type 3" in out:
            ok = False
        elif "Starting" in out:
            ok = True
    except Exception:
        ok = None
    try:
        BOOT_PROBE.parent.mkdir(parents=True, exist_ok=True)
        BOOT_PROBE.write_text(json.dumps({"t": time.time(), "ok": ok}))
    except Exception:
        pass
    return ok


def boot_status() -> dict:
    apk = {"path": str(BOOT_APK).replace(str(Path.home()), "~"), "exists": BOOT_APK.exists()}
    if BOOT_APK.exists():
        st = BOOT_APK.stat()
        apk.update({"bytes": st.st_size,
                    "mtime": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")})
    scripts = []
    if BOOT_DIR.exists():
        scripts = sorted(p.name for p in BOOT_DIR.iterdir() if p.is_file())
    pm_ok = _pkg_installed(BOOT_PKG)
    probe = None if pm_ok else _boot_probe()
    return {"package": BOOT_PKG, "installed": bool(pm_ok or probe),
            "sumber_semakan": "pm" if pm_ok else ("activity" if probe else "tiada"),
            "apk": apk,
            "boot_dir": str(BOOT_DIR).replace(str(Path.home()), "~"), "boot_scripts": scripts,
            "checked_at": datetime.now().isoformat(timespec="seconds"),
            "note": "Buka app Termux:Boot SEKALI selepas pasang, jika tidak skrip boot tidak berjalan."}


@app.get("/api/device/boot")
def api_boot_status():
    return boot_status()


@app.post("/api/device/boot-open")
def api_boot_open():
    """Buka app Termux:Boot (perlu sekali selepas pasang)."""
    try:
        r = subprocess.run(["am", "start", "-n", f"{BOOT_PKG}/.BootActivity"],
                           capture_output=True, text=True, timeout=30)
        out = ((r.stdout or "") + (r.stderr or "")).strip()
        ok = "does not exist" not in out and "Error type 3" not in out
    except Exception as e:
        raise HTTPException(500, f"gagal buka app: {e}")
    if not ok:
        raise HTTPException(404, "app Termux:Boot belum dipasang")
    return {"ok": True, "out": out[:300], "status": boot_status()}


@app.post("/api/device/boot-install")
def api_boot_install():
    """Buka pemasang APK Android untuk Termux:Boot (pengguna tekan PASANG)."""
    if not BOOT_APK.exists():
        raise HTTPException(404, f"APK tiada di {BOOT_APK} — muat turun dahulu")
    log = []
    pkg = "application/vnd.android.package-archive"
    saf = ("content://com.android.externalstorage.documents/document/"
           "primary%3ADownload%2FTermuxBoot.apk")
    tries = [
        ["termux-open", "--content-type", pkg, str(BOOT_APK)],
        ["am", "start", "-a", "android.intent.action.VIEW", "-t", pkg, "-d", f"file://{BOOT_APK}"],
        ["am", "start", "-a", "android.intent.action.VIEW", "--grant-read-uri-permission",
         "-t", pkg, "-d", saf],
        ["am", "start", "-a", "android.intent.action.INSTALL_PACKAGE", "-d", saf],
    ]
    for cmd in tries:
        if not shutil.which(cmd[0]):
            log.append({"cara": cmd[0], "skip": "tidak dijumpai"})
            continue
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
            out = ((r.stdout or "") + (r.stderr or "")).strip()
            log.append({"cara": " ".join(cmd[:3]), "kod": r.returncode, "out": out[:300],
                        "nampak_berjaya": r.returncode == 0 and "Error" not in out})
        except Exception as e:
            log.append({"cara": cmd[0], "ralat": str(e)[:200]})
    return {"ok": True, "apk": str(BOOT_APK), "log": log, "status": boot_status(),
            "next": "Di telefon: tekan PASANG pada dialog Android, kemudian buka app Termux:Boot sekali."}


# --------------------------------------------------------------------------- #
# laporan harian + penghantaran Telegram + inbox fail/imej
# --------------------------------------------------------------------------- #
INBOX_DIR = BASE / "inbox"
REPORT_DIR = BASE / "data" / "reports"
ENV20 = home_path("hermes20") / ".env"
TEXT_EXT = {".md", ".txt", ".csv", ".json", ".py", ".js", ".ts", ".yaml", ".yml",
            ".html", ".css", ".sql", ".log", ".sh", ".toml", ".xml"}


def _env20() -> dict:
    out = {}
    try:
        for line in ENV20.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return out


def _history_summary(days: int = 7) -> dict:
    return api_history(days)



def _proc_alive(pattern: str) -> dict:
    """Cari proses mengikut corak cmdline (tanpa pgrep)."""
    hits = []
    try:
        for pid in os.listdir("/proc"):
            if not pid.isdigit():
                continue
            try:
                cmd = Path(f"/proc/{pid}/cmdline").read_bytes().decode("utf-8", "replace")
            except Exception:
                continue
            if pattern in cmd.replace("\x00", " "):
                hits.append({"pid": int(pid), "cmd": cmd.replace("\x00", " ").strip()[:160]})
    except Exception:
        pass
    return {"alive": bool(hits), "procs": hits[:3]}


def paper_state() -> dict:
    """Keadaan demo paper trading ATC hermes19 (CSV + log + proses)."""
    atc = home_path("hermes19") / "autonomous_trading_controller"
    csvp, logp = atc / "paper_trading_log.csv", atc / "paper_run.log"
    proc = _proc_alive("run_paper.py")
    header, rows, total = [], [], 0
    if csvp.exists():
        try:
            lines = csvp.read_text(encoding="utf-8", errors="replace").splitlines()
            if lines:
                header = [h.strip() for h in lines[0].split(",")]
                body = [ln for ln in lines[1:] if ln.strip()]
                total = len(body)
                rows = [[c.strip() for c in ln.split(",")] for ln in body[-12:]]
        except Exception:
            pass
    events = []
    if logp.exists():
        try:
            for ln in logp.read_text(encoding="utf-8", errors="replace").splitlines()[-800:]:
                s = ln.strip()
                if s.startswith("[") and any(k in s for k in ("TRADE_CANDIDATE", "NO_TRADE", "WIN", "LOSS", "VETO")):
                    events.append(s[:200])
        except Exception:
            pass
    feed = {}
    try:
        feed = json.loads((atc / "data" / "feed_status.json").read_text())
    except Exception:
        pass
    return {"alive": proc["alive"], "procs": proc["procs"], "header": header, "feed": feed,
            "rows": rows, "rows_total": total, "events": events[-8:],
            "csv": str(csvp).replace(str(Path.home()), "~"),
            "csv_mtime": datetime.fromtimestamp(csvp.stat().st_mtime).isoformat(timespec="seconds") if csvp.exists() else None}

def build_daily_report(day: str | None = None) -> str:
    """Laporan harian Markdown dari data hidup + arkib run."""
    import agency_runner as ar

    now = datetime.now()
    day = day or now.strftime("%Y-%m-%d")
    st = live_state()
    s = st["stats"]
    cost = _runs_today_cost()
    hist = api_history(7)
    runs_today = []
    if ar.RUNS.exists():
        for d in sorted(ar.RUNS.iterdir()):
            r = ar.load(d.name)
            if not r:
                continue
            created = (r.get("created") or "")[:10]
            if created != day:
                continue
            u = r.get("usage") or {}
            runs_today.append((r, u))

    L = []
    L.append(f"# Laporan Harian — Hermes Console ({day})")
    L.append("")
    L.append(f"Dijana: {now.strftime('%Y-%m-%d %H:%M:%S')} · home: `~/.hermes20` · model: `{default_model('hermes20')}`")
    L.append("")
    L.append("## Ringkasan")
    L.append("")
    L.append("| Metrik | Nilai |")
    L.append("|---|---|")
    L.append(f"| Gateway | {'HIDUP' if (st['gateway'] or {}).get('pid_alive') else 'MATI'} |")
    L.append(f"| Sesi hari ini | {s.get('sessions_today', 0)} |")
    L.append(f"| Sesi aktif (5m) | {s.get('active_sessions', 0)} |")
    L.append(f"| Tool call | {s.get('tools_today', 0)} |")
    L.append(f"| Token | {s.get('tokens_today', 0):,} |")
    L.append(f"| Kos sesi Hermes | ${float(s.get('cost_today') or 0):.4f} |")
    L.append(f"| Kos konsol (ejen) | ${float(cost.get('total') or 0):.4f} |")
    L.append(f"| Run hari ini | {len(runs_today)} |")
    L.append("")

    if runs_today:
        L.append("## Run & kos per ejen")
        L.append("")
        L.append("| Run | Status | Ejen | Token | Kos |")
        L.append("|---|---|---|---|---|")
        for r, u in runs_today:
            slugs = ", ".join(a["slug"] for a in (r.get("plan") or {}).get("ejen", []))
            L.append(f"| `{r['id']}` | {r.get('status')} | {slugs} | {int(u.get('total_tokens') or 0):,} | ${float(u.get('total_cost') or 0):.4f} |")
        L.append("")
        L.append("### Pecahan kos per ejen")
        L.append("")
        for r, u in runs_today:
            agents = u.get("agents") or {}
            if not agents:
                continue
            L.append(f"**{r['id']}** — pelan ${float((u.get('plan') or {}).get('cost') or 0):.4f} · "
                     f"sintesis ${float((u.get('synthesis') or {}).get('cost') or 0):.4f}")
            for slug, au in sorted(agents.items(), key=lambda x: -float(x[1].get("cost") or 0)):
                L.append(f"- `{slug}` — ${float(au.get('cost') or 0):.4f} · {int(au.get('total') or 0):,} tok · {au.get('calls') or 0} panggilan")
            L.append("")

    if st["runs"]:
        L.append("## Sedang berjalan")
        L.append("")
        for r in st["runs"]:
            L.append(f"- `{r['id']}` · {r['status']} · gelombang {r['wave']}/{r['wave_total']} · "
                     f"{r['finished']}/{r['total']} ejen · kos setakat ${float(r.get('cost_so_far') or 0):.4f}")
            for a in r["agents"]:
                if a["state"] == "running":
                    L.append(f"  - AKTIF `{a['slug']}` di {a.get('location')} ({a.get('elapsed_s')}s)")
        L.append("")

    days = hist.get("days") or []
    if days:
        L.append("## 7 hari")
        L.append("")
        L.append("| Tarikh | Kos konsol | Puncak ejen | Sampel |")
        L.append("|---|---|---|---|")
        for d in days:
            L.append(f"| {d['date']} | ${float(d.get('console_cost') or d.get('cost') or 0):.4f} | {d.get('agents_peak', 0)} | {d.get('samples', 0)} |")
        L.append("")

    L.append("## Pautan")
    L.append("")
    L.append(f"- Papan pemantau: `{SCHEME}://{CONSOLE_HOST}:{CONSOLE_PORT}/`")
    L.append("- Alur kerja: `/static/img/workflow.png`")
    L.append("")
    L.append("_Dijana automatik oleh Hermes Console._")
    return "\n".join(L)


def tg_send(text: str, caption: str | None = None, file_path: Path | None = None) -> dict:
    """Hantar mesej/dokumen ke Telegram guna Bot API (token home hermes20)."""
    e = _env20()
    token = e.get("TELEGRAM_BOT_TOKEN")
    chat = e.get("TELEGRAM_HOME_CHANNEL") or e.get("TELEGRAM_ALLOWED_USERS", "").split(",")[0]
    if not token or not chat:
        raise RuntimeError("TELEGRAM_BOT_TOKEN / TELEGRAM_HOME_CHANNEL tiada dalam ~/.hermes20/.env")
    base = f"https://api.telegram.org/bot{token}"

    if file_path and file_path.exists():
        boundary = "----hermesconsole" + secrets.token_hex(8)
        parts = []
        def field(name, val):
            parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{val}\r\n".encode())
        field("chat_id", str(chat))
        if caption:
            field("caption", caption[:1000])
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"document\"; filename=\"{file_path.name}\"\r\n"
            f"Content-Type: text/markdown\r\n\r\n".encode() + file_path.read_bytes() + b"\r\n"
        )
        parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(parts)
        req = urllib.request.Request(f"{base}/sendDocument", data=body,
                                     headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                                     method="POST")
    else:
        body = json.dumps({"chat_id": str(chat), "text": text[:4000],
                           "disable_web_page_preview": True}).encode()
        req = urllib.request.Request(f"{base}/sendMessage", data=body,
                                     headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.loads(r.read().decode())
    if not j.get("ok"):
        raise RuntimeError(f"Telegram: {j}")
    res = j.get("result") or {}
    return {"ok": True, "message_id": res.get("message_id"), "chat": chat,
            "kind": "document" if file_path else "text"}


@app.get("/api/report/daily")
def api_report_daily(day: str = ""):
    from fastapi.responses import PlainTextResponse

    md = build_daily_report(day or None)
    return PlainTextResponse(md, media_type="text/markdown",
                             headers={"Content-Disposition": f'inline; filename="laporan-{day or datetime.now():%Y-%m-%d}.md"'})


@app.post("/api/report/send")
def api_report_send(payload: dict = Body(...)):
    channel = (payload.get("channel") or "telegram").lower()
    if channel != "telegram":
        raise HTTPException(400, "channel tidak disokong (telegram sahaja)")
    day = (payload.get("day") or datetime.now().strftime("%Y-%m-%d")).strip()
    md = build_daily_report(day)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    f = REPORT_DIR / f"laporan-{day}.md"
    f.write_text(md)
    try:
        res = tg_send("", caption=f"Laporan harian {day} · Hermes Console", file_path=f)
    except Exception as e:
        raise HTTPException(502, f"gagal hantar: {e}")
    return {"ok": True, "file": str(f).replace(str(Path.home()), "~"), "bytes": f.stat().st_size, **res}


@app.get("/api/inbox")
def api_inbox():
    items = []
    if INBOX_DIR.exists():
        for d in sorted(INBOX_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)[:40]:
            meta = d / "meta.json"
            if not meta.exists():
                continue
            try:
                m = json.loads(meta.read_text())
            except Exception:
                continue
            m["path"] = str(d)
            items.append(m)
    return {"items": items, "dir": str(INBOX_DIR).replace(str(Path.home()), "~"),
            "count": len(items)}


@app.post("/api/inbox")
def api_inbox_add(payload: dict = Body(...)):
    name = (payload.get("filename") or "nota.txt").strip().replace("/", "_")[:120]
    note = (payload.get("note") or "").strip()[:2000]
    b64 = payload.get("content_b64") or ""
    raw = b""
    if b64:
        try:
            raw = base64.b64decode(b64.split(",")[-1])
        except Exception:
            raise HTTPException(400, "kandungan base64 tidak sah")
    if len(raw) > 8 * 1024 * 1024:
        raise HTTPException(400, "fail melebihi 8 MB")
    ext = Path(name).suffix.lower()
    text = ""
    if ext in TEXT_EXT and raw:
        try:
            text = raw.decode("utf-8", "replace")[:20000]
        except Exception:
            text = ""
    iid = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + secrets.token_hex(3)
    d = INBOX_DIR / iid
    d.mkdir(parents=True, exist_ok=True, mode=0o700)
    if raw:
        safe = f"{iid}{ext or '.bin'}"
        (d / safe).write_bytes(raw)
    else:
        safe = None
    meta = {"id": iid, "filename": name, "stored": safe, "bytes": len(raw),
            "note": note, "text_preview": text[:4000], "has_text": bool(text),
            "created": datetime.now().isoformat(timespec="seconds"),
            "kind": "image" if ext in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".heic"} else
                    ("text" if text else ("file" if raw else "note"))}
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    return meta


@app.get("/api/inbox/{iid}/file")
def api_inbox_file(iid: str):
    if not re.fullmatch(r"\d{8}_\d{6}_[0-9a-f]{6}", iid or ""):
        raise HTTPException(400, "id tidak sah")
    d = INBOX_DIR / iid
    meta = json.loads((d / "meta.json").read_text())
    stored = meta.get("stored")
    if not stored or not (d / stored).exists():
        raise HTTPException(404, "fail tiada")
    return FileResponse(d / stored, filename=meta.get("filename") or stored)


def inbox_context(ids: list[str]) -> list[dict]:
    out = []
    for iid in ids or []:
        d = INBOX_DIR / str(iid)
        try:
            m = json.loads((d / "meta.json").read_text())
        except Exception:
            continue
        out.append(m)
    return out

# --------------------------------------------------------------------------- #
# lokasi + kos per ejen, rekod 7 hari, bot status
# --------------------------------------------------------------------------- #
DIV_TO_SYSTEM = {d: s for s, ds in DIV_SYSTEM.items() for d in ds}
_META = {"key": None, "map": {}}
HIST_FILE = BASE / "data" / "history.jsonl"


def agent_meta() -> dict:
    data = _load_agency()
    key = (len(data["agents"]), id(data["agents"]))
    if _META["key"] != key:
        _META["map"] = {
            a["slug"]: {"name": a.get("name"), "division": a.get("division"), "emoji": a.get("emoji")}
            for a in data["agents"]
        }
        _META["key"] = key
    return _META["map"]


def _locate(slug: str) -> dict:
    m = agent_meta().get(slug) or {}
    div = m.get("division")
    sysm = DIV_TO_SYSTEM.get(div, "—")
    return {"slug": slug, "nama": m.get("name") or slug, "emoji": m.get("emoji"),
            "division": div, "system": sysm,
            "location": f"{sysm} → {div} → {slug}" if div else slug}


def _runs_today_cost() -> dict:
    import agency_runner as ar

    total, per_run, per_agent = 0.0, [], {}
    today = datetime.now().strftime("%Y%m%d")
    if not ar.RUNS.exists():
        return {"total": 0.0, "runs": [], "agents": {}}
    for d in sorted(ar.RUNS.iterdir()):
        if not d.name.startswith(today):
            continue
        r = ar.load(d.name)
        if not r:
            continue
        u = r.get("usage") or {}
        c = float(u.get("total_cost") or 0)
        total += c
        per_run.append({"id": r["id"], "status": r.get("status"), "cost": round(c, 6),
                        "tokens": int(u.get("total_tokens") or 0),
                        "agents": [a["slug"] for a in (r.get("plan") or {}).get("ejen", [])]})
        for slug, au in (u.get("agents") or {}).items():
            e = per_agent.setdefault(slug, {"cost": 0.0, "tokens": 0, "calls": 0})
            e["cost"] += float(au.get("cost") or 0)
            e["tokens"] += int(au.get("total") or 0)
            e["calls"] += int(au.get("calls") or 0)
    return {"total": round(total, 6), "runs": per_run, "agents": per_agent}


def _history_append() -> None:
    """Satu snapshot setiap 60s (rekod 7 hari)."""
    HIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        st = live_state()
        s = st["stats"]
        rec = {"ts": time.time(), "date": datetime.now().strftime("%Y-%m-%d"),
               "tools": s.get("tools_today", 0), "tokens": s.get("tokens_today", 0),
               "cost": s.get("cost_today", 0), "sessions": s.get("sessions_today", 0),
               "agents": len(st.get("active_agents") or []), "runs": len(st.get("runs") or []),
               "console_cost": round(float((_runs_today_cost() or {}).get("total") or 0), 6)}
        with HIST_FILE.open("a") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass


def _history_worker() -> None:
    while True:
        _history_append()
        time.sleep(60)


@app.get("/api/history")
def api_history(days: int = Query(7, ge=1, le=30)):
    by_day: dict[str, dict] = {}
    if HIST_FILE.exists():
        for line in HIST_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                r = json.loads(line)
            except Exception:
                continue
            d = r.get("date")
            if not d:
                continue
            cur = by_day.setdefault(d, {"date": d, "tools": 0, "tokens": 0, "cost": 0.0,
                                        "console_cost": 0.0, "agents_peak": 0, "samples": 0})
            cur["tools"] = max(cur["tools"], int(r.get("tools") or 0))
            cur["tokens"] = max(cur["tokens"], int(r.get("tokens") or 0))
            cur["cost"] = max(cur["cost"], float(r.get("cost") or 0))
            cur["console_cost"] = max(cur["console_cost"], float(r.get("console_cost") or 0))
            cur["agents_peak"] = max(cur["agents_peak"], int(r.get("agents") or 0))
            cur["samples"] += 1
    days_sorted = sorted(by_day.values(), key=lambda x: x["date"])[-days:]
    return {"days": days_sorted, "file": str(HIST_FILE).replace(str(Path.home()), "~"),
            "samples": sum(d["samples"] for d in days_sorted)}


@app.get("/api/agent-live/{slug}")
def api_agent_live(slug: str):
    import agency_runner as ar

    loc = _locate(slug)
    live = live_state()
    active = next((a for r in live["runs"] for a in r["agents"] if a["slug"] == slug), None)
    run_ctx, output = None, None
    if ar.RUNS.exists():
        for d in sorted(ar.RUNS.iterdir(), reverse=True)[:12]:
            r = ar.load(d.name)
            if not r:
                continue
            outs = {o["slug"]: o for o in (r.get("outputs") or [])}
            planned = [a["slug"] for a in (r.get("plan") or {}).get("ejen", [])]
            if slug in outs or slug in planned:
                u = (r.get("usage") or {}).get("agents", {}).get(slug) or {}
                atts = [{"id": x.get("id"), "filename": x.get("filename"), "kind": x.get("kind"),
                         "bytes": x.get("bytes")} for x in (r.get("attachments") or [])]
                run_ctx = {"id": r["id"], "status": r.get("status"), "wave": r.get("wave"),
                           "wave_total": r.get("wave_total"), "instruction": (r.get("instruction") or "")[:220],
                           "planned": slug in planned, "cost": u.get("cost"), "tokens": u.get("total"),
                           "attachments": atts}
                if slug in outs:
                    output = {"status": outs[slug]["status"], "text": outs[slug]["text"][:8000],
                              "ms": outs[slug].get("ms")}
                break
    return {**loc, "active": active, "run": run_ctx, "output": output,
            "uses": 0, "today": _runs_today_cost()["agents"].get(slug)}


BOT_HELP = """Arahan yang tersedia:
/status        ringkasan sistem + apa yang berjalan
/agents        siapa aktif, di lokasi mana, kos setakat ini
/where <slug>  lokasi + tugasan ejen tertentu
/cost          kos hari ini (Ketua + ejen + sintesis)
/runs          run terakhir + kos
/help          senarai arahan"""


@app.post("/api/bot")
def api_bot(payload: dict = Body(...)):
    cmd = (payload.get("cmd") or "").strip()
    st = live_state()
    runs = st["runs"]
    active = st["active_agents"]
    today = _runs_today_cost()
    if not cmd or cmd in ("/help", "help"):
        return {"reply": BOT_HELP}
    head = cmd.split()[0].lower()

    if head == "/status":
        gw = st["gateway"]
        lines = [
            f"Gateway      : {'HIDUP' if gw.get('pid_alive') else 'MATI'} (pid {gw.get('pid')})",
            f"Sesi aktif   : {st['stats']['active_sessions']} (5m) · {st['stats']['sessions_today']} hari ini",
            f"Run aktif    : {len(runs)}" + (f" · gelombang {runs[0]['wave']}/{runs[0]['wave_total']}" if runs else ""),
            f"Ejen aktif   : {len(active)}" + (f" — {', '.join(active)}" if active else ""),
            f"Kos konsol   : ${today['total']:.4f} hari ini",
            f"Tool / token : {st['stats']['tools_today']} / {st['stats']['tokens_today']}",
        ]
        return {"reply": "\n".join(lines)}

    if head == "/agents":
        if not runs:
            return {"reply": "Tiada ejen berjalan sekarang."}
        out = []
        for r in runs:
            out.append(f"RUN {r['id']} · {r['status']} · gelombang {r['wave']}/{r['wave_total']} · {r['finished']}/{r['total']} ejen")
            for a in r["agents"]:
                loc = _locate(a["slug"])
                state = a["state"]
                cost = (r.get("cost_by_agent") or {}).get(a["slug"])
                tail = f" · ${cost:.4f}" if cost else ""
                el = f" · {int(a.get('elapsed_s') or 0)}s" if a.get("elapsed_s") else ""
                out.append(f"  {state:8} {loc['emoji'] or ''} {loc['nama']:<24} {loc['location']}{el}{tail}")
        return {"reply": "\n".join(out)}

    if head == "/where":
        parts = cmd.split(maxsplit=1)
        if len(parts) < 2:
            return {"reply": "Guna: /where <slug>  (contoh /where brand-guardian)"}
        slug = parts[1].strip().lower().replace(" ", "-")
        info = api_agent_live(slug)
        state = (info.get("active") or {}).get("state") or ("tiada dalam run aktif")
        lines = [
            f"{info['nama']} ({slug})",
            f"Lokasi  : {info['location']}",
            f"Status  : {state}",
        ]
        if info.get("run"):
            r = info["run"]
            lines.append(f"Run     : {r['id']} · {r['status']} · gelombang {r.get('wave')}/{r.get('wave_total')}")
            lines.append(f"Tugasan : {r['instruction'][:150]}")
            if r.get("cost"):
                lines.append(f"Kos     : ${float(r['cost']):.4f} · {r.get('tokens') or 0} token")
        if info.get("output"):
            lines.append(f"Output  : {info['output']['status']} · {len(info['output']['text'])} aksara")
        return {"reply": "\n".join(lines)}

    if head == "/cost":
        if not today["runs"]:
            return {"reply": "Belum ada run konsol hari ini."}
        lines = [f"Kos konsol hari ini: ${today['total']:.4f}", ""]
        for r in today["runs"]:
            lines.append(f"  {r['id']}  ${r['cost']:.4f}  {r['tokens']} tok  [{r['status']}]  {', '.join(r['agents'])}")
        if today["agents"]:
            lines.append("\nMengikut ejen:")
            for slug, e in sorted(today["agents"].items(), key=lambda x: -x[1]["cost"])[:8]:
                lines.append(f"  {slug:<24} ${e['cost']:.4f}  {e['tokens']} tok  {e['calls']} panggilan")
        return {"reply": "\n".join(lines)}

    if head == "/runs":
        import agency_runner as ar

        rs = ar.latest(6)
        if not rs:
            return {"reply": "Tiada run."}
        lines = []
        for r in rs:
            full = ar.load(r["id"]) or {}
            u = full.get("usage") or {}
            lines.append(f"{r['id']}  {r['status']:<10} ${float(u.get('total_cost') or 0):.4f}  {', '.join(r['agents'])}")
        return {"reply": "\n".join(lines)}

    return {"reply": f"Arahan tidak dikenali: {cmd}\n\n{BOT_HELP}"}

# --------------------------------------------------------------------------- #
# DEWAN ARAHAN — Ketua merancang, ejen melaksana
# --------------------------------------------------------------------------- #
@app.get("/api/agency/analysis")
def api_agency_analysis():
    f = BASE / "data" / "agent_style.json"
    if not f.exists():
        raise HTTPException(404, "analisis belum dijana — jalankan tools/analyze_agents.py")
    d = json.loads(f.read_text())
    return {k: d[k] for k in ("generated_at", "source", "totals", "sections_top", "archetypes",
                              "styles", "feature_presence", "by_division", "clusters")}


@app.get("/api/agency/workflow")
def api_agency_workflow():
    f = BASE / "static" / "img" / "workflow.png"
    if not f.exists():
        raise HTTPException(404, "imej alur kerja belum dijana")
    return {"png": "/static/img/workflow.png", "svg": "/static/img/workflow.svg",
            "w": 1500, "h": 1210, "bytes": f.stat().st_size}


_PLAN_LOCK = {"n": 0}


@app.get("/api/agency/guard")
def api_agency_guard():
    import agency_runner as ar
    return ar.guard_status()


@app.post("/api/agency/plan")
def api_agency_plan(payload: dict = Body(...)):
    instr = (payload.get("instruction") or "").strip()
    if len(instr) < 12:
        raise HTTPException(400, "arahan terlalu pendek (minimum 12 aksara)")
    if len(instr) > 4000:
        raise HTTPException(400, "arahan terlalu panjang (maksimum 4000 aksara)")
    max_agents = max(1, min(6, int(payload.get("max_agents") or 3)))
    atts = inbox_context([str(x) for x in (payload.get("attachment_ids") or [])])
    if _PLAN_LOCK["n"] >= 1:
        raise HTTPException(429, "Ketua sedang merancang arahan lain — tunggu sebentar")
    _PLAN_LOCK["n"] += 1
    try:
        import agency_runner as ar
        run = ar.plan_run(instr, max_agents, atts)
    except Exception as e:
        raise HTTPException(500, f"Ketua gagal merancang: {e}")
    finally:
        _PLAN_LOCK["n"] -= 1
    if run.get("status") == "failed":
        return JSONResponse(run, status_code=502)
    run.pop("trace", None)
    return run


@app.post("/api/agency/run/{run_id}")
def api_agency_start(run_id: str):
    try:
        import agency_runner as ar
        if not ar.valid_run_id(run_id):
            raise HTTPException(400, "id run tidak sah")
        run = ar.start_run(run_id)
    except Exception as e:
        raise HTTPException(400, str(e))
    run.pop("trace", None)
    return run


@app.get("/api/agency/run/{run_id}")
def api_agency_run(run_id: str):
    import agency_runner as ar
    if not ar.valid_run_id(run_id):
        raise HTTPException(400, "id run tidak sah")
    run = ar.load(run_id)
    if not run:
        raise HTTPException(404, "run tidak dijumpai")
    run.pop("trace", None)
    return run


@app.post("/api/agency/run/{run_id}/note")
def api_run_note(run_id: str, payload: dict = Body(...)):
    """Tambah nota/lampiran ke run yang sedang berjalan (untuk betulkan tugas)."""
    import agency_runner as ar

    if not ar.valid_run_id(run_id):
        raise HTTPException(400, "id run tidak sah")
    run = ar.load(run_id)
    if not run:
        raise HTTPException(404, "run tidak dijumpai")
    text = (payload.get("text") or "").strip()[:2000]
    atts = inbox_context([str(x) for x in (payload.get("attachment_ids") or [])])
    if not text and not atts:
        raise HTTPException(400, "nota atau lampiran diperlukan")
    body = text
    for at in atts:
        body += f"\n[LAMPIRAN {at.get('filename')} · {at.get('kind')}]"
        if at.get("note"):
            body += f" nota: {at['note']}"
        if at.get("text_preview"):
            body += "\n" + at["text_preview"][:2500]
    entry = {"ts": datetime.now().isoformat(timespec="seconds"), "text": body,
             "attachments": [a["id"] for a in atts]}
    updated = ar.append_inbox(run_id, entry, atts)
    if not updated:
        raise HTTPException(404, "run tidak dijumpai")
    return {"ok": True, "run": run_id, "inbox": updated["inbox"]}


@app.get("/api/agency/runs")
def api_agency_runs():
    import agency_runner as ar
    return {"runs": ar.latest(12), "dir": str(ar.RUNS).replace(str(Path.home()), "~")}


# --------------------------------------------------------------------------- #
# GUDANG — hantar fail dari kilang ($HOME) ke storan telefon (SEHALA)
# --------------------------------------------------------------------------- #
UIM_ROOT = Path("/sdcard/Documents/UIM")
UIM_LOG = Path.home() / ".hermes20" / "logs" / "uim_hantar.log"
UIM_HANTAR = Path.home() / ".hermes20" / "scripts" / "uim_hantar.sh"
UIM_PDF = Path.home() / ".hermes20" / "scripts" / "uim_pdf.sh"
UIM_KATEGORI = ("01-LAPORAN", "02-GAMBAR", "03-AUDIO", "04-VIDEO", "05-HANTAR")
HOME_REAL = Path(os.path.realpath(str(Path.home())))


def _uim_sumber(path_val) -> Path:
    """Sahkan laluan sumber: fail biasa, selepas realpath mesti di dalam $HOME."""
    if not isinstance(path_val, str) or not path_val.strip():
        raise HTTPException(400, "path diperlukan")
    raw = path_val.strip()
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = HOME_REAL / p
    try:
        real = Path(os.path.realpath(str(p), strict=True))
    except (FileNotFoundError, NotADirectoryError):
        raise HTTPException(400, f"fail tidak wujud: {raw}")
    except OSError as e:
        raise HTTPException(400, f"laluan tidak sah: {e}")
    if real != HOME_REAL and HOME_REAL not in real.parents:
        raise HTTPException(400, "path mesti di dalam $HOME (kilang Termux sahaja)")
    if not real.is_file():
        raise HTTPException(400, "path bukan fail biasa")
    return real


def _uim_jalan(skrip: Path, args: list[str]) -> dict:
    if not skrip.exists():
        raise HTTPException(503, f"skrip belum sedia: {skrip.name}")
    try:
        p = subprocess.run([str(skrip), *args], capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        raise HTTPException(504, f"{skrip.name} tamat masa (120s)")
    except OSError as e:
        raise HTTPException(500, f"gagal jalankan {skrip.name}: {e}")
    out = ((p.stdout or "") + (p.stderr or "")).strip()
    return {"kod": p.returncode, "output": out[:8000], "stdout": p.stdout or ""}


@app.get("/api/uim/state")
def api_uim_state():
    """Keadaan gudang telefon + calon fail dalam $HOME + ekor log salinan."""
    gudang: list[dict] = []
    jumlah = 0
    if UIM_ROOT.is_dir():
        for kat in sorted(UIM_ROOT.iterdir()):
            if not kat.is_dir() or kat.name.startswith("_"):
                continue
            try:
                fail = [f for f in kat.iterdir() if f.is_file() and not f.is_symlink()]
            except OSError:
                continue
            for f in fail:
                try:
                    st = f.stat()
                except OSError:
                    continue
                jumlah += 1
                gudang.append({
                    "nama": f.name, "kategori": kat.name, "saiz": st.st_size,
                    "masa": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
                })
    gudang.sort(key=lambda x: x["masa"], reverse=True)

    calon: list[dict] = []
    punca = sorted((Path.home() / ".hermes20" / "docs").glob("*.md"))
    for ob in (Path.home() / ".hermes20" / "workspaces").glob("*/outbox/*"):
        if ob.is_file() and not ob.is_symlink():
            punca.append(ob)
    def _mt(f: Path) -> float:
        try:
            return f.stat().st_mtime
        except OSError:
            return 0.0

    for f in sorted(punca, key=_mt, reverse=True)[:20]:
        try:
            st = f.stat()
            calon.append({"laluan": str(f), "nama": f.name, "saiz": st.st_size,
                          "masa": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")})
        except OSError:
            continue

    log = tail(UIM_LOG, n=20) if UIM_LOG.exists() else []
    return {"gudang": gudang, "calon": calon, "log": log,
            "ringkasan": {"fail": jumlah, "saiz": sum(g["saiz"] for g in gudang)},
            "kategori": list(UIM_KATEGORI), "akar": str(UIM_ROOT)}


@app.post("/api/uim/hantar")
def api_uim_hantar(payload: dict = Body(...)):
    """Salin satu fail ke /sdcard/Documents/UIM/<kategori> melalui uim_hantar.sh."""
    src = _uim_sumber(payload.get("path"))
    kat = (payload.get("kategori") or "").strip()
    if kat and kat not in UIM_KATEGORI:
        raise HTTPException(400, f"kategori tidak sah: {kat}")
    args = [str(src)]
    if kat:
        args += ["--ke", kat]
    res = _uim_jalan(UIM_HANTAR, args)
    laluan, telegram = "", ""
    for line in res["stdout"].splitlines():
        if line.startswith("SIAP:"):
            laluan = line.split(":", 1)[1].strip()
        elif line.startswith("SIAP PDF:") or line.startswith("SIAP-PDF:"):
            laluan = line.split(":", 1)[1].strip()
        elif line.startswith("HANTAR-TELEGRAM:"):
            telegram = line.split(":", 1)[1].strip()
    if not telegram and laluan:
        telegram = f"MEDIA:{laluan}"
    return {"ok": res["kod"] == 0, "kod": res["kod"], "output": res["output"],
            "laluan": laluan, "telegram": telegram,
            "arahan": "Buka app Files → Documents → UIM" if res["kod"] == 0 else ""}


@app.post("/api/uim/pdf")
def api_uim_pdf(payload: dict = Body(...)):
    """Jana PDF daripada fail .md melalui uim_pdf.sh lalu salin ke 01-LAPORAN."""
    src = _uim_sumber(payload.get("path"))
    if src.suffix.lower() != ".md":
        raise HTTPException(400, "PDF hanya untuk fail .md")
    args = [str(src)]
    nama = (payload.get("nama") or "").strip()
    if nama:
        if "/" in nama or ".." in nama:
            raise HTTPException(400, "nama tidak sah")
        args += ["--nama", nama[:120]]
    res = _uim_jalan(UIM_PDF, args)
    laluan = ""
    for line in res["stdout"].splitlines():
        if line.startswith("SIAP-PDF:") or line.startswith("SIAP PDF:"):
            laluan = line.split(":", 1)[1].strip()
        elif line.startswith("SIAP:") and not laluan:
            laluan = line.split(":", 1)[1].strip()
    return {"ok": res["kod"] == 0, "kod": res["kod"], "output": res["output"],
            "laluan": laluan,
            "arahan": "Buka app Files → Documents → UIM → 01-LAPORAN" if res["kod"] == 0 else ""}


@app.exception_handler(HTTPException)
def http_err(request, exc):
    return JSONResponse({"error": exc.detail}, status_code=exc.status_code)


import threading  # noqa: E402

threading.Thread(target=_size_worker, daemon=True, name="size-worker").start()
try:
    _n = _steps_seed()
    if _n:
        print(f"panduan: {_n} langkah di-seed")
except Exception as _e:
    print("panduan seed gagal:", _e)

th = threading.Thread(target=_history_worker, daemon=True, name="history-worker")
th.start()

try:  # tutup run yang terhenti akibat server mati / thread crash
    import agency_runner as _ar

    _stale = _ar.recover_stale(max_age_s=900)
    if _stale:
        print("run stale ditutup:", ", ".join(_stale))
except Exception as _e:
    print("recover_stale gagal:", _e)


def _stale_janitor() -> None:
    """Setiap 5 min: tutup run yang thread-nya mati (server restart / proses dibunuh).

    Tanpa ini, run kekal 'synthesizing' sampai 15 min dan UI nampak tergantung.
    """
    import agency_runner as _a

    while True:
        time.sleep(300)
        try:
            fixed = _a.recover_stale(max_age_s=420)
            if fixed:
                print("janitor: run stale ditutup:", ", ".join(fixed))
        except Exception as e:  # noqa: BLE001
            print("janitor gagal:", e)


threading.Thread(target=_stale_janitor, daemon=True, name="stale-janitor").start()

if __name__ == "__main__":
    import uvicorn

    # Satu fail pid IKUT PORT — dua instance (8787 hermes20 / 8790 hermes19)
    # tidak boleh berkongsi fail pid yang sama, jika tidak stop_server akan
    # mematikan instance yang salah.
    pidf = Path(__file__).resolve().parent / f"server-{CONSOLE_PORT}.pid"
    pidf.write_text(str(os.getpid()))
    if CONSOLE_PORT == 8787:  # keserasian lama
        (Path(__file__).resolve().parent / "server.pid").write_text(str(os.getpid()))
    url = f"{SCHEME}://{CONSOLE_HOST}:{CONSOLE_PORT}"
    print(f"HERMES CONSOLE → {url}" + ("  [LAN + TOKEN]" if LAN_TOKEN else "")
          + f"  [home={DEFAULT_HOME} · tab={DEFAULT_TAB}]")
    kw = {}
    if CONSOLE_TLS:
        cert = Path(os.environ.get("CONSOLE_CERT", BASE / "certs" / "console.crt"))
        key = Path(os.environ.get("CONSOLE_KEY", BASE / "certs" / "console.key"))
        if cert.exists() and key.exists():
            kw = {"ssl_certfile": str(cert), "ssl_keyfile": str(key)}
            print(f"TLS: {cert.name}")
        else:
            print("TLS diminta tetapi sijil tiada — jatuh balik ke HTTP")
    try:
        uvicorn.run(app, host=CONSOLE_BIND, port=CONSOLE_PORT, log_level="warning", **kw)
    finally:
        try:
            if pidf.read_text().strip() == str(os.getpid()):
                pidf.unlink()
        except Exception:
            pass
