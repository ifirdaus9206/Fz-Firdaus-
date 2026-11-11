# Background survival diagnostics — "kenapa Termux mati / tidur?"

Goal: decide **process killed** vs **device slept (Doze / App Freezer)** vs **service tree
restarted**, using only app-uid access. No root, adb not paired.

## 1. Baseline facts (cheap, always works)

```bash
getprop ro.build.version.release; getprop ro.product.model; getprop ro.build.version.sdk
getprop ro.miui.ui.version.name          # HyperOS/MIUI version, e.g. V816
termux-info                              # TERMUX_VERSION, arch, kernel, Android
```

Read `TERMUX_VERSION`. `googleplay.*` = Play-signed Termux → **cannot** install F-Droid
add-ons (Termux:Boot, Termux:API, Termux:Widget); signature mismatch. Say this out loud before
recommending Termux:Boot — otherwise the advice is dead on arrival.

## 2. What app uid is DENIED (do not burn calls re-discovering)

Verified denials on Android 16 / HyperOS, uid `u0_a2xx`:

| Command | Result |
|---|---|
| `dumpsys power` | `Permission Denial: can't dump PowerManagerService … missing android.permission.DUMP` |
| `dumpsys deviceidle` | `can't dump DeviceIdleController` |
| `dumpsys deviceidle whitelist [+pkg]` | same denial → **battery whitelist unverifiable** |
| `dumpsys activity` | `can't dump ActivityManager` |
| `settings get global …` | `SecurityException: requires android.permission.INTERACT_ACROSS_USERS` |
| `cmd appops get <pkg> RUN_IN_BACKGROUND` | same `INTERACT_ACROSS_USERS` denial |
| `dmesg` | empty output |
| `cat /proc/uptime`, `cat /proc/sys/kernel/pid_max` | `Permission denied` |
| `dumpsys package <pkg>` | empty |

Still readable: `uptime`, `logcat`, `ps -A` (only own processes), `/proc/self/*`, `pm list packages`
(filtered), `sv status`.

`am` is the **Termux wrapper** (`Activity manager (activity) commands provided by the com.termux
app.`), so `am get-standby-bucket` does not exist — it prints the wrapper usage instead.

## 3. Kill vs sleep — the decisive comparison

```bash
uptime                                   # kernel uptime (works even though /proc/uptime is denied)
ps -A -o pid,ppid,etimes,args | grep -E 'runsvdir|app\.py|gateway'
sv status $PREFIX/var/service/<name>     # "run: … (pid N) 6280s"
date
```

Reasoning rules:

- **kernel `uptime` ≫ process `etimes`** → the *device did not reboot*; only app/service
  processes restarted. A claim like "phone came back alive" is then false and must be corrected.
- **pid identical across error timestamps** (logcat pid field, `ps`, `sv status`) → the process
  **never died**; a `httpx.ReadError` / socket timeout at that moment is **network**, i.e. Doze
  cut the radio / app frozen, not a kill.
- Whole supervision tree (`runsvdir` + all `runsv`) sharing the same `etimes` while the Termux
  app process pid is much older → **child tree was killed / restarted, app survived**: phantom
  process killer, LMK of children, or a manual `termux-services start`.

## 4. Log buffers — spans lie, check them

```bash
logcat -d | wc -l                 # main buffer can hold only ~5k lines (minutes!)
logcat -d | head -1               # first line = how far back it actually reaches
logcat -d -b events | head -3     # events buffer may start at the interesting minute
logcat -d | grep -ci phantom      # 0 says nothing if the buffer is short
```

The `crash` buffer (`--------- beginning of crash`) often retains days of `libc`/`DEBUG` aborts
while `main` has rotated. Absence of `am_kill` / `lowmemorykiller` / `phantom` lines is **not**
evidence of no kill when the buffer is short — report it as "boleh dibaca tetapi tidak meliputi
peristiwa itu".

## 5. Wake lock — prove it, don't trust exit code

```bash
termux-wake-lock; echo exit=$?         # exit 0 alone is weak: it's a local shell script
logcat -d | grep -E 'TermuxService' | tail -6
```

Proof of a held lock:

```
D TermuxService: ACTION_WAKE_LOCK intent received
V TermuxService: Ignoring acquiring WakeLocks since they are already held
```

Key insight for the boss: **a wake lock keeps the CPU awake but does not exempt the app from Doze
network restrictions.** So "wake lock held + ReadError" is a coherent, expected combination —
it points at battery-optimisation whitelisting, not at a broken lock.

## 6. Termux:API / add-ons

```bash
pm list packages com.termux.api; pm list packages com.termux.boot
termux-toast 'ujian'; echo exit=$?
```

`termux-toast` returning 0 with `com.termux.api` absent means the broadcast went nowhere
(`am broadcast` → `Broadcast sent without waiting for result`). Silent no-op, not success.

## 7. Supervision health (runit / termux-services)

```bash
command -v sv; ls $PREFIX/var/service; sv status $PREFIX/var/service/*
ls ~/.termux/ ~/.termux/boot/          # boot script present? (needs Termux:Boot to ever run)
```

- `down: … 1s, normally up, want up` repeating = **crash-loop**. Read the `run` script and the
  service log; a wrong `cd` path gives `FileNotFoundError` every second, burns CPU/battery and
  grows the log without bound (seen: 173 MB `~/.web-server.log`).
- Orphans: `ppid=1` with `readlink /proc/<pid>/cwd` → started by a shell that exited, **not**
  supervised; nothing restarts it. Recommend moving it under runit.

## 8. Fix menu paths (HyperOS 2 / Android 16, Bahasa Melayu)

1. Tetapan → Apl → Urus apl → Termux → Bateri → **Tiada had**
2. Tetapan → Apl → Urus apl → Termux → **Mulakan automatik → ON**
3. Recents → tekan lama kad Termux → ikon **kunci**
4. Tetapan → Bateri → Penjimatan bateri → Tiada had; matikan Mod tidur / Ultra battery saver
5. Pilihan Pembangun → "Jangan simpan aktiviti" OFF; "Tangguh app cache" → Dilumpuhkan
6. **[adb]** `settings put global settings_enable_monitor_phantom_procs false`
7. **[adb]** `dumpsys deviceidle whitelist +com.termux`
8. **[adb]** `am set-standby-bucket com.termux active`
9. Termux:Boot/API → hanya selepas tukar ke binaan F-Droid/GitHub + backup + pasang semula

## 9. Report shape that satisfied the boss

Malay, bullets, **raw output pasted beside every claim**, and denied commands written as
"gagal: <ralat sebenar>" instead of omitted. Close with: (a) kill vs sleep verdict, (b) ranked
causes, (c) numbered steps with real menu paths and an explicit `[PERLU ADB]` tag, (d) one
no-adb recommendation plus its risk. Also flag self-inflicted fragility found on the way
(crash-looping service, unsupervised process, oversized log) — those are fixable without adb and
reduce the kill probability directly.
