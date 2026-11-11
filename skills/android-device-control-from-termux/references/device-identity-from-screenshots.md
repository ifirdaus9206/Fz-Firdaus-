# Device identity from the user's own screenshots

When ADB is not yet paired the agent is blind — but the user can hand over evidence. Two screens
carry almost everything needed to continue:

| Screen | Gives | Use it for |
|---|---|---|
| Seting › Perihal telefon | model, OS build, Android version, kernel, storage | confirming which phone the guides are for; deciding menu wording |
| Seting › Status | model name, **Wi-Fi IPv4 address**, IPv6 link-local, MAC, BT, uptime | pre-filling the ADB pairing form |

Measured 2026-11-11 (HyperOS / Android 16, Redmi Note 15 Pro 5G):

- model number `25080RABDG` + "REDMI Note 15 Pro 5G" + MediaTek Dimensity 7400-Ultra — the user had
  named the phone verbally, the screenshot proved it, and the schematic guides could then be labelled
  with the real model instead of a generic "HyperOS".
- IP `192.168.0.8` from the Status screen was written straight into the console form as
  `value="192.168.0.8:"`, so the user only had to add the pairing **port** and the 6-digit code.

## Rules

1. **Quote only model + IP back.** The same screens contain IMEI (both slots), EID, MAC and BT
   address. State that they were visible and deliberately **not recorded** — never copy them into
   chat, logs, DEVICE.md, or a report.
2. **Pre-fill, don't ask twice.** If the IP is known, ship it as the input's `value` (placeholders are
   invisible once typed over). Remaining unknowns: pairing **port** (changes every time the dialog is
   opened) and the 6-digit code (~2 min TTL).
3. **Screenshots can arrive degraded.** In one session every portrait screenshot came back with
   long repeated lines (`feb6b:920c…`, `MediaTek Dimensity 7400-Ultra` ×N) while the key fields stayed
   readable. Say what you can read, name the corruption, and offer to re-read if exact strings matter —
   do not invent a value you could not see.
4. **Persist the evidence.** Copy the screenshot into the console gallery (`data/steps/`) with a
   caption naming the phone, then verify it serves (`GET /api/steps/<id>/file` → `200 image/jpeg`).
   A saved screenshot is also the artefact that settles "which model are these guides for?" later.
5. **`ip -4 addr show wlan0` / `ifconfig wlan0` may return nothing** for the Termux app uid on
   HyperOS. When both are empty, take the address from the screenshot or the pairing dialog instead of
   promising the shell will find it.
