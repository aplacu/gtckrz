import numpy as np
import pandas as pd
import pytest

from core import enhanced_analyzer as analyzer


def price_data(rows=30):
    index = pd.date_range("2024-01-01", periods=rows, freq="D")
    close = pd.Series(np.linspace(100, 130, rows), index=index)
    return pd.DataFrame(
        {
            "Open": close - 1,
            "High": close + 2,
            "Low": close - 2,
            "Close": close,
            "Volume": pd.Series(1000.0, index=index),
        },
        index=index,
    )


def test_calculate_greeks_returns_call_and_put_with_expected_delta_relation():
    call = analyzer.calculate_greeks(100, 100, 30, 0.05, 0.2, "call")
    put = analyzer.calculate_greeks(100, 100, 30, 0.05, 0.2, "put")

    assert set(call) == {"delta", "gamma", "theta", "vega"}
    assert call["gamma"] > 0
    assert call["vega"] > 0
    assert put["delta"] == pytest.approx(call["delta"] - 1)


def test_invalid_greeks_input_returns_zeroed_error_payload():
    result = analyzer.calculate_greeks(100, 100, 0, 0.05, 0.2)

    assert result["delta"] == 0
    assert result["gamma"] == 0
    assert "error" in result


def test_alert_creation_normalizes_type_and_condition_evaluation():
    data = price_data()
    alert = analyzer.create_smart_alert("BBCA.JK", "price_alert", 120, "above")
    result = analyzer.check_alert_conditions("BBCA.JK", data, alert)

    assert alert["type"] == "price"
    assert alert["active"] is True
    assert result["triggered"] is True
    assert result["current_value"] == 130


def test_signal_dataset_validation_coerces_types_and_removes_invalid_prices():
    raw = pd.DataFrame(
        {
            "timestamp": ["2024-01-01", "not-a-date", "2024-01-01"],
            "symbol": [" bbca.jk ", "TLKM.JK", "BBCA.JK"],
            "entry": [100, 0, 100],
            "sl": [90, 90, 90],
            "tp": [110, 110, 110],
            "outcome": [1, 2, 1],
            "strategy_name": [" trend ", "mean", "trend"],
        }
    )

    result = analyzer.validate_signal_dataset(raw)
    cleaned = result["cleaned_df"]

    assert result["valid"] is False
    assert {"invalid_timestamp", "invalid_outcome_values", "non_positive_prices", "duplicate_signal_keys"} <= set(result["issues"])
    assert result["duplicate_rows"] == 1
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["symbol"] == "BBCA.JK"
    assert cleaned.iloc[0]["outcome"] == 1


def test_paper_trading_tracks_position_profit_and_metrics():
    trader = analyzer.PaperTradingSimulator(initial_balance=1000)

    bought, _ = trader.buy_stock("ABC", 5, 100)
    sold, message = trader.sell_stock("ABC", 2, 120)
    portfolio = trader.get_portfolio_value({"ABC": 130})
    metrics = trader.get_performance_metrics()

    assert bought is True
    assert sold is True
    assert "Profit: Rp 40" in message
    assert trader.positions["ABC"]["shares"] == 3
    assert portfolio["stock_value"] == 390
    assert portfolio["total_value"] == 1130
    assert metrics == {"total_trades": 2, "win_rate": 100.0, "total_profit": 40, "avg_profit_per_trade": 40.0}


def test_paper_trading_rejects_insufficient_balance_and_missing_position():
    trader = analyzer.PaperTradingSimulator(initial_balance=100)

    bought, buy_message = trader.buy_stock("ABC", 2, 100)
    sold, sell_message = trader.sell_stock("ABC", 1, 100)

    assert bought is False
    assert buy_message == "Insufficient balance"
    assert sold is False
    assert sell_message == "Position not found or insufficient shares"


def test_empty_and_nan_helpers_use_defined_fallbacks():
    empty = pd.DataFrame(columns=["High", "Low", "Close", "Volume"])

    assert analyzer.detect_regime(empty) == 0
    assert analyzer.position_size_kelly(0.4, 1, 1000) == 0
    assert analyzer.calculate_vwap(empty).equals(empty["Close"])
