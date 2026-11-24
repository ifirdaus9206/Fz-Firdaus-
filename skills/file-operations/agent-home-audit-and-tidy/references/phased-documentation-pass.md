# Phased documentation pass — commands, report skeleton, measured outcome

Companion to `agent-home-audit-and-tidy`. Everything below was run on a 17 GB /
215k-file Termux agent home (`~/.hermes20`), 2026-11-24.

## 1. Phase 1 scope

In: `README.md`, `OPERASI.md`, `SOUL.md`, `docs/`, `system/`, `knowledge_base/`.
Out (later phases): `scripts/`, `tools/`, `logs/`, `cache/`, `profiles/`, `archive/`, `legacy-*`.

State the scope in the reply before starting — "Fasa 1 = dokumen teras, bukan `tools/`" — so the
owner does not read a partial pass as a missed one.

## 2. Read + completeness scan (one shot, no manual reading)

Cheap triage that separates "stub" from "complete" without opening 28 files by hand:

```python
import os, re
H = os.path.expanduser("~/.hermes20")
files = ["README.md", "OPERASI.md", "SOUL.md",
         "docs/README.md", "docs/KETUA.md", "docs/PELAN-AI-TEAM.md",
         "docs/STORAN-UIM.md", "docs/DASHBOARD.md", "docs/hermes-agent-summary.md"]
files += ["system/" + f for f in os.listdir(H + "/system") if f.endswith(".md")]
files += sorted(os.path.relpath(os.path.join(r, f), H)
                for r, _, fs in os.walk(H + "/knowledge_base") for f in fs if f.endswith(".md"))

for rel in files:
    t = open(os.path.join(H, rel), encoding="utf-8", errors="replace").read()
    stubs = len(re.findall(r"(?i)\b(TODO|TBD|FIXME|XXX|placeholder)\b", t))
    heads = len(re.findall(r"^#{1,3} ", t, re.M))
    print(f"{rel:42} {len(t):>6}b  h{heads}  stub{stubs}")
```

**Trap:** a naive `grep -i kosong` on Malay docs matches ordinary prose ("folder kosong",
"kosongkan cache") and reports healthy files as unfinished. Grep only real markers
(`TODO|TBD|FIXME|placeholder`); if the scan reports hits, print the matching **lines** before
believing it — one pass produced 17 "hits" that were all prose.

## 3. Which of these N scripts are actually used?

Cross-reference three sources, then classify. Unreferenced ≠ dead: manual tools live only here.

```python
import os, json, glob
H = os.path.expanduser("~/.hermes20"); S = H + "/scripts"
files = [f for f in sorted(os.listdir(S)) if os.path.isfile(os.path.join(S, f))]

jobs = json.load(open(H + "/cron/jobs.json"))
jobs = jobs if isinstance(jobs, list) else jobs.get("jobs", [])
cron = {j.get("script") for j in jobs if j.get("script")}          # AUTO - cron

runit = set()                                                      # AUTO - service
for p in glob.glob("/data/data/com.termux/files/usr/var/service/*/run"):
    t = open(p, encoding="utf-8", errors="replace").read()
    runit |= {f for f in files if f in t}

ref = {f: [] for f in files}                                       # called by other scripts
for f in files:
    for o in files:
        if o != f and f in open(os.path.join(S, o), encoding="utf-8", errors="replace").read():
            ref[f].append(o)

print("AUTO cron:", sorted(cron & set(files)))
print("AUTO service:", sorted(runit))
print("unreferenced:", [f for f in files if f not in cron and f not in runit and not ref[f]])
```

Measured on 35 scripts: 14 cron · 2 service · 13 manual · 6 true one-shots
(`*_once.sh`, `gw_handover.sh`, `probe_*.py`, `repro_runner.py`).

Then syntax-check everything before claiming the folder is healthy:

```bash
for f in scripts/*.sh; do bash -n "$f" || echo "ROSAK $f"; done
for f in scripts/*.py; do python3 -m py_compile "$f" || echo "ROSAK $f"; done
rm -rf scripts/__pycache__
```

## 4. Route inventory for a FastAPI console (feeds `docs/API-KONSOL.md`)

```python
import re
src = open("/data/data/com.termux/files/home/hermes-console/app.py", encoding="utf-8").read()
routes = re.findall(r'@app\.(get|post|put|delete)\("([^"]+)"\)', src)
print(len(routes))
for m, p in sorted(routes, key=lambda r: r[1]):
    print(f"{m.upper():6} {p}")
```

72 routes → 11 groups. Grouping is what makes the doc usable; a flat list of 72 is not.

## 5. Phase report skeleton (`docs/LAPORAN-FASA-N.md`)

```markdown
# LAPORAN FASA N — <kerja>
**Tarikh:** YYYY-MM-DD · **Skop:** <folders> · **Status:** SIAP · **Tiada fail dipadam**

## 1. Fail yang dibaca (N) — untuk semakan bos
| Fail | Saiz | Status |
|---|---|---|
| `path` | 2518 b | DIBINA SEMULA (dulu 39 b) |

## 2. Isi yang ditambah
| Fail | Apa ditambah | Sebab |

## 3. Penyusunan (bukan pemadaman)
| Kerja | Hasil |

## 4. Cadangan lanjutan
| Cadangan | Faedah | Risiko |

## 5. Belum disentuh (fasa berikut)
| Item | Saiz | Fasa |

## 6. Semakan pantas
```bash
ls docs/ ; ls system/ ; head -30 README.md
```
```

Section 1 is the section the owner actually audits. Keep it exhaustive — every file touched or
read, with byte size, because size is what proves a stub was rebuilt.

## 6. What the owner accepted as "done"

- Phase 1: 28 files read; 6 new docs; `README.md` rebuilt 39 B → 2.5 KB; `bin/<old-home>` turned
  into a warning shim; root `*.bak` → `backups/`; evidence reports → `docs/arkib/`.
- Phase 2: 35 scripts read, syntax 35/35, documented in `docs/SKRIP.md`, six one-shots **flagged
  but not deleted**.
- Every phase ended with a written report + spot-check commands + the line
  "tiada fail dipadam dalam fasa ini", and the next phase started only after the owner said
  "sahkan / mula fasa N".

Deletion never happened inside a phase — it stayed queued as the last phase, which is exactly what
the owner asked for.
