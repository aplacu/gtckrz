import numpy as np
import pandas as pd
import pytest

from core import shared_analysis as analysis


def ohlcv_frame(rows=80):
    index = pd.date_range("2024-01-01", periods=rows, freq="D")
    close = pd.Series(np.linspace(100, 140, rows), index=index)
    return pd.DataFrame(
        {
            "Open": close - 1,
            "High": close + 2,
            "Low": close - 2,
            "Close": close,
            "Volume": pd.Series(np.full(rows, 1000.0), index=index),
        },
        index=index,
    )


def test_technical_indicators_return_expected_shapes_and_values():
    data = ohlcv_frame(30)

    rsi = analysis.calculate_rsi(data, period=5)
    bands = analysis.calculate_bollinger_bands(data, period=5, std_dev=2)
    macd = analysis.calculate_macd(data, fast=3, slow=5, signal=2)
    vwap = analysis.calculate_vwap(data)
    atr = analysis.calculate_atr(data, period=5)

    assert len(rsi) == len(data)
    assert pd.isna(rsi.iloc[-1])
    assert bands["middle_band"].iloc[-1] == data["Close"].iloc[-5:].mean()
    assert bands["upper_band"].iloc[-1] > bands["middle_band"].iloc[-1]
    assert set(macd) == {"macd_line", "signal_line", "histogram"}
    assert macd["histogram"].iloc[0] == 0
    assert vwap.iloc[-1] == pytest.approx(data["Close"].mean())
    assert atr.iloc[-1] == 4


def test_adx_has_named_components_and_empty_frame_is_handled_for_patterns():
    data = ohlcv_frame(30)
    adx = analysis.calculate_adx(data, period=5)

    assert set(adx) == {"adx", "plus_di", "minus_di"}
    assert adx["adx"].iloc[-1] >= 0
    assert analysis.detect_price_patterns(pd.DataFrame()) == []
    assert analysis.check_volume_spike(pd.DataFrame()) == {"alert": False}


def test_backtest_unsupported_strategy_returns_zeroed_result():
    result = analysis.backtest_strategy(ohlcv_frame(80), strategy_type="unknown")

    assert result["total_trades"] == 0
    assert result["total_return"] == 0
    assert result["trades"] == []


def test_monte_carlo_rejects_empty_or_insufficient_data():
    result = analysis.monte_carlo_simulation(pd.DataFrame(), simulations=2)

    assert result == {"error": "Insufficient data for Monte Carlo simulation"}


def test_monte_carlo_is_repeatable_when_numpy_seed_is_reset():
    data = ohlcv_frame(80)

    np.random.seed(7)
    first = analysis.monte_carlo_simulation(data, simulations=3)
    np.random.seed(7)
    second = analysis.monte_carlo_simulation(data, simulations=3)

    assert first == second
    assert first["simulations"] == 3
    assert "mean_return" in first


def test_volume_spike_reports_ratio_and_severity():
    data = ohlcv_frame(21)
    data.loc[data.index[-1], "Volume"] = 3000

    result = analysis.check_volume_spike(data, threshold=2)

    assert result["alert"] is True
    assert result["volume_ratio"] == 3000 / 1100
    assert result["severity"] == "LOW"


def test_nan_inputs_do_not_create_false_volume_alert():
    data = ohlcv_frame(21)
    data.loc[data.index[-1], "Volume"] = np.nan

    result = analysis.check_volume_spike(data)

    assert result == {"alert": False}