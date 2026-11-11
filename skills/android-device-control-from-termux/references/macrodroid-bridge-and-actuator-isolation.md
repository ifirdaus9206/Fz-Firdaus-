# MacroDroid as the free actuator bridge — and how to test it honestly

Measured 2026-11-11 on HyperOS 3 / Android 16, Play-signed Termux, ADB pairing blocked
("Disekat oleh penyedia kredit anda"). Goal: Ketua sends a signal from Termux → phone
vibrates / taps / screenshots.

## Vocabulary in the Malay MacroDroid UI

| Malay label on screen | English | What it does |
|---|---|---|
| `Pencetus` (red bar) | Trigger | WHEN the macro runs. Zero triggers = macro never runs. |
| `Tindakan` (blue bar) | Action | WHAT it does. |
| `Kekangan` (green bar) | Constraint | Extra AND-condition. **All** must be true or the macro is silently skipped. |
| `Tambah Tindakan` | Add Action | Category list: AI, Aplikasi, Fail, Interaksi Web, Kamera/Foto, Kelantangan, Kesambungan, Khusus MacroDroid, Lokasi, Makro, Media, Pemberitahuan, Pemboleh Ubah, … |
| `Tindakan Peranti` → `Getar` | Device Actions → Vibrate | The cheapest end-to-end test action. Scroll: it is **not** on the first screen of the category list. |
| `Kesambungan` → `Webhook (URL)` | Connectivity → Webhook | Premium feature; renders a **cloud** URL `https://trigger.macrodroid.com/<device-id>/<identifier>` when created (see A0). |
| `Pemberitahuan diterima` | Notification received | Free trigger. The app selector must be **`Termux:API`**, not `Termux`. |
| `Jalankan Makro: X` | Run Macro X | Chains to another macro — useless as an action if macro X has no actions of its own. |

Order of assembly: **trigger → action → (no constraints)**. Users build the action first
because `Tambah Tindakan` is the button they find; nothing can be tested until a trigger exists,
so say that before walking them through anything else.

## Two bridges

### A0. Cloud webhook facts (from the official wiki, macrodroidforum.com/wiki — read 2026-11-11)

Localhost `127.0.0.1:8080` is **not** what the app gives you any more. The `Webhook (URL)` trigger
renders a **cloud** URL:

```
https://trigger.macrodroid.com/[device-id]/[identifier]
# real example: https://trigger.macrodroid.com/49bca42b-0def-4597-b94d-03167897772b/hello world
```

- `device-id` is per install; it changes on reinstall / clear-data. `Export Device ID` /
  `Import Device ID` in the trigger screen preserve URLs across devices; `Generate New Device ID`
  invalidates every existing URL.
- `identifier` is any text the owner types (may contain **spaces** → percent-encode: `hello world`
  → `hello%20world`); it supports magic text. Several macros may share one identifier, so one call
  can fire them all.
- Delivery is a **Firebase Cloud Messaging push**: the phone needs Google Play services and
  internet, and must be online at call time. Devices without Play services are unsupported. A 200
  therefore means "queued", not "acted" — the phone can still be asleep, offline or the macro off.
- **Query parameters only set variables that already exist** (macro-local or global):
  `?myVar=42`, `?mydict(k)=v`. The webhook never creates a variable. So a design like
  `?act=tap&text=…` fails silently until `act`/`text` exist as variables; for arbitrary payloads
  enable `Save query parameters to dictionary` (read via `{webhook_query_params}`) or
  `Save body to string variable` (POST body, ≤3800 chars, JSON-parsable).
- Magic text available in the macro: `{webhook_caller_ip}`, `{webhook_query_params}`,
  `{webhook_url}`. Security options: IP whitelist, variable whitelist.
- **Design consequence:** prefer **one identifier per command** (`/ping`, `/shot`, `/tap`) — zero
  variables, zero dictionary setup. Reach for query params only when a command needs a payload.

### A1. Reading the HTTP answer — it *is* the diagnosis

| Answer | Meaning | Next move |
|---|---|---|
| `200` + JSON | (device-id, identifier) registered, push queued | if nothing happens: phone offline/asleep, macro disabled, no action, or a false constraint |
| `404 {"error":"Not found"}` | server answered; this identifier is **not registered for that device-id** | **not** a network fault and **not** a URL-encoding fault — see the ladder below |
| `000` | no HTTP answer at all (DNS/TLS/offline); only meaningful for a local mock | check connectivity |

