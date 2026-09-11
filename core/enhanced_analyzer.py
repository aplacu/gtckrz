"""
Enhanced Stock Analyzer Module + ML Pipeline
Modul lengkap: Backtesting, Options, Alerts, ML Signal Prediction, Regime Detection
"""

import yfinance as yf
import pandas as pd
import numpy as np
import math
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from sklearn.ensemble import RandomForestClassifier
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core.shared_analysis import (
    calculate_rsi as shared_calculate_rsi,
    backtest_strategy as shared_backtest_strategy,
    monte_carlo_simulation as shared_monte_carlo_simulation,
    detect_price_patterns as shared_detect_price_patterns,
    check_volume_spike as shared_check_volume_spike,
)

# ML Dataset Path
DATASET_PATH = "signal_history.csv"
EXCEL_DATASET_PATH = "signal_history.xlsx"
SIGNAL_DATASET_COLUMNS = [
    "timestamp",
    "symbol",
    "entry",
    "sl",
    "tp",
    "rsi",
    "volume_ratio",
    "atr_pct",
    "ma_slope",
    "regime",
    "strategy_name",
    "outcome",
]

def calculate_rsi(data, period=14):
    """Compatibility wrapper to shared RSI."""
    return shared_calculate_rsi(data, period=period)


# === ADVANCED BACKTESTING ENGINE ===
def backtest_strategy(data, strategy_type='ma_crossover', initial_capital=10000000, **cost_params):
    """Shared advanced backtesting engine wrapper."""
    return shared_backtest_strategy(data, strategy_type, initial_capital, **cost_params)

def monte_carlo_simulation(data, strategy_type='ma_crossover', initial_capital=10000000, simulations=1000):
    """Shared Monte Carlo wrapper."""
    return shared_monte_carlo_simulation(data, strategy_type, initial_capital, simulations)

# === OPTIONS ANALYSIS MODULE ===
def calculate_greeks(current_price, strike_price, time_to_expiry, risk_free_rate, volatility, option_type='call'):
    """
    Calculate option Greeks (Delta, Gamma, Theta, Vega)
    Simplified Black-Scholes implementation
    """
    try:
        # Convert time to expiry to years
        T = time_to_expiry / 365.0
        
        # Calculate d1 and d2
        d1 = (math.log(current_price / strike_price) + (risk_free_rate + 0.5 * volatility ** 2) * T) / (volatility * math.sqrt(T))
        d2 = d1 - volatility * math.sqrt(T)
        
        # Standard normal cumulative distribution function
        def norm_cdf(x):
            return 0.5 * (1 + math.erf(x / math.sqrt(2)))
        
        # Standard normal probability density function
        def norm_pdf(x):
            return math.exp(-0.5 * x ** 2) / math.sqrt(2 * math.pi)
        
        if option_type == 'call':
            delta = norm_cdf(d1)
            theta = -(current_price * norm_pdf(d1) * volatility) / (2 * math.sqrt(T)) - risk_free_rate * strike_price * math.exp(-risk_free_rate * T) * norm_cdf(d2)
        else:  # put
            delta = norm_cdf(d1) - 1
            theta = -(current_price * norm_pdf(d1) * volatility) / (2 * math.sqrt(T)) + risk_free_rate * strike_price * math.exp(-risk_free_rate * T) * norm_cdf(-d2)
        
        gamma = norm_pdf(d1) / (current_price * volatility * math.sqrt(T))
        vega = current_price * norm_pdf(d1) * math.sqrt(T) / 100  # Per 1% change in volatility
        
        return {
            'delta': delta,
            'gamma': gamma,
            'theta': theta / 365,  # Daily theta
            'vega': vega
        }
    except Exception as e:
        return {
            'delta': 0,
            'gamma': 0,
            'theta': 0,
            'vega': 0,
            'error': str(e)
        }

def get_implied_volatility(ticker, option_type='call'):
    """
    Estimate implied volatility from historical volatility
    Simplified calculation
    """
    try:
        # Get historical data
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        
        # Calculate historical volatility (annualized)
        returns = hist['Close'].pct_change().dropna()
        historical_vol = returns.std() * math.sqrt(252)  # 252 trading days
        
        # Add volatility premium based on market conditions
        current_price = hist['Close'].iloc[-1]
        sma_20 = hist['Close'].rolling(20).mean().iloc[-1]
        
        # Adjust volatility based on trend
        if current_price > sma_20:
            implied_vol = historical_vol * 0.9  # Lower vol in uptrend
        else:
            implied_vol = historical_vol * 1.1  # Higher vol in downtrend
        
        return min(max(implied_vol, 0.1), 1.0)  # Clamp between 10% and 100%
        
    except Exception:
        return 0.3  # Default 30% volatility

