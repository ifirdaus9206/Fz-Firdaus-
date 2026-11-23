# Two-tier agent memory: daily log + distilled long-term facts

Trigger: the owner says *"tambah memori masa pendek dan memori masa panjang supaya kau boleh
belajar lebih setiap hari"*. `memories/*.md` is already the injected scratch file; this is the
durable layer **outside** it, so facts survive context compaction and can be audited as plain files.

## Layout

```
~/vault/memori/
  01-pendek/YYYY-MM-DD.md      # short-term: one bullet per fact/event, appended all day
  02-panjang/MEMORI-PANJANG.md # long-term: deduped, categorised, <4000 chars
  03-pelajaran/YYYY-MM.md      # lessons rolled up per month
```

## Short-term writer (called by the agent, not by cron)

```bash
#!/data/data/com.termux/files/usr/bin/bash
# memori_pendek.sh "teks fakta" [tag]
set -u
BASE="$HOME/vault/memori"; DAY="$(date +%Y-%m-%d)"; F="$BASE/01-pendek/$DAY.md"
TAG="${2:-umum}"; TXT="${1:-}"
[ -z "$TXT" ] && { echo "Guna: memori_pendek.sh \"teks\" [tag]"; exit 2; }
[ -f "$F" ] || printf '# Memori Pendek %s\n\n' "$DAY" > "$F"
printf -- '- %s | [%s] %s\n' "$(date +%H:%M)" "$TAG" "$TXT" >> "$F"
```

Keep the append **cheap and dumb** — no LLM call per fact. The intelligence belongs in the nightly
distillation, otherwise every small observation costs a model round-trip.

## Digest builder (deterministic, no LLM)

`memori_panjang.py [hari]` prints the current long-term file plus the last N days of short-term
bullets as `### YYYY-MM-DD` sections, and echoes the target paths. That stdout is the **context**
handed to the distillation cron job — the script never summarises, so it can be re-run and diffed.

```python
base = pathlib.Path(os.path.expanduser("~/vault/memori"))
pendek = base / "01-pendek"
panjang = base / "02-panjang" / "MEMORI-PANJANG.md"
for i in range(days):
    d = today - datetime.timedelta(days=i)
    f = pendek / f"{d.isoformat()}.md"
    if f.exists():
        body = [l for l in f.read_text().splitlines() if l.startswith("- ")]
        if body: chunks.append(f"### {d.isoformat()}\n" + "\n".join(body))
```

## Nightly distillation cron

Prompt shape (silent, local delivery):

```
Jalankan: python3 ~/.hermes20/scripts/memori_panjang.py 7. Baca output.
Kemudian tulis semula ~/vault/memori/02-panjang/MEMORI-PANJANG.md: gabungkan fakta penting,
buang duplikasi, kekalkan di bawah 4000 aksara, susun ikut kategori (sistem, bos, projek,
pelajaran). Tulis juga ~/vault/memori/03-pelajaran/YYYY-MM.md dengan 3-5 pelajaran bulan ini.
Jangan hantar mesej; kerja senyap.
```

- `deliver: local` — the owner's rule is "cron senyap bila sihat".
- `schedule: 30 23 * * *` (after the 21:00 daily report, before the 02:00 git backup so the
  distilled file is inside that night's commit).
- Toolsets limited to `["terminal","file"]`.

## Seed the long-term file by hand the first day

Do **not** wait for the first cron tick to prove the feature. Write `MEMORI-PANJANG.md` once with
the facts you already have (environment paths, owner preferences, project inventory, lessons), then
let the nightly job maintain it. A cron job that has never fired is not evidence the memory tier
works; a populated file the console/agent can read is.

Good sections for that first file: **SISTEM** (homes, ports, services that are off), **BOS**
(preferences that reduce steering), **PROJEK** (what exists and where), **PELAJARAN** (things that
cost time and must not be relearned).

## Evidence to report

```bash
ls ~/vault/memori/01-pendek/ ~/vault/memori/02-panjang/
head -12 ~/vault/memori/02-panjang/MEMORI-PANJANG.md
hermes cron list | grep -A4 'Suling memori'      # schedule + deliver: local
```

Report the byte sizes and the cron id — "memory installed" without the files on disk is a claim.

## Pitfall — `hermes cron create` drops later parameters

Measured: calls carrying `script`, `no_agent`, `workdir` and `deliver` together failed with
`schedule is required` / `create requires either prompt or at least one skill`, because the later
keys never reached the job. Two-step that always worked:

```text
1) create with the minimum set: action=create, prompt=<short>, schedule=<cron>
2) update the returned job_id with script / no_agent / deliver / toolsets, one concern at a time
   (setting no_agent=true before script exists errors: "Cannot set no_agent=True on a job without a script")
```

Order matters on update as well: add `script` first, then flip `no_agent`, then `deliver`.
