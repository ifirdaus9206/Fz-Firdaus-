# Termux space audit — measured facts and the "free 700 GB" myth

Verified on Xiaomi 25080RABDG (Redmi Note 15 Pro 5G, HyperOS 3 / Android 16, no root), 2026-11-12.

## What the numbers actually are

| Measure | Value |
|---|---|
| Partition `/data` (= `/storage/emulated`) | 225 G total, 140 G used, **84 G free** (63% used) |
| `$HOME` (`/data/data/com.termux/files/home`) | **19 G** |
| `~/.hermes20` | 17 G |
| `~/.hermes20/archive` | 8.7 G (`ultimate-2026-10` 7.7 G, `code-server-2026-10` 939 M) |
| `~/.hermes20/tools` | 5.1 G (`others` 2.8 G, `hermes-source` 2.4 G) |
| `~/.hermes20/legacy-ultimate` | 2.1 G (projects 1.8 G) |
| `~/.cargo` / `~/.local` / `~/.hermes_venvs` / `~/.cache` | 926 M / 725 M / 235 M / 222 M |
| `/sdcard/Documents/UIM` (warehouse) | 241 K — handoff is not what fills the disk |
| `ls /storage` | `emulated` only → **no SD card** |

Safe quick reclaim without touching the factory: `archive/ultimate-2026-10`,
`archive/code-server-2026-10`, `~/.cache` ≈ **8.9 G**.

## There is no "700 GB free Termux storage"

Termux has no per-app quota and no hosted storage tier. It runs as a normal Android app: everything
it writes lands on the phone's data partition, so **free space = phone free space**. On a 256 GB
handset (~225 GiB usable) a 700 GB figure is arithmetically impossible. `termux-setup-storage` only
creates `~/storage/*` symlinks into `/sdcard` — it adds zero bytes, it just exposes what is already
there. The only ways to genuinely *add* capacity are physical: an SD card (see
`termux/termux-app` discussions #2437 and #3567 for bind-mount/symlink layouts) or a bigger phone.

## Verifying a claim the user says they saw

1. **GitHub** — REST search is reliable and needs no auth for light use:
   `curl -s "https://api.github.com/search/issues?q=termux+700GB+storage&per_page=5"`
   and, for "did *I* write this?":
   `curl -s "https://api.github.com/search/issues?q=author:<user>&per_page=20"`
   `total_count: 0` on both author and commenter queries = the account never posted anything.
2. **Reddit** — `https://www.reddit.com/search.json?q=...` answers with an HTML challenge page (CSS
   `:root{--rem…}` markup), not JSON, so a naive `json.load` fails. Route through DuckDuckGo Lite:
   ```bash
   curl -s -A "Mozilla/5.0 (Linux; Android 16)" \
     "https://lite.duckduckgo.com/lite/?q=termux+700GB+free+storage+reddit"
   ```
   then regex the `uddg=` redirect anchors to recover real URLs.
3. Report what was found (or not) and give the link list, instead of arguing from memory.

## Watchdog

`scripts/space_watch.sh` — `WARN_GB=15`, `CRIT_GB=8`, silent above the warn band, graded alert with
the top consumer table below it. Registered as a `no_agent` cron job (`0 */6 * * *`,
`deliver=origin`) so a healthy day sends nothing at all.

Testing the alert branch without a nearly-full disk: copy with thresholds raised
(`sed 's/^WARN_GB=15/WARN_GB=200/;s/^CRIT_GB=8/CRIT_GB=190/'`) into **`$HOME`**, run it, delete it.
`/tmp` is unwritable on Termux, so staging there fails with `Permission denied`.
