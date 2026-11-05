# Persona edit & 3-way catalog sync (resipi penuh)

## Tiga salinan yang mesti segerak

| Peranan | Path |
|---|---|
| Sumber persona (repo git, subfolder) | `~/.hermes20/agency-agents/<division>/<division>-<slug>.md` |
| Korpus app (SUMBER build katalog) | `~/.hermes20/agency-agents-app/src-tauri/resources/corpus-baseline/<division>/<division>-<slug>.md` |
| Katalog aktif router | `~/.hermes20/plugins/agency-agents-router/data/agents.json` |

Korpus app menyimpan path rata (`game-development/unity-architect.md`); repo git menyimpan
subfolder (`game-development/unity/unity-architect.md`). Itu "beza susun atur", bukan drift.

## Logik sync yang mesti ditiru tepat

`~/.hermes20/scripts/sync_agency_catalog.py`:

```python
FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)

def parse_frontmatter(text):
    m = FM.match(text)
    meta, body = {}, text
    if m:
        body = text[m.end():]
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    return meta, body.strip()
```

Kunci entri tepat: `slug, name, description, division, color, emoji, vibe, source_path, body`.

```python
e["description"] = meta["description"]
e["body"] = body                       # sudah strip
# JANGAN tambah kunci "tools" ke JSON
json.dump(d, f, ensure_ascii=False, indent=1)
```

`--build` membaca corpus-baseline → kemas korpus dahulu, baru build.

## Semakan andal

```bash
cd ~/.hermes20
cp agency-agents/<div>/<div>-<slug>.md \
   agency-agents-app/src-tauri/resources/corpus-baseline/<div>/<div>-<slug>.md
cmp agency-agents/<div>/<div>-<slug>.md \
    agency-agents-app/src-tauri/resources/corpus-baseline/<div>/<div>-<slug>.md && echo IDENTIK
md5sum <kedua-dua fail>

cp plugins/agency-agents-router/data/agents.json \
   plugins/agency-agents-router/data/agents.json.bak-$(date +%Y%m%d-%H%M)
python3 scripts/sync_agency_catalog.py        # mod lalai = check
grep -c '<slug>' logs/agency-catalog-drift.txt   # 0 = tiada drift
```

## Contoh nyata: `master-plan-architect` (P1 — "tiada keupayaan mengesahkan")

Masalah: persona melarang Bash secara absolut ("ZERO CODE EXECUTION") sehingga tiada dakwaan
dalam pelan boleh disahkan. Peranan teras (pelan Markdown dahulu, red-team, tiada mutasi kod)
mesti kekal.

Suntingan:

1. Frontmatter — tambah selepas `emoji: "🏛️"`:
   `tools: Read, Write, Edit, Bash` (gaya ejen lain: `tools: WebFetch, WebSearch, Read, Write, Edit, Bash`).
2. `description` — "with ZERO code execution." →
   "with zero unplanned code execution and read-only shell verification."
3. Peraturan #1 → **PLAN-FIRST BOUNDARY — NO PRODUCTION MUTATION**: larangan mutasi kekal;
   kebenaran tegas untuk Bash baca-sahaja (`ls, cat, head, wc, grep, find, stat, git status,
   git log, curl -I, python3 -c` yang hanya membaca); setiap dakwaan mesti disokong output
   sebenar, jika tidak label "unverified"; sub-bullet "The write line": tulis/delete/install/push
   DILARANG, dicadang dalam pelan sahaja.
4. Dua rujukan frasa lama yang lain (baris pengenalan + tajuk "GOLDEN RULE") diselaraskan kepada
   "Plan-First, Read-Only Verification" / "PLAN FIRST, VERIFY READ-ONLY".
5. Metrik → "100% of plans produced without mutating production code; every factual claim backed
   by read-only shell output."

Keputusan: 282 entri kekal; `description`/`body` JSON sama tepat dengan fail; `cmp` dua fail
kembar rc=0; `grep -c 'tools: Read, Write, Edit, Bash'` = 1; hanya 1 slug berubah berbanding
backup (281 lain hash sama); `grep -c '<slug>' logs/agency-catalog-drift.txt` = 0.

Nota: laporan drift masih menyenaraikan 8 ejen lain (marketing, paid-media, spatial-computing)
di bawah "badan berbeza" — itu **pra-wujud** dan tidak disentuh; dibuktikan dengan perbandingan
backup→semasa yang menunjukkan hanya slug sasaran berubah.

## Prinsip yang boleh diulang

Melonggarkan larangan **bukan** membuangnya: sempitkan larangan kepada mutasi, tambah kebenaran
baca-sahaja yang boleh diaudit, dan kekalkan kewajipan bukti (output sebenar, bukan andaian).
