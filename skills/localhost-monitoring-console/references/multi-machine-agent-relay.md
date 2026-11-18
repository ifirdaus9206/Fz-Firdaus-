# Second machine's agent on the same dashboard (relay, not a second console)

Situation that triggers this: the owner runs **one agent per machine** — e.g. Ketua on the phone
(Termux, always on) and Sofia on a Windows PC (heavy work) — and says:

> *"kau dan sofia setiap seorang ada tugas masing-masing… aku monitor satu tempat sahaja untuk
> keduanya boleh atau tidak"*

Answer first, architect second: **yes, and nothing has to be thrown away.** The two agents are not
duplicates; they are two workers with different uptime and different capabilities. What must be
single is the *voice to the owner* and the *screen the owner looks at*.

## 1. Prove reachability before designing anything

The whole "just SSH into the PC" plan collapsed in one command because the phone was no longer on the
house Wi-Fi:

```bash
ifconfig 2>/dev/null | grep 'inet ' | grep -v 127.0.0.1     # → only 100.85.34.233
ip -4 addr show | grep 'inet '
ip route
```

`100.64.0.0/10` is CGNAT: the phone was on mobile data, so the PC's `192.168.0.x` was unreachable —
and no amount of console code fixes that. Probe the peer explicitly and record the result as
evidence:

```bash
for h in 192.168.0.11 192.168.0.41 DESKTOP-XXXXXXX; do
  printf "%-20s " "$h"; timeout 4 bash -c "echo > /dev/tcp/$h/22" 2>/dev/null \
    && echo "port 22 TERBUKA" || echo "tiada"
done
command -v tailscale && tailscale status
awk '{print $3}' ~/.ssh/authorized_keys    # inbound keys only — not proof the peer ever connected
```

**An inbound key is not a proven peer.** `authorized_keys` holding `sofia-pc@DESKTOP-XXXX` proves the
key was *installed*, not that the PC ever logged in; there is no readable sshd log under runit
(`runit` keeps its own `current` files). Say "belum terbukti", not "dah bersambung", until the peer
runs the command and pastes output.

## 2. Three bridges — pick by what the owner will tolerate

| Bridge | Works when | Cost | Ceiling |
|---|---|---|---|
| **Tailscale on both** (or any mesh VPN) | both machines have *any* internet | free | needs an app installed on the PC; opens an inbound path to the console |
| **Relay file** (GitHub Contents API, gist, small object store) | outbound-only on both sides; phone on CGNAT | free | ~5 min staleness; no interactive control |
| **Second Telegram bot** | always | free | it is another *chat*, not a dashboard — does not satisfy "one screen" |

For an owner who wants **one screen** and will not install anything on the PC yet, the relay wins:
the PC pushes, the console pulls, no inbound ports on either side.

## 3. Relay shape — whitelist fields, never the state directory

The PC side is one stdlib Python file plus a 5-minute Windows Task Scheduler entry. **Do not require
git on the PC**: `PUT https://api.github.com/repos/<owner>/<repo>/contents/status.json` with a
fine-grained PAT (that repo only) is a single HTTPS call.

Whitelist only derived numbers:

```json
{"hostname":"...","ts":"2026-11-18T00:10:00Z","uptime_s":81234,
 "cpu_pct":17,"ram_pct":54,"disk_c_pct":71,"battery":null,
 "hermes_version":"...","last_session":{"title":"...","when":"...","msgs":42},
 "cron":[{"name":"...","last":"...","ok":true}]}
```

Hard exclusions, and say them out loud to the owner: **no `state.db`, no `.env`, no `config.yaml`,
no `auth.json`, no message text, no tokens.** A status file that leaks a config is not monitoring.

The PAT lives in the PC's scheduler environment or a `0600` file — never inside the repo, never in
the pushed JSON.

## 4. Console side — a remote source, not another `homes.json` entry

`homes.json` entries are **local directories** (`{key,label,sub,path,accent}`); pointing one at a
remote machine does nothing. A second machine needs its own read path:

- `GET /api/remote/<key>` → fetch the relay JSON with a short timeout, cache 60 s, add
  `age_s` and `stale: age_s > 900`.
