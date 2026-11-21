# Recurring-job reporting policy, batch sweeps, and the shared-storage mirror

Everything here was measured on the Android/Termux owner setup (2026-11-20) and is about jobs that
run quietly on the owner's behalf. The rule that keeps them useful is the same in all three cases:
**silence is the default, one scheduled message is the exception, and a failure is the only thing
allowed to interrupt.**

## 1. Reporting policy for `no_agent` jobs

The owner's words: *"bagi laporan setiap 9 malam satu kali sahaja, tak payah banyak kali, ada masalah
baru bagitahu"* — one report at 21:00, nothing else, tell me immediately only when something breaks.

Implementation shape:

| Branch | Behaviour | Where |
|---|---|---|
| success, nothing changed | `exit 0` with **no stdout** | work script |
| success, work done | append to log, `exit 0`, **still no stdout** | work script |
| failure | one `⚠️ …` line to stdout, then `exit 0` | work script |
| daily summary | one block, fixed hour (21:00) | separate `no_agent` job |

Two jobs, not one:

```
work    : */15 * * * *   script=email_autosort.sh   (silent)
digest  : 0 21 * * *     script=email_digest.sh    (one message)
```

`exit 0` on failure matters: a non-zero exit makes the scheduler report the job itself as broken and
buried the real message.

### Digest script pattern

Read the work log for **today's** totals, then take live counts from the source of truth:

```bash
TODAY=$(date '+%Y-%m-%d')
while IFS= read -r line; do
  case "$line" in
    *"$TODAY"*RINGKASAN*)
      p=$(printf '%s' "$line" | sed -n 's/.*"PENTING": \([0-9]*\).*/\1/p')
      ...
      RUNS=$((RUNS+1)) ;;
  esac
done < "$LOG"
```

then one IMAP `select()` per label for the current state, printed as
`INBOX=15740 1-PENTING=382 2-KERJA=336 3-PROMOSI=1188 0-LAIN=66`. Measured runtime: **6.7 s**.
If both totals are zero and the counts are unavailable, exit silently rather than sending an empty
report.

### Verifying "silent"

Run the work script and check stdout is empty — not that it exited 0. A background
`terminal(background=true, notify_on_complete=true)` run is the honest way to see the full output
after it finishes; a foreground call on a 7-minute batch hits the tool timeout and looks like a hang.
Note that an interactive `bash script.sh` may print the shell's `.bashrc` banner; cron runs it
non-interactively, so the banner never reaches the owner (proved by earlier cron outputs containing
only the work line, never the banner).

## 2. Batch sweeps and their silent coverage ceiling

Symptom: the owner says *"bukan kesemuanya emel yang kau susun, kenapa?"*

Cause class: the job has a ceiling that the log never mentions.

```
python autosort.py apply --max 80 --days 2      # 80 newest, last 2 days, every 15 min
IMAP INBOX = 17,585    labelled = 31 + 32 + 115 + 66 = 244
```

The log looked perfect ("1 email disusun") because it was perfect — for 80 messages out of 17,585.

Diagnosis that settles it in one call: count the source per label before touching anything.

```python
M = imaplib.IMAP4_SSL("imap.gmail.com"); M.login(user, app_password)
for box in ("INBOX", "1-PENTING", "2-KERJA", "3-PROMOSI", "0-LAIN"):
    typ, d = M.select(f'"{box}"', readonly=True)
    print(f"{box:10} {int(d[0])}")
```

Then size the batch:

| Batch | Measured | Implication |
|---|---|---|
| 400 messages | 3 m 18 s | safe at a 15-minute cadence |
| 800 messages | ~7 min | still under 15 min, but little headroom |

Rules that keep a backfill honest:

- One batch must finish well inside the cron interval; time it before raising `--max` again.
- Items matching no rule stay in the source and are re-scanned every run (40 % here: 159 of 400).
  Either accept the waste, or archive unmatched into a catch-all label **with the owner's consent**
  (it moves mail they may still want in the inbox).
- Report the remainder, not just the count moved: "INBOX 17,585 → 17,343, 242 moved, ~9 h to finish"
  is a claim the owner can check; "sorted" is not.
- The sweep archives by copying to the label and deleting from INBOX (`UID COPY` + `STORE \Deleted`
  + `EXPUNGE`), so a rerun is idempotent — but only if the label copy succeeded; log both steps.

## 3. Mirroring artifacts into the phone's shared storage

Owners ask *"fail ini masuk dalam Termux ke dalam memori telefon aku?"* — the honest answer is that
everything lives in `/data/data/com.termux/files/home` (app-private, invisible in Files, deleted with
the app), while `/sdcard/Documents/UIM/01-LAPORAN` is the only place they can open from the phone.

Contract for the mirror (`scripts/mirror_to_shared_storage.sh`, cron 03:00):

- **one-way** Termux → `/sdcard/Documents/...`;
- **sha256 compare** before copying, so a second run is silent and never duplicates;
- **never delete** anything in the destination;
- one stdout line only when something actually copied (`📁 N fail disalin …`);
- state/log under `<HERMES_HOME>/logs/`, so the digest can read it later.

Measured: home `~/.hermes20` = **17 GB** (archive 8.7 GB, tools 5.5 GB, legacy 2.1 GB, state.db 59 MB)
versus the shared folder at **85 KB** before the first run and 10 files after. Say the sizes out loud —
"17 GB inside Termux" is what stops the owner assuming their work is safely in Files.

## 4. Device bridges from Termux (verified capability matrix)

Useful when the owner asks *"kau tak boleh guna aksesibiliti ni untuk jalankan semua?"*

| Probe | Result |
|---|---|
| `am start -a android.settings.SETTINGS` | **works** — `Starting: Intent { … }`, app opens |
| `am broadcast -a com.ketua.TAP` | **works** — `Broadcast sent without waiting for result` |
| `input keyevent 0` | **blocked** — `SecurityException: … INJECT_EVENTS` |
| `ls /dev/input`, `/dev/uinput` | Permission denied |
| `settings get …`, `content query …`, `dumpsys …`, `cmd accessibility get-bindings` | Permission denied / empty |
| `pm list packages` | works but visibility-filtered |

Consequences: launching apps/URLs is fine from Termux; **tapping inside another app is not**, and the
accessibility services listed in Settings belong to the apps that own them (Screenshot, HyperAI) —
they do not hand control to Termux. A third-party automation app is the only no-ADB bridge, and it
must be triggered by something Termux can emit (broadcast action or its HTTP webhook).

**Unverified — do not present as a recipe.** In that session MacroDroid (`com.arlosoft.macrodroid`)
was installed with a macro built as *Intent Received `com.ketua.TAP` → Toast → Tap(540,1200)*, four
broadcast variants were sent (`-p`, `-f 32`, both, plain), and **nothing on screen changed**; the tap
action was also missing from the macro at first. The only tested guidance is the isolation ladder,
in order: run the macro manually (▶) → replace the Toast action with **Launch Application → Settings**
(works without accessibility, so it isolates trigger-vs-action) → read MacroDroid's own log → check
HyperOS autostart/battery → only then debug the trigger. Treat any "it works now" claim as unproven
until the owner confirms the on-device effect.
