# runit supervision for a Termux console + schematic guides

Measured on Xiaomi 25080RABDG (HyperOS, Android 16), Termux from Google Play, home `~/.hermes20`,
2026-11-10. Console = FastAPI `app.py` on 127.0.0.1:8787; legacy service `web-server` = AINA live
server on 8081 that crash-looped.

## 1. Diagnose before touching anything

```bash
sv status <svc>                      # 'down: Ns, normally up, want up' = crash loop
ls -la $PREFIX/var/service/          # which services exist (no trailing slash in listing seen)
cat $PREFIX/var/service/<svc>/run    # the actual command
find ~ -maxdepth 4 -type f -size +10M \( -name '*.log' -o -name '*log*' \) -printf '%s %p\n' | sort -rn
ps aux | grep -E 'app.py|runsv' | grep -v grep
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8787/
```

Two `python3 app.py` rows under the same cwd are **orphans**, not a supervisor: they survive until the
phone kills them. `ss -ltnp` needs netlink permission on Android; `lsof -p <pid>` returns nothing —
identify a console by `cat ~/hermes-console/run/*.pid` (`server-8787.pid`) instead.

## 2. Stop a service permanently (not just `sv down`)

```bash
sv down web-server
printf 'down\n' > $PREFIX/var/service/web-server/down && chmod 644 .../web-server/down
sv status web-server            # 'down: web-server: 17s'  (no more 'normally up')
: > ~/.web-server.log           # truncate; keeps the inode if a dead writer still holds it
```

Why the extra file: `$PREFIX/etc/profile.d/start-services.sh` runs `service-daemon start` on every
Termux shell start, which brings up **every** service without a `down` file. `sv down` alone is
forgotten after that rescan.

## 3. Register the console under runit

`$PREFIX/var/service/hermes-console/run` (mode 755):

```sh
#!/bin/sh
export HOME=/data/data/com.termux/files/home
export PATH=/data/data/com.termux/files/usr/bin:$HOME/.local/bin:$PATH
export CONSOLE_HOST=127.0.0.1
export CONSOLE_PORT=8787
export PYTHONUNBUFFERED=1
cd "$HOME/hermes-console" || exit 1
exec 2>&1
exec /data/data/com.termux/files/usr/bin/python3 -u app.py
```

`.../hermes-console/log/run`:

```sh
#!/bin/sh
exec svlogd -tt /data/data/com.termux/files/home/.hermes20/logs/hermes-console
```

`~/.hermes20/logs/hermes-console/config`:

```
s1000000     # rotate at 1 MB
n5           # keep 5 old files -> ceiling ~5 MB
```

Sequence that actually worked:

```bash
chmod 755 $PREFIX/var/service/hermes-console/run $PREFIX/var/service/hermes-console/log/run
kill 25498 25549            # the orphans; runsv already started the new instance
sv status hermes-console    # 'run: hermes-console: (pid N) 5s; run: log: (pid M)'
tail ~/.hermes20/logs/hermes-console/current
# 2026-11-10_11:52:58.68042 HERMES CONSOLE → http://127.0.0.1:8787  [home=hermes20 · tab=pusat]
```

Traps seen:

- runsv reported `run:` while the **orphan still owned 8787** — `curl` answered 200 and the service
  looked fine. Only after `kill -9` of the orphan did `ps` show a single `app.py`. Verify with
  `ps aux | grep app.py | grep -v grep` (exactly one row) plus `curl /api/ping`.
- The log stayed at **0 bytes** until `-u` / `PYTHONUNBUFFERED=1` was added: Python block-buffers when
  stdout is a pipe.

## 4. Auto-restart drill (quote both observations)

```bash
PID=$(cat ~/hermes-console/server-8787.pid); kill -9 "$PID"; sleep 6
sv status hermes-console                  # new pid
cat ~/hermes-console/server-8787.pid      # differs from $PID
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8787/api/ping
```

Measured: `19095 → 19229`, `23704 → 23848`, `24089 → 25360`, each recovered < 6 s with ping 200.

## 5. Boot ceiling (say it out loud)

- `~/.termux/boot/*.sh` only runs when **Termux:Boot** is installed; `pm list packages | grep termux`
  showed only `com.termux`, so the boot script is inert.
- `$PREFIX/etc/profile.d/start-services.sh` brings the daemon (and therefore every service) up when a
  Termux shell starts → after a reboot the console returns **when Termux is opened**, not by itself.
- Never write "auto-start selepas reboot" without that qualifier.

## 6. Smoke-test script pattern

`scripts/smoke_test_runit_service.sh` (generic): service state, `/api/ping`, key asset URLs, log
directory size, and a kill-drill check. Two implementation notes learned the hard way:

- `curl -o /tmp/x` gives an empty body ( `/tmp` unwritable) and `|| echo 000` produced the absurd code
  `200000`. Use `TMPF=$(mktemp "${TMPDIR:-$HOME}/uji.XXXXXX")`.
- Print `[LULUS]`/`[GAGAL]` with the evidence inline and `exit $FAIL` — the report then quotes real
  lines instead of a summary.

## 7. Schematic (SVG) guide images

Generator → `static/img/panduan/*.svg`, preview → `rsvg-convert -w 480 x.svg -o preview/x.png`,
then read the PNG with `vision_analyze` and fix what you see.

Reusable helper shapes: dark phone frame `720x1280`, status bar, title bar, `baris(y, icon, title, sub,
right=on|chev, sorot)`, vector `ikon()` for gear/grid/shield/battery/screen/up/bell/lock/key, and
`label_anak_panah()` = yellow label + arrow + target dot.

Defects the proofread pass found (fix these patterns up-front):

| Symptom | Cause | Fix |
|---|---|---|
| label cut off at the right edge | `teks(..., anchor="start")` at `x=600` of 720 | `text-anchor="end"` at `W - 70`, arrow to the element |
| empty circles where icons should be | emoji glyphs, missing from `rsvg-convert` fonts | draw paths in `ikon()` |
| two options with the same label in one sheet | duplicated list entry while iterating | one entry per real option; mark the chosen one with a `PILIH INI` pill |
| arrow pointing into the gap between rows | arrow endpoint guessed from row height | point at the row's radio/chevron `cy` |
| sub-text over the icon tile | sub-line x reused the tile's x | sub starts after the tile (`x + 94`) |

CSS: portrait images need their own class, because `.stepimg` (`aspect-ratio:1000/620;object-fit:cover`)
crops them:

```css
.hguides{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px}
.hguide img{width:100%;aspect-ratio:720/1280;object-fit:contain;background:#050807}
```

## 8. HyperOS persistence content (the three settings users always need)

Panel copy that matches this device (HyperOS 2 / Android 16):

1. **Autostart** — Seting › Apl › Urus apl → Termux → suis **Autostart** = hijau.
2. **Bateri → Tiada had** — same app page → **Bateri** → `Tiada had` (repeat for `Termux:API`,
   `Termux:Boot` if present). This is what stops the freezer/LMK from killing Termux when the screen
   goes off.
3. **Kunci kad Recents** — open Recents, long-press the Termux card, tap the lock icon; the card
   survives "clear all".
4. Optional 4th: `termux-wake-lock` (works without the API add-on).

Caption must say the images are UI schematics, not real screenshots, and point at
`SISTEM → TANGKAP SKRIN PERANTI` (`POST /api/device/shot`) for replacing them once ADB is paired.
