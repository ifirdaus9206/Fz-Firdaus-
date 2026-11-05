# Module roster — `~/.hermes20/system/`

Absolute path: `/data/data/com.termux/files/home/.hermes20/system/` (Termux, Android).

The 8 modules form the KETUA agent-factory pipeline. Each is a `<name>.md` file whose body is
the authoritative system prompt for that stage (newer style: plain markdown between
`<!-- MULA KANDUNGAN -->` / `<!-- TAMAT KANDUNGAN -->`; older style: a Python module with
`SYSTEM_PROMPT`, dataclasses and validators).

| Fail | Peranan | Bila dipakai |
|---|---|---|
| `agent_factory.md` | Arkitek tenaga kerja AI | Menerima objektif projek |
| `role_generator.md` | 12 medan spec peranan, merge & gap rule | Selepas analisis projek |
| `orchestrator.md` | Ketua pipeline, handoff, gate | Setiap penugasan & peralihan fasa |
| `workflow_generator.md` | DAG + WBS + gate | Selepas agent dijana |
| `memory_manager.md` | 4 lapisan memori, konteks berterusan | Setiap handoff |
| `qa_system.md` | Bukti mengatasi dakwaan, lalai NEEDS_WORK | Selepas setiap output |
| `recovery_system.md` | Pemulihan, rollback, eskalasi | Apabila gagal/blok |
| `completion_system.md` | Definisi selesai, verdict akhir | Penutupan projek |

Waajib flow (from SOUL.md):

```
objektif → agent_factory → role_generator → workflow_generator
        → orchestrator → qa_system → recovery_system (max 3) → completion_system
```

## Notes from real sessions

- The user re-authors these prompts periodically and wants the files emptied to a skeleton so
  they can paste new text themselves — they do NOT want the agent inventing replacement content.
- Sizes before a typical wipe (Oct 2026): agent_factory 6,420 B; orchestrator 6,165 B;
  role_generator 6,408 B; recovery 5,936 B; completion 5,514 B; memory 5,478 B; workflow 5,472 B;
  qa 4,649 B. Blank skeleton lands around 390–415 B.
- A `.bak` is only as good as its current byte count. The user has emptied a `.bak` by hand
  while tidying, so verify before promising the old version is recoverable.
