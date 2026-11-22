# MacroDroid as launcher: `Intent Diterima` → `Lancar Aplikasi` (verified)

Purpose: move the phone screen when `am start` cannot (Android 10+ background activity launch
blocks third-party apps started by Termux). Termux sends a broadcast; MacroDroid does the launch
through its accessibility service.

## Verified result

Measured 2026-11-22, HyperOS 3 / Android 16, Play-signed Termux, MacroDroid 6.1.5 (Malay UI):

| Step | Result |
|---|---|
| `buka notes` → `am start -n com.miui.notes/…SnsEditActivity` | `OK · exit 0`, screen stayed on Chrome |
| macro `BUKA NOTA` = `Intent Diterima com.ketua.OPEN.NOTES` + `Lancar Nota` | **Notes opened on the phone** |
| `am broadcast -a com.ketua.OPEN.NOTES` | `Broadcast sent without waiting for result` → app appeared ≈1 s later |

Conclusion: the intent trigger *does* reach MacroDroid on this build; what had failed in earlier
attempts was the **action**, not the trigger.

## Macro spec (one macro per app)

```
Nama      : BUKA <APP>
Pencetus 1: Intent Diterima   Action = com.ketua.OPEN.<APP>      (exact, uppercase)
Tindakan 1: Lancar Aplikasi   <app>            → row must read "Lancar <app>"
Kekangan 0: Tiada
```

Suggested action strings and packages:

| App | Action | Package |
|---|---|---|
| Nota | `com.ketua.OPEN.NOTES` | `com.miui.notes` |
| Chrome | `com.ketua.OPEN.CHROME` | `com.android.chrome` |
| Claude | `com.ketua.OPEN.CLAUDE` | `com.anthropic.claude` |
| Grok | `com.ketua.OPEN.GROK` | `ai.x.grok` |
| Tetapan | `com.ketua.OPEN.SETTINGS` | `com.android.settings` |

System activities (`android.settings.SETTINGS`, `ACTION_MAIN`+`CATEGORY_HOME`) still launch from
Termux — they do not need a macro.

## AI prompt template (MacroDroid "Create with AI")

English works better than Malay here. Naming the **package** is what stops the null action.

```
Create ONE macro named "BUKA NOTA".
Trigger: Intent Received — Action equals exactly: com.ketua.OPEN.NOTES
Actions: exactly ONE action only — Launch Application, application package: com.miui.notes
Rules: Do NOT add "Run Macro", do NOT add UI Interaction, do NOT add Wait or any condition.
No constraints. Keep the macro enabled after saving.
```

Repair prompts when the saved macro is wrong:

```
Delete every action except Launch Application (com.miui.notes). The macro must have exactly one action.
The Launch Application action has a null application. Set it to package com.miui.notes.
```

## Read the action row, never the AI prose

Two failures seen live with the AI macro builder, both invisible in its chat reply:

1. **Self-call instead of a tap.** Asked for a UI tap, the AI saved
   `1. Mesej Popup` + `2. Jalankan Makro → <the same macro>` — an infinite self-call. The reply
   claimed a `screen tap at X=540, Y=1200` had been added.
2. **`Lancar null`.** A `Lancar Aplikasi` action with no application selected. The macro looks
   complete (`Tindakan: 1`) and every broadcast still does nothing. Fix: tap the row → *Pilih
   Aplikasi* → search the app → **OK** (not Back) → Save → the row must now read
   `Lancar <app>`.

Rule: after any AI build, screenshot the macro and confirm the literal row text. If it says
`null`, the problem is not the trigger.

## Picker tips (Malay UI)

- The application chooser is searchable; clearing the box and scrolling to the letter of the app
  is more reliable than typing (users reported "cuma ada <X> saja" when a stale search filtered
  the list).
- `Lancar Skrin Utama`, `Lancar Aplikasi` and UI taps all need the accessibility service; without
  it they fail exactly like a dead trigger
  (`references/hyperos-restricted-settings-accessibility.md`).

## Wiring it to the console / user-facing buttons

Once the macro exists, the console action becomes a broadcast, not `am start`:

```
POST /api/buka {"target":"nota"}  →  run: am broadcast -a com.ketua.OPEN.NOTES
```

Keep the `am start` path for URL (`ACTION_VIEW`) and for system screens, and route everything else
through the macro — otherwise the BUKA tab keeps printing `OK · exit 0` with no visible change,
which reads to the owner as "tak jalan".
