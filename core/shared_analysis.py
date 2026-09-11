import numpy as np
import pandas as pd


def calculate_rsi(data, period=14):
    delta = data["Close"].diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.mask((loss == 0) & (gain > 0), 100)
    rsi = rsi.mask((loss == 0) & (gain == 0), 50)
    return rsi


def calculate_bollinger_bands(data, period=20, std_dev=2):
    sma = data["Close"].rolling(window=period).mean()
    std = data["Close"].rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return {
        "middle_band": sma,
        "upper_band": upper_band,
        "lower_band": lower_band,
        "band_width": (upper_band - lower_band) / sma
    }


def calculate_macd(data, fast=12, slow=26, signal=9):
    exp1 = data["Close"].ewm(span=fast, adjust=False).mean()
    exp2 = data["Close"].ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return {
        "macd_line": macd_line,
        "signal_line": signal_line,
        "histogram": histogram
    }


def calculate_adx(data, period=14):
    high = data["High"]
    low = data["Low"]
    close = data["Close"]
    
    # Calculate True Range (TR)
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Calculate Directional Movement (DM)
    up = high - high.shift()
    down = low.shift() - low
    
    plus_dm = np.where((up > down) & (up > 0), up, 0)
    minus_dm = np.where((down > up) & (down > 0), down, 0)
    
    # Smooth TR, +DM, -DM
    tr_smoothed = tr.rolling(window=period).sum()
    plus_dm_smoothed = pd.Series(plus_dm, index=data.index).rolling(window=period).sum()
    minus_dm_smoothed = pd.Series(minus_dm, index=data.index).rolling(window=period).sum()
    
    # Calculate +DI and -DI
    plus_di = 100 * (plus_dm_smoothed / tr_smoothed)
    minus_di = 100 * (minus_dm_smoothed / tr_smoothed)
    
    # Calculate DX and ADX
    dx = 100 * abs((plus_di - minus_di) / (plus_di + minus_di))
    adx = dx.rolling(window=period).mean()
    
    return {
        "adx": adx,
        "plus_di": plus_di,
        "minus_di": minus_di
    }


def calculate_vwap(data):
    typical_price = (data["High"] + data["Low"] + data["Close"]) / 3
    vwap = (typical_price * data["Volume"]).cumsum() / data["Volume"].cumsum()
    return vwap


def calculate_atr(data, period=14):
    high = data["High"]
    low = data["Low"]
    close = data["Close"]
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr


