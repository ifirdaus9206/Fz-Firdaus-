# ATC Integration Notes (from session)

## Critical User-Fill Fields (.env)
| Field | Default | What to Set |
|-------|---------|-------------|
| `ATC_MODE` | `paper` | `paper`, `backtest`, or `live` |
| `ACCOUNT_BALANCE` | `30.00` | Your actual account balance |
| `ACCOUNT_CURRENCY` | `GBP` | Your currency code (USD, EUR, GBP, etc.) |
| `MT5_BRIDGE_TOKEN` | `atc_demo_token_001` | Your MetaAPI access token |

## Leverage Settings
| Symbol | Leverage | Notes |
|--------|----------|-------|
| `XAUUSD` | 100 | Gold - metals, highest leverage |
| `XAGUSD` | 100 | Silver - metals |
| `EURUSD` | 50 | Major forex pair |
| `GBPUSD` | 50 | Major forex pair |
| `USDCHF` | 50 | Major forex pair |
| `AUDUSD` | 50 | Major forex pair |
| `USDJPY` | 50 | Major forex pair |
| `WTI` | 20 | Crude oil |
| `BREN` | 20 | Brent crude |

## Risk Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `MAX_RISK_PER_TRADE` | `2.0` | Max % of equity risked per trade |
| `MAX_DAILY_DRAWDOWN` | `5.0` | Max % equity lost before system pauses |
| `MAX_CONCURRENT_POSITIONS` | `5` | Max open trades at once |
| `MIN_CONFIDENCE` | `0.55` | Minimum confidence for trade signal |

## Learning Agent Configuration
| Setting | Default | Description |
|---------|---------|-------------|
| `ENABLE_TRADE_LEARNING` | `true` | Track WIN/LOSS/NO_TRADE outcomes |
| `MIN_TRADES_BEFORE_ADJUST` | `10` | Trades before win rate re-evaluation |
| `WIN_RATE_THRESHOLD` | `0.55` | Win rate to keep current strategy |
| `MAX_CONSECUTIVE_LOSSES` | `5` | Forced pause after this many losses |

## Key Files & Their Purpose
| File | Purpose |
|------|---------|
| `AGENTS.md` | Lists all active agents with roles and confidence thresholds |
| `SYSTEM_PROMPT.md` | Complete ATC system directives and fail-closed rules |
| `run_monitor.py` | Live monitoring loop (60s interval, JSONL logging) |
| `run_paper.py` | Paper trading logger (configurable interval, CSV logging) |
| `decisions.log.jsonl` | Live trading decisions history (25+ records typical) |
| `paper_trading_log.csv` | Paper trading equity curve and trade outcomes |
| `.env` | Configuration with account settings and credentials |
| `.env.example` | Template - never commit this file |

## Verification Scripts
- `hermes-verify-env-config.py`: Validates .env has all critical fields populated
- `hermes-verify-structure.py`: Checks 14/14 directories present
- `hermes-verify-files.py`: Confirms key files exist with content
- `hermes-verify-agent.py`: Tests learning agent position sizing & confidence logic

## Integration Checklist (New Session)
- [ ] Copy .env template, fill critical fields
- [ ] Verify 14 directories exist in autonomous_trading_controller/
- [ ] Review AGENTS.md agent list
- [ ] SYSTEM_PROMPT.md fail-closed rules reviewed
- [ ] Run: `python3 hermes-verify-env-config.py`
- [ ] Paper trade: `python3 run_paper.py --interval 30`
- [ ] Monitor outputs: decisions.log.jsonl, paper_trading_log.csv