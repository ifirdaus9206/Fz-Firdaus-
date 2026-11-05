# Guided steps + device status — when the user must do the physical bit

Use this when the console's job becomes *"tell me exactly where to tap"*: installing an APK,
granting a permission, pairing ADB, anything the agent provably cannot do from the sandbox.
The user's words: *"aku cari tak jumpa di mana"*, *"hantar screenshots satu per satu di sana"*.

Pattern: a **PANDUAN** tab that (a) proves current state, (b) shows numbered illustrated steps,
(c) accepts the user's own screenshots as new steps, in order.

## 1. Prove state first — `/api/device/status`

One endpoint, cheap, read-only, returns a verdict plus the caveat that keeps it honest:

```python
@app.get("/api/device/status")
def api_device_status():
    return {
      "checked_at": now_iso(),
      "fdroid":   {"installed": "package:org.fdroid.fdroid" in pm_list(), "package": "org.fdroid.fdroid"},
      "apk":      {"path": "~/storage/downloads/F-Droid.apk", "exists": True,
                   "bytes": 12569951, "mtime": "...", "sha256": "19d51fad…7b52"},
      "termux_api": {"cli": bool(shutil.which("termux-battery-status")), "working": battery_json_ok},
      "adb":      {"binary": bool(shutil.which("adb")), "devices": adb_devices()},
      "caveat":   "pm list ditapis oleh Android package-visibility; kalau app baharu tak muncul, "
                  "sahkan melalui app drawer atau ADB sebagai shell.",
    }
```

Rules:
- `pm list packages` (captured via `subprocess.run`, never shell-joined) is the fast check, but
  **package visibility makes a false negative possible** — the caveat text ships with the verdict.
- Include the APK `sha256` in the payload and show a truncated copy in the UI: the user can compare
  it with the checksum you quoted earlier, which is how "same file" becomes verifiable.
- Do not shell out to `termux-battery-status` on every poll; the status endpoint is called on tab
  open, not by the SSE loop.

## 2. Illustrated steps — generate, seed, serve

Generate diagrams with Pillow in the console's own palette (dark `#070c0b`, panel `#0c1613`,
accent `#5ee3a1`, gold `#f0b429`), 1000×620, phone frame + list rows + highlighted target row +
arrow + `tekan sini` tag. Store at `static/img/steps/stepN-*.png`.

```python
SEED_STEPS = [("step1-files.png",  "Buka app Files, kemudian folder Download"),
              ("step2-apk.png",    "Cari fail F-Droid.apk (12.6 MB) dalam Download"),
              ("step3-install.png","Tekan Install pada dialog Android"),
              ("step4-allow.png",  "Jika disekat: benarkan 'Pasang apl tidak diketahui' untuk Files")]

def _steps_seed():                      # called once at startup, idempotent by seed filename
    items = _steps_load()
    have = {i.get("seed") for i in items}
    for idx, (fn, cap) in enumerate(SEED_STEPS, 1):
        if fn in have: continue
        copy(static/img/steps/fn -> data/steps/seedN.png)
        items.append({"id": f"seed{idx}", "seed": fn, "caption": cap, "order": idx, ...})
```

API: `GET /api/steps` (sorted by `order`), `POST /api/steps` (JSON + `content_b64`, ≤8 MB,
`order = max+1`), `GET /api/steps/<id>/file` (`FileResponse`, id regex-validated).
Storage `data/steps/{images,steps.json}`.

UI: `figure.stepcard` grid (`repeat(auto-fill, minmax(300px, 1fr))`), absolute `stepnum` badge,
`<a href=url target=_blank><img loading=lazy></a>` so any step can be opened full-size, caption +
timestamp in `figcaption`. Upload form = file input + caption + one button; on success reload the
grid so the new step appears at the end.

## 3. The user's screenshots ARE steps

The upload form is the two-way part: after each physical tap the user sends a screenshot and it
becomes step N+1 with their caption. That turns the pane into a shared, ordered log of the
procedure instead of a chat scroll. Tag rows with `source: "panduan" | "pengguna"` so you can tell
generated illustrations from evidence.

## Pitfalls (both hit for real)

- **Emoji/arrow glyphs render as tofu.** `ImageFont.truetype("/system/fonts/Roboto-Regular.ttf")`
  has no emoji: `📁`, `⬇️`, `→` come out as boxes, and a title with `→` looks broken. Use drawn
  shapes (rounded letter tiles: `d.rounded_rectangle(...)`, letter centred) and words instead of
  arrows; then **look at the PNG** with `vision_analyze` before shipping.
- **Don't call `save()` from inside the draw function.** `def s1(d): ...; save("step1.png", s1)`
  plus `for fn in (s1, s2): save(name, fn)` is infinite recursion (save calls the drawer, which
  calls save). Drawers must only draw; a single loop at the bottom saves.
- **Seed once, keyed on the seed filename**, or every restart appends duplicate steps and the
  ordering balloons.
- **Say what the status endpoint cannot see.** "Termux reports TIADA, but visibility filtering can
  hide a package; open the app drawer to confirm, or pair ADB and let `adb shell pm list` answer."
  Presenting a filtered list as ground truth is how you tell a user their installed app is missing.

## Verification

```bash
curl -s localhost:8787/api/device/status | python3 -m json.tool | head -20
curl -s localhost:8787/api/steps | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["count"])'
for i in 1 2 3 4; do curl -s -o /dev/null -w "seed$i %{http_code} %{size_download}b\n" \
  "localhost:8787/api/steps/seed$i/file"; done
```
Add two render checks: `#pd-status` contains the package name, and `#pd-steps` contains ≥N
`stepcard` occurrences — otherwise a broken tab looks identical to an empty one.
