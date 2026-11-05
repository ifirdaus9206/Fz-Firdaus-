# Named profile provisioning (validated runs)

Task 1: "create a profile called Sofia, build its capabilities like the SOUL.md you wrote,
rename the old identity name to Sofia, then run everything."
Task 2 (P2): "rename profile `sofia` -> `siti`, and create 6 runnable agent profiles
(finance, sales, marketing, ops, engineering, assistant) — each with its own SOUL.md,
credentials, and a valid config."

Environment: Termux/Android, main home `~/.hermes20`, second home `~/.hermes19`,
launcher `$PREFIX/bin/hermes` -> source tree inside the main home.

## 1. Create the profile

```bash
hermes profile create sofia
# -> 71 bundled skills synced
# -> Wrapper created: ~/.local/bin/sofia
# -> warns: "This profile has no API keys yet"
```

Layout created: `profiles/sofia/{memories,sessions,skills,skins,logs,plans,workspace,cron,home}`,
plus `SOUL.md` (default Hermes text) and an empty `.env` template.

## 2. Make it callable for real

```bash
P=$HOME/.hermes20/profiles/sofia
cp $HOME/.hermes20/.env     "$P/.env"
cp $HOME/.hermes20/auth.json "$P/auth.json"
cp $HOME/.hermes20/config.yaml "$P/config.yaml"
chmod 600 "$P/.env" "$P/auth.json"

# a fresh profile has no plugins/ dir -> drop the block copied from the parent
~/.hermes_venvs/hermes19/bin/python - <<'PY'
import yaml
p="/data/data/com.termux/files/home/.hermes20/profiles/sofia/config.yaml"
d=yaml.safe_load(open(p)); d.pop("plugins", None)
yaml.safe_dump(d, open(p,"w"), sort_keys=False)
PY
```

Resulting `config.yaml` keeps `model.*` (provider/base_url/api_mode), `agent.max_turns`,
`display.tool_progress`, `session_reset`, `onboarding`, `fallback_providers`,
`_config_version`. In the P2 run the surviving key set was exactly:
`['_config_version','agent','display','fallback_providers','model','onboarding','session_reset']`
(491 bytes after `plugins` was dropped from the 546-byte parent copy).

## 3. Author the profile SOUL.md

Same shape as the second-home SOUL (see `second-home-verified-run.md`), with:

1. Identity block naming the agent (name, role, language, personality, 5 core principles).
2. Capability table (market analysis / risk / systems / engineering / data / research / docs).
3. Domain parameter tables (symbols, leverage, sessions).
4. Hard risk doctrine with numeric limits.
5. Workflow phases A–D.
6. Data-provenance & truthfulness discipline.
7. **Home map table** — the one addition a profile needs:

   | Konteks | Rumah | Arahan | SOUL yang dibaca |
   |---|---|---|---|
   | Utama | `~/.hermes20` | `hermes` | `~/.hermes20/SOUL.md` |
   | Dagangan | `~/.hermes19` | `hermes19` | `~/.hermes19/SOUL.md` |
   | Profil | `~/.hermes20/profiles/sofia` | `sofia` | profile `SOUL.md` |

8. Report format block.
9. Specialist roster (if the profile carries one) with the slugs copied from
   `data/agents.json`, never from memory.
10. Prohibitions, including "no work files outside the homes; ask before creating a new
    location".

## 4. Verify (three separate proofs)

```bash
hermes profile list              # default (◆) + sofia (alias: sofia)
sofia --version                  # v0.20.0 · upstream 3f2afed3
sofia chat -q "Nama awak siapa? Jawab satu ayat."
# -> "Saya Sofia — pembantu AI peribadi Bos untuk dagangan, analisis pasaran dan kejuruteraan sistem."
```

A profile that answers with its own name has both the SOUL load and the provider path
working. `--version` alone proves neither.

## 5. Scoped identity rename (old name -> new name)

```python
import os, re
roots = [f"{H}/skills", f"{H}/docs", f"{H}/memories", f"{H2}/skills", f"{H2}/ANIS"]
pat = re.compile(r"(?<![A-Za-z0-9_-])(Oldname|oldname)(?![A-Za-z0-9_-])")
skip = ("/legacy", "/archive", "node_modules", "__pycache__", "/venv", ".venv")
```

1. **Count pass first** — print `(file, hits)` for every match. 30 hits / 13 files is a
   realistic, reviewable scope for an identity rename.
2. **Rewrite pass**, same regex, same skip list; then recount and assert **0 remain**.
3. **Report** the file list, the total, and every folder name left untouched
   (`legacy-OLDNAME-*`, `oldname-downloads`, `oldname-launch`, `oldname_compress_plugin`)
   with the reason: renaming them breaks paths and imports.
4. Never touch `sessions/` dumps, vendor templates, or another home's live identity file
   without asking.

## 6. Multi-agent roster provisioning (P2 validated run)

Trigger: "tukar nama profil X -> Y dan cipta N profil ejen yang benar-benar boleh
dijalankan" — one home, N sibling profiles, each a runnable agent with its own identity.

### 6a. Rename first, verify the wrapper swap

```bash
hermes profile rename --help        # usage: hermes profile rename old_name new_name
hermes profile rename sofia siti
# ✓ Renamed sofia → siti
# ✓ Alias updated: siti
# Path: .../.hermes20/profiles/siti
```

Verify all three surfaces, because the rename moves the dir and the wrapper but does NOT
rewrite SOUL.md text:

```bash
hermes profile list                  # siti present, sofia gone
ls -1 ~/.hermes20/profiles/          # only siti
command -v sofia || echo "sofia: NOT FOUND"   # old wrapper is removed, not aliased
command -v siti
```

