# Termux ↔ phone shared storage — findings and test matrix

Device: Redmi Note 15 Pro 5G, HyperOS 3 / Android 16, Termux uid `u0_a221`, no root.
Date of measurements: 2026-11-12.

## Permission reality

| Path | Read | Create folder | Notes |
|---|---|---|---|
| `/sdcard` (= `/storage/emulated/0`) | yes | **no** — `Permission denied` | root of shared storage is not writable by apps |
| `/sdcard/Documents` | yes | **yes** | owner `u0_a282`/`media_rw`, group-writable by the app sandbox; visible in Files app |
| `/sdcard/Download` | yes | yes | alternative warehouse root |
| `/sdcard/Pictures` | yes | no (`Operation not permitted`) | media-indexed dir, avoid |
| `$PREFIX/tmp` | yes | yes | Terminal `/tmp` is **not** writable — use this for outside-`$HOME` tests |
| `/storage/emulated` mounted `/dev/fuse`, 225 G total | | | ~84 G free at time of setup |

Consequence: the documented warehouse root is `/sdcard/Documents/UIM/` (Files app: Documents → UIM),
not `/sdcard/UIM`.

## Symlinks that come from `termux-setup-storage`

`$HOME/storage/{shared,documents,downloads,dcim,pictures,music,movies,podcasts,audiobooks,external-0,media-0}`
and `$HOME/phone`. These all point into `/sdcard` **legitimately**. First version of the auditor
flagged all 12 as policy violations — exclude `$HOME/storage` and `$HOME/phone` from any
"no symlinks to shared storage" check, otherwise every clean run reports a fake breach.

## Guard test matrix (actual results)

| Test | Expected | Observed |
|---|---|---|
| copy `docs/*.md` | lands in `01-LAPORAN/`, hash equal | `SIAP: …/01-LAPORAN/STORAN-UIM.md`, `sha256 7f9ed20e…` |
| copy `.png` | auto-routes to `02-GAMBAR/` | ok |
| source under `$PREFIX/tmp` | refused, exit 3 | `GAGAL: source outside $HOME …` |
| source is a symlink | refused, exit 3 | `GAGAL: source is a SYMLINK …` |
| same filename twice | timestamp suffix, never silent overwrite | `uji_gambar-20261112-133752.png` |
| `--ke ../../etc` | refused, exit 64 | `GAGAL: invalid category` |
| folder copy | recursive + file count | `2 files, 15K` |
| auditor, clean state | silent, exit 0 | silent, code 0 |
| auditor + symlink to `/sdcard` | listed, exit 1 | `FORBIDDEN SYMLINK: …/gudang_pautan` |
| auditor + `.env.uji` in warehouse | listed, exit 1 | `SECRET IN WAREHOUSE: …/.env.uji` |

Cron wiring that worked: `cronjob(action='create', script='uim_semak.sh', no_agent=True,
schedule='0 8 * * *')` — script path resolves under `~/.hermes20/scripts/`; empty stdout means the
user sees nothing on a clean day; `action='run'` then showed `last_status: ok`.

## Log format (`~/.hermes20/logs/uim_hantar.log`)

```
<ISO date time> | <source abs path> | <dest abs path> | <sha256 first 16> | <bytes> bytes | <category>
<ISO date time> | FOLDER | <source> | <dest> | folder | <n> files
```
Folder copies log file counts only — hashing a tree is optional; re-run per-file if the user needs
per-file proof.

## Reporting shape the user expects

1. Component table (what · where · state) with absolute paths.
2. Guard-test table with the real messages and exit codes, not "tested successfully".
3. Log tail.
4. State the known limits honestly (top-level `/sdcard` not writable; auditor needs the
   `~/storage` exclusion; old warehouse copies are not auto-pruned).
5. End with 3–4 numbered next-step options; the user replies with a number.
