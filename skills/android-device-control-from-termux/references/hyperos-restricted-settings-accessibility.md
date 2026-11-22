# HyperOS "Dikawal oleh Tetapan Terhad" — why an accessibility service can't be switched on

Measured 2026-11-21, Xiaomi 25080RABDG (HyperOS 3 / Android 16), MacroDroid 6.1.5 installed
**from Play Store** (`pm list packages -i com.arlosoft.macrodroid` → `installer=com.android.vending`).

## Symptom

`Tetapan → Kebolehcapaian → Apl yang dimuat turun` shows the app's services greyed out:

```
Interaksi UI MacroDroid    Dikawal oleh Tetapan Terhad
MacroDroid                 Dikawal oleh Tetapan Terhad
```

Rows cannot be tapped; toggle absent. Every accessibility-dependent action (UI tap, and MacroDroid's
`Lancar Aplikasi` / `Lancar Skrin Utama`, which bypass the Android 10+ background-activity-launch
block through the accessibility service) therefore fails **silently** — the macro still runs, logs
nothing, and the screen never changes. This is the real root cause behind "macro betul tapi tiada
apa-apa jadi", not a bad trigger.

## Where the unlock is NOT

- `Info apl → ⋮` contains only **Info apl** and **Kongsi** on HyperOS. There is no
  "Benarkan tetapan terhad / Allow restricted settings" item, even though it is Play-installed.
- Bottom of `Info apl` only lists `Sumber pemasangan: Google Play Store`, install/update times,
  version — no restricted-settings row.
- So the AOSP recipe ("App info ⋮ → Allow restricted settings") is wrong for this build;
  don't send the user hunting for it twice.

## What the APK proves / what to try instead

`pm path com.android.settings` → `/system_ext/priv-app/Settings/Settings.apk` (readable). Scan its
binary `AndroidManifest.xml` string pool (UTF-16LE + 8-bit union) for `restricted`/`accessibility`:

```
android.settings.SHOW_RESTRICTED_SETTING_DIALOG
android.settings.ACCESSIBILITY_SETTINGS
android.settings.ACCESSIBILITY_DETAILS_SETTINGS
android.settings.ACCESSIBILITY_SHORTCUT_SETTINGS
com.android.settings.accessibility.AccessibilitySettings
```

The dialog that carries the unlock button is launchable directly:

```bash
am start -a android.settings.SHOW_RESTRICTED_SETTING_DIALOG \
         --es android.intent.extra.PACKAGE_NAME com.arlosoft.macrodroid
# -> Starting: Intent { act=...SHOW_RESTRICTED_SETTING_DIALOG (has extras) }   rc=0
```

Then: allow the restricted setting (PIN/pattern), then re-open
`Kebolehcapaian → Apl yang dimuat turun → <app>` and switch the service on.

## Where the unlock actually is (confirmed, same build)

Not in `⋮` — **lower down the App-info page, in the `Tetapan lanjutan` (Advanced settings) block**:

```
Info apl → MacroDroid → skrol ke bawah → Tetapan lanjutan
    Padam tetapan lalai        : Tiada tetapan lalai
    Benarkan tetapan terhad    : ● ON (biru)      ← the unlock
```

Turning `Benarkan tetapan terhad` ON is what unblocks the service; no PIN was requested on this
build. Immediately after that, `Kebolehcapaian → Apl yang dimuat turun` showed real toggles instead of
`Dikawal oleh Tetapan Terhad`, both entries (`MacroDroid`, `Interaksi UI MacroDroid`) could be
switched on, and a macro action that had done nothing for hours (`Lancar Skrin Utama`) moved the
screen on the user's own `Uji tindakan dari sini` test.

Order that lands: (1) `am start -a android.settings.APPLICATION_DETAILS_SETTINGS -d package:<pkg>`
to put the App-info page on screen, (2) user scrolls to `Tetapan lanjutan`, flips
`Benarkan tetapan terhad`, (3) accessibility → both service rows ON, (4) re-run the action test.
If the block is not visible, the `SHOW_RESTRICTED_SETTING_DIALOG` intent above surfaces the dialog
that carries the allow button.

After a reboot HyperOS may drop accessibility services again — re-check the row before blaming the
macro, and keep the app's Autostart ON.

## Termux wrapper traps hit in the same round

- `am start -a android.settings.ACCESSIBILITY_DETAILS_SETTINGS -d 'component:pkg/pkg.Service'`
  arrives as `dat=component:` — termux-am truncates the value at `/`, exactly like the
  `-d ":settings:show_fragment…"` truncation documented in the SKILL. Use `-e` extras instead of
  putting a component in `-d`.
- Accessibility service class names for this app, from its own manifest (needed for a details page):
  `com.arlosoft.macrodroid.action.services.UIInteractionAccessibilityService`,
  `com.arlosoft.macrodroid.triggers.services.MacroDroidAccessibilityServiceJellyBean`,
  `com.arlosoft.macrodroid.accessibility.KeepAccessibilityServicesRunningActivity`.

## Reading the state (what is denied)

```bash
settings get secure enabled_accessibility_services   # SecurityException: INTERACT_ACROSS_USERS
content query --uri content://settings/secure ...     # SecurityException: ACCESS_CONTENT_PROVIDERS_EXTERNALLY
cmd accessibility get-bindings                        # empty output
pm dump com.arlosoft.macrodroid                       # Permission Denial: DUMP
```

So the enabled/disabled state can only be read off the user's screenshot. Ask for the
`Apl yang dimuat turun` list, not for "is it on".

## Honest fallback when the unlock is refused

Without accessibility there is **no tap path**: `input` is blocked (`INJECT_EVENTS`), Tasker-style
plugins need the same permission, and ADB pairing may be impossible (financing lock). What still
works is the intent surface — `am start` for URLs, system settings pages, and any app whose
launcher activity was resolved from its APK — so say "kawalan ketukan tidak tersedia, kita guna
buka app/URL sahaja" rather than continuing to rebuild macros that cannot fire.
