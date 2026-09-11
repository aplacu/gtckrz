# Test Generation Plan

## Phase 1: Shared analysis

Create `tests/test_shared_analysis.py` with deterministic OHLCV fixtures and tests for RSI, Bollinger Bands, MACD, VWAP/ATR, backtest empty/unsupported paths, seeded Monte Carlo, breakout/empty pattern handling, and volume spike/empty handling.

## Phase 2: Enhanced analyzer and data module

Create `tests/test_enhanced_analyzer.py` for Greeks, smart alerts, dataset coercion/validation, paper trading state transitions, regime/position sizing, and NaN/empty fallback behavior. Create `tests/test_data_module.py` for validation matrix, sector lookup, and mocked single/batch download paths where useful.

## Phase 3: Telegram integration

Create `tests/test_telegram_bot.py` for factory credentials, deterministic formatter assertions using a frozen datetime patch, request payload assertions with mocked `requests.post`, failure handling, and chunk dispatch without network.

## Validation

- Run each phase's focused pytest command with `.venv\\Scripts\\python.exe`.
- Run the complete `tests` suite with the same interpreter.
- Run `compileall` for the workspace Python modules.
- Review generated assertions against the acceptance checklist and record status in `.testagent/status.md`.