import unittest
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import requests

from addons.telegram_bot import TelegramBot
from core.data_module import assess_market_data_quality, validate_stock_data
from core.shared_analysis import backtest_strategy, calculate_rsi


class CoreAnalysisTests(unittest.TestCase):
    def setUp(self):
        dates = pd.date_range("2025-01-01", periods=80, freq="D")
        close = pd.Series(np.linspace(100, 180, 80), index=dates)
        self.market_data = pd.DataFrame(
            {
                "Open": close - 1,
                "High": close + 2,
                "Low": close - 2,
                "Close": close,
                "Volume": 1000,
            },
            index=dates,
        )

    def test_rsi_returns_series_with_expected_length(self):
        result = calculate_rsi(self.market_data)

        self.assertEqual(len(result), len(self.market_data))
        self.assertTrue(result.iloc[-1] > 0)

    def test_validate_stock_data_accepts_complete_data(self):
        is_valid, message = validate_stock_data(self.market_data)

        self.assertTrue(is_valid)
        self.assertEqual(message, "Valid")

    def test_validate_stock_data_rejects_missing_required_column(self):
        incomplete = self.market_data.drop(columns=["Volume"])

        is_valid, message = validate_stock_data(incomplete)

        self.assertFalse(is_valid)
        self.assertIn("Volume", message)

    def test_validate_stock_data_rejects_nan_close(self):
        invalid = self.market_data.copy()
        invalid.loc[invalid.index[-1], "Close"] = np.nan

        is_valid, message = validate_stock_data(invalid)

        self.assertFalse(is_valid)
        self.assertEqual(message, "Ada data kosong di kolom penting")

    def test_market_data_quality_reports_missing_data(self):
        quality = assess_market_data_quality(self.market_data.iloc[:10], min_rows=50)

        self.assertEqual(quality["status"], "WARNING")
        self.assertEqual(quality["rows"], 10)
        self.assertIn("tidak cukup", quality["message"])

    def test_market_data_quality_reports_empty_data(self):
        quality = assess_market_data_quality(pd.DataFrame(), min_rows=50)

        self.assertEqual(quality["status"], "INVALID")
        self.assertEqual(quality["rows"], 0)

    def test_backtest_returns_expected_result_shape(self):
        result = backtest_strategy(self.market_data)

        self.assertIn("total_return", result)
        self.assertIn("equity_curve", result)
        self.assertIsInstance(result["trades"], list)
        self.assertEqual(result["total_fees"], 0)
        self.assertEqual(result["cost_assumptions"]["lot_size"], 1)

    def test_backtest_rejects_invalid_cost_parameters(self):
        result = backtest_strategy(self.market_data, buy_fee=-0.01)

        self.assertIn("error", result)
        self.assertIn("non-negative", result["error"])

    def test_rsi_handles_flat_prices_as_neutral(self):
        flat_data = self.market_data.copy()
        flat_data["Close"] = 100

        result = calculate_rsi(flat_data)

        self.assertEqual(result.iloc[-1], 50)


class TelegramFormatterTests(unittest.TestCase):
    def setUp(self):
        self.bot = TelegramBot("test-token", "test-chat")

    def test_formatter_sorts_results_and_limits_to_twenty(self):
        results = [
            {
                "ticker": f"T{i}.JK",
                "signal": "BUY",
                "score": i,
                "price": 1000,
                "change": 1.5,
                "sector": "Energy",
            }
            for i in range(25)
        ]

        message = self.bot.format_scanner_results(results)

        self.assertIn("T24.JK", message)
        self.assertNotIn("T4.JK", message)
        self.assertIn("Total found: 25 stocks", message)

    def test_send_message_returns_false_on_request_failure(self):
        with patch(
            "addons.telegram_bot.requests.post",
            side_effect=requests.RequestException("network"),
        ):
            result = self.bot.send_message("test")

        self.assertFalse(result)

    def test_send_message_returns_false_when_telegram_rejects_request(self):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"ok": False, "description": "chat not found"}

        with patch("addons.telegram_bot.requests.post", return_value=response):
            result = self.bot.send_message("test")

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
