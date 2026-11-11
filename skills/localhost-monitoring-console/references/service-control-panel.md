# Service control panel + APK one-tap handoff

Measured 2026-11-11 on Xiaomi 25080RABDG / HyperOS (Android 16), Termux (Play build), console at
`127.0.0.1:8787` supervised by runit as `hermes-console`. Everything below was exercised live:
`sv status`, `POST /api/svc/...` restart drill, 21-check smoke test, 10/10 SVG text check.

---

## 1. Backend — whitelisted `sv` control

```python
PREFIX_DIR = Path(os.environ.get("PREFIX") or "/data/data/com.termux/files/usr")
SVDIR = PREFIX_DIR / "var" / "service"
SVC_ALLOW = {
    "hermes-console": ("Konsol 8787", Path.home() / ".hermes20/logs/hermes-console/current"),
    "hermes-gateway": ("Gateway Telegram", None),
    "web-server":     ("AINA live 8081 (lama, sengaja mati)", Path.home() / ".web-server.log"),
}
SVC_ACTIONS = {"up", "down", "restart", "status"}

def _sv(*args, timeout: int = 25):
    exe = shutil.which("sv") or str(PREFIX_DIR / "bin" / "sv")
    return subprocess.run([exe, *args], capture_output=True, text=True, timeout=timeout)
```

`_svc_one(name)` parses one status line:

| field | source |
|---|---|
| `state` | first token of `sv status` output → `run` / `down` / `fail` / `finish` |
| `pid` | `\(pid (\d+)\)` |
| `seconds` | `\)\s*(\d+)s` (run lines) **or** `:\s*(\d+)s` (down lines) |
| `has_down_file` | `(SVDIR/name/"down").exists()` — the difference between "down now" and "stays down" |
| `log_bytes` | `stat().st_size` of the log the service itself writes |

Endpoint shapes:

```python
@app.get("/api/svc")                      # {"services":[...], "svdir": "..."}
@app.post("/api/svc/{name}")              # {"action": "up|down|restart|status"}
@app.get("/api/svc/{name}/log?lines=80")  # {"file","bytes","lines":[...]}
```

Reject unknown names with 400 and list the allowed ones in the message (`"hanya: hermes-console,
hermes-gateway, web-server"`). Do not accept a path, a unit file, or arbitrary `sv` arguments.

### The deferred-restart rule (the one that bites)

`sv restart hermes-console` issued *from inside* `hermes-console` kills the process before uvicorn
flushes the response → the browser reports a failure for a restart that actually worked.

```python
def _sv_later(action: str, name: str) -> None:
    time.sleep(0.8)
    try: _sv(action, name)
    except Exception: pass

@app.post("/api/svc/{name}")
def api_svc_action(name: str, payload: dict = Body(default={}), bg: BackgroundTasks = None):
    ...
    if name == "hermes-console" and action in ("restart", "down") and bg is not None:
        bg.add_task(_sv_later, action, name)
        return {"ok": True, "deferred": True, "status": _svc_one(name)}
    ...
```

Measured drill: `pid 27591` → response `{"ok":true,"deferred":true}` → new pid `27987`, `ping 200`
after ~10 s. The downtime is real (port released, then re-bound), so the panel text says
"**MULA SEMULA ambil ~10 saat — muat semula halaman selepas itu**". Immediately after the response
`sv status` briefly prints `run: … got TERM`; that is shutdown, not a crash.

`down` on the console's own service is a one-way door from the UI's perspective — the panel must say
so and name the terminal command that brings it back (`sv up hermes-console`). Confirm in JS:

```js
if (act === "down" && !confirm(`Matikan servis ${name}? Konsol 8787 akan berhenti serta-merta.`)) return;
```

## 2. Frontend