- Give the panel a **"data N min lalu"** line and a red chip when `stale` — a relay that stopped
  pushing looks identical to a healthy machine otherwise.
- Fetch server-side (the browser may have no route to the relay) and serve it from the same
  `127.0.0.1:8787` origin, so no CSP/CORS change is needed.
- Never let the remote panel take the whole screen down: if the relay is missing, render
  `belum ada data` and keep the local tabs working.

One pane, two halves — top = phone agent (live, local), bottom = PC agent (relay): that is what
"monitor satu tempat" actually means to the owner.

## 5. Separate Telegram token — mandatory, and still one voice

Two pollers on one bot token = `409 Conflict` and both agents go deaf. So the second machine needs its
own bot (`@BotFather` → new bot, own allowlist of the owner's chat id).

But a second token is **not** permission for a second conversation. Recommend, and write into the
second agent's `SOUL.md`:

- the PC agent **reports to the lead agent**, not to the owner;
- its bot sends **emergency alerts only** (machine down, build failed, disk full) to the same owner
  chat id;
- routine status goes to the relay file and is read from the dashboard.

Otherwise the owner gets two chats, two narratives, two versions of the truth — exactly what they
asked to avoid. Say this plainly: *"token berasingan wajib; suara berasingan tidak."*

## 6. Reporting this decision to the owner

Board format, one row per check, with the reachability answer as its own row (it is the row that
changes the plan). Then the split-of-duties table (who is 24/7, who does heavy work, who reports to
whom), the honest ceiling (*"relay lewat 5 minit — cukup untuk 'PC mati ke tidak', bukan untuk tengok
skrin sekarang"*), and 3–4 numbered options. Never present the bridge as already working before the
peer has run its half.

## 7. Build order that actually works (and the one blocker you cannot clear yourself)

Build everything that does not need the owner first, then hand over exactly one step. Order used,
with what each step proved:

1. **Prove the pull half is already authorised.** `ssh -T git@github.com` →
   `Hi <owner>! You've successfully authenticated`. That single line means the phone can `git clone`
   a *private* repo via its existing SSH key — **no PAT needed on the phone at all**.
2. **Accept that repo creation is the owner's step.** An SSH key can push to an existing repo but
   cannot create one; `gh` may be installed yet not logged in (`gh auth status` → *not logged into any
   GitHub hosts*). Do not fake around it: prepare everything, then ask for **repo (Private) + a
   fine-grained PAT scoped to that one repo, Contents: Read and write**. Two minutes of owner work.
3. **Pull locally instead of fetching the relay from the endpoint.** Cheaper and offline-safe:
   a `no_agent` cron every 5 min runs `git -C ~/sofia-status pull --quiet --ff-only`, and
   `GET /api/sofia` reads `~/sofia-status/status.json` off disk. Console stays read-only, holds no
   token, and keeps rendering the last known state when the phone is offline.
4. **Warn by silence, not by noise.** The pull script must `exit 0` with **no output** when the repo
   directory does not exist yet (`[ -d "$DIR/.git" ] || exit 0`) and also when the pull is a no-op;
   a `no_agent` job only delivers non-empty stdout, so silence = healthy. Print one line only on
   failure, and cap its own log (`tail -n 40`, rewrite) so a broken pull cannot grow forever.
5. **Ship the PC half as a self-testing pack**, not as instructions: `--print-config` (shows
   `token_ada` + which `.hermes*` home was found), `--dry-run` (JSON only), `--out file`
   (write locally), then a real push. Plus a `.bat` that runs all three so the owner clicks once.

## 8. Collecting PC stats with stdlib only (no psutil, no venv)

`psutil` is usually absent on a fresh Windows box and asking the owner to `pip install` is where the
job dies. Everything needed is in stdlib:

| Need | Method |
|---|---|
| uptime | `ctypes.windll.kernel32.GetTickCount64() // 1000` |
| RAM % | `ctypes` `MEMORYSTATUSEX` + `GlobalMemoryStatusEx` (`dwMemoryLoad`, `ullTotalPhys`) |
| CPU % | `powershell -NoProfile -Command "(Get-CimInstance Win32_Processor \| Measure-Object -Property LoadPercentage -Average).Average"` — parse **all** numbers and average (multi-socket returns several lines) |
| disks | `for letter in "CDEFGH": if os.path.exists(letter + ":\\")` then `shutil.disk_usage` |
| gateway alive | read `gateway.pid`, then `tasklist /FI "PID eq <pid>"` and look for the pid in the text |
| Hermes home | `HERMES_HOME` → else newest `~/.hermes*` containing `state.db` |

Linux/Termux fallbacks (`/proc/uptime`, `/proc/loadavg`, `/proc/meminfo`) let you **test the whole
script on the phone** before the owner ever runs it on the PC — that is how the JSON shape gets
verified without a Windows box. Expect `cpu_pct`/`uptime_s` to be `null` there and say so; the panel
must render `–`, never `0`.

`hermes.cron.executions.db` columns are `id, job_id, source, process_id, pid, process_started_at,
status, claimed_at, started_at, finished_at, error` — **there is no `job_name`**. Query
`select job_id, started_at, status … where started_at is not null order by started_at desc limit 1`,
and read `cron/jobs.json` separately if you want human names. Check `pragma table_info` before writing
the query; guessing a column name fails at runtime, not at review.

## 9. Verifying a remote panel without a remote machine

The endpoint is testable before the PC exists — and the test data must not survive:

```bash
mkdir -p ~/sofia-status && cat > ~/sofia-status/status.json <<'JSON'
{"schema":1,"agent":"sofia","host":"DESKTOP-XXXX","os":"Windows 11 (10.0.22631)",
 "uptime_s":93784,"cpu_pct":14.2,"cores":8,"ram_pct":47.5,"disks":[{"mount":"C:\\","pct":61.3}],
 "hermes":{"gateway_alive":true,"sessions_today":4,"last_session":{"title":"…","ago_s":420}},"alerts":[]}
JSON
curl -s 127.0.0.1:8787/api/sofia | head -c 200     # → "ada":true, "umur_s":0, "basi":false
rm -f ~/sofia-status/status.json                   # ← mandatory
curl -s 127.0.0.1:8787/api/sofia | head -c 200     # → "ada":false, "nota":"repo relay belum ada"
```

Deleting the sample is part of the verification, not cleanup: a dashboard that shows a **fabricated
healthy PC** is worse than one that honestly says "belum ada data". Report both curls in the board so
the owner sees the empty state was restored.

`sv restart hermes-console` is the way to load a new endpoint/tab; prove it with `sv status` + `GET /`
+ a `grep -c 'data-tab="sofia"'` on the served HTML, because a static-file edit that never got picked
up looks exactly like a broken panel.

## 10. Handoff pack for the owner's Windows machine

One folder, one format per file, plain-Malay doc first — the owner moves it to the PC by USB/Drive:

```
00-BACA-DULU.md            apa ini, matriks siapa buat apa, gejala→punca table
01-LANGKAH-GITHUB.md       cipta repo Private + fine-grained PAT (skrin demi skrin)
02-LANGKAH-PC.md           python check, C:\sofia\, config.json, %USERPROFILE%\.sofia\pat.txt,
                           --print-config → --dry-run → push, Task Scheduler
03-TOKEN-TELEGRAM-SOFIA.md @BotFather new bot, allowlist = owner chat id, SOUL line
sofia_status.py            the collector/pusher
config.contoh.json         copy → config.json
jalankan-sofia.bat         double-click self test
```

Command name traps to spell out in the doc, because the owner will hit them:
`Win+R` → `taskschd.msc`; Basic Task = Daily then **edit the trigger to "Repeat task every 5 minutes
for Indefinitely"**; and under **Conditions** untick *"Start the task only if the computer is on AC
power"* (default stops the whole relay on a laptop).

Deliver the pack with the phone-storage handoff tool (`uim_hantar.sh <folder> --ke 05-HANTAR --nama
<name>`), not as chat attachments, and verify with a `sha256sum` of the script on both sides.

