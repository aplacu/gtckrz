# Repository publishing boundary

## Publish to the repository

These files are application source, configuration defaults, or dependency metadata:

- `app.py`
- `config.py` (keep credentials empty; use deployment secrets)
- `data_module.py`
- `enhanced_analyzer.py`
- `idx_all_tickers.py`
- `logger.py`
- `market_timing.py`
- `requirements.txt`
- `shared_analysis.py`
- `stock_data.py`
- `sync_stocks.py`
- `telegram_bot.py`
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