def analyze_option_chain(ticker, current_price):
    """
    Analyze option chain for a ticker
    """
    try:
        # Generate sample option chain (simplified)
        # In real implementation, this would fetch from options data provider
        
        risk_free_rate = 0.06  # 6% risk-free rate
        time_to_expiry = 30   # 30 days to expiry
        
        strikes = [current_price * 0.9, current_price * 0.95, current_price, current_price * 1.05, current_price * 1.1]
        
        option_chain = []
        
        for strike in strikes:
            implied_vol = get_implied_volatility(ticker)
            
            # Calculate call option
            call_greeks = calculate_greeks(current_price, strike, time_to_expiry, risk_free_rate, implied_vol, 'call')
            
            # Calculate put option
            put_greeks = calculate_greeks(current_price, strike, time_to_expiry, risk_free_rate, implied_vol, 'put')
            
            # Estimate option prices (simplified)
            call_price = max(current_price - strike, 0) + (implied_vol * current_price * 0.1)
            put_price = max(strike - current_price, 0) + (implied_vol * current_price * 0.1)
            
            option_chain.append({
                'strike': strike,
                'call_price': call_price,
                'put_price': put_price,
                'call_greeks': call_greeks,
                'put_greeks': put_greeks,
                'implied_volatility': implied_vol
            })
        
        return {
            'current_price': current_price,
            'option_chain': option_chain,
            'max_pain': current_price,  # Simplified max pain
            'put_call_ratio': 0.8,  # Simplified put/call ratio
            'data_status': 'SIMULATED',
            'data_source': 'Black-Scholes estimate from historical volatility',
            'as_of': datetime.now().isoformat(timespec='seconds'),
        }
        
    except Exception as e:
        return {
            'current_price': current_price,
            'option_chain': [],
            'error': str(e),
            'data_status': 'UNAVAILABLE',
        }

# === SMART WATCHLIST & ALERTS ===
def detect_price_patterns(data, pattern_type='breakout'):
    """Shared price-pattern detection wrapper."""
    return shared_detect_price_patterns(data, pattern_type)

def check_volume_spike(data, threshold=2.0):
    """Shared volume-spike wrapper."""
    return shared_check_volume_spike(data, threshold)

def create_smart_alert(ticker, alert_type, threshold, condition='above'):
    """
    Create smart alert with multiple conditions
    """
    alert_type_map = {
        "price_alert": "price",
        "volume_spike": "volume",
        "rsi_alert": "rsi",
        "price": "price",
        "volume": "volume",
        "rsi": "rsi",
    }
    normalized_type = alert_type_map.get(str(alert_type).lower(), str(alert_type).lower())
    return {
        'ticker': ticker,
        'type': normalized_type,
        'threshold': threshold,
        'condition': condition,
        'created_at': datetime.now(),
        'active': True,
        'triggered': False
    }

def check_alert_conditions(ticker, data, alert, calculate_rsi_func=None):
    """
    Check if alert conditions are met
    """
    try:
        current_price = data['Close'].iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        
        alert_type = str(alert.get('type', '')).lower()
        if alert_type in ('price_alert',):
            alert_type = 'price'
        elif alert_type in ('volume_spike',):
            alert_type = 'volume'
        elif alert_type in ('rsi_alert',):
            alert_type = 'rsi'

        if alert_type == 'price':
            if alert['condition'] == 'above' and current_price > alert['threshold']:
                return {
                    'triggered': True,
                    'current_value': current_price,
                    'message': f"{ticker} naik di atas Rp {alert['threshold']:,.0f}"
                }
            elif alert['condition'] == 'below' and current_price < alert['threshold']:
                return {
                    'triggered': True,
                    'current_value': current_price,
                    'message': f"{ticker} turun di bawah Rp {alert['threshold']:,.0f}"
                }
        
        elif alert_type == 'volume':
            avg_volume = data['Volume'].rolling(20).mean().iloc[-1]
            if current_volume > alert['threshold'] * avg_volume:
                return {
                    'triggered': True,
                    'current_value': current_volume,
                    'message': f"{ticker} volume spike {current_volume/avg_volume:.1f}x rata-rata"
                }
        
        elif alert_type == 'rsi' and calculate_rsi_func:
            rsi = calculate_rsi_func(data).iloc[-1]
            if alert['condition'] == 'above' and rsi > alert['threshold']:
                return {
                    'triggered': True,
                    'current_value': rsi,
                    'message': f"{ticker} RSI di atas {alert['threshold']} (sekarang: {rsi:.1f})"
                }
            elif alert['condition'] == 'below' and rsi < alert['threshold']:
                return {
                    'triggered': True,
                    'current_value': rsi,
                    'message': f"{ticker} RSI di bawah {alert['threshold']} (sekarang: {rsi:.1f})"
                }
        
        return {'triggered': False}
        
    except Exception:
        return {'triggered': False}

