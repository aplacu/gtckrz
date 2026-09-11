"""
Market Timing Analysis for BEI (Bursa Efek Indonesia)
Features: Pre-market vs Post-opening analysis, Session-based timing
"""

import datetime
import pandas as pd
from typing import Dict, Any

def get_bei_session_info():
    """Get BEI trading session information"""
    return {
        'pre_market': {'start': '08:45', 'end': '09:00'},
        'opening_auction': {'start': '09:00', 'end': '09:15'},
        'session_1': {'start': '09:15', 'end': '12:00'},
        'istihtarah': {'start': '12:00', 'end': '13:30'},
        'session_2': {'start': '13:30', 'end': '14:50'},
        'closing_auction': {'start': '14:50', 'end': '15:00'}
    }

def analyze_timing_windows(current_time: str = None) -> Dict[str, Any]:
    """Analyze optimal timing windows for BEI trading"""
    
    if current_time is None:
        current_time = datetime.datetime.now().strftime('%H:%M')
    
    sessions = get_bei_session_info()
    
    # Timing recommendations
    timing_recommendations = {
        'pre_market': {
            'optimal_actions': ['scan_signals', 'prepare_watchlist', 'set_alerts'],
            'risk_level': 'LOW',
            'volatility': 'LOW',
            'liquidity': 'VERY_LOW'
        },
        'opening_auction': {
            'optimal_actions': ['avoid_new_entries', 'monitor_price_discovery'],
            'risk_level': 'HIGH',
            'volatility': 'VERY_HIGH',
            'liquidity': 'INCREASING'
        },
        'session_1_golden_hour': {
            'optimal_actions': ['entry_positions', 'trend_confirmation', 'volume_analysis'],
            'risk_level': 'MEDIUM',
            'volatility': 'MEDIUM',
            'liquidity': 'HIGH'
        },
        'session_1_closing': {
            'optimal_actions': ['partial_exit', 'position_adjustment', 'profit_taking'],
            'risk_level': 'MEDIUM',
            'volatility': 'INCREASING',
            'liquidity': 'HIGH'
        },
        'session_2_restart': {
            'optimal_actions': ['momentum_check', 'trend_continuation', 'new_entries'],
            'risk_level': 'MEDIUM',
            'volatility': 'MEDIUM',
            'liquidity': 'HIGH'
        },
        'session_2_power_hour': {
            'optimal_actions': ['final_entries', 'position_optimization', 'pre_close_setup'],
            'risk_level': 'MEDIUM_HIGH',
            'volatility': 'HIGH',
            'liquidity': 'VERY_HIGH'
        },
        'closing_auction': {
            'optimal_actions': ['avoid_entries', 'final_exit', 'position_closing'],
            'risk_level': 'HIGH',
            'volatility': 'VERY_HIGH',
            'liquidity': 'EXTREME'
        }
    }
    
    return {
        'current_time': current_time,
        'sessions': sessions,
        'recommendations': timing_recommendations,
        'next_optimal_window': get_next_optimal_window(current_time)
    }

def get_next_optimal_window(current_time: str) -> Dict[str, Any]:
    """Get the next optimal trading window"""
    
    time_windows = [
        ('09:15', 'session_1_start', 'Entry positions - Session 1 begins'),
        ('10:00', 'session_1_golden', 'Golden hour - High probability entries'),
        ('11:30', 'session_1_closing', 'Pre-break positioning'),
        ('13:30', 'session_2_restart', 'Session 2 momentum check'),
        ('14:00', 'session_2_power', 'Power hour - Final entries'),
        ('14:45', 'pre_closing', 'Pre-auction positioning')
    ]
    
    current_hour, current_minute = map(int, current_time.split(':'))
    current_minutes = current_hour * 60 + current_minute
    
    for window_time, window_key, description in time_windows:
        window_hour, window_minute = map(int, window_time.split(':'))
        window_minutes = window_hour * 60 + window_minute
        
        if current_minutes < window_minutes:
            return {
                'time': window_time,
                'key': window_key,
                'description': description,
                'minutes_until': window_minutes - current_minutes
            }
    
    return {'time': '09:15', 'key': 'tomorrow_session', 'description': 'Tomorrow session', 'minutes_until': 999}

