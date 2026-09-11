1️⃣ Simpan Semua Signal Jadi Dataset

Tambahin ini di setiap generate_signal berhasil.

import pandas as pd
from datetime import datetime
import os

DATASET_PATH = "signal_history.csv"

def log_signal(symbol, entry, sl, tp, features):
    row = {
        "timestamp": datetime.now(),
        "symbol": symbol,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        **features,
        "outcome": None  # diisi nanti
    }

    df = pd.DataFrame([row])

    if os.path.exists(DATASET_PATH):
        df.to_csv(DATASET_PATH, mode='a', header=False, index=False)
    else:
        df.to_csv(DATASET_PATH, index=False)


Di dalam generate_signal() lo, tambahkan:
features = {
    "rsi": rsi_value,
    "volume_ratio": volume_ratio,
    "atr_pct": atr / entry,
    "ma_slope": ma_slope,
    "regime": regime_code
}

log_signal(symbol, entry, sl, tp, features)

🧠 PHASE 2 — Auto Label Outcome

Bikin evaluator:
def evaluate_outcomes(df_price):
    df = pd.read_csv(DATASET_PATH)

    for i, row in df[df["outcome"].isna()].iterrows():
        entry = row["entry"]
        sl = row["sl"]
        tp = row["tp"]

        future_prices = df_price[df_price.index > pd.to_datetime(row["timestamp"])]

        hit_tp = (future_prices["High"] >= tp).any()
        hit_sl = (future_prices["Low"] <= sl).any()

        if hit_tp:
            df.loc[i, "outcome"] = 1
        elif hit_sl:
            df.loc[i, "outcome"] = 0

    df.to_csv(DATASET_PATH, index=False)

    🧠 PHASE 3 — Train Model (Monster Mode)
pip install scikit-learn

Tambahkan:

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

def train_model():
    df = pd.read_csv(DATASET_PATH)
    df = df.dropna()

    features = ["rsi", "volume_ratio", "atr_pct", "ma_slope", "regime"]
    X = df[features]
    y = df["outcome"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = RandomForestClassifier(n_estimators=200)
    model.fit(X_train, y_train)

    accuracy = model.score(X_test, y_test)

    return model, accuracy

🧠 PHASE 4 — Prediksi Confidence

Saat ada signal baru:
model, acc = train_model()

new_data = pd.DataFrame([features])
prob = model.predict_proba(new_data)[0][1]

print(f"Signal Confidence: {prob*100:.2f}%")

🧠 PHASE 5 — Tambahin Regime Detection (Biar Adaptif)

Tambahkan:
def detect_regime(df):
    if df["Close"].rolling(50).mean().iloc[-1] > df["Close"].rolling(200).mean().iloc[-1]:
        return 1  # trending
    elif df["ATR"].iloc[-1] > df["ATR"].rolling(20).mean().iloc[-1]:
        return 2  # volatile
    else:
        return 0  # sideways

🧠 LEVEL 2 — Feature Importance Analyzer

Tujuannya:
Biar lo tahu fitur mana yang beneran ngasih edge.
Bukan feeling.

Tambahkan setelah training:
def train_model():
    df = pd.read_csv(DATASET_PATH)
    df = df.dropna()

    features = ["rsi", "volume_ratio", "atr_pct", "ma_slope", "regime"]
    X = df[features]
    y = df["outcome"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=6,
        min_samples_split=10,
        random_state=42
    )

    model.fit(X_train, y_train)

    accuracy = model.score(X_test, y_test)

    # FEATURE IMPORTANCE
    importance = pd.DataFrame({
        "feature": features,
        "importance": model.feature_importances_
    }).sort_values(by="importance", ascending=False)

    return model, accuracy, importance
Lalu tampilkan:
model, acc, importance = train_model()

st.write(f"Model Accuracy: {acc*100:.2f}%")
st.dataframe(importance)

🧠 LEVEL 3 — Adaptive Model per Regime

Ini bikin mesin lo jauh lebih cerdas.

Alih-alih 1 model untuk semua kondisi,
kita bikin model per regime.

Step 1 — Pisahkan Dataset
def train_regime_models():
    df = pd.read_csv(DATASET_PATH)
    df = df.dropna()

    features = ["rsi", "volume_ratio", "atr_pct", "ma_slope"]

    models = {}
    accuracies = {}

    for regime in df["regime"].unique():
        df_reg = df[df["regime"] == regime]

        if len(df_reg) < 50:
            continue

        X = df_reg[features]
        y = df_reg["outcome"]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

        model = RandomForestClassifier(
            n_estimators=300,
            max_depth=6,
            random_state=42
        )

        model.fit(X_train, y_train)

        acc = model.score(X_test, y_test)

        models[regime] = model
        accuracies[regime] = acc

    return models, accuracies
Step 2 — Prediksi Berdasarkan Regime Aktif

Saat signal muncul:
regime_now = detect_regime(df_price)

models, accuracies = train_regime_models()

if regime_now in models:
    model = models[regime_now]
    acc = accuracies[regime_now]

    new_data = pd.DataFrame([{
        "rsi": rsi_value,
        "volume_ratio": volume_ratio,
        "atr_pct": atr_pct,
        "ma_slope": ma_slope
    }])

    prob = model.predict_proba(new_data)[0][1]

    st.success(f"Confidence: {prob*100:.2f}%")
    st.write(f"Regime Model Accuracy: {acc*100:.2f}%")
else:
    st.warning("Regime model not enough data yet.")

🧠 PART 1 — Expectancy Engine (Otak Duit Asli)

Tambahkan ini:
def calculate_expectancy(df):
    wins = df[df["outcome"] == 1]
    losses = df[df["outcome"] == 0]

    win_rate = len(wins) / len(df)
    loss_rate = len(losses) / len(df)

    avg_win = (wins["tp"] - wins["entry"]).mean()
    avg_loss = (losses["entry"] - losses["sl"]).mean()

    expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)

    return {
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "expectancy": expectancy
    }
Tampilkan:
metrics = calculate_expectancy(df)
st.write(metrics)
🧠 PART 2 — Position Sizing Berdasarkan Confidence

Kita pakai model Kelly-lite.
def position_size(confidence, rr_ratio, capital):
    edge = (confidence * rr_ratio) - (1 - confidence)
    kelly_fraction = edge / rr_ratio

    # Biar gak brutal, kita pakai 25% dari Kelly
    safe_fraction = max(0, kelly_fraction * 0.25)

    return capital * safe_fraction
Saat signal muncul:
rr = (tp - entry) / (entry - sl)

size = position_size(prob, rr, capital=100000000)

st.success(f"Recommended Position Size: {size:,.0f}")

🧠 PART 3 — Auto Strategy Selection per Regime

Tambahkan tracking performance per regime + per strategy.

Misal lo punya:

Strategy_MA

Strategy_RSI

Strategy_Breakout

Tambahkan kolom strategy_name saat log_signal.

Lalu bikin ranking:
def best_strategy_per_regime(df):
    result = {}

    for regime in df["regime"].unique():
        df_reg = df[df["regime"] == regime]

        grouped = df_reg.groupby("strategy_name")["outcome"].mean()

        if not grouped.empty:
            best = grouped.idxmax()
            result[regime] = best

    return result
Saat regime terdeteksi:
best_map = best_strategy_per_regime(df)

strategy_to_use = best_map.get(regime_now)

st.write(f"Best Strategy in Current Regime: {strategy_to_use}")