# === FUNDAMENTAL ANALYSIS MODULE ===
def get_fundamental_ratios(ticker):
    """
    Get fundamental ratios (simplified)
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        return {
            'pe_ratio': info.get('trailingPE', 0),
            'pb_ratio': info.get('priceToBook', 0),
            'roe': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0,
            'debt_to_equity': info.get('debtToEquity', 0),
            'current_ratio': info.get('currentRatio', 0),
            'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
            'market_cap': info.get('marketCap', 0),
            'enterprise_value': info.get('enterpriseValue', 0),
            'price_to_sales': info.get('priceToSalesTrailing12Months', 0)
        }
    except Exception:
        return {
            'pe_ratio': 0, 'pb_ratio': 0, 'roe': 0, 'debt_to_equity': 0,
            'current_ratio': 0, 'dividend_yield': 0, 'market_cap': 0,
            'enterprise_value': 0, 'price_to_sales': 0
        }

def calculate_dcf_value(ticker, growth_rate=0.05, discount_rate=0.10):
    """
    Simplified DCF calculator
    """
    try:
        stock = yf.Ticker(ticker)
        financials = stock.financials
        
        if financials.empty:
            return {'fair_value': 0, 'current_price': 0, 'upside': 0, 'data_status': 'UNAVAILABLE'}
        
        # Get latest free cash flow (simplified)
        fcf = financials.loc['Total Cash From Operating Activities'].iloc[0] if 'Total Cash From Operating Activities' in financials.index else 0
        
        # Project cash flows for 5 years
        projected_fcf = []
        for year in range(1, 6):
            projected_fcf.append(fcf * (1 + growth_rate) ** year)
        
        # Calculate terminal value
        terminal_fcf = projected_fcf[-1] * (1 + 0.03)  # 3% perpetual growth
        terminal_value = terminal_fcf / (discount_rate - 0.03)
        
        # Discount all cash flows
        total_pv = 0
        for i, cash_flow in enumerate(projected_fcf):
            total_pv += cash_flow / (1 + discount_rate) ** (i + 1)
        
        total_pv += terminal_value / (1 + discount_rate) ** 5
        
        # Get shares outstanding
        shares = stock.info.get('sharesOutstanding', 1)
        fair_value = total_pv / shares if shares > 0 else 0
        
        current_price = stock.history(period="1d")['Close'].iloc[-1]
        upside = ((fair_value - current_price) / current_price * 100) if current_price > 0 else 0
        
        return {
            'fair_value': fair_value,
            'current_price': current_price,
            'upside': upside,
            'assumptions': {
                'growth_rate': growth_rate,
                'discount_rate': discount_rate
            },
            'data_status': 'SIMPLIFIED_ESTIMATE',
            'data_source': 'Yahoo Finance financial statements',
            'as_of': datetime.now().isoformat(timespec='seconds'),
        }
        
    except Exception:
        return {'fair_value': 0, 'current_price': 0, 'upside': 0, 'assumptions': {}, 'data_status': 'UNAVAILABLE'}

# === PAPER TRADING SIMULATOR ===
class PaperTradingSimulator:
    def __init__(self, initial_balance=100000000):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions = {}
        self.trade_history = []
        self.start_date = datetime.now()
        
    def buy_stock(self, ticker, shares, price):
        """Buy stock in paper trading"""
        total_cost = shares * price
        
        if total_cost <= self.balance:
            self.balance -= total_cost
            
            if ticker in self.positions:
                # Update existing position
                old_shares = self.positions[ticker]['shares']
                old_price = self.positions[ticker]['avg_price']
                total_shares = old_shares + shares
                
                self.positions[ticker] = {
                    'shares': total_shares,
                    'avg_price': (old_shares * old_price + shares * price) / total_shares,
                    'total_investment': old_shares * old_price + total_cost
                }
            else:
                # New position
                self.positions[ticker] = {
                    'shares': shares,
                    'avg_price': price,
                    'total_investment': total_cost
                }
            
            # Record trade
            self.trade_history.append({
                'type': 'BUY',
                'ticker': ticker,
                'shares': shares,
                'price': price,
                'total': total_cost,
                'date': datetime.now(),
                'balance': self.balance
            })
            
            return True, f"Bought {shares} shares of {ticker} at Rp {price:,.0f}"
        else:
            return False, "Insufficient balance"
    
    def sell_stock(self, ticker, shares, price):
        """Sell stock in paper trading"""
        if ticker in self.positions and self.positions[ticker]['shares'] >= shares:
            total_value = shares * price
            avg_price = self.positions[ticker]['avg_price']
            profit = (price - avg_price) * shares
            
            # Update position
            self.positions[ticker]['shares'] -= shares
            self.positions[ticker]['total_investment'] -= shares * avg_price
            
            if self.positions[ticker]['shares'] == 0:
                del self.positions[ticker]
            
            self.balance += total_value
            
            # Record trade
            self.trade_history.append({
                'type': 'SELL',
                'ticker': ticker,
                'shares': shares,
                'price': price,
                'total': total_value,
                'profit': profit,
                'date': datetime.now(),
                'balance': self.balance
            })
            
            return True, f"Sold {shares} shares of {ticker} at Rp {price:,.0f} (Profit: Rp {profit:,.0f})"
        else:
            return False, "Position not found or insufficient shares"
    
    def get_portfolio_value(self, current_prices):
        """Get current portfolio value"""
        stock_value = 0
        
        for ticker, position in self.positions.items():
            if ticker in current_prices:
                stock_value += position['shares'] * current_prices[ticker]
        
        total_value = self.balance + stock_value
        
        return {
            'balance': self.balance,
            'stock_value': stock_value,
            'total_value': total_value,
            'total_return': ((total_value - self.initial_balance) / self.initial_balance) * 100
        }
    
    def get_performance_metrics(self):
        """Calculate performance metrics"""
        if not self.trade_history:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_profit': 0,
                'avg_profit_per_trade': 0
            }
        
        sell_trades = [t for t in self.trade_history if t['type'] == 'SELL']
        winning_trades = [t for t in sell_trades if t.get('profit', 0) > 0]
        
        total_profit = sum([t.get('profit', 0) for t in sell_trades])
        
        return {
            'total_trades': len(self.trade_history),
            'win_rate': len(winning_trades) / len(sell_trades) * 100 if sell_trades else 0,
            'total_profit': total_profit,
            'avg_profit_per_trade': total_profit / len(sell_trades) if sell_trades else 0
        }

# === MARKET MICROSTRUCTURE ANALYSIS ===
def analyze_bid_ask_spread(ticker):
    """
    Analyze bid-ask spread (simplified simulation)
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        
        current_price = hist['Close'].iloc[-1]
        avg_volume = hist['Volume'].mean()
        
        # Simulate bid-ask spread based on liquidity
        if avg_volume > 1000000:  # High liquidity
            spread_pct = 0.01  # 0.01%
        elif avg_volume > 100000:  # Medium liquidity
            spread_pct = 0.05  # 0.05%
        else:  # Low liquidity
            spread_pct = 0.1   # 0.1%
        
        bid_price = current_price * (1 - spread_pct/200)  # Half spread
        ask_price = current_price * (1 + spread_pct/200)  # Half spread
        
        return {
            'bid_price': bid_price,
            'ask_price': ask_price,
            'spread_pct': spread_pct,
            'spread_value': ask_price - bid_price,
            'liquidity': 'HIGH' if spread_pct < 0.03 else 'MEDIUM' if spread_pct < 0.08 else 'LOW'
        }
        
    except Exception:
        return {
            'bid_price': 0, 'ask_price': 0, 'spread_pct': 0,
            'spread_value': 0, 'liquidity': 'UNKNOWN'
        }

