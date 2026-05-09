import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

def detect_stock_anomalies(data: list) -> dict:
    """Detect anomalies in stock price data using Isolation Forest"""
    try:
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        df["pct_change"] = df["close"].pct_change().fillna(0)
        vol_mean = df["volume"].mean()
        rolling_mean = df["volume"].rolling(20, min_periods=1).mean()
        rolling_mean = rolling_mean.replace(0, vol_mean if vol_mean != 0 else 1)
        df["volume_ratio"] = (df["volume"] / rolling_mean).fillna(1.0)

        features = df[["close", "pct_change", "volume_ratio"]].fillna(0)
        model = IsolationForest(contamination=0.05, random_state=42)
        labels = model.fit_predict(features)
        scores = model.score_samples(features)

        anomalies = []
        for i, (label, score) in enumerate(zip(labels, scores)):
            if label == -1:
                pct = float(df["pct_change"].iloc[i])
                atype = "Price Spike" if pct > 0.03 else ("Price Crash" if pct < -0.03 else "Volume Anomaly")
                severity_score = abs(float(score))
                severity = "High" if severity_score > 0.15 else ("Medium" if severity_score > 0.10 else "Low")
                pct_pct = round(pct * 100, 2)
                description = (
                    f"Price moved {pct_pct:+.2f}% with anomalous volume ratio {df['volume_ratio'].iloc[i]:.2f}x"
                )
                anomalies.append({
                    "date": df["date"].iloc[i].strftime("%Y-%m-%d"),
                    "price": round(float(df["close"].iloc[i]), 2),
                    "type": atype,
                    "severity": severity,
                    "severity_score": round(severity_score, 3),
                    "pct_change": pct_pct,
                    "description": description,
                })

        return {
            "total": len(anomalies),
            "anomalies": sorted(anomalies, key=lambda x: x["severity_score"], reverse=True),
        }
    except Exception as e:
        return {"error": str(e), "total": 0, "anomalies": []}
