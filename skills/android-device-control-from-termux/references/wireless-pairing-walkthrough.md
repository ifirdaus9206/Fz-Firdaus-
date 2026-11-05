# Wireless ADB pairing — user-facing walkthrough (Settings → done)

Use when a non-technical user says "terangkan satu persatu dari tetapan sampai siap" or "aku pun
tak faham". Verified on MIUI/Android 16, Termux, android-tools 35.0.2; console form path verified
on `~/hermes-console` (Flask) `/api/device/adb-pair`.

## The one idea that unblocks everything

Two different `IP:port` values exist. Say this BEFORE the steps; users conflate them and then
report "tak jadi" without knowing which field was wrong.

| Value | Where it appears | Used by | Field in console form |
|---|---|---|---|
| **A** `ip:port` on the main *Wireless debugging* screen (e.g. `192.168.0.55:37123`) | main screen | `adb connect` | `adb-conn` (label "IP:port connect (pilihan)") |
| **B** `ip:port` + 6-digit code inside the *Pair device with pairing code* dialog (e.g. `192.168.0.55:40567`) | pairing dialog | `adb pair` | `adb-host` + `adb-code` |

Ports A and B are always different. The code is single-use and expires in minutes; the dialog
closes when the user leaves that screen. Say "jangan tutup dialog" explicitly.

## Phone side (the other person's phone) — 11 numbered taps

1. Join the **same Wi-Fi** as the agent's phone (not mobile data, not guest SSID).
2. Open **Tetapan / Settings**.
3. Scroll → **Tentang telefon** (About phone).
4. Find **"Versi MIUI"** (Xiaomi/Redmi) or **"Nombor binaan"** (AOSP; Samsung: Software information → Build number).
5. **Tap it 7 times** → "Anda kini seorang pembangun". May ask for the lock PIN.
6. Back → **Tetapan tambahan** (Additional settings) → **Pilihan pembangun** (Developer options).
7. Turn on **Nyahpepijat wayarles** (Wireless debugging) → **Benarkan / Allow**.
8. Note **IP address & Port** on that screen → value **A**.
9. Tap **"Pasangkan peranti dengan kod"** (Pair device with pairing code).
10. Dialog shows 6-digit code + IP:port → both are value **B**. Note them.
11. Keep the dialog open until the web form has been submitted.

The agent cannot read another person's screen (no root, no adb yet) — these values must be relayed
by a human. Do not offer to "detect" them.

## Console side (fields confirmed in `~/hermes-console`)

`http://127.0.0.1:8787` → top-bar button **ADB** (or tab **SISTEM** → panel **PASANG ADB WAYARLES**):

- `#adb-host` → value **B** (`ip:pair_port`)
- `#adb-code` → the 6 digits
- `#adb-conn` → value **A** (`ip:connect_port`)
- `#adb-go` = **PASANGKAN**; log renders into `#adb-log`.

Success markers in the log: `Successfully paired to …` then `connected to …`; the status tag turns
green `ADB: ip:port`. Then `adb devices` lists the device. Documented output goes to
`~/hermes-console/DEVICE.md`.

## Failure → cause table (give this, not "cuba lagi")

| Log line | Cause | Action |
|---|---|---|
| `failed to pair` / `wrong password` | code expired or was mistyped | reopen the pairing dialog, take a fresh code |
| `failed to connect` / timeout | different network, guest SSID / AP isolation, phone hotspot off | same Wi-Fi, no client isolation |
| `error: unknown host service 'mdns:services'` | android-tools 35.0.2 has no mdns | read port A off the screen and pass it explicitly |
| pairs OK but `adb devices` empty | connect port missing/wrong (value A vs B swap) | retry with value A, or `adb disconnect` then connect |
| port changed after toggling wireless debugging | Android reassigns ports | re-read both values |

## Delivery rules (this user)

- Malay, plain wording, one action per numbered line, no jargon ("SSID", "daemon", "adbd" → avoid).
- Split into **Bahagian 1 = their phone**, **Bahagian 2 = this phone/console**; never interleave.
- Point at a visible control (button label / tab name), not a shell command.
- Save the same walkthrough to a file (`~/hermes-console/PANDUAN-ADB.md`) and name the path in the
  chat reply, so the steps survive the chat scroll.
- End with the verification evidence you will produce (`adb devices`, green tag), not an assurance.
