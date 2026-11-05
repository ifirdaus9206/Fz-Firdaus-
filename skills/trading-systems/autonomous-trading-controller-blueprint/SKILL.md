---
name: autonomous-trading-controller-blueprint
description: Create ATC blueprint directory structure and files exactly as specified.
category: trading-systems
---

# Autonomous Trading Controller Blueprint Creation Skill

## Purpose
Create a complete directory structure and file set for an Autonomous Trading Controller (ATC) blueprint as per user specifications, ensuring exact compliance with instructions, proper file placement, and structured documentation.

## When to Use
When the user requests to build the ATC blueprint with numerous files and folders (README.md, AGENTS.md, SYSTEM_PROMPT.md, config/, schemas/, prompts/, docs/, core/, brains/, market/, risk/, execution/, learning/, backtest/, monitoring/, tests/, etc.) and wants them either empty or filled with specific content.

## Prerequisites
- Hermes agent with access to file, terminal, and write_file tools.
- Working directory where the blueprint should be created (typically inside a Hermes profile, e.g., ~/.hermes19/ or a profile subdirectory).
- Clear understanding of the required file list and optional content (user may provide exact content or want empty files).

## Steps
1. **Determine target directory** 
   - If user specifies a profile (e.g., "Sofia"), use `~/.hermes19/profiles/<profile>/autonomous_trading_controller` or equivalent.
   - If user wants the blueprint at the profile root, use `~/.hermes19/autonomous_trading_controller`.
   - **Critical:** The user may request the profile directory name to be in a specific case (e.g., `.AINA` instead of `.Sofia` or `.hermes19` vs `.hermes20`). Always respect the exact case provided - do not assume or convert to lowercase/uppercase.
   - Confirm with user if unsure about the exact path or case.

2. **Create the directory** 
   ```bash
   mkdir -p <target_path>
   ```
   - Verify the directory was created at the exact path specified by the user
   - Use `pwd` to verify you're in the correct location before proceeding

3. **Create all required directories** (if not using a template): 
   ```
   config/
   schemas/
   prompts/
   docs/
   core/
   brains/
   market/
   risk/
   execution/
   learning/
   backtest/
   monitoring/
   tests/
   ```
   - Create each directory with `mkdir -p <directory_path>` to ensure parent paths exist
   - Verify each directory was created before proceeding

4. **Create empty placeholder files** for each item in the list (use `touch` or write_file with empty content): 
   - README.md
   - AGENTS.md
   - SYSTEM_PROMPT.md
   - .env.example
   - .gitignore
   - Plus all files under the subdirectories as per the user's list.
   - For each file, verify it was created at the exact location specified

5. **If user provides specific content** (e.g., from a blueprint template), write that content into the appropriate files using `write_file`. 
   - Ensure content matches exactly what the user supplied (no alterations, no summarizing, no reformatting)
   - For JSON files, validate syntax after writing using `python -m json.tool <file>` or equivalent
   - For Markdown files, do not modify the user's provided content unless explicitly instructed

6. **Verify the structure** 
   - Run `find <target_path> -type f | sort` to list all files
   - Compare with expected list - ensure every expected file exists at the exact path
   - Run a validation script to ensure JSON files are valid
   - Verify file sizes match expectations (0 bytes for empty files, expected size for content files)

7. **Report completion** 
   - Inform the user of the final location using the exact path they specified
   - Confirm that the blueprint is ready at that exact location
   - Offer to proceed with filling specific files if further instructions are given

## Auditing a scaffold after creation (do this before trusting it)

A scaffold that lists every file is **not** a working system. Run
`scripts/audit_atc_placeholders.py [PROJECT_ROOT]` — it reports empty modules, brains that
return literal constants, config keys no code reads, hardcoded decision fields, real test
collection, and one live orchestrator cycle.

```bash
python3 scripts/audit_atc_placeholders.py ~/.hermes19/autonomous_trading_controller
```

Interpretation rules:

- **Constant brains + unanimity fusion = permanent signal.** If all three `analyze()`
  functions return a literal `BUY`/`bullish`, fusion reports 3/3 agreement with fixed
  confidence 0.9, and `risk_engine` approves on `confidence >= 0.5`. The system then can
  never emit SELL or NO_TRADE. Never enable live trading in that state.
- **Trace imports, not file sizes.** Logic stranded outside the entry point
  (`run_paper.py` -> `core.orchestrator` -> brains/risk/execution) is dead weight. One
  project carried 421 lines of learning logic in `brains/learning-agent.py` that the
  orchestrator never imported.
- **A config file is a claim, not an implementation.** Grep every policy key
  (`risk_policy.json`, `decision_policy.json`) against `*.py`; zero references is the norm
  in fresh scaffolds.
- **`instruments.json` templates block position sizing.** While `contract_size`,
  `tick_value`, `tick_size` are `null`, lot calculation is untestable. Fill broker contract
  specs *before* writing `risk/position_sizing.py`.
- **`pytest tests` returning "no tests ran"** means the empty test files were never filled
  in; a present `tests/` directory is not coverage.
- Report the probe output verbatim, then a P0/P1/P2 add-list, then persist it as
  `docs/AUDIT_<topic>_<date>.md` inside the project. Classify legacy styles and old trees
  first, and ask before deleting anything.

## Turning a scaffold into a live-data paper loop

An audited scaffold can be made honest in one pass, without touching its architecture:

1. **Real candles, provider chain.** Add `market/data_feed.py` returning
   `(rows, meta)`; try the broker/paid source first, then a free one, and write
   `data/feed_status.json` (`source, symbol, price, last_time, proxy, errors[]`) on
   success *and* total failure. Never let a failed provider raise through the cycle.
