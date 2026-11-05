# UI discoverability + ADB pairing from the console

Session-tested patterns for the moment a console feature exists but the user cannot find it, and
for the physical step (APK install) that only ADB can complete.

## 1. Symptom

The panel was built, served, and present in the HTML (`curl / | grep -c "PASANG ADB"` → 1), static
assets were `cache-control: no-store`, yet the user reported *"aku tak jumpa"* / *"ada cara lain ke"*
repeatedly. Cause: it lived in the **last tab** (`SISTEM`), while the user was looking at `PANDUAN`
(which only carried a note pointing elsewhere). Nothing was broken — it was unfindable.

Rule: a form the user must operate needs a named entry point in the reply, not just a tab.

## 2. Deep link

```js
// after the default assignment, never before
S.tab = S.pendingHome ? "pusat" : (S.meta.default_tab || "pusat");
const qsTab = new URLSearchParams(location.search).get("tab")
           || (location.hash || "").replace("#", "");
if (qsTab && TABS.some(([k]) => k === qsTab)) S.tab = qsTab;
...
setTab(S.tab);   // not loadTab(): this also fixes the .active class on tab buttons
```

Then the reply can say: `http://127.0.0.1:8787/?tab=system`.

## 3. Header quick-jump

```html
<div class="brand">
  <span class="dot" id="livedot"></span>
  <span class="logo">HERMES<span class="ac">CONSOLE</span></span>
  <span class="ver" id="ver">v1.0</span>
  <button class="btn" id="quick-adb" title="Terus ke borang pasang ADB">ADB</button>
</div>
```

```js
$("#quick-adb").addEventListener("click", () => {
  setTab("system");
  const el = $("#adb-host");
  if (el) { el.scrollIntoView({ behavior: "smooth", block: "center" }); el.focus(); }
});
```

Check after editing: exactly one element per id (`grep -c 'id="clock"' static/index.html`).

## 4. Status endpoint with an explicit caveat

```python
@app.get("/api/device/status")
def api_device_status():
    return device_status()
# {checked_at, fdroid:{installed,package}, apk:{path,exists,bytes,mtime,sha256},
#  termux_api:{cli,working}, adb:{binary,devices[]},
#  caveat: "pm list ditapis oleh Android package-visibility; ..."}
```

`installed:false` from `pm list` is **not** proof of absence (visibility filtering). Ship the caveat
string with the payload so the UI never asserts a false negative; confirm via the app drawer or ADB.

## 5. Pair from the browser

```python
@app.post("/api/device/adb-pair")
def api_adb_pair(payload: dict = Body(...)):
    host = (payload.get("host") or "").strip()      # 192.168.0.11:37123
    code = str(payload.get("code") or "").strip()   # 6 digits from Android
    conn = (payload.get("connect") or "").strip()
    if not re.fullmatch(r"[0-9a-zA-Z][0-9a-zA-Z.\-]*:\d{2,5}", host):
        raise HTTPException(400, "IP:port tidak sah (contoh 192.168.1.7:37123)")
    if not re.fullmatch(r"\d{6}", code):
        raise HTTPException(400, "kod mesti 6 digit")
    out = []
    p = subprocess.run(["adb", "pair", host], input=code + "\n",
                       capture_output=True, text=True, timeout=90)
    out.append({"step": f"adb pair {host}", "out": (p.stdout + p.stderr).strip()[:800]})
    if not conn:                       # some adb builds: `adb mdns services` -> unknown host service
        conn = f"{host.split(':')[0]}:5555"
    c = subprocess.run(["adb", "connect", conn], capture_output=True, text=True, timeout=45)
    out.append({"step": f"adb connect {conn}", "out": (c.stdout + c.stderr).strip()[:400]})
    devs = _adb_devices()
    return {"ok": bool(devs), "devices": devs, "connect": conn, "log": out}
```

UI: three inputs (host, code, optional connect port) + a mono log pane printing `log[].step/out`.
Tell the user, in the same message, that the phone's IP is on the pairing screen and can also be
read from the shell with `ifconfig wlan0 | grep "inet "`.

## 6. Screenshot into the guided steps

```python
@app.post("/api/device/shot")
def api_device_shot(payload: dict = Body(default={})):
    devs = _adb_devices()
    if not devs:
        raise HTTPException(400, "tiada peranti adb — pasangkan dahulu (borang ADB)")
    p = subprocess.run(["adb", "exec-out", "screencap", "-p"], capture_output=True, timeout=60)
    raw = p.stdout or b""
    if len(raw) < 2000 or raw[:4] != b"\x89PNG":
        raise HTTPException(500, "screencap tidak pulang PNG yang sah")
    ...  # save to data/steps/<id>.png and append to steps.json with order = max+1
```

Each capture becomes step N+1 in the `PANDUAN` tab, so "what is on the screen now" is documented by
the artifact itself instead of being asserted in chat.

## 7. Verification actually used

```bash
curl -s -o /dev/null -w "%{http_code}\n" "http://127.0.0.1:8787/?tab=system"   # 200
curl -s -X POST -H "Content-Type: application/json" -H "X-Console-Token: $T" \
     -d '{"host":"abc","code":"701862"}' http://127.0.0.1:8787/api/device/adb-pair
# -> 400 IP:port tidak sah (validation path)
curl -s -X POST -H "X-Console-Token: $T" -d '{}' http://127.0.0.1:8787/api/device/shot
# -> 400 tiada peranti adb — pasangkan dahulu
node tools/render_test.js | grep -E "PANDUAN|GAGAL"
```

Wrap these in separate short commands; long compound pipelines can be rejected by the command parser.

## 8. Wording that stopped the confusion

- "Console tiada log masuk. 701862 bukan kata laluan — ia **kod pasangan ADB**."
- "IP ada pada skrin yang sama: baris *IP address & Port*; port untuk connect muncul di baris kedua
  selepas pairing."
- Always end with the one physical action + the exact URL that opens the form.