def backtest_strategy(data, strategy_type="ma_crossover", initial_capital=10000000,
                      buy_fee=0.0, sell_fee=0.0, slippage=0.0, lot_size=1):
    try:
        results = {
            "total_trades": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "max_drawdown": 0,
            "sharpe_ratio": 0,
            "total_return": 0,
            "equity_curve": [],
            "trades": [],
            "total_fees": 0,
            "total_slippage": 0,
            "cost_assumptions": {
                "buy_fee": buy_fee,
                "sell_fee": sell_fee,
                "slippage": slippage,
                "lot_size": lot_size,
            },
        }

        data = data.copy()
        capital = initial_capital
        equity_curve = [capital]
        trades = []
        position = 0
        entry_price = 0
        entry_cost = 0
        total_fees = 0
        total_slippage = 0

        if buy_fee < 0 or sell_fee < 0 or slippage < 0 or lot_size < 1:
            raise ValueError("Trading cost and lot size parameters must be non-negative")

        if strategy_type == "ma_crossover":
            data["SMA20"] = data["Close"].rolling(20).mean()
            data["SMA50"] = data["Close"].rolling(50).mean()

            for i in range(50, len(data)):
                current_price = data["Close"].iloc[i]
                if data["SMA20"].iloc[i] > data["SMA50"].iloc[i] and position == 0:
                    execution_price = current_price * (1 + slippage)
                    shares = int(capital / (execution_price * (1 + buy_fee)) / lot_size) * lot_size
                    if shares > 0:
                        position = shares
                        entry_price = execution_price
                        entry_cost = shares * execution_price * (1 + buy_fee)
                        total_fees += shares * execution_price * buy_fee
                        total_slippage += shares * abs(execution_price - current_price)
                        capital -= entry_cost
                        trades.append(
                            {
                                "type": "BUY",
                                "price": current_price,
                                "shares": shares,
                                "date": data.index[i],
                                "capital": capital,
                            }
                        )
                elif data["SMA20"].iloc[i] < data["SMA50"].iloc[i] and position > 0:
                    execution_price = current_price * (1 - slippage)
                    gross_proceeds = position * execution_price
                    sell_cost = gross_proceeds * sell_fee
                    capital += gross_proceeds - sell_cost
                    total_fees += sell_cost
                    total_slippage += position * abs(execution_price - current_price)
                    trades.append(
                        {
                            "type": "SELL",
                            "price": execution_price,
                            "shares": position,
                            "date": data.index[i],
                            "capital": capital,
                            "profit": gross_proceeds - sell_cost - entry_cost,
                        }
                    )
                    position = 0
                equity_curve.append(capital + (position * current_price if position > 0 else 0))

        elif strategy_type == "rsi_divergence":
            data["RSI"] = calculate_rsi(data)
            for i in range(14, len(data)):
                current_price = data["Close"].iloc[i]
                current_rsi = data["RSI"].iloc[i]
                if current_rsi < 30 and position == 0:
                    execution_price = current_price * (1 + slippage)
                    shares = int(capital / (execution_price * (1 + buy_fee)) / lot_size) * lot_size
                    if shares > 0:
                        position = shares
                        entry_price = execution_price
                        entry_cost = shares * execution_price * (1 + buy_fee)
                        total_fees += shares * execution_price * buy_fee
                        total_slippage += shares * abs(execution_price - current_price)
                        capital -= entry_cost
                        trades.append(
                            {
                                "type": "BUY",
                                "price": current_price,
                                "shares": shares,
                                "date": data.index[i],
                                "capital": capital,
                            }
                        )
                elif current_rsi > 70 and position > 0:
                    execution_price = current_price * (1 - slippage)
                    gross_proceeds = position * execution_price
                    sell_cost = gross_proceeds * sell_fee
                    capital += gross_proceeds - sell_cost
                    total_fees += sell_cost
                    total_slippage += position * abs(execution_price - current_price)
                    trades.append(
                        {
                            "type": "SELL",
                            "price": execution_price,
                            "shares": position,
                            "date": data.index[i],
                            "capital": capital,
                            "profit": gross_proceeds - sell_cost - entry_cost,
                        }
                    )
                    position = 0
                equity_curve.append(capital + (position * current_price if position > 0 else 0))

        if len(trades) > 0:
            sell_trades = [t for t in trades if t["type"] == "SELL"]
            winning_trades = [t for t in sell_trades if t.get("profit", 0) > 0]
            losing_trades = [t for t in sell_trades if t.get("profit", 0) <= 0]

            results["total_trades"] = len(trades)
            results["win_rate"] = (len(winning_trades) / len(sell_trades) * 100) if sell_trades else 0

            total_profit = sum(t.get("profit", 0) for t in winning_trades)
            total_loss = abs(sum(t.get("profit", 0) for t in losing_trades))
            results["profit_factor"] = total_profit / total_loss if total_loss > 0 else (total_profit if total_profit > 0 else 0)

            peak = max(equity_curve)
            trough = min(equity_curve[equity_curve.index(peak):])
            results["max_drawdown"] = ((peak - trough) / peak) * 100 if peak > 0 else 0

            returns = [
                (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1] * 100
                for i in range(1, len(equity_curve))
                if equity_curve[i - 1] > 0
            ]
            if len(returns) > 1:
                avg_return = sum(returns) / len(returns)
                std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
                results["sharpe_ratio"] = avg_return / std_return if std_return > 0 else 0

            results["total_return"] = ((equity_curve[-1] - initial_capital) / initial_capital) * 100
            results["total_fees"] = total_fees
            results["total_slippage"] = total_slippage
            results["equity_curve"] = equity_curve
            results["trades"] = trades

        return results
    except Exception as e:
        return {
            "total_trades": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "max_drawdown": 0,
            "sharpe_ratio": 0,
            "total_return": 0,
            "equity_curve": [],
            "trades": [],
            "error": str(e),
        }