def compare_pre_post_market(ticker: str, data: pd.DataFrame) -> Dict[str, Any]:
    """Compare pre-market vs post-opening analysis"""
    
    if len(data) < 2:
        return {'error': 'Insufficient data for comparison'}
    
    # Pre-market analysis (using previous close)
    prev_close = data['Close'].iloc[-2]
    prev_volume = data['Volume'].iloc[-2]
    
    # Post-opening analysis (using current data)
    current_open = data['Open'].iloc[-1]
    current_price = data['Close'].iloc[-1]
    current_volume = data['Volume'].iloc[-1]
    
    # Calculate gaps and changes
    price_gap = current_open - prev_close
    price_gap_pct = (price_gap / prev_close) * 100
    
    current_change = current_price - current_open
    current_change_pct = (current_change / current_open) * 100
    
    volume_ratio = current_volume / prev_volume if prev_volume > 0 else 0
    
    # Signal comparison
    pre_market_signal = generate_pre_market_signal(prev_close, prev_volume)
    post_opening_signal = generate_post_opening_signal(current_price, current_volume, price_gap_pct)
    
    return {
        'pre_market': {
            'signal': pre_market_signal,
            'reference_price': prev_close,
            'reference_volume': prev_volume
        },
        'post_opening': {
            'signal': post_opening_signal,
            'current_price': current_price,
            'current_volume': current_volume,
            'open_price': current_open,
            'intraday_change': current_change_pct
        },
        'market_dynamics': {
            'price_gap_pct': price_gap_pct,
            'volume_ratio': volume_ratio,
            'signal_change': detect_signal_change(pre_market_signal, post_opening_signal)
        }
    }

def generate_pre_market_signal(prev_close: float, prev_volume: float) -> str:
    """Generate signal based on pre-market conditions"""
    # Simplified pre-market signal logic
    if prev_volume > 1000000:  # High volume previous day
        return "BULLISH_SETUP"
    elif prev_volume < 500000:  # Low volume
        return "NEUTRAL_SETUP"
    else:
        return "STANDARD_SETUP"

def generate_post_opening_signal(current_price: float, current_volume: float, gap_pct: float) -> str:
    """Generate signal based on post-opening conditions"""
    
    # Gap analysis
    if gap_pct > 2:
        gap_signal = "STRONG_GAP_UP"
    elif gap_pct > 1:
        gap_signal = "MODERATE_GAP_UP"
    elif gap_pct < -2:
        gap_signal = "STRONG_GAP_DOWN"
    elif gap_pct < -1:
        gap_signal = "MODERATE_GAP_DOWN"
    else:
        gap_signal = "FLAT_OPENING"
    
    # Volume analysis
    if current_volume > 2000000:  # High volume
        volume_signal = "HIGH_VOLUME"
    elif current_volume < 500000:  # Low volume
        volume_signal = "LOW_VOLUME"
    else:
        volume_signal = "NORMAL_VOLUME"
    
    # Combined signal
    signal_combinations = {
        "STRONG_GAP_UP": {"HIGH_VOLUME": "STRONG_BUY", "NORMAL_VOLUME": "BUY", "LOW_VOLUME": "CAUTIOUS_BUY"},
        "MODERATE_GAP_UP": {"HIGH_VOLUME": "BUY", "NORMAL_VOLUME": "BUY", "LOW_VOLUME": "NEUTRAL"},
        "FLAT_OPENING": {"HIGH_VOLUME": "BUY", "NORMAL_VOLUME": "NEUTRAL", "LOW_VOLUME": "HOLD"},
        "MODERATE_GAP_DOWN": {"HIGH_VOLUME": "SELL", "NORMAL_VOLUME": "NEUTRAL", "LOW_VOLUME": "HOLD"},
        "STRONG_GAP_DOWN": {"HIGH_VOLUME": "STRONG_SELL", "NORMAL_VOLUME": "SELL", "LOW_VOLUME": "CAUTIOUS_SELL"}
    }
    
    return signal_combinations.get(gap_signal, {}).get(volume_signal, "NEUTRAL")

def detect_signal_change(pre_signal: str, post_signal: str) -> Dict[str, Any]:
    """Detect if signal changed from pre-market to post-opening"""
    
    bullish_signals = ["STRONG_BUY", "BUY", "CAUTIOUS_BUY"]
    bearish_signals = ["STRONG_SELL", "SELL", "CAUTIOUS_SELL"]
    neutral_signals = ["NEUTRAL", "HOLD"]
    
    pre_category = categorize_signal(pre_signal, bullish_signals, bearish_signals, neutral_signals)
    post_category = categorize_signal(post_signal, bullish_signals, bearish_signals, neutral_signals)
    
    change_type = "NO_CHANGE"
    if pre_category != post_category:
        change_type = f"{pre_category}_TO_{post_category}"
    
    return {
        'change_type': change_type,
        'pre_category': pre_category,
        'post_category': post_category,
        'significance': get_signal_significance(change_type)
    }

def categorize_signal(signal: str, bullish: list, bearish: list, neutral: list) -> str:
    """Categorize signal into bullish, bearish, or neutral"""
    if signal in bullish:
        return "BULLISH"
    elif signal in bearish:
        return "BEARISH"
    else:
        return "NEUTRAL"

def get_signal_significance(change_type: str) -> str:
    """Determine the significance of signal change"""
    significance_map = {
        "NEUTRAL_TO_BULLISH": "HIGH",
        "BEARISH_TO_BULLISH": "VERY_HIGH",
        "BULLISH_TO_BEARISH": "VERY_HIGH",
        "NEUTRAL_TO_BEARISH": "HIGH",
        "BULLISH_TO_NEUTRAL": "MEDIUM",
        "BEARISH_TO_NEUTRAL": "MEDIUM"
    }
    return significance_map.get(change_type, "LOW")

