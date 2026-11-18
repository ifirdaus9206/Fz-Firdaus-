#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""remote_status_push.py — TEMPLATE: remote machine pushes a whitelisted status.json
to a private GitHub repo (Contents API) for a localhost console to read.

Copy → rename (e.g. sofia_status.py) → set cfg["repo"] → run the three self-tests:
    python <script> --print-config     # token_ada? which hermes home found?
    python <script> --dry-run          # JSON only, nothing sent
    python <script>                    # real PUT; exit 0 ok / 2 failed

Why Contents API and not git: the remote box usually has no git, and a single
HTTPS PUT needs no clone, no working tree, no hooks. Token = fine-grained PAT
scoped to that one repo, Contents: Read and write, kept OUTSIDE the repo.

NEVER push: state.db, .env, config.yaml, auth.json, message text, tokens.
Only derived numbers. See references/multi-machine-agent-relay.md §3, §7–§9.
"""
import argparse, base64, json, os, platform, re, shutil, socket, sqlite3
import subprocess, sys, time, urllib.error, urllib.request
from datetime import datetime, timedelta

DP = os.path.expanduser("~")            # e.g. C:\Users\User  or  /data/data/com.termux/files/home
BASE = os.path.join(DP, ".sofia")       # private config dir on the REMOTE machine


# ---------------------------------------------------------------- config/token
def load_config():
    cfg = {"repo": "",                  # "<owner>/<repo>" — owner fills this in
           "path": "status.json", "branch": "main", "hermes_home": "",
           "disk_alert_pct": 90.0, "ram_alert_pct": 92.0}
    p = os.path.join(BASE, "config.json")
    if os.path.isfile(p):
        try:
            with open(p, encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception as e:
            print("AMARAN: config.json: %s" % e, file=sys.stderr)
    return cfg


def load_token():
    t = os.environ.get("SOFIA_GH_TOKEN", "").strip()
    if t:
        return t
    p = os.path.join(BASE, "pat.txt")   # one line, no quotes, 0600 if posix
    if os.path.isfile(p):
        with open(p, encoding="utf-8") as f:
            return f.read().strip()
    return ""


# ------------------------------------------------------------------ host stats
def _run(cmd, timeout=12):
    try:
        return (subprocess.run(cmd, capture_output=True, text=True,
                               timeout=timeout).stdout or "").strip()
    except Exception:
        return ""


def os_label():
    if platform.system() == "Windows":
        return "Windows %s (%s)" % (platform.release(), platform.version())
    return "%s %s" % (platform.system(), platform.release())


def uptime_seconds():
    if platform.system() == "Windows":
        try:
            import ctypes
            return int(ctypes.windll.kernel32.GetTickCount64() // 1000)
        except Exception:
            return None
    try:
        with open("/proc/uptime") as f:
            return int(float(f.read().split()[0]))
    except Exception:
        return None


def cpu_percent():
    if platform.system() == "Windows":
        out = _run(["powershell", "-NoProfile", "-Command",
                    "(Get-CimInstance Win32_Processor | Measure-Object "
                    "-Property LoadPercentage -Average).Average"])
        try:                                  # multi-socket returns several lines
            vals = [float(x) for x in re.findall(r"-?\d+\.?\d*", out)]
            return round(sum(vals) / len(vals), 1) if vals else None
        except Exception:
            return None
    try:
        with open("/proc/loadavg") as f:
            l1 = float(f.read().split()[0])
        return round(min(100.0, l1 / (os.cpu_count() or 1) * 100.0), 1)
    except Exception:
        return None


def ram_info():
    if platform.system() == "Windows":
        try:
            import ctypes

            class MSX(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            st = MSX(); st.dwLength = ctypes.sizeof(MSX)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
                return None, None, None
            total = st.ullTotalPhys / (1024 ** 3)
            return round(st.dwMemoryLoad, 1), round((st.ullTotalPhys - st.ullAvailPhys) / (1024 ** 3), 2), round(total, 2)
        except Exception:
            return None, None, None
    try:
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":", 1)
                info[k.strip()] = float(v.strip().split()[0])
        total = info.get("MemTotal", 0) / (1024 ** 2)
        used = total - info.get("MemAvailable", info.get("MemFree", 0)) / (1024 ** 2)
        return round(used / total * 100, 1), round(used, 2), round(total, 2)
    except Exception:
        return None, None, None


def disks(alert_pct):
    out, alerts = [], []
    mounts = [l + ":\\" for l in "CDEFGH" if platform.system() == "Windows" and os.path.exists(l + ":\\")] \
        if platform.system() == "Windows" else ["/"]
    for m in mounts:
        try:
            u = shutil.disk_usage(m)
        except Exception:
            continue
        pct = round(u.used / u.total * 100, 1) if u.total else None
        out.append({"mount": m, "pct": pct, "free_gb": round(u.free / 1024 ** 3, 1),
                    "total_gb": round(u.total / 1024 ** 3, 1)})
        if pct is not None and pct >= alert_pct:
            alerts.append("disk %s %.0f%%" % (m, pct))
    return out, alerts


# --------------------------------------------------------------- hermes (read-only)
def find_hermes_home(cfg):
    if cfg.get("hermes_home"):
        p = os.path.expanduser(cfg["hermes_home"])
        return p if os.path.isdir(p) else None
    env = os.environ.get("HERMES_HOME", "").strip()
    if env and os.path.isdir(env):
        return env
    home = os.path.expanduser("~")
    calon = [os.path.join(home, n) for n in
             (os.listdir(home) if os.path.isdir(home) else []) if n.startswith(".hermes")]
    calon = [p for p in calon if os.path.isfile(os.path.join(p, "state.db"))]
    return max(calon, key=lambda p: os.path.getmtime(os.path.join(p, "state.db"))) if calon else None


def ro(path):
    return sqlite3.connect("file:%s?mode=ro" % path.replace("\\", "/"), uri=True, timeout=5)


def hermes_info(cfg, alerts):
    info = {"home": None, "gateway_alive": None, "sessions_today": None,
            "messages_today": None, "last_session": None, "cron_jobs": None, "last_cron": None}
    home = find_hermes_home(cfg)
    if not home:
        alerts.append("hermes home not found")
        return info
    info["home"] = home
    pidf, gstate = os.path.join(home, "gateway.pid"), os.path.join(home, "gateway_state.json")
    if os.path.isfile(pidf):
        try:
            pid = int(open(pidf, encoding="utf-8").read().split()[0])
            if platform.system() == "Windows":
                info["gateway_alive"] = str(pid) in _run(["tasklist", "/FI", "PID eq %d" % pid], timeout=10)
            else:
                os.kill(pid, 0); info["gateway_alive"] = True
        except Exception:
            info["gateway_alive"] = False
    if info["gateway_alive"] is None and os.path.isfile(gstate):
        info["gateway_alive"] = (time.time() - os.path.getmtime(gstate)) < 600

    db = os.path.join(home, "state.db")
    if not os.path.isfile(db):
        alerts.append("state.db missing")
        return info
    cutoff = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    try:
        c = ro(db)
        try:
            info["sessions_today"] = c.execute("select count(*) from sessions where started_at>=?", (cutoff,)).fetchone()[0]
            info["messages_today"] = c.execute("select count(*) from messages where timestamp>=?", (cutoff,)).fetchone()[0]
            row = c.execute("select title,last_activity_at from sessions "
                            "order by coalesce(last_activity_at,started_at) desc limit 1").fetchone()
            if row:
                info["last_session"] = {"title": (row[0] or "(untitled)")[:80],
                                        "ago_s": int(time.time() - float(row[1])) if row[1] else None}
        finally:
            c.close()
    except Exception as e:
        alerts.append("state.db unreadable: %s" % str(e)[:80])

    jobs = os.path.join(home, "cron", "jobs.json")
    if os.path.isfile(jobs):
        try:
            d = json.load(open(jobs, encoding="utf-8"))
            lst = d.get("jobs", d) if isinstance(d, dict) else d
            info["cron_jobs"] = len(lst) if hasattr(lst, "__len__") else None
        except Exception:
            pass
    ex = os.path.join(home, "cron", "executions.db")
    if os.path.isfile(ex):
        try:  # NOTE: columns are job_id/started_at/status — there is NO job_name
            c = ro(ex)
            try:
                r = c.execute("select job_id,started_at,status from executions "
                              "where started_at is not null order by started_at desc limit 1").fetchone()
                if r:
                    info["last_cron"] = {"name": (r[0] or "?")[:60],
                                         "ago_s": int(time.time() - float(r[1])) if r[1] else None,
                                         "status": r[2]}
            finally:
                c.close()
        except Exception:
            pass
    return info


def collect(cfg):
    alerts = []
    ram_pct, ram_used, ram_total = ram_info()
    dsk, dalerts = disks(float(cfg.get("disk_alert_pct", 90.0)))
    alerts += dalerts
    if ram_pct is not None and ram_pct >= float(cfg.get("ram_alert_pct", 92.0)):
        alerts.append("RAM %.0f%%" % ram_pct)
    h = hermes_info(cfg, alerts)
    last = (h.get("last_session") or {})
    if last.get("ago_s") and last["ago_s"] > 6 * 3600:
        alerts.append("no hermes activity > 6h")
    return {"schema": 1, "agent": "remote", "host": socket.gethostname(), "os": os_label(),
            "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
            "uptime_s": uptime_seconds(), "cpu_pct": cpu_percent(), "cores": os.cpu_count(),
            "ram_pct": ram_pct, "ram_used_gb": ram_used, "ram_total_gb": ram_total,
            "disks": dsk, "hermes": h, "alerts": alerts}


# ------------------------------------------------------------------------ push
def gh(url, method="GET", token=None, payload=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "remote-status/1")
    if token:
        req.add_header("Authorization", "Bearer %s" % token)
    body = None
    if payload is not None:
        body = json.dumps(payload).encode()
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, body, timeout=20) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            msg = e.read().decode()[:300]
        except Exception:
            msg = ""
        return e.code, {"error": msg}


def push(data, cfg, token):
    if not cfg.get("repo"):
        return {"ok": False, "why": "repo not set in config.json"}
    if not token:
        return {"ok": False, "why": "no token (env or pat.txt)"}
    api = "https://api.github.com/repos/%s/contents/%s" % (cfg["repo"], cfg.get("path", "status.json"))
    code, cur = gh("%s?ref=%s" % (api, cfg.get("branch", "main")), token=token)
    payload = {"message": "status %s %s" % (data["host"], data["ts"]),
               "content": base64.b64encode(json.dumps(data, ensure_ascii=False, indent=1).encode()).decode(),
               "branch": cfg.get("branch", "main")}
    if code == 200 and cur.get("sha"):
        payload["sha"] = cur["sha"]          # update existing file
    code, res = gh(api, "PUT", token=token, payload=payload)
    if code in (200, 201):
        return {"ok": True, "commit": (res.get("commit") or {}).get("sha", "")[:12]}
    return {"ok": False, "why": "HTTP %s %s" % (code, str(res.get("error", ""))[:160])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--print-config", action="store_true")
    a = ap.parse_args()
    cfg = load_config()
    if a.print_config:
        print(json.dumps({"config_file": os.path.join(BASE, "config.json"), "config": cfg,
                          "token_ada": bool(load_token()),
                          "hermes_home_dijumpai": find_hermes_home(cfg)}, indent=1, ensure_ascii=False))
        return 0
    data = collect(cfg)
    if a.out:
        json.dump(data, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if a.dry_run:
        print(json.dumps(data, ensure_ascii=False, indent=1))
        return 0
    hasil = push(data, cfg, load_token())
    print(json.dumps({"ts": data["ts"], "host": data["host"], "push": hasil,
                      "alerts": data["alerts"]}, ensure_ascii=False))
    return 0 if hasil.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())
