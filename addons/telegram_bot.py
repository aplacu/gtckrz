"""
Telegram Bot Integration Module
For sending stock scanner results to Telegram channels/groups
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime

from core.logger import alert_logger


class TelegramBot:
    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram bot
        
        Args:
            bot_token: Telegram bot token from @BotFather
            chat_id: Target chat ID (channel/group/user ID)
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_base = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """
        Send a text message to Telegram
        
        Args:
            text: Message text
            parse_mode: Parse mode (Markdown or HTML)
            
        Returns:
            Success status
        """
        try:
            url = f"{self.api_base}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            response_data = response.json()
            if not response_data.get("ok", False):
                alert_logger.error("Telegram rejected message: %s", response_data.get("description", "unknown error"))
                return False
            return True
        except (requests.RequestException, ValueError) as exc:
            alert_logger.error("Error sending Telegram message: %s", exc)
            return False
    
    def format_scanner_results(self, results: List[Dict], title: str = "📊 Stock Scanner Results") -> str:
        """
        Format scanner results for Telegram message
        
        Args:
            results: List of scanner result dictionaries
            title: Message title
            
        Returns:
            Formatted message text
        """
        message_parts = [f"*{title}*", f"_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_", ""]
        
        if not results:
            message_parts.append("No stocks found matching criteria.")
            return "\n".join(message_parts)
        
        # Sort by score descending
        sorted_results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
        
        for i, stock in enumerate(sorted_results[:20], 1):  # Limit to 20 results
            ticker = stock.get('ticker', 'N/A')
            signal = stock.get('signal', 'N/A')
            score = stock.get('score', 0)
            price = stock.get('price', 0)
            change = stock.get('change', 0)
            sector = stock.get('sector', 'N/A')
            
            # Signal emoji
            signal_emoji = {
                'STRONG BUY': '🚀',
                'BUY': '📈',
                'WEAK BUY': '📊',
                'SELL': '📉',
                'AVOID': '⚠️'
            }.get(signal, '🔹')
            
            message_parts.append(
                f"{i}. {signal_emoji} *{ticker}*\n"
                f"   Signal: {signal}\n"
                f"   Score: {score:.0f}\n"
                f"   Price: Rp {price:,.0f}\n"
                f"   Change: {change:+.2f}%\n"
                f"   Sector: {sector}\n"
            )
        
        total_found = len(results)
        message_parts.append(f"\n_*Total found: {total_found} stocks*_")
        
        return "\n".join(message_parts)
    
    def send_scanner_results(self, results: List[Dict], title: str = "📊 Stock Scanner Results") -> bool:
        """
        Send formatted scanner results to Telegram
        
        Args:
            results: List of scanner result dictionaries
            title: Message title
            
        Returns:
            Success status
        """
        message = self.format_scanner_results(results, title)
        
        # Telegram has message length limit (4096 chars)
        # Split if necessary
        if len(message) <= 4096:
            return self.send_message(message)
        else:
            # Split into chunks
            chunks = []
            current_chunk = []
            current_length = 0
            
            for line in message.split('\n'):
                line_length = len(line) + 1  # +1 for newline
                if current_length + line_length > 4000:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = [line]
                    current_length = line_length
                else:
                    current_chunk.append(line)
                    current_length += line_length
            
            if current_chunk:
                chunks.append('\n'.join(current_chunk))
            
            # Send all chunks
            success = True
            for i, chunk in enumerate(chunks):
                chunk_title = f"{title} (Part {i+1}/{len(chunks)})" if len(chunks) > 1 else title
                if i > 0:
                    chunk = f"*{chunk_title}*\n" + chunk
                if not self.send_message(chunk):
                    success = False
            
            return success


def create_telegram_bot(bot_token: Optional[str] = None, chat_id: Optional[str] = None) -> Optional[TelegramBot]:
    """
    Factory function to create Telegram bot instance
    
    Args:
        bot_token: Telegram bot token
        chat_id: Target chat ID
        
    Returns:
        TelegramBot instance or None if credentials missing
    """
    if not bot_token or not chat_id:
        return None
    return TelegramBot(bot_token, chat_id)
