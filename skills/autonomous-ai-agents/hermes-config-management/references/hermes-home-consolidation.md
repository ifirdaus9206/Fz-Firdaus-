# Consolidating a legacy Hermes home — worked reference

Companion to the "Consolidating a legacy Hermes home into the live one" section of `SKILL.md`.
Grounded in a real merge: two stale homes (`~/.AINA` with a nested `~/.AINA/.Sofia`) folded into
the live `~/.hermes20`, then the sources deleted.

---

## 1. What lives in a Hermes home — merge or drop?

| Path | Contains | Decision |
|------|----------|----------|
| `SOUL.md` | identity / roster registry | **merge**, but the live one wins. A 513-byte stub must never replace a generated 57 KB registry. |
| `config.yaml` | model, provider, plugins | **archive**; the live config is authoritative. Never copy an old one over a working one. |
| `.env` | secrets | **compare keys first** (below), then archive. |
| `auth.json`, `auth.lock` | provider credentials | archive — stale creds are worse than none. |
| `state.db`, `state.db-shm`, `state.db-wal` | conversation/session store | archive; merging SQLite from two homes is not worth it. |
| `verification_evidence.db` | evidence cache | archive. |
| `skills/<category>/<name>/` | skills | **merge** the ones absent live, into the correct category; skip identical. |
| `profiles/<profile>/<project>/` | per-profile project trees | **merge** if absent live; `diff -rq` first (may already be identical). |
| `pastes/` | user-pasted buffers | **preserve** verbatim under `archive/…/pastes/`. |
| `memories/` | `MEMORY.md`, `USER.md` | read before dropping; live files win, but skim for facts worth re-adding. |
| `cron/`, `hooks/` | jobs, hooks | usually empty; check with `find cron hooks -type f`. |
| `logs/`, `.hermes_history`, `interrupt_debug.log`, `.update_check` | forensics | archive. |
| `models_dev_cache.json` (~6 MB), `cache/`, `provider_models_cache.json`, `ollama_cloud_models_cache.json` | regenerable caches | archive under `_regenerable_cache/` (or skip). Never merge — they are large and refetched on demand. |
| `bin/<native tool>` | e.g. a 33 MB sandbox binary | **compare size/hash**; if the live `bin/` already has it, skip rather than duplicating 33 MB. |
| `sandboxes/`, `pairing/`, `audio_cache/`, `image_cache/` | scratch | archive or skip. |

Sizes seen: stale home with a nested home ≈ 57 MB; the archive of everything except one
duplicated binary ≈ 24 MB; ~2/3 of the raw bytes were regenerable caches.

---

## 2. Secrets check

```bash
sed 's/=.*/=***/' .OLD/.env
sed 's/=.*/=***/' .LIVE/.env
```

Real outcome: the legacy `.env` held only `OPENROUTER_API_KEY`, already present live (which had
an extra `HASS_URL`). Nothing lost. Write that finding into the manifest — "no secrets lost" is
the first question after a merge.

---

## 3. Duplicate detection actually pays

Running `diff -rq` before copying avoided three pointless copies in one merge:

- an 80-file project tree — byte-identical already (0 diff, both sides 80 files)
- a `project-scaffold` skill — identical
- `bin/tirith` — 33,852,096 bytes on both sides

Without the diff step the archive would have been ~57 MB of pure duplication.

---

## 4. Archive manifest shape

`archive/legacy-<NAME>-<YYYY-MM-DD>/README.md` — keep it short and decision-oriented:

```markdown
# Archive — legacy `.OLD` and `.OLD/.nested` homes

Consolidated into `~/.LIVE` on YYYY-MM-DD.
| Source | What it was | Size |
|---|---|---|

## What was MERGED into the live home (not archived)
| Item | Old location | New location | Notes |

## Nothing here is needed for Hermes to run
Everything is superseded or regenerable. Delete with:
    rm -rf ~/.LIVE/archive/legacy-OLD-YYYY-MM-DD
```

The "merged → where" table is what makes the merge auditable six months later.

---

## 5. Stale paths after merging skills

Merged skills and their `references/` files routinely hardcode the legacy home:

```
SKILL.md:  copy it to the Hermes workspace (`~/.hermes19/` ...)
```

Grep the whole merged category, rewrite, then prove discovery:

```bash
grep -rn "hermes19" .LIVE/skills/<category>/
# → rewrite hermes19 -> hermes20 in .md/.yaml/.py/.sh
```

Then confirm registration: `skills_list(category=<category>)` should return the new skills with
their descriptions. A file on disk that does not appear in `skills_list` is not installed.

---

## 6. Completeness gate, then delete

`scripts/verify_merge_completeness.py` is the gate. On the real merge the first pass reported
3 unaccounted files, all benign but invisible to a name check:

| Reported | Reality | Fix |
|----------|---------|-----|
| `models_dev_cache.json` | archived as `_regenerable_cache/AINA-models_dev_cache.json` | `--rename` |
| `.Sofia/models_dev_cache.json` | archived as `…/aina-nested-models_dev_cache.json` | `--rename` |
| `skills/.usage.json` (356 B) | distinct from the nested `skills/.usage.json` (828 B) — same name, different size, not yet archived | copy it, then re-run |

Lesson: a `(filename, size)` index alone is not enough — two files can share a name *and* differ,
and renames hide entirely. Always finish with the rename map plus SHA256 before `rm -rf`.

Final state of the worked merge:

```
source files scanned : 3
verified identical   : 2   (sha256 checked: 2)
intentionally skipped: 0
unaccounted          : 0
rename mismatches    : 0
RESULT: complete — safe to delete the source.
```

---

## 7. Post-delete verification

Removing a sibling home can still surface breakage, so verify behaviour, not listings:

```bash
hermes config get model.default        # still your model
hermes config check                    # no validation errors
hermes -z "Reply with exactly: OK"     # live provider round-trip
skills_list                            # merged skills discoverable
```

Observed trap: the live config had been left pointing at a `:free` model whose upstream idles
out. The merge is not "done" until a one-shot prompt actually returns.