Do **not** burn calls on identifier-variant guessing (`%20` vs `+` vs `_` vs no-space, case changes).
Tried once each on 2026-11-11 → identical 404 every time; the encoding was never the problem.

**404 ladder** (ask for one screenshot per rung; never guess twice):
1. macro **saved** (✓) — the URL is rendered client-side even for an unsaved macro, so having the
   URL proves nothing;
2. macro **enabled** — switch ON in the `Makro` list;
3. identifier text **matches exactly** (spacing/case) the text in the trigger's `Identifier` field;
4. macro has at least one `Tindakan` — an empty macro normally cannot be saved/enabled at all.

Honesty note: at hand-off on 2026-11-11 the 404 was **still open**; rungs 1–4 are the documented
order, not yet confirmed end-to-end on this device. Report it as "pelayan jawab 404 = belum
didaftar", then hand over the ladder — do not claim the bridge works.

### A2. Bridge script shape for a cloud URL (`~/phone_bridge/mdr.sh` v2)

```bash
BASE="https://trigger.macrodroid.com/<device-id>"      # in webhook.conf, with the real id
ID_PING="hello world"
urlenc() { python3 -c 'import sys,urllib.parse;print(urllib.parse.quote(sys.argv[1]))' "$1"; }
curl -sS -m 20 -w "\n[HTTP %{http_code}]\n" "$BASE/$(urlenc "$ID_PING")"
# commands: ping | raw "<identifier>" "?q=1" | list
```

Keep the mock (`mock_webhook.py` + `BASE=http://127.0.0.1:18080/trigger`) as the way to prove the
Termux half; `HTTP 000` against it means no listener, which is expected until it is started. Keep
both of these facts on the report: "Termux side OK (200 from mock)" and "cloud side 404".

### B. Notification (free)
```bash
termux-notification --title "KETUA-UJI-21:18:58" --content "Notifikasi ujian" \
                    --id 91 --priority high
```
Trigger: `Pemberitahuan diterima`, app = `Termux:API`.
The notification is posted by `com.termux.api`, so selecting the plain `Termux` app never matches —
this is the single most common reason "no vibration".

## Actuator isolation — the test that actually proves something

Two actuators in one test proves nothing:

- Termux:API can vibrate by itself (`termux-vibrate -d 800 -f`).
- MacroDroid can vibrate too.

If you fire both, the user feels a buzz and you cannot say which one did it. So:

1. **Round 1 — prove Termux:API is alive:** `termux-battery-status` (real JSON = the API app is
   installed and answering), then `termux-vibrate -d 800 -f`. Ask the user to confirm the buzz.
2. **Round 2 — prove MacroDroid fires:** send **only** `termux-notification`, with **no**
   `termux-vibrate` in the same command. Any vibration now belongs to MacroDroid.
3. Make the signal identifiable: put the wall clock in the title (`KETUA-UJI-<HH:MM:SS>`) and use a
   fresh `--id` each round, so the user can match "the one that just appeared".

State which actuator was suppressed in the report. "Aku sengaja tak hantar getar" is what turns a
buzz into evidence.

## Probe for a listener without `ss` / `netstat`

Neither exists on this Termux install. Per-port `curl` with the status code is enough:

```bash
for p in 18080 8080 8787; do
  curl -s -m 2 -o /dev/null -w "$p -> %{http_code}\n" http://127.0.0.1:$p/
done      # 000 = nothing listening, 200 = something answers
```

## Constraint trap (silent, total)

A `Kekangan` of type `Alamat IP` whose value is `127.0.0.1:18080{model}{mode}` (looks like a pasted
template) can never be true for the device's own IP → the macro is skipped every time, with no
error, no toast, nothing. Green bar with anything in it is a suspect: read it out loud to the user,
then tell them to delete it before any further test.

## What a good report looks like for this user

- Paste the commands and their real output (exit codes, HTTP codes, JSON) — never "dah diuji".
- Separate the two layers explicitly: "Termux → telefon" (proven) vs "MacroDroid → telefon"
  (pending).
- Plain Malay, one tap per numbered line, name the visible button label rather than a shell command.
- End with 3–4 numbered choices and let them answer by number.
