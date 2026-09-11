# Test Generation Research

## Scope

Current repository is authoritative. The requested test scope is:

- `core/shared_analysis.py`
- `core/enhanced_analyzer.py`
- `core/data_module.py` when safely importable
- `addons/telegram_bot.py`

`addons/tambahan.py` is a non-Python instruction note and is intentionally out of scope.

## Environment and Conventions

- Interpreter: `.venv\\Scripts\\python.exe`
- Framework: pytest is expected to be run through the project virtualenv.
- Streamlit 1.63.0 and all target module imports succeeded during research.
- No existing test files or test configuration were found.
- Tests should use pandas/numpy fixtures, `unittest.mock`, and `monkeypatch`; no network, Telegram, filesystem exports, or real yfinance calls.

## Target Inventory

### `core/shared_analysis.py`

- Technical indicators: RSI, Bollinger Bands, MACD, ADX, VWAP, ATR.
- Signal/backtest behavior: `backtest_strategy`, `monte_carlo_simulation`.
- Pattern and volume behavior: `detect_price_patterns`, `check_volume_spike`.
- Edge cases: empty and undersized frames, NaN-sensitive inputs, unsupported strategy.

### `core/enhanced_analyzer.py`

- Options math: `calculate_greeks`.
- Alert normalization/evaluation: `create_smart_alert`, `check_alert_conditions`.
- Dataset validation: `_coerce_signal_dataset`, `validate_signal_dataset`.
- Portfolio behavior: `PaperTradingSimulator` buy/sell/value/metrics.
- Deterministic helpers: `calculate_vwap`, `detect_regime`, `position_size_kelly`.
- Avoid network-backed functions except through mocks.

### `core/data_module.py`

- `validate_stock_data` for empty, short, missing-column, NaN, and valid data.
- Sector lookup helpers and `build_stock_lookup`.
- Download functions only through mocked `yfinance` calls if included.

### `addons/telegram_bot.py`

- Credential factory.
- Message formatter for empty, sorted, limited, and representative result payloads.
- `send_message` payload and success/failure via mocked `requests.post`.
- Chunked `send_scanner_results` via mocked `send_message`.

## Acceptance Checklist

1. Technical indicators have concrete value/shape assertions.
2. Signal/backtest behavior and Monte Carlo invalid-input handling are covered deterministically.
3. Data validation covers empty/NaN and structural failures.
4. Telegram formatter/payload behavior is covered without real Telegram calls.
5. Edge cases for empty/NaN data are covered where the current implementation has defined behavior.
6. No production code changes unless a test-discovered blocker is unavoidable.