def get_session_based_recommendation(session: str, data: pd.DataFrame) -> Dict[str, Any]:
    """Get trading recommendations based on current session"""
    
    if data.empty:
        return {'error': 'No data available'}
    
    latest_data = data.iloc[-1]
    
    session_recommendations = {
        'session_1': {
            'optimal_entry_time': '09:15-10:30',
            'optimal_exit_time': '11:30-12:00',
            'risk_management': 'Tight stops, quick profits',
            'focus': 'Trend establishment, volume confirmation'
        },
        'session_2': {
            'optimal_entry_time': '13:30-14:30',
            'optimal_exit_time': '14:45-15:00',
            'risk_management': 'Moderate stops, trend following',
            'focus': 'Momentum continuation, closing strength'
        }
    }
    
    if session in {"session_1", "session_2", "auction_period"}:
        current_session = session
    else:
        current_session = get_current_session(session)
    
    return {
        'current_session': current_session,
        'recommendations': session_recommendations.get(current_session, {}),
        'market_condition': analyze_current_condition(latest_data),
        'next_action': suggest_next_action(current_session, latest_data)
    }

def get_current_session(session_time: str) -> str:
    """Determine current trading session"""
    # Simplified session detection
    if '09:15' <= session_time <= '12:00':
        return 'session_1'
    elif '13:30' <= session_time <= '14:50':
        return 'session_2'
    else:
        return 'auction_period'

def analyze_current_condition(data: pd.Series) -> str:
    """Analyze current market condition"""
    # Simplified condition analysis
    if data.get('Volume', 0) > data.get('Volume_Avg', 0) * 1.5:
        return 'HIGH_VOLUME_BREAKOUT'
    elif data.get('RSI', 50) > 70:
        return 'OVERBOUGHT'
    elif data.get('RSI', 50) < 30:
        return 'OVERSOLD'
    else:
        return 'NORMAL_CONDITION'

def suggest_next_action(session: str, data: pd.Series) -> str:
    """Suggest next trading action based on session and condition"""
    condition = analyze_current_condition(data)
    
    action_matrix = {
        'session_1': {
            'HIGH_VOLUME_BREAKOUT': 'CONSIDER_ENTRY',
            'OVERBOUGHT': 'WAIT_FOR_PULLBACK',
            'OVERSOLD': 'LOOK_FOR_BOUNCE',
            'NORMAL_CONDITION': 'MONITOR_CLOSELY'
        },
        'session_2': {
            'HIGH_VOLUME_BREAKOUT': 'RIDE_MOMENTUM',
            'OVERBOUGHT': 'PREPARE_EXIT',
            'OVERSOLD': 'LOOK_FOR_RECOVERY',
            'NORMAL_CONDITION': 'FOLLOW_TREND'
        }
    }
    
    return action_matrix.get(session, {}).get(condition, 'HOLD_POSITION')

# Main timing analysis function
def comprehensive_timing_analysis(ticker: str, data: pd.DataFrame, current_time: str = None) -> Dict[str, Any]:
    """Comprehensive market timing analysis"""
    
    if data.empty or len(data) < 2:
        return {'error': 'Insufficient data for timing analysis'}
    
    # Get timing windows
    timing_info = analyze_timing_windows(current_time)
    
    # Compare pre vs post market
    comparison = compare_pre_post_market(ticker, data)
    
    # Session-based recommendations
    current_session = get_current_session(current_time or datetime.datetime.now().strftime('%H:%M'))
    session_recommendations = get_session_based_recommendation(current_session, data)
    
    return {
        'ticker': ticker,
        'timing_analysis': timing_info,
        'pre_post_comparison': comparison,
        'session_recommendations': session_recommendations,
        'summary': generate_timing_summary(timing_info, comparison, session_recommendations)
    }

def generate_timing_summary(timing_info: Dict, comparison: Dict, session_rec: Dict) -> str:
    """Generate concise timing summary"""
    
    next_window = timing_info.get('next_optimal_window', {})
    signal_change = comparison.get('market_dynamics', {}).get('signal_change', {})
    
    summary_parts = []
    
    # Next optimal window
    if next_window.get('minutes_until', 999) < 60:
        summary_parts.append(f"Next optimal window: {next_window.get('time', '')} ({next_window.get('description', '')})")
    
    # Signal change
    change_type = signal_change.get('change_type', '')
    if change_type != 'NO_CHANGE':
        significance = signal_change.get('significance', '')
        summary_parts.append(f"Signal change: {change_type} ({significance} significance)")
    
    # Session recommendation
    next_action = session_rec.get('next_action', '')
    if next_action:
        summary_parts.append(f"Recommended action: {next_action}")
    
    return " | ".join(summary_parts) if summary_parts else "Market timing neutral - monitor for opportunities"
