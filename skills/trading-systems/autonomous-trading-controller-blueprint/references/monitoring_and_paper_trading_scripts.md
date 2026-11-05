# Monitoring and Paper Trading Scripts for ATC Blueprint

## Overview
This document details the two validation scripts created to test the Autonomous Trading Controller (ATC) blueprint in real-time conditions:
1. `run_monitor.py` - Live monitoring loop that runs the orchestrator every minute and logs decisions to JSON Lines
2. `run_paper.py` - Paper trading logger that runs the orchestrator at a configurable interval and logs detailed decisions to CSV

## Live Monitoring Script (`run_monitor.py`)

### Purpose
Continuously runs the ATC orchestrator at regular intervals (default 60 seconds) and logs each decision with timestamp for real-time monitoring of the trading system's behavior.

### Key Features
- Loads environment variables from `.env` file manually (avoids external dependencies)
- Adds ATC root to Python path for proper module imports
- Imports and runs the orchestrator's `run_cycle()` function
- Logs each decision as a JSON Line (JSONL) to `decisions.log.jsonl`
- Provides real-time console feedback with timestamp and decision summary
- Handles keyboard interrupt gracefully for clean shutdown
- Calculates dynamic sleep time to maintain consistent interval despite processing time

### Output Format (JSON Lines)
Each line in `decisions.log.jsonl` is a valid JSON object containing:
```json
{
  "timestamp_utc": "2026-10-16T22:01:45.256958+00:00",
  "decision": {
    "status": "TRADE_CANDIDATE",
    "direction": "BUY",
    "confidence": 0.9,
    "fused_signal": {
      "direction": "BUY",
      "confidence": 0.9,
      "agreement": "3 BUY, 0 SELL",
      "fast_view": {...},
      "medium_view": {...},
      "long_view": {...}
    },
    "risk_result": {
      "approved": true,
      "calculated_risk": 0.02,
      "veto_reasons": []
    },
    "symbol": "XAUUSD",
    "timestamp": "2024-01-01T00:00:00Z",
    "model_version": "0.1.0",
    "mode": "backtest",
    "data_quality": "PASS",
    "risk_check": "PASS"
  }
}
```

### Usage
```bash
# Foreground (will show output and accept Ctrl+C)
python3 run_monitor.py

# Background (runs silently, use process tools to monitor)
nohup python3 run_monitor.py > monitor.out 2>&1 &
```

## Paper Trading Script (`run_paper.py`)

### Purpose
Runs the ATC orchestrator at specified intervals and logs each decision to a CSV file for later analysis, enabling detailed backtesting and performance evaluation.

### Key Features
- Loads environment variables from `.env` file manually
- Properly configures Python path for ATC module imports
- Creates CSV with header if file doesn't exist
- Flattens the nested decision structure into CSV-friendly columns
- Logs comprehensive decision data including:
  - Basic trade signal (status, direction, confidence)
  - Fused signal details (direction, confidence from fusion engine)
  - Risk assessment results (approval, calculated risk, veto reasons)
  - Metadata (model version, mode, data quality, risk check)
- Accepts custom interval via command-line argument (`-i` or `--interval`)
- Graceful shutdown on keyboard interrupt

### CSV Columns
- `timestamp_utc`: When the decision was made
- `symbol`: Trading symbol (default XAUUSD)
- `status`: TRADE_CANDIDATE, NO_TRADE, or BLOCKED
- `direction`: BUY, SELL, or FLAT
- `confidence`: Confidence score (0-1) from decision engine
- `fused_direction`: Direction from fusion engine
- `fused_confidence`: Confidence from fusion engine
- `risk_approved`: Boolean from risk engine
- `risk_calculated_risk`: Numerical risk value (0-1 typically)
- `veto_reasons`: Semicolon-separated list of risk veto reasons
- `model_version`: Version of the model used
- `mode`: backtest/paper/demo/live
- `data_quality`: PASS/WARN/FAIL
- `risk_check`: PASS/FAIL from risk check

### Usage
```bash
# Default 60-second interval
python3 run_paper.py

# Custom interval (e.g., 30 seconds)
python3 run_paper.py --interval 30
# or
python3 run_paper.py -i 30

# Stop with Ctrl+C
```

## Implementation Notes

### Environment Handling
Both scripts manually load the `.env` file to avoid external dependencies:
```python
def load_env_file(env_path: Path):
    if not env_path.is_file():
        return
    with env_path.open('r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                k, v = line.split('=', 1)
                os.environ[k.strip()] = v.strip()
```

### Import Strategy
Scripts ensure the ATC root is in Python path:
```python
ATC_ROOT = Path(__file__).resolve().parent
if str(ATC_ROOT) not in sys.path:
    sys.path.insert(0, str(ATC_ROOT))
```

### Error Handling
- Network errors (e.g., MetaAPI unreachable) are caught and logged but don't stop the loop
- Orchestrator exceptions are captured and logged as error decisions
- Keyboard interrupts are handled for graceful shutdown
- Timeout protection in verification scripts prevents hanging

### File Locations
Both scripts create their log files in the same directory as the scripts:
- `decisions.log.jsonl` (live monitor)
- `paper_trading_log.csv` (paper trader)

These are located in:
`/data/data/com.termux/files/home/.AINA/profiles/Sofia/autonomous_trading_controller/`

## Validation and Testing
The scripts were validated by:
1. Confirming `.env` file exists with proper token and account ID
2. Verifying both scripts import without error
3. Testing `run_paper.py` with a short interval (5 seconds) to confirm CSV logging works
4. Testing `run_monitor.py` briefly to confirm JSONL logging works
5. Ensuring the orchestrator's `run_cycle()` function can be called and returns a valid decision object

## Future Improvements
1. Add command-line argument to specify alternative symbols (e.g., WTI, BTCUSD)
2. Implement log rotation to prevent unlimited file growth
3. Add option to send notifications (Telegram, Discord) on specific signals
4. Include performance metrics calculation in paper trader (win rate, profit factor, etc.)
5. Add configuration file to adjust logging frequency and output paths without code changes