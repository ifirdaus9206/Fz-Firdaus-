# Audit: 3-brain ATC scaffold — placeholder logic findings

Source session: scaffolding created empty files as specified, then weeks later the user
asked "semak gaya trading ... ada apa yang perlu di tambah". The scaffold looked complete
(docs, config, schemas, tests, 40+ files) but was non-functional in a specific, dangerous
way. Recorded here so a future audit starts from the known failure modes instead of
rediscovering them.

## The headline failure: a permanent BUY machine

Probe:

```python
from core.orchestrator import run_cycle
run_cycle('XAUUSD')
```

Output:

```
status       : TRADE_CANDIDATE
direction    : BUY
confidence   : 0.9
timestamp    : 2024-01-01T00:00:00Z    # hardcoded
mode         : backtest                # hardcoded
data_quality : PASS                    # hardcoded
risk_result  : approved=True, calculated_risk=0.02   # dummy
```

Why it can never emit SELL or NO_TRADE:

1. `brains/fast_brain.py` → `return {"direction": "BUY", "timing_ok": True, ...}` (constant)
2. `brains/medium_brain.py` → `return {"direction": "BUY", "setup_valid": True, ...}` (constant)
3. `brains/long_brain.py` → `return {"bias": "bullish", "regime": "trending_up", ...}` (constant)
4. `core/fusion_engine.py` → unanimity rule: 3/3 BUY ⇒ `BUY`, confidence `0.9` (fixed)
5. `risk/risk_engine.py` → approves whenever `confidence >= 0.5`

Every cycle lands in step 5. Enabling live trading on this scaffold is a guaranteed
losing loop, not a strategy.

**Lesson:** unanimity-based fusion + constant brains = degenerate signal. Any fusion that
returns a *fixed* confidence on agreement should be treated as a red flag during review.

## Config that exists but no code reads

`config/decision_policy.json` defined weights 0.3/0.4/0.3, `min_agreement: 2`,
`thresholds.strong_signal: 0.7`, `conflict_resolution: defer_to_higher_timeframe`.
`fusion_engine.py` read none of it — it hardcoded "all three must agree".

`config/risk_policy.json` defined max daily loss 5%, max total exposure 20%,
max open trades, Kelly 0.5, ATR SL/TP multipliers, spread/slippage caps, kill switch,
correlation limit 0.7. `risk_engine.py` read none of it.

`config/model_registry.json` defined promotion thresholds; `learning/model_registry.py`
was 0 bytes.

**Lesson:** a config file is a claim, not an implementation. Grep each policy key against
`*.py` before believing the system honours it.

## Blocking data gap: instruments.json still a template

All instruments had `contract_size: null`, `tick_value: null`, `tick_size: null`,
`price_digits: null`, `broker_symbol: "SET_REAL_BROKER_SYMBOL"`.

Lot size = risk_amount / (stop_distance × tick_value per lot). With `tick_value` null,
**position sizing cannot be implemented or tested**. This is the first thing to fill from
the broker's contract specification, before writing `risk/position_sizing.py`.

## Empty-module inventory (21 of the 40+ scaffolded files)

market/{data_feed,data_validator,feature_engine,regime_detector}.py
learning/{evaluator,label_engine,model_registry,trade_memory,trainer,walk_forward}.py
backtest/{cost_model,performance_metrics,simulator}.py
execution/{execution_interface,order_reconciler}.py
monitoring/{drift_detector,health_check,logger}.py
risk/{exposure_manager,kill_switch,position_sizing}.py

Only real code present: `execution/mt5_adapter.py` (295), `brains/learning-agent.py` (421),
`core/orchestrator.py` (133), `run_paper.py` (130), `run_monitor.py` (79),
`fusion_engine` (45), `decision_engine` (35), `state_manager` (32), `risk_engine` (25).

**Orphan logic:** `brains/learning-agent.py` held 421 lines of genuine learning/sizing
logic but the orchestrator never imported it. Real code stranded outside the pipeline
looks like progress in a file listing and changes nothing at runtime — always trace
imports from the entry point (`run_paper.py` → `core.orchestrator` → brains/risk/execution).

## Tests that collect nothing

`python -m pytest tests -q` → `no tests ran in 0.02s`. The four test files existed but
contained no test functions (or imported empty modules). A green-looking `tests/`
directory is not coverage.

## Remediation order that actually unblocks the system

P0 — without this there are no three brains:
1. Real logic in fast/medium/long (branch on snapshot fields).
2. `market/data_feed.py` — MT5 bridge or local CSV, with an explicit fallback.
3. `market/data_validator.py` — missing candles, gaps, outliers, staleness.
4. `market/feature_engine.py` — ATR, swings, VWAP, momentum, spread stats.
5. `market/regime_detector.py` — trending / ranging / volatile.
6. A single `schemas/market_snapshot.schema.json` contract all three brains consume.
7. `fusion_engine` honours `decision_policy.json` (weights, min_agreement, thresholds,
   conflict resolution) instead of unanimity.
8. Real timestamp/mode/symbol in `decision_engine`.
9. `risk_engine` reads `risk_policy.json`.

P1 — money safety and learning:
10. Fill `config/instruments.json` from broker contract specs first.
11. `risk/position_sizing.py` — lots from equity × risk% ÷ (SL distance × tick value).
12. `risk/kill_switch.py` — consecutive-loss and drawdown stops.
13. `risk/exposure_manager.py` — exposure cap, XAU/XAG correlation, max open trades.
14. Wire `brains/learning-agent.py` into the orchestrator.
15. `trade_memory` + `label_engine` + `evaluator` — the WIN/LOSS/NO_TRADE loop.
16. Fast-brain spread/slippage/latency gate.
17. Session filter + tier-1 news calendar (the SOUL.md doctrine demanded it; code had none).

P2 — audit trail:
18. `backtest/simulator.py` + `cost_model.py` + `performance_metrics.py`.
19. `learning/walk_forward.py` + `model_registry.py` promotion gate.
20. `monitoring/*` + Telegram alerting (`.env` tokens were empty).
21. Make `tests/` collect real assertions per brain, fusion, and risk gate.

Until P1 item 11–13 are done: keep `ATC_MODE=paper` and `ATC_ALLOW_LIVE_TRADING=false`.

## Reporting shape the user accepted

Deliver: (a) the real probe output verbatim, (b) a table of empty modules, (c) which
config keys are unread, (d) a prioritized P0/P1/P2 add-list with counts, then (e) write it
to `docs/AUDIT_<topic>_<date>.md` in the project so the user can review offline. Ask before
deleting any legacy style/tree — this user reviews first and expects classification before
destructive action.
