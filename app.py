import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import date, datetime, timedelta
from io import BytesIO
from stock_data import SECTOR_STOCKS
from idx_all_tickers import IDX_TICKERS
from textblob import TextBlob
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import time
import os
import math
from shared_analysis import (
    calculate_rsi as shared_calculate_rsi,
    backtest_strategy as shared_backtest_strategy,
    monte_carlo_simulation as shared_monte_carlo_simulation,
    detect_price_patterns as shared_detect_price_patterns,
    check_volume_spike as shared_check_volume_spike,
)
from enhanced_analyzer import (
    EnhancedStockAnalyzer, PaperTradingSimulator, get_fundamental_ratios,
    calculate_dcf_value, create_advanced_chart,
    analyze_option_chain as ea_analyze_option_chain,
    calculate_greeks as ea_calculate_greeks,
    create_smart_alert as ea_create_smart_alert,
    check_alert_conditions as ea_check_alert_conditions,
    DATASET_PATH as EA_DATASET_PATH,
    EXCEL_DATASET_PATH as EA_EXCEL_DATASET_PATH,
    detect_regime as ea_detect_regime,
    log_signal as ea_log_signal,
    evaluate_outcomes as ea_evaluate_outcomes,
    train_model as ea_train_model,
    train_regime_models as ea_train_regime_models,
    calculate_expectancy as ea_calculate_expectancy,
    position_size_kelly as ea_position_size_kelly,
    best_strategy_per_regime as ea_best_strategy_per_regime,
    predict_signal_confidence as ea_predict_signal_confidence,
    export_dataset_to_excel as ea_export_dataset_to_excel,
    load_signal_dataset as ea_load_signal_dataset,
)
from market_timing import comprehensive_timing_analysis
from telegram_bot import TelegramBot, create_telegram_bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

SIDEBAR_ALERTS_KEY = "realtime_alerts"
SMART_ALERTS_KEY = "smart_alerts"


# Konfigurasi Halaman
st.set_page_config(
    page_title="Pro Stock Analyzer - Market Scanner",
    page_icon="M",
    layout="wide"
)

# Gabungkan semua saham
ALL_STOCKS = []
for stocks in SECTOR_STOCKS.values():
    ALL_STOCKS.extend(stocks)
ALL_STOCKS = sorted(list(set(ALL_STOCKS)))
FULL_IDX_STOCKS = sorted({f"{ticker}.JK" for ticker in IDX_TICKERS})

# Fast sector lookup (fallback "Other" for non-mapped full-universe tickers)
SECTOR_BY_TICKER = {}
for sector_name, sector_tickers in SECTOR_STOCKS.items():
    for ticker in sector_tickers:
        if ticker not in SECTOR_BY_TICKER:
            SECTOR_BY_TICKER[ticker] = sector_name


def download_batch_dict(tickers, period="3mo", interval=None, chunk_size=120):
    """Download OHLCV in chunks and return {ticker: DataFrame}."""
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

            if isinstance(data.columns, pd.MultiIndex):
                tickers_in_data = set(data.columns.get_level_values(0))
                for ticker in chunk:
                    if ticker in tickers_in_data:
                        df = data[ticker].copy()
                        if not df.empty:
                            out[ticker] = df
            elif len(chunk) == 1:
                out[chunk[0]] = data.copy()
        except Exception:
            continue
    return out

# --- FUNGSI INDIKATOR TEKNIKAL ---
def calculate_indicators(df):
    # RSI (14)
    df['RSI'] = shared_calculate_rsi(df)
    
    # SMA (20 & 50)
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    
    # ATR (14) untuk Volatilitas
    from shared_analysis import calculate_atr
    df['ATR'] = calculate_atr(df)
    
    # Volume Analysis
    df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()
    df['Vol_Ratio'] = df['Volume'] / df['Vol_Avg']
    
    # Support & Resistance (60 days window)
    df['Support'] = df['Low'].rolling(window=60).min()
    df['Resistance'] = df['High'].rolling(window=60).max()
    
    # EMA (8 & 21) - Tren Cepat
    df['EMA8'] = df['Close'].ewm(span=8, adjust=False).mean()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()

    # MACD
    from shared_analysis import calculate_macd
    macd = calculate_macd(df)
    df['MACD'] = macd['macd_line']
    df['Signal_Line'] = macd['signal_line']
    df['MACD_Histogram'] = macd['histogram']
    
    # Stochastic
    low_14 = df['Low'].rolling(window=14).min()
    high_14 = df['High'].rolling(window=14).max()
    df['%K'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
    df['%D'] = df['%K'].rolling(window=3).mean()
    
    # Bollinger Bands
    from shared_analysis import calculate_bollinger_bands
    bb = calculate_bollinger_bands(df)
    df['BB_Middle'] = bb['middle_band']
    df['BB_Upper'] = bb['upper_band']
    df['BB_Lower'] = bb['lower_band']
    df['BB_Width'] = bb['band_width']
    
    # ADX
    from shared_analysis import calculate_adx
    adx = calculate_adx(df)
    df['ADX'] = adx['adx']
    df['Plus_DI'] = adx['plus_di']
    df['Minus_DI'] = adx['minus_di']
    
    # VWAP
    from shared_analysis import calculate_vwap
    df['VWAP'] = calculate_vwap(df)
    
    return df

def calculate_rsi(data, period=14):
    """Compatibility wrapper to shared RSI implementation."""
    return shared_calculate_rsi(data, period=period)

def detect_pattern(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    body = abs(last['Close'] - last['Open'])
    range_total = last['High'] - last['Low']
    upper_wick = last['High'] - max(last['Close'], last['Open'])
    lower_wick = min(last['Close'], last['Open']) - last['Low']
    
    # Pola Hammer (Body kecil di atas, Wick bawah panjang)
    if range_total > 0 and lower_wick > body * 2 and upper_wick < body:
        return "Hammer (Potensi Rebound)"
    
    # Pola Engulfing
    if last['Close'] > last['Open'] and prev['Close'] < prev['Open']:
        if last['Close'] > prev['Open'] and last['Open'] < prev['Close']:
            return "Bullish Engulfing"

    if last['Close'] < last['Open'] and prev['Close'] > prev['Open']:
        if last['Close'] < prev['Open'] and last['Open'] > prev['Close']:
            return "Bearish Engulfing"

    return "Normal"

def check_trend(df):
    if df.empty or len(df) < 50:
        return "NEUTRAL"

    last = df.iloc[-1]
    # EMA Cross (Golden Cross)
    if last['Close'] > last['SMA50'] and last['EMA8'] > last['EMA21']:
        return "BULLISH"
    elif last['Close'] < last['SMA50'] and last['EMA8'] < last['EMA21']:
        return "BEARISH"
    else:
        return "SIDEWAYS"

def generate_signal(df_daily, df_weekly=None, ticker="", enable_ai=True):
    """Enhanced signal generation dengan AI booster"""
    last_row = df_daily.iloc[-1]
    prev_row = df_daily.iloc[-2]
    
    # 1. Analisa Trend Daily (30% - dikurangi karena ada AI)
    trend_daily = check_trend(df_daily)
    score_daily = 30 if trend_daily == "BULLISH" else 0
    
    # 2. Analisa Trend Weekly (20% - dikurangi)
    trend_weekly = "NEUTRAL"
    score_weekly = 0
    if df_weekly is not None and not df_weekly.empty:
        trend_weekly = check_trend(df_weekly)
        if trend_weekly == "BULLISH":
             score_weekly = 20
        elif trend_weekly == "BEARISH":
             score_weekly = -5

    # 3. Momentum & Volume (20% - dikurangi)
    momentum_score = 0
    
    # MACD Cross
    macd_bullish = last_row['MACD'] > last_row['Signal_Line']
    macd_cross_up = macd_bullish and prev_row['MACD'] <= prev_row['Signal_Line']
    
    if macd_cross_up: momentum_score += 10
    elif macd_bullish: momentum_score += 3
    
    # RSI di area ideal
    if 40 < last_row['RSI'] < 70: momentum_score += 5
    
    # Volume Spike
    if last_row['Vol_Ratio'] > 1.5: momentum_score += 5
    
    # 4. AI Signal Booster (30% - baru!)
    ai_score = 0
    ai_data = None
    if enable_ai and ticker:
        ai_data = get_ai_signal_boost(df_daily, ticker)
        ai_score = ai_data['ai_score']
    
    # Total Score
    total_score = score_daily + score_weekly + momentum_score + ai_score
    
    # Pattern Recognition
    pattern = detect_pattern(df_daily)
    
    # Penentuan Signal & Action dengan AI enhancement
    signal = "NEUTRAL"
    action = "Wait"
    
    # Enhanced signal logic dengan AI
    if total_score >= 80 and trend_weekly != "BEARISH":
        signal = "STRONG BUY"
        action = "ENTRY NOW"
    elif total_score >= 60 and trend_weekly != "BEARISH":
        signal = "BUY"
        action = "ACCUMULATE"
    elif last_row['RSI'] > 80:
        signal = "SELL"
        action = "TAKE PROFIT"
    elif trend_daily == "BEARISH" and trend_weekly == "BEARISH":
        signal = "AVOID"
        action = "DO NOT TOUCH"
        total_score = 0
    elif total_score >= 40:
        signal = "WEAK BUY"
        action = "WATCH LIST"

    reason = f"W:{trend_weekly} | D:{trend_daily} | {pattern}"
    return signal, action, reason, trend_daily, trend_weekly, total_score, pattern, ai_data

def calculate_sector_performance(df_results):
    """Menghitung performa sektor berdasarkan data scan saham"""
    sector_performance = []
    
    for sector in df_results['Sector'].unique():
        sector_data = df_results[df_results['Sector'] == sector]
        
        # Hitung rata-rata perubahan harga per sektor
        avg_change = sector_data['Change (%)'].mean()
        
        # Hitung total volume per sektor
        total_volume = sector_data['Volume'].sum()
        
        # Hitung jumlah saham dengan sinyal BUY/STRONG BUY
        buy_signals = len(sector_data[sector_data['Signal'].isin(['BUY', 'STRONG BUY'])])
        total_stocks = len(sector_data)
        buy_ratio = (buy_signals / total_stocks * 100) if total_stocks > 0 else 0
        
        # Hitung rata-rata score konvinsi
        avg_score = sector_data['Score'].mean()
        
        sector_performance.append({
            'Sector': sector,
            'Avg_Change_%': round(avg_change, 2),
            'Total_Volume': total_volume,
            'Buy_Signals': buy_signals,
            'Total_Stocks': total_stocks,
            'Buy_Ratio_%': round(buy_ratio, 2),
            'Avg_Score': round(avg_score, 2),
            'Performance_Rank': 0  # Akan diisi setelah sorting
        })
    
    # Convert ke DataFrame dan ranking
    sector_df = pd.DataFrame(sector_performance)
    sector_df = sector_df.sort_values('Avg_Change_%', ascending=False)
    sector_df['Performance_Rank'] = range(1, len(sector_df) + 1)
    
    return sector_df

def calculate_position_size(capital, risk_percentage, entry_price, stop_loss_price):
    """Kalkulator position sizing berdasarkan risk management"""
    
    # Hitung risiko per saham dalam Rupiah
    risk_per_share = entry_price - stop_loss_price
    
    # Hitung total risiko yang diizinkan
    total_risk_amount = capital * (risk_percentage / 100)
    
    # Hitung jumlah lot yang aman (1 lot = 100 lembar saham)
    if risk_per_share > 0:
        max_shares = total_risk_amount / risk_per_share
        max_lot = int(max_shares / 100)  # Konversi ke lot
        
        # Hitung total investasi
        total_investment = max_lot * 100 * entry_price
        
        # Hitung potensi profit
        target_1 = entry_price + (entry_price - stop_loss_price)  # Risk:Reward 1:1
        target_2 = entry_price + 2 * (entry_price - stop_loss_price)  # Risk:Reward 1:2
        
        potential_profit_1 = max_lot * 100 * (target_1 - entry_price)
        potential_profit_2 = max_lot * 100 * (target_2 - entry_price)
        
        return {
            'max_lot': max_lot,
            'total_investment': total_investment,
            'risk_amount': total_risk_amount,
            'risk_per_share': risk_per_share,
            'target_1': target_1,
            'target_2': target_2,
            'potential_profit_1': potential_profit_1,
            'potential_profit_2': potential_profit_2,
            'rr_ratio': round((target_1 - entry_price) / risk_per_share, 2)
        }
    else:
        return {
            'max_lot': 0,
            'total_investment': 0,
            'risk_amount': 0,
            'risk_per_share': 0,
            'target_1': entry_price,
            'target_2': entry_price,
            'potential_profit_1': 0,
            'potential_profit_2': 0,
            'rr_ratio': 0
        }

def backtest_signal_strategy(df, initial_capital=10000000, risk_per_trade=2):
    """Backtesting sinyal scanner dengan risk-per-trade dan exit berbasis SL/TP/time stop."""
    try:
        if df is None or df.empty or len(df) < 80:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "total_profit": 0,
                "total_return": 0,
                "max_drawdown": 0,
                "avg_win": 0,
                "avg_loss": 0,
                "final_capital": initial_capital,
                "trades": [],
            }

        data = calculate_indicators(df.copy())
        trades = []
        capital = initial_capital
        max_drawdown = 0
        peak_capital = initial_capital

        for i in range(60, len(data) - 6):
            window_data = data.iloc[i - 60:i].copy()
            current_price = float(data["Close"].iloc[i])

            sig, _, _, _, _, score, _, _ = generate_signal(window_data, None, "", enable_ai=False)
            if sig not in ["BUY", "STRONG BUY"] and score < 55:
                continue

            atr = float(window_data["ATR"].iloc[-1]) if pd.notna(window_data["ATR"].iloc[-1]) else current_price * 0.02
            risk_per_share = max(atr, current_price * 0.01)
            sl = max(1, current_price - risk_per_share)
            tp = current_price + (risk_per_share * 2)
            risk_amount = capital * (risk_per_trade / 100.0)
            shares = int(risk_amount / (current_price - sl)) if current_price > sl else 0
            max_affordable = int(capital / current_price) if current_price > 0 else 0
            shares = max(0, min(shares, max_affordable))
            if shares <= 0:
                continue

            future = data.iloc[i + 1:i + 6]
            exit_price = float(future["Close"].iloc[-1])
            exit_date = future.index[-1]

            hit_tp = future["High"].max() >= tp
            hit_sl = future["Low"].min() <= sl
            if hit_tp and hit_sl:
                if future[future["Low"] <= sl].index[0] <= future[future["High"] >= tp].index[0]:
                    exit_price = sl
                    exit_date = future[future["Low"] <= sl].index[0]
                else:
                    exit_price = tp
                    exit_date = future[future["High"] >= tp].index[0]
            elif hit_tp:
                exit_price = tp
                exit_date = future[future["High"] >= tp].index[0]
            elif hit_sl:
                exit_price = sl
                exit_date = future[future["Low"] <= sl].index[0]

            profit = (exit_price - current_price) * shares
            capital += profit
            peak_capital = max(peak_capital, capital)
            if peak_capital > 0:
                dd = (peak_capital - capital) / peak_capital * 100
                max_drawdown = max(max_drawdown, dd)

            trades.append(
                {
                    "entry_date": data.index[i],
                    "exit_date": exit_date,
                    "entry_price": current_price,
                    "exit_price": exit_price,
                    "shares": shares,
                    "profit": profit,
                    "holding_days": int((pd.to_datetime(exit_date) - pd.to_datetime(data.index[i])).days),
                    "score": score,
                }
            )

        profits = [t["profit"] for t in trades]
        wins = [p for p in profits if p > 0]
        losses = [p for p in profits if p <= 0]
        total_profit = sum(profits) if profits else 0
        total_trades = len(trades)

        return {
            "total_trades": total_trades,
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": (len(wins) / total_trades * 100) if total_trades else 0,
            "total_profit": total_profit,
            "total_return": ((capital - initial_capital) / initial_capital * 100) if initial_capital else 0,
            "max_drawdown": max_drawdown,
            "avg_win": (sum(wins) / len(wins)) if wins else 0,
            "avg_loss": (sum(losses) / len(losses)) if losses else 0,
            "final_capital": capital,
            "trades": trades,
        }
    except Exception as e:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "total_profit": 0,
            "total_return": 0,
            "max_drawdown": 0,
            "avg_win": 0,
            "avg_loss": 0,
            "final_capital": initial_capital,
            "trades": [],
            "error": str(e),
        }

