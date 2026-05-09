import os
from typing import Optional

def generate_insight(context: str, user_message: str) -> str:
    """Generate AI insight. Tries DeepSeek → Gemini → mock fallback."""
    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
    if deepseek_key and deepseek_key != "your_deepseek_api_key_here":
        result = _deepseek_insight(deepseek_key, context, user_message)
        if result:
            return result

    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key and gemini_key != "your_gemini_api_key_here":
        result = _gemini_insight(gemini_key, context, user_message)
        if result:
            return result

    return _mock_insight(context, user_message)


def _build_prompt(context: str, user_message: str) -> str:
    parts = ["You are a professional data scientist and financial analyst AI assistant."]
    if context:
        parts.append(f"\nContext: {context}")
    parts.append(f"\nUser question: {user_message}")
    parts.append("\nProvide a clear, concise, data-driven response in 3-5 sentences.")
    return "\n".join(parts)


def _deepseek_insight(api_key: str, context: str, user_message: str) -> Optional[str]:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        prompt = _build_prompt(context, user_message)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None


def _gemini_insight(api_key: str, context: str, user_message: str) -> Optional[str]:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = _build_prompt(context, user_message)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return None


def _mock_insight(context: str, user_message: str) -> str:
    msg = (context + " " + user_message).lower()

    if any(w in msg for w in ["anomaly", "anomalies", "spike", "crash", "outlier"]):
        return (
            "Anomaly detection identified statistically significant deviations from expected price behavior. "
            "Price spikes often correlate with earnings announcements or macro news events, while crashes can signal "
            "liquidity-driven selling. The IsolationForest model flags points whose feature combinations are "
            "rare across the distribution — these warrant deeper investigation before drawing conclusions."
        )
    if any(w in msg for w in ["forecast", "predict", "future", "projection"]):
        return (
            "The forecast model combines exponential moving average trend extrapolation with a mean-reverting "
            "random walk calibrated to historical volatility. Confidence intervals widen with the horizon, "
            "reflecting compounding uncertainty. Short-term forecasts (7–14 days) tend to be more reliable "
            "than longer-term projections due to reduced noise accumulation."
        )
    if any(w in msg for w in ["stock", "price", "equity", "share", "aapl", "tsla", "msft", "nvda", "googl"]):
        # Extract symbol if present in context
        symbol = ""
        for tok in context.split():
            if tok.isupper() and 2 <= len(tok) <= 5:
                symbol = tok
                break
        name = f"{symbol} " if symbol else "This stock "
        return (
            f"{name}is exhibiting price action consistent with broader market momentum. "
            "Volume trends suggest institutional participation, which often precedes sustained directional moves. "
            "Key levels to watch are recent swing highs/lows. Risk management via position sizing is advisable "
            "given current market volatility conditions."
        )
    if any(w in msg for w in ["dataset", "data", "csv", "column", "feature", "model"]):
        return (
            "The dataset structure suggests multiple viable modeling approaches. "
            "Numeric features with high variance are strong candidates for normalization before training. "
            "Correlation analysis reveals potential multicollinearity that could affect linear model coefficients. "
            "Consider feature selection techniques like LASSO or tree-based importance scores to reduce dimensionality."
        )
    return (
        "Based on the available data, patterns emerge that warrant both statistical and domain-driven interpretation. "
        "Outlier analysis and trend decomposition are recommended first steps. "
        "Combining quantitative signals with qualitative context typically yields the most actionable insights."
    )


def generate_dataset_insights(analysis: dict) -> list:
    insights = []
    if analysis.get("numeric_columns"):
        insights.append(f"Dataset contains {len(analysis['numeric_columns'])} numeric features suitable for statistical analysis.")
    if analysis.get("missing_values"):
        total_missing = sum(analysis["missing_values"].values())
        insights.append(f"Found {total_missing} missing values across {len(analysis['missing_values'])} columns - consider imputation strategies.")
    if analysis.get("categorical_columns"):
        insights.append(f"{len(analysis['categorical_columns'])} categorical columns detected - encoding recommended before ML modeling.")
    insights.append("Data distribution appears suitable for predictive modeling with standard preprocessing.")
    return insights