2. **Bridge into the SDK venv instead of installing SDKs into system python.** Provider
   SDKs (e.g. `metaapi_cloud_sdk`) usually already live in a project venv; run a small
   `market/<provider>_bridge.py` with that interpreter, parse the last stdout line as JSON.
3. **MetaAPI reality check.** `GET /users/current/accounts` (header `auth-token`) works on
   the provisioning host `mt-provisioning-api-v1.agiliumtrade.agiliumtrade.ai`; market data
   requires the account `state == "DEPLOYED"`, and deployment is billing-gated
   (`ForbiddenException: … please top up your account`). Report that verbatim, then fall back.
4. **Free fallback with proxy honesty.** Yahoo `v8/finance/chart` has no `XAUUSD=X` (404):
   use `GC=F`/`SI=F`/`CL=F`/`BZ=F` and mark `proxy: true` in meta *and* UI; FX pairs are real.
   Resample `4h` from four `60m` bars if the source lacks it.
5. **Fix the clock.** Replace `timestamp: "2024-01-01…"` / `mode: "backtest"` in
   `core/decision_engine.py` with `datetime.now(timezone.utc).isoformat()` and a mode from
   `ATC_MODE`, and pass the requested `symbol` through. Then prove it from the CSV row, not
   the log banner.
6. **Control script with pid adoption.** `start|stop|status` that scans `/proc` for the
   worker's script name before trusting its pid file — a manually started loop otherwise
   reports MATI while alive.

Full implementation notes, measured evidence and the credential-archaeology discipline
(demo vs live tokens, `sha256[:8]` fingerprints, `0600` writes):
`localhost-monitoring-console` → `references/external-worker-monitoring.md` §7–§8.

## Pitfalls
- **Undercounting empty modules**: scanning only `market/`, `learning/`, `backtest/`, `monitoring/` misses `risk/`. Count with `wc -l <dir>/*.py | sort -n` across *every* package — one audit reported 18 empty modules when the real number was 21 (three in `risk/`). State the corrected number explicitly if a first count was wrong.
- **Deleting "old trading style" without a decision**: legacy trees (old bots, old backtest, old strategy engines, old skills in archives) are the user's money-making history. Classify and size them, then offer concrete options — delete, quarantine to `_old_<topic>_<date>/`, or keep — and act only on the answer. Expect "jangan padam apa-apa, saya nak semak sendiri"; in that case leave everything in place, confirm with `ls` + `du -sh`, and hand over the audit document instead of doing nothing.
- **Reporting a working pipeline as healthy**: `run_cycle()` returning `TRADE_CANDIDATE/BUY/0.9` is not success — check whether the fields are constants (`timestamp`, `mode`, `data_quality`, `symbol`) before describing the system as functional.
- **Incorrect placement**: Placing files in the wrong directory (e.g., putting config files under src/) will require rework. Always verify the target path before creating.
- **Overwriting existing content**: If the directory already exists and contains files, the user may want to preserve them. Ask before removing or overwriting.
- **Content mismatch**: If the user provides exact content, do not modify, rephrase, or summarize unless instructed. Use `write_file` to replace entire file content exactly as provided.
- **Missing directories**: Forgetting to create a subdirectory before placing files inside will cause errors. Create parent directories first with `mkdir -p`.
- **Case sensitivity**: Ensure filenames and directory names match exactly the case user provided (e.g., `.AINA` not `.Sofia`, `README.md` not `readme.md`). The file system may be case-sensitive.
- **Path assumption**: Never assume the profile directory name - always use exactly what the user specifies, even if it seems unconventional.
- **Tool failures**: When creating code-server or other tools, be prepared for architecture-specific issues (like ARM compatibility problems in Termux) and have fallback plans.
- **Environment file handling**: Do not overwrite an existing `.env` file without explicit user instruction. If `.env` does not exist, create it from `.env.example` or prompt the user to provide values. Never commit `.env` to version control.

## Verification
- After creation, run a quick check: 
  ```bash
  tree <target_path>   # if tree installed
  find <target_path> -type f | wc -l   # count files
  ```
- For JSON files, validate with `python -m json.tool <file>` or equivalent
- Verify the exact path matches what the user requested, including case sensitivity

## References
- See `references/session-detail.md` for any session-specific notes or user-provided content used in this blueprint creation.
- See `references/mt5_adapter_and_code_server_notes.md` for notes on MT5 adapter creation and code-server troubleshooting from the session where the user requested exact compliance with instructions and precise file placement.
- See `references/env_handling_best_practices.md` for best practices on handling environment variables and sensitive credentials like MetaAPI tokens.
- See `references/monitoring_and_paper_trading_scripts.md` for details on the live monitoring and paper trading scripts created to validate the ATC blueprint in real-time.
- See `references/placeholder-audit-3-brains.md` for the audited failure modes of a finished-looking 3-brain scaffold (constant brains -> permanent BUY, unread policy configs, `instruments.json` nulls blocking lot sizing, orphan learning logic, tests that collect nothing) plus the P0/P1/P2 remediation order.
- See `scripts/audit_atc_placeholders.py` — read-only audit runner: empty modules, constant brains, config keys never read, hardcoded decision fields, test collection, one live `run_cycle` probe.

## Example
User request: "buat satu persatu fail macam ni autonomous_trading_controller/ ..." with a list of folders and files.
Follow steps above to create the structure exactly as listed, respecting exact case and path specifications.

## Changelog
- Initial creation: captured from session where user requested ATC blueprint creation with precise file placement.
- Updated: Enhanced with stricter case sensitivity requirements, improved verification steps, and added troubleshooting notes based on session where user required exact compliance with instructions and precise file placement in .AINA profile.