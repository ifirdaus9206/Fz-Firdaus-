---
name: hermes-system-prompt-modules
description: Blank, back up, refill system/*.md prompt modules.
version: 1.0.0
author: Hermes Agent
license: MIT
categories: [software-development, hermes]
---

# Hermes System Prompt Modules

**Trigger:** User asks to empty / wipe / replace the contents of one or more files in
`~/.hermes20/system/` (agent_factory, role_generator, orchestrator, workflow_generator,
memory_manager, qa_system, recovery_system, completion_system), or says "kosongkan fail itu",
"padam isi", "aku akan masukan balik", or pastes a new long prompt to be installed as a module.

**Class of work:** destructive-but-reversible content replacement on a fixed set of prompt
module files, where the user intends to author the new content themselves.

## Non-negotiable order

1. **Stat first, never assume.** `ls -la` + `wc -c *` on `~/.hermes20/system/`. The user often
   edits these files by hand between messages — a read from two turns ago is stale.
2. **Back up before wiping — outside the folder.** Backups do NOT belong in `system/`.
   Copy to `~/.hermes20/archive/system-backup-<YYYY-MM-DD>/f.md.bak` and confirm the byte
   count in the same command. The user counts files: 8 modules + 8 sibling `.bak` read as
   "kenapa fail ni dah jadi banyak". Never wipe without a verified copy; never clutter the
   module folder with one.
3. **Blank to a marker skeleton, not to 0 bytes.** A zero-byte file gives the user no
   insertion point. Use `templates/blank-module.md`: header + `<!-- MULA KANDUNGAN -->` /
   `<!-- TAMAT KANDUNGAN -->`.
4. **Wait for replacement content before wiping anything else.** If the user says "kosongkan
   dan masukkan ini" but the prompt body is missing, do NOT destroy the file — ask for the
   text first (see Long-prompt truncation below).
5. **Refill, then tidy.** After the user pastes their content between the markers, fix the
   cosmetic damage: a paste usually lands on the *same line* as the `MULA` marker. Patch in a
   blank line. Update the `# STATUS:` header line to `TERISI` with the date.
6. **Verify and report a table.** `wc -c *` and present `| Fail | Saiz | Status |` — the user
   expects structured, evidence-backed reporting, not prose claims.

## Refill format: the Python module is the live convention

Latest instruction from this user (agent_factory + role_generator, both v2.0):
**"ikut code arahan python setiap satu"** — each file is markdown header + one fenced
```python block containing `SYSTEM_PROMPT = r"""…"""`, schema tuples, a `@dataclass …Spec`,
and a `validate_…()` function. Full recipe, schema mapping and verbatim-fidelity rules:
`references/python-module-convention.md`. Copy the shape from
`templates/python-prompt-module.md`.

Older blank skeletons use markdown between `<!-- MULA KANDUNGAN -->` markers. Do not assume
either format — the format of the *neighbouring filled files* wins; if the folder is a mix,
ask.

**Always smoke-test what you wrote** (compile alone is not proof — the module must import):

```bash
python3 ~/.hermes20/skills/software-development/hermes-system-prompt-modules/scripts/verify_prompt_module.py ~/.hermes20/system/<name>.md
```

Then report `PROMPT_LEN`, schema tuple counts, and both branches of the validator
(empty spec → N errors, complete spec → `[]`) as evidence in the status table.



## Batch-safe wiping (multiple files)

Use `execute_code` looping `terminal(cp ...)` + `write_file(...)` so 15 stat/copy/write calls
happen in one pass. Immediately after the batch, re-run `ls`/`wc -c` — do not trust the
per-file return values alone, because the user may have written into a file mid-batch.

## Long-prompt truncation (Telegram / chat)

Long prompts (>~4 KB) get silently cut off when sent through chat. When the user's message
reads like an instruction but the body is absent, assume truncation, not forgetfulness.

Tell them the three ways to deliver it:
1. Chunked: `BAHAGIAN 1/N:` … each chunk under ~3,500 characters.
2. As an uploaded `.md` / `.txt` file — read it directly, no length limit.
3. Paste straight into the file themselves between the markers (what this user prefers).

## Pitfalls

- ❌ Wiping first, asking later. Backup + blank skeleton is reversible; a wiped `.bak` is not.
- ❌ `write_file` on a file previously read with `offset`/`limit` — the tool warns
  "last read with offset/limit pagination". Read the whole file (or `wc -c`) before overwriting.
- ❌ Assuming the `.bak` still holds the old content. The user may empty it themselves while
  tidying (seen: `agent_factory.md.bak` reduced 6,420 B → 1 B). Always re-stat backups and say
  plainly when an old version is gone for good.
- ❌ Reporting "KOSONG" for files the user has already refilled — re-check before every status
  table; their edits are authoritative.
- ❌ Guessing the refill format. Both exist: plain markdown between comment markers (older)
  and a full `SYSTEM_PROMPT = r"""…"""` python module with dataclass + validator (current
  preference — *"ikut code arahan python setiap satu"*). Mirror the neighbouring filled files.
- ❌ Dropping `.bak` files next to the modules. The user reads that as files multiplying
  ("kenapa fail ni dah jadi bayak"); back up to `~/.hermes20/archive/system-backup-<date>/`.
  Strip stale `# Fail lama diarkibkan di:` header lines that name the old in-folder `.bak`.
  If the user wants the folder truly clean, say where the archive lives and offer `rm` rather
  than deleting it unasked.
- ❌ Embellishing the user's prompt while "converting" it to Python. Copy verbatim; fix layout
  only (numbering, bullets, one `✓` per line). Adding a field the user did not list is a defect.
- ❌ `py_compile` as proof. It passes while the module still cannot import: a
  `@dataclass(slots=True)` loaded via `spec_from_file_location` + `exec_module` raises
  `AttributeError: 'NoneType' object has no attribute '__dict__'` (module not in `sys.modules`).
  Verify with `runpy.run_path` — `scripts/verify_prompt_module.py` does it.
- ❌ Treating `*.md` module files as Python modules unless asked. Older versions wrapped the
  prompt in `SYSTEM_PROMPT = r"""…"""` with dataclasses/validators; the newer authoring style is
  plain markdown between HTML comment markers. Ask which format if unclear.

## Support files

- `templates/blank-module.md` — skeleton to copy per file (header + content markers).
- `references/module-roster.md` — role of each of the 8 modules and the pipeline they form.
