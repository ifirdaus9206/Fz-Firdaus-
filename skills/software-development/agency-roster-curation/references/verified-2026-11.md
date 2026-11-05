# Keadaan disahkan — November 2026 (`~/.hermes20`, Termux)

Rekod pemeriksaan sebenar, bukan andaian. Guna sebagai titik mula; sahkan semula sebelum bertindak.

## Kiraan dan laluan

- `plugins/agency-agents-router/data/agents.json` — **282 entri**, skema:
  `slug, name, description, division, color, emoji, vibe, source_path, body` (tiada `tools`).
- Korpus git: `~/.hermes20/agency-agents/` (26 divisi, subfolder untuk game-development).
- Korpus app / sumber build:
  `~/.hermes20/agency-agents-app/src-tauri/resources/corpus-baseline/`
- Fail persona contoh: `agency-agents/specialized/specialized-master-plan-architect.md` (7584 bait).
- Medan `tools:` hanya muncul dalam ~17 fail (marketing, paid-media, product, project-management,
  specialized). Nilai lazim: `WebFetch, WebSearch, Read, Write, Edit` (+ `Bash` pada 7 fail).

## Kes `master-plan-architect` (P1 "tiada akses shell")

Baris bermasalah dalam persona:

- `description:` — “…Implementation Plans in Markdown with **ZERO code execution**.”
- Peraturan #1 (sekitar baris 53) — “**ZERO CODE EXECUTION:** Never use file-editing or execution
  tools on production source code during your planning turn. Only author the Markdown blueprint.”
- Metrik (sekitar baris 146) — “Zero Unplanned Code Mutations: 100% … without illicit direct code
  execution.”

Diagnosis: bukan tool dikonfigurasi salah — persona melarang mutlak, dan frontmatter tiada `tools`.
Pembetulan: `tools: Read, Write, Edit, Bash` + tulis semula peraturan #1 supaya larangan mutasi
kekal tetapi pengesahan baca-sahaja dibenarkan dan **diwajibkan**; selaraskan metrik.

## Perangkap yang dijumpai semasa memeriksa

- `find … | head -1` kemudian `sed -n "$f"` boleh gagal dengan "No such file" jika pembolehubah
  mengandungi baris tambahan. Guna laluan literal atau `find -exec`.
- `du -sh ~/.hermes20/*` **timeout >120s** (node_modules, archive, tools/hermes-source).
  Ukur per-folder atau `du -sh --max-depth=1` pada calon tertentu sahaja.
- `session_search(session_id=...)` terpotong pada sesi panjang dan memulangkan mesej **awal**;
  untuk ekor sesi guna `sqlite3 state.db "… ORDER BY id DESC LIMIT 8"`.
- `hermes profile list` (Nov 2026): default (◆, gateway running) + `sofia`. `hermes profile`
  menyokong `rename`, jadi tukar nama profil tidak perlu `mv` manual + pembaikan rujukan.