`hermes profile rename` leaves the old name inside SOUL.md. Fix only the identity lines —
do not rewrite the file:

```python
edits = [
 ("# SOUL.md — SOFIA", "# SOUL.md — SITI"),
 ("> Nama saya **Sofia**.", "> Nama saya **Siti**."),
 ("- **Nama**: Sofia", "- **Nama**: Siti"),
 ("| Profil ini | `~/.hermes20/profiles/sofia` | `sofia` | fail ini |",
  "| Profil ini | `~/.hermes20/profiles/siti` | `siti` | fail ini |"),
]
```

Assert `grep -c -i <oldname> SOUL.md` -> `0` and the line count is unchanged (151 here),
which proves nothing else was rewritten.

### 6b. Create N profiles in one loop, then one config pass

`hermes profile create <name>` per profile (it syncs bundled skills and writes the
wrapper). Then a single python pass over all names — copy + chmod + drop `plugins`:

```python
import yaml, shutil, os
H = os.path.expanduser("~/.hermes20")
for n in ["finance","sales","marketing","ops","engineering","assistant"]:
    P = f"{H}/profiles/{n}"
    for f in [".env", "auth.json", "config.yaml"]:
        shutil.copy2(f"{H}/{f}", f"{P}/{f}")
    for f in [".env", "auth.json"]:
        os.chmod(f"{P}/{f}", 0o600)
    p = f"{P}/config.yaml"
    d = yaml.safe_load(open(p))
    d.pop("plugins", None)
    yaml.safe_dump(d, open(p, "w"), sort_keys=False)
```

### 6c. Role-specific SOUL.md — write from a template dict, not freehand

Build one `template.format(...)` string and a `roles` dict (title, subtitle, agent name,
scope list of 6 items, "not-do" list). Validated structure that passed review:

1. `# SOUL.md — <NAME>` + subtitle
2. `> Nama saya **Ejen <Role>**...` (one-line identity)
3. Identiti (name / role / watak / bahasa)
4. `## SKOP KERJA` — numbered, 6 role-specific items
5. `## APA EJEN INI TIDAK BUAT` — explicit out-of-scope bullets (finance: no code;
   engineering: no budgets)
6. `## RUMAH KERJA` — `~/.hermes20/workspaces/<name>/` with inbox/outbox/notes
7. `## PERATURAN BUKTI` — no pass without real command output, no invented numbers,
   status SIAP/JALAN/GAGAL/BLOK
8. `## LARANGAN` — other profiles, main config, main SOUL.md, others' `.env`
9. `## PETA RUMAH` table, `## FORMAT LAPORAN`, `## BAHASA & GAYA`

Target 100–110 lines; the six profiles landed at 103–106 lines each (~3.9–4.2 KB).

### 6d. Verify per profile, then once globally

```bash
for n in finance sales marketing ops engineering assistant; do
  printf "%-12s " $n
  for f in .env auth.json config.yaml SOUL.md; do [ -f "$n/$f" ] && printf "%s " "$f" || printf "%s:MISSING " "$f"; done
  python3 -c "import yaml;d=yaml.safe_load(open('$n/config.yaml'));assert 'plugins' not in d;print('yaml-ok')"
done
```

Global proof set the user demanded: `hermes profile list` (default ◆ + siti + 6 roles),
`ls -1 profiles/`, `wc -l */SOUL.md`, `<name> --version` for all 7 wrappers, one real
`chat -q` on a single profile (not all six), and an unchanged-mtime check on the parent
identity:

```bash
ls -l --time-style=+%Y-%m-%d\ %H:%M ~/.hermes20/SOUL.md ~/.hermes20/config.yaml
```

Both must keep their original timestamps (5653 B / 00:55 and 546 B / 21:33 here) — that
is the proof the roster build never touched the default identity.

### 6e. Pitfalls specific to this run

- **Do not use `/tmp` for helper scripts.** The sandbox refused `open("/tmp/strip.py","w")`
  with `PermissionError`; write the helper under the home dir (e.g.
  `~/.hermes20/profiles/.strip_tmp.py`) and delete it afterwards.
- **Do not build SOUL bodies from `read_file` output without stripping line numbers.**
  `read_file` returns `NN|content`; copying it verbatim bakes `1|`, `2|` into the file and
  the line count inflates. Strip with `re.sub(r'^\d+\|', '', line)` and drop `---`
  separators before writing.
- **Chat-test one profile, not six.** Six `chat -q` calls burn provider quota and time;
  the user asked for exactly one functional chat proof (ops here).
- **Role profiles keep the role name, not the person's name.** `siti` stays the personal
  assistant; the six siblings use "Ejen Finance" etc. so a chat test identifies the right
  SOUL without ambiguity.

## Gotchas seen

| Symptom | Cause | Fix |
|---|---|---|
| New profile answers nothing / 401 | `.env` + `auth.json` never copied | copy both, chmod 600, re-test with `chat -q` |
| Plugin silently absent in profile | `plugins.enabled` copied but profile has no `plugins/` | drop the block, or copy the plugin dir too |
| `hermes tools` fails inside profile | needs a TTY | use `hermes profile list` / `plugins list` / `doctor` |
| Rename makes paths dead | bare-name regex replaced `name-tools` | lookaround regex, exclude folder tokens |
| Rename leaves old name in SOUL.md | rename only moves dir + wrapper | patch the 3–4 identity lines, assert 0 old hits |
| Old wrapper still resolves after rename | stale script in `~/.local/bin` | `command -v <old>` must be empty; delete leftovers |
| Config "valid" but profile is bare | `plugins` dropped without copying plugin dir | expected for role agents; verify key set = 7 |
