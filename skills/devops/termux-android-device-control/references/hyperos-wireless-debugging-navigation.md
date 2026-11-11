# Reaching wireless-debugging pairing on HyperOS (Malay UI) — navigation map + human protocol

Verified against REDMI Note 15 Pro 5G (Xiaomi 25080RABDG), HyperOS 3, Android 16
(`Versi OS 3.0.304.0.WPPMIDC.C07`, `Versi Android 16 / BP2A.250605.031.A3`), locale Bahasa Melayu,
Termux from Play, no root, adb not yet paired.

## 1. The screen the user *thinks* is wireless debugging

`Tetapan` → `Kesalinghubungan` → **`Lebih banyak pilihan sambungan`** contains an **OTG** toggle plus
NFC, Pencetakan, Pautan ke Windows, Paparan wayarles. Users tap the OTG row, see a switch flip, and
report "Nyahpepijat wayarles cuma buka tutup". Tapping the *label* of a SwitchPreference on HyperOS
toggles it — it does not open a sub-screen, so "tap the text, not the switch" is not a fix there.

Telltale: the page has **no ⋮** and no `Nama peranti` / `Peranti berpasangan` rows.

## 2. The real blocker: Developer options are off

`Tetapan` scrolled to the very bottom ends at `Perkhidmatan Google` → `Tetapan tambahan` → `Privasi` →
`Lokasi` → `Maklum balas`. **No `Pilihan pembangun` row** = never enabled, and every wireless-debugging
surface (toggle row, pairing dialog, 3-dot menu) is hidden with it.

Enable path: `Tetapan` → **`Mengenai telefon`** → tap **`Versi OS`** (the row showing
`3.0.304.0.WPPMIDC.C07`) **7×** → confirm lock-screen PIN → `Pilihan pembangun` appears near the
bottom of `Tetapan`. On HyperOS the version row is `Versi OS`, not `Versi MIUI` / `Nombor binaan`
(those exist only as extra rows on some builds).

Dead end seen in the wild: `Pentadbir peranti` (device-admin) page for "Telecoms Client" — its
"Nyahtifkan" button is greyed out. Nothing to do there; `Batal` / ← and continue.

## 3. Malay ↔ English label map (for instructions)

| Malay | English |
|---|---|
| Tetapan | Settings |
| Mengenai telefon | About phone |
| Versi OS / Versi Android | OS version / Android version |
| Pilihan pembangun | Developer options |
| Nyahpepijat wayarles | Wireless debugging |
| Pasangkan peranti dengan kod | Pair device with pairing code |
| Peranti berpasangan | Paired devices |
| Nama peranti | Device name |
| Tetapan tambahan | Additional settings |
| Lebih banyak pilihan sambungan | More connection options |
| Pentadbir peranti | Device admin apps |
| Log penyahpepijat | Bug report / debug log |

## 4. What the agent can and cannot do here

- Cannot open the screen for them: `am start -a android.settings.APPLICATION_DEVELOPMENT_SETTINGS` and
  `-n com.android.settings/.Settings$DevelopmentSettingsActivity` both print `Starting: Intent {...}`
  with no error while Termux is backgrounded, and the phone keeps showing the old page (background
  activity start blocked, Android 10+). Ask the user to foreground Termux first if you want to retry.
- Cannot read the screen: `screencap` → "Capturing failed" until adb is paired.
- Cannot read the code: it is rendered only in the dialog. Human reads, agent pairs.

## 5. Protocol that worked for a non-technical user

1. **One step per reply.** State the step number, the exact label to tap, and what should appear.
2. **Ask for a screenshot after every step** (power + volume-down) and read it before the next step;
   two of five screenshots showed the user was somewhere else entirely than they described.
3. **Identify the screen by its title**, not by what the user claims. Report the title back
   ("ini skrin *Lebih banyak pilihan sambungan*, bukan Nyahpepijat wayarles").
4. **Annotate the target row** instead of describing it. Crop-free PIL pass on the screenshot just
   received, red box + arrow on the row, send as `MEDIA:/path.png`:
   ```python
   from PIL import Image, ImageDraw
   im = Image.open(src).convert("RGB"); d = ImageDraw.Draw(im)
   d.rectangle([16, 472, 575, 552], outline=(255, 0, 0), width=8)
   d.line([(300, 600), (300, 565)], fill=(255, 0, 0), width=10)
   d.polygon([(285, 570), (315, 570), (300, 550)], fill=(255, 0, 0)])
   im.save("/data/data/com.termux/files/home/.hermes20/cache/target.png")
   ```
   Read pixel coordinates off the received screenshot's real size (`Image.open(p).size`); the chat
   preview is scaled, so never guess.
5. Tell them the code expires in ~2 minutes and ask for code **and** pairing port in one message.

## 6. Terminal case: the phone is financing-locked — ADB is impossible

Observed on the same REDMI Note 15 Pro 5G after tapping `Versi OS` 7×: a modal with a padlock icon
and the title **`Disekat oleh penyedia kredit anda`** ("Blocked by your credit provider"), buttons
`Tutup` and `Ketahui lebih lanjut`. Nothing happens to developer options, ever.

Meaning: the handset is a **subsidised / instalment unit** and the credit provider (telco or
financier) enforces a device-owner policy that disables Developer options. Consequences, in order:

- No `Pilihan pembangun` → no `Nyahpepijat wayarles` → no pairing code → **no ADB**, no `input tap`,
  no `screencap`, no `uiautomator`. Every Recipe 4 helper is unusable on this device.
- Stop the whole navigation ladder the moment that dialog appears. Do not hunt for another toggle,
  another menu, or a hidden activity — it is a policy, not a UI bug.
- The only legitimate unlock is the provider releasing the IMEI (contract settled / device paid off).
  Never attempt a bypass; it is the owner's lock, it is a legal matter, and it cannot succeed without
  root anyway. Say this plainly and offer to draft the request message instead.
- `Pentadbir peranti → Telecoms Client` with a greyed `Nyahtifkan` is a **red herring** — a normal
  system component. Correct the user when they blame it (this session: they concluded "my monthly
  line is the cause" from that screen).

### What is still possible without developer options

Accessibility-based automation (MacroDroid / Automate / Easer) needs no Developer options: the user
enables the app's accessibility service, and MacroDroid's **Webhook (URL)** trigger (its own HTTP
server, e.g. `http://127.0.0.1:8080`) can be fired from Termux with `curl`, with **UI Interaction**
actions clicking by text. Verified prerequisites only: `localhost` HTTP round-trip from Termux works,
Termux cannot install APKs itself (`aapt dump permissions` on com.termux → 0 `INSTALL_PACKAGES`),
f-droid.org reachable while apkmirror answers 403 on this network. The macro chain itself was **not**
proven end-to-end — present it as a costed experiment (the human builds every macro by tapping), not
as a solution.