def calculate_vwap(data):
    """
    Calculate Volume Weighted Average Price (VWAP)
    """
    try:
        # Typical price = (High + Low + Close) / 3
        typical_price = (data['High'] + data['Low'] + data['Close']) / 3
        
        # VWAP = Cumulative(Typical Price * Volume) / Cumulative(Volume)
        cumulative_typical_volume = (typical_price * data['Volume']).cumsum()
        cumulative_volume = data['Volume'].cumsum()
        
        vwap = cumulative_typical_volume / cumulative_volume
        
        return vwap
        
    except Exception:
        return data['Close']  # Fallback to closing price

# === ML SIGNAL LOGGING & TRAINING ===
def _coerce_signal_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize dataset schema/types to keep history clean for ML."""
    out = df.copy()
    for col in SIGNAL_DATASET_COLUMNS:
        if col not in out.columns:
            out[col] = np.nan
    out = out[SIGNAL_DATASET_COLUMNS]
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
    numeric_cols = ["entry", "sl", "tp", "rsi", "volume_ratio", "atr_pct", "ma_slope", "regime", "outcome"]
    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["symbol"] = out["symbol"].astype(str).str.upper().str.strip()
    out["strategy_name"] = out["strategy_name"].fillna("Unknown").astype(str).str.strip()
    return out


def validate_signal_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """Run lightweight quality checks and return cleaned frame + diagnostics."""
    cleaned = _coerce_signal_dataset(df)
    issues = []

    if cleaned["timestamp"].isna().any():
        issues.append("invalid_timestamp")

    invalid_outcomes = cleaned["outcome"].dropna()
    if not invalid_outcomes.isin([0, 1]).all():
        issues.append("invalid_outcome_values")
        cleaned.loc[~cleaned["outcome"].isin([0, 1]), "outcome"] = np.nan

    invalid_prices = (cleaned["entry"] <= 0) | (cleaned["sl"] <= 0) | (cleaned["tp"] <= 0)
    if invalid_prices.fillna(False).any():
        issues.append("non_positive_prices")
        cleaned = cleaned[~invalid_prices.fillna(False)]

    duplicate_key = ["timestamp", "symbol", "strategy_name"]
    dup_count = int(cleaned.duplicated(subset=duplicate_key).sum())
    if dup_count > 0:
        issues.append("duplicate_signal_keys")
        cleaned = cleaned.drop_duplicates(subset=duplicate_key, keep="last")

    return {"valid": len(issues) == 0, "issues": issues, "duplicate_rows": dup_count, "cleaned_df": cleaned}


def _load_signal_dataset() -> pd.DataFrame:
    if os.path.exists(DATASET_PATH):
        df = pd.read_csv(DATASET_PATH)
        return validate_signal_dataset(df)["cleaned_df"]
    if os.path.exists(EXCEL_DATASET_PATH):
        df = pd.read_excel(EXCEL_DATASET_PATH)
        cleaned = validate_signal_dataset(df)["cleaned_df"]
        cleaned.to_csv(DATASET_PATH, index=False)
        return cleaned
    return pd.DataFrame(columns=SIGNAL_DATASET_COLUMNS)


def load_signal_dataset() -> pd.DataFrame:
    """Public loader for signal history (CSV master with Excel fallback)."""
    return _load_signal_dataset()


def _save_signal_dataset(df: pd.DataFrame, auto_export_excel: bool = True) -> None:
    cleaned = validate_signal_dataset(df)["cleaned_df"]
    cleaned.to_csv(DATASET_PATH, index=False)
    if auto_export_excel:
        export_dataset_to_excel(cleaned)


def export_dataset_to_excel(df: Optional[pd.DataFrame] = None) -> bool:
    """Hybrid mode: keep CSV for ML pipeline, keep Excel snapshot for manual review."""
    try:
        if df is None:
            df = _load_signal_dataset()
        df_to_export = _coerce_signal_dataset(df)
        df_to_export.to_excel(EXCEL_DATASET_PATH, index=False)
        return True
    except Exception:
        return False


def log_signal(symbol, entry, sl, tp, features, strategy_name="Enhanced_Signal"):
    """Log signal into CSV master and keep an Excel mirror snapshot."""
    try:
        row = pd.DataFrame(
            [
                {
                    "timestamp": datetime.now(),
                    "symbol": str(symbol).upper().strip(),
                    "entry": entry,
                    "sl": sl,
                    "tp": tp,
                    "rsi": features.get("rsi", 50),
                    "volume_ratio": features.get("volume_ratio", 1.0),
                    "atr_pct": features.get("atr_pct", 0.02),
                    "ma_slope": features.get("ma_slope", 0.0),
                    "regime": features.get("regime", 0),
                    "strategy_name": strategy_name,
                    "outcome": np.nan,
                }
            ]
        )
        dataset = _load_signal_dataset()
        dataset = pd.concat([dataset, row], ignore_index=True)
        _save_signal_dataset(dataset, auto_export_excel=True)
        return True
    except Exception as e:
        print(f"Error logging signal: {e}")
        return False

def detect_regime(df):
    """
    Deteksi regime pasar: 1=Trending, 2=Volatile, 0=Sideways
    """
    try:
        if df.empty or len(df) < 200:
            return 0
        
        # Trend: SMA50 vs SMA200
        sma_50 = df['Close'].rolling(50).mean().iloc[-1]
        sma_200 = df['Close'].rolling(200).mean().iloc[-1]
        
        if pd.notna(sma_50) and pd.notna(sma_200):
            if sma_50 > sma_200 * 1.01:
                return 1  # Trending up
            elif sma_50 < sma_200 * 0.99:
                return -1  # Trending down
        
        # Volatility check
        if 'ATR' in df.columns:
            current_atr = df['ATR'].iloc[-1]
            avg_atr = df['ATR'].rolling(20).mean().iloc[-1]
            if pd.notna(current_atr) and pd.notna(avg_atr) and current_atr > avg_atr * 1.3:
                return 2  # Volatile
        
        return 0  # Sideways
    except Exception:
        return 0

def _evaluate_outcome_from_price_row(row: pd.Series, price_data: pd.DataFrame, max_holding_days: int = 7) -> Optional[int]:
    signal_time = pd.to_datetime(row["timestamp"])
    if pd.isna(signal_time):
        return None

    future = price_data[price_data.index > signal_time]
    if future.empty:
        return None

    cutoff = signal_time + timedelta(days=max_holding_days)
    window = future[future.index <= cutoff]
    if window.empty:
        return None

    hit_tp = window["High"] >= float(row["tp"])
    hit_sl = window["Low"] <= float(row["sl"])
    tp_hits = window[hit_tp]
    sl_hits = window[hit_sl]

    if not tp_hits.empty and not sl_hits.empty:
        return 0 if sl_hits.index[0] <= tp_hits.index[0] else 1
    if not tp_hits.empty:
        return 1
    if not sl_hits.empty:
        return 0
    return None


def evaluate_outcomes(price_data_by_symbol: Optional[Dict[str, pd.DataFrame]] = None, max_holding_days: int = 7):
    """Evaluate pending outcomes using market candles; exports refreshed Excel snapshot."""
    try:
        df = _load_signal_dataset()
        if df.empty:
            return "No dataset"

        pending_idx = df[df["outcome"].isna()].index
        if len(pending_idx) == 0:
            export_dataset_to_excel(df)
            return f"All {len(df)} signals evaluated"

        cache: Dict[str, pd.DataFrame] = {}
        evaluated = 0
        for idx in pending_idx:
            row = df.loc[idx]
            symbol = str(row["symbol"]).upper().strip()
            if not symbol or symbol == "NAN":
                continue

            symbol_data = None
            if price_data_by_symbol and symbol in price_data_by_symbol:
                symbol_data = price_data_by_symbol[symbol]
            else:
                if symbol not in cache:
                    try:
                        cache[symbol] = yf.Ticker(symbol).history(period="6mo")
                    except Exception:
                        cache[symbol] = pd.DataFrame()
                symbol_data = cache[symbol]

            if symbol_data is None or symbol_data.empty:
                continue

            outcome = _evaluate_outcome_from_price_row(row, symbol_data, max_holding_days=max_holding_days)
            if outcome in (0, 1):
                df.at[idx, "outcome"] = outcome
                evaluated += 1

        _save_signal_dataset(df, auto_export_excel=True)
        return f"Evaluated {evaluated} pending signals. Total rows: {len(df)}"
    except Exception as e:
        return f"Error: {str(e)}"


def _chronological_split(X, y, test_size=0.2):
    """Split ordered observations without allowing future rows into training."""
    split_index = max(1, int(len(X) * (1 - test_size)))
    return X.iloc[:split_index], X.iloc[split_index:], y.iloc[:split_index], y.iloc[split_index:]


def _positive_probability(model, feature_frame):
    """Return probability for outcome=1, including single-class models."""
    probabilities = model.predict_proba(feature_frame)[0]
    classes = list(model.classes_)
    if 1 not in classes:
        return 0.0
    return float(probabilities[classes.index(1)])


def train_model():
    """
    Train ML model + return accuracy + feature importance
    """
    try:
        df = _load_signal_dataset()
        df = df.dropna(subset=["outcome"])
        
        if len(df) < 30:
            return None, 0, f"Need 30+ evaluated signals. Have {len(df)}"
        
        features = ["rsi", "volume_ratio", "atr_pct", "ma_slope", "regime"]
        X = df[features]
        y = df["outcome"]

        X_train, X_test, y_train, y_test = _chronological_split(X, y)
        if X_test.empty or y_train.nunique() < 2:
            return None, 0, "Need both outcome classes and a non-empty chronological test set"

        model = RandomForestClassifier(
            n_estimators=300,
            max_depth=6,
            min_samples_split=10,
            random_state=42
        )

        model.fit(X_train, y_train)
        accuracy = model.score(X_test, y_test)

        importance_df = pd.DataFrame({
            "feature": features,
            "importance": model.feature_importances_
        }).sort_values("importance", ascending=False)

        return model, accuracy, importance_df
        
    except Exception as e:
        return None, 0, str(e)

def train_regime_models():
    """
    Train separate models per market regime
    """
    try:
        df = _load_signal_dataset()
        df = df.dropna(subset=["outcome"])
        
        features = ["rsi", "volume_ratio", "atr_pct", "ma_slope"]
        models = {}
        accuracies = {}

        for regime in df["regime"].dropna().unique():
            regime_int = int(regime)
            df_reg = df[df["regime"] == regime_int]

            if len(df_reg) < 20:
                continue

            X = df_reg[features]
            y = df_reg["outcome"]

            X_train, X_test, y_train, y_test = _chronological_split(X, y)
            if X_test.empty or y_train.nunique() < 2:
                continue

            model = RandomForestClassifier(n_estimators=200, max_depth=5, random_state=42)
            model.fit(X_train, y_train)
            acc = model.score(X_test, y_test)

            models[regime_int] = model
            accuracies[regime_int] = acc

        return models, accuracies
        
    except Exception as e:
        return {}, {"error": str(e)}

def calculate_expectancy():
    """
    Hitung expectancy dari historical signals
    """
    try:
        df = _load_signal_dataset()
        df_eval = df.dropna(subset=["outcome"])
        
        if len(df_eval) < 10:
            return 0, 0, 0, 0
        
        wins = df_eval[df_eval["outcome"] == 1]
        losses = df_eval[df_eval["outcome"] == 0]

        win_rate = len(wins) / len(df_eval)
        avg_win = (wins["tp"] - wins["entry"]).mean()
        avg_loss = (losses["entry"] - losses["sl"]).mean()

        expectancy = (win_rate * avg_win) - ((1-win_rate) * avg_loss)

        return win_rate, avg_win, avg_loss, expectancy
        
    except Exception:
        return 0, 0, 0, 0

def predict_signal_confidence(features, regime=None):
    """
    Prediksi confidence untuk signal baru
    """
    model, accuracy, _ = train_model()
    if model is None:
        return {"confidence": 0.5, "accuracy": 0, "status": "no_model"}

    feature_payload = {
        "rsi": features.get("rsi", 50),
        "volume_ratio": features.get("volume_ratio", 1.0),
        "atr_pct": features.get("atr_pct", 0.02),
        "ma_slope": features.get("ma_slope", 0.0),
        "regime": features.get("regime", 0),
    }
    feature_df = pd.DataFrame([feature_payload])
    prob = _positive_probability(model, feature_df)

    if regime is not None:
        regime_models, regime_accuracies = train_regime_models()
        regime_model = regime_models.get(int(regime))
        if regime_model is not None:
            feature_regime_df = feature_df[["rsi", "volume_ratio", "atr_pct", "ma_slope"]]
            prob = _positive_probability(regime_model, feature_regime_df)
            accuracy = float(regime_accuracies.get(int(regime), accuracy))

    return {
        "confidence": prob,
        "accuracy": accuracy,
        "model_available": True,
        "message": f"{prob*100:.1f}% confidence (Model acc: {accuracy*100:.1f}%)",
    }

def position_size_kelly(confidence, rr_ratio, capital):
    """
    Kelly Criterion position sizing (conservative)
    """
    edge = confidence * rr_ratio - (1 - confidence)
    if edge <= 0:
        return 0
    
    kelly_fraction = edge / rr_ratio
    safe_fraction = min(kelly_fraction * 0.25, 0.10)  # Max 10%
    
    return capital * safe_fraction


def best_strategy_per_regime():
    """Return best strategy by average outcome per regime."""
    try:
        df = _load_signal_dataset()
        df_eval = df.dropna(subset=["outcome"])
        if len(df_eval) < 20:
            return {}

        out = {}
        for regime in sorted(df_eval["regime"].dropna().unique()):
            reg = df_eval[df_eval["regime"] == regime]
            if len(reg) < 5:
                continue
            grouped = reg.groupby("strategy_name")["outcome"].mean()
            if not grouped.empty:
                out[int(regime)] = str(grouped.idxmax())
        return out
    except Exception:
        return {}

# === UTILITY FUNCTIONS ===
def create_advanced_chart(data, ticker, indicators=None):

    """
    Create advanced multi-panel chart
    """
    try:
        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            subplot_titles=('Price & Volume', 'RSI', 'MACD', 'Volume Profile'),
            row_heights=[0.4, 0.2, 0.2, 0.2]
        )
        
        # Price chart
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='Price'
        ), row=1, col=1)
        
        # Volume
        fig.add_trace(go.Bar(
            x=data.index,
            y=data['Volume'],
            name='Volume',
            marker_color='lightblue'
        ), row=4, col=1)
        
        # Add indicators if provided
        if indicators:
            if 'sma20' in indicators:
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=data['Close'].rolling(20).mean(),
                    name='SMA20',
                    line=dict(color='orange', width=2)
                ), row=1, col=1)
            
            if 'rsi' in indicators:
                rsi = calculate_rsi(data)
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=rsi,
                    name='RSI',
                    line=dict(color='purple', width=2)
                ), row=2, col=1)
                
                # Add RSI levels
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        
        fig.update_layout(
            title=f"Advanced Chart: {ticker}",
            height=800,
            showlegend=True,
            xaxis_rangeslider_visible=False
        )
        
        return fig
        
    except Exception as e:
        return go.Figure().add_annotation(text=f"Error creating chart: {str(e)}")

# === MAIN ENHANCED ANALYZER CLASS ===
class EnhancedStockAnalyzer:
    def __init__(self):
        self.paper_trading = PaperTradingSimulator()
        self.watchlist = []
        self.alerts = []
        
    def comprehensive_analysis(self, ticker, period='6mo'):
        """
        Run comprehensive analysis on a stock
        """
        try:
            # Get data
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)
            
            if data.empty:
                return {'error': 'No data available'}
            
            current_price = data['Close'].iloc[-1]
            
            # Run all analyses
            results = {
                'ticker': ticker,
                'current_price': current_price,
                'backtest_ma': backtest_strategy(data, 'ma_crossover'),
                'backtest_rsi': backtest_strategy(data, 'rsi_divergence'),
                'option_chain': analyze_option_chain(ticker, current_price),
                'fundamentals': get_fundamental_ratios(ticker),
                'dcf': calculate_dcf_value(ticker),
                'price_patterns': detect_price_patterns(data),
                'volume_spike': check_volume_spike(data),
                'bid_ask': analyze_bid_ask_spread(ticker),
                'vwap': calculate_vwap(data).iloc[-1]
            }
            
            return results
            
        except Exception as e:
            return {'error': str(e)}
    
    def add_to_watchlist(self, ticker):
        """Add stock to watchlist"""
        if ticker not in self.watchlist:
            self.watchlist.append(ticker)
            return True
        return False
    
    def remove_from_watchlist(self, ticker):
        """Remove stock from watchlist"""
        if ticker in self.watchlist:
            self.watchlist.remove(ticker)
            return True
        return False
    
    def create_alert(self, ticker, alert_type, threshold, condition='above'):
        """Create custom alert"""
        alert = create_smart_alert(ticker, alert_type, threshold, condition)
        self.alerts.append(alert)
        return alert
    
    def check_all_alerts(self):
        """Check all alerts and return triggered ones"""
        triggered_alerts = []
        
        for alert in self.alerts:
            if alert['active'] and not alert['triggered']:
                try:
                    stock = yf.Ticker(alert['ticker'])
                    data = stock.history(period='5d')
                    
                    if not data.empty:
                        result = check_alert_conditions(alert['ticker'], data, alert)
                        if result['triggered']:
                            alert['triggered'] = True
                            triggered_alerts.append({
                                'alert': alert,
                                'result': result
                            })
                except Exception:
                    continue
        
        return triggered_alerts
