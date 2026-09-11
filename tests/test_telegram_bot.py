from unittest.mock import Mock, patch

from addons import telegram_bot


class FixedDateTime:
    @classmethod
    def now(cls):
        return cls()

    def strftime(self, format_string):
        return "2024-01-02 03:04:05"


def test_factory_requires_both_credentials():
    assert telegram_bot.create_telegram_bot() is None
    assert telegram_bot.create_telegram_bot(bot_token="token") is None
    bot = telegram_bot.create_telegram_bot("token", "chat")

    assert isinstance(bot, telegram_bot.TelegramBot)
    assert bot.api_base == "https://api.telegram.org/bottoken"


def test_formatter_is_deterministic_sorts_results_and_handles_empty():
    bot = telegram_bot.TelegramBot("token", "chat")
    results = [
        {"ticker": "LOW", "signal": "SELL", "score": 20, "price": 100, "change": -1.5, "sector": "A"},
        {"ticker": "HIGH", "signal": "STRONG BUY", "score": 90, "price": 200, "change": 2.5, "sector": "B"},
    ]

    with patch.object(telegram_bot, "datetime", FixedDateTime):
        message = bot.format_scanner_results(results, title="Daily")
        empty_message = bot.format_scanner_results([], title="Daily")

    assert message.startswith("*Daily*\n_2024-01-02 03:04:05_")
    assert message.index("HIGH") < message.index("LOW")
    assert "🚀 *HIGH*" in message
    assert "Score: 90" in message
    assert "Change: +2.50%" in message
    assert "Total found: 2 stocks" in message
    assert "No stocks found matching criteria." in empty_message


def test_send_message_posts_expected_payload_and_returns_success():
    bot = telegram_bot.TelegramBot("token", "chat")
    response = Mock()
    response.raise_for_status.return_value = None

    with patch.object(telegram_bot.requests, "post", return_value=response) as post:
        result = bot.send_message("hello", parse_mode="HTML")

    assert result is True
    post.assert_called_once_with(
        "https://api.telegram.org/bottoken/sendMessage",
        json={
            "chat_id": "chat",
            "text": "hello",
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=10,
    )


def test_send_message_returns_false_when_request_fails():
    bot = telegram_bot.TelegramBot("token", "chat")

    with patch.object(telegram_bot.requests, "post", side_effect=RuntimeError("offline")):
        result = bot.send_message("hello")

    assert result is False


def test_send_scanner_results_splits_long_message_and_sends_all_chunks():
    bot = telegram_bot.TelegramBot("token", "chat")
    results = [
        {
            "ticker": f"TICK{i}",
            "signal": "BUY",
            "score": i,
            "price": 100,
            "change": 1,
            "sector": "Sector " + ("X" * 300),
        }
        for i in range(20)
    ]

    with patch.object(bot, "send_message", return_value=True) as send_message:
        result = bot.send_scanner_results(results, title="Long")

    assert result is True
    assert send_message.call_count > 1
    assert all(len(call.args[0]) <= 4096 for call in send_message.call_args_list)