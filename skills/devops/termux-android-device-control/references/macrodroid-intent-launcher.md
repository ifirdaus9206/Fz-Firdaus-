# MacroDroid Intent Received launcher (Termux → app, no ADB)

Measured 2026-11-22, Xiaomi 25080RABDG, HyperOS 3 / Android 16, MacroDroid 6.1.5 (Play Store),
screen 1280×2772, accessibility granted after `Benarkan tetapan terhad`.

## Why this exists

`am start -n pkg/Activity` from Termux prints `Starting: Intent {...}`, exits 0, and the screen does
not change (background activity launch blocked; Termux has no overlay permission and HyperOS does not
expose one for it). `buka` (am start) therefore reports success without visible effect on this class
of device. MacroDroid holds accessibility and **can** bring apps to the front, so Termux broadcasts
and MacroDroid does the launch.

## Macro contract (one macro per app)

| Field | Value |
|---|---|
| Name | `BUKA <APP>` |
| Trigger | `Intent Diterima` / *Intent Received*, Action **exactly** `com.ketua.OPEN.<APP>` |
| Action | exactly one: **`Lancar Aplikasi`** → the app (row must read `Lancar <App>`) |
| Constraints | none |
| State | enabled (green toggle) |

Broadcast from Termux:

```bash
am broadcast -a com.ketua.OPEN.NOTES
am broadcast -a com.ketua.OPEN.CLAUDE
```

Verified: `OPEN.NOTES` opened Mi Notes repeatedly; after the action of that same macro was repointed
to Claude, the same broadcast opened Claude — proving delivery, trigger and launch all work, and
isolating any failure to the individual macro.

## AI prompt that MacroDroid's generator follows

```
Create ONE macro named "BUKA CLAUDE".
Trigger: Intent Received — Action equals exactly: com.ketua.OPEN.CLAUDE
Actions: exactly ONE action only — Launch Application, package: com.anthropic.claude
No constraints, no Run Macro, no UI Interaction, no Toast. Keep enabled.
```

Repair prompts when it misbehaves:

```
Delete every action except Launch Application (com.anthropic.claude). The macro must have exactly one action.
```
```
The Launch Application action has a null application. Set it to package com.miui.notes.
```

## Failure → cause table

| Symptom | Cause | Fix |
|---|---|---|
| Action row reads **`Lancar null`** | AI left the app unset | tap the row → pick the app → OK → Save |
| Manual "Uji" opens the app, broadcast does not | macro disabled, or trigger text differs | enable toggle; compare the action string character by character |
| Broadcast opens app A, never app B | macro B's trigger/toggle, not delivery | control test (below) |
| Nothing ever opens, even the known-good app | accessibility off / app hibernated | `Benarkan tetapan terhad`, then Tetapan → Apl → Bateri → Tanpa had |
| Tap action "succeeds" but nothing moves | `Interaksi UI` in **Piksel** mode with tiny X/Y (50,75 = top-left) | switch to `Peratusan`, or use real pixels for the 1280×2772 screen |
| Macro contains `Jalankan Makro → <itself>` | AI generator self-call replacing the real action | delete that row, add the real action |

## Control test (always do this before more guessing)

```bash
am broadcast -a com.ketua.OPEN.NOTES    # known-good macro, record the time
sleep 9
am broadcast -a com.ketua.OPEN.CLAUDE   # suspect macro, record the time
```
Ask which screens changed at each timestamp: control-only → suspect macro; both → working; neither →
activation/trigger, not the app.

## User-facing rules learned here

- One step per message; end with "balas **N siap**". Long multi-step lists get half-executed.
- The word **"test"** means: fire the broadcast immediately and print the timestamps.
- Apps open on the **phone screen**, not in the Telegram/PC chat window — say so explicitly, or the
  user reports "tiada apa-apa" while the app is standing open in front of them.
- Never trust "OK · exit 0"; only a screen change confirmed by the human counts.
