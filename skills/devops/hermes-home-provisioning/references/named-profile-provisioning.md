# Named profile provisioning (validated run)

Task: "create a profile called Sofia, build its capabilities like the SOUL.md you wrote,
rename the old identity name to Sofia, then run everything."

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
`_config_version`.

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

## Gotchas seen

| Symptom | Cause | Fix |
|---|---|---|
| New profile answers nothing / 401 | `.env` + `auth.json` never copied | copy both, chmod 600, re-test with `chat -q` |
| Plugin silently absent in profile | `plugins.enabled` copied but profile has no `plugins/` | drop the block, or copy the plugin dir too |
| `hermes tools` fails inside profile | needs a TTY | use `hermes profile list` / `plugins list` / `doctor` |
| Rename makes paths dead | bare-name regex replaced `name-tools` | lookaround regex, exclude folder tokens |
