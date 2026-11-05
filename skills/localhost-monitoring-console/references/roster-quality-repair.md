# Roster quality repair — thin persona bodies, tier vs grade, archetype skew

Session evidence: `~/hermes-console`, roster of 282 agents, 2026-11-05.
Use when the user says *"baiki ejen tier C"*, *"naikkan kualiti roster"*, or asks why the
number of low-quality agents never drops.

## 0. Decide what "tier C" actually means before touching anything

The quality score is relative by construction:

```python
p85 = percentile(scores, 85); p40 = percentile(scores, 40)
tier = "A" if s >= p85 else "B" if s >= p40 else "C"   # always 15% / 45% / 40%
```

So **the count of tier C can never fall** — improve ten agents and ten others slide down.
Saying "I will fix the 112 tier-C agents" is therefore unfalsifiable. Add an **absolute**
band next to it and report that instead:

```python
gred = "kuat" if s >= 80 else "sederhana" if s >= 60 else "asas"   # <60 = asas
```

Measured before/after on 8 repaired agents: `asas 42 → 34`, `≥80: 83 → 89`,
median `75.0 → 76.0`, mean `72.7 → 74.0` — while tier stayed `A43/B127/C112` exactly.
Put both in the docs and in the UI badge (`TIER B · 76 · sederhana`) or the user will
(rightly) think nothing happened.

## 1. Diagnose: parser bug or genuinely thin source?

Compare catalogue body words against the source `.md` word count:

```python
mdw = len(source_md.split());  bodyw = len(agent["body"].split())
# mdw - bodyw ≈ 30-70 (frontmatter only)  →  body is complete, the document is thin
# mdw >> bodyw                            →  extraction/truncation bug, fix the builder
```

Measured: all 20 weakest had `md - body ≈ 32-71` words → frontmatter only, **no parser
bug**. They simply lacked operational sections. That distinction decides the whole plan
(fix the builder vs author the document).

## 2. Audit script — rank by absolute score, show the missing headings

Section detector (headings are matched case-insensitively as substrings):

```python
SEKSYEN = {
 "identity": ["identity & memory", "identity", "who you are"],
 "mission": ["core mission", "mission", "your mission"],
 "rules": ["critical rule", "rules", "guardrails"],
 "workflow": ["workflow", "process", "how you work"],
 "deliverables": ["deliverable", "output", "what you deliver"],
 "metrics": ["success metric", "metrics", "kpi"],
 "comms": ["communication style", "communication", "tone"],
 "memory": ["memory", "context", "what you remember"],
}
```

Output a markdown table (`reports/TIER-C.md`): rank · slug · division · score · grade ·
words · `n/8` sections · **missing headings**. The missing-heading column is what turns
"low score" into an actionable edit list. Beware: an agent can read `2/8` yet have real
content under different headings (`Key Technologies`, `Approach`, `Limitations`) — the
gap is the *operational* sections, not the expertise sections.

## 3. Enrichment pipeline (authoring, with hard gates)

Edit the **source `.md`**, then update the catalogue body, then rebuild the roster.
Never write a new body straight into the catalogue without the `.md` — the next catalogue
rebuild would silently revert it.

Prompt contract that worked (one agent per call, ~60–120 s on a congested provider):

- keep the YAML frontmatter **exactly** as-is; keep the H1;
- preserve every existing fact, technology name, constraint and limitation;
- add the missing sections using these exact headings:
  `## 🎯 Your Core Mission`, `## 🚨 Critical Rules`, `## 🔄 Your Workflow Process`,
  `## 📋 Your Deliverables`, `## 📊 Success Metrics`, `## 💬 Communication Style`,
  `## 🧠 Your Memory & Context`;
- never invent vendors, URLs, credentials, certifications, prices or client names;
- numbers allowed only as target thresholds, clearly framed;
- 750–1100 words in the body; output only the finished markdown.

**Always keep the original frontmatter**, whatever the model returns — it reorders keys and
re-quotes values. Validation gates (reject, do not "fix"):

```python
if not body.startswith("#"):                  reject("no H1")
if words_after < max(600, int(words_before*1.15)): reject("too short")
if len(missing_after) > 1:                    reject(f"still missing {missing_after}")
if re.search(r"\bTODO\b|lorem ipsum", body, re.I): reject("placeholder")
```

Persistence, with a way back:

```python
src.with_suffix(f".md.bak-{ts}").write_text(old_md)      # per-agent backup
CATALOG.with_name(f"agents.json.bak-{YYYYMMDD}")         # one catalogue backup per day
# then: python3 tools/build_ketua_roster.py
```

Measured result on the 8 worst (all gates passed first try except a frontmatter
mismatch, which is why the original frontmatter is reused rather than compared):

| agent | score | words |
|---|---|---|
| visionos-spatial-engineer | 24.5 → 87.7 | 343 → 1,282 |
| terminal-integration-specialist | 26.6 → 80.9 | 443 → 1,241 |
| xr-interface-architect | 29.1 → 75.6 | 192 → 980 |
| xr-immersive-developer | 32.8 → 83.7 | 214 → 1,074 |
| xr-cockpit-interaction-specialist | 34.9 → 70.0 | 201 → 958 |
| content-creator | 37.7 → 82.9 | 335 → 1,130 |
| growth-hacker | 37.7 → 84.0 | 340 → 1,343 |
| auditor | 43.9 → 85.6 | 650 → 1,741 |

After any catalogue edit, re-run the fleet sweep (`verify_roster.py`) — 282/282 must still
answer and the "short body" counter must drop to 0.

## 4. Archetype skew — do not force balance

Two tempting "fixes", one of them wrong:

- **IDF reweighting (rejected).** Weighting keywords by inverse document frequency sounds
  principled but punishes *definitional* words (`code`, `build`, `implement` appear in most
  bodies) and promotes rare decorative ones. Measured on 282 agents: 68 reclassifications,
  including `senior-developer → Pencipta`, `software-architect → Pencipta`,
  `pdf-engine-architect → Pencipta`. Test any classifier change offline against a sample
  and read the moved rows before adopting it; keep definitional keywords heavy.
- **Secondary archetype (adopted).** Store a second archetype when it reaches ≥60% of the
  top score — real agents are dual-role (incident responder = operations + investigation):

```python
calon = sorted(((v,k) for k,v in scores.items() if k != best), reverse=True)
kedua = calon[0][1] if calon and calon[0][0] >= 0.6 * scores[best] else None
```

Measured: 56/282 gained a second archetype; primary distribution unchanged (0 churn).
Surface it as a `juga: Pencipta` badge and let the planner use it.

- **A single-agent archetype is usually a true property of the roster.** `Penyiasat = 1`
  survived every honest reweighting because the corpus is engineering-heavy (94 builders,
  65 engineering agents). Say that plainly; the honest next step is *authoring new agents*
  for that role, not relabelling existing ones.

## 5. Weekly regression job (no_agent cron)

Hermes cron rejects absolute script paths → 3-line wrapper in `~/.hermesNN/scripts/`:

```python
import runpy, sys
TARGET = "/data/.../hermes-console/tools/weekly_check.py"
sys.argv[0] = TARGET
runpy.run_path(TARGET, run_name="__main__")
```

Job: `no_agent=true`, `schedule="0 9 * * 1"`, `script="ketua_weekly.py"`, `deliver="origin"`.
The script itself runs: `/api/agency/health` → fleet sweep → UI harness → offline LLM-retry
test → one real end-to-end case, then prints a compact Malay block.

Exit-code semantics matter: a script that exits 1 on a *soft* finding makes cron report
`error` and the user sees an alarm. Two traps hit in practice:

1. The E2E report had no `lulus` key, so `kes.get("lulus")` was `None` → false failure while
   the run had 2/2 agents done and a verdict. Either write `lulus` in the test, or derive it
   (`status=="done" and all agents done and final_aksara > 200`).
2. `STATUS AKHIR: NEEDS_WORK` is the QA system's **default verdict**, not a test failure.
   Judge the pipeline (ran, produced output, has a verdict), not the verdict's content.

Regenerate the report from `runs/*/run.json` (a `report_agents.py` that matches the latest
run per case) instead of merging partial test output — a single re-run otherwise wipes the
other cases from `test_agents_result.json`.

## 6. Delivery is a separate failure mode

`hermes send -t telegram` timed out once while the gateway chat was healthy; a retry 30 s
later succeeded in 5.5 s, and a direct `curl .../sendMessage` returned 200 in 1.7 s. Treat a
single delivery timeout as transient: retry once, prove the channel with a direct API call,
and only then diagnose. Do not record "Telegram delivery is broken".
