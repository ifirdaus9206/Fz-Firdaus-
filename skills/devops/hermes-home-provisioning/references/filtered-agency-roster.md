# Filtered agency roster for a second Hermes home

Validated in a Termux session: a trading home (`~/.hermes19`) received 17 of 282
agency agents instead of the full roster. Full roster stays in the main home.

## Why filter

- 282 agents ≈ 4.2 MB of `agents.json`; tools are lazy but selection quality collapses
  when a generalist roster competes with domain work.
- A trading home needs finance/risk/model-QA/data specialists, not marketing or GIS.
- SOUL.md can then name the roster, so the agent knows which specialist to call for what.

## Install steps

```bash
SRC=~/.hermes20/plugins/agency-agents-router     # source plugin (full catalog)
DST=~/.hermes19/plugins/agency-agents-router     # target home

mkdir -p $DST/data
cp $SRC/__init__.py $SRC/plugin.yaml $DST/
```

Filter by `source_path` (the catalog stores repo-relative paths, so this keeps
`slug`, `name`, `description`, `division`, `color`, `emoji`, `vibe`, `body` intact):

```python
import json
chosen = [
  "finance/finance-financial-analyst.md",
  "finance/finance-investment-researcher.md",
  "finance/finance-fpa-analyst.md",
  "finance/finance-bookkeeper-controller.md",
  "academic/academic-statistician.md",
  "specialized/agents-orchestrator.md",
  "specialized/specialized-model-qa.md",
  "specialized/business-strategist.md",
  "engineering/engineering-data-engineer.md",
  "engineering/engineering-ai-engineer.md",
  "engineering/engineering-llm-post-training-engineer.md",
  "engineering/engineering-data-visualization-engineer.md",
  "testing/testing-reality-checker.md",
  "testing/testing-performance-benchmarker.md",
  "testing/testing-test-results-analyzer.md",
  "product/product-trend-researcher.md",
  "support/support-finance-tracker.md",
]
agents = json.load(open(f"{SRC}/data/agents.json"))
by_path = {a["source_path"]: a for a in agents}
selected = [by_path[p] for p in chosen]
missing = [p for p in chosen if p not in by_path]     # always print this
json.dump(selected, open(f"{DST}/data/agents.json", "w"), ensure_ascii=False, indent=1)
```

Enable the plugin (nested list → python3 + yaml, never hand-edit `config.yaml`):

```python
import yaml
p = "/home/<user>/.hermes19/config.yaml"
d = yaml.safe_load(open(p))
d.setdefault("plugins", {}).setdefault("enabled", []).append("agency-agents-router")
yaml.safe_dump(d, open(p, "w"), sort_keys=False)
```

## Verification (both required)

```bash
HERMES_HOME=$DST hermes plugins list | grep agency      # enabled | user
HERMES_HOME=$DST hermes chat -q "use agency_agents_search for 'risk'; \
list 3 finance agents and the roster size; do not guess"
```

Pass criteria: the answer names real slugs (e.g. `financial-analyst`, `fp-a-analyst`)
and does not invent agents. A `Duration: ~13s / Messages: 6 (4 tool calls)` shape is
normal for that probe.

Then record the roster in the home's `SOUL.md` as a table of
`role | agent (slug) | when to call`, plus usage rules (e.g. "live decisions require
Reality Checker + Statistician"). Keep slugs exact — `model-qa-specialist`, not `model-qa`.

## Rebuilding a catalog from a bundled app corpus

An agency-agents-app (Tauri) checkout carries its own catalog at
`src-tauri/resources/corpus-baseline/<division>/<division>-<agent>.md` (282 files, all
with `name/description/color/emoji/vibe` frontmatter).

- Slug = filename minus the `<division>-` prefix.
- Store `body` = file text *after* the frontmatter block.
- Compare before overwriting the installed catalog: path layouts drift (app flattens
  `game-development/unity-*.md`, repo nests it) and 60+ bodies may differ by version.
  Write a drift report first (`only-in-app`, `only-in-active`, `body-differs`), keep
  `agents.json.bak-<date>`, then rebuild and assert
  `len == expected`, `len(set(slug)) == len`, `all(body)`.
- Re-verify with a live tool call (`agency_agents_search`) — count and slug shape must
  reflect the new file.