Rows are `.svc-row` (label + state `tag` + `pid/uptime/log` hint on one line, four buttons on the
other, `flex-wrap` so it survives a 360 px phone). Buttons carry `data-svc` + `data-act`; one
delegated handler calls `svcGo(name, act, btn)`, which disables the button, POSTs, `toast()`s
`name: act → state`, prints the raw `sv` output into a `<pre class="log">`, then re-renders. `LOG`
is a GET into the same `<pre>` with the file path and byte size in the header line.

The panel is useless if the user cannot find it: place it **above** the read-only panels of the
tab, and mention the tab name in the chat reply.

## 3. Termux:Boot — status + one-tap install

```python
BOOT_PKG = "com.termux.boot"
BOOT_APK = Path.home() / "storage" / "downloads" / "TermuxBoot.apk"

def _pkg_installed(pkg: str) -> bool:
    r = subprocess.run(["pm", "list", "packages", pkg], capture_output=True, text=True, timeout=25)
    return f"package:{pkg}" in (r.stdout or "")
```

`GET /api/device/boot` → `{package, installed, apk{path,bytes,mtime}, boot_dir, boot_scripts[],
checked_at, note}`. `boot_scripts` comes from listing `~/.termux/boot/`; it is **not** proof the app
exists — measured: folder had `10-hermes-gateway.sh` while `installed` was `false`.

`POST /api/device/boot-install` tries two intents, records both outcomes, then re-reads status:

```python
tries = [["termux-open", "--content-type", "application/vnd.android.package-archive", str(BOOT_APK)],
         ["am", "start", "-a", "android.intent.action.VIEW",
          "-d", f"file://{BOOT_APK}", "-t", "application/vnd.android.package-archive"]]
```

Both returned `exit 0` and `Starting: Intent { … }` while `installed` stayed `false` — an exit code is
not a UI action. Deliverable is therefore: APK present, intent fired, 3 illustrated steps, and an
honest sentence — *"Android tak benarkan Termux pasang senyap; tekan PASANG sekali, kemudian buka app
Termux:Boot sekali"*. Only `pm list packages com.termux.boot` flips the chip to TERPASANG.

## 4. Smoke-test extensions

`tools/uji_konsol.sh` grew from 10 to 21 checks; each is one `[LULUS]/[GAGAL]` line and the exit code
is the failure count:

```bash
SVC=$(curl -s -m 8 "$URL/api/svc")
printf '%s' "$SVC" | grep -q '"name":"hermes-console"'          # service listed
for pid in panel-svc panel-boot panel-adb-guide; do             # panels in the HTML
  printf '%s' "$HOME_HTML" | grep -q "$pid"
done
for f in boot-01-fail boot-02-install boot-03-selesai adb-01-pembangun adb-02-wayarles adb-03-kod; do
  curl -s -o /dev/null -w '%{http_code}:%{size_download}' "$URL/static/img/panduan/$f.svg"
done
B=$(curl -s -m 8 "$URL/api/device/boot"); printf '%s' "$B" | grep -q '"apk"'
```

Termux traps hit while writing it:

- `curl -o /tmp/ping.$$` fails (`/tmp` unwritable) and the `|| echo 000` fallback concatenates with
  `-w %{http_code}` → `code=200000`, body empty → a healthy endpoint reported GAGAL. Use
  `TMPF=$(mktemp "${TMPDIR:-$HOME}/uji.XXXXXX")`.
- POST endpoints need the CSRF header: `TOK=$(curl -s $URL/api/meta | … .csrf)` then
  `-H "X-Console-Token: $TOK"`. Without it every action returns
  `{"error":"token konsol tiada atau salah"}` and looks broken.

## 5. What is honestly left for the user

| Item | Why it cannot be automated |
|---|---|
| One PASANG tap + open the app | Termux declares no `REQUEST_INSTALL_PACKAGES`; `file://` APK URIs blocked since Android 7 |
| ADB pairing code | Android generates a 6-digit code valid ~2 min; reading it needs ADB (circular) |

Both are answered with illustrated steps + a form, never with a shell command the user has to find.
