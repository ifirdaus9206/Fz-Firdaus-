# Team-layer waves — blueprints that passed verification

Concrete artifacts from a real three-child wave (workspaces + Obsidian + LLM Wiki) that the lead
verified independently. Reuse the shapes, keep the prohibition list.

## Wave 1 / child A — workspace per role (P3)

```
~/.hermesNN/workspaces/
├── README.md              # index table: role | scope | inbox | outbox + 5 rules
├── finance/
│   ├── README.md          # 5–8 line scope + "APA EJEN INI TIDAK BUAT"
│   ├── AGENTS.md          # write-scope rule + inbox/outbox/notes flow + out-of-scope protocol
│   ├── inbox/.gitkeep
│   ├── outbox/.gitkeep
│   └── notes/.gitkeep
├── sales/ marketing/ ops/ engineering/ assistant/   # same shape
```

Result: 31 files (1 root README + 6 × 5). Two load-bearing lines inside each `AGENTS.md`:

```
Tulis **hanya** dalam ~/.hermesNN/workspaces/<role>/
JANGAN sentuh ~/.hermesNN/workspaces/<ejen-lain>/
```

Why it matters: without this, six roles write into one directory and the owner cannot tell whose
output is whose — the exact failure the video calls "konteks bercampur".

## Wave 1 / child B — long-term memory vault (P4)

```
~/vault/
├── README.md        # hub, alias "Rumah"; rule: notes = experience, facts → knowledge_base/
├── 00-Inbox/README.md
├── 10-Projek/README.md
├── 20-Ejen/{finance,sales,marketing,ops,engineering,assistant}.md
├── 30-Keputusan/2026-11-05-ketua-jadi-pengarah.md
├── 40-Pelajaran/README.md
├── 90-Arkib/
└── templates/nota-ejen.md    # frontmatter: tarikh, ejen, projek, tag, status
```

Result: 15 notes, 99 wikilinks, 17 unique targets. Proven two-way: `20-Ejen/<role>.md → [[README]]`
and `README.md → [[20-Ejen/<role>]]`. Cross-folder links use the layered form
`[[folder/README|label]]` because seven `README.md` files share one basename; the root hub gets a
unique alias so `[[Rumah]]` is unambiguous.

## Wave 1 / child C — knowledge base (P5)

See `references/knowledge-base-wiki.md` for page conventions; shape used:
`index.md`, `SCHEMA.md`, `log.md`, `sop/arahan-ejen.md`, `sop/backup.md`,
`fakta/status-sistem.md`, `fakta/enam-peranan.md`, `templat/brief-ejen.md` — 8 files, 29 internal
links, zero broken.

## Wave 1 / child D — runbook pair (P1 gap)

See `references/runbook-pair.md`. Trigger: `SOUL.md` header cites `OPERASI.md` + `docs/KETUA.md` and
`ls` says neither exists. A wave may be "done" and P1 still unfinished.

## Brief skeleton that produced clean output

```
OBJEKTIF / KONTEKS / INPUT / SKOP / LARANGAN / FORMAT OUTPUT / KRITERIA LULUS / DEADLINE
```

Two fields do most of the work:

- **LARANGAN** — name the forbidden paths explicitly (`config.yaml`, `SOUL.md`, `memories/`, `skills/`,
  `plugins/`, no `sudo`/`apt`) plus "jangan tulis di luar <scope> kecuali fail laporan".
- **FORMAT OUTPUT** — demand the *real* command output be pasted into `docs/LAPORAN-*.md`
  (`find ... | sort`, `wc -l`, `ls -la`), not a summary of it. That is what makes the verdict cheap.

## Lead verification (copy-paste)

```bash
find ~/.hermesNN/workspaces -type f | wc -l      # 31
find ~/vault -type f -name '*.md' | wc -l        # 15
find ~/.hermesNN/knowledge_base -type f | wc -l  # 8
ls -la ~/.hermesNN/docs/                         # LAPORAN-*.md present, with sizes
ls -la ~/.hermesNN/SOUL.md                       # mtime unchanged
grep -c '^## ' ~/.hermesNN/OPERASI.md            # section count, not just line count
grep -n 'P1\|P2\|P3\|P4' ~/.hermesNN/OPERASI.md  # escalation ladder really there
```

## Findings worth reporting, not silently fixing

- `SOUL.md` cites docs that do not exist → P1 incomplete (dispatch the runbook pair).
- A wiki page records "X tidak dijumpai" and a later wave creates X → the page is now wrong; queue it.
- Source doc self-contradicts ("11 lapisan" heading vs 14-row table) → record both in the wiki, do not
  reconcile by guessing.
- `gh` not authenticated / target dir not a git repo → backup layer is blocked; ask the owner for the
  account or repo instead of inventing a remote.
