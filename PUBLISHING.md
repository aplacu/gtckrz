# Repository publishing boundary

## Publish to the repository

These files are application source, configuration defaults, or dependency metadata:

- `app.py`
- `core/config.py` (keep credentials empty; use deployment secrets)
- `core/data_module.py`
- `core/enhanced_analyzer.py`
- `core/idx_all_tickers.py`
- `core/logger.py`
- `core/market_timing.py`
- `requirements.txt`
- `core/shared_analysis.py`
- `core/stock_data.py`
- `addons/sync_stocks.py`
- `addons/telegram_bot.py`
- `signal_history.csv` only when the dataset is intentionally shared and contains no private data

## Keep local on the laptop

These files and folders are generated or environment-specific and are ignored by Git:

- `logs/`
- `__pycache__/`
- `*.pyc`
- `*.xlsx` and `*.xls`
- `.env*`
- `.streamlit/secrets.toml`
- `secrets/`
- `config.local.py`
- `.venv/`, `venv/`, and `env/`
- `local/`
- `notes/`
- editor and OS files

## Before publishing

1. Confirm Telegram credentials are not in `config.py`, `.env`, or any committed file.
2. Review `signal_history.csv` and remove any private or unintended records.
3. Run `git status --short` and confirm only intended source and documentation files are tracked.
4. Do not commit generated logs, Excel exports, caches, or local secrets.

The existing source layout is intentionally unchanged so the current imports and Streamlit entry point continue to work.