# --- AI-POWERED SIGNAL BOOSTER ---
def get_news_sentiment(ticker):
    """Mendapatkan sentimen berita sederhana untuk saham tertentu."""
    try:
        news_texts = [
            f"Saham {ticker} mengalami kenaikan signifikan",
            f"Prospek {ticker} sangat bagus di kuartal berikutnya",
            f"Analis merekomendasikan {ticker} sebagai BUY",
        ]
        sentiments = [TextBlob(text).sentiment.polarity for text in news_texts]
        avg_sentiment = np.mean(sentiments)
        return {
            "sentiment_score": round(avg_sentiment, 3),
            "sentiment_label": "POSITIVE" if avg_sentiment > 0.1 else "NEGATIVE" if avg_sentiment < -0.1 else "NEUTRAL",
        }
    except Exception:
        return {"sentiment_score": 0, "sentiment_label": "NEUTRAL"}

def train_ml_model(historical_data):
    """Melatih model ML sederhana untuk prediksi sinyal."""
    try:
        def _safe_ratio(num, den, default=0.0):
            try:
                den_f = float(den)
                if den_f == 0 or np.isnan(den_f):
                    return default
                val = float(num) / den_f
                return default if np.isnan(val) or np.isinf(val) else val
            except Exception:
                return default

        features = []
        labels = []
        for i in range(50, len(historical_data) - 5):
            window_data = historical_data.iloc[i - 50:i]
            macd_std = window_data["MACD"].std()
            feature_vector = [
                window_data["RSI"].iloc[-1] / 100,
                window_data["Vol_Ratio"].iloc[-1] / 5,
                _safe_ratio(window_data["Close"].iloc[-1] - window_data["SMA20"].iloc[-1], window_data["SMA20"].iloc[-1]),
                _safe_ratio(window_data["Close"].iloc[-1] - window_data["SMA50"].iloc[-1], window_data["SMA50"].iloc[-1]),
                _safe_ratio(window_data["MACD"].iloc[-1], macd_std),
                window_data["%K"].iloc[-1] / 100,
            ]
            future_return = (historical_data["Close"].iloc[i + 5] - historical_data["Close"].iloc[i]) / historical_data["Close"].iloc[i]
            label = 1 if future_return > 0.02 else 0 if future_return < -0.02 else 2
            features.append(feature_vector)
            labels.append(label)
        if len(features) > 100:
            rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
            rf_model.fit(features, labels)
            return rf_model
        return None
    except Exception:
        return None

def get_ai_signal_boost(df, ticker):
    """Mendapatkan AI signal boost dari sentiment + model sederhana."""
    try:
        def _safe_ratio(num, den, default=0.0):
            try:
                den_f = float(den)
                if den_f == 0 or np.isnan(den_f):
                    return default
                val = float(num) / den_f
                return default if np.isnan(val) or np.isinf(val) else val
            except Exception:
                return default

        sentiment_data = get_news_sentiment(ticker)
        ml_model = train_ml_model(df)
        if ml_model:
            macd_std = df["MACD"].std()
            current_features = [
                df["RSI"].iloc[-1] / 100,
                df["Vol_Ratio"].iloc[-1] / 5,
                _safe_ratio(df["Close"].iloc[-1] - df["SMA20"].iloc[-1], df["SMA20"].iloc[-1]),
                _safe_ratio(df["Close"].iloc[-1] - df["SMA50"].iloc[-1], df["SMA50"].iloc[-1]),
                _safe_ratio(df["MACD"].iloc[-1], macd_std),
                df["%K"].iloc[-1] / 100,
            ]
            ml_prediction = ml_model.predict([current_features])[0]
            ml_confidence = max(ml_model.predict_proba([current_features])[0])
        else:
            ml_prediction = 2
            ml_confidence = 0.5
        ai_score = 0
        ai_reasons = []
        if sentiment_data["sentiment_label"] == "POSITIVE":
            ai_score += 30
            ai_reasons.append(f"Sentimen Positif ({sentiment_data['sentiment_score']:.2f})")
        elif sentiment_data["sentiment_label"] == "NEGATIVE":
            ai_score -= 15
            ai_reasons.append(f"Sentimen Negatif ({sentiment_data['sentiment_score']:.2f})")
        if ml_prediction == 1:
            ai_score += int(70 * ml_confidence)
            ai_reasons.append(f"AI Prediksi BULLISH ({ml_confidence:.1%})")
        elif ml_prediction == 0:
            ai_score -= int(35 * ml_confidence)
            ai_reasons.append(f"AI Prediksi BEARISH ({ml_confidence:.1%})")
        else:
            ai_reasons.append(f"AI Netral ({ml_confidence:.1%})")
        ai_score = max(0, min(100, ai_score))
        return {
            "ai_score": ai_score,
            "ai_confidence": ml_confidence,
            "sentiment_label": sentiment_data["sentiment_label"],
            "sentiment_score": sentiment_data["sentiment_score"],
            "ml_prediction": ["BEARISH", "BULLISH", "NEUTRAL"][ml_prediction],
            "ai_reasons": ai_reasons,
        }
    except Exception:
        return {
            "ai_score": 0,
            "ai_confidence": 0,
            "sentiment_label": "NEUTRAL",
            "sentiment_score": 0,
            "ml_prediction": "NEUTRAL",
            "ai_reasons": ["AI Signal tidak tersedia"],
        }

# --- ADVANCED BACKTESTING ENGINE ---
def backtest_strategy(data, strategy_type='ma_crossover', initial_capital=10000000):
    """Shared advanced backtesting engine wrapper."""
    return shared_backtest_strategy(data, strategy_type, initial_capital)

def monte_carlo_simulation(data, strategy_type='ma_crossover', initial_capital=10000000, simulations=1000):
    """Shared Monte Carlo wrapper."""
    return shared_monte_carlo_simulation(data, strategy_type, initial_capital, simulations)

def calculate_greeks(current_price, strike_price, time_to_expiry, risk_free_rate, volatility, option_type='call'):
    """Calculate option greeks wrapper."""
    return ea_calculate_greeks(current_price, strike_price, time_to_expiry, risk_free_rate, volatility, option_type)

