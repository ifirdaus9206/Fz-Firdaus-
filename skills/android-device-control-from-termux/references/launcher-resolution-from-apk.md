# Resolving an app's launcher activity from its APK (pure stdlib, no aapt)

Measured 2026-11-22 on Xiaomi 25080RABDG, HyperOS 3 / Android 16, Play-signed Termux.
Used when `aapt` is absent, `cmd package resolve-activity` and `pm dump` are denied
(`INTERACT_ACROSS_USERS` / `DUMP`), and `am start -a MAIN -c LAUNCHER -p <pkg>` answers
`unable to resolve Intent` because package visibility hides the app.

Result: a `buka <name>` command that opened Claude, Grok, Chrome, MacroDroid and Mi Notes
first try after the two fixes below, with the component cached in `~/.cache/buka.json`.

## Pipeline

```python
# 1. package search (visibility-filtered but enough for installed apps)
pkgs = [l.split(":",1)[1] for l in sh("pm","list","packages").splitlines() if l.startswith("package:")]

# 2. APK path — pm path prints ONE LINE PER SPLIT; take the first (base.apk)
path = sh("pm","path",pkg).strip().splitlines()[0].replace("package:","")

# 3. activity names out of the binary manifest string pool (UTF-16LE runs)
data = zipfile.ZipFile(path).read("AndroidManifest.xml")
names = set()
for m in re.finditer(rb'(?:[\x20-\x7e]\x00){5,}', data):
    s = re.sub(r'^[^A-Za-z]+', '', m.group(0).decode("utf-16le","ignore"))   # strip length-prefix junk
    s = re.sub(r'[^A-Za-z0-9_.]+$', '', s)                                   # strip trailing junk
    if s.endswith("Activity") and "/" not in s and 6 < len(s) < 120:
        if "." not in s: s = pkg + "." + s
        if s.startswith(pkg): names.add(s)

# 4. order by likelihood, then validate by launching
def score(n):
    low = n.rsplit(".",1)[-1].lower()
    return 0 if low in ("mainactivity","launcheractivity") else \
           1 if "launcher" in low else 2 if low.startswith("main") else \
           3 if "splash" in low else 4 if "home" in low else 5

for cls in sorted(names, key=lambda n:(score(n), len(n)))[:15]:
    out = sh("am","start","-W","-n","%s/%s" % (pkg,cls))
    if "Status: ok" in out:      # first hit wins -> cache it
        break
```

## Two bugs that make every candidate fail silently

1. **AXML strings carry a one-character length prefix.** Decoded runs look like
   `$com.arlosoft.macrodroid.MacroDroidService` or `.com.anthropic.claude.mainactivity.MainActivity`.
   Appending that junk to `pkg/` produces a component that does not exist, so *every* candidate
   returns `Error type 3` and the scan looks like "this app has no launcher activity".
   Strip leading non-letters and trailing non-name characters before use.
2. **`pm path` returns multiple lines for split (AAB) installs.** The whole output run through
   `.replace("package:","")` is not a valid path (`open()` raises, the resolver returns `[]`).
   Take `splitlines()[0]`.

## Launchers whose class name is outside the package prefix

The `startswith(pkg)` filter drops them, so keep a small explicit map:

| Package | Activity |
|---|---|
| `com.android.chrome` | `com.google.android.apps.chrome.Main` (starts with `com.google`, not the package) |

Everything else observed resolved naturally from the manifest:
`com.anthropic.claude/com.anthropic.claude.mainactivity.MainActivity`,
`ai.x.grok/ai.x.grok.main.GrokActivity`,
`com.arlosoft.macrodroid/com.arlosoft.macrodroid.LauncherActivity`,
`com.miui.notes/com.miui.pc.frame.PcMainActivity`.

## Validate with `-W`, never with the first output line

`am start` prints `Starting: Intent {…}` even for a component that does not exist. With `-W`,
a real launch also prints `Status: ok`; a wrong name prints `Error type 3` +
`Error: Activity class … does not exist`. Cost of a failed `-W` probe is ~0.2 s, so probing
15 candidates is cheaper than one wrong answer given to the user.

## Also useful from the same scan

- `Settings.apk` (`/system_ext/priv-app/Settings/Settings.apk`) yields real intent actions:
  `android.settings.SHOW_RESTRICTED_SETTING_DIALOG`, `android.settings.ACCESSIBILITY_DETAILS_SETTINGS`,
  `android.settings.APPLICATION_DETAILS_SETTINGS`. Launching the restricted-settings dialog for a
  package: `am start -a android.settings.SHOW_RESTRICTED_SETTING_DIALOG --es android.intent.extra.PACKAGE_NAME <pkg>`.
- `-d 'component:pkg/pkg.Service'` is truncated at the `/` by the Termux `am` wrapper (`dat=component:`);
  prefer `-n` for components and `-e` for argument-style values.
- Installer provenance without root: `pm list packages -i | grep <pkg>` → `installer=com.android.vending`
  proves a Play install (rules out the sideload-only "restricted settings" path, so the block is the
  OEM's own layer).
