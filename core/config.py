"""
Configuration and constants for gtckrz application
Centralized settings for all modules
"""

from pathlib import Path
from datetime import timedelta

# ==================== PATH CONFIGURATION ====================
APP_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = APP_ROOT / "logs"
DATA_DIR = APP_ROOT / "data"

# ==================== STREAMLIT CONFIGURATION ====================
PAGE_TITLE = "Pro Stock Analyzer - Market Scanner"
PAGE_ICON = "M"
LAYOUT = "wide"

# ==================== DATA CONFIGURATION ====================
DEFAULT_PERIOD = "3mo"
DEFAULT_INTERVAL = "1d"
CHUNK_SIZE_DOWNLOADS = 120
MAX_RETRIES_DOWNLOAD = 3
TIMEOUT_DOWNLOAD = 30  # seconds

# ==================== TECHNICAL INDICATOR PERIODS ====================
RSI_PERIOD = 14
SMA_FAST = 20
SMA_SLOW = 50
EMA_FAST = 8
EMA_SLOW = 21
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
STOCHASTIC_PERIOD = 14
STOCHASTIC_SMOOTH = 3
ATR_PERIOD = 14
SUPPORT_RESISTANCE_WINDOW = 60

# ==================== SIGNAL SCORING ====================
SIGNAL_SCORE_DAILY_WEIGHT = 0.30  # 30%
SIGNAL_SCORE_WEEKLY_WEIGHT = 0.20  # 20%
SIGNAL_SCORE_MOMENTUM_WEIGHT = 0.20  # 20%
SIGNAL_SCORE_AI_WEIGHT = 0.30  # 30%

SCORE_STRONG_BUY = 80
SCORE_BUY = 60
SCORE_WEAK_BUY = 40
SCORE_NEUTRAL = 0
SCORE_BEARISH = -20
SCORE_AVOID = -100

# ==================== PATTERN DETECTION ====================
PATTERN_HAMMER_WICK_RATIO = 2.0  # Lower wick should be 2x the body
PATTERN_ENGULFING_THRESHOLD = 0.05  # 5% minimum difference

# ==================== BACKTESTING ====================
BACKTEST_INITIAL_CAPITAL = 10_000_000  # Rp 10 juta
BACKTEST_RISK_PER_TRADE = 2.0  # 2% per trade
BACKTEST_MIN_DATA_LENGTH = 80
BACKTEST_LOOKAHEAD_DAYS = 6
BACKTEST_ATR_MULTIPLIER_SL = 1.0
BACKTEST_ATR_MULTIPLIER_TP = 2.0

# ==================== MONTE CARLO ====================
MC_SIMULATIONS = 1000
MC_WINDOW_SIZE = 252

# ==================== POSITION SIZING ====================
POSITION_SIZE_DEFAULT_RISK = 2.0  # 2% per position
LOT_SIZE = 100  # 1 lot = 100 shares (Indonesian market)

# ==================== ALERT CONFIGURATION ====================
SIDEBAR_ALERTS_KEY = "realtime_alerts"
SMART_ALERTS_KEY = "smart_alerts"

ALERT_TYPES = {
    "price": "Price Alert",
    "volume": "Volume Spike",
    "rsi": "RSI Alert"
}

# ==================== ALERT THRESHOLDS ====================
VOLUME_SPIKE_THRESHOLD = 1.5  # 150% of average
RSI_OVERBOUGHT = 80
RSI_OVERSOLD = 20

# ==================== OPTIONS ANALYSIS ====================
RISK_FREE_RATE = 0.05  # 5% annual (default)
VOLATILITY_THRESHOLD = 0.3  # 30% implied volatility
TIME_TO_EXPIRY_DEFAULT = 30  # days

# ==================== MARKET TIMING (BEI) ====================
BEI_SESSIONS = {
    'pre_market': {'start': '08:45', 'end': '09:00'},
    'opening_auction': {'start': '09:00', 'end': '09:15'},
    'session_1': {'start': '09:15', 'end': '12:00'},
    'istihtarah': {'start': '12:00', 'end': '13:30'},
    'session_2': {'start': '13:30', 'end': '14:50'},
    'closing_auction': {'start': '14:50', 'end': '15:00'}
}

# ==================== SCANNER CONFIGURATION ====================
SCANNER_MODES = {
    "Sector Scan": "Scan by selected sector",
    "Favorites Scan": "Scan favorite stocks",
    "Full IDX Universe": "Scan all 300+ IDX tickers"
}

DEFAULT_SCANNER_MODE = "Sector Scan"

# ==================== DATASET PATHS ====================
DATASET_PATH = "signal_history.csv"
EXCEL_DATASET_PATH = "signal_history.xlsx"

# ==================== ML MODEL ====================
ML_TEST_SIZE = 0.2
ML_RANDOM_STATE = 42
ML_N_ESTIMATORS = 100

# ==================== TIME CONFIGURATION ====================
SESSION_TIMEOUT = timedelta(hours=1)
DATA_REFRESH_INTERVAL = timedelta(minutes=1)

# ==================== ERROR MESSAGES ====================
ERROR_NO_DATA = "Data tidak ditemukan."
ERROR_INVALID_TICKER = "Kode saham tidak valid. Gunakan format: KODE.JK"
ERROR_INSUFFICIENT_DATA = "Data tidak cukup untuk analisis. Minimal 20 hari data diperlukan."

# ==================== SUCCESS MESSAGES ====================
SUCCESS_DATA_LOADED = "Data berhasil dimuat"
SUCCESS_ANALYSIS_COMPLETE = "Analisis selesai"

# ==================== DISPLAY FORMATS ====================
PRICE_FORMAT = "{:,.0f}"
PERCENTAGE_FORMAT = "{:+.2f}%"
SCORE_FORMAT = "{:.0f}%"

# ==================== SECTOR MAPPING ====================
# Mapped from stock_data.py
SECTOR_NAMES = [
    "Financials (Keuangan)",
    "Energy (Energi)",
    "Basic Materials (Barang Baku)",
    "Industrials (Industri)",
    "Consumer Discretionary (Barang Konsumsi)",
    "Consumer Staples (Kebutuhan Pokok)",
    "Healthcare (Kesehatan)",
    "Utilities (Utilitas)",
    "Real Estate (Properti)",
    "Information Technology (Teknologi)",
    "Telecommunications (Telekomunikasi)",
    "Transportation (Transportasi)",
    "Construction (Konstruksi)"
]

# ==================== TELEGRAM CONFIGURATION ====================
TELEGRAM_BOT_TOKEN = ""  # Get from @BotFather
TELEGRAM_CHAT_ID = ""    # Channel/group/user ID

# ==================== FEATURE FLAGS ====================
ENABLE_AI_SIGNALS = True
ENABLE_PAPER_TRADING = True
ENABLE_OPTIONS_ANALYSIS = True
ENABLE_MARKET_TIMING = True
ENABLE_ML_DASHBOARD = True
ENABLE_EARLY_MOVERS = True
ENABLE_WALK_FORWARD_VALIDATION = True