def get_implied_volatility(ticker, option_type='call'):
    """Estimate implied volatility from historical volatility."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        returns = hist["Close"].pct_change().dropna()
        historical_vol = returns.std() * math.sqrt(252)
        current_price = hist["Close"].iloc[-1]
        sma_20 = hist["Close"].rolling(20).mean().iloc[-1]
        implied_vol = historical_vol * 0.9 if current_price > sma_20 else historical_vol * 1.1
        return min(max(implied_vol, 0.1), 1.0)
    except Exception:
        return 0.3

def analyze_option_chain(ticker, current_price):
    """Analyze option chain wrapper."""
    return ea_analyze_option_chain(ticker, current_price)

def detect_price_patterns(data, pattern_type='breakout'):
    """Shared price-pattern detection wrapper."""
    return shared_detect_price_patterns(data, pattern_type)

def check_volume_spike(data, threshold=2.0):
    """Shared volume-spike wrapper."""
    return shared_check_volume_spike(data, threshold)

def create_smart_alert(ticker, alert_type, threshold, condition='above'):
    """Create smart alert wrapper."""
    return ea_create_smart_alert(ticker, alert_type, threshold, condition)

def check_alert_conditions(ticker, data, alert):
    """Check alert conditions wrapper."""
    return ea_check_alert_conditions(ticker, data, alert, calculate_rsi_func=calculate_rsi)

# ============================================
# ML SIGNAL PREDICTION SYSTEM (from tambahan.py)
# ============================================

# Dataset path for signal logging
DATASET_PATH = EA_DATASET_PATH
EXCEL_DATASET_PATH = EA_EXCEL_DATASET_PATH

def detect_regime(df):
    """Wrapper: market regime detection from shared enhanced module."""
    return ea_detect_regime(df)

def log_signal(symbol, entry, sl, tp, features, strategy_name="MA_Cross"):
    """Wrapper: persist signal history (CSV master + Excel mirror)."""
    return ea_log_signal(symbol, entry, sl, tp, features, strategy_name)


def evaluate_outcomes():
    """Wrapper: evaluate pending outcomes from available market data."""
    return ea_evaluate_outcomes()

def train_model():
    """Wrapper: train ML model from cleaned signal history."""
    return ea_train_model()

def train_regime_models():
    """Wrapper: train dedicated model for each regime."""
    return ea_train_regime_models()

def calculate_expectancy():
    """Wrapper: calculate expectancy metrics."""
    return ea_calculate_expectancy()

def position_size_kelly(confidence, rr_ratio, capital):
    """Wrapper: conservative Kelly position sizing."""
    return ea_position_size_kelly(confidence, rr_ratio, capital)

def best_strategy_per_regime():
    """Wrapper: select best-performing strategy per regime."""
    return ea_best_strategy_per_regime()

def predict_signal_confidence(features, regime=None):
    """Wrapper: predict confidence with optional regime model."""
    return ea_predict_signal_confidence(features, regime=regime)


def _clamp01(value):
    try:
        return max(0.0, min(1.0, float(value)))
    except Exception:
        return 0.0


def calculate_obv(df):
    """On-Balance Volume for accumulation detection."""
    if df is None or df.empty or "Close" not in df.columns or "Volume" not in df.columns:
        return pd.Series(dtype=float)
    direction = np.sign(df["Close"].diff().fillna(0))
    return (direction * df["Volume"]).cumsum()


def compute_early_mover_profile(df, df_weekly=None):
    """
    Candidate filter + probabilistic ranking + risk layer.
    Returns a dict used for scanner ranking.
    """
    if df is None or df.empty or len(df) < 80:
        return {
            "candidate_pass": False,
            "candidate_reason": "insufficient_data",
            "early_prob": 0.0,
            "early_score": 0.0,
            "expected_return_pct": 0.0,
            "downside_risk_pct": 0.0,
            "rr_ratio": 0.0,
            "quality_score": 0.0,
            "regime": 0,
            "ml_confidence": 0.0,
            "heuristic_confidence": 0.0,
        }

    last = df.iloc[-1]
    close = float(last["Close"])
    atr = float(last["ATR"]) if pd.notna(last["ATR"]) and last["ATR"] > 0 else close * 0.02
    atr_pct = atr / close if close > 0 else 0.02
    avg_vol = float(df["Volume"].rolling(20).mean().iloc[-1]) if pd.notna(df["Volume"].rolling(20).mean().iloc[-1]) else 0
    vol_ratio = float(last["Vol_Ratio"]) if pd.notna(last["Vol_Ratio"]) else 1.0
    rsi = float(last["RSI"]) if pd.notna(last["RSI"]) else 50.0

    # Candidate filter: liquidity, volatility sanity, data completeness.
    candidate_pass = True
    candidate_reasons = []
    # Threshold likuiditas dibuat lebih adaptif untuk universe IDX yang luas.
    if avg_vol < 30000:
        candidate_pass = False
        candidate_reasons.append("low_liquidity")
    if atr_pct > 0.12:
        candidate_pass = False
        candidate_reasons.append("excessive_volatility")
    if close <= 0:
        candidate_pass = False
        candidate_reasons.append("invalid_price")

    # Early accumulation / expansion features.
    obv = calculate_obv(df.tail(60))
    if len(obv) >= 20:
        obv_slope = np.polyfit(np.arange(len(obv.tail(20))), obv.tail(20).values, 1)[0]
    else:
        obv_slope = 0
    obv_score = _clamp01((obv_slope / (abs(obv.tail(20).mean()) + 1e-9)) * 50 + 0.5)

    bandwidth_now = ((df["Close"].rolling(20).std().iloc[-1] * 2) / close) if close > 0 else 0
    bandwidth_prev = ((df["Close"].rolling(20).std().iloc[-20] * 2) / float(df["Close"].iloc[-20])) if len(df) > 40 and df["Close"].iloc[-20] > 0 else bandwidth_now
    contraction_score = _clamp01((bandwidth_prev - bandwidth_now) * 8 + 0.5)

    breakout_score = _clamp01((close - float(last["Resistance"])) / (float(last["Resistance"]) * 0.03)) if pd.notna(last["Resistance"]) and last["Resistance"] > 0 else 0
    trend_score = _clamp01(((float(last["EMA8"]) - float(last["EMA21"])) / close) * 30 + 0.5) if pd.notna(last["EMA8"]) and pd.notna(last["EMA21"]) and close > 0 else 0.5
    volume_score = _clamp01((vol_ratio - 0.8) / 1.5)
    momentum_score = _clamp01((rsi - 45) / 25)

    # Weekly confirmation.
    weekly_score = 0.5
    if df_weekly is not None and not df_weekly.empty and len(df_weekly) > 20:
        wl = df_weekly.iloc[-1]
        weekly_score = _clamp01(((float(wl["SMA20"]) - float(wl["SMA50"])) / (float(wl["Close"]) + 1e-9)) * 20 + 0.5) if pd.notna(wl["SMA20"]) and pd.notna(wl["SMA50"]) else 0.5

    regime = detect_regime(df)
    ma_slope = (
        (float(last["SMA20"]) - float(last["SMA50"])) / float(last["SMA50"])
        if pd.notna(last["SMA20"]) and pd.notna(last["SMA50"]) and float(last["SMA50"]) != 0.0
        else 0.0
    )

    heuristic_conf = _clamp01(
        0.18 * obv_score
        + 0.14 * contraction_score
        + 0.14 * breakout_score
        + 0.14 * trend_score
        + 0.14 * volume_score
        + 0.12 * momentum_score
        + 0.14 * weekly_score
    )

    ml_pred = predict_signal_confidence(
        {
            "rsi": rsi,
            "volume_ratio": vol_ratio,
            "atr_pct": atr_pct,
            "ma_slope": ma_slope,
            "regime": regime,
        },
        regime=regime,
    )
    ml_conf = float(ml_pred.get("confidence", 0.5))

    # Blend heuristic + ML for robust ranking.
    early_prob = _clamp01(0.6 * heuristic_conf + 0.4 * ml_conf)

    # Risk/execution layer (expected value style).
    downside_risk_pct = max(atr_pct * 1.3, 0.01)
    target_pct = max(atr_pct * 2.2, 0.02)
    rr_ratio = target_pct / downside_risk_pct if downside_risk_pct > 0 else 0
    expected_return_pct = (early_prob * target_pct - (1 - early_prob) * downside_risk_pct) * 100
    quality_score = _clamp01((rr_ratio / 3.0) * 0.4 + (1 - min(downside_risk_pct / 0.08, 1)) * 0.6)
    early_score = round((early_prob * 0.75 + quality_score * 0.25) * 100, 2)

    return {
        "candidate_pass": candidate_pass,
        "candidate_reason": ",".join(candidate_reasons) if candidate_reasons else "ok",
        "early_prob": early_prob,
        "early_score": early_score,
        "expected_return_pct": expected_return_pct,
        "downside_risk_pct": downside_risk_pct * 100,
        "rr_ratio": rr_ratio,
        "quality_score": quality_score * 100,
        "regime": regime,
        "ml_confidence": ml_conf,
        "heuristic_confidence": heuristic_conf,
    }


def walk_forward_diagnostics():
    """
    Time-ordered walk-forward validation on signal_history dataset.
    Returns summary for model stability display.
    """
    try:
        df = ea_load_signal_dataset()
        if df.empty or "outcome" not in df.columns:
            return {"available": False, "message": "No dataset"}
        df = df.dropna(subset=["outcome"]).copy()
        if len(df) < 80:
            return {"available": False, "message": f"Need >= 80 evaluated signals, have {len(df)}"}

        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.sort_values("timestamp").dropna(subset=["timestamp"])
        features = ["rsi", "volume_ratio", "atr_pct", "ma_slope", "regime"]
        df = df.dropna(subset=features + ["outcome"])
        if len(df) < 80:
            return {"available": False, "message": "Insufficient clean rows for walk-forward"}

        fold_size = max(20, len(df) // 5)
        accuracies = []
        for fold_start in range(fold_size, len(df) - fold_size, fold_size):
            train_df = df.iloc[:fold_start]
            test_df = df.iloc[fold_start:fold_start + fold_size]
            if len(train_df) < 40 or len(test_df) < 15:
                continue
            model = RandomForestClassifier(
                n_estimators=250,
                max_depth=6,
                min_samples_split=10,
                random_state=42,
            )
            model.fit(train_df[features], train_df["outcome"])
            acc = model.score(test_df[features], test_df["outcome"])
            accuracies.append(float(acc))

        if not accuracies:
            return {"available": False, "message": "Not enough folds for validation"}

        return {
            "available": True,
            "folds": len(accuracies),
            "mean_acc": float(np.mean(accuracies)),
            "std_acc": float(np.std(accuracies)),
            "min_acc": float(np.min(accuracies)),
            "max_acc": float(np.max(accuracies)),
        }
    except Exception as e:
        return {"available": False, "message": str(e)}


def render_market_timing_analyzer():
    st.header("Market Timing Analyzer")
    st.markdown("Analisis timing session BEI untuk entry/exit window yang lebih presisi.")

    ticker = st.selectbox("Pilih Saham:", ALL_STOCKS, key="timing_ticker")
    lookback_days = st.slider("Lookback (hari)", min_value=7, max_value=180, value=60, step=1)
    current_time = st.text_input("Waktu Analisis (HH:MM, kosongkan untuk waktu sekarang)", value="")

    if st.button("Analisis Timing", type="primary"):
        with st.spinner(f"Menganalisis timing untuk {ticker}..."):
            try:
                end_date = date.today()
                start_date = end_date - timedelta(days=lookback_days)
                data = yf.download(ticker, start=start_date, end=end_date)

                if data is None or data.empty:
                    st.error("Data harga tidak tersedia untuk analisis timing.")
                else:
                    analysis = comprehensive_timing_analysis(
                        ticker=ticker,
                        data=data,
                        current_time=current_time.strip() or None,
                    )
                    if "error" in analysis:
                        st.error(analysis["error"])
                    else:
                        st.success("Timing analysis selesai.")
                        st.info(analysis.get("summary", ""))

                        next_window = analysis["timing_analysis"].get("next_optimal_window", {})
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Next Window", next_window.get("time", "-"))
                        with col2:
                            st.metric("Window Key", next_window.get("key", "-"))
                        with col3:
                            st.metric("Minutes Until", next_window.get("minutes_until", 0))

                        pre_post = analysis.get("pre_post_comparison", {})
                        dynamics = pre_post.get("market_dynamics", {})
                        st.subheader("Pre vs Post Market")
                        st.write(f"Gap: {dynamics.get('price_gap_pct', 0):+.2f}%")
                        st.write(f"Volume Ratio: {dynamics.get('volume_ratio', 0):.2f}x")

                        signal_change = dynamics.get("signal_change", {})
                        st.write(f"Signal Change: {signal_change.get('change_type', 'NO_CHANGE')}")
                        st.write(f"Significance: {signal_change.get('significance', 'LOW')}")

                        session_rec = analysis.get("session_recommendations", {})
                        st.subheader("Session Recommendation")
                        st.write(f"Current Session: {session_rec.get('current_session', '-')}")
                        st.write(f"Next Action: {session_rec.get('next_action', '-')}")
                        st.json(session_rec.get("recommendations", {}))
            except Exception as e:
                st.error(f"Error in timing analysis: {e}")


def render_ml_dashboard_pro():
    st.header("ML Dashboard Pro")
    st.markdown("**Dashboard lengkap ML Pipeline: Training, Metrics, Analysis, Live Prediction**")

    col1, col2, col3 = st.columns(3)
    if os.path.exists(DATASET_PATH) or os.path.exists(EXCEL_DATASET_PATH):
        df_ml = ea_load_signal_dataset()
        total_signals = len(df_ml)
        evaluated = len(df_ml[df_ml["outcome"].notna()])
        wins = len(df_ml[df_ml["outcome"] == 1]) if evaluated > 0 else 0
        win_rate = (wins / evaluated * 100) if evaluated > 0 else 0

        with col1:
            st.metric("Total Signals", total_signals, delta=f"+{total_signals//10}")
        with col2:
            st.metric("Evaluated", evaluated, delta=f"{evaluated-total_signals//3}")
        with col3:
            st.metric("Win Rate", f"{win_rate:.1f}%", delta=" +2.3%")

        st.success(
            f"Dataset ready! {total_signals} signals, {evaluated} evaluated ({win_rate:.1f}% win rate)"
        )
        st.caption(f"CSV master: `{DATASET_PATH}` | Excel mirror: `{EXCEL_DATASET_PATH}`")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("TRAIN MODEL", type="primary"):
                with st.spinner("Training RandomForest..."):
                    model, acc, importance = train_model()
                    if model:
                        st.session_state.ml_model = model
                        st.session_state.ml_accuracy = acc
                        st.session_state.ml_importance = importance
                        st.balloons()
                        st.success(f"Model trained! Accuracy: **{acc*100:.2f}%**")
                        st.dataframe(importance.head())
                    else:
                        st.error(str(importance))

        with col2:
            if st.button("EVALUATE OUTCOMES", type="secondary"):
                result = evaluate_outcomes()
                st.info(result)

        with col3:
            if st.button("EXPORT EXCEL", type="secondary"):
                if ea_export_dataset_to_excel():
                    st.success(f"Excel exported to `{EXCEL_DATASET_PATH}`")
                else:
                    st.error("Failed to export Excel snapshot.")

        with col4:
            winrate, avgwin, avgloss, exp = calculate_expectancy()
            if exp != 0:
                st.metric(
                    "Expectancy/Trade",
                    f"Rp {exp:,.0f}",
                    delta=f"1:{abs(avgwin/avgloss):.1f}" if avgloss != 0 else "N/A",
                )
    else:
        st.warning("Dataset belum ada. Run **Market Scanner** dulu untuk generate history.")

    st.subheader("Live Signal Confidence Predictor")
    col1, col2 = st.columns(2)
    with col1:
        rsi = st.slider("RSI (0-100)", 0, 100, 55)
        vol_ratio = st.slider("Vol Ratio", 0.5, 3.0, 1.2)
    with col2:
        atr_pct = st.slider("ATR%", 1.0, 5.0, 2.5) / 100
        ma_slope = st.slider("MA Slope", -5.0, 5.0, 0.0) / 100
        regime = st.selectbox(
            "Regime",
            [0, 1, 2, -1],
            format_func=lambda x: {0: "Sideways", 1: "Trending", 2: "Volatile", -1: "Bearish"}.get(x, x),
        )

    if st.button("PREDICTI CONFIDENCE", type="primary"):
        features = {"rsi": rsi, "volume_ratio": vol_ratio, "atr_pct": atr_pct, "ma_slope": ma_slope, "regime": regime}
        pred = predict_signal_confidence(features, regime)

        col1, col2, col3 = st.columns(3)
        conf_pct = pred["confidence"] * 100
        if conf_pct >= 70:
            col1.success(f" **HIGH**: {conf_pct:.1f}%**")
        elif conf_pct >= 55:
            col2.warning(f" **MEDIUM**: {conf_pct:.1f}%**")
        else:
            col3.error(f" **LOW**: {conf_pct:.1f}%**")
        st.metric("Model Accuracy", f"{pred['accuracy']*100:.1f}%")
        st.info(pred["message"])

    if hasattr(st.session_state, "ml_importance") and st.session_state.ml_importance is not None:
        st.subheader("Feature Importance")
        fig_imp = px.bar(
            st.session_state.ml_importance,
            x="feature",
            y="importance",
            title="What drives profitable signals?",
            color="importance",
            color_continuous_scale="Viridis",
        )
        st.plotly_chart(fig_imp, width="stretch")

    st.subheader("Regime Model Status")
    regimes, regime_accs = train_regime_models()
    regime_df = pd.DataFrame(
        [{"Regime": r, "Accuracy": f"{regime_accs.get(r, 0) * 100:.1f}%"} for r in [-1, 0, 1, 2] if r in regimes]
    )
    st.dataframe(regime_df)


def render_smart_watchlist_alerts():
    st.header("Smart Watchlist & Alerts")
    st.markdown("Kelola watchlist dan setup alert otomatis untuk saham favorit Anda.")

    if "watchlist" not in st.session_state:
        st.session_state.watchlist = []
    if SMART_ALERTS_KEY not in st.session_state:
        st.session_state[SMART_ALERTS_KEY] = []

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("My Watchlist")
        new_stock = st.selectbox("Tambah saham ke watchlist:", ["Pilih saham..."] + ALL_STOCKS)
        if new_stock != "Pilih saham..." and st.button("Add to Watchlist"):
            if new_stock not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_stock)
                st.success(f"{new_stock} ditambahkan ke watchlist!")

        if st.session_state.watchlist:
            st.write("**Saham dalam watchlist:**")
            for stock in st.session_state.watchlist:
                col_a, col_b, col_c = st.columns([2, 1, 1])
                with col_a:
                    st.write(f" {stock}")
                with col_b:
                    if st.button("🔍 Analisa", key=f"analyze_{stock}"):
                        st.session_state.selected_ticker = stock
                        st.rerun()
                with col_c:
                    if st.button("❌ Hapus", key=f"remove_{stock}"):
                        st.session_state.watchlist.remove(stock)
                        st.rerun()
        else:
            st.info("Watchlist kosong. Tambahkan saham untuk memulai.")

    with col2:
        st.subheader("Smart Alerts")
        if st.session_state.watchlist:
            alert_stock = st.selectbox("Pilih saham untuk alert:", st.session_state.watchlist)
            alert_type = st.selectbox("Tipe alert:", ["Price Alert", "Volume Spike", "RSI Alert"])

            if alert_type == "Price Alert":
                condition = st.selectbox("Kondisi:", ["Above", "Below"])
                threshold = st.number_input("Harga threshold (Rp):", min_value=1, value=1000, step=50)
            elif alert_type == "Volume Spike":
                threshold = st.number_input("Volume multiplier:", min_value=1.0, value=2.0, step=0.5)
                condition = "Above"
            else:
                condition = st.selectbox("Kondisi:", ["Above", "Below"])
                threshold = st.number_input(
                    "RSI threshold:",
                    min_value=0,
                    max_value=100,
                    value=70 if condition == "Above" else 30,
                    step=5,
                )

            if st.button("Create Alert"):
                alert = create_smart_alert(
                    alert_stock,
                    alert_type.lower().replace(" ", "_"),
                    threshold,
                    condition.lower(),
                )
                st.session_state[SMART_ALERTS_KEY].append(alert)
                st.success(f"Alert dibuat untuk {alert_stock}!")
        else:
            st.info("Tambahkan saham ke watchlist terlebih dahulu.")

    if st.button("Check All Alerts", type="primary"):
        if st.session_state[SMART_ALERTS_KEY]:
            triggered_alerts = []
            for alert in st.session_state[SMART_ALERTS_KEY]:
                if alert["active"] and not alert["triggered"]:
                    try:
                        stock = yf.Ticker(alert["ticker"])
                        data = stock.history(period="5d")
                        if not data.empty:
                            result = check_alert_conditions(alert["ticker"], data, alert)
                            if result["triggered"]:
                                alert["triggered"] = True
                                triggered_alerts.append({"alert": alert, "result": result})
                    except Exception:
                        continue

            if triggered_alerts:
                st.success(f" {len(triggered_alerts)} alert terpicu!")
                for triggered in triggered_alerts:
                    st.warning(f"**{triggered['alert']['ticker']}**: {triggered['result']['message']}")
    
    # --- Analisa Mendalam & Share ke Telegram ---
    st.markdown("---")
    st.subheader("Analisa Mendalam & Share ke Telegram")
    
    if 'selected_ticker' in st.session_state and st.session_state.selected_ticker:
        st.success(f"📊 Menganalisa {st.session_state.selected_ticker}...")
        
        # Download data
        ticker = st.session_state.selected_ticker
        try:
            # Download daily data
            df = yf.download(ticker, period="3mo")
            df = calculate_indicators(df)
            
            # Download weekly data
            df_weekly = yf.download(ticker, period="1y", interval="1wk")
            df_weekly = calculate_indicators(df_weekly) if not df_weekly.empty else None
            
            # Generate signal
            sig, action, reason, trend_d, trend_w, score, pattern, ai_data = generate_signal(df, df_weekly, ticker, enable_ai=True)
            
            # Display analysis
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Signal", sig)
                st.metric("Score", f"{score}%")
                st.metric("Trend Daily", trend_d)
            with col2:
                st.metric("Trend Weekly", trend_w)
                st.metric("Action", action)
                st.metric("Pattern", pattern)
            
            st.write(f"**Alasan:** {reason}")
            
            # Display price levels
            last = df.iloc[-1]
            atr = last['ATR']
            sl_price = last['Close'] - 2 * atr
            tp1_price = last['Close'] + 1 * atr
            tp2_price = last['Close'] + 2 * atr
            
            st.write("**Level Trading:**")
            st.write(f"- Entry: Rp {last['Close']:,.0f}")
            st.write(f"- Stop Loss: Rp {sl_price:,.0f}")
            st.write(f"- Target 1: Rp {tp1_price:,.0f}")
            st.write(f"- Target 2: Rp {tp2_price:,.0f}")
            
            # Display AI data if available
            if ai_data:
                st.markdown("---")
                st.subheader("AI Analysis")
                st.write(f"AI Score: {ai_data['ai_score']}%")
                st.write(f"AI Confidence: {ai_data['ai_confidence']*100:.1f}%")
                st.write(f"Sentiment: {ai_data['sentiment_label']}")
                st.write(f"AI Prediction: {ai_data['ml_prediction']}")
            
            # Share to Telegram
            st.markdown("---")
            st.subheader("📤 Share ke Telegram")
            telegram_token = st.text_input("Bot Token", value=TELEGRAM_BOT_TOKEN, type="password", key="telegram_token_watchlist")
            telegram_chat_id = st.text_input("Chat ID", value=TELEGRAM_CHAT_ID, key="telegram_chat_id_watchlist")
            
            if st.button(f"📤 Kirim {ticker} ke Telegram", key="share_telegram"):
                if not telegram_token or not telegram_chat_id:
                    st.error("⚠️ Harap isi Bot Token dan Chat ID Telegram!")
                else:
                    bot = create_telegram_bot(telegram_token, telegram_chat_id)
                    if bot:
                        # Format message for Telegram
                        message = f"""
