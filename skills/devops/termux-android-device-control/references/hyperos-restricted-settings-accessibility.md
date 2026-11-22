# HyperOS restricted settings vs accessibility services (why a macro "runs" and nothing moves)

Measured 2026-11-21 · Xiaomi 25080RABDG (HyperOS 3 / Android 16) · MacroDroid 6.1.5 from Play
Store (`pm list packages -i` → `installer=com.android.vending`).

## Symptom

`Tetapan → Kebolehcapaian → Apl yang dimuat turun`:

```
Interaksi UI MacroDroid    Dikawal oleh Tetapan Terhad     (grey, no toggle)
MacroDroid                 Dikawal oleh Tetapan Terhad
```

Android 10+ blocks background activity launches, so MacroDroid routes **`Lancar Aplikasi`** and
`Lancar Skrin Utama` through its accessibility service too. Without the service the macro executes,
prints nothing, opens nothing — indistinguishable from a dead trigger unless you check this screen.

## Dead ends (don't retry, don't send the user)

- `Info apl → ⋮` shows only **Info apl** and **Kongsi**; there is no "Benarkan tetapan terhad".
- Bottom of `Info apl` lists only install source/times — no restricted-settings row.
- Being Play-installed does **not** exempt the app on this build.
- `settings get secure enabled_accessibility_services` → `INTERACT_ACROSS_USERS`;
  `content query --uri content://settings/secure` → `ACCESS_CONTENT_PROVIDERS_EXTERNALLY`;
  `pm dump <pkg>` → `Permission Denial: DUMP`; `cmd accessibility get-bindings` → empty.
  Only the user's screenshot can tell you the state.

## What works

```bash
# 1. Settings.apk is readable → mine intent actions from its binary manifest string pool
pm path com.android.settings          # /system_ext/priv-app/Settings/Settings.apk
#   python: zipfile → AndroidManifest.xml → union of [\x20-\x7e]{6,} and (?:[\x20-\x7e]\x00){6,}
#   grep restricted|accessibility →
#     android.settings.SHOW_RESTRICTED_SETTING_DIALOG
#     android.settings.ACCESSIBILITY_SETTINGS / _DETAILS_SETTINGS / _SHORTCUT_SETTINGS

# 2. Open the unlock dialog carrying "Benarkan"
am start -a android.settings.SHOW_RESTRICTED_SETTING_DIALOG \
         --es android.intent.extra.PACKAGE_NAME com.arlosoft.macrodroid
# -> Starting: Intent { act=...SHOW_RESTRICTED_SETTING_DIALOG (has extras) }  rc=0
```

Then the human allows it (PIN), returns to `Kebolehcapaian → Apl yang dimuat turun`, switches the
service on and accepts Android's warning.

## Component/extra extraction for the automation app

From `base.apk`'s manifest (same string-pool scan):
`com.arlosoft.macrodroid.action.services.UIInteractionAccessibilityService`,
`...triggers.services.MacroDroidAccessibilityServiceJellyBean`,
`...accessibility.KeepAccessibilityServicesRunningActivity`.
`am start -a android.settings.ACCESSIBILITY_DETAILS_SETTINGS -d 'component:pkg/pkg.Service'` is
**truncated at the `/`** by termux-am (`dat=component:`) — use `-e` extras for components.

## Fallback if the unlock is refused

No accessibility = no tap path (`input` → `INJECT_EVENTS`). Say so plainly and use the intent
surface that does work: `am start` for URLs, system settings pages, and any app whose launcher
activity was resolved from its APK. Stop rewriting macros that cannot fire.