def monte_carlo_simulation(data, strategy_type="ma_crossover", initial_capital=10000000, simulations=1000):
    try:
        if data is None or data.empty or len(data) < 60:
            return {"error": "Insufficient data for Monte Carlo simulation"}

        results = []
        block_size = min(10, max(3, len(data) // 25))
        n_rows = len(data)

        for _ in range(simulations):
            boot_parts = []
            while sum(len(part) for part in boot_parts) < n_rows:
                start = np.random.randint(0, max(1, n_rows - block_size + 1))
                boot_parts.append(data.iloc[start:start + block_size])
            synthetic_data = pd.concat(boot_parts).iloc[:n_rows].copy()
            synthetic_data.index = data.index

            backtest_result = backtest_strategy(synthetic_data, strategy_type, initial_capital)
            if "error" in backtest_result:
                continue
            results.append(
                {
                    "total_return": backtest_result["total_return"],
                    "max_drawdown": backtest_result["max_drawdown"],
                    "win_rate": backtest_result["win_rate"],
                    "sharpe_ratio": backtest_result["sharpe_ratio"],
                }
            )

        if not results:
            return {"error": "Monte Carlo simulation failed to generate valid runs"}

        returns = [r["total_return"] for r in results]
        drawdowns = [r["max_drawdown"] for r in results]

        return {
            "mean_return": sum(returns) / len(returns),
            "std_return": (sum((r - sum(returns) / len(returns)) ** 2 for r in returns) / len(returns)) ** 0.5,
            "min_return": min(returns),
            "max_return": max(returns),
            "percentile_5": sorted(returns)[int(len(returns) * 0.05)],
            "percentile_95": sorted(returns)[int(len(returns) * 0.95)],
            "mean_drawdown": sum(drawdowns) / len(drawdowns),
            "probability_profit": len([r for r in returns if r > 0]) / len(returns) * 100,
            "simulations": len(results),
        }
    except Exception as e:
        return {
            "mean_return": 0,
            "std_return": 0,
            "min_return": 0,
            "max_return": 0,
            "percentile_5": 0,
            "percentile_95": 0,
            "mean_drawdown": 0,
            "probability_profit": 0,
            "simulations": 0,
            "error": str(e),
        }


def detect_price_patterns(data, pattern_type="breakout"):
    try:
        patterns = []
        current_price = data["Close"].iloc[-1]

        if pattern_type == "breakout":
            resistance = data["High"].rolling(20).max().iloc[-2]
            if current_price > resistance * 1.02:
                patterns.append(
                    {
                        "pattern": "RESISTANCE_BREAKOUT",
                        "level": resistance,
                        "current_price": current_price,
                        "strength": "STRONG" if current_price > resistance * 1.05 else "MODERATE",
                    }
                )

            support = data["Low"].rolling(20).min().iloc[-2]
            if current_price < support * 0.98:
                patterns.append(
                    {
                        "pattern": "SUPPORT_BREAKDOWN",
                        "level": support,
                        "current_price": current_price,
                        "strength": "STRONG" if current_price < support * 0.95 else "MODERATE",
                    }
                )

        elif pattern_type == "pullback":
            recent_high = data["High"].rolling(10).max().iloc[-1]
            recent_low = data["Low"].rolling(10).min().iloc[-1]
            fib_levels = {
                "38.2%": recent_high - (recent_high - recent_low) * 0.382,
                "50%": recent_high - (recent_high - recent_low) * 0.5,
                "61.8%": recent_high - (recent_high - recent_low) * 0.618,
            }
            for level_name, level_price in fib_levels.items():
                if abs(current_price - level_price) / level_price < 0.02:
                    patterns.append(
                        {
                            "pattern": "FIBONACCI_PULLBACH",
                            "level": level_name,
                            "price": level_price,
                            "current_price": current_price,
                        }
                    )

        elif pattern_type == "reversal":
            recent_candles = data.tail(5)
            for i, candle in recent_candles.iterrows():
                body_size = abs(candle["Close"] - candle["Open"])
                lower_shadow = min(candle["Open"], candle["Close"]) - candle["Low"]
                upper_shadow = candle["High"] - max(candle["Open"], candle["Close"])
                if lower_shadow > 2 * body_size and upper_shadow < body_size * 0.3:
                    if candle["Close"] > candle["Open"]:
                        patterns.append({"pattern": "HAMMER", "date": i, "type": "BULLISH_REVERSAL"})
                    else:
                        patterns.append({"pattern": "HANGING_MAN", "date": i, "type": "BEARISH_REVERSAL"})

        return patterns
    except Exception:
        return []


def check_volume_spike(data, threshold=2.0):
    try:
        avg_volume = data["Volume"].rolling(20).mean().iloc[-1]
        current_volume = data["Volume"].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

        if volume_ratio > threshold:
            return {
                "alert": True,
                "volume_ratio": volume_ratio,
                "current_volume": current_volume,
                "avg_volume": avg_volume,
                "severity": "HIGH" if volume_ratio > 5 else "MEDIUM" if volume_ratio > 3 else "LOW",
            }
        return {"alert": False}
    except Exception:
        return {"alert": False}