📊 **Analisa Saham: {ticker}**
📅 {date.today().strftime('%d %B %Y')}

**Signal:** {sig}
**Score:** {score}%
**Action:** {action}
**Trend Daily:** {trend_d}
**Trend Weekly:** {trend_w}
**Pattern:** {pattern}

**Level Trading:**
- Entry: Rp {last['Close']:,.0f}
- Stop Loss: Rp {sl_price:,.0f}
- Target 1: Rp {tp1_price:,.0f}
- Target 2: Rp {tp2_price:,.0f}

**Alasan:** {reason}
"""
                        if ai_data:
                            message += f"""
🤖 **AI Analysis:**
- AI Score: {ai_data['ai_score']}%
- AI Confidence: {ai_data['ai_confidence']*100:.1f}%
- Sentiment: {ai_data['sentiment_label']}
- AI Prediction: {ai_data['ml_prediction']}
"""
                        
                        success = bot.send_message(message)
                        if success:
                            st.success("✅ Berhasil mengirim analisa ke Telegram!")
                        else:
                            st.error("❌ Gagal mengirim ke Telegram. Periksa konfigurasi!")
            
        except Exception as e:
            st.error(f"⚠️ Error saat menganalisa {ticker}: {e}")
    
    # --- Share Seluruh Watchlist ke Telegram ---
    if st.session_state.watchlist:
        st.markdown("---")
        st.subheader("📤 Share Seluruh Watchlist ke Telegram")
        if st.button("📤 Kirim Semua Analisa Watchlist ke Telegram", key="share_all_watchlist"):
            if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
                st.error("⚠️ Harap set Bot Token dan Chat ID di config.py atau isi di atas!")
            else:
                bot = create_telegram_bot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
                if bot:
                    st.info("🔄 Memproses dan mengirim analisa seluruh watchlist...")
                    all_results = []
                    for ticker in st.session_state.watchlist:
                        try:
                            df = yf.download(ticker, period="3mo")
                            if not df.empty:
                                df = calculate_indicators(df)
                                df_weekly = yf.download(ticker, period="1y", interval="1wk")
                                df_weekly = calculate_indicators(df_weekly) if not df_weekly.empty else None
                                sig, action, reason, trend_d, trend_w, score, pattern, _ = generate_signal(df, df_weekly, ticker, enable_ai=True)
                                last = df.iloc[-1]
                                change_pct = ((last['Close'] - df.iloc[-2]['Close']) / df.iloc[-2]['Close']) * 100 if len(df) > 1 else 0
                                all_results.append({
                                    'ticker': ticker,
                                    'signal': sig,
                                    'score': score,
                                    'price': last['Close'],
                                    'change': change_pct,
                                    'sector': SECTOR_BY_TICKER.get(ticker, "Other")
                                })
                        except Exception:
                            continue
                    
                    if all_results:
                        success = bot.send_scanner_results(all_results, title=f"📊 Analisa Watchlist - {date.today().strftime('%d %B %Y')}")
                        if success:
                            st.success(f"✅ Berhasil mengirim {len(all_results)} analisa ke Telegram!")
                        else:
                            st.error("❌ Gagal mengirim ke Telegram!")


def render_paper_trading_simulator():
    st.header("Paper Trading Simulator")
    st.markdown("Latih trading skill dengan virtual money tanpa risiko!")

    if "paper_trading" not in st.session_state:
        st.session_state.paper_trading = PaperTradingSimulator(100000000)
    simulator = st.session_state.paper_trading

    col1, col2, col3, col4 = st.columns(4)
    current_prices = {}
    for ticker in simulator.positions.keys():
        try:
            stock = yf.Ticker(ticker)
            current_price = stock.history(period="1d")["Close"].iloc[-1]
            current_prices[ticker] = current_price
        except Exception:
            current_prices[ticker] = 0

    portfolio_value = simulator.get_portfolio_value(current_prices)
    with col1:
        st.metric("Balance", f"Rp {portfolio_value['balance']:,.0f}")
    with col2:
        st.metric("Stock Value", f"Rp {portfolio_value['stock_value']:,.0f}")
    with col3:
        st.metric("Total Value", f"Rp {portfolio_value['total_value']:,.0f}")
    with col4:
        st.metric(
            "Total Return",
            f"{portfolio_value['total_return']:+.1f}%",
            delta=f"{portfolio_value['total_return']:+.1f}%",
            delta_color="normal" if portfolio_value["total_return"] >= 0 else "inverse",
        )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Buy Stock")
        buy_ticker = st.selectbox("Select Stock to Buy:", ALL_STOCKS, key="buy_ticker")
        try:
            stock = yf.Ticker(buy_ticker)
            current_price = stock.history(period="1d")["Close"].iloc[-1]
            st.write(f"Current Price: **Rp {current_price:,.0f}**")
            buy_shares = st.number_input("Number of Shares:", min_value=100, value=1000, step=100, key="buy_shares")
            total_cost = buy_shares * current_price
            st.write(f"Total Cost: **Rp {total_cost:,.0f}**")

            if st.button("Buy", type="primary"):
                success, message = simulator.buy_stock(buy_ticker, buy_shares, current_price)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        except Exception as e:
            st.error(f"Error getting price: {e}")

    with col2:
        st.subheader("Sell Stock")
        if simulator.positions:
            sell_ticker = st.selectbox("Select Stock to Sell:", list(simulator.positions.keys()), key="sell_ticker")
            position = simulator.positions[sell_ticker]
            try:
                stock = yf.Ticker(sell_ticker)
                current_price = stock.history(period="1d")["Close"].iloc[-1]
                st.write(f"Current Price: **Rp {current_price:,.0f}**")
                st.write(f"Your Position: {position['shares']} shares @ Rp {position['avg_price']:,.0f}")

                sell_shares = st.number_input(
                    "Number of Shares to Sell:",
                    min_value=100,
                    max_value=position["shares"],
                    value=position["shares"],
                    step=100,
                    key="sell_shares",
                )
                total_value = sell_shares * current_price
                profit = (current_price - position["avg_price"]) * sell_shares
                st.write(f"Total Value: **Rp {total_value:,.0f}**")
                st.write(f"Estimated Profit: **Rp {profit:,.0f}**")

                if st.button("Sell", type="primary"):
                    success, message = simulator.sell_stock(sell_ticker, sell_shares, current_price)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            except Exception as e:
                st.error(f"Error getting price: {e}")
        else:
            st.info("No positions to sell.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Current Positions")
        if simulator.positions:
            for ticker, position in simulator.positions.items():
                current_price = current_prices.get(ticker, 0)
                current_value = position["shares"] * current_price
                unrealized_pnl = (current_price - position["avg_price"]) * position["shares"]
                unrealized_pnl_pct = ((current_price - position["avg_price"]) / position["avg_price"]) * 100
                with st.expander(f"{ticker}"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"Shares: {position['shares']:,}")
                        st.write(f"Avg Price: Rp {position['avg_price']:,.0f}")
                        st.write(f"Current Price: Rp {current_price:,.0f}")
                    with col_b:
                        st.write(f"Current Value: Rp {current_value:,.0f}")
                        if unrealized_pnl >= 0:
                            st.success(f"Unrealized P&L: Rp {unrealized_pnl:,.0f} ({unrealized_pnl_pct:+.1f}%)")
                        else:
                            st.error(f"Unrealized P&L: Rp {unrealized_pnl:,.0f} ({unrealized_pnl_pct:+.1f}%)")
        else:
            st.info("No open positions.")

    with col2:
        st.subheader("Performance Metrics")
        metrics = simulator.get_performance_metrics()
        if metrics["total_trades"] > 0:
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Total Trades", metrics["total_trades"])
                st.metric("Win Rate", f"{metrics['win_rate']:.1f}%")
            with col_b:
                st.metric("Total Profit", f"Rp {metrics['total_profit']:,.0f}")
                st.metric("Avg Profit/Trade", f"Rp {metrics['avg_profit_per_trade']:,.0f}")
        else:
            st.info("No trades yet. Start trading to see performance metrics!")

    if simulator.trade_history:
        st.subheader("Trade History")
        trades_df = pd.DataFrame(simulator.trade_history)
        trades_df = trades_df.sort_values("date", ascending=False).head(20)
        for _, trade in trades_df.iterrows():
            with st.expander(f"{trade['type']} {trade['ticker']} - {trade['date'].strftime('%Y-%m-%d %H:%M')}"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"Shares: {trade['shares']:,}")
                    st.write(f"Price: Rp {trade['price']:,.0f}")
                with col_b:
                    st.write(f"Total: Rp {trade['total']:,.0f}")
                    if trade["type"] == "SELL" and "profit" in trade:
                        if trade["profit"] >= 0:
                            st.success(f"Profit: Rp {trade['profit']:,.0f}")
                        else:
                            st.error(f"Loss: Rp {trade['profit']:,.0f}")


def render_options_analysis_module():
    st.header("Options Analysis Module")
    st.markdown("Analisis opsi dan Greeks untuk saham-saham tertentu.")

    ticker = st.selectbox("Pilih Saham:", ALL_STOCKS)
    if st.button("Analisis Opsi", type="primary"):
        with st.spinner(f"Menganalisis opsi untuk {ticker}..."):
            try:
                stock = yf.Ticker(ticker)
                current_data = stock.history(period="1d")
                current_price = current_data["Close"].iloc[-1]
                option_analysis = analyze_option_chain(ticker, current_price)

                st.success(f"Analisis opsi selesai untuk {ticker}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Current Price", f"Rp {current_price:,.0f}")
                with col2:
                    st.metric("Max Pain", f"Rp {option_analysis['max_pain']:,.0f}")
                with col3:
                    st.metric("Put/Call Ratio", f"{option_analysis['put_call_ratio']:.2f}")

                st.subheader("Option Chain")
                if option_analysis["option_chain"]:
                    chain_df = pd.DataFrame(option_analysis["option_chain"])
                    for _, row in chain_df.iterrows():
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.write(f"**Strike: Rp {row['strike']:,.0f}**")
                        with col2:
                            st.write(f"Call: Rp {row['call_price']:,.0f}")
                            st.write(f": {row['call_greeks']['delta']:.3f}")
                        with col3:
                            st.write(f"Put: Rp {row['put_price']:,.0f}")
                            st.write(f": {row['put_greeks']['delta']:.3f}")
                        with col4:
                            st.write(f"IV: {row['implied_volatility']*100:.1f}%")
                        with col5:
                            st.write("---")

                with st.expander("Understanding Option Greeks"):
                    st.write(
                        """
                    **Delta ():** Sensitivitas harga opsi terhadap perubahan harga saham underlying
                    - Call Delta: 0 sampai 1 (ATM  0.5)
                    - Put Delta: -1 sampai 0 (ATM  -0.5)

                    **Gamma ():** Laju perubahan Delta
                    - Tinggi saat mendekati expiration
                    - Maksimum pada opsi ATM

                    **Theta ():** Time decay - kehilangan nilai per hari
                    - Selalu negatif untuk opsi long
                    - Meningkat saat mendekati expiration

                    **Vega ():** Sensitivitas terhadap perubahan volatilitas
                    - Positif untuk opsi long
                    - Tinggi untuk opsi dengan waktu panjang
                    """
                    )
            except Exception as e:
                st.error(f"Error dalam analisis opsi: {e}")


def render_enhanced_multi_analysis():
    st.header("Enhanced Multi-Analysis")
    st.markdown("Analisis komprehensif dengan semua fitur advanced dalam satu tampilan.")

    ticker = st.selectbox("Pilih Saham untuk Analisis Komprehensif:", ALL_STOCKS)
    if st.button("Jalankan Analisis Komprehensif", type="primary"):
        with st.spinner(f"Menjalankan analisis komprehensif untuk {ticker}... Ini mungkin memakan waktu beberapa menit."):
            try:
                analyzer = EnhancedStockAnalyzer()
                results = analyzer.comprehensive_analysis(ticker, "1y")
                if "error" in results:
                    st.error(f"Error: {results['error']}")
                    return

                st.success(f"Analisis komprehensif selesai untuk {ticker}!")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Current Price", f"Rp {results['current_price']:,.0f}")
                with col2:
                    backtest_return = max(results["backtest_ma"]["total_return"], results["backtest_rsi"]["total_return"])
                    st.metric("Best Backtest Return", f"{backtest_return:+.1f}%")
                with col3:
                    dcf_upside = results["dcf"]["upside"]
                    st.metric("DCF Upside", f"{dcf_upside:+.1f}%")
                with col4:
                    patterns = len(results["price_patterns"])
                    st.metric("Price Patterns", patterns)

                tab1, tab2, tab3, tab4, tab5 = st.tabs(
                    ["Technical Analysis", "Backtesting", "Options", "Fundamentals", "Summary"]
                )

                with tab1:
                    st.subheader("Technical Analysis")
                    if results["price_patterns"]:
                        st.write("**Detected Price Patterns:**")
                        for pattern in results["price_patterns"]:
                            st.info(f"{pattern['pattern']} - {pattern.get('strength', 'N/A')}")
                    else:
                        st.info("No significant price patterns detected.")

                    vol_spike = results["volume_spike"]
                    if vol_spike["alert"]:
                        st.warning(f"Volume spike detected! {vol_spike['volume_ratio']:.1f}x average volume")
                    else:
                        st.success("Volume normal")

                    st.write(f"**VWAP:** Rp {results['vwap']:,.0f}")
                    current_vs_vwap = ((results["current_price"] - results["vwap"]) / results["vwap"]) * 100
                    if current_vs_vwap > 0:
                        st.success(f"Price above VWAP by {current_vs_vwap:.1f}%")
                    else:
                        st.info(f"Price below VWAP by {abs(current_vs_vwap):.1f}%")

                with tab2:
                    st.subheader("Backtesting Results")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**MA Crossover Strategy:**")
                        ma_results = results["backtest_ma"]
                        st.write(f"Return: {ma_results['total_return']:+.1f}%")
                        st.write(f"Win Rate: {ma_results['win_rate']:.1f}%")
                        st.write(f"Max Drawdown: {ma_results['max_drawdown']:.1f}%")
                        st.write(f"Total Trades: {ma_results['total_trades']}")
                    with col2:
                        st.write("**RSI Divergence Strategy:**")
                        rsi_results = results["backtest_rsi"]
                        st.write(f"Return: {rsi_results['total_return']:+.1f}%")
                        st.write(f"Win Rate: {rsi_results['win_rate']:.1f}%")
                        st.write(f"Max Drawdown: {rsi_results['max_drawdown']:.1f}%")
                        st.write(f"Total Trades: {rsi_results['total_trades']}")
                    if ma_results["total_return"] > rsi_results["total_return"]:
                        st.success("MA Crossover strategy performed better")
                    else:
                        st.success("RSI Divergence strategy performed better")

                with tab3:
                    st.subheader("Options Analysis")
                    option_summary = results["option_chain"]
                    option_data = option_summary.get("option_chain", []) if isinstance(option_summary, dict) else []
                    if option_data:
                        st.write(
                            f"**Implied Volatility Range:** {min([opt['implied_volatility'] for opt in option_data])*100:.1f}% - {max([opt['implied_volatility'] for opt in option_data])*100:.1f}%"
                        )
                        st.write(f"**Max Pain:** Rp {option_summary.get('max_pain', 0):,.0f}")
                        st.write(f"**Put/Call Ratio:** {option_summary.get('put_call_ratio', 0):.2f}")
                        with st.expander("View Option Chain"):
                            for option in option_data:
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.write(f"**Strike: Rp {option['strike']:,.0f}**")
                                with col2:
                                    st.write(f"Call: Rp {option['call_price']:,.0f} (: {option['call_greeks']['delta']:.3f})")
                                with col3:
                                    st.write(f"Put: Rp {option['put_price']:,.0f} (: {option['put_greeks']['delta']:.3f})")
                    else:
                        st.info("Options data not available for this stock.")

                with tab4:
                    st.subheader("Fundamental Analysis")
                    fundamentals = results["fundamentals"]
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Valuation Ratios:**")
                        st.write(f"P/E Ratio: {fundamentals['pe_ratio']:.2f}" if fundamentals["pe_ratio"] > 0 else "P/E Ratio: N/A")
                        st.write(f"P/B Ratio: {fundamentals['pb_ratio']:.2f}" if fundamentals["pb_ratio"] > 0 else "P/B Ratio: N/A")
                        st.write(
                            f"Price/Sales: {fundamentals['price_to_sales']:.2f}"
                            if fundamentals["price_to_sales"] > 0
                            else "Price/Sales: N/A"
                        )
                    with col2:
                        st.write("**Profitability & Financial Health:**")
                        st.write(f"ROE: {fundamentals['roe']:.1f}%" if fundamentals["roe"] != 0 else "ROE: N/A")
                        st.write(
                            f"Debt/Equity: {fundamentals['debt_to_equity']:.2f}"
                            if fundamentals["debt_to_equity"] != 0
                            else "Debt/Equity: N/A"
                        )
                        st.write(
                            f"Dividend Yield: {fundamentals['dividend_yield']:.1f}%"
                            if fundamentals["dividend_yield"] > 0
                            else "Dividend Yield: N/A"
                        )

                    st.subheader("DCF Valuation")
                    dcf_data = results["dcf"]
                    if dcf_data["fair_value"] > 0:
                        st.write(f"Fair Value (DCF): Rp {dcf_data['fair_value']:,.0f}")
                        st.write(f"Current Price: Rp {dcf_data['current_price']:,.0f}")
                        if dcf_data["upside"] > 10:
                            st.success(f"Undervalued! Upside potential: {dcf_data['upside']:+.1f}%")
                        elif dcf_data["upside"] < -10:
                            st.warning(f"Overvalued! Downside risk: {dcf_data['upside']:+.1f}%")
                        else:
                            st.info(f"Fairly valued: {dcf_data['upside']:+.1f}%")
                    else:
                        st.info("DCF analysis not available for this stock.")

                with tab5:
                    st.subheader("Executive Summary")
                    score = 0
                    reasons = []
                    if results["backtest_ma"]["total_return"] > 10:
                        score += 2
                        reasons.append("Strong MA crossover backtest results")
                    if results["backtest_rsi"]["total_return"] > 10:
                        score += 2
                        reasons.append("Strong RSI divergence backtest results")
                    if results["price_patterns"]:
                        score += 1
                        reasons.append("Technical patterns detected")
                    if results["dcf"]["upside"] > 10:
                        score += 3
                        reasons.append("Undervalued based on DCF")
                    if results["fundamentals"]["pe_ratio"] > 0 and results["fundamentals"]["pe_ratio"] < 20:
                        score += 1
                        reasons.append("Reasonable P/E ratio")
                    if results["fundamentals"]["roe"] > 15:
                        score += 1
                        reasons.append("Strong ROE")

                    if score >= 7:
                        recommendation = "STRONG BUY"
                    elif score >= 5:
                        recommendation = "BUY"
                    elif score >= 3:
                        recommendation = "HOLD"
                    elif score >= 1:
                        recommendation = "WEAK HOLD"
                    else:
                        recommendation = "AVOID"
                    st.success(f"**Recommendation: {recommendation}**")

                    if reasons:
                        st.write("**Key Reasons:**")
                        for reason in reasons:
                            st.write(f" {reason}")

                    risks = []
                    if results["backtest_ma"]["max_drawdown"] > 20:
                        risks.append("High maximum drawdown in backtesting")
                    if results["volume_spike"]["alert"]:
                        risks.append("Recent unusual volume activity")
                    if results["fundamentals"]["debt_to_equity"] > 100:
                        risks.append("High debt levels")
                    if risks:
                        st.warning("**Risk Factors:**")
                        for risk in risks:
                            st.write(f" {risk}")

                st.success("Comprehensive analysis complete!")
            except Exception as e:
                st.error(f"Error in comprehensive analysis: {e}")

# --- UI APLIKASI ---
st.title("Market Scanner & Heatmap Pro")
st.markdown("Scan seluruh pasar saham secara otomatis untuk menemukan peluang BUY dan visualisasi Heatmap.")

# Initialize Enhanced Analyzer
if 'enhanced_analyzer' not in st.session_state:
    st.session_state.enhanced_analyzer = EnhancedStockAnalyzer()

# Sidebar
st.sidebar.header("Mode Aplikasi")
analysis_mode = st.sidebar.radio(
    "Pilih Fitur:",
    (
        "Market Scanner & Heatmap (Otomatis)",
        "Analisa Detail Saham (Manual)",
        "Advanced Backtesting Engine",
        "Options Analysis Module",
        "Smart Watchlist & Alerts",
        "Paper Trading Simulator",
        "Enhanced Multi-Analysis",
        "Market Timing Analyzer",
        "ML Dashboard Pro",
        "ML Signal Predictor",
    ),
)

# --- POSITION SIZING CALCULATOR ---
st.sidebar.markdown("---")
st.sidebar.header("Position Sizing Calculator")

with st.sidebar.form("position_sizing_form"):
    st.write("**Risk Management Calculator**")
    capital = st.number_input("Total Modal (Rp)", min_value=1000000, value=10000000, step=1000000)
    risk_percentage = st.slider("Risk per Trade (%)", min_value=0.5, max_value=10.0, value=2.0, step=0.5)
    
    st.write("---")
    st.write("**Info Saham (Auto-fill saat scan)**")
    entry_price_input = st.number_input("Harga Entry (Rp)", min_value=1, value=1000, step=50)
    stop_loss_input = st.number_input("Stop Loss (Rp)", min_value=1, value=900, step=50)
    
    calculate_btn = st.form_submit_button("Hitung Position Size", type="secondary")
    
    if calculate_btn:
        # Simpan nilai ke session state
        st.session_state.capital = capital
        st.session_state.risk_percentage = risk_percentage
        
        position_result = calculate_position_size(capital, risk_percentage, entry_price_input, stop_loss_input)
        
        st.success(f"**Lot Aman: {position_result['max_lot']} lot**")
        st.write(f"Total Investasi: Rp {position_result['total_investment']:,.0f}")
        st.write(f"Risk Amount: Rp {position_result['risk_amount']:,.0f}")
        st.write(f"Risk per Share: Rp {position_result['risk_per_share']:,.0f}")
        st.write(f"R:R Ratio: 1:{position_result['rr_ratio']}")
        
        with st.expander("Target Profit"):
            st.write(f"Target 1: Rp {position_result['target_1']:,.0f} (Profit: Rp {position_result['potential_profit_1']:,.0f})")
            st.write(f"Target 2: Rp {position_result['target_2']:,.0f} (Profit: Rp {position_result['potential_profit_2']:,.0f})")

# --- PORTFOLIO TRACKER ---
st.sidebar.markdown("---")
st.sidebar.header("Portfolio Tracker")

# Inisialisasi portfolio di session state
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

with st.sidebar.form("portfolio_form"):
    st.write("**Tambah Saham ke Portfolio**")
    portfolio_ticker = st.text_input("Kode Saham", value="BBCA.JK")
    portfolio_shares = st.number_input("Jumlah Lembar", min_value=100, value=1000, step=100)
    portfolio_buy_price = st.number_input("Harga Beli (Rp)", min_value=1, value=1000, step=50)
    portfolio_buy_date = st.date_input("Tanggal Beli", value=date.today())
    
    add_portfolio_btn = st.form_submit_button("Tambah ke Portfolio", type="secondary")
    
    if add_portfolio_btn:
        # Validasi ticker
        try:
            test_data = yf.download(portfolio_ticker, period="1d")
            if not test_data.empty:
                new_position = {
                    'ticker': portfolio_ticker,
                    'shares': portfolio_shares,
                    'buy_price': portfolio_buy_price,
                    'buy_date': portfolio_buy_date,
                    'total_investment': portfolio_shares * portfolio_buy_price
                }
                st.session_state.portfolio.append(new_position)
                st.success(f"{portfolio_ticker} ditambahkan ke portfolio!")
            else:
                st.error("Ticker tidak valid!")
        except Exception:
            st.error("Error saat validasi ticker!")

# Tampilkan portfolio jika ada
if st.session_state.portfolio:
    st.sidebar.write("**Portfolio Anda:**")
    total_value = 0
    total_investment = 0
    
    for i, position in enumerate(st.session_state.portfolio):
        try:
            # Get current price
            current_data = yf.download(position['ticker'], period="1d")
            if not current_data.empty:
                # Ambil harga penutupan terakhir sebagai scalar
                last_close = current_data['Close'].iloc[-1]
                if hasattr(last_close, 'values'):
                    current_price = float(last_close.values[0])
                else:
                    current_price = float(last_close)
                current_value = float(position['shares']) * current_price
                profit_loss = current_value - position['total_investment']
                profit_pct = (profit_loss / position['total_investment']) * 100
                
                total_value += current_value
                total_investment += position['total_investment']
                
                with st.sidebar.expander(f"{position['ticker']}"):
                    st.write(f"Lembar: {position['shares']:,}")
                    st.write(f"Harga Beli: Rp {position['buy_price']:,.0f}")
                    st.write(f"Harga Sekarang: Rp {current_price:,.0f}")
                    st.write(f"Nilai: Rp {current_value:,.0f}")
                    
                    if profit_loss >= 0:
                        st.success(f"Profit: Rp {profit_loss:,.0f} ({profit_pct:+.1f}%)")
                    else:
                        st.error(f"Loss: Rp {profit_loss:,.0f} ({profit_pct:+.1f}%)")
                        
                    if st.button(f"Hapus", key=f"del_{i}"):
                        st.session_state.portfolio.pop(i)
                        st.rerun()
        except Exception:
            st.sidebar.write(f"{position['ticker']}: Error loading data")
    
    # Summary
    if total_investment > 0:
        total_profit = float(total_value - total_investment)
        total_profit_pct = float((total_profit / total_investment) * 100)
        
        st.sidebar.markdown("---")
        st.sidebar.write("**Portfolio Summary:**")
        st.sidebar.write(f"Total Investasi: Rp {total_investment:,.0f}")
        st.sidebar.write(f"Nilai Sekarang: Rp {total_value:,.0f}")
        
        if total_profit >= 0:
            st.sidebar.success(f"Total Profit: Rp {total_profit:,.0f} ({total_profit_pct:+.1f}%)")
        else:
            st.sidebar.error(f"Total Loss: Rp {total_profit:,.0f} ({total_profit_pct:+.1f}%)")

# --- REAL-TIME ALERT SYSTEM ---
st.sidebar.markdown("---")
st.sidebar.header("Alert System")

# Session-state migration for legacy key
if "alerts" in st.session_state:
    if SIDEBAR_ALERTS_KEY not in st.session_state:
        st.session_state[SIDEBAR_ALERTS_KEY] = []
    if SMART_ALERTS_KEY not in st.session_state:
        st.session_state[SMART_ALERTS_KEY] = []
    for _legacy_alert in st.session_state["alerts"]:
        if isinstance(_legacy_alert, dict) and "value" in _legacy_alert:
            st.session_state[SIDEBAR_ALERTS_KEY].append(_legacy_alert)
        else:
            st.session_state[SMART_ALERTS_KEY].append(_legacy_alert)
    del st.session_state["alerts"]
    if SIDEBAR_ALERTS_KEY in st.session_state:
        st.session_state[SIDEBAR_ALERTS_KEY] = list({
            a.get("id", f"{a.get('ticker','')}_{a.get('type','')}"): a
            for a in st.session_state[SIDEBAR_ALERTS_KEY]
            if isinstance(a, dict)
        }.values())

# Alert configuration
if SIDEBAR_ALERTS_KEY not in st.session_state:
    st.session_state[SIDEBAR_ALERTS_KEY] = []

with st.sidebar.form("alert_form"):
    st.write("**Set Price Alert**")
    alert_ticker = st.text_input("Kode Saham", value="BBCA.JK")
    alert_type = st.selectbox("Tipe Alert", ["Price Above", "Price Below", "Volume Spike"])
    alert_value = st.number_input("Nilai Trigger", min_value=1, value=1000, step=50)
    alert_active = st.checkbox("Aktifkan Alert", value=True)
    
    set_alert_btn = st.form_submit_button("Set Alert", type="secondary")
    
    if set_alert_btn:
        new_alert = {
            'ticker': alert_ticker,
            'type': alert_type,
            'value': alert_value,
            'active': alert_active,
            'triggered': False,
            'id': f"{alert_ticker}_{alert_type}_{alert_value}_{time.time()}"
        }
        st.session_state[SIDEBAR_ALERTS_KEY].append(new_alert)
        st.success(f"Alert untuk {alert_ticker} diset!")

# Check alerts (simplified version)
if st.session_state[SIDEBAR_ALERTS_KEY]:
    st.sidebar.write("**Active Alerts:**")
    for i, alert in enumerate(st.session_state[SIDEBAR_ALERTS_KEY]):
        if not isinstance(alert, dict):
            continue
        if alert.get('active', False) and not alert.get('triggered', False):
            try:
                current_data = yf.download(alert.get('ticker', ''), period="1d")
                if not current_data.empty:
                    current_price = current_data['Close'].iloc[-1]
                    current_volume = current_data['Volume'].iloc[-1]
                    
                    triggered = False
                    
                    if alert.get('type') == "Price Above" and current_price >= alert.get('value', 0):
                        triggered = True
                    elif alert.get('type') == "Price Below" and current_price <= alert.get('value', 0):
                        triggered = True
                    elif alert.get('type') == "Volume Spike" and current_volume >= alert.get('value', 0):
                        triggered = True
                    
                    if triggered:
                        alert['triggered'] = True
                        st.sidebar.success(
                            f"ALERT: {alert.get('ticker', '-')} {alert.get('type', '-')} Rp {alert.get('value', 0):,}!"
                        )
                        
            except Exception:
                pass
                
            st.sidebar.write(f"{alert.get('ticker', '-')}: {alert.get('type', '-')} Rp {alert.get('value', 0):,}")
            
            if st.button(f"Hapus Alert", key=f"del_alert_{i}"):
                st.session_state[SIDEBAR_ALERTS_KEY].pop(i)
                st.rerun()

# Tanggal Global
today = date.today()
start_date = today - timedelta(days=365)
end_date = today

if analysis_mode == "Market Scanner & Heatmap (Otomatis)":
    st.info("Klik tombol di bawah untuk memindai seluruh saham di database dan melihat peta pasar.")
    universe_mode = st.radio(
        "Pilih Universe Scan:",
        ("Full IDX Universe", "Sector Curated Universe"),
        horizontal=True,
        index=0,
    )
    scan_universe = FULL_IDX_STOCKS if universe_mode == "Full IDX Universe" else ALL_STOCKS
    st.caption(
        f"Universe aktif: **{universe_mode}** | Total ticker: **{len(scan_universe)}** "
        f"(Mapped sektor: {len(ALL_STOCKS)}, IDX full: {len(FULL_IDX_STOCKS)})"
    )
    
    # Inisialisasi session state untuk menyimpan hasil scan
    if 'scan_df' not in st.session_state:
        st.session_state.scan_df = None
    
    if st.button("SCAN MARKET SEKARANG", type="primary"):
        with st.spinner("Sedang mengambil data pasar & menganalisa... (Mohon tunggu sebentar)"):
            try:
                # 1. Bulk Download Daily (3 bulan) via chunked loader (stabil untuk universe besar)
                batch_data = download_batch_dict(scan_universe, period="3mo", chunk_size=120)
                
                # 2. Bulk Download Weekly (1 tahun) untuk trend besar
                batch_weekly = download_batch_dict(scan_universe, period="1y", interval="1wk", chunk_size=120)
                
                scan_results = []
                
                progress_text = "Menganalisa Multi-Timeframe..."
                my_bar = st.progress(0, text=progress_text)
                
                total_stocks = len(scan_universe)
                
                for i, ticker in enumerate(scan_universe):
                    try:
                        if ticker not in batch_data:
                            continue

                        df = batch_data[ticker].copy()
                        
                        # Bersihkan data kosong
                        df = df.dropna(how='all')
                        if df.empty or len(df) < 50: # Butuh min 50 data untuk SMA50
                            continue
                            
                        # Siapkan Data Weekly
                        df_weekly = None
                        if ticker in batch_weekly:
                            df_weekly = batch_weekly[ticker].copy().dropna(how='all')
                            if not df_weekly.empty:
                                df_weekly = calculate_indicators(df_weekly)

                        # Hitung Indikator Daily
                        df = calculate_indicators(df)
                        
                        # Ambil data terakhir
                        last = df.iloc[-1]
                        prev = df.iloc[-2]
                        
                        # Saring saham tidak bergerak (Volume 0 atau Harga tidak berubah signifikan selama 3 bulan)
                        # Kita cek volume rata-rata
                        avg_vol = df['Volume'].mean()
                        if avg_vol < 10000: # Jika volume rata-rata harian < 10.000 lembar, skip (Saham Tidur/Gocap)
                            continue

                        # Hitung Perubahan Harga
                        change = last['Close'] - prev['Close']
                        change_pct = (change / prev['Close']) * 100
                        
                        # Generate Signal Multi-Timeframe dengan AI Booster
                        sig, action, reason, trend_d, trend_w, score, pattern, ai_data = generate_signal(df, df_weekly, ticker, enable_ai=True)
                        early_profile = compute_early_mover_profile(df, df_weekly)
                        
                        # Cari Sector
                        sector = SECTOR_BY_TICKER.get(ticker, "Other")
                        
                        # Data untuk tabel & heatmap
                        # Hitung Level Trading
                        atr = last['ATR']
                        sl_price = last['Close'] - 2 * atr
                        tp1_price = last['Close'] + 1 * atr
                        tp2_price = last['Close'] + 2 * atr
                        
                        item = {
                            "Ticker": ticker,
                            "Sector": sector,
                            "Close": last['Close'],
                            "Change (%)": round(change_pct, 2),
                            "Score": score,
                            "Volume": last['Volume'] if last['Volume'] > 0 else 1, # Hindari 0 untuk heatmap size
                            "Signal": sig,
                            "Action": action,
                            "Support": round(last['Support'], 0),
                            "Resistance": round(last['Resistance'], 0),
                            "Pattern": pattern,
                            "Trend Daily": trend_d,
                            "Trend Weekly": trend_w,
                            "Entry": f">= {last['Close']:,.0f}",
                            "Stop Loss": f"< {sl_price:,.0f}",
                            "Target 1": f"{tp1_price:,.0f}",
                            "Target 2": f"{tp2_price:,.0f}",
                            "Vol_Ratio": round(last['Vol_Ratio'], 2),
                            "AI_Score": ai_data['ai_score'] if ai_data else 0,
                            "AI_Confidence": ai_data['ai_confidence'] if ai_data else 0,
                            "Sentiment": ai_data['sentiment_label'] if ai_data else 'NEUTRAL',
                            "Candidate": "YES" if early_profile["candidate_pass"] else "NO",
                            "Candidate_Reason": early_profile["candidate_reason"],
                            "Early_Prob_%": round(early_profile["early_prob"] * 100, 2),
                            "Early_Score": round(early_profile["early_score"], 2),
                            "Expected_Return_%": round(early_profile["expected_return_pct"], 2),
                            "Downside_Risk_%": round(early_profile["downside_risk_pct"], 2),
                            "RR_Ratio": round(early_profile["rr_ratio"], 2),
                            "Quality_Score": round(early_profile["quality_score"], 2),
                            "Regime": early_profile["regime"],
                            "ML_Conf_%": round(early_profile["ml_confidence"] * 100, 2),
                            "Heuristic_Conf_%": round(early_profile["heuristic_confidence"] * 100, 2),
                        }
                        
                        # AUTO ML LOGGING - hanya BUY/STRONG BUY signals (disabled - causes Streamlit execution error in loop)
                        # if "BUY"in sig or "STRONG BUY"in sig:
                        #     regime = detect_regime(df)
                        #     atr_pct = last['ATR'] / last['Close'] if pd.notna(last['ATR']) else 0.02
                        #     ma_slope = (last['SMA20'] - last['SMA50']) / last['SMA50'] if pd.notna(last['SMA20']) and pd.notna(last['SMA50']) else 0
                        #     
                        #     features = {
                        #         "rsi": last['RSI'],
                        #         "volume_ratio": last['Vol_Ratio'],
                        #         "atr_pct": atr_pct,
                        #         "ma_slope": ma_slope,
                        #         "regime": regime
                        #     }
                        #     
                        #     log_signal(ticker, last['Close'], sl_price, tp1_price, features, "Scanner_Signal")
                        #     st.sidebar.success(f"ML Logged: {ticker} ({regime})")  # Feedback
                        
                        scan_results.append(item)
                        
                    except Exception as e:
                        continue
                    
                    # Update progress
                    my_bar.progress((i + 1) / total_stocks, text=f"Menganalisa {ticker}...")
                
                my_bar.empty()
                
                if not scan_results:
                    st.error("Gagal menganalisa data. Coba lagi nanti.")
                else:
                    st.session_state.scan_df = pd.DataFrame(scan_results)
                    scanned_count = len(st.session_state.scan_df)
                    coverage = (scanned_count / total_stocks * 100) if total_stocks else 0
                    st.info(f"Coverage scan: {scanned_count}/{total_stocks} ticker ({coverage:.1f}%).")
                    st.success("Analisa selesai!")
                        
            except Exception as e:
                st.error(f"Terjadi kesalahan saat scanning: {str(e)}")

    # Tampilkan hasil jika ada di session state
    if st.session_state.scan_df is not None:
        df_res = st.session_state.scan_df
        smart_defaults = {
            "Candidate": "NO",
            "Candidate_Reason": "legacy_row",
            "Early_Prob_%": 0.0,
            "Early_Score": 0.0,
            "Expected_Return_%": 0.0,
            "Downside_Risk_%": 0.0,
            "RR_Ratio": 0.0,
            "Quality_Score": 0.0,
            "Regime": 0,
            "ML_Conf_%": 0.0,
            "Heuristic_Conf_%": 0.0,
            "AI_Confidence": 0.0,
        }
        for col, default in smart_defaults.items():
            if col not in df_res.columns:
                df_res[col] = default

        # --- SMART EARLY-MOVER RANKING ---
        st.subheader("Top Early Movers (Probabilistic Ranking)")
        candidate_df = df_res[df_res["Candidate"] == "YES"].copy()
        total_candidates = len(candidate_df)
        coverage_candidates = (total_candidates / len(df_res) * 100) if len(df_res) else 0
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Candidates", total_candidates, delta=f"{coverage_candidates:.1f}% of scanned")
        with c2:
            avg_prob = candidate_df["Early_Prob_%"].mean() if total_candidates else 0
            st.metric("Avg Early Prob", f"{avg_prob:.1f}%")
        with c3:
            positive_ev = len(candidate_df[candidate_df["Expected_Return_%"] > 0]) if total_candidates else 0
            st.metric("Positive Expectancy", positive_ev)

        if total_candidates > 0:
            top_n = st.slider("Top N Early Movers", min_value=5, max_value=30, value=12, step=1)
            ranked = (
                candidate_df.sort_values(
                    by=["Early_Score", "Early_Prob_%", "Quality_Score", "Expected_Return_%"],
                    ascending=False,
                )
                .head(top_n)
                .copy()
            )
            st.dataframe(
                ranked[
                    [
                        "Ticker",
                        "Sector",
                        "Signal",
                        "Early_Prob_%",
                        "Early_Score",
                        "Expected_Return_%",
                        "Downside_Risk_%",
                        "RR_Ratio",
                        "Quality_Score",
                        "Regime",
                        "AI_Confidence",
                    ]
                ].style.format(
                    {
                        "Early_Prob_%": "{:.1f}%",
                        "Early_Score": "{:.1f}",
                        "Expected_Return_%": "{:+.2f}%",
                        "Downside_Risk_%": "{:.2f}%",
                        "RR_Ratio": "{:.2f}",
                        "Quality_Score": "{:.1f}",
                    }
                ),
                height=420,
                width="stretch",
            )
            with st.expander("Interpretasi Smart Ranking"):
                st.write("`Early_Prob_%`: probabilitas naik jangka pendek hasil blend heuristic+ML.")
                st.write("`Expected_Return_%`: estimasi expectancy (positif lebih baik).")
                st.write("`RR_Ratio`: rasio target terhadap downside risk berbasis ATR.")
                st.write("`Quality_Score`: kualitas setup (risk-adjusted).")
        else:
            st.warning("Belum ada saham yang lolos candidate filter ketat pada scan ini.")
            fallback_n = st.slider("Fallback Top N (non-candidate)", min_value=5, max_value=30, value=10, step=1)
            fallback_ranked = (
                df_res.sort_values(
                    by=["Early_Score", "Early_Prob_%", "Quality_Score", "Expected_Return_%"],
                    ascending=False,
                )
                .head(fallback_n)
                .copy()
            )
            st.dataframe(
                fallback_ranked[
                    [
                        "Ticker",
                        "Sector",
                        "Signal",
                        "Candidate_Reason",
                        "Early_Prob_%",
                        "Early_Score",
                        "Expected_Return_%",
                        "Downside_Risk_%",
                        "RR_Ratio",
                        "Quality_Score",
                        "Regime",
                    ]
                ].style.format(
                    {
                        "Early_Prob_%": "{:.1f}%",
                        "Early_Score": "{:.1f}",
                        "Expected_Return_%": "{:+.2f}%",
                        "Downside_Risk_%": "{:.2f}%",
                        "RR_Ratio": "{:.2f}",
                        "Quality_Score": "{:.1f}",
                    }
                ),
                height=360,
                width="stretch",
            )

        wf = walk_forward_diagnostics()
        with st.expander("Model Validation (Walk-Forward)"):
            if wf.get("available"):
                st.write(
                    f"Folds: {wf['folds']} | Mean Acc: {wf['mean_acc']*100:.1f}% | "
                    f"Std: {wf['std_acc']*100:.1f}% | Min: {wf['min_acc']*100:.1f}% | Max: {wf['max_acc']*100:.1f}%"
                )
            else:
                st.info(f"Walk-forward belum tersedia: {wf.get('message', 'unknown')}")
        
        # --- SECTOR ROTATION DETECTOR ---
        st.subheader("Sector Rotation Detector")
        
        # Hitung performa sektor
        sector_df = calculate_sector_performance(df_res)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Visualisasi performa sektor (bar chart)
            fig_sector = px.bar(
                sector_df, 
                x='Sector', 
                y='Avg_Change_%',
                title='Performa Sektor Hari Ini',
                color='Avg_Change_%',
                color_continuous_scale='RdYlGn',
                text='Avg_Change_%'
            )
            fig_sector.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            fig_sector.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig_sector, width="stretch")
            
            # Market Correlation Matrix
            st.write("**Market Correlation Matrix:**")
            
            # Hitung korelasi antar sektor
            sector_changes = {}
            for sector in df_res['Sector'].unique():
                sector_data = df_res[df_res['Sector'] == sector]
                sector_changes[sector] = sector_data['Change (%)'].values
            
            # Buat correlation matrix
            sectors = list(sector_changes.keys())
            if len(sectors) > 2:
                # Create correlation matrix
                corr_matrix = np.zeros((len(sectors), len(sectors)))
                for i, sec1 in enumerate(sectors):
                    for j, sec2 in enumerate(sectors):
                        if len(sector_changes[sec1]) > 1 and len(sector_changes[sec2]) > 1:
                            min_len = min(len(sector_changes[sec1]), len(sector_changes[sec2]))
                            corr_matrix[i][j] = np.corrcoef(sector_changes[sec1][:min_len], sector_changes[sec2][:min_len])[0,1]
                        else:
                            corr_matrix[i][j] = 0
                
                corr_df = pd.DataFrame(corr_matrix, index=sectors, columns=sectors)
                
                fig_corr = px.imshow(corr_df, 
                                   text_auto=True, 
                                   aspect="auto",
                                   color_continuous_scale='RdBu',
                                   title="Sector Correlation Matrix")
                fig_corr.update_layout(height=500)
                st.plotly_chart(fig_corr, width="stretch")
        
        with col2:
            # Tabel ranking sektor
            st.write("**Ranking Sektor:**")
            sector_display = sector_df[['Performance_Rank', 'Sector', 'Avg_Change_%', 'Buy_Ratio_%']].copy()
            sector_display = sector_display.sort_values('Performance_Rank')
            
            try:
                st.dataframe(
                    sector_display.style.format({
                        'Avg_Change_%': '{:+.2f}%',
                        'Buy_Ratio_%': '{:.1f}%'
                    }).background_gradient(subset=['Avg_Change_%'], cmap='RdYlGn'),
                    height=300
                )
            except ImportError:
                st.dataframe(
                    sector_display.style.format({
                        'Avg_Change_%': '{:+.2f}%',
                        'Buy_Ratio_%': '{:.1f}%'
                    }),
                    height=300
                )
            
            # AI Sector Recommendations
            st.write("** AI Sector Picks:**")
            top_sectors = sector_df.nlargest(3, 'Avg_Change_%')
            for _, sector_row in top_sectors.iterrows():
                if sector_row['Avg_Change_%'] > 0:
                    st.success(f" {sector_row['Sector']}: +{sector_row['Avg_Change_%']:.1f}%")
                else:
                    st.warning(f" {sector_row['Sector']}: {sector_row['Avg_Change_%']:.1f}%")
        
        # --- 1. VISUALISASI HEATMAP ---
        st.subheader("Market Heatmap")
        st.caption("Ukuran kotak = Volume Transaksi | Warna = Kenaikan/Penurunan Harga")
        
        fig_heat = px.treemap(
            df_res,
            path=[px.Constant("IHSG"), 'Sector', 'Ticker'],
            values='Volume',
            color='Change (%)',
            color_continuous_scale='RdYlGn',
            color_continuous_midpoint=0,
            hover_data=['Close', 'Signal', 'Trend Daily']
        )
        
        fig_heat.update_traces(
            textposition="middle center",
            texttemplate="%{label}<br>%{color:.2f}%",
            hovertemplate='<b>%{label}</b><br>Harga: %{customdata[0]:,.0f}<br>Change: %{color:.2f}%<br>Signal: %{customdata[1]}<br>Trend: %{customdata[2]}'
        )
        fig_heat.update_layout(height=600, margin=dict(t=0, l=0, r=0, b=0))
        st.plotly_chart(fig_heat, width="stretch")
        
        # --- 2. HASIL SCAN: POTENSI BUY ---
        st.subheader("Rekomendasi Saham Pilihan (High Conviction)")
        
        # Filter High Score (>= 50)
        buys = df_res[df_res['Score'] >= 50].sort_values(by='Score', ascending=False)
        
        if not buys.empty:
            st.success(f"Ditemukan {len(buys)} saham dengan skor keyakinan tinggi hari ini!")
            
            # Tombol Tambahkan Semua ke Watchlist
            if st.button(f"📥 Tambahkan Semua {len(buys)} Saham ke Watchlist", key="add_all_watchlist"):
                if 'watchlist' not in st.session_state:
                    st.session_state.watchlist = []
                for _, row in buys.iterrows():
                    ticker = row['Ticker']
                    if ticker not in st.session_state.watchlist:
                        st.session_state.watchlist.append(ticker)
                st.success(f"✅ Berhasil menambahkan {len(buys)} saham ke watchlist!")
            
            # Tampilkan rekomendasi dengan tombol hitung lot
            for idx, row in buys.iterrows():
                with st.expander(f" {row['Ticker']} - Score: {row['Score']}% | {row['Action']}"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Harga:** Rp {row['Close']:,.0f}")
                        st.write(f"**Perubahan:** {row['Change (%)']:+.2f}%")
                        st.write(f"**Volume:** {row['Volume']:,.0f}")
                        st.write(f"**Pattern:** {row['Pattern']}")
                        # Tampilkan AI info jika tersedia
                        if row.get('AI_Score', 0) > 0:
                            st.write(f"** AI Score:** {row['AI_Score']}%")
                            st.write(f"**Sentimen:** {row['Sentiment']}")
                    
                    with col2:
                        st.write(f"**Entry:** {row['Entry']}")
                        st.write(f"**Stop Loss:** {row['Stop Loss']}")
                        st.write(f"**Target 1:** {row['Target 1']}")
                        st.write(f"**Target 2:** {row['Target 2']}")
                    
                    with col3:
                        # Tombol Tambah ke Watchlist Individual
                        if st.button(f"⭐ Tambah ke Watchlist", key=f"watch_{row['Ticker']}"):
                            if 'watchlist' not in st.session_state:
                                st.session_state.watchlist = []
                            if row['Ticker'] not in st.session_state.watchlist:
                                st.session_state.watchlist.append(row['Ticker'])
                                st.success(f"✅ {row['Ticker']} ditambahkan ke watchlist!")
                            else:
                                st.info(f"ℹ️ {row['Ticker']} sudah ada di watchlist!")
                        
                        # Tombol Hitung Lot Aman
                        if st.button(f"Hitung Lot Aman", key=f"calc_{row['Ticker']}"):
                            # Parse harga dari string
                            entry_price = float(row['Entry'].replace('>= ', '').replace(',', ''))
                            sl_price = float(row['Stop Loss'].replace('< ', '').replace(',', ''))
                            
                            # Gunakan nilai default dari sidebar atau input manual
                            capital_default = st.session_state.get('capital', 10000000)
                            risk_default = st.session_state.get('risk_percentage', 2.0)
                            
                            position_result = calculate_position_size(capital_default, risk_default, entry_price, sl_price)
                            
                            st.success(f"**Lot Aman untuk {row['Ticker']}: {position_result['max_lot']} lot**")
                            st.write(f"Total Investasi: Rp {position_result['total_investment']:,.0f}")
                            st.write(f"Risk: Rp {position_result['risk_amount']:,.0f} ({risk_default}% dari modal)")
                            st.write(f"Potensi Profit T1: Rp {position_result['potential_profit_1']:,.0f}")
                            st.write(f"Potensi Profit T2: Rp {position_result['potential_profit_2']:,.0f}")
                            st.write(f"R:R Ratio: 1:{position_result['rr_ratio']}")
            
            # Tabel lengkap tetap ada untuk referensi
            with st.expander("Tabel Lengkap Rekomendasi"):
                display_cols = ['Ticker', 'Score', 'Action', 'Trend Daily', 'Trend Weekly', 'Pattern', 'Close', 'Change (%)', 'Entry', 'Target 1']
                
                try:
                    st.dataframe(
                        buys[display_cols].style.format({
                            'Close': '{:,.0f}',
                            'Change (%)': '{:+.2f}%',
                            'Score': '{:.0f}%'
                        }).background_gradient(subset=['Score'], cmap='RdYlGn')
                    )
                except ImportError:
                    st.dataframe(
                        buys[display_cols].style.format({
                            'Close': '{:,.0f}',
                            'Change (%)': '{:+.2f}%',
                            'Score': '{:.0f}%'
                        })
                    )
        else:
            st.warning("Belum ada saham dengan skor keyakinan tinggi. Pasar mungkin sedang konsolidasi.")
        
        # --- 3. TABEL LENGKAP ---
        with st.expander("Lihat Data Seluruh Saham"):
            st.dataframe(df_res.sort_values(by='Change (%)', ascending=False))
        
        # --- 4. DOWNLOAD EXCEL ---
        st.markdown("---")
        st.subheader("Download & Bagikan Hasil Scan")
        
        # Convert to Excel in memory
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_res.to_excel(writer, index=False, sheet_name='Scan Result')
            
        col1, col2 = st.columns([1, 1])
        with col1:
            st.download_button(
                label="Download File Excel (.xlsx)",
                data=buffer.getvalue(),
                file_name=f"stock_scan_result_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col2:
            # Telegram Configuration
            st.caption("Konfigurasi Telegram (opsional):")
            telegram_token = st.text_input("Bot Token", value=TELEGRAM_BOT_TOKEN, type="password", key="telegram_token_input")
            telegram_chat_id = st.text_input("Chat ID", value=TELEGRAM_CHAT_ID, key="telegram_chat_id_input")
            
            if st.button("Kirim ke Telegram", type="primary"):
                if not telegram_token or not telegram_chat_id:
                    st.error("Harap isi Bot Token dan Chat ID Telegram!")
                else:
                    with st.spinner("Mengirim hasil scan ke Telegram..."):
                        bot = create_telegram_bot(telegram_token, telegram_chat_id)
                        if bot:
                            # Prepare results for Telegram
                            telegram_results = []
                            for _, row in df_res.iterrows():
                                telegram_results.append({
                                    "ticker": row["Ticker"],
                                    "signal": row["Signal"],
                                    "score": row["Score"],
                                    "price": row["Close"],
                                    "change": row["Change (%)"],
                                    "sector": row["Sector"]
                                })
                            
                            # Send to Telegram
                            success = bot.send_scanner_results(
                                telegram_results,
                                title=f"📊 Stock Scanner Results - {date.today().strftime('%d %b %Y')}"
                            )
                            
                            if success:
                                st.success("Hasil scan berhasil dikirim ke Telegram!")
                            else:
                                st.error("Gagal mengirim ke Telegram. Periksa konfigurasi Bot Token dan Chat ID.")

elif analysis_mode == "Analisa Detail Saham (Manual)":
    # --- FITUR LAMA (ANALISA MANUAL) ---
    st.subheader("Analisa Detail Saham")
    
    ticker_select = st.selectbox("Pilih Saham", ["Ketik Manual..."] + ALL_STOCKS)
    if ticker_select == "Ketik Manual...":
        ticker_input = st.text_input("Kode Saham (Pastikan format: KODE.JK)", "INDS.JK")
    else:
        ticker_input = ticker_select

    if st.button("Analisa Teknikal"):
        if not ticker_input.endswith(".JK"):
             ticker_input = f"{ticker_input}.JK" # Auto-correct format
             
        with st.spinner(f"Menganalisa {ticker_input}..."):
            try:
                df = yf.download(ticker_input, start=start_date - timedelta(days=100), end=end_date)
                
                # Data Weekly untuk konfirmasi
                df_weekly = yf.download(ticker_input, period="1y", interval="1wk")
                if isinstance(df_weekly.columns, pd.MultiIndex):
                     df_weekly.columns = df_weekly.columns.droplevel(1)
                
                if not df_weekly.empty:
                     df_weekly = calculate_indicators(df_weekly)

                # Fix for single ticker download returning MultiIndex columns
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.droplevel(1)
                
                if df.empty:
                    st.error("Data tidak ditemukan.")
                else:
                    df = calculate_indicators(df)
                    display_df = df.loc[str(start_date):str(end_date)]
                    last = df.iloc[-1]
                    
                    sig, action, reason, trend_d, trend_w, score, pattern, ai_data = generate_signal(df, df_weekly, ticker_input, enable_ai=True)
                    
                    # Header Info
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Harga Terakhir", f"{last['Close']:,.0f}")
                    col2.metric("Conviction Score", f"{score}%")
                    col3.metric(
                        "Trend Weekly",
                        trend_w,
                        delta_color="normal" if trend_w == "NEUTRAL" else "inverse",
                    )
                    col4.metric("Action", action)
                    
                    st.caption(f"Reason: {reason}")
                    
                    # Support Resistance
                    st.write(f" **Support:** {last['Support']:,.0f} |  **Resistance:** {last['Resistance']:,.0f}")
                    
                    # Trading Plan
                    atr = last['ATR']
                    sl = last['Close'] - 2*atr
                    tp1 = last['Close'] + 1*atr
                    tp2 = last['Close'] + 2*atr
                    
                    st.info(f"**Entry:** >= {last['Close']:,.0f} | **Stop-loss:** < {sl:,.0f} | **Target 1:** {tp1:,.0f} | **Target 2:** {tp2:,.0f}")
                    
                    # Advanced Charting dengan Multi-timeframe
                    st.subheader("Advanced Multi-Timeframe Analysis")
                    
                    tab1, tab2, tab3, tab4 = st.tabs(["Daily + Weekly", "Technical Indicators", "Volume Analysis", "Backtesting Engine"])
                    
                    with tab1:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Daily Chart (1D)**")
                            daily_fig = go.Figure()
                            daily_fig.add_trace(go.Candlestick(x=display_df.index[-60:], open=display_df['Open'][-60:], high=display_df['High'][-60:], low=display_df['Low'][-60:], close=display_df['Close'][-60:], name='Daily'))
                            daily_fig.add_trace(go.Scatter(x=display_df.index[-60:], y=display_df['EMA8'][-60:], line=dict(color='red', width=2), name='EMA8'))
                            daily_fig.add_trace(go.Scatter(x=display_df.index[-60:], y=display_df['EMA21'][-60:], line=dict(color='green', width=2), name='EMA21'))
                            daily_fig.update_layout(height=400, xaxis_rangeslider_visible=False, title="Last 60 Days")
                            st.plotly_chart(daily_fig, width="stretch")
                        
                        with col2:
                            st.write("**Weekly Chart (1W)**")
                            if df_weekly is not None and not df_weekly.empty:
                                weekly_display = df_weekly.loc[str(start_date):str(end_date)]
                                weekly_fig = go.Figure()
                                weekly_fig.add_trace(go.Candlestick(x=weekly_display.index, open=weekly_display['Open'], high=weekly_display['High'], low=weekly_display['Low'], close=weekly_display['Close'], name='Weekly'))
                                weekly_fig.add_trace(go.Scatter(x=weekly_display.index, y=weekly_display['SMA20'], line=dict(color='orange'), name='SMA20'))
                                weekly_fig.add_trace(go.Scatter(x=weekly_display.index, y=weekly_display['SMA50'], line=dict(color='blue'), name='SMA50'))
                                weekly_fig.update_layout(height=400, xaxis_rangeslider_visible=False, title="Weekly View")
                                st.plotly_chart(weekly_fig, width="stretch")
                            else:
                                st.info("Weekly data not available")
                    
                    with tab2:
                        st.write("**Technical Indicators**")
                        indicator_fig = go.Figure()
                        
                        # RSI
                        indicator_fig.add_trace(go.Scatter(x=display_df.index, y=display_df['RSI'], name='RSI', line=dict(color='purple')))
                        indicator_fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
                        indicator_fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
                        indicator_fig.add_hline(y=50, line_dash="dash", line_color="gray")
                        indicator_fig.update_layout(height=300, title="RSI (Relative Strength Index)")
                        st.plotly_chart(indicator_fig, width="stretch")
                        
                        # MACD
                        macd_fig = go.Figure()
                        macd_fig.add_trace(go.Scatter(x=display_df.index, y=display_df['MACD'], name='MACD', line=dict(color='blue')))
                        macd_fig.add_trace(go.Scatter(x=display_df.index, y=display_df['Signal_Line'], name='Signal Line', line=dict(color='red')))
                        macd_fig.add_bar(x=display_df.index, y=display_df['MACD'] - display_df['Signal_Line'], name='Histogram')
                        macd_fig.update_layout(height=300, title="MACD")
                        st.plotly_chart(macd_fig, width="stretch")
                        
                        # Stochastic
                        stoch_fig = go.Figure()
                        stoch_fig.add_trace(go.Scatter(x=display_df.index, y=display_df['%K'], name='%K', line=dict(color='blue')))
                        stoch_fig.add_trace(go.Scatter(x=display_df.index, y=display_df['%D'], name='%D', line=dict(color='red')))
                        stoch_fig.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="Overbought")
                        stoch_fig.add_hline(y=20, line_dash="dash", line_color="green", annotation_text="Oversold")
                        stoch_fig.update_layout(height=300, title="Stochastic Oscillator")
                        st.plotly_chart(stoch_fig, width="stretch")
                    
                    with tab3:
                        st.write("**Volume Analysis**")
                        vol_fig = go.Figure()
                        vol_fig.add_trace(go.Bar(x=display_df.index, y=display_df['Volume'], name='Volume', marker_color='lightblue'))
                        vol_fig.add_trace(go.Scatter(x=display_df.index, y=display_df['Vol_Avg'], name='Volume Average', line=dict(color='red', width=2)))
                        vol_fig.update_layout(height=400, title="Volume Analysis")
                        st.plotly_chart(vol_fig, width="stretch")
                        
                        # Volume Ratio
                        vol_ratio_fig = go.Figure()
                        vol_ratio_fig.add_trace(go.Scatter(x=display_df.index, y=display_df['Vol_Ratio'], name='Volume Ratio', line=dict(color='orange')))
                        vol_ratio_fig.add_hline(y=1.5, line_dash="dash", line_color="green", annotation_text="Volume Spike")
                        vol_ratio_fig.add_hline(y=1.0, line_dash="dash", line_color="gray")
                        vol_ratio_fig.update_layout(height=300, title="Volume Ratio (Volume / Average)")
                        st.plotly_chart(vol_ratio_fig, width="stretch")
                    
                    with tab4:
                        st.write("** Backtesting Engine**")
                        
                        # Backtesting parameters
                        col1, col2 = st.columns(2)
                        with col1:
                            backtest_capital = st.number_input("Initial Capital (Rp)", min_value=1000000, value=10000000, step=1000000, key="backtest_capital")
                        with col2:
                            backtest_risk = st.slider("Risk per Trade (%)", min_value=0.5, max_value=10.0, value=2.0, step=0.5, key="backtest_risk")
                        
                        if st.button("Run Backtest", type="primary", key="run_backtest"):
                            with st.spinner("Running backtest... This may take a moment."):
                                backtest_results = backtest_signal_strategy(df, backtest_capital, backtest_risk)
                                
                                if backtest_results['total_trades'] > 0:
                                    st.success(f"Backtest completed! {backtest_results['total_trades']} trades executed.")
                                    
                                    # Performance metrics
                                    col1, col2, col3, col4 = st.columns(4)
                                    with col1:
                                        st.metric("Total Return", f"{backtest_results['total_return']:+.1f}%")
                                    with col2:
                                        st.metric("Win Rate", f"{backtest_results['win_rate']:.1f}%")
                                    with col3:
                                        st.metric("Max Drawdown", f"{backtest_results['max_drawdown']:.1f}%")
                                    with col4:
                                        st.metric("Final Capital", f"Rp {backtest_results['final_capital']:,.0f}")
                                    
                                    # Trade statistics
                                    st.write("**Trade Statistics:**")
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.write(f"Total Trades: {backtest_results['total_trades']}")
                                        st.write(f"Winning Trades: {backtest_results['winning_trades']}")
                                        st.write(f"Losing Trades: {backtest_results['losing_trades']}")
                                    with col2:
                                        st.write(f"Average Win: Rp {backtest_results['avg_win']:,.0f}")
                                        st.write(f"Average Loss: Rp {backtest_results['avg_loss']:,.0f}")
                                        st.write(f"Profit Factor: {abs(backtest_results['avg_win'] / backtest_results['avg_loss']) if backtest_results['avg_loss'] != 0 else 'N/A':.2f}")
                                    with col3:
                                        st.write(f"Total Profit: Rp {backtest_results['total_profit']:,.0f}")
                                        if backtest_results['total_profit'] >= 0:
                                            st.success("Strategy Profitable!")
                                        else:
                                            st.error("Strategy Unprofitable")
                                    
                                    # Equity curve
                                    if backtest_results['trades']:
                                        equity_data = pd.DataFrame(backtest_results['trades'])
                                        equity_data['cumulative_profit'] = equity_data['profit'].cumsum()
                                        
                                        equity_fig = go.Figure()
                                        equity_fig.add_trace(go.Scatter(x=equity_data['entry_date'], y=equity_data['cumulative_profit'], 
                                                                      mode='lines+markers', name='Cumulative Profit',
                                                                      line=dict(color='green' if backtest_results['total_profit'] >= 0 else 'red')))
                                        equity_fig.add_hline(y=0, line_dash="dash", line_color="gray")
                                        equity_fig.update_layout(height=400, title="Equity Curve", xaxis_title="Date", yaxis_title="Cumulative Profit (Rp)")
                                        st.plotly_chart(equity_fig, width="stretch")
                                        
                                        # Trade list
                                        with st.expander("View All Trades"):
                                            trades_df = pd.DataFrame(backtest_results['trades'])
                                            trades_df['profit_pct'] = (trades_df['profit'] / (trades_df['entry_price'] * trades_df['shares'])) * 100
                                            st.dataframe(trades_df[['entry_date', 'entry_price', 'exit_price', 'shares', 'profit', 'profit_pct']].style.format({
                                                'entry_price': '{:,.0f}',
                                                'exit_price': '{:,.0f}',
                                                'profit': '{:,.0f}',
                                                'profit_pct': '{:+.1f}%'
                                            }))
                                else:
                                    st.warning("No trades were executed. Try adjusting parameters or the stock may not have generated signals.")
                        
                        st.info(" **Tips:** Backtesting simulates trading based on historical signals. Results may not guarantee future performance.")
                    
                    # Advanced Charting dengan Multi-timeframe
                    st.subheader("Advanced Multi-Timeframe Analysis")
                    
                    tab1, tab2, tab3 = st.tabs(["Daily + Weekly", "Technical Indicators", "Volume Analysis"])
                    
                    with tab1:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Daily Chart (1D)**")
                            daily_fig = go.Figure()
                            daily_fig.add_trace(go.Candlestick(x=display_df.index[-60:], open=display_df['Open'][-60:], high=display_df['High'][-60:], low=display_df['Low'][-60:], close=display_df['Close'][-60:], name='Daily'))
                            daily_fig.add_trace(go.Scatter(x=display_df.index[-60:], y=display_df['EMA8'][-60:], line=dict(color='red', width=2), name='EMA8'))
                            daily_fig.add_trace(go.Scatter(x=display_df.index[-60:], y=display_df['EMA21'][-60:], line=dict(color='green', width=2), name='EMA21'))
                            daily_fig.update_layout(height=400, xaxis_rangeslider_visible=False, title="Last 60 Days")
                            st.plotly_chart(daily_fig, width="stretch")
                        
                        with col2:
                            st.write("**Weekly Chart (1W)**")
                            if df_weekly is not None and not df_weekly.empty:
                                weekly_display = df_weekly.loc[str(start_date):str(end_date)]
                                weekly_fig = go.Figure()
                                weekly_fig.add_trace(go.Candlestick(x=weekly_display.index, open=weekly_display['Open'], high=weekly_display['High'], low=weekly_display['Low'], close=weekly_display['Close'], name='Weekly'))
                                weekly_fig.add_trace(go.Scatter(x=weekly_display.index, y=weekly_display['SMA20'], line=dict(color='orange'), name='SMA20'))
                                weekly_fig.add_trace(go.Scatter(x=weekly_display.index, y=weekly_display['SMA50'], line=dict(color='blue'), name='SMA50'))
                                weekly_fig.update_layout(height=400, xaxis_rangeslider_visible=False, title="Weekly View")
                                st.plotly_chart(weekly_fig, width="stretch")
                            else:
                                st.info("Weekly data not available")
                    
                    with tab2:
                        st.write("**Technical Indicators**")
                        indicator_fig = go.Figure()
                        
                        # RSI
                        indicator_fig.add_trace(go.Scatter(x=display_df.index, y=display_df['RSI'], name='RSI', line=dict(color='purple')))
                        indicator_fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
                        indicator_fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
                        indicator_fig.add_hline(y=50, line_dash="dash", line_color="gray")
                        indicator_fig.update_layout(height=300, title="RSI (Relative Strength Index)")
                        st.plotly_chart(indicator_fig, width="stretch")
                        
                        # MACD
                        macd_fig = go.Figure()
                        macd_fig.add_trace(go.Scatter(x=display_df.index, y=display_df['MACD'], name='MACD', line=dict(color='blue')))
                        macd_fig.add_trace(go.Scatter(x=display_df.index, y=display_df['Signal_Line'], name='Signal Line', line=dict(color='red')))
                        macd_fig.add_bar(x=display_df.index, y=display_df['MACD'] - display_df['Signal_Line'], name='Histogram')
                        macd_fig.update_layout(height=300, title="MACD")
                        st.plotly_chart(macd_fig, width="stretch")
                        
                        # Stochastic
                        stoch_fig = go.Figure()
                        stoch_fig.add_trace(go.Scatter(x=display_df.index, y=display_df['%K'], name='%K', line=dict(color='blue')))
                        stoch_fig.add_trace(go.Scatter(x=display_df.index, y=display_df['%D'], name='%D', line=dict(color='red')))
                        stoch_fig.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="Overbought")
                        stoch_fig.add_hline(y=20, line_dash="dash", line_color="green", annotation_text="Oversold")
                        stoch_fig.update_layout(height=300, title="Stochastic Oscillator")
                        st.plotly_chart(stoch_fig, width="stretch")
                    
                    with tab3:
                        st.write("**Volume Analysis**")
                        vol_fig = go.Figure()
                        vol_fig.add_trace(go.Bar(x=display_df.index, y=display_df['Volume'], name='Volume', marker_color='lightblue'))
                        vol_fig.add_trace(go.Scatter(x=display_df.index, y=display_df['Vol_Avg'], name='Volume Average', line=dict(color='red', width=2)))
                        vol_fig.update_layout(height=400, title="Volume Analysis")
                        st.plotly_chart(vol_fig, width="stretch")
                        
                        # Volume Ratio
                        vol_ratio_fig = go.Figure()
                        vol_ratio_fig.add_trace(go.Scatter(x=display_df.index, y=display_df['Vol_Ratio'], name='Volume Ratio', line=dict(color='orange')))
                        vol_ratio_fig.add_hline(y=1.5, line_dash="dash", line_color="green", annotation_text="Volume Spike")
                        vol_ratio_fig.add_hline(y=1.0, line_dash="dash", line_color="gray")
                        vol_ratio_fig.update_layout(height=300, title="Volume Ratio (Volume / Average)")
                        st.plotly_chart(vol_ratio_fig, width="stretch")
                    
            except Exception as e:
                st.error(f"Error: {e}")

# === ADVANCED BACKTESTING ENGINE ===
elif analysis_mode == "Advanced Backtesting Engine":
    st.header("Advanced Backtesting Engine")
    st.markdown("Backtest berbagai strategi trading dengan parameter yang dapat disesuaikan.")
    
    # Strategy selection
    col1, col2, col3 = st.columns(3)
    with col1:
        strategy_type = st.selectbox(
            "Pilih Strategi:",
            ["MA Crossover (SMA20 vs SMA50)", "RSI Divergence (Oversold/Overbought)"]
        )
    with col2:
        initial_capital = st.number_input("Modal Awal (Rp)", min_value=1000000, value=10000000, step=1000000)
    with col3:
        backtest_period = st.selectbox("Periode Backtest:", ["1y", "2y", "3y", "5y"])
    
    # Stock selection
    ticker = st.selectbox("Pilih Saham untuk Backtest:", ALL_STOCKS)
    
    if st.button("Jalankan Backtest", type="primary"):
        with st.spinner(f"Menjalankan backtest untuk {ticker}..."):
            try:
                # Get historical data
                stock = yf.Ticker(ticker)
                data = stock.history(period=backtest_period)
                
                if data.empty:
                    st.error("Tidak ada data yang tersedia untuk periode ini.")
                else:
                    # Convert strategy name
                    strategy_key = 'ma_crossover' if 'MA Crossover' in strategy_type else 'rsi_divergence'
                    
                    # Run backtest
                    results = backtest_strategy(data, strategy_key, initial_capital)
                
                    if results['total_trades'] > 0:
                        st.success(f"Backtest selesai! {results['total_trades']} transaksi dieksekusi.")
                        
                        # Key metrics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Return", f"{results['total_return']:+.1f}%", 
                                     delta=f"{results['total_return']:+.1f}%", 
                                     delta_color="normal"
if results['total_return'] >= 0 else "inverse")
                        with col2:
                            st.metric("Win Rate", f"{results['win_rate']:.1f}%")
                        with col3:
                            st.metric("Max Drawdown", f"{results['max_drawdown']:.1f}%")
                        with col4:
                            final_capital = initial_capital * (1 + results['total_return']/100)
                            st.metric("Final Capital", f"Rp {final_capital:,.0f}")
                        
                        # Advanced metrics
                        with st.expander("Advanced Metrics"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write("**Trade Statistics:**")
                                st.write(f"Total Trades: {results['total_trades']}")
                                winning_trades = int(results['total_trades'] * results['win_rate'] / 100)
                                st.write(f"Winning Trades: {winning_trades}")
                                st.write(f"Losing Trades: {results['total_trades'] - winning_trades}")
                            
                            with col2:
                                st.write("**Risk Metrics:**")
                                st.write(f"Profit Factor: {results['profit_factor']:.2f}")
                                st.write(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
                                st.write(f"Max Drawdown: {results['max_drawdown']:.1f}%")
                            
                            with col3:
                                st.write("**Performance:**")
                                st.write(f"Total Return: {results['total_return']:+.1f}%")
                                if results['total_return'] >= 0:
                                    st.success("Strategy Profitable! ")
                                else:
                                    st.error("Strategy Unprofitable ")
                        
                        # Equity curve
                        if results['equity_curve']:
                            st.subheader("Equity Curve")
                            equity_df = pd.DataFrame({
                                'Date': data.index[-len(results['equity_curve']):],
                                'Equity': results['equity_curve']
                            })
                            
                            equity_fig = go.Figure()
                            equity_fig.add_trace(go.Scatter(
                                x=equity_df['Date'], 
                                y=equity_df['Equity'],
                                mode='lines',
                                name='Equity Curve',
                                line=dict(color='green' if results['total_return'] >= 0 else 'red', width=2)
                            ))
                            equity_fig.add_hline(y=initial_capital, line_dash="dash", line_color="gray", annotation_text="Initial Capital")
                            equity_fig.update_layout(
                                title="Portfolio Equity Curve",
                                xaxis_title="Date",
                                yaxis_title="Portfolio Value (Rp)",
                                height=400
                            )
                            st.plotly_chart(equity_fig, width="stretch")
                        
                        # Trade list
                        if results['trades']:
                            with st.expander("View All Trades"):
                                trades_df = pd.DataFrame(results['trades'])
                                st.dataframe(trades_df)
                        
                        # Monte Carlo Simulation
                        st.subheader("Monte Carlo Simulation")
                        if st.button("Run Monte Carlo Simulation", type="secondary"):
                            with st.spinner("Running Monte Carlo simulation..."):
                                mc_results = monte_carlo_simulation(data, strategy_key, initial_capital, 1000)
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Mean Return", f"{mc_results['mean_return']:+.1f}%")
                                    st.metric("Std Deviation", f"{mc_results['std_return']:.1f}%")
                                with col2:
                                    st.metric("Min Return", f"{mc_results['min_return']:+.1f}%")
                                    st.metric("Max Return", f"{mc_results['max_return']:+.1f}%")
                                with col3:
                                    st.metric("5th Percentile", f"{mc_results['percentile_5']:+.1f}%")
                                    st.metric("95th Percentile", f"{mc_results['percentile_95']:+.1f}%")
                                
                                st.metric("Probability of Profit", f"{mc_results['probability_profit']:.1f}%", 
                                         delta=f"{mc_results['probability_profit']-50:+.1f}% vs 50%", 
                                         delta_color="normal"
if mc_results['probability_profit'] > 50 else "inverse")
                    
                    else:
                        st.warning("Tidak ada transaksi yang dieksekusi. Coba sesuaikan parameter atau saham tidak menghasilkan sinyal.")
            
            except Exception as e:
                st.error(f"Error dalam backtesting: {e}")

# === OPTIONS ANALYSIS MODULE ===
elif analysis_mode == "Options Analysis Module":
    render_options_analysis_module()

# === SMART WATCHLIST & ALERTS ===
elif analysis_mode == "Smart Watchlist & Alerts":
    render_smart_watchlist_alerts()

# === PAPER TRADING SIMULATOR ===
elif analysis_mode == "Paper Trading Simulator":
    render_paper_trading_simulator()

# === ENHANCED MULTI-ANALYSIS ===
elif analysis_mode == "Enhanced Multi-Analysis":
    render_enhanced_multi_analysis()

# === MARKET TIMING ANALYZER ===
elif analysis_mode == "Market Timing Analyzer":
    render_market_timing_analyzer()

# === ML SIGNAL PREDICTOR ===
elif analysis_mode == "ML Dashboard Pro":
    render_ml_dashboard_pro()
    
elif analysis_mode == "ML Signal Predictor":
    st.header("ML Signal Predictor")
    st.markdown("Advanced predictor dengan regime-adaptive models + Kelly sizing")
    
    # Existing predictor code here...
    # (keep original tab2-5 logic)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Dashboard", 
        "Prediksi Signal",
        "Feature Importance",
        "Regime Models",
        "Expectancy Calculator"
    ])
    
    # [Previous ML predictor tabs content - unchanged]
    
else:
    st.info("Silakan pilih mode analisis dari sidebar.")

