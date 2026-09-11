"""
Data fetching and management module
Handles stock data downloads with caching and error handling
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, Optional, Tuple
import numpy as np

from core.logger import data_logger, PerformanceLogger
from core.config import (
    CHUNK_SIZE_DOWNLOADS,
    MAX_RETRIES_DOWNLOAD,
    TIMEOUT_DOWNLOAD,
    ERROR_NO_DATA,
    DEFAULT_PERIOD,
    DEFAULT_INTERVAL
)

# Import stock lists
from core.stock_data import SECTOR_STOCKS
from core.idx_all_tickers import IDX_TICKERS


def build_stock_lookup():
    """
    Build lookup dictionaries for sectors and tickers

    Returns:
        Tuple of (ALL_STOCKS, FULL_IDX_STOCKS, SECTOR_BY_TICKER)
    """
    all_stocks = []
    for stocks in SECTOR_STOCKS.values():
        all_stocks.extend(stocks)
    all_stocks = sorted(list(set(all_stocks)))

    full_idx_stocks = sorted({f"{ticker}.JK" for ticker in IDX_TICKERS})

    # Build sector lookup
    sector_by_ticker = {}
    for sector_name, sector_tickers in SECTOR_STOCKS.items():
        for ticker in sector_tickers:
            if ticker not in sector_by_ticker:
                sector_by_ticker[ticker] = sector_name

    data_logger.info(f"Built lookup: {len(all_stocks)} tickers, {len(full_idx_stocks)} IDX tickers")

    return all_stocks, full_idx_stocks, sector_by_ticker


def download_single_stock(
    ticker: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    period: str = DEFAULT_PERIOD,
    interval: str = DEFAULT_INTERVAL
) -> Optional[pd.DataFrame]:
    """
    Download single stock data with error handling

    Args:
        ticker: Stock ticker
        start_date: Start date (if None, uses period)
        end_date: End date (default: today)
        period: Period if using (1d, 5d, 1mo, 3mo, 6mo, 1y, etc.)
        interval: Interval (1m, 5m, 15m, 30m, 60m, 1d, 1wk, 1mo)

    Returns:
        DataFrame with OHLCV data or None if failed
    """
    try:
        if end_date is None:
            end_date = datetime.now().date()

        download_kwargs = {
            "progress": False,
            "timeout": TIMEOUT_DOWNLOAD
        }

        if start_date and end_date:
            download_kwargs["start"] = start_date
            download_kwargs["end"] = end_date
        else:
            download_kwargs["period"] = period

        if interval != "1d":
            download_kwargs["interval"] = interval

        df = yf.download(ticker, **download_kwargs)

        if df is None or df.empty:
            data_logger.warning(f"No data returned for {ticker}")
            return None

        # Fix MultiIndex columns from single ticker download
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(0)

        data_logger.debug(f"Downloaded {ticker}: {len(df)} rows")
        return df

    except Exception as e:
        data_logger.error(f"Failed to download {ticker}: {e}")
        return None


def download_batch_dict(
    tickers: list,
    period: str = DEFAULT_PERIOD,
    interval: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    chunk_size: int = CHUNK_SIZE_DOWNLOADS
) -> Dict[str, pd.DataFrame]:
    """
    Download multiple tickers in chunks without persistent caching

    Args:
        tickers: List of tickers to download
        period: Time period (3mo, 1y, etc.)
        interval: Data interval (1d, 1wk, 1mo)
        start_date: Optional start date
        end_date: Optional end date
        chunk_size: Number of tickers per download call

    Returns:
        Dictionary of {ticker: DataFrame}
    """
    result = {}

    if not tickers:
        data_logger.warning("Empty ticker list provided")
        return result

    with PerformanceLogger(f"Download batch: {len(tickers)} tickers"):
        result = _fetch_batch_uncached(tickers, period, interval, chunk_size)

    data_logger.info(f"Batch download result: {len(result)}/{len(tickers)} tickers")
    return result


def _fetch_batch_uncached(
    tickers: list,
    period: str,
    interval: Optional[str],
    chunk_size: int
) -> Dict[str, pd.DataFrame]:
    """
    Internal function to fetch uncached batch data
    """
    out = {}

    for i in range(0, len(tickers), chunk_size):
        chunk = tickers[i:i + chunk_size]
        try:
            kwargs = {
                "tickers": chunk,
                "period": period,
                "group_by": "ticker",
                "threads": False,
                "progress": False,
            }
            if interval:
                kwargs["interval"] = interval

            data = yf.download(**kwargs)

            if data is None or data.empty:
                continue

            # Handle MultiIndex columns
            if isinstance(data.columns, pd.MultiIndex):
                tickers_in_data = set(data.columns.get_level_values(0))
                for ticker in chunk:
                    if ticker in tickers_in_data:
                        df = data[ticker].copy()
                        if not df.empty:
                            out[ticker] = df
            elif len(chunk) == 1:
                out[chunk[0]] = data.copy()

        except Exception as e:
            data_logger.error(f"Chunk download failed: {e}")
            continue

    return out


def download_with_fallback(
    ticker: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    period: str = DEFAULT_PERIOD
) -> Optional[pd.DataFrame]:
    """
    Download with retry logic and fallback

    Args:
        ticker: Stock ticker
        start_date: Start date
        end_date: End date
        period: Period

    Returns:
        DataFrame or None
    """
    for attempt in range(MAX_RETRIES_DOWNLOAD):
        try:
            data_logger.debug(f"Download attempt {attempt + 1}/{MAX_RETRIES_DOWNLOAD} for {ticker}")
            df = download_single_stock(ticker, start_date, end_date, period)

            if df is not None and not df.empty:
                return df

        except Exception as e:
            data_logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES_DOWNLOAD - 1:
                import time
                time.sleep(1)  # Wait before retry

    data_logger.error(f"All download attempts failed for {ticker}")
    return None


def validate_stock_data(df: pd.DataFrame, min_rows: int = 20) -> Tuple[bool, str]:
    """
    Validate downloaded stock data

    Args:
        df: DataFrame to validate
        min_rows: Minimum required rows

    Returns:
        Tuple of (is_valid, message)
    """
    if df is None or df.empty:
        return False, "Data kosong"

    if len(df) < min_rows:
        return False, f"Data tidak cukup ({len(df)}/{min_rows})"

    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        return False, f"Kolom hilang: {missing}"

    # Check for NaN values in critical columns
    if df[['Close', 'Volume']].isnull().any().any():
        return False, "Ada data kosong di kolom penting"

    return True, "Valid"


def get_sector_tickers(sector: str) -> list:
    """
    Get all tickers in a sector

    Args:
        sector: Sector name

    Returns:
        List of tickers
    """
    return SECTOR_STOCKS.get(sector, [])


def get_all_sectors() -> list:
    """Get list of all available sectors"""
    return sorted(list(SECTOR_STOCKS.keys()))


def get_ticker_sector(ticker: str, sector_lookup: Dict) -> str:
    """
    Get sector for a ticker

    Args:
        ticker: Ticker code
        sector_lookup: Sector lookup dictionary

    Returns:
        Sector name or "Other"
    """
    return sector_lookup.get(ticker, "Other")
